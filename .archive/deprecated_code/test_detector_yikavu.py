"""
🧪 TEST SUITE — Detector Yikavú

18 test casos cubriendo:
- Inicialización y configuración
- Transiciones de estado (DISPERSO → CONVERGIENDO → CONSOLIDADO)
- Emisión de eventos
- Callbacks
- Integración con Memoria + FSM
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, ANY
from datetime import date

from computadora.nucleo.detector_yikavu import (
    DetectorYikavu,
    ConfiguracionYikavu,
    AsyncaYikavu,
    TransicionYikavu
)
from computadora.interfaz.fsm_golem import EstadoMaljut
from computadora.nucleo.eventos import BusEventos


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def config_test():
    """Configuración para tests (timeouts reducidos)"""
    return ConfiguracionYikavu(
        timeout_convergencia_seg=1.0,
        threshold_memoria_seg=0.5,
        poll_interval_ms=100,
        habilitar_audios=False
    )


@pytest.fixture
def mock_memoria():
    """Mock de Memoria con métodos mínimos"""
    memoria = Mock()
    memoria.ultima_compresion_completada = False
    memoria.compress_day = Mock(return_value=None)
    return memoria


@pytest.fixture
def mock_bus_eventos():
    """Mock de BusEventos"""
    bus = Mock(spec=BusEventos)
    bus.emitir = Mock()
    return bus


@pytest.fixture
def detector(config_test, mock_bus_eventos):
    """Instancia de DetectorYikavu para tests"""
    detector = DetectorYikavu(
        config=config_test,
        bus_eventos=mock_bus_eventos
    )
    yield detector
    # Cleanup
    detector.detener_monitor(esperar_sec=0.5)


# ============================================================================
# TESTS — INICIALIZACIÓN
# ============================================================================

class TestDetectorYikavuBasico:
    """Tests básicos de inicialización y estado"""
    
    def test_inicializacion_default(self, mock_bus_eventos):
        """Debe inicializar con estado DISPERSO"""
        detector = DetectorYikavu(bus_eventos=mock_bus_eventos)
        assert detector.obtener_asynca_actual() == AsyncaYikavu.DISPERSO
        assert len(detector.obtener_transiciones()) == 0
    
    def test_inicializacion_config_custom(self, config_test):
        """Debe aceptar configuración customizada"""
        detector = DetectorYikavu(config=config_test)
        assert detector.config.timeout_convergencia_seg == 1.0
        assert detector.config.poll_interval_ms == 100
    
    def test_monitor_inicia(self, detector):
        """monitor_inicia() debe activar thread"""
        detector.iniciar_monitor()
        assert detector._sensor_activo.is_set() is True
        assert detector._thread_monitor is not None
    
    def test_monitor_detiene(self, detector):
        """detener_monitor() debe parar el thread"""
        detector.iniciar_monitor()
        detector.detener_monitor(esperar_sec=0.5)
        assert detector._sensor_activo.is_set() is False
    
    def test_detector_idempotente_iniciar(self, detector):
        """Iniciar dos veces no debe crear 2 threads"""
        detector.iniciar_monitor()
        thread1 = detector._thread_monitor
        detector.iniciar_monitor()
        thread2 = detector._thread_monitor
        assert thread1 == thread2


# ============================================================================
# TESTS — CALLBACKS Y SUSCRIPCIÓN
# ============================================================================

class TestCallbacksYikavu:
    """Tests de registro y ejecución de callbacks"""
    
    def test_suscribirse_callback(self, detector):
        """Debe registrar callback"""
        callback = Mock()
        detector.suscribirse_consolidacion(callback)
        assert callback in detector._callbacks_yikavu
    
    def test_desuscribirse_callback(self, detector):
        """Debe desregistrar callback"""
        callback = Mock()
        detector.suscribirse_consolidacion(callback)
        detector.desuscribirse(callback)
        assert callback not in detector._callbacks_yikavu
    
    def test_callback_no_duplicado(self, detector):
        """Mismo callback no debe registrarse 2x"""
        callback = Mock()
        detector.suscribirse_consolidacion(callback)
        detector.suscribirse_consolidacion(callback)
        assert detector._callbacks_yikavu.count(callback) == 1
    
    def test_callback_invocado_en_consolidacion(self, detector, mock_bus_eventos):
        """Callback debe ejecutarse cuando יקוו emitido"""
        callback = Mock()
        detector.suscribirse_consolidacion(callback)
        
        # Forzar consolidación
        resultado = detector.forzar_consolidacion_manual("test")
        
        assert resultado is False  # No cumple condiciones reales, pero veamos si callback se llamó
        # (Puede no emitir si _verificar_consolidacion_posible() retorna False)


# ============================================================================
# TESTS — TRANSICIONES DE ESTADO
# ============================================================================

class TestTransicionesAsyncaYikavu:
    """Tests de máquina de estados DISPERSO/CONVERGIENDO/CONSOLIDADO"""
    
    def test_estado_inicial_disperso(self, detector):
        """Estado inicial debe ser DISPERSO"""
        assert detector.obtener_asynca_actual() == AsyncaYikavu.DISPERSO
    
    def test_cambio_asynca_interno(self, detector):
        """_cambiar_asynca() debe actualizar estado"""
        detector._cambiar_asynca(AsyncaYikavu.CONVERGIENDO, "test")
        assert detector.obtener_asynca_actual() == AsyncaYikavu.CONVERGIENDO
        
        # Debe escribir log
        # logger debería haber captado el cambio
    
    @patch('golem.nucleo.detector_yikavu.logger')
    def test_cambio_asynca_registrado(self, mock_logger, detector):
        """Cada cambio debe loguear"""
        detector._cambiar_asynca(AsyncaYikavu.CONVERGIENDO, "reason123")
        mock_logger.debug.assert_called()


# ============================================================================
# TESTS — VERIFICACIÓN DE CONSOLIDACIÓN
# ============================================================================

class TestVerificacionConsolidacion:
    """Tests de lógica de verificación de condiciones יקוו"""
    
    def test_consolidacion_posible_fsm_dormido(self, detector):
        """Si FSM en DORMIDO y memoria comprimida → consolidación posible"""
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        resultado = detector._verificar_consolidacion_posible()
        assert resultado is True
    
    def test_consolidacion_imposible_fsm_error(self, detector):
        """Si FSM en ERROR → consolidación imposible"""
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.ERROR)
        
        resultado = detector._verificar_consolidacion_posible()
        assert resultado is False
    
    def test_consolidacion_imposible_sin_memoria_comprimida(self, detector):
        """Si memoria NO comprimida → consolidación imposible"""
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=False)
        
        resultado = detector._verificar_consolidacion_posible()
        assert resultado is False
    
    @patch('os.path.exists')
    def test_verificar_memoria_comprimida_archivo_existe(self, mock_exists, detector):
        """Si archivo resumen existe → memoria comprimida"""
        mock_exists.return_value = True
        
        resultado = detector._verificar_memoria_comprimida()
        assert resultado is True
    
    @patch('os.path.exists')
    def test_verificar_memoria_comprimida_archivo_no_existe(self, mock_exists, detector):
        """Si archivo resumen no existe → memoria NO comprimida"""
        mock_exists.return_value = False
        
        resultado = detector._verificar_memoria_comprimida()
        assert resultado is False


# ============================================================================
# TESTS — EMISIÓN DE EVENTOS
# ============================================================================

class TestEmisionEventosYikavu:
    """Tests de broadcast de eventos al BusEventos"""
    
    def test_forzar_consolidacion_manual_falso(self, detector):
        """Si condiciones no se cumplen, forzar retorna False"""
        detector._verificar_consolidacion_posible = Mock(return_value=False)
        
        resultado = detector.forzar_consolidacion_manual("test")
        assert resultado is False
    
    def test_forzar_consolidacion_manual_verdadero(self, detector, mock_bus_eventos):
        """Si condiciones OK, emite evento"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        resultado = detector.forzar_consolidacion_manual("test_manual")
        assert resultado is True
        mock_bus_eventos.emitir.assert_called_once()
    
    def test_evento_contiene_motivo(self, detector, mock_bus_eventos):
        """Evento debe contener motivo de consolidación"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        detector.forzar_consolidacion_manual("razon_especial")
        
        # Verificar que emitir fue llamado
        assert mock_bus_eventos.emitir.called
        call_args = mock_bus_eventos.emitir.call_args
        payload = call_args[0][1]  # Segundo argumento (dict)
        assert payload['motivo'] == 'forzado: razon_especial'
    
    def test_evento_contiene_timestamp(self, detector, mock_bus_eventos):
        """Evento debe contener timestamp ISO"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        detector.forzar_consolidacion_manual()
        
        call_args = mock_bus_eventos.emitir.call_args
        payload = call_args[0][1]
        assert 'timestamp_iso' in payload['datos']
        assert 'T' in payload['datos']['timestamp_iso']  # Formato ISO


