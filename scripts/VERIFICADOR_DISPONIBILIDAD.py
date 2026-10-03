#!/usr/bin/env python3
"""
✅ VERIFICADOR DE DISPONIBILIDAD - DESENCRIPTACIÓN PDF

Verifica que tengas TODO lo necesario para obtener transcripciones y 
desencriptar el PDF.
"""

import sys
from pathlib import Path

print("""
═══════════════════════════════════════════════════════════════════════════════
✅ VERIFICADOR - DESENCRIPTACIÓN PDF + TRANSCRIPCIONES
═══════════════════════════════════════════════════════════════════════════════
""")

checks = []

# 1. PDF existe
pdf_path = Path(r"C:\Users\woire\Downloads\resiste-protected.pdf")
check1 = pdf_path.exists()
checks.append(("PDF resiste-protected.pdf existe", check1))
if check1:
    print(f"✅ {pdf_path.name} ({pdf_path.stat().st_size} bytes)")
else:
    print(f"❌ {pdf_path} NO ENCONTRADO")

# 2. PyPDF2 disponible
try:
    from PyPDF2 import PdfReader
    checks.append(("PyPDF2 instalado", True))
    print("✅ PyPDF2 disponible")
except ImportError:
    checks.append(("PyPDF2 instalado", False))
    print("❌ PyPDF2 NO DISPONIBLE - instala con: pip install PyPDF2")

# 3. Scripts disponibles
scripts = {
    'ANALIZAR_Y_DESENCRIPTAR.py': 'scripts/ANALIZAR_Y_DESENCRIPTAR.py',
    'GUIA_TRANSCRIPCIONES_YOUTUBE.py': 'scripts/GUIA_TRANSCRIPCIONES_YOUTUBE.py',
}

print("\n📂 Scripts disponibles:")
for nombre, path in scripts.items():
    p = Path(path)
    existe = p.exists()
    checks.append((f"Script {nombre}", existe))
    status = "✅" if existe else "❌"
    print(f"{status} {nombre}")

# 4. Transcripciones guardadas
print("\n📝 Transcripciones:")
trans_archivos = {
    'es': 'transcripcion_es.txt',
    'de': 'transcripcion_de.txt',
    'en': 'transcripcion_en.txt',
    'ja': 'transcripcion_ja.txt',
    'pt': 'transcripcion_pt.txt',
}

transcripciones_encontradas = 0
for lang, filename in trans_archivos.items():
    p = Path(filename)
    existe = p.exists()
    checks.append((f"Transcripción {lang}", existe))
    if existe:
        print(f"✅ {filename} ({p.stat().st_size} bytes)")
        transcripciones_encontradas += 1
    else:
        print(f"❌ {filename} NO ENCONTRADO")

# 5. Resumen
print("\n" + "="*70)
todos_ok = all(c[1] for c in checks[:-5])  # Sin transcripciones

if pdf_path.exists():
    print("✅ PDF LISTO")
else:
    print("❌ PDF NO ENCONTRADO")

if transcripciones_encontradas == 5:
    print("✅ TODAS LAS TRANSCRIPCIONES PRESENTES")
    print("   → Ejecuta: python scripts/ANALIZAR_Y_DESENCRIPTAR.py")
elif transcripciones_encontradas > 0:
    print(f"🟡 {transcripciones_encontradas}/5 transcripciones presentes")
    print("   → Faltan transcripciones, ve a YouTube a copiarlas")
else:
    print("❌ SIN TRANSCRIPCIONES")
    print("   → Necesitas copiar del video de YouTube")
    print("   → Sigue la guía: GUIA_OBTENER_TRANSCRIPCIONES.md")

print("="*70)

# Próximos pasos
print("""
📋 PRÓXIMOS PASOS
────────────────────────────────────────────────────────────────────────────────

OPCIÓN A: Copiar transcripciones manuales (recomendado, 15 min)
────────────────────────────────────────────────────────────────────────────────
1. Lee: GUIA_OBTENER_TRANSCRIPCIONES.md
2. Ve a YouTube: https://www.youtube.com/watch?v=Apv4cRO0DWo
3. Copia 5 transcripciones (una por idioma)
4. Guárdalas como: transcripcion_es.txt, transcripcion_de.txt, etc.
5. Vuelve a ejecutar este verificador
6. Una vez 5/5 OK → python scripts/ANALIZAR_Y_DESENCRIPTAR.py

OPCIÓN B: Proporcionar transcripciones al agente
────────────────────────────────────────────────────────────────────────────────
Si ya tienes las transcripciones en texto, puedes:
1. Compartir el contenido del video (primeras líneas de cada idioma)
2. El agente las guardará en archivos automáticamente
3. Ejecutará el analizador

════════════════════════════════════════════════════════════════════════════════
""")

sys.exit(0)
