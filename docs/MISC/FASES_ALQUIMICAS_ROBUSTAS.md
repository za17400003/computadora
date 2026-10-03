# 🔄 FASES ALQUÍMICAS ROBUSTAS — Framework de Coherencia

**Fecha**: Abril 18, 2026  
**Propósito**: Describir cómo cada fase alquímica MANTIENE coherencia estructural + terminológica  
**Inyectable**: Usar este framework ANTES de cada ciclo de trabajo  

---

## 📋 Tabla de Fases + Verificaciones de Coherencia

| Fase | Duración | Objetivo | Verificaciones Coherencia | Hallazgo |
|------|----------|----------|----------------------------|----------|
| **NIGREDO** | 30min | Diagnóstico destructivo | ✓ Auditoría de estructura ✓ Terminología ✓ Duplicación ✓ Referencias ✓ Mapeos | Output: reporte JSON (errores/warnings) |
| **ALBEDO** | 30-60min | Investigación limpieza | ✓ Validar pre-condiciones ✓ Especificar solución ✓ Verificar no rompe axiomas | Output: plan sin contradicciones |
| **CITRINITAS** | 30-60min | Síntesis optimización | ✓ Trade-offs justificados ✓ Código pasa tests ✓ EMET validación | Output: código verificado |
| **RUBEDO** | 30-120min | Manifestación | ✓ Cambios atómicos ✓ Tests verdes ✓ Estructura respetada | Output: commit sellado |
| **PALINGENESIA** | 20-30min | Retrospectiva | ✓ Lección documentada ✓ Memoria actualizada ✓ Semilla para WI siguiente | Output: SEMILLA + lección |

---

## 🔍 NIGREDO — Auditoría Automatizada (INYECTABLE)

### Checklist OBLIGATORIO (antes de actuar)

```python
# Pseudo-código - equivalente a nigredo_audit.py

audit = NigresoAudit()
report = audit.run_full_audit()

# Si hay ERRORES → RECHAZAR petición
if report["status"] == "FAILED":
    print("❌ NIGREDO detectó incoherencias críticas")
    print("Errores:")
    for error in report["errors"]:
        print(f"  • {error}")
    # No proceder hasta que errores sean resueltos
    
# Si hay WARNINGS → ALERTAR pero proceder
if report["warnings"]:
    print("⚠️  Advertencias (proceder con precaución):")
    for warning in report["warnings"]:
        print(f"  • {warning}")
```

### Verificaciones Específicas

#### 1️⃣ Organización de Raíz
```
✓ Raíz limpia (solo ~10 archivos permitidos)
✓ Todos los archivos están categorizados:
  - Documentación → _docs/
  - Auditorías → _docs/REPORTS/
  - Ciclos cerrados → _archive/CICLOS/
  - Gestión → .management/
✓ Directorios permitidos presentes
```

#### 2️⃣ Terminología Coherente
```
✓ Enciclopedia (JAMÁS "Grimorio" en código)
✓ COMPUTADORA (JAMÁS "Golem" en pragmático)
✓ Comandos (JAMÁS "Palabras Mágicas" en codigo)
✓ Mapeo explícito: esotérico ↔ pragmático
```

#### 3️⃣ Sin Duplicación
```
✓ NO: servidor_grimorio.py (removido)
✓ NO: iniciar_grimorio.bat (removido)
✓ NO: código duplicado sin propósito
```

#### 4️⃣ Referencias Válidas
```
✓ Todas las referencias internas existen
✓ Cross-links funcionan (markdown links)
✓ Archivos deletreados correctamente
```

#### 5️⃣ Mapeos Actualizados
```
✓ _docs/ARCHITECTURE/MAPEO_ESOTERICO_PRAGMATICO.md existe
✓ Contiene mapeos clave (9 conceptos)
✓ Regla de Oro documentada
```

---

## 🕰️ ALBEDO — Investigación Limpieza (Fase 2)

### Verificaciones Coherencia

```
PRE-CONDICIÓN: NIGREDO pasó sin errores
    ↓
✓ Leer especificación del WI (o petición)
✓ Buscar precedentes (cambios similares históricamente)
✓ Identificar impacto (¿qué archivos cambian? ¿qué referencias?)
✓ Mapear dependencias (¿otro módulo usa esto?)
✓ Validar contra axiomas (¿contradice alguna ley?)
    ↓
SALIDA: Plan que NO introduce inconsistencias
```

### Checklist Anti-Contaminación

