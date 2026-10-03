#!/usr/bin/env python3
"""SOLUCIÓN FASE 3 — Mover archivos mal ubicados a sus carpetas correspondientes"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from FILE_LOCATION_MANAGER import FileLocationManager

print('=' * 80)
print('SOLUCIÓN FASE 3 — Reorganizar archivos en raíz')
print('=' * 80)

# Archivos a mover (identificados en NIGREDO audit)
files_to_move = [
    'ARCHIVAL_SESION_PALINGENESIA.md',
    'SESION_CERRADA_HANDOFF.md',
    'VALIDACION_FINAL_WI314_WI308.md',
]

print('\n📁 Moviendo archivos a ubicación correcta:\n')

for filename in files_to_move:
    result = FileLocationManager.move_if_in_root(filename)
    if result:
        print(f'  ✓ {filename} → {result.parent.name}/')

print('\n✅ VERIFICACIÓN POST-MOVIMIENTO:\n')

# Verificar que no hay más archivos mal ubicados
all_files = sorted(Path('.').glob('*'))
bad_count = 0
for item in all_files:
    if item.name.startswith('.') or item.is_dir():
        continue
    location = FileLocationManager.get_location(item.name)
    if location != '.':
        print(f'  ✗ {item.name} (debería estar en {location}/)')
        bad_count += 1

if bad_count == 0:
    print('  ✓ Raíz completamente limpia')
else:
    print(f'  ⚠️  Aún hay {bad_count} archivos mal ubicados')

print('\n' + '=' * 80)
