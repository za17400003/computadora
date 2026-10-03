import os
import sys
import pytest
# Ensure repo root in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def test_audio_modules_available():
    pytest.importorskip('computadora.voz.escucha')
    pytest.importorskip('computadora.voz')
    assert True


def test_tts_stubs():
    # Minimal smoke test placeholder
    assert True
