#!/usr/bin/env python3
"""
DIAGNÓSTICO VOLUMEN MICRÓFONO — Computadora No Responde
Verifica que el micrófono en Windows capture volumen suficiente.

GOTCHA (Abril 26, 2026): 90% de los reportes "no me entiende" son por
micrófono MUY BAJO en Windows, no bugs de código.

Umbral crítico: RMS > 0.015 (sistema detecta voz), < 0.001 (sistema "sordo")
Intel Bluetooth típicamente entrega: 0.00003-0.0001 (SOS)
USB externo típicamente entrega: 0.02-0.05 (OK)
"""

import sys
import time
import numpy as np
from pathlib import Path

# Agregar proyecto al path
proyecto_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proyecto_root))

print("=" * 80)
print("🎤 DIAGNÓSTICO VOLUMEN MICRÓFONO — Computadora No Responde a Voz")
print("=" * 80)

# TEST 1: sounddevice disponible
print("\n[TEST 1] Verificar sounddevice")
print("-" * 80)
try:
    import sounddevice as sd
    import scipy.io.wavfile as wavfile
    print("✓ sounddevice importado")
except ImportError as e:
    print(f"❌ ERROR: sounddevice NO disponible: {e}")
    print("  FIX: pip install sounddevice scipy")
    sys.exit(1)

# TEST 2: Listar dispositivos de audio
print("\n[TEST 2] Listar Dispositivos de Audio")
print("-" * 80)
devices = sd.query_devices()
mics = []
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:  # Entrada (micrófono)
        mics.append((i, dev['name'], dev['max_input_channels']))
        marker = " ◄ DEFAULT" if i == sd.default.device[0] else ""
        print(f"  [{i:2d}] {dev['name']:<50s} (canales={dev['max_input_channels']}){marker}")

if not mics:
    print("❌ ERROR: No hay dispositivos de entrada (micrófono) detectados")
    sys.exit(1)

# TEST 3: Capturar audio y medir RMS
print("\n[TEST 3] Capturar Audio (10 segundos) y Medir Nivel")
print("-" * 80)
print("👂 Hablando NORMAL (en voz conversacional)...")
print("   Espera 10 segundos... puedes hablar libremente")

SAMPLERATE = 16000
DURATION = 10  # segundos

try:
    audio = sd.rec(int(SAMPLERATE * DURATION), samplerate=SAMPLERATE, channels=1, dtype='float32')
    sd.wait()
    print("✓ Audio capturado")
except Exception as e:
    print(f"❌ ERROR al capturar: {e}")
    sys.exit(1)

# Calcular estadísticas
audio_mono = audio[:, 0] if audio.ndim > 1 else audio
rms_nivel = np.sqrt(np.mean(audio_mono ** 2))
pico_nivel = np.abs(audio_mono).max()
ruido_piso = np.percentile(np.abs(audio_mono), 10)  # 10% cuantil = ruido de fondo

print(f"\n📊 ESTADÍSTICAS DE AUDIO CAPTURADO:")
print(f"   RMS Nivel:       {rms_nivel:.6f}")
print(f"   Pico Máximo:     {pico_nivel:.6f}")
print(f"   Piso de Ruido:   {ruido_piso:.6f}")

# TEST 4: Diagnosticar problema
print("\n[TEST 4] DIAGNÓSTICO")
print("-" * 80)

UMBRAL_CRITICO = 0.015   # Sistema detecta voz
UMBRAL_SORDO = 0.001     # Sistema "sordo" (mudo)
UMBRAL_BAJO = 0.005      # Muy bajo, errores de reconocimiento

if rms_nivel < UMBRAL_SORDO:
    print(f"🔴 CRÍTICO: RMS {rms_nivel:.6f} < {UMBRAL_SORDO:.6f}")
    print("   Sistema está SORDO (no detecta voz)")
    print("")
    print("   SOLUCIONES (en orden):")
    print("   1. Abre 'Sound Settings' (Settings > System > Sound)")
    print("   2. Bajo 'Input': Sube el slider de 'Microphone' a 100%")
    print("   3. Haz clic en 'App volume and device preferences'")
    print("   4. Busca 'computadora' y asegúrate de que input esté a 100%")
    print("   5. Abre 'Control Panel > Sound > Recording devices'")
    print("   6. Click derecho en tu micrófono > Properties > Levels")
    print("   7. Sube 'Microphone' al máximo (100)")
    print("   8. Activa 'Microphone Boost' (+20dB minimum)")
    print("   9. Aplica cambios")
    print("")
    print("   Si aún sigue bajo, prueba con un micrófono USB externo.")
    
elif rms_nivel < UMBRAL_BAJO:
    print(f"🟠 BAJO: RMS {rms_nivel:.6f} < {UMBRAL_BAJO:.6f}")
    print("   Sistema probablemente NO detecta voz o tiene errores")
    print("")
    print("   SOLUCIONES:")
    print("   1. Sube volumen en Windows (ver arriba, paso 1-8)")
    print("   2. Acércate más al micrófono cuando hables")
    print("   3. Prueba hablando más fuerte")
    print("   4. Verifica que no haya ruido competidor")
    
elif rms_nivel < UMBRAL_CRITICO:
    print(f"🟡 MARGINAL: RMS {rms_nivel:.6f} < {UMBRAL_CRITICO:.6f}")
    print("   Sistema PUEDE detectar voz pero es inestable")
    print("")
    print("   RECOMENDACIÓN:")
    print("   1. Sube un poco más en Windows Sound Settings")
    print("   2. O acércate más al micrófono")
    
else:
    print(f"✅ OK: RMS {rms_nivel:.6f} > {UMBRAL_CRITICO:.6f}")
    print("   Nivel de micrófono ADECUADO para reconocimiento de voz")
    print("")
    print("   Si aún Computadora no responde, problema NO es volumen.")
    print("   Ejecuta: scripts/diagnostico_audio.py")

# TEST 5: Guardar archivo de debug si bajo
print("\n[TEST 5] Guardar Captura de Audio")
print("-" * 80)
audio_output = Path("_audit/audio_debug.wav")
audio_output.parent.mkdir(parents=True, exist_ok=True)
try:
    # sounddevice da float32 [-1, 1], scipy.wavfile espera int16 o float32
    wavfile.write(str(audio_output), SAMPLERATE, audio_mono.astype('float32'))
    print(f"✓ Audio guardado en: {audio_output}")
    print(f"  Puedes revisar manualmente para verificar que contiene voz")
except Exception as e:
    print(f"⚠ Error al guardar: {e}")

print("\n" + "=" * 80)
print("📝 PRÓXIMOS PASOS:")
print("-" * 80)
if rms_nivel < UMBRAL_CRITICO:
    print("1. Ajusta volumen en Windows Sound Settings (ver arriba)")
    print("2. Vuelve a ejecutar este diagnóstico")
    print("3. Si aún bajo, ejecuta: python scripts/diagnostico_audio.py")
else:
    print("1. Ejecuta: computadora_start.bat")
    print("2. Prueba hablando con Computadora")
    print("3. Si aún no responde, el problema es otro (vuelve a revisar logs)")

print("=" * 80)
