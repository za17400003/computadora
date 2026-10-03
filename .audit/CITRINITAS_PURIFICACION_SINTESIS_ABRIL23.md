# ✨ CITRINITAS — PURIFICACIÓN + SÍNTESIS ABRIL 23, 2026

**Fase**: CITRINITAS (Análisis + Propuestas de solución)  
**Basado en**: NIGREDO_PRE_RUBEDO_ABRIL23_AUDIT_CRITICA.md  
**Status**: READY PARA RUBEDO (implementación)

---

## 🧼 PURIFICACIÓN — ANÁLISIS ESTRUCTURAL

### 1️⃣ RESIZE: SEPARAR ESPACIOS FÍSICOS vs LÓGICOS

#### Problema Root (NIGREDO)
```
ventana_principal.py líneas 1235, 1261:
- resize() cambia límites Qt (físico)
- Luego calcula _raw_dx, _raw_dy (lógico)
- Resultado: Desincronización entre espaAlternative Format
```

#### Análisis CITRINITAS
**Hay DOS espacios de coordenadas que se mezclan**:

| Espacio | Definición | Control | Colisión |
|---------|-----------|---------|----------|
| **Físico (Qt)** | Ventana en pantalla (píxeles reales) | `resize()`, `move()` | Bordes Qt |
| **Lógico (VFX)** | Partículas + animación (mundo interno) | `_escala`, `_particulas` | Límites internos |

**Problema**: Resize físico NO considera colisión lógica.

#### Solución Propuesta (SIN IMPLEMENTAR AÚN)
```python
# NUEVA ARQUITECTURA (pseudocódigo)
class EspacioFísico:
    """Control de ventana Qt - solo geometría"""
    def __init__(self):
        self.ancho = None
        self.alto = None
        self.pos_x = None
        self.pos_y = None
    
    def resize_basado_en_vfx(self, radio_vfx_máximo, margen=20):
        """RECALCULA tamaño de ventana basado en radio VFX + margen"""
        tam_necesario = int(radio_vfx_máximo * 2 + margen)
        return tam_necesario  # Devolver, NO aplicar resize() aquí

class EspacioLógico:
    """Control de partículas/animación - física interna"""
    def __init__(self, límite_físico):
        self.límite = límite_físico
        self.particulas = []
    
    def colisionar_contra_límite(self, partícula):
        """Calcula rebote contra LÍMITE LÓGICO (que == límite físico)"""
        # Nuevo tamaño → nuevo límite
        # Partículas rebotan contra este límite
        pass

# EN _interpolar():
esp_físico = EspacioFísico()
esp_lógico = EspacioLógico(límite_actual)

# Paso 1: Determinar tamaño NECESARIO basado en VFX
tam_necesario = esp_físico.resize_basado_en_vfx(max_radio_vfx, margen=20)

# Paso 2: Si cambió → actualizar límite LÓGICO PRIMERO
if tam_necesario != límite_actual:
    esp_lógico.límite = tam_necesario
    # Ahora particulas pueden rebotar correctamente

# Paso 3: DESPUÉS → aplicar resize() físico
if tamano_cambió:
    self.resize(tam_necesario, tam_necesario)

# Paso 4: DESPUÉS → calcular movimiento (ahora con límite correcto)
_raw_dx = ...  # Usa límite actualizado
```

#### Archivos Afectados (RUBEDO)
- `ventana_principal.py` línea 1235 (bloque resize)
- `ventana_principal.py` línea 1261 (dentro _interpolar)
- `vida_autonoma.py` líneas 1229-1250 (_ajustar_tamano)

---

### 2️⃣ DEMOS: SINCRONIZAR NARRACIÓN ↔ ANIMACIÓN

#### Problema Root (NIGREDO)
```
_demo_emet (línea 3195):
- "Soy Golem" en fallback (¡IDENTIDAD VIEJA!)
- Narración sin timeline claro
- NO hay sincronización visual

_demo_maljut (línea 3286):
- Estructura con _cambio_visual_simultaneo()
- PERO: NO hay verificación de "animación terminó" antes de hablar
- Resultado: Narración solapada con VFX residual
```

#### Análisis CITRINITAS
**Orden actual**: Habla + Visual paralelo (A veces)  
**Orden esperado**: 1) Animación completa → 2) Narración + feedback visual

