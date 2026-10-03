#!/usr/bin/env python3
import pikepdf
import itertools

# Palabras base para generar combinaciones
palabras_base = [
    'vuelve', 'empezar', 'vuelta', 'atrás', 'atras', 
    'vida', 'video', 'verdad', 'verdadero', 'verdadera',
    'humanidad', 'potencial', 'resiste', 'resistencia',
    'rip', 'fin', 'inicio', 'principio', 'desde', 'el',
    'no', 'hay', 'ya', 'trabajas', 'ellos', 'trabajar',
    'esto', 'es', 'esto es el fin', 'vuelve a empezar',
]

# Palabras adicionales comunes
palabras_comunes = [
    'password', 'pass', '123456', 'admin', 'user',
    'root', 'test', 'demo', 'secret', 'key',
    'capsula', 'cápsula', 'matriz', 'matrix',
]

# Números comunes
numeros = ['', '123', '1234', '12345', '2024', '2025', '2026']

# Generar contraseñas candidatas
contraseñas = set()

# Agregar palabras individuales
for palabra in palabras_base + palabras_comunes:
    contraseñas.add(palabra)
    contraseñas.add(palabra.upper())
    contraseñas.add(palabra.capitalize())

# Combinaciones de 2 palabras
for p1, p2 in itertools.combinations(palabras_base[:10], 2):
    for sep in [' ', '_', '-', '']:
        contraseñas.add(f'{p1}{sep}{p2}')
        contraseñas.add(f'{p1}{sep}{p2}'.upper())

# Agregar números
for pwd in list(contraseñas)[:100]:
    for num in numeros:
        contraseñas.add(f'{pwd}{num}')
        if num:
            contraseñas.add(f'{num}{pwd}')

print(f'[*] Probando {len(contraseñas)} contraseñas...\n')

encontrada = False
for i, pwd in enumerate(sorted(contraseñas), 1):
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
        if i % 100 == 0:
            print(f'[...] Probadas {i} contraseñas...')

if not encontrada:
    print(f'\n[-] Ninguna de {len(contraseñas)} contraseñas funcionó.')
    print('\nPrimeras 20 probadas:')
    for pwd in sorted(list(contraseñas))[:20]:
        print(f'  - {pwd!r}')
