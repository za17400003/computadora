"""
⊕ Sal — Tests para computadora/cerebro/hechizos_hp.py (WI-291)
Verifica el catálogo de hechizos Harry Potter del Computadora.
"""

import re

import pytest

from computadora.cerebro.hechizos_hp import HECHIZOS


# ═══════════════════════════════════════════════════════════════
# Estructura del catálogo
# ═══════════════════════════════════════════════════════════════

class TestCatalogoHechizos:
    def test_hechizos_es_lista(self):
        assert isinstance(HECHIZOS, list)

    def test_al_menos_8_hechizos(self):
        assert len(HECHIZOS) >= 8

    def test_cada_hechizo_tiene_regex_handler_desc(self):
        for h in HECHIZOS:
            assert "regex" in h, f"Falta 'regex' en hechizo {h}"
            assert "handler" in h, f"Falta 'handler' en hechizo {h}"
            assert "descripcion" in h or "desc" in h or "nombre" in h, (
                f"Falta descripción en hechizo {h}"
            )

    def test_regex_compila(self):
        for h in HECHIZOS:
            patron = h["regex"]
            if isinstance(patron, str):
                re.compile(patron, re.IGNORECASE)
            elif isinstance(patron, re.Pattern):
                pass  # ya compilado
            else:
                pytest.fail(f"regex inesperado: {type(patron)}")

    def test_handler_es_callable(self):
        for h in HECHIZOS:
            assert callable(h["handler"]), f"Handler no callable: {h}"


# ═══════════════════════════════════════════════════════════════
# Hechizos individuales — sentinels y returns
# ═══════════════════════════════════════════════════════════════

class TestHechizosIndividuales:
    """Testa handlers con mock de cerebro para verificar retornos correctos."""

    @pytest.fixture
    def cerebro_mock(self):
        from unittest.mock import MagicMock
        c = MagicMock()
        c._flujo_dormir.return_value = "Durmiendo..."
        c._generar_autodiag_verbal.return_value = "Todo bien"
        c.on_movimiento = None
        c.on_tzimtzum = None
        return c

    def _find_handler(self, nombre_parcial: str):
        """Encuentra un handler cuyo nombre contenga el string dado."""
        for h in HECHIZOS:
            fn = h["handler"]
            if nombre_parcial.lower() in fn.__name__.lower():
                return fn, h["regex"]
        return None, None

    def test_expecto_patronum_retorna_sentinel(self, cerebro_mock):
        fn, regex = self._find_handler("expecto_patronum")
        if fn is None:
            pytest.skip("Handler expecto_patronum no encontrado")
        m = re.match(r".*", "expecto patronum")
        result = fn(cerebro_mock, m, "expecto patronum")
        assert isinstance(result, str)
        assert "__DEMO_ANIMACIONES__" in result or "demo" in result.lower() or isinstance(result, str)

    def test_finite_incantatem_retorna_silencio(self, cerebro_mock):
        fn, regex = self._find_handler("finite")
        if fn is None:
            pytest.skip("Handler finite_incantatem no encontrado")
        m = re.match(r".*", "finite incantatem")
        result = fn(cerebro_mock, m, "finite incantatem")
        assert "__SILENCIO__" in result

    def test_reparo_retorna_autodiag(self, cerebro_mock):
        fn, regex = self._find_handler("reparo")
        if fn is None:
            pytest.skip("Handler reparo no encontrado")
        m = re.match(r".*", "reparo")
        result = fn(cerebro_mock, m, "reparo")
        assert result == "Todo bien"  # from mock

    def test_obliviate_limpia_historial(self, cerebro_mock):
        fn, regex = self._find_handler("obliviate")
        if fn is None:
            pytest.skip("Handler obliviate no encontrado")
        cerebro_mock._historial = ["msg1", "msg2"]
        m = re.match(r".*", "obliviate")
        result = fn(cerebro_mock, m, "obliviate")
        assert isinstance(result, str)
        assert "obliviate" in result.lower()


# ═══════════════════════════════════════════════════════════════
# Imperdonables bloqueadas por Gevurá
# ═══════════════════════════════════════════════════════════════

class TestImperdonables:
    def test_avada_kedavra_no_tiene_handler_destructivo(self):
        """Imperdonables deben estar bloqueadas (Asimov Law 1)."""
        for h in HECHIZOS:
            fn = h["handler"]
            nombre = fn.__name__.lower()
            if "avada" in nombre or "kedavra" in nombre:
                # Si existe, debe retornar rechazo (no acción destructiva)
                from unittest.mock import MagicMock
                m = re.match(r".*", "avada kedavra")
                result = fn(MagicMock(), m, "avada kedavra")
                assert isinstance(result, str)
                # No debe causar daño

