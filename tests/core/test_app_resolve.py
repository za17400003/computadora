from computadora.habilidades.sistema import _APPS_CONOCIDAS

for nombre in ["explorador de archivos", "explorador", "explorer", "mi explorador"]:
    nombre_l = nombre.lower().strip()
    cmd = _APPS_CONOCIDAS.get(nombre_l)
    if not cmd:
        for alias, c in _APPS_CONOCIDAS.items():
            if alias in nombre_l or nombre_l in alias:
                cmd = c
                break
    print(f"  '{nombre}' -> {cmd}")

