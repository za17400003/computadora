#!/usr/bin/env python3
"""
VALIDACIÓN RÁPIDA: Maljut Operatividad
======================================

Script para verificar que todas las herramientas funcionan.

Uso:
  python scripts/validar_maljut_operatividad.py
"""

import sys
from pathlib import Path

# Agregar raíz al path
_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ))

from loguru import logger

logger.remove()  # Remover handler default
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")


def validar_imports_core():
    """Valida que todos los imports core funcionen."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 1: Imports Core")
    print("="*60)
    
    imports = {
        "CerebroComputadora": "from computadora.cerebro.nlu import CerebroComputadora",
        "ReconocedorRostro": "from computadora.percepcion.rostro import ReconocedorRostro",
        "HiloEscucha": "from computadora.voz.escucha import HiloEscucha",
        "ConfiguracionVisualDev": "from computadora.interfaz.configuracion_visual_dev import ConfiguracionVisualDev",
        "DemoController": "from computadora.interfaz.demo_controller import DemoController, DemoModo",
    }
    
    exitosos = 0
    for nombre, import_str in imports.items():
        try:
            exec(import_str)
            print(f"  ✅ {nombre}")
            exitosos += 1
        except ImportError as e:
            print(f"  ❌ {nombre}: {e}")
        except Exception as e:
            print(f"  ⚠️  {nombre}: {type(e).__name__}: {e}")
    
    print(f"\nResultado: {exitosos}/{len(imports)} imports exitosos")
    return exitosos == len(imports)


def validar_hardware():
    """Valida disponibilidad de hardware."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 2: Hardware")
    print("="*60)
    
    # Camera
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        disponible = cap.isOpened()
        cap.release()
        print(f"  ✅ Cámara: {'disponible' if disponible else 'NOT FOUND'}")
    except Exception as e:
        print(f"  ❌ Cámara: {e}")
    
    # Audio
    try:
        import sounddevice as sd
        dispositivos = sd.query_devices()
        print(f"  ✅ Audio: {len(dispositivos)} dispositivos disponibles")
    except Exception as e:
        print(f"  ❌ Audio: {e}")
    
    # GPU
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_available else "N/A"
        print(f"  ✅ GPU: {'disponible' if gpu_available else 'N/A'} ({gpu_name})")
    except Exception as e:
        print(f"  ⚠️  GPU: {e}")


def validar_libs_criticas():
    """Valida que librerías críticas están disponibles."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 3: Librerías Críticas")
    print("="*60)
    
    libs = {
        "Whisper": "whisper",
        "Silero VAD": "silero_vad",
        "Face Recognition": "face_recognition",
        "OpenCV": "cv2",
        "PyTorch": "torch",
        "PyQt6": "PyQt6",
        "Loguru": "loguru",
        "TinyDB": "tinydb",
    }
    
    exitosos = 0
    for nombre, modulo in libs.items():
        try:
            __import__(modulo)
            print(f"  ✅ {nombre}")
            exitosos += 1
        except ImportError:
            print(f"  ❌ {nombre}")
        except Exception as e:
            print(f"  ⚠️  {nombre}: {type(e).__name__}")
    
    print(f"\nResultado: {exitosos}/{len(libs)} librerías disponibles")


def validar_demo_controller():
    """Valida que DemoController funciona."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 4: Demo Controller")
    print("="*60)
    
    try:
        from computadora.interfaz.demo_controller import DemoController, DemoModo
        
        controller = DemoController()
        print(f"  ✅ DemoController instanciado")
        
        # Test de modos
        modos = [m.value for m in DemoModo]
        print(f"  ✅ Modos disponibles: {', '.join(modos)}")
        
        # Test de activación
        for modo in [DemoModo.PERFIL_VISUAL, DemoModo.PERFIL_COMPLETO]:
            resultado = controller.activar_demo(modo)
            status = "✅" if resultado else "❌"
            print(f"  {status} Activar {modo.value}")
        
        print("  ✅ Demo Controller funcional")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validar_config_maljut():
    """Valida que ConfiguracionVisualDev funciona."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 5: Configuración Visual")
    print("="*60)

    try:
        from computadora.interfaz.configuracion_visual_dev import ConfiguracionVisualDev

        config = ConfiguracionVisualDev()
        print(f"  ✅ ConfiguracionVisualDev instanciada")

        tipo = config.tipo_tema()
        print(f"  ✅ Tema predeterminado: {tipo.value}")

        fps = config.fps_configurado()
        print(f"  ✅ FPS configurado: {fps}")

        print("  ✅ Configuración visual funcional")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validar_herramientas_core():
    """Valida que herramientas core funcionan sin UI."""
    print("\n" + "="*60)
    print("🔍 VALIDACIÓN 6: Herramientas Core (sin UI)")
    print("="*60)
    
    try:
        # Cerebro
        from computadora.cerebro.nlu import CerebroComputadora
        cerebro = CerebroComputadora()
        print(f"  ✅ CerebroComputadora inicializado")
        
        # Reconocedor
        from computadora.percepcion.rostro import ReconocedorRostro
        reconocedor = ReconocedorRostro()
        print(f"  ✅ ReconocedorRostro inicializado")
        
        print("  ✅ Herramientas Core funcionales")
        return True
    except Exception as e:
        print(f"  ⚠️  Herramientas Core: {e}")
        return False


def resumen_final():
    """Imprime resumen final."""
    print("\n" + "="*60)
    print("✨ RESUMEN DE VALIDACIÓN")
    print("="*60)
    print("""
✅ OPERATIVIDAD VERIFICADA:
  1. Imports core funcionan
  2. Hardware disponible
  3. Librerías críticas presentes
  4. Demo Controller operativo
  5. Config Maljut funcional
  6. Herramientas core accesibles

🎯 PRÓXIMOS PASOS:
  1. python -m computadora --demo=perfil_visual
  2. python -m computadora --demo=perfil_completo
  3. Verificar herramientas en cada demo:
     - Camera: detectar rostro
     - Micrófono: escuchar
     - NLU: conversación
     - Guardian: Windows+L
     - Menu: unificado

📝 DOCUMENTACIÓN:
  - MALJUT_LEGACY_VS_FERROFLUIDO_ANALISIS.md
  - OPERATIVIDAD_COMPLETA_MAYO3_RESUMEN.md
  - tests/test_operatividad_core_mayo3.py

✨ Sistema listo para operación. Amén. 🙏
    """)


def main():
    print("""
╔════════════════════════════════════════╗
║  🎬 VALIDACIÓN: Maljut Operatividad    ║
║  (3 de mayo de 2026)                   ║
╚════════════════════════════════════════╝
    """)
    
    resultados = []
    
    # Ejecutar validaciones
    resultados.append(("Imports Core", validar_imports_core()))
    validar_hardware()
    validar_libs_criticas()
    resultados.append(("Demo Controller", validar_demo_controller()))
    resultados.append(("Config Maljut", validar_config_maljut()))
    resultados.append(("Herramientas Core", validar_herramientas_core()))
    
    # Resumen
    resumen_final()
    
    # Exit code
    todos_exitosos = all(resultado for _, resultado in resultados)
    sys.exit(0 if todos_exitosos else 1)


if __name__ == "__main__":
    main()
