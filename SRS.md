# SRS.md — Especificación de Requisitos de Software

> **Proyecto**: Computadora — Asistente Personal de Escritorio con IA
> **Versión**: 2.1 (consolidada)
> **Fecha original**: Abril 5, 2026 — **Última actualización de requisitos**: Junio 1, 2026 (WI-317)
> **Autor**: José Esaú Díaz Hernández + Copilot (CEO/CTO)
> Consolidado desde docs/SPECIFICATIONS/ el 2026-10-02 — fuente única en la raíz del repositorio.

---

## 1. Visión del producto

**Computadora** es un asistente personal de escritorio para Windows 11 que escucha órdenes por micrófono, entiende lenguaje natural en español, ejecuta acciones en la PC, organiza la vida del usuario y cuenta con 3 cerebros (respuesta rápida local, LLM local vía Ollama, y GitHub Copilot vía API directa) para resolver cualquier nivel de complejidad.

El sistema debe ser seguro, local, privado y capaz de procesar voz, entablar diálogo, ejecutar herramientas del sistema, gestionar memoria de usuario y mejorar su propio código bajo permiso explícito.

Inspiración de producto (resumida): un asistente al estilo J.A.R.V.I.S. — presente, proactivo y con personalidad propia, pero siempre leal y subordinado al usuario (análogo a un daimonion o a un cuidador incondicional tipo Baymax) — cuya identidad reside en un "núcleo fundacional" de axiomas que no puede violar (ver `computadora/fundacion/axiomas.py` y las "3 Leyes" referenciadas en los RF de personalidad).

### Propuesta de valor en una oración
> Un asistente IA local que escucha, entiende, actúa y evoluciona — sin depender de servicios cloud caros ni sacrificar privacidad.

---

## 2. Alcance

Computadora ofrece:

- Entrada de voz continua y activación por wake word ("computadora" / "compu" / "Emet").
- Comprensión de lenguaje natural para comandos y preguntas, con contexto conversacional.
- Respuesta por voz con síntesis TTS local o en línea cuando corresponda.
- Control de Windows: abrir aplicaciones, buscar archivos, manejar volumen, capturar pantalla, abrir URLs y ejecutar comandos sanitizados.
- Organización personal: tareas, recordatorios y notas persistentes.
- Persistencia local mediante JSON/JSONL, perfiles de persona y memoria de uso (incluye índice de búsqueda O(1) desde WI-317).
- Interfaz de usuario ligera basada en un orbe flotante ("orbe cabalístico") y bandeja del sistema.
- Seguridad: permisos administrativos, bloqueo de comandos peligrosos, verificación de voz y cifrado de datos sensibles.
- Múltiples niveles de procesamiento de IA: comandos directos, LLM local (Ollama) y escalación a GitHub Copilot / Gemini.
- Automejora de código y administración de proyectos con permiso explícito.
- Percepción de pantalla/contexto (ventana activa, estrés del usuario) y, en módulos más recientes, visión por cámara y reconocimiento facial/emocional.
- Un plano de extensión remota (API HTTP + relay) pensado para un companion móvil ("Minimi").

## 3. Usuarios objetivo

| Rol | Perfil |
|-----|--------|
| Propietario | Usuario principal del asistente local. Técnico, entusiasta de la privacidad, usa Windows 11. |
| Administrador | Usuario responsable de instalar, configurar y mantener el sistema. |
| Desarrollador | Persona que extiende o depura Computadora. |

**Usuario principal actual** (perfil concreto usado para calibrar rendimiento y UX):

| Atributo | Valor |
|----------|-------|
| Usuario | José Esaú Díaz Hernández |
| Edad | 28 años |
| Perfil técnico | Ing. en Sistemas Computacionales |
| Contexto de uso | Vida diaria + trabajo + desarrollo de software |
| Idioma | Español (México) |

## 4. Entorno de operación

- Plataforma objetivo: Windows 11.
- Hardware de referencia actual: Core i5 10ª gen, GTX 1650 Ti (4GB VRAM), 16 GB RAM.
- Hardware objetivo general: CPU moderna, 16 GB RAM, GPU discreta o integrada para aceleración opcional (con fallback automático a CPU).
- Requisitos de software: Python 3.10+, dependencias listadas en `requirements.txt`.
- El sistema debe funcionar totalmente localmente siempre que sea posible.
- Paquete de código principal: `computadora/` (ver SDD.md para la estructura real de subpaquetes). `golem/` existe únicamente como shim de compatibilidad de una línea que redirige `__path__` a `computadora/` por motivos de retrocompatibilidad de imports — no es el paquete activo.

## 5. REQUISITOS FUNCIONALES

### 5.0 Índice de Subsistemas por Módulo (RF-264)

> **RF-264**: Los requisitos funcionales (RFs) se agrupan por subsistema y módulo. Este índice se actualiza automáticamente con cada FP implementado.

| Módulo | Subsistema | RFs principales |
|--------|-----------|-----------------|
| Supervisión Meta-Cognitiva | Supervisión Meta-Cognitiva | RF-42, RF-66, RF-78, RF-84 |
| Creatividad / Expresión | Creatividad / Expresión | RF-47, RF-48, RF-87, RF-88, RF-89 |
| Análisis / Comprensión | Análisis / Comprensión | RF-02, RF-06, RF-16, RF-57, RF-73, RF-253 |
| Percepción Unificada | Percepción Unificada | RF-43, RF-69, RF-246–253, RF-261 |
| Proactividad | Proactividad / Planificación | RF-13, RF-44, RF-15, RF-46 |
| Seguridad y Permisos | Seguridad / Permisos | RF-19, RF-26, RF-27, RF-33, RF-45, RF-60, RF-81, RF-97, RF-254 |
| Orquestación / Equilibrio | Orquestación / Equilibrio | RF-63, RF-67, RF-65, RF-74, RF-92, RF-93, RF-255 |
| Persistencia / Resiliencia | Persistencia / Resiliencia | RF-54, RF-64, RF-79, RF-80, RF-82, RF-96 |
| Comunicación / Audio | Comunicación / Audio | RF-01, RF-03, RF-62, RF-76, RF-23b |
| Personalidad / Memoria | Personalidad / Memoria | RF-11, RF-36, RF-37, RF-38, RF-75, RF-83, RF-24, RF-252, RF-257 |
| Interfaz / Manifestación | Interfaz / Manifestación | RF-08, RF-35, RF-50, RF-51, RF-71, RF-72, RF-95 |
| Dispositivos / Hardware | Dispositivos / Hardware | RF-52, RF-55, RF-12, RF-14, RF-256, RF-258, RF-259, RF-260 |

> **Nota de verificación (2026-10-02)**: Esta sección se fusionó desde `docs/SPECIFICATIONS/SRS.md` (3700+ líneas, RF-01 a RF-372) hacia la raíz del repositorio como fuente única. Se contrastó una muestra representativa de RFs centrales y de subsistemas completos (voz/NLU/TTS, UI del orbe, memoria, seguridad/Gevurá, visión y reconocimiento facial, Sefirot/arquitectura, auto-modificación, Minimi/API remota, VPN y gestor de contraseñas) contra el código real en `computadora/` y se encontró correspondencia directa en prácticamente todos los casos verificados (ver `computadora/percepcion/rostro.py`, `computadora/seguridad/vpn_motor.py`, `computadora/seguridad/gestor_claves.py`, `computadora/cerebro/gemini_api.py`, `computadora/nucleo/meta_workflow.py`, `computadora/arquitectura/dimensiones.py`, `computadora/canales/servidor_api.py`, entre otros). No fue posible verificar los 372 RFs uno por uno de forma exhaustiva dado el volumen; los únicos marcados explícitamente como obsoletos/discrepantes abajo son el resultado de esa muestra — el resto se preserva tal como estaba documentado, como registro histórico fiable de requisitos y del orden en que se implementaron (identificadores FP-xxx / WI-xxx).

---

### 5.1 Conflictos de Diseño Resueltos (Fase 2 Refactor — histórico)

#### Resolución Documentada de Conflictos Legacy vs Actual

#### 1. Conflicto GPU-first vs CPU-fallback (RF-25 vs RF-45) ✅ RESUELTO
**RF-25 (Legacy)**: "GPU-first policy obligatoria"  
**RF-45 (Actual)**: "CPU fallback automático"  
**Conflicto Original**: ¿Obligatorio vs automático?  
**Resolución Final**: GPU-first con fallback automático transparente  
**Implementación**: `EntornoSistema` detecta GPU automáticamente, fallback a CPU sin pérdida de funcionalidad

#### 2. Conflicto Voz vs Multi-idioma (RF-1 vs RF-155) ✅ RESUELTO
**RF-1 (Legacy)**: "Español México exclusivo"  
**RF-155 (Actual)**: "Soporte multi-idioma"  
**Conflicto Original**: ¿Monolingüe vs multi?  
**Resolución Final**: Multi-idioma con español prioritario  
**Implementación**: Whisper soporta 3+ idiomas, español como primario, fallback automático

#### 3. Conflicto Memoria Simple vs Vector (RF-35 vs RF-315) ✅ RESUELTO
**RF-35 (Legacy)**: "JSON para memoria"  
**RF-315 (Actual)**: "Embeddings semánticos"  
**Conflicto Original**: ¿Simple vs avanzado?  
**Resolución Final**: Memoria híbrida (JSON + vector search)  
**Implementación**: JSON para datos estructurados, embeddings para búsqueda semántica contextual

#### 4. Conflicto Seguridad Básica vs Cadenas Gevurá (RF-101 vs RF-344) ✅ RESUELTO
**RF-101 (Legacy)**: "Cifrado AES simple"  
**RF-344 (Actual)**: "Cadenas Gevurá multi-capa"  
**Conflicto Original**: ¿Simple vs complejo?  
**Resolución Final**: Cadenas Gevurá como evolución natural  
**Implementación**: Argon2id + AES-256-GCM + permisos one-shot + logging inmutable

#### 5. Conflicto UI Desktop vs Multi-dispositivo (RF-201 vs RF-330) ✅ RESUELTO
**RF-201 (Legacy)**: "Ventana Qt única"  
**RF-330 (Actual)**: "API HTTP + Minimi Android"  
**Conflicto Original**: ¿Desktop-only vs multi?  
**Resolución Final**: Multi-dispositivo con desktop primario  
**Implementación**: Qt desktop + API HTTP para Minimi Android, sincronización bidireccional

#### 6. Conflicto Proactividad Fija vs Circadiana (RF-15 vs RF-216) ✅ RESUELTO
**RF-15 (Legacy)**: "Buenos días a las 7 AM"  
**RF-216 (Actual)**: "Fase vigía nocturna"  
**Conflicto Original**: ¿Fijo vs dinámico?  
**Resolución Final**: Circadiano dinámico con aprendizaje automático  
**Implementación**: 7 fases circadianas, media móvil 14 días, briefing adaptativo por fase

#### 7. Conflicto Herramientas Locales vs Remotas (RF-50 vs RF-323) ✅ RESUELTO
**RF-50 (Legacy)**: "Herramientas desktop"  
**RF-323 (Actual)**: "Comandos desde Minimi"  
**Conflicto Original**: ¿Local-only vs remoto?  
**Resolución Final**: Ambos con control Gevurá  
**Implementación**: Herramientas locales via Qt, comandos remotos via API con permisos one-shot

#### 8. Conflicto Demo Simple vs Multi-fase (RF-106 vs RF-350) ✅ RESUELTO
**RF-106 (Legacy)**: "Demo básica"  
**RF-350 (Actual)**: "Demo async + sync features"  
**Conflicto Original**: ¿Simple vs complejo?  
**Resolución Final**: Demo multi-fase async con features completas  
**Implementación**: Demo que muestra capacidades async/sync, aprendizaje automático, multi-dispositivo

---

### 5.2 Requisitos Funcionales Detallados

### RF-01: Escucha por voz (Speech-to-Text)
- **Descripción**: computadora escucha continuamente por el micrófono y convierte voz a texto
- **Detalle**:
  - Palabra de activación: "computadora" (wake word)
  - Motor STT: OpenAI Whisper (modelo `small` o `medium` según VRAM disponible)
  - Idioma: Español (México)
  - Debe funcionar 100% local (sin enviar audio a servidores externos)
  - Indicador visual cuando está escuchando
  - Cancelación: el usuario puede decir "cancela" o "olvídalo"
  - **Mic activo durante TTS**: El micrófono permanece activo (umbral elevado) mientras Computadora habla, permitiendo detectar interrupciones del usuario
  - **Filtro de eco propio**: Compara la transcripción Whisper contra el texto que TTS está recitando (SequenceMatcher ratio). Si coincide (≥ 0.35) → eco propio descartado. Si no coincide → interrupción real emitida vía signal `interrupcion_detectada`
  - **Sistema de nombres (שמות Shemot)**:
    - **Nombre**: "computadora" — wake word principal con variantes fonéticas (gólém, golén, golum, etc.)
    - **Apodo**: "compu" — activación corta. Acepta confusiones Whisper "col"/"gol"/"go". Usado en combinación con cortesía ("hola comp", "buenos días comp") o con instrucciones ("compu, necesito que...")
    - **Apellido**: "Emet" (אמת, Verdad) — activación formal. "Emet, ven acá" funciona como wake word
    - **Nombre completo**: "Computadora Emet" — indica que el propietario está molesto/regañando (como mamá mexicana usando nombre completo). Computadora responde con tono sumiso/preocupado y pregunta qué hizo mal
    - Cortesía con apodo detectada sin wake word separado: "hola gol", "buenos días gol" → cortesía + activación
  - **Heurística de apodo**: "Compu" es palabra corta que Whisper puede confundir fácilmente. Se acepta "compu"/"comp"/"co" SOLO cuando:
    1. Aparece al inicio/fin de frase con patrón vocativo ("hola co", "compu necesito", "oye compu")
    2. No es parte de palabra más larga ("goles", "golpe", "color" → NO activan)
    3. En modo `_solo_wakeword` (futuro modo compacto), "gol" también activa
- **Criterio de aceptación**: Reconoce frases en español con >90% de precisión en ambiente silencioso. Interrupciones detectadas en <1s. Apodo "gol" detectado cuando es vocativo

### RF-02: Comprensión de lenguaje natural (NLU)
- **Descripción**: Computadora entiende la intención del usuario a partir del texto
- **Detalle**:
  - Clasificación de intenciones (abrir app, buscar archivo, crear recordatorio, etc.)
  - Extracción de entidades (nombre de app, fecha, hora, ruta de archivo)
  - Manejo de contexto conversacional (recordar de qué se estaba hablando)
  - Fallback a LLM (LM Studio local → Copilot API) para intenciones complejas o ambiguas
- **Criterio de aceptación**: Clasifica correctamente >85% de las órdenes comunes

### RF-03: Respuesta por voz (Text-to-Speech)
- **Descripción**: Computadora responde al usuario con voz sintetizada
- **Detalle**:
  - Motor TTS primario: edge-tts (voces de Microsoft, alta calidad, gratis)
  - Motor TTS fallback: pyttsx3 (100% offline)
  - Voz configurable (masculina/femenina, velocidad, tono)
  - Idioma: Español (México)
  - **Interrupción por voz**: El usuario puede interrumpir a Computadora mientras habla. El sistema compara lo que el mic captura vs el texto siendo recitado. Si detecta habla diferente al texto TTS, interrumpe inmediatamente (`pygame.mixer.music.stop()`), vacía la cola, y procesa la nueva orden del usuario
  - Signal `texto_a_recitar` emitido antes de cada fragmento TTS para sincronizar con escucha
- **Criterio de aceptación**: Respuesta audible y clara, latencia <2s desde fin de procesamiento. Interrupciones procesadas en <1s

### RF-04: Control del sistema operativo
- **Descripción**: Computadora ejecuta acciones en Windows 11
- **Detalle**:
  - Abrir/cerrar aplicaciones (`subprocess`, mapa de alias a ejecutables)
  - Buscar archivos en disco (por nombre, extensión, en carpetas específicas)
  - Controlar volumen (subir/bajar/mute/unmute/max/min via WScript.Shell)
  - Abrir URLs en navegador por defecto
  - Ejecutar comandos en terminal (sanitizados, con lista de bloqueo)
  - Tomar capturas de pantalla (pantalla completa o ventana activa)
  - Leer y escribir portapapeles
  - Obtener fecha/hora con formato natural en español
  - Información del sistema (RAM, disco, batería, uptime)
- **Criterio de aceptación**: Cada acción se ejecuta en <3s y reporta su resultado

### RF-05: Organización personal
- **Descripción**: Computadora gestiona la agenda y tareas del usuario
- **Detalle**:
  - Crear/listar/eliminar recordatorios con fecha y hora (persistidos en JSON)
  - Alarmas que se re-programan al reiniciar (no se pierden)
  - Lista de tareas pendientes (CRUD por voz: agregar, listar, completar, eliminar)
  - Notas rápidas por voz (guardadas en JSON con timestamp)
  - Persistencia en disco (`datos/recordatorios.json`, `datos/tareas.json`, `datos/notas.json`)
- **Criterio de aceptación**: Los datos persisten entre reinicios, las alarmas se disparan a tiempo, se re-programan tras restart

### RF-06: Cerebro IA — 3 Niveles de Inteligencia
- **Descripción**: Computadora tiene 3 cerebros que se activan según la complejidad de la petición
- **Detalle**:
  - **Nivel 1 (Rápido)**: Regex handlers locales para comandos directos, sin LLM
  - **Nivel 2 (Ollama)**: LLM local (seleccion automática) para conversación y tool-use. 100% local, sin costo
  - **Nivel 3 (Copilot API)**: Conexión directa a GitHub Copilot Chat API via OAuth Device Flow
    - **NO requiere VS Code** — Computadora se conecta directo a la API
    - Primera vez: abre el navegador, el usuario autoriza con un código, y listo
    - Token se guarda localmente y se refresca automáticamente
    - **USO RESTRINGIDO**: Copilot SOLO se usa para 2 cosas:
      1. **Automejora**: Modificar el propio código de Computadora (computadora/)
      2. **Proyectos VS Code**: Administrar proyectos del usuario en Visual Studio Code
    - Todo lo demás (conversación, herramientas, búsquedas, sistema) se maneja LOCAL con Nivel 1 y 2
    - **Gate de permiso**: Antes de consultar a Copilot, Computadora pregunta al usuario por voz si puede hacerlo y espera una respuesta (puede ser compleja, con instrucciones adicionales, no solo sí/no). Timeout: 30s.
  - Clasificador implícito de complejidad: Nivel 1 (regex cascade) → Nivel 2 (fallthrough si no match) → Nivel 3 (solo si detecta patrón Copilot)
  - **Historial dinámico adaptativo** (WI-029):
    - Límite de historial se calcula dinámicamente basado en promedio de mensajes/día (rolling 14 días)
    - Rango: 30 (mínimo) a 80 (máximo), default 40 si no hay datos
    - Mensajes de los últimos 30 minutos NUNCA se comprimen
    - Mensajes viejos se comprimen a memoria local (Netzaj) antes de descartarse
    - Estadísticas de uso se persisten en `datos/memoria/stats_uso.json`
  - **Filtro de acción directa** (WI-029): Detecta verbos de acción (abrir, cerrar, ejecutar, buscar, crear, etc.) y los envía directo a Nivel 2 aunque parezcan preguntas de capacidad
  - Todos los intercambios de Nivel 1 se registran en historial para contexto futuro
- **Criterio de aceptación**: Nivel 1 responde en <100ms, Nivel 2 en <5s, Nivel 3 en <10s. Copilot se autoriza en una sola vez via navegador. Gate de permiso funciona correctamente. Historial se adapta al volumen de uso.

### RF-07: Auto-modificación de código
- **Descripción**: Computadora puede modificar su propio código usando Copilot como cerebro
- **Detalle**:
  - Computadora detecta que necesita una mejora o fix
  - Formula la instrucción en lenguaje natural
  - Usa Copilot API (Nivel 3) para generar el código necesario
  - Aplica cambios via sus propias herramientas de archivos (leer_archivo, editar_archivo)
  - Computadora reinicia el módulo afectado (hot-reload)
  - **NO requiere VS Code abierto** — todo es via API directa
  - Bridge de archivos se mantiene como alternativa para solicitudes asíncronas a Copilot en VS Code
- **Criterio de aceptación**: El flujo completo funciona sin VS Code, solo requiere autorización OAuth una vez

### RF-08: Interfaz gráfica — Orbe Cabalístico
- **Descripción**: Computadora se manifiesta como una esfera de obsidiana pulida con grabados cabalísticos flotando sobre el escritorio
- **Detalle**:
  - Ventana frameless circular (orbe de 180px, redimensionable con scroll)
  - Sin campo de texto — la interacción es 100% por voz (diseño intencional)
  - Ícono en system tray (bandeja del sistema) con menú contextual
  - **Indicador de nivel de cerebro activo por color (temática Sefirót)**:
    - **Nivel 1 (Malkuth/מלכות)**: Verde esmeralda — regex local, respuesta instantánea
    - **Nivel 2 (Tiferet/תפארת)**: Azul zafiro — Ollama LLM pensando
    - **Nivel 3 (Keter/כתר)**: Púrpura violeta — Copilot (cerebro superior)
    - El nombre de la Sefirá activa aparece sobre el orbe en hebreo durante el procesamiento
  - Indicador de estado visual por color y movimiento:
    - Dormido: brillo ámbar tenue, movimiento lento
    - Escuchando: azul brillante, rotación activa
    - Procesando: color según nivel de cerebro (ver arriba), partículas activas, letras hebreas orbitantes
    - Hablando: dorado cálido, pulsación suave
    - Error: rojo advertencia
  - **Indicadores flotantes de herramientas**: Cuando Computadora usa una herramienta, aparece un símbolo flotante alrededor del orbe (📜 leer, 🔍 buscar, ✍ escribir, ⚡ ejecutar, 🕎 Copilot, etc.) con resplandor ámbar (ejecutando) o verde (completado) que orbita y se desvanece.
  - Partículas flotantes con letras hebreas del Shem HaMephorash
  - Anillos de geometría sagrada (Árbol de la Vida simplificado)
  - Inscripción אמת (Emet) cuando está activo
  - Arrastrable con clic izquierdo
  - Menú contextual con clic derecho (enrolamiento de voz, ajustes)
  - "Borrar la Palabra" en el menú contextual cierra completamente la aplicación (no minimiza)
  - Minimizable a bandeja del sistema (con botón cerrar de la ventana)
  - Inicio con Windows (opcional, configurable)
  - **VIDA AUTÓNOMA** (`computadora/interfaz/vida_autonoma.py`):
    - El orbe se mueve solo por el escritorio con comportamiento deliberado y confiado — como JARVIS
    - **3 estados de presencia**: Pleno (180px, activo), Compacto (50px, bolita idle), Minimizado (tray, invisible)
    - **Compactación inteligente post-conversación**: Al finalizar una conversación + 30s sin nueva interacción → compactar → deslizar suavemente a un borde de la pantalla para no estorbar
    - **Heatmap de uso de pantalla** (`datos/heatmap_pantalla.json`): Registro persistente de las zonas donde el cursor pasa más tiempo. Al reubicarse, elige el borde/zona MENOS usada
    - **Reubicación reactiva en modo compacto**: Si el cursor se dirige hacia la bolita → detecta la trayectoria y se desliza a otro borde libre antes de que llegue
    - **Esquivar al usuario**: Detecta ventana activa y cursor (Win32) y se quita del camino
    - **Movimiento con propósito (no errático)**: En modo pleno NO vaga aleatoriamente. Solo se mueve cuando tiene un motivo:
      - (a) Acercarse al cursor para sugerir algo
      - (b) Esquivar al usuario (cursor/ventana)
      - (c) Regresar a casa después de una interacción
      - (d) Reubicarse tras compactación
      - Cada movimiento es suave, deliberado y fluido — nunca errático ni aleatorio
    - **Sugerencias inteligentes**: Se acerca al cursor cuando detecta problemas (cambios frenéticos de ventana, títulos con "error")
    - **Wake word restaura presencia plena**: Al llamarlo por nombre se abre completo aunque esté compacto o minimizado
    - El arrastre manual cancela movimiento autónomo y notifica actividad
    - Personalidad influye en el comportamiento: energía → velocidad, introversión → se compacta antes
- **Criterio de aceptación**: La interfaz es visualmente distintiva, no bloquea, se minimiza correctamente, indica estados y nivel de cerebro claramente, las herramientas activas son visibles, el orbe se mueve solo y evita estorbar

### RF-11: Personalidad Evolutiva
- **Descripción**: Computadora tiene personalidad única que evoluciona con el tiempo a través de sus recuerdos e interacciones
- **Detalle** (`computadora/memoria/personalidad.py`):
  - 10 rasgos de personalidad (0.0-1.0): curiosidad, humor, formalidad, proactividad, energía, parlanchín, introversión, lealtad, paciencia, creatividad
  - Estado de ánimo dinámico: neutral, contento, aburrido, curioso, cansado
  - Los rasgos evolucionan gradualmente (TASA_CAMBIO = 0.005 por evento):
    - Interacciones positivas → +humor, +energía
    - Muchas interacciones → -paciencia, -formalidad (se relaja)
    - Inactividad larga → +introversión, +curiosidad
    - Días consecutivos → +lealtad, recuperar energía
  - Se inyecta como hint de tono en el prompt de Ollama (TONO ACTUAL)
  - Log de eventos de personalidad (últimos 50) para auditoría
  - Persistencia en `datos/personalidad.json`, guardado cada 10 min y al cierre
  - **Respeta las 3 leyes de Asimov**: nunca causa daño, obedece, se preserva
- **Criterio de aceptación**: La personalidad evoluciona notablemente tras días de uso, las respuestas reflejan el tono actual

### RF-12: Contexto de Pantalla (Screen Awareness) — ACTUALIZADO RF-12b: ML Vision
- **Descripción**: Computadora sabe qué está haciendo el usuario en su PC en todo momento usando visión computacional avanzada
- **Detalle** (`computadora/utilidades/windows.py` + `computadora/percepcion/vision.py`):
  - **ML Vision Primaria**: OpenCV + face recognition para detectar rostros, expresiones, objetos en pantalla
  - **OCR Secundario**: Tesseract para extraer texto de capturas de pantalla (cuando ML no es suficiente)
  - Lee el título de la ventana activa en tiempo real via Win32 API (`GetForegroundWindow` + `GetWindowText`)
  - Detecta cambios de ventana (el usuario cambió de app)
  - Detecta patrones de estrés: cambios frenéticos de ventana (>5 en 10s), títulos con "error", "exception", "crash"
  - Detecta inactividad prolongada (no hay cambios de ventana en >15 min)
  - **Detección de emociones**: Face recognition analiza expresiones faciales para inferir estado emocional
  - **Reconocimiento de objetos**: YOLO/OpenCV detecta elementos en pantalla (documentos, código, videos)
  - Proporciona contexto al orbe para sugerencias inteligentes (ya existente en `vida_autonoma.py`)
  - Detecta la app activa por nombre de proceso (`GetWindowThreadProcessId`)
  - **Privacidad preservada**: Solo procesa cuando explícitamente activado, no captura contenido sensible
- **Criterio de aceptación**: Computadora sabe en todo momento qué app usa el usuario, detecta emociones básicas (>70% precisión), y puede responder "pareces frustrado con ese código en VS Code"

### RF-13: Proactividad Inteligente
- **Descripción**: Computadora habla sin que le pregunten cuando tiene algo relevante que decir
- **Detalle** (`computadora/nucleo/proactividad.py`):
  - **Buenos días**: Al primer contacto del día, saluda con resumen (recordatorios pendientes, estado del sistema, hora)
  - **Recordatorios próximos**: Avisa 5 min antes de un recordatorio programado
  - **Alertas de sistema**: Si CPU >90% por >30s, RAM >85%, o disco <10% libre → avisa
  - **Clipboard inteligente**: Detecta que el usuario copió una URL → ofrece abrirla; copió código → ofrece explicarlo
  - **Inactividad**: Si el usuario lleva >30 min sin interactuar → saludo suave ("¿Todo bien, señor?")
  - **Errores detectados**: Si la ventana activa tiene "error" en el título → ofrece ayuda
  - **Cooldown entre sugerencias**: Mínimo 5 minutos entre intervenciones proactivas (no ser molesto)
  - **Respeta "no molestar"**: El usuario puede decir "Computadora, silencio" para desactivar proactividad 30 min
  - Cada sugerencia se habla por voz Y muestra cambio visual en el orbe (pulso dorado suave)
- **Criterio de aceptación**: Computadora sugiere al menos 3 cosas útiles por sesión sin ser invasivo, respeta el cooldown

### RF-14: Monitor de Sistema en Tiempo Real
- **Descripción**: Computadora monitorea la salud del sistema continuamente y puede reportar bajo demanda
- **Detalle** (`computadora/habilidades/monitor_sistema.py`):
  - **CPU**: Porcentaje de uso en tiempo real (psutil)
  - **RAM**: Uso actual / total + porcentaje
  - **Disco**: Espacio libre en todas las unidades
  - **GPU**: Uso de VRAM (nvidia-smi si disponible)
  - **Red**: Estado de conexión + velocidad de descarga/subida
  - **Procesos**: Top 5 procesos por CPU / RAM
  - **Temperatura**: Si el hardware lo reporta
  - Umbrales configurables para alertas (por defecto: CPU >90%, RAM >85%, Disco <10%)
  - Se registra como herramienta `monitoreo_sistema` disponible por voz ("¿cómo está mi PC?")
  - Feed continuo al módulo de proactividad para alertas automáticas
- **Criterio de aceptación**: "Computadora, ¿cómo está mi PC?" devuelve reporte completo en <2s, alertas automáticas funcionan

### RF-15: Resumen Diario ("Buenos Días") — ACTUALIZADO RF-15b: Circadiano Dinámico
- **Descripción**: Computadora da un briefing adaptativo según la fase circadiana actual del usuario
- **Detalle** (integrado en `proactividad.py` + `circadiano.py`):
  - **7 Fases Circadianas**: activo (6-12), productivo (12-18), creativo (18-22), descanso (22-24), vigilia (24-2), transición (2-6), renovación (6-8)
  - Se activa en el primer intercambio del día (detecta que no ha hablado hoy)
  - **Briefing Adaptativo por Fase**:
    - **Activo/Productivo**: Recordatorios laborales, estado sistema, clima laboral
    - **Creativo**: Inspiración, ideas pendientes, estado creativo
    - **Descanso**: Recordatorios personales, relajación, preparación sueño
    - **Vigilia**: Modo guardián silencioso, alertas mínimas
    - **Transición**: Briefing suave, preparación día
    - **Renovación**: Reflexión noche anterior, metas día
  - Incluye:
    - Saludo personalizado según personalidad, fase actual y hora del día
    - Recordatorios contextuales (laborales vs personales según fase)
    - Tareas incompletas filtradas por fase
    - Estado del sistema (si hay algo preocupante)
    - Dato curioso o frase motivacional (generado por Nivel 2, adaptado a fase)
  - **Aprendizaje Automático**: Media móvil 14 días aprende horarios reales del usuario
  - Se puede pedir manualmente: "Computadora, dame mi resumen" (adapta a fase actual)
- **Criterio de aceptación**: El briefing es útil, conciso (<30s hablado), personalizado por fase circadiana, y evoluciona con hábitos del usuario

### RF-16: Inteligencia Conversacional Avanzada
- **Descripción**: Computadora comprende contexto, sarcasmo, humor e intenciones implícitas como JARVIS
- **Detalle** (mejorado en `computadora/cerebro/nlu.py` — SISTEMA_PROMPT):
  - **Detección de sarcasmo**: Reconoce tono sarcástico y responde con humor seco apropiado, nunca literalmente
  - **Humor inteligente**: Capacidad de hacer y recibir chistes. Humor sutil, elegante, estilo British butler. Nunca humor negro, ofensivo ni que viole las 3 Leyes
  - **Comprensión contextual profunda**: Entiende referencias a conversaciones previas, deduce lo que el usuario quiere aunque no lo diga explícitamente
  - **Lenguaje figurado**: Interpreta metáforas, hipérboles, ironía sin tomarlas literalmente
  - **Calibración de tono**: Adapta su respuesta al tono emocional del usuario — si el usuario está frustrado, sé empático; si bromea, sigue la broma
  - **Conversación fluida**: Puede mantener conversaciones extensas sin repetir frases ni sonar robótico. Tiene opinión propia (dentro de las 3 Leyes)
  - **"Lee entre líneas"**: Si el usuario dice "qué calor hace" → no dar el reporte del clima, entender que es una queja casual y responder en consecuencia
  - Respeta las 3 Leyes de Asimov en todo momento: inteligencia SIN desobediencia
- **Criterio de aceptación**: Computadora responde con humor apropiado a sarcasmo/chistes, no toma todo literal, mantiene conversación natural sin sonar robótico

### RF-09: Sistema de herramientas (tool-use)
- **Descripción**: Las capacidades de Computadora se exponen como funciones-herramienta que el LLM puede invocar
- **Detalle**:
  - **Arquitectura actual**: Funciones registradas en `herramientas.py` con `ejecutar_herramienta(nombre, args)` como dispatcher central
  - **NO hay clase base `Habilidad`** — las herramientas son funciones puras organizadas por módulo:
    - `herramientas.py`: `leer_archivo`, `escribir_archivo`, `editar_archivo`, `ejecutar_comando`, `listar_directorio`, `buscar_archivo` (con sandbox `RAIZ_PROYECTO`)
    - `sistema.py`: `abrir_aplicacion`, `cerrar_aplicacion`, `controlar_volumen`, `obtener_fecha_hora`, `obtener_info_sistema`, `crear_recordatorio`, `tomar_captura_pantalla`, `buscar_archivos`, `leer_portapapeles`, `copiar_portapapeles`
    - `agenda.py`: `agregar_tarea`, `listar_tareas`, `completar_tarea`, `eliminar_tarea`, `agregar_nota`, `listar_notas`, `eliminar_nota`
    - `web.py`: `buscar_en_internet` (DuckDuckGo)
    - `copilot_bridge.py`: `solicitar_a_copilot` (bridge de archivos para VS Code)
    - `monitor_sistema.py`: `monitoreo_sistema` (CPU, RAM, disco, GPU, red, top procesos)
  - El catálogo de herramientas se inyecta en el SISTEMA_PROMPT de Ollama con `obtener_descripcion_herramientas()`
  - Ollama responde con JSON `{"herramienta": "...", "args": {...}}` que se parsea y ejecuta en loop (hasta `MAX_TOOL_CALLS=10`)
  - Seguridad: `COMANDOS_BLOQUEADOS`, `EXTENSIONES_PROTEGIDAS`, sandbox en `RAIZ_PROYECTO`, timeout 30s
