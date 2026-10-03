#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROCESAR AUDIOS MULTIIDIOMA - TRANSCRIBIR + EXTRAER CONTRASEÑA
5 archivos OGG → Whisper → Candidatos → PDF Decrypt
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

os.system("chcp 65001 > nul 2>&1")

print("""
═══════════════════════════════════════════════════════════════════════════════
🎙️  PROCESADOR MULTIIDIOMA - WORKFLOW COMPLETO
═══════════════════════════════════════════════════════════════════════════════

FASES:
  1️⃣  Verificar archivos de audio
  2️⃣  Transcribir con Whisper (cada idioma)
  3️⃣  Extraer candidatos de contraseña
  4️⃣  Desencriptar PDF
  5️⃣  Reportar resultado ✨

═══════════════════════════════════════════════════════════════════════════════
""")

# Archivos de audio disponibles (en orden de creación)
audios_esperados = {
    "audio_1_es.ogg": ("es", "Español (MX)"),
    "audio_2_pt.ogg": ("pt", "Portugués (BR)"),
    "audio_3_de.ogg": ("de", "Alemán"),
    "audio_4_en.ogg": ("en", "Inglés"),
    "audio_5_ja.ogg": ("ja", "Japonés"),
}

# Detectar archivos WhatsApp recibidos
print("📂 FASE 1: VERIFICANDO ARCHIVOS DE AUDIO")
print("─" * 79)

audios_encontrados = []
for archivo in Path(".").glob("WhatsApp Ptt *.ogg"):
    audios_encontrados.append(str(archivo))
    print(f"  ✅ {archivo.name} ({archivo.stat().st_size} bytes)")

if not audios_encontrados:
    print("  ❌ No se encontraron archivos OGG")
    sys.exit(1)

audios_encontrados.sort()
print(f"\n✅ Total: {len(audios_encontrados)} archivos de audio\n")

# FASE 2: TRANSCRIBIR
print("🧠 FASE 2: TRANSCRIBIENDO CON WHISPER")
print("─" * 79)

transcripciones = {}
idiomas = ["es", "pt", "de", "en", "ja"]
nombres_idiomas = {
    "es": "Español (MX)",
    "pt": "Portugués (BR)",
    "de": "Alemán",
    "en": "Inglés",
    "ja": "Japonés"
}

