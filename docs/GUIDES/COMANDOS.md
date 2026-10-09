# 📋 Comandos del Sistema (Formerly: Palabras Mágicas)

**Propósito**: Mapeo de todos los comandos disponibles en COMPUTADORA v2.0  
**Terminología**: "Palabras Mágicas" (lado esotérico) = "Comandos" (lado pragmático)  
**Ubicación de Código**: `computadora/nlp/commands/`  
**Owner**: Copilot (CTO)

---

## 📊 Comandos Implementados (Tabla Principal)

| # | Comando (Pragmático) | Palabra Mágica (Esotérico) | Acción | Handler | Estado | Notas |
|---|---|---|---|---|---|---|
| 1 | `tiempo` | Kronos | Obtener hora actual + zona horaria | `cmd_tiempo()` | ✅ | Básico |
| 2 | `ayuda` | Thoth | Listar comandos disponibles | `cmd_ayuda()` | ✅ | Básico |
| 3 | `estado` | Binah | Reportar estado del sistema | `cmd_estado()` | ✅ | Básico |
| 4 | `busca` | Chokmah | Búsqueda simple en web | `cmd_busca()` | ✅ | DuckDuckGo |
| 5 | `busca_verificada` | Emet | Búsqueda con verificación de fuente | `cmd_busca_verificada()` | ✅ | Con hierarchy |
| 6 | `auditoría` | Gevurah | Análisis de seguridad | `cmd_auditoria()` | ✅ | OWASP scan |
| 7 | `tarea` | Adam | Crear/listar/cerrar WIs | `cmd_tarea()` | ✅ | CRUD WI |
| 8 | `configurar` | Tetragramaton | Ver/cambiar settings | `cmd_configurar()` | ✅ | Config.json |
| 9 | `prueba` | Baján | Ejecutar tests | `cmd_prueba()` | ✅ Aprobada (04-06) | QA rápida |
| 10 | `sella` | Jatám | Tag de versión + CHANGELOG | `cmd_sella()` | ✅ Aprobada (04-06) | Git tag |
| 11 | `vigila` | Tzafá | Audit seguridad en tiempo real | `cmd_vigila()` | ✅ Aprobada (04-06) | Monitoreo |
| 12 | `recuerda` | Zajór | Búsqueda en memoria local | `cmd_recuerda()` | ✅ Aprobada (04-06) | Retrieval |
| 13 | `demuestra` | Hadguém | Ejecutar demos | `cmd_demuestra()` | ✅ Aprobada (04-06) | Demo mode |
| 14 | `blinda` | Sheriyón | OWASP scan focalizado | `cmd_blinda()` | ✅ Aprobada (04-07) | Security |
| 15 | `vincula` | Keshér | Conectar módulos huérfanos | `cmd_vincula()` | ✅ Aprobada (04-07) | Integration |
| 16 | `verifica` | Emet (formal) | Verificación coherencia SRS↔SDD↔Código | `cmd_verifica()` | ✅ Aprobada (04-08) | Consistency |
| 17 | **raziel** | Raziel (revelador) | Revelar estado protección 3 torres | `cmd_raziel()` | ⏳ CITRINITAS | Batch 9 |
| 18 | **wu_xing** | Wu Xing (5 fases) | Diagnóstico ciclo seguridad | `cmd_wu_xing()` | ⏳ CITRINITAS | Batch 9 |
| 19 | **shabbat** | Shabbat (descanso) | Graceful standby | `cmd_shabbat()` | ⏳ CITRINITAS | Batch 9 |
| 20 | merkavá | Merkavá (carro) | Orquestación 3 sistemas | `cmd_merkava()` | ⏳ DIFERIDA | Q2 2026 |
| 21 | tzaruf | Tzaruf (combinación) | Testing combinatorial | `cmd_tzaruf()` | ⏳ DIFERIDA | Q3 2026 |

---

## 🔄 Ciclo de Vida de Un Comando

```
NIGREDO (Diagnosis)
  → Necesidad identificada
  → "¿Qué acción quiere usuario que no existe?"
  → Output: Hallazgo + propuesta

ALBEDO (Investigation)  
  → Validar factibilidad
  → "¿Qué módulo ejecutaría? ¿Dependencias?"
  → Output: Especificación de comando

CITRINITAS (Synthesis)
  → Investigación externa + mejores prácticas
  → "¿Cómo otros sistemas hacen esto?"
  → Output: Recomendación + motivación

RUBEDO (Implementation)
  → Crear handler en NLU
  → Crear tests (happy path + edge)
  → Integrar con módulo target
  → Output: Comando funcional + testeado

PALINGENESIA (Retrospective)
  → Documentar en esta tabla (oficializar)
  → Registrar en git history
  → Lección aprendida
  → Output: Comando ✅ CLOSED
```

