# 🔄 COORDINATE FLOW DIAGRAM — Centering Bug During Autonomous Movement

## NORMAL RENDERING (No Movement) ✅ CORRECTO

```
ESTADO: _en_transito = False, _render_offset_x/y = 0.0

┌─ paintEvent() ──────────────────────────────────┐
│                                                 │
│  centro = self.rect().center()                 │
│  cx = centro.x() + int(0.0) = width/2  ✅      │
│  cy = centro.y() + int(0.0) = height/2 ✅      │
│                                                 │
│  ANILLOS SAGRADOS:                             │
│  └─ dibujar_patron_sagrado(painter, cx, cy, ..)│
│     └─ Render en (width/2, height/2)  ✅       │
│                                                 │
│  FERROFLUIDO 4D:                               │
│  └─ _animador.renderizar(painter,              │
│     self.width(), self.height(), ...)          │
│     └─ DENTRO: cx, cy = width//2, height//2  ✅
│        └─ Render en (width/2, height/2)  ✅    │
│                                                 │
│ RESULTADO: Anillos y ferrofluido ALINEADOS ✅  │
└─────────────────────────────────────────────────┘
```

---

## DURING AUTONOMOUS MOVEMENT ❌ BUG

```
ESTADO: _en_transito = True, _render_offset_x = +50, _render_offset_y = +30

PASO 1: _expandir_ventana_transito() calcula offset inicial
═════════════════════════════════════════════════════════════
Ventana física:  180×180 (TAMANO_PLENO) → Nueva: 400×300 (expandida)
Posición física: (100, 100) → Nueva: (50, 80)

orbe_local_x = 100 - 50 = 50
orbe_local_y = 100 - 80 = 20

_render_offset_x = 50 + 180/2 - 400/2 = 50 + 90 - 200 = -60
_render_offset_y = 20 + 180/2 - 300/2 = 20 + 90 - 150 = -40

✅ Offsets calculados correctamente


PASO 2: _interpolar_movimiento() (interpolación continua del offset)
═════════════════════════════════════════════════════════════════════
Cada frame, si no hemos llegado a destino:

target_off_x = ... (cálculo basado en destino)
dx = target_off_x - _render_offset_x

_render_offset_x += dx * factor  ← Offset se actualiza suavemente

Ej después algunos frames: _render_offset_x = -40, _render_offset_y = -20


PASO 3: paintEvent() renderiza FRAME ACTUAL
═════════════════════════════════════════════
┌─ paintEvent() ──────────────────────────────────────────┐
│                                                        │
│  centro = self.rect().center()                         │
│         = (400/2, 300/2) = (200, 150) (LOCAL coords)  │
│                                                        │
│  cx = 200 + int(-40) = 160   ← OFFSET APLICADO ✅      │
│  cy = 150 + int(-20) = 130   ← OFFSET APLICADO ✅      │
│                                                        │
│  ANILLOS SAGRADOS:                                     │
│  └─ dibujar_patron_sagrado(painter, 160, 130, ..)     │
│     └─ Render en (160, 130)  ✅ CORRECTO               │
│        (orbe desplazado del center de ventana)         │
│                                                        │
│  FERROFLUIDO 4D:                              ❌ BUG   │
│  └─ _animador.renderizar(painter,                      │
│     self.width()=400, self.height()=300, ...)          │
│     │                                                  │
│     └─ DENTRO: cx, cy = 400//2, 300//2                 │
│        cx, cy = (200, 150)   ❌ SIN OFFSET             │
│        └─ Render en (200, 150)  ❌ INCORRECTO          │
│           (núcleo, aura, spikes en CENTER de ventana)  │
│                                                        │
│ ┌─ ANILLOS:      render en (160, 130)  ← offseteado    │
│ └─ FERROFLUIDO: render en (200, 150)  ← SIN offsetear  │
│ DESALIENACIÓN: Δ = (-40, -20) pixeles ❌                 │
└────────────────────────────────────────────────────────┘

RESULTADO: ❌ Anillos y ferrofluido DESALINEADOS
                Distancia visual: ~44 pixeles diagonal
```

