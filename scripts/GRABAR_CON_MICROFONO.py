#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRABADOR DE AUDIO CON MICRÓFONO
Captura audio del micrófono, transcribe con Whisper, busca contraseña en PDF
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path

# Asegurar UTF-8
os.system("chcp 65001 > nul 2>&1")

print("""
═══════════════════════════════════════════════════════════════════════════════
🎤 GRABADOR DE AUDIO - OPCIÓN MICRÓFONO
═══════════════════════════════════════════════════════════════════════════════

INSTRUCCIONES:
1. Asegúrate de tener un micrófono conectado
2. Ve a YouTube: https://www.youtube.com/watch?v=Apv4cRO0DWo
3. CAMBIA EL IDIOMA A PORTUGUÉS (opción de idioma en el video)
4. Coloca el micrófono CERCA del altavoz
5. Presiona ENTER para empezar a grabar
6. REPRODUCE el video (primeros 30 segundos son suficientes)
7. El script grabará y transcribirá automáticamente

═══════════════════════════════════════════════════════════════════════════════
""")

input("⏱️  Presiona ENTER cuando estés listo para grabar...")

print("\n🔴 GRABANDO AUDIO (30 segundos)...")
print("🔊 Sube el volumen del altavoz y reproduce el video en portugués\n")

# Ruta del archivo de audio
audio_file = "audio_capturado.wav"

# Grabar audio del micrófono por 30 segundos
# Nombre exacto del dispositivo detectado
mic_name = "Microphone Array (IntelÂ® Smart Sound Technology (IntelÂ® SST))"

ffmpeg_cmd = [
    "ffmpeg",
    "-f", "dshow",
    "-i", f"audio={mic_name}",
    "-t", "30",
    "-y",  # Sobrescribir sin preguntar
    audio_file
]

