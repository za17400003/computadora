"""
FP-027 WI-154: Parseo de tool calls extraído de Tiféret (nlu.py).
Funciones puras para extraer, reparar y detectar herramientas en respuestas LLM.
"""

import json
import re
import threading
from typing import Callable, Optional

from loguru import logger


# ── Normalización de comillas Unicode ────────────────────────────────

def normalizar_comillas(texto: str) -> str:
    """Reemplaza comillas tipográficas/Unicode por comillas ASCII estándar."""
    for ch in ('\u201c', '\u201d', '\u201e', '\u201f', '\u00ab', '\u00bb',
               '\u2018', '\u2019', '\u201a', '\u201b',
               '\u00f4', '\u00f6',  # ô ö — artefactos comunes de encoding
               '\uff02', '\u02ee', '\u02ba', '\u02dd',
               '\u2033', '\u2036', '\u3003'):
        texto = texto.replace(ch, '"')
    return texto


# ── Regex compilados ─────────────────────────────────────────────────

# Non-greedy match: captura JSON entre delimitadores tool (ReDoS-safe)
TOOL_PATTERN = re.compile(r"```tool\s*\n?\s*(\{.*?\})\s*\n?\s*```", re.DOTALL)
TOOL_JSON_PATTERN = re.compile(r'\{\s*["\u201c\u00f4]\s*herramienta', re.DOTALL)

# Palabras clave que sugieren que el usuario quiere acción sobre archivos/código
PISTAS_HERRAMIENTAS = re.compile(
    r"(modifica|cambia|edita|lee|crea|agrega|quita|borra|elimina|"
    r"tu código|tu archivo|tu cerebro|tu oído|tu voz|tu config|"
    r"estructura|archivos|directorio|carpeta|proyecto\s+\w+|continua|"
    r"instala|ejecuta|corre|busca en internet|investiga|"
    r"busca\s+(?:todo|información|info|datos|algo)\b|"
    r"dime\s+(?:todo|sobre|acerca)|búscame|averigua|"
    r"encuentra\s+(?:todo|información)|"
    r"hazme|genera|escribe|programa|desarrolla|implementa|"
    # Datos actuales/externos que requieren buscar_en_internet (WI tool-calling
    # nativo): precios, clima, noticias — el caso real reportado por el
    # usuario ("¿a cuánto está el dólar?") no matcheaba ningún patrón previo.
    r"a\s+cu[áa]nto\s+est[áa]|cu[áa]nto\s+(?:cuesta|vale|est[áa])|"
    r"precio\s+(?:de|del|actual)|cotizaci[óo]n|tipo\s+de\s+cambio|"
    r"\bclima\b|qu[eé]\s+tiempo\s+hace|"
    r"pron[oó]stico(?:\s+del?\s+tiempo)?|"
    r"noticias?\s+(?:de|sobre|hoy|actuales?)|qu[eé]\s+pas[oó]\s+con|"
    r"[uú]ltima\s+hora|resultado\s+(?:del?\s+)?(?:partido|juego))",
    re.IGNORECASE,
)

# Pistas específicas de que necesita Copilot — SOLO automejorar Computadora o proyectos VS Code
PISTAS_COPILOT = re.compile(
    r"(mejora\s+tu\s+(código|cerebro|interfaz|voz|oído)|automejorar|automejora|"
    r"modifica\s+tu\s+(código|cerebro|interfaz|voz)|cambia\s+tu\s+(código|cerebro)|"
    r"en\s+mi\s+proyecto\s+de\s+(vs\s*code|visual\s*studio|vscode)|"
    r"proyecto\s+de\s+(vs\s*code|visual\s*studio|vscode))",
    re.IGNORECASE,
)


# ── Funciones de parseo ──────────────────────────────────────────────

