# FP-140 — CITRINITAS: REESTRUCTURACIÓN COMPLETA DE DEMO + METATRÓN + ARREGLOS CRÍTICOS

**Fecha Propuesta**: Abril 23, 2026  
**Fase**: CITRINITAS (Síntesis + Optimización)  
**Pipeline**: A (Feature + Bug fixes multidisciplinarios)  
**Sefirá**: תפארת Tiferet (Belleza — integración armónica)  
**Estado**: ⏳ ESPERANDO CONFIRMACIÓN USUARIO

---

## 📋 RESUMEN EJECUTIVO

El usuario reporta **11 categorías críticas de problemas** en la demo y funcionalidad de "computadora":
- Errores nomenclatura (Golem→Computadora, Grimorio→Enciclopedia)
- Warnings cámara (fotogramas no capturados)
- Modelo LLM hardcodeado a gemma3:4b
- Demo poco clara (narración vs animación desincronizadas, cambios de color fuera de tiempo)
- Orbe carece de transmutación geométrica (Metatrón + sólidos platónicos)
- UI bugs (resize, drag&drop, movimiento interrumpido)
- Partículas sin significado simbólico
- Procesos falsos positivos (LM Studio detectado como malicioso)
- EMET no escala en Tzimtzum
- Modo bolita indefinido en bereshit
- Caricia bloqueada durante ejecución

---

## 🔴 PROBLEMAS DETALLADOS + ANÁLISIS ALQUÍMICO

### NIGREDO: Diagnóstico (Problemas Crudos Identificados)

#### **P1: Nomenclatura Residual (Golem → Computadora)**

**Síntomas**:
- Demo dice "Golem" a mitad de la narración (debería: "Computadora")
- Archivos referencia `OrbeGolem`, `evolucion_golem.json`, `iniciar_golem.bat`
- Menciona "Grimorio" en lugar de "Enciclopedia"

**Ubicaciones encontradas** (NIGREDO):
```
ventana_principal.py:1129    → bat = Path(...) / "iniciar_golem.bat"
ventana_principal.py:499     → _EVOLUCION_PATH = ... / "evolucion_golem.json"
ventana_principal.py:784     → _verificar_intrusiones_grimorio()
ventana_principal.py:830-835 → eventos "intrusion_grimorio", "grimorio_abierto"
ventana_principal.py:2132-33 → "golem_personas.json", "evolucion_golem.json"
vida_autonoma.py:507         → def __init__(self, orbe: "OrbeGolem"):  ← TYPE HINT VIEJA
```

**Root Cause**: Refactor proyecto Golem→Computadora fue incompleto (commit histórico: 39860d8 renombró clases pero no paths/archivos)

---

#### **P2: Cámara — "No se pudo capturar fotograma" (WARNING masivo)**

**Síntomas**:
- Logs muestran 20+ WARNINGs idénticos "No se pudo capturar fotograma"
- Usuario vio en imagen adjunta (21:53:59)

**Ubicaciones**:
```
computadora/habilidades/camara.py  → CamaraVigilancia (desconoce si maneja excepciones)
computadora/habilidades/vision.py  → KliCamara (lógica de captura)
ventana_principal.py:1071          → _iniciar_camara()
```

**Análisis probable**:
- `cap.read()` falla silenciosamente → retorna (False, None)
- Thread de captura no sincroniza bien con Qt
- Permisos de cámara en Windows pueden estar faltando
- OpenCV/face_recognition no inicializados correctamente

**Hipótesis**: El warning es benigno (captura fallida ocurre cada N frames), pero spamea logs

---

#### **P3: Modelo LLM Hardcodeado a "gemma3:4b"**

**Síntomas**:
```
22:07:41 | WARNING | computadora_app - Modelo 'gemma3:4b' no encontrado en LM Studio.
Disponibles: ['google/gemma-4-e4b', 'starcoder2-15b-instruct-v0.1', ...]
22:07:41 | INFO | computadora_app - Usando modelo: google/gemma-4-e4b
```