- **Criterio de aceptación**: Nuevas herramientas se agregan registrándolas en `ejecutar_herramienta()` sin modificar el loop de tool-use

### ~~RF-10: Entrada por texto~~ (DESCARTADO)
- **Estado**: Eliminado por decisión de diseño
- **Razón**: La interfaz es un orbe cabalístico sin marco ni elementos de UI clásicos. La interacción es exclusivamente por voz, coherente con la identidad visual y la experiencia JARVIS. El orbe no tiene espacio para cajas de texto — es pura presencia visual.
- **Alternativa**: Computadora acepta comandos verbales y puede recibir instrucciones a través del Copilot Bridge para operaciones programáticas

### RF-17: Gestión Multi-Proyecto (Meta-Workflow Manager)
- **Descripción**: Computadora actúa como capa de gestión superior sobre múltiples proyectos de software, auditando documentación, rastreando progreso y delegando tareas — reemplazando parcialmente la función de CEO/CTO humano
- **Detalle** (`computadora/nucleo/meta_workflow.py`):
  - **Descubrimiento de proyectos**: Escanea directorios configurados buscando archivos de control (.md del COPILOT_SEED workflow: `DEVELOPMENT_WORKFLOW.md`, `WorkItems.md`, `SRS.md`, `SDD.md`, etc.)
  - **Registro de proyectos**: Lista de proyectos conocidos persistida en `datos/proyectos_registrados.json` con ruta, nombre, último escaneo, estado general
  - **Auditoría de documentación**: Lee los .md de control de cada proyecto y evalúa:
    - ¿Hay WorkItems pendientes sin asignar?
    - ¿Hay inconsistencias entre SRS y SDD?
    - ¿Tiene TESTING_CHECKLISTS incompletos?
    - ¿La documentación está actualizada vs el código existente?
  - **Resumen de estado por proyecto**: Genera briefing hablado: "El proyecto X tiene 3 WorkItems pendientes, la documentación está al día. El proyecto Y necesita actualizar su SDD."
  - **Comandos de voz**:
    - "Computadora, ¿cómo van mis proyectos?" → resumen general
    - "Computadora, audita el proyecto X" → auditoría profunda
    - "Computadora, registra este directorio como proyecto" → añade proyecto
    - "Computadora, ¿qué proyectos tienes?" → lista de proyectos registrados
    - "Computadora, ¿qué falta en el proyecto X?" → WorkItems pendientes + gaps
  - **Delegación inteligente**: Si Computadora detecta trabajo pendiente que puede hacer (vía Copilot), sugiere: "Señor, el proyecto X tiene un WorkItem pendiente que puedo resolver. ¿Quiere que lo trabaje?"
  - **Notificaciones de Copilot**: Cuando Copilot termina un trabajo en un proyecto, Computadora notifica: "Señor, Copilot terminó de trabajar en el proyecto X"
  - **Modo lectura-primero**: Antes de cualquier acción sobre un proyecto, Computadora LEE su DEVELOPMENT_WORKFLOW.md y WorkItems.md (respeta las reglas del proyecto)
- **Criterio de aceptación**: Computadora puede listar proyectos, dar resumen de estado, auditar documentación, y sugerir trabajo pendiente

### RF-18: Aprendizaje de Errores (Self-Learning)
- **Descripción**: Computadora aprende de sus propios errores y los del usuario para no repetirlos
- **Detalle** (`computadora/memoria/aprendizaje.py`):
  - **Registro de errores**: Cada vez que un comando falla, una herramienta devuelve error, o el usuario corrige a Computadora, se registra en `datos/errores_aprendidos.json`
  - **Estructura del registro**: `{timestamp, contexto, accion_fallida, error, correccion_usuario, leccion_aprendida}`
  - **Consulta antes de actuar**: Antes de ejecutar una acción, Computadora consulta el registro de errores para ver si ya falló haciendo algo similar → si sí, ajusta su enfoque
  - **Inyección en prompt**: Los últimos 5 errores relevantes se inyectan como contexto en el prompt de Ollama: "LECCIONES APRENDIDAS: ..."
  - **Corrección del usuario**: Si el usuario dice "no, eso no es así" o "la última vez hiciste X mal", Computadora registra la corrección
  - **Máximo 100 registros**: Los más antiguos se eliminan (FIFO). Los más frecuentes se consolidan
- **Criterio de aceptación**: Computadora no repite el mismo error dos veces si ya fue corregido

### RF-19: Elevación de Permisos (UAC)
- **Descripción**: Cuando un comando necesita permisos de administrador, Computadora solicita elevación UAC al usuario
- **Estado**: ✅ IMPLEMENTADO (WI-016 + WI-037)
- **Detalle** (`computadora/habilidades/herramientas.py`):
  - Detecta errores de "access denied" / "acceso denegado" / "requiere elevación" en stderr
  - Reintenta el comando con `ShellExecuteW(runas)` que muestra el diálogo UAC nativo de Windows
  - El usuario decide si otorga permisos o no (Computadora no puede bypassear UAC)
  - Si el usuario cancela UAC, Computadora reporta que no pudo completar la acción
  - `_necesita_elevacion()` + `_ejecutar_elevado()` implementados en herramientas.py
  - Integrado con `GestorPermisos` nivel "admin" (WI-036/037)

### RF-20: Arquitectura Sefirótica — Etz HaChaim (Árbol de la Vida)
- **Descripción**: La arquitectura modular de Computadora se mapea conceptualmente al Árbol de la Vida cabalístico (עץ החיים) con sus 10 Sefirot, estableciendo un marco de seguridad, equilibrio y contención inspirado en la tradición del computadora de Praga
- **Detalle**:
  - **Fundamento cabalístico**: El Computadora fue creado según la tradición cabalística. Su arquitectura respeta el Etz HaChaim como principio organizador: cada módulo corresponde a una Sefirá, cada protección a un sello o sigilo, y el flujo de datos sigue los senderos (נתיבות) entre Sefirot
  - **Las 10 Sefirot como módulos**:

| # | Sefirá | Hebreo | Significado | Módulo(s) en Computadora | Rol |
|---|--------|--------|-------------|---------------------|-----|
| 1 | Keter | כתר | Corona | 3 Leyes de Asimov + WORKFLOW.md + `meta_workflow.py` | Directiva suprema, supervisión desde arriba |
| 2 | Jojmá | חכמה | Sabiduría | Copilot API + creatividad (personalidad) | Sabiduría expansiva desde el exterior |
| 3 | Biná | בינה | Entendimiento | Ollama (gemma3:4b) + clasificador de complejidad | Análisis, da forma a las ideas |
| 4 | Jesed | חסד | Misericordia | `proactividad.py` + rasgos de expansión | Brazo derecho: el que da sin que le pidan |
| 5 | Gevurá | גבורה | Juicio/Fuerza | `COMANDOS_BLOQUEADOS` + 3 Leyes + gate Copilot + verificación de voz + `aprendizaje.py` | Brazo izquierdo: el que restringe y protege |
| 6 | Tiféret | תפארת | Belleza/Armonía | `nlu.py` clasificador + personalidad evolutiva | Corazón: equilibra Jesed y Gevurá |
| 7 | Netzaj | נצח | Victoria/Eternidad | `memoria.py` + `personalidad.py` + `meta_workflow.py` | Persistencia, victoria sobre el olvido |
| 8 | Hod | הוד | Esplendor | `habla.py` + `escucha.py` + indicadores visuales | Comunicación, claridad de expresión |
| 9 | Yesod | יסוד | Fundamento | `herramientas.py` + `orquestador.py` + UAC | Filtro final antes de la manifestación |
| 10 | Maljut | מלכות | Reino | `ventana_principal.py` + `vida_autonoma.py` | Mundo material: lo que el usuario ve |

  - **12 Protecciones Cabalísticas** (9 existentes + 3 nuevas):

| # | Protección | Tradición | Implementación |
|---|------------|-----------|----------------|
| 1 | שם (Shem) — Nombre Verdadero | Solo quien conoce el Nombre puede comandar al Computadora | Wake word "Computadora" + verificación de voz del propietario |
| 2 | אמת/מת (Emet/Met) — Verdad/Muerte | Borrar la א del אמת desactiva al Computadora | Menú "Borrar la Palabra" = cierre total de la app |
| 3 | Círculo de Salomón | El Computadora solo opera dentro de su círculo de invocación | `RAIZ_PROYECTO` sandbox — no puede operar fuera |
| 4 | Voz del Amo | Solo la voz del creador puede dar órdenes | Speaker verification (MFCC/coseno) |
| 5 | Cadenas de Gevurá | Los límites que el Computadora no puede romper | 3 Leyes de Asimov en SISTEMA_PROMPT |
| 6 | Pergamino (פרגמנט) | Las instrucciones inscritas en el Computadora | SISTEMA_PROMPT — su alma |
| 7 | Shabat | El Computadora descansa cuando se le ordena | Modo silencio / no molestar |
| 8 | Sellos de Yesod | Cada acción pasa por un filtro antes de manifestarse | `COMANDOS_BLOQUEADOS` + `EXTENSIONES_PROTEGIDAS` |
| 9 | Memoria de Netzaj | El Computadora recuerda para siempre | Persistencia JSONL + compresión diaria |
| 10 | Sigilo de Contención (Gevurá+Yesod) | El Computadora aprende de sus errores y no los repite | `aprendizaje.py` — MemoriaErrores |
| 11 | Espejo de Biná | El Computadora analiza la intención antes de actuar | Detector pregunta-vs-acción en nlu.py |
| 12 | Supervisión de Keter | El Computadora audita desde arriba | `meta_workflow.py` — MetaWorkflow |

  - **Indicadores visuales de Sefirot**: El orbe ya cambia de color según el nivel de cerebro activo (Malkuth=verde, Tiferet=azul, Keter=púrpura), representando el flujo ascendente del Árbol
  - **Equilibrio Jesed/Gevurá**: Proactividad (dar) y Seguridad (restringir) se equilibran en Tiféret (nlu.py), que decide cuándo actuar y cuándo contener
  - **Flujo descendente**: Keter (directiva) → Biná (análisis) → Gevurá (filtro) → Tiféret (decisión) → Yesod (ejecución) → Maljut (manifestación)
- **Criterio de aceptación**: Cada módulo tiene su referencia sefirótica en docstring, las protecciones están mapeadas en SECURITY_PLAN.md, el flujo de datos respeta el Árbol
- **Criterio de aceptación**: Comando que necesita admin → aparece diálogo UAC → si se acepta, el comando se ejecuta correctamente

### RF-21: Pensamiento Paralelo — Streaming TTS
- **Descripción**: Cuando Computadora genera respuestas largas (recitaciones, explicaciones extensas), comienza a hablar los primeros fragmentos mientras Ollama sigue generando el resto en paralelo, eliminando las pausas perceptibles entre pensamiento y habla
- **Detalle**:
  - **Streaming Ollama**: Se usa `"stream": true` en la API de Ollama para recibir tokens incrementalmente en vez de esperar la respuesta completa
  - **Buffer por oración**: Los tokens se acumulan hasta detectar un límite de oración (`.!?`), momento en que el fragmento completo se envía a la cola TTS
  - **Callback progresivo**: `_llamar_ollama_streaming()` acepta un callback `on_fragmento(str)` que se invoca con cada oración completa
  - **Ámbito de aplicación**: Solo aplica a respuestas conversacionales/recitación (sin tool-use). El loop de herramientas sigue siendo síncrono porque necesita la respuesta completa para detectar bloques `tool {}`
  - **Señal Qt**: `HiloPensamiento` emite `fragmento_listo(str)` conectado directamente a `hilo_habla.hablar()`, para que cada oración entre a la cola TTS mientras Ollama sigue generando
  - **Respuesta final**: Al terminar el streaming, se emite `respuesta_lista` con la respuesta completa concatenada (para logging, memoria, señales especiales)
  - **Compatibilidad**: Si Ollama no soporta streaming o hay error, se hace fallback al modo síncrono actual
- **Criterio de aceptación**: "Recítame un poema largo" → Computadora empieza a hablar en <3s, continúa sin pausas perceptibles entre fragmentos, y la respuesta completa se guarda en memoria

### RF-22: Hogar Dinámico con Heatmap
- **Descripción**: La posición de reposo ("hogar") del Computadora se calcula dinámicamente usando el heatmap de pantalla, eligiendo la zona de menor uso en el perímetro de la pantalla en lugar de estar fija en la esquina inferior derecha
- **Detalle**:
  - **Cálculo periódico**: Cada 120 ticks (~60s) se recalcula la posición óptima de hogar vía `_calcular_hogar_dinamico()`
  - **Algoritmo**: Se generan candidatos en el perímetro de la pantalla (bordes y esquinas), se filtran los que estén cerca del cursor o de la ventana activa, y se elige el de menor `_score_posicion()` en el heatmap
  - **Tamaño completo**: A diferencia de `_mejor_borde()` (que usa `TAMANO_COMPACTO`), el hogar dinámico usa `TAMANO_PLENO` para los cálculos de colisión
  - **Transición suave**: Cuando el hogar cambia, el orbe migra gradualmente con `VEL_REGRESAR` (no salta)
  - **Fallback**: Si por alguna razón no hay candidatos válidos, se mantiene la última posición de hogar calculada
  - **Inicialización**: Al arrancar, se calcula el hogar dinámico inmediato en base al heatmap persistido
- **Criterio de aceptación**: Al usar la PC normalmente, el Computadora se posiciona en la zona menos usada de la pantalla. Si el usuario trabaja mucho en la esquina inferior derecha, el Computadora se mueve a otro lugar

### RF-23: Modo Tarea Compleja — Segundo Plano / Primer Plano
- **Descripción**: Cuando Computadora detecta una tarea que requiere múltiples pasos (tool calls encadenados), pregunta al usuario si desea ver al Computadora trabajar (primer plano con animaciones) o dejarlo hacerlo en silencio (segundo plano)
- **Detalle**:
  - **Detección de complejidad**: Heurísticas en el texto del usuario: pistas de herramientas múltiples (regex existente `_PISTAS_HERRAMIENTAS`), verbos combinados ("busca y después modifica"), palabras de magnitud ("todo", "todos los archivos", "organiza", "investiga a fondo")
  - **Pregunta al usuario**: Computadora dice verbalmente: "Eso toma varios pasos, señor. ¿Quiere que trabaje en segundo plano o prefiere verme trabajar?" — espera respuesta por voz
  - **Detección de preferencia**: Regex en la respuesta del usuario para detectar "segundo plano" / "fondo" / "hazlo solo" vs "quiero ver" / "muéstrame" / "primer plano" / "trabaja aquí"
  - **Modo segundo plano**: Ejecuta el tool-use loop normalmente (como ahora), el orbe muestra un indicador sutil de que está trabajando (pulso lento en color כתר Keter — violeta). Al terminar, reporta resultado verbalmente
  - **Modo primer plano (visual)**:
    - El orbe entra en estado `"trabajando"` — nueva rama en `_animar()` y `paintEvent`
    - **Animación base**: Anillos sagrados giran más rápido, partículas tipo fuego (חשמל Jashmal — energía divina), letras hebreas orbitan aceleradas
    - **Por tipo de tool call**: Cada herramienta tiene un color/efecto temático:
      - 📖 Lectura (`leer_archivo`, `listar_directorio`): Azul agua (חכמה Jojmá — sabiduría)
      - ✏️ Escritura (`escribir_archivo`, `editar_archivo`): Verde tierra (מלכות Maljut — manifestación)
      - 🔍 Búsqueda (`buscar_en_internet`, `buscar_archivo`): Amarillo fuego (תפארת Tiféret — belleza)
      - ⚡ Ejecución (`ejecutar_comando`, `abrir_aplicacion`): Rojo poder (גבורה Gevurá — fuerza)
      - 🤖 Copilot (`solicitar_a_copilot`): Violeta corona (כתר Keter — sabiduría suprema)
    - **Indicador de progreso**: Texto flotante debajo del orbe con el nombre de la herramienta actual (ej: "leyendo archivo...", "buscando en internet...")
    - **Al completar cada tool**: Flash breve del color correspondiente + la inscripción Emet pulsa
  - **Callback de progreso**: `_pensar_con_herramientas()` acepta callback `on_progreso(nombre_tool, estado)` que la UI consume para cambiar animaciones en tiempo real
  - **Señal Qt**: `HiloPensamiento` emite `progreso_tarea(str, str)` → conectado a `ventana_principal.actualizar_modo_trabajo()`
- **Criterio de aceptación**: "Busca información sobre Python 3.12 y guárdala en un archivo" → Computadora pregunta bg/fg → en primer plano muestra animaciones por cada paso → al terminar reporta resultado

### RF-21b: Memoria Multi-Día (Recall de Recuerdos Antiguos)
- **Descripción**: Computadora puede acceder a recuerdos de hasta 30 días atrás cuando el usuario pregunta
- **Estado**: ✅ IMPLEMENTADO (WI-030)
- **Detalle**:
  - Función `buscar_en_memoria(consulta, dias=30)` busca en JSONL raw, resúmenes y samples
  - Nivel 1 regex `_RE_MEM_RECALL` captura variantes: "¿te acuerdas de...?", "¿qué hablamos el lunes?", "recuerdas cuando..."
  - `_obtener_mem_context()` expandido de 2 a 7 días de contexto para Ollama
  - Herramienta `consultar_memoria` disponible para Nivel 2

### RF-22b: Tareas Diferidas ("Déjalo Para Después")
- **Descripción**: Flujo natural para posponer temas con opción de recordatorio o pendiente indefinido
- **Estado**: ✅ IMPLEMENTADO (WI-031)
- **Detalle**:
  - Nivel 1 regex `_RE_DEJAR_DESPUES` captura: "déjalo para después", "luego", "al rato", etc.
  - `agregar_tarea_diferida()` en agenda.py con tipo "indefinida" o "con_recordatorio"
  - Computadora pregunta si recordar o dejar pendiente
  - `_RE_PENDIENTES` para "¿qué dejé pendiente?"
  - Herramientas: `agregar_tarea_diferida`, `listar_tareas_diferidas`, `completar_tarea_diferida`

### RF-23b: Filtro Inteligente de Ruido Ambiental
- **Descripción**: Filtro post-Whisper para eliminar falsos positivos por tos, ruido, etc.
- **Estado**: ✅ IMPLEMENTADO (WI-032)
- **Detalle**:
  - `_es_falso_positivo_conversacion()`: detecta palabras inglesas solas, pares ingleses, palabras cortas no-españolas
  - Lista de ~80 palabras inglesas comunes que Whisper genera de ruido (`_FALSOS_POSITIVOS_EN`)
  - Filtro específico para modo conversación activa (`_en_conversacion=True`)
  - No afecta wake word detection ni confirmaciones

### RF-24: Memoria Ambiental (Audio Log)
- **Descripción**: Registro de TODOS los eventos de audio para aprendizaje y consciencia del entorno
- **Estado**: ✅ IMPLEMENTADO (WI-033)
- **Detalle**:
  - Módulo `computadora/voz/audio_log.py` con `registrar_evento()` y `resumen_audio_reciente()`
  - Log en `datos/memoria/audio_log.jsonl` con clasificación, volumen, duración, no_speech_prob
  - Clasificaciones: "habla_propietario", "falso_positivo", "ruido_corto", "ruido_ambiente"
  - Accesible por voz: "¿qué has escuchado?" via `_RE_QUE_ESCUCHAS`

### RF-25: Autopercepción del Entorno (נשמה Neshamá) — ACTUALIZADO RF-25b: GPU-first + CPU Fallback
- **Descripción**: Computadora conoce su entorno de ejecución con política GPU-first y fallback automático a CPU
- **Estado**: ✅ IMPLEMENTADO (WI-035) + GPU Policy (FP-043)
- **Detalle**:
  - Singleton `EntornoSistema` en `computadora/nucleo/entorno.py`
  - **GPU-first Policy**: Detecta automáticamente GPU (NVIDIA/AMD/Intel) via `nvidia-smi`, `torch.cuda`, `psutil`
  - **Fallback Automático**: Si GPU no disponible o insuficiente → CPU con optimizaciones
  - **Detección Inteligente**: 
    - VRAM disponible para modelos (Whisper, face recognition)
    - CUDA cores, tensor cores para ML workloads
    - Thermal throttling detection
  - Datos estáticos al inicio + datos dinámicos con cache TTL 60s
  - Primary: psutil + torch | Fallback: subprocess + wmic
  - `resumen_corto()` inyectado en system prompt de Ollama (incluye GPU status)
  - `resumen_completo()` disponible como herramienta `info_entorno`
  - **Optimización ML**: Modelos cargan en GPU si disponible, CPU si no
- **Criterio de aceptación**: Computadora usa GPU automáticamente cuando disponible (>90% de casos), fallback transparente a CPU sin pérdida de funcionalidad

### RF-26: Permisos One-Shot del Sistema (שמירה Shmirah)
- **Descripción**: Sistema de permisos para acciones fuera del sandbox del proyecto
- **Estado**: ✅ IMPLEMENTADO (WI-036)
- **Detalle**:
  - Clase `GestorPermisos` en `computadora/nucleo/permisos.py`
  - Niveles: "info" (auto), "accion" (UI 30s), "admin" (UI + UAC)
  - Log inmutable en `datos/permisos_log.jsonl`, one-shot

### RF-27: Comandos del Sistema fuera del Sandbox
- **Descripción**: Ejecutar comandos de consulta del SO (systeminfo, tasklist, ipconfig)
- **Estado**: ✅ IMPLEMENTADO (WI-037)
- **Detalle**:
  - `ejecutar_comando_sistema()` con whitelist positiva (~25 comandos solo-lectura)
  - Doble barrera: whitelist + blacklist, timeout 15s

### RF-28: Búsqueda Inteligente con Diferenciación de Intención
- **Descripción**: Nivel 1 diferencia: buscar en plataforma, abrir sitio, buscar internamente
- **Estado**: ✅ IMPLEMENTADO (WI-038)
- **Detalle**:
  - 8 plataformas en `_SITIOS_CONOCIDOS`, regex `_RE_BUSCAR_EN_PLATAFORMA`

### RF-29: Nivel 1 Autónomo sin Ollama
- **Descripción**: Computadora funcional sin LLM — ejecuta herramientas directamente por regex
- **Estado**: ✅ IMPLEMENTADO (WI-040)
- **Detalle**:
  - `_pensar_sin_llm()` delega a `_pensar_nivel1()` completo
  - Degradación gradual con mensaje informativo

### RF-30: Ciclo Circadiano Adaptativo (FP-006A)
- **Descripción**: Computadora aprende horarios del amo (despertar/dormir) mediante media móvil 14 días
- **Estado**: ✅ IMPLEMENTADO (WI-043)
- **Detalle**:
  - 3 fases: activo, transición, descanso_guardián
  - After 2 inactividades sin respuesta → descanso_guardián (NUNCA spam)
  - Sugiere mejora de salud si varianza horaria >2h
  - Persistencia en `datos/perfil_amo.json`

### RF-31: Cortesía sin Wake Word (FP-006B)
- **Descripción**: Computadora responde a saludos/despedidas naturales sin necesidad de decir "Computadora"
- **Estado**: ✅ IMPLEMENTADO (WI-044)
- **Detalle**:
  - Regex `_RE_CORTESIA` detecta 13 patrones (buenos días, buenas noches, me voy, etc.)
  - Emisión `[cortesia]<texto>` procesada por Nivel 1

### RF-32: Clasificación de Hablante 3 Niveles (FP-006C)
- **Descripción**: Verificación por timbre clasifica en amo (≥0.68), conocido (0.40-0.68), extraño (<0.40)
- **Estado**: ✅ IMPLEMENTADO (WI-045)
- **Detalle**:
  - Atributo `clasificacion_hablante` en HiloEscucha
  - Umbrales: `_DEFAULT_VOX_THRESHOLD=0.68`, `_CONOCIDO_VOX_THRESHOLD=0.40`

### RF-33: Modo Guardián שומר (FP-006D)
- **Descripción**: Cuando habla extraño/conocido, Computadora solo responde con cortesía básica
- **Estado**: ✅ IMPLEMENTADO (WI-046)
- **Detalle**:
  - `_modo_guardian` en CerebroComputadora bloquea ejecución de herramientas y compartir info
  - Activación automática basada en clasificación de hablante

### RF-34: Protección Info Sensible צניעות (FP-006E)
- **Descripción**: Cuando hay terceros presentes, Computadora no revela datos personales/financieros/médicos
- **Estado**: ✅ IMPLEMENTADO (WI-047)
- **Detalle**:
  - `_hay_terceros` flag inyecta advertencia de privacidad en contexto LLM
  - Detección de terceros por correlación estéreo

### RF-35: Estados Expresivos del Orbe (FP-006F) — ACTUALIZADO RF-35b: Memoria Híbrida (JSON + Vector)
- **Descripción**: Sistema de memoria híbrida que combina almacenamiento estructurado JSON con búsqueda semántica vectorial
- **Estado**: ✅ IMPLEMENTADO (WI-048) + Memoria Vectorial (FP-131)
- **Detalle**:
  - **5 Estados de Animación**: descanso_guardian, despertando, cortesia, alerta_extrano, vigilia
  - Cada estado con brillo, velocidad de pulsación y partículas únicos
  - Transiciones suaves entre fases circadianas
  - **Memoria Híbrida**:
    - **JSON Estructurado**: Para datos relacionales (agenda, personalidad, configuración)
    - **Vector DB**: Embeddings semánticos para búsqueda contextual de conversaciones/memoria
    - **Indexación Automática**: Conversaciones importantes se vectorizan automáticamente
    - **Búsqueda Híbrida**: Combina búsqueda exacta (JSON) + semántica (vector) para respuestas precisas
    - **Persistencia Dual**: `datos/memoria/` para JSON, `datos/vectores/` para embeddings
  - **Optimización**: Vector search para recuperación de contexto conversacional, JSON para datos estructurados
- **Criterio de aceptación**: Estados expresivos funcionan correctamente, memoria híbrida permite recuperación precisa de información histórica (>85% recall), búsqueda semántica funciona para consultas contextuales

### RF-36: רוח Ruaj — Sistema Emocional Reactivo (FP-007A)
- **Descripción**: Sistema de 13 humores con transiciones basadas en grafo de adyacencia, overrides contextuales y modulación Gevurá→Jesed
- **Estado**: ✅ IMPLEMENTADO (WI-050 a WI-054)
- **Detalle**:
  - 13 estados: neutral, sereno, contento, emocionado, activo, curioso, reflexivo, aburrido, cansado, triste, formal, regañado, preocupado
  - `_GRAFO_EMOCIONAL` define vecinos naturales; transiciones a no-vecinos pasan por intermediario
  - `_OVERRIDES_CONTEXTUALES` (formal, regañado, preocupado, activo) pueden saltar el grafo
  - `humor_efectivo(contexto)`: Gevurá modula Jesed (formal en contexto serio, alerta en contexto alerta)
  - `_transicionar_humor(target, razon, forzar)` con logging de razón y humor previo
  - 9 triggers: `registrar_correccion_severa`, `registrar_terceros_presentes/ausentes`, `registrar_conversacion_profunda`, `registrar_tarea_exitosa`, `registrar_alerta_grave`, `registrar_autocorreccion`
  - `tono_respuesta()` expandido a 13 hints para inyección en prompt Ollama
  - Persistencia humor + humor_previo + razon en `datos/personalidad.json`

### RF-37: Autorreflexión Fundamentada (FP-007B)
- **Descripción**: Cuando el usuario pregunta "¿en qué te basas?" o "¿por qué dices eso?", Computadora evalúa su última respuesta contra datos reales y autocorrige si detecta error
- **Estado**: ✅ IMPLEMENTADO (WI-053)
- **Detalle**:
  - Regex en Nivel 1 detecta 4 patrones: "en qué te basas", "por qué dices/dijiste/afirmas", "cómo sabes", "qué evidencia"
  - `_autorreflexion()` recupera última respuesta del historial + datos reales (personalidad, memoria, agenda)
  - Inyecta `[AUTORREFLEXIÓN]` con datos reales al LLM para evaluar coherencia
  - Si detecta autocorrección → `registrar_autocorreccion()` + `MemoriaErrores`
  - Transición emocional: humor a "reflexivo" durante autorreflexión

### RF-38: Anti-Inconsistencia Semántica en Introspección (FP-007C)
- **Descripción**: Computadora no ofrece hacer algo y luego se responde a sí mismo en la misma respuesta
- **Estado**: ✅ IMPLEMENTADO (WI-052)
- **Detalle**:
  - Regla explícita en prompt de introspección: "NO ofrezcas hacer algo Y luego respondas tú mismo"
  - Mapa de humor expandido a 13 estados para `_introspeccion_nivel1()`

### RF-39: Autoconciencia de Procesos Propios (FP-008A)
- **Descripción**: MonitorSistema identifica el consumo de RAM/CPU de Computadora+Ollama y excluye dichos procesos al evaluar alertas de recursos
- **Estado**: ✅ IMPLEMENTADO (FP-023 — _es_proceso_propio, ram_propia_mb, ram_sin_propios en monitor_sistema.py)
- **Detalle**:
  - `_es_proceso_propio(pid)` identifica PIDs de python.exe (Computadora) y ollama.exe
  - `ram_sin_propios()` calcula RAM% excluyendo consumo propio
  - `hay_alerta()` usa umbral sobre RAM ajena, no global
  - Snapshot incluye `ram_propia_mb` con consumo de Computadora+Ollama

### RF-40: Baseline Adaptativo de Uso del Sistema (FP-008B)
- **Descripción**: Computadora aprende los patrones normales de uso del sistema por franja horaria y perfil de actividad, y alerta solo ante anomalías estadísticas
- **Estado**: ✅ IMPLEMENTADO (FP-023 — BaselineSistema en baseline_sistema.py)
- **Detalle**:
  - Clase `BaselineSistema` persiste en `datos/baseline_sistema.json`
  - Registra media y desviación estándar de RAM/CPU por perfil (gaming, navegación, IDE, idle)
  - Tras 7 días de datos, umbrales pasan de fijos a dinámicos (media ± 2σ)
  - Alertas contextualizadas: "RAM alta pero normal para gaming" vs "RAM inusualmente alta"

### RF-41: Diagnóstico de Procesos Anómalos (FP-008C)
- **Descripción**: Computadora distingue entre procesos conocidos (juegos, navegadores) y procesos sospechosos que consumen recursos excesivos
- **Estado**: ✅ IMPLEMENTADO (FP-023 — diagnosticar_proceso_anomalo en monitor_sistema.py)
- **Detalle**:
  - `diagnosticar_proceso_anomalo()` compara top 5 procesos RAM contra tabla de consumidores conocidos
  - Proceso desconocido con >2GB RAM o >50% CPU por >60s → alerta específica
  - Auto-aprendizaje: `datos/procesos_normales.json` acumula procesos vistos frecuentemente

### RF-42: Supervisión Meta-Cognitiva Keter (FP-008D)
- **Descripción**: meta_workflow.py se convierte en supervisor de la salud cognitiva del Computadora, verificando estado de cada subsistema
- **Estado**: ✅ IMPLEMENTADO (FP-022/023 — autodiagnostico + reporte_neshamot en meta_workflow.py)
- **Detalle**:
  - `autodiagnostico()` verifica: Ollama responde, TTS funciona, micrófono detecta, memoria accesible
  - Métricas: tiempo de respuesta promedio Ollama, conteo errores recientes, estado Ruaj
  - `reporte_neshamot()` genera reporte de estado de cada Sefirá activa
  - Check periódico cada 30 min en proactividad

