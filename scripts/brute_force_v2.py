#!/usr/bin/env python3
import pikepdf

# Palabras EXACTAS del audio y sus variaciones
palabras_audio = [
    # Audio 1
    'este', 'es', 'el', 'final', 'así', 'vuelve', 'a', 'empezar', 
    'desde', 'el', 'principio', 'del', 'video', 'no', 'hay', 'vuelta', 'atrás',
    'volviéndote', 'loco', 'locura', 'matrix', 'se', 'da', 'cuenta',
    
    # Audio 5 - las más relevantes
    'vida', 'puede', 'ser', 'libre', 'hermosa', 'soldado', 'vale', 'más',
    'violenta', 'todo', 'estará', 'perdido', 'rip', 'rest', 'in', 'peace',
    
    # Conceptos clave
    'libertad', 'esclavitud', 'despertar', 'dormir', 'realidad', 'ilusión',
    'verdad', 'mentira', 'resistencia', 'rendición', 'lucha', 'paz',
]

# Frases completas que merecen prueba
frases_completas = [
    'este es el final',
    'Este es el final',
    'ESTE ES EL FINAL',
    'no hay vuelta atras',
    'NO HAY VUELTA ATRAS',
    'No hay vuelta atras',
    'la vida puede ser libre y hermosa',
    'LA VIDA PUEDE SER LIBRE Y HERMOSA',
    'violenta y todo estara perdido',
    'VIOLENTA Y TODO ESTARA PERDIDO',
]

# Generar contraseñas
contraseñas = set()

# Agregar palabras
for p in palabras_audio:
    contraseñas.add(p)
    contraseñas.add(p.upper())
    contraseñas.add(p.capitalize())
    contraseñas.add(p.title())

# Agregar frases
for f in frases_completas:
    contraseñas.add(f)

# Variaciones sin acentos/ñ
contraseñas.add('atras')
contraseñas.add('ATRAS')
contraseñas.add('Atras')
contraseñas.add('atrás')
contraseñas.add('ATRÁS')
contraseñas.add('volviendote')
contraseñas.add('VOLVIENDOTE')
contraseñas.add('estara')
contraseñas.add('ESTARA')
contraseñas.add('perdido')
contraseñas.add('PERDIDO')
contraseñas.add('hermosa')
contraseñas.add('HERMOSA')

# Más variantes
variantes = [
    'vuelve', 'VUELVE', 'a', 'A', 'empezar', 'EMPEZAR',
    'desde', 'DESDE', 'principio', 'PRINCIPIO', 'video', 'VIDEO',
]

for v in variantes:
    contraseñas.add(v)

print(f'[*] Total contraseñas a probar: {len(contraseñas)}\n')

encontrada = False
para_mostrar = []
for i, pwd in enumerate(sorted(contraseñas), 1):
    para_mostrar.append(pwd)
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'\n[✓✓✓ ¡CONTRASEÑA ENCONTRADA! ✓✓✓]\n')
            print(f'Contraseña: {pwd!r}\n')
            print('='*70 + '\n')
            for j, page in enumerate(pdf.pages):
                print(f'--- PÁGINA {j+1} ---')
                print('='*70)
                text = page.extract_text()
                print(text if text else '[Sin texto extraíble]')
                print()
            encontrada = True
            break
    except:
        if i % 50 == 0:
            print(f'[...] {i} probadas... último: {pwd!r}')

if not encontrada:
    print(f'\n[-] Ninguna funcionó ({len(contraseñas)} probadas)')
    print('\nÚltimas 30 probadas:')
    for pwd in para_mostrar[-30:]:
        print(f'  {pwd!r}')
