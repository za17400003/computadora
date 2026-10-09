"""
⊕ Sal — Tests para computadora/habilidades/web.py (WI-291)
Verifica la habilidad de búsqueda web.
"""

from unittest.mock import MagicMock, patch

import pytest

from computadora.habilidades import web


# ═══════════════════════════════════════════════════════════════
# buscar_en_internet
# ═══════════════════════════════════════════════════════════════

class TestBuscarEnInternet:
    def test_resultado_es_string(self):
        with patch.object(web, "DDGS") as mock_ddgs:
            mock_ctx = MagicMock()
            mock_ctx.text.return_value = [
                {"title": "Python docs", "body": "Documentación oficial"},
            ]
            mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)

            resultado = web.buscar_en_internet("python docs", max_resultados=1)
            assert isinstance(resultado, str)
            assert "Python docs" in resultado

    def test_sin_resultados_retorna_vacio(self):
        with patch.object(web, "DDGS") as mock_ddgs:
            mock_ctx = MagicMock()
            mock_ctx.text.return_value = []
            mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)

            resultado = web.buscar_en_internet("xyz imposible query")
            assert resultado == ""

    def test_excepcion_retorna_vacio(self):
        with patch.object(web, "DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__ = MagicMock(side_effect=RuntimeError("API error"))

            resultado = web.buscar_en_internet("test")
            assert resultado == ""

    def test_max_resultados_se_pasa(self):
        with patch.object(web, "DDGS") as mock_ddgs:
            mock_ctx = MagicMock()
            mock_ctx.text.return_value = [
                {"title": f"R{i}", "body": f"Body {i}"} for i in range(3)
            ]
            mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)

            resultado = web.buscar_en_internet("test", max_resultados=3)
            assert "1." in resultado
            assert "3." in resultado