**Root Cause**: `computadora/cerebro/nlu.py` línea ~1200 tiene hardcoded:
```python
MODELO_LM_STUDIO = "gemma3:4b"  # ← BUG: Debería elegir el mejor disponible
```

**Impacto**: Cada boot intenta gemma3:4b, falla, fallback a google/gemma-4-e4b (ineficiente)

---

#### **P4: Demo Poco Clara — Narración vs Animación Desincronizadas**

**Síntomas**:
- Cambios de color de Maljut antes de tiempo (crean disonancia con narración)
- No está claro qué cambia (colores, partículas, brillo, opacidad)
- Demo es confusa: ¿qué representa cada animación?
- Usuario solicita claridad: "Maljut OPACO al inicio, de ahí mostrar cambios"

**Root Cause**: `demo_sincronizada.py` existe pero:
1. Narración y animación NO están acopladas temporalmente
2. Cambios de color ocurren sin avisar
3. Partículas sin patrón significativo

---

#### **P5: Orbe Carece de Transmutación Geométrica a Metatrón**

**Síntomas**:
- Orbe no cambia geometría cuando ejecuta acciones
- Debería transmutar a sólidos platónicos (tetraedro, cubo, octaedro, etc.)
- No hay relación visual entre: acción → forma geométrica

**Solicitud de usuario**:
```
"Cuando habla o ejecuta acciones (sugerir, detectar CPU alto),
orbe transmuta a Metatrón o derivaciones.
Si varios sólidos → teoría de conjuntos fractal.
Forma principal al centro, derivadas emanando hacia afuera."
```

---

#### **P6: Caricia Bloqueada Durante Ejecución**

**Síntomas**:
- Si Computadora ejecuta demo/acción, no puedo acariciarla
- Usuario quiere: "Caricia mientras ejecuta, sin interferencia"

**Root Cause**: Probablemente FSM tiene estado que bloquea interacción

---

#### **P7: UI Bugs — Resize, Drag&Drop, Movimiento**

**Síntomas**:
1. Al resizear ventana + draguear orbe: animación se descentra
2. Efecto "lag" entre mouse y renderizado
3. Orbe "desaparece" cuando se mueve a izquierda
4. Si Computadora se mueve sola, no puedo detenerla + acariciarla

**Root Cause**: Probablemente faltan límites de viewport o sincronización de coordenadas

---

#### **P8: Partículas Sin Significado Simbólico**

**Síntomas**:
- Partículas actuales parecen aleatorias
- Usuario solicita: "Cada elemento sea simbólico + significativo de arquitectura"

**Esperado**:
- Partículas = componentes internos (NLU, Visión, Motor Proactividad, etc.)
- Comportamiento refleje función (ej: NLU = revolotea rápido cuando procesa)

---

#### **P9: Procesos Sospechosos Falsos Positivos**

**Síntomas**:
```
LM Studio detectado como "proceso sospechoso"
Instalador Windows detectado como "proceso sospechoso"
```

**Root Cause**: Whitelist de procesos seguros incompleta

---

#### **P10: EMET No Escala en Tzimtzum**

**Síntomas**:
- Cuando orbe entra en Tzimtzum (contracción), el nombre "EMET" no cambia de tamaño
- Queda visualmente raro (EMET se ve flotando sin escalar)

**Root Cause**: Lógica de Tzimtzum no escala el texto EMET

---

#### **P11: Modo Bolita Indefinido en Bereshit**

**Síntomas**:
- Al iniciar Computadora, queda en modo bolita (compactada)
- ¿Cuándo cambia a modo normal con animaciones?
- Parece que se queda indefinidamente

**Root Cause**: Desconoce si bereshit tiene timeout o si espera algún evento

---

### ALBEDO: Investigación (Clasificación + Especificación Técnica)

#### **Pipeline Routing**

