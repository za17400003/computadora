import pikepdf

passwords = [
    'vuelve a empezar',
    'VUELVE A EMPEZAR',
    'Vuelve a empezar',
    'vuelta atrás',
    'VUELTA ATRÁS',
    'Vuelta atrás',
    'vuelve a empezar desde el principio del video',
    'VUELVE A EMPEZAR DESDE EL PRINCIPIO DEL VIDEO',
    'video',
    'VIDEO',
]

pdf_path = 'resiste-protected.pdf'
found = False

for pwd in passwords:
    try:
        with pikepdf.open(pdf_path, password=pwd) as pdf:
            print(f'[✓] ¡CONTRASEÑA CORRECTA!: {pwd!r}\n')
            print('='*70)
            for i, page in enumerate(pdf.pages):
                print(f'\nPÁGINA {i+1}')
                print('='*70)
                text = page.extract_text()
                if text:
                    print(text)
                else:
                    print('[Sin texto extraíble]')
            found = True
            break
    except Exception as e:
        pass

if not found:
    print('[-] Ninguna contraseña funcionó. Probando más variantes...')
