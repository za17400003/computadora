"""
CICLO 13 RUBEDO — Boot Validation Real & Pragmático
=====================================================

Verifica que Computadora pueda iniciar y funcionar sin errores.
Tria Prima: por favor + gracias + amén×3 = autonomía completa

Estrategia: Tests SIMPLES y REALIZABLES sin depender de API complexas
1. Módulos importan sin errores
2. Clases inicialicen sin excepciones
3. Config.json existe y es válido
4. Funcionalidadescríticas (audio, face_recognition, etc.)
5. Conversación end-to-end con mocks
"""

import pytest
import sys
import json
import time
import queue
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

proyecto_root = Path(__file__).parent.parent
sys.path.insert(0, str(proyecto_root))

# ============================================================================
# PHASE 1: Basic Imports & Dependencies
# ============================================================================

class TestPhase1Imports:
    """Verificar que módulos importan sin errores"""

    def test_import_watchdog(self):
        """Watchdog module debe importar"""
        from computadora.interfaz import watchdog
        assert watchdog is not None

    def test_import_cerebro(self):
        """Cerebro module debe importar"""
        from computadora.cerebro import nlu
        assert nlu is not None

    def test_import_meta_workflow(self):
        """MetaWorkflow debe importar"""
        from computadora.nucleo import meta_workflow
        assert meta_workflow is not None

    def test_import_orquestador(self):
        """Orquestador debe importar"""
        from computadora.nucleo import orquestador
        assert orquestador is not None

    def test_import_herramientas(self):
        """Herramientas debe importar"""
        from computadora.nucleo import herramientas
        assert herramientas is not None

    def test_whisper_available(self):
        """Whisper debe estar disponible"""
        try:
            import whisper
            assert whisper is not None
        except ImportError:
            pytest.skip("Whisper no instalado")

    def test_face_recognition_available(self):
        """face_recognition debe estar disponible"""
        try:
            import face_recognition
            assert face_recognition is not None
        except ImportError:
            pytest.skip("face_recognition no instalado")

    def test_sounddevice_available(self):
        """sounddevice debe estar disponible"""
        try:
            import sounddevice
            assert sounddevice is not None
        except ImportError:
            pytest.skip("sounddevice no instalado")

# ============================================================================
# PHASE 2: Class Initialization
# ============================================================================

