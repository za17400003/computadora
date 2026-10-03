#!/usr/bin/env python3
"""NIGREDO AUDIT COMPLETO - Detectar deuda técnica post-reorganización"""

from pathlib import Path
import os

print('=' * 70)
print('NIGREDO AUDIT — Deuda técnica post-reorganización')
print('=' * 70)

# 1. Logs en raíz que deberían estar en .logs/
print('\n❌ PROBLEMA 1: LOGS EN RAÍZ')
root_logs = list(Path('.').glob('*.log')) + list(Path('.').glob('*.txt'))
root_logs = [p for p in root_logs if p.name not in ['README.txt', 'config.txt']]
if root_logs:
    for log in sorted(root_logs):
        print(f'  - {log.name} ({log.stat().st_size} bytes)')
else:
    print('  ✓ Ninguno encontrado')

# 2. Carpetas vacías o redundantes en raíz
print('\n❌ PROBLEMA 2: CARPETAS REDUNDANTES/VACÍAS EN RAÍZ')
suspect_dirs = [
    'ARCHITECTURE', 'REPORTS', '_docs', '.docs', '_legacy_*', '_archive', 
    '_audit', '_test', '_temp', 'interfaz', 'nucleo'
]
found_dirs = []
for pattern in suspect_dirs:
    matches = list(Path('.').glob(pattern))
    found_dirs.extend(matches)

if found_dirs:
    for d in sorted(set(found_dirs)):
        if d.is_dir():
            items = list(d.iterdir())
            print(f'  - {d.name}/ ({len(items)} items)')
            if len(items) < 3 and items:
                for item in items[:3]:
                    print(f'      • {item.name}')
else:
    print('  ✓ Ninguno encontrado')

# 3. INDEX.md referenciado en workflows
print('\n❌ PROBLEMA 3: INDEX.md NO REFERENCIADO EN WORKFLOWS')
workflows_checked = 0
index_refs = 0
for wf in Path('.').rglob('*WORKFLOW*.md'):
    workflows_checked += 1
    content = wf.read_text(encoding='utf-8', errors='ignore')
    if 'INDEX.md' in content or 'docs/INDEX.md' in content:
        index_refs += 1
        print(f'  ✓ {wf.relative_to(".")} SÍ referencia INDEX.md')
    else:
        print(f'  ✗ {wf.relative_to(".")} NO referencia INDEX.md')

# 4. Archivos de configuración de workflows
print('\n📋 WORKFLOWS EXISTENTES + PROPÓSITO')
for wf in sorted(Path('.').rglob('*WORKFLOW*.md')):
    content = wf.read_text(encoding='utf-8', errors='ignore')
    is_local = 'local' in wf.name.lower() or 'ollama' in content.lower()
    is_cloud = 'cloud' in wf.name.lower() or 'copilot' in content.lower() or 'azure' in content.lower()
    is_operacional = 'operacional' in wf.name.lower()
    
    tipo = []
    if is_local: tipo.append('LOCAL')
    if is_cloud: tipo.append('CLOUD')
    if is_operacional: tipo.append('OPERACIONAL')
    
    path = wf.relative_to('.')
    print(f'  - {path}')
    print(f'      Tipo: {" / ".join(tipo) if tipo else "GENÉRICO"}')
    
    # Primeras líneas de propósito
    lines = content.split('\n')[:10]
    for line in lines:
        if 'Para:' in line or 'PROPÓSITO' in line:
            print(f'      {line.strip()}')
            break

# 5. CodeGraph referenciado
print('\n❌ PROBLEMA 4: CodeGraph NO REFERENCIADO EN WORKFLOWS')
for wf in sorted(Path('.').rglob('*WORKFLOW*.md')):
    content = wf.read_text(encoding='utf-8', errors='ignore')
    has_codegraph = 'CodeGraph' in content or 'codegraph' in content or 'CODEGRAPH' in content
    path = wf.relative_to('.')
    if has_codegraph:
        print(f'  ✓ {path} SÍ menciona CodeGraph')
    else:
        print(f'  ✗ {path} NO menciona CodeGraph')

print('\n' + '=' * 70)
print('PROBLEMAS IDENTIFICADOS:')
print('=' * 70)
print('\n1. INDEX.md copia en raíz, pero NO referenciado en workflows')
print('2. CodeGraph NO integrado en workflows operacionales')
print('3. Posibles logs residuales en raíz')
print('4. Carpetas no completamente removidas')
print('5. Workflows duplicados (raíz + docs/REFERENCE/)')
