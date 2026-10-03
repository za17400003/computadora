#!/usr/bin/env python3
"""
🔐 DESENCRIPTADOR CON TRANSCRIPCION REAL

Usa el contenido del video para generar y probar candidatos de contraseña.
"""

import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

def cargar_transcripcion():
    """Carga transcripción española"""
    trans_file = Path("transcripcion_es.txt")
    if trans_file.exists():
        with open(trans_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def extraer_palabras_v(texto):
    """Extrae palabras que empiezan con V"""
    palabras = texto.split()
    palabras_v = []
    
    for p in palabras:
        limpio = p.strip('.,;:!?¿"\'()[]{}«»').lower()
        if limpio and limpio[0] == 'v':
            palabras_v.append(limpio)
    
    # Eliminar duplicados manteniendo orden
    visto = set()
    unicos = []
    for p in palabras_v:
        if p not in visto:
            unicos.append(p)
            visto.add(p)
    
    return unicos

def extraer_frases_clave(texto):
    """Extrae frases potenciales como contraseña"""
    frases = [
        "Este video no es lo que piensas",
        "Este video",
        "Estás aquí porque sabes algo",
        "Vivir por ti mismo",
        "vivir por ti mismo",
        "No hay vuelta atrás",
        "no hay vuelta atrás",
        "La última oportunidad",
        "ultima oportunidad",
        "Despierta",
        "despierta",
        "Verdad",
        "verdad",
        "Conciencia",
        "conciencia",
        "Madriguera del conejo",
        "madriguera del conejo",
    ]
    
    return frases

def intentar_desencriptar(pdf_path, contraseña):
    """Intenta desencriptar el PDF"""
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            if reader.decrypt(contraseña):
                return True
    except Exception:
        pass
    return False

def main():
    print("="*70)
    print("🔐 DESENCRIPTADOR PDF CON TRANSCRIPCIÓN REAL")
    print("="*70 + "\n")
    
    # Verificar PDF
    pdf_path = Path(r"C:\Users\woire\Downloads\resiste-protected.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return 1
    
    # Cargar transcripción
    transcripcion = cargar_transcripcion()
    if not transcripcion:
        print("❌ No se encontró transcripcion_es.txt")
        return 1
    
    print(f"✅ Transcripción cargada ({len(transcripcion)} caracteres)\n")
    
    # Extraer candidatos
    print("🔍 EXTRAYENDO CANDIDATOS...\n")
    
    palabras_v = extraer_palabras_v(transcripcion)
    frases = extraer_frases_clave(transcripcion)
    
    print(f"📍 Palabras que empiezan con V ({len(palabras_v)}):")
    print(f"   {', '.join(palabras_v[:10])}\n")
    
    # Combinar candidatos
    candidatos = []
    
    # 1. Palabras con V
    candidatos.extend(palabras_v)
    
    # 2. Frases clave
    candidatos.extend(frases)
    
    # 3. Variaciones de frases importantes
    candidatos.extend([
        "vivir",
        "video",
        "Vivir",
        "Video",
        "verdad",
        "Verdad",
        "VIVIR",
        "VIDEO",
        "VERDAD",
    ])
    
    # Eliminar duplicados
    candidatos = list(dict.fromkeys(candidatos))
    
    print(f"🎯 CANDIDATOS TOTALES: {len(candidatos)}\n")
    print("🔓 INTENTANDO DESENCRIPTAR...\n")
    
    if not HAS_PYPDF2:
        print("❌ PyPDF2 no disponible")
        return 1
    
    for i, pwd in enumerate(candidatos, 1):
        pwd_str = str(pwd).strip()
        if not pwd_str:
            continue
        
        print(f"[{i:3d}/{len(candidatos)}] {pwd_str[:60]:60s}", end=" → ")
        sys.stdout.flush()
        
        if intentar_desencriptar(pdf_path, pwd_str):
            print(f"✅ ¡ENCONTRADA!")
            print(f"\n{'='*70}")
            print(f"🎉 CONTRASEÑA: {pwd_str}")
            print(f"{'='*70}\n")
            
            # Intentar leer
            try:
                reader = PdfReader(pdf_path)
                reader.decrypt(pwd_str)
                print(f"📄 PDF DESENCRIPTADO - {len(reader.pages)} páginas\n")
                
                # Primeras líneas
                if len(reader.pages) > 0:
                    print("--- CONTENIDO (primeras 500 caracteres) ---\n")
                    texto = reader.pages[0].extract_text()
                    print(texto[:500])
            except Exception as e:
                print(f"⚠️ {e}")
            
            return 0
        
        print("❌")
    
    print(f"\n{'='*70}")
    print("⚠️ NO ENCONTRADA CON TRANSCRIPCIÓN ESPAÑOLA")
    print(f"{'='*70}\n")
    
    print("💡 PRÓXIMOS PASOS:")
    print("  1. Necesitamos los OTROS 4 idiomas (especialmente PORTUGUÉS)")
    print("  2. El video dice: 'cambia a portugués y vuelve al principio'")
    print("  3. Descarga los otros idiomas en downsub.com")
    print("  4. Repite este proceso\n")
    
    print("Idiomas requeridos:")
    print("  • Portugués (PT) ← MUY IMPORTANTE (mencionado en video)")
    print("  • Alemán (DE)")
    print("  • Inglés (EN)")
    print("  • Japonés (JA)")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
