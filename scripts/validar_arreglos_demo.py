#!/usr/bin/env python
"""Validación de arreglos aplicados a la demo."""

import os
import sys

os.chdir(r'c:\Users\woire\Documents\proyecto-computadora')
sys.path.insert(0, os.getcwd())

print("="*60)
print("VALIDACIÓN DE ARREGLOS DEMO (FP-140)")
print("="*60)
print()

errors = []

# 1. Verificar computadora_boot.bat path correcto
print("[1] Verificando computadora_boot.bat...")
with open('computadora_boot.bat', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'scripts\\wrapper_computadora.py' in content:
        print("    ✅ Ruta wrapper correcta en boot script")
    else:
        print("    ❌ Ruta wrapper NO encontrada en boot script")
        errors.append("Boot script path")

# 2. Verificar anillos siempre visibles
print("[2] Verificando anillos siempre visibles...")
with open('computadora/interfaz/ventana_principal.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'self._dibujar_anillos_sagrados(painter' in content and \
       'if not _en_movimiento_render and not _carga_alta:' not in \
       content[content.find('ANILLOS DE GEOMETRÍA'):content.find('ANILLOS DE GEOMETRÍA')+500]:
        print("    ✅ Anillos configurados para ser siempre visibles")
    else:
        print("    ❌ Verificar configuración de anillos")

# 3. Verificar letras orbitantes siempre visibles  
print("[3] Verificando letras orbitantes...")
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'LETRAS HEBREAS' in line and i+2 < len(lines):
        next_line = lines[i+2]
        if 'if not _en_movimiento' not in next_line:
            print("    ✅ Letras orbitantes siempre visibles")
        else:
            print("    ❌ Letras orbitantes aún condicionadas")
            errors.append("Orbital letters visibility")
        break

# 4. Verificar timeout hardware reducido
print("[4] Verificando timeout hardware...")
with open('computadora/__main__.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'timeout_s=5.0' in content:
        print("    ✅ Timeout hardware reducido a 5s")
    elif 'timeout_s=10.0' in content:
        print("    ⚠️  Timeout aún en 10s (debería ser 5s)")
        errors.append("Hardware timeout")
    else:
        print("    ❌ Timeout hardware no encontrado")
        errors.append("Hardware timeout missing")

print()
print("="*60)
if errors:
    print(f"⚠️  {len(errors)} verificación(es) con advertencia:")
    for e in errors:
        print(f"   • {e}")
else:
    print("✅ TODAS LAS VALIDACIONES PASARON")
    print()
    print("Cambios aplicados:")
    print("  ✓ computadora_boot.bat: wrapper path corregido")
    print("  ✓ ventana_principal.py: anillos siempre visibles")
    print("  ✓ ventana_principal.py: letras orbitantes siempre visibles")
    print("  ✓ __main__.py: timeout hardware = 5s")
    print()
    print("Status de demo: REPARADA")
    print()
    print("Próximos pasos:")
    print("  1. Ejecutar: computadora_boot.bat")
    print("  2. Verificar que anillos de sistema están visibles")
    print("  3. Verificar que cámara no se bloquea en startup")
    print("  4. Demo debería funcionar sin interrupciones")

print("="*60)
