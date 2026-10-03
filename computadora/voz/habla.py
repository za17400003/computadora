"""
הוד (Hod) — Esplendor. Claridad de expresión.
Módulo de habla de COMPUTADORA.
Usa edge-tts como motor principal y pyttsx3 como fallback.
"""

import asyncio
import os
import queue
import re
import tempfile

from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger


class HiloHabla(QThread):
    """Hilo que genera y reproduce voz a partir de texto."""

    habla_iniciada = pyqtSignal()
    habla_terminada = pyqtSignal()
    cola_vacia = pyqtSignal()  # Emitida cuando NO quedan más fragmentos tras hablar
    texto_a_recitar = pyqtSignal(str)  # Emitida con el texto antes de hablarlo

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._cola = queue.Queue()
        self._activo = True
        self._interrumpido = False
        self._hablando = False
        self._voz = config.obtener("voz.tts_voz", "es-MX-JorgeNeural")
        self._motor = config.obtener("voz.tts_motor", "edge-tts")
        # FP-021: Referencias externas para audio adaptativo (Da'at→Hod)
        self._ciclo_circadiano_ref = None  # Se asigna externamente
        self._personalidad_ref = None      # Se asigna externamente

    def hablar(self, texto: str):
        """Añade texto a la cola de habla. Texto largo se divide en fragmentos."""
        self._interrumpido = False
        texto = texto.strip()
        if not texto:
            return
        texto = self._sanitizar_para_voz(texto)
        if not texto:
            return
        # Dividir texto largo en fragmentos por oraciones para evitar truncamiento
        if len(texto) > 500:
            fragmentos = self._dividir_texto(texto)
            for frag in fragmentos:
                self._cola.put(frag)
        else:
            self._cola.put(texto)

    @staticmethod
    def _sanitizar_para_voz(texto: str) -> str:
        texto = texto.strip()
        texto = texto.replace('...', ', etcétera')
        texto = texto.replace('```', '')
        texto = texto.replace('\\', ' ')
        texto = texto.replace('/', ' ')
        texto = texto.replace('_', ' ')
        texto = re.sub(r'[`#*]+', '', texto)
        texto = re.sub(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF]+', '', texto)
        texto = re.sub(r'[\uFE0E\uFE0F]+', '', texto)
        texto = re.sub(r' {2,}', ' ', texto)
        return texto.strip()

    @staticmethod
    def _dividir_texto(texto: str, max_chars: int = 450) -> list[str]:
        """Divide texto largo en fragmentos por oraciones completas."""
        import re
        oraciones = re.split(r'(?<=[.!?])\s+', texto)
        fragmentos = []
        actual = ""
        for oracion in oraciones:
            if len(actual) + len(oracion) + 1 > max_chars and actual:
                fragmentos.append(actual.strip())
                actual = oracion
            else:
                actual = (actual + " " + oracion).strip() if actual else oracion
        if actual:
            fragmentos.append(actual.strip())
        return fragmentos if fragmentos else [texto]

    def _calcular_audio_adaptativo(self) -> tuple[str, str]:
        """FP-021: Calcula rate/volume adaptativos según Da'at (fase circadiana) y Ruaj (humor).
        
        Returns:
            (rate_str, volume_str) en formato edge-tts: "+0%", "-10%", etc.
        """
        rate_delta = 0   # porcentaje
        volume_delta = 0  # porcentaje
        fase = None

        # Da'at → fase circadiana (singleton global)
        try:
            from computadora.nucleo.proactividad import obtener_fase_actual
            fase = obtener_fase_actual()
            if fase in ("transición", "transicion"):
                rate_delta -= 5
                volume_delta -= 10
            elif fase == "descanso_guardian":
                rate_delta -= 15
                volume_delta -= 25
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.debug("No se pudo obtener fase circadiana para audio adaptativo")

        # Ruaj → override por humor energético
        persona = self._personalidad_ref
        if persona:
            try:
                humor = persona.humor_actual
                if humor in ("emocionado", "activo"):
                    rate_delta += 10
                elif humor == "cansado":
                    if fase == "descanso_guardian":
                        rate_delta -= 5
                        volume_delta -= 10
                    else:
                        rate_delta -= 2
                        volume_delta -= 2
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                logger.debug("No se pudo obtener humor para audio adaptativo")

        rate_str = f"{rate_delta:+d}%" if rate_delta != 0 else "+0%"
        volume_str = f"{volume_delta:+d}%" if volume_delta != 0 else "+0%"
        return rate_str, volume_str

    def interrumpir(self):
        """Detiene el habla inmediatamente."""
        self._interrumpido = True
        if self._hablando:
            try:
                import pygame
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                logger.debug("pygame no disponible para interrumpir")
            logger.info("Habla interrumpida")
        # Vaciar cola pendiente
        while not self._cola.empty():
            try:
                self._cola.get_nowait()
            except queue.Empty:
                break

    def detener(self):
        self._activo = False
        self._interrumpido = True
        self._cola.put(None)

    def run(self):
        import pygame
        pygame.mixer.init(frequency=24000)
        logger.info("Motor de habla inicializado (frecuencia: 24kHz)")

        loop = asyncio.new_event_loop()

        try:
            while self._activo:
                try:
                    texto = self._cola.get(timeout=0.5)
                except queue.Empty:
                    continue

                if texto is None:
                    break

                self._interrumpido = False
                self._hablando = True
                self.texto_a_recitar.emit(texto)
                self.habla_iniciada.emit()

                intento = 0
                max_intentos = 2  # 1 intento principal + 1 fallback
                exito = False

                while intento < max_intentos and not exito and not self._interrumpido:
                    try:
                        if self._motor == "edge-tts":
                            loop.run_until_complete(self._hablar_edge_tts(texto))
                            exito = True
                        else:
                            self._hablar_pyttsx3(texto)
                            exito = True
                    except Exception as e:
                        intento += 1
                        if intento < max_intentos and not self._interrumpido:
                            logger.warning(f"HiloHabla: Intento {intento} falló con {self._motor}: {e} → intentando fallback")
                            try:
                                # Si fue edge-tts, intentar pyttsx3
                                if self._motor == "edge-tts":
                                    self._hablar_pyttsx3(texto)
                                    exito = True
                                else:
                                    raise  # Si fue pyttsx3, no hay fallback
                            except Exception as e2:
                                logger.error(f"HiloHabla: Fallback también falló: {e2}")
                                # Continuar de todas formas (no bloquear demo)
                                break
                        else:
                            logger.error(f"HiloHabla: Error final (motor={self._motor}, intento={intento}): {e}")
                            break

                self._hablando = False
                self.habla_terminada.emit()

                # FP-XXX: GARANTÍA CRÍTICA: Emitir cola_vacia cuando no hay más fragmentos
                # Esto SIEMPRE se ejecuta, incluso si hubo error de TTS
                if self._cola.empty():
                    logger.info("HiloHabla: Cola vacía — emitiendo señal (progreso)")
                    self.cola_vacia.emit()
                else:
                    logger.debug(f"HiloHabla: Cola con {self._cola.qsize()} fragmentos pendientes")
        finally:
            loop.close()
            logger.info("Motor de habla finalizado")

    async def _hablar_edge_tts(self, texto: str):
        """Genera y reproduce audio con edge-tts con timeout y error handling robusto."""
        import edge_tts
        import pygame

        archivo_tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp3", dir=tempfile.gettempdir()
        )
        archivo_tmp.close()

        try:
            # FP-021: Audio adaptativo — rate/volume según fase circadiana + humor
            rate_str, volume_str = self._calcular_audio_adaptativo()
            logger.debug(f"HiloHabla: Generando audio (rate={rate_str}, volume={volume_str}) para: {texto[:50]}...")
            
            comunicar = edge_tts.Communicate(texto, self._voz, rate=rate_str, volume=volume_str)
            
            # FP-XXX: Timeout de 10 segundos máximo para generar audio
            try:
                await asyncio.wait_for(comunicar.save(archivo_tmp.name), timeout=10.0)
                logger.debug(f"HiloHabla: Audio generado exitosamente en {archivo_tmp.name}")
            except asyncio.TimeoutError:
                logger.error(f"HiloHabla: Timeout generando audio (>10s) para: {texto[:50]}... → fallback")
                raise

            # Verificar que archivo existe y tiene contenido
            if not os.path.exists(archivo_tmp.name):
                raise FileNotFoundError(f"Archivo TTS no creado: {archivo_tmp.name}")
            
            size = os.path.getsize(archivo_tmp.name)
            if size < 1000:
                logger.warning(f"HiloHabla: Archivo MP3 sospechosamente pequeño ({size}b) — posible generación incompleta")

            # Verificar interrupción DESPUÉS de generar
            if self._interrumpido:
                logger.debug("HiloHabla: Reproducción interrumpida por usuario")
                return

            # Cargar y reproducir con pygame
            try:
                pygame.mixer.music.load(archivo_tmp.name)
                pygame.mixer.music.play()
                logger.debug("HiloHabla: Reproducción de audio iniciada")
            except pygame.error as e:
                logger.error(f"HiloHabla: Error pygame cargando audio: {e}")
                raise

            # Esperar a que termine la reproducción (con timeout de seguridad)
            timeout_count = 0
            max_timeout_ms = 60000  # 60 segundos máximo de reproducción
            while pygame.mixer.music.get_busy() and not self._interrumpido:
                await asyncio.sleep(0.1)
                timeout_count += 1
                if timeout_count > (max_timeout_ms // 100):  # timeout_count * 100ms > max_timeout_ms
                    logger.warning(f"HiloHabla: Timeout reproducción (>{max_timeout_ms}ms) — deteniendo")
                    pygame.mixer.music.stop()
                    break

            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            logger.debug(f"HiloHabla: Reproducción completada ({timeout_count * 100}ms total)")
            
        except asyncio.TimeoutError as e:
            logger.error(f"HiloHabla: Timeout en edge_tts (generación): {e}")
            raise  # Intentar fallback en run()
        except Exception as e:
            logger.error(f"HiloHabla: Error en edge_tts: {e}", exc_info=True)
            raise
        finally:
            # Limpiar archivo temporal
            try:
                if os.path.exists(archivo_tmp.name):
                    os.unlink(archivo_tmp.name)
                    logger.debug(f"HiloHabla: Archivo temporal limpiado")
            except OSError as e:
                logger.debug(f"HiloHabla: No se pudo limpiar archivo temporal: {e}")

        logger.info(f"Hablado (edge-tts): '{texto}'")

    def _hablar_pyttsx3(self, texto: str):
        """Fallback: genera voz con pyttsx3 (offline)."""
        import pyttsx3

        motor = pyttsx3.init()
        voces = motor.getProperty("voices")

        # Buscar voz en español
        for voz in voces:
            if "spanish" in voz.name.lower() or "es" in voz.id.lower():
                motor.setProperty("voice", voz.id)
                break

        motor.say(texto)
        motor.runAndWait()
        motor.stop()
        logger.debug(f"Hablado (pyttsx3): '{texto}'")


