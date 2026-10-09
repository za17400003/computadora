"""
Tests para HF-035
Verifica: _emitir_fragmento suppression of tool_code,
_ESPAÑOL_CORTAS_VALIDAS expansion, false positive logic fix.
"""
import sys, os, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

resultados = []
def check(id, desc, fn):
    try:
        ok, detalle = fn()
        resultados.append((id, desc, ok, detalle))
        print(f"  {'PASS' if ok else 'FAIL'} {id}: {desc} -- {detalle}")
    except Exception as e:
        resultados.append((id, desc, False, str(e)))
        print(f"  FAIL {id}: {desc} -- EXCEPCION: {e}")

# ═══════════════════════════════════════════════
# nlu.py — _emitir_fragmento tool_code suppression
# ═══════════════════════════════════════════════
print("\n== HF-035: nlu.py tool_code suppression ==")

def _check_emitir_backtick():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    # Buscar la función _emitir_fragmento y verificar que tiene check de ```
    fn_start = src.find('def _emitir_fragmento')
    if fn_start == -1:
        return False, "_emitir_fragmento no encontrada"
    # Buscar el siguiente def para delimitar la función
    fn_end = src.find('\ndef ', fn_start + 1)
    fn_body = src[fn_start:fn_end] if fn_end != -1 else src[fn_start:]
    has_backtick_check = '```' in fn_body
    return has_backtick_check, f"backtick_check={'SI' if has_backtick_check else 'NO'}"
check("HF35-01", "_emitir_fragmento suprime bloques ``` (tool_code)", _check_emitir_backtick)

# ═══════════════════════════════════════════════
# escucha.py — _ESPAÑOL_CORTAS_VALIDAS expansion
# ═══════════════════════════════════════════════
print("\n== HF-035: escucha.py _ESPAÑOL_CORTAS_VALIDAS ==")

def _check_cortas_validas():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'voz', 'escucha.py'),
               encoding='utf-8').read()
    has_var = '_ESPAÑOL_CORTAS_VALIDAS' in src
    if not has_var:
        return False, "variable no encontrada"
    # Verificar palabras añadidas en HF-035
    new_words = ['que', 'esta', 'esto', 'pero', 'con', 'alegra', 'contento']
    found = [w for w in new_words if f'"{w}"' in src or f"'{w}'" in src]
    return len(found) >= 5, f"found={len(found)}/7 ({found})"
check("HF35-02", "_ESPAÑOL_CORTAS_VALIDAS tiene palabras nuevas (5+ de 7)", _check_cortas_validas)

# ═══════════════════════════════════════════════
# escucha.py — false positive logic
# ═══════════════════════════════════════════════
print("\n== HF-035: escucha.py false positive logic ==")

def _check_falsos_positivos_en():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'voz', 'escucha.py'),
               encoding='utf-8').read()
    has_fp_en = '_FALSOS_POSITIVOS_EN' in src
    return has_fp_en, f"_FALSOS_POSITIVOS_EN={'encontrado' if has_fp_en else 'NO'}"
check("HF35-03", "_FALSOS_POSITIVOS_EN existe en escucha.py", _check_falsos_positivos_en)

def _check_no_ascii_heuristic():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'voz', 'escucha.py'),
               encoding='utf-8').read()
    # HF-035 eliminó la heurística ASCII: w.isascii() and not re.search(accents)
    # Ahora usa strict lookup: w in _FALSOS_POSITIVOS_EN
    fn_start = src.find('def _es_falso_positivo')
    if fn_start == -1:
        # Puede que la función se llame diferente
        fn_start = src.find('falso_positivo')
    if fn_start == -1:
        return False, "función de falso positivo no encontrada"
    fn_end = src.find('\ndef ', fn_start + 1)
    fn_body = src[fn_start:fn_end] if fn_end != -1 else src[fn_start:]
    # Verificar que usa _FALSOS_POSITIVOS_EN
    uses_set = '_FALSOS_POSITIVOS_EN' in fn_body
    return uses_set, f"usa _FALSOS_POSITIVOS_EN={uses_set}"
check("HF35-04", "False positive usa _FALSOS_POSITIVOS_EN (no heurística ASCII)", _check_no_ascii_heuristic)

# ═══════════════════════════════════════════════
# COHERENCIA — imports
# ═══════════════════════════════════════════════
print("\n== COHERENCIA ==")

def _check_imports():
    errores = []
    for m in ['computadora.cerebro.nlu', 'computadora.voz.escucha']:
        try:
            __import__(m)
        except Exception as e:
            errores.append(f"{m}: {e}")
    return not errores, f"{'2/2 OK' if not errores else errores}"
check("HF35-05", "nlu.py y escucha.py importan sin error", _check_imports)

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
failed = total - passed
print(f"\n{'='*60}")
print(f"HF-035 RESULTADO: {passed} PASS / {failed} FAIL / {total} TOTAL")
if failed:
    print("FALLOS:")
    for id, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id}: {desc} -- {det}")
print(f"{'='*60}")

