#!/usr/bin/env python
"""Test rápido de TTS: verifica que habla.py genera y reproduce audio sin bloquear."""

import sys
import time
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtCore import QCoreApplication, QTimer
from loguru import logger
from computadora.voz.habla import HiloHabla

# Setup logs
logger.remove()
logger.add(sys.stderr, level="DEBUG", format="<level>{level: <8}</level> | {message}")

def test_habla_basico():
    """Test básico: crear hilo, hablar, esperar cola_vacia."""
    print("\n" + "="*60)
    print("TEST: HiloHabla TTS Básico")
    print("="*60)
    
    app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    
    # Mock config
    class ConfigMock:
        def obtener(self, key, default=None):
            defaults = {
                "voz.tts_voz": "es-MX-JorgeNeural",
                "voz.tts_motor": "edge-tts",
            }
            return defaults.get(key, default)
    
    config = ConfigMock()
    habla = HiloHabla(config)
    
    # Track signals
    signals = {
        "habla_iniciada": 0,
        "habla_terminada": 0,
        "cola_vacia": 0,
    }
    
    def on_habla_iniciada():
        signals["habla_iniciada"] += 1
        print("✓ Señal: habla_iniciada")
    
    def on_habla_terminada():
        signals["habla_terminada"] += 1
        print("✓ Señal: habla_terminada")
    
    def on_cola_vacia():
        signals["cola_vacia"] += 1
        print("✓ Señal: cola_vacia")
        # Detener app
        app.quit()
    
    # Conectar signals
    habla.habla_iniciada.connect(on_habla_iniciada)
    habla.habla_terminada.connect(on_habla_terminada)
    habla.cola_vacia.connect(on_cola_vacia)
    
    # Iniciar hilo
    habla.start()
    print("\n✓ Hilo iniciado")
    
    # Enviar texto corto
    texto = "Hola. Este es un test de síntesis de voz."
    print(f"\n➤ Enviando texto: '{texto}'")
    habla.hablar(texto)
    
    # Timeout de seguridad (30 segundos)
    def timeout():
        print("\n✗ TIMEOUT: Demo tardó más de 30 segundos")
        app.quit()
    
    timer = QTimer()
    timer.timeout.connect(timeout)
    timer.start(30000)
    
    # Ejecutar app event loop
    print("\n➤ Esperando a que TTS termine...")
    app.exec()
    
    timer.stop()
    habla.detener()
    habla.wait(5000)
    
    # Resultados
    print("\n" + "="*60)
    print("RESULTADOS:")
    print(f"  habla_iniciada: {signals['habla_iniciada']} (esperado: 1)")
    print(f"  habla_terminada: {signals['habla_terminada']} (esperado: 1)")
    print(f"  cola_vacia: {signals['cola_vacia']} (esperado: 1)")
    print("="*60)
    
    success = all(v == 1 for v in signals.values())
    if success:
        print("\n✅ TEST PASÓ: TTS funcionando correctamente\n")
    else:
        print("\n❌ TEST FALLÓ: Alguna señal no se emitió\n")
    
    return success

if __name__ == "__main__":
    try:
        result = test_habla_basico()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Error en test: {e}", exc_info=True)
        sys.exit(1)

