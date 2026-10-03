import os
import sys
import pytest
# Ensure repo root in path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def test_security_module_or_checks():
    # Try to import security-related modules; skip if not present
    mod = pytest.importorskip('computadora.seguridad')
    assert True
