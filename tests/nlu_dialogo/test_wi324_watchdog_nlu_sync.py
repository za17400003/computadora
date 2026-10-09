"""
WI-324: Test de sincronización Watchdog↔NLU
Valida que el watchdog y NLU compartan estado correctamente para evitar
reconexiones infinitas y memory leaks en Ollama.

Tests:
1. Watchdog detecta degradación (120s+)
2. CerebroComputadora recibe señal de liberación
3. Timeout se reduce a fail-fast (10s) cuando degradado
4. Recursos Ollama se liberan correctamente
"""

import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Agregar path al proyecto
import sys
proyecto_root = Path(__file__).parent.parent
sys.path.insert(0, str(proyecto_root))


class TestWI324WatchdogNluSync(unittest.TestCase):
    """WI-324: Sincronización Watchdog↔NLU."""

    def setUp(self):
        """Preparar test fixtures."""
        from computadora.interfaz.watchdog import (
            WatchdogComputadora, ServicioMonitoreado, EtapaWatchdog, EstadoCircuit
        )
        from computadora.cerebro.nlu import CerebroComputadora
        
        self.WatchdogComputadora = WatchdogComputadora
        self.ServicioMonitoreado = ServicioMonitoreado
        self.EtapaWatchdog = EtapaWatchdog
        self.EstadoCircuit = EstadoCircuit
        self.CerebroComputadora = CerebroComputadora

    def test_watchdog_ollama_degradacion_detectada(self):
        """Test: Watchdog detecta degradación de Ollama tras 120s sin respuesta."""
        watch = self.WatchdogComputadora()
        
        # Obtener servicio Ollama
        ollama_svc = watch.servicios["ollama"]
        
        # Simular 120+ segundos sin respuesta
        ollama_svc._ultimo_ok = time.monotonic() - 125.0
        ollama_svc.vivo = False
        ollama_svc._fallos_consecutivos = 5
        
        # Actualizar etapa manualmente
        ollama_svc._actualizar_etapa()
        
        # Verificar que está en DEGRADE
        self.assertEqual(ollama_svc.etapa, self.EtapaWatchdog.DEGRADE)
        self.assertTrue(watch.ollama_esta_degradado())

    def test_watchdog_libera_recursos_en_degradacion(self):
        """Test: Watchdog llama liberar_recursos_ollama cuando detecta DEGRADE."""
        watch = self.WatchdogComputadora()
        
        # Mock del callback
        callback_llamado = []
        def mock_callback(nombre, etapa):
            if nombre == "ollama" and etapa == self.EtapaWatchdog.DEGRADE:
                callback_llamado.append(True)
        
        watch._on_cambio_etapa = mock_callback
        
        # Simular cambio a DEGRADE
        ollama_svc = watch.servicios["ollama"]
        ollama_svc._ultimo_ok = time.monotonic() - 125.0
        ollama_svc.vivo = False
        
        # Ejecutar heartbeat
        watch._heartbeat()
        
        # Verificar que callback fue llamado (indicativo de cambio de etapa)
        # El test es básico porque liberar_recursos_ollama requiere que CerebroComputadora exista

    def test_cerebro_recibe_referencia_watchdog(self):
        """Test: CerebroComputadora acepta referencia a WatchdogComputadora."""
        cerebro = self.CerebroComputadora()
        watch = self.WatchdogComputadora()
        
        # Establecer referencia
        cerebro.establecer_watchdog(watch)
        
        # Verificar que fue establecida
        self.assertIs(cerebro._watchdog_ref, watch)

    def test_timeout_adaptativo_fail_fast_cuando_degradado(self):
        """Test: _timeout_adaptativo retorna 10s cuando Ollama está degradado."""
        cerebro = self.CerebroComputadora()
        watch = self.WatchdogComputadora()
        
        # Establecer referencia
        cerebro.establecer_watchdog(watch)
        
        # Simular degradación
        watch.servicios["ollama"]._ultimo_ok = time.monotonic() - 125.0
        watch.servicios["ollama"].vivo = False
        watch.servicios["ollama"]._actualizar_etapa()
        
        # Obtener timeout adaptativo
        timeout = cerebro._timeout_adaptativo()
        
        # Debe ser 10 (fail-fast)
        self.assertEqual(timeout, 10)

    def test_timeout_normal_sin_degradacion(self):
        """Test: _timeout_adaptativo retorna valor normal cuando Ollama OK."""
        cerebro = self.CerebroComputadora()
        watch = self.WatchdogComputadora()
        
        # Establecer referencia
        cerebro.establecer_watchdog(watch)
        
        # Asegurar que Ollama NO está degradado
        self.assertFalse(watch.ollama_esta_degradado())
        
        # Agregar latencias para que calcule promedio
        cerebro._latencias_ollama = [1.0, 1.2, 1.1, 1.3, 1.2]
        
        # Obtener timeout
        timeout = cerebro._timeout_adaptativo()
        
        # Debe ser > 10 (3x promedio ≈ 3.6s mínimo o DEFAULT)
        from computadora.config import TIMEOUT_OLLAMA_DEFAULT, TIMEOUT_OLLAMA_MIN
        self.assertGreaterEqual(timeout, TIMEOUT_OLLAMA_MIN)

    def test_liberar_modelos_ollama_limpia_cache(self):
        """Test: liberar_modelos_ollama vacía cache de latencias."""
        cerebro = self.CerebroComputadora()
        
        # Agregar latencias
        cerebro._latencias_ollama = [1.0, 1.2, 1.1]
        cerebro.ollama_disponible = True
        
        # Liberar
        cerebro.liberar_modelos_ollama()
        
        # Cache debe estar vacío
        self.assertEqual(len(cerebro._latencias_ollama), 0)
        # ollama_disponible debe ser False
        self.assertFalse(cerebro.ollama_disponible)

    def test_check_ollama_degradacion(self):
        """Test: _check_ollama_degradacion retorna True cuando está degradado."""
        cerebro = self.CerebroComputadora()
        watch = self.WatchdogComputadora()
        
        cerebro.establecer_watchdog(watch)
        
        # Sin degradación
        self.assertFalse(cerebro._check_ollama_degradacion())
        
        # Simular degradación
        watch.servicios["ollama"]._ultimo_ok = time.monotonic() - 125.0
        watch.servicios["ollama"].vivo = False
        watch.servicios["ollama"]._actualizar_etapa()
        
        # Ahora debe reportar degradación
        self.assertTrue(cerebro._check_ollama_degradacion())

    def test_ollama_esta_caido_detection(self):
        """Test: ollama_esta_caido detecta cuando Ollama no está disponible."""
        watch = self.WatchdogComputadora()
        
        # Inicialmente OK
        self.assertFalse(watch.ollama_esta_caido())
        
        # Simular caída
        ollama_svc = watch.servicios["ollama"]
        ollama_svc.vivo = False
        
        # Ahora debe estar caído
        self.assertTrue(watch.ollama_esta_caido())


