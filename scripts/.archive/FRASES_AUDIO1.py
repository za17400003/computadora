#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frases clave del AUDIO #1 - análisis de Matrix
"""

from PyPDF2 import PdfReader

pdf_path = "resiste-protected.pdf"

# Frases principales del AUDIO #1 (es claramente la reinterpretación del discurso de Morfeo)
# Basadas en Matrix y la transcripción actual

candidatos = [
    # Del AUDIO #1 - frases clave
    "este video no es lo que piensas",
    "Este video no es lo que piensas",
    "estás aquí porque sabes algo",
    "Estás aquí porque sabes algo",
    "ya no hay vuelta atrás",
    "Ya no hay vuelta atrás",
    "madriguera del conejo",
    "Madriguera del conejo",
    "conejo",
    "Conejo",
    
    # Conceptos Matrix que podrían ser la contraseña
    "the one",
    "theone",
    "el elegido",
    "elegido",
    "Elegido",
    "red pill",
    "redpill",
    "pastilla roja",
    "parabólica",  # en caso de error de transcripción
    
    # Variaciones de "vuelve"
    "vuelve y empieza",
    "Vuelve y empieza",
    "volviéndote",
    "Volviéndote",
    "vuelvea",
    "vuelta",
    "Vuelta",
    
    # Posibles errores en la transcripción que Whisper cometió
    "despierta",  # en lugar de "despertar"
    "Despierta",
    "despierte",
    "Despierte",
    
    # Del patrón "la frase que hemos usado"
    "cambio",
    "Cambio",
    "CAMBIO",
    
    # Frases completas largas que podrían ser contraseña
    "vuelve a empezar desde el inicio",
    "Vuelve a empezar desde el inicio",
    "vuelve al principio",
    "Vuelve al principio",
]

print("🔐 PROBANDO FRASES DE AUDIO #1...\n")

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
    
    print(f"[{i:2d}/{len(candidatos)}] {pwd:50s} → ❌")

print(f"\n❌ Ninguno funcionó")
