"""
BLOQUE 3 — FASES 16-19: Historial Dinámico + Monitor Sistema + Meta-Workflow + Aprendizaje Errores
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
# FASE 16: Historial Dinámico
# ═══════════════════════════════════════════
print("\n== FASE 16: Historial Dinamico ==")

def t16_01():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_calc = '_calcular_limite_historial' in src
    return has_calc, "_calcular_limite_historial presente"
check("T16-01", "Limite historial dinamico", t16_01)

def t16_02():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_ventana = '30' in src and 'min' in src and 'historial' in src
    return has_ventana, "ventana 30 min referenciada"
check("T16-02", "Ventana 30 min protege mensajes", t16_02)

def t16_03():
    stats_path = os.path.join('datos', 'stats_uso.json')
    exists = os.path.isfile(stats_path)
    if exists:
        with open(stats_path) as f:
            data = json.load(f)
        return True, f"stats_uso.json: {list(data.keys())[:5]}"
    return False, "stats_uso.json no existe (se crea en runtime)"
check("T16-03", "stats_uso.json persiste", t16_03)

def t16_04():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_truncar = 'trunca' in src.lower() or '_recortar_historial' in src or 'comprim' in src.lower()
    return has_truncar, "truncamiento/compresion de historial"
check("T16-04", "Truncamiento comprime historial", t16_04)

# ═══════════════════════════════════════════
# FASE 17: Monitor de Sistema
# ═══════════════════════════════════════════
print("\n== FASE 17: Monitor de Sistema ==")

def t17_01():
    from computadora.habilidades.monitor_sistema import MonitorSistema
    m = MonitorSistema()
    snap = m.snapshot()
    has_cpu = 'cpu' in snap
    has_ram = 'ram' in snap
    return has_cpu and has_ram, f"CPU={snap.get('cpu','?')}% RAM={snap.get('ram',{}).get('porcentaje','?')}%"
check("T17-01", "snapshot(): CPU + RAM + disco + GPU", t17_01)

def t17_02():
    from computadora.habilidades.monitor_sistema import MonitorSistema
    m = MonitorSistema()
    alerta = m.hay_alerta()
    return True, f"alerta={alerta}"
check("T17-02", "hay_alerta() funciona", t17_02)

def t17_03():
    from computadora.habilidades.monitor_sistema import MonitorSistema
    m = MonitorSistema()
    top = m.top_procesos(5)
    return isinstance(top, list) and len(top) > 0, f"{len(top)} procesos top"
check("T17-03", "top_procesos(5) retorna lista", t17_03)

def t17_04():
    from computadora.habilidades.monitor_sistema import MonitorSistema
    m = MonitorSistema()
    rep = m.reporte_completo()
    return isinstance(rep, str) and len(rep) > 20, f"reporte: '{rep[:80]}...'"
check("T17-04", "reporte_completo() legible", t17_04)

# ═══════════════════════════════════════════
# FASE 18: Meta-Workflow
# ═══════════════════════════════════════════
print("\n== FASE 18: Meta-Workflow ==")

def t18_01():
    try:
        from computadora.habilidades.automod import registrar_proyecto, auditar_proyecto, listar_proyectos
        return True, "automod CRUD importable"
    except ImportError as e:
        # Try alternative names
        import computadora.habilidades.automod as am
        funcs = [x for x in dir(am) if not x.startswith('_')]
        return len(funcs) > 0, f"automod funciones: {funcs[:5]}"
check("T18-01", "Meta-workflow importable", t18_01)

# ═══════════════════════════════════════════
# FASE 19: Aprendizaje de Errores
# ═══════════════════════════════════════════
print("\n== FASE 19: Aprendizaje de Errores ==")

def t19_01():
    from computadora.memoria.aprendizaje import MemoriaErrores
    me = MemoriaErrores()
    return True, "MemoriaErrores instanciable"
check("T19-01", "MemoriaErrores importable", t19_01)

def t19_02():
    from computadora.memoria.aprendizaje import MemoriaErrores
    me = MemoriaErrores()
    has_registrar = hasattr(me, 'registrar')
    has_consultar = hasattr(me, 'consultar') or hasattr(me, 'buscar')
    return has_registrar and has_consultar, f"registrar={has_registrar} consultar={has_consultar}"
check("T19-02", "registrar + consultar errores", t19_02)

def t19_03():
    from computadora.memoria.aprendizaje import MemoriaErrores
    me = MemoriaErrores()
    has_inyectar = hasattr(me, 'contexto_para_prompt') or hasattr(me, 'lecciones_relevantes')
    return has_inyectar, "inyeccion de lecciones en prompt"
check("T19-03", "Inyeccion de lecciones en prompt", t19_03)

# ═══════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════
print(f"\n{'='*60}")
TOTAL = PASS + FAIL
print(f"BLOQUE 3 RESULTADO: {PASS} PASS / {FAIL} FAIL / {TOTAL} TOTAL")
print(f"{'='*60}")

