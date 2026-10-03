#!/usr/bin/env python3
import json

d = json.load(open('codegraph_report.json', encoding='utf-8'))
print(f'Total: {d["total_classes"]} clases, {d["total_functions"]} funciones')
clases = [c for cs in [info.get("classes",[]) for info in d["modules"].values()] for c in cs]
print(f'Primeras 10 clases: {clases[:10]}')

# Buscar OrbeGolem
found = [f for f, info in d["modules"].items() if "OrbeGolem" in info.get("classes", [])]
print(f'\nOrbeGolem en: {found}')

# Buscar HiloEscucha
found = [f for f, info in d["modules"].items() if "HiloEscucha" in info.get("classes", [])]
print(f'HiloEscucha en: {found}')
