#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Candidatos en INGLÉS + otras variaciones
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

candidatos = [
    # Inglés - Matrix/Despierta
    "wake up",
    "Wake up",
    "WAKE UP",
    "wakeup",
    "Wakeup",
    "the matrix",
    "The Matrix",
    "THE MATRIX",
    "matrix",
    "Matrix",
    "MATRIX",
    "follow the white rabbit",
    "Follow the white rabbit",
    "the truth will set you free",
    "The truth will set you free",
    "truth",
    "Truth",
    "TRUTH",
    "freedom",
    "Freedom",
    "FREEDOM",
    "awakening",
    "Awakening",
    "reality",
    "Reality",
    "REALITY",
    
    # Potencial error de transcripción - "ove" podría ser "over"
    "overcome",
    "Overcome",
    "OVERCOME",
    "over",
    "Over",
    "OVER",
    "overtake",
    "Overtake",
    "over the truth",
    "Over the truth",
    
    # Número de día/audio
    "5",
    "cinco",
    "Cinco",
    "CINCO",
    
    # Fecha
    "17042026",
    "04172026",
    "2026",
    
    # Otras palabras clave
    "begin",
    "Begin",
    "BEGIN",
    "restart",
    "Restart",
    "RESTART",
]

print("🔐 PROBANDO CANDIDATOS EN INGLÉS + VARIANTES...\n")

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
print("\n💡 Próximos pasos: Necesitamos información adicional de los audios")
