#!/usr/bin/env python3
"""
🔐 DESCIFRADOR PDF v2: CON ANÁLISIS ESTEGANOGRÁFICO
"""

import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# ═══════════════════════════════════════════════════════════════
# CANDIDATOS EXPANDIDOS (del análisis esteganográfico)
# ═══════════════════════════════════════════════════════════════

CANDIDATOS_FASE2 = [
    # Nuevos del análisis
    "Este",
    "este",
    "Ahora",
    "ahora",
    "Lo",
    "lo",
    "Solo",
    "solo",
    "Video",
    "video",
    "VIDEO",
    "Vivir",
    "vivir",
    "VIVIR",
    "Voy",
    "voy",
    "VOY",
    "Vivencia",
    "vivencia",
    "Vivirlo",
    "vivirlo",
    "Vívelo",
    "vívelo",
    "Videncia",
    "videncia",
    "Veneración",
    "veneración",
    "Verdadero",
    "verdadero",
    "Verificación",
    "verificación",
    "Vigilancia",
    "vigilancia",
    "Victor",
    "victor",
    "Victoria",
    "victoria",
    "Víctor",
    "víctor",
    
    # Combinaciones sin espacios
    "video_video",
    "vivir_voy",
    "videovideo",
    "vivirvoy",
    "Este_Ahora_Lo_Solo",
    "EstAhoraLoSolo",
    
    # Variantes numéricas
    "v1",
    "v01",
    "V1",
    "V01",
    "video1",
    "vivir1",
    
    # Conceptos del video
    "video_no_es",
    "Lo_tienes_que_vivir",
    "vivir_por_ti_mismo",
    "ultimo_rip",
    "rip",
    "RIP",
    "Rip",
    
    # Acróstimos
    "EALS",  # Este Ahora Lo Solo
    "EVN",   # Primeras letras
    
    # Palabras inversas
    "rifV",
    "riv",
    "ripV",
    
    # Masonería (pilares V)
    "Voluntad",
    "voluntad",
    "Verdad",
    "verdad",
    "Virtud",
    "virtud",
    
    # Del proyecto Golem
    "Verdad Recursiva",
    "verdad recursiva",
    "Verdad y Transmutación",
    
    # Conceptos esotéricos
    "Velo",
    "velo",
    "Vigencia",
    "vigencia",
    
    # Variantes con puntuación
    "V",
    "V.",
    "V-",
    "v",
    "v.",
    "v-",
]

def intentar_desencriptar(pdf_path, contraseña):
    """Intenta desencriptar con PyPDF2"""
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            if reader.decrypt(contraseña):
                return True
        else:
            return False
    except Exception:
        pass
    return False

def main():
    pdf_path = Path(r"C:\Users\woire\Downloads\resiste-protected.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return 1
    
    print(f"🔐 FASE 2: DESCIFRADOR CON ANÁLISIS ESTEGANOGRÁFICO")
    print(f"   Archivo: {pdf_path.name}")
    print(f"   Tamaño: {pdf_path.stat().st_size / 1024:.1f} KB")
    print(f"   Total candidatos: {len(CANDIDATOS_FASE2)}\n")
    
    if not HAS_PYPDF2:
        print("❌ PyPDF2 no disponible")
        return 1
    
    print("="*70)
    print("INTENTANDO CONTRASEÑAS (FASE 2)...")
    print("="*70 + "\n")
    
    for i, pwd in enumerate(CANDIDATOS_FASE2, 1):
        print(f"[{i:2d}/{len(CANDIDATOS_FASE2)}] {pwd:40s}", end=" → ")
        
        if intentar_desencriptar(pdf_path, pwd):
            print(f"✅ ¡FUNCIONÓ!")
            print(f"\n{'='*70}")
            print(f"🎉 CONTRASEÑA ENCONTRADA: {pwd}")
            print(f"{'='*70}\n")
            
            # Intentar leer contenido
            try:
                reader = PdfReader(pdf_path)
                reader.decrypt(pwd)
                print(f"📄 Contenido del PDF ({len(reader.pages)} páginas):")
                for j, page in enumerate(reader.pages[:3], 1):  # Primeras 3 páginas
                    text = page.extract_text()
                    print(f"\n--- PÁGINA {j} ---")
                    print(text[:500] + ("..." if len(text) > 500 else ""))
            except Exception as e:
                print(f"⚠️ No se pudo leer contenido: {e}")
            
            return 0
        
        print("❌")
    
    print("\n" + "="*70)
    print("⚠️ FASE 2 COMPLETADA - NO SE ENCONTRÓ CONTRASEÑA")
    print("="*70)
    print("\n🎯 PRÓXIMOS PASOS:")
    print("  1. Proporciona ENLACE del video para análisis")
    print("  2. Proporciona TIMESTAMP exacto donde menciona contraseña")
    print("  3. ¿Hay AUDIO en el video? (escucha atentamente)")
    print("  4. ¿Hay TEXTO on-screen? (pausar y leer)")
    print("  5. ¿Hay NÚMEROS o CÓDIGOS visuales?")
    print("  6. Metadata del video (título, descripción, creador)")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