---

## DIAGRAMA DE CAPAS DURANTE TRÁNSITO

```
VENTANA EXPANDIDA (400×300) en posición pantalla (50, 80)
═══════════════════════════════════════════════════════════════

    Local coords inside window:
    ┌─────────────────────────────────┐
    │ (0,0)                   (400,0) │
    │                                 │
    │        CENTER=(200,150) ◄       │ Window center
    │                │                │
    │                ├─ OFFSET=(-40,-20)
    │                │                │
    │               ◆ (160,130)        │ ← ORBE REAL (con offset)
    │             ╱   ╲               │
    │            ╱     ╲              │
    │           ●─────●               │ ← ANILLOS (con offset)  ✅
    │                                 │
    │        • • • •    • •           │ ← Ferrofluido sin offset ❌
    │      •  •  •   •   •  •  •      │
    │     •    •    •   •   •   •     │
    │                                 │
    │ (0,300)             (400,300)   │
    └─────────────────────────────────┘
    Screen pos: (50, 80)

KEY:
  ◆       = orbe (posición real)
  ●───●   = ANILLOS sagrados (dibujados en cx+offset ✅)
  • • •   = Ferrofluido núcleo/aura (dibujado sin offset ❌)
  ╱   ╲   = Distancia visual entre capas = EL BUG
```

---

## TIMELINE DIAGRAMA

```
TIEMPO →

[00] START: Usuario solicita movimiento autónomo
     └─ _pos_objetivo = (400, 200)

[01] _expandir_ventana_transito() CALLED
     ├─ Calcula nuevo bounding box (origen → destino)
     ├─ RESIZE ventana: 180×180 → 400×300
     ├─ MOVE ventana: (100,100) → (50,80)
     └─ CALCULA: _render_offset_x = -60, _render_offset_y = -40

[02-50] INTERPOLACIÓN ANIMADA
     Cada frame (~33ms a 30fps):
     ├─ _interpolar_movimiento() actualiza offsets
     │  _render_offset_x: -60 → -50 → -40 → ... → 0
     │  _render_offset_y: -40 → -30 → -20 → ... → 0
     │
     └─ paintEvent() renderiza
        ├─ ANILLOS:     cx = center.x() + offset  ✅ CORRECTO
        └─ FERROFLUIDO: cx = width//2 (SIN offset)❌ INCORRECTO

[51] ARRIVAL: dist < 2.0 pixels
     ├─ Fijar: _render_offset = FINAL_VALUE
     └─ _pos_objetivo = None

[52] COLLAPSE WINDOW
     ├─ RESIZE: 400×300 → 220×220
     ├─ MOVE: (50,80) → FINAL_POSITION
     └─ RESET: _render_offset_x = 0, _render_offset_y = 0

[53+] REPOSO
     └─ Volver a rendering normal (offset = 0)
```

---

## TRACE DETALLADO DE UNA INTERPOLACIÓN