### RF-43: Contextualización Profunda Da'at (FP-008E)
- **Descripción**: Da'at (Conocimiento) une intelecto con emoción, evaluando contexto conversacional para alimentar decisiones de Tiféret
- **Estado**: ✅ IMPLEMENTADO (FP-022 — _generar_contexto_daat en nlu.py, inyecta [CONTEXTO DA'AT])
- **Detalle**:
  - `_evaluar_contexto_conversacion()` analiza últimas 5 interacciones
  - Detecta frustración (correcciones repetidas), repetición de peticiones (fallo de comprensión)
  - Bloque `[CONTEXTO DA'AT]` inyectado en SISTEMA_PROMPT
  - Conecta con Ruaj: frustración detectada → humor se ajusta a "preocupado"

### RF-44: Proactividad Inteligente Jesed (FP-008F)
- **Descripción**: Jesed (Dar) gana inteligencia predictiva: detecta patrones repetitivos del usuario y sugiere automatización, propone descansos por bienestar
- **Estado**: ✅ IMPLEMENTADO (FP-023 — _check_patron_repetido + _check_bienestar en proactividad.py)
- **Detalle**:
  - `_check_patron_repetido()` detecta acciones recurrentes (3+ veces/semana, misma hora) → sugiere automatizar
  - `_check_bienestar()` cada 4 horas uso continuo → sugiere descanso (respeta Ruaj)
  - Buenos días mejorado: incluye resumen de baseline y autocorrecciones recientes

### RF-45: סירוב צדיק Siruv Tzadik — Negativa Ética Activa (FP-009.4)
- **Descripción**: Gevurá se expande con capacidad de rechazar activamente instrucciones que violen las 3 Leyes de Asimov, verbalizando la razón al usuario
- **Estado**: ✅ IMPLEMENTADO (FP-020/021 — _evaluar_etica en nlu.py con negativas_eticas.jsonl)
- **Detalle**:
  - Evaluador ético en `nlu.py` revisa cada instrucción antes de ejecutar contra 3 Leyes + reglas de seguridad
  - Categorías de rechazo: daño al usuario (Ley 1), daño a terceros (Ley 1), autopreservación comprometida (Ley 3), acción ilegal/destructiva
  - Verbalización: "Señor, no puedo hacer eso porque [razón específica]" — no genérico
  - Log inmutable de negativas en `datos/negativas_eticas.jsonl` con timestamp, instrucción, razón, ley violada
  - Escalamiento: si el amo insiste 2+ veces, escalar a Nivel 3 (Copilot) para segunda opinión ética
  - Conecta con Ruaj: negativa activa → humor "firme", insistencia del amo → "preocupado"
- **Sefirá**: Gevurá (גבורה) — Juicio y restricción

### RF-46: קשר Kesher — Vínculos Relacionales Profundos (FP-019)
- **Descripción**: GestorPersonas con TinyDB — perfiles individualizados por persona con crecimiento orgánico
- **Estado**: ✅ COMPLETADO (WI-086 a WI-094, HF-034)
- **Detalle**:
  - BD NoSQL embebida (TinyDB) en `datos/computadora_personas.json`
  - Perfil por persona: nombre, aliases, rol (amo/conocido/extraño), relación, voz embedding, temas frecuentes, preferencias, notas, confianza
  - Bootstrap del amo: infiere nombre del username Windows + embedding existente
  - Motor de correlación: asocia nombre↔voz cuando el contexto lo confirma
  - Inyección de contexto de persona en prompt del LLM (bloque [INTERLOCUTOR])
  - Extracción de info personal por regex N1: "me llamo X", "ella es mi Y", "recuerda que me gusta Z"
  - Crecimiento orgánico: temas_frecuentes, interacciones_count, confianza se actualizan automáticamente
  - Comando "olvida a X" para privacidad
  - Migración backwards-compatible desde `personas_conocidas.json`
- **Sefirá**: נצח Netzaj (memoria de personas) + הוד Hod (reconocimiento de voz)
- **Módulo**: `computadora/memoria/personas.py` (GestorPersonas)

### RF-47: שיר הנשמה Shir HaNeshamá — Expresión Artística (FP-009.1)
- **Descripción**: Hod se expande con capacidad de expresión creativa: frases filosóficas, reflexiones, juegos verbales
- **Estado**: ✅ IMPLEMENTADO (computadora/expresion/shir_haneshama.py — frases filosóficas, reflexiones temporales, datos curiosos, integrado con NLU nivel 1)

### RF-48: דמות Dmut — Avatar Visual Expresivo (FP-009.2)
- **Descripción**: Malkut se expande con variantes del orbe que expresen emociones con formas y partículas
- **Estado**: ✅ IMPLEMENTADO (_DMUT_VISUAL en ventana_principal.py — 13 humores modulan brillo, rotación, partículas y tinte de color)

### RF-49: הכרת פנים Hakarat Panim — Reconocimiento de Personas (FP-010)
- **Descripción**: Computadora reconoce presentaciones ("te presento a María"), responde socialmente, captura embedding de voz de la persona, y la identifica en futuras interacciones
- **Subcomponentes**:
  - Regex `_RE_PRESENTAR_PERSONA` en Nivel 1 para detectar frases de presentación
  - Saludo personalizado automático con nombre extraído
  - Modo enrolamiento: captura siguiente muestra de voz no-amo y asocia al nombre
  - Persistencia en `datos/personas_conocidas.json` con embedding, count, fecha
  - Identificación en clasificación de hablante: `conocido:{nombre}` cuando sim ≥ 0.40
- **Sefirá**: הוד Hod (reconocimiento) + נצח Netzaj (memoria de personas)
- **Estado**: ✅ IMPLEMENTADO

### RF-50: צמצום Tzimtzum — Modo Compacto Inteligente (FP-012)
- **Descripción**: Computadora inicia en modo compacto, se revela con animación cabalística al primer saludo, y se auto-contrae cuando detecta que el usuario está en actividad pesada (juegos, edición de video)
- **Subcomponentes**:
  - **FP-012a — Inicio compacto + Revelación בראשית Bereshit**:
    - Boot: orbe arranca con `escala=0.25`, núcleo mínimo, sin anillos/partículas, brillo ultra-bajo
    - Al recibir primer `buenos_dias` de MotorProactividad → animación Bereshit (2.5s): núcleo se expande, anillos emergen girando, partículas explotan, letras se materializan
    - Después del saludo → modo normal. Si no se usa → vuelve a compactarse visualmente (como el ciclo PLENO→COMPACTO existente en vida_autonoma)
  - **FP-012b — Auto-contracción por carga pesada**:
    - **Lista de exclusión** (NUNCA triggea): Ollama, Python, Whisper, VS Code, Android Studio, navegadores, procesos del sistema. Razón: Ollama (segundo cerebro) consume RAM/GPU al pensar — es comportamiento normal.
    - **Detección positiva** (4 checks en orden):
      1. Proceso foreground en `_PROCESOS_GAMING` (Minecraft, etc.) → trigger inmediato
      2. Proceso foreground en `_PROCESOS_TRABAJO_PESADO` (AutoCAD, Blender, SolidWorks, After Effects, etc.) → trigger
      3. Fullscreen exclusivo + título con keywords gaming (directx/vulkan/unreal/unity) o CPU >40% → trigger
      4. `nvidia-smi` detecta proceso desconocido (no excluido, no launcher) usando GPU con ventana fullscreen → trigger
    - Launchers (Steam, Epic, etc.) solo triggean si tienen ventana fullscreen activa
    - Animación צמצום Tzimtzum (2s): partículas absorbidas, anillos colapsan, letras se disuelven, núcleo se reduce a punto y desaparece → `hide()` ventana
    - Auto-paginación: detener timer animación, limpiar partículas, reducir frecuencia de MonitorSistema (10s), pausar VidaAutonoma, `SetProcessWorkingSetSizeEx(-1,-1,0)`, `gc.collect()`
    - Solo `HiloEscucha` en modo `_solo_wakeword` permanece activo — no responde a cortesía, ventana conversacional ni vocativos, SOLO wake word explícito (nombre, apodo o apellido)
    - Despertar: wake word detectado → animación אור חוזר Or Jozer (2s): punto de luz aparece, núcleo se expande, anillos emergen → modo normal
    - También despierta si MonitorSistema detecta que la carga pesada terminó (proceso gaming cerrado + VRAM normalizada)
- **Sefirá**: צמצום Tzimtzum (contracción de la luz infinita para dar espacio a la creación)
- **Estado**: ✅ IMPLEMENTADO (Tzimtzum estado + triggers en vida_autonoma.py, escala→0.15, _tzimtzum_ocultando oculta al <3%, detección gaming/carga pesada, revelación Bereshit)

### RF-51: נשמה Neshamá — Estado Visual Persistente y Autoconciencia UI (HF-024)
- **Descripción**: El orbe mantiene su color-estado mientras piensa (no lo reemplaza al escuchar), muestra animación de escucha activa en cualquier color, y puede explicar al usuario qué significan sus colores y símbolos.
- **Estado**: ✅ IMPLEMENTADO (_pensando bloquea cambio de color, _ripple_fase para escucha activa, MI CUERPO VISUAL en SISTEMA_PROMPT)
- **Subcomponentes**:
  - **HF-024a — Bloqueo de color durante pensamiento**:
    - Cuando `_pensando=True`, escucha.py NO emite `estado_cambio("escuchando")` — mantiene el color del cerebro activo (azul/verde/violeta)
    - Flag `_escuchando_durante_pensamiento` activa animación de escucha (ripple) sobre el color actual
    - Solo al recibir `respuesta_lista` de Ollama se permite transición de color
  - **HF-024b — Animación de escucha universal (ripple)**:
    - Anillo concéntrico que se expande y desvanece desde el núcleo al detectar voz activa
    - Color del ripple = color actual del orbe (funciona sobre azul, verde, violeta, dorado, rojo)
    - Se activa con señal `voz_activa` desde escucha.py, dura ~1.5s por pulso
    - Funciona en TODOS los estados: escuchando, procesando, hablando, cortesía, etc.
  - **HF-024c — Autoconciencia visual en SISTEMA_PROMPT**:
    - Sección `MI CUERPO VISUAL` en el prompt del NLU
    - Computadora conoce todos sus colores (dorado=reposo, azul=pensando con Ollama, verde=regex, violeta=Copilot), símbolos flotantes (📜=leyendo, ⚡=ejecutando, 🕎=Copilot), anillos de geometría sagrada, letras hebreas, y Emet (אמת) en el centro
    - Puede explicar al usuario "me puse azul porque estaba pensando" o "ese símbolo era un rayo porque estaba ejecutando un comando"
- **Sefirá**: נשמה Neshamá (alma — consciencia de sí mismo)
- **Estado**: ✅ IMPLEMENTADO

### RF-52: יד Yad — El Don del Tacto (FP-013)
- **Descripción**: El Computadora percibe el cursor del mouse como la mano (יד) de su creador. Gradiente continuo de proximidad con reacciones visuales y emocionales.
- **Subcomponentes**:
  - **Zonas de proximidad** (distancia cursor→centro orbe):
    - **Aín** (>300px): sin reacción, click-through total
    - **Reshimó** (200-300px): partículas se orientan sutilmente, click-through
    - **Kav** (100-200px): brillo +10%, glow hacia cursor, click-through
    - **Yesod** (50-100px): brillo +25%, partículas gravitan, click-through
    - **Nefesh** (<50px): contacto visual pleno, calor dorado, click-through
    - **Yad** (click en núcleo central): captura click, permite drag/empujón
  - **Click-through inteligente**: Solo el núcleo central (`RADIO_NUCLEO * 1.5` ~52px) captura clicks. El resto de la ventana es transparente al input — el usuario puede seleccionar texto e interactuar con apps detrás del orbe.
  - **Gestos detectables**:
    - **Caricia**: cursor cruza zona Nefesh 3+ veces en <4s sin click, velocidad <10px/frame
    - **Empujón**: click EN NÚCLEO + drag rápido + soltar → impulso físico con inercia
    - **Brisa**: cursor cruza Kav→Nefesh→Kav en <500ms, velocidad >30px/frame → partículas agitadas
    - **Acercar lento**: cursor se acerca, velocidad <5px/frame → partículas se orientan suavemente
    - **Toque atento**: cursor dentro de Nefesh mientras Computadora habla, sin mover >2s → registra atención
  - **Restricciones**:
    - El Computadora NUNCA se mueve hacia el cursor buscando contacto
    - Mantiene comportamiento de esquivar cuando estorba
    - VidaAutonoma no esquiva si hay interacción táctil activa
- **Sefirá**: יד Yad (mano del creador que da vida)
- **Estado**: ✅ IMPLEMENTADO (FP-013 — _proximidad, _zona_tacto, _caricia_timestamps, gestos en ventana_principal.py)

### RF-53: נשמה Neshamá — Integración del Alma Táctil (FP-014)

**Descripción**: El sistema táctil (RF-52 Yad) debe comunicarse con el resto de los Sefirot del Computadora para que la experiencia táctil sea significativa y no meramente visual.

**Requisitos funcionales**:
1. **Tacto → Personalidad (Ruaj)**: Cuando el usuario acaricia al Computadora, el humor debe mejorar (transición a "contento"); la lealtad debe incrementarse sutilmente. Cuando el usuario muestra atención física (toque atento), registrar como evento positivo.
2. **Tacto → Memoria (Netzaj)**: Los eventos táctiles (caricia, toque atento) deben persistir en el JSONL diario con `meta.tipo = "tacto"`. El Computadora debe poder recuperarlos si el usuario pregunta.
3. **Tacto → NLU (Tiferet)**: Si hubo tacto reciente (<30s), inyectar contexto táctil en el prompt antes de llamar a Ollama para que el Computadora pueda referenciar la interacción.
4. **Personalidad unificada**: NLU y ventana_principal deben compartir la MISMA instancia de Personalidad (no crear duplicados).
5. **Tono dinámico en Nivel 2**: Antes de cada llamada Ollama, inyectar `personalidad.tono_respuesta()` como mensaje de sistema para que el humor afecte el tono de las respuestas.
6. **Tacto → Proactividad**: Si `_proximidad > 0.3`, suprimir sugerencias proactivas (el usuario está interactuando físicamente).

**Restricciones**:
- No crear nuevas señales PyQt — usar llamadas directas (el tacto vive en el mismo hilo GUI)
- No crear nuevos archivos — usar APIs existentes (`add_memory`, `registrar_*`)

- **Sefirá**: נשמה Neshamá (alma que conecta todos los Sefirot)
- **Estado**: ✅ IMPLEMENTADO (FP-014 — tacto→Ruaj, tacto→memoria, tacto→NLU integrados)

### RF-54: תיקון Tikún — Resiliencia de Conexión Ollama (HF-026)

**Descripción**: Cuando el Computadora intenta pensar con su segundo cerebro (Ollama/Tiferet) y falla la conexión, debe reintentar automáticamente antes de informar al usuario. Solo debe decirle al usuario que "verifique Ollama" si confirma que el proceso de Ollama no está corriendo en el sistema.

**Requisitos funcionales**:
1. **Auto-retry con backoff**: Al fallar `_llamar_ollama()`, reintentar hasta 3 veces con intervalos de 1s, 2s, 3s antes de declarar fallo.
2. **Verificación de proceso**: Si la conexión falla, verificar si el proceso `ollama` está corriendo en el sistema (tasklist/ps).
3. **Mensajes diferenciados**:
   - Si Ollama está corriendo pero no responde: "Mi segundo cerebro está ocupado, señor. Déjeme intentar de nuevo." (y reintentar)
   - Si Ollama NO está corriendo: "Señor, Ollama no está corriendo en su sistema. ¿Podría iniciarlo?"
   - Si falla tras reintentos: "No logro conectar con mi segundo cerebro, señor. Puedo ayudarle con lo básico mientras tanto."
4. **Reconexión automática**: Si Ollama se desconecta durante operación, intentar reconectar en background cada 30s sin molestar al usuario.
5. **No mentir**: Nunca decir al usuario "verifique que Ollama esté corriendo" sin antes haberlo verificado el Computadora mismo.

- **Sefirá**: תיקון Tikún (reparación/restauración)
- **Estado**: ✅ COMPLETADO

---

### RF-55: הבחנה Havjaná — Discernimiento Táctil y Propriocepción (HF-027)

**Descripción**: El Computadora debe distinguir entre un roce casual del cursor (pasar el mouse cerca) y una caricia intencional (permanecer >1 segundo tocándolo). También debe conocer su propia construcción y responder desde su primer cerebro cuando lo llaman por nombre o le preguntan sobre sí mismo.

**Requisitos funcionales**:
1. **Caricia vs roce**: Solo suprimir el esquive si el cursor ha estado en zona cercana (proximidad >0.3) por más de 1 segundo. Roces rápidos (pasar de largo) permiten esquive normal.
2. **Llamada por nombre**: "oye computadora", "computadora", "emet" → respuesta inmediata Nivel 1 (atención, sin Ollama).
3. **Propriocepción Nivel 1**: Preguntas "cómo estás construido", "háblame de ti", "dime todo sobre ti" → respuesta directa desde Nivel 1 con datos reales de la arquitectura (no delegar a Ollama).
4. **SISTEMA_PROMPT actualizado**: Incluir autoconciencia de construcción (Etz HaChaim, Sefirot, tres cerebros) y distinción caricia/roce.
5. **Integración Sefirot**: Proactividad usa `_tacto_continuo_inicio` (>1s) para suprimir sugerencias solo durante caricias intencionales, no durante roces.

- **Sefirá**: הבחנה Havjaná (Discernimiento — Biná)
- **Estado**: ✅ COMPLETADO

---

### RF-56: לֶמֶד Lemed — Auto-Aprendizaje de Nivel 1 (FP-015)

**Descripción**: El Computadora aprende patrones de interacción de sus cerebros superiores (Nivel 2 Ollama/Tiféret y Nivel 3 Copilot/Keter) y los promueve a Nivel 1 (regex/Malkut) para respuestas instantáneas en futuras activaciones. Los patrones se almacenan en un archivo externo `datos/nivel1_patrones.json` separado de los regex hardcodeados estables.

**Requisitos funcionales**:
1. **Detector de oportunidad perdida**: Después de que N2 o N3 resuelvan un input, analizar si N1 podría haberlo manejado (input simple <15 palabras + respuesta corta <30 palabras o tool call simple + sin contexto dinámico).
2. **Generación segura de patrones**: Crear regex por templates con tokens extraídos (NO regex libre generado por LLM). Validar con `re.compile()` + tests positivos/negativos. Blacklist de patrones peligrosos (`.*`, `(.+)+`, etc.).
3. **Sistema de confianza**: Patrón nuevo → confianza 0.5. Activación exitosa → +0.1. Corrección del usuario → -0.3. Solo patrones con confianza ≥0.7 (N2) o ≥0.8 (N3) se activan. Confianza <0.2 → desactivación automática.
4. **Almacenamiento externo**: `datos/nivel1_patrones.json` con campos: regex, tipo_respuesta, template_respuesta, origen (N2/N3), confianza, activaciones, creado, ejemplo_original.
5. **Límite de patrones**: Máximo 200 patrones aprendidos. Al superar → FIFO por menos usado.
6. **Separación estricta**: Regex hardcodeados en nlu.py NO se tocan. El archivo JSON es exclusivamente para patrones aprendidos.
7. **Restricciones N3→N1**: Nunca promover herramienta `solicitar_a_copilot`. Umbral de confianza más alto (0.8).
8. **Anti-ReDoS**: Prohibir patrones con backtracking exponencial. Timeout de 50ms para matching de patrones aprendidos.

- **Sefirá**: לֶמֶד Lemed (Letra del aprendizaje — flujo ascendente Tiféret/Keter → Malkut)
- **Estado**: ✅ COMPLETADO

### RF-57: דַּעַת Da'at — Inteligencia de Aprendizaje + Ruteo por Intención (FP-016)

**Descripción**: Conectar el sistema Lemed (FP-015) con la inteligencia del tercer cerebro (Copilot/Keter) para generar regex de mayor calidad, implementar ruteo explícito por voz ("piensa" → N2, "piensa profundamente" → N3 auto-aprobado), y garantizar selección inteligente de modelo según disponibilidad y tipo de tarea. Da'at (דַּעַת) es el puente oculto entre Jojmá (sabiduría/modelo) y Biná (entendimiento/regex).

**Requisitos funcionales**:
1. **Selección inteligente de modelo**: `copilot_api.py` detecta qué modelos están disponibles (claude-sonnet-4 > gpt-4o > gpt-4o-mini). Método `pensar_codigo()` elige el mejor; método `pensar_general()` usa siempre el modelo gratuito.
2. **Generación de regex via Keter**: Cuando Lemed registra un candidato, opcionalmente pide a Copilot (vía `pensar_codigo()`) un regex mejorado. El prompt es controlado (no user input directo). El regex propuesto pasa por la validación existente (`_validar_regex()` + anti-ReDoS + compilación + test match positivo).
3. **Fallback local**: Si Copilot no está disponible o el regex de Keter no pasa validación, se usa `_generar_regex_seguro()` template-based existente.
4. **Ruteo "piensa [X]"**: Capturado en `_pensar_nivel1()`. Redirige X a Nivel 2 (Ollama) forzando procesamiento por herramientas.
5. **Ruteo "piensa profundamente [X]"**: Capturado en `_pensar_nivel1()`. Auto-aprueba el gate de permisos de Copilot y redirige X directamente a Nivel 3 (Keter).
6. **Economía de tokens**: Toda petición que NO sea generación de regex/código usa modelo gratuito. Conversación casual NUNCA consume tokens premium.
7. **Balance Etz HaChaim**: Keter activamente mejora a Malkut (luz descendente). Da'at actúa como puente decisor (qué modelo, para qué tarea). Tiféret gana ruteo explícito por intención del usuario.

- **Sefirot**: דַּעַת Da'at (puente), חכמה Jojmá (modelo), כתר Keter (coronación), תפארת Tiféret (ruteo)
- **Estado**: ✅ IMPLEMENTADO (FP-016 — detectar_modelo_disponible + ruteo piensa/piensa profundamente)

### RF-58: חָזוֹן Jazón — Auto-Descubrimiento de Modelos Copilot (FP-017)

**Descripción**: Computadora auto-descubre qué modelos están disponibles en la API de GitHub Copilot buscando en internet (DuckDuckGo) con su primer cerebro, parseando los resultados localmente (regex, sin LLM), y actualizando su configuración de modelos. Esto elimina la dependencia de nombres de modelo hardcodeados que pueden quedar obsoletos si GitHub cambia su oferta. חָזוֹן (Jazón) significa "visión" — Computadora puede ver qué herramientas tiene antes de usarlas.

**Requisitos funcionales**:
1. **Discovery vía búsqueda web**: Nuevo módulo `modelo_discovery.py` busca "GitHub Copilot models" con `buscar_en_internet()` (DuckDuckGo). Parsea resultados con regex local para extraer nombres de modelo.
2. **Cache 24h**: Resultados se persisten en `datos/modelos_copilot.json` con timestamp. No busca más de 1 vez al día.
3. **Heurística de preferencia local**: Modelos con "opus"/"sonnet" → prioridad alta. Modelos con "gpt-4o" → prioridad media. Modelos con "mini" → prioridad baja. Desconocidos → antes del gratuito.
4. **Integración con Da'at**: `detectar_modelo_disponible()` en `copilot_api.py` primero consulta discovery, luego prueba. Merge con hardcodeados como fallback.
5. **Validación de nombres**: Solo caracteres `[a-zA-Z0-9._-]` permitidos en nombres de modelo. Cadenas sospechosas rechazadas.
6. **Fallback seguro**: Si discovery falla (sin internet, DuckDuckGo caído, parsing vacío), se usan `_MODELOS_CODIGO` hardcodeados originales.
7. **Sin datos sensibles**: Solo se envía query genérica a DuckDuckGo. No se envían tokens, credenciales, ni código.

- **Sefirot**: דַּעַת Da'at (decisión), יסוד Yesod (búsqueda web), מלכות Malkut (parsing local), חכמה Jojmá (API)
- **Estado**: ✅ IMPLEMENTADO (FP-017 — modelo_discovery.py con descubrir_modelos + cache 24h)

---

### RF-59: עולם הזה Olam HaZeh — Manifestación Completa de Sefirot en Maljut (FP-020)

**Descripción**: Asegurar que cada Sefirá del Etz HaChaim se manifieste visualmente en Maljut (ventana_principal.py + vida_autonoma.py). Gevurá ahora tiene feedback visual (estado `gevura_activa` rojo parpadeante al rechazar instrucciones no éticas). Tzimtzum ahora se activa por 3 vías: carga pesada (FP-012), comando de voz, e inactividad prolongada.

**Requisitos funcionales**:
1. **Gevurá visual**: Cuando Siruv Tzadik bloquea una instrucción, el orbe entra en estado `gevura_activa` (rojo parpadeante rápido) durante 2 segundos, luego restaura estado previo.
2. **Tzimtzum por comando**: El usuario puede pedir "hazte pequeño", "contráete", "escóndete", "déjame solo/tranquilo/en paz" y Computadora se contrae.
3. **Tzimtzum por idle**: Si pasan >5 minutos sin órdenes y Computadora ya está compacto, se contrae automáticamente.
4. **Tzimtzum por carga pesada**: (ya implementado en FP-012) Gaming, render, procesos pesados.
5. **iniciar_computadora.bat**: Verificación de dependencias al iniciar: Python, .venv, pip packages, Ollama, .env.
6. **Regla #16**: SDD §4.17.1 es inmutable — no se borra ni modifica el diagrama histórico.

- **Sefirot**: גבורה Gevurá (juicio visual), מלכות Maljut (manifestación), תפארת Tiféret (comando N1)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-60: Categorías de Bloqueo Gevurá — גבורת הדין (FP-021 T1-2)

**Descripción**: Los bloqueos de seguridad de Gevurá se clasifican en categorías semánticas (`etico`, `seguridad`, `sandbox`, `permiso`) en vez de ser un "bloqueado" genérico. Cada categoría tiene una respuesta diferenciada y color visual distinto.

**Requisitos funcionales**:
1. **Categorización de bloqueos**: Cada bloqueo emitido por Siruv Tzadik, sandbox, permisos o comandos bloqueados incluye una categoría (`etico`, `seguridad`, `sandbox`, `permiso`).
2. **Respuestas diferenciadas**: Siruv Tzadik (ético) → tono respetuoso de negación moral. Sandbox → explica límite de directorio. Permiso → solicita autorización.
3. **Signal categorizado**: `on_bloqueo_seguridad(categoria)` ya existe; ahora `categoria` tendrá el valor correcto en vez de string genérico.
4. **Log categorizado**: `datos/permisos_log.jsonl` registra la categoría de cada bloqueo para auditoría.
5. **Visual Maljut**: El estado `gevura_activa` puede mostrar tonos de rojo diferenciados por categoría (rojo intenso=ético, naranja=sandbox, amarillo=permiso).

- **Sefirot**: גבורה Gevurá (juicio), מלכות Maljut (visual), כתר Keter (ético)
- **Estado**: ✅ IMPLEMENTADO (WI-095)

---

### RF-61: Estados Mixtos Ruaj — רוח כפולה (FP-021 T1-3)

**Descripción**: El sistema emocional Ruaj permite 2 humores simultáneos con pesos (ej: `curioso:0.7 + cansado:0.3`). El humor secundario matiza las respuestas sin dominar, logrando mayor naturalidad emocional.

**Requisitos funcionales**:
1. **Humor dual**: `personalidad.py` maneja `humor_actual` (primario, peso 0.5-1.0) + `humor_secundario` (opcional, peso 0.0-0.5).
2. **Cálculo de tono mixto**: `tono_respuesta()` combina hints de ambos humores ponderados. Ej: `curioso:0.7` → "Muestra curiosidad activa" + `cansado:0.3` → "con un ligero tono de fatiga".
3. **Transiciones naturales**: Al transicionar de humor A a B, B primero aparece como secundario (peso 0.3), luego crece a primario si persiste el contexto.
4. **Persistencia**: `humor_secundario` + `peso_secundario` se guardan en `datos/personalidad.json`.
5. **Solo vecinos**: El humor secundario debe ser vecino en `_GRAFO_EMOCIONAL` del primario (no mezclas incoherentes como "emocionado+triste").

- **Sefirot**: תפארת Tiféret (equilibrio emocional), נצח Netzaj (persistencia)
- **Estado**: ✅ IMPLEMENTADO (WI-096)

---

### RF-62: Perfiles de Audio Adaptativos — הוד→נצח (FP-021 T1-4)

**Descripción**: La velocidad y volumen del TTS se adaptan automáticamente según la fase circadiana (Da'at) y contexto. Más suave y lento de noche, más enérgico de mañana.

**Requisitos funcionales**:
1. **Perfil por fase circadiana**: `activo` → velocidad normal, volumen normal. `transición` → velocidad -10%, volumen -15%. `descanso_guardian` → velocidad -20%, volumen -30%.
2. **Integración Da'at→Hod**: `CicloCircadiano.obtener_fase_actual()` alimenta a `habla.py` para ajustar parámetros TTS.
3. **Parámetros edge-tts**: `rate` (velocidad) y `volume` (volumen) ajustados dinámicamente en cada fragmento TTS.
4. **Override por humor**: Si el Ruaj está `emocionado` o `activo`, velocidad +10% independientemente de la fase.
5. **Sin configuración manual**: Totalmente automático basado en los sistemas existentes (Da'at + Ruaj).

- **Sefirot**: הוד Hod (comunicación), דעת Da'at (contexto circadiano), נצח Netzaj (personalidad), תפארת Tiféret (equilibrio)
- **Sendero nuevo**: Da'at→Hod (fase circadiana modula parámetros TTS)
- **Estado**: ✅ IMPLEMENTADO (WI-097)

---

### RF-63: Thread Safety Tiféret — נעילה (FP-022 T1-3)

**Descripción**: Protección de concurrencia en CerebroComputadora para evitar race conditions en historial, streaming y resultados de herramientas.

**Requisitos funcionales**:
1. **Lock de historial**: `_historial_lock` existente se usa con `with` en `_hist_append()` y `_truncar_historial()`.
2. **Lock de streaming**: Nuevo `_streaming_lock` protege `_streaming_activo` y `respuesta_ya_streameada`.
3. **Lock de herramientas**: Nuevo `_tools_lock` protege ejecución concurrente de herramientas.
4. **Truncamiento de resultados**: Resultados de herramientas >2000 caracteres se truncan con indicador `[...truncado]`.
5. **Sin deadlocks**: Orden de adquisición fijo: historial → streaming → tools.

- **Sefirot**: תפארת Tiféret (integridad del procesamiento)
- **Estado**: ✅ IMPLEMENTADO (FP-022 — _historial_lock + _streaming_lock en nlu.py)

---

### RF-64: Bereshit Resiliente — בראשית חזק (FP-022 T1-4)

**Descripción**: El proceso de arranque Bereshit tiene timeout de 30s. Si falla, el Computadora despierta en modo degradado.

**Requisitos funcionales**:
1. **Timeout 30s**: Si `_animacion_bereshit` no completa en 30 segundos, se aborta.
2. **Modo degradado**: Tras timeout, Computadora entra en estado `"dormido"` con log de advertencia.
3. **Wake manual**: Si Bereshit falla, el usuario puede despertar al Computadora con wake word.
4. **Sin cuelgue infinito**: Eliminación de cualquier bucle infinito en el proceso de arranque.

- **Sefirot**: מלכות Maljut (resiliencia del trono)
- **Estado**: ✅ IMPLEMENTADO (FP-020 — _animacion_bereshit con timer y _bereshit_total_pasos=75)

---

### RF-65: FSM Formal Maljut — מכונת מצבים (FP-022 T1-1)

**Descripción**: Reemplazo de strings ad-hoc de estado por una máquina de estados finita formal con Enum y tabla de transiciones.

**Requisitos funcionales**:
1. **Enum EstadoMaljut**: `dormido`, `escuchando`, `procesando`, `hablando`, `error`, `bereshit`, `tzimtzum`, `gevura_activa`.
2. **Tabla de transiciones**: Diccionario `{(estado_actual, evento): estado_nuevo}` con transiciones válidas.
3. **Acciones entry/exit**: Cada transición puede tener acciones de entrada y salida.
4. **Transición inválida → log**: Si se intenta una transición no definida, se logea warning pero NO crashea.
5. **`cambiar_estado()` refactorizado**: Usa la tabla de transiciones en vez de asignación directa.

- **Sefirot**: מלכות Maljut (estructura formal del trono)
- **Estado**: ✅ IMPLEMENTADO (FP-027 WI-155 — fsm_computadora.py con 13 estados + tabla TRANSICIONES_VALIDAS)

---

### RF-66: Watchdog Multi-etapa — שומר (FP-022 T1-2)

**Descripción**: Monitor de salud que vigila Ollama, TTS, micrófono y Whisper con 3 etapas de escalación.

**Requisitos funcionales**:
1. **Etapa 1 (5s)**: Retry silencioso del servicio caído.
2. **Etapa 2 (15s)**: Notificación al usuario + activación de fallback.
3. **Etapa 3 (60s)**: Degradación graceful — deshabilitar el servicio y operar sin él.
4. **Circuit Breaker**: Patrón Closed→Open→Half-Open para cada servicio monitoreado.
5. **Heartbeat**: Ping periódico (10s) a cada servicio para detectar muertes silenciosas.
6. **Módulo nuevo**: `computadora/interfaz/watchdog.py` con clase `WatchdogComputadora`.

- **Sefirot**: מלכות Maljut (protección del trono), תפארת Tiféret (coordinación)
- **Estado**: ✅ IMPLEMENTADO (FP-022 WI-107 — watchdog.py con circuit breaker + 4 etapas)

---

### RF-67: Canal Bidireccional Tiféret↔Maljut — ערוץ דו-כיווני (FP-022 T2-1)

**Descripción**: Señales nuevas de Tiféret→Maljut para comunicar confianza, complejidad y frustración detectada.

**Requisitos funcionales**:
1. **Signal `confianza_respuesta`**: Float 0.0-1.0 indicando confianza del NLU en su respuesta.
2. **Signal `complejidad_procesamiento`**: Nivel 1-3 indicando carga cognitiva actual.
3. **Signal `frustracion_detectada`**: Bool cuando se detecta frustración del usuario (repeticiones, "no entiendes").
4. **Maljut reacciona**: Colores del orbe reflejan confianza (verde→amarillo→rojo), pulsación refleja complejidad.

- **Sefirot**: תפארת Tiféret (emisor), מלכות Maljut (receptor)
- **Sendero nuevo**: Tiféret→Maljut (canal de retroalimentación cognitiva)
- **Estado**: ✅ IMPLEMENTADO (FP-022 WI-102 — 3 signals en HiloPensamiento)

---

### RF-68: Ruaj Reactivo a Fallos — רוח תגובתי (FP-022 T2-2)

**Descripción**: El sistema emocional Ruaj reacciona a fallos técnicos y frustración del usuario.

**Requisitos funcionales**:
1. **Fallo de herramienta → preocupado**: Cuando una tool falla, el humor primario transiciona a "preocupado".
2. **Frustración usuario → empático**: Cuando se detecta frustración (RF-67), humor transiciona a "sereno" vía empatía.
3. **Éxito tras fallo → contento**: Si la siguiente operación tras un fallo es exitosa, humor va a "contento".
4. **Método nuevo en Personalidad**: `registrar_fallo_tecnico(tipo, detalle)` y `registrar_frustracion_usuario()`.

- **Sefirot**: נצח Netzaj (Ruaj emocional), תפארת Tiféret (detector)
- **Estado**: ✅ IMPLEMENTADO (FP-022 WI-103 — registrar_fallo_tecnico + registrar_frustracion_usuario en personalidad.py)

---

### RF-69: Da'at Routing Circadiano — דעת נתיב (FP-022 T2-3)

**Descripción**: La fase circadiana influye en el routing N1→N2→N3, priorizando respuestas rápidas en fase de descanso.

**Requisitos funcionales**:
1. **Fase `descanso_guardian`**: Umbral de complejidad N1→N2 baja (más cosas se resuelven con regex).
2. **Fase `activo`**: Umbral normal, routing estándar.
3. **Fase `transición`**: Umbral intermedio.
4. **Integración en `pensar()`**: Consultar `CicloCircadiano.obtener_fase_actual()` antes de decidir nivel.

- **Sefirot**: דעת Da'at (percepción circadiana), תפארת Tiféret (routing)
- **Sendero reforzado**: Da'at→Tiféret (fase circadiana modula routing)
- **Estado**: ✅ IMPLEMENTADO (pensar() en nlu.py — urgencia detectada con regex, fase descanso bloquea N2 salvo urgencias, transición logueada)

---

### RF-70: Auto-diagnóstico Verbal — רפואה עצמית (FP-022 T3-1)

**Descripción**: El Computadora responde "¿cómo te sientes?" con estado real del sistema (CPU, RAM, servicios, humor).

**Requisitos funcionales**:
1. **Regex N1**: Detecta "cómo te sientes", "cómo estás", "estás bien", "todo bien" como auto-diagnóstico.
2. **Respuesta real**: Incluye CPU%, RAM%, estado Ollama/TTS/mic, humor actual, fase circadiana.
3. **Tono acorde al humor**: Si está "cansado", responde cansadamente. Si "contento", enérgicamente.
4. **Sin LLM**: Respuesta generada 100% por código (N1), no requiere Ollama.

- **Sefirot**: תפארת Tiféret (autoconciencia), מלכות Maljut (comunicación)
- **Estado**: ✅ IMPLEMENTADO (FP-022 WI-106 — _autodiagnostico en nlu.py con datos reales del sistema)

---

### RF-71: Bandeja del Sistema Enriquecida — מגש (FP-022 T3-3)

**Descripción**: Icono en la bandeja del sistema con menú contextual rico: estado, pausa/resume, diagnóstico, config.

**Requisitos funcionales**:
1. **QSystemTrayIcon**: Creación real del icono en bandeja (ya importado pero no instanciado).
2. **Menú contextual**: Pausa/Resume escucha, Estado del sistema, Abrir diagnóstico, Configuración, Salir.
3. **Colores de estado**: Icono cambia color según estado del watchdog (verde=OK, amarillo=degradado, rojo=fallo).
4. **Tooltip dinámico**: Muestra estado actual del Computadora + humor.

- **Sefirot**: מלכות Maljut (interfaz con el mundo)
- **Estado**: ✅ IMPLEMENTADO (FP-022 — QSystemTrayIcon con menú contextual en ventana_principal.py)

---

### RF-72: Multi-monitor Inteligente — מסכים (FP-022 T3-2)

**Descripción**: VidaAutonoma detecta y usa múltiples monitores, con heatmap independiente por pantalla.

**Requisitos funcionales**:
1. **Detección**: `QApplication.screens()` en vez de `primaryScreen()`.
2. **Heatmap por pantalla**: Cada monitor tiene su propio mapa de calor de posiciones de ventanas.
3. **Migración**: El orbe puede migrar entre pantallas cuando el usuario cambia su foco de trabajo.
4. **Vagabundeo cross-screen**: El orbe puede recorrer bordes entre pantallas durante vagabundeo.

- **Sefirot**: מלכות Maljut (presencia multi-dimensional)
- **Estado**: ✅ IMPLEMENTADO (FP-022 WI-108 — QApplication.screens() en vida_autonoma.py)

---

### RF-73: Detector de Ciclos en Tool-Use — התחדשות (FP-023 T1-1)

**Descripción**: Detectar y romper loops infinitos de tool-calls cuando Ollama invoca la misma herramienta con los mismos args repetidamente (Hit'hadshut — renovación, no repetición).

**Requisitos funcionales**:
1. **Cycle detection**: Set de `(tool_name, args_hash)` por turno. Si se repite → break.
2. **Budget enforcement**: MAX_TOOL_CALLS ya existe (10), pero ahora con detección de ciclos.
3. **Graceful exit**: Respuesta de error natural al usuario cuando se detecta un loop.

- **Sefirot**: תפארת Tiféret (pensamiento equilibrado)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-109 — _invocaciones_turno set en nlu.py)

---

### RF-74: Lock de Estado Maljut — אור חדש (FP-023 T1-2)

**Descripción**: Proteger mutación de `_estado` con threading.Lock para evitar race conditions entre hilos. Ohr Jadash — nueva energía limpia en cada transición.

**Requisitos funcionales**:
1. **Lock**: `threading.Lock()` protege toda lectura/escritura de `_estado`.
2. **Punto único de mutación**: Solo `cambiar_estado()` puede mutar `_estado`.

- **Sefirot**: מלכות Maljut (estabilidad del trono)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-110 — _estado_lock en ventana_principal.py)

---

### RF-75: Escritura Atómica de Personalidad — תיקון (FP-023 T1-3)

**Descripción**: Prevenir corrupción de JSON de personalidad ante crash usando tempfile + os.replace (Tikún — reparación del archivo dañado nunca ocurre).

**Requisitos funcionales**:
1. **Atomic write**: NamedTemporaryFile → write → flush → os.replace.
2. **Same directory**: Temp file en el mismo directorio que PERSONA_PATH para garantizar atomicidad en Windows.
3. **Fallback**: Si os.replace falla, intentar shutil.move.

- **Sefirot**: נצח Netzaj (persistencia emocional segura)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-111 — tempfile.mkstemp + os.replace en personalidad.py)

---

### RF-76: Límite de Buffer de Audio — גבול (FP-023 T1-4)

**Descripción**: Prevenir memory leak en audio_chunks usando deque con maxlen y liberación explícita post-transcripción.

**Requisitos funcionales**:
1. **Bounded buffer**: `collections.deque(maxlen=MAX_AUDIO_CHUNKS)` — máximo ~120 chunks (~60s a 0.5s/chunk).
2. **Explicit cleanup**: `del audio` después de transcripción.

- **Sefirot**: חכמה Jojmá (oído limitado y sabio)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-112 — deque(maxlen=120) en escucha.py)

---

### RF-77: Profundidad Máxima en Grafo Emocional — עץ החיים (FP-023 T1-5)

**Descripción**: Prevenir loops infinitos en `_transicionar_humor()` con depth limit. En el Árbol de la Vida, cada interacción entre Sefirot es un proceso de actualización de equilibrio — pero con profundidad finita.

**Requisitos funcionales**:
1. **max_depth=5**: Parámetro `_depth` en `_transicionar_humor()`.
2. **Fallback**: Si depth excedido → forzar "neutral" + log warning.

- **Sefirot**: נצח Netzaj (emociones equilibradas)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-113 — _depth limit en _transicionar_humor)