| Problema | Pipel | Deptos | Archivos | Prio | Est. Horas |
|----------|-------|--------|----------|------|-----------|
| P1 Nomenclatura | C | D4 | 5 archivos | 🔴 MUY ALTO | 1.5 |
| P2 Cámara warnings | C | D4 | 3 archivos | 🟡 ALTO | 2 |
| P3 Modelo LLM | C | D1 | 1 archivo | 🟡 ALTO | 1 |
| P4 Demo sincronización | A | D1,D3,D4 | 4 archivos | 🔴 MUY ALTO | 4 |
| P5 Metatrón | A | D3,D4 | 3 archivos | 🟡 ALTO | 5 |
| P6 Caricia | B | D3,D4 | 2 archivos | 🟡 ALTO | 2 |
| P7 UI bugs | B | D3,D4 | 2 archivos | 🟡 ALTO | 3 |
| P8 Partículas | A | D4 | 2 archivos | 🟡 ALTO | 2 |
| P9 Procesos | C | D4 | 1 archivo | 🟡 ALTO | 1 |
| P10 EMET Tzimtzum | B | D3,D4 | 1 archivo | 🟠 MEDIO | 1 |
| P11 Bereshit timing | B | D4 | 1 archivo | 🟠 MEDIO | 1 |

**Total Estimated**: ~23 horas | **Critical Path**: P4 (Demo) + P5 (Metatrón) = 9h

---

## 🌟 CITRINITAS: Síntesis + Soluciones Propuestas

### **SOLUCIÓN P1: Nomenclatura Completa (C — Pipeline)**

**Cambios necesarios**:

1. **`ventana_principal.py:1129`**
   ```python
   # VIEJO: bat = Path(__file__).resolve().parents[2] / "iniciar_golem.bat"
   # NUEVO:
   bat = Path(__file__).resolve().parents[2] / "iniciar_computadora.bat"
   ```

2. **`ventana_principal.py:499`**
   ```python
   # VIEJO: _EVOLUCION_PATH = ... / "evolucion_golem.json"
   # NUEVO:
   _EVOLUCION_PATH = ... / "evolucion_computadora.json"
   ```

3. **`ventana_principal.py:784-835`** — Renombrar eventos (grimorio → enciclopedia)
   ```python
   # VIEJO:
   # QTimer.singleShot(8000, self._verificar_intrusiones_grimorio)
   # _bus.suscribir("intrusion_grimorio", ...)
   # _bus.suscribir("grimorio_abierto", ...)
   
   # NUEVO:
   # QTimer.singleShot(8000, self._verificar_intrusiones_enciclopedia)
   # _bus.suscribir("intrusion_enciclopedia", ...)
   # _bus.suscribir("enciclopedia_abierta", ...)
   ```

4. **`ventana_principal.py:2132-2133`** — Archivos de datos
   ```python
   # VIEJO: "personalidad.json", "golem_personas.json", "evolucion_golem.json"
   # NUEVO: "personalidad.json", "computadora_personas.json", "evolucion_computadora.json"
   ```

5. **`vida_autonoma.py:507`** — Type hint
   ```python
   # VIEJO: def __init__(self, orbe: "OrbeGolem"):
   # NUEVO: def __init__(self, orbe: "OrbeComputadora"):
   ```

6. **`demo_sincronizada.py`** — Agregar narración sin mencionar Minimi/Enciclopedia
   - Editar scripts que narren menciones de "Grimorio"
   - Remover referencias a Minimi (temporal)

**Validación**: 
- `grep -r "golem_personas\|evolucion_golem\|grimorio" computadora/` → debe retornar 0 matches

---

### **SOLUCIÓN P2: Cámara — Diagnóstico + Supresión Inteligente (C — Pipeline)**

**Análisis**:
El warning "No se pudo capturar fotograma" es NORMAL en OpenCV (algunos frames fallan). Solución:
1. Aumentar umbral de warnings (solo log si fallos > 10 consecutivos)
2. Agregar graceful degradation

