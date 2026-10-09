"""
⊕ Sal — Tests para computadora/cerebro/patrones_guardian.py (WI-291)
Verifica los patrones regex del Shomer HaBáyit.
"""

import re

import pytest

from computadora.cerebro.patrones_guardian import (
    RE_BUENOS_DIAS,
    RE_DORMIR,
    RE_DORMIR_VIGILA,
    RE_DUERMETE,
    RE_GUARDIAN_OFF,
    RE_GUARDIAN_ON,
    RE_REINICIAR_COMPUTADORA,
)


class TestPatronesGuardian:
    """Todos los patrones son regex compilados."""

    @pytest.mark.parametrize("patron", [
        RE_GUARDIAN_ON, RE_GUARDIAN_OFF, RE_DORMIR, RE_DORMIR_VIGILA,
        RE_DUERMETE, RE_BUENOS_DIAS, RE_REINICIAR_COMPUTADORA,
    ])
    def test_es_regex_compilado(self, patron):
        assert isinstance(patron, re.Pattern)


class TestGuardianOn:
    @pytest.mark.parametrize("texto", [
        "ponte en modo guardián",
        "vigila la casa",
        "activa el guardián",
        "modo seguridad",
    ])
    def test_matchea_activacion(self, texto):
        assert RE_GUARDIAN_ON.search(texto)

    def test_no_matchea_texto_random(self):
        assert RE_GUARDIAN_ON.search("hola cómo estás") is None


class TestGuardianOff:
    @pytest.mark.parametrize("texto", [
        "desactiva el guardián",
        "ya no vigiles",
        "modo normal",
        "ya estoy aquí",
    ])
    def test_matchea_desactivacion(self, texto):
        assert RE_GUARDIAN_OFF.search(texto)


class TestDormir:
    def test_matchea_dormir(self):
        assert RE_DORMIR.search("ya me voy a dormir")

    def test_matchea_buenas_noches(self):
        assert RE_DORMIR.search("buenas noches, duerme bien")


class TestBuenosDias:
    def test_matchea_buenos_dias(self):
        assert RE_BUENOS_DIAS.search("buenos días")

    def test_matchea_ya_desperte(self):
        assert RE_BUENOS_DIAS.search("ya desperté")


class TestReiniciar:
    def test_matchea_reiniciate(self):
        assert RE_REINICIAR_COMPUTADORA.search("reiníciate")

    def test_matchea_restart(self):
        assert RE_REINICIAR_COMPUTADORA.search("restart")

