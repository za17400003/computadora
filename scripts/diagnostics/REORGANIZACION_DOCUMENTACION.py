#!/usr/bin/env python3
"""
FP-044C: Reorganizar documentación de raíz a carpetas correctas.

Usa FILE_LOCATION_MANAGER para PRE-determinar ubicación de cada .md.
Archivos en blancalist se quedan en raíz.
"""

import shutil
from pathlib import Path
import sys

# Importar FILE_LOCATION_MANAGER
sys.path.insert(0, str(Path(__file__).parent.parent))
from FILE_LOCATION_MANAGER import FileLocationManager

def reorganizar_documentacion():
    """Reorganizar .md de raíz a ubicaciones correctas."""
    raiz = Path(__file__).resolve().parent.parent.parent  # c:\...\proyecto-golem
    
    # Archivos que DEBEN estar en raíz
    whitelist = FileLocationManager.WHITELIST_RAIZ
    
    # Encontrar todos los .md en raíz
    archivos_md = list(raiz.glob("*.md"))
    
    reorganizados = []
    no_reorganizados = []
    
    for archivo in archivos_md:
        nombre = archivo.name
        
        if nombre in whitelist:
            print(f"  ✓ {nombre} — WHITELIST (se queda en raíz)")
            no_reorganizados.append(nombre)
            continue
        
        # Determinar destino
        destino_dir = FileLocationManager.get_location(nombre)
        if destino_dir == '.':
            print(f"  ✓ {nombre} — determina raíz (pero no en whitelist, redirigiendo...)")
            destino_dir = 'docs/REFERENCE'  # Default para docs
        
        destino_path = raiz / destino_dir / nombre
        
        # Crear directorio si no existe
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Mover archivo
        try:
            shutil.move(str(archivo), str(destino_path))
            print(f"  ✅ {nombre} → {destino_dir}/{nombre}")
            reorganizados.append((nombre, destino_dir))
        except Exception as e:
            print(f"  ❌ Error moviendo {nombre}: {e}")
    
    return reorganizados, no_reorganizados

if __name__ == "__main__":
    print("\n🔄 FP-044C: Reorganizando documentación...")
    print("=" * 70)
    reorganizados, no_reorganizados = reorganizar_documentacion()
    
    print("\n" + "=" * 70)
    print(f"\n📊 RESUMEN:")
    print(f"  Reorganizados: {len(reorganizados)}")
    print(f"  En whitelist: {len(no_reorganizados)}")
    
    if reorganizados:
        print(f"\n📁 Movidos a:")
        dirs_count = {}
        for nombre, destino in reorganizados:
            dirs_count[destino] = dirs_count.get(destino, 0) + 1
        for destino, count in sorted(dirs_count.items()):
            print(f"  • {destino}: {count} archivos")
