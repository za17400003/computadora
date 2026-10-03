#!/usr/bin/env python3
"""
📹 GUÍA MANUAL + DESCARGADOR YT-DLP

Opción 1 (MANUAL): Copiar transcripciones directamente de YouTube
Opción 2 (AUTOMÁTICO): Usar yt-dlp para descargar

Instrucciones paso a paso para obtener las transcripciones del video
"Esto es el fin" de YouTube.
"""

import sys
import subprocess
from pathlib import Path

print("""
═══════════════════════════════════════════════════════════════════════════════
📹 CÓMO OBTENER TRANSCRIPCIONES DE YOUTUBE MANUALMENTE
═══════════════════════════════════════════════════════════════════════════════

OPCIÓN 1: COPIAR DIRECTAMENTE DE YOUTUBE (100% confiable)
──────────────────────────────────────────────────────────────────────────────

Pasos para cada idioma:

1. Abre YouTube: https://www.youtube.com/watch?v=Apv4cRO0DWo

2. En la esquina inferior derecha, click en el ícono de "..."  (más opciones)

3. Selecciona "Mostrar transcripción" o "Show transcript"

4. A la derecha debería aparecer el panel de transcripción

5. En la transcripción, hay un botón con 3 puntos (⋮) 
   → Click en él y selecciona "Copiar"

6. Abre un editor de texto (Notepad, VSCode, etc.)

7. Pega el contenido

8. Guarda como: transcripcion_es.txt

9. REPITE PARA CADA IDIOMA (5 total):
   - Español (MX) original
   - Alemán
   - Inglés (GB)
   - Japonés
   - Portugués (BR)

💡 PISTA: En YouTube, cambia el idioma de la transcripción en el selector 
   que dice "Español" → otras opciones disponibles

═══════════════════════════════════════════════════════════════════════════════

OPCIÓN 2: DESCARGAR AUTOMÁTICAMENTE CON YT-DLP
──────────────────────────────────────────────────────────────────────────────
""")

# Intentar con yt-dlp
try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False

if HAS_YT_DLP:
    print("✅ yt-dlp está disponible")
    print("\nEjecutando descarga de transcripciones...")
    print("(Esto puede tomar unos momentos)\n")
    
    video_url = "https://www.youtube.com/watch?v=Apv4cRO0DWo"
    output_dir = Path("_transcripciones_youtube")
    output_dir.mkdir(exist_ok=True)
    
    # Comando para descargar subtítulos/captions en todos los idiomas
    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-langs", "es,de,en,ja,pt",
        "--skip-download",
        "-o", str(output_dir / "%(title)s.%(ext)s"),
        video_url
    ]
    
    print(f"Ejecutando: {' '.join(cmd[:3])}...\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Descarga completada!")
            
            # Listar archivos
            archivos = list(output_dir.glob("*"))
            if archivos:
                print(f"\n📁 Archivos descargados ({len(archivos)}):")
                for f in sorted(archivos):
                    size = f.stat().st_size if f.is_file() else "DIR"
                    print(f"   - {f.name}")
                
                print(f"\n📂 Ubicación: {output_dir.absolute()}")
            else:
                print("⚠️ No se encontraron archivos")
        else:
            print(f"❌ Error: {result.stderr[:200]}")
    
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout - operación tomó demasiado tiempo")
    except Exception as e:
        print(f"❌ Error: {e}")

else:
    print("❌ yt-dlp no disponible")
    print("\nInstala con:")
    print("   pip install yt-dlp")

print("""

═══════════════════════════════════════════════════════════════════════════════
📋 PRÓXIMO PASO
═══════════════════════════════════════════════════════════════════════════════

Una vez tengas las transcripciones guardadas, guárdalas en archivos separados:
- transcripcion_es.txt
- transcripcion_de.txt  
- transcripcion_en.txt
- transcripcion_ja.txt
- transcripcion_pt.txt

Después ejecuta el analizador de contraseñas que buscará patrones en las 
transcripciones para encontrar la contraseña del PDF.

═══════════════════════════════════════════════════════════════════════════════
""")
