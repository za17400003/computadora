"""
FP-050 Tikún HaDibúr VeEtz — Tests RF-130/RF-132/RF-133
- RF-130: "malcut" en whitelist + regex
- RF-132: Variantes Whisper de "haz tu demostración"
- RF-133: demo_visual como herramienta N2
"""
import re
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestRF130_MalcutVariantes:
    """RF-130: malcut/malkut/malhut en whitelist y regex."""

    def test_malcut_en_whitelist_escucha(self):
        from computadora.voz.escucha import _ESPAÑOL_CORTAS_VALIDAS
        for v in ("maljut", "malkut", "malcut", "malhut", "malhud", "maljud"):
            assert v in _ESPAÑOL_CORTAS_VALIDAS, f"{v} falta en whitelist"

    def test_malcut_no_es_falso_positivo(self):
        from computadora.voz.escucha import _es_falso_positivo_conversacion
        for v in ("malcut", "malkut", "maljut", "malhut", "malhud", "maljud"):
            resultado = _es_falso_positivo_conversacion(v)
            assert resultado == "", f"'{v}' descartado: {resultado}"

    def test_malcut_regex_demo(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("malcut"), "malcut no matchea regex"

    def test_malkut_regex_demo(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("malkut"), "malkut no matchea regex"

    def test_cut_en_alternacion(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("demo de malcut"), "demo de malcut no matchea"


class TestRF132_WhisperVariantesDemo:
    """RF-132: Whisper transcribe 'haz tu demo' como variantes."""

    def test_hasta_demostracion(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("hasta demostración")

    def test_as_tu_demostracion(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("as tu demostración")

    def test_has_tu_demo(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("has tu demo")

    def test_hasta_tu_demo(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("hasta tu demo")

    def test_haz_tu_demo_sigue_funcionando(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("haz tu demostración")

    def test_ejecuta_tu_demo_sigue_funcionando(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("ejecuta tu demo")

    def test_activa_demo_sigue_funcionando(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        assert _RE_DEMO_ANIMACIONES.search("activa demo")


class TestRF133_DemoVisualTool:
    """RF-133: demo_visual como herramienta para N2 (balance Keter)."""

    def test_demo_visual_en_herramientas(self):
        from computadora.habilidades.herramientas import HERRAMIENTAS
        assert "demo_visual" in HERRAMIENTAS

    def test_demo_visual_retorna_magic_string(self):
        from computadora.habilidades.herramientas import ejecutar_herramienta
        resultado = ejecutar_herramienta("demo_visual", {}, orden_directa=True)
        assert resultado == "__DEMO_ANIMACIONES__"

    def test_demo_visual_permiso_info(self):
        from computadora.habilidades.herramientas import _NIVELES_PERMISO
        assert _NIVELES_PERMISO.get("demo_visual") == "info"

    def test_sistema_prompt_menciona_demo_visual(self):
        from computadora.cerebro.nlu import SISTEMA_PROMPT
        assert "demo_visual" in SISTEMA_PROMPT

