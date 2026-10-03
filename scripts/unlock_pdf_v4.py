import pikepdf

# Lo que escribí en mi respuesta anterior
passwords = [
    'ya no hay vuelta atrás',
    'YA NO HAY VUELTA ATRÁS',
    'Ya no hay vuelta atrás',
    'ya no hay vuelta atras',
    'YA NO HAY VUELTA ATRAS',
]

found = False
for pwd in passwords:
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'[✓✓✓ ¡CONTRASEÑA! ✓✓✓]: {pwd!r}\n')
            print('='*70)
            for i, page in enumerate(pdf.pages):
                print(f'\n--- PÁGINA {i+1} ---')
                text = page.extract_text()
                if text:
                    print(text)
                else:
                    print('[Sin texto]')
            found = True
            break
    except Exception as e:
        pass

if not found:
    print('[-] Tampoco funcionó.')