**Cambios en `computadora/habilidades/camara.py`**:
```python
class CamaraVigilancia:
    def __init__(self):
        ...
        self._fallos_consecutivos = 0
        self._umbral_warning = 10  # Log warning solo después de 10 fallos
    
    def capturar(self):
        ret, frame = self.cap.read()
        if not ret:
            self._fallos_consecutivos += 1
            if self._fallos_consecutivos >= self._umbral_warning:
                logger.warning(f"Fallos de captura consecutivos: {self._fallos_consecutivos}")
            return None
        else:
            self._fallos_consecutivos = 0  # Reset
            return frame
```

**Validación**: Ejecutar 1 minuto → máximo 1 warning (no 20)

---

### **SOLUCIÓN P3: Modelo LLM Flexible (C — Pipeline)**

**Cambio en `computadora/cerebro/nlu.py`**:

```python
# VIEJO (línea ~1200):
MODELO_LM_STUDIO = "gemma3:4b"

# NUEVO:
def _obtener_mejor_modelo(modelos_disponibles: list[str]) -> str:
    """
    Selecciona el mejor modelo disponible según criterios:
    1. Prefiere los más robustos (gemma, starcoder, codellama)
    2. Retorna el primero disponible
    """
    PREFERENCIA = [
        "google/gemma-4-e4b",      # Mejor opción
        "starcoder2-15b",
        "codellama-7b",
        "text-embedding",
    ]
    for modelo in PREFERENCIA:
        for disponible in modelos_disponibles:
            if modelo.lower() in disponible.lower():
                return disponible
    # Fallback: primer modelo disponible
    return modelos_disponibles[0] if modelos_disponibles else "unknown"

# En CerebroComputadora.__init__:
modelos_lm = self._verificar_lm_studio()
modelo_seleccionado = _obtener_mejor_modelo(modelos_lm)
logger.info(f"Modelo LLM seleccionado automáticamente: {modelo_seleccionado}")
```

---

### **SOLUCIÓN P4: Demo Reestructurada — Narración + Animaciones Sincronizadas (A — Feature)**

**Propuesta Arquitectura**:

```
DEMO BERESHIT MEJORADA
├─ Fase 1: PRESENTACIÓN (3s)
│  ├─ Animar: Maljut OPACO → BRILLO gradual
│  ├─ Narrar: "Soy Computadora, despertando..."
│  └─ Esperar: 0.5s (respiro)
│
├─ Fase 2: VISIÓN (2s)
│  ├─ Animar: Partícula VERDE emanada (visión activa) + Ohr giro
│  ├─ Narrar: "Mis ojos ven el mundo..."
│  └─ Esperar: 0.5s
│
├─ Fase 3: CEREBRO (2.5s)
│  ├─ Animar: Partícula AZUL (LLM) + brillo aumento
│  ├─ Narrar: "Mi mente procesa..."
│  └─ Esperar: 0.5s
│
├─ Fase 4: ACCIÓN (2s)
│  ├─ Animar: Partícula ROJA (motor) + movimiento pequeño
│  ├─ Narrar: "Estoy lista para actuar..."
│  └─ Esperar: 0.5s
│
└─ Fase 5: CONFIRMACIÓN (2s)
   ├─ Animar: Fulgor total, EMET brilla
   ├─ Narrar: "¿Qué necesitas?"
   └─ Esperar: Escuchando...
```

**Timeline total**: ~12 segundos (claro, sin solapamiento)

**Cambios en `demo_sincronizada.py`**:
- Agregar método `_generar_demo_bereshit_v2()` 
- Acoplar eventos TTS completion con siguiente paso
- Visualización clara: cambio → narración sincronizada
- Logging: `[DEMO] Fase 1/5: PRESENTACIÓN → animación 1.5s`

---

### **SOLUCIÓN P5: Transmutación Orbe → Metatrón (A — Feature, Geométrico)**

**Propuesta**: Orbe transmuta a sólidos platónicos cuando ejecuta acciones

