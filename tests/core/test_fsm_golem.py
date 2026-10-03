"""
⊕ Sal — Tests para golem/interfaz/fsm_golem.py (WI-291)
Verifica la FSM formal del Maljut.
"""

import pytest

from computadora.interfaz.fsm_golem import EstadoMaljut, TRANSICIONES_VALIDAS


# ═══════════════════════════════════════════════════════════════
# EstadoMaljut enum
# ═══════════════════════════════════════════════════════════════

class TestEstadoMaljut:
    def test_tiene_13_estados(self):
        assert len(EstadoMaljut) == 13

    def test_estados_requeridos(self):
        nombres = {e.name for e in EstadoMaljut}
        for n in ("DORMIDO", "ESCUCHANDO", "PROCESANDO", "HABLANDO",
                   "TRABAJANDO", "ERROR", "BERESHIT", "DESPERTANDO",
                   "DESCANSO_GUARDIAN", "VIGILIA", "CORTESIA",
                   "ALERTA_EXTRANO", "GEVURA_ACTIVA"):
            assert n in nombres, f"Falta estado {n}"

    def test_valores_son_strings(self):
        for e in EstadoMaljut:
            assert isinstance(e.value, str)


# ═══════════════════════════════════════════════════════════════
# Tabla de transiciones
# ═══════════════════════════════════════════════════════════════

class TestTransicionesValidas:
    def test_todos_los_estados_tienen_entrada(self):
        """Ningún estado es huérfano — todos aparecen como key."""
        for e in EstadoMaljut:
            assert e in TRANSICIONES_VALIDAS, f"{e.name} no tiene transiciones definidas"

    def test_no_hay_dead_ends(self):
        """Cada estado tiene al menos 1 transición de salida."""
        for e, destinos in TRANSICIONES_VALIDAS.items():
            assert len(destinos) >= 1, f"{e.name} es dead-end (0 transiciones)"

    def test_dormido_puede_ir_a_escuchando(self):
        assert EstadoMaljut.ESCUCHANDO in TRANSICIONES_VALIDAS[EstadoMaljut.DORMIDO]

    def test_bereshit_puede_ir_a_despertando(self):
        assert EstadoMaljut.DESPERTANDO in TRANSICIONES_VALIDAS[EstadoMaljut.BERESHIT]

    def test_escuchando_puede_ir_a_procesando(self):
        assert EstadoMaljut.PROCESANDO in TRANSICIONES_VALIDAS[EstadoMaljut.ESCUCHANDO]

    def test_destinos_son_estados_validos(self):
        """Ninguna transición apunta a un estado inexistente."""
        estados_validos = set(EstadoMaljut)
        for origen, destinos in TRANSICIONES_VALIDAS.items():
            for d in destinos:
                assert d in estados_validos, f"{origen.name}→{d} inválido"

    def test_error_puede_volver_a_escuchando(self):
        assert EstadoMaljut.ESCUCHANDO in TRANSICIONES_VALIDAS[EstadoMaljut.ERROR]

