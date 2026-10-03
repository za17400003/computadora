# 🧲 FERROFLUIDO VISUAL — Mejora FP-156 (PROPUESTA)

**Fecha**: Mayo 1, 2026  
**Problema**: Ferrofluido se ve "cortado", sin forma esférica, sin cambio de color, sin coherencia visual  
**Usuario Feedback**: "Parece un montón de partículas sin sentido, no se nota que sea una esfera ni que cambie"  

---

## I. ANÁLISIS DE PROBLEMA

### Situación Actual (❌ INCORRECTA)

```
- N=800 electrones + 200 neutrones en orbitas elípticas aleatorias
- Renderizado como puntos individuales sin conexión visual
- Colores: RGB fijos (sin mapeo a Ruaj)
- Sin delimitación clara de esfera → se ve "cortado"
- No hay diferencia visual entre REPOSO/ESCUCHANDO/PROCESANDO
```

### Raíz del Problema

1. **Falta de "Surface Cohesion"**: Partículas sueltas sin "piel" que las contenga
2. **Falta de "Magnetic Field Lines"**: No se ve que sea ferrofluido atraído por campo
3. **Sin mapeo de color**: REPOSO = verde, ESCUCHANDO = azul, etc. NO implementado
4. **Rendimiento vs Coherencia**: Prioridad fue speed (numpy) sobre visual fidelity

---

## II. INVESTIGACIÓN: FERROFLUIDO VISUAL REAL

### Propiedades Físicas del Ferrofluido
- **Forma base**: Gota esférica / blob cohesivo (no puntos sueltos)
- **En campo magnético**: Forma "spikes" (tendrils) que salen del blob
- **Tensión superficial**: Las partículas se "pegan" entre sí (radio de adhesión ~2-3px)
- **Colores**: Negro oscuro en realidad (Fe₃O₄ + aceite), pero parametrizable aquí

### Técnicas de Visualización Comprobadas

| Técnica | Ventaja | Desventaja |
|---------|---------|-----------|
| **Marching Cubes** | Forma suave, real | Costo computacional alto (~5-10ms) |
| **Convex Hull + Smooth** | Forma esférica, rápido | Puede perder detalles (spikes pequeños) |
| **Sphere Packing** | Coherencia inmediata | Visual "chunky" |
| **Distance Field + Particles** | Mejor visual, rendimiento OK | Requiere shader (WebGL/GPU) |
| **Blob Metaballs** | Clásico, suave, intuitivo | CPU-bound pero viable (~3-5ms) |

**Recomendación para PyQt6**: **Convex Hull + Spikes dinámicos** (mejor balance visual/rendimiento)

---

## III. PROPUESTA: FERROFLUIDO MEJORADO (RUBEDO)

### 3.1 Arquitectura Nuevo

```python
# Reemplazar FerroffluidoMercurial con FerroffluidoRubedo

class FerroffluidoRubedo:
    """Ferrofluido visual coherente + dinámico + mapeado a Ruaj."""
    
    # Layer 0: CORE SHAPE (Convex Hull esférico)
    # - 50-80 "vertices de control" que definen la forma general
    # - Actualizados cada 5 frames (no cada frame)
    # - Renderizado como polígono suave (contorno)
    
    # Layer 1: SURFACE SPIKES (Tendrils magnéticos)
    # - 20-40 "spikes" que salen del core en direcciones aleatorias
    # - Aparecen/desaparecen según emoción (EMOCIONADO = más)
    # - Longitud proporcional a carga emocional
    
    # Layer 2: PARTICLES (Brillo + movimiento)
    # - 300-400 partículas pequeñas dentro del blob
    # - SE MUEVEN JUNTAS (parte del sistema, no sueltas)
    # - Color según Ruaj (REPOSO=verde, ESCUCHANDO=azul, etc.)
    
    # Layer 3: GLOW AURA (Efecto de borde)
    # - Semi-transparente, color + claro que core
    # - Parpadea con ritmo circadiano
```

### 3.2 Mapeo de Color → Ruaj

| Estado Ruaj | Emoción | Color Base | Color Spike | Animación |
|-------------|---------|-----------|------------|-----------|
| **REPOSO** | Sereno | Verde esmeralda (40, 200, 100) | Verde claro | Respiración lenta (1s ciclo) |
| **ESCUCHANDO** | Atento | Azul agua (60, 140, 220) | Azul brillante | Ondas (2Hz) |
| **PROCESANDO** | Concentrado | Púrpura (160, 80, 220) | Púrpura vivido | Rotación rápida + spikes |
| **HABLANDO** | Expresivo | Oro cálido (255, 200, 80) | Dorado | Pulsación suave |
| **PENSANDO** | Reflexivo | Plateado (180, 180, 200) | Azul violeta | Movimiento aleatorio |
| **EMOCIONADO** | Excitado | Rojo profundo (200, 60, 100) | Rojo brillante | Spikes animados + salpicaduras |

