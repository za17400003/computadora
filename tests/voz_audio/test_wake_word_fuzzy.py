# tests/test_wake_word_fuzzy.py
import pytest
from computadora.voz.escucha import HiloEscucha
from computadora.metatron import MetatronOrquestador

def test_wake_word_exact():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    assert escucha._check_wake_word_fuzzy("computadora") == True
    assert escucha._check_wake_word_fuzzy("computa") == True
    assert escucha._check_wake_word_fuzzy("compu") == True

def test_wake_word_typos():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    assert escucha._check_wake_word_fuzzy("comutadora") == True  # Missing 'p'
    assert escucha._check_wake_word_fuzzy("computadoraa") == True  # Extra 'a'
    assert escucha._check_wake_word_fuzzy("komputadora") == True  # 'k' instead of 'c'

def test_wake_word_false_positives():
    metatron = MetatronOrquestador()
    escucha = HiloEscucha(None)
    escucha.metatron = metatron

    assert escucha._check_wake_word_fuzzy("ordenador") == False  # Different word
    assert escucha._check_wake_word_fuzzy("computacional") == False  # Too different

def test_wake_word_fallback_without_fuzzywuzzy():
    """Test fallback when fuzzywuzzy is not available"""
    # Mock fuzzywuzzy as unavailable
    import computadora.voz.escucha as escucha_module
    original_fuzzy = escucha_module._FUZZY_AVAILABLE
    escucha_module._FUZZY_AVAILABLE = False

    try:
        metatron = MetatronOrquestador()
        escucha = HiloEscucha(None)
        escucha.metatron = metatron

        # Should still work with exact matches
        assert escucha._check_wake_word_fuzzy("computadora") == True
        assert escucha._check_wake_word_fuzzy("ordenador") == False
    finally:
        # Restore original value
        escucha_module._FUZZY_AVAILABLE = original_fuzzy
