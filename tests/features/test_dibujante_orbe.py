"""
⊕ Sal — Tests para golem/interfaz/dibujante_orbe.py (WI-291)
Verifica las constantes y estructuras del dibujante (sin QPainter activo).
"""

import pytest

from computadora.interfaz.dibujante_orbe import (
    RADIO_NUCLEO,
    RADIO_RESPLANDOR,
    DrawState,
)


class TestConstantes:
    def test_radio_nucleo_positivo(self):
        assert RADIO_NUCLEO > 0

    def test_radio_resplandor_mayor_que_nucleo(self):
        assert RADIO_RESPLANDOR > RADIO_NUCLEO


class TestDrawState:
    def test_instanciable(self):
        ds = DrawState(
            escala=1.0, fase=0.0,
            rot_anillo1=0.0, rot_anillo2=0.0, rot_letras=0.0,
            particulas=[], indicadores_herramientas=[],
            cerebro_nivel="nivel1",
        )
        assert ds.escala == 1.0
        assert ds.cerebro_nivel == "nivel1"

    def test_defaults(self):
        ds = DrawState(
            escala=1.0, fase=0.0,
            rot_anillo1=0.0, rot_anillo2=0.0, rot_letras=0.0,
            particulas=[], indicadores_herramientas=[],
            cerebro_nivel="nivel2",
        )
        assert ds.patron_sagrado == ""
        assert ds.patron_progreso == 0.0
        assert ds.etapa_alquimica == "nigredo"

