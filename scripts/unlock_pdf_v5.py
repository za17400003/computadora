import pikepdf

# Variaciones de la frase más famosa
passwords = [
    'vuelveaempezar',
    'VUELVEAEMPEZAR',
    'vuelve-a-empezar',
    'VUELVE-A-EMPEZAR',
    'vuelve_a_empezar',
    'VUELVE_A_EMPEZAR',
    'vuelveaempezardesdeelprincipiodelv ideo',
    'a empezar',
    'A EMPEZAR',
    'empezar',
    'EMPEZAR',
    'desde el principio',
    'DESDE EL PRINCIPIO',
]

found = False
for pwd in passwords:
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'\n[✓✓✓ ¡CORRECTO! ✓✓✓]: {pwd!r}\n')
            print('='*70 + '\n')
            for i, page in enumerate(pdf.pages):
                print(f'PÁGINA {i+1}:')
                print('='*70)
                text = page.extract_text()
                print(text if text else '[Sin texto]')
                print()
            found = True
            break
    except:
        pass

if not found:
    print('[-] Sigue sin funcionar.')
