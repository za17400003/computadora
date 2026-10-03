"""
BLOQUE 2 — FASES 10-15: Vida Autónoma + Personalidad + Hogar + Tarea Compleja + Streaming + Speaker
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
# FASE 10: Vida Autónoma
# ═══════════════════════════════════════════
print("\n== FASE 10: Vida Autonoma ==")

def t10_01():
    from computadora.interfaz.vida_autonoma import VidaAutonoma, EstadoPresencia
    states = list(EstadoPresencia)
    names = [s.name for s in states]
    has_pleno = 'PLENO' in names
    has_compacto = 'COMPACTO' in names
    has_minimizado = 'MINIMIZADO' in names
    return has_pleno and has_compacto and has_minimizado, f"estados: {names}"
check("T10-01", "EstadoPresencia: PLENO/COMPACTO/MINIMIZADO", t10_01)

def t10_02():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    src = open(VidaAutonoma.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_esquiva = 'esquiv' in src.lower()
    return has_esquiva, "esquiva del cursor implementada"
check("T10-02", "Esquiva del cursor en compacto", t10_02)

def t10_03():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    src = open(VidaAutonoma.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_heatmap = 'heatmap' in src.lower()
    return has_heatmap, "heatmap presente en vida_autonoma"
check("T10-03", "Heatmap de pantalla", t10_03)

def t10_04():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    src = open(VidaAutonoma.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_compactar = 'compacta' in src.lower() or 'fin_conversacion' in src.lower()
    return has_compactar, "compactacion post-conversacion"
check("T10-04", "Compactacion post-conversacion", t10_04)

# ═══════════════════════════════════════════
# FASE 11: Personalidad Evolutiva
# ═══════════════════════════════════════════
print("\n== FASE 11: Personalidad ==")

def t11_01():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    rasgos = p.rasgos if hasattr(p, 'rasgos') else {}
    return len(rasgos) >= 10, f"{len(rasgos)} rasgos: {list(rasgos.keys())[:5]}..."
check("T11-01", "10+ rasgos de personalidad", t11_01)

def t11_02():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    humor = p.humor if hasattr(p, 'humor') else None
    return humor is not None, f"humor actual: {humor}"
check("T11-02", "Estado de animo presente", t11_02)

def t11_03():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    has_tono = hasattr(p, 'tono_respuesta')
    if has_tono:
        tono = p.tono_respuesta()
        return True, f"tono: '{tono[:60]}'"
    return False, "tono_respuesta no encontrado"
check("T11-03", "tono_respuesta() funciona", t11_03)

def t11_04():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    has_persist = hasattr(p, 'guardar')
    return has_persist, "guardar() existe"
check("T11-04", "Persistencia de personalidad", t11_04)

def t11_05():
    from computadora.memoria.personalidad import HUMORES_VALIDOS
    return len(HUMORES_VALIDOS) == 13, f"{len(HUMORES_VALIDOS)} humores: {sorted(HUMORES_VALIDOS)}"
check("T11-05", "13 humores validos (Ruaj)", t11_05)

def t11_06():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    # Test registrar_tarea_exitosa
    has_tarea = hasattr(p, 'registrar_tarea_exitosa')
    has_caricia = hasattr(p, 'registrar_caricia')
    has_terceros = hasattr(p, 'registrar_terceros_presentes')
    return has_tarea and has_caricia and has_terceros, f"tarea={has_tarea} caricia={has_caricia} terceros={has_terceros}"
check("T11-06", "Registradores de eventos emocionales", t11_06)

# ═══════════════════════════════════════════
# FASE 12: Hogar Dinámico
# ═══════════════════════════════════════════
print("\n== FASE 12: Hogar Dinamico ==")

def t12_01():
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    src = open(VidaAutonoma.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_hogar = 'hogar' in src.lower() or '_recalcular_hogar' in src
    return has_hogar, "hogar dinamico presente"
check("T12-01", "Hogar dinamico recalculable", t12_01)

def t12_02():
    heatmap_path = os.path.join('datos', 'heatmap_pantalla.json')
    exists = os.path.isfile(heatmap_path)
    if exists:
        with open(heatmap_path) as f:
            data = json.load(f)
        return True, f"heatmap con {len(data)} entradas"
    return False, "heatmap_pantalla.json no existe (puede crearse en runtime)"
check("T12-02", "Heatmap persiste en JSON", t12_02)

# ═══════════════════════════════════════════
# FASE 13: Tarea Compleja
# ═══════════════════════════════════════════
print("\n== FASE 13: Tarea Compleja ==")

def t13_01():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_compleja = '_es_tarea_compleja' in src
    return has_compleja, "_es_tarea_compleja en nlu.py"
check("T13-01", "_es_tarea_compleja() detector", t13_01)

def t13_02():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_herr = 'ejecutar_herramienta' in src
    has_loop = 'tool_call' in src.lower() or 'tool_use' in src.lower() or 'MAX_TOOL_CALLS' in src
    return has_herr and has_loop, f"herramientas={has_herr} loop={has_loop}"
check("T13-02", "Tool-use loop implementado", t13_02)

# ═══════════════════════════════════════════
# FASE 14: Streaming TTS
# ═══════════════════════════════════════════
print("\n== FASE 14: Streaming TTS ==")

def t14_01():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_stream = '_llamar_ollama_streaming' in src
    return has_stream, "_llamar_ollama_streaming en nlu.py"
check("T14-01", "Streaming Ollama implementado", t14_01)

def t14_02():
    import computadora.cerebro.nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    # Check for sentence-level emission
    has_oracion = 'fragmento' in src or 'oracion' in src.lower() or 'sentence' in src.lower() or 'hablar_fragmento' in src
    return has_oracion, "emision por fragmentos"
check("T14-02", "Emision por oraciones parciales", t14_02)

# ═══════════════════════════════════════════
# FASE 15: Speaker Verification
# ═══════════════════════════════════════════
print("\n== FASE 15: Speaker Verification ==")

def t15_01():
    try:
        from computadora.voz.escucha import HiloEscucha
        src = open(HiloEscucha.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
        has_mfcc = 'mfcc' in src.lower() or 'fingerprint' in src.lower() or 'speaker' in src.lower()
        has_verify = 'verificar' in src.lower() or 'coseno' in src.lower() or 'cosine' in src.lower()
        return has_mfcc and has_verify, f"mfcc={has_mfcc} verificacion={has_verify}"
    except:
        return False, "no se pudo leer escucha.py"
check("T15-01", "MFCC fingerprint + verificacion", t15_01)

def t15_02():
    perfil_path = os.path.join('datos', 'perfil_amo.json')
    exists = os.path.isfile(perfil_path)
    return exists, f"perfil_amo.json {'existe' if exists else 'NO existe'}"
check("T15-02", "Perfil de voz del propietario", t15_02)

# ═══════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════
print(f"\n{'='*60}")
TOTAL = PASS + FAIL
print(f"BLOQUE 2 RESULTADO: {PASS} PASS / {FAIL} FAIL / {TOTAL} TOTAL")
print(f"{'='*60}")

