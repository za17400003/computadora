#!/usr/bin/env python3
"""Leer últimos logs y buscar escaneo facial"""
from pathlib import Path
import sys

log_dir = Path("logs")
if not log_dir.exists():
    print("❌ No hay directorio logs/")
    sys.exit(1)

log_file = max(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, default=None)
if not log_file:
    print("❌ No hay archivos .log")
    sys.exit(1)

print(f"📋 Leyendo: {log_file.name}")
print("=" * 70)

content = log_file.read_text(encoding="utf-8", errors="ignore")
lines = content.split("\n")

# Buscar líneas relevantes
keywords = ["escaneo", "propietario", "reconocido", "facial", "WI-253", "WI-264"]
relevant_lines = [
    line for line in lines 
    if any(kw.lower() in line.lower() for kw in keywords)
]

if relevant_lines:
    print(f"✓ Encontradas {len(relevant_lines)} líneas relevantes:")
    for line in relevant_lines[-20:]:  # Últimas 20
        print(line)
else:
    print("⚠️  No se encontraron líneas de escaneo/reconocimiento")
    
print("\n" + "=" * 70)
print("ÚLTIMAS 10 LÍNEAS DEL LOG:")
for line in lines[-10:]:
    if line.strip():
        print(line)
