"""
Tests para FP-018 Tikún HaNetivot (HF-033)
Verifica: modelo_discovery.py, copilot_api model detection,
nivel1_aprendido Keter regex, nlu _RE_PIENSA routing, Regla #15.
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
# modelo_discovery.py
# ═══════════════════════════════════════════════
print("\n== FP-018: modelo_discovery.py ==")

check("FP18-01", "Import modelo_discovery", lambda: (
    True, "importable"
) if __import__('computadora.cerebro.modelo_discovery', fromlist=['descubrir_modelos']) else (False, ""))

def _check_constants():
    from computadora.cerebro import modelo_discovery as md
    has_cache_path = hasattr(md, '_CACHE_PATH')
    has_ttl = hasattr(md, 'CACHE_TTL') and md.CACHE_TTL == 86400
    has_nombre = hasattr(md, '_NOMBRE_VALIDO')
    has_ignorados = hasattr(md, '_MODELOS_IGNORADOS') and isinstance(md._MODELOS_IGNORADOS, frozenset)
    return all([has_cache_path, has_ttl, has_nombre, has_ignorados]), \
        f"cache={has_cache_path}, ttl={has_ttl}, nombre_valido={has_nombre}, ignorados={has_ignorados}"
check("FP18-02", "Constantes de modelo_discovery", _check_constants)

def _check_prioridad():
    from computadora.cerebro.modelo_discovery import _prioridad_modelo
    p_sonnet = _prioridad_modelo("claude-sonnet-4")
    p_gpt = _prioridad_modelo("gpt-4o")
    p_mini = _prioridad_modelo("gpt-4o-mini")
    ok = p_sonnet < p_gpt <= p_mini  # sonnet mejor que gpt, gpt mejor o igual que mini
    return ok, f"sonnet={p_sonnet}, gpt4o={p_gpt}, mini={p_mini}"
check("FP18-03", "_prioridad_modelo: sonnet > gpt-4o > mini", _check_prioridad)

def _check_nombre_valido():
    from computadora.cerebro import modelo_discovery as md
    pat = re.compile(md._NOMBRE_VALIDO)
    valid = ["claude-sonnet-4", "gpt-4o", "gpt-4o-mini", "o1-mini"]
    invalid = ["<script>", "rm -rf", "model with spaces", "a"]
    ok_valid = all(pat.match(n) for n in valid)
    ok_invalid = all(not pat.match(n) for n in invalid)
    return ok_valid and ok_invalid, f"valid_pass={ok_valid}, invalid_reject={ok_invalid}"
check("FP18-04", "_NOMBRE_VALIDO regex valida y rechaza correctamente", _check_nombre_valido)

def _check_descubrir_callable():
    from computadora.cerebro.modelo_discovery import descubrir_modelos
    return callable(descubrir_modelos), "callable"
check("FP18-05", "descubrir_modelos() es callable", _check_descubrir_callable)

def _check_cache_fns():
    from computadora.cerebro import modelo_discovery as md
    has_cargar = callable(getattr(md, '_cargar_cache', None))
    has_guardar = callable(getattr(md, '_guardar_cache', None))
    return has_cargar and has_guardar, f"cargar={has_cargar}, guardar={has_guardar}"
check("FP18-06", "_cargar_cache y _guardar_cache existen", _check_cache_fns)

# ═══════════════════════════════════════════════
# copilot_api.py — model selection (FP-016/018)
# ═══════════════════════════════════════════════
print("\n== FP-018: copilot_api model selection ==")

def _check_copilot_methods():
    from computadora.cerebro.copilot_api import CerebroCopilot
    has_detectar = hasattr(CerebroCopilot, 'detectar_modelo_disponible')
    has_codigo = hasattr(CerebroCopilot, 'pensar_codigo')
    has_general = hasattr(CerebroCopilot, 'pensar_general')
    return all([has_detectar, has_codigo, has_general]), \
        f"detectar={has_detectar}, codigo={has_codigo}, general={has_general}"
check("FP18-07", "CerebroCopilot: detectar_modelo, pensar_codigo, pensar_general", _check_copilot_methods)

def _check_modelos_hardcoded():
    from computadora.cerebro.copilot_api import CerebroCopilot
    has_modelos_codigo = hasattr(CerebroCopilot, '_MODELOS_CODIGO')
    has_gratuito = hasattr(CerebroCopilot, '_MODELO_GRATUITO')
    return has_modelos_codigo and has_gratuito, \
        f"modelos_codigo={has_modelos_codigo}, gratuito={has_gratuito}"
check("FP18-08", "CerebroCopilot tiene _MODELOS_CODIGO y _MODELO_GRATUITO", _check_modelos_hardcoded)

# ═══════════════════════════════════════════════
# nivel1_aprendido.py — Keter regex (FP-016)
# ═══════════════════════════════════════════════
print("\n== FP-018: nivel1_aprendido Keter regex ==")

def _check_keter_method():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    has_keter = hasattr(Nivel1Aprendido, '_generar_regex_con_keter')
    has_seguro = hasattr(Nivel1Aprendido, '_generar_regex_seguro')
    has_validar = hasattr(Nivel1Aprendido, '_validar_regex')
    return all([has_keter, has_seguro, has_validar]), \
        f"keter={has_keter}, seguro={has_seguro}, validar={has_validar}"
check("FP18-09", "Nivel1Aprendido: _generar_regex_con_keter + _seguro + _validar", _check_keter_method)

def _check_validar_regex():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    n = Nivel1Aprendido()
    # Regex válido
    ok_valid = n._validar_regex(r"\bhola\b")
    # Regex peligroso: (.+)+ es ReDoS catastrófico
    ok_redos = not n._validar_regex(r"(.+)+")
    # Regex peligroso: backreference
    ok_backref = not n._validar_regex(r"(\w+)\1")
    return ok_valid and ok_redos and ok_backref, \
        f"valid={ok_valid}, redos_blocked={ok_redos}, backref_blocked={ok_backref}"
check("FP18-10", "_validar_regex: acepta válido, bloquea peligrosos", _check_validar_regex)

# ═══════════════════════════════════════════════
# nlu.py — routing _RE_PIENSA (FP-016)
# ═══════════════════════════════════════════════
print("\n== FP-018: nlu.py routing ==")

def _check_re_piensa():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    has_profundo = '_RE_PIENSA_PROFUNDO' in src or '_RE_PENSAR_PROFUNDO' in src
    has_piensa = '_RE_PIENSA' in src or '_RE_PENSAR' in src
    return has_profundo and has_piensa, f"profundo={has_profundo}, piensa={has_piensa}"
check("FP18-11", "_RE_PIENSA_PROFUNDO y _RE_PIENSA en nlu.py", _check_re_piensa)

# ═══════════════════════════════════════════════
# DEVELOPMENT_WORKFLOW.md — Regla #15
# ═══════════════════════════════════════════════
print("\n== FP-018: Regla #15 ==")

def _check_rule15():
    wf_path = os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md')
    content = open(wf_path, encoding='utf-8').read()
    has_rule = '| **15** |' in content
    has_integracion = 'integración' in content.lower() or 'integracion' in content.lower()
    return has_rule and has_integracion, f"rule15={has_rule}, integracion={has_integracion}"
check("FP18-12", "Regla #15 (Análisis de integración) en WORKFLOW", _check_rule15)

# ═══════════════════════════════════════════════
# COHERENCIA
# ═══════════════════════════════════════════════
print("\n== COHERENCIA ==")

def _check_imports():
    errores = []
    for m in ['computadora.cerebro.modelo_discovery', 'computadora.cerebro.copilot_api',
              'computadora.cerebro.nivel1_aprendido', 'computadora.cerebro.nlu']:
        try:
            __import__(m)
        except Exception as e:
            errores.append(f"{m}: {e}")
    return not errores, f"{'4/4 OK' if not errores else errores}"
check("FP18-13", "4 módulos modificados importan sin error", _check_imports)

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
failed = total - passed
print(f"\n{'='*60}")
print(f"FP-018 / HF-033 RESULTADO: {passed} PASS / {failed} FAIL / {total} TOTAL")
if failed:
    print("FALLOS:")
    for id, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id}: {desc} -- {det}")
print(f"{'='*60}")

