#!/usr/bin/env python3
"""
TEST HÍBRIDO AUDIO SYSTEM — Computadora con fallback automático
"""

import sys
import os
import time
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

def test_audio_system():
    """Test del sistema de audio híbrido."""
    print("=" * 80)
    print("🎙️ TEST SISTEMA AUDIO HÍBRIDO — Computadora")
    print("=" * 80)

    # Test 1: Verificar que podemos importar los módulos
    print("\n📦 TEST 1: Importación de módulos")
    try:
        from computadora.voz.multi_microphone import MultiMicrophoneSystem
        print("✅ MultiMicrophoneSystem importado")
    except ImportError as e:
        print(f"❌ Error importando MultiMicrophoneSystem: {e}")
        return

    try:
        from computadora.voz.escucha import HiloEscucha
        print("✅ HiloEscucha importado")
    except ImportError as e:
        print(f"❌ Error importando HiloEscucha: {e}")
        return

    # Test 2: Configuración mock
    print("\n⚙️ TEST 2: Configuración")
    class MockConfig:
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

    config = MockConfig()
    print("✅ Configuración mock creada")

    # Test 3: Sistema multi-micrófono independiente
    print("\n🎙️ TEST 3: Sistema Multi-Micrófono Independiente")
    try:
        multi_mic = MultiMicrophoneSystem(config)
        status = multi_mic.get_device_status()
        print(f"   📊 Dispositivos encontrados: {status['total_devices']}")
        print(f"   ✅ Dispositivos funcionales: {len(status['devices'])}")

        if len(status['devices']) > 0:
            print("   🎯 Multi-micrófono DISPONIBLE")
            for device in status['devices'][:2]:
                print(f"      [{device['index']}] {device['name']}")
        else:
            print("   ⚠️ Multi-micrófono NO disponible (usará single-device)")

    except Exception as e:
        print(f"❌ Error en sistema multi-micrófono: {e}")
        return

    # Test 4: HiloEscucha con sistema híbrido
    print("\n🎧 TEST 4: HiloEscucha con Sistema Híbrido")
    try:
        hilo_escucha = HiloEscucha(config)

        # Verificar inicialización
        if hasattr(hilo_escucha, '_multi_mic') and hilo_escucha._multi_mic:
            multi_status = hilo_escucha._multi_mic.get_device_status()
            use_multi = getattr(hilo_escucha, '_use_multi_mic', False)
            print(f"   📊 Multi-mic inicializado: {multi_status['total_devices']} dispositivos")
            print(f"   🎯 Usará multi-micrófono: {use_multi}")
        else:
            print("   ⚠️ Multi-micrófono no inicializado (fallback a single-device)")

        print("✅ HiloEscucha creado correctamente")

    except Exception as e:
        print(f"❌ Error creando HiloEscucha: {e}")
        return

    # Test 5: Carga del modelo Whisper
    print("\n🤖 TEST 5: Carga del Modelo Whisper")
    try:
        hilo_escucha._cargar_modelo()
        print("✅ Modelo Whisper cargado")
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return

    # Test 6: Simulación breve de escucha
    print("\n🎤 TEST 6: Simulación de Escucha (3 segundos)")
    print("   💡 Habla al micrófono durante los próximos 3 segundos...")

    # Configurar señales para logging
    def on_estado(estado):
        print(f"   📡 Estado: {estado}")

    def on_texto(texto):
        print(f"   🎤 TEXTO: '{texto}'")

    def on_mensaje(msg):
        print(f"   💬 {msg}")

    hilo_escucha.estado_cambio.connect(on_estado)
    hilo_escucha.texto_detectado.connect(on_texto)
    hilo_escucha.mensaje_sistema.connect(on_mensaje)

    # Iniciar
    hilo_escucha.start()
    time.sleep(1)  # Dar tiempo para inicializar

    # Monitorear por 3 segundos
    start_time = time.time()
    while time.time() - start_time < 3:
        time.sleep(0.5)

    # Detener
    print("   🛑 Deteniendo...")
    hilo_escucha.detener()
    if hilo_escucha.isRunning():
        hilo_escucha.wait()

    print("✅ Test completado")

    # Resumen
    print("\n" + "=" * 80)
    print("📋 RESUMEN DEL TEST")
    print("=" * 80)

    if hasattr(hilo_escucha, '_use_multi_mic') and hilo_escucha._use_multi_mic:
        print("🎯 MODO: MULTI-MICRÓFONO")
        print("   ✅ Computadora escuchará en todos los micrófonos simultáneamente")
        print("   ✅ Seleccionará automáticamente el mejor audio")
        print("   ✅ Mejor detección en entornos con múltiples hablantes")
    else:
        print("🎯 MODO: SINGLE-DEVICE")
        print("   ✅ Computadora usará el mejor micrófono disponible")
        print("   ⚠️ No hay multi-micrófono disponible")
        print("   💡 Posible causa: Problemas de compatibilidad con QThread")

    print("\n💡 RECOMENDACIONES:")
    print("   1. Si usas single-device: Asegúrate de que el micrófono esté bien configurado")
    print("   2. Si usas multi-micrófono: Disfruta de mejor detección de voz!")
    print("   3. El sistema es automático — no necesitas cambiar nada")

    print("=" * 80)

if __name__ == "__main__":
    test_audio_system()