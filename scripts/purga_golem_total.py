#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PURGA TOTAL: Reemplazar TODAS las instancias de "Golem" por "COMPUTADORA" en logs
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent / "computadora"
def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Replace all variations of Golem
        content = content.replace('el Golem ', 'COMPUTADORA ')
        content = content.replace('El Golem ', 'COMPUTADORA ')
        content = content.replace('"Golem"', '"COMPUTADORA"')
        content = content.replace("'Golem'", "'COMPUTADORA'")
        content = content.replace('cerebro_golem', 'cerebro_computadora')
        content = content.replace('"golem"', '"computadora"')
        content = content.replace("'golem'", "'computadora'")
        content = content.replace('paso.actor == "golem"', 'paso.actor == "computadora"')
        content = re.sub(r'(\bdirectorio\s+)golem/', r'\1computadora/', content)
        content = re.sub(r'(renacerá en esta sesión).*Golem', r'\1 COMPUTADORA', content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"❌ Error en {filepath}: {e}")
        return False

if __name__ == "__main__":
    count = 0
    for py_file in ROOT.rglob("*.py"):
        if fix_file(py_file):
            rel_path = py_file.relative_to(ROOT.parent)
            print(f"  ✓ {rel_path}")
            count += 1
    
    print(f"\n✅ Completado: {count} archivos actualizados")
