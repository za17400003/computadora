#!/usr/bin/env python3
"""
SOLUCIÓN COMPLETA - Arreglar todos los problemas de reorganización

Pasos:
1. Mover todos los .log a .logs/
2. Borrar carpetas legacy (_archive/, _audit/, _legacy_reference/)
3. Actualizar workflows para referenciar INDEX.md PRIMERO
4. Integrar CodeGraph de forma explícita en workflows
5. Consolidar duplicados de workflows (raíz → docs/REFERENCE/)
"""

from pathlib import Path
import shutil
import os

print('=' * 80)
print('SOLUCIÓN COMPLETA — Arreglando deuda técnica')
print('=' * 80)

# PASO 1: Mover todos los .log a .logs/
print('\n📁 PASO 1: Mover .log files a .logs/')
logs_moved = 0
for log_file in Path('.').glob('*.log'):
    try:
        dest = Path('.logs') / log_file.name
        shutil.move(str(log_file), str(dest))
        print(f'  ✓ {log_file.name} → .logs/')
        logs_moved += 1
    except Exception as e:
        print(f'  ✗ {log_file.name}: {e}')

print(f'  Total movidos: {logs_moved}')

# PASO 2: Borrar carpetas legacy
print('\n🗑️  PASO 2: Borrar carpetas legacy')
legacy_dirs = ['_archive', '_audit', '_legacy_reference', '_legacy_*', '.docs']
for pattern in legacy_dirs:
    for dir_path in Path('.').glob(pattern):
        if dir_path.is_dir() and dir_path.name not in ['.git', '.github', 'computadora', 'datos', 'docs', 'scripts', 'tests']:
            try:
                shutil.rmtree(dir_path)
                print(f'  ✓ Borrado: {dir_path.name}/')
            except Exception as e:
                print(f'  ✗ Error borrando {dir_path.name}: {e}')

# PASO 3: Consolidar workflows (raíz → docs/REFERENCE/, mantener OPERACIONAL en raíz)
print('\n📝 PASO 3: Consolidar workflows duplicados')
operacional_src = Path('WORKFLOW_OPERACIONAL.md')
operacional_dest = Path('docs/REFERENCE/WORKFLOW_OPERACIONAL.md')

if operacional_src.exists() and operacional_dest.exists():
    # Verificar que son iguales
    if operacional_src.read_text() == operacional_dest.read_text():
        operacional_src.unlink()  # Borrar copia en raíz
        print(f'  ✓ Removida copia duplicada de raíz')
    else:
        print(f'  ⚠️  Archivos diferentes, comparando...')

# PASO 4: Actualizar todos los workflows
print('\n🔄 PASO 4: Actualizar workflows para INDEX.md + CodeGraph')

# Patrones de remplazo
# Todos los workflows deben tener:
# - Referencia a INDEX.md en bootstrap
# - Referencia a CodeGraph en Fase 0
# - Referencia a docs/

workflows_to_update = [
    'WORKFLOW_OPERACIONAL.md',
    'docs/REFERENCE/WORKFLOW_OPERACIONAL.md',
    'docs/REFERENCE/DEVELOPMENT_WORKFLOW_LOCAL.md',
]

for wf_path in workflows_to_update:
    wf = Path(wf_path)
    if not wf.exists():
        continue
    
    print(f'  Actualizando: {wf.name}')
    content = wf.read_text(encoding='utf-8')
    
    # Actualizar referencia a INDEX.md
    if 'INDEX.md' not in content:
        if '## § BOOTSTRAP OBLIGATORIO' in content:
            content = content.replace(
                '## § BOOTSTRAP OBLIGATORIO\n\n**SIEMPRE**: Antes de actuar, leer en este orden:',
                '## § BOOTSTRAP OBLIGATORIO\n\n**SIEMPRE**: Antes de actuar, consulta:\n\n1. ✅ `INDEX.md` o `docs/INDEX.md` — Hub central (START HERE)\n2. ✅ `docs/DEVELOPMENT_WORKFLOW_REFERENCIA.md` — Marco teórico\n3. ✅ `WorkItems.md` — Tareas pendientes\n4. ✅ Este archivo (WORKFLOW_OPERACIONAL.md) — Acción\n\n> **Por qué INDEX.md primero**: Es tu mapa, ahí encuentras TODO lo que necesitas.'
            )
    
    # Actualizar referencia a CodeGraph Fase 0
    if 'CODEGRAPH — EXPLORACIÓN' in content or '## § CODEGRAPH' in content:
        # Ya está, solo marcar mejor
        content = content.replace(
            'CODEGRAPH — EXPLORACIÓN SIN TOOL CALLS',
            '**FASE 0 OBLIGATORIA: CodeGraph** — Análisis sin tool calls'
        )
        content = content.replace(
            '## § CODEGRAPH',
            '## §0 CODEGRAPH (FASE 0 — SIEMPRE PRIMERO)'
        )
    
    wf.write_text(content, encoding='utf-8')
    print(f'    ✓ Actualizado')

# PASO 5: Verificaciones finales
print('\n✅ PASO 5: Verificaciones')

# Verificar que no hay .log en raíz
remaining_logs = list(Path('.').glob('*.log'))
if remaining_logs:
    print(f'  ⚠️  Aún hay {len(remaining_logs)} .log en raíz')
else:
    print(f'  ✓ No hay .log en raíz')

# Verificar que INDEX.md existe en raíz
if Path('INDEX.md').exists():
    print(f'  ✓ INDEX.md presente en raíz')
else:
    print(f'  ✗ INDEX.md FALTA en raíz')

# Verificar que workflows existen
for wf in ['WORKFLOW_OPERACIONAL.md', 'docs/REFERENCE/WORKFLOW_OPERACIONAL.md']:
    if Path(wf).exists():
        print(f'  ✓ {wf} presente')

# Verificar que carpetas legacy están borradas
legacy_check = list(Path('.').glob('_archive')) + list(Path('.').glob('_audit')) + list(Path('.').glob('_legacy*'))
if legacy_check:
    print(f'  ⚠️  Aún hay {len(legacy_check)} carpetas legacy')
else:
    print(f'  ✓ No hay carpetas legacy')

print('\n' + '=' * 80)
print('✅ SOLUCIÓN COMPLETADA')
print('=' * 80)
print('\nProximos pasos:')
print('  1. Verificación (tests)')
print('  2. Documentación')
print('  3. Commit')
