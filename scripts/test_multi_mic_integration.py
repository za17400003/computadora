#!/usr/bin/env python3
"""
TEST MULTI-MICROPHONE INTEGRATION — Computadora con HiloEscucha
"""

import sys
import os
import time
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from computadora.voz.escucha import HiloEscucha

class MockConfig:
    """Configuración mock para testing."""
    def obtener(self, key, default=None):
        configs = {
            "escucha.umbral_volumen": 0.01,
            "escucha.frecuencia_muestreo": 16000,
            "escucha.silencio_max_segundos": 1.5,
            "whisper.modelo": "base",
            "whisper.dispositivo": "cpu",
            "multi_mic.min_volume": 0.001,
            "multi_mic.max_volume": 0.8,
            "multi_mic.min_snr": 5.0
        }
        return configs.get(key, default)

def test_multi_mic_integration():
    """Test de integración del sistema multi-micrófono con HiloEscucha."""
    print("=" * 80)
    print("🎙️ TEST INTEGRACIÓN MULTI-MICRÓFONO — HiloEscucha")
    print("=" * 80)

    # Crear configuración mock
    config = MockConfig()

    # Crear HiloEscucha
    print("🔧 Inicializando HiloEscucha con sistema multi-micrófono...")
    hilo_escucha = HiloEscucha(config)

    # Verificar que el sistema multi-micrófono se inicializó
    if hasattr(hilo_escucha, '_multi_mic'):
        print("✅ Sistema multi-micrófono encontrado")
        status = hilo_escucha._multi_mic.get_device_status()
        print(f"   📊 Dispositivos totales: {status['total_devices']}")
        print(f"   🎙️ Dispositivos funcionales: {len(status['devices'])}")
        print(f"   🔄 Streams activos: {status['active_streams']}")
        print(f"   📦 Queue size: {status['queue_size']}")
        print(f"   ▶️  Running: {status['is_running']}")

        if len(status['devices']) == 0:
            print("   ⚠️  ADVERTENCIA: No hay dispositivos funcionales detectados")
            print("   💡 Posibles causas:")
            print("      - Dispositivos ocupados por otra aplicación")
            print("      - Configuración de audio de Windows incorrecta")
            print("      - Drivers de audio problemáticos")
        else:
            for device in status['devices'][:3]:  # Mostrar primeros 3
                print(f"      [{device['index']}] {device['name']} ({device['channels']}ch, {device['sample_rate']}Hz)")
    else:
        print("❌ Sistema multi-micrófono NO encontrado")
        return

    # Test de carga del modelo Whisper
    print("\n🤖 Cargando modelo Whisper...")
    try:
        hilo_escucha._cargar_modelo()
        print("✅ Modelo Whisper cargado correctamente")
    except Exception as e:
        print(f"❌ Error cargando modelo Whisper: {e}")
        return

    # Test de captura (corto)
    print("\n🎯 Test de captura multi-micrófono (5 segundos)...")

    def on_estado_cambio(estado):
        print(f"📡 Estado cambiado: {estado}")

    def on_texto_detectado(texto):
        print(f"🎤 TEXTO DETECTADO: '{texto}'")

    def on_mensaje_sistema(msg):
        print(f"💬 Sistema: {msg}")

    # Conectar señales
    hilo_escucha.estado_cambio.connect(on_estado_cambio)
    hilo_escucha.texto_detectado.connect(on_texto_detectado)
    hilo_escucha.mensaje_sistema.connect(on_mensaje_sistema)

    # Iniciar hilo
    hilo_escucha.start()

    # Esperar un poco para que inicie
    time.sleep(2)

    # Monitorear por 5 segundos
    print("🎧 Escuchando... (habla al micrófono)")
    start_time = time.time()

    try:
        while time.time() - start_time < 5:
            time.sleep(0.5)
            # Mostrar status del sistema multi-mic
            if hasattr(hilo_escucha, '_multi_mic'):
                status = hilo_escucha._multi_mic.get_device_status()
                if status['queue_size'] > 0:
                    print(f"📦 Queue size: {status['queue_size']}")

    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por usuario")

    # Detener
    print("\n🛑 Deteniendo test...")
    hilo_escucha.detener()
    # Usar wait sin timeout para QThread
    if hilo_escucha.isRunning():
        hilo_escucha.wait()

    print("✅ Test completado")
    print("=" * 80)

if __name__ == "__main__":
    test_multi_mic_integration()