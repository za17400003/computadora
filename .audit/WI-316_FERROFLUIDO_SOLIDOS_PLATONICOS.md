# WI-316 CITRINITAS — Diseño Ferrofluido Sólidos Platónicos Giratorios

**Fecha**: Mayo 1, 2026 ~20:15 UTC  
**Estado**: CITRINITAS (síntesis + optimización)  
**Objetivo**: Diseño técnico para ferrofluido con nanopartículas formando sólidos platónicos giratorios en 3D→2D

## 🎯 REQUERIMIENTOS SINTETIZADOS

Basado en investigación ferrofluida real + requerimientos usuario:

### 1. Nanopartículas Realistas
- **Tamaño**: Radio 1-2 px (vs actual 5-10px) — simula 10nm reales
- **Cantidad**: 2000-5000 partículas (vs 350 actuales) — balance visual/performance
- **Distribución**: Clusters gaussianos alrededor de vértices platónicos

### 2. Sólidos Platónicos Sagrados
Implementar 5 sólidos platónicos con coordenadas 3D normalizadas:

| Sólido | Vértices | Caras | Simetría | Energía Sagrada |
|--------|----------|-------|----------|-----------------|
| **Tetraedro** | 4 | 4 | Fuego | Keter (corona) |
| **Cubo/Hexa** | 8 | 6 | Tierra | Malkut (reino) |
| **Octaedro** | 6 | 8 | Aire | Tiféret (belleza) |
| **Dodecaedro** | 20 | 12 | Éter | Binah (comprensión) |
| **Icosaedro** | 12 | 20 | Agua | Hokmah (sabiduría) |

### 3. Animación 3D→2D
- **Rotación**: Giro continuo alrededor eje Y (0.1 rad/s) + leve precesión
- **Proyección**: Perspectiva simple (z' = z / (1 + z), x' = x / (1 + z))
- **Transición**: Suave entre sólidos (2s lerp) cuando cambia Ruaj
- **Campo magnético simulado**: Atracción a vértices con fuerza dipolar

### 4. Integración con Sistema Ruaj
Añadir nuevo estado: `EstadoRuaj.GEOMETRIA_SAGRADA`
- Trigger: Cuando personalidad alcanza "iluminación" o usuario solicita
- Duración: Ciclo completo de 5 sólidos (10s cada uno)
- Color: Gradiente dorado (iluminación)

## 🏗️ ARQUITECTURA PROPUESTA

### Clase PlatonicSolid
```python
class PlatonicSolid:
    def __init__(self, tipo: str):
        self.tipo = tipo  # 'tetraedro', 'cubo', etc.
        self.vertices = self._calcular_vertices()  # Lista [(x,y,z), ...]
        self.rotacion_actual = 0.0
    
    def _calcular_vertices(self) -> List[Tuple[float, float, float]]:
        # Coordenadas normalizadas para cada sólido
        pass
    
    def rotar(self, delta_t: float) -> None:
        self.rotacion_actual += 0.1 * delta_t  # 0.1 rad/s
    
    def proyectar_2d(self, vertices_3d: List) -> List[Tuple[float, float]]:
        # Proyección perspectiva
        pass
```

### Extensión FerroffluidoRubedo
Añadir atributos:
- `solido_actual: PlatonicSolid | None`
- `modo_geometria: bool = False`
- `transicion_t: float = 0.0`

Métodos nuevos:
- `activar_geometria_sagrada(solido: str)`
- `actualizar_geometria(delta_t)`
- `calcular_fuerzas_platonicas()` — física de atracción a vértices

### Modo de Operación
1. **Modo Normal**: Partículas en esfera con spikes (actual)
2. **Modo Geometría**: Partículas migran a vértices del sólido actual
3. **Transición**: Lerp suave entre modos (2s)
4. **Rotación**: Sólido gira continuamente mostrando forma 3D

## 📊 CÁLCULOS TÉCNICOS

### Coordenadas Sólidos Platónicos (Normalizadas Radio=1)

**Tetraedro**:
```python
vertices = [
    (1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)
]
# Normalizar: dividir por sqrt(3) ≈ 1.732
```

**Cubo**:
```python
vertices = [(±1, ±1, ±1) for all combinations]
```

**Octaedro**:
```python
vertices = [(0,0,±1), (0,±1,0), (±1,0,0)]
```

**Dodecaedro/Icosaedro**: Usar fórmulas con φ = (1+√5)/2

### Física de Atracción
Para cada partícula:
```python
for vertice in solido.vertices:
    distancia = np.linalg.norm(particula.pos - vertice)
    fuerza = (vertice - particula.pos) / (distancia + 0.1)**2  # Atracción dipolar
    particula.vel += fuerza * delta_t * 10.0  # Fuerza magnética
```

### Performance Target
- 2000 partículas: ~2-3ms/frame
- 5000 partículas: ~4-5ms/frame (límite superior)
- Optimizaciones: Vectorizar cálculos con NumPy

## 🔄 INTEGRACIÓN CON ANIMADOR

En `AnimadorOrbe4D.actualizar()`:
```python
if ruaj == EstadoRuaj.GEOMETRIA_SAGRADA:
    self.ferrofluido.activar_geometria_sagrada('tetraedro')  # O ciclo automático
```

En `renderizar()`:
- Si modo geometría: renderizar sólido proyectado + partículas atraídas
- Mantener layers aura/spikes/core para cohesión

## 🎨 RESULTADO ESPERADO

- **Visual**: Nanopartículas diminutas formando sólidos giratorios luminosos
- **Emocional**: Sensación de geometría sagrada manifestándose
- **Técnico**: 3D→2D fluido con physics realista ferrofluida

**Próximo**: RUBEDO - Implementación del código.