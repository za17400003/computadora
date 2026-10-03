"""
Tests para FP-020 Olam HaZeh + HF-036 Auto-compactar
Verifica: imports, signals, callbacks, regex, constantes, estados visuales.
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
# FASE FP-020: Gevurá visual + Tzimtzum 3 triggers
# ═══════════════════════════════════════════════
print("\n== FP-020: Olam HaZeh — Gevurá + Tzimtzum ==")

# --- Imports ---
check("FP20-01", "Import ventana_principal (signals)", lambda: (
    True,
    "importable"
) if __import__('golem.interfaz.ventana_principal', fromlist=['HiloPensamiento']) else (False, ""))

check("FP20-02", "Import nlu (callbacks)", lambda: (
    True,
    "importable"
) if __import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora']) else (False, ""))

check("FP20-03", "Import orquestador (set_callbacks)", lambda: (
    True,
    "importable"
) if __import__('golem.nucleo.orquestador', fromlist=['Orquestador']) else (False, ""))

check("FP20-04", "Import vida_autonoma", lambda: (
    True,
    "importable"
) if __import__('golem.interfaz.vida_autonoma', fromlist=['VidaAutonoma']) else (False, ""))

# --- Signals en HiloPensamiento ---
def _check_signal(nombre):
    from computadora.interfaz.ventana_principal import HiloPensamiento
    return hasattr(HiloPensamiento, nombre), f"{nombre} existe={hasattr(HiloPensamiento, nombre)}"

check("FP20-05", "HiloPensamiento.bloqueo_seguridad signal", lambda: _check_signal("bloqueo_seguridad"))
check("FP20-06", "HiloPensamiento.tzimtzum_solicitado signal", lambda: _check_signal("tzimtzum_solicitado"))

# --- Bridge methods en HiloPensamiento ---
def _check_bridge(nombre):
    from computadora.interfaz.ventana_principal import HiloPensamiento
    return hasattr(HiloPensamiento, nombre), f"{nombre} existe={hasattr(HiloPensamiento, nombre)}"

check("FP20-07", "HiloPensamiento._on_bloqueo_seguridad bridge", lambda: _check_bridge("_on_bloqueo_seguridad"))
check("FP20-08", "HiloPensamiento._on_tzimtzum bridge", lambda: _check_bridge("_on_tzimtzum"))

# --- Callbacks en CerebroComputadora ---
def _check_callback():
    from computadora.cerebro.nlu import CerebroComputadora
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    has_bloqueo = 'on_bloqueo_seguridad' in src
    has_tzimtzum = 'on_tzimtzum' in src
    return has_bloqueo and has_tzimtzum, f"on_bloqueo_seguridad={has_bloqueo}, on_tzimtzum={has_tzimtzum}"

check("FP20-09", "CerebroComputadora callbacks: on_bloqueo_seguridad + on_tzimtzum", _check_callback)

# --- Orquestador set_callbacks tiene los nuevos params ---
def _check_orq_params():
    import inspect
    from computadora.nucleo.orquestador import Orquestador
    sig = inspect.signature(Orquestador.set_callbacks)
    params = list(sig.parameters.keys())
    has_bloqueo = 'on_bloqueo_seguridad' in params
    has_tzimtzum = 'on_tzimtzum' in params
    return has_bloqueo and has_tzimtzum, f"params={params}"

check("FP20-10", "Orquestador.set_callbacks tiene on_bloqueo_seguridad + on_tzimtzum", _check_orq_params)

# --- _RE_TZIMTZUM regex existe y matchea ---
def _check_re_tzimtzum():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    if '_RE_TZIMTZUM' not in src:
        return False, "_RE_TZIMTZUM no encontrado en nlu.py"
    # Extraer el regex y verificar patterns
    # Importar directamente
    m = re.search(r'_RE_TZIMTZUM\s*=\s*re\.compile\(\s*r"([^"]+)"', src)
    if not m:
        return False, "No se pudo extraer el pattern"
    pattern = re.compile(m.group(1), re.IGNORECASE)
    tests = [
        ("hazte pequeño", True),
        ("contráete", True),
        ("escóndete", True),
        ("déjame solo", True),
        ("déjame tranquilo", True),
        ("déjame en paz", True),
        ("hola golem", False),
    ]
    fails = []
    for texto, esperado in tests:
        resultado = bool(pattern.search(texto))
        if resultado != esperado:
            fails.append(f"'{texto}'→{resultado} (esperado {esperado})")
    if fails:
        return False, f"Fallos: {fails}"
    return True, f"7/7 patterns OK"

check("FP20-11", "_RE_TZIMTZUM regex matchea correctamente", _check_re_tzimtzum)

# --- _RE_MOVIMIENTO ya NO contiene patterns de Tzimtzum ---
def _check_re_mov_separado():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    # Buscar _RE_MOVIMIENTO y verificar que NO tiene "hazte pequeño"
    m = re.search(r'_RE_MOVIMIENTO\s*=\s*re\.compile\(\s*r"([^"]+)"', src)
    if not m:
        return False, "_RE_MOVIMIENTO no encontrado"
    pattern_text = m.group(1)
    has_pequeno = 'peque' in pattern_text
    has_achica = 'ach[ií]cate' in pattern_text
    separado = not has_pequeno and not has_achica
    return separado, f"separado={separado} (pequeno={has_pequeno}, achica={has_achica})"

check("FP20-12", "_RE_MOVIMIENTO separado de Tzimtzum (sin 'hazte pequeño')", _check_re_mov_separado)

# --- Gevurá visual: on_bloqueo_seguridad emitido en Siruv Tzadik ---
def _check_gevura_emit():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'nlu.py'),
               encoding='utf-8').read()
    # Buscar la emisión del callback en la zona de Siruv Tzadik
    # Buscar la ÚLTIMA aparición de סירוב צדיק (la de código, no la de comentario)
    idx_siruv = src.rfind('סירוב צדיק')
    if idx_siruv < 0:
        return False, "No se encontró sección Siruv Tzadik"
    zona = src[idx_siruv:idx_siruv+800]
    has_emit = 'self.on_bloqueo_seguridad(cat_rechazo)' in zona
    return has_emit, f"emit en Siruv={has_emit}"

check("FP20-13", "on_bloqueo_seguridad emitido en Siruv Tzadik", _check_gevura_emit)

# --- Estado visual gevura_activa en _animar() ---
def _check_gevura_visual():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'ventana_principal.py'),
               encoding='utf-8').read()
    has_state = 'gevura_activa' in src
    has_brillo = 'self._fase * 5.0' in src  # frecuencia rápida
    return has_state and has_brillo, f"estado={has_state}, brillo_rapido={has_brillo}"

check("FP20-14", "Estado visual gevura_activa en _animar()", _check_gevura_visual)

# --- _al_bloqueo_seguridad slot existe en OrbeComputadora ---
def _check_slot_bloqueo():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'ventana_principal.py'),
               encoding='utf-8').read()
    has_slot = 'def _al_bloqueo_seguridad' in src
    has_timer = 'QTimer.singleShot(2000' in src
    return has_slot and has_timer, f"slot={has_slot}, timer_2s={has_timer}"

check("FP20-15", "_al_bloqueo_seguridad slot con QTimer 2s restore", _check_slot_bloqueo)

# --- _al_tzimtzum_solicitado slot existe ---
def _check_slot_tzimtzum():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'ventana_principal.py'),
               encoding='utf-8').read()
    has_slot = 'def _al_tzimtzum_solicitado' in src
    return has_slot, f"slot={has_slot}"

check("FP20-16", "_al_tzimtzum_solicitado slot existe", _check_slot_tzimtzum)

# ═══════════════════════════════════════════════
# FASE HF-036: Auto-compactar 1 min
# ═══════════════════════════════════════════════
print("\n== HF-036: Auto-compactar 1 min ==")

# --- TICKS_ANTES_COMPACTAR constante ---
def _check_ticks_compactar():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    val = VidaAutonoma.TICKS_ANTES_COMPACTAR
    return val == 120, f"TICKS_ANTES_COMPACTAR={val} (esperado 120)"

check("HF36-01", "TICKS_ANTES_COMPACTAR = 120", _check_ticks_compactar)

# --- DECISIÓN 2b en _tick() ---
def _check_decision_2b():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'vida_autonoma.py'),
               encoding='utf-8').read()
    has_decision = 'DECISIÓN 2b' in src
    has_compactar = 'TICKS_ANTES_COMPACTAR' in src
    has_log = 'Auto-compactado' in src
    return has_decision and has_compactar and has_log, f"decision2b={has_decision}, const={has_compactar}, log={has_log}"

check("HF36-02", "DECISIÓN 2b auto-compactación en _tick()", _check_decision_2b)

# --- _TICKS_UMBRAL_IDLE_TZIMTZUM constante (>5 min) ---
def _check_idle_tzimtzum():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    # Acceder via instancia mock no es posible, leer del source
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'vida_autonoma.py'),
               encoding='utf-8').read()
    m = re.search(r'_TICKS_UMBRAL_IDLE_TZIMTZUM\s*=\s*(\d+)', src)
    if not m:
        return False, "constante no encontrada"
    val = int(m.group(1))
    return val == 600, f"_TICKS_UMBRAL_IDLE_TZIMTZUM={val} (esperado 600)"

check("HF36-03", "_TICKS_UMBRAL_IDLE_TZIMTZUM = 600 (5 min)", _check_idle_tzimtzum)

# --- DECISIÓN 0.5 idle Tzimtzum en _tick() ---
def _check_idle_decision():
    src = open(os.path.join(os.path.dirname(__file__), '..', 'golem', 'interfaz', 'vida_autonoma.py'),
               encoding='utf-8').read()
    has_decision = 'DECISIÓN 0.5' in src
    has_idle_check = '_TICKS_UMBRAL_IDLE_TZIMTZUM' in src
    has_inactividad = 'inactividad >5 min' in src
    return has_decision and has_idle_check and has_inactividad, \
        f"decision0.5={has_decision}, const={has_idle_check}, msg={has_inactividad}"

check("HF36-04", "DECISIÓN 0.5 idle Tzimtzum en _tick()", _check_idle_decision)

# ═══════════════════════════════════════════════
# FASE BAT: iniciar_golem.bat
# ═══════════════════════════════════════════════
print("\n== BAT: iniciar_golem.bat ==")

def _check_bat():
    bat_path = os.path.join(os.path.dirname(__file__), '..', 'iniciar_golem.bat')
    if not os.path.exists(bat_path):
        return False, "iniciar_golem.bat no existe"
    content = open(bat_path, encoding='utf-8').read()
    checks = {
        'python_check': 'where python' in content,
        'venv_check': '.venv\\Scripts\\python.exe' in content,
        'pip_install': 'pip.exe install' in content or 'pip install' in content,
        'requirements': 'requirements.txt' in content,
        'ollama_check': 'where ollama' in content,
        'env_check': '.env' in content,
    }
    all_ok = all(checks.values())
    return all_ok, f"{checks}"

check("BAT-01", "iniciar_golem.bat tiene todas las verificaciones", _check_bat)

# ═══════════════════════════════════════════════
# FASE WORKFLOW: Regla #16
# ═══════════════════════════════════════════════
print("\n== WORKFLOW: Regla #16 ==")

def _check_rule16():
    wf_path = os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md')
    content = open(wf_path, encoding='utf-8').read()
    has_rule = '| **16** |' in content
    has_inmutable = '§4.17.1 es inmutable' in content or '4.17.1 es inmutable' in content
    return has_rule and has_inmutable, f"rule16={has_rule}, inmutable={has_inmutable}"

check("WF-01", "Regla #16 en DEVELOPMENT_WORKFLOW.md", _check_rule16)

# ═══════════════════════════════════════════════
# COHERENCIA: tests existentes no rotos
# ═══════════════════════════════════════════════
print("\n== COHERENCIA: imports cruzados ==")

def _check_imports_cruzados():
    """Verifica que los 4 archivos modificados importan sin error."""
    errores = []
    mods = [
        'golem.interfaz.ventana_principal',
        'golem.cerebro.nlu',
        'golem.nucleo.orquestador',
        'golem.interfaz.vida_autonoma',
    ]
    for m in mods:
        try:
            __import__(m)
        except Exception as e:
            errores.append(f"{m}: {e}")
    if errores:
        return False, f"Errores: {errores}"
    return True, f"4/4 módulos importan OK"

check("COH-01", "4 módulos modificados importan sin error", _check_imports_cruzados)

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
failed = total - passed
print(f"\n{'='*60}")
print(f"FP-020 + HF-036 RESULTADO: {passed} PASS / {failed} FAIL / {total} TOTAL")
if failed:
    print("FALLOS:")
    for id, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id}: {desc} -- {det}")
print(f"{'='*60}")

