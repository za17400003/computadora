# PRUEBA DE LECTURA DE ARCHIVOS

## Instrucciones para probar:

1. Reinicia VS Code completamente
2. Abre el panel de Continue (Ctrl+Shift+P → "Continue: Open Chat")
3. Pregunta: "Lee las primeras 10 líneas del archivo _docs/TEST_LECTURA_SIMPLE.md"

## Lo que debería responder (contenido real):

```
# TEST FILE - VERIFICACIÓN DE LECTURA

Esta es una línea de prueba número 1.
Esta es una línea de prueba número 2.
Esta es una línea de prueba número 3.
Esta es una línea de prueba número 4.
Esta es una línea de prueba número 5.
Esta es una línea de prueba número 6.
Esta es una línea de prueba número 7.
Esta es una línea de prueba número 8.
Esta es una línea de prueba número 9.
Esta es una línea de prueba número 10.
```

## Si alucina (inventando contenido):

- Significa que el modelo no está usando las herramientas MCP
- Necesitamos cambiar a un modelo diferente o configuración

## Contenido real del archivo DEVELOPMENT_WORKFLOW_REFERENCIA.md:

```
# DEVELOPMENT_WORKFLOW_COPILOT.md — Proyecto Golem

> **Versión**: 2.1 — GitHub Copilot / Claude Haiku Edition
> **Fecha**: Abril 7, 2026 (Copilot Optimized: Abril 29, 2026)
> **Proyecto**: Golem — Asistente personal de escritorio con IA
> **Propietario**: José Esaú Díaz Hernández
> **⚠️ NOTA**: Esta es la versión para GitHub Copilot/Claude Haiku. Para Ollama local, usa `DEVELOPMENT_WORKFLOW_LOCAL.md`
```

El modelo anterior inventó contenido sobre "Introduction", "Workflow Overview", etc. que NO existe en el archivo.