"""
Tests para FP-019 Késher (HF-034)
Verifica: GestorPersonas + TinyDB, regex persona en nlu.py, requirements.txt.
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
# personas.py — GestorPersonas
# ═══════════════════════════════════════════════
print("\n== FP-019: GestorPersonas ==")

check("FP19-01", "import computadora.memoria.personas", lambda: (
    True, "importable"
) if __import__('golem.memoria.personas', fromlist=['GestorPersonas']) else (False, ""))

def _check_class_exists():
    from computadora.memoria.personas import GestorPersonas
    return True, f"GestorPersonas class OK"
check("FP19-02", "GestorPersonas class existe", _check_class_exists)

def _check_singleton():
    from computadora.memoria.personas import obtener_gestor
    return callable(obtener_gestor), "obtener_gestor() callable"
check("FP19-03", "obtener_gestor() singleton existe", _check_singleton)

def _check_methods():
    from computadora.memoria.personas import GestorPersonas
    methods = ['bootstrap_amo', 'obtener_amo', 'obtener_persona',
               'registrar_persona', 'actualizar_embedding', 'identificar_por_voz']
    found = [m for m in methods if hasattr(GestorPersonas, m)]
    missing = [m for m in methods if m not in found]
    return not missing, f"found={len(found)}/6 missing={missing or 'none'}"
check("FP19-04", "GestorPersonas tiene 6 métodos clave", _check_methods)

def _check_migrar():
    from computadora.memoria.personas import GestorPersonas
    return hasattr(GestorPersonas, 'migrar_desde_json'), "migrar_desde_json"
check("FP19-05", "GestorPersonas.migrar_desde_json existe", _check_migrar)

# ═══════════════════════════════════════════════
# nlu.py — regex de persona
# ═══════════════════════════════════════════════
print("\n== FP-019: nlu.py regex persona ==")

def _check_nlu_persona_regex():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    patterns = ['_RE_PRESENTAR_PERSONA', '_RE_MI_NOMBRE', '_RE_RELACION',
                '_RE_RECUERDA_DATO', '_RE_OLVIDA_PERSONA']
    found = [p for p in patterns if p in src]
    missing = [p for p in patterns if p not in found]
    return len(found) >= 4, f"found={found}, missing={missing}"
check("FP19-06", "nlu.py tiene regex de persona (mínimo 4/5)", _check_nlu_persona_regex)

def _check_re_presentar():
    from computadora.cerebro.nlu import _RE_PRESENTAR_PERSONA
    test_ok = bool(_RE_PRESENTAR_PERSONA.search("te presento a María"))
    return test_ok, f"matches='te presento a María'={test_ok}"
check("FP19-07", "_RE_PRESENTAR_PERSONA matchea 'te presento a María'", _check_re_presentar)

def _check_re_mi_nombre():
    from computadora.cerebro.nlu import _RE_MI_NOMBRE
    test_ok = bool(_RE_MI_NOMBRE.search("mi nombre es Juan"))
    return test_ok, f"matches='mi nombre es Juan'={test_ok}"
check("FP19-08", "_RE_MI_NOMBRE matchea 'mi nombre es Juan'", _check_re_mi_nombre)

# ═══════════════════════════════════════════════
# requirements.txt — TinyDB
# ═══════════════════════════════════════════════
print("\n== FP-019: requirements.txt ==")

def _check_tinydb_req():
    req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
    if not os.path.exists(req_path):
        return False, "requirements.txt no existe"
    content = open(req_path, encoding='utf-8').read().lower()
    return 'tinydb' in content, f"tinydb={'encontrado' if 'tinydb' in content else 'NO encontrado'}"
check("FP19-09", "tinydb en requirements.txt", _check_tinydb_req)

def _check_tinydb_import():
    try:
        import tinydb
        return True, f"v{tinydb.__version__}"
    except ImportError:
        return False, "tinydb no instalado"
check("FP19-10", "tinydb importable en .venv", _check_tinydb_import)

# ═══════════════════════════════════════════════
# COHERENCIA
# ═══════════════════════════════════════════════
print("\n== COHERENCIA ==")

def _check_persona_imports():
    errores = []
    for m in ['golem.memoria.personas']:
        try:
            __import__(m)
        except Exception as e:
            errores.append(f"{m}: {e}")
    return not errores, f"{'OK' if not errores else errores}"
check("FP19-11", "golem.memoria.personas importa sin error", _check_persona_imports)

def _check_nlu_persona_handler():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    has_presentar = 'presentar' in src.lower() or '_RE_PRESENTAR' in src
    has_persona_import = 'personas' in src or 'GestorPersonas' in src or 'obtener_gestor' in src
    return has_presentar and has_persona_import, \
        f"handler_presentar={has_presentar}, import_persona={has_persona_import}"
check("FP19-12", "nlu.py importa y usa GestorPersonas", _check_nlu_persona_handler)

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
failed = total - passed
print(f"\n{'='*60}")
print(f"FP-019 / HF-034 RESULTADO: {passed} PASS / {failed} FAIL / {total} TOTAL")
if failed:
    print("FALLOS:")
    for id, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id}: {desc} -- {det}")
print(f"{'='*60}")

