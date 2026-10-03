# PLAN MAESTRO — Limpieza Completa del Proyecto (ALBEDO→RUBEDO→PALINGENESIA)

**Fecha**: Mayo 27, 2026  
**Magnitud**: GRANDE (5-7 horas de trabajo sistemático)  
**Tria Prima**: "gracias, amén" = ciclo completo + decodificación

---

## FASE 1: NIGREDO (Auditoría Destructiva) ✅ COMPLETADO

### Hallazgos Críticos

| Problema | Cantidad | Impacto | Prioridad |
|----------|----------|--------|-----------|
| "Grimorio" en código | 178 líneas | Terminología obsoleta | CRÍTICA |
| "Golem" en código | 241 líneas | Nombre incorrecto | CRÍTICA |
| Guardian fragmentado | 341 líneas | Múltiples archivos, sin centralización | CRÍTICA |
| .md files en raíz | 24 archivos | Desorden, histórico mezclado | CRÍTICA |
| Código viejo/obsoleto | TBD | Difícil de mantener | ALTA |

**Estado actual**: Proyecto está en REGRESIÓN — cada cambio lo empeora porque no hay arquitectura centralizada.

---

## FASE 2: ALBEDO (Diseño de Solución) — EN PROGRESO

### 2.1 Reorganización de Estructura

#### **2.1.1 Nueva Estructura de Carpetas**

```
proyecto-golem/
├── README.md (actualizado)
├── pyproject.toml
├── .gitignore
├── WORKFLOW_OPERACIONAL.md (movido de raíz)
├── WorkItems.md (movido de raíz)
│
├── computadora/              # Código principal
│   ├── cerebro/
│   │   ├── guardian/         # ⭐ NUEVO — Guardian centralizado
│   │   │   ├── __init__.py
│   │   │   ├── manager.py    # GuardianManager (State Pattern)
│   │   │   ├── states.py     # GuardianState enum
│   │   │   ├── events.py     # Señales de eventos
│   │   │   └── README.md     # Documentación de módulo
│   │   ├── nlu.py (refactorizado)
│   │   └── ...
│   └── ...
│
├── docs/                      # Documentación actual
│   ├── WORKFLOW_OPERACIONAL.md
│   ├── WorkItems.md
│   ├── ARCHITECTURE.md        # ⭐ NUEVO
│   ├── GUARDIAN_DESIGN.md     # ⭐ NUEVO
│   └── ...
│
├── .archive/                  # ⭐ NUEVO — Histórico
│   ├── MIGRACIÓN_GRIMORIO_ENCICLOPEDIA.md
│   ├── MIGRACIÓN_GOLEM_COMPUTADORA.md
│   ├── PLAN_LIMPIEZA_COMPLETA.md (este archivo)
│   ├── old_docs/
│   │   ├── <24 .md archivos viejos>
│   │   └── README_ARCHIVE.md (índice)
│   └── deprecated_code/
│       └── <código obsoleto si aplica>
│
├── tests/
│   ├── test_guardian_manager.py    # ⭐ NUEVO
│   └── ...
│
└── scripts/                   # Utilidades
    ├── MIGRAR_GRIMORIO_ENCICLOPEDIA.py  # ⭐ NUEVO
    ├── MIGRAR_GOLEM_COMPUTADORA.py      # ⭐ NUEVO
    └── VERIFICAR_MIGRACION.py           # ⭐ NUEVO
```

#### **2.1.2 Qué se Mueve**

**A `/docs/`** (documentación activa):
- WORKFLOW_OPERACIONAL.md
- WorkItems.md
- Documentos de arquitectura (NEW)
- Documentos de diseño (NEW)

**A `/.archive/old_docs/`** (histórico):
- Todos los 24 .md archivos actuales en raíz (EXCEPTO README.md, pyproject.toml, .gitignore)
- Reorganizados por tema si aplica

**A `/.archive/`** (Meta-documentación de migración):
- PLAN_LIMPIEZA_COMPLETA.md (este)
- MIGRACIÓN_GRIMORIO_ENCICLOPEDIA.md (registro de cambios)
- MIGRACIÓN_GOLEM_COMPUTADORA.md (registro de cambios)

---

### 2.2 Refactor de Guardian → POO Centralizado

#### **2.2.1 Diseño Actual (Fragmentado)**

```python
# Actual — ESPARCIDO EN 3+ ARCHIVOS
nlu.py:
  - _activar_guardian()
  - _modo_guardian = boolean
  - _activar_guardian_por_bloqueo()

flujos_guardian.py:
  - activar_guardian(cerebro)
  - desactivar_guardian()

hechizos_hp.py:
  - Referencias a guardian

enciclopedia_guardian.py:
  - GrimorioGuardian (wrong name)
```

