#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS SEMÁNTICO PROFUNDO - TRANSCRIBA, COMPRENDA, BUSQUE PISTAS
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from collections import Counter
import re

os.system("chcp 65001 > nul 2>&1")

print("""
═══════════════════════════════════════════════════════════════════════════════
🔍 ANÁLISIS SEMÁNTICO PROFUNDO - TODO ES PISTA
═══════════════════════════════════════════════════════════════════════════════

FASES:
  1️⃣  Transcribir audios con Whisper
  2️⃣  Guardar transcripciones completas
  3️⃣  Analizar semánticamente (palabras clave, frases, conceptos)
  4️⃣  Generar candidatos inteligentes
  5️⃣  Probar contra PDF
  6️⃣  REPORTAR

═══════════════════════════════════════════════════════════════════════════════
""")

# FASE 1: TRANSCRIBIR
print("🎙️  FASE 1: TRANSCRIBIENDO AUDIOS")
print("─" * 79)

wav_files = list(Path(".").glob("WhatsApp Ptt *.wav"))
wav_files.sort()

idiomas = ["es", "pt", "de", "en", "ja"]
nombres_idiomas = {
    "es": "Español (MX)",
    "pt": "Portugués (BR)",
    "de": "Alemán",
    "en": "Inglés",
    "ja": "Japonés"
}

transcripciones = {}

