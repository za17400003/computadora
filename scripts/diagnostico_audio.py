#!/usr/bin/env python3
"""
DIAGNÓSTICO AUDIO — Computadora Mudo
Prueba: HiloEscucha, Whisper, micrófono, wake word
"""

import sys
import time
from pathlib import Path

# Agregar proyecto al path
proyecto_root = Path(__file__).resolve().parent
sys.path.insert(0, str(proyecto_root))

print("=" * 70)
print("🔊 DIAGNÓSTICO: SISTEMA DE AUDIO COMPUTADORA")
print("=" * 70)

# TEST 1: ¿Se puede importar Whisper?
print("\n[TEST 1] Whisper (ASR - Automatic Speech Recognition)")
print("-" * 70)
try:
    import whisper
    print("✓ Whisper importado correctamente")
    print(f"  Ubicación: {whisper.__file__}")
    
    # Probar modelo tiny (rápido)
    print("  Intentando cargar modelo 'base' (esto toma ~50MB)...")
    try:
        import torch
        dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Dispositivo: {dispositivo}")
        
        # NO CARGAMOS realmente para ahorrar tiempo
        print("  ✓ Whisper está disponible para cargar (skipping actual load para ahorrar tiempo)")
    except Exception as e:
        print(f"  ⚠ Error al verificar dispositivo: {e}")
except ImportError as e:
    print(f"❌ ERROR: Whisper NO instalado: {e}")
    print("  FIX: pip install openai-whisper")
    sys.exit(1)

# TEST 2: ¿Se puede acceder a micrófono?
print("\n[TEST 2] Dispositivo de Micrófono (Sounddevice)")
print("-" * 70)
try:
    import sounddevice as sd
    print("✓ sounddevice importado correctamente")
    
    # Listar dispositivos
    print("\n  Dispositivos de audio disponibles:")
    info = sd.query_devices()
    
    default_input = sd.default.device[0]
    default_output = sd.default.device[1]
    
    print(f"\n  INPUT (micrófono):")
    try:
        input_info = sd.query_devices(default_input)
        print(f"    ID: {default_input}")
        print(f"    Nombre: {input_info['name']}")
        print(f"    Canales: {input_info['max_input_channels']}")
        print(f"    Frecuencia: {input_info['default_samplerate']} Hz")
        
        if input_info['max_input_channels'] == 0:
            print("    ❌ ERROR: No hay canales de entrada (micrófono no disponible)")
        else:
            print("    ✓ OK")
    except Exception as e:
        print(f"    ⚠ Error al queryar: {e}")
    
    print(f"\n  OUTPUT (parlante):")
    try:
        output_info = sd.query_devices(default_output)
        print(f"    ID: {default_output}")
        print(f"    Nombre: {output_info['name']}")
        print(f"    Canales: {output_info['max_output_channels']}")
        
        if output_info['max_output_channels'] == 0:
            print("    ❌ ERROR: No hay canales de salida")
        else:
            print("    ✓ OK")
    except Exception as e:
        print(f"    ⚠ Error al queryar: {e}")
        
except ImportError as e:
    print(f"❌ ERROR: sounddevice NO instalado: {e}")
    print("  FIX: pip install sounddevice")
    sys.exit(1)

# TEST 3: edge-tts (para respuestas de voz)
print("\n[TEST 3] Text-to-Speech (edge-tts)")
print("-" * 70)
try:
    import edge_tts
    print("✓ edge-tts importado correctamente")
    print("  ✓ TTS disponible para respuestas de voz")
except ImportError as e:
    print(f"❌ ERROR: edge-tts NO instalado: {e}")
    print("  FIX: pip install edge-tts")

# TEST 4: ¿Computadora config está bien?
print("\n[TEST 4] Configuración Computadora")
print("-" * 70)
try:
    from computadora.utilidades.config import Config
    config = Config()
    
    print("✓ Configuración cargada")
    
    # Wake word
    wake_word = config.obtener("escucha.wake_word", "computadora")
    print(f"  Wake word: '{wake_word}'")
    
    # Whisper config
    modelo = config.obtener("whisper.modelo", "base")
    dispositivo = config.obtener("whisper.dispositivo", "auto")
    print(f"  Whisper: modelo='{modelo}', dispositivo='{dispositivo}'")
    
    # Umbral de volumen
    umbral = config.obtener("escucha.umbral_volumen", 0.015)
    print(f"  Umbral de volumen: {umbral}")
    
