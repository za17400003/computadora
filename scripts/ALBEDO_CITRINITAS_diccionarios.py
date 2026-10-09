#!/usr/bin/env python3
"""
ALBEDO (טהרה): Purificación - Verificar viabilidad de ataques
CITRINITAS (אור חדש): Iluminación - Generar diccionarios masivos LOCALES

Estrategias de MENOR a MAYOR viabilidad según dificultad de la encriptación AES-256:
1. ✓ Diccionario de palabras españolas comunes
2. ✓ Palabras del proyecto + mutaciones
3. ✓ Patrones numéricos + fechas
4. ✓ Combinaciones de palabras del audio
5. ✓ Fuerza bruta restringida (seeds + expansión)
"""

import os
import itertools
import time

print("\n" + "="*80)
print("ALBEDO + CITRINITAS: PURIFICACIÓN + ILUMINACIÓN".center(80))
print("="*80 + "\n")

# DICCIONARIOS LOCALES
print("[1] GENERANDO DICCIONARIOS LOCALES\n")

# A. Palabras clave del proyecto
proyecto_palabras = [
    'resiste', 'verdad', 'verdadero', 'verdadera', 'vida', 'video',
    'vuelve', 'empezar', 'potencial', 'humanidad', 'libertad', 'libre',
    'chaplin', 'chaperon', 'computadora', 'computadora', 'escucha', 'emet',
    'ouroboros', 'alquimia', 'gilgul', 'bereshit', 'palingenesia',
    'nigredo', 'albedo', 'citrinitas', 'rubedo', 'sefirot', 'árbol',
    'amen', 'por favor', 'gracias', 'prosigue', 'continúa', 'obra',
    'punto fijo', 'fijo', 'punto', 'aprobacion', 'aprobación', 'circulo',
    'ciclo', 'fase', 'etapa', 'nivel', 'mundo', 'ser', 'ente',
]

# B. Palabras españolas comunes
palabras_comunes = [
    'password', 'pass', 'secret', 'secreto', 'codigo', 'código',
    'acceso', 'entrada', 'clave', 'documento', 'archivo', 'pdf',
    'contenido', 'verdades', 'manifestacion', 'manifestación', 'realidad',
    'poder', 'control', 'dominio', 'resistencia', 'rebeldía', 'revelación',
]

# C. Números significativos
numeros = [
    '2026', '2025', '2024', '2023', '2022', '2021',
    '1717', '1718', '711', '912', '123', '321',
    '1111', '0000', '7777', '1234', '4321',
]

# D. Palabras del audio (críticas)
audio_palabras = [
    'vuelveaempezar', 'vuelve a empezar',
    'yaноhayvueltaatras', 'ya no hay vuelta atrás',
    'vidapuedeserlibreyheromosa', 'la vida puede ser libre y hermosa',
    'verdaderahumanidad', 'verdadera humanidad',
    'verdaderopot encial', 'verdadero potencial humano',
    'humanidadverdadera', 'potencialhumano', 'potencial humano',
]

# Generar candidatos
candidatos = []

print("[A] Palabras proyecto")
candidatos.extend(proyecto_palabras)
print(f"    + {len(proyecto_palabras)} palabras del proyecto")

print("[B] Palabras comunes español/inglés")
candidatos.extend(palabras_comunes)
print(f"    + {len(palabras_comunes)} palabras comunes")

print("[C] Números significativos")
candidatos.extend(numeros)
print(f"    + {len(numeros)} números")

print("[D] Palabras del audio (críticas)")
candidatos.extend(audio_palabras)
print(f"    + {len(audio_palabras)} palabras del audio")

print(f"\n    Total base: {len(candidatos)} candidatos")

# MUTACIONES (CLAVE)
print("\n[2] MUTACIONES DE CANDIDATOS\n")

mutaciones = []

def mutar(palabra):
    """Genera mutaciones de una palabra"""
    mutadas = set()
    
    # Original
    mutadas.add(palabra)
    
    # Mayúsculas
    mutadas.add(palabra.upper())
    mutadas.add(palabra.lower())
    mutadas.add(palabra.capitalize())
    
    # Sin espacios
    sin_espacios = palabra.replace(' ', '')
    mutadas.add(sin_espacios)
    mutadas.add(sin_espacios.upper())
    
    # Con guiones
    con_guion = palabra.replace(' ', '-')
    mutadas.add(con_guion)
    mutadas.add(con_guion.upper())
    
    # Con underscore
    con_underscore = palabra.replace(' ', '_')
    mutadas.add(con_underscore)
    mutadas.add(con_underscore.upper())
    
    # Con números al final
    for n in ['2026', '2025', '1717', '711', '123']:
        mutadas.add(f"{palabra}{n}")
        mutadas.add(f"{palabra.upper()}{n}")
    
    # Con prefijos/sufijos comunes
    prefijos = ['el', 'la', 'los', 'del', 'un', 'una']
    for prefijo in prefijos:
        mutadas.add(f"{prefijo}{palabra}")
        mutadas.add(f"{prefijo}_{palabra}")
        mutadas.add(f"{prefijo}-{palabra}")
    
    return mutadas

print("Mutando candidatos...")
todas_mutaciones = set()
for palabra in candidatos:
    todas_mutaciones.update(mutar(palabra))

print(f"    Total con mutaciones: {len(todas_mutaciones)} candidatos")

# COMBINACIONES CRÍTICAS
print("\n[3] COMBINACIONES CRÍTICAS\n")

# Combinar palabras clave del audio
palabras_criticas = [
    'vuelve', 'empezar', 'vida', 'libre', 'hermosa',
    'ya', 'no', 'hay', 'vuelta', 'atrás',
    'verdadera', 'humanidad', 'verdadero', 'potencial'
]

combinaciones = set()
print("Generando combinaciones de 2 palabras...")

for p1, p2 in itertools.combinations(palabras_criticas[:10], 2):
    combinaciones.add(f"{p1}{p2}")
    combinaciones.add(f"{p1} {p2}")
    combinaciones.add(f"{p1}-{p2}")
    combinaciones.add(f"{p1}_{p2}")
    combinaciones.add(f"{p1.upper()}{p2.upper()}")
    combinaciones.add(f"{p2}{p1}")
    combinaciones.add(f"{p2} {p1}")

print(f"    + {len(combinaciones)} combinaciones de 2 palabras")

# LISTA FINAL
todas_palabras = todas_mutaciones.union(combinaciones)
print(f"\n[4] LISTA FINAL DE CANDIDATOS")
print(f"    Total: {len(todas_palabras)} candidatos")

# Guardar en archivo
candidatos_list = sorted(list(todas_palabras))
with open('candidatos_albedo_citrinitas.txt', 'w', encoding='utf-8') as f:
    for candidato in candidatos_list:
        f.write(candidato + '\n')

print(f"    Guardado en: candidatos_albedo_citrinitas.txt")

# ESTADÍSTICAS
print(f"\n[5] ESTADÍSTICAS")
print(f"    Longitud mín: {min(len(c) for c in candidatos_list)}")
print(f"    Longitud máx: {max(len(c) for c in candidatos_list)}")
print(f"    Promedio: {sum(len(c) for c in candidatos_list) / len(candidatos_list):.1f}")

# Mostrar ejemplos
print(f"\n    Ejemplos de candidatos:")
for ejemplo in sorted(candidatos_list)[:30]:
    print(f"      - {ejemplo}")

print("\n" + "="*80)
print("ALBEDO + CITRINITAS COMPLETADO".center(80))
print("="*80)