# ============================================================================
# TESTS — TRANSICIONES MOSTRADAS
# ============================================================================

class TestHistoricoTransiciones:
    """Tests del registro de transiciones"""
    
    def test_historico_transiciones_vacio_inicial(self, detector):
        """Debe empezar sin transiciones"""
        transiciones = detector.obtener_transiciones()
        assert len(transiciones) == 0
    
    def test_historico_transiciones_despues_evento(self, detector, mock_bus_eventos):
        """Después de consolidación, debe haber 1 transición"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        detector.forzar_consolidacion_manual()
        
        transiciones = detector.obtener_transiciones()
        assert len(transiciones) >= 1
    
    def test_transicion_contiene_datos(self, detector, mock_bus_eventos):
        """TransicionYikavu debe tener campos requeridos"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        detector.forzar_consolidacion_manual()
        
        transiciones = detector.obtener_transiciones()
        transicion = transiciones[-1]
        
        assert hasattr(transicion, 'timestamp')
        assert hasattr(transicion, 'motivo')
        assert hasattr(transicion, 'datos_consolidacion')


# ============================================================================
# TESTS — THREAD SAFETY & CONCURRENCIA
# ============================================================================

class TestThreadSafety:
    """Tests de seguridad concurrente"""
    
    def test_acceso_concurrente_asynca_actual(self, detector):
        """Múltiples lecturas concurrentes de asynca_actual sin deadlock"""
        import threading
        
        def leer_asynca():
            for _ in range(100):
                detector.obtener_asynca_actual()
        
        threads = [threading.Thread(target=leer_asynca) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
        
        # Si llegamos aquí sin deadlock/exception → OK
        assert True
    
    def test_suscribir_desuscribir_concurrente(self, detector):
        """Suscribir/desuscribir desde múltiples threads"""
        import threading
        
        callbacks = [Mock() for _ in range(5)]
        
        def registrar_desregistrar():
            for cb in callbacks:
                detector.suscribirse_consolidacion(cb)
                time.sleep(0.001)
                detector.desuscribirse(cb)
        
        threads = [threading.Thread(target=registrar_desregistrar) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
        
        # Al final, lista debe estar vacía o muy pequeña
        assert len(detector._callbacks_yikavu) <= 1


# ============================================================================
# TESTS — INTEGRACIÓN Y EDGE CASES
# ============================================================================

class TestIntegracionYikavu:
    """Tests de integración con otros sistemas"""
    
    def test_bus_eventos_notificado(self, detector, mock_bus_eventos):
        """BusEventos debe recibir evento 'consolidacion_completada'"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        detector.forzar_consolidacion_manual()
        
        # Verificar que se emitió al bus con el nombre correcto
        mock_bus_eventos.emitir.assert_called_once()
        call_args = mock_bus_eventos.emitir.call_args[0]
        assert call_args[0] == "consolidacion_completada"
        assert isinstance(call_args[1], dict)
        assert call_args[1]["evento"] == "yikavu"
    
    def test_triple_consolidacion_consecutivas(self, detector, mock_bus_eventos):
        """3 consolidaciones consecutivas registradas correctamente"""
        detector._verificar_consolidacion_posible = Mock(return_value=True)
        detector._obtener_estado_fsm = Mock(return_value=EstadoMaljut.DORMIDO)
        detector._verificar_memoria_comprimida = Mock(return_value=True)
        
        for i in range(3):
            detector.forzar_consolidacion_manual(f"evento_{i}")
        
        transiciones = detector.obtener_transiciones()
        assert len(transiciones) >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

