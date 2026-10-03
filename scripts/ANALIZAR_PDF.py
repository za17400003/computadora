#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba alternativa - revisar propiedades del PDF y métodos de descifrado
"""

from PyPDF2 import PdfReader
import os

pdf_path = "resiste-protected.pdf"

print("📋 ANALIZANDO PDF...\n")
print(f"Archivo: {pdf_path}")
print(f"Tamaño: {os.path.getsize(pdf_path)} bytes\n")

reader = PdfReader(pdf_path)

print(f"¿Es encriptado? {reader.is_encrypted}")

if reader.is_encrypted:
    print("\n🔐 PDF ENCRIPTADO - intentando descifrar con contraseña vacía...")
    
    try:
        resultado = reader.decrypt("")
        if resultado:
            print("✅ Desencriptado con contraseña vacía!")
        else:
            print("❌ Contraseña vacía no funcionó")
            print("\nLeyendo metadatos sin descifrar...")
            print("Se requiere contraseña correcta para acceder al contenido")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("\n✅ PDF NO ENCRIPTADO")

print(f"\nIntentando acceder al número de páginas...")
try:
    num_pages = len(reader.pages)
    print(f"Número de páginas: {num_pages}")
except Exception as e:
    print(f"No se puede acceder (requiere descifrado): {e}")

if reader.is_encrypted:
    print("\n🔐 PDF ENCRIPTADO")
    print("Intentando decrypt() sin contraseña...")
    
    try:
        resultado = reader.decrypt("")
        print(f"Resultado decrypt(''): {resultado}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nIntentando acceder a pages sin contraseña...")
    try:
        paginas = len(reader.pages)
        print(f"Número de páginas: {paginas}")
        
        print("\nIntentando extraer texto de página 0...")
        texto = reader.pages[0].extract_text()
        print(f"Texto extraído: {texto[:200]}")
    except Exception as e:
        print(f"Error accediendo a pages: {type(e).__name__}: {e}")
else:
    print("\n✅ PDF NO ENCRIPTADO")
    print(f"Número de páginas: {len(reader.pages)}")
    
    # Extraer contenido
    contenido = ""
    for i, page in enumerate(reader.pages):
        contenido += f"[PÁGINA {i+1}]\n{page.extract_text()}\n\n"
    
    print(contenido)
    
    # Guardar
    with open("contenido_desencriptado.txt", 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("\n✅ Contenido guardado en: contenido_desencriptado.txt")
