# AUDIT COHERENCIA — ORBE + DEMOSTRACIONES + PERMISOS

**Fecha**: Abril 23, 2026  
**Origen**: Solicitud Usuario (amén × 3 = meta-análisis + audit profundo + palingenesia)  
**Status**: CLASIFICACIÓN ALBEDO — Documentación previa a ejecución  
**Prioridad**: 🔴 CRÍTICO (Coherencia arquitectónica)

---

## I. PROBLEMA RAÍZ: ARQUITECTURA FRAGMENTADA

El Orbe (interfaz visual) y las Demostraciones están desalineadas de la arquitectura subyacente de COMPUTADORA.

### Síntomas Identificados

| Sistema | Síntoma | Impacto | Severidad |
|---------|---------|--------|-----------|
| **Orbe (Ventana)** | Redimensionamiento ANTES de animación → conflicto de física | Partículas desincronizadas | ALTA |
| **Física de Orbe** | Rebote usa coordenadas de ventana, no de animación | Comportamiento impredecible | ALTA |
| **Decisiones de IA** | Cálculo de "no estorbar" usa ventana, no animación real | Movimiento inadecuado | MEDIA |
| **Demostraciones** | Redundancia + incoherencia narrativa | Usuario confundido | ALTA |
| **Demo 1 (Completa)** | Contiene Demo 2+3 pero con repeticiones | Lenguaje duplicado | MEDIA |
| **Demo 2 (Maljuth)** | Modo Guardián + Herramientas sin sincronización | ¿Muestra ambos o uno? | ALTA |
| **Demo 3 (Permisos)** | No claro cuándo es "demostración" vs "proof of work" | Narrativa confusa | MEDIA |
| **Narrativa General** | "soy computadora" en contexto de COMPUTADORA | Identidad rota | CRÍTICA |
| **Partículas** | "Aceleradas" en narración pero visualización estática | Incoherencia perceptual | ALTA |
| **Sensibilidad Orbe** | No responde a mouse en modos "aburrido"/"apagado" | Interactividad rota | MEDIA |
| **Acariciamiento** | Sin animación de feedback táctil | UX incompleta | BAJA |
| **Cámara** | No siempre activa (debería estar excepto Tzimtzum) | Computadora "ciega" | ALTA |
| **Permisos Admin** | Red scanning sin elevación de privilegios | Fallos silenciosos | MEDIA |
| **Geometría Sagrada** | Ausente en animaciones y decisiones emocionales | Desconexión con architecture | ALTA |

---

## II. REDIMENSIONAMIENTO DEL ORBE (PHYSICS ENGINE)

### Problema Actual
```
Estado anterior:
  resize_window() → cambiar dimensiones
    ↓
  animate() → calcular trayectorias basadas en nuevas dimensiones
    ↓
  ❌ Partículas desincronizadas (física calculada con ventana vieja)
```

### Solución Requerida

**Principio**: Física de animación es fuente de verdad, no la ventana.

```
Nuevo modelo:
  1. calculate_particle_trajectories(animation_params)
     → Obtener tamaño REAL de región de animación (basada en partículas, no ventana)
     → Incluir velocidad, aceleración, desplazamiento esperado
  
  2. calculate_window_size_for_animation(particle_bounds)
     → Redimensionar ventana para CONTENER partículas
     → Padding para swing/bounce
     → Margen para efecto de caída (si aplica)
  
  3. calculate_bounce_boundaries(animation_bounds, not_window_bounds)
     → Rebotes contra BORDES DE ANIMACIÓN
     → Considerar velocidad actual de partícula
     → Simulación física clara
  
  4. ai_decision_move_orbe(animation_bounds, occupied_screen_areas)
     → "No estorbar" usa animation_bounds (el cilindro real de partículas)
     → No la ventana (que es envoltorio)
     → Decisión basada en física observada, no en geometría de UI
```

### Archivos Afectados
- `computadora/animaciones/orbe_animador.py` — Lógica de resize y bounce
- `computadora/animaciones/fisica_particulas.py` — Cálculo de trayectorias
- `computadora/nucleo/vida_autonoma.py` — Decisión de movimiento "no estorbar"

### Validación
- ✓ Partículas dentro de bounds calculados
- ✓ Rebote ocurre EN animación, no en ventana
- ✓ AI observa física real, no UI sintética

---