### 3.3 Algoritmo Actualización por Frame

```
FRAME N:
┌─────────────────────────────────────────────────────────
│ 1. OBTENER RUAJ ACTUAL
│    - Desde `personalidad.ruaj_actual()` (JSON)
│    - Mapear a color base + velocidad animación
│
│ 2. UPDATE CORE SHAPE (cada 5 frames)
│    - Calcular Convex Hull de 80 puntos de control
│    - Suavizar con Catmull-Rom spline
│    - Mantener dentro de `radio_max_particulas` (clipping-safe)
│
│ 3. UPDATE SPIKES
│    - Para cada spike:
│      - target_length = carga_emocional * 30px (0-30)
│      - current_length += (target_length - current_length) * 0.1
│    - Opacity = (carga_emocional + 0.2) * 200
│
│ 4. UPDATE PARTICLES
│    - Mantener dentro del CORE SHAPE (confinamiento)
│    - Aplicar pequeña inercia + atracción al centro
│    - Cambiar color interpolando hacia color base (2s)
│
│ 5. RENDER
│    - Dibujar GLOW AURA (blur + alpha 0.3)
│    - Dibujar SPIKES (líneas de grosor variable)
│    - Dibujar CORE SHAPE (polígono relleno suave)
│    - Dibujar PARTICLES (puntos pequeños)
└─────────────────────────────────────────────────────────
```

### 3.4 Performance Target

- **Convex Hull**: ~1ms (cada 5 frames = 0.2ms/frame)
- **Spikes update**: ~0.5ms
- **Particles update**: ~2ms (300 partículas)
- **Renderizado total**: ~3-4ms/frame (vs. actual ~2ms)

**Impacto**: +1.5-2ms/frame es ACEPTABLE para visual coherencia

---

## IV. CAMBIOS TÉCNICOS REQUERIDOS

### 4.1 Nuevo Módulo: `geometria/ferrofluido_rubedo.py`

```python
# Clases nuevas
- class PuntoControl: pos, vel, atractor
- class Spike: origen, direccion, longitud, edad
- class SurfaceCore: vertices suavizados, radio dinámico
- class FerroffluidoRubedo: orquestador completo

# Métodos críticos
- calcular_convex_hull_suavizado()
- interpolar_spline_catmull_rom()
- confinamiento_particulas_a_core()
- mapear_ruaj_a_color()
```

### 4.2 Integración con `AnimadorOrbe4D`

- Reemplazar `FerroffluidoMercurial` por `FerroffluidoRubedo`
- Pasar `ruaj_actual()` del orbe en cada actualización
- Aumentar `radio_max_particulas` a 110 (para spikes)

### 4.3 Archivos a Modificar

1. `computadora/geometria/ferrofluido_rubedo.py` (NUEVO, ~300 líneas)
2. `computadora/interfaz/animador_orbe_4d.py` (UPDATE, ~30 líneas)
3. `computadora/interfaz/ventana_principal.py` (UPDATE, ~10 líneas - acceso a ruaj)

---

## V. IMPLEMENTACIÓN PROPUESTA

### Fase 1: CORE SHAPE (1 día)
- [ ] Implementar PuntoControl + SurfaceCore
- [ ] Convex Hull inicial (sin suavizado)
- [ ] Renderizar como polígono simple
- [ ] Test visual: orbe se ve "redondo"

### Fase 2: SPIKES (1 día)
- [ ] Clase Spike + lógica de aparición/desaparición
- [ ] Renderizar como líneas
- [ ] Animación de longitud
- [ ] Test visual: emoción alta = más spikes

### Fase 3: COLOR RUAJ (1 día)
- [ ] Mapeo Ruaj → RGB
- [ ] Interpolación de color (2s transición)
- [ ] Aplicar a particles + core shape
- [ ] Test visual: cambia de color al hablar/pensar

### Fase 4: INTEGRACIÓN (0.5 días)
- [ ] Juntar todo en `FerroffluidoRubedo`
- [ ] Reemplazar en `AnimadorOrbe4D`
- [ ] Tests de rendimiento
- [ ] Revisión visual usuario

---

## VI. SIGUIENTE PASO

**Si usuario acepta esta propuesta:**
1. Crear `computadora/geometria/ferrofluido_rubedo.py` con Phase 1+2
2. Integrar en `AnimadorOrbe4D`
3. Validar visual + rendimiento
4. Iterar Phase 3+4

**Alternativa "Quick Fix" (1h):**
Si quieres resultado RÁPIDO: Solo cambiar colores + hacer spikes simples (sin full refactor).

---

## Citation

- **Investigación**: Ferrofluido visualization techniques (Wikipedia)
- **Problema**: User feedback "ferrofluido se ve cortado/sin coherencia"
- **Propuesta**: FP-156 Phase 2 (RUBEDO - Manifestación coherente)
