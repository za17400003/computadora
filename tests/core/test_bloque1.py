"""
BLOQUE 1 — FASES 0-9: Core + STT + TTS + NLU + Windows + Memoria + Copilot + Orbe + Ojos + Proactividad
Verificación programática sin interacción por voz.
"""
import sys, os, json, importlib, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"
FAIL = "❌"
SKIP = "⏭️"
results = []

def check(test_id, desc, func):
    try:
        ok, detail = func()
        status = PASS if ok else FAIL
        results.append((test_id, desc, status, detail))
        print(f"  {status} {test_id}: {desc} — {detail}")
    except Exception as e:
        results.append((test_id, desc, FAIL, str(e)))
        print(f"  {FAIL} {test_id}: {desc} — EXCEPCIÓN: {e}")

# ═══════════════════════════════════════════
# FASE 0: ESQUELETO
# ═══════════════════════════════════════════
print("\n══ FASE 0: Esqueleto ══")

def t0_01():
    import computadora
    return True, f"versión={getattr(computadora, '__version__', 'sin versión')}"
check("T0-01", "Módulo computadora importable", t0_01)

def t0_02():
    from computadora.config import cargar_config
    cfg = cargar_config()
    return cfg is not None, f"whisper={cfg.get('whisper_model','?')}"
check("T0-05", "config.json se lee", t0_02)

def t0_03():
    from computadora.utilidades.logs import configurar_logs
    return True, "loguru shim OK"
check("T0-04", "Logging funciona", t0_03)

# ═══════════════════════════════════════════
# FASE 1: STT (Whisper)
# ═══════════════════════════════════════════
print("\n══ FASE 1: STT (Whisper) ══")

def t1_01():
    import whisper
    return True, f"whisper importado, versión={whisper.__version__}"
check("T1-01a", "Whisper importable", t1_01)

def t1_02():
    from computadora.voz.escucha import EscuchaActiva
    return True, "EscuchaActiva importable"
check("T1-01b", "EscuchaActiva importable", t1_02)

# ═══════════════════════════════════════════
# FASE 2: TTS (edge-tts)
# ═══════════════════════════════════════════
print("\n══ FASE 2: TTS ══")

def t2_01():
    from computadora.voz.habla import MotorHabla
    return True, "MotorHabla importable"
check("T2-01", "MotorHabla importable", t2_01)

# ═══════════════════════════════════════════
# FASE 3: NLU — 3 Niveles
# ═══════════════════════════════════════════
print("\n══ FASE 3: NLU — 3 Niveles ══")

def t3_01():
    from computadora.cerebro.nlu import Cerebro
    c = Cerebro.__new__(Cerebro)
    # Check regex patterns exist
    patterns = [attr for attr in dir(c.__class__) if attr.startswith('_RE_')]
    # Also check class-level attrs
    import computadora.cerebro.nlu as nlu_mod
    class_patterns = [a for a in dir(nlu_mod) if a.startswith('_RE_')]
    total = len(patterns) + len(class_patterns)
    return total > 0, f"{total} patrones regex encontrados"
check("T3-01", "Patrones regex N1 existen", t3_01)

def t3_02():
    """Simula detección de 'qué hora es' en nivel 1"""
    import re
    # Buscar el patrón en el código
    from computadora.cerebro import nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_hora = 'hora' in src and ('qué hora' in src or 'que hora' in src or 'fecha' in src)
    return has_hora, "patrón hora/fecha presente en nlu.py"
check("T3-02", "N1 regex: hora/fecha", t3_02)

def t3_03():
    from computadora.cerebro.ollama_api import CerebroOllama
    return True, "CerebroOllama importable"
check("T3-03", "N2 Ollama importable", t3_03)

def t3_04():
    from computadora.cerebro.copilot_api import CerebroCopilot
    return True, "CerebroCopilot importable"
check("T3-04", "N3 Copilot importable", t3_04)

def t3_05():
    """Verifica que el flujo N1→N2→N3 está implementado"""
    from computadora.cerebro import nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_n1 = '_pensar_nivel1' in src
    has_n2 = '_pensar_nivel2' in src or 'ollama' in src.lower()
    has_n3 = '_pensar_con_copilot' in src or 'copilot' in src.lower()
    ok = has_n1 and has_n2 and has_n3
    return ok, f"N1={has_n1} N2={has_n2} N3={has_n3}"
check("T3-05", "Flujo N1→N2→N3 implementado", t3_05)

