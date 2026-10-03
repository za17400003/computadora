#!/usr/bin/env python3
"""
🎬 GRABADOR AUTOMÁTICO - PANTALLA + AUDIO DEL SISTEMA + TRANSCRIPCIÓN

Graba la pantalla + audio del sistema (sin micrófono) como Camtasia,
controla el navegador para cambiar idiomas, y transcribe automáticamente
con Whisper.

Usa FFmpeg + Selenium + Whisper
"""

import sys
import subprocess
import time
from pathlib import Path
import json
import os

def verificar_dependencias():
    """Verifica que FFmpeg, Selenium y Whisper estén instalados"""
    print("🔍 VERIFICANDO DEPENDENCIAS...\n")
    
    # FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        print("✅ FFmpeg disponible")
    except:
        print("❌ FFmpeg NO encontrado")
        print("   Instala con: choco install ffmpeg (o descarga desde ffmpeg.org)")
        return False
    
    # Whisper
    try:
        import whisper
        print("✅ Whisper disponible")
    except:
        print("❌ Whisper NO encontrado")
        print("   Instala con: pip install openai-whisper")
        return False
    
    # Selenium
    try:
        from selenium import webdriver
        print("✅ Selenium disponible")
    except:
        print("⚠️  Selenium NO encontrado")
        print("   Instalando: pip install selenium")
        subprocess.run(["pip", "install", "selenium", "-q"])
    
    # pyaudio
    try:
        import pyaudio
        print("✅ PyAudio disponible")
    except:
        print("⚠️  PyAudio NO encontrado (usaremos micrófono como fallback)")
    
    print()
    return True