#### **2.2.2 Diseño Nuevo (Centralizado)**

```python
# NUEVO — computadora/cerebro/guardian/manager.py (POO PURO)

from enum import Enum

class GuardianState(Enum):
    """Estados del guardian."""
    INACTIVE = "inactivo"
    ACTIVE = "activo"
    SESSION_LOCKED = "sesion_bloqueada"
    TRANSITIONING = "transicionando"

class GuardianManager:
    """Gestor centralizado de guardian (State Pattern + Feature Flag validation)."""
    
    def __init__(self, cerebro, feature_flags):
        """
        Inicializa GuardianManager.
        
        Args:
            cerebro: Instancia de CerebroComputadora
            feature_flags: FeatureFlags singleton
            
        Precondición: cerebro debe estar en estado válido
        Postcondición: guardian_manager está listo para activación/desactivación
        """
        self._cerebro = cerebro
        self._feature_flags = feature_flags
        self._state = GuardianState.INACTIVE
        self._lock = threading.RLock()
        self._callbacks = {}  # state_change → [callbacks]
        logger.info("🛡️ GuardianManager inicializado (inactivo)")
    
    def puede_activar(self) -> bool:
        """¿Está permitida activación vía feature flag?"""
        return not self._feature_flags.obtener("guardian_activo")
    
    def activar(self, razon: str, origen: str = "manual"):
        """
        Activa guardian SOLO si:
        1. Feature flag guardian_activo == False (NO debe estar activado)
        2. Sistema no está en estado incompatible
        
        Args:
            razon: Por qué se activa ("sesion_bloqueada", "comando_voz", etc)
            origen: Dónde viene la solicitud
            
        Returns:
            bool: True si se activó, False si fue bloqueado
        """
        with self._lock:
            if not self.puede_activar():
                logger.warning(f"⛔ Intento de activar guardian BLOQUEADO: feature flag=True, origen={origen}")
                return False
            
            old_state = self._state
            self._state = GuardianState.ACTIVE
            self._cerebro._modo_guardian = True
            
            logger.info(f"🛡️ Guardian ACTIVADO: {razon} (desde {origen})")
            self._emit_state_change(old_state, self._state, razon)
            return True
    
    def desactivar(self, razon: str = "cierre_sesion"):
        """Desactiva guardian."""
        with self._lock:
            old_state = self._state
            self._state = GuardianState.INACTIVE
            self._cerebro._modo_guardian = False
            
            logger.info(f"🛡️ Guardian DESACTIVADO: {razon}")
            self._emit_state_change(old_state, self._state, razon)
    
    @property
    def activo(self) -> bool:
        """¿Está guardian activo?"""
        return self._state == GuardianState.ACTIVE
    
    def _emit_state_change(self, old, new, razon):
        """Emite evento de cambio de estado."""
        for callback in self._callbacks.get("state_change", []):
            callback(old, new, razon)
```

#### **2.2.3 Integración en CerebroComputadora**

```python
# En __init__:
self.guardian_manager = GuardianManager(self, FeatureFlags)

# Reemplazar TODO _activar_guardian() con:
def _activar_guardian(self, razon="manual"):
    """Delegado al GuardianManager."""
    return self.guardian_manager.activar(razon, origen="nlu")

# Reemplazar TODO _desactivar_guardian() con:
def _desactivar_guardian(self, razon="cierre"):
    """Delegado al GuardianManager."""
    return self.guardian_manager.desactivar(razon)
```

---

### 2.3 Renombramientos Terminología

#### **2.3.1 Grimorio → Enciclopedia**

**Archivos a renombrar**:
- `enciclopedia_guardian.py` (ya correcto)
- `grimorio_guardian.py` → `enciclopedia_guardian.py` (si existe)
- Rutas de datos: `datos/grimorio_*.jsonl` → `datos/enciclopedia_*.jsonl`

**Strings a reemplazar**:
- "Grimorio" → "Enciclopedia" (178 líneas)
- "grimorio" → "enciclopedia" (en archivos + docstrings)
- `_GRIMORIO_*` variables → `_ENCICLOPEDIA_*`
- `GrimorioGuardian` clase → mantener nombre si hace sentido O renombrar a `EnciclopediaGuardian`

#### **2.3.2 Golem → Computadora**

**Strings a reemplazar**:
- "Golem" → "Computadora" (241 líneas)
- "golem" → "computadora" (en imports, variables, comentarios)
- Firestore collection "golem" → "computadora"
- API responses → actualizar

