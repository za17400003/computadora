#!/usr/bin/env python3
"""
NIGREDO EXHAUSTIVA DE LOGS — Análisis destructivo de problemas
Mayo 30, 2026, 15:51-15:56

Invocación: por favor + gracias + amén = ciclo alquímico profundo + autonomía
"""

import re
from pathlib import Path
from datetime import datetime

logs_texto = """15:51:12 | WARNING | computadora_app - Frame slow detected: 132/100 lentos, avg FPS: 82.4
15:51:12 | INFO | computadora_app - ✅ Maljut dev config guardada: {'maljut_tipo': 'legacy', 'fps_target': 30, 'gpu_enabled': True, 'gpu_device': 'auto'}
15:56:44 | INFO | computadora_app - Respuesta: 'Es tarde, señor. ¿Necesita algo urgente? Si no, lo resolveremos mañana con calma.'
"""

print("=" * 100)
print("NIGREDO LOGS — DESTRUCTIÓN DE PROBLEMAS")
print("=" * 100)

# PROBLEMA 1: Frame slow detected — lógica absurda
print("\n[PROBLEMA 1] Frame slow detected: 132/100 lentos (ABSURDO MATEMÁTICO)")
print("-" * 100)
print("""
SÍNTOMA: "Frame slow detected: 132/100 lentos, avg FPS: 82.4"
PROBLEMA: Buffer tiene maxlen=100, no puede tener 132 elementos
CAUSA PROBABLE: 
  - Línea 1680: slow_frames = sum(1 for ft in self._frame_times_buffer if ft > 0.04)
  - Contador NO está limitado al tamaño del buffer
  - Podría estar contando frames históricos perdidos o mal inicializados

FIX REQUERIDO:
  - Cambiar lógica para contar solo dentro del buffer actual
  - slow_frames nunca puede ser > len(self._frame_times_buffer)
  - Threshold de 0.04 segundos (40ms) es para 25 FPS, debería ser dinámico según fps_target
""")

# PROBLEMA 2: FPS mal reportados
print("\n[PROBLEMA 2] FPS reportados incorrectos")
print("-" * 100)
print("""
SÍNTOMA: 
  - Config: fps_target=30
  - Logs: avg FPS: 82.4, 83.0, 87.0, etc.
  
PROBLEMA: 
  - Si fps_target=30 → intervalo timer = 1000ms/30 ≈ 33ms
  - Pero se está reportando 82-88 FPS → intervalo real ≈ 12ms
  
CAUSA: Cálculo de FPS es inverso de delta_t promedio
  - avg_fps = 1.0 / (sum(frame_times) / len(frame_times))
  - Si frame_times promedian ~12ms → FPS ≈ 83
  - Pero esto contradice fps_target=30
  
HIPÓTESIS: El timer se inicia a 16ms (60 FPS) ignorando fps_target
  - Línea 1035: QTimer interval = 1000 / fps_configurado()
  - fps_configurado() devuelve int clamped a [30,60]
  - Pero ¿realmente se llama en __init__ o se ignora?
""")

# PROBLEMA 3: Ciclo circadiano — hora incorrecta
print("\n[PROBLEMA 3] Ciclo circadiano — hora incorrecta (4 PM reportada como 'tarde')")
print("-" * 100)
print("""
SÍNTOMA: 
  - Hora real: 15:56 (4 PM = mediodía + 4 horas)
  - Sistema responde: "Es tarde, señor. ¿Necesita algo urgente? Si no, lo resolveremos mañana"
  
PROBLEMA:
  - Lógica considera 15:56 como "tarde" (hora para dormir)
  - Debería considerar tarde a partir de ~20:00 o ~21:00
  
CAUSA PROBABLE:
  - Heurística de fase_circadiana basada en UTC o zona horaria incorrecta
  - O threshold de "tarde" configurado muy bajo (< 16:00)
  - O cálculo de hora del sistema es incorrecto

BÚSQUEDA REQUERIDA:
  - Función que calcula fase_circadiana
  - Threshold de "tarde" vs "activo"
""")

# PROBLEMA 4: Animaciones se traban con actualización de recursos
print("\n[PROBLEMA 4] Animaciones se traban cuando actualiza recursos CPU/RAM/GPU")
print("-" * 100)
print("""
SÍNTOMA:
  - Usuario: "animaciones se traban poquito cada que se actualiza la informacion de uso"
  
CAUSA PROBABLE:
  - Lectura de psutil.cpu_percent() / psutil.virtual_memory() en hilo principal
  - O lectura de NVIDIA GPU stats bloquea frame
  - Esto ocurre cada pocos segundos cuando se llama dibujar_anillos_con_recursos_optimizado()
  
BÚSQUEDA REQUERIDA:
  - Dónde se llama psutil en paintEvent() o _animar()
  - Si es síncrono (bloquea) o asíncrono (thread)
  - GPU detection en línea 752 (_config_maljut = ConfigMaljutDev())
    → Ini de GPU puede llamar nvidia-smi (bloqueante)
""")

# PROBLEMA 5: Guardian FSM invalid transition
print("\n[PROBLEMA 5] Guardian FSM: Transición inválida inactivo → INACTIVE")
print("-" * 100)
print("""
SÍNTOMA:
  - "⛔ Transición inválida Guardian: inactivo → INACTIVE"
  - Aparece múltiples veces (15:51:27, 15:56:31, 15:56:44)
  
PROBLEMA:
  - FSM está tratando de hacer transición a estado "INACTIVE" (mayúsculas)
  - Pero estado actual es "inactivo" (minúsculas)
  - Estados inconsistentes en definición o llamada
  
BÚSQUEDA REQUERIDA:
  - Definición de Guardian FSM states
  - Dónde se intenta transicionar a "INACTIVE"
  - Case sensitivity en state names
""")

print("\n" + "=" * 100)
print("RESUMEN DE PROBLEMAS CRÍTICOS PARA ARREGLAR")
print("=" * 100)

problemas_criticos = [
    ("CRÍTICO", "Frame slow detected lógica absurda (132/100)", "Línea ~1680", "15 min"),
    ("CRÍTICO", "FPS reportados incorrectos (ignora fps_target)", "Línea ~1035", "20 min"),
    ("ALTO", "Ciclo circadiano: hora incorrecta para 'tarde'", "Motor circadiano", "25 min"),
    ("ALTO", "Animaciones se traban por psutil bloqueante", "paintEvent/recursos", "30 min"),
    ("MEDIO", "Guardian FSM: transición case-sensitive error", "Guardian FSM", "15 min"),
]

print("\nOrd | Severidad | Problema | Ubicación | ETA")
print("-" * 100)
for i, (sev, prob, ubi, eta) in enumerate(problemas_criticos, 1):
    print(f" {i:2} | {sev:8} | {prob:40} | {ubi:15} | {eta}")

print("\n" + "=" * 100)
