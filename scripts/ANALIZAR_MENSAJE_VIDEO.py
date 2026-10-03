#!/usr/bin/env python3
"""
🔍 ANÁLISIS ESTEGANOGRÁFICO DEL VIDEO

Mensaje original:
"Este video no es lo que piensas. Ahora no te puedo decir que es exactamente este video. 
Lo tienes que vivir por ti mismo, con tu propia conciencia. 
Solo te digo que es el ultimo rip que voy a hacer por mucho tiempo."

Estrategias de análisis:
1. Primeras letras de cada palabra (acróstimo)
2. Palabras que empiezan por V
3. Números escondidos
4. Patrones alquímicos
5. Numerología
6. Orden de aparición de conceptos
"""

def analizar_mensaje(texto):
    """Análisis profundo del mensaje"""
    
    print("="*70)
    print("📊 ANÁLISIS ESTEGANOGRÁFICO DEL MENSAJE")
    print("="*70)
    
    # Limpiar y separar
    palabras = texto.split()
    
    print(f"\n📋 Texto original ({len(palabras)} palabras):")
    print(f"  {texto}\n")
    
    # 1. ACRÓSTIMO (primeras letras)
    print("1️⃣ ACRÓSTIMO (primera letra de cada palabra):")
    acrostimo = "".join([p[0].upper() for p in palabras if p])
    print(f"   {acrostimo}")
    print(f"   Interpretación: {acrostimo[:3]}, {acrostimo[:5]}, {acrostimo[:10]}\n")
    
    # 2. PALABRAS QUE EMPIEZAN POR CADA LETRA
    print("2️⃣ PALABRAS POR LETRA (índice):")
    por_letra = {}
    for i, p in enumerate(palabras):
        primera = p[0].upper()
        if primera not in por_letra:
            por_letra[primera] = []
        por_letra[primera].append((i, p))
    
    for letra in sorted(por_letra.keys()):
        print(f"   {letra}: {[p[1] for p in por_letra[letra]]}")
    
    # 3. PALABRAS QUE EMPIEZAN POR V
    print("\n3️⃣ PALABRAS QUE EMPIEZAN POR V:")
    palabras_v = [p for p in palabras if p[0].upper() == 'V']
    print(f"   {palabras_v}")
    print(f"   Contraseña posible: {' '.join(palabras_v)}")
    
    # 4. PRIMERAS PALABRAS DE CADA ORACIÓN
    print("\n4️⃣ PRIMERAS PALABRAS DE CADA ORACIÓN:")
    oraciones = texto.split('.')
    primeras = [o.strip().split()[0] if o.strip().split() else "" for o in oraciones]
    print(f"   {primeras}")
    print(f"   Contraseña posible (primeras): {' '.join(primeras)}")
    
    # 5. PALABRAS ÚNICAS QUE EMPIEZAN POR V
    print("\n5️⃣ PALABRAS ÚNICAS CON V EN CUALQUIER POSICIÓN:")
    con_v = [p.rstrip('.,;:!?') for p in palabras if 'v' in p.lower()]
    print(f"   {set(con_v)}")
    
    # 6. NÚMEROS EN TEXTO
    print("\n6️⃣ NÚMEROS EXTRAÍDOS:")
    numeros = []
    for p in palabras:
        if any(c.isdigit() for c in p):
            numeros.append(p)
    print(f"   {numeros if numeros else 'Ninguno'}")
    
    # 7. PATRONES ALQUÍMICOS (5 fases)
    print("\n7️⃣ CONCEPTOS ALQUÍMICOS:")
    conceptos_alquimia = {
        'NIGREDO': ['negro', 'oscuro', 'muerte', 'rip'],
        'ALBEDO': ['blanco', 'luz', 'purificación'],
        'CITRINITAS': ['amarillo', 'aurora', 'iluminación'],
        'RUBEDO': ['rojo', 'sangre', 'manifestación'],
        'PALINGENESIA': ['renacimiento', 'transformación', 'nuevo']
    }
    
    for fase, palabras_fase in conceptos_alquimia.items():
        encontrados = [p for p in palabras if any(kw in p.lower() for kw in palabras_fase)]
        if encontrados:
            print(f"   {fase}: {encontrados}")
    
    # 8. ESTRUCTURA DEL MENSAJE
    print("\n8️⃣ ESTRUCTURA:")
    print(f"   Oración 1: Este video no es lo que piensas")
    print(f"   Oración 2: Ahora no te puedo decir que es exactamente este video")
    print(f"   Oración 3: Lo tienes que vivir por ti mismo, con tu propia conciencia")
    print(f"   Oración 4: Solo te digo que es el ultimo rip que voy a hacer por mucho tiempo")
    print(f"\n   Tema: Vivencia personal (NO EXPLICACIÓN EXTERNA)")
    print(f"   Clave: 'vivir por ti mismo' = auto-vivencia")
    print(f"   Pista: 'último rip' = última revelación/extracción")
    print(f"   Tiempo: 'por mucho tiempo' = ciclo largo")
    
    # 9. CONTRASEÑAS ALTERNATIVAS DERIVADAS
    print("\n9️⃣ CONTRASEÑAS CANDIDATAS ALTERNATIVAS:")
    candidatos_nuevos = [
        "Este",
        "Ahora",
        "Lo",
        "Solo",
        "Video",
        "Vivir",
        "Vivencia",
        "Vivirlo",
        "Vívelo",
        "Videncia",
        "Veneración",
        "Verdadero",
        "Verificación",
        "Vigilancia",
        "Victor",
        "Victoria",
        "Víctor",
        # Combinaciones
        "Este_que_piensas",
        "Vivir_por_ti",
        "Lo_vivido",
        # Números
        "v1",
        "v01",
        "V1",
        "V01",
    ]
    for i, c in enumerate(candidatos_nuevos, 1):
        print(f"   [{i:2d}] {c}")
    
    return candidatos_nuevos

def main():
    mensaje = """Este video no es lo que piensas. Ahora no te puedo decir que es exactamente este video. 
Lo tienes que vivir por ti mismo, con tu propia conciencia. 
Solo te digo que es el ultimo rip que voy a hacer por mucho tiempo."""
    
    candidatos = analizar_mensaje(mensaje)
    
    print("\n" + "="*70)
    print("📌 RECOMENDACIONES PARA DESENCRIPTAR:")
    print("="*70)
    print("""
1. El mensaje enfatiza VIVENCIA PERSONAL
   → Contraseña probablemente es forma de VIVIR/VIDA

2. "Último rip" puede significar:
   → Última revelación
   → Último acceso
   → Último ciclo

3. Empieza por V y es "frase del comienzo":
   → ¿Primera oración completa? "Este video..." → No empieza por V
   → ¿Primera palabra con V? "video" (posición 2)
   → ¿Concepto del comienzo? "Vida" (general)

4. INVESTIGAR VIDEO DIRECTAMENTE:
   → ¿Hay voz hablada que dice explícitamente la contraseña?
   → ¿Hay texto on-screen?
   → ¿Hay código QR/imagen/números?

5. ALTERNATIVAS:
   → Quizás la contraseña está en el ORIGEN/FUENTE del video
   → Metadata del video (titulo, descripción, canal)
   → Comentarios del video

❓ ¿Puedes compartir:
   - Enlace del video
   - Timestamp exacto donde menciona la contraseña
   - Metadata del video (título exacto, creador, fecha)
   - Descripción completa del video
""")

if __name__ == "__main__":
    main()
