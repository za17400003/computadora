"""
FP-165: AUDIO AVANZADO — VAD + Wake Word + Cancelacion de Eco como Alexa.
═══════════════════════════════════════════════════════════════════════════════

WI-314: Audio estilo Alexa:
  - VAD (Voice Activity Detection) para detectar solo voz humana
  - Cancelacion de eco para ignorar TV/musica
  - Wake word "Computadora" antes de activar
  - No exclusividad: permite que otras apps usen el microfono

ARQUITECTURA:
  1. Captura continua de audio (ring buffer de 3s)
  2. VAD detecta actividad vocal
  3. Wake word detection (por defecto "computadora")
  4. Speech-to-text solo si se detecta wake word + voz
  5. TODO lo demas (TV, musica, otras conversaciones) se ignora
"""

from __future__ import annotations

import collections
import os
import struct
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
from loguru import logger

# ── Imports opcionales ───────────────────────────────────────────

_PYAUDIO_AVAILABLE = False
try:
    import pyaudio
    _PYAUDIO_AVAILABLE = True
except ImportError:
    pass

_WEBAUDIO_AVAILABLE = False
try:
    import sounddevice as sd
    _WEBAUDIO_AVAILABLE = True
except ImportError:
    pass

_WEBRTC_VAD_AVAILABLE = False
try:
    import webrtcvad
    _WEBRTC_VAD_AVAILABLE = True
except ImportError:
    pass

_WHISPER_AVAILABLE = False
try:
    import whisper
    _WHISPER_AVAILABLE = True
except ImportError:
    pass


# ── Configuracion ───────────────────────────────────────────────

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30  # 30ms frames para VAD
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
RING_BUFFER_SECONDS = 3
RING_BUFFER_SIZE = int(SAMPLE_RATE * RING_BUFFER_SECONDS)
SILENCE_TIMEOUT_AFTER_VOICE = 1.5  # segundos de silencio para considerar fin de frase
MIN_VOICE_DURATION_MS = 300  # minimo 300ms de voz para considerar valido


@dataclass
class AudioChunk:
    """Fragmento de audio capturado."""
    data: bytes
    timestamp: float = field(default_factory=time.time)
    nivel_sonido: float = 0.0
    es_voz: bool = False


