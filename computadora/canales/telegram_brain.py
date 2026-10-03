"""
📡 Sharvít Merajók — Canal Telegram → COMPUTADORA (נשמה Neshamá / N3)

Permite enviar órdenes a Computadora desde Telegram de forma privada y segura.
Las órdenes se procesan a través del Orquestador (Yesod)
con acceso al tercer cerebro (Copilot/Neshamá).

Uso:
    from computadora.canales.telegram_brain import TelegramBrain
    bot = TelegramBrain(orquestador, config)
    bot.iniciar_background()  # No bloquea — lanza en hilo daemon
"""

import asyncio
import threading

from loguru import logger

try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters,
    )

    TELEGRAM_DISPONIBLE = True
except ImportError:
    TELEGRAM_DISPONIBLE = False


class TelegramBrain:
    """Bot de Telegram que enruta mensajes al Orquestador de Computadora."""

    def __init__(self, orquestador, config):
        self.orquestador = orquestador
        self.config = config
        self.token = config.obtener("telegram.token", "")
        self.owner_id = config.obtener("telegram.owner_id", None)
        self._app = None
        self._loop = None
        self._thread = None

        if not self.token:
            logger.warning("Telegram: No hay token configurado en telegram.token")

        if not TELEGRAM_DISPONIBLE:
            logger.warning(
                "Telegram: python-telegram-bot no instalado. "
                "Ejecuta: pip install python-telegram-bot>=21.0"
            )

    def _es_owner(self, user_id: int) -> bool:
        """Verifica si el usuario es el propietario autorizado."""
        if not self.owner_id:
            return False
        return str(user_id) == str(self.owner_id)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler del comando /start."""
        if not self._es_owner(update.effective_user.id):
            logger.debug(
                f"📡 Telegram SKIP /start de {update.effective_user.id} "
                f"(no es owner {self.owner_id})"
            )
            return

        await update.message.reply_text(
            "🜂 Sharvít Merajók activo. Escribe tu orden, maestro."
        )
        logger.info(f"📡 Telegram: Owner conectado ({update.effective_user.id})")

    async def _manejar_mensaje(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler de mensajes de texto."""
        user = update.effective_user
        texto = (update.message.text or "").strip()

        logger.debug(
            f"📡 Telegram RECV: '{texto[:80]}' "
            f"de {user.first_name} (id={user.id})"
        )

        # Filtro de seguridad: solo el owner
        if not self._es_owner(user.id):
            logger.debug(
                f"📡 Telegram SKIP: usuario {user.id} no es owner {self.owner_id}"
            )
            return

        if not texto:
            return

        logger.info(f"📡 Telegram → COMPUTADORA: '{texto}' (de {user.first_name})")

        try:
            # Indicador de "escribiendo..."
            await update.message.chat.send_action("typing")

            # Procesar en hilo separado para no bloquear el event loop
            respuesta = await asyncio.to_thread(
                self.orquestador.procesar, texto
            )

            # Filtrar sentinels internos (acciones de UI que no aplican en remoto)
            _SENTINEL_MSGS = {
                "__DEMO_ANIMACIONES__": "Demo ejecutada en la PC, señor.",
                "__DEMO_HERRAMIENTAS__": "Demo Gevurá ejecutada en la PC, señor.",
                "__ALERTAS_OFF__": "Alertas del sistema desactivadas.",
                "__ALERTAS_ON__": "Alertas del sistema activadas.",
                "__MINIMIZAR__": "COMPUTADORA minimizada en la PC.",
            }
            if respuesta in _SENTINEL_MSGS:
                respuesta = _SENTINEL_MSGS[respuesta]

            if respuesta:
                logger.info(f"📡 Telegram → COMPUTADORA: '{respuesta[:120]}'")
                # Telegram tiene límite de 4096 caracteres por mensaje
                for i in range(0, len(respuesta), 4000):
                    fragmento = respuesta[i:i + 4000]
                    await update.message.reply_text(fragmento)
            else:
                logger.warning("📡 Telegram: Orquestador devolvió respuesta vacía")
                await update.message.reply_text("🜁 Silencio... COMPUTADORA no ha respondido.")

        except Exception as e:
            logger.error(
                f"📡 Telegram ERROR procesando '{texto}': {type(e).__name__}: {e}"
            )
            await update.message.reply_text(f"🜁 Error interno: {type(e).__name__}")

    async def iniciar(self):
        """Inicia el bot (bloquea). Usar iniciar_background() para no bloquear."""
        if not self.token:
            logger.error("Telegram: No se puede iniciar sin token")
            return
        if not TELEGRAM_DISPONIBLE:
            logger.error("Telegram: python-telegram-bot no instalado")
            return

        logger.info("📡 Iniciando Sharvít Merajók (Telegram)...")
        self._app = Application.builder().token(self.token).build()
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._manejar_mensaje)
        )

        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling(drop_pending_updates=True)
        logger.info("📡 Sharvít Merajók activo — polling iniciado")

        # Mantener vivo hasta que se cancele
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self.detener()

    async def detener(self):
        """Detiene el bot."""
        if self._app:
            try:
                await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
                logger.info("📡 Sharvít Merajók desconectado")
            except Exception as e:
                logger.debug(f"📡 Telegram detener: {e}")

    def iniciar_background(self):
        """Inicia el bot en un hilo de fondo. No bloquea."""
        if not self.token:
            logger.warning("Telegram: Sin token — Sharvít Merajók desactivado")
            return
        if not TELEGRAM_DISPONIBLE:
            logger.warning("Telegram: python-telegram-bot no instalado — desactivado")
            return

        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self.iniciar())
            except Exception as e:
                logger.error(f"📡 Telegram error: {type(e).__name__}: {e}")
            finally:
                self._loop.close()

        self._thread = threading.Thread(
            target=_run,
            name="SharvitMerajok-Telegram",
            daemon=True,
        )
        self._thread.start()
        logger.info("📡 Sharvít Merajók lanzado en hilo de fondo")

    def detener_sync(self):
        """Detiene el bot de forma síncrona (para llamar desde el hilo principal)."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.detener(), self._loop)