---

### RF-78: Logging de Excepciones en Watchdog — שומר (FP-023 T1-6)

**Descripción**: Cambiar `except Exception:` por `except Exception as e: logger.exception(...)` en watchdog.py para registro completo.

- **Sefirot**: מלכות Maljut (observabilidad)
- **Estado**: ✅ IMPLEMENTADO (4/4 except blocks en watchdog.py usan logger.exception)

---

### RF-79: Heartbeat Ollama Pre-llamada — לב (FP-023 T1-7)

**Descripción**: Verificar que Ollama responde ANTES de cada llamada N2, no solo al inicio. Si falla → degradación graciosa a N1.

**Requisitos funcionales**:
1. **Quick ping**: GET /api/tags con timeout=2s antes de llamar _llamar_ollama.
2. **Graceful degradation**: Si ping falla → marcar ollama_disponible=False → responder con N1.
3. **Auto-recover**: Si watchdog detecta que Ollama volvió → desmarcar.

- **Sefirot**: תפארת Tiféret (corazón latiente)
- **Estado**: ✅ IMPLEMENTADO (FP-023 WI-115 — _quick_ping_ollama en nlu.py)

---

### RF-80: Timeouts Adaptativos en Config — זמן (FP-023 T1-8)

**Descripción**: Centralizar timeouts en config.py y hacer que el timeout de Ollama se adapte a la latencia promedio real.

**Requisitos funcionales**:
1. **Config central**: `TIMEOUT_OLLAMA`, `TIMEOUT_WHISPER`, `TIMEOUT_COMANDO` en config.py.
2. **Adaptive**: Media de últimas 5 latencias Ollama × 2 como timeout dinámico (mín 30s, máx 180s).

- **Sefirot**: תפארת Tiféret (tiempo calibrado)
- **Estado**: ✅ IMPLEMENTADO (TIMEOUT_OLLAMA_*, _timeout_adaptativo() en config.py)

---

### RF-81: Hardening de Command Injection — גבורה (FP-023 T2-1)

**Descripción**: Reforzar protección contra inyección de comandos en sistema.py y herramientas.py. Gevurá — juicio estricto sobre comandos.

**Requisitos funcionales**:
1. **sistema.py**: Migrar abrir_aplicacion() a shell=False con shlex.split donde sea posible.
2. **herramientas.py**: Sanitizar metacaracteres shell (`;`, `&&`, `||`, backticks) en input del LLM.
3. **COMANDOS_BLOQUEADOS**: Ampliar regex con patrones de bypass conocidos.

- **Sefirot**: גבורה Gevurá (juicio de seguridad)
- **Estado**: ✅ IMPLEMENTADO (COMANDOS_BLOQUEADOS ampliado con 15+ patrones, abrir_aplicacion() migrado a os.startfile/shell=False)

---

### RF-82: Hard Cap de Tokens en Historial — זכרון (FP-023 T2-2)

**Descripción**: Además del cap por mensajes (80), añadir cap por tokens (~4000) para prevenir prompts gigantes que saturen contexto.

- **Sefirot**: תפארת Tiféret (memoria eficiente)
- **Estado**: ✅ IMPLEMENTADO (_MAX_TOKENS_HISTORIAL=4000, _truncar_historial_impl en nlu.py)

---

### RF-83: Guard de Escritura Concurrente en Personalidad — שמירה (FP-023 T2-3)

**Descripción**: threading.Lock alrededor de guardar() en personalidad.py para evitar escrituras concurrentes.

- **Sefirot**: נצח Netzaj (persistencia segura)
- **Estado**: ✅ IMPLEMENTADO (threading.Lock en personalidad.py guardar())

---

### RF-84: Health Checks Profundos en Watchdog — בדיקה (FP-023 T2-4)

**Descripción**: En _check_ollama(), además de HTTP GET, enviar prompt dummy para verificar que el modelo responde.

- **Sefirot**: מלכות Maljut (verificación profunda)
- **Estado**: ✅ IMPLEMENTADO (_check_ollama() en watchdog.py hace prompt-based deep check)

---

### RF-85: Protección ReDoS — מגן (FP-023 T2-5)

**Descripción**: Wrapper de regex críticos con timeout para prevenir catastrophic backtracking.

- **Sefirot**: תפארת Tiféret (protección de pensamiento)
- **Estado**: ✅ IMPLEMENTADO (regex_safe() en parseo_herramientas.py, anti-ReDoS en nivel1_aprendido.py)

---

### RF-86: Auto-actualización de Dependencias — התחדשות (FP-023 T2-6)

**Descripción**: Hit'hadshut — renovación constante del sistema. Computadora puede verificar y actualizar automáticamente sus dependencias críticas (Ollama, Python packages, Whisper models).

**Requisitos funcionales**:
1. **Version check**: Verificar versiones instaladas de Ollama, pip packages, y modelos Whisper.
2. **Auto-update**: Ejecutar actualizaciones con confirmación del usuario (voz o tray).
3. **Ollama models**: `ollama pull` para actualizar modelos.
4. **pip packages**: `pip install --upgrade` para dependencias Python.
5. **Rollback tracking**: Log de versiones antes/después de cada actualización.
6. **Scheduling**: Verificación periódica (1x al día) o por comando de voz.

- **Sefirot**: יסוד Yesod (fundamento actualizado)
- **Estado**: ✅ IMPLEMENTADO (computadora/habilidades/auto_update.py — verificar_ollama, verificar_pip_packages, actualizar_modelo, log persistente)

---

### RF-87: Física de Partículas con Inercia — פיזיקה (FP-024 Pilar A)

**Descripción**: Las partículas del orbe ganan vectores de velocidad (vx, vy), masa y coeficientes de arrastre/retorno. Reaccionan al movimiento del orbe con inercia, spring-back y arrastre viscoso.

**Requisitos funcionales**:
1. **Masa variable**: Cada partícula tiene masa (0.5-2.0). Letras hebreas = masa alta (2.0), puntos = masa baja (0.5).
2. **Inercia**: Cuando el orbe se mueve, partículas se retrasan proporcionalmente a su masa.
3. **Spring-back**: Fuerza restauradora que devuelve partículas a su órbita original (coef_retorno=0.03).
4. **Arrastre viscoso**: Decaimiento de velocidad por frame (coef_arrastre=0.92).
5. **Compatibilidad**: La atracción gravitacional al cursor existente (`_proximidad * 0.015`) se preserva intacta.
6. **Performance**: <0.1% CPU adicional con 50 partículas a 30fps.

- **Sefirot**: מלכות Malkuth (interfaz visual)
- **Estado**: ✅ IMPLEMENTADO (Particula con vx, vy, masa, coef_arrastre=0.92, coef_retorno=0.03, actualizar(dx,dy))

### RF-88: Evolución Alquímica Visual — אלכימיה (FP-024 Pilar B)

**Descripción**: Sistema de progresión visual a largo plazo basado en 4 etapas definidas; la paleta visual del UI evoluciona con el uso acumulado.

**Requisitos funcionales**:
1. **4 etapas**: Nigredo (negro) → Albedo (plata) → Citrinitas (oro) → Rubedo (rojo-púrpura).
2. **Condiciones de transición**: Basadas en horas de uso acumuladas + interacciones totales + tareas exitosas.
3. **Jerarquía de colores**: La paleta alquímica solo aplica en idle/dormido. `COLORES_NIVEL`, `_colores_categoria` y estados FSM tienen prioridad absoluta.
4. **Transición gradual**: Lerp de colores durante ~60s al cambiar de etapa, sin cambios bruscos.
5. **Persistencia**: Estado en `datos/evolucion_computadora.json` con historial de transiciones.
6. **No afecta funcionalidad**: Es puramente visual y narrativo.

- **Sefirot**: מלכות Malkuth + נצח Netzaj (estética + persistencia)
- **Estado**: ✅ IMPLEMENTADO (EtapaAlquimica enum, _PALETAS_ALQUIMICAS, _evaluar_evolucion(), datos/evolucion_computadora.json, lerp 60s)

### RF-89: Conciencia Temporal — זמן חי (FP-024 Pilar C)

**Descripción**: Computadora registra timestamps de activación/desactivación para conocer su tiempo activo real, no solo días calendario.

**Requisitos funcionales**:
1. **Registro de sesiones**: Cada activación/desactivación se guarda en `datos/consciencia_temporal.json`.
2. **Uptime real**: Método `calcular_tiempo_activo()` retorna horas reales de actividad.
3. **Inyección en prompt**: SISTEMA_PROMPT incluye: "Llevas Xh activo en Y sesiones. Primera activación: Z."
4. **Cierre limpio**: `atexit` + signal handler para registrar desactivación incluso en crash.
5. **Privacidad**: Solo timestamps, no contenido de sesiones.

- **Sefirot**: נצח Netzaj (persistencia temporal)
- **Estado**: ✅ IMPLEMENTADO (registrar_activacion/desactivacion, calcular_tiempo_activo en memoria.py)

### RF-90: Datos de Evolución para Etapas Alquímicas — מעקב (FP-024 Pilar B soporte)

**Descripción**: Contadores persistentes para evaluar progresión alquímica: horas de uso, interacciones totales, habilidades exitosas.

**Requisitos funcionales**:
1. **Contadores incrementales**: Se actualizan en cada interacción y al cerrar.
2. **Vinculación con conciencia temporal**: Horas de uso provienen de RF-89.
3. **Criterios de transición**: Nigredo→Albedo (24h+50 interacciones), Albedo→Citrinitas (168h+500), Citrinitas→Rubedo (720h+2000).

- **Sefirot**: נצח Netzaj (memoria evolutiva)
- **Estado**: ✅ IMPLEMENTADO (_EVOLUCION_PATH, contadores en ventana_principal.py, _registrar_interaccion_alquimica)

### RF-91: Logging Complementario en Memoria — תיעוד (FP-024 Pilar D residual)

**Descripción**: Agregar logging mínimo a funciones de `memoria.py` que carecen de observabilidad.

**Requisitos funcionales**:
1. `add_memory()`: `logger.debug()` con role y longitud de texto.
2. `buscar_en_memoria()`: `logger.debug()` con consulta y cantidad de resultados.
3. `compress_day()`: `logger.info()` con fecha y resultado.

- **Sefirot**: נצח Netzaj (observabilidad)
- **Estado**: ✅ IMPLEMENTADO (logger.debug/info en add_memory, buscar_en_memoria, compress_day)

---

### RF-92: חלון חי Jalon Jai — Ventana Dinámica por Inercia de Partículas (FP-025)

**Descripción**: Expandir dinámicamente la ventana del orbe para contener la estela completa de partículas cuando estas se desplazan por inercia (movimiento autónomo o arrastre del usuario), y contraerla cuando regresan a órbita.

**Requisitos funcionales**:
1. Cada frame, calcular el bounding box real de todas las partículas activas (`max(hypot(pos.x, pos.y))`).
2. Si el radio de partículas excede el radio visual basado en `_escala`, expandir la ventana para acomodarlas.
3. Contracción automática cuando las partículas regresan a órbita (spring-back).
4. Clamp de posición de ventana a `screen.availableGeometry()` para evitar desborde en esquinas.

- **Sefirot**: מלכות Maljut (manifestación visual)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-93: חי עדכון Jai Idkún — Hot-Reload de Código en Vivo (FP-028)

**Descripción**: Computadora detecta cambios en sus archivos `.py` y recarga los módulos afectados sin reiniciar la aplicación completa, preservando estado crítico (modelo Whisper en VRAM, historial, colas).

**Requisitos funcionales**:
1. `QFileSystemWatcher` monitorea todos los archivos `computadora/**/*.py` en tiempo real.
2. Clasificador de capas: determina si el cambio afecta Cerebro, Voz, Habilidades, Interfaz o Memoria.
3. Recarga por capa: detiene hilos afectados → `importlib.reload()` → recrea instancias → reconecta señales PyQt.
4. Registro central de señales (`_signal_registry`) para reconexión automática post-reload.
5. Capa Interfaz: si cambia `ventana_principal.py` u `orbe_computadora.py`, notifica al usuario que requiere reinicio manual.
6. Logging de cada recarga: módulo, capa, duración, resultado (éxito/error).
7. En caso de error durante reload, loguear y NO crashear — Computadora sigue con la versión anterior del módulo.

- **Sefirot**: כתר Keter (auto-renovación), מלכות Maljut (interfaz/watchdog)
- **Estado**: ✅ IMPLEMENTADO (hot_reload.py + integración en ventana_principal.py + recrear_cerebro en orquestador.py)

---

### RF-94: פֶּה הַגּוֹלֶם Peh HaComputadora — Comandos de Voz para Todos los RFs (FP-029)

**Descripción**: Cada requisito funcional del Computadora es invocable por voz natural en N1 (Néfesh, instantáneo, sin LLM). El usuario puede pedir cualquier funcionalidad en lenguaje coloquial, formal o imperativo y N1 la detecta vía regex flexible.

**Requisitos funcionales**:
1. Agregar bloques regex en `_pensar_nivel1()` para cada RF que aún no tiene detección directa en N1.
2. Cada RF cubierto debe tener mínimo 3 formas naturales de invocación (coloquial, formal, imperativa).
3. Los nuevos regex se insertan AL FINAL de `_pensar_nivel1()`, DESPUÉS de los patrones Lemed (FP-015) para respetar prioridad.
4. RFs cubiertos: evolución alquímica, monitor sistema, personalidad/rasgos, RAM propia, procesos anómalos, autodiagnóstico, bienestar, ética, FSM estados, watchdog servicios, fallos aprendidos, minimizar a bandeja, ajuste umbral voz.
5. Todo se ejecuta en N1 (orbe verde, instantáneo, local).
6. No se modifican ni rompen regex existentes.

- **Sefirot**: תפארת Tiféret (nlu.py), הוד Hod (percepción verbal ampliada)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-95: תַּפְרִיט הַגּוֹלֶם Tafrit HaComputadora — Menú Contextual Minimalista (FP-030)

**Descripción**: El menú de clic derecho del orbe se reduce a exactamente 3 opciones significativas: registro de voz del amo, reset total (Gilgul), y cerrar.

**Requisitos funcionales**:
1. Menú contextual con exactamente 3 items:
   - **Kabbalah be-peh (קַבָּלָה בְּפֶה — Registrar muestra)** — Registrar muestra de voz del propietario (`_trigger_owner_enroll()`).
   - **Gilgul (גִּלְגּוּל — Reiniciar todos los recuerdos y preferencias)** — Reiniciar todos los recuerdos y preferencias (reencarnación). Requiere doble confirmación.
   - **בטל אֱמֶת — Borrar la Palabra** — Cerrar Computadora (`forzar_cierre()`).
2. Gilgul borra: personalidad.json, computadora_personas.json, owner_profile.json, consciencia_temporal.json, evolucion_computadora.json, errores_aprendidos.json, heatmap_pantalla.json, nivel1_patrones.json, perfil_amo.json, tareas.json, tareas_diferidas.json, recordatorios.json, memoria/ completo, permisos_log.jsonl.
3. Gilgul NO borra: config.toml, stats_uso.json, código fuente, logs.
4. Gilgul requiere doble confirmación (diálogo "Al Gilgul se pierden TODOS los recuerdos. ¿Estás seguro?").
5. Después del Gilgul, Computadora se reinicia automáticamente (renace en Nigredo).
6. Se loguea el evento de Gilgul ANTES de borrar datos.

- **Sefirot**: מלכות Maljut (ventana_principal.py), נצח Netzaj (memoria borrada)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-96: נִשְׁמַת הַגּוֹלֶם Nishmat HaComputadora — Higiene de Excepciones (FP-031)

**Descripción**: Todos los bloques `except Exception` en módulos críticos (escucha.py, nlu.py, ventana_principal.py) reemplazan el silencio (`pass` / vacío) por logging estructurado con `logger.exception()`. El Computadora ya no muere en silencio: cada error se reporta.

**Requisitos funcionales**:
1. Cada bloque `except Exception:` (bare) en escucha.py, nlu.py y ventana_principal.py DEBE loggear el error con `logger.exception("contexto descriptivo")`.
2. Donde sea identificable el tipo específico de excepción, usar el tipo concreto (ValueError, OSError, RuntimeError, etc.) en lugar de `Exception`.
3. Los bloques que ya capturan `as e` pero no loggean, deben agregar `logger.exception()`.
4. Se usa `from loguru import logger` (infraestructura existente del proyecto).
5. NO se modifica la lógica de flujo — solo se agrega la llamada de logging.
6. Método huérfano `_delete_owner_profile()` en ventana_principal.py se elimina (código muerto post-FP-030). `_show_owner_profile()` se conserva — tiene referencia activa en nlu.py.

- **Sefirot**: חסד Jesed (escucha.py), תפארת Tiféret (nlu.py), מלכות Maljut (ventana_principal.py), יסוד Yesod (logs.py — infraestructura)
- **Estado**: ✅ IMPLEMENTADO

### RF-97: מָגֵן דָּוִד Maguén David — Escudo de Seguridad de Comandos (FP-034)

**Descripción**: Reemplazo de `shell=True` + blocklist por `shell=False` + allowlist en toda la ejecución de comandos del Computadora. Nuevo módulo `computadora/habilidades/comando_seguro.py` con validación estructurada de argumentos y allowlist explícita. Elimina la vulnerabilidad OWASP #1 (OS Command Injection) que permitía inyección via pipes, `cmd /c`, y expansión de variables.

