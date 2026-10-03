#!/usr/bin/env python3
"""
MULTI-MICROPHONE DIAGNOSTIC — Computadora con múltiples micrófonos
"""

import sounddevice as sd
import numpy as np
import time
import threading
import queue
from pathlib import Path

print("=" * 80)
print("🎙️ DIAGNÓSTICO MULTI-MICRÓFONO — Computadora")
print("=" * 80)

# LISTAR TODOS LOS DISPOSITIVOS DE ENTRADA
print("\n📋 DISPOSITIVOS DE ENTRADA DISPONIBLES:")
print("-" * 80)

dispositivos = sd.query_devices()
dispositivos_entrada = []

for i, d in enumerate(dispositivos):
    if d["max_input_channels"] > 0:
        dispositivos_entrada.append((i, d))
        ha = sd.query_hostapis(d["hostapi"])
        print("2d")
        print(f"    Canales: {d['max_input_channels']}")
        print(f"    Sample Rate: {d['default_samplerate']} Hz")
        print(f"    Host API: {ha['name']}")
        print()

if not dispositivos_entrada:
    print("❌ NO HAY DISPOSITIVOS DE ENTRADA")
    exit(1)

print(f"✅ ENCONTRADOS {len(dispositivos_entrada)} DISPOSITIVOS DE ENTRADA")

# TEST MULTI-CAPTURA SIMULTÁNEA
print("\n🎯 TEST MULTI-CAPTURA (5 segundos)")
print("-" * 80)

duracion = 5
sr = 16000
resultados = {}

def capturar_dispositivo(idx, nombre, queue_result):
    """Captura audio de un dispositivo específico."""
    try:
        audio_data = sd.rec(int(duracion * sr), samplerate=sr, channels=1, dtype='float32', device=idx)
        sd.wait()

        # Análisis
        volumen_promedio = np.abs(audio_data).mean()
        volumen_max = np.abs(audio_data).max()
        volumen_rms = np.sqrt(np.mean(audio_data ** 2))

        queue_result.put({
            'idx': idx,
            'nombre': nombre,
            'volumen_promedio': volumen_promedio,
            'volumen_max': volumen_max,
            'volumen_rms': volumen_rms,
            'exito': True
        })
    except Exception as e:
        queue_result.put({
            'idx': idx,
            'nombre': nombre,
            'error': str(e),
            'exito': False
        })

# Iniciar capturas simultáneas
threads = []
queue_result = queue.Queue()

for idx, d in dispositivos_entrada:
    nombre = d['name']
    t = threading.Thread(target=capturar_dispositivo, args=(idx, nombre, queue_result))
    threads.append(t)
    t.start()

# Esperar que terminen
for t in threads:
    t.join()

# Recolectar resultados
while not queue_result.empty():
    resultado = queue_result.get()
    idx = resultado['idx']
    resultados[idx] = resultado

# MOSTRAR RESULTADOS
print("\n📊 RESULTADOS DE CAPTURA:")
print("-" * 80)

mejor_volumen = 0
mejor_dispositivo = None

for idx, res in resultados.items():
    print(f"\n🎙️ DISPOSITIVO {idx}: {res['nombre']}")
    if res['exito']:
        vol_prom = res['volumen_promedio']
        vol_max = res['volumen_max']
        vol_rms = res['volumen_rms']

        print(f"    Volumen Promedio: {vol_prom:.6f}")
        print(f"    Volumen Máximo: {vol_max:.6f}")
        print(f"    Volumen RMS: {vol_rms:.6f}")

        if vol_prom > mejor_volumen:
            mejor_volumen = vol_prom
            mejor_dispositivo = idx

        # Diagnóstico
        if vol_prom < 0.001:
            print("    ❌ MUY BAJO — Aumentar volumen en Windows Settings")
        elif vol_prom < 0.01:
            print("    ⚠ BAJO — Considerar aumentar volumen")
        else:
            print("    ✅ BUEN NIVEL")
    else:
        print(f"    ❌ ERROR: {res['error']}")

# RECOMENDACIÓN
print("\n🎯 RECOMENDACIÓN:")
print("-" * 80)

if mejor_dispositivo is not None:
    mejor_info = resultados[mejor_dispositivo]
    print(f"✅ MEJOR DISPOSITIVO: [{mejor_dispositivo}] {mejor_info['nombre']}")
    print(f"    Volumen: {mejor_info['volumen_promedio']:.6f}")
    print("\n💡 Computadora debería usar este dispositivo por defecto")
    print("   Pero para multi-micrófono, necesitamos implementar:")
    print("   - Captura simultánea de todos los dispositivos")
    print("   - Comparación en tiempo real de calidad de audio")
    print("   - Selección automática del mejor canal")
else:
    print("❌ NINGÚN DISPOSITIVO FUNCIONA")
    print("   Revisar configuración de audio en Windows")

# PROPUESTA DE IMPLEMENTACIÓN
print("\n🔧 PROPUESTA PARA MULTI-MICRÓFONO:")
print("-" * 80)
print("""
1. Modificar HiloEscucha para capturar de múltiples dispositivos simultáneamente
2. Usar threading para streams paralelos
3. Comparar volumen/SNR en tiempo real
4. Elegir el dispositivo con mejor calidad para transcribir
5. Fallback automático si un dispositivo falla

VENTAJAS:
- ✅ Mejor detección de voz (el micrófono más cercano gana)
- ✅ Redundancia (si un mic falla, usa otro)
- ✅ Mejor calidad en entornos con múltiples hablantes

DESAFÍOS:
- ⚠ Mayor uso de CPU/memoria
- ⚠ Sincronización de streams
- ⚠ Latencia potencial
""")

print("=" * 80)
print("✓ Diagnóstico multi-micrófono completado")
print("=" * 80)
