#!/usr/bin/env python3
"""Complete project structure analysis."""
import os
import json
from pathlib import Path
from collections import defaultdict

root = Path(".")

# 1. Carpetas en raíz y su contenido
print("\n=== CARPETAS EN RAÍZ ===\n")
folders = {}
for item in sorted(root.iterdir()):
    if item.is_dir() and not item.name.startswith('.'):
        try:
            file_count = len(list(item.rglob("*")))
            folders[item.name] = file_count
            print(f"📁 {item.name:30} ({file_count} items)")
        except:
            pass

# 2. Archivos en raíz
print("\n=== ARCHIVOS EN RAÍZ ===\n")
root_files = {}
for item in sorted(root.iterdir()):
    if item.is_file() and item.suffix in ['.md', '.bat', '.txt', '.json', '.py']:
        root_files[item.name] = item.stat().st_size
        size_kb = root_files[item.name] / 1024
        print(f"📄 {item.name:40} ({size_kb:.1f} KB)")

# 3. Buscar duplicados de archivos clave
print("\n=== DUPLICADOS (Archivos clave) ===\n")
name_map = defaultdict(list)
for item in root.rglob("*"):
    if item.is_file() and item.name in ['WorkItems.md', 'INDEX.md', 'WORKFLOW_OPERACIONAL.md', 'SRS.md', 'SDD.md']:
        rel_path = item.relative_to(root)
        name_map[item.name].append(str(rel_path))

for fname, paths in sorted(name_map.items()):
    if len(paths) > 1:
        print(f"🔄 {fname} ({len(paths)} copias):")
        for p in paths:
            print(f"   - {p}")
    else:
        print(f"✓ {fname}: {paths[0]}")

# 4. Carpetas que podrían ser duplicadas o innecesarias
print("\n=== CARPETAS POTENCIALMENTE INNECESARIAS ===\n")
duplicate_patterns = ['_archive', '_backup', '_old', 'backup', 'archive', 'test_', '.git']
for folder in root.iterdir():
    if folder.is_dir():
        if any(pattern in folder.name.lower() for pattern in duplicate_patterns):
            item_count = len(list(folder.rglob("*")))
            print(f"⚠️  {folder.name}/ ({item_count} items) - CANDIDATE FOR DELETION")

print("\n✅ Análisis completado\n")
