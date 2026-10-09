"""
⊕ Sal — Tests para computadora/cerebro/jojma_local.py (WI-291)
Verifica el motor de respuestas locales (sin LLM).
"""

import re

import pytest

from computadora.cerebro.jojma_local import (
    JojmaLocal,
    _PATRONES_INTENCION,
    _PLANTILLAS,
    _clasificar_intencion,
    _extraer_tema,
)


# ═══════════════════════════════════════════════════════════════
# Plantillas
# ═══════════════════════════════════════════════════════════════

class TestPlantillas:
    def test_categorias_requeridas(self):
        for cat in ("opinion", "explicacion", "sugerencia", "empatia", "desconocido"):
            assert cat in _PLANTILLAS, f"Falta categoría '{cat}'"

    def test_cada_categoria_tiene_al_menos_una_plantilla(self):
        for cat, lista in _PLANTILLAS.items():
            assert len(lista) >= 1, f"'{cat}' sin plantillas"

    def test_plantillas_son_strings(self):
        for cat, lista in _PLANTILLAS.items():
            for t in lista:
                assert isinstance(t, str)


# ═══════════════════════════════════════════════════════════════
# Patrones de intención
# ═══════════════════════════════════════════════════════════════

class TestPatronesIntencion:
    def test_patrones_son_tuplas_regex_str(self):
        for patron, categoria in _PATRONES_INTENCION:
            assert isinstance(patron, re.Pattern), f"'{patron}' no es regex compilado"
            assert isinstance(categoria, str)


# ═══════════════════════════════════════════════════════════════
# Clasificación de intención
# ═══════════════════════════════════════════════════════════════

class TestClasificarIntencion:
    def test_pregunta_opinion(self):
        assert _clasificar_intencion("¿qué opinas de Python?") == "opinion"

    def test_pregunta_explicacion(self):
        assert _clasificar_intencion("explícame cómo funciona esto") == "explicacion"

    def test_pregunta_sugerencia(self):
        assert _clasificar_intencion("qué recomiendas para aprender") == "sugerencia"

    def test_texto_sin_patron_retorna_desconocido(self):
        assert _clasificar_intencion("xyz123abc") == "desconocido"


# ═══════════════════════════════════════════════════════════════
# Extracción de tema
# ═══════════════════════════════════════════════════════════════

class TestExtraerTema:
    def test_extrae_tema_con_sobre(self):
        tema = _extraer_tema("dime algo sobre Python")
        assert "python" in tema.lower()

    def test_retorna_algo_no_vacio(self):
        tema = _extraer_tema("hola qué tal cómo estás hoy")
        assert isinstance(tema, str)
        assert len(tema) > 0


# ═══════════════════════════════════════════════════════════════
# JojmaLocal.generar
# ═══════════════════════════════════════════════════════════════

class TestJojmaLocalGenerar:
    def test_genera_respuesta_no_vacia(self):
        jojma = JojmaLocal()
        resp = jojma.generar("¿qué opinas de la vida?")
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_genera_con_humor(self):
        jojma = JojmaLocal()
        resp = jojma.generar("dime algo", humor="contento")
        assert isinstance(resp, str)

    def test_genera_con_memoria(self):
        jojma = JojmaLocal()
        resp = jojma.generar("recuérdame algo", memoria_contexto="Te gusta el café")
        assert isinstance(resp, str)

    def test_genera_respuesta_diferente_categorias(self):
        jojma = JojmaLocal()
        r1 = jojma.generar("¿qué opinas de esto?")
        r2 = jojma.generar("explícame la fotosíntesis")
        # Ambas válidas (strings no vacíos)
        assert r1 and r2

