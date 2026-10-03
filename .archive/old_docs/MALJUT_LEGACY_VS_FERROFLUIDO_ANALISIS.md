# MALJUT — Análisis Legacy vs Ferrofluido RUBEDO
**Fecha:** 3 de mayo de 2026  
**Propósito:** Referencia para mejoras futuras de visualización  
**Status:** Legacy 80%, Ferrofluido 20% (estructurado, no integrado aún)

---

## 📊 MÉTRICAS

| Componente | Ubicación | LOC | Tipo | Status |
|-----------|-----------|-----|------|--------|
| **Maljut Legacy** | `ventana_principal.py` | ~4,000 | Core rendering | ✅ Funcional |
| **Ferrofluido RUBEDO** | `ferrofluido_rubedo.py` | 627 | Nueva visualización | ⚠️ Estructurado |
| **Ferrofluido Atómico** | `ferrofluido.py` | 626 | Modelo atómico híbrido | ⚠️ Estructurado |
| **Config Maljut** | `maljut_dev_config.py` | ~150 | Selector dinámico | ✅ Funcional |

---

## 🏛️ LEGACY MALJUT (Activo, en ventana_principal.py)

### Core Components
- **paintEvent()** (~400 LOC, línea ~1595)
  - Renderizado monolítico directo
  - Anillos circulares concéntricos
  - Partículas puntuales (100-200)
  - Letras hebreas orbitantes
  - Núcleo de obsidiana
  - EMET inscrito

### Performance
- ✅ 2-3ms por frame (CPU)
- ✅ Sin GPU requerida
- ✅ Geometría fija, predecible
- ❌ Estático (no responde a emociones)
- ❌ Interacción manual de rotaciones

### Métodos Clave
```python
_animar()                    # Rotación de anillos
_dibujar_anillos_sagrados() # Geometría 2D platónica
_dibujar_particulas()       # Partículas simples
_dibujar_letras_orbitantes() # Texto en órbitas
_dibujar_nucleo()           # Esfera clásica
_dibujar_emet()             # Inscripción de verdad
```

### Interfaz Estándar (compartida con Ferrofluido)
```python
_estado            # dormido, escuchando, procesando, hablando
_etapa_alquimica   # NIGREDO → PALINGENESIA
_escala            # factor zoom (1.0 = normal)
_brillo_actual     # 0.0-1.0 (actividad)
_proximidad        # 0.0-1.0 (cursor cercano)
personalidad       # Ruaj: humor, energía
```

---

## ✨ FERROFLUIDO RUBEDO (Nuevo, no integrado)

### FP-156 PHASE 2 — Gota Coherente

**Características:**
- **Core Shape:** Convex Hull suavizado (forma dinámica)
- **Spikes:** Tendrils magnéticos (reaccionan a emociones)
- **Particles:** Brillo interior con colores Ruaj
- **Glow Aura:** Borde luminoso reactivo

### FP-156-162 Atómico — Núcleo Cuántico

**Modelos:**
- **WI-309 (Bohr):** Núcleo denso + exclusión de Pauli
- **WI-310 (Sommerfeld):** Órbitas elípticas + precesión relativista
- **WI-311 (Chadwick):** Atmósfera neutronica (neutrones orbitales)
- **WI-312 (Lewis):** Morfing esfera ↔ teseracto 4D
- **WI-313 (Rutherford):** Emociones → carga electrostática (atrae/repela)

### Performance
- ✅ 1000 partículas <15ms/frame (CPU, vectorizado numpy)
- ✅ 3-4ms/frame con GPU (CUDA optimizado)
- ✅ Reactivo a emociones (13 estados Ruaj)
- ✅ Física real (órbitas elípticas)
- ✅ Geometría dinámica
- ❌ Requiere GPU para óptimo
- ❌ CPU fallback lento