except Exception as e:
    print(f"❌ ERROR: No se pudo cargar configuración: {e}")

# TEST 5: ¿Puede iniciar HiloEscucha?
print("\n[TEST 5] HiloEscucha Thread")
print("-" * 70)
try:
    from computadora.voz.escucha import HiloEscucha
    from computadora.utilidades.config import Config
    
    config = Config()
    hilo = HiloEscucha(config)
    print("✓ HiloEscucha creado exitosamente")
    print(f"  Activo: {hilo._activo}")
    print(f"  Wake variants: {len(hilo._wake_variants)}")
    
    # NO iniciamos el thread para no bloquear el diagnóstico
    print("  (Thread NO iniciado — skipping para no bloquear diagnóstico)")
    
except Exception as e:
    print(f"❌ ERROR: No se pudo crear HiloEscucha: {e}")
    import traceback
    traceback.print_exc()

# TEST 6: ¿Ollama responde?
print("\n[TEST 6] Ollama (Backend LLM)")
print("-" * 70)
try:
    import requests
    response = requests.get("http://localhost:1234/v1/models", timeout=5)
    if response.status_code == 200:
        modelos = response.json().get("data", [])
        print(f"✓ Ollama conectado")
        print(f"  Modelos cargados: {len(modelos)}")
        if modelos:
            for m in modelos[:3]:
                print(f"    - {m.get('id', 'unknown')}")
    else:
        print(f"⚠ Ollama respondió con HTTP {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Ollama NO disponible en http://localhost:1234")
    print("  FIX: Inicia Ollama (debe estar corriendo en background)")
except Exception as e:
    print(f"⚠ Error al conectar Ollama: {e}")

# TEST 7: ¿Detecta voz?
print("\n[TEST 7] Test de Micrófono (3 segundos)")
print("-" * 70)
try:
    import sounddevice as sd
    import numpy as np
    
    print("  Escuchando durante 3 segundos...")
    duracion = 3
    sr = 16000
    
    audio_data = sd.rec(int(duracion * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    
    volumen_promedio = np.abs(audio_data).mean()
    volumen_max = np.abs(audio_data).max()
    
    umbral_default = 0.015
    
    print(f"  ✓ Audio capturado")
    print(f"    Volumen promedio: {volumen_promedio:.6f}")
    print(f"    Volumen máximo: {volumen_max:.6f}")
    print(f"    Umbral predeterminado: {umbral_default:.6f}")
    
    if volumen_promedio > umbral_default:
        print(f"    ✓ Se detectó voz/sonido (volumen > umbral)")
    else:
        print(f"    ⚠ Volumen muy bajo (volumen < umbral)")
        print(f"      → Aumenta volumen del micrófono en Windows Settings")
        print(f"      → O ajusta escucha.umbral_volumen en config.json")
        
except Exception as e:
    print(f"⚠ Error en test de micrófono: {e}")

# RESUMEN
print("\n" + "=" * 70)
print("📋 RESUMEN DIAGNÓSTICO")
print("=" * 70)

print("""
Si TODO está en ✓:
  → Computadora debería estar escuchando
  → Verifica que HiloEscucha.start() se llama en ventana_principal.py
  → Busca "escuchando" en logs

Si hay ⚠ o ❌:
  → Sigue las recomendaciones de FIX arriba
  → Instala dependencias faltantes
  → Verifica micrófono en Windows Settings
  → Verifica que Ollama está corriendo
  
Comandos útiles:
  - Ver logs: tail -f logs/computadora.log (Linux/Mac)
  - Ver logs: Get-Content logs/computadora.log -Tail 50 -Wait (PowerShell)
  - Verificar Whisper: python -c "import whisper; print(whisper.__file__)"
  - Iniciar Ollama: (debe estar en PATH o ejecutable)
""")

print("=" * 70)
print("✓ Diagnóstico completado")
print("=" * 70)
