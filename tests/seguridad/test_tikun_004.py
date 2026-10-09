"""
Tests del ciclo Tikún 004 — FP-041 Shemirat Gevurá
Verifica:
  - _gevura_esperando flag existe y se inicializa False
  - _al_recibir_voz tiene early return cuando _gevura_esperando=True
  - _on_solicitar_permiso activa/desactiva _gevura_esperando
  - Regression locks FP-039 + FP-040
"""
import ast
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestFP041_ShemiratGevura(unittest.TestCase):
    """Verificar blindaje de _al_recibir_voz durante Gevurá permiso."""

    @classmethod
    def setUpClass(cls):
        cls.src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")

    def test_gevura_esperando_init_false(self):
        """_gevura_esperando se inicializa como False en __init__."""
        self.assertIn("self._gevura_esperando = False", self.src)

    def test_al_recibir_voz_guard_gevura(self):
        """_al_recibir_voz tiene early return si _gevura_esperando."""
        bloque = re.search(
            r"def _al_recibir_voz\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        self.assertIsNotNone(bloque, "_al_recibir_voz no encontrado")
        texto = bloque.group()
        self.assertIn("self._gevura_esperando", texto)
        self.assertIn("return", texto.split("_gevura_esperando")[1][:60])

    def test_on_solicitar_permiso_activa_flag(self):
        """_on_solicitar_permiso establece _gevura_esperando = True."""
        bloque = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        self.assertIsNotNone(bloque, "_on_solicitar_permiso no encontrado")
        texto = bloque.group()
        self.assertIn("self._gevura_esperando = True", texto)

    def test_on_solicitar_permiso_desactiva_flag(self):
        """_on_solicitar_permiso limpia _gevura_esperando = False en cleanup."""
        bloque = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        texto = bloque.group()
        self.assertIn("self._gevura_esperando = False", texto)
        # Debe haber al menos 2 resets (normal + except)
        count = texto.count("self._gevura_esperando = False")
        self.assertGreaterEqual(count, 2, "Debe resetear en flujo normal Y en except")

    def test_threading_event_sigue_presente(self):
        """Regression FP-039: _on_solicitar_permiso sigue usando threading.Event."""
        bloque = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        texto = bloque.group()
        self.assertIn("threading.Event()", texto)
        self.assertNotIn("_ultima_transcripcion_raw", texto)


class TestFP041_AST(unittest.TestCase):
    """Verificar integridad AST post-cambio."""

    def test_ventana_principal_parsea(self):
        """ventana_principal.py se parsea sin errores de sintaxis."""
        src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")
        try:
            ast.parse(src)
        except SyntaxError as e:
            self.fail(f"SyntaxError en ventana_principal.py: {e}")


class TestFP041_RegressionLock(unittest.TestCase):
    """Locks de regresión para FPs anteriores."""

    def test_fp039_fsm_guard_procesando(self):
        """FP-039: guards FSM procesando→procesando siguen presentes."""
        src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")
        self.assertIn('if self._estado != "procesando":', src)

    def test_fp040_workflow_no_tiene_diagrama(self):
        """FP-040: DEVELOPMENT_WORKFLOW.md no contiene el diagrama ASCII duplicado."""
        wf = (RAIZ / "DEVELOPMENT_WORKFLOW.md").read_text(encoding="utf-8")
        self.assertNotIn("╔══════════════", wf, "Diagrama ASCII no debería estar en workflow")
        self.assertIn("ETZ HACHAIM OPERATIVO", wf)


if __name__ == "__main__":
    unittest.main()

