from pathlib import Path
p = Path('computadora/nucleo/observador.py')
text = p.read_text(encoding='utf-8')
text = text.replace('\\"', '"')
p.write_text(text, encoding='utf-8')
print('done')
