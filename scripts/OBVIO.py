#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar lo más OBVIO - visible a simple vista
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Lo más simple:
candidatos = [
    # Nombre del PDF
    "resiste",
    "Resiste",
    "RESISTE",
    "resiste-protected",
    "resiste protected",
    
    # RIP (mencionado en los audios)
    "rip",
    "Rip",
    "RIP",
    
    # Combinaciones obvias
    "voltea",
    "Voltea",
    "vuelta a empezar",
    "Vuelta a empezar",
    "vuelta",
    "Vuelta",
    
    # Video ID
    "Apv4cRO0DWo",
    "apv4crO0DWo",
    
    # Duración en segundos (si todos duran "lo mismo")
    "60",
    "300",
    "333",
    
    # Palabras clave del contexto
    "despertar",
    "Despertar",
    "secreto",
    "Secreto",
    "video",
    "Video",
    
    # Del título
    "mindshop",
    "Mindshop",
    
    # Posibilidad: las instrucciones de idioma
    "portugues",
    "Portugues",
    "PORTUGUES",
    "portugu",
    
    # Literalmente lo que dice el audio
    "la frase que hemos usado",
    "La frase que hemos usado",
    
    # Tal vez "RIP" + "Vuelve"
    "ripvuelve",
    "Ripvuelve",
    "rip vuelve",
    "Rip Vuelve",
]

print("🔐 PROBANDO LO OBVIO - VISIBLE A SIMPLE VISTA...\n")

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
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:35s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)}")
