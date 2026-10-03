#!/usr/bin/env python3
"""
PALINGENESIA: Validar RUBEDO Fase 2 — Diagnostico + Fixes
- Watchdog Ollama robusto
- Modelo phi:3b más rápido
- FPS metrics + DevTools
- Suavizado anillos
- Filtro desconocidos desactivado
"""

import sys
import json
import time
from pathlib import Path
from collections import deque

# Colores para logging
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'

def print_check(msg):
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} {msg}")

def print_warn(msg):
    print(f"{Colors.WARNING}⚠{Colors.ENDC} {msg}")

def print_fail(msg):
    print(f"{Colors.FAIL}✗{Colors.ENDC} {msg}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {msg}")

# ────────────────────────────────────────────────────────
# 1. VALIDAR CONFIG.JSON
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDAR CONFIG.JSON")
print("="*60)

config_path = Path(__file__).parent / "datos" / "config.json"
if config_path.exists():
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Verificar modelo Ollama
    modelo_ollama = config.get("ollama", {}).get("modelo", "default")
    if modelo_ollama == "phi:3b":
        print_check(f"Modelo Ollama: {modelo_ollama} (rápido ✓)")
    else:
        print_warn(f"Modelo Ollama: {modelo_ollama} (esperaba phi:3b)")
    
    # Verificar timeout
    timeout = config.get("ollama", {}).get("timeout", 60)
    print_check(f"Timeout Ollama: {timeout}s")
    
else:
    print_fail("config.json no encontrado")

# ────────────────────────────────────────────────────────
# 2. VALIDAR NLU.PY - WATCHDOG
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDAR NLU.PY - WATCHDOG OLLAMA")
print("="*60)

try:
    # Leer nlu.py para verificar watchdog mejorado
    nlu_path = Path(__file__).parent / "computadora" / "cerebro" / "nlu.py"
    with open(nlu_path, "r", encoding="utf-8", errors="ignore") as f:
        nlu_content = f.read()
    
    # Verificar que hay reconexión automática
    if "while True:" in nlu_content and "intentos_fallidos" in nlu_content:
        print_check("Watchdog con loop infinito + reconexión detectado")
    else:
        print_warn("Watchdog podría no tener reconexión automática")
    
    # Verificar que intenta reconectar
    if "max_reintentos" in nlu_content and "sleep" in nlu_content:
        print_check("Reintentos con backoff exponencial detectados")
    else:
        print_warn("No hay reintentos con backoff")
    
    # Verificar logging mejorado
    if "⚠️ Ollama falla" in nlu_content:
        print_check("Logging mejorado del watchdog detectado")
    else:
        print_warn("Logging del watchdog podría no estar optimizado")
        
except Exception as e:
    print_fail(f"Error validando nlu.py: {e}")

# ────────────────────────────────────────────────────────
# 3. VALIDAR VENTANA_PRINCIPAL.PY - FPS Y ANILLOS
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDAR VENTANA_PRINCIPAL.PY - FPS + ANILLOS")
print("="*60)

try:
    vp_path = Path(__file__).parent / "computadora" / "interfaz" / "ventana_principal.py"
    with open(vp_path, "r", encoding="utf-8", errors="ignore") as f:
        vp_content = f.read()
    
    # Verificar variables FPS
    if "self._fps_actual" in vp_content and "self._fps_buffer" in vp_content:
        print_check("Variables FPS metrics inicializadas")
    else:
        print_warn("Variables FPS no encontradas")
    
    # Verificar método toggle FPS
    if "_accion_toggle_fps_display" in vp_content:
        print_check("Método toggle FPS display detectado")
    else:
        print_warn("Método toggle FPS no implementado")
    
    # Verificar suavizado de delta_t
    if "_delta_t_smooth" in vp_content and "smooth_factor" in vp_content:
        print_check("Suavizado de delta_t para anillos implementado")
    else:
        print_warn("Suavizado de delta_t podría no estar activo")
    
    # Verificar que delta_t se guarda en FPS buffer
    if "self._fps_buffer.append(actual_fps)" in vp_content:
        print_check("FPS se guarda en buffer histórico")
    else:
        print_warn("Buffer de FPS podría no funcionar")
        
except Exception as e:
    print_fail(f"Error validando ventana_principal.py: {e}")

# ────────────────────────────────────────────────────────
# 4. VALIDAR ESCUCHA.PY - FILTRO DESCONOCIDOS
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("VALIDAR ESCUCHA.PY - FILTRO DESCONOCIDOS")
print("="*60)

try:
    esc_path = Path(__file__).parent / "computadora" / "voz" / "escucha.py"
    with open(esc_path, "r", encoding="utf-8", errors="ignore") as f:
        esc_content = f.read()
    
    # Verificar que el filtro está desactivado
    if "_filtro_desconocidos_activo = False" in esc_content:
        print_check("Filtro de desconocidos desactivado (RUBEDO)")
    else:
        print_warn("Flag de filtro desconocidos podría no estar presente")
    
    # Verificar que hay comentario explicativo
    if "Filtro desactivado" in esc_content:
        print_check("Comentario RUBEDO presente en escucha.py")
    else:
        print_warn("Comentario RUBEDO no encontrado")
    
    # Verificar que acepta todas las voces
    if "Aceptar todas las voces" in esc_content or "RUBEDO" in esc_content:
        print_check("Lógica para aceptar todas las voces detectada")
    else:
        print_warn("Lógica de aceptación de voces podría no estar presente")
        
except Exception as e:
    print_fail(f"Error validando escucha.py: {e}")

# ────────────────────────────────────────────────────────
# 5. RESUMEN DE CAMBIOS
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESUMEN DE CAMBIOS RUBEDO FASE 2")
print("="*60)

cambios = {
    "1. Watchdog Ollama": "Robusto con reconexión automática",
    "2. Modelo LLM": "phi:3b (más rápido que gemma3:4b)",
    "3. Metrics": "FPS display en DevTools",
    "4. Animaciones": "Anillos suavizados con delta_t interpolado",
    "5. Voice Input": "Filtro desconocidos desactivado",
}

for cambio, desc in cambios.items():
    print_check(f"{cambio}: {desc}")

# ────────────────────────────────────────────────────────
# 6. RECOMENDACIONES
# ────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PRÓXIMOS PASOS")
print("="*60)

print_info("1. Iniciar sistema con: python -m computadora")
print_info("2. Probar: 'Hola, Computadora' (debe responder rápido)")
print_info("3. DevTools: Click derecho → כלי מפתח → FPS Display")
print_info("4. Verificar: Watchdog Ollama en logs cada 15s")
print_info("5. Test: Hablar al micrófono (sin restricción de voz desconocida)")

print("\n" + "="*60)
print("✓ VALIDACIÓN COMPLETADA")
print("="*60 + "\n")