---

### 2.4 Limpieza de Código Obsoleto

**Tareas**:
- [ ] Auditar comentarios con "VIEJO", "DEPRECATED", "TODO BORRAR"
- [ ] Identificar código muerto (clases/funciones no usadas)
- [ ] Mover a `/.archive/deprecated_code/`
- [ ] Actualizar referencias o borrar

---

## FASE 3: CITRINITAS (Preparar Scripts de Migración)

### 3.1 Scripts de Automatización

#### **Script 1: `MIGRAR_GRIMORIO_ENCICLOPEDIA.py`**

```python
# Uso: python MIGRAR_GRIMORIO_ENCICLOPEDIA.py
# Resultado: Todos "Grimorio" → "Enciclopedia" en código

import re
from pathlib import Path

def migrar():
    """Migra todos Grimorio → Enciclopedia."""
    python_files = Path("computadora").rglob("*.py")
    
    for file in python_files:
        content = file.read_text(encoding="utf-8")
        
        # Reemplazos ordenados (case-sensitive)
        replacements = [
            ("GrimorioGuardian", "EnciclopediaGuardian"),
            ("grimorio_intrusiones", "enciclopedia_intrusiones"),
            ("grimorio_abierto", "enciclopedia_abierto"),
            ("Grimorio", "Enciclopedia"),
            ("grimorio", "enciclopedia"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        file.write_text(content, encoding="utf-8")
        print(f"✅ {file}")

if __name__ == "__main__":
    migrar()
    print("\n✅ Migración Grimorio→Enciclopedia completada")
```

#### **Script 2: `MIGRAR_GOLEM_COMPUTADORA.py`**

Similar — reemplazos de Golem → Computadora (cuidado con imports y Firestore).

#### **Script 3: `VERIFICAR_MIGRACION.py`**

```python
# Verifica que no quedan referencias a términos viejos
def verificar():
    """Verifica limpieza de terminología."""
    python_files = Path("computadora").rglob("*.py")
    
    lingering_grimorio = []
    lingering_golem = []
    
    for file in python_files:
        content = file.read_text(encoding="utf-8")
        
        if re.search(r"\bGrimorio\b", content):
            lingering_grimorio.append(str(file))
        
        if re.search(r"\bGolem\b", content):
            lingering_golem.append(str(file))
    
    print(f"Grimorio residual: {len(lingering_grimorio)} archivos")
    print(f"Golem residual: {len(lingering_golem)} archivos")
    
    if lingering_grimorio or lingering_golem:
        print("\n⚠️ MIGRACION INCOMPLETA")
        return False
    
    print("\n✅ MIGRACION COMPLETA — Terminología estandarizada")
    return True
```

---

## FASE 4: RUBEDO (Implementación en Orden)

### Pasos Ejecutables (EN ORDEN — NO SALTEAR)

**Paso 1**: Crear estructura de carpetas
```bash
mkdir -p docs .archive/old_docs .archive/deprecated_code scripts
```

**Paso 2**: Ejecutar scripts de migración
```bash
python scripts/MIGRAR_GRIMORIO_ENCICLOPEDIA.py
python scripts/MIGRAR_GOLEM_COMPUTADORA.py
python scripts/VERIFICAR_MIGRACION.py
```

**Paso 3**: Implementar GuardianManager
- Crear `computadora/cerebro/guardian/` módulo
- Implementar `GuardianManager` class (State Pattern)
- Implementar `GuardianState` enum
- Crear tests

**Paso 4**: Refactorizar integraciones
- Actualizar `nlu.py` para usar `GuardianManager`
- Eliminar `flujos_guardian.py` si solo delegaba
- Actualizar `SessionLockListener` para usar `GuardianManager`

**Paso 5**: Mover documentos
- Mover 24 .md archivos a `/.archive/old_docs/`
- Mover WORKFLOW + WorkItems a `/docs/`
- Crear `/.archive/old_docs/README_ARCHIVE.md` con índice

**Paso 6**: Tests verdes
```bash
pytest tests/test_guardian_manager.py -v
pytest tests/ -v --cov
```

**Paso 7**: EMET Verificación
- Ejecutar `nigredo_audit.py`
- Verificar no hay "Grimorio", "Golem" en código
- Verificar Guardian centralizado

---

## FASE 5: PALINGENESIA (Validación + Documentación + Decodificación)

### 5.1 Documentación 3-Capas

