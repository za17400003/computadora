#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Candidatos basados en "El Gran Dictador" de Chaplin + análisis final
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

candidatos = [
    # Gran Dictador / Chaplin
    "dictador",
    "Dictador",
    "DICTADOR",
    "gran dictador",
    "Gran Dictador",
    "GRAN DICTADOR",
    "el gran dictador",
    "El Gran Dictador",
    "chaplin",
    "Chaplin",
    "CHAPLIN",
    "la humanidad",
    "La Humanidad",
    "humanidad",
    "Humanidad",
    
    # Posibles errores de transcripción
    "no es un día",
    "No es un día",
    "donde",
    "Donde",
    "donde",
    
    # De todas las transcripciones - último mensaje
    "llegaste al final",
    "Llegaste al final",
    
    # Temas centrales combinados
    "vivir", 
    "Vivir",
    "vivir la felicidad",
    "Vivir la felicidad",
    
    # Frase de AUDIO #5 - comienzo
    "no quiero",
    "No quiero",
    "NO QUIERO",
    
    # Centro del tema
    "quiero ayudar",
    "Quiero ayudar",
    "quiero ayudar a todos",
    "Quiero ayudar a todos",
    
    # Variaciones
    "vencer",
    "Vencer",
    "vincular",
    "Vincular",
    "vivencia",
    "Vivencia",
]

print("🔐 PROBANDO CANDIDATOS (Gran Dictador + Análisis Final)...\n")

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
                
                print(f"{'─'*79}")
                print(contenido)
                print(f"{'─'*79}\n")
                print(f"✅ Guardado: contenido_desencriptado.txt\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:45s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)}")
