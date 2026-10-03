#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS SEMÁNTICO - USANDO API DE WHISPER DIRECTAMENTE
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import Counter

os.system("chcp 65001 > nul 2>&1")

print("""
═══════════════════════════════════════════════════════════════════════════════
🔍 ANÁLISIS SEMÁNTICO PROFUNDO - TODO ES PISTA
═══════════════════════════════════════════════════════════════════════════════
""")

try:
    import whisper
except ImportError:
    print("❌ Whisper no disponible")
    sys.exit(1)

# FASE 1: TRANSCRIBIR
print("🎙️  FASE 1: TRANSCRIBIENDO AUDIOS")
print("─" * 79)

wav_files = sorted(list(Path(".").glob("WhatsApp Ptt *.wav")))

idiomas = ["es", "pt", "de", "en", "ja"]
nombres_idiomas = {
    "es": "Español (MX)",
    "pt": "Portugués (BR)",
    "de": "Alemán",
    "en": "Inglés",
    "ja": "Japonés"
}

transcripciones = {}

# Cargar modelo una vez
print("📦 Cargando modelo Whisper base...")
modelo = whisper.load_model("base")
print("✅ Modelo cargado\n")

for idx, wav_file in enumerate(wav_files):
    idioma = idiomas[idx] if idx < len(idiomas) else "es"
    nombre_idioma = nombres_idiomas.get(idioma, idioma)
    
    print(f"📥 [{idx+1}/{len(wav_files)}] {nombre_idioma}")
    print(f"   Archivo: {wav_file.name}")
    
    try:
        resultado = modelo.transcribe(str(wav_file), language=idioma)
        texto = resultado["text"].strip()
        
        if texto:
            transcripciones[idioma] = texto
            print(f"   ✅ Transcrito: {len(texto)} caracteres")
            print(f"   📝 Primeros 120 chars: {texto[:120]}...")
        else:
            print(f"   ⚠️  Audio vacío")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Total transcripciones: {len(transcripciones)}\n")

if not transcripciones:
    print("❌ No se obtuvieron transcripciones")
    sys.exit(1)

# FASE 2: GUARDAR DOCUMENTO
print("📄 FASE 2: GUARDANDO TRANSCRIPCIONES COMPLETAS")
print("─" * 79)

doc_content = """
═══════════════════════════════════════════════════════════════════════════════
TRANSCRIPCIONES COMPLETAS - ANÁLISIS SEMÁNTICO
═══════════════════════════════════════════════════════════════════════════════

"""

for idioma_ord in ["es", "pt", "de", "en", "ja"]:
    if idioma_ord in transcripciones:
        texto = transcripciones[idioma_ord]
        nombre = nombres_idiomas.get(idioma_ord, idioma_ord)
        doc_content += f"\n{'='*79}\n"
        doc_content += f"🗣️  {nombre.upper()} ({idioma_ord})\n"
        doc_content += f"{'='*79}\n\n"
        doc_content += f"{texto}\n\n"

with open("TRANSCRIPCIONES_COMPLETAS.txt", 'w', encoding='utf-8') as f:
    f.write(doc_content)

print(f"✅ Documento guardado: TRANSCRIPCIONES_COMPLETAS.txt\n")

# FASE 3: ANÁLISIS SEMÁNTICO
print("🧠 FASE 3: ANÁLISIS SEMÁNTICO PROFUNDO")
print("─" * 79)

analisis = {}

for idioma, texto in transcripciones.items():
    nombre = nombres_idiomas.get(idioma, idioma)
    print(f"\n📍 {nombre}:")
    
    # Stopwords comunes
    stopwords = {
        "es": {"el", "la", "de", "que", "es", "y", "a", "en", "con", "los", "las", "por", "para", "del", "un", "una", "al", "o", "como"},
        "pt": {"o", "a", "de", "que", "é", "e", "em", "com", "para", "os", "as", "por", "dos", "das", "um", "uma", "ao", "ou"},
        "de": {"der", "die", "das", "und", "ist", "ein", "eine", "mit", "in", "zu", "von", "den", "des", "dem", "für", "oder"},
        "en": {"the", "and", "a", "to", "of", "is", "in", "it", "for", "with", "that", "on", "this", "be", "you", "or"},
        "ja": {"は", "を", "に", "が", "で", "も", "から", "まで", "ある", "いる"}
    }
    
    stop = stopwords.get(idioma, set())
    
    # Palabras significativas
    palabras = texto.split()
    palabras_sig = []
    for p in palabras:
        p_clean = p.lower().strip('.,!?;:"\'-—«»')
        if len(p_clean) > 2 and p_clean not in stop:
            palabras_sig.append(p_clean)
    
    # Frecuencias
    freq = Counter(palabras_sig)
    top_palabras = freq.most_common(20)
    
    print(f"   Palabras clave (top 10):")
    for palabra, count in top_palabras[:10]:
        print(f"      • {palabra} ({count}x)")
    
    # Frases significativas
    frases_simples = []
    for i in range(len(palabras) - 2):
        frase = " ".join(palabras[i:i+3]).lower().strip('.,!?;:"\'-—«»')
        if len(frase) > 5:
            frases_simples.append(frase)
    
    frase_freq = Counter(frases_simples)
    frases_unicas = [f for f, c in frase_freq.most_common(20) if c >= 1]
    
    print(f"   Frases principales:")
    for frase in frases_unicas[:5]:
        print(f"      • {frase}")
    
    analisis[idioma] = {
        "palabras_clave": top_palabras[:15],
        "frases_principales": frases_unicas[:5]
    }