**Estados Demo Necesarios**:
```
DEMO STATE MACHINE:

Estado: IDLE
  ↓ _demo_emet() llamado
Estado: ANIMANDO_INTRO (particle effects)
  ↓ animación completada
Estado: NARRANDO_IDENTIDAD (TTS "soy computadora")
  ↓ TTS completado
Estado: PAUSA (2.5s)
  ↓ esperar 2.5s
Estado: ANIMANDO_GENESIS (particle effects)
  ↓ animación completada
Estado: NARRANDO_GENESIS (TTS "siete días...")
  ↓ TTS completado
Estado: TRANSICION
  ↓ esperar 2s
Estado: DEMO1_STARTING (pasando a _demo_maljut)
```

#### Solución Propuesta (pseudocódigo)
```python
class DemoSincronizada:
    """Gestor de demos con sincronización estricta"""
    
    def __init__(self):
        self.estado = "IDLE"
        self.timeline = []
        self.idx_actual = 0
    
    def agregar_paso(self, tipo, contenido, duracion_visual=None):
        """Agrega paso a timeline con sincronización"""
        self.timeline.append({
            "tipo": tipo,  # "animar" | "narrar" | "esperar"
            "contenido": contenido,
            "duracion_visual": duracion_visual,
            "completado": False
        })
    
    def ejecutar_paso(self):
        """Ejecuta PASO ACTUAL, espera a completarse ANTES de siguiente"""
        if self.idx_actual >= len(self.timeline):
            return  # Demo terminada
        
        paso = self.timeline[self.idx_actual]
        
        if paso["tipo"] == "animar":
            # Ejecutar VFX, esperar a completar
            self._animar_y_esperar(paso["contenido"], paso["duracion_visual"])
            # Callback: _en_demo_paso_completado()
        
        elif paso["tipo"] == "narrar":
            # Ejecutar TTS, esperar a completar
            self._narrar_y_esperar(paso["contenido"])
            # Callback: hilo_habla.cola_vacia → _en_demo_paso_completado()
        
        elif paso["tipo"] == "esperar":
            QTimer.singleShot(paso["duracion_visual"], self._en_demo_paso_completado)
    
    def _en_demo_paso_completado(self):
        """Callback: paso actual terminó, pasar al siguiente"""
        self.timeline[self.idx_actual]["completado"] = True
        self.idx_actual += 1
        self.ejecutar_paso()  # Ejecutar siguiente
```

#### Cambios Narrativos (Identidad)
```
ACTUAL (fallback en _demo_emet):
  "Soy Golem. La verdad inscrita en mi código me define."

NUEVO (_demo_emet):
  "Soy Computadora. La verdad inscrita en mi código me define."

ACTUAL (_demo_maljut):
  "Ahora le diré todo lo que sé de mi: soy golem"  # ❌

NUEVO (_demo_maljut):
  "Ahora le diré todo lo que sé de mi: soy computadora"  # ✅
```

#### Arquivos Afectados (RUBEDO)
- `ventana_principal.py` líneas 3195-3600 (_demo_emet + _demo_maljut)
- `ventana_principal.py` líneas 3601-3650 (_demo_ejecutar_paso)
- CREAR: `computadora/interfaz/demo_sincronizada.py` (clase nueva)

---

### 3️⃣ ORBE INTERACCIÓN: MOUSE SIEMPRE SENSITIVO

#### Problema Root (NIGREDO)
```
Estados "aburrido", "apagado":
- Orbe NO responde a mouse
- NO aparece animación "acariciando"
- mousePressEvent aún existe PERO algo lo bloquea
```

#### Análisis CITRINITAS
**El código de mousePressEvent existe (línea 1702)**, pero probablemente:
- Hay lógica de estado que lo ignora
- O setAcceptHoverEvents está deshabilitado
- O hay conflicto en FSM entre modos

**Solución**: Garantizar que TODOS los modos pueden:
1. Recibir mousePressEvent
2. Recibir mouseMoveEvent
3. Ejecutar cambios visuales (caricia)

