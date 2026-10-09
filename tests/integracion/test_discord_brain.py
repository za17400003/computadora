"""
⊕ Sal — Tests para computadora/canales/discord_brain.py (WI-291)
Verifica la estructura del bot Discord (sin conexión real).
"""

from unittest.mock import MagicMock, patch

import pytest


class TestDiscordBrainImport:
    def test_clase_importable(self):
        from computadora.canales.discord_brain import DiscordBrain
        assert DiscordBrain is not None

    def test_prefijo_es_computadora(self):
        from computadora.canales.discord_brain import DiscordBrain
        assert DiscordBrain.PREFIJO.startswith("computadora")


class TestDiscordBrainInit:
    def test_instanciable_con_mock(self):
        from computadora.canales.discord_brain import DiscordBrain
        orq = MagicMock()
        config = MagicMock()
        config.obtener.return_value = ""
        bot = DiscordBrain(orq, config)
        assert bot.orquestador is orq
        assert bot.token == ""