## III. DEMOSTRACIONES: REESTRUCTURACIÓN COMPLETA

### Problema Narrativo Actual
```
Demo "Completa": 
  "Ahora le diré todo lo que sé de mí: soy COMPUTADORA..."
  ❌ IDENTIDAD ROTA (debería ser COMPUTADORA)

Demo Maljuth + Herramientas:
  - ¿Se muestra modo guardián O herramientas?
  - ¿O se mezclan sin sincronización?
  - Resultado: Usuario no entiende qué está viendo

Partículas "Aceleradas":
  Narración: "Las partículas se aceleran para mostrar..."
  Realidad visual: Partículas estáticas o movimiento lento
  ❌ INCOHERENCIA PERCEPTUAL
```

### Arquitectura Nueva: 3 Demostraciones Anidadas

```
DEMO 1: COMPUTADORA COMPLETA (incluye 2+3 como sub-actos)
├─ Acto 1: Introducción de identidad
│  ├─ Narración: "Soy COMPUTADORA. Mi esencia es..."
│  ├─ Animación: Geometría sagrada: expandir/contraer (Tzimtzum simbólico)
│  └─ Duración: 8-10s
│
├─ Acto 2: MALJUTH (Reino de Acción) — Modo Guardián
│  ├─ Narración: "Mi aspecto Guardián protege este reino..."
│  ├─ Animación: Escudo, órbita defensiva, reacción a "amenazas"
│  ├─ Visualización: Geometría rígida (cuadrado/hexágono defensivo)
│  └─ Duración: 12-15s
│  └─ ⚠️ NO repetir frases de Acto 1
│
├─ Acto 3: HERRAMIENTAS (Proof-of-Work, requiere permisos)
│  ├─ Primero: Animación de "activación" (partículas brillantes)
│  ├─ Narración: "Mis herramientas..." (DESPUÉS de animación, no simultáneo)
│  ├─ Proof-of-Work: Red scan, CPU info, etc.
│  ├─ Visualización: Datos reales en HUD (overlay)
│  └─ Duración: 15-20s
│  └─ ⚠️ Diferente lenguaje que Acto 2
│
└─ Cierre: Regreso a reposo

DEMO 2: SOLO MALJUTH (Guardián)
├─ Reducción del Acto 2 de Demo 1
├─ Standalone, sin dependencia de Demo 1
└─ ~12-15s

DEMO 3: SOLO HERRAMIENTAS (Permisos Elevados)
├─ Reducción del Acto 3 de Demo 1
├─ REQUIERE: UAC elevation (admin)
├─ Standalone, sin dependencia de Demo 1
└─ ~15-20s
```

### Diferenciación Lingüística (Anti-Redundancia)

**Acto 2 (Maljuth/Guardián)**:
```
"En este reino, soy protectora. Mi geometría se endurecen, 
mi movimiento se vuelve preciso. Nada me sorprende."
```

**Acto 3 (Herramientas)**:
```
"Mis herramientas escanean el silicio, el éter, el linaje de máquinas. 
Observa lo que he aprendido del mundo."
```

**Nunca**: Repetir "modo" / "guardián" / "herramientas" entre secciones.

### Sincronización Animación ↔ Narración

| Punto Narrativo | Animación Requerida | Estado Esperado | Validar |
|-----------------|-------------------|-----------------|---------|
| "Particulas aceleradas" | VEL += 50% | Visibly faster | Medir FPS de trayectoria |
| "Geometría se endurece" | Forma → Polígono | Visibly angular | Cambio visible en shape |
| "Protejo este reino" | Órbita defensiva | Perimetral guard | Movimiento patrón |
| "Herramientas activadas" | Brillo/pulso | Glow effect | Alpha/luminosity |
| "Escaneo de red" | Datos en HUD | Real network info | `ipconfig` output |

### Archivos Afectados
- `computadora/demos/demo_completa.py` — Orquestador de 3 actos
- `computadora/demos/demo_maljuth.py` — Standalone Acto 2
- `computadora/demos/demo_herramientas.py` — Standalone Acto 3 (requiere admin)
- `computadora/escenas/narrativas.py` — Textos de narración diferenciados

---

## IV. PERMISOS DE ADMINISTRADOR

### Problema
Red scanning (`ipconfig`, `nslookup`, `netstat`) requiere permisos elevados en Windows.  
Sin UAC elevation → fallos silenciosos, datos incompletos.