```
[ ] ¿Cambia terminología? → Verificar no mezcla esotérico+pragmático
[ ] ¿Crea archivos nuevos? → Verificar ubicación según estructura
[ ] ¿Elimina archivos? → Verificar no son necesarios en otras partes
[ ] ¿Actualiza referencias? → Verificar todas las menciones
[ ] ¿Toca código sensible? → Verificar impacto en tests + EMET
```

---

## 🌟 CITRINITAS — Síntesis Optimización (Fase 3)

### Verificaciones Coherencia

```
PRE-CONDICIÓN: ALBEDO plan aprobado
    ↓
✓ Código pasa tests (pytest verde)
✓ EMET validación (introspección Computadora)
✓ Trade-offs documentados (por qué se eligió así)
✓ Alternativas consideradas (por qué NO las otras opciones)
✓ Impacto mapeado (cambios cascada documentados)
    ↓
SALIDA: Código verificado, listo para manifestar
```

### Checklist de Validación

```
[ ] Tests corren sin errores
[ ] Cobertura >= 80% (si es código sensible)
[ ] EMET puede introspeccionar los cambios
[ ] Documentación interna clara (docstrings)
[ ] No hay imports circulares
[ ] No hay violaciones de axiomas
```

---

## 🔴 RUBEDO — Manifestación (Fase 4)

### Verificaciones Coherencia

```
PRE-CONDICIÓN: CITRINITAS código verificado
    ↓
✓ Cambios ATÓMICOS (1 commit = 1 idea)
✓ Estructura respetada (archivos en lugares correctos)
✓ Referencias actualizadas (documentación, links)
✓ Tests verdes (ejecución final)
✓ Commit con mensaje claro (Tria Prima style)
    ↓
SALIDA: Código vivo + validado + documentado
```

### Checklist de Consolidación

```
[ ] Cambios están en rama local
[ ] Git status: only intended files modified
[ ] Commit message explicita:
    - Qué problema se soluciona
    - Cómo se soluciona
    - Por qué esta solución
[ ] Tests pasan (pytest final)
[ ] EMET validación post-deploy
[ ] Documentación actualizada
```

---

## 🔄 PALINGENESIA — Retrospectiva (Fase 5)

### Verificaciones Coherencia

```
PRE-CONDICIÓN: RUBEDO código en rama main
    ↓
✓ Lección documentada (¿qué aprendimos?)
✓ Memoria actualizada (_user_memory.md)
✓ Antifraude (¿qué podría haber salido mal?)
✓ Semilla generada (insumo para WI siguiente)
✓ Coherencia post-merge (auditoría NIGREDO nuevamente)
    ↓
SALIDA: Semilla inyectable + lección + estado limpio
```

### Checklist de Cierre

```
[ ] Reporte de retrospectiva creado
[ ] Lección en /memories/repo/ (si aplica)
[ ] Semilla para próximo WI documentada
[ ] Estado post-merge validado:
    [ ] NIGREDO auditoría: PASSED
    [ ] Raíz limpia
    [ ] Terminología coherente
    [ ] Referencias válidas
```

---

## 🔌 INYECCIÓN AUTOMÁTICA — Framework Injectable

### Cómo Inyectar en Cada Petición

**PATRÓN**: Antes de procesar cualquier petición del usuario, ejecutar NIGREDO audit.

```python
# Pseudocódigo para Copilot

def procesar_peticion_usuario(peticion):
    """
    PATRÓN OBLIGATORIO: NIGREDO primero, luego acción
    """
    
    # PASO 1: NIGREDO Audit
    print("🔍 NIGREDO Audit iniciado...")
    audit = NigresoAudit()
    report = audit.run_full_audit()
    
    # PASO 2: Evaluar resultado
    if report["status"] == "FAILED":
        print("❌ NIGREDO detectó incoherencias críticas:")
        for error in report["errors"]:
            print(f"   • {error}")
        print("\n⚠️  No se puede proceder. Resolver primero:")
        print("   1. git status")
        print("   2. Revisar archivos en raíz")
        print("   3. Verificar terminología")
        print("   4. Remover duplicados")
        return "RECHAZADA: coherencia estructural comprometida"
    
    if report["warnings"]:
        print("⚠️  ADVERTENCIAS (proceder con precaución):")
        for warning in report["warnings"]:
            print(f"   • {warning}")
    
    # PASO 3: Proceder con petición
    print(f"\n✅ NIGREDO PASSED — Proceeding...")
    print(f"📋 Petición del usuario: {peticion}\n")
    
    # AQUÍ COMIENZA EL WORKFLOW NORMAL (Gate 0 → Gate 1 → ALBEDO...)
    return procesar_workflow_normal(peticion)
```