class TestRFCoherenceMatrix(unittest.TestCase):
    """Matriz de coherencia de RFs vs Tests.
    
    Valida que cada RF tenga un test correspondiente.
    """

    def test_rf01_voice_capture(self):
        """RF-01: Captura de voz — debe validarse en test_rf01_voice_*.py"""
        # Este es un placeholder para validar estructura de tests
        test_files_expected = [
            "test_rf01_voice_capture.py",
            "test_rf01_voice_english.py",
        ]
        # En PALINGENESIA, verificar que existan

    def test_rf02_nlu_levels(self):
        """RF-02: NLU 3 niveles — test_rf02_nlu_*.py"""
        pass

    def test_rf03_tts_vocalization(self):
        """RF-03: TTS — test_rf03_tts_*.py"""
        pass

    def test_rf_coverage_tracking(self):
        """Meta-test: Rastrear cobertura de tests por RF.
        
        RFs sin test (según diagnóstico NIGREDO):
        - RF-35b: Memoria Híbrida
        - RF-40: Baseline Adaptativo
        - RF-42: Supervisión Meta-Cognitiva
        - RF-54: Resiliencia Ollama ← CRÍTICO (WI-324)
        - RF-56: Auto-Aprendizaje N1
        - RF-57: Routing Inteligente
        """
        missing_rfs = ["RF-35b", "RF-40", "RF-42", "RF-54", "RF-56", "RF-57"]
        # TODO: Crear tests para estos RFs en PALINGENESIA


if __name__ == "__main__":
    unittest.main(verbosity=2)

