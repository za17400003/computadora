"""Tests para WI-292 ☿ Mercurio — NLU introspección de subsistemas.

Verifica que los 5 nuevos regexes (_RE_EMOCION_DETECTADA, _RE_PERFIL_LINGUISTICO,
_RE_ESTADO_FSM, _RE_HOT_RELOAD, _RE_CIFRADO_STATUS) compilan y matchean inputs válidos.
"""
import re
import pytest

from computadora.cerebro.nlu import (
    _RE_EMOCION_DETECTADA,
    _RE_PERFIL_LINGUISTICO,
    _RE_ESTADO_FSM,
    _RE_HOT_RELOAD,
    _RE_CIFRADO_STATUS,
)


# ── _RE_EMOCION_DETECTADA ────────────────────────────────────
class TestEmocionDetectada:
    @pytest.mark.parametrize("frase", [
        "qué emoción detectas",
        "qué sientes",
        "cómo me ves emocionalmente",
        "qué emoción me percibes",
        "detecta mi emoción",
        "análisis emocional",
        "qué sentimiento detectas",
    ])
    def test_match(self, frase):
        assert _RE_EMOCION_DETECTADA.search(frase)

    @pytest.mark.parametrize("frase", [
        "abre chrome",
        "qué hora es",
        "buenos días",
    ])
    def test_no_match(self, frase):
        assert not _RE_EMOCION_DETECTADA.search(frase)


# ── _RE_PERFIL_LINGUISTICO ───────────────────────────────────
class TestPerfilLinguistico:
    @pytest.mark.parametrize("frase", [
        "cómo hablo",
        "cómo me expreso",
        "mi estilo de hablar",
        "mi perfil lingüístico",
        "analiza mi lenguaje",
        "análisis de mi expresión",
        "mi forma de comunicar",
        "mi patrón de expresión",
    ])
    def test_match(self, frase):
        assert _RE_PERFIL_LINGUISTICO.search(frase)

    @pytest.mark.parametrize("frase", [
        "hola computadora",
        "qué hora es",
        "abre youtube",
    ])
    def test_no_match(self, frase):
        assert not _RE_PERFIL_LINGUISTICO.search(frase)


# ── _RE_ESTADO_FSM ───────────────────────────────────────────
class TestEstadoFSM:
    @pytest.mark.parametrize("frase", [
        "en qué estado estás",
        "en qué estado te encuentras",
        "estado de maljut",
        "estado del fsm",
        "qué estado tienes",
        "cuál es tu estado actual",
        "cuál es tu estado interno",
    ])
    def test_match(self, frase):
        assert _RE_ESTADO_FSM.search(frase)

    @pytest.mark.parametrize("frase", [
        "estado del clima",
        "cómo estás",
        "qué tal",
    ])
    def test_no_match(self, frase):
        assert not _RE_ESTADO_FSM.search(frase)


# ── _RE_HOT_RELOAD ───────────────────────────────────────────
class TestHotReload:
    @pytest.mark.parametrize("frase", [
        "recarga tu código",
        "hot reload",
        "reload",
        "recarga módulos",
        "actualiza tu código en vivo",
    ])
    def test_match(self, frase):
        assert _RE_HOT_RELOAD.search(frase)

    @pytest.mark.parametrize("frase", [
        "recarga la página",
        "actualiza las dependencias",
    ])
    def test_no_match(self, frase):
        assert not _RE_HOT_RELOAD.search(frase)


# ── _RE_CIFRADO_STATUS ───────────────────────────────────────
class TestCifradoStatus:
    @pytest.mark.parametrize("frase", [
        "está activo el cifrado",
        "estado del cifrado",
        "cifrado activado",
        "estado de la encriptación",
        "encriptación activa",
    ])
    def test_match(self, frase):
        assert _RE_CIFRADO_STATUS.search(frase)

    @pytest.mark.parametrize("frase", [
        "cifra este mensaje",
        "encripta el archivo",
        "descifra esto",
    ])
    def test_no_match(self, frase):
        assert not _RE_CIFRADO_STATUS.search(frase)


# ── Compiled regex validation ─────────────────────────────────
class TestRegexCompiled:
    """Verify all 5 patterns are compiled re.Pattern objects."""
    @pytest.mark.parametrize("pattern", [
        _RE_EMOCION_DETECTADA,
        _RE_PERFIL_LINGUISTICO,
        _RE_ESTADO_FSM,
        _RE_HOT_RELOAD,
        _RE_CIFRADO_STATUS,
    ])
    def test_is_compiled(self, pattern):
        assert isinstance(pattern, re.Pattern)
        assert pattern.flags & re.IGNORECASE

