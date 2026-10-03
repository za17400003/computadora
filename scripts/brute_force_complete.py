#!/usr/bin/env python3
import pikepdf
import itertools

# PALABRAS Y FRASES EXACTAS DE LOS AUDIOS
palabras_criticas = [
    # Audio 1
    'descubrir', 'espina', 'madriguera', 'portugués', 'vuelta', 'atrás',
    'este video', 'no hay vuelta atrás', 'ya no hay vuelta atrás',
    'ilusión', 'desperta', 'rip',
    
    # Audio 2
    'secreto', 'misterio', 'verdadero secreto', 'verdad', 'inglés',
    'vislumbrar', 'descifrar',
    
    # Audio 3
    'sufrimiento', 'potencial', 'miedo', 'pereza', 'verdadero potencial',
    'filósofo', 'artista', 'platón', 'nietzsche', 'humanidad',
    'japonés',
    
    # Audio 4
    'sueño', 'destino', 'soldado', 'poder absoluto', 'clase',
    'alemán', 'verdadera clase privilegiada',
    
    # Audio 5 - CRÍTICO
    'humanidad', 'bondad', 'empatía', 'chaplin', 'vida',
    'libertad y hermosa', 'la vida puede ser libre y hermosa',
    'violenta', 'sueños', 'odios',
]

# FRASES COMPLETAS MÁS LARGAS
frases_largas = [
    'vuelve a empezar desde el principio del video',
    'VUELVE A EMPEZAR DESDE EL PRINCIPIO DEL VIDEO',
    'vuelve a empezar desde el principio',
    'VUELVE A EMPEZAR DESDE EL PRINCIPIO',
    'vuelve a empezar este video',
    'VUELVE A EMPEZAR ESTE VIDEO',
    'vuelve a empezar',
    'VUELVE A EMPEZAR',
    'Vuelve a empezar',
    'ya no hay vuelta atrás',
    'YA NO HAY VUELTA ATRÁS',
    'la vida puede ser libre y hermosa',
    'LA VIDA PUEDE SER LIBRE Y HERMOSA',
    'la vida',
    'LA VIDA',
    'humanidad',
    'HUMANIDAD',
    'humanidad y potencial',
    'HUMANIDAD Y POTENCIAL',
    'verdadero potencial humano',
    'VERDADERO POTENCIAL HUMANO',
    'rip',
    'RIP',
    'Rip',
]

# Variaciones con y sin acentos
acentos = [
    ('portugués', 'portugues'),
    ('atrás', 'atras'),
    ('filosofía', 'filosofia'),
    ('día', 'dia'),
    ('más', 'mas'),
]

# Generar contraseñas base
contraseñas = set()

# Agregar frases largas primero (son las más probables)
for frase in frases_largas:
    contraseñas.add(frase)

# Agregar palabras
for palabra in palabras_criticas:
    contraseñas.add(palabra)
    contraseñas.add(palabra.upper())
    contraseñas.add(palabra.capitalize())

# Combos 2-3 palabras
combos_2 = [
    ('vuelve', 'empezar'),
    ('vuelta', 'atrás'),
    ('verdadero', 'potencial'),
    ('verdadera', 'humanidad'),
    ('vida', 'libre'),
    ('libre', 'hermosa'),
    ('humanidad', 'bondad'),
    ('rip', 'vuelve'),
    ('no', 'hay'),
    ('hay', 'vuelta'),
]

for w1, w2 in combos_2:
    for sep in [' ', '_', '-', '']:
        contraseñas.add(f'{w1}{sep}{w2}')
        contraseñas.add(f'{w1}{sep}{w2}'.upper())

print(f'[*] Total contraseñas a probar: {len(contraseñas)}\n')
print('[*] Probando en orden de probabilidad (frases largas primero)...\n')

encontrada = False
contador = 0
for pwd in sorted(contraseñas, key=lambda x: (-len(x), x)):
    contador += 1
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'\n{"="*70}')
            print(f'[✓✓✓ ¡¡¡ CONTRASEÑA ENCONTRADA !!! ✓✓✓]')
            print(f'{"="*70}')
            print(f'\n✓ Contraseña: {pwd!r}\n')
            print('='*70 + '\n')
            
            for j, page in enumerate(pdf.pages):
                print(f'--- PÁGINA {j+1} ---')
                print('='*70)
                text = page.extract_text()
                if text:
                    print(text)
                    print()
                else:
                    print('[Sin texto extraíble]')
                    print()
            
            encontrada = True
            break
    except:
        if contador % 50 == 0:
            print(f'[...] {contador} probadas... último: {pwd!r}')

if not encontrada:
    print(f'\n[-] Ninguna funcionó ({len(contraseñas)} probadas).')
    print(f'\n[!] Mostrando primeras 30 intentadas:')
    for pwd in sorted(contraseñas, key=lambda x: (-len(x), x))[:30]:
        print(f'  ✗ {pwd!r}')
