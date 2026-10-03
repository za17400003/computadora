import pikepdf

# Palabras simples que comienzan con V
passwords = [
    'vive',
    'VIVE',
    'Vive',
    'vale',
    'VALE', 
    'Vale',
    'vos',
    'VOS',
    'vas',
    'VAS',
    'Vas',
    've',
    'VE',
    'ven',
    'VEN',
    'verdad',
    'VERDAD',
    'verdad completamente',
    'verdadera',
    'VERDADERA',
    'yo trabajas',
    'ya',
    'YA',
]

found = False
for pwd in passwords:
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'\n[✓✓✓ ¡ÉXITO! ✓✓✓]: {pwd!r}\n')
            print('='*70)
            for i, page in enumerate(pdf.pages):
                print(f'\n--- PÁGINA {i+1} ---')
                print('='*70)
                text = page.extract_text()
                if text:
                    print(text)
                else:
                    print('[Sin texto]')
            found = True
            break
    except:
        pass

if not found:
    print('[-] Aún no encontrada.')
