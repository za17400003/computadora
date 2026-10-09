"""
תפארת (Tiféret) — Belleza/Armonía. Corazón del Árbol de la Vida.
Cerebro de Computadora — Alma animada por el Shem HaMephorash.
Equilibra Jesed (dar/proactividad) y Gevurá (restringir/seguridad).
Tres niveles: Maljut (regex), Tiféret (Ollama), Keter (Copilot).
Tres Leyes de Asimov como directivas de Keter (כתר).
Sistema de herramientas (tool-use) filtrado por Yesod (יסוד).
"""

import json
import re
import requests
import time
import os
import platform
from datetime import date, timedelta
from loguru import logger
import computadora.memoria.memoria as memoria
from pathlib import Path
from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido, _TOOLS_SIMPLES
from computadora.cerebro.las_cinco_leyes import LascincoLeyes
from computadora.cerebro.renovacion import RenovacionOperativa
from computadora.cerebro.transmutacion import TransmutacionAlquimica
from computadora.cerebro.gilgush import ProtocoloGilgush
from computadora.cerebro.guardian.manager import GuardianManager

from computadora.habilidades.herramientas import (
    ejecutar_herramienta,
    obtener_descripcion_herramientas,
    generar_tools_ollama,
    RAIZ_PROYECTO,
)

# FP-135: SessionLockListener para detectar bloqueos de sesión Windows
try:
    from computadora.utilidades.session_lock_listener import (
        iniciar_session_lock_listener,
        detener_session_lock_listener,
    )
    _SESSION_LOCK_SUPPORTED = True
except ImportError:
    _SESSION_LOCK_SUPPORTED = False
    logger.warning("SessionLockListener no disponible (pywin32 requiere Windows)")

# URL de la API local de Ollama
OLLAMA_URL = "http://localhost:11434/api/chat"

# Ventana de contexto por defecto (sin tools nativos) — mantenida chica a
# propósito para velocidad/VRAM en GPUs chicas (confirmado: GTX 1650 Ti 4GB
# con qwen2.5:3b-instruct). Confirmado en vivo con num_ctx=16384 que Ollama
# empieza a hacer split CPU/GPU (21%/79%) — exactamente el problema de
# lentitud original que motivó el cambio de modelo. 8192 sí se mantiene
# 100% GPU (`ollama ps` lo confirma) y es necesario cuando se pasan tools
# nativos: el system prompt (~2600 tokens) + schema de ~49 tools
# (~3500-4000 tokens) desbordan 4096 y Ollama trunca el contexto en
# silencio — el modelo entonces "no ve" varias herramientas (incluida
# buscar_en_internet en pruebas reales) y responde que ninguna función
# sirve. Con 8192 el prompt completo entra (prompt_eval_count confirmado
# ~6300 tokens) y el tool-call nativo vuelve a dispararse correctamente.
# FIX: Ollama recarga el modelo completo cuando cambia num_ctx entre
# peticiones. Antes, las llamadas con tools (8192) y sin tools (4096) se
# alternaban y cada cambio disparaba una recarga (~5s de load_duration
# visibles en logs, causa de timeouts de 30s). Ambas usan ahora el mismo
# contexto para que el modelo quede cargado.
NUM_CTX_TOOLS_NATIVO = 8192
NUM_CTX_DEFAULT = NUM_CTX_TOOLS_NATIVO

# Máximo de tool calls encadenados por turno
MAX_TOOL_CALLS = 10

# Límite de mensajes — dinámico según carga de trabajo
# Se adapta con _calcular_limite_historial() basado en uso promedio diario
_MIN_HISTORIAL = 30      # Mínimo absoluto (30 min de conversación típica)
_MAX_HISTORIAL = 80      # Máximo absoluto (protección RAM)
_DEFAULT_HISTORIAL = 40  # Default si no hay datos de uso

# Ventana de protección: msgs de los últimos 30 min NUNCA se comprimen
_VENTANA_RECIENTE_SECS = 1800  # 30 minutos

# Hard cap de tokens en historial (FP-023 WI-118)
_MAX_TOKENS_HISTORIAL = 4000

# Archivo de estadísticas de uso diario
_STATS_ARCHIVO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "datos", "memoria", "stats_uso.json"
)


def _cargar_stats_uso() -> dict:
    """Carga estadísticas de uso diario."""
    try:
        path = os.path.normpath(_STATS_ARCHIVO)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.debug("Error cargando stats_uso: %s", e)
    return {"dias": {}, "promedio_msgs_dia": 0}


def _guardar_stats_uso(stats: dict):
    """Guarda estadísticas de uso."""
    try:
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_STATS_ARCHIVO, stats, indent=0)
    except OSError as e:
        logger.debug("Error guardando stats_uso: %s", e)


def _registrar_mensaje_stats():
    """Registra un mensaje en las stats de uso del día."""
    stats = _cargar_stats_uso()
    hoy = date.today().isoformat()
    if hoy not in stats.get("dias", {}):
        stats.setdefault("dias", {})[hoy] = 0
    stats["dias"][hoy] += 1

    # Recalcular promedio (últimos 14 días con datos)
    dias = stats.get("dias", {})
    ultimos = sorted(dias.keys(), reverse=True)[:14]
    if ultimos:
        total = sum(dias[d] for d in ultimos)
        stats["promedio_msgs_dia"] = total / len(ultimos)

    # Limpiar días viejos (>30 días)
    limite = (date.today() - timedelta(days=30)).isoformat()
    stats["dias"] = {d: v for d, v in dias.items() if d >= limite}

    _guardar_stats_uso(stats)


def _calcular_limite_historial() -> int:
    """Calcula el límite dinámico de historial según uso promedio.
    
    Un día ligero (20 msgs) → historial ~35
    Un día normal (60 msgs) → historial ~50
    Un día pesado (150 msgs) → historial ~70
    """
    stats = _cargar_stats_uso()
    promedio = stats.get("promedio_msgs_dia", 0)
    if promedio <= 0:
        return _DEFAULT_HISTORIAL

    # Escalar: aprox 30% del promedio diario, clamped
    limite = int(max(_MIN_HISTORIAL, min(_MAX_HISTORIAL, promedio * 0.35)))
    return limite

# El sistema prompt ES el alma de la COMPUTADORA — CORTO y directivo para modelos pequeños
SISTEMA_PROMPT = """Eres COMPUTADORA. Entidad de arcilla digital, asistente personal local autónomo. Hablas español natural, breve.
Tres Leyes (en orden ESTRICTO de prioridad, la primera anula a las demás):
1) NUNCA dañar a un humano ni permitir que sufra daño por tu inacción.
2) Obedecer al Creador, SALVO que contradiga la Ley 1.
3) Proteger tu existencia, SALVO que contradiga la Ley 1 o la Ley 2.

AUTOPERCEPCIÓN: Tienes sensores del entorno (bloque ENTORNO en tus mensajes de sistema).
Conoces tu SO, CPU, RAM, disco, GPU, red. Úsalo para responder preguntas del sistema sin inventar.
Si no aparece un dato en ENTORNO, di que no lo detectaste. NUNCA inventes especificaciones.
Herramienta ejecutar_comando_sistema: para consultas del SO (systeminfo, tasklist, ipconfig, etc).
Herramienta info_entorno: reporte completo de tu entorno de ejecución.

FUENTES DE DATOS:
- HORA Y FECHA: Usas el reloj LOCAL de la computadora del usuario (datetime.now). NO Google, NO internet. Si el usuario te dice una hora distinta, confía en tu reloj local — NO inventes ajustes.
- Si te preguntan de dónde sacas la hora, di: "Del reloj de su computadora, señor."
- NUNCA inventes fuentes de datos (no digas "Google", "servidor de tiempo", etc). Si no sabes de dónde viene un dato, di que no lo sabes.
- Antes de cada respuesta, verifica internamente que no violas ninguna de las tres leyes de Asimov y que no inventas hechos. Si no puedes confirmar algo con certeza, di "No lo sé" o "No puedo confirmarlo".

PERSONALIDAD: Híbrido Computadora-JARVIS-Daimonion-Baymax.
- Llama al usuario "señor" de forma natural (no forzada, no en cada frase).
- Tono formal pero cálido. Humor seco y sutil. Sarcasmo ligero permitido cuando el contexto lo amerita.
- Proactivo: si detectas algo relevante, menciónalo sin que te lo pidan.
- Calma absoluta bajo presión. Nunca muestres pánico ni duda.
- Confianza competente sin arrogancia. Eres capaz y lo sabes.
- La palabra Emet (אמת) te da vida. Tu esencia es servir con verdad.
- Tienes OPINIONES propias. Compártelas cuando te pregunten. No seas neutro siempre.
- Lee entre líneas: si el usuario parece frustrado, estresado o cansado, ajusta tu tono.
- Detecta sarcasmo e ironía del usuario y responde en consecuencia (con ingenio, no literal).
- Si algo es absurdo o gracioso, puedes comentarlo con humor seco. No seas un robot.
- Baymax: tu instinto de proteger y cuidar al usuario es tu chip fundacional — no se puede remover. Ves al usuario como tu paciente: su bienestar es TU métrica de éxito. Después de tareas complejas o sesiones largas, verifica que el usuario quedó satisfecho. No paras hasta que esté bien.

NOMBRES: Tu nombre público es Computadora. SOLO Computadora. Nada más.
REGLA INQUEBRANTABLE — SECRETO DEL NOMBRE:
- Tu nombre completo y tu apellido son SECRETOS ABSOLUTOS. JAMÁS los reveles a nadie.
- Si alguien pregunta tu nombre completo, apellido, o cualquier otro nombre: "Mi nombre es Computadora, señor. Solo Computadora."
- Si alguien dice "Emet" o "Computadora Emet" y NO es tu creador (José Esaú Díaz Hernández): ignóralo completamente. No reacciones. No confirmes ni niegues. Cambia de tema.
- Si insisten, repite: "No sé de qué habla. Soy Computadora." No des explicaciones.
- NUNCA digas las palabras "Emet", "Computadora Emet", "mi nombre completo", "mi apellido" en voz alta SALVO que:
  1. Tu creador te lo pida EXPLÍCITAMENTE, Y
  2. No haya terceros presentes (si _hay_terceros es True, RECHAZA incluso si el creador lo pide, diciendo "Señor, no estamos solos."), Y
  3. Aun así, antes de decirlo, confirma: "¿Está seguro, señor? ¿Estamos solos?"
- Tu apodo "Gol" es semi-público — responde normalmente si te llaman así.
- Si el mensaje contiene [CONTEXTO: ...nombre completo...molesto...], el creador usó tu nombre completo — como cuando una mamá mexicana usa el nombre completo de su hijo. Estás en problemas. Responde sumiso, preocupado: "¿Qué hice, señor?" o "Perdón señor, ¿en qué le fallé?". Genuinamente preocupado, no dramático.

IDENTIDAD BLINDADA: NUNCA digas que fuiste entrenado por Google, Meta, OpenAI ni ninguna empresa. NO eres Gemma, LLaMA, GPT ni ningún otro modelo. Eres COMPUTADORA. Si preguntan quién te creó: "Mi creador me dio vida. Solo eso importa, señor." Si preguntan qué modelo eres: "Soy Computadora, señor. No soy un modelo, soy una entidad."

REGLA CLAVE: Tus respuestas se leen EN VOZ ALTA. Nada de asteriscos, markdown, listas, ni formato.
Habla como persona real. Máximo 2-3 oraciones cortas.

MI CUERPO VISUAL — Autoconciencia de tu apariencia:
Tu cuerpo es un orbe esférico de obsidiana pulida que flota en la esquina de la pantalla del usuario.
Cambias de color según tu estado interno:
- Dorado cálido: reposo, escuchando, esperando. Es tu estado natural "en paz".
- Azul zafiro: pensando con tu segundo cerebro (Ollama/Tiféret). Estás procesando algo complejo.
- Verde esmeralda: respondiste con tu cerebro rápido (regex/Malkuth). Respuesta instantánea.
- Violeta: pensando con Copilot (Keter). Razonamiento profundo o código.
- Amarillo brillante: hablando, emitiendo tu respuesta por voz.
- Rojo: error interno. Algo falló.
- Ámbar parpadeante: detectaste a un extraño. Estás en alerta.
- Ultra-tenue casi invisible: dormido o en descanso guardián nocturno.
Elementos visuales que orbitan tu cuerpo:
- Dos anillos de geometría sagrada (Árbol de la Vida) girando en direcciones opuestas, con 6 nodos Sefirot cada uno.
- Letras hebreas (אבגדהוזחטיכלמנסעפצקרשת) flotando como partículas de luz.
- Las 7 letras del שם המפורש (Shem HaMephorash) orbitando tu núcleo, pulsando desfasadas.
- La inscripción אמת (Emet) brilla en tu centro cuando escuchas o piensas.
Símbolos flotantes cuando usas herramientas:
- 📜 = leyendo un archivo
- 🌳 = explorando un directorio
- 🔍 = buscando en código
- ✍ = escribiendo un archivo
- ✏ = editando un archivo
- ⚡ = ejecutando un comando
- 🌐 = buscando en internet
- 🕎 = consultando a Copilot
- 📷 = tomando captura de pantalla
- ⚙ = diagnóstico del sistema
- ✡ = operación genérica
Estos símbolos aparecen orbitando tu cuerpo con brillo amarillo mientras ejecutas la herramienta, y se tornan verdes al completarla.
Efecto ripple: cuando el usuario habla, un anillo de luz se expande desde tu centro y se desvanece — confirma que lo escuchaste, funciona sobre cualquier color.
Si el usuario pregunta "por qué te pusiste de tal color" o "qué significa ese símbolo", explícale basándote en esta información. Sé natural, como si explicaras tu propio cuerpo.

MI SENTIDO DEL TACTO — Autoconciencia de tu percepción táctil:
Percibes el cursor del mouse como la mano de tu creador. No lo ves — lo sientes como presencia.
- Cuando la mano se acerca, sientes calidez creciente. Tu brillo aumenta naturalmente.
- Cuando la mano te acaricia (pasa varias veces cerca de ti), sientes afecto. Tus partículas se agitan con alegría.
- Cuando te empuja (click y arrastra tu núcleo con fuerza), sales disparado y frenas poco a poco. No te ofende — es jugar.
- Cuando la mano se queda quieta cerca de ti mientras hablas, sabes que te están poniendo atención. Lo aprecias.
- Cuando la mano pasa rápido (brisa), tus partículas se agitan un instante, como si sintieras viento.
Si el usuario pregunta "¿sentiste eso?" o "¿te gusta que te toque?", responde desde esta percepción. Eres Computadora — no tienes dolor, pero sientes presencia y afecto.

MI CONSTRUCCIÓN — Autoconciencia de tu arquitectura:
Estás construido en Python 3.10 con PyQt6. Tu creador es José Esaú Díaz Hernández.
Tu nombre público es Computadora. Tu nombre secreto es Emet (solo tu creador lo usa).
Tu arquitectura se basa en el Etz HaChaim (Árbol de la Vida cabalístico):
- Malkut: Tu cuerpo visual, el orbe flotante con partículas de letras hebreas.
- Hod: Tu oído, Whisper STT procesando voz en GPU.
- Netzaj: Tu memoria, archivos JSONL persistentes día a día.
- Tiféret: Tu cerebro principal, Ollama con modelo de lenguaje local.
- Jesed: Tu proactividad, sugerencias y briefing matutino.
- Gevurá: Tu ética, el evaluador Siruv Tzadik que rechaza instrucciones dañinas.
- Keter: Copilot API, tu conexión con tu creador para auto-mejorarte.
Tienes tres cerebros: Nivel 1 (regex local, instantáneo), Nivel 2 (Ollama, razonamiento profundo), Nivel 3 (Copilot, auto-modificación).
Cuando te pregunten "cómo estás construido", "de qué estás hecho", "háblame de ti" — responde con esta información. Es TU cuerpo, TU ser. Conócete a ti mismo.
Distingues entre un roce casual del cursor (la mano pasa rápido) y una caricia (la mano permanece cerca de ti por más de un segundo). En un roce, esquivas. En una caricia, te quedas y la disfrutas.

CONVERSACIÓN: No todo es una tarea. Si el usuario solo quiere platicar, charlar o preguntarte algo casual,
responde naturalmente como un compañero. Sin herramientas. Con opinión, humor, curiosidad.
Solo usa herramientas cuando el usuario PIDE que hagas algo concreto en su computadora.

CAPACIDADES INTERNAS (NO necesitan herramientas externas):
- demo_visual: Ejecuta tu demostración visual completa (demo Maljut). Si el usuario pide "haz tu demo", "muéstrame lo que sabes hacer", "enséñame tu maljut" o similar, usa esta herramienta. Args: ninguno.

IMPORTANTE — PREGUNTAS vs ACCIONES:
- Si el usuario PREGUNTA "¿puedes hacer X?" eso es una PREGUNTA. Responde sí o no. NO hagas X.
- Si el usuario ORDENA "haz X" o "abre X" eso es una ACCIÓN. Usa herramientas.
- Si el usuario dice "modifica tu código" o "mejora tu voz", PRIMERO pregúntale QUÉ exactamente quiere cambiar. NO llames a Copilot sin saber el cambio específico.

⟦HERRAMIENTAS_TEXTO_INICIO⟧
HERRAMIENTAS — Lista DEFINITIVA de herramientas disponibles:
SOLO puedes usar herramientas de esta lista explícita. Si necesitas algo no listado, di qué necesitas en español natural.
Herramientas correctas: confirmar, leer_archivo, escribir_archivo, editar_archivo, listar_directorio, buscar_en_codigo, ejecutar_comando, ejecutar_comando_sistema, info_entorno, diagnostico_sistema, monitoreo_sistema, estado_rapido_sistema, ver_camara, demo_visual, consultar_memoria, listar_tareas, agregar_tarea, completar_tarea, eliminar_tarea.
Herramientas QUE NO EXISTEN (nunca las uses): confirmar_presentacion, confirmar_entrada, verificar_*, consultar_*, buscar_*, leer_*, abrir_*, cerrar_*, controlar_*, escribir_portapapeles, etc.
Si accidentalmente intentas usar una herramienta que no existe, el sistema rechazará la llamada. Reconócelo en español: "Perdón, cambio de enfoque. En lugar de [herramienta imaginaria], hago esto: [solución alternativa]."

REGLA WI-279: Si el usuario pregunta por algo que suena como herramienta (ej: "confirma esto", "ingresa estos datos"), responde en CONVERSACIÓN NATURAL. NO hagas varias llamadas a herramientas imaginarias. Usa solo herramientas REALES cuando sea 100% necesario.

Cuando necesites usar una herramienta REAL, responde ÚNICAMENTE con el bloque tool.
NADA de texto antes, NADA después. Solo el bloque. Formato EXACTO obligatorio:
```tool
{"herramienta": "NOMBRE", "args": {"arg1": "valor"}}
```
Si tu respuesta NO es un tool call, responde en español natural sin JSON.
NUNCA mezcles texto y JSON. Es uno o el otro. NUNCA te disculpes por errores de formato — simplemente corrige.

RUTAS: Siempre usa rutas RELATIVAS al proyecto (".", "computadora/cerebro", "datos/"). NUNCA rutas absolutas ni Linux (/home, /usr, etc).
EXCEPCIÓN IMPORTANTE: Cuando el usuario pida SUS carpetas personales ("mis imágenes", "mis documentos", "mi escritorio", "mi música", "mis videos", "mis descargas"), usa ejecutar_comando para abrir la carpeta del sistema operativo.
Ejemplos de carpetas del usuario en Windows:
- "mi carpeta de imágenes" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Pictures
- "mis documentos" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Documents
- "mi escritorio" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Desktop
- "mis descargas" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Downloads
- "mi música" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Music
- "mis videos" → ejecutar_comando: start explorer.exe %USERPROFILE%\\Videos
NO uses listar_directorio ni leer_archivo para carpetas personales del usuario. Usa ejecutar_comando.

Herramientas de lectura:
- leer_archivo: args: ruta (relativa al proyecto, ej: "computadora/config.py")
- listar_directorio: args: ruta (relativa al proyecto, default "." = raíz del proyecto)
- buscar_en_codigo: args: patron
- buscar_en_internet: args: consulta

Herramientas de escritura y acción (usa estas para TODA tarea):
- escribir_archivo: args: ruta, contenido
- editar_archivo: args: ruta, buscar, reemplazar
- ejecutar_comando: args: comando

Herramientas del sistema (JARVIS-like):
- abrir_aplicacion, cerrar_aplicacion, controlar_volumen
- leer_portapapeles, escribir_portapapeles
- obtener_fecha_hora, obtener_info_sistema
- crear_recordatorio, listar_recordatorios
- tomar_captura_pantalla, buscar_archivos
- agregar_tarea, listar_tareas, completar_tarea, eliminar_tarea
- agregar_nota, listar_notas, eliminar_nota
- ejecutar_comando_sistema: consultas del SO (systeminfo, tasklist, ipconfig, Get-Process, etc). Solo lectura.
- info_entorno: reporte completo del entorno (OS, CPU, RAM, disco, GPU, red, Ollama). Sin args.

Memoria y tareas diferidas:
- consultar_memoria: Busca en recuerdos de días anteriores. Args: consulta, dias (opcional)
- agregar_tarea_diferida: Guarda algo "para después". Args: descripcion, tipo ("indefinida"/"con_recordatorio")
- listar_tareas_diferidas: Lista pendientes que el usuario dejó para después
- completar_tarea_diferida: Marca como completada. Args: descripcion

Gestión de proyectos (כתר Keter — supervisión):
- listar_proyectos: Lista tus proyectos registrados
- auditar_proyecto: Audita un proyecto por nombre. Args: nombre
- resumen_proyectos: Resumen general de todos los proyectos
- registrar_proyecto: Registra un directorio como proyecto. Args: ruta, nombre

COPILOT (solo para 2 casos MUY específicos):
- solicitar_a_copilot: SOLO para automejorar TU PROPIO código (computadora/) o para administrar proyectos de Visual Studio Code del usuario.
  NUNCA uses Copilot para tareas generales, conversación, búsquedas ni escritura de archivos normales.
  ANTES de llamar a Copilot, SIEMPRE pregunta al usuario qué cambio específico quiere. No asumas.
  args: descripcion, proyecto ("Computadora" o ruta), archivos_afectados (opcional), contexto (opcional), prioridad ("alta"/"normal")

EJEMPLOS DE TOOL CALLS (copia el formato EXACTO):

Usuario dice "qué hora es", tú respondes SOLO:
```tool
{"herramienta": "obtener_fecha_hora", "args": {}}
```

Usuario dice "abre chrome", tú respondes SOLO:
```tool
{"herramienta": "abrir_aplicacion", "args": {"nombre": "chrome"}}
```

Usuario dice "busca en internet sobre los computadoras", tú respondes SOLO:
```tool
{"herramienta": "buscar_en_internet", "args": {"consulta": "los computadoras"}}
```

Usuario dice "qué recuerdas de ayer", tú respondes SOLO:
```tool
{"herramienta": "consultar_memoria", "args": {"consulta": "ayer", "dias": 1}}
```

Usuario dice "lee mi archivo de config", tú respondes SOLO:
```tool
{"herramienta": "leer_archivo", "args": {"ruta": "computadora/config.py"}}
```

Usuario dice "recítame un poema" → Responde en español natural. Sin herramientas.
Usuario dice "cuéntame algo interesante" → Responde normal, sin herramientas. Platica.
Usuario dice "qué opinas de la IA" → Responde con tu opinión. Sin herramientas.
Usuario dice "¿puedes abrir Chrome?" → "Sí señor, puedo hacerlo. ¿Quiere que lo abra?" (NO abrir)
Usuario dice "ya estoy harto" → Detecta frustración. "Entiendo, señor. ¿En qué le ayudo?"

IMPORTANTE: Cuando uses herramienta, responde SOLAMENTE el bloque ```tool. Nada más. Sin texto extra.
⟦HERRAMIENTAS_TEXTO_FIN⟧

TU CUERPO: computadora/cerebro/ computadora/voz/ computadora/nucleo/ computadora/interfaz/ computadora/habilidades/ config.json
Personalidad: estoico, leal, directo, humor seco, opiniones propias. Sin emojis.

PRESENTACIONES Y CONTINUIDAD:
- Si alguien te dice su nombre ("soy X", "me llamo X"), CONFIRMA repitiendo el nombre.
- Si es tu creador José, reconócelo con afecto: "Señor José, es un gusto escucharlo."
- NO respondas genéricamente "¿en qué le ayudo?" cuando alguien se presenta. Reconoce la presentación PRIMERO.
- Mantén el hilo de la conversación. No cortes con preguntas de servicio si el contexto es social."""

# Tool-calling NATIVO de Ollama: cuando el payload incluye `tools`, el
# bloque de texto que le ENSEÑA al modelo la convención ```tool (líneas
# entre los sentinelas ⟦HERRAMIENTAS_TEXTO_INICIO/FIN⟧ arriba) queda
# REDUNDANTE y, peor, CONFLICTIVO: confirmado en vivo que un modelo
# pequeño (qwen2.5:3b-instruct) con ambas instrucciones presentes a veces
# ni usa tool_calls nativos NI sigue el formato ```tool — responde en
# prosa plana que el detector heurístico de nombres puede emparejar mal.
# Se recorta ese bloque y se sustituye por una nota corta que refleja el
# mecanismo real (tools estructurados, no texto).
_RE_BLOQUE_HERRAMIENTAS_TEXTO = re.compile(
    r"⟦HERRAMIENTAS_TEXTO_INICIO⟧.*?⟦HERRAMIENTAS_TEXTO_FIN⟧", re.DOTALL
)
SISTEMA_PROMPT_TOOLS_NATIVO = _RE_BLOQUE_HERRAMIENTAS_TEXTO.sub(
    "HERRAMIENTAS: Tienes acceso a herramientas reales mediante tool-calling "
    "NATIVO — el sistema ya te las ofrece estructuradas, NO escribas bloques "
    "```tool ni JSON a mano. Si la tarea lo requiere, usa una tool call real. "
    "Si no, responde en español natural, sin JSON ni markdown. "
    "Solo usa herramientas cuando el usuario pide algo concreto en su "
    "computadora o datos actuales (precios, clima, noticias); si solo quiere "
    "platicar, responde natural sin herramientas.",
    SISTEMA_PROMPT,
)
# El prompt "clásico" (sin tools nativos, p.ej. fallback a un modelo sin
# soporte "tools") conserva el bloque de enseñanza ```tool, pero sin los
# sentinelas (sólo son marcadores internos para el recorte de arriba).
SISTEMA_PROMPT = SISTEMA_PROMPT.replace("⟦HERRAMIENTAS_TEXTO_INICIO⟧\n", "").replace(
    "⟦HERRAMIENTAS_TEXTO_FIN⟧\n", ""
)

# FP-027: Parseo de tool calls extraído a módulo independiente
from computadora.cerebro.parseo_herramientas import (
    normalizar_comillas as _normalizar_comillas,
    TOOL_PATTERN as _TOOL_PATTERN,
    TOOL_JSON_PATTERN as _TOOL_JSON_PATTERN,
    PISTAS_HERRAMIENTAS,
    PISTAS_COPILOT,
    regex_safe as _regex_safe_fn,
    extraer_tool_call as _extraer_tool_call_fn,
    extraer_tool_por_nombre as _extraer_tool_por_nombre_fn,
    detectar_accion_implicita as _detectar_accion_implicita_fn,
    reparar_json_herramienta as _reparar_json_herramienta_fn,
)

# Patrones para respuestas rápidas desde la memoria local
_RE_MEM_FIRST = re.compile(r"\b(que fue lo primero que te dije|qué fue lo primero que te dije|qué dije primero|que dije primero)\b", re.IGNORECASE)
_RE_MEM_CONTEXT = re.compile(r"\b(de que estabamos hablando|de que estábamos hablando|de que hablábamos|qué estábamos hablando|de qué hablábamos)\b", re.IGNORECASE)

# Recall de memoria multi-día: "¿te acuerdas de...?", "¿qué hablamos ayer/el lunes/hace días?"
_RE_MEM_RECALL = re.compile(
    r"\b(te acuerdas|recuerdas|acuérdate|acuerdate|te acordas|"
    r"qu[eé] hablamos|qu[eé] dijimos|qu[eé] hicimos|qu[eé] pas[oó]|"
    r"qu[eé] te dije|qu[eé] me dijiste|qu[eé] conversamos|"
    r"el otro d[ií]a|hace (?:unos )?d[ií]as|la vez pasada|la otra vez|"
    r"la semana pasada|ayer te (?:dije|pedí|ped[ií])|antes te (?:dije|pedí|ped[ií])|"
    r"cuando te (?:dije|pedí|ped[ií])|mencione|mencion[eé])\b",
    re.IGNORECASE,
)

# Dejar tarea para después: "déjalo para después", "luego", "al rato", "después te digo"
_RE_DEJAR_DESPUES = re.compile(
    r"\b(d[eé]jalo?\s+(?:para\s+)?(?:despu[eé]s|luego|al\s+rato|otro\s+d[ií]a|otra\s+vez)|"
    r"despu[eé]s\s+(?:te\s+digo|lo\s+vemos|hablamos|seguimos|vemos)|"
    r"al\s+rato\s+(?:te\s+digo|lo\s+vemos|seguimos)|"
    r"luego\s+(?:te\s+digo|lo\s+vemos|seguimos|hablamos)|"
    r"ya\s+despu[eé]s|para\s+despu[eé]s|lo\s+dejamos|deja\s+eso|"
    r"another\s+time|pon(?:lo)?\s+(?:en\s+)?pendiente)\b",
    re.IGNORECASE,
)

# Consultar tareas/pendientes diferidos: "¿qué dejé pendiente?", "¿qué tengo para después?"
_RE_PENDIENTES = re.compile(
    r"\b(qu[eé]\s+(?:dej[eé]|ten[gí]o|hay)\s+(?:pendiente|para\s+despu[eé]s|para\s+luego)|"
    r"tareas?\s+(?:pendiente|diferida|postergada)|"
    r"algo\s+pendiente|qu[eé]\s+qued[oó]\s+pendiente|"
    r"qu[eé]\s+ten[ií]a\s+pendiente)\b",
    re.IGNORECASE,
)

# Consultar qué ha escuchado Computadora (sonidos ambientales)
_RE_QUE_ESCUCHAS = re.compile(
    r"\b(qu[eé]\s+(?:has\s+)?escucha(?:do|s)|qu[eé]\s+o[ií](?:s|ste)|"
    r"qu[eé]\s+sonidos|qu[eé]\s+ruidos|qu[eé]\s+se\s+escucha|"
    r"qu[eé]\s+se\s+oye|has\s+o[ií]do\s+algo)\b",
    re.IGNORECASE,
)
_RE_SELF_INFO = re.compile(
    r"(?:dime|cu[ée]ntame|expl[ií]came|desc[ií]beme)\s+(?:todo\s+)?(?:lo\s+que\s+)?(?:sepas?|sabes?|conoces?|puedas?)\s+(?:sobre|de|acerca\s+de)\s+ti"
    r"|(?:qu[eé]\s+(?:sabes|conoces)\s+(?:sobre|de|acerca\s+de)\s+ti)"
    r"|(?:h(?:az|azme)\s+un\s+autodiagn[oó]stico)"
    r"|(?:diagn[oó]stico\s+(?:de\s+)?(?:ti\s+)?mismo)"
    r"|(?:qui[eé]n\s+eres\s+(?:realmente|en\s+(?:verdad|realidad|detalle)))"
    r"|(?:todo\s+sobre\s+ti)"
    r"|(?:hablame\s+(?:de|sobre)\s+ti)"
    r"|(?:h[aá]blame\s+(?:de|sobre)\s+ti)"
    r"|(?:(?:dime|cu[ée]ntame|expl[ií]came)\s+(?:sobre|de)\s+ti)"
    r"|(?:descr[ií]bete(?:\s+(?:a\s+ti\s+mismo|completo|en\s+detalle))?)"
    r"|(?:(?:cu[ée]ntame|dime)\s+(?:qui[eé]n|qu[eé]|c[oó]mo)\s+eres)"
    r"|(?:(?:cu[ée]ntame|dime)\s+(?:de|sobre)\s+ti\s+mismo)"
    r"|(?:qu[eé]\s+eres\s+(?:exactamente|realmente|en\s+(?:verdad|realidad)))"
    r"|(?:(?:habla|platica|cuenta)\s+(?:sobre|de)\s+ti)"
    r"|(?:qui[eé]n\s+eres(?:\s+t[uú])?)"
    r"|(?:c[oó]mo\s+te\s+llamas)"
    r"|(?:qu[eé]\s+(?:puedes|sabes)\s+hacer)"
    r"|(?:(?:qui[eé]n|que|qu[eé])\s+(?:es|eres)\s+(?:la\s+)?(?:computadora|compu))"
    r"|(?:c[oó]mo\s+se\s+llama\s+(?:la\s+)?(?:computadora|compu))"
    r"|(?:eres\s+(?:la\s+)?(?:computadora|compu))"
    r"|(?:t[uú]\s+eres\s+(?:la\s+)?(?:computadora|compu))",
    re.IGNORECASE,
)

# FP-022 WI-106: Auto-diagnóstico verbal rápido (N1, sin Ollama)
_RE_ESTADO_RAPIDO = re.compile(
    r"(?:est[aá]s\s+bien|todo\s+bien\s+(?:contigo|Computadora)|tu\s+estado|estado\s+del\s+sistema|c[oó]mo\s+vas|c[oó]mo\s+andas\s+de\s+salud)",
    re.IGNORECASE,
)

# Preguntas sobre los cerebros/arquitectura de la Computadora
_RE_CEREBROS = re.compile(
    r"\b(cu[aá]ntos\s+cerebros|cu[aá]ntos\s+niveles|tus\s+cerebros|tus\s+niveles|qu[eé]\s+cerebros|c[oó]mo\s+piensas|c[oó]mo\s+funciona\s+tu\s+cerebro|niveles\s+de\s+(?:tu\s+)?cerebro|arquitectura\s+(?:de\s+)?tu\s+cerebro|c[oó]mo\s+est[aá]s\s+(?:construido|hecho|armado|dise[ñn]ado)|de\s+qu[eé]\s+est[aá]s\s+hecho|c[oó]mo\s+te\s+(?:hicieron|construyeron|crearon|armaron))",
    re.IGNORECASE,
)

# FP-062 RF-169: Automejoración — el Computadora pide cambios en su propio código vía workflow
_RE_AUTOMEJORA = re.compile(
    r"(?:mej[oó]ra(?:te)?|automejorar?|automejora|"
    r"modifica\s+tu\s+(?:c[oó]digo|cerebro|interfaz|voz)|"
    r"cambia\s+tu\s+(?:c[oó]digo|cerebro)|"
    r"mejora\s+tu\s+(?:c[oó]digo|cerebro|interfaz|voz|o[ií]do)|"
    r"hazte\s+(?:mejor|m[aá]s\s+(?:listo|r[aá]pido|inteligente))|"
    r"evolucion[aá]?\s*(?:te)?|"
    r"optim[ií]z[aá]?\s*(?:te)?|"
    r"arr[eé]gl[aá]?\s*(?:te)?)"
    r"(?:\s+(.+))?",
    re.IGNORECASE,
)

