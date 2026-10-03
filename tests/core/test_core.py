import os
import sys
import pytest

# Asegura que el paquete local se pueda importar desde el repo root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def test_import_computadora():
    import computadora
    assert hasattr(computadora, '__file__')


def test_config_loader_available():
    cfg_mod = pytest.importorskip('computadora.config')
    if hasattr(cfg_mod, 'cargar_config'):
        cfg = cfg_mod.cargar_config()
        assert isinstance(cfg, dict) or cfg is None
    else:
        pytest.skip('cargar_config no disponible')
