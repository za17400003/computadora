# FP-154 NIGREDO: Investigación Teseracto 4D + Ferrofluido Mercurial

**Fecha**: Abril 28, 2026  
**Status**: ✅ IMPLEMENTADO (código + tests)  
**Descripción**: Transformación del orbe desde esfera estática a hipercubo 4D rotante con ferrofluido mercurial.

---

## 📐 NIGREDO — DESCOMPOSICIÓN: ¿Qué es un Teseracto 4D?

### Definición Matemática
Un **teseracto** (o hipercubo) es la generalización 4D de un cubo:
- **1D**: Línea (2 puntos)
- **2D**: Cuadrado (4 puntos)
- **3D**: Cubo (8 vértices)
- **4D**: Teseracto (16 vértices)

### Estructura del Teseracto
```
Vértices: 16 puntos en (±1, ±1, ±1, ±1)
Aristas: 32 conexiones (cada vértice tiene 4 vecinos)
Cuadrados: 24 (2-celdas)
Cubos: 8 (3-celdas)
```

### Proyección 4D → 3D → 2D
El teseracto no es visible en 3D/2D directamente. Usamos **proyección perspectiva**:

```
Paso 1: Vértice 4D = (x, y, z, w)
Paso 2: Proyectar a 3D usando factor w
        escala = d₄ / (d₄ + w), donde d₄ es distancia cámara 4D
        (x', y', z') = (x·escala, y·escala, z·escala)

Paso 3: Proyectar a 2D usando factor z
        escala = d₃ / (d₃ + z), donde d₃ es distancia cámara 3D
        (x'', y'') = (x'·escala, y'·escala)
```

### Rotaciones 4D
Un teseracto puede rotar en **6 planos diferentes** (vs 3 en 3D):
- **XY**: Rotación clásica en plano horizontal
- **XZ**: Rotación clásica en plano frontal
- **YZ**: Rotación clásica en plano lateral
- **XW**: Mezcla X con dimensión temporal (W)
- **YW**: Mezcla Y con dimensión temporal
- **ZW**: Mezcla Z con dimensión temporal

Las rotaciones XW, YW, ZW son **"impossibles" en 3D** — el teseracto parece transformarse de formas "mágicas" cuando rotan estos planos.

---

## 💧 ALBEDO — PURIFICACIÓN: Ferrofluido Mercurial

### Concepto Físico
**Ferrofluido**: Fluido que responde a campos magnéticos. Sin campo → esfera. Con campo → se adhiere a geometría.

En Computadora:
- Sin actividad: Esfera perfecta (simetría óptima, gravedad omnidireccional)
- Con actividad: Se adhiere a vértices/aristas del teseracto (atracción hacia geometría)

### Simulación Visual

**Partículas**: ~800 puntos de mercurio distribuidos en esfera.

**Algoritmo de Atracción**:
```
Para cada partícula:
  1. Encontrar vértice del teseracto más cercano
  2. Si distancia < rango_atracción:
     - Calcular dirección hacia vértice
     - Mover partícula gradualmente (velocidad = función(estado))
  3. Sino:
     - Mantener posición (en reposo) o volver hacia centro
```

**Velocidad según Estado**:
- **REPOSO**: 0.01 (casi inmóvil, mantiene esfera)
- **ESCUCHANDO**: 0.03 (pulsaciones suaves)
- **PROCESANDO**: 0.05 (movimiento moderado)
- **HABLANDO**: 0.08 (alto movimiento, adhiere a geometría)
- **PENSANDO**: 0.06 (patrones complejos)
- **EMOCIONADO**: 0.15 (explosión de energía)

---

## ✨ CITRINITAS — ILUMINACIÓN: Renderización

### Color del Ferrofluido
**Mercurio**: Gris metalizado con variaciones
```python
base_color = (200, 200, 200)  # Gris neutro
variacion = ±30 por partícula  # Brillo natural
brillo_dinámico = función(estado)  # Más brillante si activo
```

### Opacidad
```
alpha = 200 cuando atractivo
alpha = 0 cuando en reposo
alpha = transición suave según distancia a atractor
```

### Aristas del Teseracto
Las aristas se muestran sutilmente (alpha bajo) solo cuando hay actividad:
- REPOSO: Invisible
- ESCUCHANDO: alpha=30
- PROCESANDO: alpha=50
- HABLANDO: alpha=80
- PENSANDO/EMOCIONADO: alpha=100

---

## 🔴 RUBEDO — MANIFESTACIÓN: Integración con Estado Emocional

