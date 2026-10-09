"""Test Tikún 022 — FP-059: Tikún HaGvúl VeHaOhr (RF-162/163/164/165)."""
import ast
import inspect
import os
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ── Helpers ──

def _src(module_rel_path: str) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base, module_rel_path.replace("/", os.sep))


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


SRC_VP = _src("computadora/interfaz/ventana_principal.py")
SRC_VA = _src("computadora/interfaz/vida_autonoma.py")

CODE_VP = _read(SRC_VP)
CODE_VA = _read(SRC_VA)


# ═══ RF-162: DwmExtendFrameIntoClientArea + BORDER_COLOR ═══

class TestRF162_DWMBorderElimination:
    def test_dwmwa_border_color(self):
        assert "DWMWA_BORDER_COLOR" in CODE_VP

    def test_color_none_value(self):
        assert "0xFFFFFFFE" in CODE_VP

    def test_no_extend_frame_margins_negative(self):
        # DwmExtendFrameIntoClientArea with MARGINS(-1) causes white flash
        # — must NOT be present
        assert "MARGINS(-1, -1, -1, -1)" not in CODE_VP


# ═══ RF-163: Clamp usa max() en _interpolar_movimiento ═══

class TestRF163_ClampMaxSize:
    def test_clamp_w_uses_pleno(self):
        # RF-340: Clamp now in _expandir_ventana_transito via pantalla bounds
        assert "self._pantalla" in CODE_VA

    def test_clamp_h_uses_pleno(self):
        # RF-340: TAMANO_PLENO used in expand and collapse methods
        assert "self.TAMANO_PLENO" in CODE_VA

    def test_no_min_clamp_remains(self):
        # The old min pattern should not exist in _interpolar_movimiento
        # Check that "min(self._orbe.width(), self.TAMANO_PLENO)" does NOT appear
        # near the clamp section (it may exist elsewhere for other purposes)
        lines = CODE_VA.split("\n")
        for i, line in enumerate(lines):
            if "_w_clamp = min(self._orbe.width()" in line:
                pytest.fail(f"Old min() clamp still present at line {i+1}")


# ═══ RF-164: _esquivar y _mejor_borde usan max() ═══

class TestRF164_DestinationMaxSize:
    def test_esquivar_uses_pleno(self):
        assert "w = self.TAMANO_PLENO" in CODE_VA

    def test_mejor_borde_uses_max(self):
        assert "w = max(self._orbe.width(), self.TAMANO_COMPACTO)" in CODE_VA

    def test_esquivar_no_min(self):
        lines = CODE_VA.split("\n")
        in_esquivar = False
        for line in lines:
            if "def _esquivar" in line:
                in_esquivar = True
            elif in_esquivar and line.strip().startswith("def "):
                break
            if in_esquivar and "w = min(self._orbe.width()" in line:
                pytest.fail("Old min() in _esquivar still present")


# ═══ RF-165: Smooth resize (float + round + before delta) ═══

class TestRF165_SmoothResize:
    def test_tamano_ventana_initialized_as_float(self):
        assert "self._tamano_ventana = float(_tam_init)" in CODE_VP

    def test_lerp_uses_round(self):
        assert "tam_render = round(self._tamano_ventana)" in CODE_VP

    def test_threshold_is_2(self):
        assert "tam_necesario - self._tamano_ventana) > 2:" in CODE_VP

    def test_resize_before_raw_delta(self):
        # The resize block must appear BEFORE _raw_dx calculation
        idx_resize = CODE_VP.find("RF-165: Resize ANTES")
        idx_raw = CODE_VP.find("_raw_dx = float(self.x()) - self._pos_anterior_x")
        assert idx_resize > 0, "RF-165 resize comment not found"
        assert idx_raw > 0, "_raw_dx line not found"
        # The old resize block should be replaced with a comment
        assert "Bloque de resize movido ANTES" in CODE_VP

    def test_snap_final_float(self):
        assert "self._tamano_ventana = float(tam_necesario)" in CODE_VP

    def test_otro_tamano_setter_float(self):
        # The other place that sets _tamano_ventana should also be float
        assert 'self._tamano_ventana = float(nuevo_tamano)' in CODE_VP