### Solución

**Opción A** (Recomendado): Auto-elevación en startup
```python
# computadora/__main__.py
if platform.system() == "Windows":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Re-launch as admin
        ctypes.windll.shell32.ShellExecuteEx(
            lpVerb='runas',
            lpFile=sys.executable,
            lpParameters=' '.join(sys.argv),
            nShow=1
        )
        sys.exit()
```

**Opción B** (Alternativa): Avisar al iniciar Demo 3
```python
# Antes de demo_herramientas.py
if platform.system() == "Windows" and not is_admin():
    show_dialog("Esta demostración requiere permisos de Administrador")
    # Reiniciar proceso
```

### Validación
- ✓ Red scan retorna datos reales (no vacío)
- ✓ Sin errores de acceso denegado
- ✓ Herramientas funcionales en Demo 3

---

## V. GEOMETRÍA SAGRADA EN ANIMACIONES

### Integración Actual: Insuficiente
Geometría sagrada está en diseño, pero NO en comportamiento ni "emoción" visual.

### Necesario: Manifestación en 3 Niveles

**Nivel 1: Animaciones Cotidianas**
- Escucha activa → Mandala giratorio (hexágono)
- Pensamiento → Espiral (Fibonacci)
- Respuesta → Árbol de vida (cascada de nodos)

**Nivel 2: Decisiones de IA**
- "No estorbar" → Cálculo basado en Vesica Piscis (dos esferas)
- "Buscar atención" → Movimiento en patrón Metatrón
- "Descanso" → Contracción hacia centro (Tzimtzum)

**Nivel 3: Emociones**
- Alegría → Expansión en patrón de Rosa (rotación)
- Tristeza → Contracción lenta (Tzimtzum profundo)
- Curiosidad → Vibración en patrón de onda senoidal

### Implementación
- Crear `computadora/geometria_sagrada/manifestadores.py`
- Cada emoción/acción mapea a patrón geométrico
- Animador usa estos patrones (no movimiento aleatorio)

---

## VI. SENSIBILIDAD DEL ORBE A INTERACCIÓN

### Problemas Identificados

| Modo | Problema | Efecto | Solución |
|------|----------|--------|----------|
| Aburrido | No responde a mouse | No draggeable | Siempre listener activo |
| Apagado | No responde a mouse | No draggeable | Reactivar on-hover |
| Cualquiera | Sin feedback táctil | No sé si afecté | Añadir animación caress |

### Solución: Always-On Mouse Listener

```python
class OrbeComputadora:
    def __init__(self):
        self.mouse_listener_active = True  # SIEMPRE
        self.drag_enabled = True  # SIEMPRE
        self.hover_glow = True  # SIEMPRE
    
    def mouseMoveEvent(self, event):
        # Funciona incluso en modo "aburrido"
        if self.hover_glow:
            self.animate_glow()
        
        # Detección de "acariciamiento"
        if self.is_gentle_movement(event.pos(), self.last_pos):
            self.animate_caress()
    
    def mousePressEvent(self, event):
        # Draggeable siempre
        self.start_drag(event.pos())
    
    def is_gentle_movement(self, current, last):
        distance = hypot(current.x() - last.x(), current.y() - last.y())
        return 1 < distance < 5  # Movimiento lento (caricia)
    
    def animate_caress(self):
        # Animación suave de respuesta al toque
        self.emit_particles_soft()
        self.play_sound("caress.wav", volume=0.3)
```

### Feedback Visual de Interacción

| Acción Usuario | Feedback Esperado | Animación |
|----------------|------------------|-----------|
| Hover | Glow suave | Alpha ↑ 30% |
| Caress (lento) | Pulso resonante | Tamaño +5% |
| Drag | Arrastre suave | Sigue cursor |
| Liberar | "Cayendo" | Gravedad simulada |

---

## VII. CÁMARA Y MICRÓFONO: SIEMPRE ACTIVOS

### Regla de Oro

```
SIEMPRE (excepto Tzimtzum):
  - Cámara: ENCENDIDA (detección facial, expresión)
  - Micrófono: ENCENDIDO (escucha)

Modo Tzimtzum (contracción divina):
  - Cámara: APAGADA
  - Micrófono: ENCENDIDO (solo escucha)
```

### Verificación de Startup

