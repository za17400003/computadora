# 🎙️ GUÍA: Arreglar Computadora Mudo

## El Problema
**Tu micrófono captura 500 veces MÁS BAJO de lo necesario**
- Computadora espera volumen: **0.015**
- Tu micrófono: **0.00003** ← ¡Casi silencio!

Por eso Computadora no te escucha cuando hablas.

---

## ✅ SOLUCIONES (en orden de preferencia)

### OPCIÓN 1: Subir Volumen del Micrófono (RECOMENDADO)

#### Windows 10/11:
1. **Click derecho** en icono de volumen (abajo a la derecha)
2. Selecciona **"Sonidos"** o abre **Settings → Sound**
3. Baja hasta **"Advanced"** → **"Volume mixer"** o **"App volume and device preferences"**
4. Busca **"Microphone Array (Intel...)"** 
5. **Sube volumen a 100%**
6. **IMPORTANTE**: Verifica que NO esté en **"Muted"** (silenciado)

#### Si aún es muy bajo:
1. Settings → Sound → Microphone → **"Device properties"**
2. Pestaña **"Advanced"**
3. **"Additional device properties"**
4. Pestaña **"Levels"**
5. Sube **"Microphone Boost"** a máximo (+20 dB)

---

### OPCIÓN 2: Ajustar Configuración (Solución Rápida)

Si no puedes aumentar volumen en Windows (o no funciona):

1. Abre: `_config/config.json`
2. Busca la sección `"escucha"`
3. Cambia:
   ```json
   "umbral_volumen": 0.015,
   ```
   Por:
   ```json
   "umbral_volumen": 0.00005,
   ```
4. Guarda el archivo
5. **Reinicia Computadora**

**⚠️ NOTA**: Esto hará que Computadora sea muy sensible a CUALQUIER ruido. Mejor hacer OPCIÓN 1.

---

### OPCIÓN 3: Usar Otro Dispositivo

Si el micrófono Intel Bluetooth está roto:

1. Settings → Sound → Microphone
2. Cambia a **"Microphone Array (otro nombre)"** si disponible
3. O conecta un micrófono USB externo

---

## 🧪 VERIFICAR QUE FUNCIONA

Después de hacer los cambios:

```bash
# Ejecuta esto en PowerShell:
cd C:\Users\woire\Documents\proyecto-golem

# Prueba 1: Verificar volumen
python scripts\calibrar_microfono.py

# Prueba 2: Iniciar Computadora
python -m computadora
```

**Busca en la consola**:
- `"escuchando"` → significa que está escuchando
- `"voz detectada"` → significa que te escuchó
- `"procesando"` → significa que está procesando lo que dijiste

---

## 📝 RESUMEN DE COMPONENTES

| Componente | Status | Nota |
|-----------|--------|------|
| Whisper (ASR) | ✅ OK | Instalado, listo |
| edge-tts (TTS) | ✅ OK | Instalado, listo |
| Sounddevice | ✅ OK | Detecta micrófono |
| LM Studio | ✅ OK | 6 modelos cargados |
| **Micrófono** | ❌ BAJO | ← **ARREGLA ESTO** |
| HiloEscucha | ✅ OK | Thread ready |

---

## 🔊 DESPUÉS DE ARREGLARLO

Computadora debería:
1. ✓ Escuchar continuamente
2. ✓ Responder al wake word **"computadora"**
3. ✓ Responder a tu rostro detectado
4. ✓ Procesar con LM Studio
5. ✓ Responder por voz (edge-tts)

---

## ❓ SI SIGUE SIN FUNCIONAR

Ejecuta el diagnóstico completo:
```bash
python scripts\diagnostico_audio.py
```

Y comparte los resultados en el chat.

---

**Instrucciones creadas**: Abril 26, 2026
**Problema**: Micrófono bajo
**Solución**: ↑ Volumen Windows o ↓ Umbral config