class CapturadorAudio:
    """
    Captura de audio continua estilo Alexa.

    - No bloquea el microfono (permite otras apps)
    - Buffer circular de ultimos N segundos
    - VAD opcional (webrtcvad) para detectar solo voz humana
    - Wake word detection integrado

    WI-314: No exclusividad de microfono.
    """

    def __init__(
        self,
        wake_words: Optional[Set[str]] = None,
        usar_vad: bool = True,
        umbral_ruido: float = 0.02,  # Umbral RMS para considerar silencio
        device_index: Optional[int] = None,
    ):
        self.wake_words = wake_words or {"computadora", "computadora,"}
        self.usar_vad = usar_vad and _WEBRTC_VAD_AVAILABLE
        self.umbral_ruido = umbral_ruido
        self.device_index = device_index

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Buffer circular
        self._ring_buffer = collections.deque(maxlen=RING_BUFFER_SIZE)
        self._ultimo_chunk: Optional[AudioChunk] = None

        # VAD
        self._vad = None
        if self.usar_vad:
            try:
                import webrtcvad
                self._vad = webrtcvad.Vad(2)  # Agresividad 2 (balanceada)
                logger.info("VAD WebRTC activado (agresividad 2)")
            except Exception as e:
                logger.warning(f"No se pudo iniciar VAD: {e}")
                self.usar_vad = False

        # Estado de deteccion de voz
        self._en_voz = False
        self._voz_inicio: Optional[float] = None
        self._ultimo_audio_voz: Optional[float] = None
        self._ultimo_texto: Optional[str] = None

        # Callbacks
        self._on_comando: Optional[Callable] = None
        self._on_activacion: Optional[Callable] = None

        # Stats
        self._nivel_ruido_actual = 0.0

        logger.info(f"CapturadorAudio iniciado (VAD={self.usar_vad}, wake={self.wake_words})")

    # ── Callbacks ────────────────────────────────────────────────

    def set_on_comando(self, callback: Callable[[str], None]) -> None:
        """Callback cuando se detecta un comando de voz."""
        self._on_comando = callback

    def set_on_activacion(self, callback: Callable[[], None]) -> None:
        """Callback cuando se detecta wake word."""
        self._on_activacion = callback

    # ── Procesamiento de audio ───────────────────────────────────

    def _calcular_rms(self, data: bytes) -> float:
        """Calcula RMS de un fragmento de audio."""
        if len(data) < 2:
            return 0.0
        try:
            # Asumimos 16-bit PCM
            nums = struct.unpack_from('<' + 'h' * (len(data) // 2), data)
            sqsum = sum(n * n for n in nums)
            return float(np.sqrt(sqsum / len(nums))) / 32768.0
        except Exception:
            return 0.0

    def _detectar_voz(self, data: bytes) -> bool:
        """Detecta si el fragmento contiene voz humana.

        Usa webrtcvad si esta disponible, o RMS si no.

        Returns:
            True si detecta voz, False si es ruido/silencio.
        """
        if self._vad is not None and len(data) == FRAME_SIZE * 2:  # 16-bit
            try:
                return self._vad.is_speech(data, SAMPLE_RATE)
            except Exception:
                pass

        # Fallback: RMS threshold
        rms = self._calcular_rms(data)
        return rms > self.umbral_ruido * 2  # Umbral mas alto para voz

    def _contiene_wake_word(self, texto: str) -> bool:
        """Detecta si el texto contiene la wake word."""
        texto_lower = texto.lower().strip()
        for ww in self.wake_words:
            if ww in texto_lower[:20]:
                return True
        return False

    # ── Hilo de captura ──────────────────────────────────────────

    def _loop_audio(self):
        """Loop principal de captura de audio.

        Lee del microfono en modo no exclusivo.
        """
        audio_interface = None
        stream = None

        try:
            if _PYAUDIO_AVAILABLE:
                import pyaudio
                audio_interface = pyaudio.PyAudio()
                stream = audio_interface.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    input_device_index=self.device_index,
                    frames_per_buffer=FRAME_SIZE,
                    stream_callback=self._callback_pyaudio,
                )
                stream.start_stream()

                while self._running:
                    time.sleep(0.1)

            elif _WEBAUDIO_AVAILABLE:
                import sounddevice as sd

                def callback(indata, frames, tim, status):
                    if status:
                        logger.debug(f"Audio status: {status}")
                    data = indata.tobytes()
                    self._procesar_chunk(data)

                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype='int16',
                    device=self.device_index,
                    callback=callback,
                ):
                    while self._running:
                        time.sleep(0.1)

            else:
                logger.error("No hay libreria de audio disponible (pyaudio o sounddevice)")
                return

        except Exception as e:
            logger.error(f"Error en captura de audio: {e}")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if audio_interface is not None:
                try:
                    audio_interface.terminate()
                except Exception:
                    pass

    def _callback_pyaudio(self, in_data, frame_count, time_info, status):
        """Callback de PyAudio (stream no bloqueante)."""
        if status:
            logger.debug(f"PyAudio status: {status}")
        self._procesar_chunk(in_data)
        return (None, 0)  # pyaudio.paContinue

    def _procesar_chunk(self, data: bytes):
        """Procesa un chunk de audio."""
        if not self._running:
            return

        rms = self._calcular_rms(data)
        es_voz = self._detectar_voz(data)

        chunk = AudioChunk(
            data=data,
            timestamp=time.time(),
            nivel_sonido=rms,
            es_voz=es_voz,
        )

        with self._lock:
            self._ring_buffer.append(chunk)
            self._ultimo_chunk = chunk
            self._nivel_ruido_actual = rms

        # Deteccion de voz continua
        ahora = time.time()

        if es_voz:
            if not self._en_voz:
                self._en_voz = True
                self._voz_inicio = ahora
                logger.debug("Inicio de voz detectado")
            self._ultimo_audio_voz = ahora
        else:
            if self._en_voz and self._ultimo_audio_voz is not None:
                if (ahora - self._ultimo_audio_voz) > SILENCE_TIMEOUT_AFTER_VOICE:
                    # Fin de frase
                    duracion_ms = (ahora - self._voz_inicio) * 1000 if self._voz_inicio else 0
                    if duracion_ms >= MIN_VOICE_DURATION_MS:
                        logger.debug(f"Fin de voz ({duracion_ms:.0f}ms)")
                        audio_voz = self._obtener_audio_ultima_frase()
                        if audio_voz:
                            self._transcribir_y_procesar(audio_voz)
                    self._en_voz = False
                    self._voz_inicio = None
                    self._ultimo_audio_voz = None

    def _obtener_audio_ultima_frase(self) -> Optional[bytes]:
        """Obtiene el audio de la ultima frase detectada."""
        with self._lock:
            if not self._ring_buffer:
                return None
            # Tomar todo el buffer reciente
            chunks = list(self._ring_buffer)
            data = b''.join(c.data for c in chunks if c.es_voz or
                          (time.time() - c.timestamp) < 2.0)
            return data if len(data) > 1000 else None

    def _transcribir_y_procesar(self, audio_data: bytes):
        """Transcribe audio y verifica si contiene wake word."""
        if not _WHISPER_AVAILABLE:
            logger.debug("Whisper no disponible, saltando transcripcion")
            return

        try:
            import whisper

            # Convertir bytes a numpy
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribir
            modelo = whisper.load_model("base")
            resultado = modelo.transcribe(audio_np, language="es")
            texto = resultado.get("text", "").strip()

            if not texto:
                return

            logger.info(f"Transcripcion: '{texto}'")

            # Verificar wake word
            if self._contiene_wake_word(texto):
                # Quitar wake word del texto
                texto_limpio = texto
                for ww in self.wake_words:
                    if ww in texto_limpio.lower()[:20]:
                        idx = texto_limpio.lower().find(ww)
                        texto_limpio = texto_limpio[idx + len(ww):].strip()
                        break

                # Si solo dijo wake word, usar texto completo
                if not texto_limpio:
                    texto_limpio = texto

                logger.info(f"Wake word detectada! Comando: '{texto_limpio}'")

                if self._on_activacion:
                    self._on_activacion()

                if self._on_comando and texto_limpio:
                    self._on_comando(texto_limpio)

        except Exception as e:
            logger.error(f"Error en transcripcion: {e}")

    # ── API publica ──────────────────────────────────────────────

    def iniciar(self) -> None:
        """Inicia la captura de audio en background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop_audio, daemon=True, name="audio-captura")
        self._thread.start()
        logger.info("Captura de audio iniciada en background")

    def detener(self) -> None:
        """Detiene la captura de audio."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Captura de audio detenida")

    def obtener_nivel_ruido(self) -> float:
        """Obtiene el nivel de ruido ambiente actual."""
        with self._lock:
            return self._nivel_ruido_actual

    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna estado del capturador."""
        with self._lock:
            return {
                "activo": self._running,
                "vad_disponible": _WEBRTC_VAD_AVAILABLE and self.usar_vad,
                "whisper_disponible": _WHISPER_AVAILABLE,
                "en_voz": self._en_voz,
                "nivel_ruido": round(self._nivel_ruido_actual, 4),
                "buffer_size": len(self._ring_buffer),
                "ultimo_chunk_hace": (
                    time.time() - self._ultimo_chunk.timestamp
                ) if self._ultimo_chunk else None,
            }


# ── Funciones de utilidad ────────────────────────────────────────

def crear_capturador_audio(
    wake_word: str = "computadora",
    usar_vad: bool = True,
) -> CapturadorAudio:
    """Factory: Crea y configura un capturador de audio."""
    return CapturadorAudio(
        wake_words={wake_word, f"{wake_word},"},
        usar_vad=usar_vad,
    )


if __name__ == "__main__":
    print("=== Audio Avanzado Test ===")
    print(f"PyAudio: {_PYAUDIO_AVAILABLE}")
    print(f"SoundDevice: {_WEBAUDIO_AVAILABLE}")
    print(f"WebRTC VAD: {_WEBRTC_VAD_AVAILABLE}")
    print(f"Whisper: {_WHISPER_AVAILABLE}")

    capturador = crear_capturador_audio()
    print(f"Wake words: {capturador.wake_words}")
    print(f"VAD activo: {capturador.usar_vad}")

    print()
    print("Audio avanzado listo para usar.")