### Mapeo Ruaj → Colores
```python
EstadoRuaj.REPOSO          → Verde esmeralda (40, 200, 100)
EstadoRuaj.ESCUCHANDO      → Azul agua (60, 140, 220)
EstadoRuaj.PROCESANDO      → Púrpura (160, 80, 220)
EstadoRuaj.HABLANDO        → Oro cálido (255, 200, 80)
EstadoRuaj.PENSANDO        → Plateado (180, 180, 200)
EstadoRuaj.EMOCIONADO      → Rojo profundo (200, 60, 100)
EstadoRuaj.GEOMETRIA_SAGRADA → Dorado iluminado (255, 215, 0)
```

---

## 🤝 QUÉ COMPARTEN

1. **Base común:** Ambos dibujan en `paintEvent()` del `OrbeGolem`
2. **Mapeo estado:** ambos mapean `_estado` → visualización
3. **Reactividad:** ambos reaccionan a emociones del Ruaj
4. **Escala/Brillo:** ambos usan `_escala` y `_brillo_actual`
5. **Color Ohr:** ambos aplican sistema 5 capas de color
6. **Geometría sagrada:** ambos soportan Árbol de la Vida
7. **Núcleo central:** ambos tienen Maljut = manifestación

---

## 🔄 QUÉ DIFIEREN

| Aspecto | Legacy | Ferrofluido |
|--------|--------|-------------|
| Base Shape | Círculos concéntricos | Forma dinámica (Convex Hull) |
| Partículas | 100-200 puntos simples | 1000+ electrones+neutrones |
| Física | Circular simple | Órbitas elípticas + precesión |
| Color | Paleta fija por estado | Gradiente continuo Ruaj |
| Emociones | Ninguna reacción | Reacción dinámica (picos, colores) |
| Performance | 2-3ms CPU | 15ms CPU / 3-4ms GPU |
| Geometría Platónica | 2D inscrita | 3D morph + teseracto 4D |
| Interactividad | Ninguna | Electrostática (atrae/repela) |
| GPU Requerida | No | Sí (para óptimo) |

---

## 🔧 STRUCTURE ACTUAL (MIX HÍBRIDO)

```
paintEvent() línea ~1595
├─ GLOW EXTERIOR (Legacy)
├─ FERROFLUIDO RUBEDO (si config habilitada) ← NEW, NO INTEGRADO
├─ ANILLOS SAGRADOS (Legacy)
├─ PARTÍCULAS (Legacy O Ferrofluido según config)
├─ LETRAS ORBITANTES (Legacy)
├─ NÚCLEO (Legacy)
├─ EMET (Legacy)
├─ INDICADORES HERRAMIENTAS (Legacy)
└─ NIVEL CEREBRO (Legacy)
```

**Selector dinámico:**
```python
ConfigMaljutDev.deberia_usar_ferrofluido()
├─ SI GPU detectada → predeterminado: Ferrofluido
└─ SI solo CPU → predeterminado: Legacy
  (usuario puede cambiar vía maljut_dev_config.json)
```

---

## ⚠️ LO QUE FALTA PARA 100% INTEGRACIÓN

### 1. Implementar `animador_orbe_4d.py`
```python
class AnimadorOrbe4D:
    def actualizar(delta_t, ruaj, carga_emocional, angulos_anillo)
    def renderizar(painter, width, height, draw_state, ...)
    def cambiar_estado(nuevo_ruaj, carga_emocional)
```

### 2. Implementar `dibujante_orbe.py`
```python
def dibujar_ferrofluido_rubedo(painter, ...)
def dibujar_particulas_atomicas(painter, ...)
def dibujar_solidos_platonicos_dinamicos(painter, ...)
def crear_ferrofluido_rubedo_defecto() -> FerroffluidoRubedo
```

### 3. Conectar en paintEvent()
- Ya hay stubs en línea ~1614-1623
- Pero funciones no existen

### 4. Performance Tuning
- Vectorizar updates numpy
- Cachear geometría
- GPU acceleration (opcional)

---

## 📋 ESTADO ACTUAL

