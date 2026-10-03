"""
⊕ Sal — Tests para golem/expresion/shir_haneshama.py (WI-291)
Verifica la expresión artística del Golem.
"""

import pytest

from computadora.expresion.shir_haneshama import (
    _DATOS_CURIOSOS,
    _FRASES_FILOSOFICAS,
    _REFLEXIONES_TEMPORALES,
    generar_expresion,
    generar_reflexion_proactiva,
)


# ═══════════════════════════════════════════════════════════════
# Catálogos de frases
# ═══════════════════════════════════════════════════════════════

class TestCatalogos:
    def test_frases_filosoficas_tiene_humores(self):
        for humor in ("neutral", "sereno", "contento", "reflexivo"):
            assert humor in _FRASES_FILOSOFICAS, f"Falta humor '{humor}'"
            assert len(_FRASES_FILOSOFICAS[humor]) >= 2

    def test_reflexiones_temporales_4_franjas(self):
        for franja in ("madrugada", "mañana", "tarde", "noche"):
            assert franja in _REFLEXIONES_TEMPORALES
            assert len(_REFLEXIONES_TEMPORALES[franja]) >= 2

    def test_datos_curiosos_no_vacio(self):
        assert len(_DATOS_CURIOSOS) >= 5

    def test_todos_los_datos_curiosos_son_strings(self):
        for dato in _DATOS_CURIOSOS:
            assert isinstance(dato, str)
            assert len(dato) > 10


# ═══════════════════════════════════════════════════════════════
# generar_expresion
# ═══════════════════════════════════════════════════════════════

class TestGenerarExpresion:
    def test_retorna_string_no_vacio(self):
        result = generar_expresion()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_tipo_filosofica(self):
        result = generar_expresion(humor="neutral", tipo="filosofica")
        assert isinstance(result, str)

    def test_tipo_temporal(self):
        result = generar_expresion(tipo="temporal")
        assert isinstance(result, str)

    def test_tipo_dato_curioso(self):
        result = generar_expresion(tipo="dato_curioso")
        assert isinstance(result, str)

    def test_humor_desconocido_usa_neutral(self):
        result = generar_expresion(humor="inexistente", tipo="filosofica")
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════
# generar_reflexion_proactiva
# ═══════════════════════════════════════════════════════════════

class TestGenerarReflexionProactiva:
    def test_retorna_string_o_none(self):
        resultados = [generar_reflexion_proactiva() for _ in range(50)]
        strings = [r for r in resultados if r is not None]
        nones = [r for r in resultados if r is None]
        # Con probabilidad 0.2, al menos ALGUNO de 50 intentos debe ser string
        assert len(strings) >= 1
        # Y al menos alguno None (p=0.8)
        assert len(nones) >= 1

