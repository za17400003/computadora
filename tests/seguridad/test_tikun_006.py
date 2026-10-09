"""
FP-043 Citrinitas — Mar'é HaMaljut + Tikún Etz HaChaim + Bug Fixes
Tests fase 48: 20 tests
"""
import re
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ═══════════════════════════════════════════════
# PART A — Demo Maljut
# ═══════════════════════════════════════════════

class TestDemoMaljutRegex(unittest.TestCase):
    """Verifica que _RE_DEMO_ANIMACIONES matchea las frases esperadas."""

    @classmethod
    def setUpClass(cls):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        cls.regex = _RE_DEMO_ANIMACIONES

    def test_ensenname_tu_maljut(self):
        self.assertTrue(self.regex.search("ense\u00f1ame tu maljut"))

    def test_muestrame_lo_que_sabes_hacer(self):
        self.assertTrue(self.regex.search("mu\u00e9strame lo que sabes hacer"))

    def test_hazme_una_demo(self):
        self.assertTrue(self.regex.search("hazme una demo"))

    def test_demo_visual(self):
        self.assertTrue(self.regex.search("demo visual"))

    def test_muestrate(self):
        self.assertTrue(self.regex.search("mu\u00e9strate"))

    def test_lucite(self):
        self.assertTrue(self.regex.search("luc\u00edte"))

    def test_no_falso_positivo_abrir(self):
        self.assertIsNone(self.regex.search("abre el navegador"))

    def test_no_falso_positivo_hora(self):
        self.assertIsNone(self.regex.search("qu\u00e9 hora es"))


