"""Test: graba 3 segundos y transcribe con Whisper para verificar que el pipeline funciona."""
import numpy as np
import sounddevice as sd
from scipy.signal import resample
import whisper
import torch

SR_MIC = 44100
SR_WHISPER = 16000
DURACION = 3
DEVICE = 1
CHANNELS = 2

print(f"Grabando {DURACION}s desde dispositivo [{DEVICE}] sr={SR_MIC} ch={CHANNELS}...")
print("HABLA AHORA!")
audio = sd.rec(int(DURACION * SR_MIC), samplerate=SR_MIC, channels=CHANNELS, dtype="float32", device=DEVICE)
sd.wait()
print(f"Grabación completada. Shape: {audio.shape}")

# Tomar canal 0
if audio.ndim > 1:
    audio = audio[:, 0]

print(f"Canal 0 - max={np.max(np.abs(audio)):.4f}, mean={np.mean(np.abs(audio)):.4f}")

# Resamplear
num_muestras = int(len(audio) * SR_WHISPER / SR_MIC)
audio_16k = resample(audio, num_muestras).astype(np.float32)
print(f"Resampleado: {len(audio)} -> {len(audio_16k)} muestras")
print(f"Post-resample - max={np.max(np.abs(audio_16k)):.4f}, mean={np.mean(np.abs(audio_16k)):.4f}")

# Normalizar
max_val = np.max(np.abs(audio_16k))
if max_val > 0.001:
    audio_16k = audio_16k / max_val * 0.95
print(f"Post-normalize - max={np.max(np.abs(audio_16k)):.4f}")

# Transcribir
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Cargando Whisper en {device}...")
modelo = whisper.load_model("base", device=device)
print("Transcribiendo...")
resultado = modelo.transcribe(audio_16k, language="es", fp16=(device == "cuda"))
print(f"RESULTADO: '{resultado['text']}'")
