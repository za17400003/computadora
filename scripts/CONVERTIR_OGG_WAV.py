#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONVERTIR OGG → WAV y PROCESAR CON WHISPER
"""

import os
import subprocess
from pathlib import Path

os.system("chcp 65001 > nul 2>&1")

print("🎙️  CONVIRTIENDO OGG → WAV...\n")

# Encontrar todos los OGG
ogg_files = list(Path(".").glob("WhatsApp Ptt *.ogg"))
ogg_files.sort()

for ogg_file in ogg_files:
    wav_file = ogg_file.with_suffix(".wav")
    print(f"🔄 {ogg_file.name}")
    
    # Convertir con ffmpeg
    cmd = [
        "ffmpeg",
        "-i", str(ogg_file),
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-y",
        str(wav_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if wav_file.exists():
        print(f"   ✅ → {wav_file.name}")
    else:
        print(f"   ❌ Conversión falló")

print("\n✅ Conversión completada\n")