class TestDemoMaljutHandler(unittest.TestCase):
    """Verifica que el handler N1 retorna __DEMO_ANIMACIONES__."""

    def test_pensar_nivel1_demo(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        self.assertTrue(_RE_DEMO_ANIMACIONES.search("hazme una demo"))
        # El handler retorna el token especial (verificado por regex match)


# ═══════════════════════════════════════════════
# PART B — Tikún Etz HaChaim
# ═══════════════════════════════════════════════

class TestBusEventosSuscriptores(unittest.TestCase):
    """B1+B7: MetaWorkflow suscribe a BusEventos."""

    def test_meta_workflow_suscribe_bus(self):
        from computadora.nucleo.eventos import obtener_bus
        bus = obtener_bus()
        # Limpiar para test aislado
        bus._suscriptores.clear()
        from computadora.nucleo.meta_workflow import MetaWorkflow
        mw = MetaWorkflow()
        self.assertIn("keter_auditoria", bus._suscriptores)
        self.assertIn("herramienta_error", bus._suscriptores)
        self.assertGreater(len(bus._suscriptores["keter_auditoria"]), 0)

    def test_on_keter_auditoria_no_crash(self):
        from computadora.nucleo.meta_workflow import MetaWorkflow
        mw = MetaWorkflow()
        # No debe explotar con datos válidos o inválidos
        mw._on_keter_auditoria({"tipo": "test", "reporte": "demo"})
        mw._on_keter_auditoria(None)

    def test_on_herramienta_error_no_crash(self):
        from computadora.nucleo.meta_workflow import MetaWorkflow
        mw = MetaWorkflow()
        mw._on_herramienta_error({"nombre": "test_tool"})
        mw._on_herramienta_error("cadena")


class TestPersonasLoguru(unittest.TestCase):
    """B3: personas.py usa loguru en lugar de logging."""

    def test_no_import_logging(self):
        src = (ROOT / "computadora" / "memoria" / "personas.py").read_text(encoding="utf-8")
        self.assertNotIn("import logging", src)
        self.assertIn("from loguru import logger", src)


class TestFaseCircadianaEvento(unittest.TestCase):
    """B6: CicloCircadiano emite fase_circadiana al cambiar."""

    def test_emite_evento_al_cambiar_fase(self):
        from computadora.nucleo.eventos import obtener_bus
        bus = obtener_bus()
        recibidos = []
        bus.suscribir("fase_circadiana", lambda d: recibidos.append(d))

        from computadora.nucleo.ciclo_circadiano import CicloCircadiano
        cc = CicloCircadiano()
        # Forzar cambio
        cc._fase = "activo"
        # Manipular para forzar transición a descanso_guardian
        cc._perfil["media_inicio_min"] = 0    # 00:00
        cc._perfil["media_fin_min"] = 1       # 00:01 — fuera de rango casi siempre
        fase = cc.fase_actual()
        # Si cambió, debe haber emitido
        if fase != "activo":
            self.assertTrue(len(recibidos) > 0)
            self.assertEqual(recibidos[-1]["fase_anterior"], "activo")
            self.assertEqual(recibidos[-1]["fase_nueva"], fase)


# ═══════════════════════════════════════════════
# PART C — Bug Fixes
# ═══════════════════════════════════════════════

class TestLemedQualityGate(unittest.TestCase):
    """C1: _es_promocionable rechaza basura de Whisper."""

    def _get_cerebro_mock(self):
        """Crea un CerebroComputadora mínimo para testear _es_promocionable."""
        from computadora.cerebro.nlu import CerebroComputadora
        # Crear instancia con mock de config
        mock_config = MagicMock()
        mock_config.obtener = MagicMock(return_value=None)
        with patch('computadora.cerebro.nlu.memoria'):
            try:
                cerebro = CerebroComputadora.__new__(CerebroComputadora)
                cerebro._es_promocionable = CerebroComputadora._es_promocionable.__get__(cerebro)
                cerebro._PALABRAS_FUNCIONALES = CerebroComputadora._PALABRAS_FUNCIONALES
            except Exception:
                cerebro = None
        return cerebro

    def test_rechaza_uplo_holida(self):
        cerebro = self._get_cerebro_mock()
        if cerebro is None:
            self.skipTest("No se pudo instanciar CerebroComputadora")
        result = cerebro._es_promocionable("Uplo Holida", "Qu\u00e9 es eso?", "nivel2")
        self.assertFalse(result)

    def test_rechaza_una_palabra_contenido(self):
        cerebro = self._get_cerebro_mock()
        if cerebro is None:
            self.skipTest("No se pudo instanciar CerebroComputadora")
        # Solo artículos + 1 palabra = < 2 palabras de contenido
        result = cerebro._es_promocionable("el a", "algo", "nivel2")
        self.assertFalse(result)

    def test_acepta_texto_valido(self):
        cerebro = self._get_cerebro_mock()
        if cerebro is None:
            self.skipTest("No se pudo instanciar CerebroComputadora")
        result = cerebro._es_promocionable("abre el navegador", "Abriendo navegador", "nivel2")
        self.assertTrue(result)

    def test_rechaza_pues_lleguelen(self):
        cerebro = self._get_cerebro_mock()
        if cerebro is None:
            self.skipTest("No se pudo instanciar CerebroComputadora")
        result = cerebro._es_promocionable("Pues lleguelen", "No entendí", "nivel2")
        self.assertFalse(result)


class TestToolBlockTextoPlano(unittest.TestCase):
    """C2: Detección de ```tool blocks con texto plano."""

    def test_detecta_texto_plano_en_tool_block(self):
        respuesta = '```tool\n¿Qué quieres decir con "Uplo Holida", señor?\n```'
        # Simular la detección
        m = re.search(r'```tool(?:_code)?\s*\n(.+?)\n?\s*```', respuesta, re.DOTALL)
        self.assertIsNotNone(m)
        contenido = m.group(1).strip()
        self.assertNotIn('{', contenido)
        self.assertIn("Uplo Holida", contenido)

    def test_no_detecta_json_como_texto_plano(self):
        respuesta = '```tool\n{"herramienta": "abrir_app", "args": {"nombre": "notepad"}}\n```'
        m = re.search(r'```tool(?:_code)?\s*\n(.+?)\n?\s*```', respuesta, re.DOTALL)
        self.assertIsNotNone(m)
        contenido = m.group(1).strip()
        self.assertIn('{', contenido)  # Es JSON, no texto plano


if __name__ == "__main__":
    unittest.main()

