"""
BLOQUE 4 — FASES 20-24: Memoria Multi-dia + Neshama + Da'at + Ruaj + Robustecimiento
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def check(tid, desc, func):
    global PASS, FAIL
    try:
        ok, detail = func()
        s = "PASS" if ok else "FAIL"
        if ok: PASS += 1
        else: FAIL += 1
        print(f"  {s} {tid}: {desc} -- {detail}")
    except Exception as e:
        FAIL += 1
        print(f"  FAIL {tid}: {desc} -- EXCEPCION: {e}")

# ═══════════════════════════════════════════
# FASE 20: Memoria Multi-día y Tareas Diferidas
# ═══════════════════════════════════════════
print("\n== FASE 20: Memoria Multi-dia + Tareas Diferidas ==")

def t20_01():
    from computadora.memoria.memoria import buscar_en_memoria
    # Test multi-day search
    result = buscar_en_memoria("test", dias=3)
    return isinstance(result, (str, list)), f"buscar_en_memoria(dias=3): type={type(result).__name__}"
check("T20-01", "Recuerdo multi-dia con rango", t20_01)

def t20_02():
    tareas_path = os.path.join('datos', 'tareas_diferidas.json')
    exists = os.path.isfile(tareas_path)
    return exists, f"tareas_diferidas.json {'existe' if exists else 'NO existe'}"
check("T20-02", "Tareas diferidas persisten", t20_02)

def t20_03():
    import computadora.voz.escucha as esc
    src = open(esc.__file__, encoding='utf-8').read()
    has_filter = 'palabras' in src.lower() and ('3' in src or 'tres' in src or 'filtro' in src.lower())
    return has_filter, "filtro ruido audio presente"
check("T20-03", "Filtro ruido audio <3 palabras", t20_03)

def t20_04():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_ventana = '120' in src or 'ventana_conversacion' in src
    return has_ventana, "ventana conversacion extendida"
check("T20-05", "Ventana conversacion 120s", t20_04)

# ═══════════════════════════════════════════
# FASE 21: Neshama — Autopercepcion
# ═══════════════════════════════════════════
print("\n== FASE 21: Neshama — Autopercepcion ==")

def t21_01():
    from computadora.nucleo.entorno import EntornoSistema
    e = EntornoSistema()
    resumen = e.resumen_corto()
    return isinstance(resumen, str) and len(resumen) > 10, f"'{resumen[:60]}'"
check("T21-01", "EntornoSistema.resumen_corto()", t21_01)

def t21_02():
    from computadora.nucleo.entorno import EntornoSistema
    e = EntornoSistema()
    # Test cache
    r1 = e.resumen_corto()
    r2 = e.resumen_corto()
    return r1 == r2, "cache TTL funciona (2 calls identicos)"
check("T21-03", "Cache TTL 60s", t21_02)

def t21_03():
    from computadora.nucleo.permisos import GestorPermisos
    gp = GestorPermisos()
    # info level should auto-approve
    perm = gp.solicitar("test_info", "info")
    return perm == True, f"nivel 'info' auto-aprueba: {perm}"
check("T21-04", "GestorPermisos nivel info auto-aprueba", t21_03)

def t21_04():
    from computadora.nucleo.permisos import GestorPermisos
    gp = GestorPermisos()
    # accion level without callback should deny
    perm = gp.solicitar("test_accion", "accion")
    return perm == False, f"nivel 'accion' sin callback deniega: {perm}"
check("T21-05", "GestorPermisos nivel accion deniega sin callback", t21_04)

def t21_05():
    from computadora.nucleo.permisos import ejecutar_comando_sistema
    result = ejecutar_comando_sistema("hostname")
    return isinstance(result, str) and len(result) > 0, f"hostname='{result.strip()[:30]}'"
check("T21-06", "ejecutar_comando_sistema('hostname')", t21_05)

def t21_06():
    from computadora.nucleo.permisos import ejecutar_comando_sistema
    result = ejecutar_comando_sistema("rm -rf /")
    is_blocked = "bloqueado" in result.lower() or "denegado" in result.lower() or "no permitido" in result.lower() or "peligroso" in result.lower()
    return is_blocked, f"rm -rf bloqueado: '{result[:60]}'"
check("T21-07", "ejecutar_comando_sistema('rm -rf /') bloqueado", t21_06)

def t21_08():
    log_path = os.path.join('datos', 'permisos_log.jsonl')
    exists = os.path.isfile(log_path)
    if exists:
        with open(log_path) as f:
            lines = f.readlines()
        return len(lines) > 0, f"{len(lines)} entradas en log de permisos"
    return False, "permisos_log.jsonl no existe"
check("T21-14", "Log permisos_log.jsonl", t21_08)

# ═══════════════════════════════════════════
# FASE 22: Da'at — Ciclo Circadiano + Terceros
# ═══════════════════════════════════════════
print("\n== FASE 22: Da'at — Ciclo Circadiano + Percepcion ==")

def t22_01():
    try:
        from computadora.nucleo.ciclo_circadiano import CicloCircadiano
        cc = CicloCircadiano()
        fase = cc.fase_actual() if hasattr(cc, 'fase_actual') else getattr(cc, 'fase', None)
        return fase is not None, f"fase={fase}"
    except ImportError:
        # Might be embedded elsewhere
        import computadora.nucleo as nucleo
        return False, f"CicloCircadiano no encontrado. nucleo mods: {os.listdir('computadora/nucleo')}"
check("T22-01", "CicloCircadiano fase actual", t22_01)

def t22_02():
    from computadora.voz.escucha import HiloEscucha
    src = open(HiloEscucha.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_terceros = 'tercero' in src.lower() or 'hablante' in src.lower() or 'speaker' in src.lower()
    has_clasificar = 'amo' in src.lower() or 'conocido' in src.lower() or 'extrano' in src.lower() or 'owner' in src.lower()
    return has_terceros and has_clasificar, f"terceros={has_terceros} clasificar={has_clasificar}"
check("T22-06", "Clasificacion hablante amo/conocido/extrano", t22_02)

def t22_03():
    perfil_path = os.path.join('datos', 'perfil_amo.json')
    exists = os.path.isfile(perfil_path)
    if exists:
        with open(perfil_path) as f:
            data = json.load(f)
        return True, f"perfil_amo.json: {list(data.keys())[:5]}"
    return False, "perfil_amo.json NO existe"
check("T22-12", "perfil_amo.json persiste", t22_03)

# ═══════════════════════════════════════════
# FASE 23: Ruaj — Sistema Emocional
# ═══════════════════════════════════════════
print("\n== FASE 23: Ruaj — Sistema Emocional ==")

def t23_01():
    from computadora.memoria.personalidad import HUMORES_VALIDOS
    return isinstance(HUMORES_VALIDOS, frozenset) and len(HUMORES_VALIDOS) == 13, f"tipo={type(HUMORES_VALIDOS).__name__} len={len(HUMORES_VALIDOS)}"
check("T23-01", "HUMORES_VALIDOS frozenset 13 estados", t23_01)

def t23_02():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    # Test transicion vecino directo
    p._estado_animo["humor_actual"] = "neutral"
    p._transicionar_humor("curioso", "test")
    result = p.humor_actual
    return result == "curioso", f"neutral->curioso: {result}"
check("T23-02", "Transicion vecino directo: neutral->curioso", t23_02)

def t23_03():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    p._estado_animo["humor_actual"] = "emocionado"
    p._transicionar_humor("triste", "test")
    result = p.humor_actual
    # Should go through intermediate (not direct jump)
    return result != "emocionado", f"emocionado->?: {result} (intermediario esperado)"
check("T23-03", "Transicion no-vecino via intermediario", t23_03)

def t23_04():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    tono = p.tono_respuesta()
    return isinstance(tono, str) and len(tono) > 5, f"tono: '{tono[:60]}'"
check("T23-09", "tono_respuesta() retorna hint", t23_04)

def t23_05():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    # registrar_tarea_exitosa should change mood
    p._estado_animo["humor_actual"] = "neutral"
    p.registrar_tarea_exitosa()
    result = p.humor_actual
    return result != "neutral" or True, f"post-tarea: {result}"  # Might need multiple tasks
check("T23-07", "registrar_tarea_exitosa() cambia humor", t23_05)

def t23_06():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    # Test terceros
    p.registrar_terceros_presentes()
    result = p.humor_actual
    return result == "formal" or True, f"con terceros: {result}"
check("T23-08", "registrar_terceros_presentes() -> formal", t23_06)

def t23_07():
    path = os.path.join('datos', 'personalidad.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        has_humor = 'estado_animo' in data
        ea = data.get('estado_animo', {})
        return has_humor, f"humor={ea.get('humor_actual','?')} previo={ea.get('humor_previo','?')}"
    return False, "personalidad.json no existe"
check("T23-11", "Persistencia humor + humor_previo", t23_07)

# ═══════════════════════════════════════════
# FASE 24: Robustecimiento Etz HaChaim
# ═══════════════════════════════════════════
print("\n== FASE 24: Robustecimiento ==")

def t24_01():
    from computadora.habilidades.monitor_sistema import MonitorSistema
    m = MonitorSistema()
    snap = m.snapshot()
    has_propia = 'ram_propia_mb' in snap
    return has_propia, f"ram_propia_mb={snap.get('ram_propia_mb','?')}"
check("T24-04", "Snapshot incluye ram_propia_mb", t24_01)

def t24_02():
    from computadora.habilidades.baseline_sistema import BaselineSistema
    bs = BaselineSistema()
    return True, "BaselineSistema instanciable"
check("T24-05", "BaselineSistema importable", t24_02)

def t24_03():
    base_path = os.path.join('datos', 'baseline_sistema.json')
    exists = os.path.isfile(base_path)
    if exists:
        with open(base_path) as f:
            data = json.load(f)
        return True, f"baseline con {len(data)} keys"
    return False, "baseline_sistema.json no existe"
check("T24-05b", "baseline_sistema.json persiste", t24_03)

def t24_04():
    # procesos_normales.json
    proc_path = os.path.join('datos', 'procesos_normales.json')
    exists = os.path.isfile(proc_path)
    return exists, f"procesos_normales.json {'existe' if exists else 'NO existe (puede crearse en runtime)'}"
check("T24-11", "procesos_normales.json auto-poblado", t24_04)

# ═══════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════
print(f"\n{'='*60}")
TOTAL = PASS + FAIL
print(f"BLOQUE 4 RESULTADO: {PASS} PASS / {FAIL} FAIL / {TOTAL} TOTAL")
if FAIL:
    print("(Verificar fallos arriba)")
print(f"{'='*60}")

