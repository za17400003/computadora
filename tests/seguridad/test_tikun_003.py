"""
Tests del ciclo Tikún 003 — FP-039 Shemiá Gevurá
Verifica:
  - _on_solicitar_permiso usa threading.Event (no _ultima_transcripcion_raw)
  - Guard FSM procesando→procesando eliminado
  - Imports y estructura
"""
import ast
import inspect
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestFP039_GevuraPermiso(unittest.TestCase):
    """Verificar que _on_solicitar_permiso usa threading.Event."""

    @classmethod
    def setUpClass(cls):
        cls.src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")

    def test_no_usa_ultima_transcripcion_raw(self):
        """_ultima_transcripcion_raw eliminado del código de permiso."""
        # Buscar solo en _on_solicitar_permiso
        match = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        self.assertIsNotNone(match, "_on_solicitar_permiso no encontrado")
        bloque = match.group()
        self.assertNotIn("_ultima_transcripcion_raw", bloque)

    def test_usa_threading_event(self):
        """_on_solicitar_permiso usa threading.Event para esperar."""
        match = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        bloque = match.group()
        self.assertIn("threading.Event", bloque)
        self.assertIn(".wait(", bloque)

    def test_activa_esperando_confirmacion(self):
        """Setea _esperando_confirmacion = True en escucha."""
        match = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        bloque = match.group()
        self.assertIn("_esperando_confirmacion = True", bloque)

    def test_desconecta_signal_al_salir(self):
        """Siempre desconecta texto_detectado al salir."""
        match = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        bloque = match.group()
        self.assertIn(".disconnect(", bloque)

    def test_timeout_15s(self):
        """Timeout de 15 segundos configurado."""
        match = re.search(
            r"def _on_solicitar_permiso\(.*?\n(?=    def |\nclass |\Z)",
            self.src, re.DOTALL
        )
        bloque = match.group()
        self.assertIn("timeout=15", bloque)


class TestFP039_FSMGuard(unittest.TestCase):
    """Verificar guards FSM para procesando→procesando."""

    @classmethod
    def setUpClass(cls):
        cls.src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")

    def test_guard_en_al_fragmento_hablado(self):
        """cambiar_estado('procesando') tiene guard != procesando."""
        # La línea debe tener el guard antes
        patron = r'if self\._estado != "procesando":\s+self\.cambiar_estado\("procesando"\)'
        self.assertTrue(re.search(patron, self.src), "Guard FSM no encontrado en _al_fragmento_hablado")

    def test_guard_en_al_tts_cola_vacia(self):
        """Guard en _al_tts_cola_vacia para procesando."""
        patron = r'if self\._pensando and self\._estado != "procesando"'
        self.assertTrue(re.search(patron, self.src), "Guard FSM no encontrado en _al_tts_cola_vacia")


class TestImports(unittest.TestCase):
    """Verificar que los módulos siguen importando sin error."""

    def test_import_ventana_principal_ast(self):
        src = (RAIZ / "computadora" / "interfaz" / "ventana_principal.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        self.assertIsInstance(tree, ast.Module)

    def test_import_escucha_ast(self):
        src = (RAIZ / "computadora" / "voz" / "escucha.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        self.assertIsInstance(tree, ast.Module)


class TestRegresion(unittest.TestCase):
    """Regresión: locks de FP-036/FP-038 siguen presentes."""

    def test_locks_fp036(self):
        for mod, lock in [
            ("computadora/habilidades/herramientas.py", "_gestor_permisos_lock"),
            ("computadora/cerebro/copilot_api.py", "_instancia_lock"),
        ]:
            src = (RAIZ / mod).read_text(encoding="utf-8")
            self.assertIn(lock, src, f"Lock {lock} desapareció de {mod}")

    def test_locks_fp038(self):
        for mod, lock in [
            ("computadora/nucleo/eventos.py", "_bus_global_lock"),
            ("computadora/nucleo/ciclo_circadiano.py", "_ciclo_lock"),
            ("computadora/memoria/memoria.py", "_compressor_lock"),
        ]:
            src = (RAIZ / mod).read_text(encoding="utf-8")
            self.assertIn(lock, src, f"Lock {lock} desapareció de {mod}")


if __name__ == "__main__":
    unittest.main()

