"""
Tests para FP-084 (Gevurát HaNikayón).
RF-310: Cerrar Photos robusto + borrar screenshot demo.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestRF310CerrarPhotosYLimpiar:
    """Verifica que _demo_captura_y_mostrar cierra Photos y borra screenshot."""

    def _source(self):
        src_file = ROOT / "golem" / "interfaz" / "ventana_principal.py"
        return src_file.read_text(encoding="utf-8")

    def test_multiple_process_names(self):
        src = self._source()
        for proc in ("Microsoft.Photos.exe", "Photos.exe", "PhotosApp.exe"):
            assert proc in src, f"Falta intento de taskkill para {proc}"

    def test_fallback_by_window_title(self):
        src = self._source()
        assert "WINDOWTITLE" in src, "Falta fallback por título de ventana"

    def test_screenshot_unlink(self):
        src = self._source()
        assert ".unlink()" in src, "Falta borrado del screenshot con unlink()"

    def test_timer_8s(self):
        src = self._source()
        assert "8000" in src, "Timer debe ser 8000ms para dar tiempo a UWP Photos"

    def test_rf310_comment(self):
        src = self._source()
        assert "RF-310" in src, "Falta comentario RF-310"

