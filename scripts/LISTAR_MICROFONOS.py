#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LISTAR DISPOSITIVOS DE MICRÓFONO EN WINDOWS
"""

import subprocess
import os

os.system("chcp 65001 > nul 2>&1")

print("═" * 79)
print("🎤 DISPOSITIVOS DE AUDIO EN WINDOWS")
print("═" * 79)

# Método 1: FFmpeg
print("\n[1] Dispositivos FFmpeg (dshow):")
print("─" * 79)

result = subprocess.run(
    ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
    capture_output=True,
    text=True
)

output = result.stderr + result.stdout
lines = output.split('\n')

audio_devices = []
for line in lines:
    if 'audio' in line.lower() and '@' in line:
        print(f"  {line.strip()}")
        # Extraer nombre del dispositivo
        if '"' in line:
            device_name = line.split('"')[1]
            audio_devices.append(device_name)

print(f"\n✅ Encontrados {len(audio_devices)} dispositivos de audio")

# Método 2: PowerShell (alternativa)
print("\n[2] Dispositivos PowerShell (alternativa):")
print("─" * 79)

ps_cmd = """
Get-WmiObject Win32_SoundDevice | Select-Object Name, DeviceID
"""

result = subprocess.run(
    ["powershell", "-Command", ps_cmd],
    capture_output=True,
    text=True
)

print(result.stdout[:500])

# Método 3: PyAudio
print("\n[3] Intento con PyAudio:")
print("─" * 79)

try:
    import pyaudio
    p = pyaudio.PyAudio()
    
    print(f"✅ PyAudio disponible\n")
    print(f"Total de dispositivos: {p.get_device_count()}\n")
    
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['max_input_channels'] > 0:  # Es un dispositivo de entrada
            print(f"[{i}] {info['name']}")
            print(f"    Canales entrada: {info['max_input_channels']}")
            print(f"    Frecuencia: {info['default_sample_rate']} Hz")
            print()
    
    p.terminate()
except ImportError:
    print("❌ PyAudio no disponible (ejecuta: pip install pyaudio)")

print("═" * 79)
print("""
INSTRUCCIONES SIGUIENTES:

Si viste dispositivos en [1] o [3]:
  1. Copia el nombre exacto del dispositivo (ej: "Microphone" o "USB Audio Device")
  2. Actualiza el script GRABAR_CON_MICROFONO.py con el nombre correcto
  3. Cambia la línea:
     "-i", "audio=Microphone",
     →
     "-i", "audio=<NOMBRE_EXACTO>",

Si no ves dispositivos:
  1. Verifica que el micrófono esté conectado
  2. Comprueba en Configuración → Sonido → Entrada que el micrófono esté activo
  3. Intenta con otro dispositivo USB o Bluetooth
""")
