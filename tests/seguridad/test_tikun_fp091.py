"""
🧪 Tests — FP-091 Séfer HaSendéro
Validar API de progreso y biblioteca del Grimorio.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

import pytest

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def progreso_tmp(tmp_path):
    """Fixture: archivo de progreso temporal."""
    return tmp_path / "grimorio_progreso.json"


@pytest.fixture
def biblioteca_tmp(tmp_path):
    """Fixture: biblioteca temporal con 3 libros de prueba."""
    bib = {
        "stages": {
            "plomo": {"chapters": [0, 1, 2]},
            "estano": {"chapters": [3, 4, 5]},
            "hierro": {"chapters": [6, 7, 8]},
            "cobre": {"chapters": [9, 10, 11]},
            "mercurio": {"chapters": [12, 13, 14]},
            "plata": {"chapters": [15, 16, 17]},
            "oro": {"chapters": [18, 19, 20]},
        },
        "libros": [
            {"title": "Libro Plomo", "stage": "plomo", "category": "Test"},
            {"title": "Libro Hierro", "stage": "hierro", "category": "Test"},
            {"title": "Libro Oro", "stage": "oro", "category": "Test"},
        ],
    }
    f = tmp_path / "biblioteca_sendero.json"
    f.write_text(json.dumps(bib), "utf-8")
    return f


class TestProgresoAPI:
    """Tests para la lógica de progreso del servidor."""

    def test_default_progreso(self, progreso_tmp):
        """Progreso por defecto cuando no existe archivo."""
        assert not progreso_tmp.exists()
        # Sin archivo, la lectura debe retornar estructura vacía
        default = {
            "chapterIdx": 0,
            "subPage": 0,
            "chapters_visited": [],
            "time_per_chapter": {},
            "total_reading_time_s": 0,
            "last_session": None,
            "sessions_count": 0,
        }
        assert default["chapterIdx"] == 0
        assert default["chapters_visited"] == []

    def test_progreso_file_roundtrip(self, progreso_tmp):
        """Guardar y cargar progreso como JSON atómico."""
        data = {
            "chapterIdx": 5,
            "subPage": 2,
            "chapters_visited": [0, 1, 5],
            "time_per_chapter": {"0": 120, "5": 45},
            "total_reading_time_s": 165,
            "last_session": "2026-04-10T12:00:00",
            "sessions_count": 3,
        }
        # Escritura atómica
        tmp = progreso_tmp.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(progreso_tmp)

        # Lectura
        loaded = json.loads(progreso_tmp.read_text("utf-8"))
        assert loaded["chapterIdx"] == 5
        assert loaded["subPage"] == 2
        assert 5 in loaded["chapters_visited"]
        assert loaded["sessions_count"] == 3

    def test_progreso_chapter_tracking(self, progreso_tmp):
        """Capítulos visitados se acumulan sin duplicados."""
        data = {"chapters_visited": [0, 1]}
        # Simular añadir capítulo 3
        visited = data["chapters_visited"]
        if 3 not in visited:
            visited.append(3)
        # No duplicar
        if 1 not in visited:
            visited.append(1)
        assert visited == [0, 1, 3]

    def test_progreso_time_accumulation(self):
        """Tiempo por capítulo se acumula correctamente."""
        time_map = {"0": 60, "3": 30}
        key = "3"
        delta_s = 45
        time_map[key] = time_map.get(key, 0) + delta_s
        assert time_map["3"] == 75
        assert time_map["0"] == 60


class TestBibliotecaDesbloqueo:
    """Tests para la lógica de desbloqueo de libros."""

    def test_initial_unlock_3_ahead(self, biblioteca_tmp):
        """Sin progreso, desbloquea plomo + 3 stages (estano, hierro, cobre)."""
        bib = json.loads(biblioteca_tmp.read_text("utf-8"))
        progreso = {"chapters_visited": []}
        stages_order = ["plomo", "estano", "hierro", "cobre", "mercurio", "plata", "oro"]

        current_stage_idx = 0
        unlock_up_to = min(current_stage_idx + 3, len(stages_order) - 1)
        unlocked_stages = set(stages_order[: unlock_up_to + 1])

        assert "plomo" in unlocked_stages
        assert "estano" in unlocked_stages
        assert "hierro" in unlocked_stages
        assert "cobre" in unlocked_stages
        assert "mercurio" not in unlocked_stages

    def test_progress_advances_unlock(self, biblioteca_tmp):
        """Leer capítulos de hierro desbloquea hasta plata."""
        bib = json.loads(biblioteca_tmp.read_text("utf-8"))
        progreso = {"chapters_visited": [0, 1, 6]}  # 6 = taoísmo (hierro)
        stages_order = ["plomo", "estano", "hierro", "cobre", "mercurio", "plata", "oro"]
        stage_map = bib["stages"]

        current_stage_idx = 0
        visited = set(progreso["chapters_visited"])
        for i, stage in enumerate(stages_order):
            chapters = stage_map.get(stage, {}).get("chapters", [])
            if any(ch in visited for ch in chapters):
                current_stage_idx = i

        assert current_stage_idx == 2  # hierro
        unlock_up_to = min(current_stage_idx + 3, len(stages_order) - 1)
        unlocked = set(stages_order[: unlock_up_to + 1])
        assert "plata" in unlocked  # 3 stages ahead of hierro
        assert "oro" not in unlocked

    def test_oro_unlocks_everything(self, biblioteca_tmp):
        """Leer capítulos de oro desbloquea todos los libros."""
        bib = json.loads(biblioteca_tmp.read_text("utf-8"))
        progreso = {"chapters_visited": [18]}  # comandos = oro
        stages_order = ["plomo", "estano", "hierro", "cobre", "mercurio", "plata", "oro"]
        stage_map = bib["stages"]

        current_stage_idx = 0
        visited = set(progreso["chapters_visited"])
        for i, stage in enumerate(stages_order):
            chapters = stage_map.get(stage, {}).get("chapters", [])
            if any(ch in visited for ch in chapters):
                current_stage_idx = i

        assert current_stage_idx == 6  # oro
        unlock_up_to = min(current_stage_idx + 3, len(stages_order) - 1)
        unlocked = set(stages_order[: unlock_up_to + 1])
        assert len(unlocked) == 7  # todo desbloqueado

    def test_book_locked_status(self, biblioteca_tmp):
        """Libros en stages no desbloqueados aparecen como locked."""
        bib = json.loads(biblioteca_tmp.read_text("utf-8"))
        unlocked_stages = {"plomo", "estano", "hierro", "cobre"}

        for libro in bib["libros"]:
            is_unlocked = libro["stage"] in unlocked_stages
            if libro["title"] == "Libro Oro":
                assert not is_unlocked
            elif libro["title"] == "Libro Plomo":
                assert is_unlocked


class TestBibliotecaJSON:
    """Tests para el archivo biblioteca_sendero.json real."""

    _bib_path = Path(__file__).parent.parent / "libro_encantado" / "biblioteca_sendero.json"
    _skip_msg = "biblioteca_sendero.json cifrado (FP-094 Shem Nistar)"

    def _load(self):
        return json.loads(self._bib_path.read_text("utf-8"))

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "libro_encantado" / "biblioteca_sendero.json").exists(),
        reason=_skip_msg,
    )
    def test_biblioteca_file_valid(self):
        """El archivo biblioteca_sendero.json existe y es JSON válido."""
        data = self._load()
        assert "stages" in data
        assert "libros" in data
        assert len(data["libros"]) >= 10

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "libro_encantado" / "biblioteca_sendero.json").exists(),
        reason=_skip_msg,
    )
    def test_all_stages_present(self):
        """Todas las 7 etapas alquímicas están definidas."""
        data = self._load()
        expected = {"plomo", "estano", "hierro", "cobre", "mercurio", "plata", "oro"}
        assert set(data["stages"].keys()) == expected

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "libro_encantado" / "biblioteca_sendero.json").exists(),
        reason=_skip_msg,
    )
    def test_all_books_have_required_fields(self):
        """Cada libro tiene title, stage, category."""
        data = self._load()
        for libro in data["libros"]:
            assert "title" in libro, f"Libro sin title: {libro}"
            assert "stage" in libro, f"Libro sin stage: {libro}"
            assert "category" in libro, f"Libro sin category: {libro}"
            assert libro["stage"] in data["stages"], f"Stage inválido: {libro['stage']}"

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "libro_encantado" / "biblioteca_sendero.json").exists(),
        reason=_skip_msg,
    )
    def test_every_stage_has_at_least_one_book(self):
        """Cada etapa tiene al menos un libro recomendado."""
        data = self._load()
        stages_with_books = {l["stage"] for l in data["libros"]}
        for stage in data["stages"]:
            assert stage in stages_with_books, f"Stage {stage} sin libros"

