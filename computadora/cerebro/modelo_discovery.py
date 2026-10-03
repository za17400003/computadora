"""
חָזוֹן (Jazón) — Visión: Auto-Descubrimiento de Modelos Copilot.
Camino ascendente en el Etz HaChaim: Yesod → Malkut → Da'at → Jojmá.

Busca en internet (DuckDuckGo) qué modelos ofrece GitHub Copilot,
parsea los resultados localmente (regex, sin LLM), y persiste la
configuración en datos/modelos_copilot.json con cache de 24h.
"""

import json
import re
import time
from pathlib import Path
from loguru import logger

from computadora.habilidades.herramientas import RAIZ_PROYECTO

_CACHE_PATH = Path(RAIZ_PROYECTO) / "datos" / "modelos_copilot.json"
CACHE_TTL = 86400  # 24 horas en segundos

# Whitelist estricta para nombres de modelo — previene inyección
_NOMBRE_VALIDO = re.compile(r"^[a-zA-Z0-9._-]{3,50}$")

# Regex para extraer nombres de modelo de texto web
# Captura patrones como: "gpt-4o", "claude-sonnet-4", "o3-mini", "gpt-4o-mini"
_RE_MODELO = re.compile(
    r"\b("
    r"(?:gpt-[34][\w.-]*)"          # GPT family: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
    r"|(?:claude-[\w.-]+)"           # Claude family: claude-sonnet-4, claude-opus-4
    r"|(?:o[13]-[\w.-]+)"            # Reasoning: o1-mini, o1-preview, o3-mini
    r"|(?:gemini-[\w.-]+)"           # Gemini family
    r")\b",
    re.IGNORECASE,
)

# Modelos a ignorar (no son de Copilot o no son útiles)
_MODELOS_IGNORADOS = frozenset({
    "gpt-3.5-turbo",  # legacy, no está en Copilot
})


def _prioridad_modelo(nombre: str) -> int:
    """Heurística local para ordenar modelos por calidad esperada.

    0 = máxima prioridad (mejor para código)
    3 = mínima (económico)
    """
    nl = nombre.lower()
    if "mini" in nl or "flash" in nl:
        return 3
    if "opus" in nl or "sonnet" in nl:
        return 0
    if "gpt-4o" in nl:
        return 1
    if re.search(r"\bo[13]\b", nl) or "reasoning" in nl:
        return 2
    return 2  # desconocido → probar por defecto


def _cargar_cache() -> list[str] | None:
    """Retorna modelos cacheados si el cache es válido (<24h)."""
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        ts = data.get("timestamp", 0)
        if time.time() - ts > CACHE_TTL:
            return None
        modelos = data.get("modelos", [])
        if modelos:
            logger.debug(f"Jazón: Cache válido — {len(modelos)} modelos")
            return modelos
        return None
    except Exception as e:
        logger.debug(f"Jazón: Error leyendo cache: {e}")
        return None


def _guardar_cache(modelos: list[str]):
    """Persiste modelos descubiertos con timestamp."""
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {"timestamp": time.time(), "modelos": modelos}
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_CACHE_PATH, data)
    except Exception as e:
        logger.warning(f"Jazón: Error guardando cache: {e}")


def descubrir_modelos() -> list[str]:
    """Descubre modelos disponibles en GitHub Copilot via búsqueda web.

    Retorna lista ordenada por prioridad heurística, o lista vacía si falla.
    El caller (copilot_api.py) hace merge con sus hardcodeados como fallback.
    """
    # 1. Cache check
    cached = _cargar_cache()
    if cached is not None:
        return cached

    # 2. Buscar en internet (Yesod → DuckDuckGo)
    try:
        from computadora.habilidades.web import buscar_en_internet
        texto = buscar_en_internet(
            "GitHub Copilot available AI models list 2026", max_resultados=5
        )
    except Exception as e:
        logger.warning(f"Jazón: Error en búsqueda web: {e}")
        return []

    if not texto:
        logger.info("Jazón: Búsqueda sin resultados — usando hardcodeados")
        return []

    # 3. Parsear con regex (Malkut — local, sin LLM)
    encontrados = _RE_MODELO.findall(texto)
    if not encontrados:
        logger.info("Jazón: No se encontraron nombres de modelo en resultados web")
        return []

    # 4. Validar y deduplicar
    vistos = set()
    modelos_validos = []
    for nombre in encontrados:
        nl = nombre.lower()
        if nl in vistos:
            continue
        if nl in _MODELOS_IGNORADOS:
            continue
        if not _NOMBRE_VALIDO.match(nombre):
            logger.debug(f"Jazón: Nombre rechazado por whitelist: '{nombre}'")
            continue
        vistos.add(nl)
        modelos_validos.append(nombre)

    if not modelos_validos:
        logger.info("Jazón: Todos los modelos encontrados fueron filtrados")
        return []

    # 5. Ordenar por heurística de preferencia (Da'at)
    modelos_validos.sort(key=_prioridad_modelo)

    logger.info(
        f"Jazón: {len(modelos_validos)} modelos descubiertos → "
        f"{', '.join(modelos_validos)}"
    )

    # 6. Persistir cache
    _guardar_cache(modelos_validos)

    return modelos_validos


