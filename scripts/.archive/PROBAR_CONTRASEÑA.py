#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar contraseñas basadas en análisis semántico
"""

import os
from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

candidatos = [
    # Palabras clave centrales que aparecen en todos los audios
    "vida",
    "Vida",
    "VIDA",
    "verdad",
    "Verdad",
    "VERDAD",
    "sueño",
    "Sueño",
    "SUEÑO",
    "mundo",
    "Mundo",
    "MUNDO",
    
    # Frases completas
    "vuelve a empezar",
    "Vuelve a empezar",
    "la vida",
    "La vida",
    "LA VIDA",
    "la verdad",
    "La verdad",
    "vivir",
    "Vivir",
    "VIVIR",
    "ver",
    "Ver",
    "VER",
    
    # Variaciones con espacios/sin espacios
    "vidaverdad",
    "verdadvida",
    "sueño vida",
    "Sueño vida",
    
    # Matrix-related (por las referencias)
    "red pill",
    "redpill",
    "blue pill",
    "bluepill",
    "white rabbit",
    "conejo blanco",
    "Conejo blanco",
    
    # Del audio final
    "no quiero ser emperador",
    "No quiero ser emperador",
]

print("🔓 PROBANDO CANDIDATOS...\n")

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
                
                # Extraer contenido
                print("📄 EXTRAYENDO CONTENIDO...\n")
                contenido = ""
                for page_idx, page in enumerate(reader.pages):
                    txt = page.extract_text()
                    if txt:
                        contenido += f"[PÁGINA {page_idx+1}]\n{txt}\n\n"
                
                # Guardar
                with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
                    f.write(contenido)
                
                print(f"{'─'*79}")
                print(contenido)
                print(f"{'─'*79}\n")
                print(f"✅ Contenido guardado: contenido_desencriptado.txt\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:40s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)} candidatos")
