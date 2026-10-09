#!/usr/bin/env python3
"""Test bootstrap_ouroboros después del fix"""
import sys
sys.path.insert(0, '.')
from pathlib import Path

# Eliminar archivo si existe
cycle_file = Path("datos/ouroboros_cycle.jsonl")
if cycle_file.exists():
    cycle_file.unlink()
    print("✓ Eliminado archivo de ciclo previo")

from computadora.nucleo.ouroboros_stabilizer import bootstrap_ouroboros
print("Ejecutando bootstrap...")
try:
    ouroboros = bootstrap_ouroboros()
    print("✅ Bootstrap exitoso!")
    print(f"   Archivo de ciclo: {ouroboros.CYCLE_LOG_FILE}")
    if ouroboros.CYCLE_LOG_FILE.exists():
        with open(ouroboros.CYCLE_LOG_FILE, 'r', encoding='utf-8') as f:
            entries = f.readlines()
            print(f"   Entries: {len(entries)}")
            print(f"   Contenido: {entries[0][:80]}...")
    else:
        print("   ⚠ Archivo no encontrado")
except SystemExit as e:
    print(f"❌ Exit code: {e.code}")
    sys.exit(e.code)
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ TODO OK — iniciar_computadora.bat debería funcionar")

