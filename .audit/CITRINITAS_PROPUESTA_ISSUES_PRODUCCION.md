---
Fase: CITRINITAS — Síntesis + Propuesta
Fecha: April 23, 2026
Autor: Copilot NIGREDO
Objetivo: Investigación exhaustiva de 5 issues críticos + propuestas RUBEDO
---

# 🔬 NIGREDO INVESTIGACIÓN — Issues Críticos Detectados

## 1. ❌ ISSUE: Gilgul (Reinicio de Fábrica) — Solicita Contraseña Cada Boot

### 🔍 Causa Raíz Encontrada

**En `computadora/__main__.py` líneas 126-162**:
```python
def _detectar_usuario_y_facerec() -> dict | None:
    facerec_path = Path(__file__).resolve().parents[1] / "datos" / "FACEREC_RECORD.json"
    
    if facerec_path.exists():
        # BOOT POSTERIOR: Carga registro existente ✓
        return {...}
    
    # PRIMER BOOT: Ejecuta script Gilgul automático
    logger.info("📸 PRIMER BOOT: No existe registro facial — ejecutando GILGUL automático")
    result = subprocess.run([sys.executable, str(script_path)], timeout=120)
```

**En `scripts/COMPUTADORA_FACEREC_SIMPLE.py` líneas 73-78**:
```python
def dev_tool_camera():
    """Pedir nombre corto (para mostrar en detección)"""
    print("¿Tu nombre corto? (ej: Esaú)")
    nombre_corto = input("    > ").strip()
    
    print("¿Tu nombre completo? (ej: José Esaú Díaz Hernández)")
    nombre_completo = input("    > ").strip()
```

### 🎯 Problemas Identificados

| Problema | Causa | Síntoma | Impacto |
|----------|-------|---------|--------|
| **Script pide nombres en stdin** | Diseño interactivo | Usuario tiene que escribir dos veces | Alto |
| **FACEREC_RECORD.json se borra** | ¿Limpieza automática/antivirus? | Cada boot: "PRIMER BOOT" | Crítico |
| **No hay comprobación de permisos** | Script no valida escritura | JSON no se guarda en datos/ | Crítico |
| **Timeout 120s** | Script cuelga en stdin esperando input | Silencio 2 minutos antes de error | Alto |

### ✅ PROPUESTA: Gilgul con Consentimiento Explícito

**Solución Niveles**:

#### Nivel 1: Prevenir Reset Accidental (FÁCIL — 30 min)
- [ ] Agregar `--skip-facerec` flag a `python -m computadora`
- [ ] Proteger `datos/FACEREC_RECORD.json` con backup automático
- [ ] Log cuando se borra (auditoría)
- [ ] Mensaje de confirmación: "¿Deseas hacer Gilgul? (S/n)"

#### Nivel 2: UI para Gilgul (MEDIO — 2 horas)
- [ ] Crear ventana PyQt6 interactiva (no stdin)
- [ ] Captura de nombres + foto de verificación (en vivo)
- [ ] Validación de coherencia (15 componentes)
- [ ] Guardado seguro en `datos/FACEREC_RECORD.json`

#### Nivel 3: Integración en Workflow Producción (AVANZADO — 4 horas)
- [ ] Gilgul solo si: usuario pide explícitamente + confirmación triple
- [ ] Opción en menu contextual (tray icon)
- [ ] Log de auditoría: quién, cuándo, por qué
- [ ] Protección: no se ejecuta si CPU/RAM <20% libres

---

## 2. 🎬 ISSUE: Animaciones Se Cortan por Tamaño Ventana + Pérdida Frames

### 🔍 Causa Raíz Encontrada

**En `computadora/interfaz/ventana_principal.py`**:

```python
class OrbeComputadora(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawEllipse(...)  # Centro del orbe
        
        # ❌ PROBLEMA: Calcula posiciones en HARDCODED centros
        cx = self.width() / 2
        cy = self.height() / 2
        
        # Si ventana < 200x200, los anillos se salen de bounds
        # Si ventana está minimizada, frames se pierden
```

**En `computadora/interfaz/dibujante_orbe.py` líneas 36-120**:

