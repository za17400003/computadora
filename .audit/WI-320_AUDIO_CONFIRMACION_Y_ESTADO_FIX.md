# WI-320 — Auditoría y corrección: audio overflow + confirmación vocal

## Problema detectado
Durante la demo y la operación normal se observaron estos fallos:

- `Audio input overflow` en `computadora/voz/escucha.py` cuando la cola de audio se llenaba.
- Confirmaciones de voz mal interpretadas por coincidencias parciales como `"si"` dentro de palabras como `"sistema"`.
- `Gevurá` de permisos también usaba coincidencias parciales, lo que podía validar acciones inseguras por error.
- Riesgo de transiciones de estado inválidas cuando una confirmación era interpretada como comando normal.

## Cambios realizados

### 1. Mejora de tolerancia al overflow de audio
- Archivo: `computadora/voz/escucha.py`
- En el callback de `sounddevice`, cuando la cola de audio estaba llena se descarta solo el buffer más antiguo
  en lugar de vaciar toda la cola.
- Esto mantiene la mayor parte del audio reciente disponible para transcripción y evita pérdidas masivas.

### 2. Confirmación vocal más segura
- Archivo: `computadora/interfaz/ventana_principal.py`
- El reconocimiento de `sí`/`no` en el flujo de confirmación ahora usa coincidencias por palabra completa (`\b...\b`).
- Se corrigió la interpretación de respuestas de Gevurá.
- Se agregó manejo explícito de respuestas ambiguas para evitar que piezas de texto no relacionadas activen confirmaciones.

## Validación
- `python -m py_compile computadora/voz/escucha.py computadora/interfaz/ventana_principal.py` — sin errores de sintaxis.

## Resultado esperado
- Menor probabilidad de perder audio cuando la captura no puede procesarse al vuelo.
- Confirmaciones de voz más robustas y menos falsos positivos.
- Menor riesgo de procesamiento de comandos erróneos durante una confirmación.