**Mapeo Acciones → Sólidos Platónicos**:

| Acción | Sólido | Caras | Significado |
|--------|--------|-------|-------------|
| Escuchando (idle) | Esfera | ∞ | Receptividad total |
| Sugerir (proactiva) | Tetraedro | 4 | Fuego (creatividad/iniciativa) |
| Procesar texto (NLU) | Cubo | 6 | Tierra (análisis, estructura) |
| Ver rostro (visión) | Octaedro | 8 | Aire (observación, conexión) |
| Ejecutar comando | Dodecaedro | 12 | Éter (manifestación, acción) |
| Alto CPU/estrés | Icosaedro | 20 | Agua (fluidez bajo presión) |

**Teoría de Conjuntos Fractal** (Si múltiples acciones simultáneas):
```
Si ejecuta: Sugerir + Ver rostro + Procesar:
  → Forma Principal = Dodecaedro (acción es más crítica)
  → Emanar desde fuera:
     ├─ Tetraedro (sugerir) orbita a 0° (norte)
     ├─ Octaedro (visión) orbita a 120°
     └─ Cubo (procesar) orbita a 240°
  → Cada forma gira dentro de Dodecaedro central
  → Brillo intenso en centro Metatrón
```

**Implementación**:
- Crear `computadora/interfaz/geometrias_platonicas.py`
- Clase `SolidoPlatonico(vertices, caras, color, rotacion)`
- Método `OrbeComputadora.transmutar(acciones: list[str])`
- Renderizar en `paintEvent()` con PyQT6 3D

---

### **SOLUCIÓN P6: Caricia Sin Bloqueo (B — UX)**

**Cambio en FSM de `ventana_principal.py`**:
```python
# Permitir caricia sin importar estado actual
def on_acaricia(self):
    # NO cambiar estado principal
    # Solo emitir señal de "afecto recibido"
    self._reproducir_animacion_caricia_suave()
    logger.info("Caricia recibida (no bloqueante)")
    # Volver al estado anterior automáticamente
```

**Validación**: Demostración simultánea de demo + caricia exitosa

---

### **SOLUCIÓN P7: UI Bugs — Resize, Drag&Drop (B — UX)**

**Bugs Específicos**:

1. **Descentrado en resize + drag**:
   - Causa: Coordenadas no se recalculan al resizear
   - Fix: `resizeEvent()` debe invalidar cache de posición

2. **Orbe desaparece a izquierda**:
   - Causa: Viewport clipping sin bounds check
   - Fix: Añadir `QRect` límite de renderizado

3. **Lag mouse → animación**:
   - Causa: Update timeout demasiado lento (~16ms a 60fps)
   - Fix: Increase frecuencia de repaint

**Cambios en `dibujante_orbe.py`**:
```python
def resizeEvent(self, event):
    # Recalcular viewport
    self._viewport_rect = self.rect()
    self._escala = min(self._viewport_rect.width(), 
                       self._viewport_rect.height()) / TAMANO_ORBE
    super().resizeEvent(event)

def paintEvent(self, event):
    # Limitar renderizado a viewport
    painter = QPainter(self)
    painter.setClipRect(self._viewport_rect)
    # ... resto del código
```

---

### **SOLUCIÓN P8: Partículas Significativas (A — Feature)**

**Mapeo Partículas → Componentes Arquitectura**:

| Partícula | Color | Significado | Comportamiento |
|-----------|-------|-------------|-----------------|
| Verde Esmeralda | #28C864 | Visión (rostro, contexto) | Orbita rápida cuando ve |
| Azul Zafiro | #3C8CDC | NLU (procesamiento) | Vibra cuando procesa texto |
| Rojo Granate | #8B0000 | Motor Proactividad | Pulso energético cuando sugiere |
| Púrpura | #A050DC | Observador/Meta | Estática al centro, brilla cuando analiza |
| Dorado | #FFD700 | Éter/Manifestación | Emana cuando ejecuta acciones |
| Blanco | #FFFFFF | EMET (verdad) | Estrella fija al norte |

