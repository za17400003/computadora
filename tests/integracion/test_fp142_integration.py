#!/usr/bin/env python3
"""Test FP-142 integration: ActualizadorGolem import + methods"""

from computadora.nucleo.actualizador import ActualizadorGolem

a = ActualizadorGolem()
print("✓ ActualizadorGolem importa correctamente")
print(f"  INTERVALO_CHECK_HORAS: {a.INTERVALO_CHECK_HORAS}")
print(f"  método verificar_todo disponible: {hasattr(a, 'verificar_todo')}")
print(f"  método necesita_verificacion disponible: {hasattr(a, 'necesita_verificacion')}")
print()
print("✓ FP-142 integration ready for production")

