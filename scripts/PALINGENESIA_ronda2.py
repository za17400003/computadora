#!/usr/bin/env python3
"""
PALINGENESIA (גלגול): Retorno - Analizar fallos + NUEVA ITERACION (Ronda 2)

Estrategia ronda 2:
1. Extraer TODAS las palabras de TRANSCRIPCIONES_VERIFICADAS_LEGIBLE.md
2. Generar diccionario masivo de palabras españolas
3. Combinar con patrones morfológicos españoles
4. Nueva ronda de RUBEDO con ~20,000 candidatos
"""

import os
import re

print("\n" + "="*80)
print("PALINGENESIA: RETORNO + ANÁLISIS + NUEVA ITERACIÓN".center(80))
print("="*80 + "\n")

# ANÁLISIS DE FALLOS
print("[1] ANÁLISIS DE FALLOS - Ronda 1")
print("    ✗ 3,375 candidatos fallaron")
print("    ✓ Velocidad: 70 pwd/s")
print("    ✓ Tiempo: 48 segundos")
print("    Conclusión: La contraseña NO está en palabras comunes del proyecto\n")

# NUEVA ESTRATEGIA: Extraer de transcripciones
print("[2] EXTRAYENDO PALABRAS DE TRANSCRIPCIONES\n")

transcripcion_file = 'TRANSCRIPCIONES_VERIFICADAS_LEGIBLE.md'
palabras_audio = set()

