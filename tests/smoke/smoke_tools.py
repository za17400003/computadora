from computadora.habilidades.herramientas import ejecutar_herramienta

funcs = [
    ("obtener_fecha_hora", {}),
    ("obtener_info_sistema", {}),
    ("leer_portapapeles", {}),
    ("escribir_portapapeles", {"texto": "Prueba Computadora 123"}),
    ("leer_portapapeles", {}),
    ("crear_recordatorio", {"mensaje": "Prueba corta", "minutos": "0.1"}),
    ("listar_recordatorios", {}),
]

for name, args in funcs:
    try:
        out = ejecutar_herramienta(name, args)
        print(f"--- {name} ---")
        print(out)
    except Exception as e:
        print(f"Error ejecutando {name}: {e}")

print("Smoke tests finished.")
