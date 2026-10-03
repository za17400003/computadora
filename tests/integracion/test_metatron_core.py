# tests/test_metatron_core.py
import pytest
from computadora.metatron import MetatronOrquestador, EstadoSistema

def test_metatron_initial_state():
    metatron = MetatronOrquestador()
    assert metatron.estado_actual == EstadoSistema.IDLE
    assert metatron.metricas['cpu_usage'] >= 0

def test_metatron_set_state():
    metatron = MetatronOrquestador()
    metatron.set_estado(EstadoSistema.LISTENING)
    assert metatron.estado_actual == EstadoSistema.LISTENING

def test_metatron_registrar_metrica():
    metatron = MetatronOrquestador()
    metatron.registrar_metrica('latencia_whisper', 1.5)
    assert 1.5 in metatron.metricas['latencia_whisper']

def test_metatron_health_check_normal():
    metatron = MetatronOrquestador()
    metatron.registrar_metrica('cpu_usage', 50)
    metatron.registrar_metrica('latencia_whisper', 1.5)
    assert metatron.health_check() == True

def test_metatron_health_check_overload():
    metatron = MetatronOrquestador()
    metatron.registrar_metrica('cpu_usage', 98)
    assert metatron.health_check() == False
