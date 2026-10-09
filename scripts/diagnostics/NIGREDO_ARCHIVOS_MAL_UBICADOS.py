#!/usr/bin/env python3
"""NIGREDO AUDIT — Archivos mal ubicados en raíz"""

from pathlib import Path
from datetime import datetime

print('=' * 80)
print('NIGREDO AUDIT — Archivos mal ubicados en raíz')
print('=' * 80)

# Definir qué DEBE estar en raíz (lista blanca)
WHITELIST_RAIZ = {
    'iniciar computadora.bat',      # Launcher único
    'INDEX.md',                     # Hub central
    'README.md',                    # Docs generales
    'WorkItems.md',                 # Tareas (copia de docs/)
    'WORKFLOW_OPERACIONAL.md',      # Workflow (copia de docs/)
    'SRS.md',                       # Specs (copia de docs/)
    'SDD.md',                       # Specs (copia de docs/)
}

# Directorios que DEBEN estar
WHITELIST_DIRS = {
    '.git', '.github', '.gitignore',
    'computadora', 'datos', 'docs', 'scripts', 'tests', 'memories',
    '_config', 'computadora', 'loguru', 'lmstudio-mcp'  # Pueden ser legacy/especiales
}

# Clasificación: archivo → destino
FILE_CLASSIFICATION = {
    # Patterns → destino
    '*.py': {
        'diagnose': 'scripts/diagnostics',
        'test_': 'tests',
        'NIGREDO_': 'scripts/diagnostics',
        'VALIDAR_': 'scripts/diagnostics',
        'PROFILER_': 'scripts/diagnostics',
        'CODEGRAPH': 'scripts/diagnostics',
        'audit': 'scripts/diagnostics',
        'monitor': 'scripts/diagnostics',
        'check_': 'scripts/diagnostics',
        'rubedo': 'scripts/diagnostics',
        'FIX_': 'scripts/diagnostics',
        'SOLUCION': 'scripts/diagnostics',
        'VERIFICACION': 'scripts/diagnostics',
        'NIGREDO': 'scripts/diagnostics',
    },
    '*.md': {
        'DEUDA_TECNICA': 'docs/REFERENCE',
        'REORGANIZACION': 'docs/REFERENCE',
        'ARCHIVAL': 'docs/MISC',
        'SESION': 'docs/MISC',
        'VALIDACION': 'docs/REPORTS',
    },
    '*.json': {
        'codegraph': 'scripts/diagnostics',
        'report': 'docs/REPORTS',
    },
    '*.txt': {
        'RESUMEN': '.logs',
        '': '.logs',  # Por defecto, todos .txt a logs
    },
}

print('\n❌ ARCHIVOS MAL UBICADOS EN RAÍZ:\n')

root_items = sorted(Path('.').glob('*'))
bad_files = []
good_files = []

for item in root_items:
    if item.name.startswith('.'):
        continue
    if item.is_dir():
        if item.name not in WHITELIST_DIRS:
            print(f'📁 CARPETA MALA: {item.name}/ → Revisar si es legacy')
        continue
    
    if item.name not in WHITELIST_RAIZ:
        # Clasificar dónde debería ir
        destination = None
        
        # Buscar en clasificación
        for ext, patterns in FILE_CLASSIFICATION.items():
            if item.suffix == ext or item.name.endswith(ext.replace('*', '')):
                for pattern, dest in patterns.items():
                    if pattern and pattern.lower() in item.name.lower():
                        destination = dest
                        break
                if not destination and '' in patterns:
                    destination = patterns['']
                break
        
        if not destination:
            # Inferir por contenido/tipo
            if 'CODEGRAPH' in item.name or 'codegraph' in item.name:
                destination = 'scripts/diagnostics'
            elif item.suffix == '.py':
                destination = 'scripts/diagnostics'
            elif item.suffix == '.md':
                destination = 'docs/REFERENCE'
            elif item.suffix == '.json':
                destination = 'scripts/diagnostics'
            else:
                destination = 'docs/MISC'
        
        bad_files.append((item.name, destination))
        print(f'  ✗ {item.name:50} → {destination}/')
    else:
        good_files.append(item.name)

print(f'\n✓ Archivos correctamente en raíz: {len(good_files)}')
for f in good_files:
    print(f'  ✓ {f}')

print(f'\n⚠️  TOTAL archivos a mover: {len(bad_files)}')
print('\n' + '=' * 80)
