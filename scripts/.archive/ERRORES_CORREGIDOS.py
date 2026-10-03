#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probar errores de transcripción CORREGIDOS de Whisper
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Errores identificados + correcciones
candidatos = [
    # Errores corregidos
    "descubrir",
    "Descubrir",
    "espina",
    "Espina",
    "madriguera",
    "Madriguera",
    "vislumbrar",
    "Vislumbrar",
    "descifrar",
    "Descifrar",
    "pista",
    "Pista",
    "sueños",
    "Sueños",
    "odios",
    "Odios",
    "humanidad",
    "Humanidad",
    "la humanidad",
    "La Humanidad",
    
    # RIP como parte de contraseña (mencionado en Audio #5)
    "rip",
    "Rip",
    "RIP",
    "rip vuelve",
    "Rip Vuelve",
    "vuelve rip",
    "Vuelve Rip",
    
    # Con acentos especiales
    "VUELVE A EMPEZAR",
    "Vuelve A Empezar",
    "vuelve a empezar",
    "VUÉLVE A EMPÉZAR",
    
    # Posibles formaciones con "ove" (como dice Audio #5)
    "ove",
    "Ove",
    "OVE",
    "ove a empezar",
    "vuelve ove",
    
    # Si "ove" es inglés "over"
    "over",
    "Over",
    "OVER",
    "over again",
    "Over Again",
]

print("🔐 PROBANDO ERRORES CORREGIDOS + VARIANTES...\n")

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
                    print(f"\n[...más contenido guardado en contenido_desencriptado.txt...]")
                print(f"\n{'─'*79}\n")
                exit(0)
    except:
        pass
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:35s} → ❌")

print(f"\n❌ Ninguno funcionó. Probados: {len(candidatos)}")
print("\n💡 PRÓXIMO PASO: Ver descripción de YouTube (Audio #5 lo menciona explícitamente)")
print("   URL: https://www.youtube.com/watch?v=Apv4cRO0DWo")
