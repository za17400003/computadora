#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS SEMÁNTICO PROFUNDO - TODO EN ESPAÑOL
Transcriba 5 audios (todos español), analice semánticamente, genere candidatos inteligentes
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
🔍 ANÁLISIS SEMÁNTICO PROFUNDO - TODO ES PISTA (ESPAÑOL)
═══════════════════════════════════════════════════════════════════════════════

FASES:
  1️⃣  Transcribir 5 audios como ESPAÑOL
  2️⃣  Guardar transcripciones completas (documento legible)
  3️⃣  Análisis semántico profundo (palabras, frases, conceptos)
  4️⃣  Generar candidatos inteligentes de contraseña
  5️⃣  Desencriptar PDF
  6️⃣  REPORTAR RESULTADO

═══════════════════════════════════════════════════════════════════════════════
""")

try:
    import whisper
except ImportError:
    print("❌ Whisper no disponible")
    sys.exit(1)

# FASE 1: TRANSCRIBIR TODO COMO ESPAÑOL
print("🎙️  FASE 1: TRANSCRIBIENDO AUDIOS (TODO COMO ESPAÑOL)")
print("─" * 79)

wav_files = sorted(list(Path(".").glob("WhatsApp Ptt *.wav")))

if not wav_files:
    print("❌ No hay archivos WAV")
    sys.exit(1)

transcripciones = {}

# Cargar modelo
print("📦 Cargando modelo Whisper base...")
modelo = whisper.load_model("base")
print("✅ Modelo cargado\n")

for idx, wav_file in enumerate(wav_files, 1):
    print(f"📥 [{idx}/{len(wav_files)}] {wav_file.name}")
    
    try:
        resultado = modelo.transcribe(str(wav_file), language="es")
        texto = resultado["text"].strip()
        
        if texto:
            # Guardar por índice (1-5)
            transcripciones[f"audio_{idx}"] = texto
            print(f"   ✅ {len(texto)} caracteres")
            print(f"   📝 {texto[:100]}...")
        else:
            print(f"   ⚠️  Audio vacío")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print(f"\n✅ Total transcripciones: {len(transcripciones)}\n")

if not transcripciones:
    print("❌ No se obtuvieron transcripciones")
    sys.exit(1)

# FASE 2: GUARDAR DOCUMENTO LEGIBLE
print("📄 FASE 2: GUARDANDO TRANSCRIPCIONES COMPLETAS")
print("─" * 79)

doc_content = """
═══════════════════════════════════════════════════════════════════════════════
TRANSCRIPCIONES COMPLETAS - ANÁLISIS SEMÁNTICO
═══════════════════════════════════════════════════════════════════════════════

[NOTA]: Todos los audios están en ESPAÑOL. Se transcribieron para análisis.