---

## 📍 Ubicación en Código

```
computadora/nlp/
├── engine.py                 ← NLU engine (parse intent)
├── commands/
│   ├── __init__.py
│   ├── cmd_tiempo.py        ← "tiempo" command
│   ├── cmd_busca_verificada.py  ← "busca_verificada" command
│   ├── cmd_verifica.py       ← "verifica" command
│   ├── ...
│   └── cmd_raziel.py         ← ⭐ NUEVO: raziel (Batch 9)
└── tools.py                  ← Registry de comandos
```

---

## 🎯 COMANDOS EN CICLO AHORA (Batch 9)

### raziel (רזיאל) — 360° Security Visibility

**Estado**: ⏳ CITRINITAS  
**Fase Alquímica**: 3/5  
**Timeline**: 2026-04-18 → 2026-04-22  
**Esfuerzo**: 4-6 horas

```python
# Pseudocódigo:
def cmd_raziel():
    """
    Revelar estado de protección de 3 Torres
    
    Output:
    {
      "enciclopedia": {"estado": "abierto|sellado", "sesiones": 3},
      "minimi": {"conexion": "LAN|Firestore|offline"},
      "computadora": {"modo": "hogar|foraneo", "amenaza": "normal|elevated"},
      "cifrado": {"estado": "active|inactive"},
      "vpn": {"conectado": true|false},
      "sigilo": "protegido|vulnerable"
    }
    """
```

### wu_xing (五行) — Diagnóstico Ciclo 5 Fases

**Estado**: ⏳ CITRINITAS  
**Fase Alquímica**: 3/5  
**Timeline**: 2026-04-18 → 2026-04-22  
**Esfuerzo**: 6-8 horas

```python
def cmd_wu_xing():
    """
    Diagnóstico de ciclo de seguridad (Wu Xing: 5 fases)
    
    shomer_bayit(Earth) → shomer_shaar(Metal) → 
      cifrado(Water) → vpn(Wood) → claves(Fire) → [ciclo]
    
    Output:
    {
      "fases": [
        {"nombre": "shomer_bayit", "estado": "ok|warn|error"},
        ...
      ],
      "ciclo": "generativo|destructivo",
      "ruptura_detectada": false|true,
      "recomendacion": "..."
    }
    """
```

### shabbat (שבת) — Graceful Standby

**Estado**: ⏳ CITRINITAS  
**Fase Alquímica**: 3/5  
**Timeline**: 2026-04-18 → 2026-04-20  
**Esfuerzo**: 3-4 horas

```python
def cmd_shabbat():
    """
    Modo de descanso programado (graceful shutdown)
    
    Acción:
    1. Guardar snapshot en datos/snapshot_shabbat.json
    2. Cerrar conexiones (servidor_api, servidor_enciclopedia)
    3. Desactivar escucha y percepción
    4. Entrar en modo bajo consumo
    
    Reactivación: "Computadora, despierta" → restaurar snapshot
    """
```

---

## 🛠️ Implementación: Notas para Developer

### Patrón de Handler

```python
# computadora/nlp/commands/cmd_NOMBRE.py

from computadora.nlp.tools import ToolDefinition

class ComandoNOMBRE(ToolDefinition):
    def __init__(self):
        self.name = "nombre_comando"
        self.hebrew = "hebreo"
        self.description = "..."
        self.implementation = self._execute
    
    def _execute(self, *args, **kwargs):
        # Lógica aquí
        return {"resultado": "..."}
```

### Registration

```python
# computadora/nlp/tools.py

from computadora.nlp.commands.cmd_raziel import ComandoRaziel

def register_all_commands(engine):
    engine.register_command(ComandoRaziel())
    # ... etc
```

---

## 📝 Notas de Estilo

- Nombre comando (pragmático): snake_case, verbo: `busca_verificada`
- Palabra mágica (esotérico): PascalCase, sustantivo: `Emet`
- Hebreo: transliteración + original: `Baján (בחן)`
- Documentación: siempre ambos lados visibles

---

**DE AQUÍ EN ADELANTE: Comandos claramente organizados, ciclo de vida transparente** ✨

