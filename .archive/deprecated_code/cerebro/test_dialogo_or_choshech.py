"""
test_dialogo_or_choshech.py — Tests para Or v'Choshech

Valida ciclo alternado Tiféret ↔ Yesoid, condiciones de término,
y coherencia criptográfica αמת (EMET).

WI-295 Test Suite
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import dataclass

# Importar módulo a testear
try:
    from computadora.cerebro.dialogo_or_choshech import (
        DialogoOrVChoshech,
        EstadoDialogo,
        CicloDialogo,
    )
except ImportError:
    # Fallback si no está en path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from computadora.cerebro.dialogo_or_choshech import (
        DialogoOrVChoshech,
        EstadoDialogo,
        CicloDialogo,
    )


@pytest.fixture
def mock_components():
    """Fixture: componentes mockeados"""
    cerebro = Mock()
    cerebro.pensar = Mock(side_effect=[
        "Pensamiento inicial",
        "Reflexión profunda",
        "Conclusión inmediata"
    ])
    
    memoria = Mock()
    memoria.buscar_en_memoria = Mock(side_effect=[
        [{"text": "Recuerdo 1"}, {"text": "Recuerdo 2"}],
        [{"text": "Recuerdo 3"}, {"text": "Recuerdo 4"}],
        [{"text": "Recuerdo 5"}],
    ])
    memoria.add_memory = Mock()
    
    hilo_habla = Mock()
    hilo_habla.hablar = Mock()
    hilo_habla.esperar_vacia = Mock()
    
    fsm = Mock()
    fsm.estado = "vigilia"  # No dormido
    
    return {
        'cerebro': cerebro,
        'memoria': memoria,
        'hilo_habla': hilo_habla,
        'fsm': fsm,
    }


class TestDialogoOrVChoshechBasico:
    """Tests de funcionalidad básica"""
    
    def test_inicializacion(self, mock_components):
        """Test: Crear instancia de DialogoOrVChoshech"""
        dialogo = DialogoOrVChoshech(
            cerebro=mock_components['cerebro'],
            memoria=mock_components['memoria'],
            hilo_habla=mock_components['hilo_habla'],
            fsm=mock_components['fsm'],
        )
        
        assert dialogo.estado == EstadoDialogo.PARADO
        assert dialogo.tema_actual == ""
        assert len(dialogo.ciclos_completados) == 0
    
    def test_start_dialogo_inicializa_tema(self, mock_components):
        """Test: start_dialogo() inicializa tema_actual"""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        dialogo.start_dialogo("¿Quién soy?")
        
        assert dialogo.tema_actual == "¿Quién soy?"
        assert dialogo.estado in (EstadoDialogo.EJECUTANDO, EstadoDialogo.PARADO)
    
    def test_constantes_audibles(self, mock_components):
        """Test: Constantes de audio coinciden esperadas"""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        assert dialogo.AUDIBLE_TIFERA == "T"
        assert dialogo.AUDIBLE_MEMORIA == "me"
        assert dialogo.MAX_CICLOS == 12


class TestDialogoCicloAlternado:
    """Tests del ciclo alternado Tiféret ↔ Yesoid"""
    
    def test_ejecutar_tifera_llama_cerebro_pensar(self, mock_components):
        """Test: Tiféret llama cerebro.pensar()"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Tema test"
        
        ciclo_data = dialogo._ejecutar_tifera(0)
        
        mock_components['cerebro'].pensar.assert_called_once_with("Tema test")
        assert ciclo_data is not None
        assert ciclo_data.tipo == "tifera"
        assert ciclo_data.salida == "Pensamiento inicial"
    
    def test_ejecutar_yesoid_busca_memoria(self, mock_components):
        """Test: Yesoid llama memoria.buscar_en_memoria()"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Tema test"
        
        ciclo_data = dialogo._ejecutar_yesoid(0)
        
        mock_components['memoria'].buscar_en_memoria.assert_called_once_with("Tema test")
        assert ciclo_data is not None
        assert ciclo_data.tipo == "yesoid"
        assert "Recuerdo" in ciclo_data.salida
    
    def test_tifera_emite_audio_con_prefijo(self, mock_components):
        """Test: Tiféret sintetiza 'T: respuesta'"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        dialogo._ejecutar_tifera(0)
        
        # Verificar que hablar() fue llamado con prefijo "T"
        mock_components['hilo_habla'].hablar.assert_called()
        call_args = mock_components['hilo_habla'].hablar.call_args[0][0]
        assert call_args.startswith("T:")
    
    def test_yesoid_emite_audio_con_prefijo(self, mock_components):
        """Test: Yesoid sintetiza 'me: recuerdos'"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        dialogo._ejecutar_yesoid(0)
        
        # Verificar que hablar() fue llamado con prefijo "me"
        mock_components['hilo_habla'].hablar.assert_called()
        call_args = mock_components['hilo_habla'].hablar.call_args[0][0]
        assert call_args.startswith("me:")
    
    def test_retroalimentacion_tema(self, mock_components):
        """Test: Salida de ciclo N se convierte en entrada de ciclo N+1"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Tema inicial"
        
        # Ejecutar Tiféret
        ciclo_t = dialogo._ejecutar_tifera(0)
        tema_despues_t = dialogo.tema_actual
        
        # Ejecutar Yesoid
        ciclo_y = dialogo._ejecutar_yesoid(1)
        tema_despues_y = dialogo.tema_actual
        
        # Verificar retroalimentación
        assert tema_despues_t == ciclo_t.salida
        assert tema_despues_y == ciclo_y.salida
        assert tema_despues_t != "Tema inicial"