for idx, wav_file in enumerate(wav_files):
    idioma = idiomas[idx] if idx < len(idiomas) else "es"
    nombre_idioma = nombres_idiomas.get(idioma, idioma)
    
    print(f"\n📥 [{idx+1}/{len(wav_files)}] {nombre_idioma}")
    print(f"   Archivo: {wav_file.name} ({wav_file.stat().st_size} bytes)")
    
    try:
        result = subprocess.run(
            ["whisper", str(wav_file), "--language", idioma, "--output_format", "txt", "-q"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        txt_file = wav_file.with_suffix(".txt")
        if txt_file.exists():
            with open(txt_file, 'r', encoding='utf-8') as f:
                texto = f.read().strip()
            
            transcripciones[idioma] = texto
            print(f"   ✅ Transcrito: {len(texto)} caracteres")
            print(f"   📝 Primeros 150 chars: {texto[:150]}...")
        else:
            print(f"   ⚠️  Whisper no generó salida")
    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout en transcripción")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Total transcripciones: {len(transcripciones)}")

if not transcripciones:
    print("❌ No se obtuvieron transcripciones")
    sys.exit(1)

# FASE 2: GUARDAR DOCUMENTO
print("\n📄 FASE 2: GUARDANDO TRANSCRIPCIONES COMPLETAS")
print("─" * 79)

doc_content = """
═══════════════════════════════════════════════════════════════════════════════
TRANSCRIPCIONES COMPLETAS - ANÁLISIS SEMÁNTICO
═══════════════════════════════════════════════════════════════════════════════

"""

for idioma, texto in transcripciones.items():
    nombre = nombres_idiomas.get(idioma, idioma)
    doc_content += f"\n{'='*79}\n"
    doc_content += f"🗣️  {nombre.upper()} ({idioma})\n"
    doc_content += f"{'='*79}\n\n"
    doc_content += f"{texto}\n\n"

with open("TRANSCRIPCIONES_COMPLETAS.txt", 'w', encoding='utf-8') as f:
    f.write(doc_content)

print(f"✅ Documento guardado: TRANSCRIPCIONES_COMPLETAS.txt")

# FASE 3: ANÁLISIS SEMÁNTICO
print("\n🧠 FASE 3: ANÁLISIS SEMÁNTICO PROFUNDO")
print("─" * 79)

analisis = {}

for idioma, texto in transcripciones.items():
    nombre = nombres_idiomas.get(idioma, idioma)
    print(f"\n📍 {nombre}:")
    
    # Palabras importantes (filtrar stopwords comunes)
    stopwords = {
        "es": {"el", "la", "de", "que", "es", "y", "a", "en", "con", "los", "las", "por", "para", "del", "un", "una", "en", "al"},
        "pt": {"o", "a", "de", "que", "é", "e", "em", "com", "para", "os", "as", "por", "dos", "das", "um", "uma", "ao"},
        "de": {"der", "die", "das", "und", "ist", "ein", "eine", "mit", "in", "zu", "von", "den", "des", "dem", "für"},
        "en": {"the", "and", "a", "to", "of", "is", "in", "it", "for", "with", "that", "on", "this", "be", "you"},
        "ja": {"は", "を", "に", "が", "で", "も", "から", "まで", "ある", "いる"}
    }
    
    stop = stopwords.get(idioma, set())
    
    # Palabras significativas
    palabras = texto.lower().split()
    palabras_sig = [p.strip('.,!?;:"\'-') for p in palabras if len(p.strip('.,!?;:"\'-')) > 3 and p.lower().strip('.,!?;:"\'-') not in stop]
    
    # Frecuencias
    freq = Counter(palabras_sig)
    top_palabras = freq.most_common(15)
    
    print(f"   Palabras clave (top 10):")
    for palabra, count in top_palabras[:10]:
        print(f"      • {palabra} ({count}x)")
    
    # Frases significativas (segmentos de 2-5 palabras)
    frases = []
    for i in range(len(palabras) - 4):
        frase = " ".join(palabras[i:i+5]).lower().strip('.,!?;:"\'-')
        if len(frase) > 10:
            frases.append(frase)
    
    frase_freq = Counter(frases)
    frases_unicas = [f for f, c in frase_freq.most_common(20) if c >= 1]
    
    print(f"   Frases principales:")
    for frase in frases_unicas[:5]:
        print(f"      • {frase}")
    
    # Conceptos clave por idioma
    conceptos = {
        "es": ["verdad", "vida", "muerte", "fin", "principio", "resiste", "despertar", "conciencia", "libertad", "camino"],
        "pt": ["verdade", "vida", "morte", "fim", "começo", "resista", "acordar", "consciência", "liberdade", "caminho"],
        "de": ["wahrheit", "leben", "tod", "ende", "anfang", "widerstand", "aufwachen", "bewusstsein", "freiheit", "weg"],
        "en": ["truth", "life", "death", "end", "beginning", "resist", "awake", "consciousness", "freedom", "path"],
        "ja": ["真実", "生活", "死", "終わり", "始まり", "抵抗", "目覚め", "意識", "自由", "道"]
    }
    
    conceptos_encontrados = []
    text_lower = texto.lower()
    for concepto in conceptos.get(idioma, []):
        if concepto in text_lower:
            conceptos_encontrados.append(concepto)
    
    print(f"   Conceptos encontrados: {conceptos_encontrados}")
    
    analisis[idioma] = {
        "palabras_clave": top_palabras[:10],
        "frases_principales": frases_unicas[:5],
        "conceptos": conceptos_encontrados
    }

# FASE 4: GENERAR CANDIDATOS INTELIGENTES
print("\n🔐 FASE 4: GENERANDO CANDIDATOS INTELIGENTES")
print("─" * 79)

candidatos_inteligentes = []

# Estrategia 1: Palabras clave más frecuentes en cada idioma
for idioma, data in analisis.items():
    for palabra, count in data["palabras_clave"][:5]:
        if len(palabra) > 2:
            candidatos_inteligentes.append(palabra)
            candidatos_inteligentes.append(palabra.capitalize())
            candidatos_inteligentes.append(palabra.upper())

# Estrategia 2: Frases cortas significativas
for idioma, data in analisis.items():
    for frase in data["frases_principales"][:3]:
        # Sin espacios
        frase_clean = frase.replace(" ", "").strip('.,!?;:"\'-')
        if len(frase_clean) > 3:
            candidatos_inteligentes.append(frase_clean)
        
        # Con espacios
        if len(frase) < 30:
            candidatos_inteligentes.append(frase)

# Estrategia 3: Conceptos encontrados
for idioma, data in analisis.items():
    for concepto in data["conceptos"]:
        candidatos_inteligentes.append(concepto)
        candidatos_inteligentes.append(concepto.capitalize())

# Estrategia 4: Palabras que empiezan con V (aún relevante)
for idioma, texto in transcripciones.items():
    for palabra in texto.split():
        palabra_clean = palabra.lower().strip('.,!?;:"\'-')
        if palabra_clean.startswith('v') and len(palabra_clean) > 2:
            candidatos_inteligentes.append(palabra_clean)

# Eliminar duplicados manteniendo orden
candidatos_inteligentes = list(dict.fromkeys(candidatos_inteligentes))
print(f"✅ Total candidatos generados: {len(candidatos_inteligentes)}")

# Mostrar algunos
print(f"\n🎯 Primeros 30 candidatos:")
for i, c in enumerate(candidatos_inteligentes[:30], 1):
    print(f"   [{i:2d}] {c}")

# FASE 5: DESENCRIPTAR PDF
print("\n🔓 FASE 5: DESENCRIPTANDO PDF")
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

print(f"📄 {pdf_path} ({os.path.getsize(pdf_path)} bytes)\n")

encontrada = False
total_candidatos = len(candidatos_inteligentes)

for idx, candidato in enumerate(candidatos_inteligentes, 1):
    try:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            if reader.decrypt(candidato):
                print(f"\n{'='*79}")
                print(f"✅✅✅ ¡¡¡CONTRASEÑA ENCONTRADA!!!")
                print(f"{'='*79}")
                print(f"🔑 Contraseña: '{candidato}'")
                print(f"📊 Intento: #{idx}/{total_candidatos}")
                print(f"{'='*79}\n")
                
                encontrada = True
                
                # Guardar resultado
                resultado_json = {
                    "contraseña": candidato,
                    "intento_numero": idx,
                    "total_candidatos": total_candidatos,
                    "estrategia": "análisis semántico profundo",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("contraseña_encontrada.json", 'w', encoding='utf-8') as f:
                    json.dump(resultado_json, f, ensure_ascii=False, indent=2)
                
                # Extraer contenido
                print("📄 Extrayendo contenido del PDF...\n")
                try:
                    contenido = ""
                    for page in reader.pages:
                        contenido += page.extract_text() + "\n"
                    
                    with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    
                    print(f"✅ Contenido guardado: contenido_desencriptado.txt")
                    print(f"\n{'─'*79}")
                    print("📋 CONTENIDO COMPLETO:")
                    print(f"{'─'*79}\n")
                    print(contenido)
                    print(f"\n{'─'*79}")
                except Exception as e:
                    print(f"⚠️  Error extrayendo contenido: {e}")
                
                break
    except Exception as e:
        if "Invalid password" not in str(e):
            pass  # Silenciar errores normales
    
    if (idx - 1) % 20 == 0 or idx == len(candidatos_inteligentes):
        print(f"Probando: [{idx:3d}/{total_candidatos}]", end="\r")
    
    if encontrada:
        break

if not encontrada:
    print(f"\n❌ NO SE ENCONTRÓ CONTRASEÑA")
    print(f"Probados: {total_candidatos} candidatos")
    
    # Guardar candidatos para referencia
    with open("candidatos_probados.json", 'w', encoding='utf-8') as f:
        json.dump(candidatos_inteligentes, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Candidatos guardados: candidatos_probados.json")

print("\n" + "═" * 79)
print("✨ WORKFLOW COMPLETADO")
print("═" * 79 + "\n")
