#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intenta obtener descripción del video YouTube directamente
y también prueba el acceso al Google Drive PDF
"""

import urllib.request
import urllib.error
from urllib.parse import quote
import json

# YouTube video ID
video_id = "Apv4cRO0DWo"

# Intento 1: YouTube Data API (sin key - probablemente falle)
print("🔍 Intentando obtener descripción del video YouTube...\n")

# Intento 2: Web scraping directo (puede estar bloqueado)
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    url = f"https://www.youtube.com/watch?v={video_id}"
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=5) as response:
        html = response.read().decode('utf-8')
        
        # Buscar descripción en JSON embebido
        if '"description":' in html:
            print("✓ Descripción encontrada en HTML")
            start = html.find('"description":')
            end = html.find('"', start + 15)
            desc = html[start + 15:end]
            print(f"\n{desc}\n")
        else:
            print("✗ No se encontró descripción en HTML")
            
except urllib.error.URLError as e:
    print(f"✗ Error de conexión: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

# Intento 3: Información del Google Drive PDF
print("\n" + "="*79)
print("ℹ️  Google Drive PDF:")
print("="*79)
print("URL: https://drive.google.com/file/d/1pgnRs166GVA6NEzwpz_b7sPO4N_8O08y/view")
print("\nPara descargar sin abrir en navegador:")
print("https://drive.google.com/uc?export=download&id=1pgnRs166GVA6NEzwpz_b7sPO4N_8O08y")
print("\nNOTA: El archivo bajado es: resiste-protected.pdf")
print("      Ya está en tu sistema local.")