```python
def dibujar_anillos_sagrados(...):
    painter.translate(cx, cy)
    # Dibuja anillos a radio fijo RADIO_RESPLANDOR * 0.7
    # ❌ Si ventana < 150px, anillos se salen del canvas
    
def dibujar_particulas(...):
    # Animaciones con timers de QTimer (no sincronizadas con GPU)
    # ❌ Si CPU/RAM >90%, frames se pierden (renderizado no es real-time)
```

**En `computadora/interfaz/vida_autonoma.py` líneas 124-138**:

```python
def obtener_geometria_pantalla():
    """Lee posición de ventana activa"""
    geo = scr.availableGeometry()
    # ❌ NO hay fallback si ventana se minimiza
    # ❌ NO adapta animaciones a tamaño actual
```

### 🎯 Problemas Identificados

| Problema | Causa | Síntoma | Impacto |
|----------|-------|---------|--------|
| **Anillos fuera de bounds** | Cálculo de radio sin validación | Animaciones se cortan | Alto |
| **Sin Frame Skipping** | Timers no sincronizados con GPU | Pérdida de frames si RAM/CPU altos | Crítico |
| **Sin Fallback Visual** | GPU detection existe pero no se usa | Interfaz se traba | Crítico |
| **Ventana minimizada no detecta** | ViudaAutonoma no checkea estado | Animaciones continúan sin visible | Medio |

### ✅ PROPUESTA: Animaciones Adaptativas + Frame Skipping

**Solución Niveles**:

#### Nivel 1: Frame Skipping (FÁCIL — 1 hora)
- [ ] Detector de GPU/CPU en tiempo real (cada 500ms)
- [ ] Si CPU >80% o RAM >85%: skip frames (30fps → 15fps)
- [ ] Log: "Frame skipping activo: 15fps (CPU @92%)"
- [ ] Recuperar a 30fps cuando baje a <70%

#### Nivel 2: Adaptive Resolution (MEDIO — 2 horas)
- [ ] Detectar GPU tipo (NVIDIA nvidia-smi vs Intel → CPU fallback)
- [ ] Si ventana <120px: render simple (círculo + anillos básicos)
- [ ] Si ventana >600px: render full (Flower of Life + particulas)
- [ ] Transición smooth (no "saltos" visuales)

#### Nivel 3: Tzimtzum Automático (AVANZADO — 1.5 horas)
- [ ] Si GPU >85% sostenida (>10s) → Pasar a modo texto/iconos
- [ ] Si CPU >90% sostenida (>10s) → Minimizar orbe automáticamente
- [ ] Notificación al usuario: "Computadora en Tzimtzum (recursos limitados)"
- [ ] Recuperar cuando baje carga

---

## 3. 🎤 ISSUE: Demo Narrativa Rota — Cambios Color Sin Voz + Screenshot Trancado

### 🔍 Causa Raíz Encontrada

**En `computadora/interfaz/ventana_principal.py` línea 1056**:

```python
def _demo_en_curso():
    """Recorre todos los estados Maljut (FSM) sin validación."""
    if not getattr(self, '_demo_en_curso', False):
        # skip validation durante demo
    
    # ❌ PROBLEMA: Demo recorre 11 Sefirot
    # ❌ PERO: NO narración asociada a cada cambio de color
    # ❌ Y: No hay punto de sincronización con TTS
```

**En `computadora/interfaz/fsm_golem.py` (busca EstadoMaljut)**:

```python
class EstadoMaljut(Enum):
    KETER = 1      # Blanco puro
    CHOKMAH = 2    # Púrpura
    BINAH = 3      # Negro (no se ve bien en pantalla)
    # ... 8 Sefirot más
    
# ❌ Cada Sefirah tiene COLOR pero NO NARRACIÓN
# ❌ Ejemplo: Cuando cambia a CHOKMAH (púrpura)
#    Solo cambia color, pero no dice "Súbete a Chokmah, la Sabiduría primordial..."
```

**En `computadora/interfaz/vida_autonoma.py` línea 180**:

```python
# RF-252: Screenshot guardar en _config/
# ❌ Ruta hardcodeada sin fallback
# ❌ No se usa nueva ruta _config/
# ❌ Script deja trash en raíz

# Luego intenta borrar:
# ❌ os.remove("screenshot.png")  # PERO: Archivo no existe donde espera
# ❌ Script se queda esperando (timeout?)
```