```
FRAME 1 (Frame inicial del tránsito):
─────────────────────────────────────
_render_offset_x = -60
_render_offset_y = -40

paintEvent():
  cx = 200 + (-60) = 140
  cy = 150 + (-40) = 110
  
  ANILLOS:      dibujar en (140, 110) ✅
  FERROFLUIDO:  dibujar en (200, 150) ❌
  
  DESALIGNMENT: 60 pixeles X, 40 pixeles Y
  DISTANCIA: sqrt(60² + 40²) = sqrt(5200) ≈ 72 pixeles


FRAME 2 (Interpolación avanza):
─────────────────────────────
_render_offset_x = -50
_render_offset_y = -30

paintEvent():
  cx = 200 + (-50) = 150
  cy = 150 + (-30) = 120
  
  ANILLOS:      dibujar en (150, 120) ✅
  FERROFLUIDO:  dibujar en (200, 150) ❌
  
  DESALIGNMENT: 50 pixeles X, 30 pixeles Y
  DISTANCIA: sqrt(50² + 30²) ≈ 58 pixeles


FRAME 25 (Casi llegada):
──────────────────────
_render_offset_x = -2
_render_offset_y = -1

paintEvent():
  cx = 200 + (-2) = 198
  cy = 150 + (-1) = 149
  
  ANILLOS:      dibujar en (198, 149) ✅
  FERROFLUIDO:  dibujar en (200, 150) ❌
  
  DESALIGNMENT: 2 pixeles X, 1 pixel Y
  DISTANCIA: sqrt(4 + 1) ≈ 2 pixeles (visual jitter)


FRAME 26 (ARRIVAL):
──────────────────
dist < 2.0, collapse iniciado
_render_offset_x → 0
_render_offset_y → 0

RESET offset after collapse:
_render_offset_x = 0
_render_offset_y = 0
```

---

## ¿POR QUÉ NO SE VE EL BUG EN TODA INTERPOLACIÓN?

```
Visibility del bug depende de SEPARACIÓN entre centro expandido y orbe:

PEQUEÑA SEPARACIÓN (margen ≈ 40px):
└─ offset pequeño (~10px)
   └─ desalignment apenas visible
   └─ Puede parecer "fluidez normal"

GRANDE SEPARACIÓN (ventana expandida muy grande):
└─ offset grande (~60px)
   └─ desalignment muy visible
   └─ Anillos se "estiran" lejos del ferrofluido ← BUG EVIDENTE

EJEMPLO REAL:
  Origen: (100, 100), Destino: (900, 100)
  Distancia: 800 pixeles horizontal
  Ventana expandida: ~900×200px
  Centro ventana: (950, 150)
  Offset inicial: ~150 pixeles
  └─ DESALIGNMENT VISIBLE: Anillos muy desplazados
```

---

## SOLUCIÓN VISUAL (OPCIÓN A)

```
CAMBIO EN: animador_orbe_4d.py::renderizar()

ANTES (❌ BUG):
┌─ renderizar(painter, width, height, ...) ─┐
│ cx, cy = width // 2, height // 2          │
│ └─ Ignora offset completamente             │
└──────────────────────────────────────────┘

DESPUÉS (✅ FIX):
┌─ renderizar(painter, width, height,       ┐
│              offset_x=0, offset_y=0, ...)  │
│                                            │
│ cx = width // 2 + offset_x                 │
│ cy = height // 2 + offset_y                │
│ └─ Aplica offset correctamente             │
└────────────────────────────────────────┘

LLAMADA EN ventana_principal.py:

ANTES:
  self._animador.renderizar(
    painter,
    self.width(),
    self.height(),
    ...
  )

DESPUÉS:
  self._animador.renderizar(
    painter,
    self.width(),
    self.height(),
    offset_x=int(self._render_offset_x),  ← NUEVO
    offset_y=int(self._render_offset_y),  ← NUEVO
    ...
  )
```

---

## VERIFICACIÓN POST-FIX

```
FRAME DURANTE TRÁNSITO (MISMO ESCENARIO ANTERIOR):
──────────────────────────────────────────────────

_render_offset_x = -60
_render_offset_y = -40

paintEvent():
  cx = 200 + (-60) = 140
  cy = 150 + (-40) = 110
  
  ANILLOS:      dibujar en (140, 110) ✅
  FERROFLUIDO:  
    ├─ Llamada: renderizar(..., offset_x=-60, offset_y=-40)
    ├─ DENTRO: cx = 200 + (-60) = 140     ← AHORA APLICADO ✅
    ├─ DENTRO: cy = 150 + (-40) = 110     ← AHORA APLICADO ✅
    └─ dibujar en (140, 110) ✅
  
  ALINEACIÓN: ✅ PERFECTA
  DISTANCIA: 0 pixeles (mismo punto de renderización)
```

