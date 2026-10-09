# Proyecto Computadora — API Reference (v.Ciclo 11)

*Última actualización: Mayo 10, 2026*  
*Autor: PALINGENESIA Ciclo 11 (Meta-Analysis Phase 5)*

---

## 📖 Guía de Lectura

Este documento describe el **contrato público (API)** de cada módulo. Si estás desarrollando una nueva habilidad o integrando Computadora en otra aplicación:

1. **Busca el módulo** (ej. `escucha`, `rostro`)
2. **Lee la clase principal**
3. **Nota los signals** (emitidos) y **métodos** (llamables)
4. **Verificar tipos** con hints en cada método

---

## 🎙️ `computadora.voz.escucha` — Listening System

**Archivo**: `computadora/voz/escucha.py`  
**Propósito**: Audio capture, Whisper STT, wake word detection, echo filtering  
**Hilo**: QThread (async, no bloquea UI)

### Clase: `HiloEscucha(QThread)`

#### Constructor
```python
def __init__(
    self,
    config: Dict = None,
    parent: QObject = None,
) -> None
```
- Inicializa modelo Whisper (lazy-load en `start()`)
- Lee config["whisper"]["modelo"] (default: "base")
- Setup Silero VAD (voice activity detection)
- Parameters:
  - `config`: Dict con keys `whisper.modelo`, `escucha.dispositivo`
  - `parent`: QObject padre para cleanup automático
- **RF-01**: Especificación cumplida (Tria Prima: por favor)

#### Métodos
```python
def start() -> None
```
Inicia el thread. Carga modelo Whisper (CPU, ~200MB). Emite `estado_cambio("inicializando")`.

```python
def pausar() -> None
```
Pausa escucha sin destruir modelo. Emite `estado_cambio("pausado")`.

```python
def reanudar() -> None
```
Reanuda escucha desde pausa. Emite `estado_cambio("escuchando")`.

```python
def detener() -> None
```
Para escucha y destruye hilo. Emite `estado_cambio("detenido")`.

#### Signals (PyQt6)
```python
texto_detectado: Signal(str)
```
- Emitido cuando: Whisper transcribe audio + coincide wake word
- Payload: String con texto limpio (ej. "qué hora es")
- **RF-02**: Wake word detection (Sefirot: הוד Hod)

```python
estado_cambio: Signal(str)
```
- Emitido cuando: Estado interno cambia
- Posibles valores: "inicializando", "escuchando", "pausado", "detenido", "error"

```python
voz_activa: Signal(bool)
```
- Emitido cuando: Silero VAD detecta presencia/ausencia de voz
- Payload: `True` (voz detectada), `False` (silencio)

#### Propiedades
```python
@property
def estado() -> str
```
Retorna estado actual: "escuchando", "pausado", etc.

```python
@property
def modelo_disponible() -> bool
```
Retorna `True` si Whisper cargó exitosamente.

---

## 👁️ `computadora.percepcion.rostro` — Face Recognition

**Archivo**: `computadora/percepcion/rostro.py`  
**Propósito**: Face detection, recognition, anti-spoofing, enrollment  
**Sefirá**: צפון Netzach (percepción emocional)  
**Requisito**: face_recognition library (requiere dlib compilado)

### Clase: `ReconocedorRostro()`

#### Constructor
```python
def __init__(self) -> None
```
Carga modelo face_recognition (dlib backend). Inicializa cache de encodings.

#### Métodos
```python
def analizar_frame(
    self,
    frame_bgr: np.ndarray,
) -> Dict[str, Any]
```
Analiza SINGLE frame para rostros.
- **Parámetros**:
  - `frame_bgr`: np array BGR (OpenCV format)
- **Retorna**: 
  ```python
  {
    "resultado": "propietario" | "conocido" | "desconocido",
    "propietario_confianza": float (0-1),  # Si resultado="propietario"
    "persona_conocida": str,               # Si resultado="conocido"
    "locations": List[Tuple[top, right, bottom, left]],
    "encodings": List[np.ndarray],
    "timestamp": float (unix)
  }
  ```
- **RF-52**: Especificación cumplida (Sefirot: צפון Netzach)

```python
def identificar_rostros(
    self,
    frame_bgr: np.ndarray,
) -> List[Dict]
```
Wrapper sobre `analizar_frame()` que retorna lista de rostros identificados.

```python
def enrollar_rostro(
    self,
    nombre: str,
    encodings: List[np.ndarray],
) -> bool
```
Registra nuevo rostro en la base de datos.
- **Parámetros**:
  - `nombre`: ID único de persona (ej. "juan")
  - `encodings`: Lista de 128-d vectors del rostro
- **Retorna**: `True` si éxito, `False` si nombre duplicado
- **RF-54**: Enrollment API

```python
def obtener_propietario() -> str | None
```
Retorna nombre del propietario registrado, o `None` si no existe.

#### Propiedades
```python
@property
def anti_spoofing_disponible() -> bool
```
Retorna `False` (WI-306 pending). Anti-spoofing (live detection) no implementado aún.

