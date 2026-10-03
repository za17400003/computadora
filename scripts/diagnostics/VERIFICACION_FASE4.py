#!/usr/bin/env python3
"""VERIFICACIÓN FASE 4 — Pruebas de que todo está correcto"""

from pathlib import Path

print('=' * 80)
print('VERIFICACIÓN FINAL — Fase 4')
print('=' * 80)

# 1. Verificar que INDEX.md está presente en raíz Y en docs
print('\n✅ TEST 1: INDEX.md Presente')
index_root = Path('INDEX.md').exists()
index_docs = Path('docs/INDEX.md').exists()
print(f'  Raíz: {"✓" if index_root else "✗"} INDEX.md')
print(f'  Docs: {"✓" if index_docs else "✗"} docs/INDEX.md')

# 2. Verificar que INDEX.md está referenciado en todos los workflows
print('\n✅ TEST 2: INDEX.md Referenciado en Workflows')
workflows = list(Path('.').rglob('*WORKFLOW*.md'))
index_refs = 0
for wf in sorted(workflows):
    content = wf.read_text(encoding='utf-8', errors='ignore')
    has_index = 'INDEX.md' in content
    status = '✓' if has_index else '✗'
    print(f'  {status} {wf.relative_to(".")}')
    if has_index: index_refs += 1

# 3. Verificar que CodeGraph está en workflows
print('\n✅ TEST 3: CodeGraph en Workflows')
cg_refs = 0
for wf in sorted(workflows):
    content = wf.read_text(encoding='utf-8', errors='ignore')
    has_cg = 'CodeGraph' in content or 'CODEGRAPH' in content
    status = '✓' if has_cg else '✗'
    print(f'  {status} {wf.relative_to(".")}')
    if has_cg: cg_refs += 1

# 4. Verificar que no hay .log en raíz
print('\n✅ TEST 4: No Logs en Raíz')
root_logs = list(Path('.').glob('*.log'))
print(f'  .log archivos en raíz: {len(root_logs)} (debe ser 0)')
if root_logs:
    for log in root_logs[:3]:
        print(f'    - {log.name}')

# 5. Verificar que no hay carpetas legacy
print('\n✅ TEST 5: No Carpetas Legacy')
legacy_dirs = list(Path('.').glob('_archive')) + list(Path('.').glob('_audit')) + list(Path('.').glob('_legacy*'))
print(f'  Carpetas legacy: {len(legacy_dirs)} (debe ser 0)')
if legacy_dirs:
    for d in legacy_dirs:
        print(f'    - {d.name}')

# 6. Verificar que .logs tiene los logs
print('\n✅ TEST 6: Logs en .logs/')
logs_in_dotlogs = list(Path('.logs').glob('*.log'))
print(f'  .log archivos en .logs/: {len(logs_in_dotlogs)} (debe ser 22)')

# 7. Verificar structure básica
print('\n✅ TEST 7: Estructura Raíz Limpia')
root_items = list(Path('.').iterdir())
root_items = [p for p in root_items if not p.name.startswith('.') and p.name != '__pycache__']
dirs = [p.name for p in root_items if p.is_dir()]
files = [p.name for p in root_items if p.is_file()]
print(f'  Carpetas (debe ser ~8): {len(dirs)}')
print(f'  Archivos (debe ser ~11): {len(files)}')
for d in sorted(dirs):
    if d not in ['.git', '.github']:
        print(f'    📁 {d}')
for f in sorted(files)[:15]:
    print(f'    📄 {f}')

# RESUMEN
print('\n' + '=' * 80)
print('RESUMEN DE PRUEBAS')
print('=' * 80)

all_pass = (
    index_root and index_docs and
    index_refs == len(workflows) and
    cg_refs == len(workflows) and
    len(root_logs) == 0 and
    len(legacy_dirs) == 0 and
    len(logs_in_dotlogs) == 22
)

if all_pass:
    print('✅ TODAS LAS PRUEBAS PASARON')
else:
    print('⚠️  ALGUNAS PRUEBAS FALLARON')
    if not (index_root and index_docs): print('  - INDEX.md no está presente')
    if index_refs != len(workflows): print('  - INDEX.md no en todos los workflows')
    if cg_refs != len(workflows): print('  - CodeGraph no en todos los workflows')
    if root_logs: print(f'  - Aún hay {len(root_logs)} .log en raíz')
    if legacy_dirs: print(f'  - Aún hay {len(legacy_dirs)} carpetas legacy')
    if len(logs_in_dotlogs) != 22: print(f'  - Solo {len(logs_in_dotlogs)} logs en .logs (debe ser 22)')

print('\n✅ ESTADO: VERIFICACIÓN COMPLETADA')
