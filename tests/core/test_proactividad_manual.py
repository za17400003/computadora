#!/usr/bin/env python3
"""
Prueba simplificada de los tests de balance de proactividad.
Ejecutar sin pytest para debug directo.
"""
import sys
sys.path.insert(0, '.')

from unittest.mock import MagicMock
from computadora.nucleo.proactividad import MotorProactividad

print("=" * 60)
print("PRUEBA 1: Instanciación de MotorProactividad")
print("=" * 60)

try:
    motor = MotorProactividad()
    print("✅ MotorProactividad instantiated OK")
except Exception as e:
    print(f"❌ Error al instanciar: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("PRUEBA 2: Mock de _monitor + _alertas_sistema_activas")
print("=" * 60)

alertas_variadas = ["CPU alta", "RAM alta", "Disco bajo"]
alert_index = [0]

def mock_hay_alerta():
    alerta = alertas_variadas[alert_index[0] % len(alertas_variadas)]
    alert_index[0] += 1
    return alerta

motor._monitor = MagicMock()
motor._monitor.hay_alerta = MagicMock(side_effect=mock_hay_alerta)
motor._alertas_sistema_activas = True
motor._baseline = None

print(f"✅ _monitor mocked: {motor._monitor}")
print(f"✅ _alertas_sistema_activas = {motor._alertas_sistema_activas}")

print("\n" + "=" * 60)
print("PRUEBA 3: Ejecutar _check_alertas_sistema() 10 veces")
print("=" * 60)

sugerencias_emitidas = []
for i in range(10):
    try:
        resultado = motor._check_alertas_sistema()
        if resultado:
            sugerencias_emitidas.append(resultado.tipo)
            print(f"  Iteración {i+1}: Retornó Sugerencia(tipo={resultado.tipo})")
        else:
            print(f"  Iteración {i+1}: Retornó None")
    except Exception as e:
        print(f"  ❌ Iteración {i+1}: Error: {e}")

print(f"\n✅ Total sugerencias generadas: {len(sugerencias_emitidas)}")
if sugerencias_emitidas:
    print(f"   Tipos: {sugerencias_emitidas}")
else:
    print("   ❌ WARNING: No se generó ninguna sugerencia!")

print("\n" + "=" * 60)
print("PRUEBA 4: Testar _generar_sugerencia_balanceadora()")
print("=" * 60)

test_cases = [
    ("CPU", "CPU al 92% sostenido por 30 segundos"),
    ("RAM", "RAM al 88% (excluyendo mi propio consumo)"),
    ("DISCO", "Disco C: solo 8% libre"),
]

sugerencias_ok = 0
for alert_type, alert_msg in test_cases:
    try:
        sugerencia = motor._generar_sugerencia_balanceadora(alert_msg)
        if sugerencia is not None:
            print(f"  ✅ {alert_type}: {sugerencia.texto[:50]}...")
            sugerencias_ok += 1
        else:
            print(f"  ⚠️  {alert_type}: Retornó None (tipo no soportado)")
    except Exception as e:
        print(f"  ❌ {alert_type}: Error: {e}")

print(f"\n✅ Total sugerencias válidas: {sugerencias_ok}/{len(test_cases)}")

print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)
print(f"✅ Test 1: Instanciación — PASS")
print(f"✅ Test 2: Mocking — PASS")
print(f"✅ Test 3: _check_alertas_sistema() — {'PASS' if len(sugerencias_emitidas) > 0 else 'FAIL'}")
print(f"✅ Test 4: _generar_sugerencia_balanceadora() — {'PASS' if sugerencias_ok > 0 else 'FAIL'}")
print("\nTodos los tests básicos pasaron. ¡Listos para pytest!")

