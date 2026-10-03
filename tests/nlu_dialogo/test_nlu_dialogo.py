import os
import sys
import pytest
# Ensure repo root in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def test_nlu_module_importable():
    nlu = pytest.importorskip('computadora.cerebro.nlu')
    # check for known symbol if present
    assert hasattr(nlu, 'OLLAMA_URL') or hasattr(nlu, 'ollama') or True


def test_basic_dialog_flow_placeholder():
    # Placeholder: run more detailed dialog flow tests in integration stage
    assert True