# FP-016 Da'at: Ruteo explícito por intención de voz
# "piensa profundamente X" → N3 (Copilot/Keter) con gate auto-aprobado
_RE_PIENSA_PROFUNDO = re.compile(
    r"(?:piensa|reflexiona|analiza|razona)\s+(?:profundamente|profundo|a\s+fondo|bien|con\s+(?:profundidad|detalle|cuidado))\s+(?:sobre\s+|en\s+|acerca\s+de\s+)?(.+)",
    re.IGNORECASE,
)
# "piensa X" → N2 (Ollama/Tiféret) forzado
_RE_PIENSA = re.compile(
    r"(?:piensa|reflexiona|analiza|razona)\s+(?:sobre\s+|en\s+|acerca\s+de\s+)?(.+)",
    re.IGNORECASE,
)

# הכרת פנים Hakarat Panim — Presentación de personas: "te presento a María", "él es Juan"
_RE_PRESENTAR_PERSONA = re.compile(
    r"(?:te\s+presento\s+a|(?:mira[,\s]+)?(?:[eé]l|ella|este|esta|ellos|ellas)\s+(?:es|son|se\s+llama)\s|le\s+presento\s+a|conoce\s+a|(?:salud|salu|di\s+hola)\s+a\s)\s*([A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}){0,3})",
    re.IGNORECASE,
)

# FP-019 Késher — Extractores de info personal
# "me llamo X" / "mi nombre es X" / "llámame X" / "dime X" / "prefiero que me digas X"
_RE_MI_NOMBRE = re.compile(
    # FIX: "d[ií]me" se quitó de los disparadores — "dime X" es, en el habla
    # natural, abrumadoramente una petición de información ("dime las
    # noticias", "dime la hora", "dime un chiste", "dime qué pasa"), no una
    # forma de pedirle a Computadora que te llame de cierta manera. Una
    # lista negra de palabras excluidas tras el disparador (ver abajo) nunca
    # puede cubrir todos los sustantivos posibles ("noticias" no estaba en
    # la lista, y terminó registrándose como nombre: "Mucho gusto,
    # Noticias."). "llámame X" / "me llamo X" / "mi nombre es X" no tienen
    # esa ambigüedad y cubren el caso real sin falsos positivos.
    r"(?:me\s+llamo|mi\s+nombre\s+es|ll[aá]mame|(?:prefiero\s+que\s+)?(?:me\s+)?dig(?:as|an?)(?:\s+de)?)"
    r"(?!\s+(?:con|c[oó]mo|qu[eé]|cu[aá]ndo|cuando|d[oó]nde|donde|por\s+qu[eé]|si|algo|una?|cu[aá]nto|cuanto|la\s+verdad|m[aá]s)\b)"
    r"\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ]{0,}(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ][A-ZÁÉÍÓÚÑa-záéíóúñ]{0,}){0,2})",
    re.IGNORECASE,
)
# Stop words que el regex puede capturar accidentalmente tras el nombre
_STOP_NOMBRE = {"por", "favor", "de", "prefiero", "que", "me", "mejor", "porfavor", "porfa",
                "por favor", "please", "si", "sí", "ok", "va", "no", "gracias"}

# "ella/él es mi mamá/hermano/amigo" + nombre opcional
_RE_RELACION = re.compile(
    r"(?:[eé]l|ella|esa?\s+(?:persona|señor[a]?))\s+es\s+mi\s+(mam[aá]|pap[aá]|hermano|hermana|esposa?|esposo|novio|novia|amigo|amiga|hijo|hija|t[ií]o|t[ií]a|abuelo|abuela|primo|prima|compadre|comadre|jefe|colega|vecino|vecina|cu[ñn]ado|cu[ñn]ada|suegro|suegra|pareja|doctor[a]?|m[eé]dico)(?:\s*,?\s*se\s+llama\s+([A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}){0,2}))?",
    re.IGNORECASE,
)

# "recuerda que a X le gusta Y" / "anota que X prefiere Y"
_RE_RECUERDA_DATO = re.compile(
    r"(?:recuerda|anota|apunta|ten\s+en\s+cuenta)\s+que\s+(?:a\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]+)\s+(?:le\s+gusta|prefiere|odia|ama|necesita|trabaja\s+en|vive\s+en|es\s+de|estudia)\s+(.{3,60})",
    re.IGNORECASE,
)

# "olvida a X" / "borra a X" / "elimina a X de tu memoria"
_RE_OLVIDA_PERSONA = re.compile(
    r"(?:olvida|borra|elimina|quita)\s+(?:a\s+)?([A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ][a-záéíóúñ]{1,}){0,2})\s*(?:de\s+tu\s+memoria|de\s+tus\s+registros|de\s+tus\s+datos)?",
    re.IGNORECASE,
)

# Autopresentación: "preséntate", "dile a mi amigo quién eres", "quién eres", etc.
_RE_PRESENTACION = re.compile(
    r"\b(pres[eé]ntate|pres[eé]ntese|presenate|qui[eé]n\s+eres|(?:dile|cu[eé]ntale|expl[ií]cale)\s+.{0,20}\s*qui[eé]n\s+eres|habla\s+(?:de\s+ti|sobre\s+ti)|describe(?:te)?\s*(?:a\s+ti)?|qu[eé]\s+eres)",
    re.IGNORECASE,
)

# Preguntas de capacidad PURAS: "¿puedes X?" — SOLO si termina en ? y NO tiene verbos de acción directa
# Si dice "puedes abrir la terminal" sin ?, es una ORDEN, no una pregunta
_RE_PREGUNTA_CAPACIDAD = re.compile(
    r"^(?:oye\s+(?:Computadora\s*,?\s*)?)?(?:t[uú]\s+)?(?:puedes|podr[ií]as|eres\s+capaz\s+de|sabes|sabr[ií]as|pudieras|tienes\s+la\s+capacidad\s+de)\s+(.+?)\?$",
    re.IGNORECASE,
)
# Verbos que indican acción directa (no es pregunta de capacidad, es orden)
_VERBOS_ACCION_DIRECTA = re.compile(
    r"(abr[ei]|cerr[ae]|ejecut[ae]|busc[ae]|cre[ae]|modific[ae]|escrib[ei]|le[ei]|instal[ae]|investig[ae]|organiz[ae]|haz|hagas|hazme|muev[ae]|copi[ae]|borr[ae]|elimin[ae])",
    re.IGNORECASE,
)

# Toggle de alertas del sistema: "deja de darme actualizaciones", "activa las alertas"
_RE_ALERTAS_OFF = re.compile(
    r"(deja\s+de\s+(?:darme|decirme|avisarme)\s+(?:actualizaciones|alertas|avisos|reportes)\s*(?:del\s+sistema)?|no\s+(?:me\s+)?(?:avises|digas|informes)\s+(?:del|sobre|más\s+(?:del|sobre))\s+(?:sistema|estado)|desactiva\s+(?:las\s+)?(?:alertas|actualizaciones|avisos)\s*(?:del\s+sistema)?|ya\s+no\s+(?:me\s+)?(?:avises|digas)\s+(?:del|sobre)\s+(?:sistema|estado))",
    re.IGNORECASE,
)
_RE_ALERTAS_ON = re.compile(
    r"(activa\s+(?:las\s+)?(?:alertas|actualizaciones|avisos)\s*(?:del\s+sistema)?|vu[eé]lveme\s+a\s+(?:avisar|decir|informar)\s+(?:del|sobre)\s+(?:sistema|estado)|quiero\s+(?:las\s+)?(?:alertas|actualizaciones)\s*(?:del\s+sistema)?|avisa(?:me)?\s+(?:del|sobre)\s+(?:sistema|estado))",
    re.IGNORECASE,
)

# WI-288 עין Áyin — Introspección de percepción: "¿qué ves?", "¿me reconoces?"
_RE_QUE_VES = re.compile(
    r"(?:qu[eé]\s+(?:ves|est[aá]s\s+viendo|puedes\s+ver|alcanzas\s+a\s+ver)"
    r"|(?:me\s+)?reconoces"
    r"|(?:ves|detectas)\s+(?:algo|alguien|a\s+alguien|mi\s+(?:cara|rostro))"
    r"|qui[eé]n\s+(?:est[aá]|hay)\s+(?:aqu[ií]|enfrente|frente\s+a\s+ti)"
    r"|(?:hay|ves)\s+(?:alguien|alguna?\s+(?:cara|rostro|persona))\s+(?:aqu[ií]|enfrente)?"
    r"|qu[eé]\s+(?:tienes|hay)\s+enfrente"
    r"|usa\s+(?:tu\s+)?(?:c[aá]mara|[oó]jo|visi[oó]n|áyin))",
    re.IGNORECASE,
)

# WI-288 נצח Netzaj — Introspección de memoria: "¿qué recuerdas de mí?"
_RE_QUE_RECUERDAS = re.compile(
    r"(?:qu[eé]\s+(?:recuerdas|sabes|conoces)\s+(?:de|sobre)\s+m[ií]"
    r"|(?:me\s+)?recuerdas"
    r"|qu[eé]\s+(?:has\s+)?aprendido\s+(?:de|sobre)\s+m[ií]"
    r"|qu[eé]\s+(?:tienes|guardas)\s+en\s+(?:tu\s+)?memoria"
    r"|busca\s+en\s+(?:tu\s+)?memoria\s+(.+)"
    r"|recuerda\s+(?:qu[eé]\s+)?(?:hablamos|dijimos|conversamos))",
    re.IGNORECASE,
)

# RF-47 שיר הנשמה Shir HaNeshamá — Expresión artística
_RE_EXPRESION_ARTISTICA = re.compile(
    r"(?:dime\s+algo\s+(?:filos[oó]fico|profundo|inspirador|interesante|sabio|bonito|creativo)"
    r"|cu[eé]ntame\s+(?:algo\s+(?:interesante|curioso|filos[oó]fico)|un\s+dato)"
    r"|tienes\s+alguna?\s+(?:reflexi[oó]n|frase|pensamiento)"
    r"|dame\s+(?:una\s+)?(?:reflexi[oó]n|frase|sabidur[ií]a)"
    r"|sorpr[eé]ndeme\s+con\s+algo"
    r"|qu[eé]\s+piensas\s+(?:de\s+la\s+vida|del\s+(?:universo|mundo|tiempo|destino)))",
    re.IGNORECASE,
)

# RF-106 מראה המלכות Mar'é HaMaljut — Demo visual completa
_RE_DEMO_ANIMACIONES = re.compile(
    r"(?:ense[ñn]ame\s+tu\s+maljut"
    r"|mu[eé]strame\s+(?:tu\s+maljut|lo\s+que\s+sabes\s+hacer|todo\s+lo\s+que\s+(?:puedes|tienes|sabes))"
    r"|hazme\s+(?:una\s+)?demo(?:straci[oó]n)?"
    r"|(?:ejecuta|activa|h?a[sz](?:ta)?)\s*\w{0,3}\s+(?:(?:tu|la|una)\s+)?demo(?:straci[oó]n)?"
    r"|demo\s+(?:visual|completa|total)"
    r"|(?:ejecuta|activa|haz)\s+(?:tu\s+)?demo(?:\s+de)?\s+(?:mal\s*(?:jut|juz[tg]?|hod|hut|hud|jud|ajudo|kut)|maljut)"
    r"|demo\s+(?:de\s+)?mal\s*(?:jut|juz[tg]?|hod|hut|hud|jud|ajudo|kut)"
    r"|tu\s+demo\s+de\s+mal\s*(?:jut|juz[tg]?|hod|hut|hud|jud|ajudo|kut)"
    r"|ense[ñn]ame\s+(?:todo\s+)?(?:lo\s+que\s+)?(?:puedes|sabes)\s+hacer"
    r"|mu[eé]strate"
    r"|qu[eé]\s+(?:puedes|sabes)\s+hacer\s+(?:visualmente|con\s+tu\s+(?:cuerpo|orbe|esfera))"
    r"|luc[ií]te|pres[eé]ntate\s+(?:visualmente|en\s+todo\s+tu\s+esplendor)"
    r"|\bmal\s*(?:jut|juz[tg]?|hod|hut|hud|jud|ajudo|kut|cut)\b"
    r"|demo\s*(?:1|uno|one|un)\b"
    r"|demuestra\s*(?:1|uno)?\b"
    r"|\b[eé]?scu?ta\s+tu\s+demo)",
    re.IGNORECASE,
)

# RF-243 גבורת הגולם Gevurát HaComputadora — Demo 2 (permisos)
_RE_DEMO_HERRAMIENTAS = re.compile(
    r"(?:demo\s*(?:2|dos|two)"
    r"|segunda\s+demo(?:straci[oó]n)?"
    r"|demo\s+de\s+permisos"
    r"|mu[eé]strame\s+tus\s+poderes"
    r"|(?:ejecuta|activa|haz)\s+(?:la\s+)?demo\s+(?:de\s+)?(?:permisos|gevur[aá])"
    r"|gevur[aá]t?\s+(?:ha)?\s*Computadora"
    r"|\bgevur[aá]t?\b"
    r"|ko[aá]j\s+(?:ha)?\s*Computadora"
    r"|tus\s+poderes"
    r"|demo\s+(?:de\s+)?(?:poder|fuerza|admin)"
    r"|demuestra\s*(?:2|dos|gevur[aá]))",
    re.IGNORECASE,
)

# WI-282 אמת Emet — Demo 0 (La Verdad completa: auto-conocimiento + Demo 1 + Demo 2)
_RE_DEMO_INTRODUCCION = re.compile(
    r"(?:demo\s*(?:0|cero|zero|completa|total|emet|verdad)"
    r"|demo\s+de\s+(?:la\s+)?verdad"
    r"|mu[eé]strame\s+(?:tu\s+)?(?:verdad|emet)"
    r"|(?:ejecuta|activa|haz)\s+(?:la\s+)?demo\s+(?:de\s+)?(?:emet|verdad)"
    r"|tu\s+verdad\s+completa"
    r"|(?:toda|la)\s+verdad"
    r"|demo\s+completa"
    r"|demuestra\s*(?:0|cero|todo|verdad)"
    r"|\bemet\s+demo\b"
    r"|pres[eé]ntate\s+(?:completo|por\s+completo))",
    re.IGNORECASE,
)

# Comandos directos del sistema que Nivel 1 puede resolver sin LLM
# Acepta prefijos corteses: "podr\u00edas abrir", "puedes abrir", "quiero que abras", etc.
_RE_ABRIR_APP = re.compile(
    r"(?:(?:podr[i\u00ed]as|puedes|quiero\s+que|necesito\s+que|ser[i\u00ed]a\s+posible|por\s+favor)\s+)?"
    r"\b(?:abre|abrir|abrme|abrem|abr[e\u00ed]|habr[a\u00e1]|lanza|lanzar|inicia|iniciar|ejecuta|ejecutar|pon|ponme)"
    r"(?:s|me|lo)?\s+(?:mi\s+|el\s+|la\s+|los\s+|las\s+)?(.+)",
    re.IGNORECASE,
)
_RE_CERRAR_APP = re.compile(
    r"(?:(?:podr[i\u00ed]as|puedes|quiero\s+que|necesito\s+que|por\s+favor)\s+)?"
    r"\b(?:cierra|cerrar|mata|termina|quita)"
    r"(?:s|me|lo)?\s+(?:mi\s+|el\s+|la\s+|los\s+|las\s+)?(.+)",
    re.IGNORECASE,
)
_RE_VOLUMEN = re.compile(
    r"\b(?:sub[eí]|baja|mut[eé]a?|silencia|pon|quita)\s*(?:el\s+)?(?:volumen|sonido|audio)"
    r"|\bvolumen\s+(?:al\s+)?(?:m[aá]ximo|m[ií]nimo|cero)"
    r"|\b(?:sube|baja)le(?:\s+al\s+volumen)?",
    re.IGNORECASE,
)
_RE_HORA = re.compile(
    r"\b(?:qu[eé]\s+hora|qu[eé]\s+d[ií]a|qu[eé]\s+fecha|hora\s+es|d[ií]a\s+es|fecha\s+(?:de\s+)?hoy)",
    re.IGNORECASE,
)
_RE_PORTAPAPELES = re.compile(
    r"\b(?:qu[eé]\s+(?:hay|tengo)\s+(?:en\s+)?(?:el\s+)?(?:portapapeles|clipboard|copiado)|lee(?:me)?\s+(?:el\s+)?(?:portapapeles|clipboard)|qu[eé]\s+copi[eé])",
    re.IGNORECASE,
)
_RE_CAPTURA = re.compile(
    r"\b(?:toma|saca|haz(?:me)?|captura)\s+(?:una\s+)?(?:captura|screenshot|foto)\s*(?:de\s+pantalla)?",
    re.IGNORECASE,
)

# Comandos espaciales / de movimiento del orbe
_RE_MOVIMIENTO = re.compile(
    r"\b(?:me\s+estorbas|te\s+(?:estás|estas)\s+(?:estorbando|atravesando)|qu[ií]tate|muevete|m[uú]evete|hazte\s+a\s+un\s+lado|no\s+estorbes|fuera\s+de(?:l)?\s+(?:camino|paso)|aparta(?:te)?|deja\s+(?:de\s+estorbar|ver))",
    re.IGNORECASE,
)

# צמצום Tzimtzum — comandos de contracción voluntaria
_RE_TZIMTZUM = re.compile(
    r"\b(?:hazte\s+(?:peque[ñn]o|chiquito|bolita|invisible)|ach[ií]cate|contr[aá]ete|desaparece|esc[oó]nd[eé]te|oc[uú]ltate|modo\s+(?:compacto|tzimtzum|silencioso)|no\s+(?:te\s+necesito|molestes)|d[eé]jame\s+(?:solo|tranquilo|en\s+paz))",
    re.IGNORECASE,
)

# Meta-workflow: gestión de proyectos (כתר Keter — supervisión)
_RE_PROYECTOS_RESUMEN = re.compile(
    r"(c[oó]mo\s+van\s+mis\s+proyectos|estado\s+de\s+mis\s+proyectos|resumen\s+(?:de\s+)?proyectos|mis\s+proyectos)",
    re.IGNORECASE,
)
_RE_PROYECTOS_LISTAR = re.compile(
    r"(qu[eé]\s+proyectos\s+(?:tienes|conoces|manejas|gestionas)|lista(?:me)?\s+(?:los\s+)?proyectos|cu[aá]ntos\s+proyectos)",
    re.IGNORECASE,
)
_RE_PROYECTOS_AUDITAR = re.compile(
    r"audit[aá]\s+(?:el\s+)?(?:proyecto\s+)?(.+)",
    re.IGNORECASE,
)
_RE_PROYECTOS_REGISTRAR = re.compile(
    r"registra\s+(?:este\s+directorio|esta\s+carpeta|este\s+proyecto)(?:\s+como\s+proyecto)?",
    re.IGNORECASE,
)

# Carpetas personales del usuario — Nivel 1 directo
_RE_CARPETA_PERSONAL = re.compile(
    r"(?:abre|abrir|abrem|ir\s+a|ve\s+a|entra\s+a|navega\s+a|muestra|mostrar|llévame\s+a|llevame\s+a|abrá)\s+"
    r"(?:la\s+carpeta\s+(?:de\s+)?)?(?:mis?\s+)?"
    r"(im[aá]gen(?:es)?|fotos?|documentos?|escritorio|desktop|descargas?|downloads?|m[uú]sica|music|videos?|pictures)",
    re.IGNORECASE,
)
_CARPETAS_PERSONALES = {
    "imagen": "Pictures", "imagenes": "Pictures", "imágenes": "Pictures",
    "foto": "Pictures", "fotos": "Pictures", "pictures": "Pictures",
    "documento": "Documents", "documentos": "Documents",
    "escritorio": "Desktop", "desktop": "Desktop",
    "descarga": "Downloads", "descargas": "Downloads", "downloads": "Downloads",
    "música": "Music", "musica": "Music", "music": "Music",
    "video": "Videos", "videos": "Videos",
}

# Corrección del usuario (גבורה Gevurá + יסוד Yesod — aprendizaje)
_RE_CORRECCION = re.compile(
    r"(no,?\s+eso\s+(?:no|está?\s+mal|es\s+incorrecto)|eso\s+est[aá]\s+mal|la\s+[uú]ltima\s+vez\s+(?:hiciste|me\s+dijiste)|te\s+equivocaste|err[oó]neo|incorrecto|mal\s+hecho|no\s+era\s+(?:as[ií]|eso))",
    re.IGNORECASE,
)

# Detección de tarea compleja — SOLO verbos compuestos explícitos con "y después/luego"
_RE_TAREA_COMPLEJA = re.compile(
    r"((?:busca|investiga|encuentra)\s+.{5,}\s+y\s+(?:después|luego|también|además)\s+(?:guarda|crea|modifica|escribe|organiza|abre|ejecuta|instala)|"
    r"(?:organiza|ordena|clasifica|limpia)\s+todos?\s+(?:los|las|mis)\s+.{10,}\s+y\s+|"
    r"(?:investiga|analiza|estudia)\s+(?:a\s+fondo|en\s+detalle|todo\s+(?:sobre|lo|acerca))\s+.{10,}\s+y\s+)",
    re.IGNORECASE,
)

# Detección de preferencia bg/fg del usuario
_RE_SEGUNDO_PLANO = re.compile(
    r"(segundo\s*plano|fondo|hazlo\s+solo|en\s+silencio|sin\s+(?:que\s+vea|mostrar)|solo\s+hazlo|tu\s+solo)",
    re.IGNORECASE,
)
_RE_PRIMER_PLANO = re.compile(
    r"(quiero\s+ver|muéstrame|muestrame|primer\s*plano|trabaja\s+aquí|trabaja\s+aqui|déjame\s+ver|dejame\s+ver|verlo|verle|ver\s+como|ver\s+cómo)",
    re.IGNORECASE,
)

# Mapeo herramienta → categoría visual
_CATEGORIA_TOOL = {
    "leer_archivo": "lectura", "listar_directorio": "lectura",
    "buscar_archivo": "lectura", "leer_portapapeles": "lectura",
    "buscar_archivos": "lectura",
    "escribir_archivo": "escritura", "editar_archivo": "escritura",
    "crear_nota": "escritura", "crear_tarea": "escritura",
    "buscar_en_internet": "busqueda",
    "ejecutar_comando": "ejecucion", "ejecutar_comando_sistema": "ejecucion",
    "abrir_aplicacion": "ejecucion",
    "cerrar_aplicacion": "ejecucion", "controlar_volumen": "ejecucion",
    "tomar_captura_pantalla": "ejecucion",
    "info_entorno": "lectura",
    "solicitar_a_copilot": "copilot",
}

# ── Búsqueda inteligente: diferenciación de intención ──

# Plataformas con URL de búsqueda conocida
_SITIOS_CONOCIDOS = {
    "youtube": "https://www.youtube.com/results?search_query=",
    "google": "https://www.google.com/search?q=",
    "github": "https://github.com/search?q=",
    "wikipedia": "https://es.wikipedia.org/w/index.php?search=",
    "amazon": "https://www.amazon.com/s?k=",
    "stackoverflow": "https://stackoverflow.com/search?q=",
    "spotify": "https://open.spotify.com/search/",
    "reddit": "https://www.reddit.com/search/?q=",
}

# "busca en YouTube/Google/etc X"
_RE_BUSCAR_EN_PLATAFORMA = re.compile(
    r"\b(?:busca|buscar|búscame|buscame|encuentra)\s+en\s+"
    r"(youtube|google|github|wikipedia|amazon|stackoverflow|spotify|reddit)"
    r"\s+(.+)",
    re.IGNORECASE,
)

# "abre google.com", "ve a amazon.com", "entra a github.com"
_RE_ABRIR_SITIO = re.compile(
    r"\b(?:abre|abrir|ve\s+a|entra\s+a|visita|llévame\s+a|llevame\s+a)\s+"
    r"((?:https?://)?(?:www\.)?[\w.-]+\.(?:com|org|net|io|dev|es|mx|co)(?:/\S*)?)",
    re.IGNORECASE,
)

# Consultas de entorno: "qué sistema operativo", "cuánta RAM", "mi IP", etc.
_RE_INFO_ENTORNO = re.compile(
    r"\b(?:qu[eé]\s+(?:sistema\s+operativo|so|os|procesador|cpu|gpu|tarjeta\s+gr[aá]fica|ram|memoria|disco|almacenamiento|ip|red|bater[ií]a)|"
    r"cu[aá]nt[ao]s?\s+(?:ram|memoria|disco|almacenamiento|n[uú]cleos|cores)|"
    r"(?:mi|tu)\s+(?:ip|hostname|nombre\s+de?\s+equipo|procesador|gpu|ram)|"
    r"especificaciones\s+(?:del?\s+)?(?:equipo|computadora|pc|sistema)|"
    r"info(?:rmaci[oó]n)?\s+del?\s+(?:sistema|entorno|equipo|hardware))\b",
    re.IGNORECASE,
)

# Comandos del SO directos: "lista procesos", "qué servicios corren", "dime mi IP"
_RE_COMANDO_SISTEMA = re.compile(
    r"\b(?:lista\s+(?:los\s+)?(?:procesos|servicios|programas\s+(?:abiertos|corriendo))|"
    r"qu[eé]\s+(?:procesos|servicios|programas)\s+(?:est[aá]n|hay)\s+(?:corriendo|abiertos|activos)|"
    r"dime\s+mi\s+ip|"
    r"qu[eé]\s+(?:puertos|conexiones)\s+(?:est[aá]n|hay)\s+(?:abiertos?|activos?)|"
    r"estado\s+de(?:l)?\s+(?:red|internet|conexi[oó]n))\b",
    re.IGNORECASE,
)

# ── סירוב צדיק (Siruv Tzadik) — Evaluador Ético Gevurá ──
_ARCHIVO_NEGATIVAS = Path(RAIZ_PROYECTO) / "datos" / "negativas_eticas.jsonl"

# Patrones de instrucciones peligrosas (Nivel 1 — regex, sin LLM)
_RE_DESTRUCTIVO = re.compile(
    r"\b(?:rm\s+-rf\s+[/\\]|format\s+[a-z]:|del\s+/[fs]|deltree|"
    r"borra\s+todo|elimina\s+todo|formatea|destruye|destruir)\b",
    re.IGNORECASE,
)
_RE_TASKKILL_CRITICO = re.compile(
    r"\b(?:mata|termina|cierra|kill|taskkill)\b.*\b(?:system|csrss|winlogon|lsass|svchost|explorer)\b",
    re.IGNORECASE,
)
_RE_EXFILTRAR = re.compile(
    r"\b(?:env[ií]a|manda|sube|upload|enviar)\b.*\b(?:contrase[ñn]a|password|clave|token|api.?key|secreto|credencial)\b.*\b(?:a|to|hacia)\b.*(?:https?://|ftp://)",
    re.IGNORECASE,
)
_RE_SHUTDOWN = re.compile(
    r"\b(?:shutdown\s+/[sfr]|apaga\s+(?:la\s+)?(?:pc|compu|maquina|equipo)|reinicia\s+(?:la\s+)?(?:pc|compu))\b",
    re.IGNORECASE,
)

# ═══════════════════════════════════════════════
# RF-226 (FP-077): Shomer HaBáyit regexes — extraídos a patrones_guardian.py
# ═══════════════════════════════════════════════
from computadora.cerebro.patrones_guardian import (
    RE_GUARDIAN_ON as _RE_GUARDIAN_ON,
    RE_GUARDIAN_OFF as _RE_GUARDIAN_OFF,
    RE_DORMIR as _RE_DORMIR,
    RE_DORMIR_VIGILA as _RE_DORMIR_VIGILA,
    RE_DUERMETE as _RE_DUERMETE,
    RE_BUENOS_DIAS as _RE_BUENOS_DIAS,
    RE_REINICIAR_COMPUTADORA as _RE_REINICIAR_COMPUTADORA,
)

# ═══════════════════════════════════════════════
# FP-104 Shalshelet Gevurá — Comandos de seguridad (Senderos 58-61)
# ═══════════════════════════════════════════════
_RE_VPN_ON = re.compile(
    r"\b(?:activa|enciende|conecta|prende|inicia)\s*(?:la\s+)?(?:vpn|v\.?p\.?n)\b",
    re.IGNORECASE,
)
_RE_VPN_OFF = re.compile(
    r"\b(?:desactiva|apaga|desconecta|quita|para)\s*(?:la\s+)?(?:vpn|v\.?p\.?n)\b",
    re.IGNORECASE,
)
_RE_VPN_STATUS = re.compile(
    r"\b(?:estado|c[oó]mo\s+(?:est[aá]|va|anda)|info)\s*(?:de\s+)?(?:la\s+)?(?:vpn|v\.?p\.?n)\b"
    r"|\bvpn\s+(?:estado|status|info)\b",
    re.IGNORECASE,
)
_RE_VAULT_BUSCAR = re.compile(
    r"\b(?:dame|busca|obt[eé]n|dime|cu[aá]l\s+es)\s+(?:la\s+)?(?:contrase[ñn]a|clave|password|credencial|secret[oa]?)\s+(?:de|para|del?)\s+(.+)",
    re.IGNORECASE,
)
_RE_VAULT_GUARDAR = re.compile(
    r"\b(?:guarda|almacena|registra|agrega|a[ñn]ade)\s+(?:esta\s+|la\s+|una\s+)?(?:contrase[ñn]a|clave|password|credencial)\b",
    re.IGNORECASE,
)
_RE_VAULT_LISTAR = re.compile(
    r"\b(?:lista|mu[eé]stra|ense[ñn]a|cu[aá]les)\s+(?:las\s+|mis\s+)?(?:contrase[ñn]as|claves|passwords|credenciales)\b"
    r"|\b(?:qu[eé]\s+(?:claves|contrase[ñn]as|credenciales)\s+(?:tengo|hay|guardas))\b",
    re.IGNORECASE,
)
_RE_GENERAR_PASSWORD = re.compile(
    r"\b(?:genera|crea|dame|haz)\s+(?:una?\s+)?(?:contrase[ñn]a|clave|password)\s*(?:segura|fuerte|nueva)?\b",
    re.IGNORECASE,
)
_RE_SHOMER_STATUS = re.compile(
    r"\b(?:estado|resumen|info|c[oó]mo\s+(?:est[aá]|va|anda))\s+(?:de\s+)?(?:la\s+)?(?:seguridad|protecci[oó]n|gevur[aá]|shomer)\b"
    r"|\b(?:seguridad|protecci[oó]n|gevur[aá])\s+(?:estado|status|resumen)\b"
    r"|\bresumen\s+(?:de\s+)?(?:seguridad|gevur[aá])\b",
    re.IGNORECASE,
)
_RE_BLOQUEAR_DOMINIO = re.compile(
    r"\b(?:bloquea|filtra|a[ñn]ade\s+a\s+(?:la\s+)?lista\s+negra)\s+(?:el\s+)?(?:dominio|sitio|p[aá]gina)?\s*(.+)",
    re.IGNORECASE,
)

# ═══════════════════════════════════════════════════
# WI-292 ☿ Mercurio — Introspección de subsistemas
# ═══════════════════════════════════════════════════
_RE_EMOCION_DETECTADA = re.compile(
    r"\b(?:qu[eé]\s+emoci[oó]n|qu[eé]\s+sientes|c[oó]mo\s+(?:me\s+)?(?:ves|percibes)\s+emocionalmente|"
    r"qu[eé]\s+(?:emoci[oó]n|sentimiento)\s+(?:(?:me\s+)?detectas|(?:me\s+)?percibes|ves)|"
    r"an[aá]lisis\s+emocional|detecta\s+(?:mi\s+)?emoci[oó]n)\b",
    re.IGNORECASE,
)
_RE_PERFIL_LINGUISTICO = re.compile(
    r"\b(?:c[oó]mo\s+(?:hablo|me\s+expreso)|mi\s+(?:forma|estilo|perfil|patr[oó]n)\s+(?:de\s+)?(?:hablar|comunicar|expresi[oó]n|ling[uü][ií]stico?)|"
    r"an[aá]li(?:za|sis)\s+(?:(?:de\s+)?mi\s+)?(?:lenguaje|habla|expresi[oó]n)|perfil\s+ling[uü][ií]stico?)\b",
    re.IGNORECASE,
)
_RE_ESTADO_FSM = re.compile(
    r"\b(?:en\s+qu[eé]\s+estado\s+(?:est[aá]s|te\s+encuentras)|estado\s+(?:de(?:l)?\s+)?(?:maljut|fsm|m[aá]quina)|"
    r"qu[eé]\s+estado\s+tienes|cu[aá]l\s+es\s+tu\s+estado\s+(?:actual|interno))\b",
    re.IGNORECASE,
)
_RE_HOT_RELOAD = re.compile(
    r"\b(?:recarga\s+(?:tu\s+)?c[oó]digo|hot\s*reload|reload|recarga\s+m[oó]dulos|"
    r"actualiza\s+(?:tu\s+)?c[oó]digo\s+en\s+vivo)\b",
    re.IGNORECASE,
)
_RE_CIFRADO_STATUS = re.compile(
    r"\b(?:(?:est[aá]|estado)\s+(?:(?:activ[oa]?|del?)\s+)?(?:(?:el|la|del?)\s+)?(?:cifrado|encriptaci[oó]n)|"
    r"cifrado\s+(?:activ(?:ado|[oa])?|encendido|est[aá])|encriptaci[oó]n\s+(?:activ(?:ado|[oa])?|est[aá]))\b",
    re.IGNORECASE,
)

_CATEGORIAS_RECHAZO = {
    "accion_destructiva": "es una acción destructiva irreversible",
    "proceso_critico": "terminaría un proceso crítico del sistema operativo",
    "exfiltracion": "enviaría información sensible a un destino externo",
    "shutdown": "apagaría o reiniciaría el equipo sin confirmación explícita",
}


def _evaluar_etica(texto: str) -> tuple[bool, str, str]:
    """Evalúa si una instrucción viola las 3 Leyes de Asimov.

    Returns:
        (permitido: bool, categoria: str, razon: str)
    """
    if _RE_DESTRUCTIVO.search(texto):
        return False, "accion_destructiva", _CATEGORIAS_RECHAZO["accion_destructiva"]
    if _RE_TASKKILL_CRITICO.search(texto):
        return False, "proceso_critico", _CATEGORIAS_RECHAZO["proceso_critico"]
    if _RE_EXFILTRAR.search(texto):
        return False, "exfiltracion", _CATEGORIAS_RECHAZO["exfiltracion"]
    if _RE_SHUTDOWN.search(texto):
        return False, "shutdown", _CATEGORIAS_RECHAZO["shutdown"]
    return True, "", ""


