#!/usr/bin/env python3
"""
MULTI-MICROPHONE AUDIO SYSTEM — Computadora con soporte multi-micrófono
Implementa captura simultánea de múltiples dispositivos y selección automática del mejor audio.
"""

import warnings
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

warnings.filterwarnings("ignore", message=".*sounddevice.*")

logger = logging.getLogger(__name__)

@dataclass
class AudioDevice:
    """Información de un dispositivo de audio."""
    index: int
    name: str
    channels: int
    sample_rate: float
    host_api: str
    is_working: bool = False
    volume_level: float = 0.0

@dataclass
class AudioChunk:
    """Chunk de audio con metadata."""
    device_index: int
    audio_data: np.ndarray
    timestamp: float
    volume_level: float
    snr_estimate: float

class MultiMicrophoneSystem:
    """Sistema de audio que captura simultáneamente de múltiples micrófonos."""

    def __init__(self, config):
        self.config = config
        self.devices: List[AudioDevice] = []
        self.active_streams: Dict[int, sd.InputStream] = {}
        self.audio_queue = queue.Queue(maxsize=100)  # Buffer de chunks
        self.is_running = False
        self.chunk_duration = 0.5  # 500ms chunks
        self.sample_rate = config.obtener("escucha.frecuencia_muestreo", 16000)
        self._last_discovery = time.monotonic()
        self._last_chunk_time = time.monotonic()

        # Umbrales de calidad
        self.min_volume_threshold = config.obtener("multi_mic.min_volume", 0.001)
        self.max_volume_threshold = config.obtener("multi_mic.max_volume", 0.8)  # Evitar clipping
        self.min_snr_threshold = config.obtener("multi_mic.min_snr", 5.0)

        # Inicializar dispositivos
        self._discover_devices()

    def _discover_devices(self):
        """Descubre y valida dispositivos de entrada disponibles."""
        logger.info("🔍 Descubriendo dispositivos de audio...")

        try:
            # Forzar inicialización de sounddevice en el hilo actual
            import sounddevice as sd
            sd._initialize()

            dispositivos = sd.query_devices()
            logger.info(f"Total dispositivos encontrados: {len(dispositivos)}")

            # Log detallado de dispositivos
            for i, d in enumerate(dispositivos):
                if d["max_input_channels"] > 0:
                    logger.debug(f"Input device {i}: {d['name']} (ch:{d['max_input_channels']}, sr:{d['default_samplerate']})")

        except Exception as e:
            logger.error(f"Error consultando dispositivos: {e}")
            logger.error("Posible problema: sounddevice no inicializado correctamente en QThread")
            return

        working_devices = []

        for i, d in enumerate(dispositivos):
            if d["max_input_channels"] <= 0:
                continue

            try:
                ha = sd.query_hostapis(d["hostapi"])
                device = AudioDevice(
                    index=i,
                    name=d["name"],
                    channels=min(2, d["max_input_channels"]),  # Máximo 2 canales
                    sample_rate=float(d["default_samplerate"]),
                    host_api=ha["name"]
                )

                # Test rápido del dispositivo
                if self._test_device(device):
                    device.is_working = True
                    working_devices.append(device)
                    logger.info(f"✅ Dispositivo funcional: [{i}] {d['name']}")
                else:
                    logger.debug(f"❌ Dispositivo no funcional: [{i}] {d['name']}")
            except Exception as e:
                logger.debug(f"Error procesando dispositivo {i}: {e}")

        self.devices = working_devices
        self._last_discovery = time.monotonic()
        logger.info(f"🎙️ Encontrados {len(self.devices)} dispositivos funcionales")

        if len(self.devices) == 0:
            logger.warning("⚠️ No se encontraron dispositivos funcionales")
            logger.warning("Causas posibles:")
            logger.warning("  - Dispositivos ocupados por otra aplicación")
            logger.warning("  - Configuración de audio de Windows incorrecta")
            logger.warning("  - Problemas con drivers de audio")
            logger.warning("  - sounddevice no compatible con QThread")

    def _test_device(self, device: AudioDevice) -> bool:
        """Test rápido de un dispositivo para verificar que funciona."""
        try:
            # Intentar abrir un stream corto sin crear un segundo stream concurrente.
            with sd.InputStream(
                device=device.index,
                samplerate=min(device.sample_rate, self.sample_rate),
                channels=device.channels,
                dtype="float32",
                blocksize=int(0.1 * self.sample_rate)  # 100ms test
            ) as stream:
                # Leer directamente del stream para validar el dispositivo.
                stream.start()
                stream.read(int(0.1 * self.sample_rate))
                return True
        except Exception as e:
            logger.debug(f"Test fallido para dispositivo {device.index}: {e}")
            return False

    def _calculate_audio_quality(self, audio: np.ndarray) -> Tuple[float, float]:
        """Calcula métricas de calidad de audio: (volumen, SNR estimado)."""
        if len(audio) == 0:
            return 0.0, 0.0

        # Volumen (RMS normalizado)
        volume = np.sqrt(np.mean(audio ** 2))

        # SNR estimado (relación señal-ruido)
        # Usar desviación estándar como proxy de ruido
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio)  # Varianza como estimación de ruido

        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = 60.0  # SNR alto si no hay ruido detectable

        # Clamp valores razonables
        volume = np.clip(volume, 0.0, 1.0)
        snr = np.clip(snr, 0.0, 60.0)

        return float(volume), float(snr)

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status, device_index: int):
        """Callback para procesar audio de cada dispositivo."""
        try:
            # Convertir a mono si es estéreo
            if indata.shape[1] > 1:
                audio = np.mean(indata, axis=1)
            else:
                audio = indata.flatten()

            # Calcular calidad
            volume, snr = self._calculate_audio_quality(audio)

            # Crear chunk
            chunk = AudioChunk(
                device_index=device_index,
                audio_data=audio.copy(),
                timestamp=time.time(),
                volume_level=volume,
                snr_estimate=snr
            )

            # Encolar (no bloquear si queue llena)
            try:
                self.audio_queue.put_nowait(chunk)
            except queue.Full:
                logger.debug(f"Queue llena, descartando chunk de dispositivo {device_index}")

        except Exception as e:
            logger.debug(f"Error en callback de dispositivo {device_index}: {e}")

    def _start_device_stream(self, device: AudioDevice):
        """Inicia stream de audio para un dispositivo específico."""
        try:
            def callback(indata, frames, time_info, status):
                self._audio_callback(indata, frames, time_info, status, device.index)

            stream = sd.InputStream(
                device=device.index,
                samplerate=self.sample_rate,
                channels=device.channels,
                dtype="float32",
                blocksize=int(self.chunk_duration * self.sample_rate),
                callback=callback
            )

            stream.start()
            self.active_streams[device.index] = stream
            logger.info(f"🎙️ Stream iniciado: [{device.index}] {device.name}")

        except Exception as e:
            logger.error(f"❌ Error iniciando stream para dispositivo {device.index}: {e}")

    def start_capture(self):
        """Inicia captura simultánea de todos los dispositivos."""
        if self.is_running:
            return

        if not self.devices:
            logger.warning("⚠️ No hay dispositivos funcionales para iniciar captura. Reintentando descubrimiento.")
            self._discover_devices()
            if not self.devices:
                logger.error("❌ No se pudo iniciar captura porque no hay dispositivos disponibles.")
                return

        logger.info("🚀 Iniciando captura multi-micrófono...")

        self.is_running = True

        # Iniciar streams para todos los dispositivos
        for device in self.devices:
            threading.Thread(
                target=self._start_device_stream,
                args=(device,),
                daemon=True,
                name=f"AudioStream-{device.index}"
            ).start()

        logger.info(f"✅ Captura iniciada con {len(self.devices)} dispositivos")

    def stop_capture(self):
        """Detiene todos los streams de audio."""
        if not self.is_running:
            return

        logger.info("🛑 Deteniendo captura multi-micrófono...")

        self.is_running = False

        # Detener todos los streams
        for stream in self.active_streams.values():
            try:
                stream.stop()
                stream.close()
            except Exception as e:
                logger.debug(f"Error deteniendo stream: {e}")

        self.active_streams.clear()
        logger.info("✅ Captura detenida")

    def get_best_audio_chunk(self, timeout: float = 1.0) -> Optional[AudioChunk]:
        """Obtiene el mejor chunk de audio disponible de todos los dispositivos.

        Retorna el chunk con mejor calidad (volumen + SNR) que supere los umbrales.
        """
        if not self.is_running:
            if self.devices:
                self.start_capture()
            else:
                return None

        best_chunk = None
        best_score = 0.0

        # Recolectar chunks disponibles
        chunks = []
        try:
            while True:
                chunk = self.audio_queue.get_nowait()
                chunks.append(chunk)
        except queue.Empty:
            pass

        # Reconstruir si no hay streams activos y no llega audio
        if not self.is_running and self.devices:
            self.start_capture()

        active_streams = any(
            getattr(stream, 'active', False)
            for stream in self.active_streams.values()
        )
        if not active_streams and self.is_running:
            if time.monotonic() - self._last_chunk_time > 3.0:
                logger.warning("⚠️ No hay streams activos detectados; reintentando refrescar dispositivos.")
                self.refresh_devices()
                self._last_chunk_time = time.monotonic()

        # Evaluar cada chunk
        for chunk in chunks:
            # Verificar umbrales básicos
            if chunk.volume_level < self.min_volume_threshold:
                continue
            if chunk.volume_level > self.max_volume_threshold:
                continue  # Evitar clipping
            if chunk.snr_estimate < self.min_snr_threshold:
                continue

            # Calcular score de calidad (volumen * SNR normalizado)
            snr_normalized = min(chunk.snr_estimate / 30.0, 1.0)  # Normalizar SNR a 0-1
            score = chunk.volume_level * snr_normalized

            if score > best_score:
                best_score = score
                best_chunk = chunk

        if best_chunk is not None:
            self._last_chunk_time = time.time()
        return best_chunk

    def refresh_devices(self):
        """Re-descubre y reinicia la captura cuando los dispositivos cambian."""
        if time.monotonic() - getattr(self, '_last_discovery', 0.0) < 2.0:
            return
        logger.info("🔁 Refrescando dispositivos de audio...")
        self.stop_capture()
        self._discover_devices()
        if self.devices:
            self.start_capture()

    def get_device_status(self) -> Dict[str, Any]:
        """Retorna estado actual del sistema multi-micrófono."""
        return {
            "total_devices": len(self.devices),
            "active_streams": len(self.active_streams),
            "is_running": self.is_running,
            "queue_size": self.audio_queue.qsize(),
            "devices": [
                {
                    "index": d.index,
                    "name": d.name,
                    "is_working": d.is_working,
                    "channels": d.channels,
                    "sample_rate": d.sample_rate,
                    "host_api": d.host_api
                }
                for d in self.devices
            ]
        }

