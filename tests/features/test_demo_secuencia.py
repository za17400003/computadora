#!/usr/bin/env python
"""Test de secuencia demo: simula la coreografía de Maljut con múltiples pasos."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtCore import QCoreApplication, QTimer
from loguru import logger
from computadora.voz.habla import HiloHabla

logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | {message}")

class ConfigMock:
    def obtener(self, key, default=None):
        defaults = {
            "voz.tts_voz": "es-MX-JorgeNeural",
            "voz.tts_motor": "edge-tts",
        }
        return defaults.get(key, default)

def test_demo_dos_pasos():
    """Test: simula dos pasos de la demo con espera entre ellos."""
    print("\n" + "="*60)
    print("TEST: Demo Maljut - Dos Pasos Secuenciales")
    print("="*60)
    
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    
    config = ConfigMock()
    habla = HiloHabla(config)
    
    # Solo 2 pasos para simplificar el test
    textos = [
        "Observe. Esto es el Maljut.",
        "Despertando. La luz crece.",
    ]
    
    stats = {
        "cola_vacia_count": 0,
        "pasos_enviados": 0,
        "inicio": time.time(),
    }
    
    def on_cola_vacia():
        stats["cola_vacia_count"] += 1
        idx = stats["cola_vacia_count"] - 1
        print("  [+] Signal cola_vacia #{} recibida".format(stats["cola_vacia_count"]))
        
        if stats["cola_vacia_count"] < len(textos):
            print("      (Enviando siguiente paso en 500ms)")
            # Enviar siguiente paso en 500ms
            QTimer.singleShot(500, lambda: enviar_paso())
        else:
            print("  [*] DEMO COMPLETADA: {} pasos ejecutados".format(stats["cola_vacia_count"]))
            QTimer.singleShot(100, app.quit)
    
    def enviar_paso():
        if stats["pasos_enviados"] < len(textos):
            idx = stats["pasos_enviados"]
            stats["pasos_enviados"] += 1
            print("[>>] Enviando paso {}/{}: '{}'".format(
                stats["pasos_enviados"], len(textos), textos[idx][:40]))
            habla.hablar(textos[idx])
    
    habla.cola_vacia.connect(on_cola_vacia)
    habla.start()
    
    print("[*] Iniciando secuencia de prueba...")
    enviar_paso()
    
    # Timeout de seguridad (40 segundos)
    def timeout():
        print("\n[X] TIMEOUT: Prueba tardó demasiado")
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(timeout)
    timer.setSingleShot(True)
    timer.start(40000)
    
    app.exec()
    
    timer.stop()
    habla.detener()
    habla.wait(5000)
    
    # Resultados
    elapsed = time.time() - stats["inicio"]
    print("\n" + "="*60)
    print("RESULTADOS:")
    print("  Pasos enviados: {}".format(stats["pasos_enviados"]))
    print("  Signals cola_vacia: {}".format(stats["cola_vacia_count"]))
    print("  Tiempo total: {:.1f}s".format(elapsed))
    print("="*60)
    
    success = (stats["pasos_enviados"] == len(textos) and 
               stats["cola_vacia_count"] == len(textos))
    
    if success:
        print("\n[OK] TEST PASADO: Secuencia de demo funcionando correctamente\n")
    else:
        print("\n[FAIL] TEST FALLIDO: No se completaron todos los pasos\n")
    
    return success

if __name__ == "__main__":
    try:
        result = test_demo_dos_pasos()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Error en test: {e}", exc_info=True)
        sys.exit(1)