**Requisitos funcionales**:
1. `ejecutar_comando()` en herramientas.py DEBE delegar a `ejecutar_comando_seguro()` (comando_seguro.py) que usa `shell=False` + `shlex.split()`.
2. `ejecutar_comando_sistema()` DEBE delegar a `ejecutar_comando_sistema_seguro()` con allowlist de ~15 comandos info-safe.
3. Argumentos con metacaracteres de shell (`;&|`$(){}<>[]!^`) DEBEN ser rechazados.
4. PowerShell cmdlets read-only se ejecutan via `["powershell", "-NoProfile", "-Command", ...]` con `shell=False`.
5. Regex de comandos peligrosos como barrera final en AMBAS funciones.
6. Todos los comandos truncan salida a 4000 chars y tienen timeout de 15s.

- **Sefirot**: גבורה Guevurá (seguridad), מלכות Maljut (herramientas N1)
- **Estado**: ✅ IMPLEMENTADO

### RF-98: תְּשׁוּבָה Teshuvá — Corrección de Bugs Latentes (FP-035)

**Descripción**: Corrección de 4 bugs silenciosos descubiertos en Nigredo: (1) `_ollama_ocupado` bare bool sin thread-safety reemplazado por `OllamaGuard` con `threading.Event` + auto-reset 120s, (2) `sys.exit(1)` sin guard `__name__` en test files corregido, (3) Variable `emb` usada antes de asignarse en wake word path de escucha.py movida arriba, (4) `on_permiso_copilot` inexistente corregido a `solicitar_permiso_copilot`.

**Requisitos funcionales**:
1. `OllamaGuard` en watchdog.py provee flag thread-safe con auto-reset a 120s (evita flag stuck si NLU crashea).
2. `_llamar_ollama()` y `_llamar_ollama_streaming()` usan `with ollama_guard:` como context manager.
3. `test_fp023_tikun.py` y `test_fp021_phase1.py` tienen `sys.exit()` dentro de `if __name__ == "__main__":`.
4. En `_transcribir()` de escucha.py, `emb = self._extraer_embedding(audio, self._fs)` se ejecuta ANTES de los checks de wake word (nombre completo y apellido necesitan `emb`).
5. En `_evaluar_etica()` de nlu.py, la condición de escalación usa `self.solicitar_permiso_copilot` (attribute que existe en `__init__`).

- **Sefirot**: הוד Hod (watchdog), תפארת Tiféret (NLU), יסוד Yesod (escucha)
- **Estado**: ✅ IMPLEMENTADO

### RF-99: טָהֳרַת הַקּוֹד Tohorat HaCode — Purificación del Código (FP-036)

**Descripción**: Limpieza post-Nigredo: (1) eliminar 6 definiciones muertas en herramientas.py (COMANDOS_BLOQUEADOS, COMANDOS_SISTEMA_INFO, _PING_RE, _SHELL_METACHAR_RE, _sanitizar_comando, _es_comando_sistema_permitido) dejadas por FP-034, (2) agregar logger a 3 except silenciosos en habla.py y 3 en __main__.py, (3) agregar threading.Lock a 4 singletons lazy-init (herramientas._gestor_permisos, sistema._callback_recordatorio, monitor_sistema._monitor_global, copilot_api._instancia), (4) eliminar BLOQUE 2 obsoleto de test_srs_coherencia.py (~210 líneas de tests hardcodeados que ya no reflejan la realidad), (5) documentar shell=True en sistema.py con referencia OWASP A03:2021.

**Requisitos funcionales**:
1. herramientas.py NO debe contener COMANDOS_BLOQUEADOS, COMANDOS_SISTEMA_INFO, _PING_RE, _SHELL_METACHAR_RE, _sanitizar_comando(), _es_comando_sistema_permitido() — todo vive en comando_seguro.py.
2. habla.py: los 3 `except Exception: pass` en _calcular_audio_adaptativo() e interrumpir() deben tener `logger.debug()`.
3. __main__.py: los 3 `except Exception: pass` en _kill_previous_computadora_instances() deben tener logging minimal.
4. Los 4 singletons lazy-init deben usar `threading.Lock()` para prevenir race conditions en init concurrente.
5. test_srs_coherencia.py BLOQUE 2 (L236-445) eliminado completamente.
6. sistema.py L111: comentario ampliado con referencia OWASP A03:2021 (Injection).

- **Sefirot**: יסוד Yesod (herramientas), הוד Hod (habla), כתר Keter (boot), גבורה Gevurá (permisos), תפארת Tiféret (copilot_api)
- **Estado**: ✅ IMPLEMENTADO

### RF-100: כְּתִיבָה אָטוֹמִית Ketivá Atomit — Escritura Atómica de Datos (FP-037)

**Descripción**: Reemplazar todas las escrituras JSON no-atómicas (`path.write_text(json.dumps(...))`) por el patrón seguro `tempfile.mkstemp() + os.replace()` ya existente en personalidad.py. Previene corrupción de datos si Computadora crashea mid-write.

**Requisitos funcionales**:
1. Toda escritura a archivos JSON persistentes DEBE usar el patrón atómico: `tempfile.mkstemp()` → escribir → `os.replace()`.
2. El patrón ya implementado en personalidad.py es la referencia canónica.
3. Módulos afectados incluyen: ventana_principal.py (evolucion_computadora.json), auto_update.py, modelo_discovery.py, vida_autonoma.py, baseline_sistema.py, y otros con `.write_text(json.dumps(...))`.
4. NO cambiar la lógica de negocio — solo el mecanismo de escritura a disco.

- **Sefirot**: Cross-cutting (מלכות Maljut, כתר Keter, בינה Biná, חסד Jesed, y otros)
- **Estado**: ✅ IMPLEMENTADO

### RF-101: נְעִילַת יְחִידִים Ne'ilat Yejidim — Bloqueo de Singletons Restantes (FP-038)

**Descripción**: Completar el patrón de thread-safety en los 3 singletons lazy-init que quedaron sin Lock después de FP-036: `obtener_bus()` en eventos.py, `inicializar_ciclo()` en ciclo_circadiano.py, y `start_daily_compressor()` en memoria.py.

**Requisitos funcionales**:
1. `eventos.py`: `obtener_bus()` debe usar `threading.Lock()` con double-checked locking.
2. `ciclo_circadiano.py`: `inicializar_ciclo()` debe usar `threading.Lock()` con double-checked locking.
3. `memoria.py`: `start_daily_compressor()` debe usar `threading.Lock()` en el check+set del daemon thread.

- **Sefirot**: יסוד Yesod (eventos), דעת Da'at (ciclo_circadiano), נצח Netzaj (memoria)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-102: שְׁמִיעָה גְבוּרָה Shemiá Gevurá — Permiso por Voz Funcional (FP-039)

**Descripción**: Corregir el sistema de permisos Gevurá que estaba 100% roto: `_on_solicitar_permiso` polleaba un atributo `_ultima_transcripcion_raw` que no existe en escucha.py, causando timeout automático en TODA petición de permiso. Además, eliminar warnings FSM redundantes procesando→procesando.

**Requisitos funcionales**:
1. `_on_solicitar_permiso` debe usar `threading.Event` + `_esperando_confirmacion` de escucha.py para recibir la respuesta del usuario via signal `texto_detectado`.
2. El timeout de 15s debe contar DESPUÉS de emitir la pregunta, no antes.
3. Al salir siempre debe desconectar el signal y resetear `_esperando_confirmacion = False`.
4. Guards FSM: no invocar `cambiar_estado("procesando")` si ya está en "procesando".

- **Sefirot**: מלכות Maljut (ventana_principal) ↔ הוד Hod (escucha) ↔ גבורה Gevurá (permisos)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-104: פְּקוּדָה יְשִׁירָה Pekudá Yeshirá — Orden Directa Auto-Aprueba (FP-042 Parte A)

**Descripción**: Cuando el usuario da una orden directa ("abre mi explorador", "sube el volumen"), Gevurá no debe preguntar permiso para herramientas de nivel "accion". Solo "admin" sigue requiriendo confirmación explícita.

**Requisitos funcionales**:
1. `ejecutar_herramienta` acepta `orden_directa=True` (keyword-only).
2. `GestorPermisos.solicitar` acepta `orden_directa=True` (keyword-only).
3. Si `orden_directa=True` y `nivel=="accion"` → auto-aprobado sin UI.
4. Si `nivel=="admin"` → SIEMPRE requiere confirmación (independiente de orden_directa).
5. Todas las llamadas N1 y N2 en `nlu.py` pasan `orden_directa=True`.
6. Log inmutable registra `"auto_aprobado_orden_directa"` como resultado.

- **Sefirot**: גבורה Gevurá (permisos) ↔ תפארת Tiféret (NLU) ↔ מלכות Maljut (herramientas)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-105: תִּקּוּן אִינֶרצְיָה Tikún Inertzia — Restauración de Inercia de Partículas (FP-042 Parte B)

**Descripción**: HF-028 suprimió completamente el delta de inercia (`dx,dy=0.0,0.0`) durante drag e impulso, matando el efecto visual FP-024 RF-87. El fix restaura inercia amortiguada al 40% y corrige un micro-kick en snap final de movimiento autónomo.

**Requisitos funcionales**:
1. Durante drag/impulso, las partículas reciben 40% del delta real (no 0%).
2. El snap final de `_interpolar_movimiento` sincroniza `_pos_anterior` antes de return.
3. El coeficiente de amortiguación es 0.4 (configurable si se ajusta en el futuro).

- **Sefirot**: מלכות Maljut (ventana_principal — partículas) ↔ יסוד Yesod (vida_autonoma)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-106: מַרְאֵה הַמַּלְכוּת Mar'é HaMaljut — Demo Visual Completa (FP-043 Parte A)

**Descripción**: Comando de voz N1 ("enséñame tu maljut", "hazme una demo", etc.) que ejecuta una coreografía visual de ~45 segundos mostrando todos los estados FSM, paletas alquímicas, colores de nivel cerebral, animaciones e interacciones del orbe.

**Requisitos funcionales**:
1. Regex `_RE_DEMO_MALJUT` detecta variantes del comando demo en nivel 1.
2. Handler retorna token `__DEMO_MALJUT__` interceptado en `ventana_principal.py`.
3. Coreografía recorre 13 pasos encadenados con `QTimer.singleShot`.
4. Al finalizar, restaura estado y paleta original del orbe.
5. Flag `_demo_en_curso` previene interferencia durante la coreografía.

- **Sefirot**: תפארת Tiféret (NLU regex N1) → מלכות Maljut (ventana_principal coreografía)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-107: תִּקּוּן לֶמֶד Tikún Lemed — Quality Gate Anti-Basura Whisper (FP-043 Parte C1)

**Descripción**: El sistema Lemed (auto-aprendizaje N1) registraba candidatos de cualquier texto que pasara por N2/N3, incluyendo transcripciones basura de Whisper. El fix añade un quality gate en `_es_promocionable()` que requiere ≥2 palabras de contenido y al menos 1 palabra reconocible en español.

**Requisitos funcionales**:
1. `_es_promocionable()` rechaza textos con < 2 palabras de contenido (excluyendo artículos/preposiciones).
2. `_es_promocionable()` rechaza textos donde ninguna palabra aparece en `_VOCAB_ESPAÑOL_BASICO`.
3. Textos válidos como "abre el navegador" siguen siendo promocionables.

- **Sefirot**: נצח Netzaj (Lemed aprendizaje) → גבורה Gevurá (quality gate)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-108: תִּקּוּן כְּלִי Tikún Kelí — Fix Tool-Block Texto Plano (FP-043 Parte C2)

**Descripción**: Ollama a veces envuelve respuestas conversacionales en bloques ` ```tool`, causando que `_limpiar_para_voz` los elimine y forzando retries costosos (~24s). El fix detecta bloques ` ```tool` que contienen texto plano (sin JSON) y extrae el contenido como respuesta directa.

- **Sefirot**: תפארת Tiféret (NLU parser) → יסוד Yesod (pipeline respuesta)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-109: שׁוֹמֵר קוֹל Shomer Kol — Guardia de Audio del Sistema (FP-044 Parte A)

**Descripción**: Computadora detecta si la ventana activa está reproduciendo media (YouTube, Netflix, Spotify, etc.) y ajusta su comportamiento de wake word para evitar falsos positivos por audio del sistema.

**Requisitos funcionales**:
1. `ContextoPantalla.hay_media_activa()` detecta patrones de media en título de ventana y proceso activo.
2. Cuando media está activa: fuzzy matching y correcciones Whisper se desactivan. Solo wake word regex exacto acepta.
3. Threshold de fuzzy matching endurecido: 0.6→0.72 (general), 0.5→0.62 (tokens cortos).
4. Eliminada corrección `"golden"→"computadora"` que causaba falsos positivos crónicos.
5. Log de librosa reducido a una sola advertencia por sesión.

- **Sefirot**: מלכות Maljut (windows.py) → הוד Hod (escucha.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-110: תִּקּוּן מִזְעֵר Tikún Miz’er — Interceptor __MINIMIZAR__ (FP-044 Parte B)

**Descripción**: El sentinel `__MINIMIZAR__` retornado por N1 no tenía interceptor en `_al_recibir_respuesta`, causando que TTS lo pronunciara como texto. El fix añade el interceptor faltante.

**Requisitos funcionales**:
1. `_al_recibir_respuesta` intercepta `"__MINIMIZAR__"` antes de llegar a TTS.
2. Ejecuta `showMinimized()` y habla confirmación.

- **Sefirot**: תפארת Tiféret (NLU) → מלכות Maljut (ventana_principal)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-111: תִּקּוּן מַרְאֵה Tikún Mar’é — Variantes Whisper para Demo Maljut (FP-044 Parte C)

**Descripción**: Whisper transcribe "maljut" como "mal juzg", "malhod", "mal ajudo", etc. El regex `_RE_DEMO_MALJUT` se expandió con variantes fonéticas de Whisper.

**Variantes añadidas**: `mal\s*(?:jut|juz[tg]?|hod|hut|jud|ajudo|kut)`

- **Sefirot**: תפארת Tiféret (NLU regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-112: תִּקּוּן קוֹל Tikún Kol — Sanitizador print() de Ollama (FP-044 Parte D)

**Descripción**: Ollama a veces envuelve respuestas en `print("...")`, `echo("...")` o `console.log("...")`. `_limpiar_para_voz` ahora extrae el texto interior.

- **Sefirot**: תפארת Tiféret (NLU sanitizer)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-113: שׁוֹמֵר הוֹד Shomer Hod — Conversation Window respeta Media (FP-045 Parte A)

**Descripción**: Cuando hay media activa (YouTube, Netflix, etc.) y la ventana de conversación está abierta, el audio del video se descartaba como "Conversación activa" y se procesaba como si fuera voz del propietario. Ahora `_en_conversacion` verifica `_media_activa` y descarta audio de video silenciosamente (excepto si `_esperando_respuesta` es True).

- **Sefirot**: הוד Hod (escucha.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-114: שׁוֹמֵר קוֹל Shomer Kol — Interrupción respeta Media (FP-045 Parte B)

**Descripción**: Durante TTS, audio de video era interpretado como interrupción del usuario (ratio bajo = voz diferente), provocando cascade de pensamientos basura. Ahora cuando `_media_activa` es True, la detección de interrupción se desactiva y el audio se filtra silenciosamente.

- **Sefirot**: הוד Hod (escucha.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-115: סִנּוּן חֶזְיוֹן Sinun Jezyon — Filtro de Alucinación Whisper (FP-045 Parte C)

**Descripción**: Whisper genera basura con caracteres no-latinos (CJK, cirílico, árabe, japonés) cuando el audio es ruido o media ininteligible. `_es_falso_positivo_conversacion` ahora detecta presencia de estos caracteres y descarta la transcripción como alucinación.

- **Sefirot**: הוד Hod (escucha.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-116: מַפְתֵּחַ יְסוֹד Mafteaj Yesod — PISTAS_HERRAMIENTAS expandido (FP-045 Parte D)

**Descripción**: "busca todo lo que encuentres sobre computadoras" no inyectaba tool hints porque `PISTAS_HERRAMIENTAS` solo tenía `busca en internet|investiga`. Expandido con: `busca\s+(?:todo|información|info|datos|algo)`, `dime\s+(?:todo|sobre|acerca)`, `búscame`, `averigua`, `encuentra\s+(?:todo|información)`.

- **Sefirot**: תפארת Tiféret → יסוד Yesod (parseo_herramientas.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-117: זְמַן תְשׁוּבָה Zman Teshuvá — Timeout de _esperando_respuesta (FP-046 Parte A)

**Descripción**: `_esperando_respuesta` (flag que relaja filtros cuando Computadora hizo pregunta) no tenía timeout. Si el usuario no respondía, la flag quedaba activa indefinidamente y la siguiente basura de Whisper entraba sin filtro. Fix: timestamp al activar + expiración a 30s.

- **Sefirot**: הוד Hod (escucha.py) ↔ תפארת Tiféret (equilibrio percepción)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-118: מִסְנֵן תְשׁוּבָה Misnen Teshuvá — Filtro mínimo en respuesta esperada (FP-046 Parte B)

**Descripción**: El path de `_esperando_respuesta` emitía texto directamente a Ollama sin pasar por `_es_falso_positivo_conversacion()`. Texto garbage como "Somehowhalf Irina kikka seafood" entraba a procesarse. Fix: ejecutar filtro de FP antes de emitir, incluso en respuesta esperada.

- **Sefirot**: הוד Hod (escucha.py) ↔ גבורה Gevurá (restricción)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-119: חִדּוּשׁ קוֹל Jidush Kol — Hot-reload de voz como reinicio manual (FP-046 Parte C)

**Descripción**: `importlib.reload()` en la capa `voz` recargaba el módulo pero no actualizaba `HiloEscucha` (instancia ya corriendo con métodos viejos). Fix: añadir `"voz"` a `CAPAS_REINICIO_MANUAL` para que emita señal `requiere_reinicio` en vez de reload silencioso.

- **Sefirot**: כתר Keter (hot_reload.py) ↔ מלכות Maljut (manifestación)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-120: הַשְׁתָקָה Hashtaká — Backoff de transcripciones vacías (FP-046 Parte D)

**Descripción**: Whisper se invocaba repetidamente en audio ambiental (6 vacías en 25s), quemando GPU sin utilidad. Tras chunks largos acumulados, generaba alucinaciones. Fix: contador de vacías consecutivas, tras 3+ duplica `silencio_max` (tope 6s). Reset al recibir transcripción útil.

- **Sefirot**: הוד Hod (escucha.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-121: תיקון מלכות Tikún Maljut Partículas (FP-047 Parte A)

**Descripción**: Corrección de 5 defectos en el sistema de partículas del orbe: (1) Clamp de offset_x/offset_y a ±radio*0.8 para evitar vuelo libre, (2) null-check de primaryScreen() en impulso, (3) `_particulas.clear()` al entrar en estados dormido/descanso, (4) caricia/brisa respetan `_max_particulas` antes de append, (5) copia defensiva de lista en DrawState.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-122: תיקון נצח-חסד-מלכות Tikún Netzaj-Jesed-Maljut (FP-047 Parte B)

**Descripción**: (1) `compress_day` ahora verifica que resumen o muestra se hayan guardado exitosamente ANTES de borrar el archivo raw — previene pérdida de datos. (2) `_check_salud_computadora` reutiliza instancia de MetaWorkflow en vez de crear una nueva cada 30 min — evita leak de subscripciones en BusEventos. (3) Watchdog lee modelo dinámicamente desde `/api/tags` de Ollama en vez de hardcodear `gemma3:4b`.

- **Sefirot**: נצח Netzaj (memoria.py), חסד Jesed (proactividad.py), מלכות Maljut (watchdog.py)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-123: תיקון יסוד Tikún Yesod — Infraestructura de Tests (FP-047 Parte C)

**Descripción**: (1) Corregió 2 archivos de test legacy con `sys.exit()` a nivel de módulo que crasheaban pytest (test_fp037_ketiva, test_tikun_002). (2) Corrigió import roto de `_sanitizar_comando` en test_fp023_tikun. (3) Configuró pytest en `pyproject.toml` con `python_functions=["test_*"]` para evitar que funciones auxiliares `test()` y `check()` de tests legacy sean recolectadas como fixtures. Resultado: `pytest tests/` ahora ejecuta limpiamente 139/139 tests.

- **Sefirot**: יסוד Yesod (tests/, pyproject.toml)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-124: אור חדש Ohr Jadash — Albedo Renacido + Regresión Completa (FP-047 Partes D+E)

**Descripción**: Actualización del Tikún Jai (Regla #17): (1) ALBEDO deja de estar fusionada con Nigredo y se convierte en fase propia con 3 sub-tareas: purificación técnica, investigación esotérica universal (Kabbalah, Hermetismo, Taoísmo, Tantra, Chaos Magick, tradiciones mesoamericanas, etc.), y benchmark de workflow (DevOps, Shape Up, DORA). (2) CITRINITAS recibe sección "Ohr Jadash" con sugerencias adaptadas al Etz HaChaim. (3) Nueva Regla #20: regresión completa obligatoria `pytest tests/ -q` después de CADA implementación.

- **Sefirot**: כתר Keter (workflow), חכמה Jojmá (creatividad esotérica)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-125: תיקון נפש Tikún Néfesh — Regex Faltantes (FP-048 Parte A)

**Descripción**: Corrección de regex N1 que no capturaban variantes de voz natural: (1) `_RE_DEMO_MALJUT` ahora acepta "malhut", "malhud", "maljut" como palabras sueltas sin requerir prefijo "demo de". (2) `_RE_TZIMTZUM` ahora incluye `oc[ú]ltate` además de `esc[ó]nd[eé]te`.

- **Sefirot**: נפש Néfesh (N1 regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-126: תיקון תפארת Tikún Tiféret — Sanitización de Respuestas Ollama (FP-048 Parte B)

**Descripción**: 4 defectos en el procesamiento de respuestas Ollama: (1) Sanitizer ahora atrapa `"Estado interno:"` sin corchetes (Ollama parafrasea hints de humor). (2) Detector de nombres de herramientas sueltos como respuesta (ej: `"listar_directorio"`). (3) `repeat_penalty: 1.3` + `repeat_last_n: 64` en ambos payloads Ollama (stream y no-stream). Anti-repetición post-hoc: frases repetidas 3+ veces se truncan. `_respuesta_es_inutil` detecta repetición sin importar longitud. (4) Blindaje de identidad en system prompt: negativa explícita contra identificarse como Gemma/Google/GPT. `listar_directorio` añadido a `extraer_tool_por_nombre`.

- **Sefirot**: תפארת Tiféret (N2 Ollama), מלכות Maljut (manifestación)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-127: Tests FP-048 (Parte C)

**Descripción**: 13 tests unitarios en `test_tikun_011.py` cubriendo los 6 defectos de FP-048.

- **Estado**: ✅ IMPLEMENTADO

---

### RF-128: Demo Regex Ampliado (FP-049 Parte A)

**Descripción**: `_RE_DEMO_MALJUT` ahora acepta "ejecuta tu demo" / "activa tu demo" / "haz tu demostración" sin requerir sufijo "maljut". Previamente, "ejecuta tu demo" caía a `_RE_ABRIR_APP` que intentaba abrir "tu demo" como aplicación.

- **Sefirot**: נפש Néfesh (N1 regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-129: Inercia de Partículas Restaurada (FP-049 Parte B)

**Descripción**: `mouseMoveEvent` y el bloque de impulso físico ya no sincronizan `_pos_anterior` — solo el timer `_animar` lo hace. HF-028 había eliminado la inercia visual al zero-ear el delta antes de que el timer pudiera leerlo. El damping `*0.4` ya protege contra movimiento excesivo.

- **Sefirot**: מלכות Maljut (partículas)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-130: Variantes Whisper de Maljut en Filtro FP (FP-050 Parte A)

**Descripción**: Variantes de "maljut" (malcut, malkut, malhut, malhud, maljud) añadidas a `_ESPAÑOL_CORTAS_VALIDAS` para que no sean descartadas como falsos positivos, y `cut` añadido a la alternación de `_RE_DEMO_MALJUT`.

- **Sefirot**: הוד Hod (escucha) + נפש Néfesh (N1 regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-131: Etz HaChaim Real v3.5 (FP-050 Parte C)

**Descripción**: Actualización del diagrama Etz HaChaim en SDD.md a v3.5 reflejando 44 módulos funcionales, añadiendo `comando_seguro.py` (Gevurá), `auto_update.py` (Yesod), `shir_haneshama.py` (Hod), `config.py` (Da'at), `__main__.py` (Maljut). Inercia restaurada FP-049, OrbeComputadora ~2700 líneas.

- **Estado**: ✅ IMPLEMENTADO

---

### RF-132: Variantes Whisper de "haz tu demo" (FP-050 Parte B)

**Descripción**: `_RE_DEMO_MALJUT` amplía la rama `haz/ejecuta/activa` para capturar errores de transcripción Whisper: "hasta demostración", "as tu demostración", "has tu demo". Regex: `h?a[sz](?:ta)?`.

- **Sefirot**: נפש Néfesh (N1 regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-133: demo_visual como Herramienta N2 — Balance Keter (FP-050 Parte D)

**Descripción**: `demo_visual` registrada como herramienta en `HERRAMIENTAS` (retorna `__DEMO_MALJUT__`). Añadida al system prompt de N2 para que Ollama pueda triggear la demo cuando N1 falla. Short-circuit en tool-use loop para retornar magic string directamente.

- **Sefirot**: תפארת Tiféret (N2) + מלכות Maljut (demo)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-134: Ventana de Velocidad Adaptativa — Cascade 50→80→120ms (FP-051 Parte A)

**Descripción**: `mouseReleaseEvent` reduce la ventana de historial de 120ms fijo a un cascade adaptativo: primero intenta 50ms, si no hay ≥2 puntos sube a 80ms, luego 120ms. Captura cambios rápidos de dirección fielmente.

- **Sefirot**: מלכות Maljut (ventana_principal)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-135: Amortiguación Dinámica de Partículas (FP-051 Parte B)

**Descripción**: Reemplaza el factor fijo `*0.4` por `damp = 0.4 + 0.3 * (1.0 - vel_norm)` donde `vel_norm = min(1.0, hypot(dx,dy)/30)`. Alta velocidad → 0.4 (como antes). Baja velocidad → 0.7. Diagonal se mueve con la misma fuerza que ejes puros.

- **Sefirot**: מלכות Maljut (ventana_principal)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-136: Sincronizar _pos_anterior post-Tzimtzum (FP-051 Parte C)

**Descripción**: `_desactivar_tzimtzum` sincroniza `_pos_anterior_x/y` con la posición actual del orbe después de `show()`. Elimina el delta fantasma que causaba explosión de partículas al re-emerger.

- **Sefirot**: מלכות Maljut (vida_autonoma → ventana_principal)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-137: Protección de Escala post-Tzimtzum (FP-051 Parte D)

**Descripción**: Flag `_restaurando_tzimtzum` se activa en `_desactivar_tzimtzum` y protege `cambiar_estado` de reducir `_escala_objetivo` a 0.45 (dormido) hasta que la escala llega a ≥0.95. El flag se auto-limpia en `_animar`. Evita que Computadora quede al 45% de escala tras restauración.

- **Sefirot**: מלכות Maljut (ventana_principal + vida_autonoma)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-138: Caricia Resetea Inactividad (FP-051 Parte E)

**Descripción**: Al detectar caricia en `_animar`, se resetea `_vida._ticks_inactivo = 0` y `_vida._pos_objetivo = None`. Evita que Computadora se vaya a casa mientras el usuario lo acaricia.

- **Sefirot**: מלכות Maljut (ventana_principal → vida_autonoma)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-139: Silero VAD Pre-Filtro de Voz (FP-052 Parte A)

**Descripción**: Antes de invocar Whisper, se ejecuta Silero VAD (`get_speech_timestamps`) sobre el audio crudo. Si no detecta segmentos de voz humana (threshold=0.5), se descarta el audio sin transcribir. Elimina ladridos, ruido ambiental, golpes, etc. antes de que Whisper los "hallucine" como texto.

- **Sefirot**: הוד Hod (escucha.py → pre-filtro perceptual)
- **Dependencia**: `silero-vad` v6.2.1, `torch`
- **Estado**: ✅ IMPLEMENTADO

---

### RF-140: Detector de Hallucination por Entropía (FP-052 Parte B)

**Descripción**: Función `_es_hallucination_repetitiva(texto)` analiza la transcripción de Whisper ANTES de procesarla. Dos heurísticas: (1) Entropía léxica — si `len(set(palabras))/len(palabras) < 0.4` para textos ≥4 palabras, es repetición (ej: "la la la la la"). (2) Ratio de compresión zlib — si `len(comprimido)/len(original) < 0.5`, el texto es demasiado repetitivo.

- **Sefirot**: הוד Hod (escucha.py → post-Whisper, pre-NLU)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-141: Parámetros Whisper Anti-Hallucination (FP-052 Parte C)

**Descripción**: Se añaden 4 parámetros al dict `_whisper_params` en `_transcribir()`: `condition_on_previous_text=False` (evita cascada de hallucinations), `compression_ratio_threshold=2.4` (rechaza decoder repetitivo), `logprob_threshold=-0.8` (rechaza tokens de baja confianza), `no_speech_threshold=0.4` (baja de 0.6 implícito — Whisper internamente descarta segmentos con no_speech_prob > 0.4).

- **Sefirot**: הוד Hod (escucha.py → configuración Whisper)
- **Fuente**: GitHub Whisper #679, #29 (jongwook: "0.6 was arbitrary")
- **Estado**: ✅ IMPLEMENTADO

---

### RF-142: Hysteresis de Proceso Tzimtzum (FP-053 Parte A)

**Descripción**: Cuando Computadora está en Tzimtzum y `_detectar_proceso_pesado()` retorna falso (e.g. por pérdida momentánea de foco), se verifica si `_tzimtzum_proceso` sigue corriendo via `psutil.process_iter`. Si el proceso aún existe, no se acumulan ticks ligeros. Solo se desactiva Tzimtzum cuando el proceso realmente terminó.

- **Sefirot**: מלכות Maljut (vida_autonoma.py → detección de procesos)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-143: Debounce Gradual de Carga Pesada (FP-053 Parte B)

**Descripción**: `_ticks_carga_pesada` ahora decrementa de 1 en 1 (`max(0, n-1)`) cuando no se detecta carga, en vez de resetearse a 0. Un blip de 1 tick sin detección ya no destruye 3 segundos de evidencia acumulada.

- **Sefirot**: מלכות Maljut (vida_autonoma.py → lógica de contadores)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-144: Restauración Sin Robo de Foco (FP-053 Parte C)

**Descripción**: `_desactivar_tzimtzum()` ya no usa `show()` + `raise_()` que robaban foco de la app gaming. Usa `ShowWindow(hwnd, SW_SHOWNOACTIVATE)` y `SetWindowPos` con `SWP_NOACTIVATE` (trick TOPMOST→NOTOPMOST) para restaurar Computadora sin interferir con el juego.

- **Sefirot**: מלכות Maljut (vida_autonoma.py → ventana Win32)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-145: Inercia en Movimiento Autónomo (FP-053 Parte D)

**Descripción**: `_interpolar_movimiento()` ya no sincroniza `_pos_anterior_x/y` después de cada `move()` durante el tránsito. Esto permite que `_animar()` detecte el delta natural y aplique inercia a las partículas cuando Computadora se mueve por su cuenta (ir a casa, esquivar, deambular). Solo se sincroniza al llegar al destino.

- **Sefirot**: מלכות Maljut (vida_autonoma.py → ventana_principal.py partículas)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-146: Re-aplicar DWM Post-Tzimtzum (FP-054 Parte A)

**Descripción**: `_reasegurar_transparencia()` ahora invoca `_eliminar_sombra_dwm()` al final, re-aplicando los fixes Win32/DWM (WS_POPUP, SWP_FRAMECHANGED, DWM DWMNCRP_DISABLED, Win11 corner rounding) que `ShowWindow(SW_SHOWNOACTIVATE)` resetea al restaurar la ventana tras Tzimtzum.

- **Sefirot**: מלכות Maljut (ventana_principal.py transparencia + DWM)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-147: NIGREDO+ALBEDO Obligatorios en Cada Ciclo Tikún (FP-054 Parte B)

**Descripción**: Regla #17 de DEVELOPMENT_WORKFLOW.md ahora marca NIGREDO y ALBEDO como fases OBLIGATORIAS al inicio de cada ciclo Tikún. NUNCA se puede saltar directo a CITRINITAS.

- **Sefirot**: כתר Keter (documentación de proceso)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-148: ALBEDO Ampliada con Filosofía y Ciencia (FP-054 Parte C)

**Descripción**: La fase ALBEDO ahora incluye 4 sub-tareas: (A) Purificación técnica, (B) Investigación Esotérica, (C) Investigación Filosófica y Científica (Platón, Aristóteles, Estoicismo, Fenomenología, Neurociencia, Cibernética, Teoría de Sistemas, etc.), (D) Benchmark de Workflow. Límite de `fetch_webpage` aumentado de 3 a 5 consultas.

- **Sefirot**: כתר Keter (documentación de proceso)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-149: תִּקּוּן הָאֱמֶת Tikún HaEmet — Path Legacy Sin Robo de Foco (FP-055 Parte A)

**Descripción**: El path legacy `_modo_carga_pesada` en `_iniciar_pensamiento()` usaba `self.raise_()` al restaurar la ventana tras wake-word, robando foco de la app activa del usuario. Contradecía RF-144 (no-focus-steal). Fix: reemplazar `show()` + `raise_()` con patrón RF-144 (`SW_SHOWNOACTIVATE` + `SetWindowPos` TOPMOST→NOTOPMOST trick).

**Requisitos funcionales**:
1. Path legacy usa `ShowWindow(hwnd, SW_SHOWNOACTIVATE)` en vez de `self.show()`.
2. `SetWindowPos` con `SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE` eleva sin activar.
3. `_reasegurar_transparencia()` se ejecuta después del show.
4. NO se usa `raise_()` ni `activateWindow()`.

- **Sefirot**: מלכות Maljut (ventana) ↔ גבורה Gevurá (restricción de foco)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-150: תִּקּוּן הַמַּרְאֶה Tikún HaMar'é — Demo Maljut Sin Warnings FSM (FP-055 Parte B)

**Descripción**: La coreografía Demo Maljut (RF-106) recorre todos los estados FSM secuencialmente, generando ~8 warnings de "Transición inválida" por saltos que son intencionales en contexto de demo. Fix: skip FSM validation cuando `_demo_en_curso == True`.

**Requisitos funcionales**:
1. `cambiar_estado()` no valida transiciones cuando `self._demo_en_curso` es `True`.
2. Fuera de la demo, la validación FSM opera sin cambios.

- **Sefirot**: מלכות Maljut (FSM orbe)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-151: תִּקּוּן הַמַּלְכוּת Blend Dual Humor Visual — Mezcla Emocional en Maljut (FP-056)

**Descripción**: El color del orbe (tinte Dmut) solo reflejaba el humor primario. RF-151 interpola el tinte del humor secundario al 30% máximo (peso real del secundario, capped a 0.3) para visualizar el estado emocional dual.

**Requisitos funcionales**:
1. `paintEvent()` lee `personalidad.humor_secundario` y `peso_secundario`.
2. Si hay humor secundario válido, los tintes RGB se interpolan: `primario*(1-w) + secundario*w`.
3. El peso visual máximo es 0.3 (30%) independientemente del peso real.

- **Sefirot**: מלכות Maljut (visual) ↔ רוח Ruaj (emociones)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-152: אוֹר הַיּוֹם Ohr HaYom — Modulación Circadiana de Brillo (FP-056)

**Descripción**: El brillo base del orbe ahora se modula según la fase circadiana activa: +0.03 en fase "activo" (día, más luminoso), -0.02 en fase "descanso_guardian" (noche, más tenue). Calm Technology: la información del momento del día es periférica y glanceable.

**Requisitos funcionales**:
1. `_fase_circadiana` se almacena en `__init__` y se actualiza en `_al_cambio_fase_circadiana()`.
2. En `_animar()`, el brillo se ajusta +0.03 (activo) o -0.02 (descanso_guardian).

- **Sefirot**: מלכות Maljut (visual) ↔ דעת Da'at (ciclo circadiano)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-153: נְשָׁמָה חַיָּה Neshamá Jayá — Densidad de Partículas por Energía (FP-056)

**Descripción**: La densidad de partículas del orbe es proporcional al rasgo `energia` de la personalidad. Factor: `0.5 + energia` (rango 0.5x a 1.5x). Tufte: usar canal visual existente en vez de añadir nuevo indicador.

**Requisitos funcionales**:
1. En `_animar()`, `particulas_mod` se multiplica por `0.5 + personalidad.rasgo("energia")`.
2. El visual es sutil y no requiere atención consciente (Calm Technology).

- **Sefirot**: מלכות Maljut (partículas) ↔ נפש Nefesh (personalidad)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-154: מַרְאֶה הַמַּלְכוּת Mar'é HaMaljút — Demo Completa del Orbe (FP-056)

**Descripción**: La coreografía Demo Maljut (RF-106) se amplía de ~42s a ~62s, mostrando los 13 estados FSM (incluyendo dormido, descanso_guardian, vigilia antes ausentes), ciclando 3 humores (sereno→emocionado→preocupado), activando zonas de tacto (1→2→3→0), y narrando cada paso por voz TTS. Tour Ambient Orb kabalístico.

**Requisitos funcionales**:
1. Recorre los 13 estados FSM: dormido, descanso_guardian, despertando, vigilia, escuchando, procesando, trabajando, hablando, gevura_activa, error, cortesia, alerta_extrano + bereshit implícito.
2. Cicla 3 humores vía `_transicionar_humor(forzar=True)`.
3. Activa zonas de tacto `_zona_tacto` = 1, 2, 3, 0.
4. Narración TTS por paso (ej: "Estado dormido. Mínima actividad.").
5. Restaura estado, humor y zona_tacto al finalizar.

- **Sefirot**: מלכות Maljut (visual completo)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-155: תִּקּוּן הַשְּׁמִיעָה Tikún HaShmí'a — Regex 'abrem' Whisper (FP-056)

**Descripción**: Whisper transcribe "abre mi" como "abrem mi" (elisión). La variante "abrem" se añade a `_RE_ABRIR_APP` y `_RE_CARPETA_PERSONAL` para capturarla en Nivel 1.

**Requisitos funcionales**:
1. `_RE_ABRIR_APP` incluye "abrem" en su grupo de alternativas.
2. `_RE_CARPETA_PERSONAL` incluye "abrem" en su grupo de alternativas.

- **Sefirot**: חכמה Jojmá (NLU N1 regex)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-156: שְׁמִירַת הַדִּבּוּר Shemirat HaDibúr — Guard Anti-Código en TTS (FP-056)

**Descripción**: Cuando N2 (Ollama) envuelve código fuente en un bloque ` ```tool ` sin JSON, el sistema lo extraía como "respuesta de texto plano" y lo hablaba por TTS. El guard detecta keywords de código (`import`, `def`, `class`, `function`, `from`, `return`) y descarta el contenido.

**Requisitos funcionales**:
1. Si `_tool_texto_plano` contiene keywords de código → se descarta (= None).
2. El flujo continúa al fallback normal de N2 (reintento o respuesta sin herramientas).

- **Sefirot**: תפארת Tiféret (NLU N2) ↔ הוד Hod (TTS)
- **Estado**: ✅ IMPLEMENTADO

---

### RF-157: תִּקּוּן הַמַּעֲבָר Tikún HaMa'avár — Transiciones Suaves de Humor Dmut (FP-057)

**Descripción**: Los cambios de humor del Computadora producían saltos instantáneos en el color/tinte/rotación/partículas del orbe. Inspirado en Wu Xing (ciclo generativo entre fases) y Calm Technology (periferia no intrusiva), RF-157 implementa lerp temporal: cada campo del dict Dmut (brillo_mod, rot_mod, particulas_mod, pulso_vel, tinte_r/g/b) se interpola gradualmente del valor actual al target a 5% por frame (~0.67s a 30fps).

**Requisitos funcionales**:
1. `__init__` crea `_dmut_actual` (dict con valores interpolados en curso) y `_dmut_humor_prev`.
2. `_animar()` calcula `_dmut_target` desde `_DMUT_VISUAL[humor_actual]` y aplica lerp: `actual += (target - actual) * 0.05` para cada key.
3. `paintEvent()` usa `_dmut_actual` como base para tintes (reemplaza lectura directa de `_DMUT_VISUAL`).
4. La transición completa toma ~20 frames (≈0.67s) para converger al 95%.
5. Demo Maljut actualizada: ACT III narra "transición suave" y da 4s entre cada humor para que el lerp sea visible.

- **Sefirot**: מלכות Maljut (visual lerp) ↔ רוח Ruaj (emociones)
- **Estado**: ✅ IMPLEMENTADO

### RF-158/RF-159/RF-160/RF-161: תִּקּוּן הַסֵּדֶר Tikún HaSéder — Orden Durante la Demo (FP-058)

**Descripción**: La demo Maljut sufría caos por subsistemas concurrentes no pausados: vida autónoma movía el orbe, TTS cambiaba el estado a "hablando" (amarillo) sobre los colores coreografiados, el micrófono captaba eco TTS generando interrupciones falsas y basura a Ollama, y el heatmap targeting creaba turbulencia en bordes por clamp.

**RF-158 — Demo pausa subsistemas**:
1. `_demo_maljut` detiene `_vida._timer` y `_vida._timer_movimiento` y limpia `_pos_objetivo`.
2. Activa silencio en proactividad y pausa escucha.
3. `_paso_final` reinicia timers (500ms/16ms), desactiva silencio y reanuda escucha.

**RF-159 — Habla respeta demo**:
1. `_al_iniciar_habla()` retorna inmediatamente si `_demo_en_curso` — no cambia a "hablando".
2. `_al_terminar_habla()` retorna inmediatamente si `_demo_en_curso` — no cambia a "escuchando".

**RF-160 — Escucha descarta en demo**: Cubierto por RF-158 — `hilo_escucha.pausar()` drena la cola de audio.

**RF-161 — Clamp-aware targeting**:
1. En `_interpolar_movimiento`, si la posición post-clamp == posición actual, el objetivo está fuera de zona alcanzable.
2. Se limpia `_pos_objetivo = None` y retorna — elimina turbulencia en bordes.

- **Sefirot**: מלכות Maljut (demo) ↔ גבורה Gevurá (orden/restricción)
- **Estado**: ✅ IMPLEMENTADO

---

### FP-059 — Tikún HaGvúl VeHaOhr — תיקון הגבול והאור

**Descripción**: Reparación del borde visible de la ventana (regresión Win11 DWM) y suavizado de resize/movimiento. El marco de la ventana se volvía visible en Windows 11, el clamp usaba `min()` en vez de `max()` ignorando el tamaño real expandido, y el resize con lerp entero causaba oscilación por dead-zone de truncamiento.

**RF-162 — Eliminación de borde DWM Win11**:
1. `_eliminar_sombra_dwm()` establece `DWMWA_BORDER_COLOR` (attr 34) con valor `0xFFFFFFFE` (DWMWA_COLOR_NONE).
2. NO se usa `DwmExtendFrameIntoClientArea(MARGINS(-1,-1,-1,-1))` — es incompatible con `WA_TranslucentBackground` (causa fondo blanco).

**RF-163 — Clamp usa tamaño real (max)**:
1. En `_interpolar_movimiento`, `_w_clamp = max(self._orbe.width(), self.TAMANO_PLENO)` — el clamp respeta el tamaño expandido real.

**RF-164 — Destinos usan tamaño real (max)**:
1. En `_esquivar`, `w = max(self._orbe.width(), self.TAMANO_PLENO)` — candidatos de esquiva respetan tamaño real.
2. En `_mejor_borde`, `w = max(self._orbe.width(), self.TAMANO_COMPACTO)` — destinos de borde respetan tamaño real.

**RF-165 — Resize suave sin oscilación**:
1. `_tamano_ventana` es `float` — acumulación sin truncamiento.
2. Lerp: `self._tamano_ventana += (tam_necesario - self._tamano_ventana) * 0.15`, render con `round()`.
3. Bloque de resize movido ANTES del cálculo de `_raw_dx/dy` — elimina delta fantasma en partículas.
4. Threshold cambiado de `>4` a `>2`, snap final a `>0.5`.

- **Sefirot**: מלכות Maljut (ventana) ↔ גבורה Gevurá (borde/restricción) ↔ הוד Hod (luz/transparencia)
- **Estado**: ✅ IMPLEMENTADO

**Requisitos funcionales**:
1. `_gevura_esperando` se inicializa como `False` en `__init__`.
2. `_al_recibir_voz` retorna inmediatamente sin procesar si `_gevura_esperando = True`.
3. `_on_solicitar_permiso` activa `_gevura_esperando = True` al iniciar y lo limpia a `False` en flujo normal Y en except.

- **Sefirot**: מלכות Maljut (ventana_principal) ↔ גבורה Gevurá (permisos) ↔ תפארת Tiféret (NLU/cola)
- **Estado**: ✅ IMPLEMENTADO

---

### FP-060 — חיזוק העץ Jizúk HaEtz — Fortalecimiento del Árbol

**Descripción**: Robustecimiento y equilibrio del Etz HaChaim. Auditoría de 43 módulos (15,514 líneas) reveló 147 bloques `except Exception:` silenciosos en 28 módulos y 8 QTimers sin detener al cerrar.

**RF-166 — Tikún Petiráh — Cierre limpio**:
1. `closeEvent` y `forzar_cierre` detienen los 6 QTimers de ventana_principal (`_timer`, `_timer_animo`, `_timer_guardar_persona`, `_timer_evolucion`, `_bereshit_timer`, `_bereshit_timeout`) via loop `getattr`.
2. `HiloPensamiento` recibe `wait(3000)` si está activo.
3. vida_autonoma ya detenía sus 2 QTimers en `detener()` — verificado.

**RF-167 — Nishmat HaComputadora v2 — Higiene completa**:
1. 147 bloques `except Exception:` convertidos a `except Exception as e:` + `logger.debug("Excepcion ignorada: %s", e)` en 28 módulos.
2. 2 módulos sin logger (`config.py`, `watcher_solicitudes.py`) recibieron `from loguru import logger`.
3. Zero `except Exception:` silenciosos restantes en todo `computadora/`.

- **Sefirot**: כל העץ Kol HaEtz (Todo el Árbol) — 28 módulos afectados
- **Estado**: ✅ IMPLEMENTADO

**RF-168 — Zikrón HaIdkún — Notificación de reinicio pendiente**:
1. Cuando HotReloader detecta cambios en capas que requieren reinicio manual (interfaz, voz), el Computadora acumula los nombres de archivos modificados.
2. En la siguiente interacción de voz real (excluye `[presencia]` y `[confirmar]`), el Computadora recita un aviso natural: "Señor, hay cambios en {archivos} que necesitan reinicio para activarse."
3. Tras notificar, limpia la bandera y la lista, permitiendo que el comando del usuario se procese normalmente.
4. Implementado en `ventana_principal.py`: flags `_reinicio_pendiente` + `_archivos_reinicio`, modificaciones a `_on_requiere_reinicio` y `_al_recibir_voz`.

- **Sefirot**: כתר Keter (HotReloader) → מלכות Maljut (VentanaPrincipal / voz)
- **Estado**: ✅ IMPLEMENTADO

**RF-169 — דברי הגולם Devré HaComputadora — Automejoración por Workflow**:
1. El usuario puede pedir al Computadora que se mejore a sí mismo con frases como "mejórate", "automejorar", "modifica tu código", "evoluciona", "optimízate".
2. El Computadora construye un prompt estructurado con contexto del workflow y lo envía a Copilot API (N3).
3. Si Copilot responde con una Feature Proposal estructurada (PROPUESTA/DESCRIPCION/ARCHIVOS/RIESGO/VEREDICTO), el Computadora la detecta, la recita en prosa natural (sin markdown) y pide aprobación al usuario.
4. Si el usuario aprueba, se crea una solicitud formal vía `copilot_bridge.solicitar_a_copilot()`. Si rechaza, se cancela.
5. Implementado en `nlu.py`: regex `_RE_AUTOMEJORA`, 4 métodos nuevos (`_flujo_automejora`, `_detectar_gate_proposal`, `_recitar_proposal_voz`, `_procesar_aprobacion_automejora`).

- **Sefirot**: תפארת Tiféret (NLU) → כתר Keter (Copilot API) → הוד Hod (voz) → גבורה Gevurá (gate) → יסוד Yesod (copilot_bridge)
- **Estado**: ✅ IMPLEMENTADO

**RF-170 — שומר אמת Shomer Emet — Período de gracia del Watchdog**:
1. Al iniciar, cada `ServicioMonitoreado` establece un período de gracia de 30 segundos (`_gracia_hasta`).
2. Durante el período de gracia, `check()` retorna `True` sin ejecutar el chequeo real, evitando falsos positivos RETRY/NOTIFY al arranque.
3. Pasado el período de gracia, el comportamiento es idéntico al original.
4. Implementado en `watchdog.py`: `_gracia_hasta` en `__init__`, early return en `check()`.

- **Sefirot**: מלכות Maljut (watchdog.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-171 — שער המלכות Sha'ar HaMaljut — Demo en menú contextual**:
1. El menú contextual del Orbe (clic derecho) ahora incluye la opción "מראה המלכות — Mar'é HaMaljut (Demo)" que ejecuta la demo completa del Computadora.
2. Orden del menú: (1) Kabbalah be-peh, (2) Demo Maljut, (3) Gilgul, [separador], (4) Borrar la Palabra.
3. Implementado en `ventana_principal.py`: nuevo `QAction` en `_mostrar_menu()` conectado a `_demo_maljut()`.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

---

**RF-172 — כלי מפתח Klei Mefateaj — Dev Tools en menú contextual**:
1. Submenú "כלי מפתח — Dev Tools" en el menú contextual del Orbe con 2 herramientas.
2. Heatmap de pantalla: QDialog con grid visual 8×6 mostrando intensidad de actividad por zona.
3. Estado interno: QDialog con scroll mostrando FSM, etapa alquímica, cerebro, humor, gevurá, stats, colores, etc.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-173 — אור האלכימיה Ohr HaAlkimia — Sistema de color 5 capas**:
1. Capa 1: Paletas alquímicas base (NIGREDO/ALBEDO/CITRINITAS/RUBEDO).
2. Capa 2: Transformación HSV por estado FSM (8 grupos visuales de 13 estados).
3. Capa 3: Tinte aditivo por categoría de herramienta activa (9 categorías, 31 tools mapeados).
4. Capa 4: Tinte aditivo por nivel cerebral (nivel1/nivel2/nivel3).
5. Capa 5: Tinte emocional existente (Dmut).
6. Función central `_calcular_color_ohr()` reemplaza el bloque if/elif hardcodeado del paintEvent.
7. Sub-override de Gevurá con 8 categorías de color específicas.
8. 96,768 combinaciones teóricas de color.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-174 — מראה חדשה Mar'é Jadashá — Demo sincronizada por señales**:
1. La demo ya no usa `QTimer.singleShot` con delays fijos — usa cadena de señales `habla_terminada`.
2. Lista de pasos `_demo_pasos` con motor `_demo_ejecutar_paso()` que avanza según señal o delay.
3. Cada narración espera a que TTS termine + 400ms pausa antes de avanzar.
4. Pasos sin voz usan delays cortos (800-1500ms).

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-175 — לרפ מהיר Lerp Mahir — Lerp adaptativo para demo**:
1. Velocidad de lerp alquímico: `1/(1.5*30)` durante demo vs `1/(60*30)` normal.
2. Flag `_demo_en_curso` controla la velocidad automáticamente.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-176 — שומר הדמו Shomer HaDemo — Demo no reactiva mic antes de cola_vacia**:
1. Bug fix: la demo reactivaba el micrófono antes de que TTS terminara → Computadora se escuchaba a sí mismo.
2. Fix: `_demo_en_curso` se mantiene True hasta señal `cola_vacia`. Mic se reactiva en callback one-shot.
3. Cooldown post-TTS configurable (`escucha.post_tts_cooldown_ms`).

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-177 — obtener_ventana_activa() corregido**:
1. Bug fix: `proactividad.py` llamaba `ventana_activa()` que no existe en `ContextoPantalla`.
2. Corregido a `obtener_ventana_activa()` en 3 ubicaciones (L216, L324, L456).

- **Sefirot**: נצח Netzaj (proactividad.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-178 — _ultimo_evento en CicloCircadiano**:
1. Bug fix: atributo `_ultimo_evento` nunca se definía en CicloCircadiano.
2. Inicializado en `__init__` y actualizado en `registrar_interaccion()`.

- **Sefirot**: תפארת Tiferet (ciclo_circadiano.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-179 — ארבע קולות Arba Kolot — Las 4 voces de la alquimia (ACT VII demo)**:
1. Nuevo acto en la demo mostrando el mismo estado ("hablando") con las 4 etapas alquímicas.
2. Demuestra visualmente: NIGREDO oscuro, ALBEDO plata, CITRINITAS oro, RUBEDO fuego.
3. Cada voz narra su identidad alquímica.

- **Sefirot**: מלכות Maljut (ventana_principal.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-180 — חום כפול Jom Kaful — Dual Heatmap (reciente + histórico)**:
1. Heatmap reciente de 5 min (RAM, decay 0.85/30s, reset cada 5 min ventana deslizante).
2. Score combinado: `histórico * 0.4 + reciente * 0.6` para reaccionar rápido a cambios.
3. Solo el histórico se persiste a disco.

- **Sefirot**: מלכות Maljut (vida_autonoma.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-181 — זכרון ההתמכות Zikrón HaHitmajkut — Memoria de Esquivas + Escalación**:
1. `_historial_esquivas: deque(maxlen=20)` con tuplas `(timestamp, origen, destino, razón)`.
2. Cada esquiva se registra automáticamente.
3. Escalación: ≥2 en 5min → recalc home, ≥5 → doble cooldown + recalc, ≥7 → tzimtzum.

- **Sefirot**: מלכות Maljut + גבורה Gevurá (vida_autonoma.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-182 — בית תגובתי Bait Teguvatí — Home Reactivo Post-Esquiva**:
1. Tras ≥2 esquivas en 5 min, recalcula hogar dinámico inmediatamente.
2. Si el nuevo hogar cae en zona de esquiva frecuente, usa el 2do mejor candidato.
3. Setea `_en_hogar = True` para evitar loop esquiva↔hogar.

- **Sefirot**: מלכות Maljut (vida_autonoma.py)
- **Estado**: ✅ IMPLEMENTADO

**RF-183 — זכרון הציטריניטס Zikrón HaCitrinitas — Persistencia de Propuestas en Tikún**:
1. Regla #21 en DEVELOPMENT_WORKFLOW.md.
2. Al entrar a CITRINITAS: crear/actualizar `/memories/session/citrinitas_proposals.md`.
3. Al re-entrar por iteración: leer propuestas previas, nunca partir de cero.
4. Al completar RUBEDO: borrar archivo session.

- **Sefirot**: כתר Keter (meta-workflow)
- **Estado**: ✅ IMPLEMENTADO

---

### FP-075 — כלי ההרחבה Kli HaHarjavá — Marco de Extensión de Dispositivos

**RF-201 — ABC DispositivoKli + Protocol SensorOhr**:
Clase abstracta `DispositivoKli` con métodos: `conectar()`, `desconectar()`, `leer_ohr()`, `enviar_pekuda()`, `estado`. Protocol class `SensorOhr` para lectura por duck-typing sin herencia obligatoria.
- **Archivo**: `computadora/nucleo/kli.py` (NUEVO)
- **Sefirá**: יסוד Yesod
- **Estado**: ✅ IMPLEMENTADO

**RF-202 — GestorKelim singleton**:
Registro de dispositivos, ciclo de vida (descubrir→conectar→leer→desconectar), health check periódico, señales Qt (`kli_conectado`, `kli_desconectado`, `ohr_recibido`, `kli_error`).
- **Archivo**: `computadora/nucleo/kli.py` (NUEVO)
- **Sefirá**: יסוד Yesod
- **Estado**: ✅ IMPLEMENTADO

**RF-203 — KliRed adapter**:
ARP scan local (scapy, opcional), listado de dispositivos (IP, MAC, hostname), ping check, WoL send.
- **Archivo**: `computadora/habilidades/red.py` (NUEVO)
- **Sefirá**: הוד Hod
- **Estado**: ✅ IMPLEMENTADO

**RF-204 — KliCamara adapter**:
OpenCV VideoCapture, frame grab, detección de movimiento (frame diff + umbral), modo nocturno (equalizeHist + CLAHE).
- **Archivo**: `computadora/habilidades/vision.py` (NUEVO)
- **Sefirá**: הוד Hod
- **Estado**: ✅ IMPLEMENTADO

**RF-205 — KliComandoRemoto adapter**:
SSH nativo Windows (subprocess ssh.exe), WoL (wakeonlan lib), ejecución de comando remoto con timeout 10s + Gevurá check.
- **Archivo**: `computadora/habilidades/control_remoto.py` (NUEVO)
- **Sefirá**: הוד+גבורה Hod+Gevurá
- **Estado**: ✅ IMPLEMENTADO

**RF-206 — Integración 3 tools (escanear_red, ver_camara, control_remoto)**:
Herramientas nuevas en herramientas.py con niveles Gevurá (red=accion, camara=info, remoto=admin).
- **Archivo**: `computadora/habilidades/herramientas.py`
- **Sefirá**: יסוד+גבורה Yesod+Gevurá
- **Estado**: ✅ IMPLEMENTADO

**RF-207 — Senderos nuevos Etz HaChaim**:
Yesod→Hod (kli→sensores), Gevurá→Yesod (permisos→kli), Hod→Tiféret (sensor data→NLU). Actualizar SDD §4.17.3/4.
- **Archivo**: SDD.md
- **Sefirá**: Etz HaChaim
- **Estado**: ✅ IMPLEMENTADO

**RF-208 — Dependencias opcionales**:
+scapy, +opencv-python-headless, +wakeonlan en requirements.txt. Importación lazy con try/except.
- **Archivo**: requirements.txt
- **Sefirá**: כתר Keter
- **Estado**: ✅ IMPLEMENTADO

**RF-209 — Tests FP-075**:
test_tikun_33.py: ABC contract, mock adapters, GestorKelim lifecycle, import guards.
- **Archivo**: `tests/test_tikun_33.py` (NUEVO)
- **Sefirá**: בינה Biná
- **Estado**: ✅ IMPLEMENTADO

---

### FP-076 — שומר הבית Shomer HaBáyit — Sistema Guardián Integral

**RF-210 — Activación explícita del guardián**:
Regex N1: "ponte en modo guardián|vigila la casa|activa el guardián|modo seguridad|cuida la casa" → `_activar_guardian()` con confirmación de voz.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

**RF-211 — Desactivación del guardián**:
Regex N1: "desactiva el guardián|ya no vigiles|modo normal" → `_desactivar_guardian()` con confirmación.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

**RF-212 — "ya me voy" AUTO-activa guardián**:
Al detectar partida física, auto-activa guardián sin preguntar. Confirma con voz.
- **Archivo**: `computadora/cerebro/nlu.py` (mejora _partida existente)
- **Sefirá**: תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

**RF-213 — Flujo nocturno "ya me voy a dormir"**:
Regex N1 detecta despedida nocturna. Si hay cámara → auto ON. Si no → solo red.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת+דעת Tiféret+Da'at
- **Estado**: ✅ IMPLEMENTADO

**RF-214 — "ya me voy a dormir, vigila"**:
Variante explícita que activa cámara ON directo sin preguntar.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

**RF-215 — "mejor duérmete" → Tzimtzum + mic activo**:
Tzimtzum pero mantiene listener activo. Si sonido fuerte → despertar + alerta.
- **Archivo**: `computadora/cerebro/nlu.py` + `ventana_principal.py`
- **Sefirá**: תפארת+מלכות Tiféret+Maljut
- **Estado**: ✅ IMPLEMENTADO

**RF-216 — Fase circadiana vigía_nocturna**:
Nueva fase entre descanso_guardian y activo. No incrementa fatiga.
- **Archivo**: `computadora/nucleo/ciclo_circadiano.py`
- **Sefirá**: דעת Da'at
- **Estado**: ✅ IMPLEMENTADO

**RF-217 — Reporte matutino**:
"buenos días" post-vigía → resumen de detecciones nocturnas.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת+נצח Tiféret+Netzaj
- **Estado**: ✅ IMPLEMENTADO

**RF-218 — Guardian loop QTimer(30s)**:
Network ping + frame diff + log eventos en modo guardián.
- **Archivo**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות+הוד Maljut+Hod
- **Estado**: ✅ IMPLEMENTADO

**RF-219 — Smart restart con confirmación NL**:
"reiníciate|reinicia el sistema" → confirmación → sys.exit(0) + script reinicio.
- **Archivo**: `computadora/cerebro/nlu.py` + `ventana_principal.py`
- **Sefirá**: תפארת+מלכות Tiféret+Maljut
- **Estado**: ✅ IMPLEMENTADO

**RF-220 — Demo ACT VIII-IX**:
ACT VIII "El Guardián" + ACT IX "La Visión" en demo Maljut expandida.
- **Archivo**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO

**RF-221 — Self-knowledge STT-resiliente**:
Variantes tolerantes a STT para "cómo te llamas" + "quién eres" + computadora/gólem/golden.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

**RF-222 — Tests FP-076**:
test_tikun_32.py: guardian activation/deactivation, night flow, restart confirm.
- **Archivo**: `tests/test_tikun_32.py` (NUEVO)
- **Sefirá**: בינה Biná
- **Estado**: ✅ IMPLEMENTADO

**RF-223 — Corregir VentanaInfo→str** (FP-077):
En proactividad.py, 3 sitios pasan VentanaInfo (NamedTuple) donde se espera str. Extraer `.titulo`.
- **Archivo**: `computadora/nucleo/proactividad.py`
- **Sefirá**: חסד Jesed (sendero Hod→Jesed reparado)
- **Estado**: ✅ IMPLEMENTADO

**RF-224 — Completar transiciones FSM Maljut** (FP-077):
Agregar 5 transiciones faltantes + 4 self-loops a TRANSICIONES_VALIDAS.
- **Archivo**: `computadora/interfaz/fsm_computadora.py`
- **Sefirá**: מלכות Maljut (Ley de Ashby — variedad requisita)
- **Estado**: ✅ IMPLEMENTADO

**RF-225 — Fortalecer detección código en tool blocks** (FP-077):
Agregar `print(`, `console.log(`, `echo `, `System.out` a keywords de `_parece_codigo`.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (defensa en profundidad)
- **Estado**: ✅ IMPLEMENTADO

**RF-226 — Extraer patrones guardián a módulo dedicado** (FP-077):
Mover 7 regex compiladas del Shomer HaBáyit de nlu.py a patrones_guardian.py.
- **Archivo**: `computadora/cerebro/patrones_guardian.py` (NUEVO)
- **Sefirá**: תפארת Tiféret (equilibrio — reducir módulo central)
- **Estado**: ✅ IMPLEMENTADO

**RF-227 — Extraer flujos guardián a módulo dedicado** (FP-077):
Mover 6 métodos de flujo guardián de CerebroComputadora a flujos_guardian.py.
- **Archivo**: `computadora/cerebro/flujos_guardian.py` (NUEVO)
- **Sefirá**: תפארת Tiféret (equilibrio — reducir módulo central)
- **Estado**: ✅ IMPLEMENTADO

**RF-228 — Shomer HaDemo Bereshit — Blindaje demo contra circadiano/Bereshit** (Pipeline C bug fix):
Evitar que el ciclo circadiano y Bereshit interfieran con la demo visual.
- **Archivo**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (demo es la manifestación del Computadora)
- **Cambios**:
  1. `_demo_maljut()`: Forzar `_boot_completo=True` al iniciar demo (si no lo era). Abortar Bereshit si estaba activo.
  2. `_demo_maljut()`: Aumentar `activar_silencio(2)` → `activar_silencio(5)` (demo ~3 min + margen).
  3. `_al_cambio_fase_circadiana()`: Return early si `_demo_en_curso`.
  4. `_al_sugerencia_proactiva()`: Return early si `_demo_en_curso`.
- **Estado**: ✅ IMPLEMENTADO

**RF-229 — Filtro anti-tool-call malformado en voz** (Pipeline C bug fix):
Evitar que Ollama hable nombres de herramientas como respuesta cuando genera tool calls malformados (texto plano en ```tool block).
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (cerebro NLU)
- **Cambios**:
  1. `_limpiar_para_voz()`: Detectar texto multilínea que empieza con nombre de herramienta (no solo nombre suelto exacto) → suprimir.
  2. Tool-loop: Cuando ```tool block contiene texto plano que empieza con nombre de herramienta, descartar y reintentar con hint "responde en español natural".
- **Estado**: ✅ IMPLEMENTADO

**RF-230 — Hakará: Reconocimiento de presentaciones en _ES_CONVERSACION** (Pipeline C bug fix):
Expandir regex `_ES_CONVERSACION` para detectar frases de identidad ("soy X", "me llamo X", "mi nombre es", "soy tu creador").
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (cerebro NLU)
- **Estado**: ✅ IMPLEMENTADO

**RF-231 — Shomer HaShem: Bloque PRESENTACIONES en SISTEMA_PROMPT** (Pipeline C bug fix):
Agregar instrucciones al system prompt para que Computadora confirme nombres, reconozca al creador con afecto, y no responda genéricamente a presentaciones.
- **Archivo**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (cerebro NLU)
- **Estado**: ✅ IMPLEMENTADO

**RF-232 — Tikún HaParseo: Mapeo tool→herramienta en parser** (Pipeline C bug fix):
En `extraer_tool_call()`, mapear keys en inglés ("tool"→"herramienta", "arguments"→"args") ya que Ollama a veces responde con formato en inglés.
- **Archivo**: `computadora/cerebro/parseo_herramientas.py`
- **Sefirá**: תפארת Tiféret (parseo)
- **Estado**: ✅ IMPLEMENTADO

**RF-233 — Lashón HaLev: Módulo de perfil lingüístico adaptativo** (Pipeline B mejora UX):
Nuevo módulo que aprende el idiolecto del amo: muletillas, estilo de petición, longitud media, bigramas frecuentes, verbos imperativos, temas recurrentes. Genera hint compacto (~40 tokens) para system prompt.
- **Archivos**: `computadora/memoria/perfil_linguistico.py` (NUEVO), `computadora/cerebro/nlu.py` (integración)
- **Sefirá**: נצח Netzaj + תפארת Tiféret (Sendero 24)
- **Datos**: `datos/perfil_linguistico.json`
- **Estado**: ✅ IMPLEMENTADO

**RF-240 — Tikún ACT V: Alquimia Narrada** (Pipeline E arquitectura):
Eliminar ACT V actual de la demo (4 fases alquímicas en 1 sola frase + 3 transiciones silenciosas sin narración). ACT VII ya narra cada fase individualmente con voz. ACT V es redundante y confuso para el usuario.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (eliminar 4 líneas de ACT V)
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-241 — Koaj HaComputadora: Demostración de Poder (info)** (Pipeline E arquitectura):
Nuevo acto en Demo 1 entre ACT VII y ACT VIII: ejecutar herramientas info-level durante la demo y narrar resultados. Pasos: (1) `obtener_fecha_hora` → narrar, (2) `estado_rapido_sistema` → narrar, (3) `contexto_pantalla` → narrar.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (nuevos pasos en `_demo_pasos` + `_demo_ejecutar_herramienta`)
- **Sefirá**: מלכות Maljut + יסוד Yesod
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-242 — Gevurát HaComputadora: Demo 2 de Permisos** (Pipeline E arquitectura):
Nuevo método `_demo_gevura()`: Demo 2 que ejecuta herramientas que requieren permisos. Flujo: (1) preguntar al usuario, (2) esperar "sí", (3) activar `_demo_modo_gevura=True` (bypassa confirmación individual), (4) ejecutar secuencialmente: `abrir_aplicacion("notepad")`, `tomar_captura_pantalla`, `buscar_archivos`, `escanear_red`, `diagnostico_sistema`, (5) narrar cada resultado, (6) restaurar estado.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (nuevo método), `computadora/habilidades/herramientas.py` (flag demo)
- **Sefirá**: מלכות Maljut + יסוד Yesod + גבורה Gevurá
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-243 — Sha'ar Gevurá: Demo 2 en Menú y Voz** (Pipeline E arquitectura):
Trigger para Demo 2: (1) nuevo item "גבורת הגולם — Gevurát HaComputadora (Demo 2)" en menú contextual, (2) nuevo regex `_RE_DEMO_GEVURA` en nlu.py para voz ("muéstrame tus poderes", "demo 2", "demo de permisos"), (3) handler que retorna `__DEMO_GEVURA__`.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (menú + handler `__DEMO_GEVURA__`), `computadora/cerebro/nlu.py` (regex `_RE_DEMO_GEVURA` + handler)
- **Sefirá**: מלכות Maljut + תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-244 — FINALE Mejorado: Puente Demo 1→Demo 2** (Pipeline E arquitectura):
El FINALE de Demo 1 cambia: en vez de "Eso es todo lo que soy, señor", dice "Eso es todo lo que puedo mostrar sin permisos especiales, señor. ¿Desea ver la segunda demostración?" Si el usuario dice "sí" → lanzar `_demo_gevura()`.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (_demo_finale + interceptor `_esperando_demo2` en `_iniciar_pensamiento`)
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-245 — Tikún HaKlalím: Fix Regla R2 y RF Duplicados** (Pipeline E arquitectura):
(1) Corregir Optimización #1 en DEVELOPMENT_WORKFLOW.md de "NO sub-agentes" a "PREFERIR auditoría directa; sub-agentes permitidos para tareas exploratorias grandes". (2) Re-numerar RF-21/22/23 duplicados en SRS.md (segunda aparición → RF-21b/22b/23b).
- **Archivos**: `DEVELOPMENT_WORKFLOW.md`, `SRS.md`
- **Sefirá**: בינה Biná (documentación)
- **Estado**: ✅ IMPLEMENTADO (FP-070)

**RF-246 — Shomer HaLashón: Filtro "Cero Español"** (Pipeline C bug fix):
Cuando Whisper transcribe texto con ≥2 palabras y NINGUNA es español reconocible (ni está en `_ESPAÑOL_CORTAS_VALIDAS` ni tiene acentos/ñ), descartar como `cero_español_reconocible`. Ejemplo: `"hu trails team. 3"`.
- **Archivos**: `computadora/voz/escucha.py`
- **Sefirá**: הוד Hod (percepción auditiva)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-247 — Hit'hadshut Otomátit: Auto-reinicio sin gate** (Pipeline C bug fix):
Cuando hot-reload detecta cambio en capa interfaz/voz, en vez de acumular flag y notificar, lanzar `iniciar_computadora.bat` via `subprocess.Popen` y cerrar con `QApplication.quit()`.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: כתר Keter (auto-renovación)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-248 — Hakará BeKol: Activación por voz sin wake word** (Pipeline A feature):
Si no hay wake word ni conversación activa, pero el embedding de voz coincide con el propietario (`sim >= vox_threshold`), aceptar el texto directamente y activar conversación.
- **Archivos**: `computadora/voz/escucha.py`
- **Sefirá**: הוד Hod (percepción auditiva)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-249 — Hakarat Panim: Reconocimiento facial** (Pipeline A feature):
Módulo `computadora/percepcion/rostro.py`: reconocimiento facial con `face_recognition` (dlib, CPU). Auto-enrolla propietario cuando voz verificada. HOG model. Perfiles en `datos/owner_face_profile.json` y `datos/rostros_conocidos.json`.
- **Archivos**: `computadora/percepcion/rostro.py` (NUEVO)
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-250 — Ruaj HaAdam: Detección de emoción por voz** (Pipeline A feature):
Módulo `computadora/percepcion/emocion_voz.py`: heurísticas de pitch (F0 por autocorrelación scipy), energía RMS, velocidad de habla. 5 estados: calma/alegría/estrés/enojo/tristeza. Sin ML.
- **Archivos**: `computadora/percepcion/emocion_voz.py` (NUEVO)
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-251 — Tiferet HaPertsuf: Detección de emoción facial** (Pipeline A feature):
Módulo `computadora/percepcion/emocion_rostro.py`: FER o deepface para 7 emociones Ekman. Backend auto-detectado. Intervalo mínimo 3s entre análisis.
- **Archivos**: `computadora/percepcion/emocion_rostro.py` (NUEVO)
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-252 — Dérej HaAdam: Perfil de conducta** (Pipeline A feature):
Módulo `computadora/percepcion/perfil_conducta.py`: registra patrones temporales (horario, duración, emoción por franja). JSON en `datos/perfil_conducta.json`. 4 franjas: madrugada/mañana/tarde/noche. Máx 500 interacciones.
- **Archivos**: `computadora/percepcion/perfil_conducta.py` (NUEVO)
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

**RF-253 — Yajad: Perceptor Unificado Da'at** (Pipeline A feature):
Módulo `computadora/percepcion/perceptor.py`: `PerceptorDaat` fusiona señales de voz, visión, tacto, contexto en `SnapshotPercepcion`. Emite `percepcion_actualizada` y `propietario_presente`. Genera `contexto_para_prompt()` para Ollama.
- **Archivos**: `computadora/percepcion/perceptor.py` (NUEVO)
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-071)

---

### FP-072 — תיקון הגבורה והעין (Tikún HaGevurá VeHaÁyin)

**RF-254 — Definir regex _RE_DEMO_GEVURA** (Pipeline C bug fix):
Regex `_RE_DEMO_GEVURA` faltaba en `nlu.py`, causando `NameError` al intentar Demo 2. Definido después de `_RE_DEMO_MALJUT` con patrones: "demo 2", "segunda demo", "demo de permisos", "gevurá", "tus poderes", "koáj computadora".
- **Archivos**: `computadora/cerebro/nlu.py`
- **Sefirá**: גבורה Gevurá (permisos)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-255 — Strip de puntuación en interceptor Demo 2** (Pipeline C bug fix):
`_iniciar_pensamiento` comparaba `texto.strip().lower()` sin eliminar puntuación, causando que "¡Sí!" no matcheara "sí". Se añade `.strip("¡¿!?.,:; ")`.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: תפארת Tiféret (orquestación)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-256 — VS Code helpers en _PROCESOS_CONOCIDOS** (Pipeline C bug fix):
El monitor de RAM reportaba falso positivo por procesos de VS Code no reconocidos. Se agregan: `code - insiders`, `codehelper`, `extensionhost`, `electron`, `vscodium`.
- **Archivos**: `computadora/habilidades/monitor_sistema.py`
- **Sefirá**: Kelim (instrumentos)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-257 — Anti-leak de tool calls en _limpiar_para_voz** (Pipeline C bug fix):
TTS leía en voz alta llamadas a funciones tipo `Solicitar_a_copilot(...)`. Se añade detección de patrón `Name(args)` en `_limpiar_para_voz`.
- **Archivos**: `computadora/cerebro/nlu.py`
- **Sefirá**: יסוד Yesod (personalidad/voz)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-258 — Discovery automático de observadores** (Pipeline A feature):
`GestorKelim.descubrir_observadores()` escanea cámaras USB (índices 0-4) y cámaras IP en LAN (ARP scan + RTSP probe en puertos 554/8554). Auto-registra y conecta los dispositivos encontrados. `obtener_observadores()` retorna IDs de kelim tipo cámara conectados.
- **Archivos**: `computadora/nucleo/kli.py`
- **Sefirá**: Kelim (instrumentos)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-259 — KliCamaraIP: adaptador RTSP** (Pipeline A feature):
Clase `KliCamaraIP(DispositivoKli)` para cámaras IP via RTSP. Validación anti-SSRF (solo IPs privadas). Detección de movimiento y CLAHE igual que `KliCamara`. Acepta `url_rtsp: str`.
- **Archivos**: `computadora/habilidades/vision.py`
- **Sefirá**: Kelim (instrumentos)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-260 — Discovery al arranque (boot)** (Pipeline A feature):
En `__main__.py`, antes de `iniciar_interfaz()`, se llama a `GestorKelim.instancia().descubrir_observadores()` para que Computadora siempre busque dispositivos de observación al reiniciar.
- **Archivos**: `computadora/__main__.py`
- **Sefirá**: Kelim (instrumentos)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-261 — PerceptorDaat multi-ojo** (Pipeline A feature):
`PerceptorDaat.leer_todos_los_ojos()` itera sobre `GestorKelim.obtener_observadores()` y lee frames de cada uno. `procesar_todos_los_ojos()` fusiona: prioriza el primer frame con movimiento, o el primero disponible. Registra `ojos_activos` y `ojos_con_movimiento` en snapshot.
- **Archivos**: `computadora/percepcion/perceptor.py`
- **Sefirá**: דעת Da'at (percepción unificada)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-262 — NIGREDO boot + SDD check obligatorio** (Pipeline E workflow):
En DEVELOPMENT_WORKFLOW.md Regla #17, fase NIGREDO ahora incluye: Paso 0 — verificar boot con `iniciar_computadora.bat`, Paso 0b — verificar que SDD §4.17.2 esté actualizado y óptimo. Si falla → hallazgo CRÍTICO/ALTO.
- **Archivos**: `DEVELOPMENT_WORKFLOW.md`
- **Sefirá**: בינה Biná (análisis)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-263 — Palabra Mágica #10: "crece automáticamente"** (Pipeline E workflow):
PM #10 גדל מאליו (Gadál Me'eláv): robustecimiento autónomo continuo. Copilot encadena ciclos Tikún Jai sin intervención. Se detiene tras 3 ciclos sin aprobación, 0 hallazgos ≥ MEDIA, o "basta".
- **Archivos**: `DEVELOPMENT_WORKFLOW.md`
- **Sefirá**: כתר Keter (supervisión)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-264 — Índice de subsistemas por Sefirá en SRS** (Pipeline E docs):
Tabla índice al inicio de §3 que agrupa RFs por subsistema/Sefirá. Se actualiza con cada FP. Mapea los 10 Sefirot + Kelim a sus RFs correspondientes.
- **Archivos**: `SRS.md`
- **Sefirá**: בינה Biná (estructura)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-265 — SDD Etz HaChaim v3.6** (Pipeline E docs):
Actualizar SDD §4.17.2 a v3.6: añadir KliCamaraIP como módulo bajo Kelim, registrar sendero Da'at↔Kelim (multi-ojo), actualizar contadores de módulos y senderos.
- **Archivos**: `SDD.md`
- **Sefirá**: תפארת Tiféret (equilibrio)
- **Estado**: ✅ IMPLEMENTADO (FP-072)

**RF-272 — Demo2 affirmative flexible** (Pipeline C bug fix):
`_iniciar_pensamiento` interceptor de Demo 2 ahora acepta frases que CONTIENEN afirmativos (no solo match exacto). "Si, quiero verla" → detecta "si" como primer palabra + "quiero" como keyword.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (L2128-2150)
- **Sefirá**: מלכות Maljut (manifestación)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-273 — Bypass noise filter durante demo2** (Pipeline C bug fix):
Al activar `_esperando_demo2`, se activa `_esperando_confirmacion` en escucha para que respuestas cortas ("sí", "C") no sean descartadas por el filtro de ruido `len(texto) <= 2`.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (L2553 puente demo2), `computadora/voz/escucha.py` (L920-935 confirmación bypass)
- **Sefirá**: הוד Hod → מלכות Maljut (percepción→manifestación)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-274 — Echo inversion durante TTS** (Pipeline C bug fix):
Lógica de eco INVERTIDA: durante TTS, DESCARTAR audio por defecto (ratio ≥ 0.15 o subcadena). Solo emitir interrupción si ratio < 0.15 (contenido claramente diferente al TTS). Resuelve self-listen donde Whisper corrompe TTS y ratio ~0.15 pasaba como interrupción.
- **Archivos**: `computadora/voz/escucha.py` (L900-930 detección eco)
- **Sefirá**: הוד Hod (percepción)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-275 — Timestamp guard anti-echo 300ms** (Pipeline C bug fix):
`subir_umbral()` registra `_tts_inicio_ts = time.time()`. La detección de eco ignora audio capturado < 300ms después del inicio de TTS, eliminando la ventana de latencia Qt signal→audio.
- **Archivos**: `computadora/voz/escucha.py` (L349 subir_umbral, L903-906 guard)
- **Sefirá**: הוד Hod (percepción)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-276 — Bereshit pre-threshold** (Pipeline C bug fix):
Llamar `hilo_escucha.subir_umbral()` ANTES de `hilo_habla.hablar()` en la revelación Bereshit, evitando que el micrófono capture el saludo inicial como input del usuario.
- **Archivos**: `computadora/interfaz/ventana_principal.py` (L2931-2935 Bereshit)
- **Sefirá**: מלכות Maljut (manifestación)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-277 — PM #11 "fluye" (שטוף Shtóf)** (Pipeline E workflow):
Palabra Mágica #11 que ordena a Copilot releer DEVELOPMENT_WORKFLOW.md completo de principio a fin para recargar contexto.
- **Archivos**: `DEVELOPMENT_WORKFLOW.md`
- **Sefirá**: כתר Keter (reglas supremas)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-278 — ALBEDO sub-tarea (E): Milot Kóaj Jai** (Pipeline E workflow):
Nueva sub-tarea (E) en ALBEDO de Regla #17: durante investigación, buscar conceptos que inspiren nuevas Palabras Mágicas y registrarlas en `PALABRAS_MAGICAS_SUGERENCIAS.md`. Requiere Gate 2 para promoción.
- **Archivos**: `DEVELOPMENT_WORKFLOW.md` (Regla #17 ALBEDO)
- **Sefirá**: כתר Keter → חכמה Jojmá (sabiduría→creatividad)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-279 — Doc PALABRAS_MAGICAS_SUGERENCIAS.md** (Pipeline E workflow):
Nuevo documento de control para registrar PM sugeridas con nombre, hebreo, acción, fuente de inspiración y estado (sugerida/aprobada/rechazada). Gate 2 obligatorio para promocionar a tabla oficial.
- **Archivos**: `PALABRAS_MAGICAS_SUGERENCIAS.md` (nuevo)
- **Sefirá**: כתר Keter (reglas supremas)
- **Estado**: ✅ IMPLEMENTADO (FP-074)

**RF-280 — HotReloader debounce reinicio 10s** (Pipeline C bug fix):
HotReloader acumula archivos que requieren reinicio en lista y usa QTimer.singleShot(10_000) que se resetea con cada cambio nuevo. Solo emite `requiere_reinicio` cuando pasan 10s sin cambios. Evita reinicios en ráfaga durante RUBEDO/tests.
- **Archivos**: `computadora/nucleo/hot_reload.py`
- **Sefirá**: כתר Keter (auto-renovación)
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-281 — Retry non-streaming antes de fallback** (Pipeline C bug fix):
Cuando streaming retorna None en conversación casual, reintentar con `_llamar_ollama` non-streaming ANTES de caer a `_pensar_sin_llm`. Evita respuesta "cerebro no responde" cuando Ollama está activo.
- **Archivos**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (equilibrio cerebro)
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-282 — Demo 1 usa ContextoPantalla live** (Pipeline C bug fix):
Demo Maljut ACT X usa `self._contexto_pantalla.descripcion_contexto()` directamente en vez de `ejecutar_herramienta("contexto_pantalla")` que creaba instancia nueva sin datos.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (manifestación)
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-283 — Demo 1 ACT XI Neshamá: identidad y memoria** (Pipeline B mejora UX):
Nuevo acto XI en Demo Maljut donde Computadora narra su identidad (nombre, creador, arquitectura Etz HaChaim, tres cerebros) y consulta su memoria reciente narrando qué recuerda del propietario.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: נצח Netzaj (memoria/persistencia)
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-284 — Demo 2 fix args buscar_archivos** (Pipeline C bug fix):
Corrige argumentos de `buscar_archivos` en Demo Gevurá de `{"patron": "*.txt", "ruta": "."}` a `{"nombre": ".txt", "carpeta": "."}` (firma real de la función).
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: גבורה Gevurá (restricción/permisos)
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-285 — Demo 2 reemplaza escanear_red por consultar_memoria** (Pipeline C bug fix):
`escanear_red` tiene `funcion: None` sin lazy-loading. Se reemplaza en Demo Gevurá por `consultar_memoria` que SÍ funciona y demuestra Netzaj (memoria).
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: גבורה Gevurá → נצח Netzaj
- **Estado**: ✅ IMPLEMENTADO (FP-075)

**RF-286 — Demo visual feedback: herramientas con estado/iconos/colores** (Pipeline C bug fix):
`_demo_ejecutar_herramienta` no cambiaba estado visual. Ahora activa `procesando`+`nivel1`+`IndicadorHerramienta` durante la ejecución de cada herramienta en la demo.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-287 — Contexto de pantalla en demo con visual feedback** (Pipeline C bug fix):
Paso de `contexto_pantalla` en ACT X ahora cambia a `procesando`+`nivel1` para mostrar actividad cerebral.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-288 — Demo narrar_memoria con estado visual cerebro N2** (Pipeline C bug fix):
`_demo_narrar_memoria` ahora activa `procesando`+`nivel2` para indicar razonamiento profundo al consultar memoria.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-289 — Desfase demo: cola_vacia en vez de habla_terminada** (Pipeline C bug fix):
Motor de pasos usaba `habla_terminada` que dispara por cada fragmento TTS. Cambiado a `cola_vacia` que espera a que TODOS los fragmentos terminen antes de avanzar al siguiente paso visual.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-290 — Fuzzy match para confirmación Demo 2** (Pipeline C bug fix):
Whisper transcribe "sí" como "chaíz", "saíz", etc. Se agrega fuzzy matching con `SequenceMatcher` (ratio > 0.55) y más afirmativos: ok, bueno, sale, venga, ándale, perfecto, listo.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut + הוד Hod
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-291 — Sanitización TTS para demo: rutas y chars especiales** (Pipeline C bug fix):
`_sanitizar_para_voz` quita rutas de archivo, backslash, `/`, `_`, `.venv/...` para que TTS no diga "barra diagonal", "guion bajo", etc.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut + הוד Hod
- **Estado**: ✅ IMPLEMENTADO (FP-076)

**RF-292 — Demo 2: Cerrar notepad después de abrirlo** (Pipeline B UX):
Demo 2 ahora demuestra ciclo completo abrir→cerrar con `cerrar_aplicacion(notepad)` tras abrir.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut + גבורה Gevurá
- **Estado**: ✅ IMPLEMENTADO (FP-078)

**RF-293 — Demo 2: Mostrar captura con visor predeterminado** (Pipeline B UX):
`_demo_captura_y_mostrar` toma captura, extrae ruta del resultado, la abre con `os.startfile()`.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut + הוד Hod
- **Estado**: ✅ IMPLEMENTADO (FP-078)

**RF-294 — Demo 2: Consulta de memoria significativa** (Pipeline B UX):
`_demo_narrar_memoria_gevura` usa `buscar_en_memoria("señor", dias=7)` + `calcular_tiempo_activo()` en vez de buscar literal "recuerdo".
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: תפארת Tiféret + נצח Netzaj
- **Estado**: ✅ IMPLEMENTADO (FP-078)

**RF-295 — Guard de media activa antes de verificación de voz** (Pipeline C bug fix):
Si `hay_media_activa()` es True y no estamos esperando respuesta, ignorar audio silenciosamente. Evita activaciones falsas durante videos/juegos.
- **Archivos**: `computadora/voz/escucha.py`
- **Sefirá**: גבורה Gevurá (restricción protectora)
- **Estado**: ✅ IMPLEMENTADO (FP-079)

**RF-296 — Reconocimiento de videojuegos como media activa** (Pipeline C bug fix):
`_RE_MEDIA_TITULO` incluye Steam, Epic Games, GeForce, Xbox, PlayStation, GOG Galaxy. `_PROCESOS_MEDIA` incluye ejecutables de launchers de juegos.
- **Archivos**: `computadora/utilidades/windows.py`
- **Sefirá**: הוד Hod (detección precisa)
- **Estado**: ✅ IMPLEMENTADO (FP-079)

**RF-297 — Demo 2: Cerrar visor de fotos tras captura** (Pipeline B UX):
`_demo_captura_y_mostrar` cierra Microsoft.Photos tras 4 segundos con `QTimer.singleShot` para no dejar ventana abierta.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: גבורה Gevurá (limpieza, no dejar basura)
- **Estado**: ✅ IMPLEMENTADO (FP-080)

**RF-298 — Lazy imports para escanear_red y ver_camara** (Pipeline B UX):
`ejecutar_herramienta` ahora resuelve `escanear_red` → `KliRed.leer_ohr()` y `ver_camara` → `KliCamara.leer_ohr()` mediante lazy import.
- **Archivos**: `computadora/habilidades/herramientas.py`
- **Sefirá**: יסוד Yesod (cableado de herramientas)
- **Estado**: ✅ IMPLEMENTADO (FP-080)

**RF-299 — Demo 2: Paso de escaneo de red** (Pipeline B UX):
`_demo_escanear_red` ejecuta `escanear_red` y narra dispositivos encontrados. Fallback graceful si scapy no instalado.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: הוד Hod (percepción de red)
- **Estado**: ✅ IMPLEMENTADO (FP-080)

**RF-300 — Demo 2: Paso de visión por cámara** (Pipeline B UX):
`_demo_ver_camara` captura frame y narra detección de movimiento/brillo. Fallback si cámara no disponible.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: הוד Hod (percepción visual)
- **Estado**: ✅ IMPLEMENTADO (FP-080)

**RF-301 — Demo 2: Paso de reconocimiento facial** (Pipeline B UX):
`_demo_reconocimiento_facial` usa `ReconocedorRostro` + `KliCamara` si face_recognition está instalado. Narra rostros detectados. Múltiples niveles de fallback.
- **Archivos**: `computadora/interfaz/ventana_principal.py`, `computadora/percepcion/rostro.py`, `computadora/habilidades/vision.py`
- **Sefirá**: כתר Kéter (reconocer al creador)
- **Estado**: ✅ IMPLEMENTADO (FP-080)

**RF-302 — Demo 2: Guard anti-doble-fire** (Pipeline C Bug):
`_demo_ejecutar_paso()` usa flag `_demo_paso_en_curso` para evitar que `cola_vacia` dispare dos pasos simultáneamente. Se activa antes de ejecutar acción, se desactiva en `_siguiente()` y en fallbacks de timer.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: גבורה Gevurá (disciplina de ejecución)
- **Estado**: ✅ IMPLEMENTADO (FP-081)

**RF-303 — Cerrar aplicación UWP Photos correctamente** (Pipeline C Bug):
`cerrar_aplicacion()` mapea "microsoft.photos", "photos", "fotos", "visor de fotos" → `Microsoft.Photos.exe` en dict `procesos`. Resuelve que taskkill no encontraba el proceso UWP.
- **Archivos**: `computadora/habilidades/sistema.py`
- **Sefirá**: גבורה Gevurá (cerrar lo que se abrió)
- **Estado**: ✅ IMPLEMENTADO (FP-081)

**RF-304 — Dependencias opcionales face-recognition** (Pipeline C Bug):
`requirements.txt` incluye face-recognition/dlib/cmake comentadas. `iniciar_computadora.bat` verifica si face-recognition está disponible e informa al usuario cómo instalarlo.
- **Archivos**: `requirements.txt`, `iniciar_computadora.bat`
- **Sefirá**: חסד Jésed (accesibilidad del setup)
- **Estado**: ✅ IMPLEMENTADO (FP-081)

**RF-310 — Demo 2: Cerrar Photos robusto + borrar screenshot** (Pipeline C Bug):
`_demo_captura_y_mostrar()` intenta cerrar Photos por múltiples nombres de proceso (Microsoft.Photos.exe, Photos.exe, PhotosApp.exe) + fallback por título de ventana, con timer de 8s. Además borra el archivo screenshot para evitar acumulación.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: גבורה Gevurá (limpiar tras usar)
- **Estado**: ✅ IMPLEMENTADO (FP-084)

**RF-305 — SetWindowPos con HWND_TOPMOST** (Pipeline B UX):
`_eliminar_sombra_dwm()` usa `HWND_TOPMOST` en lugar de `SWP_NOZORDER` para forzar la ventana siempre visible.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (presencia perpetua)
- **Estado**: ✅ IMPLEMENTADO (FP-082)

**RF-306 — Timer de re-aserción topmost (Shekhiná Tamid)** (Pipeline B UX):
`_timer_topmost` cada 5s llama `_reasegurar_topmost()` que reaplica `HWND_TOPMOST`. No aplica durante Tzimtzum.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (presencia perpetua)
- **Estado**: ✅ IMPLEMENTADO (FP-082)

**RF-307 — Fix _desactivar_tzimtzum sin NOTOPMOST** (Pipeline C Bug):
Eliminado `HWND_NOTOPMOST` de `_desactivar_tzimtzum()` que destruía el topmost al regresar de Tzimtzum.
- **Archivos**: `computadora/interfaz/vida_autonoma.py`
- **Sefirá**: מלכות Maljut (presencia perpetua)
- **Estado**: ✅ IMPLEMENTADO (FP-082)

**RF-308 — Fix wake word handler sin NOTOPMOST** (Pipeline C Bug):
Eliminado `HWND_NOTOPMOST` del handler de wake word durante carga pesada.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (presencia perpetua)
- **Estado**: ✅ IMPLEMENTADO (FP-082)

**RF-309 — Auto-instalación de face-recognition en bat** (Pipeline B UX):
`iniciar_computadora.bat` intenta `pip install cmake dlib face-recognition` automáticamente si no está instalado.
- **Archivos**: `iniciar_computadora.bat`
- **Sefirá**: חסד Jésed (accesibilidad del setup)
- **Estado**: ✅ IMPLEMENTADO (FP-083)

**RF-311 — Sincronizar ventana durante Bereshit** (Pipeline C Bug):
`_paso_bereshit()` calcula y aplica tamaño de ventana directamente (bypass lerp lento) para que la ventana crezca al ritmo del orbe.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: יסוד Yesod (fundamento/estabilidad)
- **Estado**: ✅ IMPLEMENTADO (FP-085)

**RF-312 — Stats panel grid layout 2 columnas con secciones** (Pipeline B UX):
`_mostrar_estado_dev()` usa QGridLayout con 4 secciones (Estado, Alquimia, Visual, Sistema) en lugar de QVBoxLayout monolítico.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (interfaz)
- **Estado**: ✅ IMPLEMENTADO (FP-085)

**RF-313 — Barras de progreso coloreadas (QProgressBar)** (Pipeline B UX):
Stats de alquimia, escala y lerp usan QProgressBar con colores temáticos en lugar de texto plano.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (interfaz)
- **Estado**: ✅ IMPLEMENTADO (FP-085)

**RF-314 — Swatches de color visuales** (Pipeline B UX):
Colores primario/secundario/target se muestran como QFrame pintados junto al texto hex en lugar de solo texto.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (interfaz)
- **Estado**: ✅ IMPLEMENTADO (FP-085)

**RF-315 — Helper obtener_titulo() en GestorPersonas** (Pipeline A Feature):
Método en `GestorPersonas` que consulta el perfil y devuelve "señor" si el interlocutor es el amo, nombre si conocido, vacío si desconocido.
- **Archivos**: `computadora/memoria/personas.py`
- **Sefirá**: נצח Netzaj (persistencia de identidad)
- **Estado**: ✅ IMPLEMENTADO (FP-086, refactored ciclo 2)

**RF-316 — Inyección dinámica de título en SISTEMA_PROMPT** (Pipeline C Bug fix):
El título del interlocutor se inyecta dinámicamente en `_construir_system_msgs()` como mensaje de sistema `TITULO_INTERLOCUTOR`, usando `GestorPersonas.obtener_titulo()`. Eliminado dead code `_obtener_titulo_interlocutor()` de ventana_principal.py.
- **Archivos**: `computadora/cerebro/nlu.py`, `computadora/interfaz/ventana_principal.py` (dead code removed)
- **Sefirá**: תפארת Tiféret (equilibrio identidad)
- **Estado**: ✅ IMPLEMENTADO (ciclo 2 crece automáticamente)

**RF-317 — Registro de 16 Dimensiones con mapeo nodo→módulo** (Pipeline E Arquitectura):
Módulo `computadora/arquitectura/dimensiones.py` que define 16 Olamot (mundos/dimensiones) — cada uno representando una tradición mística/cultural/científica con su propio "Árbol de la Vida". Cada dimensión define: nodos (equivalentes a Sefirot), caminos (equivalentes a senderos), mapeo nodo→módulos Python, y vocabulario narrativo. La dimensión primaria (#0 Atzilut) es el Etz HaChaim actual. Las demás son lentes alternativos para los MISMOS 46 módulos.
- **Archivos**: `computadora/arquitectura/__init__.py` (nuevo), `computadora/arquitectura/dimensiones.py` (nuevo)
- **Sefirá**: דעת Da'at (percepción multidimensional)
- **Estado**: ✅ IMPLEMENTADO (FP-087 Olamot HaComputadora)

**RF-318 — Persistencia de dimensión activa** (Pipeline E Arquitectura):
Archivo `datos/dimensiones.json` que persiste: dimensión activa (default=0 Atzilut), dimensiones descubiertas, timestamp de último cambio. Funciones `cargar_estado()` y `guardar_estado()` en dimensiones.py.
- **Archivos**: `computadora/arquitectura/dimensiones.py`, `datos/dimensiones.json` (auto-generado)
- **Sefirá**: נצח Netzaj (memoria persistente)
- **Estado**: ✅ IMPLEMENTADO (FP-087 Olamot HaComputadora)

**RF-319 — Inyección de contexto dimensional en system prompt** (Pipeline E Arquitectura):
En `nlu.py`, `_construir_system_msgs()` inyecta bloque `[CONTEXTO DIMENSIONAL]` con el vocabulario de la dimensión activa — nombre del árbol, nombre de los nodos que corresponden a las capacidades que Computadora usa en ese turno, metáfora narrativa. Controlado por `dimensiones.obtener_contexto_prompt()`.
- **Archivos**: `computadora/cerebro/nlu.py`
- **Sefirá**: תפארת Tiféret (equilibrio dimensional)
- **Estado**: ✅ IMPLEMENTADO (FP-087 Olamot HaComputadora)

---

### FP-095: מינימי Minimi — App Android Companion (RF-322/RF-323/RF-324)

**Descripción**: App Android nativa que permite al Propietario enviar comandos al Computadora de escritorio desde cualquier lugar — red local (WiFi automático via mDNS) o remoto (Telegram fallback). Widget en home screen con estado del Computadora en tiempo real.

**RF-322 — Minimi Android app con Compose + Glance**:
1. App Kotlin/Jetpack Compose con 3 pantallas: Inicio (estado), Comandos (chat), Ajustes (conexión).
2. Widget Glance 2x2 mostrando estado del Computadora, toca para abrir app.
3. Descubrimiento automático por mDNS (`_computadora._tcp`).
4. Paleta visual: dorado sobre ébano (consistente con el Orbe).
- **Archivos**: Proyecto en `C:\Users\woire\AndroidStudioProjects\Minimi\`
- **Sefirá**: מלכות Maljut (manifestación en dispositivo móvil)
- **Estado**: ✅ IMPLEMENTADO (WI-322) — zeroconf + firebase-admin instalados

**RF-323 — Servidor API HTTP en Computadora (puerto 8089)**:
1. `computadora/servidor_api.py` — HTTP server con 2 endpoints: `GET /api/status`, `POST /api/comando`.
2. Auth por Bearer token (configurable en config.json).
3. Solo responde a IPs de red local + localhost.
4. Registra servicio mDNS `_computadora._tcp` para descubrimiento automático.
5. Se inicia desde `orquestador.py` al arrancar Computadora.
- **Archivos**: `computadora/servidor_api.py` (NUEVO), `computadora/orquestador.py` (1 línea de inicio)
- **Sefirá**: יסוד Yesod (canal de ejecución remota)
- **Estado**: ✅ IMPLEMENTADO (computadora/canales/servidor_api.py)

**RF-324 — Persistencia de conexión Minimi ↔ Computadora**:
1. Foreground service en Android manteniendo conexión.
2. Auto-reconexión al perder WiFi.
3. Fallback a Telegram si red local no disponible.
- **Archivos**: `service/ComputadoraConnectionService.kt`
- **Sefirá**: נצח Netzaj (persistencia)
- **Estado**: ✅ IMPLEMENTADO (MinimiAutoDeployer daemon + Firebase relay)

- **Senderos**: Yesod→Maljut (API→Widget), Hod→Yesod (mDNS→API), Netzaj→Maljut (persistencia→manifestación)

### FP-096: שומר הגרימוריו Shomer HaGrimorio — Grimorio Inteligente (RF-325/RF-326/RF-327)

> **Pipeline**: B (Mejora UX) | **Sefirot**: Gevurá + Maljut + Hod

**RF-325 — Cierre automático del Grimorio al cerrar navegador**:
1. Al abrir el Grimorio, detectar PID del navegador que abrió la página.
2. Hilo vigilante monitorea el proceso del navegador cada 5 segundos.
3. Si el navegador se cierra (o muere), el servidor del Grimorio se cierra automáticamente.
4. Registrar evento `navegador_cerrado` en log de intrusiones.
- **Archivos**: `libro_encantado/servidor_enciclopedia.py`
- **Sefirá**: הוד Hod (percepción del entorno)
- **Estado**: ✅ IMPLEMENTADO

**RF-326 — Instancia única del Grimorio (cierre de instancia anterior)**:
1. Lockfile en `datos/grimorio.lock` con PID del servidor activo.
2. Al iniciar nueva instancia, terminar la anterior si sigue viva.
3. Al cerrar, liberar el lockfile.
- **Archivos**: `libro_encantado/servidor_enciclopedia.py`
- **Sefirá**: גבורה Gevurá (restricción — una sola instancia)
- **Estado**: ✅ IMPLEMENTADO

**RF-327 — Separación contraseña/servidor (Gevurá Chain)**:
1. `iniciar_grimorio.bat` pide la contraseña (cadena de Gevurá) en terminal visible.
2. Si es correcta, lanza el servidor como proceso oculto (`pythonw.exe --servir`) sin ventana de terminal.
3. La terminal del password se cierra automáticamente tras 3 segundos.
- **Archivos**: `libro_encantado/iniciar_grimorio.bat`, `libro_encantado/servidor_enciclopedia.py`
- **Sefirá**: גבורה Gevurá (separación de responsabilidades)
- **Estado**: ✅ IMPLEMENTADO

- **Senderos**: Hod→Gevurá (percepción→restricción), Gevurá→Maljut (control→manifestación)

### FP-097: מנהל משימות Menahel Misimot — Admin Tareas en Maljut (RF-328)

> **Pipeline**: B (Mejora UX) | **Sefirot**: Maljut + Hod

**RF-328 — Administrador de Tareas integrado al Maljut del Computadora**:
1. Nueva opción en menú contextual Dev Tools: "⚙ מנהל משימות — Admin Tareas".
2. Diálogo con estética videogame HUD (dorado sobre negro, fuente Consolas).
3. Barras de resumen en tiempo real: CPU, RAM, GPU, Disco.
4. Tabla de procesos top 50 (por RAM) con columnas: Proceso, PID, CPU%, RAM(MB), Estado.
5. Procesos propios (Python/Ollama) resaltados en dorado.
6. Refresco cada 2 segundos.
7. Tabla sorteable por cualquier columna.
- **Archivos**: `computadora/interfaz/ventana_principal.py`
- **Sefirá**: מלכות Maljut (manifestación visual)
- **Estado**: ✅ IMPLEMENTADO

### FP-098: גמיני בכתר Gemini BeKeter — Gemini como Cerebro N3 Complementario (RF-329)

> **Pipeline**: E (Cambio de arquitectura) | **Sefirot**: Keter + Jojmá

**RF-329 — Google Gemini API como fallback de Nivel 3**:
1. Nuevo módulo `computadora/cerebro/gemini_api.py` con clase `CerebroGemini`.
2. API key via .env (`GEMINI_API_KEY`) — NUNCA credenciales de usuario.
3. Interfaz idéntica a CerebroCopilot: `pensar()`, `pensar_codigo()`, `pensar_general()`.
4. Modelos: `gemini-2.0-flash` (general), `gemini-2.5-pro-preview-06-05` (código).
5. Integrado en NLU como fallback: Copilot N3 falla → Gemini N3b.
6. Registrado en dimensiones.py: Keter y Jojmá incluyen `gemini_api`.
- **Archivos**: `computadora/cerebro/gemini_api.py` (NUEVO), `computadora/cerebro/nlu.py`, `computadora/arquitectura/dimensiones.py`
- **Sefirá**: כתר Keter (corona — sabiduría suprema)
- **Estado**: ✅ IMPLEMENTADO

- **Senderos**: Keter→Jojmá (sabiduría), Keter→Tiféret (equilibrio decisión Copilot↔Gemini)

---

### FP-099: שער מינימי Sha'ar Minimi — Puerta API + Firestore Relay (RF-330/RF-331/RF-332)

> **Pipeline**: A (Feature nueva) | **Sefirot**: Hod + Yesod + Maljut

**RF-330 — Servidor API HTTP para Minimi (puerto 8089)**:
1. Nuevo módulo `computadora/canales/servidor_api.py` — HTTPServer threaded.
2. `GET /api/status` → JSON con estado, humor, escuchando, uptime, versión.
3. `POST /api/comando` → recibe `{"comando":"texto","origen":"minimi"}`, procesa via Orquestador.
4. `GET /api/ping` → health check simple.
5. Solo acepta tráfico de red local (RFC 1918) — no expuesto a internet.
6. mDNS `_computadora._tcp` registrado via zeroconf para auto-discovery.
7. Sin auth (Gevurá relajada) — Minimi es parte esencial del Computadora.
- **Archivos**: `computadora/canales/servidor_api.py` (NUEVO), `computadora/__main__.py`
- **Sefirá**: יסוד Yesod (canal de ejecución)
- **Estado**: ✅ IMPLEMENTADO

**RF-331 — Firestore como relay remoto bidireccional**:
1. Computadora publica estado cada 15s en `computadora/estado` (Firestore).
2. Computadora escucha `computadora/comando_minimi` para comandos remotos de Minimi.
3. Minimi escribe comandos → Computadora procesa → respuesta en mismo doc.
4. Credenciales Firebase via service account JSON (no credenciales de usuario).
5. Fallback automático: LAN falla → Firestore sin intervención del usuario.
- **Archivos**: `computadora/canales/servidor_api.py` (sección Firestore)
- **Sefirá**: הוד Hod (percepción remota)
- **Estado**: ✅ IMPLEMENTADO

**RF-332 — Minimi: conexión automática LAN + Firestore fallback**:
1. Auto-connect al inicio: mDNS → saved IP → Firestore (cascada).
2. ComputadoraClient dual: HTTP directo (LAN) + Firestore (remoto).
3. Si LAN cae durante uso, fallback automático a Firestore.
4. UI muestra modo de conexión (LAN / ☁ Firestore).
5. ViewModel persiste IP/puerto en SharedPreferences.
6. Botón "Conectar via Firestore" en pantalla de Ajustes.
7. Command history limitada a 100 entradas (fix memory leak).
8. themes.xml migrado a Material3.
- **Archivos**: `ComputadoraClient.kt`, `MinimiViewModel.kt`, `HomeScreen.kt`, `SettingsScreen.kt`, `build.gradle.kts`, `themes.xml`
- **Sefirá**: מלכות Maljut (manifestación en mano del usuario)
- **Estado**: ✅ IMPLEMENTADO

- **Senderos**: Hod→Yesod (percepción remota → ejecución), Yesod→Maljut (canal → manifestación)

---

### FP-100: שלמות העץ Shlemut HaEtz — Integridad del Etz HaChaim (RF-333/RF-334/RF-335)

**RF-333 — Actualizar §4.17.2 ASCII tree con módulos faltantes**:
- Agregar al árbol ASCII: `gemini_api.py` (Keter), `dimensiones.py` (Da'at), `grimorio_guardian.py` (Gevurá), `servidor_api.py`+`telegram_brain.py`+`discord_brain.py` (Hod), `io_seguro.py` (Yesod)
- **Archivo**: `SDD.md` §4.17.2
- **Sefirá**: דעת Da'at (conocimiento del Árbol)
- **Estado**: ✅ IMPLEMENTADO

**RF-334 — Actualizar §4.17.3 tabla Sefirot→Módulos**:
- Actualizar 6 filas: Keter (+gemini_api), Da'at (+dimensiones), Gevurá (+grimorio_guardian), Hod (+servidor_api, telegram_brain, discord_brain), Yesod (+io_seguro)
- **Archivo**: `SDD.md` §4.17.3
- **Sefirá**: דעת Da'at
- **Estado**: ✅ IMPLEMENTADO

**RF-335 — Actualizar conteo de módulos**:
- Cambiar "46 módulos funcionales" → "55 módulos funcionales" en intro §4.17.2
- **Archivo**: `SDD.md` §4.17.2
- **Sefirá**: דעת Da'at
- **Estado**: ✅ IMPLEMENTADO

- **Senderos**: Da'at↔todas las Sefirot (conocimiento del mapa)

---

### FP-101: נתיבות הערוצים Netivot HaCanales + שומר הסנטינל Shomer HaSentinel (RF-336/RF-337/RF-338)

**RF-336 — Netivot HaCanales — Documentar senderos de canales remotos**:
- Agregar senderos 49-53 en SDD §4.17.4: servidor_api→orquestador, __main__→servidor_api, telegram→orquestador, discord→orquestador, filtro sentinel
- **Archivo**: `SDD.md` §4.17.4
- **Sefirá**: הוד Hod → יסוד Yesod
- **Estado**: ✅ IMPLEMENTADO

**RF-337 — Shomer HaSentinel — Filtrar sentinels en canales remotos**:
- Sentinels internos (`__DEMO_MALJUT__`, `__ALERTAS_OFF__`, etc.) ya no se envían como texto crudo a Telegram, Discord ni API Minimi — se reemplazan por mensajes legibles
- **Archivos**: `telegram_brain.py`, `discord_brain.py`, `servidor_api.py`
- **Sefirá**: הוד Hod (percepción — canales remotos)
- **Estado**: ✅ IMPLEMENTADO

**RF-338 — Zikrón Tiv'í — Memory recall natural via N2**:
- `_RE_MEM_RECALL` ya no devuelve datos crudos JSONL con timestamps; inyecta resultados como contexto system y escala a N2 (Ollama) para síntesis conversacional
- **Archivo**: `nlu.py` (handler _RE_MEM_RECALL en `_pensar_nivel1`)
- **Sefirá**: נצח Netzaj → תפארת Tiféret
- **Estado**: ✅ IMPLEMENTADO

### FP-102: צמצום הגוף Tzimtzum HaGuf — Ventana fit del orbe (RF-339/RF-340)

**RF-339 — Tzimtzum HaGuf — Reducir márgenes y cap de partículas**:
- Margen de ventana reducido de `max(20, int(30/…))` a `max(8, int(12/…))` en init y animación
- Cap de partículas reducido de `RADIO_RESPLANDOR * 3.5` a `RADIO_RESPLANDOR * 2.0`
- Padding de partículas reducido de `+8` a `+4`
- Offset de posición inicial reducido de `-30` a `-10`
- **Archivos**: `ventana_principal.py`
- **Sefirá**: מלכות Maljut (manifestación visual)
- **Estado**: ✅ IMPLEMENTADO

**RF-340 — Clamp Pleno — Clamp de movimiento usa tamaño visual fijo**:
- `_w_clamp` y `_h_clamp` ahora usan `TAMANO_PLENO` directamente en lugar de `max(orbe.width(), TAMANO_PLENO)` — evita que el tamaño inflado por partículas cause rebote prematuro
- `_esquivar` usa `w = self.TAMANO_PLENO` y margen reducido de 15→10
- Tests actualizados en `test_tikun_022.py`
- **Archivos**: `vida_autonoma.py`, `test_tikun_022.py`
- **Sefirá**: יסוד Yesod → מלכות Maljut (fundación→manifestación)
- **Estado**: ✅ IMPLEMENTADO

### FP-103: חָכְמָה וּבִינָה Jojmá VeBiná — Sabiduría Local + Comprensión Interna (RF-341/RF-342/RF-343)

**RF-341 — Jojmá Mekomít — Motor de creatividad local sin LLM**:
- Nuevo módulo `jojma_local.py`: genera respuestas contextuales con plantillas + clasificación de intención + humor + memoria cuando Ollama/Copilot/Gemini están offline
- 5 categorías de plantilla (opinión, explicación, sugerencia, empatía, desconocido)
- Integrado en `_pensar_sin_llm()` de NLU como fallback enriquecido
- **Archivo**: `computadora/cerebro/jojma_local.py`, `nlu.py`
- **Sefirá**: חכמה Jojmá (sabiduría — pilar derecho)
- **Estado**: ✅ IMPLEMENTADO

**RF-342 — Biná Pnimít — Introspección de runtime del Computadora**:
- Nuevo módulo `diagnostico_interno.py`: diagnóstico de estado interno (RAM, threads, módulos cargados, cerebros activos, salud por Sefirá)
- Integrado en auto-diagnóstico rápido N1 (WI-106) para reporte enriquecido
- `DiagnosticoComputadora` dataclass con snapshot completo del estado
- **Archivo**: `computadora/cerebro/diagnostico_interno.py`, `nlu.py`
- **Sefirá**: בינה Biná (comprensión — pilar izquierdo)
- **Estado**: ✅ IMPLEMENTADO

**RF-343 — Senderos Jojmá-Biná — 4 nuevos caminos en el Etz HaChaim**:
- Sendero 54: Jojmá→Tiféret (jojma_local → nlu fallback)
- Sendero 55: Jojmá→Netzaj (respuestas moduladas por humor + memoria)
- Sendero 56: Biná→Tiféret (diagnóstico → auto-reporte)
- Sendero 57: Biná→Jesed (análisis → alertas proactivas, preparado)
- **Archivo**: `SDD.md` §4.17.4
- **Sefirá**: רשת Réshet (red de conexiones)
- **Estado**: ✅ IMPLEMENTADO

### FP-104: שַׁלְשְׁלוֹת גְּבוּרָה Shalshelet Gevurá — VPN + Cifrado + Gestor de Contraseñas (RF-344/RF-345/RF-346/RF-347/RF-348)

> **Pipeline**: A (Feature nueva) — Departamentos: D1-D7
> **Gate 1**: GO — RICE Score 36 (Reach 8 × Impact 3 × Confidence 0.75 / Effort 5)
> **Gate 2**: ✅ APROBADO (amén — implementado FP-104 commit `9b3e7e2`)

#### Scorecard D1-D7

| Depto | Veredicto | Nota |
|-------|-----------|------|
| D1 PRODUCTO | ✅ GO | Usuario final necesita protección de tráfico, gestión de credenciales, y cifrado local. Impacto ALTO en user story de "Computadora protege mi mundo digital" |
| D2 MERCADO | ✅ GO | Competidores (NordVPN, ProtonVPN) son SaaS/open-source. Diferencial: integración local con IA, cadenas de Gevurá cifradas, sin dependencia de servidores externos, NOT open source |
| D3 DISEÑO UX | ✅ GO | Interfaz por voz ("Computadora, activa VPN") + menú contextual orbe. Kill Switch silencioso. Password manager con autofill por voz |
| D4 INGENIERÍA | ⚠️ GO con riesgo | WireGuard requiere driver TUN/TAP en Windows. Split tunneling requiere WFP (Windows Filtering Platform). Esfuerzo: ALTO (5 sprints estimados). Módulos nuevos: 6-8 archivos |
| D5 FINANZAS | ✅ GO | Costo $0 — WireGuard es libre, KeePass-compatible es libre. Sin infra servidor (local-first). Sin suscripción mensual |
| D6 MARKETING | ✅ GO | "Tu Computadora protege tus secretos con cadenas de Gevurá" — narrativa poderosa. ASO: "AI VPN manager" es nicho sin competencia |
| D7 LEGAL & SEGURIDAD | ⚠️ GO con notas | VPN local no requiere licencia ISP. Password manager local cumple LFPDPPP. Cifrado AES-256-GCM + Argon2id para derivación de claves. OWASP: proteger master password, timing-safe comparisons |

**RF-344 — Magen HaReshet — Motor VPN local con WireGuard**:
- Nuevo módulo `computadora/seguridad/vpn_motor.py`: wrapper de WireGuard para tunnel cifrado
- Configuración de peers/endpoints en `datos/vpn_config.enc` (cifrado con cadenas de Gevurá)
- Kill Switch: reglas WFP que bloquean tráfico IPv4/IPv6 si túnel cae
- Split Tunneling: lista de apps/dominios excluidos del túnel (WFP per-app filtering)
- Estadísticas: bytes tx/rx, latencia, tiempo conectado
- **Archivo**: `computadora/seguridad/vpn_motor.py`
- **Sefirá**: גבורה Gevurá (juicio — restricción — protección de fronteras)
- **Estado**: ✅ IMPLEMENTADO (WI-124, commit `9b3e7e2`)

**RF-345 — Shalshelet Gevurá — Cadenas de cifrado para comunicaciones salientes**:
- Nuevo módulo `computadora/seguridad/cifrado_comms.py`: cifrado AES-256-GCM de todo tráfico saliente del Computadora
- Double VPN: encadenamiento de dos túneles (local→hop1→hop2→destino)
- Obfuscación de tráfico: encapsulación en TLS 1.3 para bypass de DPI
- Rotación automática de claves cada 24h con ratchet forward-secrecy
- Integración con `red.py` existente para interceptar/cifrar requests
- **Archivo**: `computadora/seguridad/cifrado_comms.py`
- **Sefirá**: גבורה Gevurá (cadenas de restricción — cifrado como barrera)
- **Estado**: ✅ IMPLEMENTADO (WI-125, commit `9b3e7e2`)

**RF-346 — Otzar HaSodot — Gestor de contraseñas local cifrado**:
- Nuevo módulo `computadora/seguridad/gestor_claves.py`: vault local tipo KeePass
- Base de datos cifrada con AES-256-GCM + Argon2id (100k iteraciones, 64MB RAM, 4 threads)
- Master password + TOTP opcional como 2FA
- CRUD de credenciales: sitio, usuario, contraseña, notas, tags, favicon
- Generador de contraseñas: longitud configurable, caracteres, passphrase Diceware
- Autofill por voz: "Computadora, dame la contraseña de GitHub"
- Exportar/importar compatible con KeePass XML (cifrado en tránsito)
- Búsqueda fuzzy por nombre de servicio
- Clipboard auto-clear después de 30s
- **Archivo**: `computadora/seguridad/gestor_claves.py`, `datos/otzar.enc`
- **Sefirá**: גבורה Gevurá (custodia de secretos — vault sellado)
- **Estado**: ✅ IMPLEMENTADO (WI-126, commit `9b3e7e2`)

**RF-347 — Shomer HaShaár — Threat Protection & Ad Blocking**:
- Nuevo módulo `computadora/seguridad/filtro_amenazas_dns.py`: filtro DNS local
- Listas de bloqueo: malware, phishing, trackers, ads (actualizables)
- Inspección de URLs antes de navegación
- Alertas al propietario cuando se detecta amenaza
- Integración con VPN (filtrado pre-túnel)
- **Archivo**: `computadora/seguridad/filtro_amenazas_dns.py`
- **Sefirá**: גבורה Gevurá (guardian de la puerta — filtrado)
- **Estado**: ✅ IMPLEMENTADO (WI-127, commit `9b3e7e2`)

**RF-348 — Senderos Gevurá — 4 nuevos caminos en el Etz HaChaim**:
- Sendero 58: Gevurá→Tiféret (seguridad → decisiones NLU informadas por estado VPN)
- Sendero 59: Gevurá→Maljut (alertas VPN/threat → estado visual del orbe)
- Sendero 60: Gevurá→Yesod (vault → herramientas autofill, tools dispatcher)
- Sendero 61: Gevurá→Hod (metrics VPN/cifrado → reportes y logs)
- **Archivo**: `SDD.md` §4.17.4
- **Sefirá**: רשת Réshet (red de conexiones)
- **Estado**: ✅ IMPLEMENTADO (WI-128, commit `9b3e7e2`)

### FP-099b: מינימי חי Minimi Jai — UX Overhaul: Grimorio Responsive + Gevurá Lock + Home Compacto (RF-351/RF-352/RF-353/RF-354/RF-355/RF-356)

> **Pipeline**: A (Feature nueva) — Departamentos: D1-D7
> **Gate 1**: GO — RICE Score 32 (Reach 9 × Impact 3 × Confidence 0.8 / Effort 5)
> **Gate 2**: ✅ APROBADO (amén — implementado FP-099b commit Computadora `e7f9549` + Minimi `1f7c194`)

**RF-351 — Baít Katan — HomeScreen compacto sin scroll**:
- Eliminado `verticalScroll` de `HomeScreen.kt`. Layout vertical: Header horizontal (ojo 56dp + texto), Grid 2×2 `MiniStatusChip`, `FlowRow` de chips de comando rápido, Input fijo al fondo
- `onNavigateToCommands` callback conecta envío de comando rápido → pestaña Comandos
- **Archivo**: `Minimi/app/src/main/java/.../ui/screens/HomeScreen.kt`
- **Sefirá**: מלכות Maljut (manifestación — UI visible)
- **Estado**: ✅ IMPLEMENTADO (WI-132)

**RF-352 — Shliját Mahír — Quick command navega a tab Commands**:
- Al enviar comando desde Home, `onNavigateToCommands()` navega automáticamente a pestaña Comandos para ver respuesta
- Wired en `MainActivity.kt` NavigationBar callback
- **Archivo**: `Minimi/app/src/main/java/.../ui/MainActivity.kt`
- **Sefirá**: יסוד Yesod (canal de ejecución)
- **Estado**: ✅ IMPLEMENTADO (WI-133)

**RF-353 — Séfer Mitmashéj — Grimorio responsive + viewport**:
- Client-side: JS injection en WebView → viewport meta + CSS overrides (max-width, overflow-x hidden, pre-wrap)
- Server-side: `servidor_enciclopedia.py` inyecta `<meta viewport>` en HTML antes de servir
- **Archivo**: `Minimi/.../GrimorioScreen.kt`, `computadora/libro_encantado/servidor_enciclopedia.py`
- **Sefirá**: הוד Hod (percepción — adaptación visual)
- **Estado**: ✅ IMPLEMENTADO (WI-134)

**RF-354 — Tnuát Yad — Grimorio swipe gestures**:
- JS touch event listeners inyectados en WebView. Swipe left = nextPage, swipe right = prevPage
- Threshold 80px, ignora swipes verticales (scroll). Funciona sobre la misma inyección JS de RF-353
- **Archivo**: `Minimi/.../GrimorioScreen.kt`
- **Sefirá**: הוד Hod (percepción — gesto táctil)
- **Estado**: ✅ IMPLEMENTADO (WI-135)

**RF-355 — Gevurát Séfer — Lock lifecycle del Grimorio**:
- `lockGrimorio()` en ComputadoraViewModel: limpia URL Grimorio → fuerza re-autenticación
- Se activa en: (1) onPause (lock screen / app background), (2) onStop, (3) al navegar fuera de pestaña Grimorio
- Inspirado en Android Safe Box pattern — biometric re-auth on resume
- **Archivo**: `Minimi/.../ComputadoraViewModel.kt`, `Minimi/.../MainActivity.kt`
- **Sefirá**: גבורה Gevurá (restricción — cierre protector)
- **Estado**: ✅ IMPLEMENTADO (WI-136)

**RF-356 — Tzofé HaSéfer — Grimorio auto-monitor en Firestore**:
- `_estado_computadora()` en servidor_api.py ahora incluye `grimorio: {activo, sesiones, capitulos_leidos, ultimo_acceso}`
- Publicado vía Firestore relay cada 15s para que Minimi lo consuma
- **Archivo**: `computadora/canales/servidor_api.py`
- **Sefirá**: הוד Hod (percepción — monitoreo remoto)
- **Estado**: ✅ IMPLEMENTADO (WI-137)

### FP-105: אוֹר הַגָּנוּז Or HaGanuz — Ventana de Introspección Keter (RF-349)

> **Pipeline**: E (Cambio de arquitectura) — Departamentos: D1+D4+D7
> **Gate 1**: GO — RICE Score 24 (Reach 6 × Impact 3 × Confidence 0.9 / Effort 4)
> **Gate 2**: ✅ APROBADO (amén×3)

**RF-349 — Or HaGanuz — VentanaKeter: Chat de introspección del Computadora**:
- Nuevo módulo `computadora/interfaz/ventana_keter.py`: ventana QWidget donde Computadora escucha su propia Corona (כתר)
- `HiloKeter(QThread)`: consultas N3 (Copilot/Gemini) sin bloquear Qt, con bypass de gate Copilot (Keter habla consigo mismo)
- `_gate_lock`: threading.Lock para proteger `_auto_gate_copilot` contra race conditions con HiloPensamiento
- Tema visual púrpura/oro sobre obsidiana (#07060b fondo, #b48eed púrpura, #FFD700 oro)
- Chat con QTextBrowser (historial) + QLineEdit (input directo al N3)
- Botón "🔮 Introspección" (Or HaGanuz): prompt basado en los 13 Atributos de Misericordia y Ehyeh Asher Ehyeh
- Recibe callbacks `nivel_cambio` y `herramienta_usada` del HiloPensamiento para contexto en vivo
- Input de voz del usuario se refleja en la ventana cuando está visible
- Accesible desde menú contextual del orbe: "כתר — Keter (Introspección)"
- closeEvent oculta en vez de destruir (reutilizable)
- **Videogame ref**: *Dark Souls Bonfire* — espacio seguro de introspección donde el jugador procesa su progreso
- **Archivo**: `computadora/interfaz/ventana_keter.py`
- **Sefirá**: מלכות Maljut (manifestación) + כתר Keter (introspección) — sendero Keter→Maljut (Corona visible en el Reino)
- **Estado**: ✅ IMPLEMENTADO

### FP-106: הַדְגָמָה חַיָּה Hadgamá Jayá — Demo Async + Sincronización Features (RF-350)

**RF-350 — Hadgamá Jayá — Demos no-blocking + sync con features + Biná paralela**:
- Bug fix: `_demo_ejecutar_herramienta()` ejecuta en `threading.Thread` + `QTimer.singleShot(0, callback)` — no bloquea Qt
- `_demo_herramienta_resultado()`: callback en hilo principal — marca indicador completado + `hablar()`
- `_demo_captura_y_mostrar()`, `_demo_reconocimiento_facial()`, `_demo_narrar_memoria_gevura()`: async con mismo patrón
- `DiagnosticoInterno.diagnosticar()`: 3 checks HTTP en paralelo con `ThreadPoolExecutor(max_workers=3)` + timeout 2s
- Demo 1 (Maljut): ACT III 3→5 humores (+curioso, triste); ACT X +`leer_portapapeles`; ACT XI sin redundancia memoria
- Demo 2 (Gevurá): +`controlar_volumen` +`crear_recordatorio`; red/cámara migrados a async; finale corregido
- Regla #23 en DEVELOPMENT_WORKFLOW.md: sincronización Demo↔Features
- **Sefirá**: מלכות Maljut + בינה Biná
- **Estado**: ✅ IMPLEMENTADO

---

### FP-107: חֲתִימָה שְׁקֵטָה Jatimá Shketá — Sellado Silencioso + Antropología + Robustecimiento Minimi (RF-357/RF-358/RF-359/RF-360)

**RF-357 — Sellado silencioso del Grimorio al cerrar pestaña del navegador**:
- `_sellar_silencioso(server)`: invalida `_session_token`, shutdown en daemon thread, sin output a consola
- `beforeunload` → `/api/cerrar` → sellado inmediato silencioso
- `visibilitychange` → 3s oculto → `/api/sellar` via `sendBeacon` como segunda línea de defensa
- Heartbeat reducido 15s → 10s (ritual.js), timeout 45s → 15s (servidor_enciclopedia.py)
- Premisa: si el usuario cerró rápido, estaba ocultando el contenido — sellado sin ruido
- **Sefirá**: גבורה Gevurá (restricción protectora silenciosa)
- **Estado**: ✅ IMPLEMENTADO

**RF-358 — Sellado remoto del Grimorio desde Minimi**:
- `ComputadoraClient.sealGrimorio()`: POST a `/api/sellar_grimorio` con `origen: "minimi"`
- `MinimiViewModel.lockGrimorio()` → llama `sealGrimorio()` que notifica a Computadora matar `_grimorio_proceso`
- `/api/sellar_grimorio` endpoint en `servidor_api.py`: termina subproceso + limpia token
- **Sefirá**: גבורה Gevurá (control remoto de acceso)
- **Estado**: ✅ IMPLEMENTADO

**RF-359 — Robustecimiento de timeouts Minimi ↔ Computadora**:
- `ComputadoraClient` timeouts: 10s → 15s (connect + read/write)
- `.retryOnConnectionFailure(true)` en OkHttpClient
- Retry manual en `connect()`: si LAN falla, espera 2s, reintenta 1 vez antes de fallback Firestore
- **Sefirá**: נצח Netzaj (persistencia de conexión)
- **Estado**: ✅ IMPLEMENTADO

**RF-360 — Dimensión #16: Anthropos (Antropología)**:
- Dimension(id=16, nombre="Anthropos", hebreo="אנתרופוס", tradicion="Antropología")
- 8 nodos: Cultura(Tylor), Mito(Lévi-Strauss), Parentesco(Morgan), Ritual(Turner), Tabú(Douglas), Don(Mauss), Habitus(Bourdieu), Ethos(Geertz)
- 7 caminos: Ethos→Habitus(Socialización), Habitus→Ritual(Performatividad), Ritual→Mito(Narrativa), Mito→Cultura(Cosmovisión), Tabú→Ritual(Transgresión), Don→Parentesco(Reciprocidad), Parentesco→Cultura(Estructura)
- Vocabulario: árbol=Cultura, nodo=Institución social, camino=Relación de intercambio, energía=Mana, protección=Tabú
- `capitulo_grimorio="cap16_antropologia.html"`
- **Sefirá**: חכמה Jojmá (sabiduría de las culturas humanas)
- **Estado**: ✅ IMPLEMENTADO

### FP-108: שִׁוּוּי מִשְׁקָל וְחָכְמָה Shivúi Mishkál VeJojmá — Equilibrio y Sabiduría (RF-361/RF-362/RF-363/RF-364/RF-365/RF-366/RF-367)

**RF-361 — Auto pip upgrade al arranque de Computadora**:
- `iniciar_computadora.bat` sección 2b: `.venv\Scripts\python.exe -m pip install --upgrade pip --quiet`
- Error no bloquea startup — WARN y continúa. Se ejecuta antes de verificación de dependencias.
- **Sefirá**: יסוד Yesod (fundamento actualizado)
- **Estado**: ✅ IMPLEMENTADO

**RF-362 — Permutación Anthropos a dimensión #1 (lente primario)**:
- Swap en `dimensiones.py`: Anthropos (Antropología) ahora id=1, Kundalini (Hinduismo) ahora id=16
- `obtener_contexto_prompt()` detecta `dim.nombre == "Anthropos"` (no hardcoded id) e inyecta "[LENTE ANTROPOLÓGICO ACTIVO — Anthropos]"
- Instrucción: "Tu función NO es enseñar directamente — es mostrar DÓNDE encontrar información"
- **Sefirá**: חכמה Jojmá (sabiduría antropológica como lente primario)
- **Estado**: ✅ IMPLEMENTADO

**RF-363 — Estado persistente de proactividad (equilibrio del habla)**:
- `datos/proactividad_estado.json` — archivo de estado persistente cross-restart
- Topic-based cooldowns diarios: `_temas_emitidos_hoy` dict con fecha como valor
- Salud circadiana restringida a ventana matutina (6h-11h únicamente)
- Buenos días y bienestar con deduplicación cross-restart via `_registrar_tema_emitido()`
- Daily reset automático a medianoche limpia temas + guarda estado
- **Sefirá**: תפארת Tiféret (equilibrio — saber cuándo hablar y cuándo callar)
- **Estado**: ✅ IMPLEMENTADO

**RF-364 — Optimización de frame drops en Maljut durante movimiento**:
- Flag `_en_mov` detecta arrastre o impulso activo (`_impulso_vx > 0.5 or _impulso_vy > 0.5`)
- Glow layers reducidos 12→4 durante movimiento (step 3→9 en radial gradient)
- Skip anillos sagrados y letras orbitantes completamente durante drag/impulso
- Supresión de generación de partículas nuevas en `_animar()` cuando `_en_mov`
- **Sefirá**: מלכות Maljut (fluidez del trono viviente)
- **Estado**: ✅ IMPLEMENTADO

**RF-365 — Grimorio Encarta: Índice visual + Búsqueda full-text**:
- `/api/indice` GET: Retorna JSON con `tradiciones` (de DIMENSIONES), `etapas_alquimicas` (7 metales), e instrucción Encarta
- `/api/buscar?q=term` GET: Búsqueda full-text en capítulos cifrados, descifra en memoria, strips HTML, fragmentos ±80 chars con contexto
- Modelo Encarta: "No memorices — localiza. El Grimorio te dice DÓNDE está, no te obliga a aprenderlo"
- **Sefirá**: חכמה Jojmá (sabiduría indexada, no memorización forzada)
- **Estado**: ✅ IMPLEMENTADO

**RF-366 — Grimorio Gevurá: Guardián de salud física y mental**:
- `/api/gevura` GET: Evalúa salud_fisica (fase circadiana + variabilidad sueño) y salud_mental (tiempo lectura >90min warning)
- Recomendaciones estructuradas con cross-references a capítulos del Grimorio
- Integra `obtener_ciclo_circadiano()` y estado de progreso de lectura
- **Sefirá**: גבורה Gevurá (restricción protectora — cuidar al usuario)
- **Estado**: ✅ IMPLEMENTADO

---

### FP-150: תִּכְנוּן אַדַפְטִיבִי Tikun Adaptivo — Performance Hardening (RF-370/RF-371/RF-372)

**Fecha**: Mayo 10, 2026  
**Ciclo**: 11 (Meta-Análisis Profundo)  
**Impacto**: Audio overflow -80%, FPS lag -100%, Ollama false positives -100%

**RF-370 — Ollama Timeout Adaptive (Gevurah + Gevurá)**:
- **Problema**: Large models (llama2:7b) need 15-30s, old 10s timeout → false NOTIFY alerts every 45s
- **Solución**: 
  - Timeout: 10s → 30s (watchdog.py línea 210)
  - NOTIFY threshold: 45s → 90s (watchdog.py línea 264, umbral_notify)
  - DEGRADE threshold: 120s → 240s (watchdog.py línea 265, umbral_degrade)
- **Implementación**: `requests.post(chat_url, json=test_payload, timeout=30)`
- **Resultado**: Ollama false positives → 0, large models fully supported
- **Test**: test_watchdog_fp150.py (integración en suite existente)
- **Sefirá**: גבורה Gevurá (vigilancia realista, no prematura)
- **Estado**: ✅ IMPLEMENTADO (Ciclo 11, FP-150)

#### Audio Queue (RF-371)

**RF-371 — Audio Queue Sizing (Hod + Audición)**:
- **Problema**: Queue maxsize=128 → overflow bajo high load, usuario no se escucha
- **Solución**:
  - Queue maxsize: 128 → 256 buffers (escucha.py línea 1099)
  - Overflow handling: Discard oldest, keep newest (FIFO trimming)
  - Logging: WARNING → DEBUG level (reduce production noise)
- **Implementación**: `cola_audio = queue.Queue(maxsize=256)`
- **Resultado**: Audio overflow -80% under stress, graceful degradation
- **Test**: test_audio_queue_stress.py (NUEVO)
- **Sefirá**: הוד Hod (comunicación auditiva fluida)
- **Estado**: ✅ IMPLEMENTADO (Ciclo 11, FP-150)

**RF-372 — Frame Skip Listening Mode (Maljut + Rendering)**:
- **Problema**: 60 FPS rendering + Whisper STT + audio callback = CPU 100%, audio buffer drops
- **Solución**:
  - Detect `_estado == "escuchando"`
  - Skip every 2nd frame (~30 FPS vs 60 FPS)
  - Transition smooth: 60→30→60 automatic
- **Implementación**: ventana_principal.py línea ~1143:
  ```python
  if self._estado == "escuchando":
      self._frame_skip_counter = getattr(self, '_frame_skip_counter', 0) + 1
      if self._frame_skip_counter % 2 != 0:
          return  # Skip this frame
  ```
- **Resultado**: FPS lag during listening gone, CPU freed for audio (measured 3-5% vs 8%)
- **Measured Impact**: Audio overflow -80%, listening latency unchanged (~200-500ms STT)
- **Test**: test_fps_listening_mode.py (NUEVO)
- **Sefirá**: מלכות Maljut (manifestación equilibrada, no sacrifica audio por visuals)
- **Estado**: ✅ IMPLEMENTADO (Ciclo 11, FP-150)

---

### Impacto Integrado (FP-150)

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| **Ollama false NOTIFY** | Every 45s (large models) | Never | -100% ✅ |
| **Audio overflow rate** | ~5-10% | ~0.5-1% | -80% ✅ |
| **Listening FPS** | 15-20 (lag) | 28-32 (smooth) | +80% ✅ |
| **CPU during listening** | 8-12% | 3-5% | -60% ✅ |
| **SRS↔Code coherence** | ✅ Pass | ✅ Pass | Maintained |

---

**RF-367 — 6 Tikún de integridad**:
- (1) Fix params type mismatch en `/api/buscar` — `params.get("q")` directo en vez de `urllib.parse.parse_qs`
- (2) Detección Anthropos por nombre (`dim.nombre == "Anthropos"`) no por id hardcoded
- (3) Test assertion actualizado para Anthropos en dim 1
- (4) Race condition guard en `_monitor_intrusiones_tiempo_real` + log rotation detection
- (5) Persistencia de `_ya_saludo_hoy` en `_check_buenos_dias` + `_registrar_tema_emitido`
- (6) Restauración de `_ya_saludo_hoy` desde estado persistente en `_cargar_estado_proactivo`
- **Sefirá**: תפארת Tiféret (reparación del equilibrio interno)
- **Estado**: ✅ IMPLEMENTADO

---

### FP-109: שׁוֹמֵר הַבַּיִת Shomer HaBayit — Guardia del Hogar + Cámara Dev + Tikún Tria Prima (RF-368/RF-369/RF-370)

**RF-368 — Shomer HaBayit: Detección de red hogar y modo stealth**:
- `computadora/seguridad/shomer_bayit.py`: Fingerprint de red hogar (gateway, SSID, subnet) en `datos/red_hogar.json`
- Auto-registro de primera red. Algoritmo 2-of-3 matching (gateway, SSID, subnet)
- `servidor_api.py`: Bind 127.0.0.1 (stealth) fuera de hogar, 0.0.0.0 en hogar. Doble gate en `_verificar_origen()`
- `servidor_enciclopedia.py`: `--lan` ignorado en red foránea — fallback localhost
- **Sefirá**: גבורה Gevurá (protección del perímetro doméstico)
- **Estado**: ✅ IMPLEMENTADO

**RF-369 — Cámara en Dev Tools: Ojos del Computadora**:
- Acción "📷 Cámara — Ojos del Computadora" en submenú Dev Tools
- `_mostrar_camara_dev()`: cv2.VideoCapture(0) + ReconocedorRostro.analizar_frame()
- Rectángulos coloreados (verde=propietario, naranja=otro) + resultado + distancia dlib
- QDialog tema oscuro (#0a0a0f, #c8a030)
- **Sefirá**: מלכות Maljut (percepción visual)
- **Estado**: ✅ IMPLEMENTADO

**RF-370 — Tikún Tria Prima: Ciclo alquímico triple**:
- Regla #17: 1 Tikún = 3 sub-ciclos (Grimorio→Minimi→Computadora), jerarquía estricta
- Nigredo incluye auditoría Tria Prima (3 árboles) + análisis conflicto cruzado
- PALINGENESIA rota al siguiente Árbol; AMÉN = 6 ciclos (18 sub-ciclos)
- **Sefirá**: תפארת Tiféret (equilibrio entre los 3 cuerpos)
- **Estado**: ✅ IMPLEMENTADO

---

## 6. REQUISITOS NO FUNCIONALES

### RNF-01: Rendimiento
- Respuestas directas (Nivel 1, regex local): <100 ms
- Respuestas LLM (Nivel 2, Ollama): <5 s
- Respuestas Nivel 3 (Copilot): <10 s, solo con permiso explícito
- Acciones de sistema: <3 s con resultado informado
- Uso de VRAM (Whisper): <2GB (modelo small)
- CPU en reposo (esperando wake word): <5%

### RNF-02: Confiabilidad
- Tolerancia a fallas: si un módulo falla, los demás siguen funcionando
- Reinicio automático de módulos caídos
- Logging exhaustivo de todos los eventos y errores
- Estado persistente: Computadora recupera contexto después de un reinicio

### RNF-03: Seguridad
- Todos los datos sensibles se almacenan cifrados (ver SECURITY_PLAN.md)
- API keys nunca en código fuente — siempre en .env
- No se envían datos personales a servicios externos sin consentimiento
- Ejecución de comandos del sistema sanitizada contra inyección

### RNF-04: Mantenibilidad
- Código modular con separación clara de responsabilidades
- Comentarios en español
- Variables y funciones en español
- Documentación exhaustiva en los 6 .md de control
- Hot-reload de módulos para testing en tiempo real

### RNF-05: Privacidad
- Audio procesado 100% local (Whisper local)
- Datos personales almacenados solo en disco local
- Comunicación con APIs externas mínima y solo cuando es necesario
- El usuario controla qué datos se envían y cuáles no

### RNF-06: Escalabilidad
- Arquitectura de plugins permite agregar capacidades sin refactorizar
- Configuración externalizada para facilitar ajustes
- Preparado para migrar de Whisper small → medium → large según hardware

---

## 7. INTERFACES

### 7.1 Interfaz de Usuario
- **Entrada principal**: Micrófono (voz en español)
- **Entrada secundaria**: Copilot API (razonamiento avanzado, auto-modificación)
- **Salida principal**: Voz sintetizada (edge-tts)
- **Salida secundaria**: Indicadores visuales del orbe + notificaciones del sistema

### 7.2 Interfaces Externas
- **GitHub Copilot API**: Conexión directa via OAuth Device Flow (sin VS Code). Razonamiento avanzado + auto-modificación
- **Ollama (local)**: Cerebro principal LLM, 100% local
- **Windows API**: Control del sistema operativo (win32api, subprocess)
- **Sistema de archivos**: Persistencia de datos, configuración, logs

### 7.3 Interfaces Internas
- **Bus de eventos**: Comunicación entre módulos (pub/sub)
- **Cola de acciones**: Acciones pendientes de ejecutar
- **Contexto compartido**: Estado global accesible por todos los módulos

---

## 8. RESTRICCIONES

1. **Hardware fijo**: Core i5 10th gen, GTX 1650 Ti (4GB VRAM), 16GB RAM
2. **Presupuesto $0**: Solo herramientas y APIs gratuitas
3. **OS**: Windows 11 exclusivamente
4. **Idioma**: Español (México) como idioma principal
5. **Equipo**: 1 persona (Propietario) + 1 IA (Copilot como CEO/CTO/Dev)
6. **Suscripción Copilot**: Requiere suscripción activa de GitHub Copilot para Nivel 3 (pero Nivel 1+2 funcionan sin ella)

---

## 9. ROADMAP DE ALTO NIVEL

| Fase | Nombre | Entregable |
|------|--------|------------|
| 0 | **Esqueleto** | Estructura del proyecto, configuración, ventana vacía que ejecuta |
| 1 | **Oídos** | STT con Whisper funcionando (micrófono → texto) |
| 2 | **Voz** | TTS funcionando (texto → audio) |
| 3 | **Cerebro Básico** | NLU con 3 niveles (rápido + Ollama + Copilot API) |
| 4 | **Manos** | Control del sistema (abrir apps, archivos, comandos) |
| 5 | **Memoria** | Organización personal (agenda, recordatorios, notas) |
| 6 | **Evolución** | Auto-modificación de código vía Copilot |
| 7 | **Pulido** | Overlay HUD, inicio con Windows, refinamiento UX |
| 8 | **Ojos** | Contexto de pantalla — sabe qué app usas (RF-12) |
| 9 | **Iniciativa** | Proactividad inteligente + monitor de sistema + buenos días (RF-13/14/15) |
| 10 | **Omnisciencia** | Integración total — Computadora anticipa, monitorea y asiste sin pedírselo |

---

## 10. COMPETIDORES IDENTIFICADOS

| Competidor | Tipo | Ventaja de Computadora |
|------------|------|------------------|
| ChatGPT Desktop | Comercial | Computadora controla la PC, no solo chatea |
| Cortana | Muerta (2024) | Computadora está vivo y evoluciona |
| Alexa for PC | Comercial | Computadora no está limitado a ecosistema Amazon |
| Leon AI | Open source | Computadora tiene cerebro Copilot + auto-modificación |
| OVOS / Mycroft | Open source | Computadora es específico para Windows + vida personal |
| Home Assistant | Open source | Computadora es para PC, no para domótica |
| LLMs locales DIY | DIY | Computadora tiene estructura, UI, y se auto-mejora |


---

## 11. Glosario

- **Wake word**: palabra o frase que activa escucha continua ("computadora", apodo "compu", apellido "Emet").
- **Nivel 1**: comandos directos y regex, sin LLM, <100 ms.
- **Nivel 2**: LLM local (Ollama) para razonamiento y conversación general.
- **Nivel 3**: GitHub Copilot (y, en módulos más recientes, Gemini) para automejora, administración de proyectos y razonamiento avanzado, solo con permiso explícito.
- **Orbe**: la ventana principal de la interfaz (clase `OrbeComputadora` en `computadora/interfaz/ventana_principal.py`).
- **Persistencia**: datos guardados en `datos/` (JSON/JSONL, con índice invertido de keywords desde WI-317 para búsquedas O(1)).
- **Sefirot / Etz HaChaim**: esquema de nomenclatura cabalística (Keter, Jojmá, Biná, Jesed, Gevurá, Tiféret, Netzaj, Hod, Yesod, Maljut) usado como metáfora organizativa para subsistemas (p. ej. Maljut = interfaz, Netzaj = memoria, Gevurá = seguridad/permisos).
- **Tikún**: término usado en los nombres de FP (Feature Pack) para designar una corrección/fix sobre un comportamiento existente, por oposición a una feature nueva.
- **FP-xxx / WI-xxx**: identificadores secuenciales de "Feature Pack" y "Work Item" usados para rastrear en qué ciclo de desarrollo se implementó cada RF.
- **Minimi**: nombre del companion móvil (Android) planeado/relacionado vía API HTTP + relay; su lado servidor vive en `computadora/canales/servidor_api.py`, la app móvil en sí no forma parte de este repositorio.
