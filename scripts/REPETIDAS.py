#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar palabras REPETIDAS en los audios y dentro de correcciones
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Palabras que aparecen REPETIDAS en los audios:
candidatos = [
    # Palabras que aparecen en MÚLTIPLES audios
    "vuelve a empezar",
    "Vuelve a empezar",
    "VUELVE A EMPEZAR",
    
    "cambia la pista",
    "Cambia la pista",
    "CAMBIA LA PISTA",
    
    "desde el principio",
    "Desde el principio",
    "DESDE EL PRINCIPIO",
    
    "desde",
    "Desde",
    "DESDE",
    
    "principio",
    "Principio",
    "PRINCIPIO",
    
    "pista",
    "Pista",
    "PISTA",
    
    # Mis correcciones (dentro de corchetes):
    "descubrir",
    "Descubrir",
    "astilla",
    "Astilla",
    "madriguera",
    "Madriguera",
    "vislumbrar",
    "Vislumbrar",
    "descifrar",
    "Descifrar",
    "pista",
    "Pista",
    
    # Más correcciones
    "portugues",
    "Portugues",
    "video",
    "Video",
    
    # Palabras clave de estructura
    "ultima",
    "Ultima",
    "final",
    "Final",
    "seccion",
    "Seccion",
    "SECCION",
    
    # Si "RIP" es palabra
    "rip",
    "Rip",
    "RIP",
]

print("🔐 PROBANDO PALABRAS REPETIDAS + CORRECCIONES...\n")

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