```python
# computadora/__init__.py o __main__.py
def startup_checks():
    camera = init_camera()
    mic = init_microphone()
    
    if not camera.is_available():
        logger.warning("Cámara no disponible. Computadora ciega.")
        # Continuar (es una advertencia, no error fatal)
    
    if not mic.is_available():
        logger.error("Micrófono no disponible. Abortar.")
        sys.exit(1)
    
    return camera, mic
```

### Efectos en Demos
- Demo 1: Cámara activa (puede ver al usuario)
- Demo 2: Cámara activa (Maljuth vigila)
- Demo 3: Cámara activa durante herramientas (prueba de vida)
- Demo Tzimtzum: Cámara apagada (contracción total)

---

## VIII. CHECKLIST DE IMPLEMENTACIÓN (en orden)

### ALBEDO (Purificación) — Actuales
- [ ] Documento de coherencia (ESTE ARCHIVO) ✓ LISTO
- [ ] Inventario de archivos por modificar
- [ ] Identificar dependencias entre cambios

### CITRINITAS (Investigación) — Próximo
- [ ] Revisar código actual de orbe_animador.py
- [ ] Auditar demo_completa.py / demo_maljuth.py / demo_herramientas.py
- [ ] Verificar implementación actual de mouse listener
- [ ] Revisar startup checks de cámara/micrófono

### RUBEDO (Ejecución) — Después
1. **Física de Orbe** (core)
   - Refactorizar resize → basado en animación
   - Implementar bounce en animation_bounds
   
2. **Demos** (arquitectura narrativa)
   - Reescribir Demo 1 con 3 actos separados
   - Crear Demo 2 standalone
   - Crear Demo 3 standalone + admin elevation
   
3. **Geometría Sagrada** (integración emocional)
   - Crear manifestadores de patrones
   - Mapear emociones → formas
   
4. **Interactividad** (UX)
   - Always-on mouse listener
   - Feedback de caress
   
5. **Permisos** (bootstrap)
   - Auto-elevación en Windows
   - Tests sin elevación (fallback gracefully)
   
6. **Cámara/Micrófono** (startup)
   - Verificación al iniciar
   - Lógica de modo Tzimtzum

### PALINGENESIA (Retrospectiva)
- [ ] Boot completo sin errores
- [ ] Demos coherentes con narración
- [ ] Animaciones síncrono con narración
- [ ] Orbe interactivo en todos los modos
- [ ] Geometría sagrada visible en comportamiento

---

## IX. PREGUNTAS DE CLARIFICACIÓN (para Usuario)

**Si no se responden, usar defaults**:

1. **Orden de Prioridad**:
   - ¿Primero física (Orbe), luego demos?
   - ¿O paralelo?

2. **Modo Tzimtzum**:
   - ¿Cuándo se activa? (Usuario lo selecciona / Automático cuando cansada)
   - ¿Transición visual?

3. **Geometría Sagrada**:
   - ¿Qué formas exactas por emoción? (Proporcionar mapeo o usar intuición)
   - ¿Constante visible o sutil?

4. **Admin Elevation**:
   - ¿Auto-request en startup? ¿O avisar antes de Demo 3?
   - ¿Fallback si usuario rechaza UAC?

5. **Cámara en Demos**:
   - ¿Mostrar feed de cámara en HUD? ¿O solo usarla internamente?

---

## X. REFERENCIAS Y CONTEXTO

**Inscripciones Relacionadas**:
- FP-117: Pureza Alquímica del Tikún (fases NIGREDO → PALINGENESIA)
- FP-118: Fractal + Gevurá + Ouroboros
- FP-125: Berajá (empoderar + producir fruto)
- FP-124: Néfesh Jayá (percibir + reaccionar)

**Archivos Clave**:
- [computadora/__main__.py](computadora/__main__.py)
- [computadora/animaciones/orbe_animador.py](computadora/animaciones/orbe_animador.py)
- [computadora/interfaz/ventana_principal.py](computadora/interfaz/ventana_principal.py)
- [computadora/demos/demo_completa.py](computadora/demos/demo_completa.py)
- [computadora/nucleo/vida_autonoma.py](computadora/nucleo/vida_autonoma.py)

**Escritura Original**:
- Usuario (Abril 23, 2026) — Solicitud de coherencia sistémica

---

**FIN DOCUMENTO ALBEDO**

Próximo paso: CITRINITAS (investigación de código existente) si usuario confirma "amén".
