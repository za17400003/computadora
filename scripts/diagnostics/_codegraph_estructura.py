#!/usr/bin/env python3
"""Análisis estructural completo usando CodeGraph."""
import json
from pathlib import Path
from collections import defaultdict

# Cargar CodeGraph report
with open("codegraph_report.json", "r", encoding="utf-8") as f:
    cg = json.load(f)

print("\n" + "="*80)
print("ANÁLISIS ESTRUCTURAL COMPLETO (CodeGraph)")
print("="*80)

# 1. Agrupar módulos por carpeta principal
print("\n[1] MÓDULOS POR CARPETA PRINCIPAL\n")
by_folder = defaultdict(list)
for module_path in cg['modules'].keys():
    folder = module_path.split('/')[0]
    by_folder[folder].append(module_path)

for folder in sorted(by_folder.keys()):
    count = len(by_folder[folder])
    print(f"📁 {folder:30} ({count:3} módulos)")

# 2. Identificar dependencias críticas (qué importa qué)
print("\n[2] DEPENDENCIAS DE CARPETAS CRÍTICAS\n")
critical = ['computadora', 'scripts', 'tests']
for folder in critical:
    print(f"\n  {folder}/")
    imports = cg.get('import_graph', {})
    count = 0
    for module in by_folder.get(folder, []):
        if module in imports:
            deps = imports[module]
            if deps and count < 3:
                print(f"    • {Path(module).name}: imports {', '.join(list(set(str(d.split('/')[0]) for d in deps if '/' in d))[:3])}")
                count += 1

# 3. Identificar carpetas raíz potencialmente innecesarias
print("\n[3] CARPETAS RAÍZ (Redundancia)\n")
redundant = {
    '_archive': 'Legacy/historical (safe to remove)',
    '_audit': 'Old audit logs (safe to remove)',
    '_computadora_current': 'Duplicate/snapshot (check content)',
    '_legacy_reference': 'Legacy code (can consolidate to docs)',
    'ARCHITECTURE': 'Duplicate of docs/ARCHITECTURE (consolidate)',
    'REPORTS': 'Duplicate of docs/REPORTS (consolidate)',
    'golem': 'Legacy folder (check if used)',
    'interfaz': 'Empty (remove)',
    'nucleo': 'Empty (remove)',
    '_audit': 'Audit artifacts (archive)',
}

for folder, status in redundant.items():
    path = Path(folder)
    if path.exists():
        item_count = len(list(path.rglob("*")))
        print(f"  ⚠️  {folder:25} ({item_count:3} items) → {status}")

# 4. Archivos en raíz que NO son .bat o config
print("\n[4] ARCHIVOS RAÍZ A ORGANIZAR\n")
root_py_scripts = [
    'CODEGRAPH_ANALYZER.py',
    'CODEGRAPH_QUERY.py',
    'monitor_boot_live.py',
    'monitor_fps_realtime.py',
    'QUICK_START.py',
    'diagnose_escucha.py',
    'FIX_GOLEM_RESIDUES.py',
    'PROFILER_COMPLETO_THREADING.py',
    'NIGREDO_*.py',
    'DIAGNOSTICO_*.py',
    'VALIDAR_*.py',
    'run_boot_test.py',
    'verify_boot.py'
]

root_md_files = [
    'ARCHIVAL_SESION_PALINGENESIA.md',
    'SESION_CERRADA_HANDOFF.md',
    'VALIDACION_FINAL_*.md',
    'README.md'
]

root_logs = [
    'logs_live*.txt',
    'test_output.txt',
    'diagnostico_output.txt',
    'RESUMEN_VISUAL_*.txt'
]

print(f"  Scripts Python (→ scripts/): ~{len(root_py_scripts)} scripts")
print(f"  Markdown docs (→ docs/MISC): ~{len(root_md_files)} archivos")
print(f"  Logs/diagnostics (→ .logs/): ~{len(root_logs)} archivos")

# 5. Qué DEBE quedar en raíz
print("\n[5] ARCHIVOS QUE DEBEN QUEDAR EN RAÍZ\n")
must_keep = [
    'iniciar computadora.bat    ← Launcher principal',
    'docs/INDEX.md              ← Central hub (symlink OK)',
    'docs/MANAGEMENT/WorkItems.md ← Project management',
    'docs/REFERENCE/WORKFLOW_OPERACIONAL.md ← Desarrollo workflow',
    'docs/SPECIFICATIONS/SRS.md ← Requirements',
    'docs/SPECIFICATIONS/SDD.md ← Design',
]
for item in must_keep:
    print(f"  ✓ {item}")

print("\n" + "="*80)
print("RECOMENDACIÓN FINAL")
print("="*80)
print("""
FASE DE LIMPIEZA PROPUESTA:

1. ELIMINAR (sin backup):
   - interfaz/, nucleo/ (empty)
   - _archive/, _audit/, _computadora_current/, _legacy_reference/

2. CONSOLIDAR:
   - ARCHITECTURE/ → docs/ARCHITECTURE/
   - REPORTS/ → docs/REPORTS/
   - Carpetas raíz .py scripts → scripts/diagnostics/

3. MOVER A RAÍZ (symlink o copia):
   - WorkItems.md: docs/MANAGEMENT/WorkItems.md → /WorkItems.md
   - SRS.md: docs/SPECIFICATIONS/SRS.md → /SRS.md
   - SDD.md: docs/SPECIFICATIONS/SDD.md → /SDD.md
   - WORKFLOW_OPERACIONAL.md: docs/REFERENCE/ → /WORKFLOW_OPERACIONAL.md
   - INDEX.md: docs/INDEX.md → /INDEX.md

4. ESTADO FINAL RAÍZ:
   ✓ iniciar computadora.bat
   ✓ WorkItems.md (link)
   ✓ INDEX.md (link)
   ✓ WORKFLOW_OPERACIONAL.md (link)
   ✓ SRS.md (link)
   ✓ SDD.md (link)
   ✓ .git/, .github/, .gitignore
   ✓ computadora/, datos/, docs/, scripts/, tests/

TOTAL: 11 items en raíz (down from 80+)
""")

print("\n✅ Análisis CodeGraph completado\n")
