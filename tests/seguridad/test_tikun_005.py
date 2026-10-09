"""
Tests del ciclo Tikún 005 — FP-042 Pekudá Yeshirá + Tikún Inertzia
Verifica:
  A) orden_directa en ejecutar_herramienta y GestorPermisos.solicitar
  B1) Inercia amortiguada (40%) durante drag/impulso — no zeroed
  B2) _pos_anterior sync en snap final de _interpolar_movimiento
"""
import ast
import inspect
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestFP042A_OrdenDirecta(unittest.TestCase):
    """Verificar param orden_directa en cadena permisos."""

    @classmethod
    def setUpClass(cls):
        cls.herr_src = (RAIZ / "computadora" / "habilidades" / "herramientas.py").read_text(encoding="utf-8")
        cls.perm_src = (RAIZ / "computadora" / "nucleo" / "permisos.py").read_text(encoding="utf-8")
        cls.nlu_src = (RAIZ / "computadora" / "cerebro" / "nlu.py").read_text(encoding="utf-8")

    def test_ejecutar_herramienta_tiene_orden_directa(self):
        """ejecutar_herramienta tiene parámetro orden_directa."""
        self.assertIn("orden_directa", self.herr_src.split("def ejecutar_herramienta")[1][:200])

    def test_gestor_solicitar_tiene_orden_directa(self):
        """GestorPermisos.solicitar tiene parámetro orden_directa."""
        self.assertIn("orden_directa", self.perm_src.split("def solicitar")[1][:200])

    def test_gestor_auto_aprueba_accion_directa(self):
        """GestorPermisos auto-aprueba nivel 'accion' cuando orden_directa=True."""
        from computadora.nucleo.permisos import GestorPermisos
        g = GestorPermisos()
        # Sin callback UI: orden_directa=True + accion → True
        self.assertTrue(g.solicitar("test_accion", "accion", orden_directa=True))
        # Sin callback UI: orden_directa=True + admin → False (admin NUNCA auto-aprueba)
        self.assertFalse(g.solicitar("test_admin", "admin", orden_directa=True))
        # Sin callback UI: orden_directa=False + accion → False (no hay UI)
        self.assertFalse(g.solicitar("test_sin_directa", "accion", orden_directa=False))

    def test_registro_auto_aprobado_orden_directa(self):
        """El log registra 'auto_aprobado_orden_directa' para ordenes directas."""
        self.assertIn("auto_aprobado_orden_directa", self.perm_src)

    def test_nlu_n1_pasa_orden_directa(self):
        """Las llamadas N1 en nlu.py pasan orden_directa=True."""
        # Buscar todas las líneas con ejecutar_herramienta( que no sean import
        for i, linea in enumerate(self.nlu_src.splitlines(), 1):
            stripped = linea.strip()
            if "ejecutar_herramienta(" in stripped and not stripped.startswith(("from ", "import ", "#")):
                # Puede ser multi-línea — buscar orden_directa en ventana
                bloque = "\n".join(self.nlu_src.splitlines()[i-1:i+4])
                self.assertIn("orden_directa=True", bloque,
                              f"L{i}: {stripped[:80]}")

    def test_nlu_n2_tool_loop_pasa_orden_directa(self):
        """La llamada N2 (tool-loop Ollama) pasa orden_directa=True."""
        # Buscar en el contexto del tool loop N2
        self.assertIn("ejecutar_herramienta(nombre, args, orden_directa=True)", self.nlu_src)

    def test_ast_valido_herramientas(self):
        """herramientas.py parsea sin errores de sintaxis."""
        ast.parse(self.herr_src)

    def test_ast_valido_permisos(self):
        """permisos.py parsea sin errores de sintaxis."""
        ast.parse(self.perm_src)


class TestFP042B1_InerciaAmortiguada(unittest.TestCase):
    """Verificar que HF-028 ya no zeroes inercia durante drag/impulso."""

    @classmethod
    def setUpClass(cls):
        cls.src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")

    def test_no_zero_delta_durante_drag(self):
        """No debe existir 'dx, dy = 0.0, 0.0' en sección de inercia."""
        # Buscar en contexto de partículas
        bloque_inercia = self.src[self.src.index("_raw_dx"):self.src.index("_raw_dx") + 500]
        self.assertNotIn("dx, dy = 0.0, 0.0", bloque_inercia)

    def test_amortiguacion_40_presente(self):
        """RF-135: Amortiguación dinámica reemplaza el 40% fijo."""
        self.assertIn("0.4 + 0.3", self.src, "Falta fórmula dinámica RF-135")

    def test_comentario_fp042(self):
        """Comentario RF-135 presente en la sección de amortiguación."""
        self.assertIn("RF-135", self.src)


class TestFP042B2_SnapFinalSync(unittest.TestCase):
    """Verificar sync de _pos_anterior en snap final de _interpolar_movimiento."""

    @classmethod
    def setUpClass(cls):
        cls.src = (RAIZ / "computadora" / "interfaz" / "vida_autonoma.py").read_text(encoding="utf-8")

    def test_snap_final_sync_pos_anterior(self):
        """RF-340: El snap final (dist < 2.0) actualiza render_offset y limpia objetivo."""
        # Extraer bloque snap final
        idx = self.src.index("dist < 2.0")
        bloque = self.src[idx:idx + 400]
        ret_idx = bloque.index("return")
        antes_return = bloque[:ret_idx]
        self.assertIn("_render_offset_x", antes_return)
        self.assertIn("_pos_objetivo = None", antes_return)

    def test_ast_valido_vida_autonoma(self):
        """vida_autonoma.py parsea sin errores de sintaxis."""
        ast.parse(self.src)


class TestFP042_Regression(unittest.TestCase):
    """Locks: no romper FP-041 ni FP-039."""

    @classmethod
    def setUpClass(cls):
        cls.vp_src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")

    def test_gevura_esperando_sigue(self):
        """FP-041: _gevura_esperando sigue presente."""
        self.assertIn("self._gevura_esperando", self.vp_src)

    def test_particula_class_presente(self):
        """FP-024: clase Particula intacta."""
        self.assertIn("class Particula:", self.vp_src)

    def test_coef_arrastre_intacto(self):
        """FP-024: coef_arrastre=0.92 intacto."""
        self.assertIn("coef_arrastre", self.vp_src)
        self.assertIn("0.92", self.vp_src)


if __name__ == "__main__":
    unittest.main()