try:
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=35)
    if result.returncode != 0 and "Unknown encoder" not in result.stderr:
        print(f"⚠️  FFmpeg aviso: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    print("⚠️  FFmpeg timeout (normal si grabó los 30s)")
except Exception as e:
    print(f"❌ Error grabando: {e}")
    print("\n💡 ALTERNATIVA: ¿Puedes copiar manualmente el texto del video?")
    sys.exit(1)

if not os.path.exists(audio_file):
    print("❌ No se grabó audio. Verifica:")
    print("  1. Micrófono conectado y funcionando")
    print("  2. Volumen del sistema activado")
    sys.exit(1)

print(f"✅ Audio grabado: {audio_file}")

# Transcribir con Whisper
print("\n🧠 Transcribiendo con Whisper (esto puede tomar 1-2 minutos)...\n")

try:
    from computadora.cerebro.whisper_local import TranscriptorWhisper
    
    transcriptor = TranscriptorWhisper()
    resultado = transcriptor.transcribir(audio_file)
    
    if resultado and "texto" in resultado:
        transcripcion = resultado["texto"]
        idioma = resultado.get("idioma", "pt")
    else:
        print("❌ Whisper no retornó texto")
        sys.exit(1)
        
except ImportError:
    print("ℹ️  Usando Whisper CLI...")
    try:
        result = subprocess.run(
            ["whisper", audio_file, "--language", "pt", "--output_format", "txt"],
            capture_output=True,
            text=True
        )
        
        txt_file = audio_file.replace(".wav", ".txt").replace(".mp3", ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                transcripcion = f.read().strip()
        else:
            print("❌ Whisper no generó archivo de salida")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error con Whisper: {e}")
        sys.exit(1)

print(f"✅ Transcripción completada ({len(transcripcion)} caracteres)")
print(f"\n📝 TEXTO CAPTURADO:\n{'─' * 79}")
print(transcripcion[:500])
if len(transcripcion) > 500:
    print(f"... [+{len(transcripcion) - 500} caracteres]")
print(f"{'─' * 79}\n")

# Guardar transcripción
transcripcion_file = "transcripcion_pt.txt"
with open(transcripcion_file, 'w', encoding='utf-8') as f:
    f.write(transcripcion)
print(f"✅ Guardado en: {transcripcion_file}")

# Generar candidatos de contraseña
print("\n🔍 GENERANDO CANDIDATOS DE CONTRASEÑA (portugueses)...")

# Palabras que empiezan con V
palabras_v = []
for palabra in transcripcion.split():
    palabra_limpio = palabra.lower().strip('.,!?;:"\'-')
    if palabra_limpio.startswith('v') and len(palabra_limpio) > 2:
        if palabra_limpio not in palabras_v:
            palabras_v.append(palabra_limpio)

# Frases que empiezan con V
frases_v = []
palabras = transcripcion.split()
for i in range(len(palabras) - 1):
    if palabras[i].lower().startswith('v'):
        # Tomar 1-4 palabras
        for j in range(1, min(5, len(palabras) - i)):
            frase = ' '.join(palabras[i:i+j]).lower().strip('.,!?;:"\'-')
            if len(frase) > 3 and frase not in frases_v:
                frases_v.append(frase)

candidatos = palabras_v + frases_v

print(f"\n📍 Palabras con V: {len(palabras_v)}")
for p in palabras_v[:15]:
    print(f"   • {p}")

print(f"\n📍 Frases con V: {len(frases_v)}")
for f in frases_v[:15]:
    print(f"   • {f}")

print(f"\n🎯 TOTAL CANDIDATOS: {len(candidatos)}")

# Intentar desencriptar PDF
pdf_path = "resiste-protected.pdf"

if not os.path.exists(pdf_path):
    print(f"\n❌ PDF no encontrado: {pdf_path}")
    sys.exit(1)

print(f"\n🔓 INTENTANDO DESENCRIPTAR PDF...")
print(f"{'─' * 79}")

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("❌ PyPDF2 no instalado")
    sys.exit(1)

encontrada = False
for idx, candidato in enumerate(candidatos, 1):
    try:
        reader = PdfReader(pdf_path)
        
        # Intentar con contraseña
        if reader.is_encrypted:
            if reader.decrypt(candidato):
                print(f"\n✅ ¡¡¡CONTRASEÑA ENCONTRADA!!!")
                print(f"🔑 Contraseña: '{candidato}'")
                print(f"📊 Intento #{idx}/{len(candidatos)}")
                encontrada = True
                
                # Guardar resultado
                resultado_json = {
                    "contraseña": candidato,
                    "idioma": "portugués",
                    "intento_numero": idx,
                    "total_candidatos": len(candidatos),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("contraseña_encontrada.json", 'w', encoding='utf-8') as f:
                    json.dump(resultado_json, f, ensure_ascii=False, indent=2)
                
                # Extraer y guardar contenido
                print("\n📄 Extrayendo contenido del PDF...")
                try:
                    contenido = ""
                    for page in reader.pages:
                        contenido += page.extract_text() + "\n"
                    
                    with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    
                    print(f"✅ Contenido guardado en: contenido_desencriptado.txt")
                    print(f"\n📋 PRIMERAS 500 CARACTERES:\n{'─' * 79}")
                    print(contenido[:500])
                    print(f"{'─' * 79}")
                except Exception as e:
                    print(f"⚠️  Error extrayendo contenido: {e}")
                
                break
        
        # Mostrar progreso
        if (idx - 1) % 10 == 0 or idx == len(candidatos):
            print(f"[{idx:3d}/{len(candidatos)}] {candidato[:40]:<40} → ❌")
    
    except Exception as e:
        if "Invalid password" not in str(e):
            print(f"⚠️  Error con '{candidato}': {e}")

if not encontrada:
    print(f"\n❌ NO SE ENCONTRÓ CONTRASEÑA")
    print(f"\n💡 PRÓXIMAS OPCIONES:")
    print(f"  1. Repite con los otros idiomas (alemán, inglés, japonés)")
    print(f"  2. Aumenta el volumen del altavoz (quizás Whisper no capturó bien)")
    print(f"  3. Comparte la transcripción manualmente si está incompleta")

print("\n" + "═" * 79)
