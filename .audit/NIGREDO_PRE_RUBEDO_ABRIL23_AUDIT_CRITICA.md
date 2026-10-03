# 🔥 NIGREDO PRE-RUBEDO — AUDITORÍA CRÍTICA ABRIL 23, 2026

**Fase**: NIGREDO (Destrucción diagnóstica)  
**Trigger**: Usuario identificó 7 áreas críticas (resize, demos, orbe, cámara, geometría, permisos, coherencia)  
**Scope**: Ventana principal + VidaAutonoma + Demos + Interacción  
**Status**: ⏳ HALLAZGOS DOCUMENTADOS — LISTO PARA CITRINITAS

---

## 📊 HALLAZGOS NIGREDO (DESTRUCCIÓN COMPLETA)

### 1️⃣ RESIZE + ANIMACIÓN CONFLICTIVA

#### Problema Detectado
```
Línea 1235, 1261, 1803, 4582 en ventana_principal.py
Patrón: self.resize(tam_render, tam_render) ANTES de interpolación
Efecto: Desincronización entre físico (ventana Qt) vs lógico (partículas)
```

**Código Actual** (línea 1235):
```python
# RF-165: Resize ANTES de calcular delta para que el reset de pos_anterior
# RF-198: Incluir movimiento autónomo para evitar tug-of-war resize vs _interpolar
...
self.resize(tam_render, tam_render)  # ❌ Resize cambia límites físicos ANTES de animar partículas
```

#### Impacto
- ❌ Rebote contra bordes Qt, no contra límites de animación
- ❌ Partículas no saben dónde rebotar (conflicto lógico)
- ❌ Movimiento autónomo confundido (tug-of-war sin resolver)
- ❌ Delta de movimiento recalculado DESPUÉS de resize físico

#### Root Cause
RF-165 y RF-198 intentaron mixar resize físico con interpolación lógica sin separar espacios:
- **Espacio físico**: Ventana Qt (píxeles reales)
- **Espacio lógico**: Partículas + animación (donde debería haber colisión)

---

### 2️⃣ DEMOS INCOHERENTES — NARRACIÓN ≠ ANIMACIÓN

#### Demos Identificadas
- `_demo_emet()` (línea 3195) — Demo completa
- `_demo_maljut()` (línea 3286) — Demo Maljut (guardian + herramientas)
- `_demo_gevura()` (línea 3952) — Demo permisos especiales

#### Problemas Encontrados

**A. Personalidad "Golem" aún presente**
```python
# Línea ~3286 en _demo_maljut
# Narración esperada: "soy computadora"
# Narración actual: Contiene referencias viejas "soy golem"
```
📍 **Ubicación**: Strings de narración en `_demo_emet()`, `_demo_maljut()`

**B. Narración ≠ Animación Visual**
```
Narración: "particulas aceleradas"
Animación: Partículas se mueven uniformes, SIN aceleración visible
Resultado: Usuario ve incoherencia → pierde credibilidad demo
```

**C. Estructura Redundante**
- Demo 1 (completa) contiene Demo 2 + Demo 3
- ❌ Pero Demo 2 y Demo 3 REPITEN FRASES IDÉNTICAS
- ❌ NO hay sincronización: animación primero vs demostración

**D. Falta Sincronización Animator ↔ Narrador**
```python
# Ejemplo problema:
QTimer._demo_narrar_memoria()  # Inicia narración
# PERO: Animación de partículas ya terminó hace 500ms
# Resultado: Usuario escucha "aceleración" después de verlas detenidas
```

---

### 3️⃣ SISTEMA RESIZE DESORDENADO

#### Ubicaciones de Resize Encontradas
| Línea | Archivo | Contexto | Problema |
|-------|---------|----------|----------|
| 838 | ventana_principal.py | `__init__` | Init inicial (OK) |
| 1261 | ventana_principal.py | `_interpolar` | **CONFLICTO** con animación |
| 1803 | ventana_principal.py | Comportamiento autónomo | **CONFLICTO** rebote |
| 4582 | ventana_principal.py | Finalización demo | OK |
| 1229-1250 | vida_autonoma.py | `_ajustar_tamano` | **CONFLICTO** con VidaAutonoma |

