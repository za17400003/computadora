# FP-156 CITRINITAS — Propuesta de cambio: Ferrofluido + Metatron

**Propósito**: Definir la transformación visual del orbe central y la gestión de cámara antes de entrar en implementación.

---

## 1. Estado actual identificado

1. `computadora/interfaz/ventana_principal.py`
   - La cámara se marca como activa/inactiva solo con un booleano (`self._camara_activa`) pero no se inicia ni detiene realmente.
   - El keepalive de cámara revisa el gestor, pero no sincroniza con la instancia real de `KliCamara`.

2. `computadora/interfaz/camera_dev_tool.py`
   - La herramienta de desarrollo asume que `GestorKelim.leer('camara_local')` devuelve un `frame`, pero `KliCamara.leer_ohr()` no devuelve `frame`.
   - Esto genera discrepancia y conflictos en la observación de la cámara.

3. Animación central del orbe
   - Actualmente la animación del núcleo se comporta como un `morph` oscilante continuo.
   - No hay un estado explícito de ferrofluido estable vs estado Metatron/tesseract.

---

## 2. Objetivo de Citrinitas

Transformar la animación del orbe en una experiencia coherente con la metáfora:

- `esfera` → `ferrofluido mercurial` → `Metatron / teseracto visual`
- La cámara debe ser confiable y debe entrar/salir de modo visual solo cuando corresponde.
- El orbe central debe sentirse como un líquido magnético inducido, no como una esfera vibrante sin control.

---

## 3. Propuesta de diseño

### 3.1 Estados visuales del orbe

Definir al menos tres modos visuales:

- `ESTADO_NUCLEO`: orbe obsidiana estático con brillo suave.
- `ESTADO_FERROFLUIDO`: orbe se vuelve fluido, con atracción magnética centrada y deformaciones controladas.
- `ESTADO_METATRON`: aparece geometría sagrada/teseracto Metatron sobre el núcleo, con partículas que siguen un campo magnético.

### 3.2 Triada de triggers

- `idle / descanso / dormido` → `ESTADO_NUCLEO`
- `escuchando / procesando / hablando` → `ESTADO_FERROFLUIDO`
- `trabajando / demo / estado especial Metatron` → `ESTADO_METATRON`

### 3.3 Comportamiento de ferrofluido

El ferrofluido debe tener estas propiedades:

- campo magnético central estable que define la forma base.
- perturbaciones suaves solo cuando el orbe está activo o cuando se le toca.
- desacoplar la oscilación de las partículas de la rotación visual general.
- evitar oscilaciones rápidas constantes en modo esfera.

### 3.4 Transmutación Metatron

Cuando el orbe habla o ejecuta una acción importante, debe:

- revelar una estructura translúcida de geometría Metatron.
- animar una proyección de teseracto/4D sin cambiar a un caos de partículas.
- usar `metatron` como un overlay activo en el centro, no como un simple efecto de brillo.

---

## 4. Cambios necesarios en cámara

### 4.1 Corrección de gestión de cámara

`ventana_principal.py` debe:

- iniciar y detener la cámara real mediante `GestorKelim` y `KliCamara`.
- no usar solo el flag `_camara_activa` como si fuera la conexión real.
- en `_iniciar_camara()`: registrar/conectar `camara_local` cuando esté disponible.
- en `_detener_camara()`: desconectar correctamente el recurso de video.
- mantener el keepalive como monitor, pero no como único mecanismo de reconexión.

### 4.2 Corrección de dev tool

`camera_dev_tool.py` debe:

- leer el frame y metadatos desde el contrato correcto de `GestorKelim`.
- o bien extender `KliCamara` para que `leer_ohr()` devuelva un `frame` usable.
- evitar crear instancias exclusivas en el monitor que compitan por `cv2.VideoCapture`.

---

## 5. Implementación propuesta en fases

### Fase Citrinitas

1. Actualizar documentación de diseño.
2. Definir el estado visual exacto y las transiciones.
3. Documentar el contrato de cámara y el flujo de `GestorKelim`.
4. Especificar cómo se integrará el `ferrofluido` y el `MetatronCube`.

### Fase Rubedo

1. Implementar `computadora/geometria/ferrofluido.py` con campo magnético central.
2. Ajustar `computadora/interfaz/dibujante_orbe.py` para dibujar núcleo ferrofluidal.
3. Añadir `computadora/interfaz/animador_orbe_4d.py` o integrar `teseracto_4d` como overlay.
4. Corregir `ventana_principal.py` para usar estados visuales explícitos y conectar cámara real.
5. Arreglar `camera_dev_tool.py` para que el dev tool muestre frames reales correctamente.

---

## 6. Impacto esperado

- El orbe deja de oscilar como un núcleo de mercurio sin control.
- El centro se ve y se siente como ferrofluido inducido magnéticamente.
- La transición a Metatron es visualmente reconocible y no solo un brillo extra.
- La cámara deja de “recurrir” a problemas porque su gestión queda determinista.

---

## 7. Checklist de entrega de Citrinitas

- [ ] Documento de diseño completo.
- [ ] Estados visuales definidos.
- [ ] Transición ferrofluido → Metatron especificada.
- [ ] Contrato de cámara clarificado.
- [ ] Lista de cambios para Rubedo creada.

---

## 8. Siguiente paso inmediato

Pasar esta propuesta a Rubedo con dos tareas principales:

1. `WI-XXX`: `Integrar Ferrofluido Mercurial en orbe central`
2. `WI-YYY`: `Corregir flujo de cámara KliCamara / Camera Dev Tool`

**Nota**: esta propuesta es la versión Citrinitas. No está todavía implementada; es el diseño que debe traducirse a código en la fase siguiente.