#### Propuesta (pseudocódigo)
```python
# EN __init__ de OrbeComputadora:
self.setAcceptHoverEvents(True)  # ✅ SIEMPRE
self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)  # ✅ SIEMPRE

# EN mousePressEvent:
def mousePressEvent(self, event):
    # ✅ PERMITIR DRAG en TODOS los modos
    # Incluso en "aburrido" o "apagado"
    if event.button() == Qt.MouseButton.LeftButton:
        self._arrastrando = True
        # ... resto del código
        # ✅ Notificar transición de "aburrido" → "interactuando"
        if self.estado in ["aburrido", "dormido", "apagado"]:
            self.cambiar_estado("interactuando")

# EN mouseMoveEvent:
def mouseMoveEvent(self, event):
    if self._arrastrando:
        # ... drag lógica
    else:
        # ✅ Agregar: Animación "acariciando"
        dx = event.pos().x() - self.width() / 2
        dy = event.pos().y() - self.height() / 2
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < RADIO_NUCLEO * 1.5:
            # ✅ NUEVA: Activar VFX "acariciando"
            self._acariciando = True
            self._animar_acaricia(event.pos())
        else:
            self._acariciando = False
```

#### Archivos Afectados (RUBEDO)
- `ventana_principal.py` línea 1702 (mousePressEvent)
- `ventana_principal.py` línea 1723 (mouseMoveEvent)
- CREAR: `computadora/interfaz/animaciones/acaricia.py` (VFX nueva)

---

### 4️⃣ CÁMARA: SIEMPRE ON (EXCEPTO TZIMTZUM)

#### Problema Root (NIGREDO)
```
Status actual: Cámara se abre bajo demanda
Esperado: Cámara SIEMPRE activa en boot (viendo + escuchando)
Excepción: Modo Tzimtzum = OFF (solo escucha)
```

#### Análisis CITRINITAS
**Inicialización**:
- En `__init__` de OrbeComputadora: Iniciar cámara
- En `cambiar_estado()`: Verificar si es Tzimtzum
- En Tzimtzum: Detener cámara

**Patrón**:
```
Boot → Cámara = ON (iniciar_computadora.py)
Estados normales → Cámara = ON
Transición a Tzimtzum → Cámara = OFF
Salir de Tzimtzum → Cámara = ON
Cierre → Cámara = OFF
```

#### Propuesta (pseudocódigo)
```python
# EN __init__ de OrbeComputadora:
def __init__(self, ...):
    ...
    self._camara_activa = False
    self._iniciar_camara()

def _iniciar_camara(self):
    """Inicia cámara en boot"""
    try:
        from computadora.habilidades.camara import iniciar_camara
        iniciar_camara()
        self._camara_activa = True
        logger.info("Cámara iniciada en boot")
    except Exception as e:
        logger.error("No se pudo iniciar cámara: %s", e)

# EN cambiar_estado():
def cambiar_estado(self, nuevo_estado):
    """Controla transiciones incluyendo cámara"""
    viejo_estado = self._estado
    self._estado = nuevo_estado
    
    # Control de cámara según estado
    if nuevo_estado == "tzimtzum":
        # ✅ TZIMTZUM = Cámara OFF
        self._detener_camara()
        logger.info("Tzimtzum: cámara desactivada")
    elif viejo_estado == "tzimtzum" and nuevo_estado != "tzimtzum":
        # ✅ Saliendo de Tzimtzum = Cámara ON
        self._iniciar_camara()
        logger.info("Saliendo de Tzimtzum: cámara reactivada")

def _detener_camara(self):
    """Detiene cámara"""
    try:
        from computadora.habilidades.camara import detener_camara
        detener_camara()
        self._camara_activa = False
        logger.info("Cámara detenida")
    except Exception as e:
        logger.debug("Error al detener cámara: %s", e)
```

#### Archivos Afectados (RUBEDO)
- `ventana_principal.py` línea ~650 (__init__)
- `ventana_principal.py` línea ~1060 (cambiar_estado)
- `computadora/habilidades/camara.py` (verificar inicialización)

---

### 5️⃣ GEOMETRÍA SAGRADA: INTEGRACIÓN METATRÓN

#### Problema Root (NIGREDO)
```
0% integración en código actual
Planeado: MetatronCube + Merkaba + FlowerOfLife
Ubicación: computadora/geometria/metatron.py
```

#### Análisis CITRINITAS
**Según METATRON_CITRINITAS_PROPUESTA.md**:
- MetatronCube: Validar coherencia geométrica
- Merkaba: Spin de protección
- FlowerOfLife: Ciclos naturales