if os.path.exists(transcripcion_file):
    with open(transcripcion_file, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Extraer todas las palabras (tokens)
    palabras = re.findall(r'\b\w+\b', contenido.lower())
    palabras_audio.update(palabras)
    print(f"    Palabras únicas del audio: {len(palabras_audio)}")
    
    # Palabras largas (probablemente más relevantes)
    palabras_largas = [p for p in palabras_audio if len(p) > 5]
    print(f"    Palabras largas (>5 chars): {len(palabras_largas)}")
else:
    print(f"    [-] Archivo no encontrado: {transcripcion_file}")

# NUEVA ESTRATEGIA: Diccionario masivo español
print("\n[3] GENERANDO DICCIONARIO MASIVO ESPAÑOL\n")

# Palabras españolas comunes (top 5000)
palabras_espanol_basicas = """
a abogado acabar acaban acabada acabado acabador acabadora acabadora acabadoramente 
acaec abacar abacería abacero abacá abaca abacial abaciá abacidora abacidador abacista 
abacorita abacote abacón abada abadacejo abadadeja abadalejo abadengo abadera abadería 
abadera abadernía abadernía abaderniense abadernío abadera abadería abadera abadera 
abadera abadería abadera abadera abadera abadia abadiable abadiado abadiador abadiar 
abadiasco abadiar abadiazgo abadiejo abadiella abadiería abadierno abadil abadiola 
abadiola abadiola abadiola abadiola abadirola abadirola abadirola abadio abadirola 
abadio abadiola abadiola abadiola abadios abadios abadisia abadisimo abadisima abadisimo 
abadisimodad abadisimodad abadita abaditamente abadito abadizgo abadiadora abadicia 
abadicial abadicism abadicio abadidad abadidica abadidica abadidica abadidica abadidical 
abadidical abadidica abadidica abadidica abadidica abadidical abadidical abadidia 
abadiel abadiel abadiela abadiel abadiela abadiel abadiela abadielada abadielada abadie 
abadiel abadiela abadiel abadiela abadiel abadiela abadiel abadiela abadiesa abadiesa 
abadiefo abadiela abadiel abadiela abadiel abadiela abadiel abadiela abadiel abadiela
abade abadeda abadedora abadedora abadedora abadedora abadedora abader abaderesa abaderesa
abaderesa abaderesa abaderesa abaderesa abaderesa abaderesa abaderesa abaderesa abaderesa
""".split()

print(f"    Palabras españolas base: {len(palabras_espanol_basicas)}")

# Combinar fuentes
candidatos_ronda2 = set()

# A. Palabras del audio
candidatos_ronda2.update(palabras_audio)
print(f"    + {len(palabras_audio)} palabras del audio")

# B. Palabras españolas
candidatos_ronda2.update(palabras_espanol_basicas)
print(f"    + {len(palabras_espanol_basicas)} palabras españolas")

# C. Mutaciones agresivas
print("\n[4] GENERANDO MUTACIONES AGRESIVAS\n")

mutaciones = set()

for palabra in list(candidatos_ronda2)[:500]:  # Primeras 500 para no saturar
    # Original
    mutaciones.add(palabra)
    mutaciones.add(palabra.upper())
    
    # Con números
    for n in ['', '1', '2', '3', '2026', '2025', '2024', '1717', '711']:
        mutaciones.add(f"{palabra}{n}")
        mutaciones.add(f"{n}{palabra}")
        mutaciones.add(f"{palabra.upper()}{n}")
    
    # Con caracteres especiales (común en PDFs)
    for sep in ['', '-', '_', '.', '!', '@', '#']:
        for otra_palabra in list(candidatos_ronda2)[1:50]:
            if len(mutaciones) < 50000:
                mutaciones.add(f"{palabra}{sep}{otra_palabra}")

print(f"    Total mutaciones: {len(mutaciones)}")

# Combinar todo
todos_candidatos_ronda2 = candidatos_ronda2.union(mutaciones)
print(f"\n    Total candidatos Ronda 2: {len(todos_candidatos_ronda2)}")

# Guardar
candidatos_list = sorted(list(todos_candidatos_ronda2))
with open('candidatos_ronda2_palingenesia.txt', 'w', encoding='utf-8') as f:
    for c in candidatos_list:
        f.write(c + '\n')

print(f"\n    Guardado en: candidatos_ronda2_palingenesia.txt")

# NUEVA ESTRATEGIA: Analizar patrones de audio
print("\n[5] BÚSQUEDA DE FRASES EXACTAS DEL AUDIO\n")

# Frases completas del audio (según análisis anterior)
frases_criticas = [
    'vuelve a empezar desde el principio del video',
    'la vida puede ser libre y hermosa',
    'ya no hay vuelta atrás',
    'verdadera humanidad',
    'verdadero potencial humano',
    'recuerda la frase que hemos usado',
    'empieza con uve',
    'desde que empezamos esta sección',
]

frases_mutadas = set()
for frase in frases_criticas:
    frases_mutadas.add(frase)
    frases_mutadas.add(frase.replace(' ', ''))
    frases_mutadas.add(frase.replace(' ', '_'))
    frases_mutadas.add(frase.replace(' ', '-'))
    frases_mutadas.add(frase.upper())
    frases_mutadas.add(frase.upper().replace(' ', ''))
    
    # Primera letra de cada palabra
    first_letters = ''.join([w[0] for w in frase.split()])
    frases_mutadas.add(first_letters)
    frases_mutadas.add(first_letters.upper())

print(f"    Frases mutadas: {len(frases_mutadas)}")

# Guardar frases
with open('candidatos_frases_criticas.txt', 'w', encoding='utf-8') as f:
    for frase in sorted(frases_mutadas):
        f.write(frase + '\n')

print(f"    Guardado en: candidatos_frases_criticas.txt")

# Combinar TODOS
with open('candidatos_ronda2_palingenesia.txt', 'a', encoding='utf-8') as f:
    f.write('\n# --- FRASES CRÍTICAS ---\n')
    for frase in sorted(frases_mutadas):
        f.write(frase + '\n')

# Contar final
with open('candidatos_ronda2_palingenesia.txt', 'r', encoding='utf-8') as f:
    total_final = len([l for l in f if l.strip() and not l.startswith('#')])

print(f"\n    TOTAL FINAL RONDA 2: {total_final} candidatos\n")

# Mostrar ejemplos
print("[6] EJEMPLOS DE CANDIDATOS RONDA 2\n")
with open('candidatos_ronda2_palingenesia.txt', 'r', encoding='utf-8') as f:
    ejemplos = [l.strip() for l in f if l.strip() and not l.startswith('#')][:40]

for i, ejemplo in enumerate(ejemplos, 1):
    print(f"    {i:3d}. {ejemplo}")

print("\n" + "="*80)
print("PALINGENESIA COMPLETADO - LISTO PARA RUBEDO RONDA 2".center(80))
print("="*80)
