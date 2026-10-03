"""
Cerebro Nivel 3b — Google Gemini API (Keter complementario).

Usa API key de Google AI Studio (NO credenciales de usuario).
Obtener la clave en: https://aistudio.google.com/apikey

La clave se almacena en .env como GEMINI_API_KEY.

Flujo:
1. Lee GEMINI_API_KEY de .env o config.json
2. Usa REST API de Gemini (generativelanguage.googleapis.com)
3. Interfaz idéntica a CerebroCopilot: pensar(), pensar_codigo(), pensar_general()
"""

import json
import threading
import time
from pathlib import Path

import httpx
from loguru import logger

# ── Configuración ──
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_MODELO_DEFAULT = "gemini-2.0-flash"
_MODELO_PRO = "gemini-2.5-pro-preview-06-05"

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _CONFIG_DIR / ".env"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def _cargar_api_key() -> str | None:
    """Carga GEMINI_API_KEY desde .env o config.json."""
    # Primero .env
    if _ENV_FILE.exists():
        for linea in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea.startswith("GEMINI_API_KEY="):
                val = linea.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val

    # Fallback: config.json → api.gemini_key
    if _CONFIG_FILE.exists():
        try:
            cfg = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            key = cfg.get("api", {}).get("gemini_key", "")
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            pass

    return None


class CerebroGemini:
    """Cerebro Nivel 3b: Google Gemini API via REST."""

    def __init__(self):
        self._api_key: str | None = _cargar_api_key()
        self._lock = threading.Lock()
        if self._api_key:
            logger.info("CerebroGemini: API key cargada correctamente")
        else:
            logger.warning(
                "CerebroGemini: Sin API key. Configura GEMINI_API_KEY en .env "
                "o api.gemini_key en config.json. Obtén la clave en https://aistudio.google.com/apikey"
            )

    def esta_disponible(self) -> bool:
        """Verifica si Gemini está configurado."""
        return self._api_key is not None

    def pensar(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """Envía un mensaje a Gemini y retorna la respuesta."""
        return self._pensar_con_modelo(mensaje, contexto, _MODELO_DEFAULT, temperature=0.3)

    def pensar_codigo(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """Usa el modelo Pro para tareas de código/razonamiento complejo."""
        return self._pensar_con_modelo(mensaje, contexto, _MODELO_PRO, temperature=0.1)

    def pensar_general(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """Usa el modelo Flash para conversación general."""
        return self._pensar_con_modelo(mensaje, contexto, _MODELO_DEFAULT, temperature=0.5)

    def _pensar_con_modelo(
        self,
        mensaje: str,
        contexto: list[dict] | None,
        modelo: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        _retry_count: int = 0,
    ) -> str | None:
        """Método interno: envía request a Gemini REST API."""
        if not self._api_key:
            logger.warning("CerebroGemini: sin API key, no se puede pensar")
            return None

        # Construir contents en formato Gemini
        contents = []

        # System instruction (si hay contexto con role=system)
        system_text = None
        if contexto:
            for msg in contexto:
                if msg.get("role") == "system":
                    system_text = msg["content"]
                elif msg.get("role") in ("user", "assistant"):
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })

        # Mensaje actual
        contents.append({
            "role": "user",
            "parts": [{"text": mensaje}]
        })

        # Payload (API key en header, no en URL — OWASP A02:2021 Cryptographic Failures)
        _MODELOS_VALIDOS = {_MODELO_DEFAULT, _MODELO_PRO}
        if modelo not in _MODELOS_VALIDOS:
            logger.error(f"CerebroGemini: modelo no permitido: {modelo!r}")
            return None
        url = f"{_GEMINI_URL}/{modelo}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_text}]
            }

        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # Extraer texto de respuesta
            candidates = data.get("candidates", [])
            if not candidates:
                logger.warning("CerebroGemini: respuesta sin candidatos")
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return None

            respuesta = parts[0].get("text", "")
            logger.info(f"Gemini ({modelo}) respondió ({len(respuesta)} chars)")
            return respuesta

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 400:
                logger.error(f"CerebroGemini: request inválido — {e.response.text[:200]}")
            elif status == 403:
                logger.error("CerebroGemini: API key inválida o sin permisos")
            elif status == 429:
                if _retry_count >= 3:
                    logger.error("CerebroGemini: rate limit excedido, máximo de reintentos alcanzado")
                    return None
                logger.warning(f"CerebroGemini: rate limit excedido, reintento {_retry_count + 1}/3...")
                time.sleep(2 ** (_retry_count + 1))  # Backoff exponencial: 2, 4, 8s
                return self._pensar_con_modelo(mensaje, contexto, modelo, temperature, max_tokens, _retry_count=_retry_count + 1)
            else:
                logger.error(f"CerebroGemini: HTTP {status}: {e}")
            return None
        except Exception as e:
            logger.error(f"CerebroGemini: error en pensar: {e}")
            return None


# Singleton (thread-safe)
_instancia: CerebroGemini | None = None
_instancia_lock = threading.Lock()


def obtener_cerebro_gemini() -> CerebroGemini:
    """Retorna la instancia singleton del cerebro Gemini (thread-safe)."""
    global _instancia
    if _instancia is None:
        with _instancia_lock:
            if _instancia is None:
                _instancia = CerebroGemini()
    return _instancia


