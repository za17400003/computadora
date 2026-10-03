"""
tests/test_guardian_manager.py — Tests de GuardianManager (POO Pattern)

Valida:
1. Feature flag bloquea activación (guardian_activo=False)
2. State transitions son válidas (según TRANSICIONES_VALIDAS)
3. Callbacks se invocan en cambios de estado
4. Thread safety con RLock
5. Interfaz pública funciona correctamente
"""

import pytest
import threading
import time
from unittest.mock import Mock, MagicMock

# Asumimos estructura de módulos correcta
from computadora.cerebro.guardian.manager import GuardianManager
from computadora.cerebro.guardian.states import GuardianState


class TestGuardianManagerBasic:
    """Tests básicos de GuardianManager."""
    
    @pytest.fixture
    def mock_cerebro(self):
        """Mock de CerebroComputadora."""
        cerebro = Mock()
        cerebro.on_nivel = None
        cerebro.on_bloqueo_seguridad = None
        return cerebro
    
    @pytest.fixture
    def mock_feature_flags(self):
        """Mock de FeatureFlags."""
        flags = Mock()
        # Nota: guardian_activo=False PERMITE activación, True la BLOQUEA
        flags.obtener = Mock(return_value=False)  # Por defecto permite
        return flags
    
    @pytest.fixture
    def manager(self, mock_cerebro, mock_feature_flags):
        """Instancia de GuardianManager para tests."""
        manager = GuardianManager(mock_cerebro, mock_feature_flags)
        return manager
    
    def test_puede_activar_cuando_flag_true(self, manager, mock_feature_flags):
        """Debe BLOQUEAR cuando guardian_activo=True (No se debe activar)."""
        mock_feature_flags.obtener.return_value = True
        assert manager.puede_activar() is False  # True=bloqueado
    
    def test_puede_activar_cuando_flag_false(self, manager, mock_feature_flags):
        """Debe permitir cuando guardian_activo=False (Se puede activar)."""
        mock_feature_flags.obtener.return_value = False
        assert manager.puede_activar() is True  # False=permitido
    
    def test_estado_inicial_es_inactivo(self, manager):
        """Estado inicial debe ser INACTIVE."""
        assert manager.estado == GuardianState.INACTIVE
        assert manager.activo is False
    
    def test_activar_cuando_permitido(self, manager):
        """Debe activar cuando feature flag permite."""
        resultado = manager.activar(razon="test", origen="test")
        assert resultado is True
        assert manager.estado == GuardianState.ACTIVE
        assert manager.activo is True
    
    def test_activar_cuando_bloqueado(self, manager, mock_feature_flags):
        """Debe BLOQUEAR activación cuando feature flag=True (No se debe activar)."""
        mock_feature_flags.obtener.return_value = True  # True = bloquea
        resultado = manager.activar(razon="test", origen="test")
        assert resultado is False
        assert manager.estado == GuardianState.INACTIVE
        assert manager.activo is False
    
    def test_desactivar_cuando_activo(self, manager):
        """Debe desactivar cuando está activo."""
        manager.activar(razon="test", origen="test")
        resultado = manager.desactivar(razon="test", origen="test")
        assert resultado is True
        assert manager.estado == GuardianState.INACTIVE
        assert manager.activo is False
    
    def test_desactivar_cuando_inactivo(self, manager):
        """Desactivar en estado INACTIVE debe retornar False."""
        resultado = manager.desactivar(razon="test", origen="test")
        assert resultado is False  # Ya inactivo
        assert manager.estado == GuardianState.INACTIVE
    
    def test_callback_invocado_en_cambio_estado(self, manager):
        """Callbacks deben ser invocados en cambios de estado."""
        callback = Mock()
        manager.registrar_callback_state_change(callback)
        
        manager.activar(razon="test", origen="test")
        
        # Callback debería ser invocado con GuardianStateChangeEvent
        assert callback.called
        event = callback.call_args[0][0]
        assert event.estado_anterior == GuardianState.INACTIVE
        assert event.estado_nuevo == GuardianState.ACTIVE
        assert event.razon == "test"
        assert event.origen == "test"
    
    def test_multiples_callbacks(self, manager):
        """Múltiples callbacks deben todos ser invocados."""
        callback1 = Mock()
        callback2 = Mock()
        manager.registrar_callback_state_change(callback1)
        manager.registrar_callback_state_change(callback2)
        
        manager.activar(razon="test", origen="test")
        
        assert callback1.called
        assert callback2.called


