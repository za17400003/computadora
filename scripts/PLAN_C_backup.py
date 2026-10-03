#!/usr/bin/env python3
"""
ESTRATEGIA ALTERNATIVA (Si Ronda 2 falla):
- Fuerza bruta ULTRA-AGRESIVA con caracteres especiales
- Patrones comunes de PDFs protegidos
- Búsqueda exhaustiva de números + palabras
"""

print("\n[!] PLAN C (Si Rondas 1 y 2 fallan):\n")

print("Estrategia 1: Patrones de passwords PDF típicos")
print("  - owner:user (contraseñas de propietario vs usuario)")
print("  - Contraseñas numéricas puras (1-1000000)")
print("  - Nombres + números")

print("\nEstrategia 2: Análisis Bayesiano de audios")
print("  - Escuchar audios nuevamente (podrían haber errores de Whisper)")
print("  - Buscar patrones fonéticos vs ortográficos")

print("\nEstrategia 3: Herramientas externas")
print("  - pdfcrack (aunque requiere compilación)")
print("  - qpdf (puede remover protección de propietario)")

print("\nEstrategia 4: Análisis de metadata")
print("  - Extraer info del PDF con exiftool (si disponible)")
print("  - Buscar pistas en strings ASCII del archivo")

print("\nEstrategia 5: Fuerza bruta pura (números)")
contraseñas_numeros = []

# Números simples (0-10000)
for i in range(10000):
    contraseñas_numeros.append(str(i))
    contraseñas_numeros.append(str(i).zfill(4))

print(f"  - {len(contraseñas_numeros)} números generados (0-9999 con padding)")

print("\n[!] Guardar Plan C para ejecución manual si es necesario")

with open('PLAN_C_backup_strategies.txt', 'w') as f:
    f.write("PLAN C - Estrategias de backup si Rondas 1 y 2 fallan\n")
    f.write("="*80 + "\n\n")
    f.write("1. Números puros (0-10000)\n")
    for num in contraseñas_numeros:
        f.write(num + '\n')

print(f"\nGuardado en: PLAN_C_backup_strategies.txt")