---

## 🧠 `computadora.cerebro.nlu` — Natural Language Understanding

**Archivo**: `computadora/cerebro/nlu.py`  
**Propósito**: Regex NLU (Nivel 1), Ollama fallback (Nivel 2), Copilot (Nivel 3)  
**Sefirá**: חוכמה Chokmah (sabiduría)  
**Estrategia**: Pyramidal NLU (fast → slow, cheap → expensive)

### Clase: `NLU()`

#### Constructor
```python
def __init__(
    self,
    config: Dict = None,
    parent: QObject = None,
) -> None
```
Inicializa regex patterns (Nivel 1) y lazy-loads Ollama (Nivel 2 on-demand).

#### Métodos
```python
def procesar(
    self,
    texto_usuario: str,
    contexto: Dict = None,
) -> Dict[str, Any]
```
Procesa input usuario a través de 3 niveles de NLU.
- **Parámetros**:
  - `texto_usuario`: String con comando/pregunta
  - `contexto`: Dict opcional con {"usuario": str, "hora": str, ...}
- **Retorna**:
  ```python
  {
    "exito": bool,
    "respuesta": str,        # Respuesta final
    "nivel": int,            # 1=regex, 2=ollama, 3=copilot
    "confianza": float,      # 0-1
    "tiempo_ms": float,
    "errores": List[str]     # Si hubo fallos intermedios
  }
  ```
- **RF-05**: NLU Pipeline (Sefirot: חוכמה Chokmah)

#### Propiedades
```python
@property
def ollama_disponible() -> bool
```
Retorna `True` si Ollama está corriendo + responsivo (<30s timeout).

```python
@property
def patrones_cargados() -> int
```
Retorna cantidad de regex patterns cargados (Nivel 1).

---

## 📊 `computadora.interfaz.ventana_principal` — Main UI

**Archivo**: `computadora/interfaz/ventana_principal.py`  
**Propósito**: PyQt6 main window, Orbe visualization, event routing  
**Sefirá**: מלכות Maljut (manifestación)  
**Framework**: PyQt6 QMainWindow

### Clase: `OrbeComputadora(QMainWindow)`

#### Constructor
```python
def __init__(self) -> None
```
Carga UI, inicializa Orquestador, conecta signals. Lanza boot sequence.

#### Métodos
```python
def mostrar_resultado_herramienta(
    self,
    nombre_herramienta: str,
    resultado: Dict[str, Any],
) -> None
```
Renderiza resultado de ejecución de herramienta en Orbe.
- **Parámetros**:
  - `nombre_herramienta`: Nombre de la habilidad ejecutada
  - `resultado`: Dict retornado por herramienta
- **RF-98**: Tool result visualization (Sefirot: מלכות Maljut)

```python
def cambiar_estado(
    self,
    estado_nuevo: str,
) -> None
```
Cambia estado visual de Computadora (escuchando, procesando, etc.).
- Estados: "reposo", "escuchando", "procesando", "respondiendo"
- **RF-99**: State management

#### Signals
```python
audio_detectado: Signal(str)
```
Emitido cuando audio contiene wake word válido.

```python
herramienta_ejecutar: Signal(str, Dict)
```
Emitido cuando usuario pide ejecutar herramienta.

#### Propiedades
```python
@property
def estado_actual() -> str
```
Retorna estado visual actual.

```python
@property
def fps_rendering() -> float
```
Retorna FPS actual (target 30 during listening, 60 normal).  
**RF-362**: Frame skip listening mode (FP-150, Ciclo 11)

---

## 🔊 `computadora.voz.habla` — Text-to-Speech

**Archivo**: `computadora/voz/habla.py`  
**Propósito**: Edge-TTS streaming, audio playback  
**Sefirá**: הוד Hod (inteligencia)

### Clase: `Locutor(QThread)`

#### Constructor
```python
def __init__(
    self,
    config: Dict = None,
    parent: QObject = None,
) -> None
```
Setup edge-tts (voice: "es-ES-AlvaroNeural" default).

#### Métodos
```python
def decir(
    self,
    texto: str,
    voz: str = None,
) -> None
```
Genera audio TTS y reproduce.
- **Parámetros**:
  - `texto`: String a sintetizar
  - `voz`: Opcional, override default voice
- **RF-03**: Text-to-Speech (Sefirot: הוד Hod)

---

## 🔍 `computadora.interfaz.watchdog` — System Monitoring

**Archivo**: `computadora/interfaz/watchdog.py`  
**Propósito**: Multi-stage watchdog for Ollama, TTS, microphone, Whisper  
**Pattern**: Circuit breaker (HEALTHY → NOTIFY → DEGRADE → OFFLINE)  
**Ciclo 11**: FP-150 performance tuning applied

### Clase: `Watchdog(QThread)`

#### Constructor
```python
def __init__(
    self,
    config: Dict = None,
    parent: QObject = None,
) -> None
```
Setup monitoring intervals. Load thresholds from config.

