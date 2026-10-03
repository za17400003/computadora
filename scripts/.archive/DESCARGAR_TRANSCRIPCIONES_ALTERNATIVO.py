#!/usr/bin/env python3
"""
📹 DESCARGADOR DE TRANSCRIPCIONES YOUTUBE - MÉTODO ALTERNATIVO

Usa requests para acceder directamente a la API de YouTube
"""

import sys
import json
import re
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def extraer_video_id(url):
    """Extrae ID del video"""
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

def obtener_transcripcion_youtube(video_id, lang='es'):
    """Obtiene transcripción de YouTube directamente"""
    
    if not HAS_REQUESTS:
        return None
    
    try:
        # URL base para obtener la configuración inicial del video
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Obtener página del video
        print(f"   📥 Obteniendo página del video...", end=" ", flush=True)
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print("❌ (No se pudo acceder)")
            return None
        
        # Buscar js inicial data
        print(f"✓", end=" ", flush=True)
        
        # Buscar captions en la página
        match = re.search(r'"captionTracks":\s*(\[.*?\])', response.text)
        if not match:
            print("❌ (Sin captions)")
            return None
        
        print(f"✓ Parseando...")
        
        captions_data = json.loads(match.group(1))
        
        # Buscar idioma solicitado
        caption_url = None
        for caption in captions_data:
            if caption.get('languageCode', '').startswith(lang):
                caption_url = caption.get('baseUrl')
                break
        
        if not caption_url:
            print(f"   ❌ Idioma {lang} no encontrado")
            return None
        
        # Descargar subtítulos
        print(f"   📥 Descargando subtítulos en {lang}...", end=" ", flush=True)
        captions = requests.get(caption_url, headers=headers, timeout=10)
        
        if captions.status_code != 200:
            print("❌")
            return None
        
        # Parsear XML de subtítulos
        print(f"✓")
        texto = re.sub(r'<[^>]+>', '', captions.text)  # Eliminar tags XML
        texto = json.loads('{"text":"' + texto + '"}')['text'] if '{"' in texto else texto
        
        return texto
    
    except Exception as e:
        print(f"❌ ({str(e)[:40]})")
        return None

def main():
    video_url = "https://www.youtube.com/watch?v=Apv4cRO0DWo"
    video_id = extraer_video_id(video_url)
    
    idiomas = {
        'es': 'Español (MX) original',
        'de': 'Alemán',
        'en': 'Inglés (GB)',
        'ja': 'Japonés',
        'pt': 'Portugués (BR)',
    }
    
    print("="*70)
    print("📹 DESCARGADOR DE TRANSCRIPCIONES YOUTUBE - MÉTODO ALTERNATIVO")
    print("="*70)
    print(f"\n🎬 Video: {video_url}")
    print(f"🆔 ID: {video_id}")
    print(f"\n{'✅' if HAS_REQUESTS else '❌'} requests disponible\n")
    
    if not HAS_REQUESTS:
        print("Instalando: pip install requests")
        sys.exit(1)
    
    print("="*70)
    print("DESCARGANDO TRANSCRIPCIONES...")
    print("="*70 + "\n")
    
    transcripciones = {}
    
    for lang_code, lang_name in idiomas.items():
        print(f"🗣️  {lang_name} ({lang_code})...", end=" ", flush=True)
        
        texto = obtener_transcripcion_youtube(video_id, lang_code)
        
        if texto:
            transcripciones[lang_code] = {
                "idioma": lang_name,
                "codigo": lang_code,
                "texto": texto,
                "longitud": len(texto)
            }
            print(f"✅ ({len(texto)} caracteres)")
        else:
            print(f"❌")
    
    if not transcripciones:
        print("\n❌ No se pudieron descargar transcripciones")
        print("\n💡 Alternativa: Abre el video en YouTube y copia manual la transcripción:")
        print("   1. Abre el video")
        print("   2. Click en 3 puntos (...) > Mostrar transcripción")
        print("   3. Copia el texto y guárdalo")
        return 1
    
    # Guardar
    output_file = Path("transcripciones_youtube_completas.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(transcripciones, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Guardado: {output_file}\n")
    
    # Mostrar
    print("="*70)
    print("📝 TRANSCRIPCIONES")
    print("="*70)
    
    for lang_code in sorted(idiomas.keys()):
        if lang_code in transcripciones:
            data = transcripciones[lang_code]
            print(f"\n{'━'*70}")
            print(f"🗣️  {data['idioma']} ({lang_code})")
            print(f"{'━'*70}")
            print(data['texto'][:600])
            print(f"\n... ({data['longitud']} caracteres totales)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
