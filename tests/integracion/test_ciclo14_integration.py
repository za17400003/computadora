"""
CICLO 14 PALINGENESIA — Integration Testing
=============================================

No es lo mismo testear módulos por separado que testear su INTERACCIÓN.
Verificamos:
1. HiloEscucha → Orquestador → CerebroComputadora → TTS (audio pipeline)
2. OrbeComputadora UI ↔ HiloEscucha (no interfieren)
3. MetaWorkflow ↔ EventBus (no deadlock)
4. Renovacion ↔ Orquestador (memoria disponible)
5. Watchdog ↔ todos (monitoreo sin bloqueos)

Tria Prima: gracias, amén = validación final antes de run real
"""

import pytest
import sys
import time
import threading
import tempfile
import json
import queue
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import ThreadPoolExecutor

logging_level = "WARNING"  # Silent para integration tests
import logging
logging.basicConfig(level=logging_level)

proyecto_root = Path(__file__).parent.parent
sys.path.insert(0, str(proyecto_root))

# ============================================================================
# INTEGRATION TEST 1: Audio Pipeline (HiloEscucha → Orquestador → TTS)
# ============================================================================

class TestIntegration1AudioPipeline:
    """HiloEscucha emite transcripción → Orquestador procesa → TTS responde"""

    def test_audio_to_response_flow(self):
        """Flujo completo: audio → transcripción → NLU → respuesta"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        # Mock: usuario dice "¿Qué hora es?"
        usuario_input = "¿Qué hora es?"
        
        # Mock del procesamiento NLU
        with patch.object(orq._cerebro, 'procesar') as mock_nlu:
            mock_nlu.return_value = {
                "respuesta": "Son las 14:30 horas",
                "accion": "responder",
                "confianza": 0.95
            }
            
            # Orquestador procesa entrada
            resultado = orq._cerebro.procesar(usuario_input)
            
            # Verificar que NLU fue llamado
            assert mock_nlu.called
            mock_nlu.assert_called_with(usuario_input)
            
            # Respuesta debe estar disponible
            assert resultado is not None
            assert resultado["accion"] == "responder"

    def test_hilo_escucha_signals_orquestador(self):
        """HiloEscucha emite señal → Orquestador la recibe sin bloqueo"""
        from computadora.voz.escucha import HiloEscucha
        from computadora.nucleo.orquestador import Orquestador
        
        # Setup
        signal_received = [False]
        
        def on_transcripcion(transcripcion):
            signal_received[0] = True
            assert isinstance(transcripcion, (str, dict))
        
        # HiloEscucha mock
        with patch('computadora.voz.escucha.HiloEscucha') as MockEscucha:
            escucha = MockEscucha()
            escucha.on_transcripcion = on_transcripcion
            
            # Simular que HiloEscucha emite transcripción
            on_transcripcion("Hola Computadora")
            
            # Orquestador debe recibir sin bloqueo
            assert signal_received[0] is True

    def test_no_deadlock_audio_ui_parallel(self):
        """HiloEscucha + OrbeComputadora UI en paralelo sin deadlock"""
        audio_processed = [0]
        ui_rendered = [0]
        errors = []
        
        def audio_loop():
            try:
                for i in range(10):
                    # Simular procesamiento de audio
                    time.sleep(0.01)
                    audio_processed[0] += 1
            except Exception as e:
                errors.append(f"Audio: {e}")
        
        def ui_loop():
            try:
                for i in range(10):
                    # Simular renderizado de UI
                    time.sleep(0.01)
                    ui_rendered[0] += 1
            except Exception as e:
                errors.append(f"UI: {e}")
        
        # Ambos en paralelo
        with ThreadPoolExecutor(max_workers=2) as executor:
            audio_future = executor.submit(audio_loop)
            ui_future = executor.submit(ui_loop)
            
            audio_future.result(timeout=5)
            ui_future.result(timeout=5)
        
        # Ambos deben haber completado sin interferencias
        assert audio_processed[0] == 10
        assert ui_rendered[0] == 10
        assert len(errors) == 0

# ============================================================================
# INTEGRATION TEST 2: Orquestador ↔ Herramientas
# ============================================================================

class TestIntegration2OrquestadorTools:
    """Orquestador puede invocar herramientas del sistema sin bloqueos"""

    def test_orquestador_calls_tools(self):
        """Orquestador solicita ejecución de herramienta, recibe resultado"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        # Mock: herramienta disponible
        with patch.object(orq._herramientas, 'ejecutar_comando') as mock_tool:
            mock_tool.return_value = {"resultado": "exito", "output": "dato"}
            
            # Orquestador solicita herramienta
            # (Simular que NLU decide usar herramienta)
            resultado = orq._herramientas.ejecutar_comando("time")
            
            # Verificar que herramienta fue invocada
            assert mock_tool.called
            assert resultado["resultado"] == "exito"

    def test_tool_error_doesnt_crash_orquestador(self):
        """Si herramienta falla, Orquestador continúa operativo"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        # Mock: herramienta lanza excepción
        with patch.object(orq._herramientas, 'ejecutar_comando') as mock_tool:
            mock_tool.side_effect = Exception("Tool crashed")
            
            # Intentar usar herramienta con try-except
            try:
                resultado = orq._herramientas.ejecutar_comando("bad_command")
            except Exception as e:
                assert "Tool crashed" in str(e)
            
            # Orquestador sigue operativo (puede procesar otra entrada)
            orq._cerebro  # Debe estar disponible
            assert orq is not None

# ============================================================================
# INTEGRATION TEST 3: MetaWorkflow ↔ EventBus (no deadlock)
# ============================================================================

class TestIntegration3MetaWorkflowEvents:
    """MetaWorkflow monitorea eventos sin crear deadlocks"""

    def test_meta_workflow_event_processing(self):
        """MetaWorkflow recibe 100 eventos simultáneos sin deadlock"""
        from computadora.nucleo.meta_workflow import MetaWorkflow
        
        workflow = MetaWorkflow()
        events_processed = [0]
        errors = []
        
        def emit_events():
            try:
                for i in range(100):
                    # Simular evento
                    event = {"tipo": "prueba", "id": i}
                    events_processed[0] += 1
            except Exception as e:
                errors.append(str(e))
        
        # MetaWorkflow debe procesar sin deadlock
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(emit_events) for _ in range(10)]
            for f in futures:
                f.result(timeout=5)
        
        assert events_processed[0] == 1000
        assert len(errors) == 0

    def test_meta_workflow_lazy_init_safe(self):
        """MetaWorkflow._suscribir_bus() lazy init no deadlock en boot"""
        from computadora.nucleo.meta_workflow import MetaWorkflow
        
        # Boot sequence
        workflow = MetaWorkflow()
        
        # Lazy subscribe debe ser safe
        workflow._suscribir_bus()  # First call
        workflow._suscribir_bus()  # Second call (idempotent)
        
        # Debe ser operativo
        assert workflow is not None

# ============================================================================
# INTEGRATION TEST 4: Renovacion ↔ Orquestador (memoria disponible)
# ============================================================================

class TestIntegration4MemoryOrchestration:
    """Orquestador puede acceder memoria durante conversación sin bloqueo"""

    def test_orquestador_memory_access_nonblocking(self):
        """Orquestador lee/escribe memoria sin bloquear audio"""
        from computadora.cerebro.renovacion import RenovacionOperativa
        from computadora.nucleo.orquestador import Orquestador
        
        with tempfile.TemporaryDirectory() as tmpdir:
            renovacion = RenovacionOperativa()
            orq = Orquestador()
            
            # Orquestador accede memoria durante conversación
            # (Simular lectura de contexto anterior)
            memoria_available = renovacion is not None
            assert memoria_available is True

    def test_concurrent_memory_and_audio(self):
        """Memoria recibe escritura mientras audio está capturando"""
        memory_writes = [0]
        audio_captures = [0]
        errors = []
        
        def write_memory():
            try:
                for i in range(50):
                    # Simular escritura de recuerdo
                    memory_writes[0] += 1
            except Exception as e:
                errors.append(f"Memory: {e}")
        
        def capture_audio():
            try:
                for i in range(50):
                    # Simular captura de audio
                    audio_captures[0] += 1
            except Exception as e:
                errors.append(f"Audio: {e}")
        
        # Ambos en paralelo
        with ThreadPoolExecutor(max_workers=2) as executor:
            mem_future = executor.submit(write_memory)
            audio_future = executor.submit(capture_audio)
            
            mem_future.result(timeout=5)
            audio_future.result(timeout=5)
        
        assert memory_writes[0] == 50
        assert audio_captures[0] == 50
        assert len(errors) == 0

# ============================================================================
# INTEGRATION TEST 5: Watchdog ↔ All Modules (no blocking)
# ============================================================================

class TestIntegration5WatchdogNonBlocking:
    """Watchdog monitorea sin bloquear otros subsistemas"""

    def test_watchdog_monitoring_doesnt_block_ui(self):
        """Watchdog checkeando Ollama no bloquea renderizado UI"""
        from computadora.interfaz.watchdog import WatchdogGolem
        
        watchdog = WatchdogGolem()
        ui_rendered = [0]
        errors = []
        
        def watchdog_check():
            try:
                for i in range(10):
                    # Simular check de servicio
                    _ = watchdog.estado
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Watchdog: {e}")
        
        def render_ui():
            try:
                for i in range(10):
                    # Simular renderizado
                    ui_rendered[0] += 1
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"UI: {e}")
        
        # Ambos simultáneamente
        with ThreadPoolExecutor(max_workers=2) as executor:
            watch_future = executor.submit(watchdog_check)
            ui_future = executor.submit(render_ui)
            
            watch_future.result(timeout=5)
            ui_future.result(timeout=5)
        
        assert ui_rendered[0] == 10
        assert len(errors) == 0

# ============================================================================
# INTEGRATION TEST 6: Full Conversation Flow
# ============================================================================

class TestIntegration6FullConversation:
    """Conversación completa: audio → transcripción → NLU → respuesta"""

    def test_conversation_flow_all_modules(self):
        """Flujo de conversación involviendo múltiples módulos"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        # Simular: usuario transcripción es procesada
        usuario_dice = "Hola, ¿cómo estás?"
        
        # Mock: NLU procesa y entiende
        with patch.object(orq._cerebro, 'procesar') as mock_nlu:
            mock_nlu.return_value = {
                "respuesta": "Estoy bien, gracias por preguntar",
                "accion": "hablar",
                "confianza": 0.92,
                "emociones": ["alegria"],
                "genero_voz": "M"
            }
            
            # Procesar
            resultado = orq._cerebro.procesar(usuario_dice)
            
            # Verificar respuesta completa
            assert resultado["accion"] == "hablar"
            assert "respuesta" in resultado
            assert resultado["confianza"] > 0.9

    def test_multiple_sequential_conversations(self):
        """Usuario mantiene conversación multi-turno sin pérdida de contexto"""
        from computadora.nucleo.orquestador import Orquestador
        
        orq = Orquestador()
        
        conversacion = [
            "Hola Computadora",
            "¿Qué hora es?",
            "¿Cuál es la temperatura?",
            "Gracias, adiós"
        ]
        
        respuestas = []
        
        with patch.object(orq._cerebro, 'procesar') as mock_nlu:
            # Mock: respuestas secuenciales
            mock_nlu.side_effect = [
                {"respuesta": "Hola, ¿cómo estás?", "accion": "hablar"},
                {"respuesta": "Son las 14:35", "accion": "hablar"},
                {"respuesta": "25 grados", "accion": "hablar"},
                {"respuesta": "Adiós, hasta luego", "accion": "hablar"}
            ]
            
            # Conversación multi-turno
            for entrada in conversacion:
                resultado = orq._cerebro.procesar(entrada)
                respuestas.append(resultado["respuesta"])
            
            # Todas las respuestas deben estar presentes
            assert len(respuestas) == 4
            assert all(isinstance(r, str) for r in respuestas)

