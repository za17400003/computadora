"""
Configuración de logging con loguru.
"""

import sys
from datetime import datetime
from pathlib import Path


def configurar_logs():
    from loguru import logger

    # Remover handler por defecto
    logger.remove()

    # Consola con color
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}",
        level="INFO",
    )

    # Archivo de log con rotación — usar datetime.now() en lugar de {time:YYYY-MM-DD}
    directorio_logs = Path(__file__).parent.parent.parent / "datos" / "logs"
    directorio_logs.mkdir(parents=True, exist_ok=True)

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_log = directorio_logs / f"computadora_{fecha_hoy}.log"

    logger.add(
        archivo_log,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8",
    )

    logger.info("Sistema de logs inicializado")


