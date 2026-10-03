"""
⊕ Sal — Tests para golem/habilidades/copilot_bridge.py (WI-291)
Verifica el puente Golem → Copilot/IDE.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.habilidades.copilot_bridge import (
    DIR_COMPLETADAS,
    DIR_PENDIENTES,
    solicitar_a_copilot,
    verificar_respuesta,
)


# ═══════════════════════════════════════════════════════════════
# Directorios
# ═══════════════════════════════════════════════════════════════

class TestDirectorios:
    def test_dir_pendientes_existe(self):
        assert DIR_PENDIENTES.exists()

    def test_dir_completadas_existe(self):
        assert DIR_COMPLETADAS.exists()


# ═══════════════════════════════════════════════════════════════
# solicitar_a_copilot
# ═══════════════════════════════════════════════════════════════

class TestSolicitarACopilot:
    def test_crea_solicitud_y_retorna_confirmacion(self, tmp_path):
        with patch("golem.habilidades.copilot_bridge.DIR_PENDIENTES", tmp_path):
            result = solicitar_a_copilot("Agregar tests", proyecto="golem")
            assert "Solicitud" in result
            assert "creada" in result.lower() or "sol_" in result

            # Verificar que se creó el archivo
            archivos = list(tmp_path.glob("sol_*.json"))
            assert len(archivos) == 1

            data = json.loads(archivos[0].read_text("utf-8"))
            assert data["estado"] == "pendiente"
            assert "golem" in data["proyecto"].lower()

    def test_proyecto_propio(self, tmp_path):
        with patch("golem.habilidades.copilot_bridge.DIR_PENDIENTES", tmp_path):
            result = solicitar_a_copilot("Fix bug", proyecto="golem")
            archivos = list(tmp_path.glob("sol_*.json"))
            data = json.loads(archivos[0].read_text("utf-8"))
            assert data["requiere_reinicio"] is True

    def test_proyecto_externo(self, tmp_path):
        with patch("golem.habilidades.copilot_bridge.DIR_PENDIENTES", tmp_path):
            solicitar_a_copilot("Fix bug", proyecto="otro_proyecto")
            archivos = list(tmp_path.glob("sol_*.json"))
            data = json.loads(archivos[0].read_text("utf-8"))
            assert data["requiere_reinicio"] is False


# ═══════════════════════════════════════════════════════════════
# verificar_respuesta
# ═══════════════════════════════════════════════════════════════

class TestVerificarRespuesta:
    def test_sin_pendientes(self, tmp_path):
        with patch("golem.habilidades.copilot_bridge.DIR_PENDIENTES", tmp_path), \
             patch("golem.habilidades.copilot_bridge.DIR_COMPLETADAS", tmp_path / "comp"):
            (tmp_path / "comp").mkdir()
            result = verificar_respuesta()
            assert "no hay" in result.lower() or "no encontré" in result.lower()

    def test_solicitud_completada(self, tmp_path):
        comp_dir = tmp_path / "completadas"
        comp_dir.mkdir()
        sol = {"estado": "completada", "resultado": "Hecho"}
        (comp_dir / "sol_test.json").write_text(json.dumps(sol), encoding="utf-8")

        with patch("golem.habilidades.copilot_bridge.DIR_COMPLETADAS", comp_dir), \
             patch("golem.habilidades.copilot_bridge.DIR_PENDIENTES", tmp_path):
            result = verificar_respuesta("sol_test")
            assert "completada" in result.lower()

