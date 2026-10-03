"""
Tikún 019 — FP-056: Tikún HaMaljút
RF-151: Blend dual humor tint (70/30)
RF-152: Circadian brightness modulation
RF-153: Particle density by personalidad.energia
RF-154: Demo Maljut overhaul (all 13 states, humores, tacto, narración)
RF-155: Regex 'abrem' in _RE_ABRIR_APP
RF-156: Code detection guard in _tool_texto_plano
"""
import sys, os, re, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── RF-155: Regex 'abrem' en _RE_ABRIR_APP ───

class TestRF155_AbremRegex:

    def test_abrem_match_abrir_app(self):
        from computadora.cerebro.nlu import _RE_ABRIR_APP
        m = _RE_ABRIR_APP.search("abrem mi explorador")
        assert m is not None, "'abrem mi explorador' no matchea _RE_ABRIR_APP"

    def test_abrem_match_carpeta(self):
        from computadora.cerebro.nlu import _RE_CARPETA_PERSONAL
        m = _RE_CARPETA_PERSONAL.search("abrem mis documentos")
        assert m is not None, "'abrem mis documentos' no matchea _RE_CARPETA_PERSONAL"

    def test_abre_sigue_funcionando(self):
        from computadora.cerebro.nlu import _RE_ABRIR_APP
        m = _RE_ABRIR_APP.search("abre el navegador")
        assert m is not None, "'abre el navegador' dejó de funcionar"

    def test_abrir_sigue_funcionando(self):
        from computadora.cerebro.nlu import _RE_CARPETA_PERSONAL
        m = _RE_CARPETA_PERSONAL.search("abrir mis descargas")
        assert m is not None, "'abrir mis descargas' dejó de funcionar"


# ─── RF-156: Code detection guard en _tool_texto_plano ───

class TestRF156_CodeGuard:

    def test_code_guard_present_in_source(self):
        from computadora.cerebro.nlu import CerebroComputadora
        src = inspect.getsource(CerebroComputadora)
        assert "_parece_codigo" in src, "Guard de código no encontrado"

    def test_guard_keywords(self):
        from computadora.cerebro.nlu import CerebroComputadora
        src = inspect.getsource(CerebroComputadora)
        for kw in ("import ", "def ", "class "):
            assert f"'{kw}'" in src or f'"{kw}"' in src, f"Keyword '{kw}' falta en guard"


# ─── RF-151: Blend dual humor tint ───

class TestRF151_DualHumorBlend:

    def test_paintEvent_has_humor_secundario(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.paintEvent)
        assert "humor_secundario" in src, "paintEvent no lee humor_secundario (RF-151)"

    def test_dmut_blend_weight_capped(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.paintEvent)
        assert "min(0.3" in src, "Tope 30% de blend no presente"


# ─── RF-152: Circadian brightness modulation ───

class TestRF152_CircadianBrightness:

    def test_fase_circadiana_attr_exists(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.__init__)
        assert "_fase_circadiana" in src, "_fase_circadiana no inicializado en __init__"

    def test_fase_stored_on_change(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._al_cambio_fase_circadiana)
        assert "_fase_circadiana" in src, "_al_cambio_fase_circadiana no almacena _fase_circadiana"

    def test_tick_uses_circadian(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "fase_circadiana" in src, "_animar no modula brillo por fase circadiana"


# ─── RF-153: Particle density by energia ───

class TestRF153_ParticleDensityEnergia:

    def test_tick_uses_energia(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "energia" in src, "_animar no usa rasgo energia para partículas (RF-153)"


# ─── RF-154: Demo Maljut overhaul ───

class TestRF154_DemoMaljut:

    def test_demo_has_all_13_states(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        for estado in ["dormido", "descanso_guardian", "despertando", "vigilia",
                       "escuchando", "procesando", "hablando",
                       "error", "cortesia", "alerta_extrano"]:
            assert estado in src, f"Estado '{estado}' falta en demo"
        # Fase 2: "trabajando" y "gevura_activa" ya no se asignan a mano — se
        # disparan vía los manejadores reales de producción que los producen
        # ante un evento genuino (_al_progreso_tarea / _al_bloqueo_seguridad),
        # con una entrada sintética en vez de fingir el estado directamente.
        assert "_al_progreso_tarea" in src, "Estado 'trabajando' falta en demo (vía _al_progreso_tarea real)"
        assert "_al_bloqueo_seguridad" in src, "Estado 'gevura_activa' falta en demo (vía _al_bloqueo_seguridad real)"

    def test_demo_cycles_humores(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "sereno" in src, "Humor sereno falta en demo"
        assert "emocionado" in src, "Humor emocionado falta en demo"
        assert "preocupado" in src, "Humor preocupado falta en demo"

    def test_demo_activates_tacto_zones(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_zona_tacto" in src, "Zonas de tacto faltan en demo"

    def test_demo_has_narration(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_narrar" in src or "hilo_habla.hablar" in src, "Narración falta en demo"

    def test_demo_restores_humor(self):
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_humor_orig" in src, "Demo no restaura humor original"

