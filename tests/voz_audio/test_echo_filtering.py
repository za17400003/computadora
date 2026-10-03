# tests/test_echo_filtering.py
import pytest
from computadora.voz.escucha import HiloEscucha
from computadora.metatron import MetatronOrquestador

def test_echo_filtering_basic():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)  # Config will be mocked
    escucha.metatron = metatron

    # Register TTS output
    escucha.registrar_tts_output("Hola, soy la computadora")

    # Echo should be filtered
    is_echo, interrupted = escucha._check_echo_timestamp("hola soy la computadora")
    assert is_echo == True
    assert interrupted is None

def test_interruption_detection():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    escucha.registrar_tts_output("El clima está soleado hoy")

    # Interruption should be detected
    is_echo, interrupted = escucha._check_echo_timestamp("espera, mejor dime la temperatura")
    assert is_echo == False
    assert interrupted is not None

def test_no_echo_when_tts_completed():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    escucha.registrar_tts_output("Mensaje completado")
    escucha.marcar_tts_completado()

    # Should not be considered echo
    is_echo, interrupted = escucha._check_echo_timestamp("mensaje completado")
    assert is_echo == False

def test_tts_buffer_cleanup():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    # Add old entry (simulate 35 seconds ago)
    import time
    old_time = time.time() - 35
    escucha.tts_buffer.append({
        'timestamp': old_time,
        'texto': 'old message',
        'activo': True
    })

    # Add new entry - should trigger cleanup
    escucha.registrar_tts_output("new message")

    # Old entry should be removed
    assert len(escucha.tts_buffer) == 1
    assert escucha.tts_buffer[0]['texto'] == 'new message'
