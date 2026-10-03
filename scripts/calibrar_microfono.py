#!/usr/bin/env python3
"""
AUDIO CALIBRATION — Ajustar micrófono para que Computadora escuche
"""

import sounddevice as sd
import numpy as np
import time
from pathlib import Path

print("=" * 70)
print("🎙️ CALIBRACIÓN DE MICRÓFONO — Computadora")
print("=" * 70)

print("""
Tu micrófono está MUY BAJO. Necesitas:
1. Aumentar volumen en Windows Settings
2. O ajustar el umbral en config.json

Vamos a calibrar automáticamente...
""")

# Capturar 10 segundos de audio para obtener estadísticas
print("\n📊 CAPTURANDO REFERENCIA (10 segundos)...")
print("   Habla, tose, haz ruido para establecer nivel")

duracion = 10
sr = 16000

# Capturar audio
audio_data = sd.rec(int(duracion * sr), samplerate=sr, channels=1, dtype='float32')
sd.wait()

# Análisis
volumen_promedio = np.abs(audio_data).mean()
volumen_max = np.abs(audio_data).max()
volumen_rms = np.sqrt(np.mean(audio_data ** 2))

# Calcular umbral necesario (80% de máximo detectado)
umbral_calculado = volumen_max * 0.2

print(f"\n📈 ESTADÍSTICAS:")
print(f"   Volumen promedio: {volumen_promedio:.6f}")
print(f"   Volumen RMS:      {volumen_rms:.6f}")
print(f"   Volumen máximo:   {volumen_max:.6f}")
print(f"\n   Umbral actual:     0.015000")
print(f"   Umbral recomendado: {umbral_calculado:.6f}")

# Diagnóstico
print(f"\n🔍 DIAGNÓSTICO:")

if volumen_promedio < 0.001:
    print("   ❌ CRÍTICO: Micrófono muy bajo")
    print("   \n   ACCIONES:")
    print("   1. Abre Settings → Sound → Volume mixer advanced")
    print("   2. Sube el volumen del micrófono al 100%")
    print("   3. Verifica que el micrófono NO esté mutead")
    print("   4. Si es Intel Bluetooth, verifica drivers")
    print("   5. Prueba otro dispositivo de audio")
    print("\n   O ALTERNATIVA:")
    print("   6. Edita _config/config.json:")
    print("      escucha.umbral_volumen: 0.00005")
    print("      (⚠ Pero será muy sensible al ruido ambiental)")
    
elif volumen_promedio < 0.01:
    print("   ⚠ BAJO: Micrófono bajo")
    print("   \n   ACCIONES:")
    print("   1. Aumenta volumen del micrófono en Windows Settings")
    print("   2. Habla más cerca del micrófono")
    print("   3. O ajusta umbral en config.json a: 0.008")
    
else:
    print("   ✓ OK: Micrófono con buen nivel")
    print("   \n   Computadora debería escuchar correctamente")

# Generar recomendación JSON
print(f"\n💾 RECOMENDACIÓN PARA config.json:")
print(f"""
"escucha": {{
    "wake_word": "computadora",
    "umbral_volumen": {umbral_calculado:.6f},
    "silencio_max_segundos": 1.5,
    "frecuencia_muestreo": 16000
}}
""")

print("=" * 70)
print("✓ Calibración completada")
print("=" * 70)
