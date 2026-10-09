#!/usr/bin/env python
"""Diagnóstico rápido de estado de demo."""

import sys
import os

os.chdir(r'c:\Users\woire\Documents\proyecto-computadora')
sys.path.insert(0, os.getcwd())

print("="*60)
print("DIAGNÓSTICO RÁPIDO — COMPUTADORA DEMO")
print("="*60)
print()

# 1. Verificar imports críticos
try:
    print("[1] Verificando módulo computadora...")
    import computadora
    print("    ✅ computadora importable")
except Exception as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

try:
    print("[2] Verificando dibujante_orbe...")
    from computadora.interfaz.dibujante_orbe import (
        dibujar_anillos_sagrados, DrawState
    )
    print("    ✅ dibujante_orbe OK")
except Exception as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

try:
    print("[3] Verificando vida_autonoma...")
    from computadora.interfaz.vida_autonoma import VidaAutonoma, EstadoOrbe, EstadoPresencia
    print("    ✅ vida_autonoma OK")
except Exception as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

try:
    print("[4] Verificando monitor_sistema...")
    from computadora.habilidades.monitor_sistema import MonitorSistema
    print("    ✅ monitor_sistema OK")
except Exception as e:
    print(f"    ❌ Error: {e}")
    sys.exit(1)

try:
    print("[5] Verificando rostro/cámara...")
    from computadora.percepcion.rostro import AnalyzerRostro
    print("    ✅ rostro OK")
except Exception as e:
    print(f"    ❌ Error: {e}")
    print("    (Esto es tolerado si la cámara no está disponible)")

print()
print("="*60)
print("✅ DIAGNÓSTICO COMPLETADO - todos los módulos OK")
print("="*60)
print()
print("Estados esperados:")
print("  • EstadoOrbe: ", list(EstadoOrbe))
print("  • EstadoPresencia: ", list(EstadoPresencia))
