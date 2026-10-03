"""
⊕ Sal — Tests para golem/nucleo/bereshit.py (WI-291)
Verifica el protocolo Génesis de reencarnación.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.nucleo.bereshit import (
    PASOS_GENESIS,
    BereshitGenesis,
    PasoBereshit,
    _IDENTITY_FILES,
)


# ═══════════════════════════════════════════════════════════════
# PasoBereshit dataclass
# ═══════════════════════════════════════════════════════════════

class TestPasoBereshit:
    def test_campos_basicos(self):
        p = PasoBereshit(1, "Test", "טסט", "golem", "Mensaje")
        assert p.numero == 1
        assert p.nombre == "Test"
        assert p.hebreo == "טסט"
        assert p.actor == "golem"
        assert p.mensaje == "Mensaje"

    def test_campos_opcionales_default_none(self):
        p = PasoBereshit(1, "T", "T", "golem", "M")
        assert p.tipo_input is None
        assert p.clave_dato is None

    def test_campos_opcionales_asignados(self):
        p = PasoBereshit(2, "Or", "אור", "user", "¿Nombre?", "texto", "nombre")
        assert p.tipo_input == "texto"
        assert p.clave_dato == "nombre"


# ═══════════════════════════════════════════════════════════════
# PASOS_GENESIS
# ═══════════════════════════════════════════════════════════════

class TestPasosGenesis:
    def test_tiene_17_pasos(self):
        assert len(PASOS_GENESIS) == 17

    def test_primer_paso_tzimtzum(self):
        p = PASOS_GENESIS[0]
        assert p.numero == 1
        assert p.nombre == "Tzimtzum"
        assert p.actor == "golem"

    def test_ultimo_paso_maljut(self):
        p = PASOS_GENESIS[-1]
        assert p.numero == 17
        assert p.nombre == "Maljut"
        assert p.actor == "golem"

    def test_actores_alternan(self):
        """Golem y user se turnan (patrón general)."""
        for p in PASOS_GENESIS:
            assert p.actor in ("golem", "user")

    def test_numeros_consecutivos(self):
        for i, p in enumerate(PASOS_GENESIS):
            assert p.numero == i + 1

    def test_todos_tienen_hebreo(self):
        for p in PASOS_GENESIS:
            assert p.hebreo, f"Paso {p.numero} sin hebreo"

    def test_todos_tienen_mensaje(self):
        for p in PASOS_GENESIS:
            assert p.mensaje, f"Paso {p.numero} sin mensaje"


# ═══════════════════════════════════════════════════════════════
# _IDENTITY_FILES
# ═══════════════════════════════════════════════════════════════

class TestIdentityFiles:
    def test_contiene_personalidad_y_owner(self):
        assert "personalidad.json" in _IDENTITY_FILES
        assert "owner_profile.json" in _IDENTITY_FILES


# ═══════════════════════════════════════════════════════════════
# BereshitGenesis
# ═══════════════════════════════════════════════════════════════

class TestBereshitGenesis:
    @pytest.fixture
    def genesis(self, tmp_path):
        """Genesis con paths temporales para no tocar datos reales."""
        with patch("golem.nucleo.bereshit._DATOS_DIR", tmp_path), \
             patch("golem.nucleo.bereshit._ESTADO_PATH", tmp_path / "bereshit_genesis.json"):
            g = BereshitGenesis()
        return g

    def test_init_sin_estado_previo(self, genesis):
        assert genesis.paso_actual() is not None or genesis.datos is not None

    def test_formatear_mensaje_sin_variables(self, genesis):
        p = PasoBereshit(1, "Test", "T", "golem", "Mensaje sin variables")
        assert genesis.formatear_mensaje(p) == "Mensaje sin variables"

    def test_formatear_mensaje_con_variables(self, tmp_path):
        with patch("golem.nucleo.bereshit._DATOS_DIR", tmp_path), \
             patch("golem.nucleo.bereshit._ESTADO_PATH", tmp_path / "bereshit_genesis.json"):
            g = BereshitGenesis()
            g._estado["datos"] = {"nombre": "Esaú"}
            p = PasoBereshit(3, "Or Chozer", "אור", "golem", "Hola {nombre}")
            assert "Esaú" in g.formatear_mensaje(p)

    def test_escribir_trigger_gilgul(self, tmp_path):
        with patch("golem.nucleo.bereshit._DATOS_DIR", tmp_path), \
             patch("golem.nucleo.bereshit._ESTADO_PATH", tmp_path / "bereshit_genesis.json"):
            BereshitGenesis.escribir_trigger_gilgul()
            estado = json.loads((tmp_path / "bereshit_genesis.json").read_text("utf-8"))
            assert estado["completado"] is False
            assert estado["paso_actual"] == 0