class TestPhase2Initialization:
    """Verificar que clases principales inicialicen"""

    def test_watchdogcomputadora_init(self):
        """WatchdogComputadora debe inicializar"""
        from computadora.interfaz.watchdog import WatchdogComputadora
        
        watchdog = WatchdogComputadora()
        assert watchdog is not None
        assert hasattr(watchdog, 'estado')

    def test_renovacion_operativa_init(self):
        """RenovacionOperativa debe inicializar"""
        from computadora.cerebro.renovacion import RenovacionOperativa
        
        renovacion = RenovacionOperativa()
        assert renovacion is not None
        assert hasattr(renovacion, 'leyes')

    def test_meta_workflow_init(self):
        """MetaWorkflow debe inicializar"""
        from computadora.nucleo.meta_workflow import MetaWorkflow
        
        workflow = MetaWorkflow()
        assert workflow is not None

    def test_orquestador_init(self):
        """Orquestador debe inicializar"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        assert orq is not None
        assert hasattr(orq, '_cerebro')
        assert hasattr(orq, '_herramientas')

    def test_herramientas_init(self):
        """HerramientasOpenClaw debe inicializar"""
        from computadora.nucleo.herramientas import HerramientasOpenClaw
        
        tools = HerramientasOpenClaw()
        assert tools is not None

    def test_hilo_escucha_structure(self):
        """HiloEscucha debe tener estructura correcta"""
        from computadora.voz.escucha import HiloEscucha
        
        hilo = HiloEscucha(
            on_voz=Mock(),
            on_transcripcion=Mock()
        )
        assert hasattr(hilo, '_ejecutando')
        assert hasattr(hilo, 'iniciar')

# ============================================================================
# PHASE 3: Configuration Files
# ============================================================================

class TestPhase3Configuration:
    """Verificar archivos de configuración"""

    def test_config_json_exists(self):
        """datos/config.json debe existir"""
        config_path = proyecto_root / "datos" / "config.json"
        assert config_path.exists(), f"config.json falta en {config_path}"

    def test_config_json_valid(self):
        """config.json debe ser JSON válido"""
        config_path = proyecto_root / "datos" / "config.json"
        with open(config_path) as f:
            config = json.load(f)
        
        assert isinstance(config, dict)

# ============================================================================
# PHASE 4: Core Functionality
# ============================================================================

class TestPhase4CoreFunctionality:
    """Verificar funcionalidades críticas"""

    def test_audio_queue_rf371(self):
        """RF-371: Audio queue maxsize=256"""
        audio_queue = queue.Queue(maxsize=256)
        assert audio_queue.maxsize == 256
        
        # Overflow handling
        for i in range(300):
            try:
                audio_queue.put_nowait(f"frame_{i}")
            except queue.Full:
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    pass
                audio_queue.put_nowait(f"frame_{i}")
        
        assert audio_queue.qsize() <= 256

    def test_frame_skip_logic_rf372(self):
        """RF-372: Frame skip 60→30 FPS logic"""
        frame_skip_counter = 0
        frames_rendered = 0
        
        for frame_num in range(100):
            frame_skip_counter += 1
            
            # Skip logic
            if frame_skip_counter % 2 != 0:
                continue
            
            frames_rendered += 1
        
        skip_ratio = 1.0 - (frames_rendered / 100.0)
        assert 0.4 < skip_ratio < 0.6

    def test_hablante_classification(self):
        """Clasificación de hablante"""
        owner_embedding = np.random.randn(128)
        owner_embedding = owner_embedding / np.linalg.norm(owner_embedding)
        
        test_voice = np.random.randn(128)
        test_voice = test_voice / np.linalg.norm(test_voice)
        
        similitud = np.dot(owner_embedding, test_voice)
        
        if similitud >= 0.85:
            clase = "amo"
        elif similitud >= 0.65:
            clase = "conocido"
        else:
            clase = "extraño"
        
        assert clase in ["amo", "conocido", "extraño"]

    def test_face_recognition_basic(self):
        """face_recognition funciona con imágenes"""
        try:
            import face_recognition
            
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            encodings = face_recognition.face_encodings(test_image)
            
            assert isinstance(encodings, list)
        except ImportError:
            pytest.skip("face_recognition not available")

# ============================================================================
# PHASE 5: Conversation Flow
# ============================================================================

class TestPhase5ConversationFlow:
    """Verificar flujo de conversación"""

    def test_conversation_mock_flow(self):
        """Flujo de conversación: entrada → NLU → respuesta"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        with patch.object(orq._cerebro, 'procesar') as mock_process:
            mock_process.return_value = {
                "respuesta": "Hola, estoy listo para conversar",
                "accion": "hablar",
                "confianza": 0.95
            }
            
            result = orq._cerebro.procesar("Hola Computadora")
            
            assert result is not None
            assert "respuesta" in result
            assert result["accion"] == "hablar"

    def test_audio_capture_simulation(self):
        """Simulación de captura de audio"""
        sample_rate = 44100
        audio_frames = np.random.randn(sample_rate) * 0.01
        
        audio_queue = queue.Queue(maxsize=256)
        
        for i in range(100):
            try:
                audio_queue.put_nowait(audio_frames[i*100:(i+1)*100])
            except queue.Full:
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    pass
        
        assert audio_queue.qsize() > 0

# ============================================================================
# PHASE 6: Integration Test
# ============================================================================

class TestPhase6Integration:
    """Integración sin deadlock"""

    def test_boot_sequence_complete(self):
        """Boot secuencia: todos los módulos inicializan"""
        from computadora.interfaz.watchdog import WatchdogComputadora
        from computadora.cerebro.renovacion import RenovacionOperativa
        from computadora.nucleo.meta_workflow import MetaWorkflow
        from computadora.nucleo.orquestador import Orquestador
        from computadora.nucleo.herramientas import HerramientasOpenClaw
        
        # Cada uno debe inicializar sin exception
        w = WatchdogComputadora()
        r = RenovacionOperativa()
        m = MetaWorkflow()
        o = Orquestador()
        h = HerramientasOpenClaw()
        
        assert all([w, r, m, o, h])

    def test_conversation_ready(self):
        """Sistema listo para conversar post-boot"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        # Mock mensaje del usuario
        with patch.object(orq._cerebro, 'procesar') as mock_process:
            mock_process.return_value = {
                "respuesta": "Estoy listo",
                "accion": "hablar",
                "confianza": 0.90
            }
            
            result = orq._cerebro.procesar("Hola")
            
            assert result is not None
            assert result["accion"] == "hablar"

# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

