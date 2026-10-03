import pikepdf

# Más variantes de contraseñas
passwords = [
    'resiste',
    'RESISTE',
    'Resiste',
    'resistencia',
    'RESISTENCIA',
    'rip',
    'RIP',
    'Rip',
    'este es el fin',
    'ESTE ES EL FIN',
    'Este es el fin',
    'verdadero potencial',
    'VERDADERO POTENCIAL',
    'verdadera humanidad',
    'VERDADERA HUMANIDAD',
    'Verdadera Humanidad',
]

for pwd in passwords:
    try:
        with pikepdf.open('resiste-protected.pdf', password=pwd) as pdf:
            print(f'\n[✓✓✓ CONTRASEÑA CORRECTA! ✓✓✓]: {pwd!r}\n')
            print('='*70)
            for i, page in enumerate(pdf.pages):
                print(f'\n--- PÁGINA {i+1} ---')
                print('='*70)
                text = page.extract_text()
                if text:
                    print(text)
                else:
                    print('[Sin texto extraíble]')
            break
    except:
        pass
else:
    print('Aún no encontrada. Probando más...')
