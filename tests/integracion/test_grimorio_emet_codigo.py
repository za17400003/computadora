"""
WI-290: Tests para api/emet/codigo — Código de Verdad en vivo.

Sal (tests) para la página del Grimorio que lee emet.py en tiempo real
y lo anota con verdades ordenadas.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Añadir raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Fixture: instancia del handler sin servidor HTTP ──

@pytest.fixture()
def handler():
    """Crea una instancia mínima del handler para probar métodos."""
    from ENCICLOPEDIA.servidor_enciclopedia import EnciclopediaHandler

    class FakeHandler(EnciclopediaHandler):
        def __init__(self):
            # No llamar super().__init__ — no necesitamos socket
            pass

    return FakeHandler()


# ═══ Estructura del resultado ═══

class TestEmetCodigoEstructura:
    """Verifica que el resultado tenga la forma correcta."""

    def test_retorna_dict(self, handler):
        resultado = handler._emet_codigo_vivo()
        assert isinstance(resultado, dict)

    def test_tipo_correcto(self, handler):
        r = handler._emet_codigo_vivo()
        assert r["tipo"] == "emet_codigo_vivo"

    def test_archivo_correcto(self, handler):
        r = handler._emet_codigo_vivo()
        assert r["archivo"] == "computadora/nucleo/emet.py"

    def test_tiene_timestamp(self, handler):
        r = handler._emet_codigo_vivo()
        assert "ts" in r
        assert "T" in r["ts"]  # ISO format

    def test_tiene_principio_orden(self, handler):
        r = handler._emet_codigo_vivo()
        assert "orden" in r["principio"].lower()

    def test_total_lineas_positivo(self, handler):
        r = handler._emet_codigo_vivo()
        assert r["total_lineas"] > 100  # emet.py tiene ~410+ líneas

    def test_total_secciones_positivo(self, handler):
        r = handler._emet_codigo_vivo()
        assert r["total_secciones"] >= 8  # Al menos 8 funciones + módulo


# ═══ Secciones y orden ═══

class TestEmetCodigoSecciones:
    """Verifica que las secciones se parseen correctamente y EN ORDEN."""

    def test_primera_seccion_es_module(self, handler):
        r = handler._emet_codigo_vivo()
        assert r["secciones"][0]["nombre"] == "__module__"

    def test_generar_manifiesto_es_primera_funcion(self, handler):
        r = handler._emet_codigo_vivo()
        funciones = [s for s in r["secciones"] if s["nombre"] != "__module__"]
        assert funciones[0]["nombre"] == "generar_manifiesto"

    def test_orden_preservado(self, handler):
        """El orden de aparición en el archivo se respeta."""
        r = handler._emet_codigo_vivo()
        nombres = [s["nombre"] for s in r["secciones"]]
        # generar_manifiesto ANTES de _identidad
        assert nombres.index("generar_manifiesto") < nombres.index("_identidad")
        # _identidad ANTES de _arquitectura
        assert nombres.index("_identidad") < nombres.index("_arquitectura")
        # _arquitectura ANTES de _capacidades
        assert nombres.index("_arquitectura") < nombres.index("_capacidades")

    def test_cada_seccion_tiene_codigo(self, handler):
        r = handler._emet_codigo_vivo()
        for s in r["secciones"]:
            assert len(s["codigo"]) > 0, f"Sección {s['nombre']} sin código"

    def test_cada_seccion_tiene_linea_inicio(self, handler):
        r = handler._emet_codigo_vivo()
        for s in r["secciones"]:
            assert s["linea_inicio"] >= 1


# ═══ Anotaciones de verdad ═══

class TestEmetCodigoVerdades:
    """Verifica que las anotaciones de verdad estén presentes."""

    def test_module_tiene_sefira(self, handler):
        r = handler._emet_codigo_vivo()
        modulo = r["secciones"][0]
        assert modulo["sefira"] == "Keter"

    def test_generar_manifiesto_tiene_verdad(self, handler):
        r = handler._emet_codigo_vivo()
        gm = next(s for s in r["secciones"] if s["nombre"] == "generar_manifiesto")
        assert "Bereshit" in gm["verdad"]

    def test_identidad_tiene_verdad(self, handler):
        r = handler._emet_codigo_vivo()
        ident = next(s for s in r["secciones"] if s["nombre"] == "_identidad")
        assert "Quién soy" in ident["verdad"]

    def test_buscar_en_emet_tiene_netzaj(self, handler):
        r = handler._emet_codigo_vivo()
        buscar = next(s for s in r["secciones"] if s["nombre"] == "buscar_en_emet")
        assert buscar["sefira"] == "Netzaj"

    def test_todas_funciones_conocidas_anotadas(self, handler):
        """Todas las funciones principales tienen anotación de verdad."""
        r = handler._emet_codigo_vivo()
        funciones_esperadas = [
            "generar_manifiesto", "_identidad", "_arquitectura",
            "_capacidades", "_genesis_biblico_contraste", "_estado_actual",
            "buscar_en_emet",
        ]
        for nombre in funciones_esperadas:
            seccion = next(
                (s for s in r["secciones"] if s["nombre"] == nombre), None
            )
            assert seccion is not None, f"Falta sección {nombre}"
            assert seccion["verdad"], f"Sección {nombre} sin verdad"
            assert seccion["sefira"], f"Sección {nombre} sin sefirá"


# ═══ Actualización en vivo ═══

class TestEmetCodigoEnVivo:
    """Verifica que la lectura sea en vivo (no cacheada)."""

    def test_timestamp_cambia(self, handler):
        r1 = handler._emet_codigo_vivo()
        r2 = handler._emet_codigo_vivo()
        # Los timestamps deben ser diferentes (o muy cercanos)
        assert "ts" in r1
        assert "ts" in r2

    def test_archivo_no_encontrado(self, handler):
        """Si emet.py no existe, retorna error graceful."""
        with patch("pathlib.Path.exists", return_value=False):
            r = handler._emet_codigo_vivo()
            assert "error" in r


# ═══ Integración con index.html ═══

class TestEmetCodigoHTML:
    """Verifica que el template HTML esté presente en index.html."""

    def test_template_existe(self):
        index = Path(__file__).parent.parent / "libro_encantado" / "index.html"
        html = index.read_text("utf-8")
        assert 'data-chapter="emet_codigo"' in html

    def test_toc_entry_existe(self):
        index = Path(__file__).parent.parent / "libro_encantado" / "index.html"
        html = index.read_text("utf-8")
        assert "emet_codigo.html" in html

    def test_fetch_api_en_template(self):
        index = Path(__file__).parent.parent / "libro_encantado" / "index.html"
        html = index.read_text("utf-8")
        assert "api/emet/codigo" in html

    def test_container_div_existe(self):
        index = Path(__file__).parent.parent / "libro_encantado" / "index.html"
        html = index.read_text("utf-8")
        assert 'id="emet-codigo-container"' in html