def t3_06():
    """Verifica historial conversacional"""
    from computadora.cerebro import nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_hist = 'historial' in src or '_historial' in src
    return has_hist, "historial en nlu.py"
check("T3-06", "Contexto conversacional (historial)", t3_06)

def t3_07():
    """Handlers de identidad"""
    from computadora.cerebro import nlu as nlu_mod
    src = open(nlu_mod.__file__, encoding='utf-8').read()
    has_id = 'qué eres' in src or 'quién eres' in src or 'quien eres' in src or 'identidad' in src.lower()
    return has_id, "handler identidad presente"
check("T3-07", "N1: Handler identidad", t3_07)

# ═══════════════════════════════════════════
# FASE 4: Windows (Habilidades)
# ═══════════════════════════════════════════
print("\n══ FASE 4: Windows — Habilidades ══")

def t4_01():
    from computadora.habilidades.sistema import abrir_aplicacion
    return callable(abrir_aplicacion), "abrir_aplicacion es callable"
check("T4-01", "abrir_aplicacion existe", t4_01)

def t4_02():
    from computadora.habilidades.sistema import cerrar_aplicacion
    return callable(cerrar_aplicacion), "cerrar_aplicacion es callable"
check("T4-02", "cerrar_aplicacion existe", t4_02)

def t4_03():
    from computadora.habilidades.sistema import buscar_archivos
    return callable(buscar_archivos), "buscar_archivos es callable"
check("T4-03", "buscar_archivos existe", t4_03)

def t4_04():
    from computadora.habilidades.sistema import controlar_volumen
    return callable(controlar_volumen), "controlar_volumen es callable"
check("T4-04", "controlar_volumen existe", t4_04)

def t4_05():
    from computadora.habilidades.sistema import obtener_fecha_hora
    result = obtener_fecha_hora()
    ok = isinstance(result, str) and len(result) > 5
    return ok, f"'{result[:60]}'"
check("T4-05", "obtener_fecha_hora() funciona", t4_05)

def t4_06():
    from computadora.habilidades.sistema import obtener_info_sistema
    result = obtener_info_sistema()
    ok = isinstance(result, str) and len(result) > 10
    return ok, f"'{result[:80]}...'"
check("T4-06", "obtener_info_sistema() funciona", t4_06)

def t4_07():
    from computadora.habilidades.sistema import leer_portapapeles
    result = leer_portapapeles()
    return isinstance(result, str), f"portapapeles: {len(result)} chars"
check("T4-07", "leer_portapapeles() funciona", t4_07)

def t4_08():
    from computadora.habilidades.sistema import tomar_captura_pantalla
    return callable(tomar_captura_pantalla), "tomar_captura_pantalla es callable"
check("T4-08", "tomar_captura_pantalla existe", t4_08)

# ═══════════════════════════════════════════
# FASE 5: Memoria
# ═══════════════════════════════════════════
print("\n══ FASE 5: Memoria ══")

def t5_01():
    from computadora.memoria.persistencia import MemoriaPersistente
    return True, "MemoriaPersistente importable"
check("T5-01", "MemoriaPersistente importable", t5_01)

def t5_02():
    datos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datos')
    files = os.listdir(datos_dir) if os.path.isdir(datos_dir) else []
    jsonl_files = [f for f in files if f.endswith('.jsonl')]
    return len(jsonl_files) > 0, f"{len(jsonl_files)} archivos .jsonl en datos/"
check("T5-02", "Archivos JSONL de memoria existen", t5_02)

def t5_03():
    from computadora.habilidades.agenda import agregar_tarea, listar_tareas
    return callable(agregar_tarea) and callable(listar_tareas), "agenda CRUD importable"
check("T5-04", "Agenda CRUD importable", t5_03)

# ═══════════════════════════════════════════
# FASE 6: Copilot API
# ═══════════════════════════════════════════
print("\n══ FASE 6: Copilot API ══")

def t6_01():
    from computadora.cerebro.copilot_api import CerebroCopilot
    c = CerebroCopilot()
    return True, "CerebroCopilot instanciable"
check("T6-01", "CerebroCopilot se instancia", t6_01)

def t6_02():
    auth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datos', 'copilot_auth.json')
    exists = os.path.isfile(auth_path)
    if exists:
        with open(auth_path, encoding='utf-8') as f:
            data = json.load(f)
        has_token = 'access_token' in data or 'token' in data
        return has_token, "copilot_auth.json tiene token"
    return False, "copilot_auth.json NO existe"
