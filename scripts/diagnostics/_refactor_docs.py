#!/usr/bin/env python3
"""Consolidates all docs folders into /docs with proper structure."""
import shutil
from pathlib import Path

root = Path(".")
docs_root = root / "docs"

# 1. Move _docs content to docs/REFERENCE
_docs_folder = root / "_docs"
if _docs_folder.exists():
    for item in _docs_folder.iterdir():
        if item.is_dir():
            dst = docs_root / "REFERENCE" / item.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                shutil.rmtree(dst)
            shutil.move(str(item), str(dst))
            print(f"✓ Moved {item.name} → docs/REFERENCE/")
        elif item.suffix in [".md", ".json", ".py"]:
            dst = docs_root / "REFERENCE" / item.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(dst))
            print(f"✓ Moved {item.name} → docs/REFERENCE/")

# 2. Move .docs folder to docs/HIDDEN (if not empty)
dot_docs = root / ".docs"
if dot_docs.exists() and any(dot_docs.iterdir()):
    for item in dot_docs.iterdir():
        dst = docs_root / "MISC" / item.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            if item.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        shutil.move(str(item), str(dst))
        print(f"✓ Moved {item.name} → docs/MISC/")

# 3. Organize existing /docs files
organize_rules = {
    "SRS.md": "SPECIFICATIONS/",
    "SDD.md": "SPECIFICATIONS/",
    "WORKFLOW_OPERACIONAL.md": "REFERENCE/",
    "API.md": "SPECIFICATIONS/",
    "SECURITY_PLAN.md": "SPECIFICATIONS/",
    "TEST_COVERAGE.md": "SPECIFICATIONS/",
    "COMANDOS.md": "GUIDES/",
    "QUICK_START_LOCAL.md": "GUIDES/",
    "PERFORMANCE.md": "GUIDES/",
    "TROUBLESHOOTING_UI_NO_APARECE.md": "GUIDES/",
    "GUIA_COPILOT_vs_GEMINI.md": "GUIDES/",
    "CONTRASEÑA": "MISC/",
    "DIAGNOSTICO": "REPORTS/",
    "RESUMEN": "REPORTS/",
    "ESTADO": "REPORTS/",
    "FP-": "PROPOSALS/",
    "RF-": "PROPOSALS/",
}

for file_path in docs_root.glob("*.md"):
    fname = file_path.name
    target_folder = "MISC/"
    
    for pattern, folder in organize_rules.items():
        if pattern in fname:
            target_folder = folder
            break
    
    target_path = docs_root / target_folder / fname
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    if target_path != file_path:
        shutil.move(str(file_path), str(target_path))
        print(f"✓ Organized {fname} → docs/{target_folder}")

print("\n✅ Consolidation complete!")