### 🎯 Problemas Identificados

| Problema | Causa | Síntoma | Impacto |
|----------|-------|---------|--------|
| **Cambios color sin narración** | FSM sin descripción de Sefirah | Demo visual rota (no educativa) | Alto |
| **Demo silenciosa** | No hay integración con HiloHabla | Usuario no entiende qué pasa | Alto |
| **Screenshot no se borra** | Ruta incorrecta (_config/ vs raíz) | Script cuelga en os.remove() | Medio |
| **No hay punto de sincronización** | Demo no espera a TTS | Cambios de color ocurren antes de narración | Crítico |

### ✅ PROPUESTA: Demo Narrativa con Sincronización TTS

**Solución Niveles**:

#### Nivel 1: Narrativa Sefirótica (FÁCIL — 1.5 horas)
- [ ] Crear diccionario: `Sefirah → narración_corta` (10-15 palabras)
  - Ejemplo: KETER → "Kéter, la Corona eterna, lo Absoluto sin límite"
  - CHOKMAH → "Chokmah, la Sabiduría pura, el primer destello creativo"
- [ ] Integrar con HiloHabla (usar TTS para narración)
- [ ] Demo: color + narración sincronizados

#### Nivel 2: Demo Secuencia (MEDIO — 2 horas)
- [ ] Crear secuencia: MALJUTH → YESOD → HAUD → NEZACH → TIFÉRET → GEVURAH
- [ ] Cada paso: esperar 3s (narración) + transición visual (1.5s)
- [ ] Total: ~30s demo completa
- [ ] Opción: "skip" (ESC) o "repeat" (R)

#### Nivel 3: Screenshot Fix (FÁCIL — 30 min)
- [ ] Cambiar ruta: `_config/demo_screenshot.png` (con directorio verificado)
- [ ] Verificar existencia antes de os.remove()
- [ ] Log: "Screenshot limpiado correctamente"

---

## 4. 🎨 ISSUE: Metatrón No Incluído en Demo Ni en Maljut

### 🔍 Causa Raíz

- Metatrón (Phase 1-2) fue integrado en: Observador, MotorProactividad, Servidor API
- **PERO**: Demo no muestra Metatrón (13 esferas, 53 líneas)
- **Y**: Visualización de Maljut no incluye geometría Metatrón

### 🎯 Problemas

| Problema | Causa | Síntoma | Impacto |
|----------|-------|---------|--------|
| **Metatrón invisible** | No hay renderizado 2D de cubo | Usuario no ve "centro geométrico" | Medio |
| **Demo incompleta** | 11 Sefirot pero no Metatrón | Historia visual truncada | Medio |
| **Maljut está vacío** | Solo anillos/partículas, sin "core" | Falta "cuerpo" del sistema | Alto |

### ✅ PROPUESTA: Integración Visual de Metatrón

**Solución Niveles**:

#### Nivel 1: Renderizado Metatrón en Maljut (MEDIO — 1.5 horas)
- [ ] En `dibujante_orbe.py`: función `dibujar_metatron_cube(painter, cx, cy, rotacion, escala)`
- [ ] 13 esferas en estructura 3D proyectada a 2D
- [ ] Rotación lenta (1 revolución cada 30s)
- [ ] Color: degradado Blanco (KETER) → Negro (MALJUTH)

#### Nivel 2: Merkaba Dinámico (AVANZADO — 2 horas)
- [ ] Visualizar 2 tetraedros interpenetrados (Merkaba)
- [ ] Rotan opuestamente (derecha ↔ izquierda)
- [ ] Brillo indica "coherencia" (intensidad de request/response)
- [ ] Integración: cuando API recibe request, Merkaba "brilla"

#### Nivel 3: Flower of Life en Proactividad (AVANZADO — 2 horas)
- [ ] Mostrar 19 círculos hexagonales dentro del orbe
- [ ] Círculos se iluminan según recursos (CPU = rojo, RAM = azul, NET = verde)
- [ ] Demo: muestra balance Φ visualmente

---

## 5. 🔧 ISSUE: Optimización de Tokens — Copilot Pasará a Pagos