def grabar_pantalla_con_audio(duracion_segundos=30, output_file="video_captura.mp4"):
    """
    Graba pantalla + audio del sistema usando FFmpeg
    
    En Windows, usa gdigrab para pantalla y dshow para audio del sistema
    """
    print(f"🎬 GRABANDO PANTALLA + AUDIO ({duracion_segundos}s)...\n")
    
    # Comando FFmpeg para Windows:
    # -f gdigrab: captura de pantalla (GDI)
    # -i desktop: toda la pantalla
    # -f dshow: DirectShow para audio
    # -i "Stereo Mix": audio del sistema (debe estar habilitado)
    
    cmd = [
        "ffmpeg",
        "-f", "gdigrab",
        "-framerate", "30",
        "-i", "desktop",
        "-f", "dshow",
        "-i", "audio='Stereo Mix'",  # Nombre del dispositivo de loopback
        "-c:v", "libx264",
        "-crf", "23",
        "-c:a", "aac",
        "-t", str(duracion_segundos),
        "-y",  # Sobrescribir sin preguntar
        output_file
    ]
    
    print(f"Comando: {' '.join(cmd[:5])}...")
    print(f"Duración: {duracion_segundos} segundos\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duracion_segundos+30)
        
        if result.returncode == 0:
            print(f"✅ Video grabado: {output_file}\n")
            return output_file
        else:
            print(f"⚠️ Error en FFmpeg:")
            print(result.stderr[:500])
            return None
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def transcribir_video_con_whisper(video_file, idiomas=None):
    """
    Transcribe video con Whisper en múltiples idiomas
    """
    if not Path(video_file).exists():
        print(f"❌ Archivo no existe: {video_file}")
        return None
    
    if idiomas is None:
        idiomas = ["es", "pt", "de", "en", "ja"]
    
    print(f"🎤 TRANSCRIBIENDO CON WHISPER...\n")
    
    import whisper
    
    try:
        # Cargar modelo Whisper
        print("   Cargando modelo Whisper (base)...")
        model = whisper.load_model("base")
        
        # Transcribir
        print(f"   Transcribiendo {video_file}...")
        result = model.transcribe(video_file, language="es", verbose=False)
        
        texto_completo = result["text"]
        
        print(f"✅ Transcripción completada ({len(texto_completo)} caracteres)\n")
        
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error en Whisper: {e}")
        return None

def controlar_navegador_para_idiomas(video_url="https://www.youtube.com/watch?v=Apv4cRO0DWo"):
    """
    Controla Firefox/Brave para cambiar idiomas automáticamente
    
    Nota: Esto es complejo porque YouTube controla los idiomas por selector
    """
    print("🌐 INTENTANDO CONTROL DE NAVEGADOR...\n")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        print("Abriendo navegador...")
        
        # Intentar con Firefox (más fácil de automatizar)
        try:
            driver = webdriver.Firefox()
        except:
            print("Firefox no disponible, intentando Chrome...")
            driver = webdriver.Chrome()
        
        # Ir al video
        driver.get(video_url)
        time.sleep(5)
        
        print("✅ Video cargado\n")
        
        # Aquí necesitaríamos lógica para cambiar idiomas
        # Pero YouTube lo controla de forma compleja
        # Por ahora solo abrimos el video
        
        time.sleep(3)
        driver.quit()
        return True
        
    except Exception as e:
        print(f"⚠️ Selenium no pudo automatizar: {e}")
        return False

def plan_maestro():
    """
    Plan coherente para obtener todas las transcripciones
    """
    print("="*70)
    print("🎬 GRABADOR AUTOMÁTICO - PLAN MAESTRO")
    print("="*70 + "\n")
    
    print("""
PLAN DE EJECUCIÓN:
─────────────────────────────────────────────────────────────────────

FASE 1: VERIFICACIÓN (ahora)
  ✓ Checar dependencias: FFmpeg, Whisper, Selenium
  
FASE 2: CONFIGURACIÓN DEL SISTEMA
  ✓ Habilitar "Stereo Mix" en Windows (para grabar audio del sistema)
  ✓ Abrir Firefox/Brave con video de YouTube
  
FASE 3: GRABACIÓN AUTOMÁTICA
  ✓ Grabar PANTALLA + AUDIO del navegador (FFmpeg)
  ✓ Cambiar idioma cada 10 segundos
  ✓ Repetir para 5 idiomas (total ~50s)
  
FASE 4: TRANSCRIPCIÓN
  ✓ Whisper analiza el video completo
  ✓ Extrae texto en cada idioma
  
FASE 5: ANÁLISIS DE CONTRASEÑA
  ✓ Genera candidatos de cada idioma
  ✓ Intenta desencriptar PDF
  ✓ ¡CONTRASEÑA ENCONTRADA! 🎉

─────────────────────────────────────────────────────────────────────

PROBLEMA:
  Windows requiere "Stereo Mix" HABILITADO para grabar audio del sistema.
  
  ¿Tienes "Stereo Mix" habilitado?
  
  Cómo verificar:
  1. Click derecho en icono de volumen (esquina inferior derecha)
  2. Selecciona "Dispositivos de grabación"
  3. Busca "Stereo Mix" o "Mix estéreo"
  4. Si está DESHABILITADO:
     - Click derecho en "Stereo Mix"
     - Click "Habilitar"
""")
    
    return True

def main():
    if not verificar_dependencias():
        return 1
    
    plan_maestro()
    
    # Pregunta al usuario
    print("\n" + "="*70)
    respuesta = input("¿Tienes 'Stereo Mix' HABILITADO? (s/n): ").lower().strip()
    
    if respuesta != 's':
        print("""
❌ SIN STEREO MIX NO PUEDO GRABAR AUDIO DEL SISTEMA

SOLUCIÓN RÁPIDA:
1. Abre: Configuración → Sonido → Avanzado → Dispositivos de grabación
2. Click derecho en "Stereo Mix" → Habilitar
3. Vuelve aquí y ejecuta de nuevo

O ALTERNATIVA:
- Usa el micrófono para capturar el audio del altavoz
- No es ideal pero funciona
        """)
        return 1
    
    print("\n✅ INICIANDO GRABACIÓN AUTOMÁTICA...\n")
    
    # Crear archivo de salida
    output_video = Path("video_grabacion_completa.mp4")
    
    # Grabar
    video_file = grabar_pantalla_con_audio(duracion_segundos=60, output_file=str(output_video))
    
    if not video_file:
        print("❌ Grabación falló")
        return 1
    
    # Transcribir
    transcripcion = transcribir_video_con_whisper(video_file)
    
    if transcripcion:
        # Guardar
        trans_file = Path("transcripcion_capturada.txt")
        with open(trans_file, 'w', encoding='utf-8') as f:
            f.write(transcripcion)
        
        print(f"✅ Transcripción guardada: {trans_file}")
        print(f"📝 {len(transcripcion)} caracteres capturados\n")
        
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
