import unittest
from computadora.nucleo.gestor_procesos import obtener_gestor_procesos

class TestGestorProcesos(unittest.TestCase):
    def test_basico(self):
        gestor = obtener_gestor_procesos()
        self.assertIsNotNone(gestor)

if __name__ == "__main__":
    unittest.main()
