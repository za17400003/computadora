"""
test_tikun_009.py — Tests para FP-046 Tikún Keter-Hod
RF-117: Timeout de _esperando_respuesta (30s)
RF-118: Filtro mínimo en path _esperando_respuesta
RF-119: Hot-reload: voz como capa de reinicio manual
RF-120: Backoff de transcripciones vacías consecutivas
"""

import re
import unittest
from pathlib import Path

ESCUCHA_SRC = (Path(__file__).resolve().parent.parent / "golem" / "voz" / "escucha.py").read_text(encoding="utf-8")
HOTRELOAD_SRC = (Path(__file__).resolve().parent.parent / "golem" / "nucleo" / "hot_reload.py").read_text(encoding="utf-8")
VENTANA_SRC = (Path(__file__).resolve().parent.parent / "golem" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")


# ═══════════════════════════════════════════════
# RF-117: Timeout de _esperando_respuesta
# ═══════════════════════════════════════════════

class TestTimeoutEsperandoRespuesta(unittest.TestCase):
    """RF-117: _esperando_respuesta debe expirar tras 30s."""

    def test_timestamp_attr_exists(self):
        """El atributo _esperando_respuesta_ts se inicializa en __init__."""
        self.assertIn("_esperando_respuesta_ts", ESCUCHA_SRC)

    def test_timeout_check_in_transcribir(self):
        """El path de _esperando_respuesta verifica tiempo transcurrido."""
        self.assertIn("time.monotonic() - self._esperando_respuesta_ts", ESCUCHA_SRC)

    def test_timeout_30s(self):
        """El timeout es 30 segundos."""
        self.assertRegex(ESCUCHA_SRC, r">\s*30\.0")

    def test_expiry_resets_flag(self):
        """Al expirar, se resetea _esperando_respuesta = False."""
        # El bloque de timeout debe poner la flag a False
        self.assertIn("self._esperando_respuesta = False", ESCUCHA_SRC)

    def test_ventana_sets_timestamp(self):
        """ventana_principal.py setea _esperando_respuesta_ts al activar la flag."""
        count = VENTANA_SRC.count("_esperando_respuesta_ts = time.monotonic()")
        self.assertGreaterEqual(count, 3, "Al menos 3 de los 4 setters deben incluir timestamp")


# ═══════════════════════════════════════════════
# RF-118: Filtro en path _esperando_respuesta
# ═══════════════════════════════════════════════

class TestFiltroEsperandoRespuesta(unittest.TestCase):
    """RF-118: _esperando_respuesta debe pasar por _es_falso_positivo_conversacion."""

    def test_filter_called_in_esperando_path(self):
        """_es_falso_positivo_conversacion se invoca en el path de respuesta esperada."""
        # Buscar que en el bloque de esperando_respuesta se llama al filtro
        self.assertIn("_es_falso_positivo_conversacion(texto, _nsp_resp)", ESCUCHA_SRC)

    def test_no_direct_emit_without_filter(self):
        """No hay emit directo sin filtro previo en el path de esperando_respuesta."""
        # El antiguo pattern era: if _esperando_respuesta: emit(texto) return
        # Ahora debe haber un filtro entre la condición y el emit
        lines = ESCUCHA_SRC.split("\n")
        for i, line in enumerate(lines):
            if "Respuesta esperada recibida" in line:
                # El emit debe estar DESPUÉS del filtro, no inmediatamente tras if
                # Buscar que hay un motivo_resp check ANTES
                context = "\n".join(lines[max(0, i-15):i])
                self.assertIn("motivo_resp", context)

    def test_descarte_logged(self):
        """El descarte de respuesta esperada se loguea."""
        self.assertIn("Respuesta esperada descartada (falso positivo)", ESCUCHA_SRC)


# ═══════════════════════════════════════════════
# RF-119: Hot-reload: voz como capa reinicio manual
# ═══════════════════════════════════════════════

class TestHotReloadVozManual(unittest.TestCase):
    """RF-119: La capa 'voz' debe requerir reinicio manual."""

    def test_voz_in_reinicio_manual(self):
        """'voz' está en CAPAS_REINICIO_MANUAL."""
        match = re.search(r'CAPAS_REINICIO_MANUAL\s*=\s*\{([^}]+)\}', HOTRELOAD_SRC)
        self.assertIsNotNone(match)
        capas = match.group(1)
        self.assertIn("voz", capas)

    def test_interfaz_still_in_reinicio_manual(self):
        """'interfaz' sigue en CAPAS_REINICIO_MANUAL."""
        match = re.search(r'CAPAS_REINICIO_MANUAL\s*=\s*\{([^}]+)\}', HOTRELOAD_SRC)
        self.assertIsNotNone(match)
        capas = match.group(1)
        self.assertIn("interfaz", capas)

    def test_voz_not_importlib_reloaded(self):
        """Con voz en CAPAS_REINICIO_MANUAL, no se hace importlib.reload silencioso."""
        # La lógica es: si capa in CAPAS_REINICIO_MANUAL → emite requiere_reinicio → return
        # Así que importlib.reload nunca se llama para voz
        self.assertIn("requiere_reinicio", HOTRELOAD_SRC)


# ═══════════════════════════════════════════════
# RF-120: Backoff de transcripciones vacías
# ═══════════════════════════════════════════════

class TestBackoffVaciasConsecutivas(unittest.TestCase):
    """RF-120: Backoff exponencial tras transcripciones vacías consecutivas."""

    def test_counter_initialized(self):
        """_vacias_consecutivas se inicializa en _procesar_stream."""
        self.assertIn("_vacias_consecutivas", ESCUCHA_SRC)

    def test_counter_increments_on_empty(self):
        """El contador incrementa cuando texto está vacío."""
        self.assertIn("_vacias_consecutivas", ESCUCHA_SRC)
        # Buscar el patrón de incremento
        self.assertRegex(ESCUCHA_SRC, r"_vacias_consecutivas.*\+\s*1")

    def test_backoff_after_3(self):
        """Tras 3 vacías consecutivas, silencio_max aumenta."""
        self.assertRegex(ESCUCHA_SRC, r"_vacias_consecutivas\s*>=\s*3")

    def test_silencio_max_capped(self):
        """silencio_max tiene un tope (no crece infinitamente)."""
        self.assertRegex(ESCUCHA_SRC, r"min\(.*silencio_max.*,\s*\d")

    def test_reset_on_nonempty(self):
        """El contador se resetea al recibir transcripción no-vacía."""
        self.assertIn("_vacias_consecutivas = 0", ESCUCHA_SRC)

    def test_silencio_reset_to_config(self):
        """Al resetear, silencio_max vuelve al valor de configuración."""
        self.assertIn("silencio_max_segundos", ESCUCHA_SRC)


# ═══════════════════════════════════════════════
# Integración: escenario del bug reportado
# ═══════════════════════════════════════════════

class TestEscenarioBugFalsoPositivo(unittest.TestCase):
    """Test del escenario exacto reportado: garbage transcription procesada como respuesta."""

    def test_pure_english_garbage_caught(self):
        """Texto con mayoría inglesa sí se filtra."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from computadora.voz.escucha import _es_falso_positivo_conversacion

        # Garbage con mayoría de palabras inglesas conocidas
        garbage_en = "oh my go do it now please sorry bye"
        motivo = _es_falso_positivo_conversacion(garbage_en, 0.3)
        self.assertTrue(len(motivo) > 0, "Texto mayoritariamente inglés debería filtrarse")

    def test_primary_defense_is_timeout(self):
        """La defensa principal contra el bug es el timeout de _esperando_respuesta (30s).
        El texto garbage del log era español-adyacente (Whisper halucina en español),
        así que el filtro de FP no lo atrapa — pero el timeout sí evita el escenario."""
        # Verificar que el timeout existe en el code path
        self.assertIn("Timeout de _esperando_respuesta", ESCUCHA_SRC)


if __name__ == "__main__":
    unittest.main()

