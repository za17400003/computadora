# 🔐 Guía Copilot Token vs Gemini API Key

> **Usuario pregunta**: "¿Cómo obtengo COPILOT_TOKEN?" 
> **Respuesta directa**: **NO LO OBTIENES — Golem lo obtiene automáticamente por ti.**

---

## Dos Cerebros, Dos Rutas Diferentes

| Característica | Copilot (Nivel 3A) | Gemini (Nivel 3B) |
|---|---|---|
| **¿Dónde obtengo Credencial?** | **Automático** 🤖 | Manual 🔑 |
| **Primera ejecución** | Popup en navegador | Paperwork en web |
| **Token guardado en** | `datos/copilot_auth.json` (cifrado) | Tú lo pegas en `.env` |
| **¿Qué hace el usuario?** | Autoriza en GitHub (1 clic) | Copia/pega API key |
| **Refresco automático?** | ✅ SÍ (antes de expirar) | ❌ NO (manual si expira) |
| **¿Necesita .env?** | NO (se ignora input manual) | SÍ (OBLIGATORIO) |
| **Riesgo de seguridad** | Bajo (OAuth estándar) | Medio (almacena key en .env) |

---

## 📖 GUÍA COPILOT — Obtención Automática

### Escenario 1: Primera vez usando Copilot

```
Tú escribes en Golem → "Copilot, ayúdame con X"
                    ↓
Golem escala a Nivel 3 (Copilot) porque Nivel 1/2 no pueden
                    ↓
copilot_api.py inicia OAuth Device Flow
                    ↓
Tu navegador se abre automáticamente con:
  "Golem solicita permiso para acceder a tu GitHub"
                    ↓
Tú ves un código de 8 caracteres (ej: ABCD-1234)
                    ↓
Haces clic >> "Autorizar" >> GitHub confirma
                    ↓
Golem recibe token y lo guarda en:
  datos/copilot_auth.json (CIFRADO)
                    ↓
✅ Listo — Copilot funciona desde ahora
```

### Escenario 2: Token expirado (ocurre ~1 vez/mes)

```
Durante charla, token expira
                    ↓
copilot_api.py detecta expiración
                    ↓
Automáticamente solicita refresco
                    ↓
GitHub envía token nuevo (sin intervención)
                    ↓
✅ Transparente — tú no haces nada
```

### ❌ QUÉ NO DEBES HACER

```
❌ NO: Copiar/pegar token manual en .env
       (Golem lo ignora, además es inseguro)

❌ NO: Dejar COPILOT_TOKEN vacío
       (Está bien — es NORMAL que esté vacío)

❌ NO: Generar token en VS Code y pegarlo aquí
       (VS Code token ≠ Golem token OAuth)

✅ SÍ: Dejar .env como está
        Autorizar en navegador cuando Golem pida
        Dejar que Golem guarde token automáticamente
```

---

## 🔑 GUÍA GEMINI — Obtención Manual

### Por qué es diferente

Gemini NO tiene OAuth Device Flow de cliente → debes obtener API key tú mismo.

### Pasos

#### Paso 1: Crear proyecto en Google Cloud

1. Ve a https://console.cloud.google.com/
2. Haz clic en el icono de proyecto (arriba) → "New Project"
3. Nombre: "Golem" (o lo que quieras)
4. Haz clic "Create" → espera 30s
5. Selecciona tu nuevo proyecto

#### Paso 2: Habilitar Gemini API

1. Ve a https://ai.google.dev/ (otra pestaña)
2. Haz clic en **"Get API Key"** (esquina superior derecha)
3. Se te ofrecerá:
   - "Crear API key en proyecto existente" → selecciona tu "Golem"
   - "Crear API key en nuevo proyecto" → crea uno automático(recomendado si no quieres configurar Google Cloud)
4. Haz clic el que prefieras → Google te genera una **API key larga**

#### Paso 3: Copiar la API key

Google te mostrará algo como:

```
<YOUR_GEMINI_API_KEY>
```

**Cópiala completamente** (incluyendo `AIzaSy...` al inicio).

#### Paso 4: Pegar en Golem

