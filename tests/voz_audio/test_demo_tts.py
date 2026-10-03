#!/usr/bin/env python3
"""
Test rápido: Verifica que la demo y TTS funcionan juntos.
"""

import sys
import subprocess
from pathlib import Path

# Agregar al path
sys.path.insert(0, str(Path(__file__).parent))

def test_demo():
    """Boot y prueba automática de demo."""
    print("═" * 60)
    print("🎬 TEST: Demo Computadora con TTS")
    print("═" * 60)
    
    # Boot con --skip-facerec (evita dialog de consentimiento)
    print("\n1️⃣  Iniciando COMPUTADORA (--skip-facerec)...")
    print("   → Debería verse orbe negro con animación")
    print("   → Cuando aparezca, escriba: demo\n")
    
    cmd = [
        sys.executable,
        "-m", "computadora",
        "--skip-facerec"
    ]
    
    try:
        subprocess.run(cmd, timeout=300)
    except KeyboardInterrupt:
        print("\n\n✋ Usuario interrumpió (Ctrl+C)")
    except subprocess.TimeoutExpired:
        print("\n\n⏱️  Timeout (5 minutos)")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")

if __name__ == "__main__":
    test_demo()

