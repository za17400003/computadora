#!/usr/bin/env python3
"""VERIFICACIÓN FASE 4 — Raíz limpia + Workflow integrado"""

from pathlib import Path

print('=' * 80)
print('VERIFICACIÓN FASE 4 — Sistema automático de ubicación')
print('=' * 80)

# Blancalist de archivos permitidos en raíz
WHITELIST = {
    'iniciar computadora.bat',
    'INDEX.md',
    'README.md',
    'WorkItems.md',
    'WORKFLOW_OPERACIONAL.md',
    'SRS.md',
    'SDD.md',
    'WORKFLOW_OPERACIONAL.md',  # En raíz (copia de docs)
}

print('\n✅ TEST 1: Raíz completamente limpia')
all_files = sorted(Path('.').glob('*'))
bad_files = []
for item in all_files:
    if item.name.startswith('.') or item.is_dir():
        continue
    if item.name not in WHITELIST:
        bad_files.append(item.name)
        print(f'  ✗ {item.name} (debería estar en carpeta)')

if not bad_files:
    print('  ✓ Raíz LIMPIA — solo archivos permitidos')
else:
    print(f'  ⚠️  Aún hay {len(bad_files)} archivos mal ubicados')

print('\n✅ TEST 2: Archivos movidos a sus ubicaciones')
checks = [
    ('docs/REPORTS/ARCHIVAL_SESION_PALINGENESIA.md', '✓ ARCHIVAL_SESION_PALINGENESIA.md en REPORTS/'),
    ('docs/MISC/SESION_CERRADA_HANDOFF.md', '✓ SESION_CERRADA_HANDOFF.md en MISC/'),
    ('docs/REFERENCE/VALIDACION_FINAL_WI314_WI308.md', '✓ VALIDACION_FINAL_WI314_WI308.md en REFERENCE/'),
]

for path_str, message in checks:
    if Path(path_str).exists():
        print(f'  {message}')
    else:
        print(f'  ✗ {path_str} NO ENCONTRADO')

print('\n✅ TEST 3: FILE_LOCATION_MANAGER presente')
if Path('scripts/FILE_LOCATION_MANAGER.py').exists():
    print('  ✓ FILE_LOCATION_MANAGER.py en scripts/')
else:
    print('  ✗ FILE_LOCATION_MANAGER.py NO ENCONTRADO')

print('\n✅ TEST 4: Workflows actualizados con regla de ubicación')
workflow_files = [
    'docs/REFERENCE/WORKFLOW_OPERACIONAL.md',
    'docs/REFERENCE/DEVELOPMENT_WORKFLOW_LOCAL.md',
    'docs/REFERENCE/DEVELOPMENT_WORKFLOW_REFERENCIA.md',
]

for wf_path in workflow_files:
    wf = Path(wf_path)
    if wf.exists():
        content = wf.read_text(encoding='utf-8', errors='ignore')
        if 'PRE-determinar' in content or 'FILE_LOCATION_MANAGER' in content or 'ubicación antes de crear' in content:
            print(f'  ✓ {wf.name} incluye regla de ubicación')
        else:
            print(f'  ⚠️  {wf.name} aún no integra FILE_LOCATION_MANAGER')
    else:
        print(f'  ✗ {wf_path} NO ENCONTRADO')

print('\n' + '=' * 80)
print('✅ VERIFICACIÓN COMPLETADA')
print('=' * 80)