**Opción A: Vía `.env`** (RECOMENDADO)

```bash
# 1. Abre .env (o cópialo de .env.example)
# 2. Busca: GEMINI_API_KEY=
# 3. Pega tu key:
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
# 4. Guarda el archivo
```

**Opción B: Vía `config.json`**

```json
{
    ...
    "gemini": {
        "api_key": "<YOUR_GEMINI_API_KEY>",
        ...
    }
}
```

#### Paso 5: Verificar

```bash
python -c "from golem.config import Configuracion; c = Configuracion(); print('✓ Gemini OK' if c.obtener('gemini.api_key') else '✗ KEY FALTANTE')"
```

Si ves `✓ Gemini OK` → **¡Éxito!**

---

## 🎯 Matriz de Decisión: "¿Debo hacer algo?"

```
¿Necesito Copilot?
  ├─ Sí → Autoriza en navegador cuando Golem pida (primera vez)
  │       Listo — ¡automático a partir de ahora!
  │
  └─ No → Nada que hacer, natural fallback a Gemini/Ollama

¿Necesito Gemini?
  ├─ Sí → Ve a https://ai.google.dev/, obtén API key, pega en .env
  │       Listo — verificar con test
  │
  └─ No → Nada que hacer, Ollama local es suficiente
```

---

## 🔒 Seguridad

| Dato | Almacenamiento | Exposición | Riesgo |
|------|----------------|-----------|--------|
| Copilot token | `datos/copilot_auth.json` | Cifrado localmente | Bajo (if BIOS segura) |
| Gemini API key | `.env` (usuario guardó) | Texto CLARO | **MEDIO** (NO subir a git) |
| Access token GitHub | Memoria RAM | Procesos solo de Golem | Bajo (volatil) |

**Recomendación**: 
- `.env` está en `.gitignore` por defecto (no sube a GitHub)
- NUNCA compartir `.env` con otros
- NUNCA copiar credenciales en chats públicos

---

## ❓ FAQ

**P: ¿Golem necesita Copilot para funcionar?**  
R: No. Ya tiene Nivel 2 (Ollama local) que es suficiente. Copilot es "escalación premium" para razonamiento avanzado.

**P: ¿Es gratis Copilot?**  
R: Sí, tienes 5000 requests/mes de cortesía **si** autorizas GitHub. No hay costo oculto.

**P: ¿Y Gemini?**  
R: Gemini tiene free tier: 15 requests/min (suficiente para asistente personal). Después, pago por uso (~$0.075/1M tokens).

**P: ¿Puedo usar AMBOS a la vez?**  
R: No necesario. Golem intenta Nivel 2 (Ollama) primero. Si falla, escala a Nivel 3 (Copilot O Gemini, según config). Usa el que prefieras.

**P: ¿Dónde veo mi token guardado?**  
R: `datos/copilot_auth.json` (Copilot) — cifrado, no legible a simple vista. Para Gemini: `.env` (si lo pusiste ahí).

**P: ¿Se expiran los tokens?**  
R: Copilot: automático (Golem lo maneja) | Gemini: sí, pero raro (>3 meses).

---

## 📞 Troubleshooting

### "Copilot no abrió el navegador"
```bash
# 1. Verifica que Golem está en terminal (no interfaz GUI bloqueada)
# 2. Mira logs: busca "OAuth" o "device code"
# 3. Si dice "pending..." → abre manualmente en navegador el link que aparece
```

### "Gemini dice 'API key inválida'"  
```bash
# 1. Verifica que copiaste la COMPLETA (incluir "AIzaSy..." inicio)
# 2. Verifica que NO hay espacios extras al pegarla
# 3. Verifica que es de https://ai.google.dev/, no otro lugar
# 4. Reinicia Golem: python -m golem
```

### "No entra navegador del OAuth"
```bash
# Si estás en WSL/servidor sin GUI:
# 1. Copia el URL del código que aparece en terminal
# 2. Abre en tu computadora local
# 3. Autoriza
# 4. Token se obtiene automáticamente
```

---

**Resumen**: Copilot = automático (OAuth). Gemini = manual (copy/paste). ¡Ambos listos en minutos! 🚀