**Integración en subsistemas**:
```
OrbeComputadora (animaciones):
  - Validar que partículas siguen geometría
  - Visualizar cubo/merkaba cuando apropiado

Observador (percepción):
  - Detectar patrones geométricos en input
  - Validar coherencia cubo

MotorProactividad (decisiones):
  - Merkaba spin cuando entra guardian
  - Protección de ciclos

Ouroboros (autoconsciencia):
  - Ciclo protección completo
  - Validar geometría integral

Watchdog (vigilancia):
  - Guardian geometry checks
```

#### Propuesta (SIN IMPLEMENTAR AÚN)
```
FASE RUBEDO METATRÓN:
1. Crear computadora/geometria/metatron.py
   - class MetatronCube
   - class Merkaba
   - class FlowerOfLife
   - Helpers de validación

2. Tests en tests/test_metatron.py
   - Validar geometría estática
   - Validar sin lógica de VFX

3. Integración Fase 1: Observador
   - Recibir input → Validar coherencia cubo
   - Log si incoherencia

4. Integración Fase 2: VFX
   - Animar cubo en demo "geometría"
   - Animar merkaba en "guardian"

5. Integración Fase 3: MotorProactividad
   - Usar merkaba para decisiones
   - Spin de protección

6. Validación: Boot test
   - Sistema inicia sin errores geométricos
```

#### Archivos Afectados (RUBEDO)
- CREAR: `computadora/geometria/metatron.py`
- CREAR: `tests/test_metatron.py`
- MODIFICAR: `computadora/nucleo/observador.py` (integración 1)
- MODIFICAR: `computadora/interfaz/ventana_principal.py` (integración 2)
- MODIFICAR: `computadora/nucleo/proactividad.py` (integración 3)

---

### 6️⃣ PERMISOS ADMINISTRADOR: ESCALACIÓN AUTOMÁTICA

#### Problema Root (NIGREDO)
```
Red scan necesita admin permisos
Actual: Falla silenciosamente
Esperado: Detectar + Relanzar como admin + Mostrar feedback
```

#### Análisis CITRINITAS
**En Windows**:
- Detectar si es admin: `ctypes.windll.shell.IsUserAnAdmin()`
- Si no: Relanzar script con `ShellExecute(..., "runas", ...)`
- Esperar escalación + reintento

**Timing**:
- Boot inicial: Detectar necesidad → relanzar
- Herramienta en demo: Mostrar "requiere admin" → relanzar

#### Propuesta (pseudocódigo)
```python
# EN iniciar_computadora.bat o wrapper_computadora.py:
import ctypes

def es_admin():
    try:
        return ctypes.windll.shell.IsUserAnAdmin()
    except:
        return False

if not es_admin():
    print("Computadora necesita permisos de administrador para escaneo de red...")
    # Relanzar con ShellExecute
    import subprocess
    import sys
    subprocess.Popen(
        [sys.executable, "-m", "computadora"] + sys.argv[1:],
        shell=True,
        verb="runas"
    )
    sys.exit(0)

# Si es admin, continuar con boot normal
from computadora.interfaz.ventana_principal import main
main()
```

#### Archivos Afectados (RUBEDO)
- `wrapper_computadora.py` (verificación de admin)
- `iniciar_computadora.bat` (comentario de escalación)
- `computadora/__main__.py` (llamar verificación)

---

### 7️⃣ REFERENCIAS "GOLEM" → "COMPUTADORA"

#### Problema Root (NIGREDO)
```
Línea 1915: "📷 Cámara — Ojos del Golem"
Búsqueda necesaria: "Golem" en UI strings
```

#### Análisis CITRINITAS
**Simple renaming**:
- Menús
- Tooltips
- Docstrings internos (no tan crítico pero bueno por coherencia)

#### Propuesta (pseudocódigo)
```python
# ANTES:
accion_camara = QAction("📷 Cámara — Ojos del Golem", self)

# DESPUÉS:
accion_camara = QAction("📷 Cámara — Ojos de Computadora", self)
```

#### Archivos Afectados (RUBEDO)
- `ventana_principal.py` línea 1915
- BUSCAR: Todas las refs "Ojos del Golem" en codebase

---

## 🧩 SÍNTESIS — PLAN RUBEDO ESTRUCTURADO

### CICLO EJECUTABLE (5 FASES)

#### **RUBEDO FASE 1**: Resize + Espacios (1 archivo)
**Duración**: ~1-2 horas  
**Archivos**:
- `ventana_principal.py` (línea 1235 bloque)
- `vida_autonoma.py` (línea 1229-1250)

