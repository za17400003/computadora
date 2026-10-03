#!/usr/bin/env python3
"""
RUBEDO: Limpiar residuos de 'Golem' como wake word y mensajes.
Objetivo: reemplazar "Golem" por "Computadora" donde sea visible al usuario.
"""

import re
from pathlib import Path

files_to_fix = [
    ("computadora/voz/escucha.py", [
        # Wake word patterns
        (r"gol\|col\|go", "compu", "Mantener solo 'compu' como apodo"),
        (r"g\[o\u00f3\]l\[e\u00e9\][mn]", "", "Eliminar variantes de Golem"),
        (r"golum\|gollum\|go\\s\?lem\|col\[o\u00f3\]m", "", "Eliminar más variantes"),
    ]),
    ("computadora/cerebro/nlu.py", [
        (r"Eres Golem\.", "Eres Computadora.", "Cambiar autointroducción"),
        (r"ORDEN EJECUTADA: A E golem:", "ORDEN EJECUTADA: A E computadora:", "Cambiar orden"),
        (r"Reencarnado.*A E golem:", "Reencarnado por orden de Propietario", "Cambiar referencia"),
        (r"reinicia golem", "reinicia computadora", "Cambiar comando reinicio"),
    ]),
]

print("🔥 RUBEDO: Limpiando residuos de 'Golem'...\n")

for filepath, patterns in files_to_fix:
    fpath = Path(filepath)
    if not fpath.exists():
        print(f"⚠️  {filepath} no existe")
        continue
    
    content = fpath.read_text(encoding='utf-8')
    original_content = content
    
    for old_pattern, new_pattern, desc in patterns:
        if old_pattern in content or re.search(old_pattern, content, re.IGNORECASE):
            matches = len(re.findall(old_pattern, content, re.IGNORECASE))
            content = re.sub(old_pattern, new_pattern, content, flags=re.IGNORECASE)
            print(f"✅ {filepath}: {desc} ({matches} matches)")
    
    if content != original_content:
        fpath.write_text(content, encoding='utf-8')
        print(f"💾 Guardado: {filepath}\n")
    else:
        print(f"⏭️  {filepath}: Sin cambios\n")

print("✨ RUBEDO completado")