def regex_safe(pattern: str, text: str, timeout_ms: int = 200):
    """FP-023 WI-121: Ejecuta regex con timeout para prevenir ReDoS.
    Retorna Match o None. En timeout retorna None."""
    resultado = [None]

    def _buscar():
        try:
            resultado[0] = re.search(pattern, text)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

    hilo = threading.Thread(target=_buscar, daemon=True)
    hilo.start()
    hilo.join(timeout=timeout_ms / 1000.0)
    return resultado[0]


def reparar_json_herramienta(texto: str) -> str | None:
    """
    Intenta reparar JSON malformado de tool calls.
    Caso común: "buscar": "idioma": "es-MX" → "buscar": "\"idioma\": \"es-MX\""
    """
    m_herr = re.search(r'"herramienta"\s*:\s*"([^"]+)"', texto)
    if not m_herr:
        return None

    herramienta = m_herr.group(1)

    m_args = re.search(r'"args"\s*:\s*\{(.*)\}', texto, re.DOTALL)
    if not m_args:
        return None

    args_texto = m_args.group(1).strip()

    args = {}
    partes = re.split(r',\s*(?="[a-z_]+"\s*:)', args_texto)
    for parte in partes:
        m = re.match(r'"([a-z_]+)"\s*:\s*(.*)', parte.strip(), re.DOTALL)
        if m:
            key = m.group(1)
            val_raw = m.group(2).strip().rstrip(",")
            if val_raw.startswith('"') and val_raw.endswith('"'):
                val = val_raw[1:-1]
            elif val_raw.startswith('"'):
                val = val_raw.strip('"').rstrip(',').rstrip('"')
            else:
                val = val_raw.strip('"')
            val = val.replace('"', '').replace('{', '').replace('}', '').strip()
            args[key] = val

    if args:
        return json.dumps({"herramienta": herramienta, "args": args})
    return None


