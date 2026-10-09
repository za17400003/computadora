#!/usr/bin/env python
"""Fix all 'computadora' imports to 'computadora' in the computadora/ package."""

import os

replacements = [
    ("from computadora.", "from computadora."),
    ("import computadora.", "import computadora."),
    ('__nombre__ = "Computadora"', '__nombre__ = "Computadora"'),
    ('__nombre__ = "computadora"', '__nombre__ = "Computadora"'),
]

pyfiles = []
for root, dirs, files in os.walk("computadora"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for f in files:
        if f.endswith(".py"):
            pyfiles.append(os.path.join(root, f))

updated = 0
for fpath in pyfiles:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            updated += 1
            print(f"✅ {fpath}")
    except Exception as e:
        print(f"❌ {fpath}: {e}")

print(f"\n✔️ Total archivos actualizados: {updated}/{len(pyfiles)}")