for idx, archivo_ogg in enumerate(audios_encontrados):
    idioma = idiomas[idx] if idx < len(idiomas) else "es"
    nombre_idioma = nombres_idiomas.get(idioma, idioma)
    
    print(f"\n📥 [{idx+1}/{len(audios_encontrados)}] {nombre_idioma}")
    print(f"   Archivo: {Path(archivo_ogg).name}")
    
    # Transcribir con Whisper
    try:
        result = subprocess.run(
            ["whisper", archivo_ogg, "--language", idioma, "--output_format", "txt", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        txt_file = archivo_ogg.replace(".ogg", ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, 'r', encoding='utf-8') as f:
                texto = f.read().strip()
            
            transcripciones[idioma] = texto
            print(f"   ✅ Transcrito: {len(texto)} caracteres")
            
            # Guardar en archivo estándar
            archivo_final = f"transcripcion_{idioma}.txt"
            with open(archivo_final, 'w', encoding='utf-8') as f:
                f.write(texto)
            print(f"   💾 Guardado: {archivo_final}")
        else:
            print(f"   ⚠️  Whisper no generó salida")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Transcripciones completadas: {len(transcripciones)}")

# FASE 3: EXTRAER CANDIDATOS
print("\n🔍 FASE 3: EXTRAYENDO CANDIDATOS DE CONTRASEÑA")
print("─" * 79)

todos_candidatos = {}

for idioma, texto in transcripciones.items():
    print(f"\n📍 {nombres_idiomas.get(idioma, idioma)}:")
    
    # Palabras que empiezan con V
    palabras_v = []
    for palabra in texto.split():
        palabra_limpio = palabra.lower().strip('.,!?;:"\'-')
        if palabra_limpio.startswith('v') and len(palabra_limpio) > 2:
            if palabra_limpio not in palabras_v:
                palabras_v.append(palabra_limpio)
    
    # Frases que empiezan con V (1-4 palabras)
    frases_v = []
    palabras = texto.split()
    for i in range(len(palabras) - 1):
        if palabras[i].lower().startswith('v'):
            for j in range(1, min(5, len(palabras) - i)):
                frase = ' '.join(palabras[i:i+j]).lower().strip('.,!?;:"\'-')
                if len(frase) > 3 and frase not in frases_v:
                    frases_v.append(frase)
    
    candidatos = palabras_v + frases_v
    todos_candidatos[idioma] = candidatos
    
    print(f"   Palabras V: {len(palabras_v)}")
    for p in palabras_v[:10]:
        print(f"      • {p}")
    
    print(f"   Frases V: {len(frases_v)}")
    for f in frases_v[:10]:
        print(f"      • {f}")
    
    print(f"   Total: {len(candidatos)}")

# FASE 4: DESENCRIPTAR PDF
print("\n🔓 FASE 4: DESENCRIPTANDO PDF")
print("─" * 79)

pdf_path = "resiste-protected.pdf"

if not os.path.exists(pdf_path):
    print(f"❌ PDF no encontrado: {pdf_path}")
    sys.exit(1)

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("❌ PyPDF2 no instalado")
    sys.exit(1)

print(f"\n📄 {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

encontrada = False
total_candidatos = sum(len(c) for c in todos_candidatos.values())
contador_global = 0

for idioma in idiomas:
    if idioma not in todos_candidatos:
        continue
    
    candidatos = todos_candidatos[idioma]
    nombre_idioma = nombres_idiomas.get(idioma, idioma)
    
    print(f"\n🧪 Probando {nombre_idioma} ({len(candidatos)} candidatos)...")
    
    for idx, candidato in enumerate(candidatos, 1):
        contador_global += 1
        
        try:
            reader = PdfReader(pdf_path)
            
            if reader.is_encrypted:
                if reader.decrypt(candidato):
                    print(f"\n{'='*79}")
                    print(f"✅✅✅ ¡¡¡CONTRASEÑA ENCONTRADA!!!")
                    print(f"{'='*79}")
                    print(f"🔑 Contraseña: '{candidato}'")
                    print(f"🗣️  Idioma: {nombre_idioma}")
                    print(f"📊 Intento: #{contador_global}/{total_candidatos}")
                    print(f"{'='*79}\n")
                    
                    encontrada = True
                    
                    # Guardar resultado
                    resultado_json = {
                        "contraseña": candidato,
                        "idioma": idioma,
                        "nombre_idioma": nombre_idioma,
                        "intento_numero": contador_global,
                        "total_candidatos": total_candidatos,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    with open("contraseña_encontrada.json", 'w', encoding='utf-8') as f:
                        json.dump(resultado_json, f, ensure_ascii=False, indent=2)
                    
                    # Extraer contenido
                    print("📄 Extrayendo contenido...")
                    try:
                        contenido = ""
                        for page in reader.pages:
                            contenido += page.extract_text() + "\n"
                        
                        with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                            f.write(contenido)
                        
                        print(f"✅ Contenido guardado: contenido_desencriptado.txt")
                        print(f"\n{'─'*79}")
                        print("📋 PRIMEROS 1000 CARACTERES:")
                        print(f"{'─'*79}\n")
                        print(contenido[:1000])
                        print(f"\n{'─'*79}")
                    except Exception as e:
                        print(f"⚠️  Error extrayendo contenido: {e}")
                    
                    break
        except Exception as e:
            if "Invalid password" not in str(e):
                print(f"⚠️  Error: {e}")
        
        if encontrada:
            break
    
    if encontrada:
        break

if not encontrada:
    print(f"\n❌ NO SE ENCONTRÓ CONTRASEÑA")
    print(f"   Probados: {contador_global} candidatos")
    print(f"\n💡 Próximas opciones:")
    print(f"   1. Verificar que todos los 5 idiomas fueron capturados")
    print(f"   2. Revisar si la calidad de audio es suficiente")
    print(f"   3. Probar con variaciones de puntuación/espacios")

print("\n" + "═" * 79)
print("🔄 WORKFLOW COMPLETADO")
print("═" * 79 + "\n")