def extraer_tool_por_nombre(respuesta: str) -> dict | None:
    """
    Fallback: si el modelo nombró una herramienta conocida sin formato JSON,
    intenta construir el tool call. Solo para herramientas sin args o con args simples.
    """
    from computadora.habilidades.herramientas import HERRAMIENTAS
    texto = respuesta.lower()
    for nombre in HERRAMIENTAS:
        if nombre in texto:
            # Herramientas sin args
            if nombre in ("obtener_fecha_hora", "obtener_info_sistema",
                          "listar_tareas", "listar_notas", "listar_recordatorios",
                          "leer_portapapeles", "diagnostico_sistema",
                          "tomar_captura_pantalla", "info_entorno",
                          "listar_tareas_diferidas", "listar_proyectos",
                          "resumen_proyectos", "demo_visual"):
                logger.info(f"Fallback: herramienta '{nombre}' detectada por nombre")
                return {"herramienta": nombre, "args": {}}
            if nombre == "listar_directorio":
                logger.info("Fallback: listar_directorio detectada por nombre (args default)")
                return {"herramienta": nombre, "args": {"ruta": "."}}
            # Herramientas con arg extraíble del texto
            if nombre == "buscar_en_internet":
                # Extraer consulta: texto después del nombre de la herramienta o del verbo
                m = re.search(r"(?:buscar?\s+en\s+internet|buscar_en_internet)[:\s]+(.+)", respuesta, re.IGNORECASE)
                if not m:
                    m = re.search(r"(?:investiga|busca|búscame)\s+(?:sobre\s+|en\s+internet\s+)?(.+)", respuesta, re.IGNORECASE)
                consulta = m.group(1).strip().rstrip(".") if m else respuesta.replace("buscar_en_internet", "").strip().strip(":'\"").strip()
                if consulta:
                    logger.info(f"Fallback: buscar_en_internet('{consulta}') detectada por nombre")
                    return {"herramienta": nombre, "args": {"consulta": consulta}}
            if nombre == "consultar_memoria":
                m = re.search(r"(?:consultar?_?memoria|recuerd[ao]s?|qué\s+(?:recuerdas|hablamos))[:\s]+(.+)", respuesta, re.IGNORECASE)
                consulta = m.group(1).strip().rstrip(".") if m else "reciente"
                logger.info(f"Fallback: consultar_memoria('{consulta}') detectada por nombre")
                return {"herramienta": nombre, "args": {"consulta": consulta, "dias": 5}}
            if nombre == "leer_archivo":
                m = re.search(r"(?:leer?_?archivo|lee(?:r)?)[:\s]+([\w/.\-]+)", respuesta, re.IGNORECASE)
                if m:
                    ruta = m.group(1).strip()
                    logger.info(f"Fallback: leer_archivo('{ruta}') detectada por nombre")
                    return {"herramienta": nombre, "args": {"ruta": ruta}}
            if nombre == "buscar_en_codigo":
                m = re.search(r"(?:buscar?_?en_?codigo|busca(?:r)?\s+en\s+(?:el\s+)?código)[:\s]+(.+)", respuesta, re.IGNORECASE)
                if m:
                    logger.info(f"Fallback: buscar_en_codigo('{m.group(1).strip()}')")
                    return {"herramienta": nombre, "args": {"patron": m.group(1).strip()}}
            if nombre in ("abrir_aplicacion", "cerrar_aplicacion"):
                m = re.search(
                    r"(?:abr[eio]r?|cerr[ao]r?|lanz[ao]r?|inici[ao]r?)\s+(\w[\w\s]{0,30})",
                    respuesta, re.IGNORECASE)
                if m:
                    app = m.group(1).strip().rstrip(".")
                    logger.info(f"Fallback: {nombre}('{app}') detectada por nombre")
                    return {"herramienta": nombre, "args": {"nombre": app}}
            if nombre == "controlar_volumen":
                for acc, val in [("sub", "subir"), ("baj", "bajar"),
                                 ("mut", "mute"), ("silenci", "mute")]:
                    if acc in texto:
                        return {"herramienta": nombre, "args": {"accion": val}}
            if nombre == "confirmar":
                m = re.search(r"(?:confirmar?)[:\s]+['\"]?(.+?)['\"]?$", respuesta, re.IGNORECASE)
                if m:
                    return {"herramienta": nombre, "args": {"respuesta": m.group(1).strip()}}
    return None


def extraer_tool_call(respuesta: str) -> dict | None:
    """
    Extrae un tool call de la respuesta del LLM.
    Soporta formato ```tool {...} ```, JSON directo, y nombres de herramienta sueltos.
    Normaliza comillas Unicode/fancy antes de parsear.
    """
    resp_norm = normalizar_comillas(respuesta)
    candidatos = []

    # 1) Formato ```tool { ... } ```
    match = TOOL_PATTERN.search(resp_norm)
    if match:
        candidatos.append(match.group(1))

    # 2) JSON directo con {"herramienta": ...}
    if TOOL_JSON_PATTERN.search(resp_norm):
        idx = resp_norm.find('{"herramienta"')
        if idx < 0:
            idx = resp_norm.find('{ "herramienta"')
        if idx < 0:
            idx = resp_norm.find('{{"herramienta"')
        if idx < 0:
            idx = resp_norm.find('{{ "herramienta"')
        if idx >= 0:
            fin = resp_norm.rfind("}") + 1
            if fin > idx:
                candidatos.append(resp_norm[idx:fin])

    for json_texto in candidatos:
        norm = json_texto.strip()
        while len(norm) > 2 and norm[0] == '{' and norm[1] == '{' and norm[-1] == '}' and norm[-2] == '}':
            norm = norm[1:-1]
        while norm.count('}') > norm.count('{') and norm.endswith('}'):
            norm = norm[:-1]
        while norm.count('{') > norm.count('}') and norm.startswith('{'):
            norm = norm[1:]
        try:
            datos = json.loads(norm)
            # RF-232: Mapear keys en inglés a español (Ollama a veces responde en inglés)
            if "tool" in datos and "herramienta" not in datos:
                datos["herramienta"] = datos.pop("tool")
            if "arguments" in datos and "args" not in datos:
                datos["args"] = datos.pop("arguments")
            if "herramienta" in datos:
                if "args" not in datos:
                    datos["args"] = {}
                return datos
        except json.JSONDecodeError:
            pass
        try:
            reparado = reparar_json_herramienta(norm)
            if reparado:
                datos = json.loads(reparado)
                if "herramienta" in datos:
                    if "args" not in datos:
                        datos["args"] = {}
                    logger.debug(f"Tool call reparado: {reparado[:200]}")
                    return datos
        except (json.JSONDecodeError, Exception):
            pass

    # 3) Fallback: el modelo mencionó una herramienta por nombre sin JSON
    herramienta_encontrada = extraer_tool_por_nombre(respuesta)
    if herramienta_encontrada:
        return herramienta_encontrada

    if candidatos:
        logger.warning(f"No pude parsear tool call: {candidatos[0][:200]}")
    return None


