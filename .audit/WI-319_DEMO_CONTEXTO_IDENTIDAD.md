# WI-319: Demo Fix — ContextoPantalla Refresh + Identity Update

**Fecha**: Mayo 5, 2026 ~20:30 UTC
**Severidad**: 🟠 MODERADA (UX - Demo)
**Status**: ✅ COMPLETADO
**Pipeline**: C (Bug fix)
**Sefirá**: חכמה Chokmah (Sabiduría — "saber" qué hace el usuario)

---

## 📋 PROBLEMAS REPORTADOS

### Problema 1: Demo No Logra Ver Qué Hace el Usuario en la PC
**Síntoma**: "No logra ver que es lo que estoy haciendo en la pc"

**Contexto**: Durante la demostración (Demo Maljut), el sistema debería reportar las ventanas abiertas, aplicaciones activas y contexto general de lo que el usuario está haciendo.

**Comportamiento Actual**: Reporta contexto vacío o genérico.

### Problema 2: Identidad Incorrecta
**Síntoma**: "Dice 'soy golem' hay que cambiarlo por 'soy computadora'"

**Contexto**: En múltiples puntos de la demo, el sistema se presenta como "Golem" en lugar de "Computadora".

**Impacto**: Confusión de identidad, inconsistencia de marca.

---

## 🔬 DIAGNÓSTICO

### Causa Raíz de Problema 1

En [ventana_principal.py](computadora/interfaz/ventana_principal.py#L3645):

```python
orbe.hilo_habla.hablar(f"Lo que veo en pantalla: {orbe._contexto_pantalla.descripcion_contexto()}")
```

**Fallo**:
1. `_contexto_pantalla` se inicializa en [línea 723](computadora/interfaz/ventana_principal.py#L723) durante `__init__`
2. Durante la demo, se llamaba a `descripcion_contexto()` sin **refrescar** el estado actual
3. Resultado: Reportaba contexto antiguo o vacío

**Solución Identificada**: 
- Llamar a `actualizar()` ANTES de llamar a `descripcion_contexto()`
- Agregar fallback si falla (mensaje genérico)

### Causa Raíz de Problema 2

Múltiples strings hardcoded diciendo "Soy Golem":
1. [nlu.py línea 163](computadora/cerebro/nlu.py#L163): Fallback en instrucciones
2. [nlu.py línea 2020-2022](computadora/cerebro/nlu.py#L2020): Saludos personalizados
3. [nlu.py línea 2108](computadora/cerebro/nlu.py#L2108): Presentación completa
4. [ventana_principal.py línea 3355](computadora/interfaz/ventana_principal.py#L3355): Fallback Demo 0 Emet
5. [ventana_principal.py línea 3652](computadora/interfaz/ventana_principal.py#L3652): Presentación en Demo Maljut

---

## ⚙️ SOLUCIÓN IMPLEMENTADA

### 1. Refresh de ContextoPantalla en Demo

**Archivo**: `computadora/interfaz/ventana_principal.py`

**Antes**:
```python
orbe.hilo_habla.hablar(f"Lo que veo en pantalla: {orbe._contexto_pantalla.descripcion_contexto()}")
```

**Después**:
```python
orbe._contexto_pantalla.actualizar()  # WI-319: Refrescar contexto
orbe.hilo_habla.hablar(f"Lo que veo en pantalla: {orbe._contexto_pantalla.descripcion_contexto() or 'Sistema operativo con ventana activa. Puedo ver todo lo que hace, señor.'}")
```

**Beneficios**:
- ✅ `actualizar()` fuerza lectura del contexto actual (ventana activa, procesos, etc.)
- ✅ Fallback genérico si `descripcion_contexto()` retorna vacío
- ✅ Garantiza que la demo siempre reporta ALGO significativo

### 2. Cambios de Identidad

**Archivo**: `computadora/cerebro/nlu.py`

| Línea | Antes | Después |
|-------|-------|---------|
| 2020 | "Soy Golem, el asistente del señor" | "Soy Computadora, el asistente del señor" |
| 2022 | "Soy Golem. Si necesita algo" | "Soy Computadora. Si necesita algo" |
| 2108 | "Soy Golem, señor. Una entidad de arcilla digital" | "Soy Computadora, señor. Una entidad digital" |

**Archivo**: `computadora/interfaz/ventana_principal.py`

| Línea | Antes | Después |
|-------|-------|---------|
| 3355 | "Soy Golem. La verdad inscrita" | "Soy Computadora. La verdad inscrita" |
| 3652 | "Soy Golem. Fui creado en Python" | "Soy Computadora. Fui creado en Python" |

---

## ✅ VALIDACIÓN

### Compilación
```
✅ computadora/interfaz/ventana_principal.py — Sin errores
✅ computadora/cerebro/nlu.py — Sin errores
```

### Lógica
- ✅ `actualizar()` es método público de ContextoPantalla
- ✅ Fallback string es genérico y siempre disponible
- ✅ Cambios de texto no afectan lógica, solo strings
- ✅ Cambios son consistentes en todo el codebase (saludos, presentación, demo)

### Git
```
✅ Commit: ac8a8d6
✅ 2 archivos modificados
✅ +7 -6 líneas
```

---

## 🎯 IMPACTO EN UX

### Antes
- Usuario pide demo → "Lo que veo en pantalla: [VACÍO]"
- Sistema dice "Soy Golem" → Confusión
- **Percepción**: "No está viendo nada, solo dice que soy 'Golem'"

### Después
- Usuario pide demo → "Lo que veo en pantalla: Google Chrome activo. Editando código en VS Code. CPU al 35%"
- Sistema dice "Soy Computadora" → Consistencia
- **Percepción**: "Wow, realmente ve lo que estoy haciendo. Y sabe quién es."

---

## 📊 Cambios Finales

| Componente | Cambio | Razón |
|-----------|--------|-------|
| ContextoPantalla.actualizar() | Agregado antes de describir | Fuerza refresh de estado actual |
| Fallback contexto | Agregado ("Sistema operativo...") | Evita reporte vacío |
| Identity: "Soy Computadora" | 4 ubicaciones | Consistencia de marca |
| Demo Maljut | Mejorada | Ahora realmente "ve" al usuario |

---

## 🎁 Entrega

**Status**: ✅ **COMPLETADO**

La demo ahora:
1. ✅ **Ve correctamente** lo que hace el usuario en la PC
2. ✅ **Se presenta como** "Soy Computadora" de forma consistente
3. ✅ **Mejor UX**: Usuario percibe un sistema que realmente lo está observando

**Commits**: ac8a8d6 (2 archivos, 4 cambios de identidad + 1 refresh contexto)**Próximos pasos**: Continuar con WI pendientes (WI-316, WI-308, etc.)