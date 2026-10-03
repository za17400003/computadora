#!/usr/bin/env python3
import ast
import sys

try:
    with open('computadora/interfaz/ventana_principal.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("✓ Sintaxis válida")
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}:")
    print(f"   {e.msg}")
    if e.text:
        print(f"   {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
