#!/usr/bin/env python3
"""
Boot Validation — Ejecuta Computadora y mide FPS durante boot.
Espera 35 segundos para capturar boot + animación inicial.
"""

import sys
import subprocess
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

def run_boot_test():
    """Ejecuta Computadora y captura logs de FPS."""
    
    print("\n" + "="*70)
    print("BOOT VALIDATION — Ejecutando Computadora con medición de FPS")
    print("="*70 + "\n")
    
    print("[TEST] Iniciando Computadora...")
    print("[TEST] Espera: Se cerrará automáticamente tras 35 segundos\n")
    
    # Ejecutar con timeout de 35 segundos
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", "computadora"],
            cwd=str(RAIZ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        start_ts = time.monotonic()
        fps_logs = []
        boot_events = []
        
        # Capturar output durante 35 segundos
        for line in iter(proc.stdout.readline, ''):
            if not line:
                break
            
            elapsed = time.monotonic() - start_ts
            
            # Capturar logs relevantes
            if "Frame rate:" in line:
                fps_logs.append((elapsed, line.strip()))
            if "Boot" in line or "boot" in line or "Boot" in line:
                boot_events.append((elapsed, line.strip()))
            if "escucha" in line.lower() and "cargado" in line.lower():
                boot_events.append((elapsed, line.strip()))
            
            # Parar después de 35 segundos
            if elapsed > 35:
                proc.terminate()
                break
        
        proc.wait(timeout=5)
        
        print(f"\n[REPORT] Boot events (primeros 20 segundos):")
        for ts, msg in boot_events:
            if ts < 20:
                print(f"  [{ts:6.2f}s] {msg[:100]}")
        
        print(f"\n[REPORT] FPS measurements:")
        if fps_logs:
            for ts, msg in fps_logs[:5]:  # Primeros 5 logs de FPS
                print(f"  [{ts:6.2f}s] {msg}")
            print(f"  ... ({len(fps_logs)} total FPS logs)")
        else:
            print("  (No FPS logs captured)")
        
        print("\n[RESULT] Boot test completado")
        if fps_logs:
            print("[OK] ✓ FPS instrumentation funcionando (logs detectados)")
        else:
            print("[WARN] ✗ FPS logs NO capturados (revisar if QTimer se inicia)")
        
    except subprocess.TimeoutExpired:
        proc.kill()
        print("[ERROR] Timeout esperando Computadora")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    run_boot_test()
