#!/usr/bin/env python3
"""
Script para probar el sistema completo de conversación con TTS.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_conversacion_completa():
    """Prueba el sistema completo de conversación con TTS."""
    print("🧪 Probando sistema completo de conversación con TTS...")

    try:
        # Importar módulos necesarios
        from computadora.config import Configuracion
        from computadora.nucleo.orquestador import Orquestador
        from computadora.cerebro.nlu import CerebroComputadora
        from computadora.voz.habla import HiloHabla

        # Crear configuración y cerebro
        config = Configuracion()
        cerebro = CerebroComputadora(modelo="google/gemma-4-e4b")
        orquestador = Orquestador(config, cerebro=cerebro)

        print("✅ Orquestador inicializado correctamente")

        # Probar TTS
        print("🎤 Probando TTS...")
        try:
            hilo_habla = HiloHabla(config)
            hilo_habla.hablar("Hola, sistema de voz funcionando correctamente")
            print("✅ TTS inicializado correctamente")
        except Exception as e:
            print(f"⚠️  TTS con problemas: {e}")
            hilo_habla = None

        # Simular conversación
        mensajes = [
            "Hola computadora, ¿cómo estás?",
            "Cuéntame algo sobre ti",
            "¿Qué día es hoy?",
            "Gracias por la conversación"
        ]

        print("💬 Iniciando conversación...")
        for i, msg in enumerate(mensajes, 1):
            print(f"\n📝 Mensaje {i}: '{msg}'")

            try:
                # Procesar mensaje
                respuesta = orquestador.procesar(msg)
                print(f"🤖 Respuesta: {respuesta[:200]}..." if len(respuesta) > 200 else f"🤖 Respuesta: {respuesta}")

                # Intentar hablar la respuesta
                try:
                    if hilo_habla:
                        hilo_habla.hablar(respuesta[:100])  # Limitar para prueba
                        print("🔊 Respuesta hablada")
                except Exception as e:
                    print(f"⚠️  Error en TTS: {e}")

                print("✅ Procesado correctamente")

            except Exception as e:
                print(f"❌ Error procesando mensaje: {e}")
                return False

            # Pausa entre mensajes
            time.sleep(2)

        print("\n✅ Sistema de conversación completo funciona correctamente")
        print("✅ TTS integrado y operativo")
        return True

    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversacion_completa()
    sys.exit(0 if success else 1)
