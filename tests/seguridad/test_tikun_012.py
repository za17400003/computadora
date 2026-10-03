"""FP-049 Tikún HaTnuá — Tests de Reparación del Movimiento.

RF-128: Demo regex acepta "ejecuta tu demo" sin sufijo maljut
RF-129: Inercia de partículas — pos_anterior solo se sincroniza en el timer
"""
import sys, os, re, inspect
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest


class TestRF128_DemoRegex(unittest.TestCase):
    """RF-128: _RE_DEMO_ANIMACIONES acepta variantes de 'ejecuta tu demo'."""

    def _get_re(self):
        return __import__('golem.cerebro.nlu', fromlist=['_RE_DEMO_ANIMACIONES'])._RE_DEMO_ANIMACIONES

    def test_ejecuta_tu_demo(self):
        self.assertIsNotNone(self._get_re().search("ejecuta tu demo"))

    def test_ejecuta_demo(self):
        self.assertIsNotNone(self._get_re().search("ejecuta demo"))

    def test_activa_tu_demo(self):
        self.assertIsNotNone(self._get_re().search("activa tu demo"))

    def test_haz_tu_demostracion(self):
        self.assertIsNotNone(self._get_re().search("haz tu demostración"))

    def test_hazme_demo_still_works(self):
        self.assertIsNotNone(self._get_re().search("hazme una demo"))

    def test_demo_de_maljut_still_works(self):
        self.assertIsNotNone(self._get_re().search("ejecuta tu demo de maljut"))

    def test_malhut_standalone_still_works(self):
        self.assertIsNotNone(self._get_re().search("malhut"))


class TestRF129_InerciaParticulas(unittest.TestCase):
    """RF-129: mouseMoveEvent y bloque impulso NO sincronizan _pos_anterior."""

    def test_mouseMoveEvent_no_sync_pos_anterior(self):
        """mouseMoveEvent no debe escribir _pos_anterior"""
        src = inspect.getsource(
            __import__('golem.interfaz.ventana_principal', fromlist=['OrbeComputadora']).OrbeComputadora.mouseMoveEvent
        )
        self.assertNotIn('_pos_anterior_x = float', src)
        self.assertNotIn('_pos_anterior_y = float', src)

    def test_impulse_block_no_sync_pos_anterior(self):
        """Bloque de impulso no debe escribir _pos_anterior"""
        src_file = inspect.getfile(__import__('golem.interfaz.ventana_principal', fromlist=['OrbeComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        # Find the impulse block (between "Impulso físico" and "self.update()")
        m = re.search(r'# Impulso físico.*?self\.update\(\)', code, re.DOTALL)
        self.assertIsNotNone(m, "No se encontró bloque de impulso")
        impulse_block = m.group(0)
        self.assertNotIn('_pos_anterior_x = float', impulse_block)
        self.assertNotIn('_pos_anterior_y = float', impulse_block)

    def test_animar_still_syncs_pos_anterior(self):
        """El timer (_animar) SÍ debe actualizar _pos_anterior"""
        src_file = inspect.getfile(__import__('golem.interfaz.ventana_principal', fromlist=['OrbeComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        # Find the particle update section
        m = re.search(r'# Actualizar partículas.*?self\._pos_anterior_y = float', code, re.DOTALL)
        self.assertIsNotNone(m, "_animar debe tener sync de pos_anterior en zona de partículas")


if __name__ == '__main__':
    unittest.main()

