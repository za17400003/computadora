#!/usr/bin/env python3
"""Verificación rápida pre-boot del sistema Computadora."""

import json
import sys

print("[VERIFICACIÓN PRE-BOOT]")
print()

# 1. Configuración
try:
    from computadora.config import Configuracion
    cfg = Configuracion()
    print("✅ Configuración cargada")
    disp = cfg.obtener("escucha.dispositivo", 1)
    umbral = cfg.obtener("escucha.umbral_volumen", 0.015)
    print(f"   Dispositivo escucha: {disp}")
    print(f"   Umbral volumen: {umbral}")
except Exception as e:
    print(f"❌ Configuración: {e}")
    sys.exit(1)

print()

# 2. Whisper
try:
    import whisper
    print("✅ Whisper disponible")
except ImportError as e:
    print(f"❌ Whisper no disponible: {e}")
    sys.exit(1)

print()

# 3. config.json
try:
    with open('datos/config.json', 'r') as f:
        cfg_json = json.load(f)
    print("✅ config.json existe y es válido")
    disp = cfg_json.get("escucha", {}).get("dispositivo")
    print(f"   Dispositivo en JSON: {disp}")
except FileNotFoundError:
    print("❌ config.json no encontrado")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ config.json inválido: {e}")
    sys.exit(1)

print()
print("✅ Sistema listo para boot")
