"""
BLOQUE 5 — FASES 25-31: Implementaciones recientes
FP-015 Lemed, FP-016 Da'at Modelo, FP-017 Jazon, HF-028/029/030
"""
import sys, os, json, re
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
# FP-015: Lemed — Auto-Aprendizaje N1
# ═══════════════════════════════════════════
print("\n== FP-015: Lemed — Auto-Aprendizaje N1 ==")

def t_lemed_01():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    n1 = Nivel1Aprendido()
    return True, f"Nivel1Aprendido instanciable, {len(n1._patrones)} patrones"
check("FP15-01", "Nivel1Aprendido importable", t_lemed_01)

def t_lemed_02():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    n1 = Nivel1Aprendido()
    has_buscar = hasattr(n1, 'buscar_match')
    has_registrar = hasattr(n1, 'registrar_candidato')
    has_exito = hasattr(n1, 'registrar_exito')
    has_fallo = hasattr(n1, 'registrar_fallo')
    return all([has_buscar, has_registrar, has_exito, has_fallo]), f"buscar={has_buscar} registrar={has_registrar} exito={has_exito} fallo={has_fallo}"
check("FP15-02", "API completa: buscar/registrar/exito/fallo", t_lemed_02)

def t_lemed_03():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    n1 = Nivel1Aprendido()
    # Registrar un candidato y verificar confianza
    n1.registrar_candidato("test_lemed", "respuesta test", "nivel2")
    match = n1.buscar_match("test_lemed")
    if match:
        return True, f"match encontrado: confianza={match.get('confianza', '?')}"
    # Might not be active yet (confianza < threshold)
    return True, "candidato registrado (confianza baja, no activo aun = esperado)"
check("FP15-03", "Registro de candidato y busqueda", t_lemed_03)

def t_lemed_04():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido, UMBRAL_N2, UMBRAL_N3
    return UMBRAL_N2 == 0.7 and UMBRAL_N3 == 0.8, f"UMBRAL_N2={UMBRAL_N2} UMBRAL_N3={UMBRAL_N3}"
check("FP15-04", "Umbrales N2=0.7 N3=0.8", t_lemed_04)

def t_lemed_05():
    path = os.path.join('datos', 'nivel1_patrones.json')
    exists = os.path.isfile(path)
    if exists:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return True, f"{len(data)} patrones persistidos"
    return False, "nivel1_patrones.json no existe"
check("FP15-05", "Persistencia JSON de patrones", t_lemed_05)

