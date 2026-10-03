#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROBAR: ourobórica + variantes + verificar transcripciones
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Candidatos basados en OUROBOROS + lo que dijo el usuario
candidatos = [
    # Ouroboros / Esotérico
    "ourobórica",
    "Ourobórica",
    "OUROBÓRICA",
    "ouroboros",
    "Ouroboros",
    "OUROBOROS",
    "ouroboras",
    "Ouroboras",
    "ourobora",
    "Ourobora",
    "ourobórica vez",
    "Ourobórica Vez",
    
    # Sin tilde
    "ouroborica",
    "Ouroborica",
    "OUROBORICA",
    
    # Variantes
    "ourobó",
    "ourobó rica",
    "la ourobórica",
    "La Ourobórica",
    
    # Si es acrónimo o código
    "OUR",
    "OUROBOROS",
    
    # Combinado con "vuelve"
    "ourobórica vuelve",
    "Ourobórica Vuelve",
    "vuelve ourobórica",
    "Vuelve Ourobórica",
]

print("🔐 PROBANDO CANDIDATOS - OUROBÓRICA (TU PISTA)...\n")

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
                print(contenido[:2000])
                print(f"[...contenido completo guardado en contenido_desencriptado.txt...]\n")
                print(f"{'─'*79}\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:35s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)}")
print("\n💡 INFO: Audio #5 dice 'Empieza con ove' = empieza con V")
print("   'ourobórica' empieza con O, así que si no funciona, la contraseña")
print("   probablemente empieza realmente con V (vuelve a empezar u otra)")
