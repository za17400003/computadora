# 🚀 QUICK START — Ollama + Continue Local

**Tiempo**: 2 minutos de setup

---

## Paso 1: Verifica Ollama corriendo
```bash
curl http://localhost:11434/api/tags
```
Deberías ver: `{"models": [{"name": "llama3.1:8b", ...}, ...]}`

Si no → Abre terminal: `ollama serve`

---

## Paso 2: Verifica modelos instalados
```bash
ollama list
```

Necesitas:
- ✅ `llama3.1:8b` (chat principal)
- ✅ `qwen2.5-coder:1.5b-base` (autocompletado)
- ✅ `nomic-embed-text:latest` (embeddings)

Si falta uno → `ollama pull nombre-modelo`

---

## Paso 3: Abre VS Code + Continue

1. Abre carpeta: `C:\Users\woire\Documents\proyecto-golem`
2. Haz Ctrl+I (o ⌘+I en Mac) → abre Continue Chat
3. Deberías ver: **"Ollama Chat"** arriba (modelo seleccionado)

---

## Paso 4: Leer el Workflow

En Continue, arriba hay un botón **"Docs"**. 
Haz click → verás **"Workflow Local"** → **Lee primero esto.**

O abre directamente: `.continue/config.yaml` tiene referencias a docs.

---

## ✅ Estás listo para actuar

Ejemplos de cosas que puedes pedir:

### Bug Fix
```
En computadora/interfaz/ventana_principal.py, línea 87, 
la variable `config` no está definida. Corrige.
```

### Feature pequeño
```
Crea función en computadora/habilidades/ que cuente 
palabras en un archivo de texto. Incluye docstring.
```

### Refactor rápido
```
En tests/test_nlu.py, importa pytest en la línea 1 
(está faltando).
```

### Pregunta sobre estructura
```
¿Dónde debo poner un helper para parsear JSON?
```

---

## 🆘 Si algo no funciona

| Problema | Solución |
|----------|----------|
| Continue no conecta a Ollama | Verifica `curl localhost:11434` → debe responder |
| Modelo muy lento | Usa `qwen2.5-coder:1.5b-base` (más rápido) en lugar de llama3.1 |
| MCP no funciona | Cierra Continue, abre terminal en proyecto, ejecuta `npx @modelcontextprotocol/server-filesystem .` |
| Contexto muy grande | Divide tarea en pasos más pequeños (máximo 2000 tokens) |
| Código roto después de cambio | Vuelve a pedir: "Verifica sintaxis y corrige errores" |

---

## 💾 Comandos útiles (en terminal del proyecto)

```bash
# Ver workflow local
cat _docs/DEVELOPMENT_WORKFLOW_LOCAL.md

# Ejecutar tests
pytest tests/

# Ver estructura
ls -la computadora/

# Revisar cambios pendientes
git status
```

---

**LISTO.** Ahora puedes actuar en Continue localmente sin GitHub Copilot.