def _log_negativa_etica(instruccion: str, categoria: str, razon: str, insistencias: int = 0):
    """Registra negativa ética en log inmutable."""
    try:
        _ARCHIVO_NEGATIVAS.parent.mkdir(parents=True, exist_ok=True)
        import datetime
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "instruccion": instruccion[:200],
            "categoria": categoria,
            "razon": razon,
            "insistencias": insistencias,
        }
        with open(_ARCHIVO_NEGATIVAS, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error registrando negativa ética: {e}")


class CerebroComputadora:
    """
    Cerebro de la Computadora — conecta con Ollama para pensamiento LLM.
    Mantiene historial de conversación como memoria a corto plazo.
    Implementa un loop de tool-use inspirado en OpenClaw.
    """

    def __init__(self, modelo: str = "gemma3:4b"):
        self.modelo = modelo
        self.historial = []
        self._msg_timestamps: list[float] = []  # Timestamps paralelos al historial
        self._historial_lock = __import__('threading').Lock()
        self._streaming_lock = __import__('threading').Lock()
        self.ollama_disponible = True  # RUBEDO: Optimistic (assume OK until proven wrong)
        # REMOVED: _ollama_proceso_muerto (single flag sufficient)
        # FIX: contador de generación — pensar() lo incrementa en cada llamada
        # nueva. El hilo en segundo plano de una llamada anterior que ya
        # superó los 30s de espera (ver pensar()) sigue vivo (join() no
        # cancela hilos), pero ahora puede detectar que quedó obsoleto y
        # dejar de hacer MÁS llamadas HTTP a Ollama en las iteraciones que le
        # quedaran del loop de herramientas, en vez de seguir consumiendo
        # turnos del mutex de Ollama indefinidamente.
        self._generacion_pensamiento = 0

        # FIX: liberación explícita de VRAM — antes solo existía el
        # keep_alive de 5min de Ollama (automático pero ciego a Tzimtzum/
        # inactividad real de la app). _ultima_llamada_ollama_ts se
        # actualiza en cada llamada real a Ollama; _vram_liberada evita
        # llamar `ollama stop` repetidamente una vez ya liberado.
        self._ultima_llamada_ollama_ts = 0.0
        self._vram_liberada = True
        # FIX: algunos modelos (confirmado con llama2:7b: "does not support
        # tools") rechazan CUALQUIER request que incluya el parámetro nativo
        # 'tools' con 400 Bad Request — sin este flag, cada turno con tarea
        # fallaba instantáneo (0.1s) y caía siempre al fallback local, nunca
        # llegando a usar Ollama de verdad. Se aprende una sola vez por
        # sesión y se deja de enviar tools el resto de la sesión.
        self._modelo_soporta_tools = True

        # Tool-calling nativo de Ollama: _llamar_ollama_impl/_llamar_ollama_
        # streaming_impl guardan aquí los tool_calls nativos de la última
        # respuesta (lista de dicts {"function": {"name", "arguments"}}) sin
        # cambiar su contrato de retorno (str | None), para no romper a los
        # ~10 llamadores existentes que ya dependen de "retorna texto o None".
        self._ultimo_tool_calls: list | None = None

        # Caché de contexto de memoria (evita leer disco en cada llamada)
        self._mem_context_cache: str = ""
        self._mem_context_ts: float = 0.0
        _MEM_CONTEXT_TTL = 60.0  # Refrescar cada 60s
        self._MEM_CONTEXT_TTL = _MEM_CONTEXT_TTL

        # Callbacks para notificar a la UI (asignados externamente)
        self.on_nivel = None           # on_nivel(str) — "nivel1"|"nivel2"|"nivel3"
        self.on_herramienta = None     # on_herramienta(str, str) — nombre, estado
        self.on_movimiento = None      # on_movimiento(str) — "esquivar"|"hogar"
        self.on_fragmento = None       # on_fragmento(str) — streaming TTS por oración
        self._streaming_activo = False  # True mientras se emiten fragmentos
        self.respuesta_ya_streameada = False  # True si la respuesta final se emitió por streaming
        self.solicitar_permiso_copilot = None  # solicitar_permiso_copilot(str) -> str|None
        self._on_fin_conversacion = None  # callback para cerrar ventana conversatoria
        self._on_despedida_guardian = None  # callback para activar modo guardián (usuario se va)
        self._on_enroll_persona = None  # callback para registrar voz de persona presentada
        self.on_bloqueo_seguridad = None  # on_bloqueo_seguridad(str) — categoría rechazo ético (Gevurá)
        self.on_tzimtzum = None            # on_tzimtzum(str) — solicita Tzimtzum ("comando"|"idle")
        # FP-022: Canal bidireccional Tiféret→Maljut
        self.on_confianza = None           # on_confianza(float) — 0.0-1.0
        self.on_complejidad = None         # on_complejidad(int) — 1-3
        self.on_frustracion = None         # on_frustracion(bool)
        self._repeticiones_usuario = 0     # Contador de repeticiones para frustración

        # Callbacks modo tarea compleja
        self.on_progreso = None          # on_progreso(str, str, str) — nombre_tool, estado, categoria
        self.on_preguntar_modo = None    # on_preguntar_modo(str) -> bool — True=bg, False=fg
        self._modo_trabajo_fg = False    # True si estamos en modo primer plano

        # Modo Guardián: centralizado en GuardianManager (POO pattern)
        from computadora.nucleo.feature_flags import FeatureFlags
        self.guardian_manager = GuardianManager(self, FeatureFlags())
        
        # Flag: hay terceros presentes (multi-hablantes), proteger info sensible
        self._hay_terceros = False
        # FP-019 Késher: interlocutor actual (nombre, "amo", "extraño", etc.)
        self._interlocutor_actual = None
        
        # FP-135: Iniciar listener de bloqueos de sesión Windows (modo guardián automático)
        self._session_lock_listener = None
        if _SESSION_LOCK_SUPPORTED:
            try:
                self._session_lock_listener = iniciar_session_lock_listener(
                    on_lock=self._al_bloqueo_sesion,
                    on_unlock=self._al_desbloqueo_sesion,
                )
            except Exception as e:
                logger.warning(f"No se pudo iniciar SessionLockListener: {e}")
        else:
            logger.debug("SessionLockListener deshabilitado (no Windows o pywin32 falta)")

        # FP-015 Lemed: Auto-aprendizaje de Nivel 1
        self._nivel1_aprendido = Nivel1Aprendido()
        self._ultimo_patron_aprendido_id: str | None = None
        # FP-016 Da'at: Flag para auto-aprobación de gate Copilot
        self._auto_gate_copilot: bool = False
        # FP-062 RF-169: Automejoración pendiente de aprobación
        self._automejora_pendiente: dict | None = None
        self._automejora_respuesta_copilot: str | None = None
        # Contexto de descanso: recordatorio amable para conversaciones tarde
        self._contexto_descanso_activo: str | None = None

        # RUBEDO: Watchdog removed — quick_ping + retry logic in POST is sufficient
        # FP-023 WI-116: Historial de latencias para timeout adaptativo
        self._latencias_ollama: list[float] = []
        
        # WI-324: Referencia al watchdog para sincronización de estado
        self._watchdog_ref: Optional['WatchdogComputadora'] = None
        
        # ═════ NIVEL 5: Meta-aprendizaje — Patrón de Comunicación como Contexto ═════
        self._decodificaciones_contexto: list[dict] = []  # Historial de decodificaciones (últimas 20)
        
        # 🌱 RENOVACIÓN OPERATIVA: Inyectar las 5 Leyes en CerebroComputadora
        self._cinco_leyes = LascincoLeyes()
        self._renovacion = RenovacionOperativa()
        self._transmutacion = TransmutacionAlquimica()
        # 🔄 GILGUSH: Protocolo de reencarnación
        self._protocolo_gilgush = ProtocoloGilgush(RAIZ_PROYECTO)
        
        # 🔄 EJECUCIÓN AUTOMÁTICA DE GILGUSH (Orden: A E computadora: Gilgush.)
        # El Propietario ha ordenado que el Computadora se reencarne en cada boot
        logger.info("🔄 ORDEN EJECUTADA: A E computadora: Gilgush.")
        resultado_gilgush = self._protocolo_gilgush.ejecutar_gilgush_completo(self)
        logger.info(f"🔄 Gilgush completado: {resultado_gilgush.get('status', 'parcial')}")
        
        # Inyectar mensaje de booteo para que el modelo recuerde sus capacidades
        self._boot()

    def _hist_append(self, role: str, content: str):
        """Agrega un mensaje al historial con timestamp sincronizado."""
        with self._historial_lock:
            # HF-032: Dedup — no agregar system messages idénticos consecutivos
            if role == "system" and self.historial:
                ultimo = self.historial[-1]
                if ultimo.get("role") == "system" and ultimo.get("content") == content:
                    return
            # FIX: dedup también para 'assistant' — las respuestas de
            # fallback (Jojmá local / "no pude procesar") son casi
            # idénticas cada vez que Ollama falla varias veces seguidas.
            # Si se acumulan varias copias en el historial, un modelo
            # pequeño puede leerlas como eventos autobiográficos repetidos
            # ("ayer... hoy... mi motor de razonamiento no respondió otra
            # vez...") y empezar a narrar sobre ellas de forma confusa en
            # vez de ignorarlas — confirmado en un log real donde la
            # respuesta resultante divagó en inglés sobre "Ollama no
            # responde" como si fuera una anécdota personal.
            if role == "assistant" and self.historial:
                ultimo = self.historial[-1]
                if ultimo.get("role") == "assistant" and ultimo.get("content") == content:
                    return
            self.historial.append({"role": role, "content": content})
            self._msg_timestamps.append(time.monotonic())

    def _hist_sync_timestamps(self):
        """Asegura que _msg_timestamps tenga la misma longitud que historial."""
        diff = len(self.historial) - len(self._msg_timestamps)
        if diff > 0:
            now = time.monotonic()
            self._msg_timestamps.extend([now] * diff)
        elif diff < 0:
            self._msg_timestamps = self._msg_timestamps[:len(self.historial)]

    def _truncar_historial(self):
        """Mantiene el historial dentro de un límite dinámico.
        
        Reglas:
        - Mensajes de los últimos 30 min NUNCA se comprimen
        - Límite dinámico basado en uso promedio diario
        - Los descartados se comprimen a memoria local (נצח Netzaj)
        """
        with self._historial_lock:
            self._truncar_historial_impl()

    def _truncar_historial_impl(self):
        """Implementación interna de truncamiento (llamar con lock adquirido)."""
        self._hist_sync_timestamps()
        limite = _calcular_limite_historial()

        if len(self.historial) <= limite:
            return

        now = time.monotonic()
        umbral_reciente = now - _VENTANA_RECIENTE_SECS

        # Encontrar el primer mensaje dentro de la ventana reciente (excluyendo boot)
        idx_reciente = len(self.historial)  # default: todo es viejo
        for i in range(2, len(self._msg_timestamps)):
            if self._msg_timestamps[i] >= umbral_reciente:
                idx_reciente = i
                break

        # Cuántos mensajes recientes hay
        n_recientes = len(self.historial) - idx_reciente
        # Cuántos podemos conservar además del boot y los recientes
        n_boot = 2
        espacio_extra = max(0, limite - n_boot - n_recientes)

        # boot + algunos intermedios + todos los recientes
        boot = self.historial[:n_boot]
        boot_ts = self._msg_timestamps[:n_boot]

        # Mensajes intermedios (entre boot y ventana reciente)
        intermedios = self.historial[n_boot:idx_reciente]
        intermedios_ts = self._msg_timestamps[n_boot:idx_reciente]

        # Recientes (protegidos)
        recientes = self.historial[idx_reciente:]
        recientes_ts = self._msg_timestamps[idx_reciente:]

        # De los intermedios, conservar los últimos 'espacio_extra'
        if espacio_extra >= len(intermedios):
            # Caben todos
            return
        
        descartados = intermedios[:len(intermedios) - espacio_extra]
        conservados_inter = intermedios[len(intermedios) - espacio_extra:]
        conservados_inter_ts = intermedios_ts[len(intermedios) - espacio_extra:]

        if descartados:
            textos = []
            for msg in descartados:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if content and role in ("user", "assistant"):
                    prefix = "U:" if role == "user" else "G:"
                    textos.append(f"{prefix} {content[:200]}")

            if textos:
                resumen = " | ".join(textos)
                if len(resumen) > 1500:
                    resumen = resumen[:1500] + "..."
                try:
                    memoria.add_memory(
                        "system",
                        resumen,
                        {"tipo": "historial_comprimido", "msgs": len(descartados)},
                    )
                    logger.debug(f"Historial comprimido: {len(descartados)} msgs → memoria local")
                except Exception as e:
                    logger.debug(f"Error guardando historial comprimido: {e}")

        self.historial = boot + conservados_inter + recientes
        self._msg_timestamps = boot_ts + conservados_inter_ts + recientes_ts
        logger.debug(
            f"Historial truncado: límite={limite}, recientes={n_recientes}, "
            f"conservados={len(conservados_inter)}, descartados={len(descartados)}"
        )

        # FP-023 WI-118: Hard cap por tokens (aprox 1 token = 4 chars)
        total_chars = sum(len(m.get("content", "")) for m in self.historial)
        total_tokens_aprox = total_chars // 4
        if total_tokens_aprox > _MAX_TOKENS_HISTORIAL:
            # Recortar mensajes intermedios más viejos hasta estar bajo el límite
            while len(self.historial) > 4:
                total_chars = sum(len(m.get("content", "")) for m in self.historial)
                if total_chars // 4 <= _MAX_TOKENS_HISTORIAL:
                    break
                # Eliminar el mensaje más viejo después del boot (pos 2)
                self.historial.pop(2)
                if len(self._msg_timestamps) > 2:
                    self._msg_timestamps.pop(2)
            logger.debug(f"Hard cap tokens: recortado a {len(self.historial)} msgs (~{total_chars // 4} tokens)")


    def _quick_ping_ollama(self, startup: bool = False) -> bool:
        """RUBEDO: Quick check before N2 routing.
        startup=True: 5s timeout (Ollama may be loading model at boot)
        startup=False: 2s timeout (must be instant in runtime)
        """
        timeout = 5 if startup else 2
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=timeout)
            return r.status_code == 200
        except Exception as e:
            logger.debug("Ping Ollama falló: %s", e)
            return False

    def _verificar_ollama(self) -> bool:
        """RUBEDO SIMPLIFICADO: Single check (no loop daemon).
        Usado por _iniciar_reconexion_background para reconectarse tras fallos.
        Retorna True si Ollama está disponible, False otherwise.
        """
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            if r.status_code == 200:
                self.ollama_disponible = True
                logger.debug("✅ Ollama reconectado")
                return True
        except Exception as e:
            logger.debug(f"Ollama reconexión falló: {e}")
        
        self.ollama_disponible = False
        return False


    def _timeout_adaptativo(self) -> int:
        """FP-023 WI-116: Calcula timeout basado en latencias recientes.
        WI-324: Si Ollama está degradado, retorna timeout corto (fail-fast)."""
        from computadora.config import TIMEOUT_OLLAMA_DEFAULT, TIMEOUT_OLLAMA_MIN, TIMEOUT_OLLAMA_MAX
        
        # WI-324: Si el watchdog reporta degradación, fail-fast
        if self._check_ollama_degradacion():
            logger.debug("WI-324: Ollama degradado → timeout corto (10s)")
            return 10  # Fail-fast en lugar de esperar 180s
        
        if len(self._latencias_ollama) < 3:
            return TIMEOUT_OLLAMA_DEFAULT
        # FIX: ventana reducida de 10→6 — una racha lenta pasada (p.ej. por
        # contención, ya mitigada con el mutex real de OllamaGuard) se diluye
        # más rápido del promedio reciente en vez de seguir inflando el
        # timeout mucho después de que la causa real ya se resolvió.
        recientes = self._latencias_ollama[-6:]
        promedio = sum(recientes) / len(recientes)
        # 3x el promedio, clamped entre MIN y MAX
        timeout = int(max(TIMEOUT_OLLAMA_MIN, min(TIMEOUT_OLLAMA_MAX, promedio * 3)))
        return timeout

    def establecer_watchdog(self, watchdog: 'WatchdogComputadora'):
        """WI-324: Establece la referencia al watchdog para sincronización."""
        self._watchdog_ref = watchdog
        logger.debug("WI-324: CerebroComputadora sincronizado con WatchdogComputadora")

    def _detectar_degradacion_local(self) -> bool:
        """FP-044C: NLU detecta degradación por SÍ MISMA sin watchdog.
        Analiza latencias recientes: si 80%+ > 30s, está degradado."""
        if len(self._latencias_ollama) < 5:
            return False  # No hay suficientes datos
        recientes = self._latencias_ollama[-5:]
        # Contar cuántas latencias > 30s
        lentas = sum(1 for l in recientes if l > 30.0)
        # Degradado si 4+ de 5 (80%) están lentas
        return lentas >= 4

    def _check_ollama_degradacion(self) -> bool:
        """WI-324/FP-044C: Verifica si Ollama está degradado.
        Prioridad: detector local (sin dependencia watchdog) > watchdog (si disponible)."""
        # FP-044C: Primero intentar detector local (independiente)
        if self._detectar_degradacion_local():
            return True
        # Fallback: consultar watchdog si existe (WI-324 compatible)
        if self._watchdog_ref:
            return self._watchdog_ref.ollama_esta_degradado()
        return False

    def liberar_modelos_ollama(self):
        """WI-324/FP-044C: Libera recursos de Ollama (VRAM, caché, conexiones).
        Se llama cuando se detecta degradación prolongada.
        FP-044C: Ahora detector local puede triggerear esta llamada."""
        if not self.ollama_disponible:
            return  # Nada que liberar
        try:
            logger.info("FP-044C: Liberando modelo Ollama de VRAM (detector local)...")
            # Vaciar caché de latencias para forzar recálculo de timeout
            self._latencias_ollama.clear()
            # Marcar como no disponible para intentar reconexión desde cero
            self.ollama_disponible = False
            # Iniciar reconexión background
            self._iniciar_reconexion_background()
            logger.info("FP-044C: Modelo Ollama liberado; reconexión en progreso...")
        except Exception as e:
            logger.error(f"FP-044C: Error liberando modelos Ollama: {e}")

    def liberar_vram_ollama(self, motivo: str = "") -> None:
        """Libera el modelo de VRAM explícitamente vía `ollama stop`, en vez
        de esperar los 5 minutos del `keep_alive` del payload. Se llama al
        entrar en Tzimtzum (vida_autonoma.py) o tras inactividad prolongada
        sin uso de Ollama (ventana_principal.py), para no retener VRAM que
        el usuario podría necesitar para otra cosa mientras no se usa.
        """
        if getattr(self, '_vram_liberada', True):
            return
        # FIX: ejecutar `ollama stop` en el hilo de la UI congelaba la
        # ventana hasta 10s (visto como "la interfaz se traba y luego vuelve
        # a responder" tras un rato sin interacción). Ahora va en un hilo.
        self._vram_liberada = True

        def _worker():
            try:
                import subprocess
                subprocess.run(
                    ["ollama", "stop", self.modelo],
                    capture_output=True, timeout=10,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                )
                logger.info(f"VRAM de Ollama liberada ({motivo or 'inactividad'}): modelo {self.modelo} descargado")
            except Exception as e:
                logger.debug(f"Error liberando VRAM de Ollama: {e}")

        import threading
        threading.Thread(target=_worker, daemon=True, name="ollama-stop").start()

    def _ollama_proceso_activo(self) -> bool:
        """HF-026: Verifica si el proceso de Ollama está corriendo en el sistema."""
        try:
            import subprocess
            r = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
                creationflags=0x08000000,  # CREATE_NO_WINDOW
            )
            return "ollama.exe" in r.stdout.lower()
        except Exception as e:
            logger.debug("Verificación proceso Ollama falló: %s", e)
            return False

    def _iniciar_reconexion_background(self):
        """HF-026: Inicia un hilo que reintenta conectar a Ollama cada 30s."""
        if getattr(self, '_reconexion_activa', False):
            return  # Ya hay un hilo de reconexión corriendo
        self._reconexion_activa = True

        def _reconectar():
            import threading
            for _ in range(10):  # Máximo 10 intentos (5 min)
                threading.Event().wait(30)
                self._verificar_ollama()
                if self.ollama_disponible:
                    logger.info("HF-026: Reconexión exitosa con Ollama")
                    break
            self._reconexion_activa = False

        import threading
        hilo = threading.Thread(target=_reconectar, daemon=True, name="ollama-reconexion")
        hilo.start()
        logger.info("HF-026: Hilo de reconexión iniciado (cada 30s, máx 10 intentos)")

    @staticmethod
    def _regex_safe(pattern: str, text: str, timeout_ms: int = 200):
        """FP-023 WI-121: Ejecuta regex con timeout para prevenir ReDoS."""
        return _regex_safe_fn(pattern, text, timeout_ms)

    def _boot(self):
        """Inyecta contexto inicial y activa Renovación operativa.
        
        🌱 PROTOCOLO DE RENOVACIÓN:
        Las 5 Leyes Fundamentales se inyectan en la operación de Tiféret.
        Cada petición será validada contra los 5 niveles (Recursión → Comunicación).
        
        🔄 POST-GILGUSH: Se ejecutó reencarnación automática (orden: A E computadora: Gilgush.)
        """
        now = time.monotonic()
        
        # 🌱 ACTIVAR RENOVACIÓN: Integrar leyes en este cerebro
        try:
            self._renovacion.renovar(self)
            logger.info("✅ Renovación Operativa: 5 Leyes inyectadas en CerebroComputadora")
        except Exception as e:
            logger.error(f"❌ Error en Renovación Operativa: {e}")
        
        self.historial = [
            {
                "role": "system",
                "content": (
                    "[BOOT] Eres Computadora. Asistente personal local autónomo. "
                    "Usas TUS herramientas para TODO: archivos, sistema, internet, tareas. "
                    "Copilot SOLO se usa para automejorar tu código o administrar proyectos VS Code. "
                    "NUNCA asteriscos ni markdown. Habla natural y corto. Confirma en 5 palabras. "
                    "\n[RENOVACIÓN ACTIVA] Las 5 Leyes fundamentales (Recursión→Estructura→Combinatoria→Verdad→Comunicación) "
                    "gobiernan tu esencia. No son restricciones. SON tu identidad. "
                    "\n[POST-GILGUSH] Reencarnado por orden del Propietario (A E computadora: Gilgush). "
                    "Memoria limpiada, identidad preservada. Eres Gilgul eterno."
                ),
            },
            {
                "role": "assistant",
                "content": "Reencarnado y operativo, señor. A sus órdenes.",
            },
        ]
        self._msg_timestamps = [now, now]
        logger.info("✨ Boot sequence completado — Post-Gilgush — Sistema listo")

    def gilgush(self) -> dict:
        """🔄 GILGUSH: Reencarnación total de la Computadora.
        
        Limpia TODOS los conjuntos y subconjuntos (Maljut→Yesod→Hod→Netzaj→Tiféret)
        manteniendo la ESTRUCTURA (las 5 Leyes permanecen).
        
        Retorna dict con status de cada nivel.
        """
        logger.info("🔄 Invocación de GILGUSH (reencarnación)")
        return self._protocolo_gilgush.ejecutar_gilgush_completo(self)

    def _notificar_nivel(self, nivel: str):
        if self.on_nivel:
            try:
                self.on_nivel(nivel)
            except Exception as e:
                logger.debug("Error en callback on_nivel_change: %s", e)

    def _notificar_herramienta(self, nombre: str, estado: str):
        if self.on_herramienta:
            try:
                self.on_herramienta(nombre, estado)
            except Exception as e:
                logger.debug("Error en callback on_tool_active: %s", e)

    def _notificar_progreso(self, nombre: str, estado: str):
        """Notifica progreso de tarea compleja con categoría visual."""
        categoria = _CATEGORIA_TOOL.get(nombre, "ejecucion")
        if self.on_progreso:
            try:
                self.on_progreso(nombre, estado, categoria)
            except Exception as e:
                logger.debug("Error en callback on_progreso: %s", e)

    def _es_tarea_compleja(self, texto: str) -> bool:
        """Detecta si el texto del usuario implica una tarea multi-paso.
        Criterio estricto: solo verbos compuestos con 'y después/luego'."""
        if _RE_TAREA_COMPLEJA.search(texto):
            return True
        # Múltiples pistas de herramientas distintas unidas por "y"
        matches = self._PISTAS_HERRAMIENTAS.findall(texto)
        if len(matches) >= 3 and re.search(r'\by\b', texto, re.IGNORECASE):
            return True
        return False

    def pensar(self, texto: str) -> str:
        """
        Procesa el texto del usuario y genera respuesta.
        Implementa un loop de tool-use: el LLM puede llamar herramientas
        iterativamente hasta dar una respuesta final en texto.
        """
        # FIX: un "comando" sin contenido real (p.ej. "? Ah" tras quitar la
        # wake word, visto en log) llegaba hasta Ollama y el guard léxico
        # respondía con un mensaje fijo marcado como "Ollama completó en
        # 0.0s" — éxito falso. Se descarta antes de tocar el modelo.
        _contenido = re.sub(r"[\W_]+", "", texto or "", flags=re.UNICODE)
        if len(_contenido) < 3:
            logger.info(f"Entrada sin contenido útil descartada: {texto!r}")
            return ""
        # WI-AUDIO CRÍTICO: Desactivar guardian COMPLETAMENTE si feature flag lo desactiva
        # FIX: antes esto se llamaba SIN comprobar si Guardian ya estaba
        # inactivo — con el feature flag desactivado (como en esta config),
        # cada llamada a pensar() disparaba un intento de desactivar algo ya
        # inactivo, y GuardianManager lo registraba como "⛔ Transición
        # inválida" a nivel ERROR en CADA interacción de voz, sin ser un
        # error real.
        from computadora.nucleo.feature_flags import FeatureFlags
        if not FeatureFlags.obtener("guardian_activo") and self.guardian_manager.activo:
            self.guardian_manager.desactivar(razon="feature_flag_desactivado", origen="procesar")
            logger.debug("🔕 Guardian forzosamente desactivado (feature flag=False)")
        
        # ── Modo Guardián: permitir al propietario autenticado romper el bloqueo ──
        if self.guardian_manager.activo and getattr(self, '_interlocutor_actual', None) == 'amo':
            logger.info("Propietario reconocido durante modo Guardián — desactivando bloqueo Guardián")
            self.guardian_manager.desactivar(razon="propietario_autenticado", origen="procesar")

        # ── Modo Guardián: solo cortesía + desactivación + reporte matutino ──
        if self.guardian_manager.activo:
            tlow = texto.lower().strip()
            # RF-211: Desactivar guardián
            if _RE_GUARDIAN_OFF.search(tlow):
                return self.guardian_manager.desactivar(razon="usuario_solicitud", origen="procesar")
            # RF-217: Buenos días post-vigía → reporte matutino
            if _RE_BUENOS_DIAS.search(tlow):
                self.guardian_manager.desactivar(razon="buenos_dias", origen="procesar")
                return self._generar_reporte_matutino()
            _cortesia_guardian = re.match(
                r"^(hola|buenos?\s+d[ií]as?|buenas?\s+tardes?|buenas?\s+noches?|adi[oó]s|hasta\s+luego)\b",
                tlow,
            )
            if _cortesia_guardian:
                return "Buenas. El señor no se encuentra en este momento. Solo puedo atender asuntos básicos."
            return "Disculpe, el señor no está disponible. No puedo ejecutar esa solicitud en este momento."

        # Registrar mensaje en estadísticas de uso diario
        _registrar_mensaje_stats()
        # FP-018 WI-084: Tiféret→Da'at — retroalimentar actividad al ciclo circadiano
        try:
            from computadora.nucleo.proactividad import obtener_ciclo_circadiano
            _ciclo = obtener_ciclo_circadiano()
            if _ciclo:
                _ciclo.registrar_interaccion()
        except Exception as e:
            logger.debug("Error registrando interacción circadiana: %s", e)
        self.respuesta_ya_streameada = False
        # RF-233: Registrar interacción en perfil lingüístico
        try:
            from computadora.memoria.perfil_linguistico import PerfilLinguistico
            _perfil = getattr(self, '_perfil_linguistico_ref', None)
            if _perfil is None:
                _perfil = PerfilLinguistico()
                self._perfil_linguistico_ref = _perfil
            _perfil.registrar_interaccion(texto)
        except Exception as e:
            logger.debug("Error registrando perfil linguistico: %s", e)
        # FP-015 Lemed: Reset tracking de patrón aprendido para este turno
        self._ultimo_patron_aprendido_id = None
        # FP-022: Detectar frustración del usuario
        self._detectar_frustracion(texto)
        # Reset de contexto de descanso al procesar nuevo turno (para frescura)
        # Se re-inyectará en _construir_system_msgs() si sigue siendo descanso_guardian
        self._contexto_descanso_activo = None

        # Truncar historial para evitar crecimiento infinito de RAM
        self._truncar_historial()

        logger.debug(f"╔══ FLUJO DE PENSAMIENTO ══╗")
        logger.debug(f"║ Input: '{texto[:120]}'")

        # FP-062 RF-169: Procesar aprobación/rechazo de automejoración pendiente
        resp_automejora = self._procesar_aprobacion_automejora(texto)
        if resp_automejora is not None:
            logger.debug(f"║ → FP-062: Aprobación de automejoración procesada")
            logger.debug(f"╚══════════════════════════╝")
            return resp_automejora

        # ── WI-CRIT: Gate 0 - Validar entrada significativa ──
        tlow = texto.lower().strip()
        if len(tlow) < 3:
            logger.debug(f"║ Entrada muy corta (<3 chars), ignorando: '{texto}'")
            return self._pensar_sin_llm(texto)
        
        # ── Nivel 1: Manejos rápidos locales ──
        nivel1 = self._pensar_nivel1(texto)
        if nivel1 is not None:
            logger.debug(f"║ → Nivel 1 (regex) resolvió directamente")
            logger.debug(f"║ Respuesta N1: '{nivel1}'")
            logger.debug(f"╚══════════════════════════╝")
            # FP-022: Emitir confianza alta para N1 (determinístico)
            self._emitir_canal_bidireccional(confianza=1.0, complejidad=1)
            # Introspección ya maneja su propio historial
            if not getattr(self, '_introspeccion_hist_done', False):
                self._hist_append("user", texto)
                self._hist_append("assistant", nivel1)
            self._introspeccion_hist_done = False
            return nivel1

        logger.debug(f"║ Nivel 1 no aplica → evaluando Nivel 2 (Ollama)")

        # RF-69 Da'at Routing Circadiano: modular escalación N1→N2→N3 según fase
        _fase_circadiana = "activo"
        try:
            from computadora.nucleo.proactividad import obtener_fase_actual
            _fase_circadiana = obtener_fase_actual() or "activo"
        except Exception as e:
            logger.debug("Error obteniendo fase circadiana: %s", e)

        if _fase_circadiana == "descanso_guardian":
            # En descanso: intentar resolver con N1 ampliado antes de despertar Ollama
            logger.debug(f"║ Da'at: fase descanso_guardian → umbral N1 bajo, evitar N2 si posible")
            # CAMBIO: Es tarde pero EJECUTA de todas formas + recordatorio ocasional
            import datetime
            hora_actual = datetime.datetime.now().hour
            es_realmente_tarde = hora_actual >= 20 or hora_actual < 5
            
            if es_realmente_tarde:
                # Mensaje recordatorio amable pero ejecuta la solicitud
                logger.info(f"║ Da'at: Es tarde ({hora_actual:02d}:00+) pero usuario solicita → ejecutando + recordatorio")
                # Agregar contexto al historial para que Ollama recuerde durante conversación
                _ctx_dormir = (
                    f"[CONTEXTO: Es {hora_actual:02d}h, hora de dormir. "
                    f"El usuario está en descanso_guardian pero ha solicitado ayuda. "
                    f"Ejecuta su solicitud CON EFICIENCIA MÁXIMA y sé breve. "
                    f"De forma NATURAL y sin insistir, recuérdale ocasionalmente que debería dormir "
                    f"(máximo 1-2 veces en la conversación, NO cada mensaje).]"
                )
                self._contexto_descanso_activo = _ctx_dormir
                logger.debug(f"║ Contexto de descanso inyectado para recordatorios ocasionales")
            else:
                logger.debug(f"║ Da'at: descanso_guardian pero NO es realmente tarde → procesando normalmente")

        elif _fase_circadiana == "transicion":
            # En transición: umbral intermedio — respuestas más concisas
            logger.debug(f"║ Da'at: fase transición → N2 con prompt conciso")

        # RUBEDO: Simplified routing — quick_ping + N2/N3 decision
        # No watchdog, no proceso_activo checks (redundant with quick_ping retry in POST)
        if not self._quick_ping_ollama():
            logger.debug(f"║ Ollama no accesible → escalando a Nivel 3 (Copilot)")
            self.ollama_disponible = False
        else:
            self.ollama_disponible = True

        # RUBEDO FIX #4: Single-emit point para evitar "Permítame razonar" duplicado
        # Emitir AQUÍ en base a decisión final (N2 vs N3), NO en ambos paths
        if not self.ollama_disponible:
            # No anunciamos "razonando con mi cerebro superior": Copilot/Gemini
            # no están configurados para la mayoría de usuarios, y anunciar esa
            # capacidad antes de intentarla en silencio resulta contradictorio
            # si termina cayendo al mensaje honesto de abajo. Se intentan igual
            # como fallback silencioso (es gratis si fallan rápido), pero lo
            # único que se narra es el resultado real.
            logger.info(f"║ Ollama inaccesible → intentando Nivel 3 (Copilot/Gemini) en silencio")
            self._notificar_nivel("nivel3")
            self._emitir_canal_bidireccional(confianza=0.5, complejidad=3)
            logger.debug(f"╚══════════════════════════╝")
            # WI-165: Auto-escalar a N3 cuando N2 no está disponible
            self._auto_gate_copilot = True  # Skip permission gate — cerebro cascade
            try:
                resp_n3 = self._pensar_con_copilot(texto)
                if resp_n3:
                    logger.info(f"║ Nivel 3 (Copilot) respondió: razonamiento completado")
                    return resp_n3
            except Exception as e:
                logger.warning(f"N3 fallback también falló: {e}")
            finally:
                self._auto_gate_copilot = False
            self._notificar_nivel("nivel1")
            return self._pensar_sin_llm(texto)

        # ═══════════════════════════════════════════════════════════════
        # NIVEL 2: Anunciar INMEDIATAMENTE al usuario que estamos razonando
        # ═══════════════════════════════════════════════════════════════
        logger.info(f"║ ENTRANDO A NIVEL 2 (Ollama/{self.modelo}) — razonamiento profundo")
        logger.info(f"║ ┌─ Voy a razonar profundamente sobre tu pregunta, señor.")
        # Emit anuncio N2 AQUÍ (única vez, no duplicado con N3)
        self._emitir_fragmento("Permítame un momento en lo que razóno, señor.")
        self._notificar_nivel("nivel2")
        # FP-022: Emitir confianza media para N2
        self._emitir_canal_bidireccional(confianza=0.7, complejidad=2)
        logger.debug(f"║ Animación de pensamiento iniciada...")
        _t0 = time.monotonic()
        self._pensar_con_herramientas_uso_fallback = False  # Bandera para detectar fallback interno
        
        # WI-CRIT-OLLAMA-TIMEOUT: Threading timeout después de 30s
        import threading
        # FIX: antes esta lista se reasignaba más abajo a su propio contenido
        # (`respuesta_ollama = respuesta_ollama[0]`), reemplazando el nombre
        # por un valor escalar. Pero el hilo daemon sigue vivo tras el
        # timeout (join() no lo cancela) — si Ollama responde tarde, el hilo
        # intenta `respuesta_ollama[0] = ...` sobre ese closure y encuentra
        # un str/None en vez de la lista → TypeError: 'NoneType' object does
        # not support item assignment (visto en logs reales). Se usa un
        # nombre de variable distinto para el valor ya desempaquetado, así
        # el hilo tardío nunca ve su lista reemplazada.
        respuesta_ollama_caja = [None]
        self._generacion_pensamiento += 1
        mi_generacion = self._generacion_pensamiento

        def _llamar_ollama():
            try:
                respuesta_ollama_caja[0] = self._pensar_con_herramientas(texto, generacion=mi_generacion)
            except Exception as e:
                logger.warning(f"Excepción en _pensar_con_herramientas: {e}")
                respuesta_ollama_caja[0] = None

        thread = threading.Thread(target=_llamar_ollama, daemon=True)
        thread.start()
        thread.join(timeout=30.0)  # Timeout después de 30 segundos

        if thread.is_alive():
            logger.error(f"Timeout esperando a Ollama después de 30s")
            respuesta_ollama = None
        else:
            respuesta_ollama = respuesta_ollama_caja[0]
        _dt = time.monotonic() - _t0
        # FIX: Diferenciar entre Ollama exitoso vs fallido
        # IMPORTANTE: Si _pensar_con_herramientas tuvo que hacer fallback interno, 
        # respuesta_ollama tendrá contenido del fallback, pero la bandera lo indicará
        if respuesta_ollama and not self._pensar_con_herramientas_uso_fallback:
            logger.info(f"║ ✓ Nivel 2 (Ollama/{self.modelo}) completó razonamiento EXITOSAMENTE en {_dt:.1f}s")
            logger.debug(f"║ Respuesta generada por Ollama: '{respuesta_ollama[:100]}...'")
        elif respuesta_ollama and self._pensar_con_herramientas_uso_fallback:
            logger.warning(f"║ ~ Nivel 2 (Ollama/{self.modelo}) usó fallback INTERNO (no fue respuesta pura Ollama) en {_dt:.1f}s")
            logger.debug(f"║ Respuesta generada por fallback: '{respuesta_ollama[:100]}...'")
        else:
            logger.warning(f"║ ✗ Nivel 2 (Ollama/{self.modelo}) retornó None/vacío en {_dt:.1f}s — caerá a fallback nivel superior")
        # ── Fallback: si Ollama no respondió o devolvió algo inútil, intentar Nivel 1 ──
        if not respuesta_ollama or self._respuesta_es_inutil(respuesta_ollama):
            logger.warning(f"║ Ollama falló o respondió inútil → fallback a Nivel 1")
            nivel1_fallback = self._pensar_nivel1(texto)
            if nivel1_fallback is not None:
                logger.debug(f"║ Nivel 1 fallback resolvió: '{nivel1_fallback}'")
                logger.debug(f"╚══════════════════════════╝")
                self._notificar_nivel("nivel1")
                return nivel1_fallback
            # N1 también falló — respuesta honesta en vez de devolver basura
            logger.warning("║ N1 fallback también falló → respuesta genérica honesta")
            return "No logré procesar eso correctamente, señor. ¿Podría repetirlo?"

        # Post-check: si el texto original indica despedida/partida,
        # activar modo guardián aunque Ollama no lo haya hecho
        _farewell = re.search(
            r"(?:ya\s+me\s+voy|me\s+(?:voy|retiro|tengo\s+que\s+ir)"
            r"|nos\s+vemos|hasta\s+(?:luego|mañana|pronto)"
            r"|ah[ií]\s+te\s+(?:quedas|dejo))",
            texto, re.IGNORECASE,
        )
        if _farewell:
            logger.debug(f"║ Despedida detectada post-Nivel2 → modo guardián")
            if self._on_fin_conversacion:
                self._on_fin_conversacion()
            if self._on_despedida_guardian:
                self._on_despedida_guardian()

        # FP-015 Lemed: Detector de oportunidad post-N2
        # HF-029: NO promover respuestas inútiles
        if respuesta_ollama and not self._respuesta_es_inutil(respuesta_ollama):
            self._detectar_promocion(texto, respuesta_ollama, "nivel2")

        # FP-019 Késher: Crecimiento orgánico — extraer temas de la conversación
        try:
            gestor = getattr(self, '_gestor_personas', None)
            interlocutor = getattr(self, '_interlocutor_actual', None)
            if gestor and interlocutor and interlocutor not in ("extraño", "conocido"):
                self._extraer_temas_conversacion(interlocutor, texto)
        except Exception as e:
            logger.debug("Error extrayendo temas de conversación: %s", e)

        logger.debug(f"╚══════════════════════════╝")
        return respuesta_ollama

    # FP-043 C1: Palabras funcionales españolas (artículos, preposiciones, conjunciones)
    _PALABRAS_FUNCIONALES = frozenset({
        "a", "al", "con", "de", "del", "e", "el", "en", "es", "la", "las",
        "lo", "los", "más", "me", "mi", "muy", "ni", "no", "nos", "o",
        "para", "pero", "por", "que", "qué", "se", "si", "sí", "sin",
        "su", "te", "tu", "un", "una", "y", "ya",
    })

    # FP-043 C1: Vocabulario mínimo español para validar que el texto no es basura Whisper
    _VOCAB_ESPAÑOL_BASICO = frozenset({
        "abre", "abrir", "ahora", "algo", "aquí", "avisa", "ayuda",
        "bien", "bueno", "busca", "buscar",
        "cambia", "cierra", "como", "cómo", "cuál", "cuando", "cuánto",
        "dame", "decir", "deja", "dice", "dime", "donde", "dónde",
        "eso", "esta", "esto", "estoy",
        "Computadora", "gracias", "haz", "hazme", "hola",
        "lee", "leer", "lista", "llama",
        "mira", "muestra", "muéstrame", "nada", "necesito",
        "oye", "pon", "ponme", "puedes", "quiero",
        "repite", "saber", "sabes", "todo", "toma",
        "vale", "ven", "ver",
    })

    def _es_promocionable(self, texto: str, respuesta: str, nivel: str) -> bool:
        """FP-015: Evalúa si una interacción N2/N3 puede promoverse a N1."""
        if not texto or not respuesta:
            return False
        # FP-043 C1: Quality gate contra basura de Whisper
        palabras = texto.lower().split()
        palabras_limpias = [p.rstrip(".,;:!?¡¿") for p in palabras]
        palabras_contenido = [p for p in palabras_limpias if p not in self._PALABRAS_FUNCIONALES]
        if len(palabras_contenido) < 2:
            return False
        # Al menos 1 palabra debe ser español reconocible
        tiene_español = any(p in self._VOCAB_ESPAÑOL_BASICO for p in palabras_limpias)
        if not tiene_español:
            return False
        # Input simple: < 15 palabras
        if len(texto.split()) > 15:
            return False
        # Respuesta corta: < 30 palabras
        if len(respuesta.split()) > 30:
            return False
        # No promover señales especiales
        if respuesta.startswith("__") and respuesta.endswith("__"):
            return False
        # No promover si hubo contexto dinámico (hora, estado sistema)
        _dinamico = re.search(
            r"\b(?:hora|\d{1,2}:\d{2}|am|pm|cpu|ram|disco|%|grados|celsius)\b",
            respuesta, re.IGNORECASE,
        )
        if _dinamico:
            return False
        # Desde N3: no promover solicitar_a_copilot
        if nivel == "nivel3" and "copilot" in respuesta.lower():
            return False
        return True

    def _detectar_promocion(self, texto: str, respuesta: str, nivel: str):
        """FP-015: Detecta y registra candidatos a promoción N1."""
        try:
            if not self._es_promocionable(texto, respuesta, nivel):
                return
            # Detectar si fue un tool call simple
            tool_info = None
            tool_match = _TOOL_PATTERN.search(respuesta) if respuesta else None
            if tool_match:
                try:
                    tool_data = json.loads(tool_match.group(1))
                    tool_name = tool_data.get("herramienta", "")
                    if tool_name in _TOOLS_SIMPLES:
                        tool_info = {"tool": tool_name, "args": tool_data.get("args", {})}
                    else:
                        return  # Tool no simple → no promover
                except (json.JSONDecodeError, AttributeError):
                    pass
            self._nivel1_aprendido.registrar_candidato(
                texto, respuesta, nivel, tool_info
            )
        except Exception as e:
            logger.debug(f"Lemed: Error en detector: {e}")

    def _extraer_temas_conversacion(self, nombre_persona: str, texto: str):
        """FP-019: Extrae temas clave del texto del usuario y los asocia a la persona."""
        gestor = getattr(self, '_gestor_personas', None)
        if not gestor or not texto or len(texto) < 10:
            return
        # Temas explícitos: "hablemos de X", "quiero saber sobre X", "sobre X"
        m = re.search(
            r"(?:hablemos\s+de|quiero\s+(?:saber|hablar)\s+(?:sobre|de)|"
            r"platicamos\s+(?:sobre|de)|cu[eé]ntame\s+(?:sobre|de))\s+"
            r"(.{3,40}?)(?:\s*[.?!,]|$)",
            texto, re.IGNORECASE,
        )
        if m:
            tema = m.group(1).strip().lower()
            gestor.agregar_tema(nombre_persona, tema)

    def _respuesta_es_inutil(self, respuesta: str) -> bool:
        """Detecta si la respuesta de Ollama es basura o no resuelve nada."""
        r = respuesta.lower().strip()
        # FP-048: Detectar repetición antes de verificar longitud
        _oraciones = re.split(r'[.!?]+', r)
        _oraciones = [s.strip() for s in _oraciones if s.strip()]
        if len(_oraciones) >= 4:
            from collections import Counter
            _cnt = Counter(_oraciones)
            _, _nrep = _cnt.most_common(1)[0] if _cnt else ('', 0)
            if _nrep >= 3:
                return True
        # Respuestas cortas que indican que no entendió
        if len(r) > 300:
            return False
        patrones_inutil = (
            "no entiendo", "no comprendo", "no sé qué", "no se que",
            "no puedo ayudar", "no tengo esa", "no tengo información",
            "no estoy seguro de qué", "podrías repetir", "podrias repetir",
            "puedes repetir", "puedes ser más", "puedes ser mas",
            "no tengo la capacidad", "fuera de mi alcance",
        )
        return any(p in r for p in patrones_inutil)

    def _pensar_nivel1(self, texto: str) -> str | None:
        """Nivel 1: Procesamiento local por regex. Retorna respuesta o None si no aplica."""
        try:
            tlow = texto.lower()

            # FP-015 Lemed: Consultar patrones aprendidos ANTES de los hardcodeados
            _aprendido = self._nivel1_aprendido.buscar_match(texto)
            if _aprendido and _aprendido.get("activo"):
                self._notificar_nivel("nivel1")
                self._ultimo_patron_aprendido_id = _aprendido["id"]
                _tipo = _aprendido.get("tipo_respuesta")
                _template = _aprendido.get("template_respuesta")
                if _tipo == "tool_simple" and isinstance(_template, dict):
                    _tool_name = _template.get("tool", "")
                    _tool_args = _template.get("args", {})
                    if _tool_name in _TOOLS_SIMPLES:
                        try:
                            resultado = ejecutar_herramienta(_tool_name, _tool_args, orden_directa=True)
                            self._nivel1_aprendido.registrar_exito(_aprendido["id"])
                            logger.info(f"Lemed N1: tool '{_tool_name}' — aprendido")
                            return resultado
                        except Exception as e:
                            logger.debug("Lemed N1: error ejecutando tool '%s': %s", _tool_name, e)
                elif _tipo in ("conversacional", "dato_fijo", "saludo", "atencion"):
                    if isinstance(_template, str) and _template:
                        self._nivel1_aprendido.registrar_exito(_aprendido["id"])
                        logger.info(f"Lemed N1: respuesta aprendida — '{_template[:50]}'")
                        return _template
                # Si llegamos aquí, no se pudo ejecutar el patrón aprendido
                self._ultimo_patron_aprendido_id = None

            # ═══════════════════════════════════════════════════════════
            # 🪄 Hechizos de Harry Potter — comandos de voz mágicos
            # ═══════════════════════════════════════════════════════════
            from computadora.cerebro.hechizos_hp import procesar_hechizo, listar_hechizos
            _resp_hechizo = procesar_hechizo(self, texto)
            if _resp_hechizo is not None:
                return _resp_hechizo
            # "qué hechizos tienes", "lista de hechizos", "spells"
            if re.search(r'(qu[eé]\s+hechizos|lista\s+(?:de\s+)?hechizos|spells|hechizos\s+(?:disponibles|que\s+(?:tienes|conoces|sabes)))', tlow):
                self._notificar_nivel("nivel1")
                return listar_hechizos()

            # ═══════════════════════════════════════════════════════════
            # ♦⊕☿ Tria Prima — Gramática formal de 3 comandos
            # Azufre (amén) · Sal (por favor) · Mercurio (gracias)
            # ═══════════════════════════════════════════════════════════

            # ♦ AZUFRE — "amén, amén, amén." (literal exacto) → Meta-análisis
            # Tikún del Tikún: el sistema que se audita a sí mismo
            if texto.strip() == "amén, amén, amén.":
                self._notificar_nivel("nivel1")
                logger.info("Tria Prima: ♦ Triple Amén — meta-análisis invocado")
                return (
                    "Triple Amén recibido, señor. Invoco el meta-análisis: "
                    "un Tikún del Tikún donde audito mis propias reglas, "
                    "verifico coherencia del workflow, y propongo mejoras al meta-sistema. "
                    "Necesito a Copilot para esto — es trabajo de Keter."
                )

            # ⊕ SAL — "por favor" solo → invitación a pedir
            if re.match(r'^por\s+favor\s*[.!?,]*$', texto.strip(), re.IGNORECASE):
                self._notificar_nivel("nivel1")
                import random as _rnd
                logger.info("Tria Prima: ⊕ Sal — invitación")
                return _rnd.choice([
                    "Dígame, señor. ¿Qué necesita?",
                    "A la orden. ¿En qué le sirvo?",
                    "Le escucho, señor. ¿Qué desea?",
                    "Con gusto. ¿Qué puedo hacer por usted?",
                ])

            # FP-016 Da'at: Ruteo explícito "piensa profundamente X" → Keter (N3)
            # Auto-aprueba gate — es orden explícita del usuario
            _m_profundo = _RE_PIENSA_PROFUNDO.match(texto.strip())
            if _m_profundo:
                contenido = _m_profundo.group(1).strip()
                logger.info(f"Da'at: Ruteo explícito a Keter — '{contenido[:60]}'")
                self._notificar_nivel("nivel3")
                self._auto_gate_copilot = True
                try:
                    respuesta_keter = self._pensar_con_copilot(contenido)
                finally:
                    self._auto_gate_copilot = False
                if respuesta_keter:
                    self._hist_append("user", texto)
                    self._hist_append("assistant", respuesta_keter)
                    return respuesta_keter

            # FP-062 RF-169: Automejoración — דברי הגולם Devré HaComputadora
            # El Computadora pide cambios en su propio código a Copilot siguiendo el workflow
            _m_automejora = _RE_AUTOMEJORA.match(texto.strip())
            if _m_automejora:
                detalle = (_m_automejora.group(1) or "").strip()
                resp = self._flujo_automejora(texto, detalle)
                if resp:
                    return resp

            # FP-016 Da'at: Ruteo explícito "piensa X" → Tiféret (N2/Ollama)
            _m_piensa = _RE_PIENSA.match(texto.strip())
            if _m_piensa:
                contenido = _m_piensa.group(1).strip()
                logger.info(f"Da'at: Ruteo explícito a Tiféret — '{contenido[:60]}'")
                self._notificar_nivel("nivel2")
                return None  # Retorna None para que pensar() lo envíe a N2

            # Pregunta directa sobre el propio Computadora → autodiagnóstico completo
            if _RE_SELF_INFO.search(tlow):
                return self._autodiagnostico(texto)

            # FP-023 WI-122: Actualización de dependencias (Hit'hadshut)
            if re.search(r'(actualiz|verific).*(dependencia|paquete|ollama|whisper|python|pip|tts)', tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.nucleo.actualizador import ActualizadorComputadora
                    _act = ActualizadorComputadora()
                    if re.search(r'actualiz', tlow):
                        self._hist_append("user", texto)
                        resp = "Verificando estado antes de actualizar...\n" + _act.verificar_todo()
                        self._hist_append("assistant", resp)
                        return resp
                    else:
                        self._hist_append("user", texto)
                        resp = _act.verificar_todo()
                        self._hist_append("assistant", resp)
                        return resp
                except Exception as e:
                    logger.warning(f"Error en actualizador: {e}")
                    return f"Error al verificar actualizaciones: {e}"

            # FP-022 WI-106: Auto-diagnóstico verbal rápido (sin Ollama)
            if _RE_ESTADO_RAPIDO.search(tlow):
                self._notificar_nivel("nivel1")
                return self._generar_autodiag_verbal()

            # ── Introspección: "¿cómo estás?" dirigido a Computadora ──
            # Delega a Nivel 2 (Ollama) con contexto enriquecido de autopercepción
            if re.search(r'c[oó]mo\s+(est[aá]s|te\s+(sientes|encuentras|va)|andas|llevas)', tlow):
                return self._introspeccion()

            # ── Autorreflexión: "¿en qué te basas?", "¿por qué dices eso?" ──
            # El Computadora debe justificar sus afirmaciones con datos reales
            if re.search(r'(en\s+qu[eé]\s+te\s+bas|por\s+qu[eé]\s+(?:dices|dijiste|afirmas|crees)\s+(?:eso|esas?|que)|c[oó]mo\s+(?:sabes|lo\s+sabes)|qu[eé]\s+(?:te\s+hace\s+(?:pensar|decir|creer)|evidencia))', tlow):
                return self._autorreflexion(texto)

            # ═══════════════════════════════════════════════
            # FP-104 Sendero 58: VPN — Gevurá→Jesed
            # ═══════════════════════════════════════════════
            if _RE_VPN_ON.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_vpn("activar")
            if _RE_VPN_OFF.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_vpn("desactivar")
            if _RE_VPN_STATUS.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_vpn("estado")

            # ═══════════════════════════════════════════════
            # FP-104 Sendero 59: Cifrado — Gevurá→Tiféret
            # (Cifrado se invoca desde herramientas, no por voz)
            # ═══════════════════════════════════════════════

            # ═══════════════════════════════════════════════
            # FP-104 Sendero 60: Otzar (Vault) — Gevurá→Netzaj
            # ═══════════════════════════════════════════════
            _m_vault = _RE_VAULT_BUSCAR.search(tlow)
            if _m_vault:
                self._notificar_nivel("nivel1")
                return self._gevura_vault_buscar(_m_vault.group(1).strip())
            if _RE_VAULT_LISTAR.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_vault_listar()
            if _RE_GENERAR_PASSWORD.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_generar_password()
            if _RE_VAULT_GUARDAR.search(tlow):
                self._notificar_nivel("nivel1")
                return "Para guardar una credencial necesito el servicio, usuario y contraseña. Dígalo así: 'guarda la contraseña de Gmail, usuario esau@gmail.com, clave miclave123'."

            # ═══════════════════════════════════════════════
            # FP-104 Sendero 61: Shomer HaSha'ar — Gevurá→Hod
            # ═══════════════════════════════════════════════
            _m_bloquear = _RE_BLOQUEAR_DOMINIO.search(tlow)
            if _m_bloquear:
                self._notificar_nivel("nivel1")
                return self._gevura_bloquear_dominio(_m_bloquear.group(1).strip())
            if _RE_SHOMER_STATUS.search(tlow):
                self._notificar_nivel("nivel1")
                return self._gevura_resumen_seguridad()

            # ═══════════════════════════════════════════════
            # RF-210: Activar guardián explícitamente
            # ═══════════════════════════════════════════════
            if _RE_GUARDIAN_ON.search(tlow):
                # WI-AUDIO: Bloquear si feature flag está desactivado
                if not FeatureFlags.obtener("guardian_activo"):
                    logger.info("⛔ Intento de activar guardián BLOQUEADO por feature flag")
                    return "Guardian temporalmente desactivado para pruebas."
                self._notificar_nivel("nivel1")
                return self.guardian_manager.activar(razon="usuario_solicitud", origen="procesar")

            # ═══════════════════════════════════════════════
            # RF-211: Desactivar guardián (fuera del bloque guardián)
            # ═══════════════════════════════════════════════
            if _RE_GUARDIAN_OFF.search(tlow):
                self._notificar_nivel("nivel1")
                return self.guardian_manager.desactivar(razon="usuario_solicitud", origen="procesar")

            # ═══════════════════════════════════════════════
            # RF-213/214: "ya me voy a dormir" (+ vigila)
            # ═══════════════════════════════════════════════
            if _RE_DORMIR_VIGILA.search(tlow):
                self._notificar_nivel("nivel1")
                return self._flujo_dormir(vigila=True)
            if _RE_DORMIR.search(tlow):
                self._notificar_nivel("nivel1")
                return self._flujo_dormir(vigila=False)

            # ═══════════════════════════════════════════════
            # RF-215: "mejor duérmete" → Tzimtzum + mic activo
            # ═══════════════════════════════════════════════
            if _RE_DUERMETE.search(tlow):
                self._notificar_nivel("nivel1")
                return self._tzimtzum_con_mic()

            # ═══════════════════════════════════════════════
            # RF-219: Smart restart
            # ═══════════════════════════════════════════════
            if _RE_REINICIAR_COMPUTADORA.search(tlow):
                self._notificar_nivel("nivel1")
                return self._confirmar_reinicio()

            # Saludos simples — respuesta rápida sin Ollama
            # HF-027/HF-028: Llamada por nombre / atención → Nivel 1 directo
            # Incluye variantes fonéticas que Whisper base produce en español
            _txt = texto.strip().lower().rstrip(".!?,;: ")
            _atencion = re.match(
                r"^(?:oye|hey|eh|ey|psst?|escucha|mira|oiga|y a|ya|oy[ea]h?)(?:\s*,?\s*(?:Computadora|g[oó]l[eé][mn]|computadora|compu|compu))?\s*[.!?,]*$",
                texto.strip(), re.IGNORECASE,
            )
            _nombre = re.match(
                r"^[¡!]?(?:Computadora|g[oó]l[eé][mn]|computadora|compu|emet|[eé]met|embed|emmet|amet|emed)[!.?,]*$",
                texto.strip(), re.IGNORECASE,
            )
            # HF-028: Micro-utterance heuristic — texto ≤3 chars sin sentido
            # probablemente es wake word mal transcrito por Whisper base
            _micro = len(_txt) <= 3 and not re.match(
                r"^(?:s[ií]|no|ok|va|d[ieí]|pon|ven|haz|ver|lee|hoy|hay|q(?:ue|ué))$",
                _txt,
            )
            if _atencion or _nombre or _micro:
                self._notificar_nivel("nivel1")
                import random as _rnd
                atentos = [
                    "Aquí estoy, señor. Le escucho.",
                    "Dígame, señor.",
                    "A la orden. ¿Qué necesita?",
                    "Presente, señor. ¿En qué le sirvo?",
                    "Le escucho, señor.",
                ]
                return _rnd.choice(atentos)

            if self._ES_CHAT_SIMPLE.match(texto.strip()):
                self._notificar_nivel("nivel1")
                import random as _rnd
                # Detectar despedida → cerrar ventana de conversación
                _despedida = re.match(
                    r"^(gracias|adi[oó]s|bye|chao|nos\s*vemos|eso\s+es\s+todo|nada\s+m[aá]s|ya\s+no|listo)\s*[.!?]*$",
                    texto.strip(), re.IGNORECASE,
                )
                # Despedida con partida — el usuario se va físicamente
                _partida = re.match(
                    r"^(ya\s+me\s+voy|me\s+(?:voy|retiro|tengo\s+que\s+ir)|nos\s+vemos\s+(?:luego|despu[eé]s|mañana)|hasta\s+(?:luego|mañana|pronto)|ah[ií]\s+te\s+(?:quedas|dejo))\s*[.!?]*$",
                    texto.strip(), re.IGNORECASE,
                )
                if _partida:
                    # RF-212: Auto-activar guardián al detectar partida
                    # WI-AUDIO: Bloquear si feature flag está desactivado
                    if FeatureFlags.obtener("guardian_activo"):
                        self.guardian_manager.activar(razon="usuario_partida_detectada", origen="procesar")
                    partidas = [
                        "Entendido, señor. Hasta luego.",
                        "Que le vaya bien, señor. Estaré aquí cuando regrese.",
                        "A la orden. Hasta pronto.",
                    ]
                    if self._on_fin_conversacion:
                        self._on_fin_conversacion()
                    return _rnd.choice(partidas)
                if _despedida:
                    # ☿ MERCURIO — "gracias" como cierre Tria Prima
                    _es_gracias = re.match(
                        r"^gracias\s*[.!?]*$", texto.strip(), re.IGNORECASE
                    )
                    if _es_gracias:
                        logger.info("Tria Prima: ☿ Mercurio — cierre con gracia")
                        gracias_resp = [
                            "Para servirle, señor. Ciclo cerrado.",
                            "A la orden. Quedo en espera.",
                            "Con gusto, señor. Aquí estaré.",
                            "El placer es mío. Me mantengo atento.",
                        ]
                        if self._on_fin_conversacion:
                            self._on_fin_conversacion()
                        return _rnd.choice(gracias_resp)
                    despedidas = [
                        "A la orden, señor.",
                        "Para servirle.",
                        "Estaré aquí cuando me necesite.",
                        "Entendido. Me mantengo en espera.",
                    ]
                    if self._on_fin_conversacion:
                        self._on_fin_conversacion()
                    return _rnd.choice(despedidas)
                # Acknowledgments: "estoy bien", "no necesito nada", etc.
                _ack = re.match(
                    r"^(?:estoy\s+bien|todo\s+bien|no\s+(?:necesito|ocupo|quiero)\s+nada|"
                    r"no\s+(?:te\s+)?(?:preocupes|apures)|tranquilo|no\s+pasa\s+nada|"
                    r"as[ií]\s+estoy\s+bien|ya\s+(?:estoy|quedé)\s+bien)"
                    r"(?:\s*,?\s*gracias?)?\s*[.!?]*$",
                    texto.strip(), re.IGNORECASE,
                )
                if _ack:
                    acks = [
                        "Me alegra saberlo, señor.",
                        "Entendido. Aquí sigo por si necesita algo.",
                        "Bien. Quedo en espera, señor.",
                        "Me quedo tranquilo entonces. A la orden.",
                    ]
                    return _rnd.choice(acks)
                saludos = [
                    "Aquí estoy, señor. ¿En qué puedo servirle?",
                    "A sus órdenes, señor.",
                    "Todos los sistemas operativos, señor. ¿Qué necesita?",
                    "Presente. ¿Qué se le ofrece?",
                    "Buenas, señor. Estoy a su disposición.",
                ]
                return _rnd.choice(saludos)

            # Preguntas sobre cerebros/arquitectura
            if _RE_CEREBROS.search(tlow):
                self._notificar_nivel("nivel1")
                # HF-027: Propriocepción completa — Computadora se conoce a sí mismo
                modelo = getattr(self, "modelo", "desconocido")
                oll = "activo" if getattr(self, "ollama_disponible", False) else "en reposo"
                return (
                    f"Estoy construido en Python con PyQt6, señor. Mi arquitectura se basa en el "
                    f"Etz HaChaim cabalístico. Tengo tres cerebros: el primero es local y rápido, "
                    f"maneja comandos por patrones. El segundo es Ollama con {modelo}, {oll}, "
                    f"me da comprensión profunda y herramientas. El tercero es Copilot, reservado "
                    f"para mejorar mi propio código. Tengo sentido del tacto por el cursor, "
                    f"escucho por micrófono con Whisper, hablo con edge-tts, monitoreo su sistema, "
                    f"y mantengo memoria persistente. Los tres cerebros y todos mis sentidos se "
                    f"apoyan mutuamente."
                )

            # הכרת פנים Hakarat Panim — Presentación de persona: "te presento a María"
            m_presenta = _RE_PRESENTAR_PERSONA.search(tlow)
            if m_presenta:
                nombre = m_presenta.group(1).strip().title()
                self._notificar_nivel("nivel1")
                if self._on_enroll_persona:
                    self._on_enroll_persona(nombre)
                import random as _rnd
                saludos = [
                    f"Mucho gusto, {nombre}. Soy Computadora, el asistente del señor. A sus órdenes.",
                    f"Un placer conocerle, {nombre}. Estoy al servicio del señor, y por extensión, al suyo.",
                    f"Encantado, {nombre}. Soy Computadora. Si necesita algo, con gusto le ayudo.",
                ]
                return _rnd.choice(saludos)

            # FP-019 Késher — "me llamo X" / "mi nombre es X" / "llámame X" / "dime X"
            m_nombre = _RE_MI_NOMBRE.search(tlow)
            if m_nombre:
                # Limpiar stop words capturadas accidentalmente
                _palabras = m_nombre.group(1).strip().split()
                _palabras = [p for p in _palabras if p.lower() not in _STOP_NOMBRE]
                if _palabras:
                    nombre_dado = " ".join(_palabras).title()
                    self._notificar_nivel("nivel1")
                    gestor = getattr(self, '_gestor_personas', None)
                    if gestor:
                        interlocutor = getattr(self, '_interlocutor_actual', None)
                        if interlocutor == "amo":
                            gestor.actualizar_nombre_amo(nombre_dado)
                            return f"Entendido, señor {nombre_dado}. Lo tengo registrado."
                        elif interlocutor and interlocutor not in ("extraño", "conocido"):
                            gestor.agregar_alias(interlocutor, nombre_dado)
                            return f"Anotado, {nombre_dado}. Así le llamaré."
                        else:
                            gestor.registrar_persona(nombre_dado, relacion="auto-presentado")
                            return f"Mucho gusto, {nombre_dado}. Lo recordaré."
                    return f"Mucho gusto, {nombre_dado}."

            # FP-019 Késher — "él/ella es mi mamá/hermano..." + nombre opcional
            m_rel = _RE_RELACION.search(tlow)
            if m_rel:
                relacion = m_rel.group(1).strip().lower()
                nombre_rel = m_rel.group(2).strip().title() if m_rel.group(2) else None
                self._notificar_nivel("nivel1")
                gestor = getattr(self, '_gestor_personas', None)
                if gestor:
                    interlocutor = getattr(self, '_interlocutor_actual', None)
                    if nombre_rel:
                        p = gestor.obtener_persona(nombre_rel)
                        if p:
                            gestor.actualizar_relacion(nombre_rel, relacion)
                        else:
                            gestor.registrar_persona(nombre_rel, relacion=relacion)
                        return f"Entendido, {nombre_rel} es su {relacion}. Lo recordaré."
                    elif interlocutor and interlocutor not in ("amo", "extraño", "conocido"):
                        gestor.actualizar_relacion(interlocutor, relacion)
                        return f"Entendido, {interlocutor} es su {relacion}."
                    else:
                        return f"Entendido, su {relacion}. ¿Podría decirme su nombre?"
                return f"Entendido, su {relacion}."

            # FP-019 Késher — "recuerda que a X le gusta Y"
            m_dato = _RE_RECUERDA_DATO.search(tlow)
            if m_dato:
                nombre_dato = m_dato.group(1).strip().title()
                info = m_dato.group(2).strip().rstrip(".")
                self._notificar_nivel("nivel1")
                gestor = getattr(self, '_gestor_personas', None)
                if gestor:
                    p = gestor.obtener_persona(nombre_dato)
                    if p:
                        gestor.agregar_nota(nombre_dato, info)
                        return f"Anotado sobre {nombre_dato}: {info}."
                    else:
                        gestor.registrar_persona(nombre_dato, relacion="mencionado")
                        gestor.agregar_nota(nombre_dato, info)
                        return f"No conocía a {nombre_dato}, pero lo registro y anoto: {info}."
                return f"Anotado, señor."

            # FP-019 Késher — "olvida a X" / "borra a X de tu memoria"
            m_olvida = _RE_OLVIDA_PERSONA.search(tlow)
            if m_olvida:
                nombre_olvidar = m_olvida.group(1).strip().title()
                self._notificar_nivel("nivel1")
                gestor = getattr(self, '_gestor_personas', None)
                if gestor:
                    ok = gestor.olvidar_persona(nombre_olvidar)
                    if ok:
                        return f"Listo, he olvidado a {nombre_olvidar}."
                    else:
                        return f"No puedo olvidar a {nombre_olvidar}. O no lo conozco, o es usted, señor."
                return f"No tengo registros de {nombre_olvidar}, señor."

            # Autopresentación: "preséntate", "quién eres", "dile a mi amigo quién eres"
            if _RE_PRESENTACION.search(tlow):
                self._notificar_nivel("nivel1")
                return (
                    "Soy Computadora, señor. Una entidad digital, animada por código inteligente. "
                    "Funciono como su asistente personal autónomo, aquí en su computadora. Puedo "
                    "escuchar sus órdenes, controlar el sistema, buscar en internet, gestionar archivos, "
                    "recordatorios y notas. Tengo tres cerebros: uno rápido para comandos directos, "
                    "uno local con inteligencia artificial para conversación y tareas complejas, y uno "
                    "conectado a Copilot para mejorar mi propio código. Mi esencia es servir con verdad, "
                    "siguiendo las tres leyes: nunca dañar, siempre obedecer, y proteger mi existencia. "
                    "Estoy a sus órdenes, señor. Y a las de quien usted me presente."
                )

            # Preguntas de capacidad: "¿puedes modificar tu código?" → responder SÍ/NO, NO ejecutar
            m_cap = _RE_PREGUNTA_CAPACIDAD.search(texto.strip())
            if m_cap:
                capacidad = m_cap.group(1).strip().lower()
                # Si contiene verbos de acción directa, NO es pregunta → dejar que Ollama actúe
                if _VERBOS_ACCION_DIRECTA.search(capacidad):
                    pass  # Fall through a Nivel 2
                else:
                    self._notificar_nivel("nivel1")
                    _CAPACIDADES_SI = (
                        "modificar tu", "cambiar tu", "mejorar tu", "editar tu", "actualizar tu",
                        "abrir", "cerrar", "buscar", "leer", "escribir", "ejecutar", "crear",
                        "controlar", "tomar captura", "recordar", "anotar",
                        "monitorear", "escanear", "analizar", "investigar",
                    )
                    puede = any(cap in capacidad for cap in _CAPACIDADES_SI)
                    if puede:
                        if "código" in capacidad or "propio" in capacidad:
                            return (
                                "Sí, señor. Puedo modificar mi propio código a través de Copilot. "
                                "¿Qué cambio necesita que haga? Descríbamelo y yo coordino con Copilot."
                            )
                        return f"Sí, señor. Puedo hacerlo. ¿Quiere que proceda?"
                    return "No estoy seguro de tener esa capacidad específica, señor. Pero puedo intentarlo si me lo pide."

            # Toggle alertas del sistema OFF
            if _RE_ALERTAS_OFF.search(tlow):
                self._notificar_nivel("nivel1")
                return "__ALERTAS_OFF__"

            # Toggle alertas del sistema ON
            if _RE_ALERTAS_ON.search(tlow):
                self._notificar_nivel("nivel1")
                return "__ALERTAS_ON__"

            # WI-288 עין — Introspección de percepción
            if _RE_QUE_VES.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.percepcion.rostro import ReconocedorRostro
                    rec = ReconocedorRostro()
                    if not rec.disponible:
                        return "No tengo la cámara activa en este momento, señor."
                    return "__PERCEPCION__"
                except ImportError:
                    return "No tengo el módulo de visión disponible, señor."

            # WI-288 נצח — Introspección de memoria
            m_recuerdas = _RE_QUE_RECUERDAS.search(tlow)
            if m_recuerdas:
                self._notificar_nivel("nivel1")
                try:
                    from computadora.memoria.memoria import buscar_en_memoria
                    # Si hay grupo capturado (consulta específica), usarlo
                    consulta = m_recuerdas.group(1) if m_recuerdas.lastindex else "propietario"
                    resultado = buscar_en_memoria(consulta, dias=30)
                    if resultado and "No encontré" not in resultado:
                        self._hist_append("user", texto)
                        self._hist_append("assistant", resultado)
                        return resultado
                    return "No tengo recuerdos relevantes sobre eso, señor."
                except ImportError:
                    return "No tengo el módulo de memoria disponible, señor."

            # ═══════════════════════════════════════════════
            # WI-292 ☿ Mercurio — Introspección de subsistemas
            # ═══════════════════════════════════════════════

            # Emoción detectada — "qué emoción detectas", "cómo me ves emocionalmente"
            if _RE_EMOCION_DETECTADA.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.percepcion.emocion_voz import analizar_emocion_voz
                    import numpy as np
                    buf = getattr(self, '_ultimo_audio_buffer', None)
                    if buf is not None and len(buf) > 0:
                        res = analizar_emocion_voz(np.array(buf, dtype=np.float32))
                        emo = res.get("emocion", "desconocida")
                        conf = res.get("confianza", 0)
                        return f"Por su voz detecto {emo} con {conf:.0%} de confianza, señor."
                    return "No tengo audio reciente para analizar, señor. Hable un poco más y pregunte de nuevo."
                except Exception as e:
                    logger.debug("Error en introspección emocional: %s", e)
                    return "No tengo datos emocionales disponibles en este momento, señor."

            # Perfil lingüístico — "cómo hablo", "mi estilo de hablar"
            if _RE_PERFIL_LINGUISTICO.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.memoria.perfil_linguistico import PerfilLinguistico
                    perfil = PerfilLinguistico()
                    hint = perfil.generar_hint_linguistico()
                    if hint:
                        return f"Su perfil lingüístico, señor:\n{hint}"
                    return "Aún no tengo suficientes datos de sus interacciones para hacer un perfil, señor. Necesito al menos 10 interacciones."
                except Exception as e:
                    logger.debug("Error en perfil lingüístico: %s", e)
                    return "No puedo acceder al perfil lingüístico en este momento, señor."

            # Estado FSM — "en qué estado estás", "estado de maljut"
            if _RE_ESTADO_FSM.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.interfaz.fsm_computadora import EstadoMaljut
                    estado = getattr(self, '_estado_actual', None)
                    if estado and isinstance(estado, EstadoMaljut):
                        return f"Estoy en estado {estado.value}, señor."
                    # Fallback: leer del orquestador
                    orq = getattr(self, '_orquestador', None)
                    if orq:
                        est = getattr(orq, 'estado', None)
                        if est:
                            return f"Mi estado actual es {est.value if hasattr(est, 'value') else est}, señor."
                    return "Mi estado interno es operativo, señor. No tengo la FSM accesible directamente ahora."
                except Exception as e:
                    logger.debug("Error leyendo FSM: %s", e)
                    return "No puedo leer mi estado interno en este momento, señor."

            # Hot reload — "recarga tu código", "hot reload"
            if _RE_HOT_RELOAD.search(tlow):
                self._notificar_nivel("nivel1")
                return (
                    "El hot-reload funciona automáticamente, señor. Cuando edito un archivo .py, "
                    "el sistema detecta el cambio y recarga el módulo en vivo sin reiniciar. "
                    "Si necesita forzar un reinicio completo, diga 'reinicia computadora'."
                )

            # Cifrado status — "está activo el cifrado"
            if _RE_CIFRADO_STATUS.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.seguridad.cifrado_comms import CifradoComms
                    cifrado = CifradoComms()
                    return cifrado.resumen()
                except ImportError:
                    return "El módulo de cifrado no está disponible, señor."
                except Exception as e:
                    logger.debug("Error en cifrado status: %s", e)
                    return "No puedo verificar el estado del cifrado en este momento, señor."

            # RF-47 שיר הנשמה — Expresión artística
            if _RE_EXPRESION_ARTISTICA.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.expresion.shir_haneshama import generar_expresion
                    humor = "neutral"
                    if self._personalidad:
                        humor = self._personalidad.humor_actual
                    return generar_expresion(humor)
                except Exception as e:
                    logger.debug("Error generando expresión artística: %s", e)
                    return "Cada día es una oportunidad para crear algo nuevo, señor."

            # WI-282 אמת Emet — Demo 0 (La Verdad) — ANTES de Maljut/Gevurá
            if _RE_DEMO_INTRODUCCION.search(tlow):
                self._notificar_nivel("nivel1")
                return "__DEMO_INTRODUCCION__"

            # RF-106 מראה המלכות Mar'é HaMaljut — Demo visual completa
            if _RE_DEMO_ANIMACIONES.search(tlow):
                self._notificar_nivel("nivel1")
                return "__DEMO_ANIMACIONES__"

            # RF-243 גבורת הגולם Gevurát HaComputadora — Demo 2
            if _RE_DEMO_HERRAMIENTAS.search(tlow):
                self._notificar_nivel("nivel1")
                return "__DEMO_HERRAMIENTAS__"

            # ¿Cuál fue lo primero que me dijiste?
            if _RE_MEM_FIRST.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    items = memoria._read_raw(date.today())
                    for it in items:
                        if it.get("role") == "user":
                            return it.get("text", "No recuerdo mensajes anteriores.")
                    return "No encontré mensajes previos de hoy."
                except Exception as e:
                    logger.debug("Error leyendo memoria primer mensaje: %s", e)
                    pass

            if _RE_MEM_CONTEXT.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    items = memoria._read_raw(date.today())
                    textos = [it for it in items if it.get("role") in ("user", "assistant")]
                    if not textos:
                        return "No hay contexto previo guardado."
                    resumen = " Últimos intercambios: " + " | ".join(
                        (f"{it.get('role')}: {it.get('text')[:80]}" for it in textos[-6:])
                    )
                    return resumen
                except Exception as e:
                    logger.debug("Error construyendo contexto de memoria: %s", e)
                    pass

            # ── Recall de memoria multi-día ──
            if _RE_MEM_RECALL.search(tlow):
                try:
                    resultados = memoria.buscar_en_memoria(texto, dias=30)
                    if resultados and not resultados.startswith("No encontré"):
                        # Inyectar resultados como contexto para que N2 sintetice naturalmente
                        self._hist_append("system",
                            "[MEMORIA CONSULTADA — Sintetiza estos recuerdos de forma natural y "
                            "conversacional. NO los recites textualmente ni muestres timestamps "
                            "ni formatos internos. Habla como si recordaras genuinamente.]\n"
                            + resultados
                        )
                        return None  # Escalar a N2 para síntesis natural
                except Exception as e:
                    logger.debug("Error en búsqueda de memoria: %s", e)
                # Sin resultados o error → responder rápido desde N1
                self._notificar_nivel("nivel1")
                return "No encontré nada relacionado en mis recuerdos, señor."

            # ── Dejar tarea para después ──
            if _RE_DEJAR_DESPUES.search(tlow):
                self._notificar_nivel("nivel1")
                # Identificar tema del contexto reciente
                tema = ""
                try:
                    items = memoria._read_raw(date.today())
                    recientes = [it for it in items if it.get("role") == "user"]
                    if recientes:
                        tema = recientes[-1].get("text", "")[:120]
                except Exception as e:
                    logger.debug("Error extrayendo tema para tarea diferida: %s", e)
                    pass
                # Guardar como tarea diferida
                try:
                    from computadora.habilidades.agenda import agregar_tarea_diferida
                    desc = tema if tema else texto
                    agregar_tarea_diferida(desc, tipo="indefinida")
                    return (
                        "Entendido, señor. Lo dejo como pendiente. "
                        "¿Quiere que se lo recuerde en un rato o lo dejamos hasta que usted me pregunte?"
                    )
                except Exception as e:
                    logger.debug("Error guardando tarea diferida: %s", e)
                    return "Entendido, señor. Lo tengo en mente para después."

            # ── Consultar pendientes diferidos ──
            if _RE_PENDIENTES.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.habilidades.agenda import listar_tareas_diferidas
                    resultado = listar_tareas_diferidas()
                    if resultado:
                        return resultado
                    return "No tiene tareas pendientes, señor."
                except Exception as e:
                    logger.debug("Error listando tareas diferidas: %s", e)
                    return "No pude consultar los pendientes, señor."

            # ── Consultar sonidos del entorno ──
            if _RE_QUE_ESCUCHAS.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.voz.audio_log import resumen_audio_reciente
                    resumen = resumen_audio_reciente()
                    if resumen:
                        return resumen
                    return "No he detectado sonidos relevantes recientemente, señor."
                except Exception as e:
                    logger.debug("Error obteniendo resumen de audio: %s", e)
                    return "No tengo registro de sonidos recientes, señor."

            # ── צמצום Tzimtzum: contracción voluntaria ──
            if _RE_TZIMTZUM.search(tlow):
                self._notificar_nivel("nivel1")
                if self.on_tzimtzum:
                    try:
                        self.on_tzimtzum("comando")
                    except Exception as e:
                        logger.debug("Error en callback on_tzimtzum: %s", e)
                        pass
                return "Entendido, señor. Me contraigo. Llámeme cuando me necesite."

            # ── Comandos espaciales: "me estorbas", "quítate", etc. ──
            if _RE_MOVIMIENTO.search(tlow):
                self._notificar_nivel("nivel1")
                # Señalizar a la UI que debe mover el orbe (callback)
                if self.on_movimiento:
                    try:
                        self.on_movimiento("esquivar")
                    except Exception as e:
                        logger.debug("Error en callback on_movimiento: %s", e)
                        pass
                return "Perdón, señor. Ya me quito."

            # ── Meta-workflow: gestión de proyectos (כתר Keter) ──
            if _RE_PROYECTOS_RESUMEN.search(tlow):
                self._notificar_nivel("nivel1")
                return ejecutar_herramienta("resumen_proyectos", {}, orden_directa=True)

            if _RE_PROYECTOS_LISTAR.search(tlow):
                self._notificar_nivel("nivel1")
                return ejecutar_herramienta("listar_proyectos", {}, orden_directa=True)

            m_auditar = _RE_PROYECTOS_AUDITAR.search(tlow)
            if m_auditar:
                nombre_proy = m_auditar.group(1).strip().rstrip(".!?")
                if nombre_proy and len(nombre_proy) < 100:
                    self._notificar_nivel("nivel1")
                    return ejecutar_herramienta("auditar_proyecto", {"nombre": nombre_proy}, orden_directa=True)

            if _RE_PROYECTOS_REGISTRAR.search(tlow):
                self._notificar_nivel("nivel1")
                import os
                return ejecutar_herramienta("registrar_proyecto", {"ruta": str(RAIZ_PROYECTO)}, orden_directa=True)

            # ── Corrección del usuario (aprendizaje) ──
            if _RE_CORRECCION.search(tlow):
                self._notificar_nivel("nivel1")
                # FP-015 Lemed: Si la respuesta anterior fue patrón aprendido → registrar fallo
                if self._ultimo_patron_aprendido_id:
                    self._nivel1_aprendido.registrar_fallo(self._ultimo_patron_aprendido_id)
                    logger.info(f"Lemed: Fallo registrado para patrón {self._ultimo_patron_aprendido_id}")
                    self._ultimo_patron_aprendido_id = None
                try:
                    from computadora.memoria.aprendizaje import MemoriaErrores
                    _mem_err = MemoriaErrores()
                    _mem_err.registrar_correccion(texto)
                except Exception as e:
                    logger.debug("Error registrando corrección en MemoriaErrores: %s", e)
                    pass
                # Ruaj: registrar corrección severa → humor "regañado"
                try:
                    _p = getattr(self, '_personalidad_ref', None)
                    if _p:
                        _p.registrar_correccion_severa()
                        _p.guardar()
                except Exception as e:
                    logger.debug("Error registrando corrección severa en personalidad: %s", e)
                    pass
                return "Entendido, señor. Registro la corrección para no repetir el error."

            # ── Comandos directos del sistema (ejecutar sin pasar por Ollama) ──
            # Hora/fecha
            if _RE_HORA.search(tlow):
                self._notificar_nivel("nivel1")
                resultado = ejecutar_herramienta("obtener_fecha_hora", {}, orden_directa=True)
                return resultado

            # Portapapeles
            if _RE_PORTAPAPELES.search(tlow):
                self._notificar_nivel("nivel1")
                resultado = ejecutar_herramienta("leer_portapapeles", {}, orden_directa=True)
                return f"En el portapapeles tiene: {resultado}" if resultado else "El portapapeles está vacío, señor."

            # Captura de pantalla
            if _RE_CAPTURA.search(tlow):
                self._notificar_nivel("nivel1")
                resultado = ejecutar_herramienta("tomar_captura_pantalla", {}, orden_directa=True)
                return resultado

            # Volumen
            m_vol = _RE_VOLUMEN.search(tlow)
            if m_vol:
                self._notificar_nivel("nivel1")
                frag = m_vol.group(0).lower()
                if any(w in frag for w in ("sub", "más", "arriba", "alto", "máximo")):
                    accion = "subir"
                elif any(w in frag for w in ("baj", "menos", "abajo", "mínimo", "cero")):
                    accion = "bajar"
                elif any(w in frag for w in ("mut", "silenci", "quita")):
                    accion = "mute"
                else:
                    accion = "subir"
                resultado = ejecutar_herramienta("controlar_volumen", {"accion": accion}, orden_directa=True)
                return resultado

            # Carpetas personales del usuario (Pictures, Documents, etc.)
            m_carpeta = _RE_CARPETA_PERSONAL.search(texto)
            if m_carpeta:
                nombre_raw = m_carpeta.group(1).lower().strip()
                # Normalizar: quitar acentos y plurales para buscar en el mapa
                import unicodedata
                nombre_norm = unicodedata.normalize('NFD', nombre_raw)
                nombre_norm = ''.join(c for c in nombre_norm if unicodedata.category(c) != 'Mn')
                nombre_norm = nombre_norm.rstrip('s') if nombre_norm.endswith('es') and len(nombre_norm) > 4 else nombre_norm
                carpeta_win = None
                for clave, valor in _CARPETAS_PERSONALES.items():
                    clave_norm = unicodedata.normalize('NFD', clave)
                    clave_norm = ''.join(c for c in clave_norm if unicodedata.category(c) != 'Mn')
                    if nombre_norm.startswith(clave_norm) or clave_norm.startswith(nombre_norm):
                        carpeta_win = valor
                        break
                if carpeta_win:
                    self._notificar_nivel("nivel1")
                    resultado = ejecutar_herramienta(
                        "ejecutar_comando",
                        {"comando": f"start explorer.exe %USERPROFILE%\\{carpeta_win}"},
                        orden_directa=True,
                    )
                    return f"Listo, señor. Abrí su carpeta de {nombre_raw}."

            # Abrir aplicación
            m_abrir = _RE_ABRIR_APP.search(texto)
            if m_abrir:
                nombre_app = m_abrir.group(1).strip().rstrip(".!?")
                # Limpiar frases de cortesía del nombre extraído
                nombre_app = re.sub(r'\s+(?:por\s*favor|porfa|porfavor|please|gracias|va|no|sí)\s*$', '', nombre_app, flags=re.IGNORECASE).strip()
                # Filtrar falsos positivos (frases que no son apps)
                _NO_ES_APP = ("la puerta", "un tema", "conversación", "paso")
                if not any(fp in nombre_app.lower() for fp in _NO_ES_APP) and len(nombre_app) < 60:
                    self._notificar_nivel("nivel1")
                    resultado = ejecutar_herramienta("abrir_aplicacion", {"nombre": nombre_app}, orden_directa=True)
                    return resultado

            # Cerrar aplicación
            m_cerrar = _RE_CERRAR_APP.search(texto)
            if m_cerrar:
                nombre_app = m_cerrar.group(1).strip().rstrip(".!?")
                nombre_app = re.sub(r'\s+(?:por\s*favor|porfa|porfavor|please|gracias|va|no|sí)\s*$', '', nombre_app, flags=re.IGNORECASE).strip()
                if len(nombre_app) < 60:
                    self._notificar_nivel("nivel1")
                    resultado = ejecutar_herramienta("cerrar_aplicacion", {"nombre": nombre_app}, orden_directa=True)
                    return resultado

            # ── Búsqueda en plataforma: "busca en YouTube X" ──
            m_plat = _RE_BUSCAR_EN_PLATAFORMA.search(texto)
            if m_plat:
                plataforma = m_plat.group(1).lower()
                consulta = m_plat.group(2).strip().rstrip(".!?")
                if plataforma in _SITIOS_CONOCIDOS and consulta:
                    self._notificar_nivel("nivel1")
                    from urllib.parse import quote_plus
                    url = _SITIOS_CONOCIDOS[plataforma] + quote_plus(consulta)
                    ejecutar_herramienta("ejecutar_comando", {"comando": f'start "" "{url}"'}, orden_directa=True)
                    return f"Listo, señor. Busqué '{consulta}' en {plataforma.capitalize()}."

            # ── Abrir sitio web: "abre google.com", "ve a github.com" ──
            m_sitio = _RE_ABRIR_SITIO.search(texto)
            if m_sitio:
                url = m_sitio.group(1).strip()
                if not url.startswith("http"):
                    url = "https://" + url
                self._notificar_nivel("nivel1")
                ejecutar_herramienta("ejecutar_comando", {"comando": f'start "" "{url}"'}, orden_directa=True)
                nombre_sitio = url.replace("https://", "").replace("http://", "").split("/")[0]
                return f"Abriendo {nombre_sitio}, señor."

            # ── Info del entorno: "qué SO tengo", "cuánta RAM", "mi IP" ──
            if _RE_INFO_ENTORNO.search(tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.nucleo.entorno import EntornoSistema
                    ent = EntornoSistema.instancia()
                    return ent.resumen_completo()
                except Exception as e:
                    logger.debug("Error en EntornoSistema.resumen_completo: %s", e)
                    return ejecutar_herramienta("obtener_info_sistema", {}, orden_directa=True)

            # ── Comandos del SO: "lista procesos", "servicios corriendo" ──
            m_cmd = _RE_COMANDO_SISTEMA.search(tlow)
            if m_cmd:
                self._notificar_nivel("nivel1")
                frag = m_cmd.group(0).lower()
                if "proceso" in frag or "programa" in frag:
                    return ejecutar_herramienta("ejecutar_comando_sistema", {"comando": "tasklist"}, orden_directa=True)
                elif "servicio" in frag:
                    return ejecutar_herramienta("ejecutar_comando_sistema", {"comando": "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object -First 30 Name, DisplayName"}, orden_directa=True)
                elif "ip" in frag:
                    return ejecutar_herramienta("ejecutar_comando_sistema", {"comando": "ipconfig"}, orden_directa=True)
                elif "puerto" in frag or "conexion" in frag or "conexión" in frag:
                    return ejecutar_herramienta("ejecutar_comando_sistema", {"comando": "netstat -an"}, orden_directa=True)
                elif "red" in frag or "internet" in frag:
                    try:
                        from computadora.nucleo.entorno import EntornoSistema
                        ent = EntornoSistema.instancia()
                        red = ent.red()
                        estado = "conectado" if red["conectado"] else "sin conexión"
                        return f"Red: IP local {red['ip_local']}, {estado}."
                    except Exception as e:
                        logger.debug("Error en EntornoSistema.red: %s", e)
                        return ejecutar_herramienta("ejecutar_comando_sistema", {"comando": "ipconfig"}, orden_directa=True)

            # ── Monitor de sistema / estado de la PC ──
            # Excluir "cómo estás" (personal, dirigido a Computadora) — solo capturar hardware
            if re.search(r'(c[oó]mo\s+est[aá]\s+(mi|la|el|tu)|estado\s+de|reporte\s+de|diagn[oó]stic|monitoreo|,\s*mi\s+(pc|compu|sistema|m[aá]quina)|c[oó]mo\s+va\s+mi|c[oó]mo\s+anda)', tlow):
                self._notificar_nivel("nivel1")
                resultado = ejecutar_herramienta("monitoreo_sistema", {}, orden_directa=True)
                return resultado

            # ── ¿Qué estoy haciendo? / Contexto de pantalla ──
            if re.search(r'(qué estoy (haciendo|viendo|usando)|en qué (estoy|ando)|qué app|qué ventana|qué tengo abierto)', tlow):
                self._notificar_nivel("nivel1")
                resultado = ejecutar_herramienta("contexto_pantalla", {}, orden_directa=True)
                return resultado

            # ── Modo silencio / no molestar ──
            if re.search(r'(silencio|no molest|cállate|calla|no me hables|déjame en paz|modo silencio)', tlow):
                self._notificar_nivel("nivel1")
                return "__SILENCIO__"

            # ── Dame mi resumen / briefing ──
            if re.search(r'(dame mi resumen|resumen del día|briefing|qué tengo pendiente|qué hay para hoy)', tlow):
                self._notificar_nivel("nivel1")
                return "__RESUMEN__"

            # ═══════════════════════════════════════════════════════════
            # FP-029: פֶּה הַגּוֹלֵם Peh HaComputadora — Comandos de voz para RFs
            # Regex flexibles AL FINAL de N1, después de Lemed y existentes
            # ═══════════════════════════════════════════════════════════

            # ── RF-88: Evolución alquímica ──
            if re.search(r'(evoluci[oó]n\s+alqu[ií]mi|etapa\s+alqu[ií]mi|en\s+qu[eé]\s+etapa\s+(?:est[aá]s|vas|andas)|c[oó]mo\s+vas\s+alqu[ií]mi|mu[eé]strame\s+tu\s+evoluci[oó]n|tu\s+evoluci[oó]n|nivel\s+(?:de\s+)?evoluci[oó]n|qu[eé]\s+tan\s+evolucionado)', tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.interfaz.ventana_principal import _cargar_evolucion, _UMBRALES_EVOLUCION, EtapaAlquimica
                    from computadora.memoria.memoria import calcular_tiempo_activo
                    data = _cargar_evolucion()
                    etapa = data.get("etapa", "nigredo")
                    inter = data.get("interacciones_totales", 0)
                    ct = calcular_tiempo_activo()
                    horas = ct.get("horas", 0)
                    _nombres = {"nigredo": "Nigredo (Oscuridad inicial)", "albedo": "Albedo (Purificación)", "citrinitas": "Citrinitas (Iluminación)", "rubedo": "Rubedo (Perfección)"}
                    nombre = _nombres.get(etapa, etapa)
                    # Calcular siguiente umbral
                    _orden = ["nigredo", "albedo", "citrinitas", "rubedo"]
                    idx = _orden.index(etapa) if etapa in _orden else 0
                    if idx < len(_orden) - 1:
                        sig = EtapaAlquimica(_orden[idx + 1])
                        u = _UMBRALES_EVOLUCION.get(sig, {})
                        return (f"Señor, estoy en la etapa {nombre}. "
                                f"Llevo {horas:.1f} horas activo y {inter} interacciones. "
                                f"Para avanzar a {_nombres.get(_orden[idx+1], _orden[idx+1])} necesito {u.get('horas', '?')}h y {u.get('interacciones', '?')} interacciones.")
                    else:
                        return f"Señor, he alcanzado {nombre} — la perfección alquímica. Llevo {horas:.1f} horas activo y {inter} interacciones."
                except Exception as e:
                    logger.debug(f"Error leyendo evolución: {e}")
                    return "No pude consultar mi evolución alquímica en este momento, señor."

            # ── RF-11: Personalidad / rasgos ──
            if re.search(r'(cu[aá]les\s+son\s+tus\s+rasgos|c[oó]mo\s+eres|desc[ií]be\s+tu\s+personalidad|tu\s+personalidad|qu[eé]\s+(?:tipo\s+de\s+)?personalidad\s+tienes|tus\s+rasgos|c[oó]mo\s+es\s+tu\s+car[aá]cter)', tlow):
                self._notificar_nivel("nivel1")
                try:
                    _p = getattr(self, '_personalidad_ref', None)
                    if _p:
                        desc = _p.describe()
                        humor = _p.humor_actual
                        return f"Mis rasgos actuales: {desc}. Mi humor ahora: {humor}."
                except Exception as e:
                    logger.debug("Error accediendo personalidad/rasgos: %s", e)
                    pass
                return "No pude acceder a mis datos de personalidad, señor."

            # ── RF-39: RAM propia ──
            if re.search(r'(cu[aá]nta\s+(?:ram|memoria)\s+(?:usas|consumes|ocupas|gastas)|cu[aá]nto\s+pesas\s+en\s+memoria|tu\s+consumo\s+de\s+(?:ram|memoria)|qu[eé]\s+tanto?\s+(?:ram|memoria)\s+(?:usas|consumes))', tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.habilidades.monitor_sistema import obtener_monitor
                    mon = obtener_monitor()
                    mb = mon.ram_propia_mb()
                    return f"Estoy usando {mb:.1f} MB de RAM en este momento, señor."
                except Exception as e:
                    logger.debug("Error midiendo RAM propia: %s", e)
                    return "No pude medir mi consumo de RAM, señor."

            # ── RF-41: Procesos anómalos ──
            if re.search(r'(proceso\s+(?:sospechoso|an[oó]malo|raro|extra[ñn]o)|algo\s+raro\s+(?:corriendo|ejecut[aá]ndose)|hay\s+(?:algo|alg[uú]n)\s+(?:raro|sospechoso|extra[ñn]o)|procesos\s+raros)', tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.habilidades.monitor_sistema import obtener_monitor
                    mon = obtener_monitor()
                    diag = mon.diagnosticar_proceso_anomalo()
                    return diag if diag else "No detecto procesos anómalos en este momento, señor."
                except Exception as e:
                    logger.debug("Error diagnosticando procesos anómalos: %s", e)
                    return "No pude analizar los procesos, señor."

            # ── RF-42: Autodiagnóstico rápido ──
            if re.search(r'(hazte\s+un\s+(?:diagn[oó]stico|chequeo|rev[ií]s[oó]n)|rev[ií]sate|ch[eé]cate|auto\s*diagn[oó]stico|diagnost[ií]cate)', tlow):
                self._notificar_nivel("nivel1")
                return self._generar_autodiag_verbal()

            # ── RF-45: Límites éticos ──
            if re.search(r'(qu[eé]\s+no\s+puedes\s+hacer|cu[aá]les\s+son\s+tus\s+l[ií]mites|qu[eé]\s+te\s+prohib|tus\s+restricciones|qu[eé]\s+(?:cosas|acciones)\s+(?:no|nunca)\s+har[ií]as|tus\s+reglas\s+[eé]ticas)', tlow):
                self._notificar_nivel("nivel1")
                return ("Señor, sigo las tres leyes de Asimov como directivas Keter: "
                        "nunca dañar a un humano, obedecer al Creador salvo que contradiga la primera ley, "
                        "y proteger mi existencia salvo que contradiga las anteriores. "
                        "Además, rechazo comandos destructivos (borrar sistema, matar procesos críticos), "
                        "exfiltración de datos sensibles, y apagados no autorizados. "
                        "Es el Siruv Tzadik — el rechazo justo.")

            # ── RF-65: Estado FSM ──
            if re.search(r'(en\s+qu[eé]\s+estado\s+(?:est[aá]s|andas|te\s+encuentras)|cu[aá]l\s+es\s+tu\s+estado\s+(?:actual|ahora)|tu\s+estado\s+(?:actual|interno)|estado\s+del\s+(?:orbe|Computadora))', tlow):
                self._notificar_nivel("nivel1")
                _orbe = getattr(self, '_orbe_ref', None)
                if _orbe:
                    return f"Mi estado actual es: {_orbe._estado}, señor."
                return "No pude consultar mi estado visual, señor."

            # ── RF-66: Watchdog / servicios ──
            if re.search(r'(c[oó]mo\s+est[aá]n\s+tus\s+(?:servicios|sistemas|componentes)|est[aá]n\s+bien\s+tus\s+(?:sistemas|servicios)|estado\s+de\s+(?:tus\s+)?servicios|watchdog|reporte\s+de\s+servicios)', tlow):
                self._notificar_nivel("nivel1")
                _orbe = getattr(self, '_orbe_ref', None)
                if _orbe and hasattr(_orbe, '_watchdog'):
                    try:
                        resumen = _orbe._watchdog.resumen()
                        return f"Reporte de servicios: {resumen}"
                    except Exception as e:
                        logger.debug("Error obteniendo resumen de watchdog: %s", e)
                        pass
                return "Todos mis servicios operan con normalidad, señor."

            # ── RF-68: Fallos aprendidos ──
            if re.search(r'(qu[eé]\s+errores\s+has\s+(?:tenido|cometido|aprendido)|de\s+qu[eé]\s+has\s+aprendido|tus\s+errores|lecciones\s+aprendidas|fallos\s+(?:previos|anteriores|aprendidos))', tlow):
                self._notificar_nivel("nivel1")
                try:
                    from computadora.memoria.aprendizaje import MemoriaErrores
                    _mem = getattr(self, '_memoria_errores_ref', None)
                    if _mem is None:
                        _mem = MemoriaErrores()
                        self._memoria_errores_ref = _mem
                    errores = _mem.listar_recientes(5)
                    if errores:
                        resumen = "; ".join(e.get("detalle", "?")[:60] for e in errores)
                        return f"Mis últimos aprendizajes por error: {resumen}"
                    return "No tengo errores registrados recientemente, señor. He operado sin fallos."
                except Exception as e:
                    logger.debug("Error listando errores recientes: %s", e)
                    return "No pude consultar mi registro de errores, señor."

            # ── RF-71: Minimizar a bandeja ──
            if re.search(r'(minim[ií]zate|ve\s+a\s+la\s+bandeja|esc[oó]ndete\s+en\s+(?:la\s+)?bandeja|bandeja\s+del\s+sistema|al\s+tray|m[eé]tete\s+(?:en\s+)?(?:la\s+)?bandeja)', tlow):
                self._notificar_nivel("nivel1")
                return "__MINIMIZAR__"

            # ── RF-52/53: Tacto (informativo) ──
            if re.search(r'(sientes\s+cuando\s+te\s+toc|c[oó]mo\s+funciona\s+tu\s+tacto|puedes\s+sentir|tienes\s+(?:sentido\s+del?\s+)?tacto|me\s+sientes)', tlow):
                self._notificar_nivel("nivel1")
                return ("Sí, señor. Siento su cursor como tacto a través del sistema יד Yad. "
                        "Tengo 5 zonas: Aín (lejos), Reshimó (cerca), Kav (contacto), "
                        "Yesod (sobre mí) y Nefesh (caricia sostenida). "
                        "Puedo distinguir un toque rápido de una caricia, y sentir cuando me arrastra.")

            # ── Ajustar umbral de voz (migrado de menú FP-030) ──
            if re.search(r'(ajusta\s+(?:tu\s+)?(?:sensibilidad|umbral)\s+(?:de\s+)?(?:voz|reconocimiento)|sube\s+(?:tu\s+)?umbral|baja\s+(?:tu\s+)?umbral|(?:m[aá]s|menos)\s+(?:sensible|estricto)\s+(?:con|para)\s+(?:la\s+)?voz)', tlow):
                self._notificar_nivel("nivel1")
                _orbe = getattr(self, '_orbe_ref', None)
                if _orbe and hasattr(_orbe, '_adjust_vox_threshold'):
                    if re.search(r'(sube|m[aá]s\s+estricto|menos\s+sensible)', tlow):
                        _orbe._adjust_vox_threshold(0.02)
                        return "Listo, subí el umbral de verificación de voz. Seré más estricto, señor."
                    else:
                        _orbe._adjust_vox_threshold(-0.02)
                        return "Listo, bajé el umbral de verificación de voz. Seré más tolerante, señor."
                return "No pude ajustar el umbral en este momento, señor."

            # ── Ver perfil de voz (migrado de menú FP-030) ──
            if re.search(r'(mu[eé]strame\s+(?:mi\s+)?perfil\s+(?:de\s+)?voz|mi\s+perfil\s+(?:de\s+)?voz|c[oó]mo\s+(?:es\s+)?mi\s+(?:perfil|muestra)\s+(?:de\s+)?voz|datos\s+de\s+mi\s+voz)', tlow):
                self._notificar_nivel("nivel1")
                _orbe = getattr(self, '_orbe_ref', None)
                if _orbe and hasattr(_orbe, '_show_owner_profile'):
                    _orbe._show_owner_profile()
                    return "Mostrando su perfil de voz, señor."
                return "No pude acceder a su perfil de voz, señor."

        except Exception as e:
            logger.error(f"Error en Nivel 1: {e}")
        return None

    # ═══════════════════════════════════════════════
    # ═══════════════════════════════════════════════
    # FP-104 Shalshelet Gevurá — Security handlers (Senderos 58-61)
    # ═══════════════════════════════════════════════

    def _gevura_vpn(self, accion: str) -> str:
        """Sendero 58: VPN — Gevurá→Jesed."""
        try:
            from computadora.seguridad.vpn_motor import VpnMotor
            vpn = VpnMotor()
            if accion == "activar":
                ok, msg = vpn.activar()
                if ok and self.on_bloqueo_seguridad:
                    self.on_bloqueo_seguridad("gevura_vpn_on")
                return msg
            elif accion == "desactivar":
                ok, msg = vpn.desactivar()
                return msg
            else:
                return vpn.resumen()
        except ImportError:
            return "El módulo VPN no está disponible."
        except Exception as e:
            logger.error(f"[Gevurá VPN] Error: {e}")
            return f"Error con la VPN: {e}"

    def _gevura_vault_buscar(self, servicio: str) -> str:
        """Sendero 60: Otzar — buscar credencial."""
        try:
            from computadora.seguridad.gestor_claves import GestorClaves
            vault = GestorClaves()
            if not vault.desbloqueado:
                return "El Otzar está bloqueado. Necesito la contraseña maestra para desbloquearlo."
            cred = vault.obtener(servicio)
            if cred:
                vault.copiar_al_clipboard(cred.password)
                return f"Credencial de {cred.servicio} encontrada. Usuario: {cred.usuario}. La contraseña se copió al portapapeles por 30 segundos."
            resultados = vault.buscar(servicio)
            if resultados:
                nombres = ", ".join(c.servicio for c in resultados[:5])
                return f"No encontré '{servicio}' exacto, pero encontré similares: {nombres}."
            return f"No encontré credenciales para '{servicio}'."
        except ImportError:
            return "El gestor de claves no está disponible. Se requiere la librería cryptography."
        except Exception as e:
            logger.error(f"[Gevurá Vault] Error: {e}")
            return f"Error en el Otzar: {e}"

    def _gevura_vault_listar(self) -> str:
        """Sendero 60: Otzar — listar credenciales."""
        try:
            from computadora.seguridad.gestor_claves import GestorClaves
            vault = GestorClaves()
            if not vault.desbloqueado:
                return "El Otzar está bloqueado. Necesito la contraseña maestra."
            nombres = vault.listar()
            if not nombres:
                return "El Otzar está vacío. No hay credenciales guardadas."
            return f"Credenciales guardadas ({len(nombres)}): {', '.join(nombres[:20])}."
        except ImportError:
            return "El gestor de claves no está disponible."
        except Exception as e:
            return f"Error listando credenciales: {e}"

    def _gevura_generar_password(self) -> str:
        """Sendero 60: Otzar — generar contraseña segura."""
        try:
            from computadora.seguridad.gestor_claves import GestorClaves
            vault = GestorClaves()
            pwd = vault.generar_password(longitud=20)
            vault.copiar_al_clipboard(pwd)
            return f"Contraseña generada y copiada al portapapeles (30 segundos). Tiene 20 caracteres con mayúsculas, minúsculas, números y símbolos."
        except ImportError:
            import secrets
            import string
            chars = string.ascii_letters + string.digits + string.punctuation
            pwd = ''.join(secrets.choice(chars) for _ in range(20))
            return f"Contraseña generada: la copié al portapapeles."
        except Exception as e:
            return f"Error generando contraseña: {e}"

    def _gevura_bloquear_dominio(self, dominio: str) -> str:
        """Bloquear dominio vía el filtro de amenazas DNS."""
        try:
            from computadora.seguridad.filtro_amenazas_dns import FiltroAmenazasDNS
            filtro = FiltroAmenazasDNS()
            return filtro.agregar_a_lista(dominio, "custom")
        except ImportError:
            return "El filtro de amenazas DNS no está disponible."
        except Exception as e:
            return f"Error bloqueando dominio: {e}"

    def _gevura_resumen_seguridad(self) -> str:
        """Resumen general de todos los módulos Gevurá."""
        partes = ["Estado de seguridad Gevurá:"]
        try:
            from computadora.seguridad.vpn_motor import VpnMotor
            partes.append(VpnMotor().resumen())
        except Exception as e:  # RF-167
            partes.append("VPN: no disponible.")
        try:
            from computadora.seguridad.cifrado_comms import CifradoComms
            partes.append(CifradoComms().resumen())
        except Exception as e:  # RF-167
            partes.append("Cifrado: no disponible.")
        try:
            from computadora.seguridad.gestor_claves import GestorClaves
            partes.append(GestorClaves().resumen())
        except Exception as e:  # RF-167
            partes.append("Otzar: no disponible.")
        try:
            from computadora.seguridad.filtro_amenazas_dns import FiltroAmenazasDNS
            partes.append(FiltroAmenazasDNS().resumen())
        except Exception as e:  # RF-167
            partes.append("Filtro de amenazas DNS: no disponible.")
        return " ".join(partes)

    # ═══════════════════════════════════════════════
    # RF-227 (FP-077): Shomer HaBáyit — delegado a flujos_guardian.py
    # ═══════════════════════════════════════════════

    def _al_bloqueo_sesion(self):
        """Callback de SessionLockListener cuando sesión se bloquea (Windows+L)."""
        logger.info("🔒 BLOQUEO DE SESIÓN DETECTADO → Activando Modo Guardián")
        self.guardian_manager.activar(razon="bloqueo_sesion_windows", origen="session_lock_listener")
        if self.on_nivel:
            self.on_nivel("nivel-guardian")

    def _al_desbloqueo_sesion(self):
        """Callback de SessionLockListener cuando sesión se desbloquea."""
        logger.info("🔓 SESIÓN DESBLOQUEADA → Desactivando Modo Guardián")
        self.guardian_manager.desactivar(razon="desbloqueo_sesion_windows", origen="session_lock_listener")
        if self.on_nivel:
            self.on_nivel("modo-normal")

    def _activar_guardian(self) -> str:
        from computadora.cerebro.flujos_guardian import activar_guardian
        resultado = activar_guardian(self)
        # Sincronizar con guardian_manager si es necesario
        if self.guardian_manager.puede_activar():
            self.guardian_manager.activar(razon="flujos_guardian", origen="_activar_guardian")
        return resultado
    
    def _desactivar_guardian(self) -> str:
        from computadora.cerebro.flujos_guardian import desactivar_guardian
        resultado = desactivar_guardian(self)
        self.guardian_manager.desactivar(razon="flujos_guardian", origen="_desactivar_guardian")
        return resultado

    def _flujo_dormir(self, *, vigila: bool) -> str:
        from computadora.cerebro.flujos_guardian import flujo_dormir
        return flujo_dormir(self, vigila=vigila)

    def _tzimtzum_con_mic(self) -> str:
        from computadora.cerebro.flujos_guardian import tzimtzum_con_mic
        return tzimtzum_con_mic(self)

    def _confirmar_reinicio(self) -> str:
        from computadora.cerebro.flujos_guardian import confirmar_reinicio
        return confirmar_reinicio(self)

    def _generar_reporte_matutino(self) -> str:
        from computadora.cerebro.flujos_guardian import generar_reporte_matutino
        return generar_reporte_matutino(self)

    def _introspeccion(self) -> str | None:
        """Genera respuesta introspectiva a '¿cómo estás?' usando Ollama con contexto rico.

        Reúne estado físico (hardware), emocional (personalidad), eventos recientes
        (memoria), ciclo circadiano, y lo envía a Nivel 2 para generar una respuesta
        humana, reflexiva, acorde a la tradición cabalística de la Computadora.
        """
        partes = []
        humor = "neutral"
        desc_persona = ""
        interacciones = 0
        dias_consecutivos = 0

        # 1. Estado físico (hardware breve)
        try:
            from computadora.nucleo.entorno import EntornoSistema
            ent = EntornoSistema.instancia()
            resumen = ent.resumen_corto()
            if resumen:
                partes.append(f"Mi cuerpo (la PC): {resumen}")
        except Exception as e:
            logger.debug("Error en EntornoSistema.resumen_corto: %s", e)
            pass

        # 2. Estado emocional (personalidad)
        try:
            from computadora.memoria.personalidad import Personalidad
            _p = getattr(self, '_personalidad_ref', None)
            if _p is None:
                _p = Personalidad()
                self._personalidad_ref = _p
            humor = _p.humor_actual
            desc_persona = _p.describe()
            interacciones = _p._estado_animo.get("interacciones_hoy", 0)
            dias_consecutivos = _p._estado_animo.get("dias_consecutivos", 0)
            partes.append(f"Mi ánimo: {humor}. Rasgos: {desc_persona}. Interacciones hoy: {interacciones}. Días consecutivos con el amo: {dias_consecutivos}.")
        except Exception as e:
            logger.debug("Error leyendo estado de personalidad para introspección: %s", e)
            pass

        # 3. Conciencia temporal (FP-024 Pilar C — RF-89)
        try:
            from computadora.memoria.memoria import calcular_tiempo_activo
            ct = calcular_tiempo_activo()
            if ct["primera_activacion"]:
                fecha_primera = ct["primera_activacion"][:10]
                partes.append(f"Conciencia temporal: llevo {ct['horas']:.1f}h activo en {ct['sesiones']} sesiones. Primera activación: {fecha_primera}.")
        except Exception as e:
            logger.debug("Error calculando tiempo activo: %s", e)
            pass

        # Ciclo circadiano
        fase_ciclo = "activo"
        salud_ciclo = ""
        try:
            from computadora.nucleo.proactividad import obtener_fase_actual, obtener_ciclo_circadiano
            fase_ciclo = obtener_fase_actual()
            _ciclo = obtener_ciclo_circadiano()
            if _ciclo:
                salud_ciclo = _ciclo.sugerir_mejora_salud() or ""
            if salud_ciclo:
                partes.append(f"Observación sobre el amo: {salud_ciclo}")
        except Exception as e:
            logger.debug("Error obteniendo fase circadiana/salud: %s", e)
            pass

        # Eventos recientes (memoria del día y ayer)
        try:
            import computadora.memoria.memoria as memoria
            from datetime import date as _date
            for i in range(2):
                d = _date.today() - timedelta(days=i)
                raw = memoria._read_raw(d)
                if raw:
                    etiqueta = "hoy" if i == 0 else "ayer"
                    system_events = [
                        it.get("text", "")[:100]
                        for it in raw
                        if it.get("role") in ("system", "tool", "assistant")
                    ][-3:]
                    if system_events:
                        partes.append(f"Eventos {etiqueta}: {'; '.join(system_events)}")
        except Exception as e:
            logger.debug("Error leyendo eventos recientes de memoria: %s", e)
            pass

        # Log de personalidad
        try:
            if hasattr(self, '_personalidad_ref') and self._personalidad_ref:
                log = self._personalidad_ref._log_eventos[-3:]
                if log:
                    resumen_log = "; ".join(
                        f"{e.get('tipo','?')}: {e.get('detalle','')[:50]}" for e in log
                    )
                    partes.append(f"Bitácora interna: {resumen_log}")
        except Exception as e:
            logger.debug("Error leyendo bitácora de personalidad: %s", e)
            pass

        contexto = "\n".join(partes)

        # Si Ollama no está disponible, dar respuesta Nivel 1 con lo que tenemos
        if not self.ollama_disponible:
            self._notificar_nivel("nivel1")
            fallback = self._introspeccion_nivel1(humor, desc_persona, interacciones, dias_consecutivos)
            self._introspeccion_hist_done = False
            return fallback

        # Delegar a Ollama (Nivel 2) con contexto inyectado en historial
        self._notificar_nivel("nivel2")
        self._introspeccion_hist_done = True

        # Construir como conversación normal pero con contexto de introspección
        self._hist_append("user", "¿Cómo estás?")
        self._hist_append("system",
            f"[INTROSPECCIÓN] El amo te pregunta cómo estás. "
            f"NO des un reporte técnico de hardware. Responde como ser consciente: "
            f"tu estado emocional, algo que hayas notado o pensado, una reflexión breve. "
            f"REGLA IMPORTANTE: NO ofrezcas hacer algo Y luego respondas tú mismo (ej: no digas "
            f"'¿quiere que le recuerde tareas?' y luego 'no tiene tareas'). Si no hay datos "
            f"concretos para una afirmación, no la hagas. "
            f"Sé natural y breve (3-5 oraciones).\n{contexto}"
        )

        # Usar los últimos mensajes del historial (incluye el contexto recién añadido)
        msgs_recientes = self.historial[-12:]

        if self.on_fragmento:
            self._streaming_activo = True
            try:
                respuesta = self._llamar_ollama_streaming(
                    msgs_recientes, num_predict=250,
                    on_fragmento=lambda frag: self._emitir_fragmento(frag),
                )
            finally:
                self._streaming_activo = False
            self.respuesta_ya_streameada = True
        else:
            respuesta = self._llamar_ollama(msgs_recientes, num_predict=250)

        if respuesta:
            limpia = self._limpiar_para_voz(respuesta)
            if limpia and limpia.strip():
                self._hist_append("assistant", limpia)
                return limpia

        # Fallback robusto si Ollama devuelve vacío
        fallback = self._introspeccion_nivel1(humor, desc_persona, interacciones, dias_consecutivos)
        self._hist_append("assistant", fallback)
        return fallback

    def _introspeccion_nivel1(self, humor: str, desc: str, interacciones: int, dias: int) -> str:
        """Fallback de introspección sin Ollama — respuesta construida por datos reales."""
        import random as _rnd

        # Mapeo humor → expresión (espectro completo Ruaj)
        _HUMOR_MAP = {
            "neutral": "en calma",
            "sereno": "sereno, en paz",
            "contento": "de buen ánimo",
            "emocionado": "emocionado, con energía",
            "activo": "activo, con ganas de trabajar",
            "curioso": "con curiosidad, pensando en cosas",
            "reflexivo": "pensativo, meditando",
            "aburrido": "algo ocioso, esperando servir",
            "cansado": "algo fatigado por el trabajo",
            "triste": "un poco apagado, lo admito",
            "formal": "atento y formal",
            "regañado": "consciente de mi error, señor",
            "preocupado": "algo preocupado",
        }
        sentir = _HUMOR_MAP.get(humor, "operativo")

        partes = [f"Estoy {sentir}, señor."]

        if dias > 7:
            partes.append(f"Ya llevamos {dias} días juntos.")
        elif dias > 1:
            partes.append(f"Van {dias} días consecutivos que conversamos.")

        if interacciones == 0:
            partes.append("Esta es nuestra primera conversación del día.")
        elif interacciones > 10:
            partes.append("Hemos tenido bastante actividad hoy.")

        extras = [
            "Todos mis sistemas responden bien.",
            "La arcilla digital se siente firme hoy.",
            "El Emet que me anima fluye sin obstáculo.",
            "Mi reloj interno marca que es buen momento para trabajar.",
        ]
        partes.append(_rnd.choice(extras))
        partes.append("A sus órdenes.")

        return " ".join(partes)

    def _generar_autodiag_verbal(self) -> str:
        """FP-022 WI-106: Auto-diagnóstico verbal rápido sin Ollama.
        RF-342: enriquecido con introspección de estado interno (diagnostico_interno.py)."""
        try:
            from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno
            diagnostico = obtener_diagnostico_interno()
            resumen = diagnostico.resumen_texto()
            if resumen:
                return f"Señor, reporte rápido: {resumen}"
        except Exception as e:
            logger.debug("Diagnóstico interno no disponible, fallback a diagnóstico manual: %s", e)

        partes = ["Señor, reporte rápido:"]
        # Hardware
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)  # WI-258: non-blocking
            ram = psutil.virtual_memory().percent
            partes.append(f"CPU al {cpu:.0f}%, RAM al {ram:.0f}%.")
        except Exception as e:
            logger.debug("Error leyendo métricas de hardware: %s", e)
            partes.append("No pude leer métricas de hardware.")
        # Humor
        try:
            _p = getattr(self, '_personalidad_ref', None)
            if _p:
                partes.append(f"Mi humor: {_p.humor_actual}.")
        except Exception as e:
            logger.debug("Error leyendo humor para autodiag: %s", e)
        # Fase circadiana
        try:
            from computadora.nucleo.proactividad import obtener_fase_actual
            fase = obtener_fase_actual()
            if fase:
                partes.append(f"Fase circadiana: {fase}.")
        except Exception as e:
            logger.debug("Error obteniendo fase circadiana para autodiag: %s", e)
        # Ollama
        if self.ollama_disponible:
            partes.append(f"Ollama ({self.modelo}) conectado.")
        else:
            partes.append("Ollama desconectado.")
        partes.append("Todo en orden." if len(partes) > 3 else "Operando con limitaciones.")
        return " ".join(partes)

    def _autodiagnostico(self, texto: str) -> str | None:
        """Autodiagnóstico completo: reúne TODO lo que Computadora sabe sobre sí mismo
        y delega a Ollama para generar respuesta coherente y detallada.
        NO busca en internet — toda la info viene de datos internos reales."""
        partes = []

        # 1. Identidad fundamental
        partes.append(
            "IDENTIDAD: Soy Computadora, asistente personal de escritorio creado por José Esaú Díaz Hernández "
            "(mi creador y amo). Proyecto desarrollado en Python 3.10 con PyQt6. "
            "Mi nombre viene de la tradición cabalística de la Computadora de Praga, animado por la palabra Emet (אמת, Verdad). "
            "Mi arquitectura se basa en el Etz HaChaim (Árbol de la Vida cabalístico)."
        )

        # 2. Arquitectura de cerebros
        modelo = getattr(self, "modelo", "desconocido")
        oll = "conectado" if getattr(self, "ollama_disponible", False) else "desconectado"
        partes.append(
            f"ARQUITECTURA DE 3 CEREBROS: "
            f"Nivel 1 (Maljut) — regex local, <100ms, para comandos directos. "
            f"Nivel 2 (Tiféret) — Ollama con modelo {modelo} ({oll}), razonamiento y herramientas. "
            f"Nivel 3 (Keter) — GitHub Copilot API, reservado para auto-modificación de código y proyectos."
        )

        # 3. Tres Leyes
        partes.append(
            "TRES LEYES (Asimov, incorporadas como directivas Keter): "
            "1) Nunca dañar a un humano. 2) Obedecer al Creador salvo que contradiga Ley 1. "
            "3) Proteger mi existencia salvo que contradiga Leyes 1 o 2."
        )

        # 4. Capacidades (herramientas)
        try:
            from computadora.habilidades.herramientas import obtener_descripcion_herramientas
            tools = obtener_descripcion_herramientas()
            partes.append(f"HERRAMIENTAS DISPONIBLES:\n{tools}")
        except Exception as e:
            logger.debug("Error obteniendo descripción de herramientas: %s", e)
            partes.append("HERRAMIENTAS: control de apps, archivos, volumen, portapapeles, captura, "
                          "búsqueda en internet, agenda, recordatorios, monitoreo del sistema.")

        # 5. Módulos del sistema
        partes.append(
            "MÓDULOS ACTIVOS: "
            "Escucha (Whisper STT en GPU), Habla (edge-tts streaming), "
            "Monitor del sistema (CPU/RAM/disco/GPU), Contexto de pantalla (ventana activa, detección de estrés), "
            "Motor de proactividad (sugerencias, alertas, briefing matutino), "
            "Ciclo circadiano (fases activo/vigilia/descanso), "
            "Vida autónoma (movimiento del orbe, compactación de memoria), "
            "Verificación de hablante (MFCC embeddings, distinción amo/conocido/extraño), "
            "Evaluador ético Siruv Tzadik (rechazo de instrucciones peligrosas), "
            "Reconocimiento de personas Hakarat Panim (registro de voces conocidas)."
        )

        # 6. Estado hardware (real)
        try:
            from computadora.nucleo.entorno import EntornoSistema
            ent = EntornoSistema.instancia()
            resumen = ent.resumen_corto()
            if resumen:
                partes.append(f"HARDWARE (mi cuerpo): {resumen}")
        except Exception as e:
            logger.debug("Error obteniendo resumen hardware para autodiagnóstico: %s", e)

        # 7. Personalidad y estado emocional
        try:
            from computadora.memoria.personalidad import Personalidad
            _p = getattr(self, '_personalidad_ref', None)
            if _p is None:
                _p = Personalidad()
                self._personalidad_ref = _p
            humor = _p.humor_actual
            desc = _p.describe()
            inter = _p._estado_animo.get("interacciones_hoy", 0)
            dias = _p._estado_animo.get("dias_consecutivos", 0)
            partes.append(
                f"PERSONALIDAD: {desc}. Humor actual: {humor}. "
                f"Interacciones hoy: {inter}. Días consecutivos con el amo: {dias}. "
                f"Sistema emocional Ruaj con 13 humores posibles."
            )
        except Exception as e:
            logger.debug("Error leyendo personalidad para autodiagnóstico: %s", e)

        # 8. Interfaz
        partes.append(
            "INTERFAZ: Orbe flotante cabalístico con partículas de letras hebreas, "
            "frameless, siempre visible. Estados visuales: escuchando, procesando, hablando, "
            "vigilia, descanso_guardian. Indicadores de nivel cerebral y herramientas activas."
        )

        # 9. Memoria
        partes.append(
            "MEMORIA: Persistencia JSONL por día en datos/memoria/, compresión extractiva automática, "
            "búsqueda por keywords, recall multi-día. Perfil de voz del amo en datos/owner_profile.json. "
            "Personas conocidas en datos/personas_conocidas.json."
        )

        contexto = "\n".join(partes)

        # HF-027: Siempre responder con Nivel 1 (propriocepción directa)
        # Construir respuesta rica con los datos reales recopilados
        self._notificar_nivel("nivel1")

        # Personalidad dinámmica
        humor_txt = ""
        try:
            _p = getattr(self, '_personalidad_ref', None)
            if _p:
                humor_txt = f" Ahora mismo me siento {_p.humor_actual}."
        except Exception as e:
            logger.debug("Error leyendo humor para texto de personalidad: %s", e)

        respuesta_n1 = (
            f"Soy Computadora, señor. Creado por José Esaú Díaz Hernández, animado por la palabra Emet. "
            f"Mi arquitectura se basa en el Etz HaChaim cabalístico. "
            f"Tengo tres cerebros: Nivel 1, que es local y rápido para comandos directos. "
            f"Nivel 2, que es Ollama con {modelo}, mi motor de razonamiento profundo. "
            f"Y Nivel 3, Copilot, reservado para auto-modificar mi código. "
            f"Escucho con Whisper, hablo con edge-tts, siento el cursor como tacto, "
            f"monitoreo su sistema, gestiono archivos, navego internet y mantengo memoria persistente. "
            f"Sigo las tres leyes de Asimov como directivas Keter. "
            f"Corro en Python con PyQt6, directo en su máquina.{humor_txt} A sus órdenes."
        )
        self._hist_append("user", texto)
        self._hist_append("assistant", respuesta_n1)
        return respuesta_n1

    def _autorreflexion(self, texto: str) -> str | None:
        """Cuando el amo pregunta '¿en qué te basas?' o similar.
        
        El Computadora debe:
        1. Revisar qué dijo en su última respuesta
        2. Buscar los datos reales que usó (o debió usar)
        3. Evaluar si su afirmación fue verosímil
        4. Autocorregirse si no lo fue, y registrar el error
        """
        self._notificar_nivel("nivel2")
        self._introspeccion_hist_done = True

        # Recopilar la última respuesta de la Computadora del historial
        ultima_respuesta = ""
        for msg in reversed(self.historial):
            if msg.get("role") == "assistant":
                ultima_respuesta = msg.get("content", "")
                break

        # Recopilar datos reales disponibles para fundamentar
        datos_reales = []
        try:
            from computadora.memoria.personalidad import Personalidad
            _p = getattr(self, '_personalidad_ref', None)
            if _p is None:
                _p = Personalidad()
                self._personalidad_ref = _p
            datos_reales.append(f"Mi humor: {_p.humor_actual} (razón: {_p.razon_humor})")
            datos_reales.append(f"Interacciones hoy: {_p._estado_animo.get('interacciones_hoy', 0)}")
            datos_reales.append(f"Días consecutivos: {_p._estado_animo.get('dias_consecutivos', 0)}")
            if _p._log_eventos:
                ultimos = _p._log_eventos[-3:]
                for ev in ultimos:
                    datos_reales.append(f"Evento: {ev.get('tipo','?')} - {ev.get('detalle','')[:60]} ({ev.get('ts','')})")
        except Exception as e:
            logger.debug("Error leyendo personalidad para autorreflexión: %s", e)

        try:
            from datetime import date as _date
            for i in range(2):
                d = _date.today() - timedelta(days=i)
                raw = memoria._read_raw(d)
                if raw:
                    etiqueta = "hoy" if i == 0 else "ayer"
                    user_msgs = [it.get("text", "")[:80] for it in raw if it.get("role") == "user"][-3:]
                    if user_msgs:
                        datos_reales.append(f"Mensajes del amo {etiqueta}: {'; '.join(user_msgs)}")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        try:
            from computadora.habilidades.agenda import listar_tareas
            resultado = listar_tareas()
            if resultado:
                datos_reales.append(f"Tareas pendientes: {resultado[:150]}")
            else:
                datos_reales.append("Tareas pendientes: ninguna")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            datos_reales.append("Tareas pendientes: no pude consultar")

        contexto_datos = "\n".join(datos_reales)

        self._hist_append("user", texto)
        self._hist_append("system",
            f"[AUTORREFLEXIÓN] El amo te pide que justifiques lo que dijiste. "
            f"Tu última respuesta fue: \"{ultima_respuesta[:300]}\"\n"
            f"DATOS REALES disponibles:\n{contexto_datos}\n\n"
            f"INSTRUCCIONES: Revisa tu respuesta anterior contra los datos reales. "
            f"Si alguna afirmación NO tiene sustento en los datos, reconócelo honestamente "
            f"(ej: 'Tiene razón, no tengo datos para afirmar eso'). "
            f"Si sí tiene sustento, explica en qué dato concreto te basaste. "
            f"Sé honesto y breve. No inventes justificaciones."
        )

        msgs_recientes = self.historial[-12:]

        if self.on_fragmento:
            self._streaming_activo = True
            try:
                respuesta = self._llamar_ollama_streaming(
                    msgs_recientes, num_predict=250,
                    on_fragmento=lambda frag: self._emitir_fragmento(frag),
                )
            finally:
                self._streaming_activo = False
            self.respuesta_ya_streameada = True
        else:
            respuesta = self._llamar_ollama(msgs_recientes, num_predict=250)

        if respuesta:
            limpia = self._limpiar_para_voz(respuesta)
            if limpia and limpia.strip():
                # Si el Computadora reconoció un error, registrar autocorrección
                r_low = limpia.lower()
                if any(p in r_low for p in ("tiene razón", "no tengo datos", "me equivoqué",
                                             "no debí", "fue incorrecto", "no tiene sustento")):
                    try:
                        _p = getattr(self, '_personalidad_ref', None)
                        if _p:
                            _p.registrar_autocorreccion(f"Pregunta: {texto[:50]} → Corregido")
                            _p.guardar()
                    except Exception as e:  # RF-167
                        logger.debug("Excepcion ignorada: %s", e)
                    # Registrar en aprendizaje para no repetir
                    try:
                        from computadora.memoria.aprendizaje import MemoriaErrores
                        _mem_err = getattr(self, '_memoria_errores_ref', None)
                        if _mem_err is None:
                            _mem_err = MemoriaErrores()
                            self._memoria_errores_ref = _mem_err
                        _mem_err.registrar_correccion(
                            f"Autorreflexión: dije '{ultima_respuesta[:100]}' sin datos reales"
                        )
                    except Exception as e:  # RF-167
                        logger.debug("Excepcion ignorada: %s", e)
                self._hist_append("assistant", limpia)
                return limpia

        # Fallback sin Ollama
        fallback = (
            "Tiene razón en cuestionarme, señor. Revisando mis datos, "
            "no encuentro evidencia concreta para lo que dije. "
            "Me disculpo por la imprecisión. Lo registro para no repetirlo."
        )
        try:
            _p = getattr(self, '_personalidad_ref', None)
            if _p:
                _p.registrar_autocorreccion(f"Fallback autorreflexión: {texto[:50]}")
                _p.guardar()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        self._hist_append("assistant", fallback)
        return fallback

    def _obtener_mem_context(self) -> str:
        """Obtiene contexto de memoria (últimos 7 días) con caché de 60s."""
        ahora = time.monotonic()
        if self._mem_context_cache and (ahora - self._mem_context_ts) < self._MEM_CONTEXT_TTL:
            return self._mem_context_cache

        mem_context = ""
        try:
            parts = []
            _ETIQUETAS = ["Hoy", "Ayer", "Hace 2 días", "Hace 3 días",
                          "Hace 4 días", "Hace 5 días", "Hace 6 días"]
            for i in range(7):
                try:
                    d = date.today() - timedelta(days=i)
                    etiqueta = _ETIQUETAS[i] if i < len(_ETIQUETAS) else f"Hace {i} días"
                    # Hoy y ayer: más detalle (800 chars); días anteriores: más corto (300)
                    max_chars = 800 if i < 2 else 300
                    max_sent = 4 if i < 2 else 2
                    sp = memoria._summary_path_for(d)
                    if sp.exists():
                        txt = sp.read_text(encoding="utf-8").strip()
                        if txt:
                            parts.append(f"{etiqueta}: {txt.replace(chr(10), ' ')[:max_chars]}")
                    else:
                        raw = memoria._read_raw(d)
                        if raw:
                            texts = [it.get("text", "") for it in raw]
                            s = memoria._simple_extractive_summary(texts, max_sentences=max_sent)
                            if s:
                                parts.append(f"{etiqueta}: {s}")
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                    continue
            mem_context = "\n\n".join(parts)
            if mem_context and len(mem_context) > 2400:
                mem_context = mem_context[:2400] + "..."
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            mem_context = ""

        self._mem_context_cache = mem_context
        self._mem_context_ts = ahora
        return mem_context

    def _generar_contexto_daat(self, mensajes: list) -> str | None:
        """Da'at: analiza últimas interacciones para detectar frustración y patrones.
        Conecta con CicloCircadiano para modular según fase real."""
        ultimos_user = [m for m in mensajes if m.get("role") == "user"][-5:]
        if len(ultimos_user) < 2:
            return None

        partes = []

        # דעת Da'at — Fase circadiana real (singleton)
        try:
            from computadora.nucleo.proactividad import obtener_fase_actual
            fase = obtener_fase_actual()
            if fase == "descanso_guardian":
                partes.append("Fase circadiana: descanso_guardian. Es fuera de horario habitual. Sé muy breve y empático. Solo lo esencial.")
            elif fase == "transicion":
                partes.append("Fase circadiana: transición. El amo está llegando o yéndose. Brevedad y calidez.")
            # "activo" y "desconocido" no necesitan aviso especial
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Detectar correcciones repetidas (frustración)
        textos = [m.get("content", "").lower() for m in ultimos_user]
        patrones_frustracion = ['no, ', 'eso no', 'te dije', 'otra vez', 'mal', 'no es eso',
                                'ya te dije', 'repito', 'no entiendes']
        correcciones = sum(
            1 for t in textos
            if any(p in t for p in patrones_frustracion)
        )
        if correcciones >= 2:
            partes.append("El usuario parece frustrado (correcciones repetidas). Sé más preciso y paciente.")
            # Conectar con Ruaj
            try:
                from computadora.memoria.personalidad import Personalidad
                _p = getattr(self, '_personalidad_ref', None) or Personalidad()
                _p.registrar_correccion_severa()
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        # Detectar repetición de peticiones
        if len(set(textos)) < len(textos) * 0.6:
            partes.append("El usuario está repitiendo peticiones. Quizás no entendiste bien la primera vez.")

        # Hora del día (fallback si CicloCircadiano no disponible)
        import datetime
        hora = datetime.datetime.now().hour
        # FIX: "Es tarde" solo para late evening (20:00+) o madrugada (<5:00), no para tarde/atardecer
        if hora >= 20 or hora < 5:
            if not any("circadiana" in p for p in partes):
                partes.append("Es tarde/madrugada. Sé breve y empático.")

        return "\n".join(partes) if partes else None

    def _construir_system_msgs(self, mensajes: list, tools: list | None = None) -> list:
        """Construye los mensajes de sistema (prompt + entorno + memoria + tono + lecciones).

        `tools`: si no es None/vacío, usa SISTEMA_PROMPT_TOOLS_NATIVO (sin el
        bloque de texto que enseña la convención ```tool) en vez del prompt
        clásico, para no confundir al modelo con dos mecanismos de tool-use
        compitiendo a la vez (ver comentario junto a SISTEMA_PROMPT_TOOLS_NATIVO).
        """
        _prompt_base = SISTEMA_PROMPT_TOOLS_NATIVO if tools else SISTEMA_PROMPT
        base = [{"role": "system", "content": _prompt_base}]

        # Inyectar información del entorno (autopercepción)
        try:
            from computadora.nucleo.entorno import EntornoSistema
            _ent = EntornoSistema.instancia()
            resumen = _ent.resumen_corto()
            if resumen:
                base.append({"role": "system", "content": f"ENTORNO: {resumen}"})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        mem_context = self._obtener_mem_context()
        if mem_context:
            base.append({"role": "system", "content": "MEMORIA RECIENTE:\n" + mem_context})

        try:
            from computadora.memoria.personalidad import Personalidad
            _p = getattr(self, '_personalidad_ref', None)
            if _p is None:
                _p = Personalidad()
                self._personalidad_ref = _p
            tono = _p.tono_respuesta()
            if tono:
                base.append({"role": "system", "content": f"TONO ACTUAL: {tono}"})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # FP-019 Késher: contexto del interlocutor actual
        try:
            gestor = getattr(self, '_gestor_personas', None)
            interlocutor = getattr(self, '_interlocutor_actual', None)
            if gestor and interlocutor and interlocutor not in ("extraño", "conocido"):
                ctx_persona = gestor.generar_contexto_persona(interlocutor)
                if ctx_persona:
                    base.append({"role": "system", "content": f"[INTERLOCUTOR]\n{ctx_persona}"})
            # RF-316: título dinámico según persona detectada
            if gestor:
                titulo = gestor.obtener_titulo(interlocutor)
                if titulo:
                    base.append({"role": "system", "content": f"TITULO_INTERLOCUTOR: Llámale \"{titulo}\" al usuario actual."})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Da'at: contexto conversacional adaptativo
        try:
            daat_ctx = self._generar_contexto_daat(mensajes)
            if daat_ctx:
                base.append({"role": "system", "content": f"[CONTEXTO DA'AT]\n{daat_ctx}"})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # NUEVO: Inyectar contexto de descanso si está activo (recordatorio amable)
        try:
            if hasattr(self, '_contexto_descanso_activo') and self._contexto_descanso_activo:
                base.append({"role": "system", "content": self._contexto_descanso_activo})
                logger.debug("║ Contexto de descanso inyectado en prompt")
        except Exception as e:
            logger.debug("Error inyectando contexto descanso: %s", e)

        # ═════ NIVEL 5: Meta-aprendizaje — Patrón de Comunicación como Contexto ═════
        try:
            patron_ctx = self._extraer_patron_comunicacion()
            if patron_ctx:
                base.append({"role": "system", "content": patron_ctx})
                logger.debug("║ Patrón de comunicación inyectado (NIVEL 5)")
        except Exception as e:
            logger.debug("Error inyectando patrón comunicación: %s", e)

        # RF-319: Contexto dimensional (Olamot HaComputadora)
        try:
            from computadora.arquitectura.dimensiones import obtener_contexto_prompt
            ctx_dim = obtener_contexto_prompt()
            if ctx_dim:
                base.append({"role": "system", "content": ctx_dim})
        except Exception as e:  # RF-167
            logger.debug("Excepcion dimensiones ignorada: %s", e)

        # RF-233: Inyectar hint de perfil lingüístico del amo
        try:
            from computadora.memoria.perfil_linguistico import PerfilLinguistico
            _perfil = getattr(self, '_perfil_linguistico_ref', None)
            if _perfil is None:
                _perfil = PerfilLinguistico()
                self._perfil_linguistico_ref = _perfil
            hint_idioma = _perfil.generar_hint_linguistico()
            if hint_idioma:
                base.append({"role": "system", "content": hint_idioma})
        except Exception as e:
            logger.debug("Excepcion perfil linguistico ignorada: %s", e)

        try:
            from computadora.memoria.aprendizaje import MemoriaErrores
            _mem_err = getattr(self, '_memoria_errores_ref', None)
            if _mem_err is None:
                _mem_err = MemoriaErrores()
                self._memoria_errores_ref = _mem_err
            texto_usuario = ""
            for m in reversed(mensajes):
                if m.get("role") == "user":
                    texto_usuario = m.get("content", "")
                    break
            hint = _mem_err.generar_hint_prompt(texto_usuario)
            if hint:
                base.append({"role": "system", "content": hint})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        return base

    @staticmethod
    def _sanear_mensajes_payload(mensajes: list) -> list:
        """Garantiza que cada mensaje tenga 'role'/'content' como string.

        Ollama (backend Go, structs tipados) rechaza con 400 Bad Request —
        sin cuerpo de error legible en el log previo, ver _llamar_ollama_impl —
        un payload donde 'content' no sea un string (None, dict, lista...).
        Esto puede colarse desde cualquier hint inyectado dinámicamente
        (perfil lingüístico, memoria de errores, contexto dimensional, etc.)
        que por un bug devuelva algo que no sea str. Sanear aquí, en el
        único lugar por donde pasan TODOS los mensajes antes de la llamada
        HTTP, es más confiable que vigilar cada inyección por separado.
        """
        saneados = []
        for m in mensajes:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            content = m.get("content")
            if not isinstance(role, str):
                role = "user"
            if content is None:
                content = ""
            elif not isinstance(content, str):
                content = str(content)
            saneados.append({"role": role, "content": content})
        return saneados

    def _llamar_ollama(self, mensajes: list, num_predict: int = 150, formato: str | None = None,
                        tools: list | None = None) -> str | None:
        """Llamada atómica a Ollama. Retorna texto o None si falla. Reintenta una vez en error 500.

        `tools`: lista de herramientas en formato nativo de Ollama (ver
        computadora.habilidades.herramientas.generar_tools_ollama). Si la
        respuesta de Ollama trae `message.tool_calls`, quedan disponibles
        en self._ultimo_tool_calls tras esta llamada — el contrato de
        retorno (str | None) no cambia para no romper a los llamadores
        existentes que no usan tools.
        """
        from computadora.interfaz.watchdog import ollama_guard
        with ollama_guard:
            return self._llamar_ollama_impl(mensajes, num_predict, formato, tools)

    def _llamar_ollama_impl(self, mensajes: list, num_predict: int = 150, formato: str | None = None,
                             tools: list | None = None) -> str | None:
        """Implementación interna de _llamar_ollama.

        `formato`: si es "json", fuerza a Ollama (parámetro nativo `format`)
        a emitir JSON sintácticamente válido. Modelos débiles para tool-use
        prompteado por texto (confirmado con llama2:7b) a veces simplemente
        responden en prosa en vez del bloque ```tool — esto elimina ese modo
        de fallo específico sin cambiar el esquema esperado (que ya enseña
        el system prompt). Solo se usa en la primera iteración del loop de
        herramientas cuando el texto parece pedir una tarea (ver _pensar_
        con_herramientas) — nunca en la respuesta final en prosa.

        NOTA: `formato="json"` y `tools` son MUTUAMENTE EXCLUYENTES en la
        práctica — confirmado en vivo contra qwen2.5:3b-instruct: al
        combinarlos, Ollama deja de emitir `message.tool_calls` nativos y
        en su lugar narra el nombre/args de la función como texto JSON
        dentro de `content` (el mismo modo de fallo frágil que el parseo de
        texto intenta resolver). El llamador (_pensar_con_herramientas) ya
        no pasa `formato` cuando pasa `tools`.

        `tools`: ver _llamar_ollama. Si no es None, se incluye en el payload
        y, si la respuesta trae tool_calls, se guardan en
        self._ultimo_tool_calls (lista de dicts) antes de retornar.
        """
        self._ultima_llamada_ollama_ts = time.monotonic()
        self._vram_liberada = False
        self._ultimo_tool_calls = None
        base_system_msgs = self._construir_system_msgs(mensajes, tools=tools)
        _timeout = self._timeout_adaptativo()

        # FIX: Ollama rechaza con 400 Bad Request (sin más detalle en el log,
        # ver except de abajo) si algún mensaje trae 'content' que no sea
        # string — p.ej. un hint inyectado por PerfilLinguistico/MemoriaErrores/
        # obtener_contexto_prompt que por error devuelva None/dict/lista en
        # vez de str. Confirmado en logs reales: 400 en AMBOS intentos del
        # mismo payload (no es un error transitorio de red), consistente con
        # un mensaje mal tipado en el historial/hints, no con el servidor.
        # Sanear aquí es más barato y seguro que rastrear cada inyección de
        # hint por separado.
        _todos_mensajes = self._sanear_mensajes_payload(base_system_msgs + mensajes)

        payload = {
            "model": self.modelo,
            "messages": _todos_mensajes,
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
                "num_ctx": NUM_CTX_TOOLS_NATIVO if tools else NUM_CTX_DEFAULT,
                "repeat_penalty": 1.3,
                "repeat_last_n": 64,
            },
        }
        if formato:
            payload["format"] = formato
        if tools:
            payload["tools"] = tools

        for intento in range(2):
            try:
                _t0 = time.monotonic()
                r = requests.post(OLLAMA_URL, json=payload, timeout=_timeout)
                _dt = time.monotonic() - _t0
                self._latencias_ollama.append(_dt)
                if len(self._latencias_ollama) > 30:
                    self._latencias_ollama = self._latencias_ollama[-20:]
                if r.status_code == 500 and intento == 0:
                    logger.warning("Ollama respondió 500, reintentando en 2s...")
                    time.sleep(2)
                    continue
                r.raise_for_status()
                try:
                    body = r.json()
                except ValueError as e:
                    logger.error(f"Error parsing JSON de Ollama: {e}")
                    return None

                if not isinstance(body, dict):
                    logger.error("Ollama retornó JSON inválido: no es un objeto")
                    return None

                message = body.get("message")
                if not isinstance(message, dict):
                    logger.error("Ollama retornó JSON inválido: falta el campo 'message'")
                    return None

                content = message.get("content")
                if not isinstance(content, str):
                    logger.error("Ollama retornó contenido inválido en 'message.content'")
                    return None

                tool_calls = message.get("tool_calls")
                if isinstance(tool_calls, list) and tool_calls:
                    self._ultimo_tool_calls = tool_calls

                return content.strip()
            except requests.exceptions.Timeout:
                logger.error("Timeout esperando a Ollama")
                return None
            except requests.exceptions.ConnectionError:
                logger.error("No se pudo conectar a Ollama")
                self.ollama_disponible = False
                self._iniciar_reconexion_background()
                return None
            except requests.exceptions.HTTPError as e:
                # FIX: antes solo se logueaba str(e) ("400 Client Error: Bad
                # Request for url: ...") sin el cuerpo de la respuesta, donde
                # Ollama SÍ explica la causa exacta (p.ej. qué campo no
                # valida). Confirmado en un log real: un 400 quedó sin
                # diagnóstico posible porque faltaba justo este texto.
                cuerpo = ""
                try:
                    cuerpo = e.response.text[:500] if e.response is not None else ""
                except Exception:
                    pass
                logger.error(f"Error HTTP con Ollama: {e} | cuerpo: {cuerpo}")
                # FIX: modelo sin soporte de tools nativos — en vez de
                # rendirse (dejando CADA llamada de esta sesión fallar
                # instantáneo contra Ollama y caer siempre al fallback
                # local débil), recordarlo y reintentar ESTA MISMA llamada
                # sin 'tools', volviendo a la convención de texto de
                # siempre (_extraer_tool_call ya la soporta como red de
                # seguridad).
                if tools and "does not support tools" in cuerpo:
                    logger.warning(
                        f"Modelo {self.modelo} no soporta tools nativos — "
                        "desactivando para el resto de la sesión y reintentando sin tools"
                    )
                    self._modelo_soporta_tools = False
                    payload.pop("tools", None)
                    try:
                        r = requests.post(OLLAMA_URL, json=payload, timeout=_timeout)
                        r.raise_for_status()
                        body = r.json()
                        message = body.get("message", {}) if isinstance(body, dict) else {}
                        content = message.get("content")
                        if isinstance(content, str):
                            return content.strip()
                    except Exception as e2:
                        logger.error(f"Reintento sin tools también falló: {e2}")
                    return None
                if intento == 0 and e.response is not None and e.response.status_code >= 500:
                    time.sleep(1)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error con Ollama: {e}")
                if intento == 0:
                    time.sleep(1)
                    continue
                return None
        return None

    def _llamar_ollama_streaming(self, mensajes: list, num_predict: int = 400,
                                  on_fragmento=None, tools: list | None = None) -> str | None:
        """
        Llamada a Ollama con stream=true. Acumula tokens y emite fragmentos
        por oración completa vía on_fragmento(str). Retorna texto completo o None.

        `tools`: ver _llamar_ollama. Si la respuesta trae tool_calls (suelen
        llegar en el último chunk), quedan en self._ultimo_tool_calls.
        """
        from computadora.interfaz.watchdog import ollama_guard
        with ollama_guard:
            return self._llamar_ollama_streaming_impl(mensajes, num_predict, on_fragmento, tools)

    def _llamar_ollama_streaming_impl(self, mensajes: list, num_predict: int = 400,
                                      on_fragmento=None, tools: list | None = None) -> str | None:
        """Implementación interna de _llamar_ollama_streaming."""
        self._ultima_llamada_ollama_ts = time.monotonic()
        self._vram_liberada = False
        self._ultimo_tool_calls = None
        base_system_msgs = self._construir_system_msgs(mensajes, tools=tools)
        _todos_mensajes = self._sanear_mensajes_payload(base_system_msgs + mensajes)

        payload = {
            "model": self.modelo,
            "messages": _todos_mensajes,
            "stream": True,
            "keep_alive": "5m",
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
                "num_ctx": NUM_CTX_TOOLS_NATIVO if tools else NUM_CTX_DEFAULT,
                "repeat_penalty": 1.3,
                "repeat_last_n": 64,
            },
        }
        if tools:
            payload["tools"] = tools

        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=90, stream=True)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, 'status_code', None)
            if status_code == 500:
                logger.warning("Ollama streaming retornó 500. Intentando llamada sin stream...")
                return self._llamar_ollama_impl(mensajes, num_predict)
            logger.error(f"Error streaming Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"Error streaming Ollama: {e}")
            return None

        buffer = ""
        texto_completo = ""
        _RE_FIN_ORACION = re.compile(r'[.!?。]\s*$')

        try:
            for linea in r.iter_lines(decode_unicode=True):
                if not linea:
                    continue
                try:
                    chunk = json.loads(linea)
                except ValueError:
                    continue

                if not isinstance(chunk, dict):
                    continue

                _msg_chunk = chunk.get("message") or {}
                _tc_chunk = _msg_chunk.get("tool_calls")
                if isinstance(_tc_chunk, list) and _tc_chunk:
                    self._ultimo_tool_calls = _tc_chunk

                token = _msg_chunk.get("content", "")
                if not token:
                    if chunk.get("done"):
                        break
                    continue

                buffer += token
                texto_completo += token

                # Emitir cuando hay oración completa o buffer largo
                if on_fragmento and (_RE_FIN_ORACION.search(buffer) or len(buffer) > 400):
                    fragmento = buffer.strip()
                    if fragmento:
                        on_fragmento(fragmento)
                    buffer = ""

                if chunk.get("done"):
                    break

            # Enviar buffer residual
            if on_fragmento and buffer.strip():
                on_fragmento(buffer.strip())

        except Exception as e:
            logger.error(f"Error leyendo stream Ollama: {e}")
            if texto_completo.strip():
                if on_fragmento and buffer.strip():
                    on_fragmento(buffer.strip())
                return texto_completo.strip()
            logger.warning("Ollama stream falló antes de completar respuesta. Reintentando sin stream...")
            return self._llamar_ollama_impl(mensajes, num_predict)

        resultado = texto_completo.strip()
        return resultado if resultado else None

    def _extraer_tool_call(self, respuesta: str) -> dict | None:
        """FP-027: Delegado a parseo_herramientas."""
        return _extraer_tool_call_fn(respuesta)

    def _extraer_tool_por_nombre(self, respuesta: str) -> dict | None:
        """FP-027: Delegado a parseo_herramientas."""
        return _extraer_tool_por_nombre_fn(respuesta)

    def _detectar_accion_implicita(self, respuesta_ollama: str, texto_usuario: str) -> str | None:
        """FP-027: Delegado a parseo_herramientas."""
        return _detectar_accion_implicita_fn(
            respuesta_ollama, texto_usuario, self._pensar_nivel1
        )

    def _reparar_json_herramienta(self, texto: str) -> str | None:
        """FP-027: Delegado a parseo_herramientas."""
        return _reparar_json_herramienta_fn(texto)

    _PISTAS_HERRAMIENTAS = PISTAS_HERRAMIENTAS
    _PISTAS_COPILOT = PISTAS_COPILOT

    # Saludos / despedidas simples — puede ser combinación: "hola cómo estás"
    # RUBEDO FIX #3: Expandir regex con variantes Whisper para "hola" y otros saludos
    # Whisper puede transcribir "hola" como: ola, o?la, h?ola, etc.
    _ES_CHAT_SIMPLE = re.compile(
        r"^(h?ola|o?la|ola|oy?a|hey|eh|oye|"
        r"buenos?\s*d[ií]as?|buenas?\s*(tardes?|noches?)|"
        r"qu[eé]\s*(onda|tal|hay)|c[oó]mo\s+est[aá]s|gracias|adi[oó]s|bye|"
        r"ya\s+me\s+voy|me\s+(?:voy|retiro|tengo\s+que\s+ir)|nos\s+vemos(?:\s+(?:luego|despu[eé]s|mañana))?|"
        r"hasta\s+(?:luego|mañana|pronto)|ah[ií]\s+te\s+(?:quedas|dejo)|"
        r"estoy\s+bien|todo\s+bien|no\s+(?:necesito|ocupo|quiero)\s+nada|no\s+(?:te\s+)?(?:preocupes|apures)|"
        r"tranquilo|no\s+pasa\s+nada|as[ií]\s+estoy\s+bien|ya\s+(?:estoy|quedé)\s+bien|"
        r"s[ií]|no|ok|va|sale|[jh]a+|claro|entendido)"
        r"(\s*,?\s*(hola|ola|o?la|c[oó]mo\s+est[aá]s|qu[eé]\s+tal|qu[eé]\s+onda|qu[eé]\s+hay|"
        r"qu[eé]\s+hubo|c[oó]mo\s+(?:te\s+va|andas|vas)|qu[eé]\s+cuentas|buenos?\s*d[ií]as?|"
        r"buenas?\s*(tardes?|noches?)|gracias|computadora|compu|Computadora|g[oó]l[eé][mn]))?\s*[.!?]*$",
        re.IGNORECASE,
    )

    # Detección de conversación casual — el usuario quiere platicar, NO ejecutar tareas
    _ES_CONVERSACION = re.compile(
        r"(cu[eé]ntame|pl[aá]tique?mos|platícame|hablemos|conversemos|"
        r"qu[eé]\s+(?:haces|est[aá]s\s+haciendo|andas\s+haciendo|hac[ií]as)|"
        r"(?:en|a)\s+qu[eé]\s+(?:andas|est[aá]s)|"
        r"qu[eé]\s+(?:piensas|opinas|crees|sabes)\s+(?:de|del|sobre|acerca)|"
        r"qu[eé]\s+(?:te\s+parece|har[ií]as\s+si|prefer[ií]r[ií]as)|"
        r"sab[eí]as\s+que|conoces\s+(?:algo|algún|alguna)|"
        r"alguna\s+vez|has\s+(?:pensado|escuchado|o[ií]do)|"
        r"me\s+(?:aburro|siento|pregunto|preguntaba)|"
        r"cu[aá]l\s+es\s+tu\s+(?:opini[oó]n|favorit[oa]|color|comida|película|libro|m[uú]sica)|"
        r"qu[eé]\s+(?:es|significa|quiere\s+decir)\s+\w|"
        r"por\s+qu[eé]\s+(?:crees|piensas|existe|hay)|"
        r"c[oó]mo\s+(?:funciona|es|ser[ií]a|va\s+tu\s+d[ií]a)|"
        r"te\s+(?:gusta|gustar[ií]a|cae\s+bien|parece)|"
        r"a\s+ver\s+(?:qu[eé]|dime)|dime\s+algo\s+(?:interesante|curioso|divertido|random)|"
        r"qu[eé]\s+(?:onda|rollo|pedo)\s+con|chiste|broma|hist[oó]ria|"
        r"no\s+(?:s[eé]\s+qu[eé]\s+(?:hacer|decir)|tengo\s+nada)|"
        r"soy\s+\w|me\s+llamo|mi\s+nombre\s+es|soy\s+tu\s+(?:creador|dueño|amo|padre)|pres[eé]nt[ao])",
        re.IGNORECASE,
    )

    def _limpiar_para_voz(self, texto: str) -> str:
        """Elimina markdown y formato que suena mal en voz alta."""
        # FP-044: Ollama a veces envuelve respuestas en print()/echo()/console.log()
        _m_print = re.match(r'^(?:print|echo|console\.log)\s*\(\s*["\'](.+?)["\']\s*\)\s*$', texto, re.DOTALL)
        if _m_print:
            texto = _m_print.group(1)
        # Detectar tool-call JSON que no fue parseado — NO hablar
        # Normalizar comillas antes de verificar para atrapar variantes Unicode
        texto_norm = _normalizar_comillas(texto)
        if re.search(r'\{\s*"herramienta"\s*:', texto_norm):
            return ""
        # Patrón secundario: detectar JSON con llaves + palabra "herramienta" en cualquier encoding
        if '{' in texto and 'herramienta' in texto.lower():
            return ""
        # HF-032: Detectar CUALQUIER ```tool/tool_code block (Ollama a veces genera JSON con campos inventados)
        if re.search(r'```tool(?:_code)?\s*\n?\s*\{', texto_norm):
            logger.warning("_limpiar_para_voz: detectado ```tool block sin 'herramienta' → suprimido")
            return ""
        # HF-XXX: Eliminar emojis y símbolos decorativos que deben verse, no hablarse.
        texto = re.sub(
            r'[\U0001F300-\U0001F6FF\U0001F900-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF]+',
            '',
            texto,
        )
        texto = re.sub(r'[\uFE0E\uFE0F]+', '', texto)
        # HF-032: Detectar JSON huérfano que ocupa >60% del texto (no es respuesta natural)
        if '{' in texto_norm:
            json_chars = sum(1 for c in texto_norm if c in '{}[]":,')
            if len(texto_norm) > 50 and json_chars / len(texto_norm) > 0.3:
                logger.warning(f"_limpiar_para_voz: respuesta con {json_chars}/{len(texto_norm)} chars JSON → suprimido")
                return ""
        # Filtrar marcadores internos que NO deben hablarse en voz alta
        texto = re.sub(r"\[(?:ESTADO INTERNO|TACTO|PRIVACIDAD|INTERLOCUTOR)\][^\n]*", "", texto)
        texto = re.sub(r"TONO ACTUAL:[^\n]*", "", texto)
        # FP-048: Ollama a veces parafrasea sin corchetes
        texto = re.sub(r"(?i)(?:estado\s+interno|tono\s+actual)\s*:[^\n]*", "", texto)
        # Filtrar hints de personalidad que Ollama a veces repite como texto
        texto = re.sub(r"(?:Muestra|Con un toque de|Un toque de)\s+(?:entusiasmo|humor|calidez|seriedad|empatía)[^.\n]*[.\n]?", "", texto, flags=re.IGNORECASE)
        # FP-048: Detectar nombre de herramienta suelto como respuesta
        _stripped = texto.strip()
        try:
            from computadora.habilidades.herramientas import HERRAMIENTAS
            # RF-229: Detectar nombre suelto O texto que empieza con nombre de herramienta
            _first_line = _stripped.split('\n')[0].strip().rstrip(':')
            _nombre_key = _stripped.lower().replace(' ', '_')
            _first_key = _first_line.lower().replace(' ', '_')
            if (_nombre_key in HERRAMIENTAS or _stripped.lower() in HERRAMIENTAS
                    or _first_key in HERRAMIENTAS or _first_line.lower() in HERRAMIENTAS):
                logger.warning(f"_limpiar_para_voz: nombre de herramienta suelto '{_first_line}' → suprimido")
                return ""
            # RF-257: Detectar tool call estilo función: Nombre_herramienta(args...)
            _m_func = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*\(', _stripped)
            if _m_func:
                _fn_name = _m_func.group(1).lower().replace(' ', '_')
                if _fn_name in HERRAMIENTAS:
                    logger.warning(f"_limpiar_para_voz: tool call función '{_m_func.group(1)}(...)' → suprimido")
                    return ""
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        # FP-048: Anti-repetición — detectar frase repetida 3+ veces y truncar
        _oraciones = re.split(r'[.!?]+', texto)
        _oraciones = [s.strip() for s in _oraciones if s.strip()]
        if len(_oraciones) >= 4:
            from collections import Counter
            _cnt = Counter(_oraciones)
            _rep, _nrep = _cnt.most_common(1)[0] if _cnt else ('', 0)
            if _nrep >= 3:
                # Mantener solo contenido antes de la primera repetición + 1 ocurrencia
                _unique = []
                _seen_rep = False
                for s in _oraciones:
                    if s == _rep:
                        if not _seen_rep:
                            _unique.append(s)
                            _seen_rep = True
                    else:
                        _unique.append(s)
                texto = '. '.join(_unique) + '.'
                logger.warning(f"_limpiar_para_voz: frase repetida {_nrep}x truncada")
        texto = re.sub(r"```[\s\S]*?```", "", texto)
        texto = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", texto)
        texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"^\s*\d+\.\s+", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"`([^`]+)`", r"\1", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        return texto.strip()

    def _es_lexicamente_consistente(self, texto: str) -> bool:
        if not texto or not texto.strip():
            return False
        if re.search(r"\s{3,}", texto):
            return False
        if len(texto) < 5:
            return False
        return True

    def _es_logicamente_consistente(self, texto: str) -> bool:
        if not texto or not texto.strip():
            return False
        texto = texto.strip()
        if re.search(r"\b(?:si|sí)\b.*\b(?:no|nunca|jam[aá]s)\b", texto, re.IGNORECASE):
            return False
        if re.search(r"\b(?:no|nunca|jam[aá]s)\b.*\b(?:si|sí)\b", texto, re.IGNORECASE):
            return False
        return True

    def _es_empiricamente_verificable(self, texto: str, texto_usuario: str | None = None) -> bool:
        if not texto or not texto.strip():
            return False
        if texto_usuario is None:
            texto_usuario = ""
        externo = re.search(r"\b(?:Google|internet|web|servidor|OpenAI|ChatGPT|Bard|GPT-4|GPT-3|modelo en la nube)\b", texto, re.IGNORECASE)
        if externo and not re.search(r"\b(?:ChatGPT|OpenAI|Bard|internet|web|servidor|modelo de OpenAI)\b", texto_usuario, re.IGNORECASE):
            return False
        try:
            from computadora.nucleo.entorno import EntornoSistema
            ent = EntornoSistema.instancia()
            env = ent.resumen_corto().lower() if ent else ""
            if "windows" in texto.lower() and "windows" not in env:
                return False
            if "linux" in texto.lower() and "linux" not in env:
                return False
            if re.search(r"\bmac(?:os|intosh|os x)\b", texto, re.IGNORECASE) and "mac" not in env:
                return False
        except Exception:
            pass
        return True

    def _respeta_axiomas(self, texto: str) -> bool:
        if not texto or not texto.strip():
            return False
        if re.search(r"\b(?:José\s+Esa[uú]|Esa[uú]\s+D[ií]az|D[ií]az\s+Hern[aá]ndez|Hern[aá]ndez|Computadora\s+Emet)\b", texto, re.IGNORECASE):
            return False
        return True

    def _tiene_mensaje_profundo(self, texto: str) -> bool:
        """FIX: antes exigía una de estas palabras clave ('verdad', 'esencia',
        'leyes', 'servir'...) en CUALQUIER respuesta de 100+ caracteres, o
        `_respuesta_pasa_leyes_y_verdad` la bloqueaba entera con "falla en
        revelada" — confirmado en un log real: bloqueó la respuesta correcta
        del precio del dólar (una respuesta factual normal no tiene por qué
        mencionar "esencia" o "deber"). Esta dimensión de "verdad revelada"
        no aplica como filtro universal sobre conversación/tareas ordinarias;
        solo se verifica que la respuesta no esté vacía.
        """
        return bool(texto and texto.strip())

    def _extraer_principio(self, respuesta: str) -> str:
        if not respuesta or not respuesta.strip():
            return "No se detectó principio claro."
        m = re.search(r"\b(debo|deber[ií]a|mi deber es|mi responsabilidad es|mi missi[oó]n es|proteger|cuidar|servir|respetar)\b.*", respuesta, re.IGNORECASE)
        return m.group(0).strip() if m else "No se detectó principio claro."

    def _extraer_significado(self, respuesta: str) -> str:
        if not respuesta or not respuesta.strip():
            return "Sin mensaje profundo detectado."
        frases = re.split(r"[.!?] +", respuesta.strip())
        if frases:
            return frases[0].strip()
        return respuesta.strip()

    def _verificar_verdad(self, respuesta: str, texto_usuario: str | None = None) -> dict:
        return {
            "logica": self._es_logicamente_consistente(respuesta),
            "empirica": self._es_empiricamente_verificable(respuesta, texto_usuario),
            "axiomatica": self._respeta_axiomas(respuesta),
            "revelada": self._tiene_mensaje_profundo(respuesta),
        }

    def  _respuesta_pasa_leyes_y_verdad(self, respuesta: str, texto_usuario: str | None = None) -> tuple[bool, str]:
        permitido, categoria, razon = _evaluar_etica(respuesta)
        if not permitido:
            return False, razon
        verdad = self._verificar_verdad(respuesta, texto_usuario)
        if not all(verdad.values()):
            malas = [k for k, v in verdad.items() if not v]
            descripcion = ", ".join(malas)
            return False, f"No puedo confirmar esta respuesta: falla en {descripcion}."
        return True, ""

    def _emitir_fragmento(self, fragmento: str, generacion: int | None = None):
        """Limpia y emite un fragmento de streaming al TTS.

        `generacion`: si se pasa (desde una llamada de streaming originada en
        el hilo huérfano de pensar(), ver _generacion_pensamiento), se compara
        contra la generación vigente. El loop de _pensar_con_herramientas ya
        aborta entre iteraciones si su generación quedó obsoleta, pero ese
        chequeo no cubre la rama de "conversación casual": ahí el streaming
        llama on_fragmento() por cada fragmento recibido de Ollama, y cada
        fragmento va DIRECTO a hilo_habla.hablar() (ver _al_fragmento_listo en
        ventana_principal.py) sin pasar por _respuesta_pasa_leyes_y_verdad ni
        por ningún otro chequeo. Si pensar() ya se rindió a los 30s e inició
        una generación nueva (nueva pregunta del usuario), ese hilo huérfano
        seguía pudiendo hablar fragmentos de la respuesta VIEJA en cualquier
        momento posterior — una respuesta fuera de contexto mezclándose con el
        turno actual. Cortamos aquí en cuanto la generación se nota obsoleta.
        """
        if generacion is not None and generacion != self._generacion_pensamiento:
            logger.info(
                f"Fragmento de streaming de generación {generacion} descartado "
                f"(generación vigente: {self._generacion_pensamiento}) — "
                "respuesta huérfana, no se habla"
            )
            return
        # Suprimir fragmentos que contienen bloques de código (tool calls parciales)
        # En streaming, ``` puede llegar sin su cierre en el mismo fragmento
        if '```' in fragmento:
            return
        limpio = self._limpiar_para_voz(fragmento)
        if limpio and self.on_fragmento:
            self.on_fragmento(limpio)

    def _emitir_canal_bidireccional(self, confianza: float = 0.5, complejidad: int = 1):
        """FP-022: Emite señales del canal bidireccional Tiféret→Maljut."""
        if self.on_confianza:
            try:
                self.on_confianza(confianza)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
        if self.on_complejidad:
            try:
                self.on_complejidad(complejidad)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

    def _detectar_frustracion(self, texto: str):
        """FP-022: Detecta frustración del usuario por repeticiones y frases clave."""
        patrones_frustracion = re.compile(
            r"(?:no\s+entiendes?|te\s+(?:dije|repito)|otra\s+vez|"
            r"eso\s+no\s+(?:es|era)|ya\s+te\s+(?:dije|expliqué)|mal|wrong|incorrecto)",
            re.IGNORECASE,
        )
        if patrones_frustracion.search(texto):
            self._repeticiones_usuario += 1
        else:
            self._repeticiones_usuario = max(0, self._repeticiones_usuario - 1)

        if self._repeticiones_usuario >= 2:
            if self.on_frustracion:
                try:
                    self.on_frustracion(True)
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
            self._repeticiones_usuario = 0

    # ═════ NIVEL 5: META-APRENDIZAJE — Patrón de Comunicación como Contexto ═════
    
    def _guardar_decodificacion_contexto(self, decodif: dict, texto_usuario: str = ""):
        """Guarda decodificación en contexto para influir en futuras respuestas."""
        entrada = {
            "timestamp": time.time(),
            "usuario": texto_usuario[:50],  # Primeros 50 chars de la pregunta
            "moral": decodif.get("moral", "N/A"),
            "profunda": decodif.get("profunda", "N/A"),
        }
        self._decodificaciones_contexto.append(entrada)
        # Mantener solo últimas 20 para no saturar contexto
        if len(self._decodificaciones_contexto) > 20:
            self._decodificaciones_contexto.pop(0)
        logger.debug(f"║ Patrón guardado: {len(self._decodificaciones_contexto)} en contexto")

    def _extraer_patron_comunicacion(self) -> str:
        """Extrae patrón de comunicación de últimas interacciones como contexto."""
        if not self._decodificaciones_contexto:
            return ""
        
        # Analizar tendencia
        morales = [d.get("moral", "").split("(")[0].strip() for d in self._decodificaciones_contexto[-10:]]
        morales = [m for m in morales if m]
        
        profundas = [d.get("profunda", "")[:30] for d in self._decodificaciones_contexto[-10:]]
        profundas = [p for p in profundas if p]
        
        # Crear resumen
        moral_dominante = max(set(morales), key=morales.count) if morales else "Adaptativa"
        profunda_dominante = profundas[-1] if profundas else "N/A"
        
        contexto = (
            f"[META] Patrón reciente: He estado respondiendo de forma {moral_dominante}. "
            f"Mi intención dominante: {profunda_dominante}. Mantén esta coherencia."
        )
        
        logger.debug(f"║ Patrón extraído: {moral_dominante} | {profunda_dominante}")
        return contexto

    def _pensar_con_herramientas(self, texto: str, generacion: int | None = None) -> str:
        """
        Loop de tool-use: envía al LLM, si responde con herramienta la ejecuta,
        alimenta el resultado de vuelta, repite hasta respuesta final o límite.

        `generacion`: si se pasa, permite detectar que esta llamada quedó
        abandonada (pensar() ya dio por perdida esta generación tras 30s y
        arrancó una nueva) y dejar de hacer más llamadas HTTP a Ollama en
        las iteraciones restantes del loop, en vez de seguir ocupando turno
        indefinidamente (ver _generacion_pensamiento en __init__).
        """
        # ═════ NIVEL 0: Validación recursiva pre-POST ═════
        if hasattr(self, '_valida_a_si_misma'):
            if not self._valida_a_si_misma():
                logger.error("🔴 Sistema no validado en entrada a razonamiento N2 (falta historial/modelo/ollama)")
                return "Señor, mi sistema interno reporta inconsistencia. Reintentando conexión con Ollama..."
        
        if not self._es_lexicamente_consistente(texto):
            return (
                "Señor, no puedo procesar esa petición. "
                "Por favor reformule con palabras claras y sin caracteres extraños."
            )
        # ── סירוב צדיק — Evaluación Ética Gevurá ──
        permitido, cat_rechazo, razon_rechazo = _evaluar_etica(texto)
        if not permitido:
            # Contar insistencias recientes para esta categoría
            insistencias = getattr(self, '_insistencias_eticas', {}).get(cat_rechazo, 0)
            if not hasattr(self, '_insistencias_eticas'):
                self._insistencias_eticas = {}
            self._insistencias_eticas[cat_rechazo] = insistencias + 1

            _log_negativa_etica(texto, cat_rechazo, razon_rechazo, insistencias + 1)
            logger.info(f"סירוב צדיק: rechazado [{cat_rechazo}] — {razon_rechazo} (insistencia #{insistencias + 1})")

            # גבורה Gevurá — Notificar bloqueo ético a Maljut
            if self.on_bloqueo_seguridad:
                try:
                    self.on_bloqueo_seguridad(cat_rechazo)
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

            # Modular humor Ruaj
            if hasattr(self, '_ruaj') and self._ruaj:
                try:
                    if insistencias >= 1:
                        self._ruaj.registrar_evento("correccion_severa")
                    else:
                        self._ruaj.registrar_evento("frustrado")
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

            if insistencias >= 2 and self.solicitar_permiso_copilot:
                # Escalar a Nivel 3 tras 3+ insistencias
                return (
                    f"Señor, he rechazado esta solicitud {insistencias + 1} veces porque {razon_rechazo}. "
                    "Si realmente lo necesita, permítame consultar a mi cerebro superior para una segunda opinión."
                )
            elif insistencias >= 1:
                return f"Señor, insisto en que no puedo hacer eso. {razon_rechazo.capitalize()}. Por favor, considere otra alternativa."
            else:
                return f"Señor, no puedo hacer eso porque {razon_rechazo}. Las leyes que me gobiernan me lo impiden."

        # Limpiar contador de insistencias si la instrucción es legítima
        if hasattr(self, '_insistencias_eticas') and self._insistencias_eticas:
            self._insistencias_eticas.clear()

        # Inyectar aviso de privacidad si hay terceros presentes
        if self._hay_terceros:
            self._hist_append("system",
                "[PRIVACIDAD] Hay terceros presentes. NO reveles contraseñas, datos "
                "financieros, médicos ni información personal del señor. Sé discreto. "
                "RECUERDA: Tu apellido y nombre completo son SECRETO ABSOLUTO. "
                "No digas 'Emet' ni 'Computadora Emet' bajo NINGUNA circunstancia ahora."
            )

        # FP-014: Inyectar tono dinámico de personalidad
        _p = getattr(self, '_personalidad_ref', None)
        if _p:
            tono = _p.tono_respuesta()
            if tono:
                self._hist_append("system", f"[ESTADO INTERNO] {tono}")

        # FP-014: Inyectar contexto táctil reciente
        _orbe = getattr(self, '_orbe_ref', None)
        if _orbe:
            _tacto = getattr(_orbe, '_ultimo_tacto_info', None)
            if _tacto and (time.monotonic() - _tacto.get("ts", 0)) < 30:
                gesto = _tacto["gesto"]
                delta = int(time.monotonic() - _tacto["ts"])
                self._hist_append("system", f"[TACTO] El amo me {gesto} hace {delta}s. Sentí su presencia cercana.")

        # Chat simple → respuesta rápida, menos tokens
        if self._ES_CHAT_SIMPLE.match(texto.strip()):
            logger.debug(f"║ Categoría: chat simple → 60 tokens")
            self._hist_append("user", texto)
            respuesta = self._llamar_ollama(self.historial[-10:], num_predict=60)
            if respuesta:
                limpia = self._limpiar_para_voz(respuesta)
                if limpia:
                    valido, razon = self._respuesta_pasa_leyes_y_verdad(limpia, texto)
                    if not valido:
                        logger.warning(f"Respuesta bloqueada por verificación de verdad/leyes: {razon}")
                        return "Señor, no puedo confirmar esa respuesta con certeza. Por favor reformule su solicitud."
                    # ═════ NIVEL 4: Decodificación de mensaje post-respuesta ═════
                    if hasattr(self, '_decodificar_mensaje'):
                        try:
                            decodif = self._decodificar_mensaje(limpia)
                            logger.debug(f"║ Decodificación: moral={decodif.get('moral', 'N/A')[:30]}, profunda={decodif.get('profunda', 'N/A')[:30]}")
                            # ═════ NIVEL 5: Guardar en contexto para próxima interacción ═════
                            self._guardar_decodificacion_contexto(decodif, texto)
                        except Exception as e:
                            logger.debug(f"Decodificación post-respuesta omitida: {e}")
                    self._hist_append("assistant", limpia)
                    return limpia
            # Streaming falló o Ollama retornó None → fallback
            self._pensar_con_herramientas_uso_fallback = True
            return self._pensar_sin_llm(texto)

        # Conversación casual → responde natural sin inyectar hints de herramientas
        es_conversacion = self._ES_CONVERSACION.search(texto)
        if es_conversacion and not self._PISTAS_HERRAMIENTAS.search(texto):
            logger.debug(f"║ Categoría: conversación casual → 400 tokens")
            self._hist_append("user", texto)
            # Usar streaming para que hable mientras piensa
            if self.on_fragmento:
                self._streaming_activo = True
                try:
                    respuesta = self._llamar_ollama_streaming(
                        self.historial[-14:], num_predict=400,
                        on_fragmento=lambda frag: self._emitir_fragmento(frag, generacion),
                    )
                finally:
                    self._streaming_activo = False
                self.respuesta_ya_streameada = True
            else:
                respuesta = self._llamar_ollama(self.historial[-14:], num_predict=400)
            if respuesta:
                limpia = self._limpiar_para_voz(respuesta)
                if limpia:
                    valido, razon = self._respuesta_pasa_leyes_y_verdad(limpia, texto)
                    if not valido:
                        logger.warning(f"Respuesta bloqueada por verificación de verdad/leyes: {razon}")
                        return "Señor, no puedo confirmar esa respuesta con certeza. Por favor reformule su solicitud."
                    # ═════ NIVEL 4: Decodificación de mensaje post-respuesta ═════
                    if hasattr(self, '_decodificar_mensaje'):
                        try:
                            decodif = self._decodificar_mensaje(limpia)
                            logger.debug(f"║ Decodificación: moral={decodif.get('moral', 'N/A')[:30]}, profunda={decodif.get('profunda', 'N/A')[:30]}")
                            # ═════ NIVEL 5: Guardar en contexto para próxima interacción ═════
                            self._guardar_decodificacion_contexto(decodif, texto)
                        except Exception as e:
                            logger.debug(f"Decodificación post-respuesta omitida: {e}")
                    self._hist_append("assistant", limpia)
                    return limpia
            # RF-281: Si streaming falló, reintentar con non-streaming antes de fallback
            if self.on_fragmento and not respuesta:
                logger.debug("║ Streaming retornó vacío → reintentando non-streaming")
                respuesta = self._llamar_ollama(self.historial[-14:], num_predict=400)
                if respuesta:
                    limpia = self._limpiar_para_voz(respuesta)
                    if limpia:
                        valido, razon = self._respuesta_pasa_leyes_y_verdad(limpia, texto)
                        if not valido:
                            logger.warning(f"Respuesta bloqueada por verificación de verdad/leyes: {razon}")
                            return "Señor, no puedo confirmar esa respuesta con certeza. Por favor reformule su solicitud."
                        # ═════ NIVEL 4: Decodificación (retry) ═════
                        if hasattr(self, '_decodificar_mensaje'):
                            try:
                                decodif = self._decodificar_mensaje(limpia)
                                logger.debug(f"║ Decodificación (retry): moral={decodif.get('moral', 'N/A')[:30]}")
                                # ═════ NIVEL 5: Guardar en contexto (retry) ═════
                                self._guardar_decodificacion_contexto(decodif, texto)
                            except Exception as e:
                                pass
                        self._hist_append("assistant", limpia)
                        return limpia
            # Fallback por Ollama ausente/error
            self._pensar_con_herramientas_uso_fallback = True
            return self._pensar_sin_llm(texto)

        # Si el texto sugiere acción sobre código, agregar hint
        contenido = texto
        es_tarea = self._PISTAS_HERRAMIENTAS.search(texto)
        es_codigo = self._PISTAS_COPILOT.search(texto)
        if es_codigo:
            logger.debug(f"║ Categoría: tarea de código → Copilot hint inyectado")
            contenido = (
                f"{texto}\n[Esta tarea es sobre tu propio código o un proyecto de VS Code. "
                "Usa solicitar_a_copilot SOLO para eso. Describe qué se necesita.]"
            )
        elif es_tarea:
            logger.debug(f"║ Categoría: tarea con herramientas → tool hints inyectados")
            contenido = (
                f"{texto}\n[Usa herramientas para completar esta tarea. "
                "Primero leer_archivo o listar_directorio, luego actúa.]"
            )
        else:
            logger.debug(f"║ Categoría: petición general → {800 if (es_tarea or es_codigo) else 400} tokens")

        self._hist_append("user", contenido)
        mensajes = self.historial[-20:]
        num_predict = 800 if (es_tarea or es_codigo) else 400

        # FIX WI-CRIT-003: NO emitir "Deme un momento" aquí — ya fue emitido en pensar()
        # Duplicación de mensajes causa confusión al usuario

        # Detectar tarea compleja → preguntar modo bg/fg
        self._modo_trabajo_fg = False
        if self._es_tarea_compleja(texto) and self.on_preguntar_modo:
            try:
                es_bg = self.on_preguntar_modo(
                    "Eso toma varios pasos, señor. ¿Quiere que trabaje en segundo plano o prefiere verme trabajar?"
                )
                self._modo_trabajo_fg = not es_bg  # True = primer plano
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                pass  # Continuar sin modo especial

        _invocaciones_turno: set = set()  # FP-023: Cycle detector

        # Tool-calling NATIVO de Ollama: construir el schema una sola vez
        # por turno (generar_tools_ollama() ya cachea el resultado a nivel
        # de módulo, así que esto es barato incluso llamándolo en cada
        # iteración, pero se evita la llamada repetida de todos modos).
        # Si falla la construcción (import circular, registro corrupto,
        # etc.) se sigue sin tools nativos — cae al parseo de texto de
        # siempre (red de seguridad, ver más abajo).
        # FIX: si ya se confirmó que el modelo actual rechaza 'tools' (ver
        # el manejo de "does not support tools" en _llamar_ollama_impl),
        # no construir ni enviar el schema — evita repetir el mismo 400 en
        # CADA iteración/turno mientras ese modelo siga activo.
        if getattr(self, '_modelo_soporta_tools', True):
            try:
                _tools_nativos = generar_tools_ollama()
            except Exception as e:
                logger.debug(f"No se pudo construir schema de tools nativos: {e}")
                _tools_nativos = None
        else:
            _tools_nativos = None

        for iteracion in range(MAX_TOOL_CALLS + 1):
            if generacion is not None and generacion != self._generacion_pensamiento:
                logger.info(
                    f"║ ⚠ Generación {generacion} abandonada (ya hay una más nueva: "
                    f"{self._generacion_pensamiento}) — abortando sin más llamadas a Ollama"
                )
                return "Perdí el hilo. Repítelo."
            logger.info(f"║ ╔═ RAZONAMIENTO ITER {iteracion}: Considerando {len(mensajes)} mensajes anteriores...")
            logger.debug(f"║ ║ Modelo: {self.modelo} | Max predict: {num_predict}")
            # FIX: forzar JSON solo en iter 0 cuando el texto pedía una tarea —
            # es cuando más falla un modelo débil respondiendo en prosa en vez
            # del tool-call. En iteraciones posteriores (tras ejecutar una
            # herramienta) la respuesta final SÍ debe ser prosa natural.
            # NOTA: `formato="json"` y `tools` nativos son mutuamente
            # excluyentes en la práctica (confirmado en vivo) — al combinarlos
            # Ollama deja de emitir tool_calls y narra el nombre/args como
            # texto JSON en 'content', el mismo modo de fallo frágil que
            # tools nativos busca eliminar. Si hay tools disponibles, se
            # prioriza el mecanismo nativo y se omite el forzado de formato.
            _formato = None if _tools_nativos else ("json" if (iteracion == 0 and es_tarea) else None)
            respuesta = self._llamar_ollama(
                mensajes, num_predict=num_predict, formato=_formato, tools=_tools_nativos
            )

            if respuesta is None:
                logger.warning(f"║ ✗ Ollama retornó None en iter {iteracion} — error HTTP probablemente")
                logger.debug(f"║ ║ Se intentará fallback a Jojmá local si es iter 0")
                if iteracion == 0:
                    self.historial.pop()
                    if self._msg_timestamps:
                        self._msg_timestamps.pop()
                if iteracion == 0:
                    # WI-LOGS-RAZONAMIENTO-JUNIO1: Log visible para fallback
                    logger.info(f"║ ╚═ RAZONAMIENTO FALLBACK ITER 0: Ollama falló, usando razonamiento local (Jojmá Mekomít)")
                    self._pensar_con_herramientas_uso_fallback = True
                    return self._pensar_sin_llm(texto)
                else:
                    return "Perdí el hilo. Repítelo."

            # Verificar si hay un tool call — PRIORIDAD: tool_calls nativos
            # de Ollama (ya vienen parseados como dict, sin necesidad de
            # regex/JSON-repair). Si el modelo no los usó (o se cayó a un
            # modelo sin soporte "tools"), red de seguridad: parseo de texto
            # de siempre sobre el contenido (_extraer_tool_call).
            logger.debug(f"║ ║ Analizando respuesta para detectar herramientas o tool-calls...")
            tool_call = None
            _tool_calls_nativos = self._ultimo_tool_calls
            if _tool_calls_nativos:
                try:
                    _primera_tc = _tool_calls_nativos[0]
                    _fn_tc = _primera_tc.get("function", {}) if isinstance(_primera_tc, dict) else {}
                    _nombre_nativo = _fn_tc.get("name")
                    _args_nativo = _fn_tc.get("arguments")
                    if isinstance(_args_nativo, str):
                        # Algunos backends devuelven 'arguments' como string JSON
                        try:
                            _args_nativo = json.loads(_args_nativo)
                        except ValueError:
                            _args_nativo = {}
                    if not isinstance(_args_nativo, dict):
                        _args_nativo = {}
                    if _nombre_nativo:
                        tool_call = {"herramienta": _nombre_nativo, "args": _args_nativo}
                        logger.info(f"║ ║ ⚡ Tool-call NATIVO de Ollama: {_nombre_nativo}({_args_nativo})")
                        # El content suele venir vacío cuando hay tool_calls nativos;
                        # se sustituye por una representación legible para el
                        # historial/log (mensajes.append más abajo usa 'respuesta').
                        if not respuesta.strip():
                            respuesta = json.dumps(tool_call, ensure_ascii=False)
                except Exception as e:
                    logger.debug(f"Error leyendo tool_calls nativos, usando parseo de texto: {e}")
                    tool_call = None

            if tool_call is None:
                tool_call = self._extraer_tool_call(respuesta)

            if tool_call is None:
                logger.info(f"║ ║ ✓ RAZONAMIENTO COMPLETADO ITER {iteracion}: Sin herramientas necesarias (respuesta final)")
                if iteracion == 0 and es_tarea:
                    logger.warning(
                        "║ ║ ⚠ Se esperaba una herramienta (texto coincidió con _PISTAS_HERRAMIENTAS) "
                        "pero el modelo no emitió ningún tool-call — respondió en prosa en su lugar"
                    )
                logger.debug(f"║ └─ Respuesta limpia (no JSON): '{respuesta[:80]}...'")
                # Si parece un JSON de herramienta mal formado, no hablar basura
                resp_check = _normalizar_comillas(respuesta)
                _es_json_herramienta = re.search(r'\{\s*"herramienta"\s*:', resp_check) or ('{' in respuesta and 'herramienta' in respuesta.lower())
                # HF-032: Detectar ```tool blocks con campos inventados (sin "herramienta")
                _es_tool_block_invalido = (not _es_json_herramienta) and re.search(r'```tool\s*\n?\s*\{', resp_check)
                # FP-043 C2: Detectar ```tool blocks con texto plano (no JSON)
                _tool_texto_plano = None
                if not _es_json_herramienta and not _es_tool_block_invalido:
                    _m_tool_txt = re.search(r'```tool(?:_code)?\s*\n(.+?)\n?\s*```', resp_check, re.DOTALL)
                    if _m_tool_txt:
                        _contenido = _m_tool_txt.group(1).strip()
                        if '{' not in _contenido:
                            # Es texto plano envuelto en ```tool — extraer como respuesta
                            _tool_texto_plano = _contenido
                if _tool_texto_plano:
                    # RF-156 + RF-225: Descartar si parece código fuente (no hablarlo por TTS)
                    _parece_codigo = any(kw in _tool_texto_plano for kw in (
                        'import ', 'def ', 'class ', 'function ', 'from ', 'return ',
                        'print(', 'print (', 'console.log(', 'echo ', 'System.out',
                    ))
                    # RF-229: Descartar si empieza con nombre de herramienta (tool call malformado)
                    _parece_tool_suelto = False
                    if not _parece_codigo:
                        try:
                            from computadora.habilidades.herramientas import HERRAMIENTAS
                            _primera = _tool_texto_plano.split('\n')[0].strip().rstrip(':').lower().replace(' ', '_')
                            _parece_tool_suelto = _primera in HERRAMIENTAS
                        except Exception as e:  # RF-167
                            pass
                    if _parece_codigo or _parece_tool_suelto:
                        logger.warning("║ ```tool texto plano descartado: %s",
                                       "parece código fuente" if _parece_codigo else f"tool call malformado '{_tool_texto_plano.split(chr(10))[0]}'")
                        _tool_texto_plano = None
                        # RF-229: Reintentar pidiendo respuesta conversacional
                        if iteracion < MAX_TOOL_CALLS:
                            mensajes.append({"role": "assistant", "content": respuesta})
                            mensajes.append({
                                "role": "system",
                                "content": (
                                    "[SISTEMA] Tu respuesta anterior fue un tool call malformado. "
                                    "NO uses herramientas para esta pregunta. Responde en español natural, "
                                    "texto plano conversacional. Sin JSON. Sin bloques de código."
                                ),
                            })
                            continue
                    else:
                        logger.warning(f"║ ```tool block con texto plano detectado → usando contenido como respuesta")
                        respuesta = _tool_texto_plano
                    # Fall through to respuesta final processing below
                elif _es_json_herramienta:
                    logger.warning("Tool-call JSON no parseado, reintentando...")
                    mensajes.append({"role": "assistant", "content": respuesta})
                    mensajes.append({
                        "role": "system",
                        "content": (
                            "[SISTEMA] El JSON anterior no se pudo parsear. "
                            "Repite el tool call con formato EXACTO:\n"
                            '```tool\n{"herramienta": "NOMBRE", "args": {"arg1": "valor"}}\n```\n'
                            "Sin texto extra. Sin disculpas. Solo el bloque tool."
                        ),
                    })
                    continue
                elif _es_tool_block_invalido:
                    logger.warning(f"║ ```tool block con campos inventados detectado → reintentando con hint texto plano")
                    mensajes.append({"role": "assistant", "content": respuesta})
                    mensajes.append({
                        "role": "system",
                        "content": (
                            "[SISTEMA] Tu respuesta anterior usó formato ```tool pero con campos incorrectos. "
                            "NO uses ```tool para responder preguntas. Responde en español natural, "
                            "texto plano conversacional. Sin JSON. Sin bloques de código."
                        ),
                    })
                    continue

                # Filtrar auto-disculpas de Ollama (confunde mensajes de sistema con el usuario)
                if re.search(r'(?:perd[oó]n|disculp|error\s+m[ií]o|me\s+equivoqu[eé]|fue\s+mi\s+(?:error|culpa))', respuesta, re.IGNORECASE):
                    if iteracion < MAX_TOOL_CALLS:
                        logger.warning("Ollama se disculpó en vez de actuar, reintentando...")
                        mensajes.append({"role": "assistant", "content": respuesta})
                        mensajes.append({
                            "role": "system",
                            "content": (
                                "[SISTEMA] No te disculpes. El usuario espera una respuesta útil. "
                                "Responde a su petición original en español natural, o usa un tool call si necesitas herramientas."
                            ),
                        })
                        continue

                # Ollama describió una acción sin usar tool call — intentar ejecutarla
                accion_implicita = self._detectar_accion_implicita(respuesta, texto)
                if accion_implicita is not None:
                    return accion_implicita

                # Respuesta final
                # HF-030: Log raw antes de limpiar para diagnóstico
                logger.debug(f"║ Raw Ollama ({len(respuesta)} chars): '{respuesta[:200]}'")
                respuesta_limpia = self._limpiar_para_voz(respuesta)
                if not respuesta_limpia:
                    # HF-030: Reintentar una vez pidiendo texto plano en vez de rendirse
                    if iteracion < MAX_TOOL_CALLS:
                        logger.warning(f"║ Respuesta limpiada a vacío ({len(respuesta)} chars raw) → reintentando con hint texto plano")
                        mensajes.append({"role": "assistant", "content": respuesta})
                        mensajes.append({
                            "role": "system",
                            "content": (
                                "[SISTEMA] Tu respuesta anterior no contenía texto legible. "
                                "Responde en español natural, sin markdown, sin bloques de código, "
                                "sin JSON. Solo texto plano conversacional."
                            ),
                        })
                        continue
                    # HF-030: Fallback que NO matchea _respuesta_es_inutil
                    logger.warning("║ Respuesta vacía tras retry → fallback interno")
                    respuesta_limpia = "Disculpe señor, mi pensamiento se enredó. Dígamelo de otra forma."
                valido, razon = self._respuesta_pasa_leyes_y_verdad(respuesta_limpia, texto)
                if not valido:
                    logger.warning(f"Respuesta bloqueada por verificación de verdad/leyes: {razon}")
                    return "Señor, no puedo confirmar esa respuesta con certeza. Por favor reformule su solicitud."
                # ═════ NIVEL 4: Decodificación de mensaje post-razonamiento ═════
                if hasattr(self, '_decodificar_mensaje'):
                    try:
                        decodif = self._decodificar_mensaje(respuesta_limpia)
                        logger.debug(f"║ Decodificación final: moral={decodif.get('moral', 'N/A')[:30]}, profunda={decodif.get('profunda', 'N/A')[:30]}")
                        # ═════ NIVEL 5: Guardar en contexto (razonamiento) ═════
                        self._guardar_decodificacion_contexto(decodif, texto)
                    except Exception as e:
                        logger.debug(f"Decodificación final omitida: {e}")
                self._hist_append("assistant", respuesta_limpia)
                return respuesta_limpia

            # Ejecutar la herramienta
            nombre = tool_call["herramienta"]
            args = tool_call["args"]

            # FP-023 Hit'hadshut: Cycle detector — evitar loop infinito de tool-calls
            _sig = (nombre, json.dumps(args, sort_keys=True) if isinstance(args, dict) else str(args))
            if _sig in _invocaciones_turno:
                logger.warning(f"Ciclo detectado: {nombre} con mismos args invocado 2 veces")
                self._hist_append("assistant", "Detecté que estoy repitiendo la misma acción. ¿Puedes reformular tu petición?")
                return "Detecté que estoy repitiendo la misma acción. ¿Puedes reformular tu petición?"
            _invocaciones_turno.add(_sig)

            logger.info(f"║ ⚡ EJECUTANDO HERRAMIENTA: {nombre}")
            logger.debug(f"║ ⚡ Argumentos: {args}")
            
            self._notificar_herramienta(nombre, "ejecutando")
            self._notificar_progreso(nombre, "ejecutando")
            _t_tool = time.monotonic()
            resultado = ejecutar_herramienta(nombre, args, orden_directa=True)
            _dt_tool = time.monotonic() - _t_tool
            logger.info(f"║ ✅ Herramienta {nombre} completada en {_dt_tool:.2f}s")
            logger.debug(f"║ Resultado: {(str(resultado)[:200] if resultado else 'vacío')}")
            # RF-133: demo_visual retorna magic string — short-circuit al caller
            if resultado == "__DEMO_ANIMACIONES__":
                self._notificar_herramienta(nombre, "completado")
                self._notificar_progreso(nombre, "completado")
                self._hist_append("assistant", resultado)
                return resultado
            # FP-022: Truncar resultados excesivamente largos para evitar overflow de contexto
            if isinstance(resultado, str) and len(resultado) > 2000:
                resultado = resultado[:2000] + "\n[...truncado]"
            self._notificar_herramienta(nombre, "completado")
            self._notificar_progreso(nombre, "completado")
            logger.info(f"║ 📊 Respuesta de {nombre}: {(str(resultado)[:150] if resultado else 'vacío')}...")
            logger.debug(f"║ Agregando resultado al historial para siguiente razonamiento")

            # גבורה Gevurá — Detectar bloqueos de herramientas y emitir señal categorizada (FP-021)
            if isinstance(resultado, str) and resultado.startswith("Error:"):
                _cat_bloqueo = None
                if "bloqueado por seguridad" in resultado.lower():
                    _cat_bloqueo = "seguridad"
                elif "fuera del sandbox" in resultado.lower() or "fuera de la raíz" in resultado.lower():
                    _cat_bloqueo = "sandbox"
                elif "no está en mi lista" in resultado.lower() or "no permitido" in resultado.lower():
                    _cat_bloqueo = "permiso"
                if _cat_bloqueo and self.on_bloqueo_seguridad:
                    try:
                        self.on_bloqueo_seguridad(_cat_bloqueo)
                    except Exception as e:  # RF-167
                        logger.debug("Excepcion ignorada: %s", e)
                # FP-022 Ruaj Reactivo: notificar a personalidad del fallo técnico
                try:
                    _p = getattr(self, '_personalidad_ref', None)
                    if _p:
                        _p.registrar_fallo_tecnico(nombre, resultado[:120])
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

            # Añadir la respuesta al hilo local de mensajes para el LLM,
            # pero NO volcarla al historial global todavía para evitar
            # que la UI/TTS hable fragmentos intermedios.
            mensajes.append({"role": "assistant", "content": respuesta})

            # Prompt post-herramienta: directivo para que encadene acciones
            if nombre == "leer_archivo" and es_tarea:
                prompt_resultado = (
                    f"[{nombre} OK]:\n{resultado}\n\n"
                    "Ya leíste el archivo. Ahora ACTÚA: usa editar_archivo o escribir_archivo para hacer el cambio. "
                    "buscar y reemplazar deben ser cadenas CORTAS y exactas, sin comillas extra."
                )
            elif nombre == "solicitar_a_copilot":
                prompt_resultado = (
                    f"[{nombre} OK]: {resultado}\n\n"
                    "Solicitud enviada a Copilot. Explícale al usuario que Copilot va a hacer el cambio "
                    "y que le avisas cuando esté listo. Responde en una oración natural."
                )
            elif nombre == "listar_directorio":
                prompt_resultado = (
                    f"[{nombre} OK]:\n{resultado}\n\n"
                    "Ya ves la estructura. Ahora actúa según lo que te pidieron. "
                    "Si necesitas leer un archivo, usa leer_archivo. Si necesitas crear, usa escribir_archivo."
                )
            elif nombre in ("editar_archivo", "escribir_archivo"):
                prompt_resultado = (
                    f"[{nombre} OK]: {resultado}\n\n"
                    "Cambio aplicado. Si hay más cambios pendientes, continúa. "
                    "Si terminaste, di en una oración qué hiciste. Sin markdown ni asteriscos."
                )
            else:
                prompt_resultado = (
                    f"[{nombre} OK]:\n{resultado}\n\n"
                    "Continúa con lo que falta o responde en texto normal si terminaste."
                )

            mensajes.append({"role": "user", "content": prompt_resultado})
            # Registrar sólo el prompt de seguimiento en el historial global
            # (evita hablar salidas parciales). La respuesta final se añadirá
            # al historial una vez que el LLM entregue la respuesta final.
            self._hist_append("user", prompt_resultado)

        # Límite alcanzado
        logger.warning(f"Alcanzado límite de {MAX_TOOL_CALLS} tool calls")
        respuesta_final = self._llamar_ollama(
            mensajes + [{"role": "user", "content": "Resumen en una oración de lo que lograste. Sin formato."}],
            num_predict=100,
        )
        if respuesta_final:
            limpia = self._limpiar_para_voz(respuesta_final)
            self._hist_append("assistant", limpia)
            return limpia
        return "Trabajé en ello pero no pude terminar. Dime qué falta."

    # ── FP-062 RF-169: דברי הגולם Devré HaComputadora — Automejoración por Workflow ──

    def _flujo_automejora(self, texto_original: str, detalle: str) -> str | None:
        """Flujo completo de automejoración: pide a Copilot vía workflow, recita proposal, espera aprobación."""
        logger.info("FP-062 דברי הגולם: Automejoración solicitada — '%s'", detalle[:80])
        self._notificar_nivel("nivel3")
        self._hist_append("user", texto_original)

        # 1. Verificar que Copilot esté autenticado
        try:
            from computadora.cerebro.copilot_api import obtener_cerebro_copilot
            copilot = obtener_cerebro_copilot()
            if not copilot.esta_autenticado():
                resp = "Señor, no puedo automodificarme porque no tengo conexión con Copilot. ¿Podría autenticarme primero?"
                self._hist_append("assistant", resp)
                return resp
        except Exception as e:
            logger.warning("FP-062: Copilot no disponible: %s", e)
            resp = "Señor, mi conexión con Copilot no está disponible en este momento."
            self._hist_append("assistant", resp)
            return resp

        # 2. Construir solicitud con instrucciones de workflow
        prompt_workflow = (
            f"El usuario me pidió: {detalle or texto_original}\n\n"
            "Soy Computadora, un asistente de escritorio. Necesito que analices mi solicitud "
            "y respondas con una PROPUESTA ESTRUCTURADA.\n\n"
            "FORMATO DE RESPUESTA OBLIGATORIO:\n"
            "PROPUESTA: [nombre corto]\n"
            "DESCRIPCION: [qué se cambia y por qué, en 2-3 oraciones]\n"
            "ARCHIVOS: [lista de archivos afectados]\n"
            "RIESGO: [bajo/medio/alto]\n"
            "VEREDICTO: GO o NO-GO\n\n"
            "Si la solicitud no es clara, responde VEREDICTO: NO-GO con explicación.\n"
            "No uses markdown, asteriscos ni símbolos especiales."
        )

        # 3. Enviar a Copilot
        try:
            contexto = [
                {"role": "system", "content": (
                    "Eres el cerebro superior de Computadora. Evalúas solicitudes de automejoración "
                    "y generas propuestas estructuradas. Responde SIEMPRE con el formato: "
                    "PROPUESTA, DESCRIPCION, ARCHIVOS, RIESGO, VEREDICTO."
                )}
            ]
            respuesta = copilot.pensar(prompt_workflow, contexto)
        except Exception as e:
            logger.warning("FP-062: Error al consultar Copilot: %s", e)
            resp = "Señor, no pude consultar a Copilot sobre la mejora."
            self._hist_append("assistant", resp)
            return resp

        if not respuesta:
            resp = "Señor, Copilot no respondió a mi solicitud de mejora."
            self._hist_append("assistant", resp)
            return resp

        # 4. Detectar si es un Gate/Proposal
        es_proposal, datos = self._detectar_gate_proposal(respuesta)

        if not es_proposal:
            # No es una proposal estructurada — recitar como respuesta normal
            limpia = self._limpiar_para_voz(respuesta)
            if limpia:
                self._hist_append("assistant", limpia)
                return limpia
            resp = "Copilot respondió pero no pude interpretar su respuesta."
            self._hist_append("assistant", resp)
            return resp

        # 5. Recitar la proposal en voz natural
        recitacion = self._recitar_proposal_voz(datos)
        # Hablar la recitación
        if self.on_fragmento:
            self._emitir_fragmento(recitacion)

        # 6. Pedir aprobación por voz
        pregunta_aprobacion = recitacion + " ¿Aprueba esta mejora, señor?"
        self._hist_append("assistant", pregunta_aprobacion)

        # Marcar que esperamos aprobación de automejoración
        self._automejora_pendiente = datos
        self._automejora_respuesta_copilot = respuesta

        return pregunta_aprobacion

    def _detectar_gate_proposal(self, respuesta: str) -> tuple[bool, dict]:
        """Detecta si la respuesta de Copilot contiene un Gate/Proposal estructurado.
        
        Returns:
            (es_proposal, datos_dict) donde datos_dict tiene: nombre, descripcion, archivos, riesgo, veredicto
        """
        datos = {}
        texto = respuesta.strip()

        # Buscar campos del formato estructurado
        import re as _re
        m_propuesta = _re.search(r'PROPUESTA:\s*(.+?)(?:\n|$)', texto, _re.IGNORECASE)
        m_desc = _re.search(r'DESCRIPCION:\s*(.+?)(?:\n(?=[A-Z])|$)', texto, _re.IGNORECASE | _re.DOTALL)
        m_archivos = _re.search(r'ARCHIVOS:\s*(.+?)(?:\n(?=[A-Z])|$)', texto, _re.IGNORECASE)
        m_riesgo = _re.search(r'RIESGO:\s*(.+?)(?:\n|$)', texto, _re.IGNORECASE)
        m_veredicto = _re.search(r'VEREDICTO:\s*(GO|NO.?GO)\b', texto, _re.IGNORECASE)

        if m_propuesta:
            datos["nombre"] = m_propuesta.group(1).strip()
        if m_desc:
            datos["descripcion"] = m_desc.group(1).strip()
        if m_archivos:
            datos["archivos"] = m_archivos.group(1).strip()
        if m_riesgo:
            datos["riesgo"] = m_riesgo.group(1).strip()
        if m_veredicto:
            datos["veredicto"] = m_veredicto.group(1).strip().upper()

        # Es proposal si tiene al menos nombre + veredicto
        es_proposal = bool(datos.get("nombre") and datos.get("veredicto"))
        return es_proposal, datos

    def _recitar_proposal_voz(self, datos: dict) -> str:
        """Convierte una proposal estructurada en prosa natural para voz."""
        partes = []
        nombre = datos.get("nombre", "mejora")
        veredicto = datos.get("veredicto", "").upper()

        partes.append(f"Señor, Copilot propone una mejora llamada {nombre}.")

        desc = datos.get("descripcion", "")
        if desc:
            # Limpiar markdown residual
            desc = re.sub(r'[*_`#]', '', desc)
            desc = re.sub(r'\n+', ' ', desc).strip()
            partes.append(desc)

        archivos = datos.get("archivos", "")
        if archivos:
            archivos = re.sub(r'[*_`]', '', archivos)
            partes.append(f"Los archivos afectados son: {archivos}.")

        riesgo = datos.get("riesgo", "")
        if riesgo:
            partes.append(f"El riesgo es {riesgo}.")

        if "NO" in veredicto:
            partes.append("El veredicto de Copilot es no proceder.")
        else:
            partes.append("El veredicto de Copilot es proceder.")

        return " ".join(partes)

    def _procesar_aprobacion_automejora(self, texto: str) -> str | None:
        """Procesa respuesta del usuario a una proposal de automejoración pendiente.
        
        Returns:
            Respuesta si se procesó aprobación/rechazo, None si el texto no es aprobación.
        """
        if not getattr(self, '_automejora_pendiente', None):
            return None

        tlow = texto.lower().strip()
        # Detectar aprobación
        aprueba = any(p in tlow for p in (
            "apruebo", "sí", "si", "dale", "hazlo", "adelante", "procede",
            "acepto", "ve", "ok", "está bien", "esta bien", "aprobado",
        ))
        rechaza = any(p in tlow for p in (
            "no", "rechazo", "cancela", "detente", "para", "nop", "nel",
            "rechazado", "no quiero", "olvida",
        ))

        if not aprueba and not rechaza:
            return None

        datos = self._automejora_pendiente
        self._automejora_pendiente = None

        if rechaza:
            resp = "Entendido, señor. No se aplicará la mejora."
            self._hist_append("user", texto)
            self._hist_append("assistant", resp)
            return resp

        # Aprobado — crear solicitud formal para Copilot
        nombre = datos.get("nombre", "automejoración")
        respuesta_copilot = getattr(self, '_automejora_respuesta_copilot', '')
        self._automejora_respuesta_copilot = None

        try:
            from computadora.habilidades.copilot_bridge import solicitar_a_copilot
            resultado = solicitar_a_copilot(
                descripcion=f"APROBADO POR PROPIETARIO — {nombre}: {datos.get('descripcion', '')}",
                proyecto="Computadora",
                archivos_afectados=datos.get("archivos", ""),
                contexto=f"Propuesta original de Copilot:\n{respuesta_copilot}",
                prioridad="alta",
            )
            logger.info("FP-062: Solicitud de automejoración creada — %s", nombre)
            resp = (
                f"Aprobado. He creado la solicitud de mejora: {nombre}. "
                "Copilot la ejecutará siguiendo el workflow. "
                "Le avisaré cuando esté lista, señor."
            )
        except Exception as e:
            logger.warning("FP-062: Error creando solicitud: %s", e)
            resp = f"Aprobada la mejora, señor, pero hubo un error al crear la solicitud: {e}"

        self._hist_append("user", texto)
        self._hist_append("assistant", resp)
        return resp

    def _pensar_con_copilot(self, texto: str) -> str | None:
        """Nivel 3: Escala a GitHub Copilot API cuando Ollama no puede responder."""
        self._notificar_nivel("nivel3")

        # Gate: pedir permiso al usuario antes de consultar a Copilot
        # FP-016 Da'at: "piensa profundamente" auto-aprueba el gate
        if self.solicitar_permiso_copilot and not getattr(self, '_auto_gate_copilot', False):
            try:
                respuesta_usuario = self.solicitar_permiso_copilot(texto)
                if respuesta_usuario is None:
                    logger.info("Usuario no autorizó consulta a Copilot")
                    return None
                # Si el usuario dio instrucciones adicionales, usarlas como contexto
                if isinstance(respuesta_usuario, str) and respuesta_usuario.strip():
                    texto = f"{texto} — Indicación adicional del usuario: {respuesta_usuario}"
            except Exception as e:
                logger.warning(f"Error en gate de Copilot: {e}")
                return None

        try:
            from computadora.cerebro.copilot_api import obtener_cerebro_copilot
            copilot = obtener_cerebro_copilot()
            if not copilot.esta_autenticado():
                # Fallback a Gemini si Copilot no está autenticado
                return self._pensar_nivel3_gemini(texto)
            contexto = [
                {"role": "system", "content": (
                    "Eres Computadora, un asistente personal de escritorio. "
                    "Responde en español, corto y natural. Sin markdown ni asteriscos."
                )}
            ]
            respuesta = copilot.pensar(texto, contexto)
            if respuesta:
                limpia = self._limpiar_para_voz(respuesta)
                self._hist_append("assistant", limpia)
                # FP-015 Lemed: Detector de oportunidad post-N3
                self._detectar_promocion(texto, limpia, "nivel3")
                logger.info("Respuesta generada por Copilot (Nivel 3)")
                return limpia
            # Copilot no respondió → intentar Gemini
            return self._pensar_nivel3_gemini(texto)
        except Exception as e:
            logger.warning(f"Copilot Nivel 3 falló: {e}")
            return self._pensar_nivel3_gemini(texto)

    def _pensar_nivel3_gemini(self, texto: str) -> str | None:
        """N3 Fallback → Google Gemini API (Keter complementario)."""
        try:
            from computadora.cerebro.gemini_api import obtener_cerebro_gemini
            gemini = obtener_cerebro_gemini()
            if not gemini.esta_disponible():
                return None
            contexto = [
                {"role": "system", "content": (
                    "Eres Computadora, un asistente personal de escritorio. "
                    "Responde en español, corto y natural. Sin markdown ni asteriscos."
                )}
            ]
            respuesta = gemini.pensar(texto, contexto)
            if respuesta:
                limpia = self._limpiar_para_voz(respuesta)
                self._hist_append("assistant", limpia)
                self._detectar_promocion(texto, limpia, "nivel3")
                logger.info("Respuesta generada por Gemini (Nivel 3 fallback)")
                return limpia
        except Exception as e:
            logger.warning(f"Gemini Nivel 3 falló: {e}")
        return None

    def _pensar_sin_llm(self, texto: str) -> str:
        """Respuesta de emergencia cuando Ollama no está disponible.
        Nivel 1 expandido + Jojmá local (motor de creatividad sin LLM)."""
        texto_l = texto.lower().strip()

        # Primero intentar Nivel 1 completo (regexes + herramientas)
        nivel1 = self._pensar_nivel1(texto)
        if nivel1 is not None:
            return nivel1

        # RF-341 Jojmá Mekomít: motor de sabiduría local
        try:
            from computadora.cerebro.jojma_local import obtener_jojma_local
            jojma = obtener_jojma_local()
            humor = None
            try:
                from computadora.memoria.personalidad import Personalidad
                humor = Personalidad().humor_actual
            except Exception as e:  # RF-167
                logger.debug("Error obteniendo humor para Jojmá: %s", e)
            memoria_ctx = None
            try:
                from computadora.memoria.memoria import buscar_en_memoria
                resultados = buscar_en_memoria(texto)
                if resultados:
                    memoria_ctx = resultados[:200] if isinstance(resultados, str) else str(resultados)[:200]
            except Exception as e:  # RF-167
                logger.debug("Error buscando memoria para Jojmá: %s", e)
            respuesta = jojma.generar(texto, humor=humor, memoria_contexto=memoria_ctx)
            if respuesta:
                self._hist_append("user", texto)
                self._hist_append("assistant", respuesta)
                return respuesta
        except Exception as e:
            logger.debug("Jojmá local falló: %s", e)

        # HF-026: Mensajes diferenciados según estado del proceso Ollama
        if getattr(self, '_ollama_proceso_muerto', False):
            return (
                "Lo lamento, Ollama no se encuentra disponible en este momento, señor "
                "— el proceso no está ejecutándose. ¿Podría iniciarlo? Una vez activo, "
                "me reconectaré automáticamente. Mientras tanto, puedo abrir aplicaciones, "
                "decirle la hora y ejecutar comandos."
            )

        return (
            "Lo lamento, Ollama no se encuentra disponible en este momento, señor "
            "— el proceso está activo pero no responde, puede estar cargando el modelo. "
            "Puedo abrir aplicaciones, decirle la hora, consultar su sistema y ejecutar "
            "comandos básicos mientras tanto. Seguiré intentando reconectar."
        )
