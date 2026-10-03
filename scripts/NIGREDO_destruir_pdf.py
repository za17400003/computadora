#!/usr/bin/env python3
"""
NIGREDO (שבירת הכלים): Destrucción - Analizar PDF a nivel bytes
Extrae: structure, metadata, posibles debilidades, datos ocultos
"""

import os
import struct
import re

print("\n" + "="*80)
print("NIGREDO: FASE DE DESTRUCCIÓN".center(80))
print("="*80 + "\n")

pdf_file = 'resiste-protected.pdf'
if not os.path.exists(pdf_file):
    print(f"[-] Archivo no encontrado: {pdf_file}")
    exit(1)

file_size = os.path.getsize(pdf_file)
print(f"[1] INFO BÁSICA")
print(f"    Tamaño: {file_size} bytes ({file_size/1024/1024:.2f} MB)")

# Leer header
with open(pdf_file, 'rb') as f:
    header = f.read(100)
    print(f"    Header: {header[:50]}")
    print(f"    Version: {header[:8].decode('latin1', errors='ignore')}")

# ESTRATEGIA 1: Buscar strings en claro en el PDF
print(f"\n[2] BÚSQUEDA DE STRINGS LEGIBLES")
with open(pdf_file, 'rb') as f:
    content = f.read()
    
# Extraer strings ASCII legibles
strings = re.findall(b'[\x20-\x7E]{4,}', content)
print(f"    Strings encontrados: {len(strings)}")
print(f"    Primeros 20:")
for s in strings[:20]:
    try:
        decoded = s.decode('utf-8', errors='ignore')
        print(f"      - {decoded}")
    except:
        pass

# ESTRATEGIA 2: Buscar diccionario (para identificar si es weak encryption)
print(f"\n[3] ANÁLISIS DE ENCRIPTACIÓN")
with open(pdf_file, 'rb') as f:
    f.seek(0)
    content = f.read()
    
# Buscar "/Encrypt" para ver nivel de encriptación
if b'/Encrypt' in content:
    print(f"    [✓] Encriptación detectada")
    enc_pos = content.find(b'/Encrypt')
    print(f"    Contexto: {content[enc_pos:enc_pos+200]}")
    
# Buscar "/Filter" (tipo de encriptación)
if b'/Filter /Standard' in content:
    print(f"    [✓] Tipo: Standard PDF encryption")
if b'/Filter /Identity' in content:
    print(f"    [✓] Tipo: Identity encryption")
    
# ESTRATEGIA 3: Buscar longitud de clave
print(f"\n[4] PARÁMETROS DE ENCRIPTACIÓN")
if b'/Length' in content:
    lengths = re.findall(b'/Length (\d+)', content)
    print(f"    Longitudes encontradas: {lengths[:10]}")

# ESTRATEGIA 4: Buscar versión de PDF y estándar de encriptación
with open(pdf_file, 'rb') as f:
    f.seek(0)
    content = f.read(500)
    
version_match = re.search(b'%PDF-(\d\.\d)', content)
if version_match:
    print(f"\n[5] VERSIÓN PDF: {version_match.group(1).decode()}")

# ESTRATEGIA 5: Buscar trailer y xref
print(f"\n[6] ESTRUCTURA DEL PDF")
xref_pos = content.rfind(b'xref')
trailer_pos = content.rfind(b'trailer')
print(f"    xref en posición: {xref_pos}")
print(f"    trailer en posición: {trailer_pos}")

# ESTRATEGIA 6: Intentar extraer Owner Password (a veces distinto de User Password)
print(f"\n[7] BÚSQUEDA DE PASSWORDS EN CLARO (raro pero posible)")
with open(pdf_file, 'rb') as f:
    content = f.read()
    
# Buscar patrones comunes de contraseñas
patterns = [
    b'Pass', b'pass', b'Pass', b'O<<', b'/O(', b'/U(',
    b'verdad', b'vuelve', b'vida', b'video', b'potencial'
]

found_patterns = {}
for pattern in patterns:
    if pattern in content:
        pos = content.find(pattern)
        context = content[pos:pos+100]
        found_patterns[pattern.decode('latin1', errors='ignore')] = context[:50].hex()

if found_patterns:
    print(f"    Patrones encontrados:")
    for pattern, ctx in found_patterns.items():
        print(f"      {pattern}: {ctx}")

# ESTRATEGIA 7: Calcular entropía (si está desencriptado vs encriptado)
print(f"\n[8] ANÁLISIS DE ENTROPÍA")
from collections import Counter

sample = content[:10000]
byte_freq = Counter(sample)
entropy = 0
for count in byte_freq.values():
    p = count / len(sample)
    entropy -= p * (p.bit_length() - 1) if p > 0 else 0

print(f"    Entropía del PDF: {entropy:.2f} (alto=encriptado, bajo=claro)")

# ESTRATEGIA 8: Buscar Owner/User Password salt
print(f"\n[9] BÚSQUEDA DE SALT/VECTORS")
salt_patterns = re.findall(b'/O\(.*?\)', content)
print(f"    /O patterns (Owner Password): {len(salt_patterns)}")
for i, salt in enumerate(salt_patterns[:3]):
    print(f"      [{i+1}] {salt[:50]}...")

user_patterns = re.findall(b'/U\(.*?\)', content)
print(f"    /U patterns (User Password): {len(user_patterns)}")
for i, user in enumerate(user_patterns[:3]):
    print(f"      [{i+1}] {user[:50]}...")

print("\n" + "="*80)
print("NIGREDO COMPLETADO".center(80))
print("="*80)
