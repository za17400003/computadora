"""
🪄 Cetro Mágico — Canal Discord → Computadora (נשמה Neshamá / N3)

Permite enviar órdenes a Computadora desde Discord.
Las órdenes se procesan a través del Orquestador (Yesod)
con acceso al tercer cerebro (Copilot/Neshamá).

Uso:
    from computadora.canales.discord_brain import DiscordBrain
    bot = DiscordBrain(orquestador, config)
    await bot.iniciar()  # Bloquea — lanzar en hilo/tarea separada
"""

import asyncio
import threading
from pathlib import Path

import discord
from discord import Intents
from loguru import logger


class DiscordBrain:
    """Bot de Discord que enruta mensajes al Orquestador de Computadora."""

    # Prefijo para comandos (evita responder a todo)
    PREFIJO = "computadora "
    # Alias legacy de compatibilidad
    PREFIJO_LEGADO = "computadora "
    # Canal restringido (opcional, None = responde en cualquier canal)
    CANAL_NOMBRE = None

    def __init__(self, orquestador, config):
        self.orquestador = orquestador
        self.config = config
        self.token = config.obtener("discord.token", "")
        self.canal_id = config.obtener("discord.canal_id", None)
        self.owner_id = config.obtener("discord.owner_id", None)

        if not self.token:
            logger.warning("Discord: No hay token configurado en discord.token")

        # Configurar intents mínimos necesarios
        intents = Intents.default()
        intents.message_content = True  # Necesario para leer mensajes

        self.client = discord.Client(intents=intents)
        self._registrar_eventos()
        self._loop = None
        self._thread = None

    def _registrar_eventos(self):
        """Registra handlers de eventos del bot."""

        @self.client.event
        async def on_ready():
            logger.info(f"🪄 Cetro Mágico conectado: {self.client.user}")
            logger.info(f"   Servidores: {len(self.client.guilds)}")
            logger.info(f"   Intents message_content: {self.client.intents.message_content}")
            logger.info(f"   Owner ID configurado: {self.owner_id}")
            logger.info(f"   Canal ID configurado: {self.canal_id}")

        @self.client.event
        async def on_message(message):
            # Log de TODA recepción (observabilidad)
            canal_nombre = getattr(message.channel, 'name', 'DM')
            logger.debug(
                f"🪄 Discord RECV: '{message.content[:80]}' "
                f"de {message.author} (id={message.author.id}) "
                f"en #{canal_nombre} (id={message.channel.id})"
            )

            # No responder a sí mismo
            if message.author == self.client.user:
                logger.debug("🪄 Discord SKIP: mensaje propio")
                return

            # Filtro de seguridad: solo el owner puede comandar
            if self.owner_id and str(message.author.id) != str(self.owner_id):
                logger.debug(f"🪄 Discord SKIP: autor {message.author.id} no es owner {self.owner_id}")
                return

            # Filtro de canal (si está configurado)
            if self.canal_id and str(message.channel.id) != str(self.canal_id):
                logger.debug(f"🪄 Discord SKIP: canal {message.channel.id} no es el configurado {self.canal_id}")
                return

            texto = message.content.strip()

            # El owner siempre habla con Computadora — no necesita prefijo
            # Otros usuarios (si no hay owner_id) necesitan prefijo o mención
            es_owner = self.owner_id and str(message.author.id) == str(self.owner_id)
            mencion = f"<@{self.client.user.id}>"
            if texto.lower().startswith(self.PREFIJO):
                comando = texto[len(self.PREFIJO):].strip()
            elif texto.lower().startswith(self.PREFIJO_LEGADO):
                comando = texto[len(self.PREFIJO_LEGADO):].strip()
            elif texto.startswith(mencion):
                comando = texto[len(mencion):].strip()
            elif es_owner:
                comando = texto  # Owner no necesita prefijo
            else:
                logger.debug(f"🪄 Discord SKIP: sin prefijo ni mención de {message.author}")
                return  # Ignorar mensajes sin prefijo de no-owners

            if not comando:
                await message.reply("🜂 El cetro espera tu orden, maestro.")
                return

            logger.info(f"🪄 Discord → Computadora: '{comando}' (de {message.author})")

            try:
                # Indicador de escritura mientras procesa
                async with message.channel.typing():
                    # Procesar en hilo separado para no bloquear el event loop
                    respuesta = await asyncio.to_thread(
                        self.orquestador.procesar, comando
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
                    logger.info(f"🪄 Discord ← Computadora: '{respuesta[:120]}'")
                    # Discord tiene límite de 2000 caracteres
                    for i in range(0, len(respuesta), 1900):
                        fragmento = respuesta[i:i + 1900]
                        await message.reply(fragmento)
                else:
                    logger.warning("🪄 Discord: Orquestador devolvió respuesta vacía")
                    await message.reply("🜁 Silencio... COMPUTADORA no ha respondido.")
            except Exception as e:
                logger.error(f"🪄 Discord ERROR procesando '{comando}': {type(e).__name__}: {e}")
                await message.reply(f"🜁 Error interno: {type(e).__name__}")

    async def iniciar(self):
        """Inicia el bot (bloquea). Usar iniciar_background() para no bloquear."""
        if not self.token:
            logger.error("Discord: No se puede iniciar sin token")
            return
        logger.info("🪄 Iniciando Cetro Mágico (Discord)...")
        await self.client.start(self.token)

    async def detener(self):
        """Detiene el bot."""
        if self.client and not self.client.is_closed():
            await self.client.close()
            logger.info("🪄 Cetro Mágico desconectado")

    def iniciar_background(self):
        """Inicia el bot en un hilo de fondo. No bloquea."""
        if not self.token:
            logger.warning("Discord: Sin token — Cetro Mágico desactivado")
            return

        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self.iniciar())
            except discord.PrivilegedIntentsRequired:
                logger.warning(
                    "🪄 Discord: MESSAGE CONTENT INTENT no habilitado. "
                    "Ve a https://discord.com/developers/applications/ → Bot → "
                    "Privileged Gateway Intents → activa MESSAGE CONTENT INTENT"
                )
            except discord.LoginFailure:
                logger.error("🪄 Discord: Token inválido o revocado. Verifica discord.token en config.json")
            except Exception as e:
                logger.error(f"🪄 Discord error: {type(e).__name__}: {e}")
            finally:
                self._loop.close()

        self._thread = threading.Thread(
            target=_run,
            name="CetroMagico-Discord",
            daemon=True
        )
        self._thread.start()
        logger.info("🪄 Cetro Mágico lanzado en hilo de fondo")

    def detener_sync(self):
        """Detiene el bot de forma síncrona (para llamar desde el hilo principal)."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.detener(), self._loop)