class TestGuardianManagerStateTransitions:
    """Tests de transiciones de estado."""
    
    @pytest.fixture
    def manager(self):
        """Manager para tests de transiciones."""
        cerebro = Mock()
        flags = Mock()
        # False = permite activación
        flags.obtener = Mock(return_value=False)
        return GuardianManager(cerebro, flags)
    
    def test_transicion_inactive_a_active(self, manager):
        """INACTIVE → ACTIVE es válido."""
        manager.activar(razon="test", origen="test")
        assert manager.estado == GuardianState.ACTIVE
    
    def test_transicion_active_a_inactive(self, manager):
        """ACTIVE → INACTIVE es válido."""
        manager.activar(razon="test", origen="test")
        manager.desactivar(razon="test", origen="test")
        assert manager.estado == GuardianState.INACTIVE
    
    def test_transicion_invalida_detectada(self, manager):
        """Transiciones inválidas deben ser detectadas."""
        # Activar
        manager.activar(razon="test", origen="test")
        assert manager.estado == GuardianState.ACTIVE
        
        # Intentar activar de nuevo (debe fallar o no hacer nada)
        result = manager.activar(razon="test", origen="test")
        # Ya activo, no debe volver a "activar"
        assert manager.estado == GuardianState.ACTIVE


class TestGuardianManagerThreadSafety:
    """Tests de thread safety con RLock."""
    
    def test_concurrent_activations(self):
        """Múltiples threads no deben causar race conditions."""
        cerebro = Mock()
        flags = Mock()
        # False = permite activación
        flags.obtener = Mock(return_value=False)
        manager = GuardianManager(cerebro, flags)
        
        results = []
        
        def activate():
            result = manager.activar(razon="concurrent", origen="thread")
            results.append(result)
        
        threads = [threading.Thread(target=activate) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Debe haber estado bien coordinado (sin crashes)
        assert len(results) == 5
        # Al menos uno debe ser True (primer activador)
        assert any(results)
    
    def test_concurrent_reads_safe(self):
        """Múltiples threads leyendo estado no debe causar crashes."""
        cerebro = Mock()
        flags = Mock()
        # False = permite activación
        flags.obtener = Mock(return_value=False)
        manager = GuardianManager(cerebro, flags)
        manager.activar(razon="test", origen="test")
        
        states = []
        
        def read_state():
            state = manager.activo
            states.append(state)
        
        threads = [threading.Thread(target=read_state) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Todos debieron leer True (activo)
        assert len(states) == 10
        assert all(states)


class TestGuardianManagerIntegration:
    """Tests de integración con FeatureFlags."""
    
    def test_feature_flag_bloquea_activacion(self):
        """Feature flag guardian_activo=True debe bloquear completamente."""
        cerebro = Mock()
        flags = Mock()
        flags.obtener = Mock(return_value=True)  # True = bloquea
        
        manager = GuardianManager(cerebro, flags)
        
        # Debe bloquear activación
        result = manager.activar(razon="test", origen="test")
        assert result is False
        assert manager.estado == GuardianState.INACTIVE
    
    def test_feature_flag_permite_activacion(self):
        """Feature flag guardian_activo=False debe permitir."""
        cerebro = Mock()
        flags = Mock()
        flags.obtener = Mock(return_value=False)  # False = permite
        
        manager = GuardianManager(cerebro, flags)
        
        result = manager.activar(razon="test", origen="test")
        assert result is True
        assert manager.estado == GuardianState.ACTIVE


@pytest.mark.parametrize("razon,origen", [
    ("test", "test"),
    ("bloqueo_sesion_windows", "session_lock_listener"),
    ("usuario_solicitud", "procesar"),
    ("flujos_guardian", "_activar_guardian"),
])
def test_razon_y_origen_registrados(razon, origen):
    """Razon y origen deben ser registrados en eventos."""
    cerebro = Mock()
    flags = Mock()
    # False = permite activación (para que el callback sea invocado)
    flags.obtener = Mock(return_value=False)
    manager = GuardianManager(cerebro, flags)
    
    callback = Mock()
    manager.registrar_callback_state_change(callback)
    
    manager.activar(razon=razon, origen=origen)
    
    event = callback.call_args[0][0]
    assert event.razon == razon
    assert event.origen == origen


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

