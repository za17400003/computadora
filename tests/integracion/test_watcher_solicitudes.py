"""
⊕ Sal — Tests para golem/habilidades/watcher_solicitudes.py (WI-291)
Verifica el watcher de solicitudes del Golem.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.habilidades.watcher_solicitudes import (
    ARCHIVO_SIGNAL,
    DIR_COMPLETADAS,
    DIR_PENDIENTES,
    escribir_signal,
    revisar_pendientes,
)


# ═══════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════

class TestConstantes:
    def test_dir_pendientes_es_path(self):
        assert isinstance(DIR_PENDIENTES, Path)

    def test_dir_completadas_es_path(self):
        assert isinstance(DIR_COMPLETADAS, Path)

    def test_archivo_signal_es_path(self):
        assert isinstance(ARCHIVO_SIGNAL, Path)


# ═══════════════════════════════════════════════════════════════
# revisar_pendientes
# ═══════════════════════════════════════════════════════════════

class TestRevisarPendientes:
    def test_sin_solicitudes_retorna_lista_vacia(self, tmp_path):
        with patch("golem.habilidades.watcher_solicitudes.DIR_PENDIENTES", tmp_path):
            result = revisar_pendientes()
            assert result == []

    def test_con_solicitud_retorna_datos(self, tmp_path):
        sol = {"id": "sol_test", "descripcion_usuario": "Test", "timestamp": "2026-04-01"}
        (tmp_path / "sol_test.json").write_text(json.dumps(sol), encoding="utf-8")

        with patch("golem.habilidades.watcher_solicitudes.DIR_PENDIENTES", tmp_path):
            result = revisar_pendientes()
            assert len(result) == 1
            assert result[0]["id"] == "sol_test"


# ═══════════════════════════════════════════════════════════════
# escribir_signal
# ═══════════════════════════════════════════════════════════════

class TestEscribirSignal:
    def test_escribe_archivo_signal(self, tmp_path):
        signal_file = tmp_path / "NUEVA_SOLICITUD.txt"
        solicitud = {
            "id": "sol_001",
            "timestamp": "2026-04-01T00:00:00",
            "proyecto": "golem",
            "prioridad": "normal",
            "requiere_reinicio": False,
            "instrucciones_para_copilot": "Test instruction",
            "archivos_afectados": ["test.py"],
        }
        with patch("golem.habilidades.watcher_solicitudes.ARCHIVO_SIGNAL", signal_file):
            escribir_signal(solicitud)
            assert signal_file.exists()
            contenido = signal_file.read_text(encoding="utf-8")
            assert "sol_001" in contenido

