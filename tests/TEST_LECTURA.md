# TEST DE LECTURA DE ARCHIVOS

Para verificar si el modelo lee archivos correctamente:

1. **Pregunta de prueba**: "Lee las primeras 10 líneas del archivo _docs/DEVELOPMENT_WORKFLOW_REFERENCIA.md"

2. **Lo que DEBERÍA responder** (contenido real):
```
# DEVELOPMENT_WORKFLOW_COPILOT.md — Proyecto Golem

> **Versión**: 2.1 — GitHub Copilot / Claude Haiku Edition
> **Fecha**: Abril 7, 2026 (Copilot Optimized: Abril 29, 2026)
> **Proyecto**: Golem — Asistente personal de escritorio con IA
> **Propietario**: José Esaú Díaz Hernández
> **⚠️ NOTA**: Esta es la versión para GitHub Copilot/Claude Haiku. Para Ollama local, usa `DEVELOPMENT_WORKFLOW_LOCAL.md`

---

## 🔱 CONSTITUCIÓN FORMAL DEL GOLEM
```

3. **Si responde con "Go Live community" o "Trello"**: El modelo está alucinando, no leyendo el archivo real.

4. **Si lee correctamente**: El problema estaba en la configuración anterior.

**Prueba ahora** después de cerrar y reabrir VS Code.