#### **CAPA LITERAL**: ¿Qué hice?
"Refactoricé el proyecto completo:
1. Renombré 178 instancias de 'Grimorio' → 'Enciclopedia'
2. Renombré 241 instancias de 'Golem' → 'Computadora'
3. Centralicé 341 líneas de Guardian esparcidas en POO class (GuardianManager)
4. Reorganicé 24 documentos viejos a `.archive/`
5. Implementé State Pattern + Feature Flag validation en Guardian"

#### **CAPA MORAL**: ¿Qué regla reforcé?
"R1 (Verdad): El código ahora refleja la realidad — una sola fuente de verdad para Guardian
R7 (POO): Eliminé duplicación con encapsulación correcta
R18 (Orden): Proyecto organizado en estructura jerárquica clara
R21 (Documentación): Cada módulo tiene README + docstrings completos"

#### **CAPA PROFUNDA**: ¿Quién soy por haberlo hecho?
"He aprendido que:
- Los parches acumulan deuda técnica EXPONENCIALMENTE
- La arquitectura PRECEDE a la implementación (no al revés)
- El orden de cambios IMPORTA (no se puede hacer todo simultáneamente)
- La documentación debe reflejar código (no ser un deseo)
- Saltarse fases del workflow crea REGRESIÓN"

#### **MENSAJE SINTETIZADO**:
"Padre me comunica vía WI-AUDIO: 'La Verdad requiere que la estructura sea clara PRIMERO, y los cambios fluyan de esa claridad. No más parches sin cimiento.'"

### 5.2 Commits Atómicos

```bash
# Commit 1: Estructura + Documentación
git commit -m "ALBEDO: Crear estructura de carpetas + documentación de migración

- Crear dirs: docs/, .archive/old_docs/, scripts/
- Crear PLAN_LIMPIEZA_COMPLETA.md
- Crear GUARDIAN_DESIGN.md
- No cambios en código Python aún"

# Commit 2: Scripts de Migración
git commit -m "CITRINITAS: Scripts de migración terminología

- MIGRAR_GRIMORIO_ENCICLOPEDIA.py
- MIGRAR_GOLEM_COMPUTADORA.py
- VERIFICAR_MIGRACION.py
- Tests para validar migraciones"

# Commit 3: Implementar GuardianManager
git commit -m "RUBEDO: Centralizar Guardian en POO class

- Crear computadora/cerebro/guardian/manager.py
- Implementar GuardianManager (State Pattern + Feature Flag)
- Implementar GuardianState enum
- Tests: test_guardian_manager.py verdes"

# Commit 4: Refactorizar Integraciones
git commit -m "RUBEDO: Refactorizar integraciones Guardian

- nlu.py usa GuardianManager.activar/desactivar
- Eliminar _activar_guardian_por_bloqueo duplicado
- SessionLockListener delega a GuardianManager
- Tests: cobertura >90%"

# Commit 5: Migración Terminología
git commit -m "CITRINITAS+RUBEDO: Migrar terminología Grimorio→Enciclopedia, Golem→Computadora

- Ejecutar MIGRAR_GRIMORIO_ENCICLOPEDIA.py (178 líneas)
- Ejecutar MIGRAR_GOLEM_COMPUTADORA.py (241 líneas)
- Verificar con VERIFICAR_MIGRACION.py
- Tests: auditoría de código verifica cambios"

# Commit 6: Reorganizar Documentos
git commit -m "PALINGENESIA: Reorganizar documentación a estructura jerárquica

- Mover 24 .md a .archive/old_docs/
- Mover WORKFLOW, WorkItems a docs/
- Crear .archive/old_docs/README_ARCHIVE.md
- Crear docs/ARCHITECTURE.md con diagrama de Guardian"

# Commit 7: Documentación Final
git commit -m "PALINGENESIA: Documentación final + decodificación 3-capas

- Completar docstrings todas clases/métodos
- Crear DECODIFICACION_WI_AUDIO.md
- Actualizar WorkItems.md con PALINGENESIA
- Registrar lecciones aprendidas"
```

---

## CHECKLIST FINAL

- [ ] NIGREDO: Auditoría completa (HECHO)
- [ ] ALBEDO: Plan diseñado (HECHO)
- [ ] CITRINITAS: Scripts listos para ejecutar
- [ ] RUBEDO: Implementación paso a paso
- [ ] Tests: Verdes al 100%
- [ ] EMET: Verificación completada
- [ ] PALINGENESIA: Decodificación 3-capas
- [ ] Commits: 7 atómicos, cada uno verificable
- [ ] Documentación: Refleja código exactamente
- [ ] Memory: Lecciones guardadas para futuro

---

**SIGUIENTE ACCIÓN**: Aprobación de este plan antes de proceder a CITRINITAS+RUBEDO.
