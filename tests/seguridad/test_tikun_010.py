"""FP-047 Gilgúl HaNeshamá — Tests de Reencarnación del Alma.

RF-121: Tikún Maljut Partículas
RF-122: Tikún Netzaj-Jesed-Maljut
RF-123: Tikún Yesod (infra tests)
RF-124: Ohr Jadash (Albedo Renacido + regresión completa)
"""
import sys, os, math, inspect, configparser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest


class TestRF121_Particulas(unittest.TestCase):
    """RF-121: Tikún Maljut Partículas."""

    def _make_particula(self):
        from computadora.interfaz.ventana_principal import Particula, RADIO_RESPLANDOR
        return Particula(RADIO_RESPLANDOR), RADIO_RESPLANDOR

    def test_offset_clamp_exists(self):
        """A1: offset se clampea tras actualizar"""
        src = inspect.getsource(__import__('computadora.interfaz.ventana_principal', fromlist=['Particula']).Particula.actualizar)
        self.assertIn('_lim', src)
        self.assertIn('max(-_lim', src)

    def test_offset_clamp_effective(self):
        """A1: offset no supera radio*0.8 con delta enorme"""
        p, radio = self._make_particula()
        for _ in range(50):
            p.actualizar(delta_x=500.0, delta_y=500.0)
        lim = p.radio * 0.8
        self.assertLessEqual(abs(p.offset_x), lim + 0.01)
        self.assertLessEqual(abs(p.offset_y), lim + 0.01)

    def test_particulas_clear_dormido(self):
        """A3: cambiar_estado a dormido limpia partículas"""
        src = inspect.getsource(__import__('computadora.interfaz.ventana_principal', fromlist=['OrbeComputadora']).OrbeComputadora.cambiar_estado)
        self.assertIn('_particulas.clear()', src)

    def test_caricia_respeta_max(self):
        """A4: explosión caricia usa min() para respetar cap"""
        src_file = inspect.getfile(__import__('computadora.interfaz.ventana_principal', fromlist=['OrbeComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        # Buscar el pattern min(8, _max_particulas - len
        self.assertIn('min(8, self._max_particulas - len(self._particulas))', code)

    def test_brisa_respeta_max(self):
        """A4: brisa usa min() para respetar cap"""
        src_file = inspect.getfile(__import__('computadora.interfaz.ventana_principal', fromlist=['OrbeComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        self.assertIn('min(3, self._max_particulas - len(self._particulas))', code)

    def test_primaryscreen_null_check(self):
        """A2: primaryScreen tiene null-check"""
        src_file = inspect.getfile(__import__('computadora.interfaz.ventana_principal', fromlist=['OrbeComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        self.assertIn('if _scr is None', code)

    def test_drawstate_copy(self):
        """A5: _draw_state pasa copia de lista"""
        src = inspect.getsource(__import__('computadora.interfaz.ventana_principal', fromlist=['OrbeComputadora']).OrbeComputadora._draw_state)
        self.assertIn('self._particulas[:]', src)


class TestRF122_NetzajJesedMaljut(unittest.TestCase):
    """RF-122: Tikún Netzaj-Jesed-Maljut."""

    def test_compress_day_write_then_delete(self):
        """B1: compress_day solo borra raw si escritura exitosa"""
        src = inspect.getsource(__import__('computadora.memoria.memoria', fromlist=['compress_day']).compress_day)
        self.assertIn('_resumen_ok', src)
        self.assertIn('_muestra_ok', src)
        self.assertIn('if _resumen_ok or _muestra_ok', src)

    def test_proactividad_reusa_metaworkflow(self):
        """B2: _check_salud_computadora reutiliza instancia"""
        src = inspect.getsource(
            __import__('computadora.nucleo.proactividad', fromlist=['MotorProactividad']).MotorProactividad._check_salud_computadora
        )
        self.assertIn('_meta_workflow_inst', src)
        self.assertNotIn('mw = MetaWorkflow()', src)

    def test_watchdog_modelo_dinamico(self):
        """B3: watchdog no hardcodea modelo — deep check eliminado, solo shallow api/tags"""
        src = inspect.getsource(__import__('computadora.interfaz.watchdog', fromlist=['_check_ollama'])._check_ollama)
        # Deep check eliminado: no debe haber api/generate ni modelo hardcodeado
        self.assertNotIn('api/generate', src)
        self.assertIn('api/tags', src)


class TestRF123_InfraTests(unittest.TestCase):
    """RF-123: Tikún Yesod — Infraestructura de Tests."""

    def test_pyproject_pytest_config(self):
        """C1: pyproject.toml tiene configuración pytest"""
        toml_path = os.path.join(os.path.dirname(__file__), '..', 'pyproject.toml')
        with open(toml_path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('[tool.pytest.ini_options]', content)
        self.assertIn('python_functions', content)
        self.assertIn('test_*', content)

    def test_legacy_files_no_bare_sys_exit(self):
        """C2: Archivos legacy no tienen sys.exit a nivel de módulo"""
        for fname in ['test_fp037_ketiva.py', 'test_tikun_002.py']:
            fpath = os.path.join(os.path.dirname(__file__), fname)
            if not os.path.exists(fpath):
                continue
            with open(fpath, encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('sys.exit('):
                    # Must be inside if __name__ block
                    # Check that at least one of the previous 3 lines has __name__
                    prev = ''.join(lines[max(0, i-4):i-1])
                    self.assertIn('__name__', prev,
                                  f"{fname}:{i} has bare sys.exit without __name__ guard")


class TestRF124_OhrJadash(unittest.TestCase):
    """RF-124: Ohr Jadash — Albedo Renacido + Regresión Completa."""

    def test_regla_17_albedo_renacido(self):
        """D+E: Regla 17 contiene Albedo como fase propia con investigación"""
        wf_path = os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md')
        with open(wf_path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Investigación Esotérica Universal', content)
        self.assertIn('Benchmark de Workflow', content)
        self.assertIn('Ohr Jadash', content)

    def test_regla_20_regresion(self):
        """D: Regla 20 de regresión completa existe"""
        wf_path = os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md')
        with open(wf_path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn('Regresión completa obligatoria', content)
        self.assertIn('pytest tests/', content)


if __name__ == '__main__':
    unittest.main()