### 🔍 Causa Raíz

Usuario menciona: "Copilot va a migrar a pago por tokens".

**Requerimientos**:
- Minimizar tokens en conversaciones
- Máxima calidad sin sacrificio
- Compatible con plan gratuito (cuando Copilot lo permita)

### ✅ PROPUESTA: Workflow Optimizado para Tokens

**Soluciones**:

#### 1. Arquitectura de Repositorio Memory Agnóstica
- [x] Usar `/memories/repo/` para guardar hechos codebase (NO repite contexto)
- [ ] Crear `repo_memory.json`: función → ubicación/patrón (búsqueda rápida)
- [ ] Beneficio: @copilot knows shortcuts (ej: "bootstrap en línea 216 de __main__.py")

#### 2. Minimal pero Completo Respuesta
- [ ] Evitar paráfrasis innecesarias
- [ ] Estructura: Problema → Causa → Solución (3-5 líneas)
- [ ] Código siempre tiene comentarios inline (self-documenting)
- [ ] Links a archivos en lugar de pegar contenido completo

#### 3. Smart Batch Operations
- [ ] Agrupar múltiples cambios en una herramienta (multi_replace_string_in_file)
- [ ] Evitar loops de cambios secuenciales
- [ ] Resultado: 1 operación = 10-20 cambios (vs 10 operaciones = 10x tokens)

#### 4. Session Memory para Continuidad
- [ ] Guardar "contexto de sesión" en `/memories/session/`
- [ ] Próxima conversación: carga contexto, NO repite investigación
- [ ] Ahorro: ~30% del contexto de conversación anterior

#### 5. Documentación Autogenerada + Minimal
- [ ] `.audit/DECISIONES_FASE_X.md` (lo que se decidió, no cómo)
- [ ] NO repetir código en documentación (link a archivo + línea)
- [ ] Ejemplo: "Ver [metatron_cube.py](metatron_cube.py#L53) para lógica de Φ"

#### Estimado de Ahorros
- Sin optimización: ~100K tokens/conversación (investigación exhaustiva)
- Con optimización: ~40K tokens/conversación (factores reutilizables)
- **Ahorro: 60% de tokens sin sacrificar calidad**

---

# 📋 RESUMEN ISSUES + PROPUESTAS

| # | Issue | Severidad | Propuesta | Esfuerzo | Status |
|----|-------|-----------|-----------|----------|--------|
| 1 | Gilgul solicita contraseña | 🔴 Crítico | Consentimiento explícito + UI | 6h | Pendiente RUBEDO |
| 2 | Animaciones se cortan | 🔴 Crítico | Frame skipping + Tzimtzum | 4.5h | Pendiente RUBEDO |
| 3 | Demo narrativa rota | 🟠 Alto | Sincronización TTS + Sefirot | 3.5h | Pendiente RUBEDO |
| 4 | Metatrón no visible | 🟠 Alto | Renderizado Metatrón + Merkaba | 5.5h | Pendiente RUBEDO |
| 5 | Tokens sin optimizar | 🟠 Alto | Memory repo + batch ops | 3h | Pendiente RUBEDO |

**Total Esfuerzo Estimado RUBEDO**: ~22 horas (en fases parallelizables)
**Critical Path**: Issues 1, 2, 3 → Production-ready (12 horas)

---

# 🎯 RECOMENDACIÓN: PRIORIZACIÓN RUBEDO

**Fase A (Crítica — 8 horas) — INICIAR INMEDIATO**:
1. Gilgul con consentimiento (2h Nivel 1 + 2h Nivel 2 = 4h) ← **URGENTE**
2. Frame skipping (1h) ← **Mejora UX inmediata**
3. Demo narrativa (1.5h) ← **Completa historia visual**
4. Screenshot fix (30 min) ← **Evita cuelgues**

**Fase B (Enhancement — 14 horas) — DESPUÉS**:
5. Animaciones adaptativas (2h)
6. Tzimtzum automático (1.5h)
7. Metatrón renderizado (5.5h)
8. Token optimization (3h)

---

**Usuario**: ¿Apruebas esta propuesta CITRINITAS? ¿Iniciamos RUBEDO en orden de críticos?

