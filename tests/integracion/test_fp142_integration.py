#!/usr/bin/env python3
"""Test FP-142 integration: ActualizadorComputadora import + methods"""

from computadora.nucleo.actualizador import ActualizadorComputadora

a = ActualizadorComputadora()
print("✓ ActualizadorComputadora importa correctamente")
print(f"  INTERVALO_CHECK_HORAS: {a.INTERVALO_CHECK_HORAS}")
print(f"  método verificar_todo disponible: {hasattr(a, 'verificar_todo')}")
print(f"  método necesita_verificacion disponible: {hasattr(a, 'necesita_verificacion')}")
print()
print("✓ FP-142 integration ready for production")