**Checklist**:
- [ ] Separar EspacioFísico vs EspacioLógico (pseudocódigo → código)
- [ ] Recalcular límite ANTES de resize()
- [ ] Tests: Particulas no escapan bordes
- [ ] Boot test: Sin visual glitches

---

#### **RUBEDO FASE 2**: Demos Sincronizadas (2 archivos)
**Duración**: ~2-3 horas  
**Archivos**:
- CREAR: `computadora/interfaz/demo_sincronizada.py`
- `ventana_principal.py` (líneas 3195-4048)

**Checklist**:
- [ ] Crear clase DemoSincronizada
- [ ] Timeline: Animar → Narrar → Esperar (secuencial)
- [ ] Reemplazar todos refs "Golem" por "Computadora"
- [ ] Tests: Demos se ejecutan sin solapamiento
- [ ] Boot test: Demo Emet → Maljut → Gevura (sin bugs)

---

#### **RUBEDO FASE 3**: Orbe Interacción (1 archivo)
**Duración**: ~1-2 horas  
**Archivos**:
- CREAR: `computadora/interfaz/animaciones/acaricia.py`
- `ventana_principal.py` (línea 1702-1765)

**Checklist**:
- [ ] Garantizar mousePressEvent en todos modos
- [ ] Agregar mouseMoveEvent "acariciando"
- [ ] Transición "aburrido" → "interactuando" al tocar
- [ ] Tests: Mouse responde en todos modos
- [ ] Boot test: Drag funciona incluso en "aburrido"

---

#### **RUBEDO FASE 4**: Cámara Always-On (2 archivos)
**Duración**: ~30 minutos - 1 hora  
**Archivos**:
- `ventana_principal.py` (__init__, cambiar_estado)
- `computadora/habilidades/camara.py` (verificaciones)

**Checklist**:
- [ ] Cámara inicia en boot
- [ ] Tzimtzum = Cámara OFF
- [ ] Salida Tzimtzum = Cámara ON
- [ ] Tests: Cámara estado sincronizado
- [ ] Boot test: Cámara activa en inicio

---

#### **RUBEDO FASE 5**: Metatrón + Permisos (5 archivos)
**Duración**: ~2-3 horas  
**Archivos**:
- CREAR: `computadora/geometria/metatron.py`
- CREAR: `tests/test_metatron.py`
- `wrapper_computadora.py` (admin check)
- `computadora/nucleo/observador.py` (integración 1)
- `computadora/interfaz/ventana_principal.py` (ref "Golem")

**Checklist**:
- [ ] Crear MetatronCube + Merkaba + FlowerOfLife
- [ ] Tests geométricos pasan
- [ ] Admin detection en boot
- [ ] Red scan obtiene permisos
- [ ] Tests: Todas herramientas funcionan
- [ ] Boot test: Sistema inicia como admin sin prompts

---

## 🔄 ORDEN EJECUCIÓN RECOMENDADO

```
RUBEDO FASE 1 (Resize) → ✅ Prueba boot
                ↓
RUBEDO FASE 2 (Demos) → ✅ Prueba demo emet-maljut-gevura
                ↓
RUBEDO FASE 3 (Orbe) → ✅ Prueba interacción todos modos
                ↓
RUBEDO FASE 4 (Cámara) → ✅ Prueba cámara on/off
                ↓
RUBEDO FASE 5 (Metatrón + Permisos) → ✅ Prueba completa + geometría
                ↓
PALINGENESIA: Retrospectiva + Commit + Cierre
```

---

## 📝 NOTAS CRÍTICAS PARA RUBEDO

1. **Fase 1 es bloqueante**: Si resize falla, todo lo demás se rompe
2. **Fase 2 requiere Fase 1**: No sincronizar demos con resize roto
3. **Tests en cada fase**: Cada cambio debe validarse antes de siguiente
4. **Boot test obligatorio**: Después de cada fase, ejecutar `iniciar_computadora.bat`
5. **Coherencia UI**: En Fase 2, cambiar TODOS los "Golem" → "Computadora" (no quedar a mitad)

---

## 🔐 VERSIONADO

**Archivo**: `.audit/CITRINITAS_PURIFICACION_SINTESIS_ABRIL23.md`  
**Status**: ✅ READY PARA RUBEDO  
**Próximo comando**: `"rubedo"` o `"sí"` = COMIENZA IMPLEMENTACIÓN

---

**Síntesis completa**: 7 problemas → 7 soluciones → 5 fases ejecutables ✅
