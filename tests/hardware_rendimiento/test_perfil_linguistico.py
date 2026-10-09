"""
⊕ Sal — Tests para computadora/memoria/perfil_linguistico.py (WI-291)
Verifica el perfil idioléctico del amo.
"""

import re
from unittest.mock import patch

import pytest

from computadora.memoria.perfil_linguistico import (
    PerfilLinguistico,
    _RE_CORTES,
    _RE_IMPERATIVOS,
    _RE_MULETILLAS,
    _STOPWORDS,
    _TEMAS_KEYWORDS,
)


# ═══════════════════════════════════════════════════════════════
# Regexes
# ═══════════════════════════════════════════════════════════════

class TestRegexPatterns:
    def test_muletillas_detecta_oye(self):
        assert _RE_MULETILLAS.search("oye computadora")

    def test_muletillas_detecta_la_neta(self):
        assert _RE_MULETILLAS.search("la neta está bien")

    def test_imperativos_detecta_abre(self):
        assert _RE_IMPERATIVOS.search("abre el navegador")

    def test_imperativos_detecta_busca(self):
        assert _RE_IMPERATIVOS.search("busca en internet")

    def test_cortes_detecta_por_favor(self):
        assert _RE_CORTES.search("por favor abre eso")

    def test_cortes_detecta_podrias(self):
        assert _RE_CORTES.search("podrías hacer eso")


# ═══════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════

class TestConstantes:
    def test_stopwords_no_vacio(self):
        assert len(_STOPWORDS) > 10

    def test_temas_keywords_tiene_categorias(self):
        assert "tecnología" in _TEMAS_KEYWORDS
        assert "sistema" in _TEMAS_KEYWORDS
        assert "computadora" in _TEMAS_KEYWORDS


# ═══════════════════════════════════════════════════════════════
# PerfilLinguistico
# ═══════════════════════════════════════════════════════════════

class TestPerfilLinguistico:
    @pytest.fixture
    def perfil(self, tmp_path):
        with patch("computadora.memoria.perfil_linguistico._DATOS_DIR", tmp_path), \
             patch("computadora.memoria.perfil_linguistico._PERFIL_PATH", tmp_path / "p.json"):
            p = PerfilLinguistico()
        return p

    def test_init_perfil_vacio(self, perfil):
        assert perfil._perfil["interacciones_analizadas"] == 0
        assert perfil._perfil["estilo_predominante"] == "directo"

    def test_registrar_interaccion_incrementa_contador(self, perfil, tmp_path):
        with patch("computadora.memoria.perfil_linguistico._DATOS_DIR", tmp_path), \
             patch("computadora.memoria.perfil_linguistico._PERFIL_PATH", tmp_path / "p.json"):
            perfil.registrar_interaccion("oye computadora busca en internet por favor")
            assert perfil._perfil["interacciones_analizadas"] == 1

    def test_registrar_detecta_muletillas(self, perfil, tmp_path):
        with patch("computadora.memoria.perfil_linguistico._DATOS_DIR", tmp_path), \
             patch("computadora.memoria.perfil_linguistico._PERFIL_PATH", tmp_path / "p.json"):
            perfil.registrar_interaccion("oye mira la neta está bueno")
            assert perfil._perfil["muletillas"].get("oye", 0) >= 1

    def test_texto_corto_se_ignora(self, perfil, tmp_path):
        with patch("computadora.memoria.perfil_linguistico._DATOS_DIR", tmp_path), \
             patch("computadora.memoria.perfil_linguistico._PERFIL_PATH", tmp_path / "p.json"):
            perfil.registrar_interaccion("ab")
            assert perfil._perfil["interacciones_analizadas"] == 0

    def test_perfil_vacio_factory(self):
        vacio = PerfilLinguistico._perfil_vacio()
        assert vacio["estilo_predominante"] == "directo"
        assert vacio["longitud_media_palabras"] == 0.0

