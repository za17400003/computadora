from loguru import logger
"""
Configuración global de Computadora.
Lee config.json y .env
"""

import json
import os
from pathlib import Path

# `python-dotenv` es opcional — si no está instalado, seguimos sin .env
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except Exception as e:  # RF-167
    logger.debug("Excepcion ignorada: %s", e)
    load_dotenv = None
    _HAS_DOTENV = False


class Configuracion:
    def __init__(self):
        self._raiz = Path(__file__).parent.parent
        self._cargar_env()
        self._cargar_json()

    def _cargar_env(self):
        archivo_env = self._raiz / "_config" / ".env"
        if archivo_env.exists():
            if _HAS_DOTENV and load_dotenv is not None:
                load_dotenv(archivo_env)
            else:
                # Si falta python-dotenv, simplemente no cargamos .env pero no fallamos
                try:
                    # Intentar parse sencillo: KEY=VAL por línea
                    with open(archivo_env, "r", encoding="utf-8") as f:
                        for ln in f:
                            ln = ln.strip()
                            if not ln or ln.startswith("#") or "=" not in ln:
                                continue
                            k, v = ln.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"'))
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

    def _cargar_json(self):
        archivo_json = self._raiz / "_config" / "config.json"
        if archivo_json.exists():
            with open(archivo_json, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            self._config = {}

    # Mapa de claves sensibles → variables de entorno (.env)
    _ENV_OVERRIDES = {
        "discord.token": "DISCORD_TOKEN",
        "telegram.token": "TELEGRAM_TOKEN",
        "gemini.api_key": "GEMINI_API_KEY",
    }

    def obtener(self, clave: str, defecto=None):
        """
        Obtiene un valor de configuración usando notación de punto.
        Ejemplo: config.obtener("whisper.modelo") → "base"
        Los tokens sensibles se resuelven desde .env si config.json los tiene vacíos.
        """
        partes = clave.split(".")
        valor = self._config
        for parte in partes:
            if isinstance(valor, dict) and parte in valor:
                valor = valor[parte]
            else:
                return defecto
        # Si el valor está vacío y hay override de env, usar .env
        if not valor and clave in self._ENV_OVERRIDES:
            valor = os.getenv(self._ENV_OVERRIDES[clave], defecto)
        return valor

    def env(self, clave: str, defecto=None) -> str:
        """Obtiene una variable de entorno."""
        return os.getenv(clave, defecto)

    @property
    def raiz(self) -> Path:
        return self._raiz


# ─── Timeouts Ollama (FP-023 WI-116) ───
TIMEOUT_OLLAMA_DEFAULT = 90
TIMEOUT_OLLAMA_MIN = 30
# FIX: 180s amplificaba el problema de solicitudes huérfanas/concurrentes —
# un pico de lentitud (p.ej. por el bug de concurrencia ya corregido en
# OllamaGuard) inflaba el promedio de latencias recientes y ese techo alto
# dejaba que el siguiente timeout se quedara igual de alto por un buen rato,
# incluso ya sin contención real. 90s es suficiente para una respuesta
# honesta y legítimamente lenta sin arrastrar tanto una degradación pasada.
TIMEOUT_OLLAMA_MAX = 90


