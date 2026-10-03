#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar metadatos del video YouTube que el usuario pasó
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Información del video YouTube que pasó
candidatos = [
    # Canal / Creador
    "mateus bolson ruzzarin",
    "Mateus Bolson Ruzzarin",
    "MATEUS BOLSON RUZZARIN",
    "mateus",
    "Mateus",
    "bolson",
    "Bolson",
    "ruzzarin",
    "Ruzzarin",
    
    # Mindshop
    "mindshop",
    "Mindshop",
    "MINDSHOP",
    
    # Fecha
    "13042026",
    "13042026",
    "2026",
    "abril",
    "Abril",
    "13abril",
    "13 abril 2026",
    
    # Suscriptores
    "81800",
    "81.8k",
    "81k",
    
    # Visualizaciones
    "19049",
    "19049views",
    
    # Combinaciones
    "mateus mindshop",
    "Mateus Mindshop",
    "mindshop mateus",
    "ruzzarin mindshop",
    "bolson ruzzarin",
]

print("🔐 PROBANDO METADATOS DEL VIDEO YOUTUBE...\n")

for i, pwd in enumerate(candidatos, 1):
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            if reader.decrypt(pwd):
                print(f"\n{'='*79}")
                print(f"✅✅✅ ¡CONTRASEÑA ENCONTRADA! ✅✅✅")
                print(f"{'='*79}\n")
                print(f"🔑 CONTRASEÑA: '{pwd}'")
                print(f"📊 Intento: #{i}/{len(candidatos)}\n")
                
                # Extraer
                print("📄 EXTRAYENDO CONTENIDO...\n")
                contenido = ""
                for page_idx, page in enumerate(reader.pages):
                    txt = page.extract_text()
                    if txt:
                        contenido += f"[PÁGINA {page_idx+1}]\n{txt}\n\n"
                
                with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                    f.write(contenido)
                
                print(f"{'─'*79}\n")
                print(contenido[:3000])
                if len(contenido) > 3000:
                    print(f"\n[...más contenido guardado...]")
                print(f"\n{'─'*79}\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:35s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)}")
