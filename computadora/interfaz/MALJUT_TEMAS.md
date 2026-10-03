# Temas Intercambiables de Maljut

## 🎨 Sistema de Temas

Maljut ahora soporta **temas intercambiables** que permiten cambiar entre diferentes estilos visuales sin reiniciar la aplicación.

### Temas Disponibles

#### 🏛️ Legacy (Por defecto)
- **Descripción**: El orbe clásico de Computadora con geometría sagrada, partículas cabalísticas y letras hebreas orbitantes
- **Características**:
  - Núcleo de obsidiana pulida
  - Anillos de geometría sagrada (Árbol de la Vida)
  - Partículas cabalísticas con fractales
  - Letras hebreas orbitantes
  - Indicadores de recursos del sistema
  - Efectos de resplandor exterior

#### 🌊 Ferrofluido (Experimental)
- **Descripción**: Tema moderno con animaciones de ferrofluido líquido que responde a emociones y estados
- **Características**:
  - Partículas magnéticas que simulan ferrofluido
  - Animaciones fluidas que responden al Ruaj (estado emocional)
  - Efectos de carga emocional visual
  - Sincronización con fases alquímicas
  - Mayor carga computacional (recomendado GPU)

## ⚙️ Configuración

### Acceso a Dev Tools
1. Click derecho en el orbe → "Dev Tools" → "Configuración Maljut"
2. O usa el menú: Herramientas → Maljut Dev Config

### Cambiar Tema
1. Abre el configurador de Maljut
2. Selecciona el checkbox del tema deseado:
   - ☑️ Legacy (Orbe clásico)
   - ☑️ Ferrofluido (Experimental)
3. Click "Guardar"
4. El cambio se aplica **inmediatamente** sin reiniciar

### Configuración Adicional
- **FPS Target**: 30 o 60 FPS (requiere reinicio)
- **GPU**: Habilitar uso de GPU dedicada (NVIDIA, requiere reinicio)

## 🔄 Intercambio en Tiempo Real

Los temas se pueden cambiar **sin reiniciar** Computadora:
- ✅ Cambios de tema (Legacy ↔ Ferrofluido): Aplicación inmediata
- ⚠️ Cambios de rendimiento (FPS, GPU): Requieren reinicio

## 🏗️ Arquitectura Técnica

### Configuración Persistente
- Archivo: `datos/maljut_dev_config.json`
- Formato JSON con valores por defecto
- Carga automática al iniciar

### Renderizado Condicional
```python
# En paintEvent()
if self._config_maljut.deberia_usar_ferrofluido():
    self._renderizar_ferrofluido(...)
```

### Gestión de Estado
- `ConfigMaljutDev`: Gestiona configuración persistente
- `TipoMaljut` enum: LEGACY, FERROFLUIDO
- Actualización automática tras cambios

## 🎯 Recomendaciones

### Para Uso General
- **Legacy**: Menos recursos, visual clásico, recomendado por defecto

### Para Presentaciones/Demos
- **Ferrofluido**: Visual impactante, responde a emociones, ideal para mostrar capacidades

### Para Desarrollo
- Cambia entre temas para comparar visuales
- Usa Legacy para debugging (menos carga GPU)
- Ferrofluido para testing de animaciones emocionales

## 🔧 Troubleshooting

### Tema no cambia
- Verifica que se guardó la configuración
- Revisa logs para errores de inicialización
- Reinicia si hay problemas de GPU

### Ferrofluido no anima
- Verifica que AnimadorOrbe4D se inicializó correctamente
- Revisa configuración GPU
- Comprueba logs de error en renderizado

### Configuración no persiste
- Verifica permisos de escritura en `datos/`
- Revisa que el archivo JSON no esté corrupto</content>
<parameter name="filePath">computadora/interfaz/MALJUT_TEMAS.md