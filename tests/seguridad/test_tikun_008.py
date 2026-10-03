"""test_tikun_008.py — Tests para FP-045 Shomer Hod (RF-113/RF-114/RF-115/RF-116)

Ciclo Tikún 8: Guardia completa de percepción.
"""
import re
import sys
import os
import unittest

# Ajustar path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── RF-113: Conversation window respeta media ──

class TestConversacionMediaGuard(unittest.TestCase):
    """Verifica que _transcribir descarta audio en conversación cuando hay media activa."""

    def test_media_guard_presente_en_escucha(self):
        """El bloque FP-045A debe existir en escucha.py."""
        src = _leer_fuente("golem/voz/escucha.py")
        self.assertIn("FP-045A", src)
        self.assertIn("media_activa_en_conversacion", src)

    def test_guard_respeta_esperando_respuesta(self):
        """Si _esperando_respuesta es True, NO debe descartar (necesita la respuesta del usuario)."""
        src = _leer_fuente("golem/voz/escucha.py")
        self.assertIn("not self._esperando_respuesta", src)

    def test_log_media_descartada(self):
        """Debe loguear con motivo 'media_descartada'."""
        src = _leer_fuente("golem/voz/escucha.py")
        self.assertIn('"media_descartada"', src)


# ── RF-114: Interrupción respeta media ──

class TestInterrupcionMediaGuard(unittest.TestCase):
    """Verifica que la detección de interrupción se desactiva con media activa."""

    def test_interrupcion_guard_presente(self):
        """El bloque FP-045B debe existir en escucha.py."""
        src = _leer_fuente("golem/voz/escucha.py")
        self.assertIn("FP-045B", src)

    def test_media_activa_filtra_silenciosamente(self):
        """Cuando media activa, debe retornar sin emitir interrupcion_detectada."""
        src = _leer_fuente("golem/voz/escucha.py")
        # Debe haber: if _media_activa: ... return (antes del ratio check)
        pattern = r"if _media_activa:\s*\n\s+logger\.debug.*Media activa durante TTS.*\n\s+return"
        self.assertRegex(src, pattern)


# ── RF-115: Filtro de alucinación Whisper ──

class TestAlucinacionWhisperFilter(unittest.TestCase):
    """Verifica que _es_falso_positivo_conversacion detecta caracteres no-latinos."""

    def _importar_filtro(self):
        """Importa la función de filtro."""
        from computadora.voz.escucha import _es_falso_positivo_conversacion
        return _es_falso_positivo_conversacion

    def test_cjk_detectado(self):
        filtro = self._importar_filtro()
        resultado = filtro("un tarro no fue que las tardes namめ les deform惹 ICU")
        self.assertIn("alucinacion_whisper", resultado)

    def test_cirilico_detectado(self):
        filtro = self._importar_filtro()
        resultado = filtro("algo рядом с вами señor")
        self.assertIn("alucinacion_whisper", resultado)

    def test_arabe_detectado(self):
        filtro = self._importar_filtro()
        resultado = filtro("hola مرحبا como estas")
        self.assertIn("alucinacion_whisper", resultado)

    def test_español_puro_no_afectado(self):
        filtro = self._importar_filtro()
        resultado = filtro("busca todo lo que encuentres sobre los golems")
        self.assertEqual(resultado, "")

    def test_acentos_españoles_ok(self):
        filtro = self._importar_filtro()
        resultado = filtro("dime la información que tengas sobre Moisés")
        self.assertEqual(resultado, "")


# ── RF-116: PISTAS_HERRAMIENTAS expandido ──

class TestPistasHerramientasExpandido(unittest.TestCase):
    """Verifica que las nuevas pistas buscan correctamente."""

    def _regex(self):
        from computadora.cerebro.parseo_herramientas import PISTAS_HERRAMIENTAS
        return PISTAS_HERRAMIENTAS

    def test_busca_todo(self):
        self.assertIsNotNone(self._regex().search("busca todo lo que encuentres"))

    def test_busca_informacion(self):
        self.assertIsNotNone(self._regex().search("busca información sobre Python"))

    def test_busca_datos(self):
        self.assertIsNotNone(self._regex().search("busca datos del clima"))

    def test_busca_algo(self):
        self.assertIsNotNone(self._regex().search("busca algo interesante"))

    def test_dime_todo(self):
        self.assertIsNotNone(self._regex().search("dime todo sobre los golems"))

    def test_dime_sobre(self):
        self.assertIsNotNone(self._regex().search("dime sobre la IA"))

    def test_dime_acerca(self):
        self.assertIsNotNone(self._regex().search("dime acerca de la historia"))

    def test_buscame(self):
        self.assertIsNotNone(self._regex().search("búscame recetas de pasta"))

    def test_averigua(self):
        self.assertIsNotNone(self._regex().search("averigua quién inventó el teléfono"))

    def test_encuentra_todo(self):
        self.assertIsNotNone(self._regex().search("encuentra todo sobre los golems"))

    def test_encuentra_informacion(self):
        self.assertIsNotNone(self._regex().search("encuentra información del tema"))

    def test_original_busca_en_internet(self):
        """Verificar que las pistas originales siguen funcionando."""
        self.assertIsNotNone(self._regex().search("busca en internet sobre Python"))

    def test_original_investiga(self):
        self.assertIsNotNone(self._regex().search("investiga sobre JavaScript"))

    def test_conversacion_no_matchea(self):
        """Saludos NO deben matchear."""
        self.assertIsNone(self._regex().search("hola cómo estás"))

    def test_pregunta_casual_no_matchea(self):
        """Preguntas casuales NO deben matchear."""
        self.assertIsNone(self._regex().search("qué opinas de la vida"))


# ── Utilidad ──

def _leer_fuente(ruta_relativa: str) -> str:
    ruta = os.path.join(os.path.dirname(__file__), "..", ruta_relativa)
    with open(ruta, encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    unittest.main()