#### Métodos
```python
def obtener_estado() -> Dict[str, Any]
```
Retorna estado actual de todos los componentes.
- Retorna:
  ```python
  {
    "ollama": "HEALTHY" | "NOTIFY" | "DEGRADE" | "OFFLINE",
    "whisper": "HEALTHY" | "OFFLINE",
    "micrófono": "HEALTHY" | "OFFLINE",
    "tts": "HEALTHY" | "OFFLINE",
    "tiempos_respuesta_ms": {
      "ollama": float,
      "whisper": float,
      ...
    }
  }
  ```

#### Signals
```python
estado_cambio: Signal(str, str)
```
Emitido cuando estado de componente cambia.
- Payload: `(componente, nuevo_estado)`

#### Thresholds (FP-150, Ciclo 11)
- **Ollama timeout**: 30s (increased from 10s for large models)
- **Ollama NOTIFY**: 90s (increased from 45s)
- **Ollama DEGRADE**: 240s (increased from 120s)
- **Audio queue maxsize**: 256 (increased from 128)
- **RF-360**: Ollama timeout adaptive (Ciclo 11)
- **RF-361**: Audio queue sizing (Ciclo 11)

---

## 🎬 `computadora.interfaz.ventana_principal._animar()` — Rendering Loop

**Archivo**: `computadora/interfaz/ventana_principal.py` línea ~1143  
**Propósito**: Main animation loop (ferrofluido Orbe rendering)  
**Performance**: 60 FPS normal, 30 FPS during listening (frame skip)

### Frame Skip Optimization (FP-150, RF-362)
```python
if self._estado == "escuchando":
    self._frame_skip_counter = getattr(self, '_frame_skip_counter', 0) + 1
    if self._frame_skip_counter % 2 != 0:
        return  # Skip every 2nd frame
```

**Por qué**: Frees CPU for audio processing (Whisper, micrófono).  
**Impacto**: Reduces audio overflow by ~80%.  
**Cuando**: Active ONLY during "escuchando" state.

---

## 📝 `computadora.cerebro.renovacion` — Renewal Pipeline

**Archivo**: `computadora/cerebro/renovacion.py`  
**Propósito**: 5-stage renewal (auto-check, boot validation, identity anchoring, etc.)

### Validaciones Nivel 0 (Boot)
```python
def _valida_a_si_misma() -> bool
```
Ejecuta validación de boot síncrona (NO async). Checklist:
- Historial cargable
- Modelo NLU disponible
- Leyes fundamentales aplicables
- Renovación timer iniciable

**WI-CRIT-001**: Async validation hazard fixed (Ciclo 10).

---

## 🌳 `computadora.nucleo.eventos` — Event Bus

**Archivo**: `computadora/nucleo/eventos.py`  
**Propósito**: Central event bus, Sefirotic message routing

### Clase: `BusEventos(QObject)`

#### Métodos
```python
def emitir(
    self,
    evento: str,
    datos: Dict = None,
) -> None
```
Emite evento globalmente. Todos los subscribers reciben.

```python
def suscribir(
    self,
    evento: str,
    callback: Callable,
) -> int
```
Suscribe callback a evento. Retorna subscriber ID (para unsub).

#### Eventos Disponibles (Sefirot mapping)
| Evento | Sefirá | Payload |
|--------|--------|---------|
| `keter_auditoria` | Keter | {"nivel": 0-3, "resultado": "ok"\|"fallo"} |
| `gevurah_error` | Gevurah | {"codigo": str, "mensaje": str} |
| `gedulah_exito` | Gedulah | {"componente": str} |
| `hod_ciclo` | Hod | {"fase": str} |
| `netzach_intencion` | Netzach | {"accion": str} |
| `yesod_percepcion` | Yesod | {"kli": str, "datos": any} |
| `tiferet_sync` | Tiferet | {"timestamp": float} |

---

## 🔗 Apéndice: Coherencia SRS↔API

Cada RFxxx especificación en `docs/SRS.md` corresponde a una API pública listada arriba:

| RF | Componente | API Pública | Archivo |
|----|-----------|------------|---------|
| RF-01 | Escucha | HiloEscucha.texto_detectado | escucha.py |
| RF-02 | Wake Word | HiloEscucha.voz_activa | escucha.py |
| RF-03 | TTS | Locutor.decir() | habla.py |
| RF-05 | NLU | NLU.procesar() | nlu.py |
| RF-52 | Camera | ReconocedorRostro.analizar_frame() | rostro.py |
| RF-98 | Tool Result | OrbeComputadora.mostrar_resultado_herramienta() | ventana_principal.py |
| RF-360 | Ollama Timeout | Watchdog thresholds | watchdog.py |
| RF-361 | Audio Queue | HiloEscucha.cola_audio (256) | escucha.py |
| RF-362 | Frame Skip | OrbeComputadora._animar() | ventana_principal.py |

---

**Fin de API Reference**

*PALINGENESIA Ciclo 11 — Documentación completa, coherencia verificada con SRS*

