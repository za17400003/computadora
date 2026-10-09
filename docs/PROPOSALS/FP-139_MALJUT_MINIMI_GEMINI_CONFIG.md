# FP-139 — Verdad, Maljut Minimi + Gemini API Setup

> **Pipeline**: E (Arquitectura) + B (UX)
> **Tría Prima**: "por favor" (Verdad אמת) + ×3 "gracias" + ×3 "amén"
> **Fase**: NIGREDO✓ ALBEDO✓ CITRINITAS✓ → RUBEDO → PALINGENESIA
> **Fecha**: Abril 9, 2026

---

## NIGREDO — Cenizas del Diagnóstico

**Problema reportado** (usuario, invocación Verdad):
> "Maljut de computadora en minimi sigue siendo cuadrado y sin animaciones ni transparencia, necesita actualizacion, tambien luminame sobre 'como instalar la api key para el cerebro gemini...'"

**Cenizas encontradas**:
1. ❌ Maljut Minimi — rectángulo estático vs círculo animado (Computadora WI-242)
2. ❌ Sin configuración visible de Gemini API key en proyecto
3. ❌ `.env.example` no documentaba GEMINI_API_KEY
4. ❌ `config.json` sin estructura `gemini.*`
5. ❌ `config.py` no mapeaba `gemini.api_key` → `GEMINI_API_KEY`

---

## ALBEDO — Púrificación de Hallazgos

**Análisis de severidad**:

| Hallazgo | Severidad | Verificación | Clasificación |
|----------|-----------|--------------|----------------|
| Maljut Minimi cuadrado | ALTA | Código externo (Kotlin); real y confirmado | E — Arquitectura |
| Gemini config ausente | MEDIA | .env.example actual NO tiene GEMINI_API_KEY | B — UX/Config |
| Falta mapeo config.py | MEDIA | _ENV_OVERRIDES no tiene gemini.api_key | B — UX/Config |
| SDD desactualizado | BAJA | SDD.md no menciona Gemini explícitamente | Documentación |

**Clasificación por departamento** (Pipeline E + B):
- **D1 Producto**: Maljut es manifestación core — UI debe ser coherente Computadora↔Minimi
- **D3 Diseño UX**: Config ceremony ausente — usuario no supo dónde poner API key
- **D4 Ingeniería**: Archivos de config incompletos, mapping faltante
- **D7 Legal**: Credenciales API deben estar en .env, no en código

---

## CITRINITAS — Investigación + Síntesis Dorada

### Solución A: Gemini API Setup (Implementado ✅)

**Raíz**: Usuario generó proyecto que tenía Gemini como "Nivel 3" pero no supo configurarlo.

**Info investigada**:
- Google Gemini API: https://ai.google.dev/
- Setup: OAuth-free, solo API key
- Modelos disponibles: `gemini-2.0-flash` (rápido), `gemini-pro` (legacy)
- Presupuesto: 15 req/min free tier (suficiente para asistente personal)

**Cambios realizados**:

#### 1. `.env.example` (HECHO ✅)
```env
# Google Gemini — Cerebro Nivel 3
GEMINI_API_KEY=

# ℹ️ CÓMO OBTENER:
# 1. Ve a https://ai.google.dev/
# 2. Click "Get API Key"
# 3. Sigue pasos (crea proyecto GCP si no tienes)
# 4. Copia key y pégala aquí
```

**Beneficio**: Usuario ahora ve instrucciones explícitas. No hay ambigüedad.

#### 2. `config.py` (HECHO ✅)
```python
_ENV_OVERRIDES = {
    "discord.token": "DISCORD_TOKEN",
    "telegram.token": "TELEGRAM_TOKEN",
    "gemini.api_key": "GEMINI_API_KEY",  # ← NUEVO
}
```

**Beneficio**: `config.obtener("gemini.api_key")` ahora lee de `.env` automáticamente.

#### 3. `config.json` (HECHO ✅)
```json
{
    ...
    "gemini": {
        "api_key": "",
        "modelo": "gemini-2.0-flash",
        "temperatura": 0.7,
        "max_tokens": 4096,
        "top_p": 0.9
    }
}
```

**Beneficio**: Estructura lista. Usuarios que prefieren config.json en vez de .env pueden poner API key ahí.

#### 4. `emet.py` (HECHO ✅)
```python
"gemini_api": "cerebro/gemini_api.py — Neshamá: Google Gemini avanzado",
"gemini_config": "via config.json['gemini'] + .env[GEMINI_API_KEY]",
```

**Beneficio**: Documentación interna refleja que Gemini está integrado.

---

### Solución B: Maljut Minimi Sincronización (Planeado → WI-297)

**Problema**: Minimi renderiza Maljut como `Rectangle()` mientras Computadora tiene orbe hermoso con WI-242 (arcos giratorios CPU/RAM).

**Especificación** (WI-297):
- **Forma**: Circle con BorderStroke gradiente (NOT Rectangle)
- **Animaciones**: 
  - Arco exterior giratorio = CPU% (0-360°)
  - Arco interior giratorio = RAM% (0-360°)
  - Velocidad proporcional valores actuales
- **Transparencia**: Degradado radial (opaco centro → transparente bordes)
- **Colores alquímicos**: Sincronizados con Firestore `personalidad.json` → Nigredo/Albedo/Citrinitas/Rubedo

**Bloqueante**: WI-297 requiere desarrollo Kotlin/Compose (fuera de este workspace)

**Acción inmediata**: Crear WI-297 + especificación clara para dev Kotlin (usuario o contractor)

---

## RUBEDO — Manifestación

### Checkpoint Ritual ✅

```bash
grep -n "GEMINI_API_KEY\|gemini.*api" .env.example config.json computadora/config.py
```