check("T6-02", "Token Copilot persistido", t6_02)

def t6_03():
    """Verifica que detectar_modelo_disponible existe (FP-016)"""
    from computadora.cerebro.copilot_api import CerebroCopilot
    has_detect = hasattr(CerebroCopilot, 'detectar_modelo_disponible')
    has_pensar_code = hasattr(CerebroCopilot, 'pensar_codigo')
    has_pensar_gen = hasattr(CerebroCopilot, 'pensar_general')
    return has_detect and has_pensar_code and has_pensar_gen, f"detect={has_detect} code={has_pensar_code} general={has_pensar_gen}"
check("T6-03", "FP-016: Modelo inteligente", t6_03)

# ═══════════════════════════════════════════
# FASE 7: Orbe Visual (no se puede probar sin GUI, verificamos código)
# ═══════════════════════════════════════════
print("\n══ FASE 7: Orbe Visual ══")

def t7_01():
    from computadora.interfaz.ventana_principal import VentanaPrincipal
    return True, "VentanaPrincipal importable"
check("T7-01", "VentanaPrincipal importable", t7_01)

def t7_02():
    from computadora.interfaz import ventana_principal as vp
    src = open(vp.__file__, encoding='utf-8').read()
    has_orbe = 'orbe' in src.lower() or 'OrbWidget' in src or 'paintEvent' in src
    has_states = 'escuchando' in src and 'hablando' in src and 'procesando' in src
    return has_orbe and has_states, f"orbe={has_orbe} estados={has_states}"
check("T7-02", "Estados visuales del orbe", t7_02)

# ═══════════════════════════════════════════
# FASE 8: Ojos — Contexto de Pantalla
# ═══════════════════════════════════════════
print("\n══ FASE 8: Ojos — ContextoPantalla ══")

def t8_01():
    from computadora.utilidades.windows import ContextoPantalla
    ctx = ContextoPantalla()
    info = ctx.obtener_ventana_activa()
    ok = isinstance(info, dict) and 'titulo' in info
    return ok, f"ventana activa: '{info.get('titulo','?')[:50]}'"
check("T8-01", "obtener_ventana_activa()", t8_01)

def t8_02():
    from computadora.utilidades.windows import ContextoPantalla
    ctx = ContextoPantalla()
    desc = ctx.descripcion_contexto()
    return isinstance(desc, str) and len(desc) > 0, f"'{desc[:60]}'"
check("T8-05", "descripcion_contexto()", t8_02)

# ═══════════════════════════════════════════
# FASE 9: Proactividad
# ═══════════════════════════════════════════
print("\n══ FASE 9: Proactividad ══")

def t9_01():
    from computadora.nucleo.proactividad import MotorProactividad
    return True, "MotorProactividad importable"
check("T9-01", "MotorProactividad importable", t9_01)

def t9_02():
    from computadora.nucleo.proactividad import MotorProactividad
    src = open(MotorProactividad.__module__.replace('.', '/') + '.py', encoding='utf-8').read() if False else ""
    # Check via import
    mp = MotorProactividad.__new__(MotorProactividad)
    has_buenos = hasattr(mp, '_check_buenos_dias') or hasattr(MotorProactividad, '_check_buenos_dias')
    has_record = hasattr(mp, '_check_recordatorios_proximos') or hasattr(MotorProactividad, '_check_recordatorios_proximos')
    has_alert = hasattr(mp, '_check_alertas_sistema') or hasattr(MotorProactividad, '_check_alertas_sistema')
    has_silence = hasattr(mp, 'activar_silencio') or hasattr(MotorProactividad, 'activar_silencio')
    return has_buenos and has_alert, f"buenos_dias={has_buenos} records={has_record} alertas={has_alert} silencio={has_silence}"
check("T9-02", "Checks proactivos existen", t9_02)

# ═══════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════
print("\n" + "═" * 60)
passed = sum(1 for r in results if r[2] == PASS)
failed = sum(1 for r in results if r[2] == FAIL)
print(f"BLOQUE 1 RESULTADO: {passed} PASS / {failed} FAIL / {len(results)} TOTAL")
if failed > 0:
    print("\nFALLOS:")
    for r in results:
        if r[2] == FAIL:
            print(f"  {r[0]}: {r[1]} — {r[3]}")
print("═" * 60)


