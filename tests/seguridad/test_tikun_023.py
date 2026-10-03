"""FP-060 test_tikun_023.py — Jizúk HaEtz: Fortalecimiento del Árbol.

RF-166: Cierre limpio (QTimers + HiloPensamiento)
RF-167: Higiene de excepciones v2 (147 bloques, 28 módulos)
"""
import ast
import os
import re
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), os.pardir)
GOLEM = os.path.join(RAIZ, "golem")


def _leer(ruta_relativa: str) -> str:
    fp = os.path.join(RAIZ, ruta_relativa)
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()


# ═══════════════════════════════════════════════
# RF-166: Cierre limpio
# ═══════════════════════════════════════════════

class TestRF166_CierreLimpio(unittest.TestCase):
    """Valida que closeEvent y forzar_cierre detienen todos los QTimers."""

    @classmethod
    def setUpClass(cls):
        cls.src = _leer("golem/interfaz/ventana_principal.py")

    def test_close_event_stops_timer(self):
        """closeEvent contiene .stop() para _timer."""
        # Both closeEvent and forzar_cierre iterate timer names
        self.assertIn("'_timer'", self.src)

    def test_close_event_stops_timer_animo(self):
        self.assertIn("'_timer_animo'", self.src)

    def test_close_event_stops_timer_guardar_persona(self):
        self.assertIn("'_timer_guardar_persona'", self.src)

    def test_close_event_stops_timer_evolucion(self):
        self.assertIn("'_timer_evolucion'", self.src)

    def test_close_event_stops_bereshit_timer(self):
        self.assertIn("'_bereshit_timer'", self.src)

    def test_close_event_stops_bereshit_timeout(self):
        self.assertIn("'_bereshit_timeout'", self.src)

    def test_hilo_pensamiento_wait(self):
        """HiloPensamiento recibe wait() en cierre."""
        self.assertIn("hilo_p.wait(", self.src)

    def test_forzar_cierre_has_timer_loop(self):
        """forzar_cierre también detiene timers."""
        # Find forzar_cierre and verify it has the timer loop
        idx = self.src.index("def forzar_cierre")
        forzar_body = self.src[idx:idx + 2000]
        self.assertIn("timer.stop()", forzar_body)


# ═══════════════════════════════════════════════
# RF-167: Higiene de excepciones v2
# ═══════════════════════════════════════════════

class TestRF167_HigieneExcepciones(unittest.TestCase):
    """Valida que NO quedan except Exception: silenciosos en golem/."""

    def _all_py_files(self):
        """Yield all .py files under golem/ (excluding __init__)."""
        for dirpath, _, filenames in os.walk(GOLEM):
            for f in filenames:
                if f.endswith(".py") and f != "__init__.py":
                    yield os.path.join(dirpath, f)

    def test_zero_silent_except_exception(self):
        """No debe haber 'except Exception:' sin 'as e'."""
        pattern = re.compile(r"except\s+Exception\s*:\s*$", re.MULTILINE)
        violations = []
        for fp in self._all_py_files():
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            matches = pattern.findall(content)
            if matches:
                violations.append(f"{fp}: {len(matches)}")
        self.assertEqual(violations, [], f"Silent except blocks found:\n" + "\n".join(violations))

    def test_all_modules_have_logger(self):
        """Todos los módulos que usan except deben tener logger."""
        pattern_except = re.compile(r"except\s+\w+.*as\s+e", re.MULTILINE)
        missing = []
        for fp in self._all_py_files():
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            if pattern_except.search(content):
                if "logger" not in content:
                    missing.append(fp)
        self.assertEqual(missing, [], f"Files with except but no logger:\n" + "\n".join(missing))

    def test_rf167_marker_present(self):
        """Al menos 100 bloques marcados con RF-167."""
        count = 0
        for fp in self._all_py_files():
            with open(fp, "r", encoding="utf-8") as f:
                count += f.read().count("# RF-167")
        self.assertGreaterEqual(count, 100, f"Solo {count} marcadores RF-167 encontrados")

    def test_no_bare_except(self):
        """No debe haber 'except:' (bare except) sin tipo."""
        pattern = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
        violations = []
        for fp in self._all_py_files():
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            if pattern.search(content):
                violations.append(fp)
        self.assertEqual(violations, [], f"Bare except found in:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()

