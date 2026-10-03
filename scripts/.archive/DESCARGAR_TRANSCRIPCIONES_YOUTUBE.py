#!/usr/bin/env python3
"""
📹 DESCARGADOR DE TRANSCRIPCIONES YOUTUBE - DIRECTO Y FIDEDIGNO

Video: https://www.youtube.com/watch?v=Apv4cRO0DWo
Método: youtube-transcript-api (acceso directo a la API de YouTube)
"""

import sys
import json
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_API = True
except ImportError:
    HAS_API = False
    print("❌ youtube-transcript-api no disponible")
    print("   pip install youtube-transcript-api")
    sys.exit(1)

def extraer_video_id(url):
    """Extrae ID del video"""
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def main():
    video_url = "https://www.youtube.com/watch?v=Apv4cRO0DWo"
    video_id = extraer_video_id(video_url)
    
    # Idiomas confirmados
    idiomas = {
        'es': 'Español (MX) original',
        'de': 'Alemán',
        'en': 'Inglés (GB)',
        'ja': 'Japonés',
        'pt': 'Portugués (BR)',
    }
    
    print("="*70)
    print("📹 DESCARGADOR DE TRANSCRIPCIONES YOUTUBE - FIDEDIGNO")
    print("="*70)
    print(f"\n🎬 Video: {video_url}")
    print(f"🆔 ID: {video_id}")
    print(f"\n🔊 Idiomas a descargar:")
    for code, name in idiomas.items():
        print(f"   [{code}] {name}")
    
    print("\n" + "="*70)
    print("DESCARGANDO TRANSCRIPCIONES...")
    print("="*70 + "\n")
    
    transcripciones = {}
    
    for lang_code, lang_name in idiomas.items():
        print(f"📥 {lang_name} ({lang_code})...", end=" ", flush=True)
        
        try:
            # Descargar transcripción directa de YouTube
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang_code])
            
            # Extraer texto
            texto_completo = " ".join([item['text'] for item in transcript_data])
            
            transcripciones[lang_code] = {
                "idioma": lang_name,
                "codigo": lang_code,
                "texto_completo": texto_completo,
                "items": transcript_data,
                "longitud": len(texto_completo),
                "numero_items": len(transcript_data)
            }
            
            print(f"✅ ({len(transcript_data)} líneas, {len(texto_completo)} caracteres)")
        
        except Exception as e:
            print(f"❌ Error: {str(e)[:60]}")
    
    if not transcripciones:
        print("\n❌ No se pudieron descargar transcripciones")
        return 1
    
    # Guardar en JSON
    output_file = Path("transcripciones_youtube_fidedignas.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transcripciones, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Guardado: {output_file}")
    
    # Mostrar transcripciones
    print("\n" + "="*70)
    print("📝 TRANSCRIPCIONES COMPLETAS")
    print("="*70)
    
    for lang_code in sorted(idiomas.keys()):
        if lang_code in transcripciones:
            data = transcripciones[lang_code]
            print(f"\n{'='*70}")
            print(f"🗣️  {data['idioma']} ({lang_code})")
            print(f"{'='*70}")
            print(data['texto_completo'])
            print(f"\n[{data['numero_items']} líneas, {data['longitud']} caracteres]")
    
    # Análisis de pistas
    print("\n" + "="*70)
    print("🔍 ANÁLISIS DE PISTAS - PALABRAS QUE EMPIEZAN POR V")
    print("="*70)
    
    pistas_v = {}
    
    for lang_code in sorted(idiomas.keys()):
        if lang_code in transcripciones:
            texto = transcripciones[lang_code]['texto_completo']
            palabras = texto.split()
            
            # Palabras que empiezan por V
            palabras_v = [p.strip('.,;:!?¿"\'') for p in palabras if p and p[0].upper() == 'V']
            
            # Eliminar duplicados pero mantener orden
            palabras_v_unicas = []
            seen = set()
            for p in palabras_v:
                if p.lower() not in seen:
                    palabras_v_unicas.append(p)
                    seen.add(p.lower())
            
            pistas_v[lang_code] = palabras_v_unicas
            
            print(f"\n{transcripciones[lang_code]['idioma']} ({lang_code}):")
            if palabras_v_unicas:
                print(f"  {palabras_v_unicas}")
            else:
                print(f"  [Sin palabras que empiezan por V]")
    
    # Guardar pistas
    pistas_file = Path("pistas_contraseña_v.json")
    with open(pistas_file, 'w', encoding='utf-8') as f:
        json.dump(pistas_v, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Pistas guardadas en: {pistas_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