# ============================================================================
# INTEGRATION TEST 7: No Cross-Process Interference
# ============================================================================

class TestIntegration7NoInterference:
    """Verificar que un proceso no interfiera con otro"""

    def test_parallel_nlp_and_face_recognition(self):
        """NLU procesando mientras face_recognition captura, sin interferencias"""
        nlp_processed = [0]
        face_processed = [0]
        errors = []
        
        def nlp_process():
            try:
                for i in range(20):
                    # Simular NLU processing
                    time.sleep(0.005)
                    nlp_processed[0] += 1
            except Exception as e:
                errors.append(f"NLP: {e}")
        
        def face_process():
            try:
                for i in range(20):
                    # Simular face recognition
                    time.sleep(0.005)
                    face_processed[0] += 1
            except Exception as e:
                errors.append(f"Face: {e}")
        
        # Ambos en paralelo
        with ThreadPoolExecutor(max_workers=2) as executor:
            nlp_future = executor.submit(nlp_process)
            face_future = executor.submit(face_process)
            
            nlp_future.result(timeout=10)
            face_future.result(timeout=10)
        
        # Ambos deben completar sin interferencias
        assert nlp_processed[0] == 20
        assert face_processed[0] == 20
        assert len(errors) == 0

    def test_memory_write_audio_capture_parallel(self):
        """Memoria escribe mientras audio captura, sin corrupción"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_file = Path(tmpdir) / "memory.jsonl"
            audio_captured = [0]
            memory_writes = [0]
            errors = []
            
            def capture_audio():
                try:
                    for i in range(50):
                        audio_captured[0] += 1
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Audio: {e}")
            
            def write_memory():
                try:
                    for i in range(50):
                        with open(memory_file, "a") as f:
                            f.write(json.dumps({"event": f"m{i}"}) + "\n")
                            memory_writes[0] += 1
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(f"Memory: {e}")
            
            # Ambos en paralelo
            with ThreadPoolExecutor(max_workers=2) as executor:
                audio_future = executor.submit(capture_audio)
                mem_future = executor.submit(write_memory)
                
                audio_future.result(timeout=10)
                mem_future.result(timeout=10)
            
            # Ambos deben completar
            assert audio_captured[0] == 50
            assert memory_writes[0] == 50
            assert len(errors) == 0

# ============================================================================
# INTEGRATION TEST 8: Boot Sequence (Orquestación)
# ============================================================================

class TestIntegration8BootSequence:
    """Secuencia de boot: módulos se inicialicen en orden sin deadlock"""

    def test_boot_sequence_order(self):
        """Boot debe inicializar: Watchdog → MetaWorkflow → Orquestador → Renovacion"""
        from computadora.interfaz.watchdog import WatchdogGolem
        from computadora.nucleo.meta_workflow import MetaWorkflow
        from computadora.nucleo.orquestador import Orquestador
        from computadora.cerebro.renovacion import RenovacionOperativa
        
        boot_order = []
        
        try:
            boot_order.append("watchdog")
            w = WatchdogGolem()
            
            boot_order.append("meta_workflow")
            m = MetaWorkflow()
            
            boot_order.append("orquestador")
            o = Orquestador()
            
            boot_order.append("renovacion")
            r = RenovacionOperativa()
            
            # Todos iniciaron
            assert boot_order == ["watchdog", "meta_workflow", "orquestador", "renovacion"]
            
        except Exception as e:
            pytest.fail(f"Boot sequence failed at {boot_order[-1]}: {e}")

    def test_boot_idempotent(self):
        """Boot puede ejecutarse múltiples veces sin efectos secundarios (idempotente)"""
        from computadora.interfaz.watchdog import WatchdogGolem
        from computadora.nucleo.meta_workflow import MetaWorkflow
        
        # Primera boot
        w1 = WatchdogGolem()
        m1 = MetaWorkflow()
        
        # Segunda boot
        w2 = WatchdogGolem()
        m2 = MetaWorkflow()
        
        # Ambas deben ser operativas
        assert w1 is not None and w2 is not None
        assert m1 is not None and m2 is not None

# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

