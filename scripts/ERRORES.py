#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar los ERRORES de Whisper (no las correcciones)
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# ERRORES de Whisper (lo incorrecto)
candidatos = [
    # Errores de Whisper directamente
    "debir",
    "Debir",
    "stilla",
    "Stilla",
    "madridera",
    "Madridera",
    "dislumbrar",
    "Dislumbrar",
    "desifral",
    "Desifral",
    "pisa",
    "Pisa",
    "sedos",
    "Sedos",
    "dia",
    "Dia",
    "DIA",
    
    # Combinaciones de errores
    "stilla en la mente",
    "Stilla en la mente",
]

print("🔐 PROBANDO ERRORES DE WHISPER...\n")

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
                print(contenido[:2000])
                if len(contenido) > 2000:
                    print(f"\n[...más contenido guardado...]")
                print(f"\n{'─'*79}\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:30s} → ❌")

print(f"\n❌ Ninguno funcionó")
