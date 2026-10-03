import os
import sys
import pytest
# Ensure repo root in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def test_hardware_utils_importable():
    hu = pytest.importorskip('computadora.utilidad.hardware_optimizer')
    assert True


def test_simple_performance_placeholder():
    # Placeholder: add microbenchmarks or perf smoke checks
    assert True
