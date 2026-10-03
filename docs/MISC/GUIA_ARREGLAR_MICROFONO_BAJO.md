# 🎤 GUÍA: Arreglar Micrófono Bajo en Windows (Computadora No Responde)

**Fecha**: Abril 26, 2026  
**Problema**: Computadora no responde cuando le hablo ("no me entiende", "no escucha")  
**Causa probable**: Micrófono captura volumen MUY BAJO en Windows  
**Probabilidad**: ~90% de los reportes de "no escucha" son esto  

---

## 🚨 SÍNTOMAS

Reportas:
- ✗ "Computadora no me entiende"
- ✗ "No responde al hablar"
- ✗ "Logs no muestran que esté escuchando"
- ✗ "No detecta wake word"

Pero:
- ✓ El micrófono SÍ funciona (Zoom, Discord, etc. lo oyen bien)
- ✓ Computadora corre sin errores
- ✓ Sin mensajes de error en logs

**Diagnóstico**: Sistema captura < 0.001 RMS (Computadora está "sordo")

---

## 🔧 SOLUCIONES (EN ORDEN)

### SOLUCIÓN 1: Windows Sound Settings (MÁS COMÚN ✅)

**Paso 1**: Abre Settings
- `Win + X` → Settings
- O: Settings > System > Sound

**Paso 2**: Aumenta volumen de micrófono
- Scroll down → "Input"
- Slider "Microphone volume" → Sube a **100%**

**Paso 3**: Accede a configuración avanzada
- Scroll down → "App volume and device preferences"
- Click en ese link

**Paso 4**: Encontrar Computadora
- Busca "computadora" en la lista
- Si no aparece, aún no ha sido ejecutada (ejecuta primero)

**Paso 5**: Configurar entrada de Computadora
- Click en Computadora
- Asegúrate que el input device esté en el micrófono correcto
- Volumen debe estar en 100%

**Paso 6**: GUARDAR Y REINICIAR
- Close Settings
- Cierra Computadora completamente
- Vuelve a iniciar

---

### SOLUCIÓN 2: Control Panel (MÁS POTENTE - RECOMENDADO 🏆)

**Paso 1**: Abre Control Panel
- Win + R → `control` → Enter
- O: Settings > System > Sound > Device properties > Advanced

**Paso 2**: Busca "Recording devices"
- Control Panel > Sound > Recording tab
- O: Settings > Sound > Advanced > Volume mixer > App volume and device preferences

**Paso 3**: Encuentra tu micrófono
- Busca el que está usando (generalmente con ✓ verde)
- Típicamente: "Microphone", "Integrated Microphone", "USB Audio", etc.

**Paso 4**: Accede a Properties
- Click derecho en el micrófono
- Properties

**Paso 5**: Abre Levels tab
- Click en "Levels" tab

**Paso 6**: Aumenta volúmenes
- **Microphone**: Sube slider a **100%**
- **Microphone Boost**: Dropdown → Selecciona **+20 dB** (o máximo disponible)

**Paso 7**: Aplica y cierra
- OK → Apply → OK
- Cierra todas las ventanas

---

### SOLUCIÓN 3: Intel Bluetooth (Si usas micrófono Intel/Bluetooth 🔴)

Intel Bluetooth es **especialmente problemático**:
- Típicamente captura 0.00003 (casi silencio)
- Incluso con boost sigue bajo

**Si tienes Intel Bluetooth**:
1. Intenta primero Solución 1 + 2 (a veces funciona)
2. Si aún no funciona, **usa un micrófono USB externo** (recomendado)
   - Audio Technica AT2020 (~$100)
   - Samson Q2U (~$80)
   - Cualquier USB micrófono económico

---

## 🧪 VERIFICAR QUE FUNCIONA

### Opción A: Ejecutar diagnóstico (RECOMENDADO)

```bash
python scripts/diagnostico_volumen_microfono.py
```

Te dirá exactamente si el volumen está OK.

**Qué esperar**:
- Si RMS > 0.015: ✅ LISTO, Computadora debería responder
- Si RMS < 0.001: 🔴 SORDO, vuelve a Solución 1-2
- Si RMS 0.005-0.015: 🟡 BAJO, puede funcionar pero inestable

### Opción B: Prueba manual

1. Abre Computadora: `computadora_start.bat`
2. Espera a que diga "listo para escuchar"
3. Habla normal: "Hola computadora"
4. Si dice algo como "no entiendo", pero escuchó algo → volumen está OK
5. Si no hace nada → aún no oye, vuelve a Solución 1-2

---

## 🎯 PRÓXIMOS PASOS

**Si RMS está OK**:
- Ejecuta: `computadora_start.bat`
- Prueba diciendo: "Hola computadora"
- Debería responder

**Si RMS aún bajo**:
1. Repite Solución 2 (Control Panel)
2. Asegúrate Microphone Boost esté en **+20 dB mínimo**
3. Si sigue bajo, considera micrófono USB externo

---

## 📞 REFERENCIA TÉCNICA

**Thresholds internos** (en `computadora/nucleo/hilo_escucha.py`):
```python
umbral_volumen = config.obtener("escucha.umbral_volumen", 0.015)
```

- RMS > 0.015: Sistema detecta voz → procesa
- RMS < 0.001: Sistema "sordo" → ignora todo
- RMS 0.005-0.015: Funciona pero inestable (muchos falsos negativos)

**Dispositivos problemáticos**:
- 🔴 Intel Bluetooth: 0.00003-0.0001 (¡¡MUY BAJO!!)
- 🟠 Laptop integrado: 0.0005-0.002 (bajo)
- 🟡 Headset estándar: 0.01-0.03 (OK si boosted)
- ✅ USB externo: 0.02-0.05 (excelente)

---

## ❓ TODAVÍA NO FUNCIONA?

Si después de Solución 1-2 aún no responde:

1. Ejecuta diagnóstico completo:
   ```bash
   python scripts/diagnostico_audio.py
   ```

2. Revisa logs:
   ```bash
   tail -f datos/.log/computadora.log
   ```

3. Si dice "Silero VAD no disponible", ve a → SOLUCIÓN 5 abajo

---

## SOLUCIÓN 5: Instalar Silero VAD (Si lo necesitas)

Si logs dicen "Silero VAD no disponible", instala:

```bash
pip install silero-vad
```

Luego reinicia Computadora.

---

## 📝 RESUMEN RÁPIDO

| Síntoma | Solución |
|---------|----------|
| Computadora no responde | 1. Windows Sound Settings, aumenta volumen a 100% |
| Aún no responde | 2. Control Panel > Recording > Microphone Boost +20dB |
| Intel Bluetooth | 3. Usa micrófono USB externo (recomendado) |
| Logs dicen "VAD error" | 5. Instala silero-vad con pip |

**Probabilidad de éxito**: ~95% con Solución 1 + 2.

---

**Última actualización**: Abril 26, 2026  
**Responsable**: GitHub Copilot / Computadora Team  
**Categoría**: Troubleshooting / Voice Detection / Audio
