from pathlib import Path
path = Path(r"C:\Users\woire\Documents\proyecto-computadora\computadora\voz\diagnostico_microfono.py")
text = path.read_text(encoding="utf-8")
old_line = '            modelo_whisper = whisper.load_model(\\"base\\", device=\\"cuda\\" if torch.cuda.is_available() else \\"cpu\\")\n'
new_line = '            dispositivo = \\"cuda\\" if torch.cuda.is_available() else \\"cpu\\"\n            modelo_whisper = whisper.load_model(\\"base\\", device=dispositivo)\n'
text = text.replace(old_line, new_line, 1)
old_block = '                language=\\"es\\",\n                verbose=False,\n'
new_block = '                language=\\"es\\",\n                verbose=False,\n                fp16=(dispositivo == \\"cuda\\"),\n'
text = text.replace(old_block, new_block, 1)
path.write_text(text, encoding="utf-8")
print("patched diagnostico")
