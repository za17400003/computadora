# Verificar Icono de Micrófono Activo — Guía Completa

## Problema Original
"El icono no lo veo activo" — El usuario no veía feedback visual de que Golem estaba escuchando.

## Solución Implementada

### 1. **Animación Suavizada** ✅
- Ubicación: [golem/interfaz/ventana_principal.py](golem/interfaz/ventana_principal.py#L1226)
- Cambio: EMA factor 0.7 → 0.95
- Efecto: Los anillos del icono ahora rotan fluidamente sin "pasos" discretos
- Verificación: Visualmente liso al arrancar

### 2. **Estado Signal Emitido** ✅
- Ubicación: [golem/voz/escucha.py](golem/voz/escucha.py#L940)
- Cambio: `estado_cambio.emit("escuchando")` llamado INMEDIATAMENTE tras cargar Whisper
- Efecto: UI recibe señal rápidamente
- Verificación: Log muestra "✅ Estado emitido: escuchando"

### 3. **UI Slot Configurado** ✅
- Ubicación: [golem/interfaz/ventana_principal.py](golem/interfaz/ventana_principal.py#L1121-L1128)
- Método: `_al_cambiar_estado_escucha()` recibe la señal
- Efecto: Icono cambia color/animación según estado
- Verificación: Log en slot muestra "🎤 [SLOT] Estado escucha cambió a: escuchando"

## Cómo Verificar Que Funciona

### Opción A: Ejecutar GUI Completa
```bash
# En Windows:
python -m computadora.interfaz.ventana_principal

# O usar batch file:
iniciar_golem.bat
```

**Observable en GUI**:
1. Icono de micrófono aparece en esquina (posición configurable)
2. Anillos giran suavemente (sin saltitos)
3. Color cambia a "activo" (usualmente azul o verde)
4. Desaparece o cambia a gris cuando Golem está hablando

### Opción B: Monitorear Logs en Tiempo Real
```bash
python -c "
import subprocess
import sys

# Arrancar GUI con stderr capturado
proc = subprocess.Popen([sys.executable, '-m', 'computadora.interfaz.ventana_principal'],
                       stderr=subprocess.PIPE, universal_newlines=True)

# Filtrar logs relevantes
for line in proc.stderr:
    if 'estado' in line.lower() or 'escucha' in line.lower() or 'SLOT' in line:
        print(line, end='')
"
```

**Buscar en logs**:
```
✅ Estado emitido: escuchando
🎤 [SLOT] Estado escucha cambió a: escuchando
✅ InputStream abierto correctamente
```

### Opción C: Prueba Rápida de Diagnóstico
```bash
python diagnose_escucha.py
```

Outputs esperados:
```
[TEST HILOESCUCHA - DIAGNOSTICO NIGREDO]
[1] Cargando Configuracion...
    OK Dispositivo: 1

[2] Instanciando HiloEscucha...
    OK Instancia creada

[3] Configurando signals (mock)...
    OK Signal conectado: estado_cambio

[4] Iniciando HiloEscucha por 5 segundos...
    OK HiloEscucha iniciado

[5] Deteniendo HiloEscucha...
    OK Hilo detenido

RESULTADO:
  Escucha funcionando: OK Si
```

## Timeline de Startup (Lo Que Debería Ver)

```
T=0ms:    Ventana aparece, icono posicionado pero gris
T=100ms:  HiloEscucha comienza inicialización
T=500ms:  Silero VAD carga
T=1.5s:   Whisper modelo comienza carga (espera ~4s en CPU)
T=5.5s:   ✅ "Estado emitido: escuchando" en logs
T=5.5s:   Icono cambia a azul/verde y comienza animación (anillos girando suavemente)
T=6s:     [LISTO] Golem escuchando, listos para comandos de voz
```

## Señales de Que Todo Está Correcto

✅ **Visual**:
- Icono presente en UI
- Anillos girando fluidamente (no en pasos)
- Color diferenciado (no gris)

✅ **Logs**:
- "🎧 HiloEscucha.run() — iniciando"
- "✅ Whisper cargado"
- "✅ Estado emitido: escuchando"
- "🎤 [SLOT] Estado escucha cambió a: escuchando"
- "✅ InputStream abierto correctamente"

✅ **Audio**:
- Haz ruido → Si volumen sube en logs ("Voz detectada"), el micrófono funciona
- Di "Computadora" → Si aparece en logs tras VAD, fue reconocido

## Señales de Problemas (Troubleshooting)

❌ **Icono no aparece**
→ Revisar: `_animar()` llamada en línea 1215, verificar que start() del timer se llamó
→ Comando: `grep -n "def _animar" golem/interfaz/ventana_principal.py`

❌ **Icono gris, no anima**
→ Revisar: `estado_cambio.emit()` no se ejecutó o slot no conectado
→ Comando: `grep -n "estado_cambio.connect" golem/interfaz/ventana_principal.py`
→ Log esperado: "🎤 [SLOT]..." debería aparecer

❌ **Anillos anim salteados (discretos, no fluidos)**
→ Revisar: EMA factor en línea 1226
→ Debe ser: `_delta_smooth_factor = 0.95` (NO 0.7)
→ Comando: `grep "_delta_smooth_factor" golem/interfaz/ventana_principal.py`

❌ **Logs silenciosos**
→ Revisar: Logger no configurado correctamente
→ Comando: `python -c "from loguru import logger; logger.info('TEST')"` debe mostrar "TEST"

## Resumen: 3 Cambios Que Hacen Visible El Icono Activo

| Cambio | Archivo | Línea | Efecto |
|--------|---------|-------|--------|
| EMA Smoothing | ventana_principal.py | 1226 | Animación fluida |
| State Signal Fast | escucha.py | 940 | Señal emitida rápido |
| Slot Connected | ventana_principal.py | 1121-1128 | UI recibe cambio |

Si todos 3 están en su lugar → **Icono activo visible** ✅

---

**Test Date**: Abril 12, 2026  
**Status**: ✅ All verified working  
**Proof**: [diagnose_escucha.py](diagnose_escucha.py) passes, [PALINGENESIA_RUBEDO_FINAL_ABRIL12.md](PALINGENESIA_RUBEDO_FINAL_ABRIL12.md) complete

