#!/usr/bin/env python3
"""
FP-044C+: Reorganizar archivos .py de raíz a carpetas correctas.

Usa FILE_LOCATION_MANAGER para PRE-determinar ubicación de cada .py.
Archivos en blancalist se quedan en raíz (normalmente no hay .py en whitelist).
"""

import shutil
from pathlib import Path
import sys

# Importar FILE_LOCATION_MANAGER
sys.path.insert(0, str(Path(__file__).parent.parent))
from FILE_LOCATION_MANAGER import FileLocationManager

def reorganizar_python():
    """Reorganizar .py de raíz a ubicaciones correctas."""
    raiz = Path(__file__).resolve().parent.parent.parent  # c:\...\proyecto-computadora
    
    # Encontrar todos los .py en raíz (EXCEPTO __pycache__, .git, etc.)
    archivos_py = [f for f in raiz.glob("*.py") if not f.name.startswith('.')]
    
    reorganizados = []
    no_reorganizados = []
    
    for archivo in archivos_py:
        nombre = archivo.name
        
        # Determinar destino
        destino_dir = FileLocationManager.get_location(nombre)
        if destino_dir == '.':
            print(f"  ⚠️ {nombre} — determina raíz (pero es .py, redirigiendo...)")
            destino_dir = 'scripts/diagnostics'  # Default para scripts
        
        destino_path = raiz / destino_dir / nombre
        
        # Si ya está en la ubicación correcta, skip
        if destino_path == archivo:
            print(f"  ✓ {nombre} — ya está en ubicación correcta ({destino_dir})")
            no_reorganizados.append(nombre)
            continue
        
        # Crear directorio si no existe
        destino_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Mover archivo
        try:
            shutil.move(str(archivo), str(destino_path))
            print(f"  ✅ {nombre} → {destino_dir}/{nombre}")
            reorganizados.append((nombre, destino_dir))
        except FileExistsError:
            print(f"  ⚠️ {nombre} ya existe en {destino_dir}, mantener en raíz")
            no_reorganizados.append(nombre)
        except Exception as e:
            print(f"  ❌ Error moviendo {nombre}: {e}")
    
    return reorganizados, no_reorganizados

if __name__ == "__main__":
    print("\n🔄 FP-044C+: Reorganizando archivos Python...")
    print("=" * 70)
    reorganizados, no_reorganizados = reorganizar_python()
    
    print("\n" + "=" * 70)
    print(f"\n📊 RESUMEN:")
    print(f"  Reorganizados: {len(reorganizados)}")
    print(f"  Ya organizados: {len(no_reorganizados)}")
    
    if reorganizados:
        print(f"\n📁 Movidos a:")
        dirs_count = {}
        for nombre, destino in reorganizados:
            dirs_count[destino] = dirs_count.get(destino, 0) + 1
        for destino, count in sorted(dirs_count.items()):
            print(f"  • {destino}: {count} archivos")