# Función de prueba independiente
def test_multi_microphone_system():
    """Función de prueba del sistema multi-micrófono."""
    print("=" * 80)
    print("🎙️ TEST SISTEMA MULTI-MICRÓFONO")
    print("=" * 80)

    # Config mock
    class MockConfig:
        def obtener(self, key, default=None):
            configs = {
                "escucha.frecuencia_muestreo": 16000,
                "multi_mic.min_volume": 0.001,
                "multi_mic.max_volume": 0.8,
                "multi_mic.min_snr": 5.0
            }
            return configs.get(key, default)

    config = MockConfig()
    system = MultiMicrophoneSystem(config)

    print(f"📋 Dispositivos encontrados: {len(system.devices)}")
    for device in system.devices[:5]:  # Mostrar primeros 5
        print(f"  [{device.index}] {device.name} ({device.channels}ch, {device.sample_rate}Hz)")

    if len(system.devices) == 0:
        print("❌ No hay dispositivos funcionales")
        return

    print("\n🎯 Iniciando test de captura (10 segundos)...")
    system.start_capture()

    try:
        start_time = time.time()
        chunks_received = 0

        while time.time() - start_time < 10:
            chunk = system.get_best_audio_chunk(timeout=0.1)
            if chunk:
                chunks_received += 1
                print(f"🎵 Chunk recibido - Disp:{chunk.device_index} "
                      f"Vol:{chunk.volume_level:.4f} SNR:{chunk.snr_estimate:.1f}dB")

        print(f"\n✅ Test completado: {chunks_received} chunks procesados")

    finally:
        system.stop_capture()

    print("=" * 80)

if __name__ == "__main__":
    test_multi_microphone_system()