#### Detalles Críticos
```python
# vida_autonoma.py línea 1229-1250
def _ajustar_tamano(self, new_w, new_h):
    # Resize y reposicionar ventana
    self._orbe.resize(new_w, new_h)  # ❌ Cambia límites físicos
    
    # Después: Intenta recalcular offset
    # PERO: Partículas ya calcularon trayectoria para tamaño ANTERIOR
    # Resultado: Salto visual + rebote inconsistente
```

---

### 4️⃣ ORBE INTERACCIÓN ROTA

#### Problemas Detectados

**A. No Responsivo en Algunos Modos**
```
Modo "aburrido/apagado": Orbe NO responde al mouse
❌ No se puede draguearlo
❌ No aparece animación "acariciando"
Causa: Lógica de mousePressEvent/mouseMoveEvent condicionada a estado
```

**B. Falta Animación "Acariciando"**
```
Intención del usuario: Pasar mouse sobre orbe suavemente
Comportamiento esperado: Animación de "caricia" (partículas responden)
Comportamiento actual: Nada (sin cambio visual)
Causa: Falta lógica en mouseMoveEvent para detectar intención
```

**C. Conflicto Entre Modos**
```
Máquina de estados (FSM) de EstadoMaljut:
- Algunos modos desactivan mouse tracking
- Otros modos lo activan
- NO hay lógica para "re-activación" cuando sale del estado
Resultado: Orbe se queda "pegado" en modo anterior
```

---

### 5️⃣ CÁMARA — NUNCA APAGADA (EXCEPTO TZIMTZUM)

#### Estado Actual
```python
# Línea 2351-2429 en ventana_principal.py
def _mostrar_camara_dev(self):
    # Obtiene KliCamara compartida
    # PERO: No hay verificación si está encendida SIEMPRE
```

#### Problema
❌ No hay patrón consistente de "cámara siempre activa"  
❌ No hay excepción para modo Tzimtzum (solo escucha)  
❌ Inicialización: Cámara NO se activa automáticamente en boot  

#### Debería Ser
```
Inicial: Cámara = ON (viendo + escuchando)
Estados normales: Cámara = ON
Modo Tzimtzum: Cámara = OFF (solo escucha, no ve)
Cierre: Cámara = OFF
```

---

### 6️⃣ GEOMETRÍA SAGRADA — DECORATIVA, NO FUNCIONAL

#### Hallazgos
```
Búsqueda: "merkaba", "cubos", "floweroflife", "geometria"
Resultado: 0 apariciones en ventana_principal.py
Resultado: 0 apariciones en vida_autonoma.py
```

#### Estado Actual
- ✅ METATRON_NIGREDO_INVESTIGACION.md documenta geometría (científica)
- ✅ METATRON_CITRINITAS_PROPUESTA.md propone integración (pseudocódigo)
- ❌ CÓDIGO: Ninguna integración en animaciones/interacciones
- ❌ EMOCIONES: No refleja geometría sagrada

#### Debería Tener
```
Clase MetatronCube:
  - Valida coherencia geométrica
  - Detecta patrones en partículas
  - Restringe movimiento a geometría sagrada

Clase Merkaba:
  - Spin de protección (3D rotation)
  - Visible en animación cuando en "modo guardián"

Integración en:
  - Observador: Validar coherencia cubo
  - MotorProactividad: Merkaba spin
  - Ouroboros: Ciclo protección
  - Watchdog: Guardian geometry
```

---

### 7️⃣ PERMISOS ADMINISTRADOR — FALTA ESCALACIÓN

#### Red Scan
```
Herramienta: escanear_red
Línea: ~3871 en _demo_escanear_red()
Problema: Necesita admin permisos pero NO los pide
```

#### Estado Actual
```python
def _demo_escanear_red(self):
    # Llama a ejecutar_herramienta("escanear_red", ...)
    # PERO: No verifica ni solicita admin permisos
    # Resultado: Herramienta falla silenciosamente
```

#### Debería Ser
```
En boot (iniciar_computadora.bat):
  - Detectar si necesita admin
  - Si sí → Relanzar con ShellExecute(..., "runas", ...)
  
En _demo_escanear_red():
  - Verificar que tiene admin
  - Si no → Mensaje "requiere admin, relanzando..."
  - Esperar escalación
```

