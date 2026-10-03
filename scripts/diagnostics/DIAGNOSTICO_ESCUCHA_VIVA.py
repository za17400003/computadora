#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIGREDO: Diagnóstico de escucha en vivo
Verifica si:
1. HiloEscucha inicia correctamente
2. Whisper carga sin errores
3. Micrófono captura audio
4. Wake word se detecta
5. Logs aparecen en consola
"""

import sys
import time
import logging
from pathlib import Path

# Setup logging con colores
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_config():
    """Verificar config.json"""
    logger.info("=" * 60)
    logger.info("TEST 1: Verificar config.json")
    logger.info("=" * 60)
    
    config_path = Path(__file__).parent / "datos" / "config.json"
    if not config_path.exists():
        logger.error(f"❌ config.json NO existe en {config_path}")
        return False
    
    import json
    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        logger.info(f"✅ config.json cargado correctamente")
        logger.info(f"   - Dispositivo escucha: {config_data.get('escucha', {}).get('dispositivo', 'N/A')}")
        logger.info(f"   - Modelo Whisper: {config_data.get('whisper', {}).get('modelo', 'N/A')}")
        return True
    except Exception as e:
        logger.error(f"❌ Error cargando config.json: {e}")
        return False

def test_whisper_import():
    """Verificar si Whisper se importa"""
    logger.info("=" * 60)
    logger.info("TEST 2: Verificar importación de Whisper")
    logger.info("=" * 60)
    
    try:
        logger.info("Importando whisper...")
        import whisper
        logger.info(f"✅ whisper importado: {whisper.__file__}")
        return True
    except ImportError as e:
        logger.error(f"❌ No se pudo importar whisper: {e}")
        logger.error("   Intenta: pip install openai-whisper")
        return False

def test_microphone():
    """Verificar dispositivos de micrófono disponibles"""
    logger.info("=" * 60)
    logger.info("TEST 3: Verificar dispositivos de micrófono")
    logger.info("=" * 60)
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        logger.info(f"✅ {len(input_devices)} dispositivo(s) de entrada detectado(s):")
        for i, d in enumerate(input_devices):
            logger.info(f"   [{i}] {d['name']} ({d['max_input_channels']} canales)")
        
        return len(input_devices) > 0
    except Exception as e:
        logger.error(f"❌ Error enumerando dispositivos: {e}")
        return False

def test_audio_capture():
    """Probar captura de audio simple"""
    logger.info("=" * 60)
    logger.info("TEST 4: Probar captura de audio (5 segundos)")
    logger.info("=" * 60)
    logger.info("🎤 Hablando en el micrófono ahora...")
    
    try:
        import sounddevice as sd
        import numpy as np
        
        fs = 16000
        duration = 5
        
        logger.info(f"Capturando {duration}s a {fs}Hz...")
        audio = sd.rec(int(fs * duration), samplerate=fs, channels=1, dtype=np.float32)
        sd.wait()
        
        # Calcular volumen
        volumen = np.max(np.abs(audio))
        logger.info(f"✅ Audio capturado: {len(audio)} muestras, volumen máx: {volumen:.4f}")
        
        if volumen < 0.01:
            logger.warning(f"⚠️  Volumen muy bajo ({volumen:.4f}). ¿Micrófono conectado/activado?")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error capturando audio: {e}")
        return False

def test_hilo_escucha_init():
    """Probar inicialización de HiloEscucha"""
    logger.info("=" * 60)
    logger.info("TEST 5: Probar inicialización de HiloEscucha")
    logger.info("=" * 60)
    
    try:
        from computadora.config import Configuracion
        from computadora.voz.escucha import HiloEscucha
        
        logger.info("Inicializando Configuracion...")
        config = Configuracion()
        
        logger.info("Creando HiloEscucha...")
        hilo = HiloEscucha(config)
        
        logger.info(f"✅ HiloEscucha creado correctamente")
        logger.info(f"   - _modelo: {hilo._modelo}")
        logger.info(f"   - _activo: {hilo._activo}")
        logger.info(f"   - _pausado: {hilo._pausado}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando HiloEscucha: {e}")
        logger.exception("Stack trace:")
        return False

def test_wake_word_detection():
    """Probar detección de wake word"""
    logger.info("=" * 60)
    logger.info("TEST 6: Probar detección de wake word")
    logger.info("=" * 60)
    
    try:
        from computadora.config import Configuracion
        from computadora.voz.escucha import HiloEscucha
        
        config = Configuracion()
        hilo = HiloEscucha(config)
        
        test_texts = [
            "computadora como estás",
            "computa, ¿qué hora es?",
            "golum dime un chiste",
            "hola amigo",  # sin wake word
            "COMPUTADORA AYUDA",
        ]
        
        logger.info("Probando detección de wake word:")
        for texto in test_texts:
            resultado = hilo._check_wake_word_fuzzy(texto)
            marca = "✅" if resultado else "❌"
            logger.info(f"   {marca} '{texto}' → {resultado}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error probando wake word: {e}")
        logger.exception("Stack trace:")
        return False

def main():
    logger.info("\n" + "=" * 60)
    logger.info("🔍 DIAGNÓSTICO DE ESCUCHA EN VIVO")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("config.json", test_config),
        ("Whisper import", test_whisper_import),
        ("Micrófono", test_microphone),
        ("Captura de audio", test_audio_capture),
        ("HiloEscucha init", test_hilo_escucha_init),
        ("Wake word detection", test_wake_word_detection),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            logger.error(f"❌ Test '{name}' falló con excepción: {e}")
            logger.exception("Stack trace:")
            results[name] = False
        
        logger.info("")
    
    # Resumen
    logger.info("=" * 60)
    logger.info("📊 RESUMEN")
    logger.info("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"\n✅ Pasados: {passed}/{total}\n")
    
    logger.info("\n" + "=" * 60)
    
    if passed == total:
        logger.info("🎉 Todos los tests pasaron. Sistema debería estar funcionando.")
    else:
        logger.error(f"⚠️  {total - passed} test(s) fallaron. Revisa arriba para detalles.")
    
    logger.info("=" * 60 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