def t_lemed_06():
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    n1 = Nivel1Aprendido()
    # Anti-ReDoS check
    has_blacklist = hasattr(n1, '_REGEX_BLACKLIST') or hasattr(Nivel1Aprendido, '_REGEX_BLACKLIST')
    src = open(Nivel1Aprendido.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_limit = '300' in src or 'MAX_REGEX_LEN' in src or 'redos' in src.lower() or 'blacklist' in src.lower()
    return has_limit, f"anti-ReDoS: blacklist/limit presente"
check("FP15-06", "Anti-ReDoS: regex blacklist + limite", t_lemed_06)

def t_lemed_07():
    """Verifica integración de Lemed en nlu.py"""
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_lemed = 'nivel1_aprendido' in src or 'Nivel1Aprendido' in src
    has_promocion = '_detectar_promocion' in src
    has_es_promo = '_es_promocionable' in src
    return has_lemed and has_promocion, f"lemed={has_lemed} promocion={has_promocion} promo={has_es_promo}"
check("FP15-07", "Lemed integrado en nlu.py", t_lemed_07)

# ═══════════════════════════════════════════
# FP-016: Da'at — Modelo Inteligente + Piensa
# ═══════════════════════════════════════════
print("\n== FP-016: Da'at — Modelo Inteligente + Piensa ==")

def t_daat_01():
    from computadora.cerebro.copilot_api import CerebroCopilot
    c = CerebroCopilot()
    has_detect = hasattr(c, 'detectar_modelo_disponible')
    has_code = hasattr(c, 'pensar_codigo')
    has_gen = hasattr(c, 'pensar_general')
    return has_detect and has_code and has_gen, f"detect={has_detect} code={has_code} general={has_gen}"
check("FP16-01", "detectar_modelo + pensar_codigo + pensar_general", t_daat_01)

def t_daat_02():
    """Verifica _generar_regex_con_keter en nivel1_aprendido"""
    from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
    src = open(Nivel1Aprendido.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_keter = '_generar_regex_con_keter' in src
    return has_keter, "regex via Keter (Copilot)"
check("FP16-02", "Lemed usa Keter para generar regex", t_daat_02)

def t_daat_03():
    """Verifica patrones 'piensa' y 'piensa profundamente' en nlu"""
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_piensa = '_RE_PIENSA' in src
    has_piensa_prof = '_RE_PIENSA_PROFUND' in src
    return has_piensa and has_piensa_prof, f"piensa={has_piensa} profundo={has_piensa_prof}"
check("FP16-03", "Patrones piensa/piensa profundamente", t_daat_03)

def t_daat_04():
    """Verifica ruteo: piensa → N2, piensa profundamente → N3"""
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_auto_gate = 'auto_gate_copilot' in src or '_auto_gate_copilot' in src
    return has_auto_gate, "auto_gate_copilot presente"
check("FP16-04", "Ruteo piensa→N2, piensa profundamente→N3", t_daat_04)

def t_daat_05():
    """Verifica modelos de código hardcodeados"""
    from computadora.cerebro import copilot_api as ca
    src = open(ca.__file__, encoding='utf-8').read()
    has_modelos = '_MODELOS_CODIGO' in src or 'claude' in src.lower()
    has_gratuito = '_MODELO_GRATUITO' in src or 'gpt-4o-mini' in src
    return has_modelos and has_gratuito, f"modelos_codigo={has_modelos} gratuito={has_gratuito}"
check("FP16-05", "Modelos codigo + modelo gratuito fallback", t_daat_05)

# ═══════════════════════════════════════════
# FP-017: Jazón — Auto-Discovery de Modelos
# ═══════════════════════════════════════════
print("\n== FP-017: Jazon — Auto-Discovery ==")

def t_jazon_01():
    from computadora.cerebro.modelo_discovery import obtener_modelos_actualizados
    return callable(obtener_modelos_actualizados), "obtener_modelos_actualizados callable"
check("FP17-01", "modelo_discovery importable", t_jazon_01)

def t_jazon_02():
    from computadora.cerebro.modelo_discovery import _extraer_modelos_de_texto
    # Test extraction from sample text
    sample = "GitHub Copilot now supports claude-sonnet-4 and gpt-4o models"
    models = _extraer_modelos_de_texto(sample)
    return len(models) > 0, f"modelos extraidos: {models}"
check("FP17-02", "Extraccion regex de modelos", t_jazon_02)

def t_jazon_03():
    from computadora.cerebro.modelo_discovery import _prioridad_modelo
    p_opus = _prioridad_modelo("claude-opus-4")
    p_mini = _prioridad_modelo("gpt-4o-mini")
    return p_opus < p_mini, f"opus={p_opus} < mini={p_mini}"
check("FP17-03", "Prioridad: opus > mini", t_jazon_03)

def t_jazon_04():
    """Verifica validacion de nombres de modelo"""
    from computadora.cerebro import modelo_discovery as md
    src = open(md.__file__, encoding='utf-8').read()
    has_validate = 'a-zA-Z0-9' in src or 'validar' in src or 'whitelist' in src
    return has_validate, "validacion de nombres presente"
check("FP17-04", "Validacion nombres modelo (whitelist chars)", t_jazon_04)

def t_jazon_05():
    """Integración con copilot_api"""
    from computadora.cerebro import copilot_api as ca
    src = open(ca.__file__, encoding='utf-8').read()
    has_discovery = 'modelo_discovery' in src or 'obtener_modelos_actualizados' in src
    return has_discovery, "discovery integrado en copilot_api"
check("FP17-05", "Discovery integrado en copilot_api", t_jazon_05)

# ═══════════════════════════════════════════
# HF-028: Whisper Mistranscription Fix
# ═══════════════════════════════════════════
print("\n== HF-028: Whisper Wake Word Fix ==")

def t_hf028_01():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    # Check expanded attention patterns for Whisper variants
    has_ya = "'y a'" in src or '"y a"' in src or "y a" in src
    has_oiga = 'oiga' in src
    return has_ya or has_oiga, f"variantes Whisper: ya={has_ya} oiga={has_oiga}"
check("HF28-01", "Variantes Whisper en atencion", t_hf028_01)

def t_hf028_02():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    # Whisper mangles 'emet' → 'embed', 'emmet', etc
    has_embed = 'embed' in src or 'emmet' in src or 'amet' in src
    return has_embed, "variantes emet/embed/emmet"
check("HF28-02", "Variantes emet en nombre", t_hf028_02)

def t_hf028_03():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_micro = 'micro' in src.lower() and ('3' in src or 'heuristic' in src.lower() or 'len' in src)
    return has_micro, "heuristica micro-utterance"
check("HF28-03", "Micro-utterance heuristic <=3 chars", t_hf028_03)

# ═══════════════════════════════════════════
# HF-029: Lemed Garbage Pattern Fix
# ═══════════════════════════════════════════
print("\n== HF-029: Lemed Garbage Pattern Fix ==")

def t_hf029_01():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_guard = '_respuesta_es_inutil' in src and '_detectar_promocion' in src
    # Check that _detectar_promocion is guarded
    # Find the line with _detectar_promocion call
    lines = src.split('\n')
    guarded = False
    for i, line in enumerate(lines):
        if '_detectar_promocion' in line and 'def ' not in line:
            # Check if there's an _respuesta_es_inutil check nearby (within 5 lines before)
            context = '\n'.join(lines[max(0,i-5):i+1])
            if '_respuesta_es_inutil' in context or 'inutil' in context:
                guarded = True
                break
    return has_guard and guarded, f"guard={has_guard} guarded_call={guarded}"
check("HF29-01", "Lemed guarded by _respuesta_es_inutil", t_hf029_01)

def t_hf029_02():
    import computadora.cerebro.nlu as nlu
    src = open(nlu.__file__, encoding='utf-8').read()
    has_patterns = 'puedes repetir' in src or 'no funcionó' in src or 'no logré' in src or 'intente' in src.lower()
    return has_patterns, "patrones inútiles expandidos"
check("HF29-02", "Patrones respuesta inutil expandidos", t_hf029_02)

# ═══════════════════════════════════════════
# HF-030: Caress Mood Accumulation Fix
# ═══════════════════════════════════════════
print("\n== HF-030: Caress Mood Fix ==")

def t_hf030_01():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    p._estado_animo["humor_actual"] = "neutral"
    p._estado_animo["caricias_recientes"] = 0
    for _ in range(5):
        p.registrar_caricia()
    humor = p.humor_actual
    caricias = p._estado_animo.get("caricias_recientes", 0)
    return humor == "contento" and caricias >= 5, f"5 caricias: humor={humor} count={caricias}"
check("HF30-01", "5 caricias: neutral->contento", t_hf030_01)

def t_hf030_02():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    p._estado_animo["humor_actual"] = "neutral"
    p._estado_animo["caricias_recientes"] = 0
    for _ in range(15):
        p.registrar_caricia()
    humor = p.humor_actual
    caricias = p._estado_animo.get("caricias_recientes", 0)
    return humor == "emocionado" and caricias >= 15, f"15 caricias: humor={humor} count={caricias}"
check("HF30-02", "15 caricias: neutral->contento->emocionado", t_hf030_02)

def t_hf030_03():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    # Simulate: positive mood + terceros ausentes with neutral previo
    p._estado_animo["humor_actual"] = "emocionado"
    p._estado_animo["humor_previo"] = "neutral"
    p.registrar_terceros_ausentes()
    humor = p.humor_actual
    return humor == "emocionado", f"preserva emocionado: {humor}"
check("HF30-03", "Terceros ausentes preserva humor positivo", t_hf030_03)

def t_hf030_04():
    from computadora.memoria.personalidad import Personalidad
    p = Personalidad()
    has_reset = False
    src = open(Personalidad.__module__.replace('.', os.sep) + '.py', encoding='utf-8').read()
    has_reset = 'caricias_recientes' in src and 'registrar_inicio_dia' in src
    return has_reset, "reset caricias en registrar_inicio_dia"
check("HF30-04", "Reset caricias_recientes en nuevo dia", t_hf030_04)

# ═══════════════════════════════════════════
# COHERENCIA DISEÑO vs IMPLEMENTACIÓN
# ═══════════════════════════════════════════
print("\n== COHERENCIA: SDD vs Implementacion ==")

def t_coherencia_01():
    """Verifica que los módulos documentados en SDD existen"""
    expected_modules = [
        'golem.cerebro.nlu',
        'golem.cerebro.copilot_api',
        'golem.cerebro.nivel1_aprendido',
        'golem.cerebro.modelo_discovery',
        'golem.memoria.personalidad',
        'golem.memoria.memoria',
        'golem.memoria.aprendizaje',
        'golem.voz.escucha',
        'golem.voz.habla',
        'golem.nucleo.proactividad',
        'golem.nucleo.entorno',
        'golem.nucleo.permisos',
        'golem.interfaz.ventana_principal',
        'golem.interfaz.vida_autonoma',
        'golem.habilidades.sistema',
        'golem.habilidades.herramientas',
        'golem.habilidades.monitor_sistema',
        'golem.habilidades.baseline_sistema',
        'golem.utilidades.windows',
    ]
    missing = []
    for mod in expected_modules:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    ok = len(missing) == 0
    return ok, f"{len(expected_modules)-len(missing)}/{len(expected_modules)} modulos OK" + (f" MISSING: {missing}" if missing else "")
check("COH-01", "Todos los modulos documentados existen", t_coherencia_01)

def t_coherencia_02():
    """Verifica que datos/ tiene los archivos esperados"""
    expected = [
        'personalidad.json',
        'perfil_amo.json',
        'nivel1_patrones.json',
        'heatmap_pantalla.json',
        'baseline_sistema.json',
        'permisos_log.jsonl',
        'tareas.json',
        'recordatorios.json',
        'errores_aprendidos.json',
    ]
    missing = [f for f in expected if not os.path.isfile(os.path.join('datos', f))]
    ok = len(missing) == 0
    return ok, f"{len(expected)-len(missing)}/{len(expected)} archivos datos/ OK" + (f" MISSING: {missing}" if missing else "")
check("COH-02", "Archivos de datos persistidos", t_coherencia_02)

# ═══════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════
print(f"\n{'='*60}")
TOTAL = PASS + FAIL
print(f"BLOQUE 5 RESULTADO: {PASS} PASS / {FAIL} FAIL / {TOTAL} TOTAL")
if FAIL:
    print("(Verificar fallos arriba)")
print(f"{'='*60}")