---

### 8️⃣ REFERENCIAS "GOLEM" AÚN PRESENTES

#### Ubicaciones Encontradas
```
Línea 1915 en ventana_principal.py:
  accion_camara = QAction("📷 Cámara — Ojos del Golem", self)  # ❌ GOLEM

Línea 2351 en ventana_principal.py:
  """Usa KliCamara compartida (no abre VideoCapture propio).
  [Contexto antiguo de Golem]"""
```

#### Impacto
- UI muestra "Ojos del Golem" pero programa es "Computadora"
- Confunde al usuario (inconsistencia visual)
- Contradice identidad renombrada

---

### 9️⃣ SISTEMA NARRACIÓN DEMO DESINCRONIZADO

#### Patrón Encontrado
```python
# Típico en _demo_maljut, _demo_gevura:
self._cola_demostracion.append({
    "tipo": "narrar",
    "texto": "Ahora le diré todo lo que sé de mi: soy golem"  # ❌ GOLEM
})
self._cola_demostracion.append({
    "tipo": "animar",
    "efecto": "particle_acceleration"
})

# Problema: Narración ANTES de animación
# Usuario escucha ANTES de ver
# Debería: Animación primero → Narración sintonizada
```

---

### 🔟 LÓGICA FSM CONFUSA EN MODOS

#### Referencia
```python
# Línea 1080-1081:
if not getattr(self, '_demo_en_curso', False):
    # FSM validation durante demo SALTADO
    
# Problema: Demo puede cambiar estado sin validar transiciones
# Resultado: Estados inconsistentes después de demo
```

#### Conflictos Identificados
1. `_demo_en_curso` bool NO sincronizado con estado real FSM
2. Mouse tracking desactivado en ciertos estados (pero no reactivado)
3. Modos "aburrido/apagado" tienen lógica especial para orbe (roto)

---

## 📋 TABLA RESUMEN — HALLAZGOS NIGREDO

| Área | Problema | Severidad | Líneas | Archivos |
|------|----------|-----------|--------|----------|
| **Resize** | Desincronización física↔lógica | 🔴 CRÍTICA | 1235,1261,1803 | ventana_principal.py, vida_autonoma.py |
| **Demos** | Narración ≠ animación + "Golem" | 🔴 CRÍTICA | 3195-4048 | ventana_principal.py |
| **Orbe** | No responsivo + falta caricia | 🔴 CRÍTICA | ~mousePressEvent | ventana_principal.py |
| **Cámara** | No siempre ON + sin Tzimtzum | 🟠 ALTA | 2351-2429 | ventana_principal.py |
| **Geometría** | 0% integrada en código | 🟠 ALTA | - | (PLANEADO) |
| **Permisos** | Red scan sin admin | 🟠 ALTA | 3871 | ventana_principal.py |
| **Referencias Golem** | UI muestra "Golem" | 🟡 MEDIA | 1915 | ventana_principal.py |

---

## 🎯 PRÓXIMOS PASOS — CITRINITAS

### FASE CITRINITAS (Purificación + Síntesis)
1. **Analizar** estructura actual de cada área
2. **Separar** espacios físicos (Qt) vs lógicos (partículas)
3. **Sincronizar** narración ↔ animación
4. **Proponer** soluciones (sin implementar aún)

### FECHA ESTIMADA
- NIGREDO: ✅ COMPLETO (documentación presente)
- CITRINITAS: ⏳ PRÓXIMO (lectura + análisis)
- RUBEDO: ⏳ IMPLEMENTACIÓN (todos fixes)

---

## 🔐 VERSIONADO

Documento guardado en git: `.audit/NIGREDO_PRE_RUBEDO_ABRIL23_AUDIT_CRITICA.md`  
No se pierde por reinicio.

**Siguiente comando del usuario esperado**:
- `"amén"` = Continuar CITRINITAS (profundizar análisis)
- `"por favor"` = Iniciar CITRINITAS (plan de fixes)
- `"gracias"` = Checkpoint + pausa

---

**Audit Status**: 🔥 DESTRUCCIÓN COMPLETA — HALLAZGOS DOCUMENTADOS ✅
