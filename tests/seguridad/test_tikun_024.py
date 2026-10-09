"""FP-061 → FP-071 test_tikun_024.py — RF-247: Auto-reinicio.

RF-168 original: hot-reload notificaba reinicio pendiente.
RF-247: reemplazado por auto-reinicio automático (subprocess.Popen + QApplication.quit).
"""
import os
import re
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), os.pardir)


def _leer(ruta_relativa: str) -> str:
    fp = os.path.join(RAIZ, ruta_relativa)
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()


class TestRF247_AutoReinicio(unittest.TestCase):
    """Valida que el hot-reload hace auto-reinicio en vez de notificar."""

    @classmethod
    def setUpClass(cls):
        cls.src = _leer("computadora/interfaz/ventana_principal.py")

    def test_import_subprocess(self):
        """subprocess está importado para el auto-reinicio."""
        self.assertIn("import subprocess", self.src)

    def test_on_requiere_reinicio_lanza_bat(self):
        """_on_requiere_reinicio usa subprocess.Popen para lanzar iniciar_computadora.bat."""
        self.assertIn("subprocess.Popen", self.src)
        self.assertIn("iniciar_computadora.bat", self.src)

    def test_on_requiere_reinicio_quit(self):
        """_on_requiere_reinicio cierra la app con QApplication.quit()."""
        # Buscar QApplication.quit() cerca de subprocess.Popen
        idx = self.src.index("subprocess.Popen")
        block = self.src[idx:idx + 300]
        self.assertIn("QApplication.quit()", block)

    def test_no_reinicio_pendiente_flag(self):
        """Ya no existe el flag _reinicio_pendiente (removido por RF-247)."""
        self.assertNotIn("self._reinicio_pendiente = False", self.src)
        self.assertNotIn("self._archivos_reinicio: list[str] = []", self.src)

    def test_no_notificacion_manual(self):
        """Ya no pide al usuario que reinicie manualmente."""
        self.assertNotIn("Necesito que me reinicies", self.src)

    def test_rf247_comment(self):
        """El código tiene referencia a RF-247."""
        self.assertIn("RF-247", self.src)


if __name__ == "__main__":
    unittest.main()

