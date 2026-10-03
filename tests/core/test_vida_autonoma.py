# tests/test_vida_autonoma.py
import pytest
from unittest.mock import Mock
from computadora.interfaz.vida_autonoma import VidaAutonoma, EstadoOrbe
from computadora.metatron import MetatronOrquestador

def test_vida_autonoma_init():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    assert vida.estado_actual == EstadoOrbe.IDLE
    assert vida.metatron == metatron
    assert vida.orbe == orbe_mock

def test_set_animacion_idle():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.IDLE)
    orbe_mock.set_parpadeo_lento.assert_called_once()

def test_set_animacion_atencion():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.ATENCION)
    orbe_mock.set_atencion.assert_called_once()

def test_set_animacion_pensando():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.PENSANDO)
    orbe_mock.set_pulsando.assert_called_once()

def test_set_animacion_hablando():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.HABLANDO)
    orbe_mock.set_resplandeciendo.assert_called_once()

def test_set_animacion_error():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.ERROR)
    orbe_mock.set_error.assert_called_once()

def test_no_animacion_duplicate():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.set_animacion(EstadoOrbe.IDLE)
    vida.set_animacion(EstadoOrbe.IDLE)  # Same state

    # Should only be called once
    orbe_mock.set_parpadeo_lento.assert_called_once()

def test_movimiento_autonomo_idle():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)

    vida.movimiento_autonomo()
    orbe_mock.rotate.assert_called_with(1)
    orbe_mock.scale_variacion.assert_called_with(0.01)

def test_movimiento_autonomo_no_idle():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    vida = VidaAutonoma(metatron, orbe_mock)
    vida.estado_actual = EstadoOrbe.PENSANDO

    vida.movimiento_autonomo()
    orbe_mock.rotate.assert_not_called()
    orbe_mock.scale_variacion.assert_not_called()

def test_check_balance():
    metatron = MetatronOrquestador()
    orbe_mock = Mock()
    orbe_mock.get_fps_actual.return_value = 30
    vida = VidaAutonoma(metatron, orbe_mock)

    result = vida.check_balance()
    assert result == True
    # Check that metric was registered
    assert 'fps_orbe' in metatron.metricas
