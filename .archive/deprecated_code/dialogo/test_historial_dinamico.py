# tests/test_historial_dinamico.py
import pytest
import time
from computadora.dialogo.historial_dinamico import HistorialDinamico, MensajeHistorial
from computadora.metatron import MetatronOrquestador

def test_mensaje_historial():
    msg = MensajeHistorial('user', 'hola')
    assert msg.tipo == 'user'
    assert msg.contenido == 'hola'
    assert msg.relevancia == 1.0

def test_relevancia_decay():
    msg = MensajeHistorial('user', 'test')
    # Fresh message
    assert msg.calcular_relevancia(time.time()) == 1.0

    # Simulate 10 minutes old
    msg.timestamp = time.time() - 600
    relevancia = msg.calcular_relevancia(time.time())
    assert 0.5 <= relevancia <= 1.0

def test_historial_agregar_mensaje():
    metatron = MetatronOrquestador()
    historial = HistorialDinamico(metatron)

    historial.agregar_mensaje('user', 'hola')
    historial.agregar_mensaje('assistant', 'hola, ¿cómo estás?')

    assert len(historial.mensajes) == 2
    assert historial.mensajes[0].contenido == 'hola'

def test_contexto_relevante():
    metatron = MetatronOrquestador()
    historial = HistorialDinamico(metatron)

    historial.agregar_mensaje('user', 'hola')
    historial.agregar_mensaje('assistant', 'hola, ¿qué tal?')

    contexto = historial.get_contexto_relevante()
    assert len(contexto) == 2
    assert contexto[0].tipo == 'assistant'  # Most recent first

def test_interrupciones_pendientes():
    metatron = MetatronOrquestador()
    historial = HistorialDinamico(metatron)

    historial.agregar_mensaje('interrupted', 'espera', {'resuelto': False})
    historial.agregar_mensaje('interrupted', 'otra vez', {'resuelto': True})

    pendientes = historial.get_interrupciones_pendientes()
    assert len(pendientes) == 1
    assert pendientes[0].contenido == 'espera'

def test_max_mensajes():
    metatron = MetatronOrquestador()
    historial = HistorialDinamico(metatron)
    historial._max_mensajes = 3

    # Add more than max
    for i in range(5):
        historial.agregar_mensaje('user', f'msg{i}')

    assert len(historial.mensajes) == 3
    assert historial.mensajes[0].contenido == 'msg2'  # Oldest remaining