def detectar_accion_implicita(
    respuesta_ollama: str,
    texto_usuario: str,
    pensar_nivel1_fn: Optional[Callable[[str], Optional[str]]] = None,
) -> str | None:
    """
    Detecta cuando Ollama DESCRIBIÓ una acción sin ejecutarla.
    Ej: "procedo a abrir el explorador de archivos" → ejecutar realmente.
    Primero intenta re-procesar el input original con Nivel 1.
    Si no, busca acciones descritas en la respuesta de Ollama.
    """
    # 1) Intentar Nivel 1 con el texto ORIGINAL del usuario
    if pensar_nivel1_fn is not None:
        resultado_n1 = pensar_nivel1_fn(texto_usuario)
        if resultado_n1 is not None:
            logger.info("Acción implícita resuelta por Nivel 1 (input original)")
            return resultado_n1

    # 2) Buscar patrones de acción en la RESPUESTA de Ollama
    resp = respuesta_ollama.lower()
    indicadores = (
        "procedo a ", "voy a ", "ahora mismo", "enseguida",
        "te abro", "te cierro", "abriendo", "cerrando",
        "déjame abrir", "dejame abrir", "ya te lo abro",
    )
    if not any(ind in resp for ind in indicadores):
        return None

    # Detectar abrir app en la respuesta
    m = re.search(
        r"(?:abr[ioí]r?|lanz[ao]r?|inici[ao]r?|abriendo)\s+(?:el\s+|la\s+|los\s+|las\s+)?(.+?)(?:\s+(?:ahora|enseguida|para\s+ti|por\s+ti)|\.|,|$)",
        respuesta_ollama, re.IGNORECASE,
    )
    if m:
        app = m.group(1).strip().rstrip(".")
        if 2 < len(app) < 40:
            logger.info(f"Acción implícita detectada: abrir_aplicacion('{app}')")
            from computadora.habilidades.herramientas import ejecutar_herramienta
            resultado = ejecutar_herramienta("abrir_aplicacion", {"nombre": app})
            return resultado if resultado else f"Listo, abrí {app}."

    # Detectar cerrar app en la respuesta
    m = re.search(
        r"(?:cerr[ao]r?|cerrando|termin[ao]r?)\s+(?:el\s+|la\s+|los\s+|las\s+)?(.+?)(?:\s+(?:ahora|enseguida)|\.|,|$)",
        respuesta_ollama, re.IGNORECASE,
    )
    if m:
        app = m.group(1).strip().rstrip(".")
        if 2 < len(app) < 40:
            logger.info(f"Acción implícita detectada: cerrar_aplicacion('{app}')")
            from computadora.habilidades.herramientas import ejecutar_herramienta
            resultado = ejecutar_herramienta("cerrar_aplicacion", {"nombre": app})
            return resultado if resultado else f"Listo, cerré {app}."

    return None


