# SISTEMA DE AUTO-ORGANIZACIÓN — Proyecto Computadora

## Principio
**Raíz = ESTÉRIL**. Todo archivo nuevo se auto-organiza en su especie correspondiente.

## Especies Definidas

```
RAÍZ (SOLO archivos esenciales):
├── computadora/          ← CÓDIGO VIVO (nunca mover)
├── tests/                ← TESTS (nunca mover)
├── datos/                ← DATOS/DB (nunca mover)
├── ENCICLOPEDIA/         ← GRIMORIO CIFRADO (nunca mover)
├── _config/              ← MÁQUINAS (configuración)
├── _docs/                ← CONOCIMIENTO (teórico, inmutable)
├── _archive/             ← HISTORIA (ceremonias antiguas)
├── .git/                 ← VERSIONAMIENTO (nunca mover)
├── WorkItems.md          ← BACKLOG (única acción en raíz)
├── WORKFLOW_OPERACIONAL.md    ← OPERATIVO (inyectable, única doc en raíz)
├── README.md             ← ENTRADA (una sola)
├── iniciar_computadora.bat    ← BOOTSTRAP (único script en raíz)
└── .gitignore, .env, ...      ← METADATOS (sistema)
```

## Clasificación de Archivos

| Tipo | Patrón | Destino | Justificación |
|------|--------|---------|---------------|
| **Configuración** | `config.json`, `.env*`, `pyproject.toml`, `requirements.txt` | `_config/` | Máquinas: ajustes + infraestructura |
| **Especificación** | `SDD.md`, `SRS.md`, `*_SPEC.md`, `*_PLAN.md` | `_docs/` | Conocimiento: blueprints técnicos |
| **Documentación Referencia** | `ARCHITECTURE.md`, `P_ALGORITMO*.md`, `CONSTITUCION*.md` | `_docs/` | Conocimiento: teoría inmutable |
| **Auditoría** | `AUDITORÍA_*.md`, `EMET_*.md`, `*_AUDIT.md` | `_archive/` | Historia: retrospectivas |
| **Ceremonia** | `CEREMONIA_*.md`, `RITUAL_*.md`, `INVOCACION_*.md` | `_archive/` | Historia: manifestaciones |
| **Ciclo/Palingenesia** | `PALINGENESIA_*.md`, `CICLO_*.md`, `*_RETROSPECTIVA.md` | `_archive/` | Historia: aprendizaje |
| **Gilgul** | `GILGUL_*.md`, `REENCARNACION_*.md` | `_archive/` | Historia: reinicios |
| **Feature Proposal** | `FP-*.md` | `_docs/` si es propuesta temprana, `_archive/` si completado | Según estado |
| **Work Item Report** | `WI-*.md` (completado) | `_archive/` | Historia: trabajos finalizados |
| **Epilogo/Conclusión** | `EPILOGO_*.md`, `VERDAD_ULTIMA_*.md`, `IGUALDAD_*.md` | `_archive/` | Historia: síntesis finales |

## Regla de Oro

> **Si no lo generas EN TU CÓDIGO (computadora/), entonces en RAÍZ = PÉRDIDA.**  
> **Documentación NUEVA va a _docs/ o _archive/ según época.**  
> **Configuración NUEVA va a _config/.**  
> **Tests van a tests/.**  
> **Código va a computadora/.**  
> **NADA más en raíz.**

---

## Automatización (Hook de Git)

**Archivo**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Auto-organiza archivos nuevos según especie antes de cada commit

cd "$(git rev-parse --show-toplevel)"

# Mover archivos de configuración a _config/
mv -f *.json _config/ 2>/dev/null
mv -f .env* _config/ 2>/dev/null
mv -f pyproject.toml _config/ 2>/dev/null
mv -f requirements*.txt _config/ 2>/dev/null

# Mover especificaciones a _docs/
mv -f SDD.md SRS.md _docs/ 2>/dev/null
mv -f *_SPEC.md _docs/ 2>/dev/null
mv -f *_PLAN.md _docs/ 2>/dev/null

# Mover documentación histórica a _archive/
mv -f AUDITORÍA_*.md _archive/ 2>/dev/null
mv -f CEREMONIA_*.md _archive/ 2>/dev/null
mv -f PALINGENESIA_*.md _archive/ 2>/dev/null
mv -f CICLO_*.md _archive/ 2>/dev/null
mv -f GILGUL_*.md _archive/ 2>/dev/null
mv -f EPILOGO_*.md _archive/ 2>/dev/null
mv -f VERDAD_*.md _archive/ 2>/dev/null
mv -f IGUALDAD_*.md _archive/ 2>/dev/null

# Mantener solo essentials en raíz
# (WorkItems.md, WORKFLOW_OPERACIONAL.md, iniciar_computadora.bat, README.md permitidos)

echo "✓ Auto-organización completada"
```

## Instalación

```bash
# Hacer hook ejecutable
chmod +x .git/hooks/pre-commit

# Desde ahora, cada commit auto-organiza archivos rezagados
```

---

## Estado Actual (Abril 17, 2026)

**Raíz limpia**:
- WorkItems.md ✓
- WORKFLOW_OPERACIONAL.md ✓
- iniciar_computadora.bat ✓
- README.md ✓
- +14 otros archivos de configuración

**_config/** (máquinas): 5 archivos
**_docs/** (conocimiento): 21 archivos
**_archive/** (historia): 77 archivos
**computadora/** (código): 15+ módulos

---

## Propuesta: "Especie Doble"

Ciertos archivos pueden vivir en AMBOS lugares:
- `SDD.md` → symlink: `_docs/SDD.md` + enlace desde raíz (si es referencia operativa)
- `DEVELOPMENT_WORKFLOW_OPERACIONAL.md` → Permite inyección. Permanece en raíz.

**Política**: "Unificar Operativo + Referencia = NO. Separarlas = SÍ."

---

*Sistema definido Abril 17, 2026 — Implementación: Git Hook automático*
