\"\"\"
הוד (Hod) — Diagnóstico de Micrófono Mejorado
Módulo para auditar y diagnosticar captura de audio.

Responsabilidades:
- Verificar disponibilidad de dispositivos de entrada
- Probar captura de audio (grabación 3s)
- Evaluar VAD (Voice Activity Detection con Silero)
- Detectar wake word en audio capturado
- Generar reporte detallado para debugging
\"\"\"

import time
import numpy as np
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

try:
    from silero_vad import load_silero_vad, get_speech_timestamps
    SILERO_DISPONIBLE = True
    _VAD_MODEL = load_silero_vad()
except ImportError:
    SILERO_DISPONIBLE = False
    _VAD_MODEL = None


class DiagnosticoMicrofono:
    \"\"\"Auditoría completa del flujo de captura de audio.\"\"\"

    def __init__(self):
        self.resultado: Dict[str, Any] = {}
        self._ruta_logs = Path(__file__).resolve().parent.parent.parent / \"datos\" / \"diagnostico_logs\"
        self._ruta_logs.mkdir(parents=True, exist_ok=True)

    def ejecutar_diagnostico_completo(self) -> Dict[str, Any]:
        \"\"\"Ejecuta diagnóstico completo del micrófono.\"\"\"
        logger.info(\"🔊 Iniciando diagnóstico de micrófono...\")
        
        self.resultado = {
            \"timestamp\": datetime.now().isoformat(),
            \"etapas\": {}
        }
        
        # Etapa 1: Listar dispositivos
        self._listar_dispositivos()
        
        # Etapa 2: Seleccionar dispositivo
        dispositivo_id = self._seleccionar_dispositivo()
        if dispositivo_id is None:
            logger.error(\"❌ No se encontró dispositivo de entrada\")
            return self.resultado
        
        # Etapa 3: Probar captura de audio
        self._probar_captura_audio(dispositivo_id)
        
        # Etapa 4: Evaluar VAD
        self._evaluar_vad()
        
        # Etapa 5: Detectar wake word
        self._detectar_wake_word()
        
        # Guardar reporte
        self._guardar_reporte()
        
        logger.info(f\"✓ Diagnóstico completado\")
        return self.resultado

    def _listar_dispositivos(self):
        \"\"\"Etapa 1: Enumera dispositivos de audio disponibles.\"\"\"
        logger.info(\"📋 Etapa 1: Listando dispositivos de audio...\")
        try:
            import sounddevice as sd
            dispositivos = sd.query_devices()
            
            entradas = []
            for i, dev in enumerate(dispositivos):
                if dev.get(\"max_input_channels\", 0) > 0:
                    entradas.append({
                        \"id\": i,
                        \"nombre\": dev.get(\"name\", \"Desconocido\"),
                        \"canales_entrada\": dev.get(\"max_input_channels\", 0),
                        \"frecuencia_muestreo\": dev.get(\"default_samplerate\", 0),
                    })
            
            self.resultado[\"etapas\"][\"dispositivos\"] = {
                \"total\": len(dispositivos),
                \"entradas_disponibles\": len(entradas),
                \"dispositivos\": entradas,
            }
            
            logger.info(f\"  ✓ {len(entradas)} dispositivo(s) de entrada disponible(s)\")
            
        except Exception as e:
            logger.error(f\"  ❌ Error listando dispositivos: {e}\")
            self.resultado[\"etapas\"][\"dispositivos\"] = {\"error\": str(e)}

    def _seleccionar_dispositivo(self) -> Optional[int]:
        \"\"\"Etapa 2: Selecciona el mejor dispositivo de entrada.\"\"\"
        logger.info(\"🎤 Etapa 2: Seleccionando dispositivo...\")
        try:
            import sounddevice as sd
            dispositivos = sd.query_devices()
            
            # Preferencia: \"Microphone\" en el nombre
            for i, dev in enumerate(dispositivos):
                if dev.get(\"max_input_channels\", 0) > 0:
                    nombre = dev.get(\"name\", \"\").lower()
                    if \"microphone\" in nombre or \"micrófono\" in nombre:
                        logger.info(f\"  ✓ Dispositivo seleccionado: {dev['name']} (ID {i})\")
                        self.resultado[\"etapas\"][\"dispositivo_seleccionado\"] = {\n                            \"id\": i,\n                            \"nombre\": dev[\"name\"],\n                        }\n                        return i\n            \n            # Fallback: primer dispositivo de entrada\n            for i, dev in enumerate(dispositivos):\n                if dev.get(\"max_input_channels\", 0) > 0:\n                    logger.info(f\"  ✓ Usando dispositivo por defecto: {dev['name']} (ID {i})\")\n                    self.resultado[\"etapas\"][\"dispositivo_seleccionado\"] = {\n                        \"id\": i,\n                        \"nombre\": dev[\"name\"],\n                        \"nota\": \"Dispositivo por defecto (no 'Microphone')\",\n                    }\n                    return i\n            \n            logger.warning(\"  ⚠️ No se encontró dispositivo de entrada\")\n            return None\n            \n        except Exception as e:\n            logger.error(f\"  ❌ Error seleccionando dispositivo: {e}\")\n            return None\n\n    def _probar_captura_audio(self, dispositivo_id: int):\n        \"\"\"Etapa 3: Captura 3 segundos de audio y evalúa.\"\"\"\n        logger.info(f\"🔴 Etapa 3: Capturando audio (3s)...\")\n        try:\n            import sounddevice as sd\n            \n            sr = 16000  # Sample rate para Silero VAD\n            duracion = 3\n            \n            logger.info(f\"  Grabando {duracion}s a {sr}Hz...\")\n            audio = sd.rec(int(sr * duracion), sr, 1, device=dispositivo_id, dtype=\"float32\")\n            sd.wait()\n            \n            # Normalizar audio\n            audio = audio.flatten()\n            rms = np.sqrt(np.mean(audio ** 2))\n            \n            self.resultado[\"etapas\"][\"captura_audio\"] = {\n                \"duracion_s\": duracion,\n                \"sample_rate\": sr,\n                \"muestras\": len(audio),\n                \"rms_nivel\": float(rms),\n                \"rms_db\": float(20 * np.log10(rms + 1e-10)),\n                \"minimo\": float(np.min(audio)),\n                \"maximo\": float(np.max(audio)),\n            }\n            \n            logger.info(f\"  ✓ Audio capturado (RMS: {rms:.4f}, dB: {20*np.log10(rms+1e-10):.1f})\")\n            \n            # Guardar para análisis posterior\n            self._ultimo_audio = audio\n            \n        except Exception as e:\n            logger.error(f\"  ❌ Error capturando audio: {e}\")\n            self.resultado[\"etapas\"][\"captura_audio\"] = {\"error\": str(e)}\n            self._ultimo_audio = None\n\n    def _evaluar_vad(self):\n        \"\"\"Etapa 4: Evalúa detección de voz (Voice Activity Detection).\"\"\"\n        logger.info(\"👂 Etapa 4: Evaluando VAD (detección de voz)...\")\n        \n        if not hasattr(self, '_ultimo_audio') or self._ultimo_audio is None:\n            logger.warning(\"  ⚠️ No hay audio capturado para evaluar\")\n            self.resultado[\"etapas\"][\"vad\"] = {\"error\": \"Sin audio capturado\"}\n            return\n        \n        if not SILERO_DISPONIBLE:\n            logger.warning(\"  ⚠️ Silero VAD no disponible\")\n            self.resultado[\"etapas\"][\"vad\"] = {\"error\": \"Silero VAD no instalado\"}\n            return\n        \n        try:\n            # Preparar audio para Silero (16kHz, mono, float32)\n            audio_torch = torch.FloatTensor(self._ultimo_audio)\n            \n            # Obtener timestamps de voz\n            timestamps = get_speech_timestamps(audio_torch, _VAD_MODEL, sampling_rate=16000)\n            \n            # Calcular porcentaje de habla\n            total_habla_samples = sum(ts[\"end\"] - ts[\"start\"] for ts in timestamps)\n            porcentaje_habla = (total_habla_samples / len(self._ultimo_audio)) * 100\n            \n            self.resultado[\"etapas\"][\"vad\"] = {\n                \"segmentos_detectados\": len(timestamps),\n                \"duracion_habla_s\": float(total_habla_samples / 16000),\n                \"porcentaje_habla\": float(porcentaje_habla),\n                \"timestamps\": timestamps[:5],  # Primeros 5 para debugging\n            }\n            \n            logger.info(f\"  ✓ VAD: {len(timestamps)} segmento(s) de voz detectado(s) ({porcentaje_habla:.1f}%)\")\n            \n            if porcentaje_habla < 10:\n                logger.warning(f\"  ⚠️ Poco audio detectado (<10% habla)\")\n            \n        except Exception as e:\n            logger.error(f\"  ❌ Error en VAD: {e}\")\n            self.resultado[\"etapas\"][\"vad\"] = {\"error\": str(e)}\n\n    def _detectar_wake_word(self):\n        \"\"\"Etapa 5: Intenta transcribir y detectar wake word.\"\"\"\n        logger.info(\"🔍 Etapa 5: Detectando wake word...\")  \n        \n        if not hasattr(self, '_ultimo_audio') or self._ultimo_audio is None:\n            logger.warning(\"  ⚠️ No hay audio para transcribir\")\n            self.resultado[\"etapas\"][\"wake_word\"] = {\"error\": \"Sin audio\"}\n            return\n        \n        try:\n            import whisper\n            import re\n            \n            # Transcribir con Whisper\n            modelo_whisper = whisper.load_model(\"base\", device=\"cuda\" if torch.cuda.is_available() else \"cpu\")\n            resultado_whisper = modelo_whisper.transcribe(\n                self._ultimo_audio,\n                language=\"es\",\n                verbose=False,\n            )\n            \n            texto = resultado_whisper.get(\"text\", \"\").strip()\n            confianza = resultado_whisper.get(\"segments\", [{}])[0].get(\"no_speech_prob\", 0.5)\n            \n            # Detectar wake words\n            patron_wake = re.compile(\n                r\"\\b(?:computadora|compu|computador|g[oó]l[eé]m|emet|oye|hey)\\b\",\n                re.IGNORECASE,\n            )\n            \n            wake_detectado = bool(patron_wake.search(texto))\n            \n            self.resultado[\"etapas\"][\"wake_word\"] = {\n                \"texto_transcrito\": texto,\n                \"confianza_habla\": float(1 - confianza),\n                \"wake_word_detectado\": wake_detectado,\n                \"matches_wake_word\": patron_wake.findall(texto) if wake_detectado else [],\n            }\n            \n            logger.info(f\"  ✓ Transcripción: '{texto}'\")\n            if wake_detectado:\n                logger.info(f\"  ✓ Wake word DETECTADO en audio\")\n            else:\n                logger.warning(f\"  ⚠️ Wake word NO detectado (pero audio SÍ capturado)\")\n            \n        except Exception as e:\n            logger.error(f\"  ❌ Error en wake word detection: {e}\")\n            self.resultado[\"etapas\"][\"wake_word\"] = {\"error\": str(e)}\n\n    def _guardar_reporte(self):\n        \"\"\"Guarda reporte en archivo JSON.\"\"\"\n        try:\n            ruta_reporte = self._ruta_logs / f\"diagnostico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\"\n            with open(ruta_reporte, \"w\", encoding=\"utf-8\") as f:\n                import json\n                json.dump(self.resultado, f, ensure_ascii=False, indent=2)\n            logger.info(f\"  📄 Reporte guardado: {ruta_reporte}\")\n        except Exception as e:\n            logger.error(f\"  ❌ Error guardando reporte: {e}\")\n\n\ndef diagnosticar_microfono() -> Dict[str, Any]:\n    \"\"\"Función pública para ejecutar diagnóstico de micrófono.\"\"\"  \n    diagnostico = DiagnosticoMicrofono()\n    return diagnostico.ejecutar_diagnostico_completo()\n

