"""
⊕ Sal — Tests para golem/interfaz/estilos.py (WI-291)
Verifica las constantes de estilo visual del Golem.
"""

import pytest

from computadora.interfaz.estilos import (
    AMBAR_BORDE,
    AMBAR_BRILLANTE,
    AMBAR_TEXTO,
    ESTILO_GLOBAL,
    GRIS_SISTEMA,
    NEGRO_FONDO,
    NEGRO_INPUT,
    NEGRO_PANEL,
    ORO,
)


class TestColores:
    @pytest.mark.parametrize("color", [
        NEGRO_FONDO, NEGRO_PANEL, NEGRO_INPUT,
        AMBAR_TEXTO, AMBAR_BORDE, AMBAR_BRILLANTE,
        ORO, GRIS_SISTEMA,
    ])
    def test_formato_hex(self, color):
        assert color.startswith("#")
        assert len(color) == 7  # #RRGGBB


class TestEstiloGlobal:
    def test_es_string_no_vacio(self):
        assert isinstance(ESTILO_GLOBAL, str)
        assert len(ESTILO_GLOBAL) > 100

    def test_contiene_selectores_qt(self):
        assert "QMainWindow" in ESTILO_GLOBAL
        assert "QWidget" in ESTILO_GLOBAL

    def test_colores_referenciados(self):
        assert NEGRO_FONDO in ESTILO_GLOBAL
        assert AMBAR_TEXTO in ESTILO_GLOBAL

