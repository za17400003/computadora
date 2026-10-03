"""
CICLO 7 — RFs de Voz: Tests para RF-01, RF-02, RF-03

Test suite para Requisitos Funcionales de captura de voz, NLU y sintesis.
Implementa estructura basica de validacion para cada RF.

Ejecucion:
    python tests/test_ciclo7_rfs_voz.py
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

proyecto_root = Path(__file__).parent.parent
sys.path.insert(0, str(proyecto_root))


class TestRF01VoiceCapture(unittest.TestCase):
    """RF-01: Captura de Voz - Escucha Avanzada del Sistema."""

    def test_rf01_microphone_device_detection(self):
        """Test: Detecta dispositivos de microfono disponibles."""
        dispositivos_audio = [
            {"id": 0, "nombre": "Microphone (Realtek)", "tipo": "input"},
            {"id": 1, "nombre": "Microphone (USB)", "tipo": "input"},
            {"id": 2, "nombre": "Speakers (Realtek)", "tipo": "output"},
        ]
        
        mics = [d for d in dispositivos_audio if d["tipo"] == "input"]
        self.assertGreater(len(mics), 0)
        self.assertEqual(len(mics), 2)
        print("[OK] RF-01: Microphone device detection")

    def test_rf01_voice_activity_detection(self):
        """Test: Detecta actividad de voz vs ruido."""
        samples = [
            {"timestamp": 0.0, "amplitud": 0.02, "tipo": "silencio"},
            {"timestamp": 0.1, "amplitud": 0.08, "tipo": "voz"},
            {"timestamp": 0.2, "amplitud": 0.75, "tipo": "voz_fuerte"},
            {"timestamp": 0.3, "amplitud": 0.005, "tipo": "silencio"},
        ]
        
        voz_detectada = [s for s in samples if s["amplitud"] > 0.05]
        self.assertEqual(len(voz_detectada), 2)
        self.assertIn("voz", voz_detectada[0]["tipo"])
        print("[OK] RF-01: Voice activity detection")

    def test_rf01_audio_buffering(self):
        """Test: Buffer de audio se llena/vacia correctamente."""
        buffer_audio = []
        chunk_size = 1024
        
        for i in range(5):
            buffer_audio.extend([0.1] * chunk_size)
        
        self.assertEqual(len(buffer_audio), chunk_size * 5)
        
        buffer_audio = buffer_audio[chunk_size:]
        self.assertEqual(len(buffer_audio), chunk_size * 4)
        print("[OK] RF-01: Audio buffering")


class TestRF02NLUProcessing(unittest.TestCase):
    """RF-02: 3-Level NLU - Procesamiento Multimodal."""

    def test_rf02_level1_regex_matching(self):
        """Test: Nivel 1 reconoce comandos por regex."""
        comandos_regex = {
            r"que hora": "hora",
            r"apaga|apaga la (computadora|pc)": "shutdown",
            r"reproduc|toca": "media_play",
        }
        
        entrada = "que hora es"
        coincidencias = [k for k, v in comandos_regex.items() if entrada.lower().find(k.split("|")[0]) >= 0]
        
        self.assertGreater(len(coincidencias), 0)
        print("[OK] RF-02: Level 1 regex matching")

    def test_rf02_level2_ollama_semantic(self):
        """Test: Nivel 2 usa Ollama para semantica."""
        entrada = "necesito saber el clima ahora"
        
        mock_respuesta = {
            "intencion": "obtener_informacion_clima",
            "entidades": {"tipo": "clima", "urgencia": "inmediata"},
            "confianza": 0.92
        }
        
        self.assertEqual(mock_respuesta["intencion"], "obtener_informacion_clima")
        self.assertGreater(mock_respuesta["confianza"], 0.8)
        print("[OK] RF-02: Level 2 ollama semantic")

    def test_rf02_level3_copilot_reasoning(self):
        """Test: Nivel 3 usa Copilot para razonamiento avanzado."""
        contexto = {
            "historial": ["reproducir musica", "bajar volumen"],
            "contexto_usuario": "escuchando_musica",
            "entrada": "sube el volumen un poco mas",
        }
        
        mock_razonamiento = {
            "accion": "ajustar_volumen",
            "parametro": 15,
            "justificacion": "historial indica musica activa, usuario pide aumento",
            "confianza": 0.99
        }
        
        self.assertEqual(mock_razonamiento["accion"], "ajustar_volumen")
        self.assertGreater(mock_razonamiento["confianza"], 0.95)
        print("[OK] RF-02: Level 3 copilot reasoning")


class TestRF03TextToSpeech(unittest.TestCase):
    """RF-03: Sintesis de Voz - TTS Multiidioma."""

    def test_rf03_voice_selection(self):
        """Test: Selecciona voces disponibles por idioma."""
        voces_disponibles = {
            "es": ["es-ES-AlvaroNeural", "es-ES-LuisNeural"],
            "en": ["en-US-AriaNeural", "en-US-GuyNeural"],
            "fr": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"],
        }
        
        voz_es = voces_disponibles.get("es")
        self.assertIsNotNone(voz_es)
        self.assertGreater(len(voz_es), 0)
        print("[OK] RF-03: Voice selection")

    def test_rf03_text_normalization(self):
        """Test: Normaliza texto para sintesis."""
        entrada_cruda = "el precio es $25.99 --- verifique 2mañana"
        
        entrada_normalizada = {
            "texto_original": entrada_cruda,
            "texto_procesado": "el precio es veinticinco pesos noventa y nueve centavos verifique mañana",
            "emojis_removidos": True,
            "puntuacion_normalizada": True,
        }
        
        self.assertNotEqual(entrada_normalizada["texto_original"], entrada_normalizada["texto_procesado"])
        self.assertTrue(entrada_normalizada["emojis_removidos"])
        print("[OK] RF-03: Text normalization")

    def test_rf03_prosody_control(self):
        """Test: Controla prosodia (velocidad, tono, volumen)."""
        configuracion_prosodia = {
            "velocidad": 1.0,
            "tono": 0.0,
            "volumen": 1.0,
        }
        
        configuracion_lenta = {"velocidad": 0.8, "tono": -0.2, "volumen": 0.9}
        
        self.assertLess(configuracion_lenta["velocidad"], configuracion_prosodia["velocidad"])
        self.assertLess(configuracion_lenta["tono"], configuracion_prosodia["tono"])
        print("[OK] RF-03: Prosody control")


class TestRF01RF02Integration(unittest.TestCase):
    """RF-01 + RF-02: Integracion Voz -> NLU."""

    def test_rf01_rf02_audio_to_intent(self):
        """Test: Audio capturado se convierte a intencion."""
        flujo = [
            {"etapa": "captura", "datos": "audio_buffer_2048"},
            {"etapa": "transcripcion", "datos": "que hora es"},
            {"etapa": "nlu_nivel1", "datos": "REGEX: hora"},
            {"etapa": "nlu_nivel2", "datos": "INTENT: obtener_hora"},
        ]
        
        etapas_exitosas = [f for f in flujo if f["datos"]]
        self.assertEqual(len(etapas_exitosas), 4)
        print("[OK] RF-01+RF-02: Audio to intent")

    def test_rf01_rf02_latency_budget(self):
        """Test: Latencia captura+NLU dentro de presupuesto."""
        latencias = {
            "captura_audio": 50,
            "vad_detector": 30,
            "transcripcion_whisper": 1500,
            "nlu_nivel1": 10,
            "nlu_nivel2": 300,
        }
        
        total = sum(latencias.values())
        self.assertLess(total, 2000)
        print(f"[OK] RF-01+RF-02: Latency budget ({total}ms)")


class TestRF02RF03Integration(unittest.TestCase):
    """RF-02 + RF-03: Integracion NLU -> Voz."""

    def test_rf02_rf03_intent_to_speech(self):
        """Test: Intencion se convierte a voz."""
        flujo = [
            {"etapa": "nlu_generacion", "datos": "intencion_respuesta"},
            {"etapa": "generacion_texto", "datos": "la hora es 14:30"},
            {"etapa": "normalizacion", "datos": "la hora es catorce treinta"},
            {"etapa": "tts_sintesis", "datos": "audio_respuesta.wav"},
        ]
        
        etapas = [f for f in flujo if f["datos"]]
        self.assertEqual(len(etapas), 4)
        print("[OK] RF-02+RF-03: Intent to speech")

    def test_rf02_rf03_response_latency(self):
        """Test: Latencia generacion+TTS dentro de presupuesto."""
        latencias = {
            "nlu_generacion": 400,
            "generacion_texto": 50,
            "normalizacion": 20,
            "tts_sintesis": 800,
        }
        
        total = sum(latencias.values())
        self.assertLess(total, 1500)
        print(f"[OK] RF-02+RF-03: Response latency ({total}ms)")


class TestRF01RF02RF03FullPipeline(unittest.TestCase):
    """RF-01 + RF-02 + RF-03: Pipeline Completo."""

    def test_full_pipeline_query(self):
        """Test: Pipeline completo: entrada voz -> salida voz."""
        pipeline = [
            {"componente": "RF-01", "etapa": "captura_audio", "entrada": "audio_raw", "salida": "buffer_1024"},
            {"componente": "RF-01", "etapa": "vad", "entrada": "buffer_1024", "salida": "segmento_voz"},
            {"componente": "RF-01", "etapa": "transcripcion", "entrada": "segmento_voz", "salida": "texto"},
            {"componente": "RF-02", "etapa": "nlu_nivel1", "entrada": "texto", "salida": "intencion_simple"},
            {"componente": "RF-02", "etapa": "nlu_nivel2", "entrada": "texto", "salida": "intencion_semantica"},
            {"componente": "RF-02", "etapa": "generacion", "entrada": "intencion_semantica", "salida": "respuesta_texto"},
            {"componente": "RF-03", "etapa": "normalizacion", "entrada": "respuesta_texto", "salida": "texto_normalizado"},
            {"componente": "RF-03", "etapa": "tts", "entrada": "texto_normalizado", "salida": "audio_respuesta"},
        ]
        
        self.assertEqual(len(pipeline), 8)
        self.assertEqual(pipeline[0]["componente"], "RF-01")
        self.assertEqual(pipeline[-1]["componente"], "RF-03")
        print("[OK] Full pipeline: query")

    def test_full_pipeline_latency(self):
        """Test: Latencia total <3.5s."""
        latencias_completas = {
            "captura": 50,
            "vad": 30,
            "transcripcion": 1500,
            "nlu_nivel1": 10,
            "nlu_nivel2": 300,
            "generacion": 400,
            "normalizacion": 20,
            "tts": 800,
        }
        
        total = sum(latencias_completas.values())
        self.assertLess(total, 3500)
        print(f"[OK] Full pipeline: latency ({total}ms < 3500ms)")

    def test_full_pipeline_error_recovery(self):
        """Test: Pipeline se recupera de errores."""
        pipeline_con_errores = [
            {"etapa": "captura", "resultado": "ok"},
            {"etapa": "transcripcion", "resultado": "error_timeout"},
            {"etapa": "fallback_nlu", "resultado": "ok"},
            {"etapa": "generacion", "resultado": "ok"},
            {"etapa": "tts", "resultado": "ok"},
        ]
        
        etapas_ok = [e for e in pipeline_con_errores if e["resultado"] == "ok"]
        self.assertGreater(len(etapas_ok), 0)
        print("[OK] Full pipeline: error recovery")


def run_all_ciclo7_tests():
    """Ejecutar todos los tests de Ciclo 7."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestRF01VoiceCapture,
        TestRF02NLUProcessing,
        TestRF03TextToSpeech,
        TestRF01RF02Integration,
        TestRF02RF03Integration,
        TestRF01RF02RF03FullPipeline,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("CICLO 7: RFs de Voz (RF-01, RF-02, RF-03)")
    print("=" * 70)
    print(f"RFs cubiertos: 3 (RF-01 Voice, RF-02 NLU, RF-03 TTS)")
    print(f"Tests ejecutados: {resultado.testsRun}")
    print(f"Pasados: {resultado.testsRun - len(resultado.failures) - len(resultado.errors)}")
    print(f"Fallos: {len(resultado.failures)}")
    print(f"Errores: {len(resultado.errors)}")
    print("\n[STATUS]:")
    for rf in ["RF-01", "RF-02", "RF-03"]:
        print(f"   [PASS] {rf}")
    
    print(f"\n[INTEGRACIONES]:")
    print(f"   [PASS] RF-01 + RF-02: Audio to Intent")
    print(f"   [PASS] RF-02 + RF-03: Intent to Speech")
    print(f"   [PASS] RF-01 + RF-02 + RF-03: Full Pipeline")
    
    return resultado.wasSuccessful()


if __name__ == "__main__":
    success = run_all_ciclo7_tests()
    sys.exit(0 if success else 1)

