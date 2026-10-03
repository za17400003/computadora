#!/usr/bin/env python3
import sys

print("[*] Intentando múltiples estrategias de desbloqueo PDF...\n")

# Estrategia 1: PyPDF4
print("[1] Intentando con PyPDF4...")
try:
    from PyPDF4 import PdfReader
    reader = PdfReader('resiste-protected.pdf')
    print(f"    Páginas: {len(reader.pages)}")
    print(f"    Encriptado: {reader.is_encrypted}")
    if not reader.is_encrypted or reader.is_reader_enabled():
        for i, page in enumerate(reader.pages[:2]):
            text = page.extract_text()
            print(f"    Página {i+1}: {text[:80] if text else '[Sin texto]'}...")
except Exception as e:
    print(f"    Error: {e}\n")

# Estrategia 2: PyPDF2 con bypass
print("\n[2] Intentando con PyPDF2 (bypass author password)...")
try:
    from PyPDF2 import PdfReader
    reader = PdfReader('resiste-protected.pdf')
    if reader.is_encrypted:
        # Intentar desencriptar sin contraseña
        if reader.decrypt(''):
            print("    [!] Desencriptado con contraseña vacía")
        else:
            print("    [!] No se pudo desencriptar con vacía")
            # Ver si es solo protección de propietario
            reader._encryption = None
            try:
                for i, page in enumerate(reader.pages[:2]):
                    text = page.extract_text()
                    print(f"    Página {i+1}: {text[:80] if text else '[Sin texto]'}...")
            except:
                print("    No funcionó bypass")
except Exception as e:
    print(f"    Error: {e}\n")

# Estrategia 3: Intentar copiar sin protección
print("\n[3] Intentando copiar sin protección...")
try:
    import pikepdf
    with pikepdf.open('resiste-protected.pdf') as pdf:
        # Remover todas las restricciones
        pdf.save('resiste-bypass.pdf')
        print("    [✓] PDF copiado a resiste-bypass.pdf")
except pikepdf.PdfError as e:
    if 'invalid password' in str(e):
        print(f"    Requiere contraseña: {e}")
except Exception as e:
    print(f"    Error: {e}\n")

# Estrategia 4: Buscar archivo PDF sin protección en el mismo directorio
print("\n[4] Buscando PDFs en el directorio...")
import os
import glob
pdfs = glob.glob('*.pdf')
for pdf in pdfs:
    try:
        from PyPDF4 import PdfReader
        r = PdfReader(pdf)
        print(f"    {pdf}: {len(r.pages)} páginas, encrypted={r.is_encrypted}")
    except:
        pass

print("\n[!] Workflow completado")