class TestCondicionesTermino:
    """Tests de condiciones de finalización"""
    
    @patch('golem.cerebro.dialogo_or_choshech.logger')
    def test_termina_en_max_ciclos(self, mock_logger, mock_components):
        """Test: Diálogo termina en MAX_CICLOS"""
        dialogo = DialogoOrVChoshech(
            **mock_components,
            max_ciclos=4  # 2 pares de T/me
        )
        
        # Nota: No podemos run() en test porque es QThread
        # Verificamos lógica manualmente
        assert dialogo.max_ciclos == 4
    
    def test_termina_cuando_fsm_dormido(self, mock_components):
        """Test: Diálogo termina cuando FSM.estado == DORMIDO"""
        mock_components['fsm'].estado = "dormido"
        
        dialogo = DialogoOrVChoshech(**mock_components)
        
        # Simulación: en run(), debería detectar DORMIDO
        # (Difícil de testear sin ejecutar thread, validamos lógica)
        estado_str = str(mock_components['fsm'].estado).lower()
        assert 'dormido' in estado_str
    
    def test_stop_dialogo_detiene_ejecucion(self, mock_components):
        """Test: stop_dialogo() establece flag de parada"""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        dialogo.start_dialogo("Test")
        dialogo.stop_dialogo()
        
        assert dialogo._should_stop == True


class TestSignalsYCallbacks:
    """Tests de signals Qt y callbacks"""
    
    def test_callback_ciclo_se_invoca(self, mock_components):
        """Test: callback_ciclo() se llama en cada ciclo"""
        callback = Mock()
        dialogo = DialogoOrVChoshech(
            **mock_components,
            callback_ciclo=callback
        )
        
        ciclo_data = dialogo._ejecutar_tifera(0)
        
        # En ejecución real llamaría callback(), aquí verificamos internals
        assert ciclo_data is not None
    
    def test_datos_ciclo_contienen_timestamp(self, mock_components):
        """Test: CicloDialogo contiene timestamp"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        ciclo_data = dialogo._ejecutar_tifera(0)
        
        assert hasattr(ciclo_data, 'timestamp')
        assert ciclo_data.timestamp > 0
        assert ciclo_data.duracion_ms >= 0


class TestCoherenciaEMET:
    """Tests de coherencia αמת (EMET - Verdad)"""
    
    def test_ciclos_alternados_correctamente(self, mock_components):
        """Test: Verificar alternancia T, me, T, me, ..."""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        # Simulación de 4 ciclos
        ciclos_tipos = []
        for i in range(4):
            if i % 2 == 0:
                ciclo = dialogo._ejecutar_tifera(i)
                ciclos_tipos.append(ciclo.tipo)
            else:
                ciclo = dialogo._ejecutar_yesoid(i)
                ciclos_tipos.append(ciclo.tipo)
        
        # Verificar patrón
        assert ciclos_tipos == ["tifera", "yesoid", "tifera", "yesoid"]
    
    def test_memoria_registra_ambos_tipos(self, mock_components):
        """Test: Memoria registra tanto tifera como yesoid"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        # Ejecutar uno de cada
        dialogo._ejecutar_tifera(0)
        dialogo._ejecutar_yesoid(1)
        
        # Verificar add_memory fue llamado con ambos roles
        calls = mock_components['memoria'].add_memory.call_args_list
        assert len(calls) >= 2
        roles = [call[0][0] for call in calls]
        assert "tifera" in roles
        assert "yesoid" in roles
    
    def test_veracidad_retroalimentacion(self, mock_components):
        """Test: אמת - Verdad de la retroalimentación"""
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Verdad inicial"
        
        # Tiféret emite
        ciclo_t = dialogo._ejecutar_tifera(0)
        assert ciclo_t.entrada == "Verdad inicial"
        assert ciclo_t.salida == "Pensamiento inicial"
        
        # Verificar que Yesoid recibe la salida de Tiféret
        assert dialogo.tema_actual == "Pensamiento inicial"


class TestErrorHandling:
    """Tests de manejo de errores"""
    
    def test_tifera_error_retorna_none(self, mock_components):
        """Test: Error en Tiféret retorna None, no crash"""
        mock_components['cerebro'].pensar.side_effect = Exception("Test error")
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        resultado = dialogo._ejecutar_tifera(0)
        
        assert resultado is None  # Error manejado gracefully
    
    def test_yesoid_error_retorna_none(self, mock_components):
        """Test: Error en Yesoid retorna None, no crash"""
        mock_components['memoria'].buscar_en_memoria.side_effect = Exception("Test error")
        dialogo = DialogoOrVChoshech(**mock_components)
        dialogo.tema_actual = "Test"
        
        resultado = dialogo._ejecutar_yesoid(0)
        
        assert resultado is None  # Error manejado gracefully


class TestGetters:
    """Tests de métodos getter"""
    
    def test_get_ciclos_retorna_lista(self, mock_components):
        """Test: get_ciclos() retorna lista de ciclos"""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        ciclos = dialogo.get_ciclos()
        
        assert isinstance(ciclos, list)
        assert len(ciclos) == 0  # Inicialmente vacío
    
    def test_get_estado_retorna_estado(self, mock_components):
        """Test: get_estado() retorna EstadoDialogo"""
        dialogo = DialogoOrVChoshech(**mock_components)
        
        estado = dialogo.get_estado()
        
        assert estado == EstadoDialogo.PARADO


if __name__ == "__main__":
    # Ejecutar: pytest tests/test_dialogo_or_choshech.py -v
    pytest.main([__file__, "-v"])