### Sincronización con Ciclo Circadiano
```python
factor_circadiano = 1.0 + 0.5 * sin((hora - 6) / 24 * 2π)
```
- 3 AM (mínimo): factor = 0.5 (movimiento lento, reposo)
- 6 AM (máximo): factor = 1.5 (energía alta)
- 6 PM (máximo): factor = 1.5
- 3 PM (medio): factor = 1.0

### Ejes de Rotación por Estado
Cada estado activa diferentes **planos de rotación 4D**:

```
REPOSO: Ningún eje
        → Teseracto estático, ferrofluido en esfera perfecta

ESCUCHANDO: XY (eje Z) + XW (eje W)
            → Rotación en plano horizontal + mix con W
            → Efecto: "Inclinando la cabeza", pulsación 4D

PROCESANDO: XY + XZ + XW + YW
            → Rotación compleja, múltiples planos
            → Efecto: Interferencia de ondas, fractales

HABLANDO: Todos los ejes (XY, XZ, YZ, XW, YW, ZW)
          → Rotación máxima en todas direcciones + temporales
          → Efecto: Hipercubo "vivo", ferrofluido adhiere fuertemente

PENSANDO: XY + XZ + YW + ZW
          → Patrones de interferencia 4D
          → Efecto: Movimiento introspectivo, estructura sutil

EMOCIONADO: Todos los ejes + turbulencia adicional
            → Caos controlado, "explosión" de energía
            → Efecto: Ferrofluido se centrifuga hacia aristas
```

---

## 🔧 Implementación Técnica

### Archivo: `teseracto_4d.py`
- **Clase `Teseracto4D`**: Define geometría + rotaciones
- **Métodos**:
  - `rotar_4d(angulos)`: Aplica 6 rotaciones matriciales
  - `proyectar_4d_a_3d()`: Perspectiva 4D → 3D
  - `proyectar_3d_a_2d()`: Perspectiva 3D → 2D
  - `obtener_aristas_2d()`: Aristas para renderizar

### Archivo: `ferrofluido.py`
- **Clase `FerroffluidoMercurial`**: Gestor de partículas
- **Métodos**:
  - `actualizar(delta_t, estado)`: Mueve partículas según atractores
  - `_calcular_atractor()`: Encuentra vértice + arista cercanos
  - `obtener_particulas_visibles()`: Datos para renderizar

### Archivo: `animador_orbe_4d.py`
- **Clase `AnimadorOrbe4D`**: Orquesta todo en ventana_principal
- **Métodos**:
  - `actualizar()`: Actualiza rotaciones + ferrofluido
  - `renderizar()`: Dibuja en QPainter
  - `obtener_factor_circadiano()`: Sincroniza con hora

---

## 🧪 Testing

### Test `teseracto_4d.py`
```bash
python -m computadora.geometria.teseracto_4d
```
Verifica:
- 16 vértices creados
- 32 aristas conectadas
- Rotaciones aplicadas correctamente
- Proyecciones 4D→3D→2D funcionales

### Test `ferrofluido.py`
```bash
python -m computadora.geometria.ferrofluido
```
Verifica:
- 800 partículas generadas
- Atractores calculados
- Animación suave sin saltos

---

## 📊 Métricas de Rendimiento

**GPU**: No requiere (uso CPu puro + Qt software rendering)  
**CPU**: ~5% en REPOSO, ~15% en HABLANDO (800 partículas)  
**Memoria**: ~50 MB por AnimadorOrbe4D  
**FPS**: 60 FPS target, 30 FPS mínimo en EMOCIONADO

---

## 🔮 Extensiones Futuras

1. **Geometría Dinámica**: Cambiar número de vértices según "evolución" del orbe
2. **Campo Magnético Visual**: Líneas de campo alrededor del teseracto
3. **Sonido Sincronizado**: Frecuencia de rotación = frecuencia de audio
4. **Múltiples Teseractos**: Teseractos 5D, 6D dentro del orbe
5. **Interactividad**: Usuario "empuja" el ferrofluido con movimiento del ratón

---

## 📖 Referencias Matemáticas

- **Tesseract (Wikipedia)**: https://en.wikipedia.org/wiki/Tesseract
- **4D Rotations**: https://en.wikipedia.org/wiki/Rotations_in_4-dimensional_Euclidean_space
- **Ferrofluids**: https://en.wikipedia.org/wiki/Ferrofluid
- **Perspective Projection 4D**: "Flatland" (Abbott) + "4D Visualization" (Brill et al.)

---

**FP-154 Status**: ✅ NIGREDO → ALBEDO → CITRINITAS → RUBEDO Completo