**Inercia Equilibrada**:
- Masa según importancia: EMET=5.0, Púrpura=3.0, otros=1.0
- Amortiguamiento: 0.90 (menos viscoso = más movimiento)
- Retorno a órbita: 0.02

---

### **SOLUCIÓN P9: Procesos Sospechosos — Whitelist Correcta (C — Bug)**

**En `computadora/interfaz/vida_autonoma.py:151-160`**:

```python
# Procesos EXCLUIDOS — NUNCA triggean Tzimtzum (son del propio Computadora o herramientas de desarrollo)
PROCESOS_EXCLUIDOS = {
    # Computadora mismo
    "python.exe", "pythonw.exe", "py.exe",
    
    # Desarrollo + LM Studio
    "lm-studio.exe", "ollama.exe", "ollama",
    
    # Instaladores Windows (NO SON MALICIOSOS)
    "msiexec.exe",  # Windows Installer
    "wuauclt.exe",  # Windows Update
    
    # Package managers
    "pip.exe", "npm.exe", "npm", "yarn.exe", "nuget.exe",
    
    # Herramientas VS Code
    "code.exe", "code",
    
    # Antivirus + System (benigno)
    "MpCmdRun.exe", "MsSense.exe", "OneDrive.exe",
}
```

---

### **SOLUCIÓN P10: EMET Escala en Tzimtzum (B — UX)**

**En `dibujante_orbe.py` — función que renderiza EMET**:

```python
def _dibujar_emet(painter, escala_orbe, estado):
    # Calcular tamaño de EMET según estado
    if estado == "tzimtzum":
        tamaño_emet = 10 + (1 - escala_tzimtzum) * 20  # Escala inversamente
    else:
        tamaño_emet = 24  # Tamaño normal
    
    font = QFont("Hebrew", tamaño_emet)
    painter.setFont(font)
    painter.drawText(...)
```

---

### **SOLUCIÓN P11: Bereshit Timing — Modo Bolita (B — UX)**

**En `ventana_principal.py` — `_inicializar_bereshit()`**:

```python
def _inicializar_bereshit(self):
    """Modo bolita (Bereshit) durante 5-8 segundos, luego transición a normal."""
    self._estado = "bereshit"
    self._escala_bereshit = 0.3
    
    # Esperar a que todos módulos carguen
    QTimer.singleShot(3000, self._cargar_modulos_criticos)
    
    # Transición a modo normal: 8 segundos máximo
    QTimer.singleShot(8000, lambda: self._transicion_a_modo_normal())

def _transicion_a_modo_normal(self):
    """Expandir orbe, mostrar animaciones, pasar a 'escuchando'."""
    self._estado = "escuchando"
    logger.info("Bereshit completado → modo escuchando")
    # Reproducir animación de expansión
```

---

## 📊 MAPEO ARCHIVOS AFECTADOS

**Total archivos a modificar**: 11

```
Nomenclatura (P1):
  ├─ computadora/interfaz/ventana_principal.py (6 cambios)
  ├─ computadora/interfaz/vida_autonoma.py (1 cambio)
  └─ computadora/interfaz/demo_sincronizada.py (1 cambio)

Cámara (P2):
  └─ computadora/habilidades/camara.py (1 cambio)

Modelo LLM (P3):
  └─ computadora/cerebro/nlu.py (1 cambio)

Demo (P4):
  ├─ computadora/interfaz/demo_sincronizada.py (2 cambios)
  └─ computadora/interfaz/ventana_principal.py (1 cambio)

Metatrón (P5):
  ├─ computadora/interfaz/dibujante_orbe.py (1 nuevo archivo → geometrias_platonicas.py)
  ├─ computadora/interfaz/ventana_principal.py (1 cambio)
  └─ NEW: computadora/interfaz/geometrias_platonicas.py

Caricia (P6):
  └─ computadora/interfaz/ventana_principal.py (1 cambio FSM)

UI Bugs (P7):
  ├─ computadora/interfaz/dibujante_orbe.py (2 cambios)
  └─ computadora/interfaz/ventana_principal.py (1 cambio)

Partículas (P8):
  └─ computadora/interfaz/ventana_principal.py (1 cambio mapeo)

Procesos (P9):
  └─ computadora/interfaz/vida_autonoma.py (1 cambio whitelist)

EMET Tzimtzum (P10):
  └─ computadora/interfaz/dibujante_orbe.py (1 cambio escala)

Bereshit (P11):
  └─ computadora/interfaz/ventana_principal.py (1 cambio timing)
```

