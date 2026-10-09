"""
Tests para FP-081 (Shomer HaDemo VeHaKelim).
RF-302: Guard anti-doble-fire en _demo_ejecutar_paso.
RF-303: Mapeo UWP Photos en cerrar_aplicacion.
RF-304: Dependencias opcionales en requirements.txt e iniciar_computadora.bat.
"""

import inspect
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════
# RF-302: Guard _demo_paso_en_curso
# ═══════════════════════════════════════════

class TestRF302GuardAntiDobleFire:
    """Verifica que _demo_ejecutar_paso tiene guard contra doble-fire (source-level)."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        src_file = ROOT / "computadora" / "interfaz" / "ventana_principal.py"
        self._full_src = src_file.read_text(encoding="utf-8")

    def test_guard_flag_check_exists(self):
        assert "_demo_paso_en_curso" in self._full_src, \
            "Falta flag _demo_paso_en_curso en ventana_principal.py"

    def test_guard_uses_getattr(self):
        assert re.search(r"getattr.*_demo_paso_en_curso", self._full_src), \
            "Debe usar getattr para evitar AttributeError"

    def test_guard_sets_true_before_action(self):
        assert "_demo_paso_en_curso = True" in self._full_src, \
            "Debe activar flag antes de ejecutar paso"

    def test_guard_resets_false(self):
        assert "_demo_paso_en_curso = False" in self._full_src, \
            "Debe resetear flag en _siguiente"


# ═══════════════════════════════════════════
# RF-303: Mapeo UWP Photos en cerrar_aplicacion
# ═══════════════════════════════════════════

class TestRF303UWPPhotosMapping:
    """Verifica que cerrar_aplicacion mapea correctamente Microsoft.Photos."""

    def _procesos(self):
        from computadora.habilidades.sistema import cerrar_aplicacion
        src = inspect.getsource(cerrar_aplicacion)
        return src

    def test_microsoft_photos_mapped(self):
        src = self._procesos()
        assert "Microsoft.Photos.exe" in src

    @pytest.mark.parametrize("alias", [
        "microsoft.photos",
        "photos",
        "fotos",
        "visor de fotos",
    ])
    def test_alias_present_in_procesos(self, alias):
        src = self._procesos()
        assert f'"{alias}"' in src, f'Alias "{alias}" no encontrado en procesos dict'


# ═══════════════════════════════════════════
# RF-304: Dependencias opcionales
# ═══════════════════════════════════════════

class TestRF304DependenciasOpcionales:
    """Verifica que requirements.txt e iniciar_computadora.bat mencionan face-recognition."""

    def test_requirements_mentions_face_recognition(self):
        reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        assert "face-recognition" in reqs, "requirements.txt no menciona face-recognition"

    def test_requirements_mentions_dlib(self):
        reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        assert "dlib" in reqs, "requirements.txt no menciona dlib"

    def test_bat_mentions_face_recognition(self):
        bat = (ROOT / "iniciar_computadora.bat").read_text(encoding="utf-8")
        assert "face_recognition" in bat or "face-recognition" in bat, \
            "iniciar_computadora.bat no verifica face-recognition"