### Checklist de Inyección

```
ANTES DE CADA ACCIÓN:

[ ] ¿He ejecutado NIGREDO audit?
    → Si ERROR: detener y arreglar
    → Si WARNING: continuar con cautela
    → Si PASSED: proceder

[ ] ¿La petición tiene coherencia pre-requisitos?
    → Lógica interna consistente
    → Mapeos explícitos
    → No contradice axiomas

[ ] ¿He documentado por qué esta es la ruta?
    → Pipeline identificado (A/B/C/D/E)
    → Fases claras (NIGREDO → RUBEDO)
    → Semilla para próximo WI

[ ] ¿La estructura se mantiene post-acción?
    → Raíz limpia
    → Archivos en lugares correctos
    → Terminología coherente
```

---

## 📊 Tabla: Coherencia por Fase

| Propiedad | NIGREDO | ALBEDO | CITRINITAS | RUBEDO | PALINGENESIA |
|-----------|---------|--------|-----------|--------|--------------|
| **Estructura** | ✓ Auditada | ✓ Planeada | ✓ Diseñada | ✓ Manifestada | ✓ Validada |
| **Terminología** | ✓ Verificada | ✓ Validada | ✓ Confirmada | ✓ Implementada | ✓ Confirmada |
| **Tests** | 🔍 N/A | 🔍 N/A | ✓ Escritos | ✓ Verdes | ✓ Final |
| **Documentación** | ✓ Diagnóstico | ✓ Plan | ✓ Design | ✓ Code docs | ✓ Retrospectiva |
| **EMET** | 🔍 N/A | 🔍 N/A | ✓ Validado | ✓ Live | ✓ Confirmed |
| **Commit** | 📝 N/A | 📝 N/A | 📝 N/A | ✓ Atomic | ✓ Sealed |

---

## 🎯 Reglas de Oro (Inviolables)

```
1. NIGREDO PRIMERO
   → Antes de cualquier acción, auditoría automática
   → Errores → rechazar petición
   → Warnings → proceder con cautela

2. COHERENCIA EN CASCADA
   → Cambio en una capa → validar todas las capas
   → Terminología contamina si no se revisa
   → Referencias rompen silenciosamente

3. ESTRUCTURA INMUTABLE
   → Raíz limpia (siempre)
   → Archivos en lugar correcto (siempre)
   → Mapeo explícito (siempre)

4. AUDITORÍA POST-ACCIÓN
   → Después de RUBEDO → PALINGENESIA incluye NIGREDO nuevamente
   → Validar que estructura NO se rompió
   → Certifique que cambios fueron atómicos

5. INYECTABLE SIEMPRE
   → NIGREDO audit = herramienta reutilizable
   → Ejecutar antes de cada petición
   → Parte integral del WORKFLOW
```

---

## 🚀 Próximos Pasos

1. ✅ **NIGREDO audit creado** (`nigredo_audit.py`)
2. ⏳ **Inyector implementado** (este documento)
3. ⏳ **Integración en WORKFLOW_OPERACIONAL.md**
4. ⏳ **Testing del framework** (validar que detecta problemas)

---

## 📝 Ejemplo de Uso

### Escenario: Usuario pide "añade comando nuevo"

```
Petición: "Crea un comando 'nuevo' en COMPUTADORA"
    ↓
NIGREDO AUDIT:
  ✅ Estructura: PASSED
  ✅ Terminología: PASSED
  ✅ Referencias: PASSED
  → Resultado: PASSED
    ↓
GATE 0: Clasificar
  → Pipeline: A (Feature nueva)
    ↓
GATE 1: Validación
  → Lógica: ✓
  → Empírica: ✓
  → Axiomática: ✓
    ↓
ALBEDO: Investigación
  → ¿Dónde va el archivo?
  → ¿Qué referencias?
  → ¿Tests necesarios?
    ↓
CITRINITAS: Síntesis
  → Código + tests verdes
    ↓
RUBEDO: Manifestación
  → Commit: "feat: comando 'nuevo' (Pipeline A)"
    ↓
GATE 3: QA
  → Tests: ✓
  → EMET: ✓
    ↓
PALINGENESIA: Retrospectiva
  → NIGREDO AUDIT nuevamente: PASSED ✓
  → Lección: documentada
  → Semilla: generada
    ↓
SALIDA: Comando vivo + coherencia mantenida ✓
```

---

**FASES ALQUÍMICAS ROBUSTAS = COHERENCIA GARANTIZADA**

Inyectable, reutilizable, verificable.
