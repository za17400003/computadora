#!/usr/bin/env python3
"""
📹 EXTRACTOR DE TRANSCRIPCIONES YOUTUBE - AUDIO TRACKS

Video: https://www.youtube.com/watch?v=Apv4cRO0DWo
Título: "Esto es el fin"

PISTAS DE AUDIO (Confirmed by user):
  ✅ Español (MX) original  ← PISTA PRINCIPAL
  - Alemán
  - Inglés (GB)
  - Japonés
  - Portugués (BR)

OBJETIVO: Extraer transcripciones en estos idiomas específicos.
Cada idioma PUEDE contener variaciones del mensaje cifrado.
"""

import sys
import json
import subprocess
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YOUTUBE_API = True
except ImportError:
    HAS_YOUTUBE_API = False

try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False

# Idiomas confirmados en el video
IDIOMAS_TARGET = {
    'es': 'Español (MX) original',
    'de': 'Alemán',
    'en': 'Inglés (GB)',
    'ja': 'Japonés',
    'pt': 'Portugués (BR)',
}

def extraer_video_id(url):
    """Extrae ID del video"""
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def metodo_youtube_api(video_id):
    """Usa youtube-transcript-api para extraer transcripciones"""
    print("\n🔵 MÉTODO: youtube-transcript-api")
    print("="*70)
    
    if not HAS_YOUTUBE_API:
        print("❌ No disponible")
        return {}
    
    transcripciones = {}
    
    try:
        # Intentar obtener cada idioma
        for lang_code, lang_name in IDIOMAS_TARGET.items():
            print(f"\n📥 {lang_name} ({lang_code})...", end=" ", flush=True)
            
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
                texto = " ".join([item['text'] for item in data])
                transcripciones[lang_code] = {
                    "idioma": lang_name,
                    "codigo": lang_code,
                    "texto": texto,
                    "items": data,
                    "longitud": len(texto)
                }
                print(f"✅ ({len(texto)} caracteres)")
            except Exception as e:
                print(f"❌ ({str(e)[:50]})")
    
    except Exception as e:
        print(f"❌ Error general: {e}")
    
    return transcripciones

def metodo_yt_dlp_cli(url):
    """Usa yt-dlp CLI para descargar subtítulos"""
    print("\n🟢 MÉTODO: yt-dlp (CLI)")
    print("="*70)
    
    if not HAS_YT_DLP:
        print("❌ No disponible")
        return {}
    
    transcripciones = {}
    
    try:
        # Crear directorio temporal
        temp_dir = Path("_transcripciones_temp")
        temp_dir.mkdir(exist_ok=True)
        
        # Descargar subtítulos
        print(f"\n📥 Descargando subtítulos con yt-dlp...")
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-langs", ",".join(IDIOMAS_TARGET.keys()),
            "--skip-download",
            "-o", str(temp_dir / "%(title)s.%(ext)s"),
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Descarga completada\n")
            
            # Buscar archivos de subtítulos generados
            vtt_files = list(temp_dir.glob("*.vtt"))
            print(f"   Encontrados {len(vtt_files)} archivos de subtítulos")
            
            for vtt_file in vtt_files:
                print(f"   - {vtt_file.name}")
                
                # Parsear VTT
                try:
                    with open(vtt_file, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    
                    # Extraer solo el texto (sin timestamps)
                    lineas = contenido.split('\n')
                    texto_lineas = []
                    for linea in lineas:
                        # Saltarse header, timestamps y líneas vacías
                        if (linea.strip() and 
                            not linea.startswith('WEBVTT') and
                            '-->' not in linea and
                            not linea.strip().endswith(':0')):
                            texto_lineas.append(linea.strip())
                    
                    texto = " ".join(texto_lineas)
                    
                    # Identificar idioma
                    for lang_code in IDIOMAS_TARGET.keys():
                        if lang_code in vtt_file.name:
                            transcripciones[lang_code] = {
                                "idioma": IDIOMAS_TARGET[lang_code],
                                "codigo": lang_code,
                                "texto": texto,
                                "longitud": len(texto),
                                "archivo": str(vtt_file)
                            }
                            print(f"      ✅ {IDIOMAS_TARGET[lang_code]}: {len(texto)} caracteres")
                            break
                
                except Exception as e:
                    print(f"      ⚠️ Error: {e}")
        
        else:
            print(f"❌ Error: {result.stderr[:200]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return transcripciones

def main():
    video_url = "https://www.youtube.com/watch?v=Apv4cRO0DWo"
    video_id = extraer_video_id(video_url)
    
    print("="*70)
    print("📹 EXTRACTOR DE TRANSCRIPCIONES YOUTUBE")
    print("="*70)
    print(f"\n🎬 Título: Esto es el fin")
    print(f"🆔 Video ID: {video_id}")
    print(f"\n🔊 Pistas de audio confirmadas:")
    for code, name in IDIOMAS_TARGET.items():
        print(f"   [{code}] {name}")
    
    print(f"\n📊 Herramientas disponibles:")
    print(f"   {'✅' if HAS_YOUTUBE_API else '❌'} youtube-transcript-api")
    print(f"   {'✅' if HAS_YT_DLP else '❌'} yt-dlp")
    
    transcripciones = {}
    
    # Intentar Método 1
    if HAS_YOUTUBE_API:
        trans1 = metodo_youtube_api(video_id)
        transcripciones.update(trans1)
    
    # Intentar Método 2
    if HAS_YT_DLP:
        trans2 = metodo_yt_dlp_cli(video_url)
        transcripciones.update(trans2)
    
    # Guardar y mostrar resultados
    if transcripciones:
        output_file = Path("transcripciones_video.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcripciones, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Guardado: {output_file}")
        
        # Mostrar transcripciones
        print("\n" + "="*70)
        print("📝 TRANSCRIPCIONES EXTRAÍDAS")
        print("="*70)
        
        for lang_code in sorted(IDIOMAS_TARGET.keys()):
            if lang_code in transcripciones:
                data = transcripciones[lang_code]
                print(f"\n🗣️  {data['idioma']} ({lang_code})")
                print(f"    {'─'*60}")
                print(f"    {data['texto'][:500]}{'...' if data['longitud'] > 500 else ''}")
        
        print(f"\n✅ Total idiomas extraídos: {len(transcripciones)}")
        
        # Análisis de contraseña por idioma
        print("\n" + "="*70)
        print("🔍 ANÁLISIS DE PISTAS (palabras que empiezan por V)")
        print("="*70)
        
        for lang_code in sorted(IDIOMAS_TARGET.keys()):
            if lang_code in transcripciones:
                texto = transcripciones[lang_code]['texto']
                palabras = texto.split()
                palabras_v = [p for p in palabras if p and p[0].upper() == 'V']
                
                print(f"\n{transcripciones[lang_code]['idioma']}:")
                if palabras_v:
                    print(f"  Palabras con V: {palabras_v[:10]}")
                else:
                    print(f"  No hay palabras que empiezan por V")
        
        return 0
    
    else:
        print("\n❌ No se pudieron extraer transcripciones")
        print("\n📋 Instala herramientas:")
        print("   pip install youtube-transcript-api yt-dlp")
        return 1

if __name__ == "__main__":
    sys.exit(main())
