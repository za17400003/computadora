"""
⊕ Sal — Tests para computadora/nucleo/proactividad.py (WI-286).

Cubre: Sugerencia NamedTuple, MotorProactividad init, check_emet_integridad,
tema_ya_dicho_hoy, check cycle, y señales.
"""

import time
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from computadora.nucleo.proactividad import MotorProactividad, Sugerencia


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def motor():
    """Motor sin dependencias hardware (contexto=None, monitor=None)."""
    with patch("computadora.nucleo.proactividad._ESTADO_PROACTIVO_ARCHIVO") as mock_path:
        mock_path.exists.return_value = False
        m = MotorProactividad(contexto_pantalla=None, monitor_sistema=None)
    return m


# ═══════════════════════════════════════════════════════════════
# Sugerencia NamedTuple
# ═══════════════════════════════════════════════════════════════

class TestSugerencia:
    def test_campos(self):
        s = Sugerencia("salud", "Problemas detectados")
        assert s.tipo == "salud"
        assert s.texto == "Problemas detectados"

    def test_es_tupla(self):
        s = Sugerencia("clipboard", "URL copiada")
        assert isinstance(s, tuple)
        assert len(s) == 2


# ═══════════════════════════════════════════════════════════════
# MotorProactividad init
# ═══════════════════════════════════════════════════════════════

class TestMotorInit:
    def test_11_checks_registrados(self, motor):
        assert len(motor._checks) == 11

    def test_check_emet_en_lista(self, motor):
        nombres = [c.__name__ for c in motor._checks]
        assert "_check_emet_integridad" in nombres

    def test_check_emet_despues_de_salud_computadora(self, motor):
        nombres = [c.__name__ for c in motor._checks]
        idx_salud = nombres.index("_check_salud_computadora")
        idx_emet = nombres.index("_check_emet_integridad")
        assert idx_emet == idx_salud + 1

    def test_atributos_emet(self, motor):
        assert motor._ultimo_emet_check == 0
        assert motor._intervalo_emet == 3600

    def test_no_detenido_al_crear(self, motor):
        assert motor._detener is False

    def test_modo_silencio_off(self, motor):
        assert motor._modo_silencio is False


# ═══════════════════════════════════════════════════════════════
# _tema_ya_dicho_hoy / _registrar_tema_emitido
# ═══════════════════════════════════════════════════════════════

class TestTemasDiarios:
    def test_tema_no_dicho(self, motor):
        assert motor._tema_ya_dicho_hoy("test_tema") is False

    def test_registrar_y_verificar(self, motor):
        with patch.object(motor, "_guardar_estado_proactivo"):
            motor._registrar_tema_emitido("test_tema")
        assert motor._tema_ya_dicho_hoy("test_tema") is True

    def test_tema_otro_dia_no_cuenta(self, motor):
        motor._temas_emitidos_hoy["test_tema"] = "2020-01-01"
        assert motor._tema_ya_dicho_hoy("test_tema") is False


# ═══════════════════════════════════════════════════════════════
# _check_emet_integridad
# ═══════════════════════════════════════════════════════════════