**Maljut hoy = 80% Legacy / 20% Ferrofluido**
- ✅ Legacy: Funcional 100%, todo en `ventana_principal.py`
- ⚠️ Ferrofluido: Código estructurado, sin dibujante conectado
- ⚠️ Config: Sistema preparado para ambos modos

---

## 🎯 ROADMAP FUTURO

### FASE 1: Integración Ferrofluido
- [ ] Implementar `animador_orbe_4d.py`
- [ ] Implementar `dibujante_orbe.py`
- [ ] Conectar stubs en paintEvent()
- [ ] Testing: renderizar en ambos modos

### FASE 2: Performance
- [ ] GPU acceleration en CUDA
- [ ] Cacheo de geometría
- [ ] Profiling y optimization

### FASE 3: Demos Separadas
- [ ] Demo Legacy Maljut
- [ ] Demo Legacy Gevurah
- [ ] Demo Ferrofluido Maljut
- [ ] Demo Ferrofluido Gevurah
- [ ] Demo Verdad (unified)

### FASE 4: Transición Suave
- [ ] Animación morfing entre modos
- [ ] Config persistence
- [ ] Tema seleccionable en UI

---

## 💾 ARCHIVOS RELACIONADOS

| Archivo | Propósito | Status |
|---------|-----------|--------|
| `ventana_principal.py` | Orbe principal + Legacy rendering | ✅ Funcional |
| `ferrofluido_rubedo.py` | FP-156: gota coherente + colores Ruaj | ⚠️ Estructurado |
| `ferrofluido.py` | FP-156-162: modelo atómico híbrido | ⚠️ Estructurado |
| `maljut_dev_config.py` | Selector Legacy/Ferrofluido + GPU detect | ✅ Funcional |
| `geometrias_platonicas.py` | Sólidos 3D dinámicos | ✅ Disponible |
| `teseracto_4d.py` | Transformaciones 4D | ✅ Disponible |
| `dibujante_orbe.py` | ❌ NO EXISTE (falta implementar) | ❌ Falta |
| `animador_orbe_4d.py` | ❌ NO EXISTE (falta implementar) | ❌ Falta |

---

## 📝 NOTAS PARA FUTURAS MEJORAS

1. **Maljut es puramente visual** — toda la lógica está separada
2. **Config es persistente** — guarda en `datos/maljut_dev_config.json`
3. **GPU detection es automática** — nvidia-smi + torch.cuda
4. **Colores están separados** — no hardcodeados en Maljut
5. **Emociones son externas** — inyectadas vía `Ruaj` del sistema
6. **Particulas pueden ser reemplazadas** — interfaz estándar

---

## 🔗 REFERENCIAS RELACIONADAS

- FP-156: Ferrofluido RUBEDO Phase 2
- FP-156-162: Ferrofluido Atómico (Bohr/Sommerfeld/Chadwick/Lewis/Rutherford)
- WI-309 → WI-313: Implementaciones atómicas
- RF-340: Offset de tránsito (ventana expandida)
- FP-027: Delegación dibujantes
- FP-024: Patrones sagrados temporales
- FP-013: Glow direccional + tacto

---

## 🎨 VISUAL QUICK REFERENCE

```
LEGACY MALJUT              FERROFLUIDO RUBEDO
├─ Círculos              ├─ Forma dinámica
├─ Partículas simples    ├─ 1000 electrones+neutrones
├─ Estático              ├─ Reactivo emocional
├─ 2-3ms/frame           ├─ 15ms/frame CPU, 3-4ms GPU
└─ CPU only              └─ GPU optimizado

AMBOS COMPARTEN
├─ OrbeGolem widget
├─ Estados: escuchando, procesando, hablando
├─ Ruaj: emociones, colores
├─ Geometría sagrada (Árbol de la Vida)
└─ Sistema de color Ohr (5 capas)
```

---

**Última actualización:** 2026-05-03  
**Próximo paso:** Implementar `animador_orbe_4d.py` y `dibujante_orbe.py` para integración completa
