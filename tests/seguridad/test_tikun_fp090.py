"""Tests para TelegramBrain — FP-090 Sharvít Merajók."""

import asyncio
from unittest.mock import MagicMock, AsyncMock

import pytest

from computadora.canales.telegram_brain import TelegramBrain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class ConfigFake:
    """Config mínima para tests."""

    def __init__(self, datos=None):
        self._datos = datos or {}

    def obtener(self, clave, default=None):
        partes = clave.split(".")
        valor = self._datos
        for p in partes:
            if isinstance(valor, dict):
                valor = valor.get(p, default)
            else:
                return default
        return valor


def _config_tg():
    return ConfigFake({"telegram": {"token": "FAKE_TOKEN", "owner_id": "12345"}})


def _config_vacia():
    return ConfigFake({})


def _orq():
    orq = MagicMock()
    orq.procesar = MagicMock(return_value="Respuesta del Computadora")
    return orq


def _update(user_id=12345, text="hola computadora", first_name="Owner"):
    u = MagicMock()
    u.effective_user.id = user_id
    u.effective_user.first_name = first_name
    u.message.text = text
    u.message.reply_text = AsyncMock()
    u.message.chat.send_action = AsyncMock()
    return u


# ---------------------------------------------------------------------------
# Tests de construcción
# ---------------------------------------------------------------------------

class TestTelegramBrainInit:

    def test_crea_con_token(self):
        bot = TelegramBrain(_orq(), _config_tg())
        assert bot.token == "FAKE_TOKEN"
        assert bot.owner_id == "12345"

    def test_crea_sin_token(self):
        bot = TelegramBrain(_orq(), _config_vacia())
        assert bot.token == ""

    def test_es_owner_correcto(self):
        bot = TelegramBrain(_orq(), _config_tg())
        assert bot._es_owner(12345) is True
        assert bot._es_owner(99999) is False

    def test_es_owner_sin_config(self):
        bot = TelegramBrain(_orq(), _config_vacia())
        assert bot._es_owner(12345) is False

    def test_iniciar_background_sin_token_no_crashea(self):
        bot = TelegramBrain(_orq(), _config_vacia())
        bot.iniciar_background()
        assert bot._thread is None


# ---------------------------------------------------------------------------
# Tests de handlers
# ---------------------------------------------------------------------------

class TestTelegramBrainHandlers:

    def test_mensaje_owner_procesado(self):
        orq = _orq()
        bot = TelegramBrain(orq, _config_tg())
        update = _update()

        asyncio.get_event_loop().run_until_complete(
            bot._manejar_mensaje(update, MagicMock())
        )

        orq.procesar.assert_called_once_with("hola computadora")
        update.message.reply_text.assert_awaited_once_with("Respuesta del Computadora")

    def test_mensaje_no_owner_ignorado(self):
        orq = _orq()
        bot = TelegramBrain(orq, _config_tg())
        update = _update(user_id=99999, text="hack", first_name="Intruso")

        asyncio.get_event_loop().run_until_complete(
            bot._manejar_mensaje(update, MagicMock())
        )

        orq.procesar.assert_not_called()
        update.message.reply_text.assert_not_awaited()

    def test_mensaje_vacio_ignorado(self):
        orq = _orq()
        bot = TelegramBrain(orq, _config_tg())
        update = _update(text="   ")

        asyncio.get_event_loop().run_until_complete(
            bot._manejar_mensaje(update, MagicMock())
        )

        orq.procesar.assert_not_called()

    def test_respuesta_larga_fragmentada(self):
        orq = _orq()
        orq.procesar.return_value = "A" * 8500
        bot = TelegramBrain(orq, _config_tg())
        update = _update(text="comando largo")

        asyncio.get_event_loop().run_until_complete(
            bot._manejar_mensaje(update, MagicMock())
        )

        assert update.message.reply_text.await_count == 3

    def test_error_orquestador_no_crashea(self):
        orq = _orq()
        orq.procesar.side_effect = RuntimeError("boom")
        bot = TelegramBrain(orq, _config_tg())
        update = _update(text="crash test")

        asyncio.get_event_loop().run_until_complete(
            bot._manejar_mensaje(update, MagicMock())
        )

        update.message.reply_text.assert_awaited_once()
        assert "RuntimeError" in update.message.reply_text.call_args[0][0]

    def test_cmd_start_owner(self):
        bot = TelegramBrain(_orq(), _config_tg())
        update = _update()

        asyncio.get_event_loop().run_until_complete(
            bot._cmd_start(update, MagicMock())
        )

        update.message.reply_text.assert_awaited_once()

    def test_cmd_start_no_owner_ignorado(self):
        bot = TelegramBrain(_orq(), _config_tg())
        update = _update(user_id=99999)

        asyncio.get_event_loop().run_until_complete(
            bot._cmd_start(update, MagicMock())
        )

        update.message.reply_text.assert_not_awaited()

