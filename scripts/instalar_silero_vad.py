#!/usr/bin/env python3
"""
INSTALADOR ROBUSTO SILERO VAD — Arregla "WinError 127"

Problema: pip install silero-vad falla con "WinError 127: No se encontró el proceso"
Causa: Faltan dependencias de ONNX Runtime o bibliotecas de sistema
Solución: Instalar onnx-runtime primero, luego silero-vad
"""

import subprocess
import sys
import importlib
from pathlib import Path

def run_command(cmd, description):
    """Ejecuta comando y reporta resultado."""
    print(f"\n▶ {description}")
    print(f"  Comando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        print(f"✓ {description} — OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} — FALLÓ")
        print(f"   Error: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {description} — TIMEOUT (>5 min)")
        return False
    except Exception as e:
        print(f"❌ {description} — EXCEPCIÓN: {e}")
        return False

def check_module(module_name):
    """Verifica si módulo está disponible."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

print("=" * 80)
print("🔧 INSTALADOR SILERO VAD — Arreglar 'WinError 127'")
print("=" * 80)

# PASO 1: Verificar Python
print("\n[PASO 1] Verificar Python")
print("-" * 80)
print(f"Python: {sys.version}")
print(f"Ejecutable: {sys.executable}")

# PASO 2: Instalar dependencias base
print("\n[PASO 2] Instalar dependencias base (pip upgrade)")
print("-" * 80)
run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            "Actualizar pip/setuptools/wheel")

# PASO 3: Instalar ONNX Runtime (la causa principal del error)
print("\n[PASO 3] Instalar ONNX Runtime")
print("-" * 80)

if check_module('onnxruntime'):
    print("✓ onnxruntime ya instalado")
else:
    print("⚠ onnxruntime NO encontrado, instalando...")
    # Intentar instalación específica para Windows
    success = run_command(
        [sys.executable, "-m", "pip", "install", "--prefer-binary", "--upgrade", "onnxruntime"],
        "Instalar onnxruntime"
    )
    if not success:
        print("  Intentando alternativa (onnxruntime-gpu)...")
        run_command(
            [sys.executable, "-m", "pip", "install", "--prefer-binary", "onnxruntime"],
            "Fallback: onnxruntime"
        )

# PASO 4: Instalar PyTorch (si no está)
print("\n[PASO 4] Instalar PyTorch (si no está)")
print("-" * 80)

try:
    import torch
    print(f"✓ PyTorch ya instalado: {torch.__version__}")
except ImportError:
    print("⚠ PyTorch NO encontrado, instalando...")
    run_command(
        [sys.executable, "-m", "pip", "install", "--prefer-binary", "torch", "torchaudio"],
        "Instalar PyTorch + torchaudio"
    )

# PASO 5: Instalar Silero VAD
print("\n[PASO 5] Instalar Silero VAD")
print("-" * 80)

if check_module('silero_vad'):
    print("✓ silero_vad ya instalado")
else:
    print("⚠ silero_vad NO encontrado, instalando...")
    success = run_command(
        [sys.executable, "-m", "pip", "install", "--prefer-binary", "--upgrade", "silero-vad"],
        "Instalar silero-vad"
    )
    
    if not success:
        print("  Intentando instalación alternativa...")
        run_command(
            [sys.executable, "-m", "pip", "install", "silero-vad", "--no-cache-dir"],
            "Fallback: silero-vad (sin cache)"
        )

# PASO 6: Instalar dependencias de audio
print("\n[PASO 6] Instalar dependencias de audio")
print("-" * 80)

audio_deps = [
    ('scipy', 'scipy'),
    ('librosa', 'librosa'),
]

for module, pkg in audio_deps:
    if check_module(module):
        print(f"✓ {pkg} ya instalado")
    else:
        print(f"⚠ {pkg} NO encontrado, instalando...")
        run_command(
            [sys.executable, "-m", "pip", "install", "--prefer-binary", pkg],
            f"Instalar {pkg}"
        )

# PASO 7: Verificación final
print("\n[PASO 7] Verificación Final")
print("-" * 80)

verification_results = {
    'onnxruntime': False,
    'silero_vad': False,
    'torch': False,
    'scipy': False,
}

for module in verification_results:
    verification_results[module] = check_module(module)
    status = "✓" if verification_results[module] else "❌"
    print(f"{status} {module}")

# PASO 8: Prueba real
print("\n[PASO 8] Prueba Real de Silero VAD")
print("-" * 80)

if verification_results['silero_vad']:
    try:
        from silero_vad import load_silero_vad
        print("  Intentando cargar modelo Silero VAD...")
        model = load_silero_vad()
        print("✓ Silero VAD modelo cargado correctamente")
        print("✓ ÉXITO: Silero VAD está funcionando")
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        print("   Este es el error 'WinError 127' — necesitas investigar más")
else:
    print("❌ Silero VAD no se instaló correctamente")

# RESUMEN
print("\n" + "=" * 80)
print("📊 RESUMEN")
print("-" * 80)

all_ok = all(verification_results.values())

if all_ok:
    print("✅ ÉXITO: Todas las dependencias están instaladas")
    print("")
    print("PRÓXIMOS PASOS:")
    print("1. Cierra y abre una terminal nueva")
    print("2. Ejecuta: computadora_start.bat")
    print("3. Silero VAD debería estar disponible ahora")
else:
    print("⚠️ FALLO: Faltan dependencias")
    print("")
    print("PRÓXIMOS PASOS:")
    print("1. Revisa errores arriba")
    print("2. Si dice 'WinError 127' en silero-vad, necesitas:")
    print("   - Instalar Visual C++ Redistributable (si en Windows)")
    print("   - O usar Python 3.10+ (no 3.8)")
    print("3. Ejecuta este script de nuevo")
    print("")
    print("ALTERNATIVA:")
    print("- Si sigue fallando, usa micrófono USB externo")
    print("- VAD es solo para optimización, no es crítico")

print("=" * 80)
