"""
Habilidad de búsqueda web de la Computadora.
Usa DuckDuckGo para buscar información en internet.
COMPUTADORA decide cuándo necesita buscar algo por sí mismo.
"""

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from loguru import logger


def buscar_en_internet(consulta: str, max_resultados: int = 5) -> str:
    """
    Busca en internet y devuelve un resumen textual de los resultados.
    Retorna string vacío si falla.
    """
    logger.info(f"Buscando en internet: '{consulta}'")

    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, region="es-mx", max_results=max_resultados))

        if not resultados:
            logger.warning(f"Sin resultados para: '{consulta}'")
            return ""

        lineas = []
        for i, r in enumerate(resultados, 1):
            titulo = r.get("title", "")
            cuerpo = r.get("body", "")
            lineas.append(f"{i}. {titulo}: {cuerpo}")

        texto = "\n".join(lineas)
        logger.info(f"Resultados obtenidos: {len(resultados)}")
        return texto

    except Exception as e:
        logger.error(f"Error buscando en internet: {e}")
        return ""


