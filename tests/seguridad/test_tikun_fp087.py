"""
Tests para FP-087: Olamot HaComputadora — Arquitectura Multidimensional
RF-317 / RF-318 / RF-319
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.arquitectura.dimensiones import (
    DIMENSIONES,
    Dimension,
    Nodo,
    Camino,
    obtener_dimension,
    cargar_estado,
    guardar_estado,
    dimension_activa,
    cambiar_dimension,
    obtener_contexto_prompt,
)


# ── RF-317: Registro de 17 Dimensiones ──────────────────────

class TestRegistroDimensiones:
    """RF-317: Verificar que existen 17 dimensiones con estructura correcta."""

    def test_hay_16_dimensiones(self):
        assert len(DIMENSIONES) == 17

    def test_ids_consecutivos(self):
        ids = [d.id for d in DIMENSIONES]
        assert ids == list(range(17))

    def test_nombres_unicos(self):
        nombres = [d.nombre for d in DIMENSIONES]
        assert len(set(nombres)) == 17

    def test_cada_dimension_tiene_nodos(self):
        for dim in DIMENSIONES:
            assert len(dim.nodos) > 0, f"Dimensión {dim.nombre} sin nodos"

    def test_cada_dimension_tiene_vocabulario(self):
        claves_requeridas = {"arbol", "nodo", "camino", "energia", "proteccion"}
        for dim in DIMENSIONES:
            faltantes = claves_requeridas - set(dim.vocabulario.keys())
            assert not faltantes, f"Dimensión {dim.nombre} le faltan: {faltantes}"

    def test_dimension_primaria_es_atzilut(self):
        assert DIMENSIONES[0].nombre == "Atzilut"
        assert DIMENSIONES[0].tradicion == "Kabbalah"

    def test_cada_nodo_tiene_sefirot_equiv(self):
        for dim in DIMENSIONES:
            for nodo in dim.nodos:
                assert nodo.sefirot_equiv, f"{dim.nombre}/{nodo.nombre} sin sefirot_equiv"

    def test_obtener_por_id(self):
        for i in range(16):
            dim = obtener_dimension(i)
            assert dim is not None
            assert dim.id == i

    def test_obtener_por_nombre(self):
        dim = obtener_dimension("Yggdrasil")
        assert dim is not None
        assert dim.tradicion == "Nórdico y Celta"

    def test_obtener_por_nombre_case_insensitive(self):
        assert obtener_dimension("kundalini") is not None
        assert obtener_dimension("KUNDALINI") is not None

    def test_obtener_inexistente(self):
        assert obtener_dimension(99) is None
        assert obtener_dimension("NoExiste") is None

    def test_tradiciones_cubiertas(self):
        tradiciones = {d.tradicion for d in DIMENSIONES}
        assert "Kabbalah" in tradiciones
        assert "Hinduismo" in tradiciones
        assert "Budismo" in tradiciones
        assert "Taoísmo" in tradiciones
        assert "Shintō" in tradiciones

    def test_capitulo_grimorio_no_vacio(self):
        for dim in DIMENSIONES:
            assert dim.capitulo_grimorio, f"Dimensión {dim.nombre} sin capítulo"


# ── RF-318: Persistencia de dimensión activa ─────────────────

class TestPersistencia:
    """RF-318: Cargar/guardar estado dimensional."""

    def test_estado_default(self):
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO",
                    Path(tempfile.gettempdir()) / "dim_test_noexist.json"):
            estado = cargar_estado()
            assert estado["dimension_activa"] == 0
            assert 0 in estado["descubiertas"]

    def test_guardar_y_cargar(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            guardar_estado({"dimension_activa": 3, "descubiertas": [0, 3]})
            estado = cargar_estado()
            assert estado["dimension_activa"] == 3
            assert 3 in estado["descubiertas"]

    def test_archivo_corrupto_retorna_default(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        archivo.write_text("{corrupto!!!", encoding="utf-8")
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            estado = cargar_estado()
            assert estado["dimension_activa"] == 0

    def test_dimension_activa_default(self, tmp_path):
        archivo = tmp_path / "dim_noexist.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            dim = dimension_activa()
            assert dim.id == 0
            assert dim.nombre == "Atzilut"

    def test_cambiar_dimension(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            dim = cambiar_dimension(2)
            assert dim is not None
            assert dim.nombre == "Yggdrasil"
            # Verificar persistencia
            assert dimension_activa().id == 2

    def test_cambiar_dimension_por_nombre(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            dim = cambiar_dimension("Hermes")
            assert dim is not None
            assert dim.tradicion == "Hermetismo y Alquimia"

    def test_cambiar_dimension_inexistente(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            result = cambiar_dimension(99)
            assert result is None

    def test_descubiertas_acumula(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            cambiar_dimension(0)
            cambiar_dimension(5)
            cambiar_dimension(10)
            estado = cargar_estado()
            assert 0 in estado["descubiertas"]
            assert 5 in estado["descubiertas"]
            assert 10 in estado["descubiertas"]


# ── RF-319: Contexto para system prompt ──────────────────────

class TestContextoPrompt:
    """RF-319: Generación de contexto dimensional para inyección."""

    def test_dimension_primaria_retorna_vacio(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            cambiar_dimension(0)
            ctx = obtener_contexto_prompt()
            assert ctx == ""

    def test_dimension_secundaria_retorna_contexto(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            cambiar_dimension(1)  # Anthropos (lente primario — FP-108)
            ctx = obtener_contexto_prompt()
            assert "LENTE ANTROPOLÓGICO" in ctx
            assert "Anthropos" in ctx
            assert "Antropología" in ctx

    def test_contexto_contiene_vocabulario(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            cambiar_dimension(2)  # Yggdrasil
            ctx = obtener_contexto_prompt()
            assert "Yggdrasil" in ctx
            assert "Ørlǫg" in ctx or "Destino" in ctx

    def test_contexto_contiene_nodos(self, tmp_path):
        archivo = tmp_path / "dimensiones.json"
        with patch("computadora.arquitectura.dimensiones._ARCHIVO_ESTADO", archivo):
            cambiar_dimension(3)  # Wu Xing
            ctx = obtener_contexto_prompt()
            assert "Madera" in ctx or "木" in ctx


# ── Integridad estructural ───────────────────────────────────

class TestIntegridad:
    """Verifica coherencia interna del metamodelo."""

    def test_todos_los_caminos_refieren_nodos_existentes(self):
        for dim in DIMENSIONES:
            nombres_nodos = {n.nombre for n in dim.nodos}
            for camino in dim.caminos:
                assert camino.de in nombres_nodos, (
                    f"{dim.nombre}: camino.de='{camino.de}' no existe en nodos"
                )
                assert camino.a in nombres_nodos, (
                    f"{dim.nombre}: camino.a='{camino.a}' no existe en nodos"
                )

    def test_sefirot_validas(self):
        sefirot_validas = {
            "Keter", "Jojmá", "Biná", "Da'at", "Jesed",
            "Gevurá", "Tiféret", "Netzaj", "Hod", "Yesod", "Maljut",
        }
        for dim in DIMENSIONES:
            for nodo in dim.nodos:
                assert nodo.sefirot_equiv in sefirot_validas, (
                    f"{dim.nombre}/{nodo.nombre}: sefirot_equiv='{nodo.sefirot_equiv}' inválida"
                )

    def test_frozen_dataclasses(self):
        """Los dataclasses son inmutables."""
        nodo = DIMENSIONES[0].nodos[0]
        with pytest.raises(AttributeError):
            nodo.nombre = "Modificado"

        dim = DIMENSIONES[0]
        with pytest.raises(AttributeError):
            dim.nombre = "Modificado"

