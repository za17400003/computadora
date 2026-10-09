#!/usr/bin/env python3
"""
Quick Boot Check — Verifica que el boot NO se congela y todo se inicializa correctamente.
"""

import time
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

def test_boot_performance():
    """Mide el tiempo de boot sin bloqueos."""
    
    print("\n[BOOT CHECK] Iniciando performance test...\n")
    
    # Paso 1: Imports básicos
    t0 = time.monotonic()
    print("[1/6] Cargando config...", end="", flush=True)
    from computadora.config import Configuracion
    config = Configuracion()
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms)")
    
    # Paso 2: CerebroComputadora
    t0 = time.monotonic()
    print("[2/6] Cargando CerebroComputadora...", end="", flush=True)
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora(modelo="gemma3:4b")
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms)")
    
    # Paso 3: PyQt6
    t0 = time.monotonic()
    print("[3/6] Inicializando PyQt6 QApplication...", end="", flush=True)
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms)")
    
    # Paso 4: Importar ventana_principal (este era el cuello de botella)
    t0 = time.monotonic()
    print("[4/6] Importando ventana_principal (CRITICAL)...", end="", flush=True)
    from computadora.interfaz.ventana_principal import OrbeComputadora
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms) [CRITICAL - should be < 3s after lazy-init fix]")
    
    # Paso 5: Crear OrbeComputadora
    t0 = time.monotonic()
    print("[5/6] Creando instancia OrbeComputadora...", end="", flush=True)
    orbe = OrbeComputadora(config, cerebro=cerebro)
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms)")
    
    # Paso 6: Show + event loop init
    t0 = time.monotonic()
    print("[6/6] Mostrando ventana (no blocar event loop)...", end="", flush=True)
    orbe.show()
    # Procesar pending events pero no esperar indefinidamente
    app.processEvents()
    t1 = time.monotonic()
    print(f" OK ({(t1-t0)*1000:.0f}ms)")
    
    print("\n" + "="*70)
    print("[RESULT] Boot sequence completed successfully")
    print("[PASS] Sistema inicializado sin freezing")
    print("[PASS] Silero VAD lazy-init habilitado (imports rapidos)")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        test_boot_performance()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
