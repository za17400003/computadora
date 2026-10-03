#!/usr/bin/env python3
"""
🔐 DESCIFRADOR PDF PROTEGIDO: resiste-protected.pdf

Pista del video:
"Este video no es lo que piensas. Ahora no te puedo decir que es exactamente este video. 
Lo tienes que vivir por ti mismo, con tu propia conciencia. 
Solo te digo que es el ultimo rip que voy a hacer por mucho tiempo."

Contraseña: Frase del INICIO que empieza con V

Análisis:
- Palabra clave en video: "vivir por ti mismo" (auto-vivencia)
- Marco alquímico: NIGREDO → ALBEDO → CITRINITAS → RUBEDO → PALINGENESIA
- Marco esotérico: Verdad, Vida, Voluntad, Vibración, Visión
"""

import sys
from pathlib import Path

# Intentar PyPDF2 primero (mejor soporte)
HAS_PYPDF2 = False
HAS_PDFPLUMBER = False

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    pass

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    pass

# ═══════════════════════════════════════════════════════════════
# CANDIDATOS DE CONTRASEÑA (empieza por V)
# ═══════════════════════════════════════════════════════════════

CANDIDATOS = [
    # Directos
    "Verdad",
    "verdad",
    "VERDAD",
    "Vida",
    "vida",
    "VIDA",
    "Vivir",
    "vivir",
    "VIVIR",
    
    # Del mensaje del video
    "Vivir por ti mismo",
    "vivir por ti mismo",
    "Vivir por tu mismo",
    "vívelo por ti mismo",
    
    # Variantes sin espacios/puntos
    "Vivirporticismo",
    "vivirporticismo",
    "VptM",  # Siglas
    "vptm",
    
    # Conceptos esotéricos (Alquimia)
    "Verdad Recursiva",
    "verdad recursiva",
    "Vibración",
    "vibración",
    "Vigencia",
    "vigencia",
    "Visión",
    "visión",
    "Voluntad",
    "voluntad",
    "Viaje",
    "viaje",
    
    # Alquimia 5 Fases
    "Verdad y Transmutación",
    "Verdad Transmutada",
    "Vibración Alquímica",
    "Vigencia del Opus",
    
    # Masonería (símbolos de V)
    "Verdad y Libertad",
    "Virtud",
    "virtud",
    "Voto Sagrado",
    "voto sagrado",
    
    # Hebreo (alquimia Cabalística)
    "emet",
    "EMET",
    "Emet",
    
    # Último "rip" = última revelación/última extracción
    "Verdad Última",
    "verdad última",
    "Última Verdad",
    "última verdad",
    "Verdad Final",
    "verdad final",
    
    # Frases completas sin puntos
    "Este video no es lo que piensas Ahora no te puedo decir que es exactamente este video Lo tienes que vivir por ti mismo con tu propia conciencia Solo te digo que es el ultimo rip que voy a hacer por mucho tiempo",
    "Lo tienes que vivir por ti mismo",
    "lo tienes que vivir por ti mismo",
    "Lo tienes que vivirlo por ti mismo",
    "lo tienes que vivirlo por ti mismo",
    
    # Primeras palabras del mensaje
    "Este video",
    "este video",
    "Este",
    "este",
    
    # Ultra-minimales
    "V",
    "v",
]

def intentar_desencriptar_pypdf2(pdf_path, contraseña):
    """Intenta desencriptar con PyPDF2"""
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            if reader.decrypt(contraseña):
                return True, "✅ DESENCRIPTADO (PyPDF2)"
        else:
            return True, "⚠️ PDF no está encriptado"
    except Exception as e:
        pass
    return False, None

def intentar_desencriptar_qpdf(pdf_path, contraseña):
    """Intenta desencriptar con qpdf (CLI)"""
    import subprocess
    try:
        output_path = pdf_path.parent / f"{pdf_path.stem}_DECODED.pdf"
        cmd = [
            "qpdf",
            f"--password={contraseña}",
            "--stream-data=uncompress",
            str(pdf_path),
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        if result.returncode == 0 and output_path.exists():
            return True, f"✅ DESENCRIPTADO (qpdf) → {output_path}"
    except Exception as e:
        pass
    return False, None

def main():
    pdf_path = Path(r"C:\Users\woire\Downloads\resiste-protected.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        sys.exit(1)
    
    print(f"🔐 INTENTANDO DESENCRIPTAR: {pdf_path}")
    print(f"   Tamaño: {pdf_path.stat().st_size / 1024:.1f} KB")
    print(f"   Total candidatos: {len(CANDIDATOS)}\n")
    
    # Verificar qué herramientas tenemos
    if HAS_PYPDF2:
        print("✅ PyPDF2 disponible")
    else:
        print("❌ PyPDF2 no disponible (pip install PyPDF2)")
    
    if HAS_PDFPLUMBER:
        print("✅ pdfplumber disponible")
    else:
        print("❌ pdfplumber no disponible (pip install pdfplumber)")
    
    print("\n" + "="*70)
    print("INTENTANDO CONTRASEÑAS...")
    print("="*70 + "\n")
    
    encontrada = False
    for i, pwd in enumerate(CANDIDATOS, 1):
        # Mostrar progreso
        print(f"[{i:3d}/{len(CANDIDATOS)}] Probando: {pwd[:40]:40s}", end=" → ")
        
        # Intentar PyPDF2
        if HAS_PYPDF2:
            success, msg = intentar_desencriptar_pypdf2(pdf_path, pwd)
            if success:
                print(f"✅ FUNCIONÓ: {pwd}")
                print(f"\n{'='*70}")
                print(f"🎉 CONTRASEÑA ENCONTRADA: {pwd}")
                print(f"{'='*70}\n")
                encontrada = True
                break
        
        # Intentar qpdf
        if not encontrada:
            success, msg = intentar_desencriptar_qpdf(pdf_path, pwd)
            if success:
                print(f"✅ FUNCIONÓ: {pwd}")
                print(f"\n{'='*70}")
                print(f"🎉 CONTRASEÑA ENCONTRADA: {pwd}")
                print(f"   {msg}")
                print(f"{'='*70}\n")
                encontrada = True
                break
        
        print("❌")
    
    if not encontrada:
        print("\n" + "="*70)
        print("⚠️ NO SE ENCONTRÓ CONTRASEÑA EN CANDIDATOS")
        print("="*70)
        print("\n📋 PRÓXIMOS PASOS:")
        print("  1. Proporciona el VIDEO para analizar el mensaje cifrado")
        print("  2. Busca la frase exacta en el inicio del video")
        print("  3. Palabras clave para investigar:")
        print("     - Primer palabra que empieza por V")
        print("     - Frases cortas antes del '.'")
        print("     - Mensajes entre líneas (esteganografía)")
        print("  4. Si tienes acceso a texto del video, paste aquí para análisis")
        return 1
    
    return 0 if encontrada else 1

if __name__ == "__main__":
    sys.exit(main())