class TestCheckEmetIntegridad:
    def test_cooldown_respetado(self, motor):
        """Si se ejecutó hace poco, retorna None."""
        motor._ultimo_emet_check = time.time()
        assert motor._check_emet_integridad() is None

    def test_tema_ya_dicho_retorna_none(self, motor):
        motor._temas_emitidos_hoy["emet_integridad"] = date.today().isoformat()
        assert motor._check_emet_integridad() is None

    def test_manifiesto_sano_retorna_none(self, motor):
        """Manifiesto real del Computadora debería estar sano."""
        with patch.object(motor, "_guardar_estado_proactivo"):
            result = motor._check_emet_integridad()
        assert result is None

    def test_detecta_alef_faltante(self, motor):
        manifiesto_roto = {
            "identidad": {"emet": "verdad sin alef"},
            "arquitectura": {
                "sefirot": {f"S{i}": {} for i in range(10)},
                "trifecta": {"azufre": {}, "sal": {}, "mercurio": {}},
            },
            "genesis_biblico": [{}] * 7,
        }
        with patch("computadora.nucleo.emet.generar_manifiesto", return_value=manifiesto_roto):
            with patch.object(motor, "_guardar_estado_proactivo"):
                result = motor._check_emet_integridad()
        assert result is not None
        assert "א" in result.texto

    def test_detecta_sefirot_incompletas(self, motor):
        manifiesto_roto = {
            "identidad": {"emet": "א verdad"},
            "arquitectura": {
                "sefirot": {"Keter": {}, "Jojma": {}},
                "trifecta": {"azufre": {}, "sal": {}, "mercurio": {}},
            },
            "genesis_biblico": [{}] * 7,
        }
        with patch("computadora.nucleo.emet.generar_manifiesto", return_value=manifiesto_roto):
            with patch.object(motor, "_guardar_estado_proactivo"):
                result = motor._check_emet_integridad()
        assert result is not None
        assert "2/10" in result.texto

    def test_detecta_trifecta_incompleta(self, motor):
        manifiesto_roto = {
            "identidad": {"emet": "א"},
            "arquitectura": {
                "sefirot": {f"S{i}": {} for i in range(10)},
                "trifecta": {"azufre": {}},
            },
            "genesis_biblico": [{}] * 7,
        }
        with patch("computadora.nucleo.emet.generar_manifiesto", return_value=manifiesto_roto):
            with patch.object(motor, "_guardar_estado_proactivo"):
                result = motor._check_emet_integridad()
        assert result is not None
        assert "sal" in result.texto or "mercurio" in result.texto

    def test_detecta_genesis_incompleto(self, motor):
        manifiesto_roto = {
            "identidad": {"emet": "א"},
            "arquitectura": {
                "sefirot": {f"S{i}": {} for i in range(10)},
                "trifecta": {"azufre": {}, "sal": {}, "mercurio": {}},
            },
            "genesis_biblico": [{}] * 3,
        }
        with patch("computadora.nucleo.emet.generar_manifiesto", return_value=manifiesto_roto):
            with patch.object(motor, "_guardar_estado_proactivo"):
                result = motor._check_emet_integridad()
        assert result is not None
        assert "3/7" in result.texto

    def test_import_error_no_explota(self, motor):
        with patch("computadora.nucleo.emet.generar_manifiesto", side_effect=ImportError):
            result = motor._check_emet_integridad()
        assert result is None


# ═══════════════════════════════════════════════════════════════
# Control: silencio, alertas, detener
# ═══════════════════════════════════════════════════════════════

class TestControl:
    def test_activar_silencio(self, motor):
        motor.activar_silencio(10)
        assert motor._modo_silencio is True
        assert motor._silencio_hasta > time.time()

    def test_desactivar_silencio(self, motor):
        motor.activar_silencio(10)
        motor.desactivar_silencio()
        assert motor._modo_silencio is False
        assert motor._silencio_hasta == 0

    def test_detener(self, motor):
        motor.detener()
        assert motor._detener is True

    def test_desactivar_alertas(self, motor):
        motor.desactivar_alertas_sistema()
        assert motor._alertas_sistema_activas is False

    def test_reactivar_alertas(self, motor):
        motor.desactivar_alertas_sistema()
        motor.activar_alertas_sistema()
        assert motor._alertas_sistema_activas is True


# ═══════════════════════════════════════════════════════════════
# Signal: sugerencia_lista
# ═══════════════════════════════════════════════════════════════

class TestSignals:
    def test_signal_existe(self, motor):
        assert hasattr(motor, "sugerencia_lista")

    def test_signal_fase_cambio(self, motor):
        assert hasattr(motor, "fase_cambio")