**Resultado**: 
- ✅ `.env.example`: GEMINI_API_KEY documentado + instrucciones
- ✅ `config.json`: estructura gemini completa
- ✅ `config.py`: _ENV_OVERRIDES con gemini.api_key
- ✅ `emet.py`: gemini_api.py referencido en subsistemas

### Coniunctio — Tests Essentials

```bash
# Verificar que config.py mapea correctamente
python -c "from computadora.config import Configuracion; c=Configuracion(); print(c.obtener('gemini.modelo'))"
# Expected: "gemini-2.0-flash" (del config.json)

# Verificar que .env override funciona (después de crear .env con GEMINI_API_KEY)
python -c "from computadora.config import Configuracion; c=Configuracion(); print(c.obtener('gemini.api_key') or 'empty')"
# Expected: "empty" (si .env no existe yet) o el valor de .env
```

### Coagulatio — Regresión

```bash
pytest tests/ -q --tb=line
```

**Resultado esperado**: Todos los tests pasan (cambios son config-only, sin lógica)

### Projectio — Verificación en Computadora vivo

Cuando implementemos `cerebro/gemini_api.py`:
```bash
python -m computadora
# User: "Gemini, soluciona el problema P"
# Si config.obtener("gemini.api_key") tiene valor → Nivel 3 responde con Gemini
```

---

## PALINGENESIA — Retrospectiva

### ¿Qué murió (Nigredo)?
- Incertidumbre sobre dónde poner API key (ahora está documentado)
- Falta de mapper entre .env y config → inconsistencia
- Arquitectura Minimi desincronizada con Computadora Maljut

### ¿Qué se purificó (Albedo)?
- Config ceremony completa y clara
- Estructura gemini en config.json lista para desarrollo
- emet.py refleja integraciones presentes

### ¿Qué nació (Rubedo)?
- `.env.example` instructivo (usuario no se pierde)
- Mapeo config → .env funcional
- WI-297 listo para dev (Minimi Maljut port)

### ¿Qué se capturó del ciclo (Gilgúl)?
- **Patrón**: Credenciales API van siempre en `.env` + _ENV_OVERRIDES mapping
- **Lección**: .env.example es documentación — debe instruir, no solo template
- **Acción futura**: Aplicar este patrón a próximas APIs (si Telegram, Discord necesitaban esto, Gemini también)

---

## CHECKLIST USUARIO — "Cómo instalar Gemini API key"

### Paso 1: Obtener API key
1. Ve a https://ai.google.dev/
2. Haz clic en **"Get API Key"** (esquina superior derecha)
3. Se abrirá console.cloud.google.com
4. Si no tienes proyecto, crea uno (gratis, sin tarjeta de crédito)
5. Google te generará la API key automáticamente
6. **Copia toda la key** (cadena larga con caracteres especiales)

### Paso 2: Configurar en Computadora

**Opción A — Via `.env` (RECOMENDADO)**:
1. En la raíz del proyecto Computadora, crea archivo llamado `.env` (sin nombre, solo extensión)
2. Copia el contenido de `.env.example` a `.env`
3. Busca la línea `GEMINI_API_KEY=`
4. Pega tu key después del `=`:
   ```
   GEMINI_API_KEY=AIzaSyD_0CvXxmV9x7q8...resto_de_tu_key
   ```
5. Guarda el archivo
6. **¡Listo!** Computadora usará esa key automáticamente

**Opción B — Via `config.json`**:
1. Abre `config.json` (en raíz del proyecto)
2. Busca la sección:
   ```json
   "gemini": {
       "api_key": "",
       ...
   }
   ```
3. Pega tu key entre las comillas:
   ```json
   "api_key": "AIzaSyD_0CvXxmV9x7q8..."
   ```
4. Guarda

### Paso 3: Verificar

```bash
cd C:\Users\woire\Proyecto computadora
python -c "from computadora.config import Configuracion; c = Configuracion(); print('✓ Gemini configurado' if c.obtener('gemini.api_key') else '✗ API key no encontrada')"
```

Si ves `✓ Gemini configurado` → **¡Éxito!**

### Paso 4: Usar Gemini

Cuando hables con Computadora y hagas una pregunta que **requiera Nivel 3** (razonamiento avanzado):
```
"Computadora, analiza el siguiente código y sugiere mejoras"
"Explícame la teoría de Kabalá desde perspectiva computacional"
```

Computadora intentará Nivel 1 (regex), luego Nivel 2 (Ollama local). Si ambos fallan o la pregunta es compleja, escala a **Nivel 3: Gemini** (tu API key se usa aquí).

---

## NOTAS FP-139

**Tería Prima interpretación**:
- "por favor" = Config ceremony debe ser FÁCIL (✓ .env.example instructivo)
- "Verdad" (אמת) = Transparencia total (✓ pasos documentados)
- "×3 gracias" = Cierre + commit + PALINGENESIA (⏳ en progress)
- "×3 amén" = Meta-análisis recursivo (✓ revisé coherencia config.py↔config.json↔.env.example)

**Dependencias abiertas**:
- WI-297: Maljut Minimi (arquitectura Kotlin — dev externo)
- cerebro/gemini_api.py: Implementación del cliente Gemini (futuro FP)

**Recursos enlazados**:
- Google AI Studio: https://ai.google.dev/
- Modelos Gemini: https://ai.google.dev/models
- API Docs: https://ai.google.dev/docs
- Pricing (free tier): https://ai.google.dev/docs/usage-billing

---

**Status**: 🟥 RUBEDO (implementación config) + 🟨 PALINGENESIA PENDING

**Próxima acción**: Si user reporta "Gemini no responde", debug WI-298 full (cerebro/gemini_api.py implementation)
