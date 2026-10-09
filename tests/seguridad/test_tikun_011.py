"""FP-048 Tikún HaDibúr — Tests de Reparación del Habla.

RF-125: Tikún Néfesh (regex faltantes)
RF-126: Tikún Tiféret (sanitización de respuestas Ollama)
RF-127: Tests
"""
import sys, os, re, inspect
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest


class TestRF125_RegexFaltantes(unittest.TestCase):
    """RF-125: Tikún Néfesh — regex N1 faltantes."""

    def _get_re(self, name):
        mod = __import__('computadora.cerebro.nlu', fromlist=[name])
        return getattr(mod, name)

    def test_demo_animaciones_standalone_malhut(self):
        """D1: 'malhut' solo dispara demo"""
        rx = self._get_re('_RE_DEMO_ANIMACIONES')
        self.assertIsNotNone(rx.search("malhut"))

    def test_demo_animaciones_standalone_malhud(self):
        """D1: 'malhud' solo dispara demo"""
        rx = self._get_re('_RE_DEMO_ANIMACIONES')
        self.assertIsNotNone(rx.search("malhud"))

    def test_demo_animaciones_standalone_maljut(self):
        """D1: 'maljut' solo dispara demo"""
        rx = self._get_re('_RE_DEMO_ANIMACIONES')
        self.assertIsNotNone(rx.search("maljut"))

    def test_demo_animaciones_with_prefix_still_works(self):
        """D1: 'demo de malhut' sigue funcionando"""
        rx = self._get_re('_RE_DEMO_ANIMACIONES')
        self.assertIsNotNone(rx.search("demo de malhut"))
        self.assertIsNotNone(rx.search("muéstrame tu maljut"))

    def test_tzimtzum_ocultate(self):
        """D2: 'ocúltate' dispara tzimtzum"""
        rx = self._get_re('_RE_TZIMTZUM')
        self.assertIsNotNone(rx.search("ocúltate"))
        self.assertIsNotNone(rx.search("ocultate"))

    def test_tzimtzum_escondete_still_works(self):
        """D2: 'escóndete' sigue funcionando"""
        rx = self._get_re('_RE_TZIMTZUM')
        self.assertIsNotNone(rx.search("escóndete"))


class TestRF126_SanitizacionOllama(unittest.TestCase):
    """RF-126: Tikún Tiféret — sanitización respuestas."""

    def test_system_prompt_identity_blind(self):
        """D6: System prompt tiene blindaje de identidad"""
        mod = __import__('computadora.cerebro.nlu', fromlist=['SISTEMA_PROMPT'])
        self.assertIn('IDENTIDAD BLINDADA', mod.SISTEMA_PROMPT)
        self.assertIn('NO eres Gemma', mod.SISTEMA_PROMPT)

    def test_repeat_penalty_in_options(self):
        """D5: repeat_penalty configurado en payloads Ollama"""
        src_file = inspect.getfile(__import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora']))
        with open(src_file, encoding='utf-8') as f:
            code = f.read()
        self.assertIn('"repeat_penalty": 1.3', code)
        self.assertIn('"repeat_last_n": 64', code)

    def test_limpiar_para_voz_estado_interno_sin_corchetes(self):
        """D3: sanitizer atrapa 'Estado interno:' sin corchetes"""
        mod = __import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora'])
        cerebro = mod.CerebroComputadora.__new__(mod.CerebroComputadora)
        resultado = cerebro._limpiar_para_voz(
            "Estado interno: Estás de buen humor, puedes ser más expresivo."
        )
        self.assertEqual(resultado.strip(), "")

    def test_limpiar_para_voz_herramienta_suelta(self):
        """D4: sanitizer suprime nombre de herramienta suelto"""
        mod = __import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora'])
        cerebro = mod.CerebroComputadora.__new__(mod.CerebroComputadora)
        resultado = cerebro._limpiar_para_voz("listar_directorio")
        self.assertEqual(resultado, "")

    def test_limpiar_para_voz_antirepeticion(self):
        """D5: sanitizer trunca frases repetidas 3+ veces"""
        mod = __import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora'])
        cerebro = mod.CerebroComputadora.__new__(mod.CerebroComputadora)
        texto_repetido = "Hola señor. Sentí una caricia. Sentí una caricia. Sentí una caricia. Sentí una caricia."
        resultado = cerebro._limpiar_para_voz(texto_repetido)
        self.assertLess(len(resultado), len(texto_repetido))
        self.assertEqual(resultado.count("Sentí una caricia"), 1)

    def test_respuesta_es_inutil_repeticion(self):
        """D5: _respuesta_es_inutil detecta repetición aunque len>300"""
        mod = __import__('computadora.cerebro.nlu', fromlist=['CerebroComputadora'])
        cerebro = mod.CerebroComputadora.__new__(mod.CerebroComputadora)
        texto = "Sentí una caricia del amo. " * 50  # >300 chars, repetitivo
        self.assertTrue(cerebro._respuesta_es_inutil(texto))

    def test_listar_directorio_en_fallback(self):
        """D4: listar_directorio reconocido por extraer_tool_por_nombre"""
        from computadora.cerebro.parseo_herramientas import extraer_tool_por_nombre
        result = extraer_tool_por_nombre("listar_directorio")
        self.assertIsNotNone(result)
        self.assertEqual(result["herramienta"], "listar_directorio")
        self.assertEqual(result["args"]["ruta"], ".")


if __name__ == '__main__':
    unittest.main()