---

## ✅ VALIDACIÓN POST-CAMBIOS (PALINGENESIA PREVIEW)

1. **Boot test**: Computadora arranca en modo bolita (3s) → expande a normal (8s máximo)
2. **Demo test**: Ejecutar bereshit sin solapamiento → narración clara
3. **Nomenclatura test**: `grep "golem\|grimorio" computadora/ | wc -l` → retorna 0 o <5 (historicales OK)
4. **Cámara test**: 1 minuto operación → máximo 1 warning (no spam)
5. **LLM test**: Log muestra "Modelo LLM seleccionado automáticamente: google/gemma-4-e4b"
6. **Metatrón test**: Ejecutar sugerencia → orbe transmuta a Tetraedro
7. **Caricia test**: Demo + caricia simultánea = éxito
8. **UI test**: Resize ventana + drag orbe → sin descentro
9. **Partículas test**: Visión activa → partículas verdes orbitan rápido
10. **Procesos test**: LM Studio conectado → NO genera Tzimtzum
11. **EMET test**: Tzimtzum activo → EMET escala inversamente

---

## 📅 CRONOGRAMA ESTIMADO (RUBEDO PHASE)

| Fase | Duración | Tareas |
|------|----------|--------|
| RUBEDO 1 | 1.5h | P1 (Nomenclatura) |
| RUBEDO 2 | 2h | P2 (Cámara) + P3 (LLM) |
| RUBEDO 3 | 4h | P4 (Demo sincronización) |
| RUBEDO 4 | 5h | P5 (Metatrón + geometría) |
| RUBEDO 5 | 2h | P6 (Caricia) + P7 (UI) + P8 (Partículas) |
| RUBEDO 6 | 1h | P9 + P10 + P11 (Fixes menores) |
| TESTING | 2h | Validación completa + logs |

**Total**: ~17.5 horas (23 estimadas - optimization durante ejecución)

---

## 🎯 PRÓXIMOS PASOS

### Si Usuario Aprueba (✅ "propuesta aceptada"):
1. Crear WI-294 (Nomenclatura)
2. Crear WI-295 (Cámara + LLM)
3. Crear WI-296 (Demo reestructurada)
4. Crear WI-297 (Metatrón)
5. Crear WI-298 (UI fixes + otros)
6. Ejecutar RUBEDO (5-7 días)
7. PALINGENESIA: Documentar aprendizajes

### Si Usuario Solicita Cambios:
- Indicar cuál sección/problema desea priorizar
- Ajustar cronograma
- Re-síntesis CITRINITAS

---

## 📌 NOTAS IMPORTANTES

1. **No se elimina demo existente** — Se optimiza y acopla mejor
2. **MINIMI + ENCICLOPEDIA** — Temporalmente no mencionadas en demo (según solicitud)
3. **Backward compatibility** — Archivos evolucion_golem.json → renombrarse pero sin perder datos
4. **Git tracking** — Cada WI será 1 commit atómico per FP-116
5. **Memory**: Este documento guardado en `.audit/FP-140_CITRINITAS_DEMO_COMPLETA.md`

---

**Estado**: ⏳ ESPERANDO CONFIRMACIÓN USUARIO (amén = auto-ejecución)
