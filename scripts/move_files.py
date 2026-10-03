import os
import shutil
from pathlib import Path

raiz = Path('.')
movidos = []

# Reglas de movimiento
reglas = {
    '_docs': ['.md', '.txt'],  # Documentación
    'scripts': ['.py'],  # Scripts utilidad
    '_audit': ['.log'],  # Auditoría/logs
    'tests': [],  # Tests ya están en tests/
}

for archivo in raiz.iterdir():
    if archivo.is_file() and not archivo.name.startswith('.') and archivo.name not in ['WorkItems.md', 'README.md', 'LICENSE']:
        destino = None
        if archivo.suffix == '.md' and 'audit' in archivo.name.lower():
            destino = '_audit'
        elif archivo.suffix in ['.md', '.txt']:
            destino = '_docs'
        elif archivo.suffix == '.py' and not archivo.name.startswith('test_'):
            destino = 'scripts'
        elif archivo.suffix == '.log':
            destino = '_audit'

        if destino:
            shutil.move(str(archivo), destino)
            movidos.append(f'{archivo.name} → {destino}')

print('Archivos movidos:')
for m in movidos:
    print(f'  {m}')