"""

for i in range(1, 6):
    key = f"audio_{i}"
    if key in transcripciones:
        texto = transcripciones[key]
        doc_content += f"\n{'='*79}\n"
        doc_content += f"🎙️  AUDIO #{i}\n"
        doc_content += f"{'='*79}\n\n"
        doc_content += f"{texto}\n\n"

with open("TRANSCRIPCIONES_COMPLETAS.txt", 'w', encoding='utf-8') as f:
    f.write(doc_content)

print(f"✅ Documento guardado: TRANSCRIPCIONES_COMPLETAS.txt\n")

# FASE 3: ANÁLISIS SEMÁNTICO
print("🧠 FASE 3: ANÁLISIS SEMÁNTICO PROFUNDO")
print("─" * 79)

# Combinar todos los textos
texto_completo = " ".join(transcripciones.values())

# Stopwords español
stopwords = {
    "el", "la", "de", "que", "es", "y", "a", "en", "con", "los", "las", 
    "por", "para", "del", "un", "una", "al", "o", "como", "más", "pero",
    "este", "ese", "aquí", "ahí", "allá", "son", "está", "están", "se",
    "me", "te", "le", "nos", "os", "les", "mi", "tu", "su", "nuestro",
    "vuestro", "mío", "tuyo", "suyo", "he", "has", "ha", "hemos", "habéis",
    "han", "haya", "hayas", "haya", "hayamos", "hayáis", "hayan"
}

# Palabras significativas (>3 letras, no stopwords)
palabras = texto_completo.split()
palabras_sig = []
for p in palabras:
    p_clean = p.lower().strip('.,!?;:"\'-—«»()[]{}')
    if len(p_clean) > 2 and p_clean not in stopwords:
        palabras_sig.append(p_clean)

# TOP palabras
freq = Counter(palabras_sig)
top_palabras = freq.most_common(30)

print("📊 PALABRAS CLAVE (más frecuentes):")
for palabra, count in top_palabras[:15]:
    print(f"   [{count:2d}x] {palabra}")

# Frases de 2-4 palabras
print("\n📝 FRASES CLAVE (segmentos de 2-4 palabras):")
frases = []
for i in range(len(palabras) - 3):
    frase = " ".join(palabras[i:i+4]).lower().strip('.,!?;:"\'-—«»()[]{}')
    if len(frase) > 8 and not any(sw in frase for sw in stopwords):
        frases.append(frase)

frase_freq = Counter(frases)
top_frases = [f for f, c in frase_freq.most_common(30) if c >= 1]

for frase in top_frases[:10]:
    print(f"   • {frase}")

# Conceptos temáticos (palabras específicas que podrían ser pista)
print("\n🎯 CONCEPTOS TEMÁTICOS ENCONTRADOS:")
conceptos_buscar = [
    "verdad", "vida", "muerte", "fin", "principio", "comienzo", "comienza",
    "resiste", "resistencia", "despertar", "despierta", "conciencia", "consciencia",
    "libertad", "libre", "camino", "viaje", "luz", "oscuridad", "sombra",
    "espejo", "realidad", "ilusión", "sueño", "soñar", "despertar",
    "conocimiento", "saber", "secreto", "verdadero", "falso", "engaño",
    "tiempo", "momento", "ahora", "siempre", "nunca", "eterno", "infinito",
    "poder", "fuerza", "débil", "fuerte", "vencer", "vencido", "victoria",
    "nombre", "identidad", "ser", "existencia", "nada", "todo", "uno"
]

conceptos_encontrados = {}
for concepto in conceptos_buscar:
    if concepto in texto_completo.lower():
        # Contar apariciones
        count = texto_completo.lower().count(concepto)
        conceptos_encontrados[concepto] = count

# Ordenar por frecuencia
conceptos_ord = sorted(conceptos_encontrados.items(), key=lambda x: x[1], reverse=True)

for concepto, count in conceptos_ord[:15]:
    print(f"   [{count:2d}x] {concepto}")

# FASE 4: GENERAR CANDIDATOS INTELIGENTES
print("\n🔐 FASE 4: GENERANDO CANDIDATOS DE CONTRASEÑA")
print("─" * 79)

candidatos = set()

# Estrategia 1: Palabras clave (top)
print("   [→] Palabras clave...")
for palabra, count in top_palabras[:20]:
    if len(palabra) > 2:
        candidatos.add(palabra)
        if count > 1:  # Si aparece varias veces
            candidatos.add(palabra.capitalize())
            candidatos.add(palabra.upper())

# Estrategia 2: Conceptos encontrados
print("   [→] Conceptos temáticos...")
for concepto in conceptos_ord[:20]:
    candidatos.add(concepto[0])
    candidatos.add(concepto[0].capitalize())

# Estrategia 3: Primeras palabras de frases clave
print("   [→] Frases clave (segmentos)...")
for frase in top_frases[:15]:
    partes = frase.split()
    if partes:
        # Primer palabra
        candidatos.add(partes[0])
        # Primeras 2 palabras sin espacio
        if len(partes) > 1:
            candidatos.add(partes[0] + partes[1])
            # Última palabra
            candidatos.add(partes[-1])

# Estrategia 4: Palabras que empiezan con V (pista original)
print("   [→] Palabras que empiezan con V...")
for palabra in palabras_sig:
    if palabra.startswith('v') and len(palabra) > 2:
        candidatos.add(palabra)
        candidatos.add(palabra.capitalize())

# Estrategia 5: Combinaciones de palabras clave
print("   [→] Combinaciones de palabras clave...")
top_5_palabras = [p[0] for p in top_palabras[:5]]
for i, p1 in enumerate(top_5_palabras):
    for p2 in top_5_palabras[i+1:]:
        candidatos.add(p1 + p2)
        candidatos.add(p1 + " " + p2)

# Filtrar: eliminar muy cortos/largos
candidatos = [c for c in candidatos if 2 < len(c) < 60]
candidatos = sorted(list(set(candidatos)))

print(f"\n✅ Total candidatos: {len(candidatos)}")
print(f"\n🎯 PRIMEROS 50 CANDIDATOS:")
for i, c in enumerate(candidatos[:50], 1):
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
total = len(candidatos)

for idx, candidato in enumerate(candidatos, 1):
    try:
        reader = PdfReader(pdf_path)
        
        if reader.is_encrypted:
            if reader.decrypt(candidato):
                print(f"\n{'='*79}")
                print(f"✅✅✅ ¡¡¡CONTRASEÑA ENCONTRADA!!!")
                print(f"{'='*79}")
                print(f"🔑 CONTRASEÑA: '{candidato}'")
                print(f"📊 INTENTO: #{idx}/{total}")
                print(f"{'='*79}\n")
                
                encontrada = True
                
                # Guardar resultado
                resultado_json = {
                    "contraseña": candidato,
                    "intento_numero": idx,
                    "total_candidatos": total,
                    "estrategia": "análisis semántico profundo",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                with open("contraseña_encontrada.json", 'w', encoding='utf-8') as f:
                    json.dump(resultado_json, f, ensure_ascii=False, indent=2)
                
                # Extraer contenido
                print("📄 EXTRAYENDO CONTENIDO...\n")
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
                    print("📋 CONTENIDO COMPLETO:")
                    print(f"{'─'*79}\n")
                    print(contenido)
                    print(f"\n{'─'*79}")
                except Exception as e:
                    print(f"⚠️  Error extrayendo: {e}")
                
                break
    except:
        pass
    
    if idx % 100 == 0 or idx == total:
        print(f"Progreso: [{idx}/{total}]", end="\r")

if not encontrada:
    print(f"\n\n❌ NO SE ENCONTRÓ LA CONTRASEÑA")
    print(f"Probados: {total} candidatos inteligentes")
    
    with open("candidatos_probados.json", 'w', encoding='utf-8') as f:
        json.dump(candidatos, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Candidatos guardados en: candidatos_probados.json")

print("\n" + "═" * 79)
print("✨ WORKFLOW COMPLETADO")
print("═" * 79 + "\n")
