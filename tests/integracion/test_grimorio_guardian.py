"""
⊕ Sal — Tests para computadora/canales/grimorio_guardian.py (WI-291)
Verifica el GrimorioGuardian.
"""

from unittest.mock import patch, MagicMock

import pytest

from computadora.canales.enciclopedia_guardian import EnciclopediaGuardian, _POLL_INTERVAL


class TestConstantes:
    def test_poll_interval_positivo(self):
        assert _POLL_INTERVAL > 0


class TestGrimorioGuardian:
    def test_instanciable(self):
        g = GrimorioGuardian(personalidad=None)
        assert g is not None

    def test_detener_sin_iniciar(self):
        g = GrimorioGuardian()
        g.detener()  # No debe lanzar excepción

    def test_iniciar_y_detener(self):
        g = GrimorioGuardian()
        g.iniciar()
        assert g._hilo is not None
        assert g._hilo.daemon is True
        g.detener()

