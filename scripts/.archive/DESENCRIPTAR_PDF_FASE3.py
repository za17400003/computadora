#!/usr/bin/env python3
"""
🔐 DESCIFRADOR PDF v3: PATRONES MULTILINGÜES

Estrategia: Usar IDIOMAS para generar nuevos candidatos.
El mensaje original está en ESPAÑOL. 
Pero ¿qué si la contraseña está en OTRO idioma?
"""

import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# CANDIDATOS MULTILINGÜES
# El concepto de "Verdad" / "Vivir" / "Vida" en diferentes idiomas

CANDIDATOS_V3 = [
    # ESPAÑOL - Conceptos con V
    "Verdad", "verdad", "VERDAD",
    "Vida", "vida", "VIDA", 
    "Vivir", "vivir", "VIVIR",
    "Vívelo", "vívelo",
    "Video", "video", "VIDEO",
    "Verdadera", "verdadera",
    "Videncia", "videncia",
    
    # PORTUGUÉS (BR) - Similares
    "Verdade", "verdade", "VERDADE",
    "Vida", "vida", "VIDA",
    "Viver", "viver", "VIVER",
    "Vivenciá", "vivencia",
    "Vídeo", "vídeo",
    
    # INGLÉS - Versiones en inglés
    "Truth", "truth", "TRUTH",
    "Life", "life", "LIFE",
    "Live", "live", "LIVE",
    "Vision", "vision", "VISION",
    "Video", "video", "VIDEO",
    
    # ALEMÁN - Con V (pocos, Wahrheit empieza con W)
    "Verantwortung",  # Responsabilidad
    "Vertrauen",      # Confianza
    "Vergangene",     # Pasado
    
    # JAPONÉS - Transliteración romana (Romaji)
    "Shinjitsu",      # 真実 - Verdad
    "Inochi",         # 命 - Vida
    "Ikiru",          # 生きる - Vivir
    "Kizutsuku",      # Video-like concept
    
    # CONCEPTOS DEL PROYECTO (Alquimia)
    "Verdad Transmutada",
    "Verdad y Vibración",
    "Vivencia Última",
    "Último Video",
    "El Fin",         # Título del video
    "Esto es el fin",
    
    # VARIABLES SIN ESPACIOS
    "VerdadVida",
    "VidaVivir",
    "VídeoVerdad",
    "EstoEsElFin",
    "ElUltimo",
    "elultimo",
    
    # ACRÓSTIMOS DE IDIOMAS
    "VVVVV",  # Cinco V?
    "V5",     # 5 idiomas?
    
    # NUMEROLOGIA - Gematría
    "Verdad22",  # V=22 en gematría?
    "V22",
    
    # COMBINACIONES CON AUDIO TRACKS
    "es_de_en_ja_pt",  # Códigos de idiomas
    "esdenjopt",
    
    # CONCEPTO "EL FIN" EN IDIOMAS
    "Das Ende",       # Alemán
    "The End",        # Inglés
    "Owari",          # 終わり - Japonés
    "O Fim",          # Portugués
    "El Fin",         # Español
    
    # CONCEPTOS ESOTÉRICOS MULTILINGÜES
    "Transmutación",
    "transmutación",
    "Alquimia",
    "alquimia",
    "ALQUIMIA",
    
    # MÁS VARIANTES
    "Viaja",
    "viaja",
    "Vejez",
    "vejez",
    "Veneración",
    "veneración",
    "Vigilancia",
    "vigilancia",
    "Vigor",
    "vigor",
    "Virtud",
    "virtud",
    "Vínculo",
    "vínculo",
    
    # REVERSED (por si acaso)
    "dadreV",
    "aviV",
    "odiV",
    "ripU",
    
    # DEL VIDEO: "Esto es el fin"
    "Esto",
    "esto",
    "ESTO",
    "es",
    "ES",
    "fin",
    "FIN",
    "Fin",
    
    # PISTA: "por mucho tiempo"
    "Tiempo",
    "tiempo",
    "TIEMPO",
    "Mucho",
    "mucho",
    "MUCHO",
    
    # ULTIMAS OPCIONES
    "RIP",
    "rip",
    "Rip",
    "Última",
    "última",
    "ÚLTIMA",
]

def intentar_desencriptar(pdf_path, contraseña):
    """Intenta desencriptar PDF"""
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
    
    print(f"🔐 FASE 3: PATRONES MULTILINGÜES")
    print(f"   Enfoque: Conceptos de V en ESPAÑOL + OTROS IDIOMAS")
    print(f"   Idiomas del video: Español (MX), Alemán, Inglés, Japonés, Portugués")
    print(f"   Total candidatos: {len(CANDIDATOS_V3)}\n")
    
    if not HAS_PYPDF2:
        print("❌ PyPDF2 no disponible")
        return 1
    
    print("="*70)
    print("INTENTANDO CONTRASEÑAS (FASE 3)...")
    print("="*70 + "\n")
    
    for i, pwd in enumerate(CANDIDATOS_V3, 1):
        print(f"[{i:3d}/{len(CANDIDATOS_V3)}] {pwd:35s}", end=" → ")
        
        if intentar_desencriptar(pdf_path, pwd):
            print(f"✅ ¡FUNCIONÓ!")
            print(f"\n{'='*70}")
            print(f"🎉 CONTRASEÑA ENCONTRADA: {pwd}")
            print(f"{'='*70}\n")
            
            # Intentar leer
            try:
                reader = PdfReader(pdf_path)
                reader.decrypt(pwd)
                print(f"📄 PDF DESENCRIPTADO - {len(reader.pages)} páginas")
                print(f"\n--- CONTENIDO (primeras 500 caracteres) ---\n")
                texto = reader.pages[0].extract_text()
                print(texto[:500])
            except Exception as e:
                print(f"⚠️ No se pudo leer: {e}")
            
            return 0
        
        print("❌")
    
    print("\n" + "="*70)
    print("⚠️ FASE 3 COMPLETADA - NO ENCONTRADO")
    print("="*70)
    print("\n🎯 PRÓXIMAS ACCIONES:")
    print("  1. Transcripción del video: verificar si YouTube proporciona subtítulos")
    print("  2. Descripción del video: revisar si contiene pistas")
    print("  3. Comentarios: buscar comentarios que mencionen la contraseña")
    print("  4. Metadata: autor, fecha, etiquetas")
    print("  5. ¿Es posible obtener el link de Google Drive de la descripción?")
    print(f"\n   Descripción: https://drive.google.com/file/d/1pgnRs166GVA6NEzwpz_b7sPO4N_8O08y/...")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
