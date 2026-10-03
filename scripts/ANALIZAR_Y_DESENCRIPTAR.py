#!/usr/bin/env python3
"""
🔐 ANALIZADOR DE TRANSCRIPCIONES + DESENCRIPTADOR PDF

Busca la contraseña del PDF en las transcripciones de YouTube.

Usa archivos de transcripción guardados manualmente en formato de texto.
"""

import sys
import json
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

def cargar_transcripciones():
    """Carga transcripciones desde archivos de texto"""
    transcripciones = {}
    
    # Archivos esperados
    archivos_trans = {
        'es': 'transcripcion_es.txt',
        'de': 'transcripcion_de.txt',
        'en': 'transcripcion_en.txt',
        'ja': 'transcripcion_ja.txt',
        'pt': 'transcripcion_pt.txt',
    }
    
    print("📂 Buscando transcripciones...\n")
    
    for lang_code, filename in archivos_trans.items():
        filepath = Path(filename)
        
        if filepath.exists():
            print(f"   ✅ Encontrado: {filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                contenido = f.read()
                transcripciones[lang_code] = {
                    'archivo': filename,
                    'texto': contenido,
                    'longitud': len(contenido)
                }
        else:
            print(f"   ❌ NO encontrado: {filename}")
    
    return transcripciones

def extraer_candidatos_transcripciones(transcripciones):
    """Extrae candidatos de contraseña de las transcripciones"""
    candidatos = []
    
    print("\n" + "="*70)
    print("🔍 ANALIZANDO TRANSCRIPCIONES PARA EXTRAER PISTAS")
    print("="*70 + "\n")
    
    for lang_code, data in transcripciones.items():
        texto = data['texto']
        print(f"🗣️  Idioma {lang_code.upper()}:")
        
        # Palabras que empiezan por V
        palabras = texto.split()
        palabras_v = set()
        for p in palabras:
            # Limpiar puntuación
            limpio = p.strip('.,;:!?¿"\'()[]{}«»')
            if limpio and limpio[0].upper() == 'V':
                palabras_v.add(limpio)
        
        if palabras_v:
            print(f"   📍 Palabras con V: {sorted(palabras_v)[:5]}")
            candidatos.extend(sorted(palabras_v))
        
        # Primeras palabras (cada línea)
        lineas = texto.split('\n')
        primeras_lineas = set()
        for linea in lineas:
            palabras_linea = linea.split()
            if palabras_linea:
                palabra = palabras_linea[0].strip('.,;:!?¿"\'')
                if palabra and len(palabra) > 2:
                    primeras_lineas.add(palabra)
        
        if primeras_lineas:
            primeras_v = [p for p in sorted(primeras_lineas) if p[0].upper() == 'V']
            if primeras_v:
                print(f"   📍 Primeras palabras (V): {primeras_v}")
                candidatos.extend(primeras_v)
        
        # Primeras 10 palabras del texto
        primeras_palabras = texto.split()[:10]
        print(f"   📍 Primeras palabras: {primeras_palabras}")
        candidatos.extend(primeras_palabras)
        
        # Primera línea completa
        primera_linea = lineas[0].strip()
        print(f"   📍 Primera línea: {primera_linea[:80]}")
        candidatos.append(primera_linea)
        
        print()
    
    return candidatos

def intentar_desencriptar(pdf_path, contraseña):
    """Intenta desencriptar el PDF"""
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
    print("="*70)
    print("🔐 ANALIZADOR DE TRANSCRIPCIONES + DESENCRIPTADOR PDF")
    print("="*70 + "\n")
    
    # Verificar si el PDF existe
    pdf_path = Path(r"C:\Users\woire\Downloads\resiste-protected.pdf")
    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return 1
    
    print(f"✅ PDF encontrado: {pdf_path.name}\n")
    
    # Cargar transcripciones
    transcripciones = cargar_transcripciones()
    
    if not transcripciones:
        print("\n❌ No se encontraron transcripciones")
        print("\n📋 Crea estos archivos de texto manualmente:")
        print("   1. Abre https://www.youtube.com/watch?v=Apv4cRO0DWo")
        print("   2. Click en '...' > 'Mostrar transcripción'")
        print("   3. Copia la transcripción")
        print("   4. Guarda en archivo: transcripcion_es.txt (para español)")
        print("   5. REPITE para otros 4 idiomas")
        return 1
    
    print(f"\n✅ Transcripciones cargadas: {len(transcripciones)} idiomas\n")
    
    # Extraer candidatos
    candidatos = extraer_candidatos_transcripciones(transcripciones)
    
    # Eliminar duplicados pero mantener orden
    candidatos_unicos = []
    seen = set()
    for c in candidatos:
        c_lower = str(c).lower()
        if c_lower not in seen and len(str(c)) > 0:
            candidatos_unicos.append(c)
            seen.add(c_lower)
    
    print(f"\n{'='*70}")
    print(f"🎯 CANDIDATOS EXTRAÍDOS: {len(candidatos_unicos)}")
    print(f"{'='*70}\n")
    
    if not HAS_PYPDF2:
        print("❌ PyPDF2 no disponible - instalando...")
        return 1
    
    # Intentar desencriptar
    print("🔓 INTENTANDO DESENCRIPTAR...\n")
    
    for i, pwd in enumerate(candidatos_unicos, 1):
        pwd_str = str(pwd)
        if not pwd_str or len(pwd_str) == 0:
            continue
        
        print(f"[{i:3d}/{len(candidatos_unicos)}] {pwd_str[:50]:50s}", end=" → ")
        
        if intentar_desencriptar(pdf_path, pwd_str):
            print(f"✅ ¡FUNCIONÓ!")
            print(f"\n{'='*70}")
            print(f"🎉 CONTRASEÑA ENCONTRADA: {pwd_str}")
            print(f"{'='*70}\n")
            
            # Intentar leer contenido
            try:
                reader = PdfReader(pdf_path)
                reader.decrypt(pwd_str)
                print(f"📄 PDF DESENCRIPTADO - {len(reader.pages)} páginas\n")
                print("--- CONTENIDO (primeras 800 caracteres) ---\n")
                texto = reader.pages[0].extract_text()
                print(texto[:800])
            except Exception as e:
                print(f"⚠️ {e}")
            
            return 0
        
        print("❌")
    
    print(f"\n{'='*70}")
    print("⚠️ NO SE ENCONTRÓ LA CONTRASEÑA")
    print(f"{'='*70}")
    print("\n💡 PRÓXIMOS PASOS:")
    print("  1. Asegúrate de que TODAS las 5 transcripciones estén cargadas")
    print("  2. Verifica que sean el contenido COMPLETO del video")
    print("  3. La contraseña puede estar al inicio, final o en medio")
    print("  4. Podría ser una palabra clave específica en ALGÚN idioma")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
