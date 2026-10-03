#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buscar todas las palabras que empiezan con V
"""

import re
from collections import Counter

with open("TRANSCRIPCIONES_COMPLETAS.txt", 'r', encoding='utf-8') as f:
    texto = f.read()

# Buscar palabras que empiezan con V (mayúscula o minúscula)
palabras = re.findall(r'\b[Vv]\w+', texto)

# Contar frecuencia
freq = Counter(palabras)

print("🔤 TODAS LAS PALABRAS QUE EMPIEZAN CON V:\n")
for palabra, count in sorted(freq.items(), key=lambda x: -x[1]):
    print(f"[{count:2d}x] {palabra}")