# FASE 4: GENERAR CANDIDATOS
print("\n🔐 FASE 4: GENERANDO CANDIDATOS INTELIGENTES")
print("─" * 79)

candidatos = []

# Estrategia 1: Palabras clave significativas
for idioma, data in analisis.items():
    for palabra, count in data["palabras_clave"]:
        if len(palabra) > 2:
            candidatos.append(palabra)
            if count > 1:  # Si aparece >1 vez, es importante
                candidatos.append(palabra.capitalize())
                candidatos.append(palabra.upper())

# Estrategia 2: Primeras 2-3 palabras de cada frase
for idioma, data in analisis.items():
    for frase in data["frases_principales"]:
        partes = frase.split()[:2]
        if partes:
            candidatos.append("".join(partes))  # Sin espacios
            if len(partes) > 1:
                candidatos.append(partes[0])
                candidatos.append(partes[-1])

# Estrategia 3: Palabras especiales (potenciales pistas)
palabras_especiales = ["principio", "fin", "verdad", "vida", "muerte", "resiste", "camino", 
                       "beginning", "end", "truth", "life", "death", "resist", "path",
                       "começo", "fim", "verdade", "vida", "morte", "resista", "caminho",
                       "anfang", "ende", "wahrheit", "leben", "tod", "widerstand", "weg"]

for texto in transcripciones.values():
    text_lower = texto.lower()
    for palabra in palabras_especiales:
        if palabra in text_lower:
            candidatos.append(palabra)

# Eliminar duplicados
candidatos = list(dict.fromkeys(candidatos))

# Filtrar muy cortos o muy largos
candidatos = [c for c in candidatos if 2 < len(c) < 50]

print(f"✅ Total candidatos: {len(candidatos)}")
print(f"\n🎯 Primeros 40 candidatos:")
for i, c in enumerate(candidatos[:40], 1):
    print(f"   [{i:2d}] {c}")

# FASE 5: DESENCRIPTAR PDF
print("\n🔓 FASE 5: DESENCRIPTANDO PDF")
print("─" * 79)

pdf_path = "resiste-protected.pdf"

if not os.path.exists(pdf_path):
    print(f"❌ PDF no encontrado")
    sys.exit(1)

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("❌ PyPDF2 no instalado")
    sys.exit(1)

print(f"📄 {pdf_path} ({os.path.getsize(pdf_path)} bytes)\n")

encontrada = False

for idx, candidato in enumerate(candidatos, 1):
    try:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            if reader.decrypt(candidato):
                print(f"\n{'='*79}")
                print(f"✅✅✅ ¡¡¡CONTRASEÑA ENCONTRADA!!!")
                print(f"{'='*79}")
                print(f"🔑 Contraseña: '{candidato}'")
                print(f"📊 Intento: #{idx}/{len(candidatos)}")
                print(f"{'='*79}\n")
                
                encontrada = True
                
                # Guardar resultado
                resultado_json = {
                    "contraseña": candidato,
                    "intento_numero": idx,
                    "total_candidatos": len(candidatos),
                    "estrategia": "análisis semántico profundo",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("contraseña_encontrada.json", 'w', encoding='utf-8') as f:
                    json.dump(resultado_json, f, ensure_ascii=False, indent=2)
                
                # Extraer contenido
                print("📄 Extrayendo contenido...\n")
                try:
                    contenido = ""
                    for page_idx, page in enumerate(reader.pages):
                        texto_pag = page.extract_text()
                        if texto_pag:
                            contenido += f"[PÁGINA {page_idx + 1}]\n{texto_pag}\n\n"
                    
                    with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                        f.write(contenido)
                    
                    print(f"✅ Contenido guardado: contenido_desencriptado.txt\n")
                    print(f"{'─'*79}")
                    print("📋 CONTENIDO:")
                    print(f"{'─'*79}\n")
                    print(contenido)
                    print(f"\n{'─'*79}")
                except Exception as e:
                    print(f"⚠️  Error extrayendo: {e}")
                
                break
    except:
        pass
    
    if idx % 50 == 0:
        print(f"Progreso: [{idx}/{len(candidatos)}]", end="\r")

if not encontrada:
    print(f"\n\n❌ NO SE ENCONTRÓ LA CONTRASEÑA")
    print(f"Probados: {len(candidatos)} candidatos")
    
    with open("candidatos_probados.json", 'w', encoding='utf-8') as f:
        json.dump(candidatos, f, ensure_ascii=False, indent=2)
    print(f"Guardados en: candidatos_probados.json")

print("\n" + "═" * 79)
print("✨ WORKFLOW COMPLETADO")
print("═" * 79 + "\n")
