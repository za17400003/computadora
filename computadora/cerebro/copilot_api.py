"""
Cerebro Nivel 3 — GitHub Copilot API directa via OAuth Device Flow.
NO requiere VS Code. El usuario autoriza una vez en el navegador.

Flujo:
1. POST github.com/login/device/code → obtiene user_code + device_code
2. Abre navegador en github.com/login/device → usuario ingresa user_code
3. Polling en github.com/login/oauth/access_token hasta aprobación
4. Con access_token → obtiene copilot_token de api.github.com
5. Usa copilot_token para llamar api.githubcopilot.com/chat/completions
"""

import json
import threading
import time
import webbrowser
from pathlib import Path

import httpx
from loguru import logger

# Client ID público de GitHub Copilot (mismo que usa VS Code)
_CLIENT_ID = "Iv1.b507a08c87ecfe98"

_AUTH_FILE = Path(__file__).resolve().parent.parent.parent / "datos" / "copilot_auth.json"

# Endpoints
_DEVICE_CODE_URL = "https://github.com/login/device/code"
_TOKEN_URL = "https://github.com/login/oauth/access_token"
_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
_CHAT_URL = "https://api.githubcopilot.com/chat/completions"


class CerebroCopilot:
    """Cerebro Nivel 3: GitHub Copilot Chat API con OAuth Device Flow."""

    # Da'at (דַּעַת): Modelos en orden de preferencia para código/regex
    _MODELOS_CODIGO = ["claude-sonnet-4", "gpt-4o", "gpt-4o-mini"]
    _MODELO_GRATUITO = "gpt-4o-mini"

    def __init__(self):
        self._access_token: str | None = None
        self._copilot_token: str | None = None
        self._copilot_token_expires: float = 0
        self._lock = threading.Lock()
        self._modelo_detectado: str | None = None
        self._modelo_detectado_ts: float = 0
        self._cargar_tokens()

    # ─── Persistencia ────────────────────────────────

    def _cargar_tokens(self):
        """Carga tokens guardados de sesiones anteriores."""
        if _AUTH_FILE.exists():
            try:
                data = json.loads(_AUTH_FILE.read_text(encoding="utf-8"))
                self._access_token = data.get("access_token")
                logger.info("Copilot: tokens cargados de sesión anterior")
            except Exception as e:
                logger.warning(f"Copilot: error cargando tokens: {e}")

    def _guardar_tokens(self):
        """Persiste el access_token en disco."""
        _AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"access_token": self._access_token}
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_AUTH_FILE, data)

    # ─── Autenticación ───────────────────────────────

    def esta_autenticado(self) -> bool:
        """Verifica si hay un access_token válido."""
        return self._access_token is not None

    def iniciar_autenticacion(self) -> dict | None:
        """
        Inicia el flujo OAuth Device Flow.
        Retorna dict con 'user_code' y 'verification_uri' o None si falla.
        Abre el navegador automáticamente.
        """
        try:
            resp = httpx.post(
                _DEVICE_CODE_URL,
                data={
                    "client_id": _CLIENT_ID,
                    "scope": "read:user",
                },
                headers={"Accept": "application/json"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_uri = data["verification_uri"]
            interval = data.get("interval", 5)
            expires_in = data.get("expires_in", 900)

            logger.info(f"Copilot OAuth: código={user_code}, uri={verification_uri}")

            # Abrir navegador automáticamente
            webbrowser.open(verification_uri)

            # Iniciar polling en background
            thread = threading.Thread(
                target=self._polling_autorizacion,
                args=(device_code, interval, expires_in),
                daemon=True,
            )
            thread.start()

            return {
                "user_code": user_code,
                "verification_uri": verification_uri,
            }

        except Exception as e:
            logger.error(f"Copilot: error iniciando autenticación: {e}")
            return None

    def _polling_autorizacion(self, device_code: str, interval: int, expires_in: int):
        """Polling en background hasta que el usuario autorice."""
        deadline = time.time() + expires_in

        while time.time() < deadline:
            time.sleep(interval)
            try:
                resp = httpx.post(
                    _TOKEN_URL,
                    data={
                        "client_id": _CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=15,
                )
                data = resp.json()

                if "access_token" in data:
                    with self._lock:
                        self._access_token = data["access_token"]
                        self._guardar_tokens()
                    logger.info("Copilot: ¡Autenticación exitosa!")
                    return

                error = data.get("error", "")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                elif error in ("expired_token", "access_denied"):
                    logger.warning(f"Copilot: autenticación fallida: {error}")
                    return

            except Exception as e:
                logger.warning(f"Copilot: error en polling: {e}")

        logger.warning("Copilot: autenticación expirada (timeout)")

    # ─── Copilot Token ───────────────────────────────

    def _obtener_copilot_token(self) -> str | None:
        """Obtiene/refresca el token de sesión de Copilot."""
        with self._lock:
            if self._copilot_token and time.time() < self._copilot_token_expires - 60:
                return self._copilot_token

            if not self._access_token:
                return None

            try:
                resp = httpx.get(
                    _COPILOT_TOKEN_URL,
                    headers={
                        "Authorization": f"token {self._access_token}",
                        "Accept": "application/json",
                    },
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                self._copilot_token = data.get("token")
                self._copilot_token_expires = data.get("expires_at", time.time() + 1800)
                logger.debug("Copilot: token de sesión obtenido/refrescado")
                return self._copilot_token

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("Copilot: access_token inválido, necesita re-autenticación")
                    self._access_token = None
                    self._copilot_token = None
                    if _AUTH_FILE.exists():
                        _AUTH_FILE.unlink()
                else:
                    logger.error(f"Copilot: error obteniendo token de sesión: {e}")
                return None
            except Exception as e:
                logger.error(f"Copilot: error obteniendo token de sesión: {e}")
                return None

    # ─── Chat Completions ────────────────────────────

    # ── Da'at: Selección inteligente de modelo ──

    def detectar_modelo_disponible(self) -> str:
        """Prueba modelos en orden de preferencia, retorna el mejor disponible.
        Cachea resultado 30 min para no probar cada vez."""
        if self._modelo_detectado and (time.time() - self._modelo_detectado_ts < 1800):
            return self._modelo_detectado

        token = self._obtener_copilot_token()
        if not token:
            return self._MODELO_GRATUITO

        # FP-017 Jazón: Discovery dinámico + merge con hardcodeados
        try:
            from computadora.cerebro.modelo_discovery import descubrir_modelos
            discovered = descubrir_modelos()
        except Exception as e:
            logger.debug(f"Da'at: Discovery no disponible: {e}")
            discovered = []

        # Merge: descubiertos primero, luego hardcodeados sin duplicados
        vistos = set()
        modelos = []
        for m in discovered + self._MODELOS_CODIGO:
            ml = m.lower()
            if ml not in vistos:
                vistos.add(ml)
                modelos.append(m)

        for modelo in modelos:
            try:
                resp = httpx.post(
                    _CHAT_URL,
                    json={
                        "messages": [{"role": "user", "content": "test"}],
                        "model": modelo,
                        "max_tokens": 1,
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Editor-Version": "Computadora/1.0",
                        "Copilot-Integration-Id": "vscode-chat",
                    },
                    timeout=10,
                )
                if resp.status_code < 400:
                    self._modelo_detectado = modelo
                    self._modelo_detectado_ts = time.time()
                    logger.info(f"Da'at: Modelo detectado → {modelo}")
                    return modelo
                logger.debug(f"Da'at: {modelo} → HTTP {resp.status_code}, probando siguiente")
            except Exception as e:
                logger.debug(f"Da'at: {modelo} → error: {e}, probando siguiente")

        self._modelo_detectado = self._MODELO_GRATUITO
        self._modelo_detectado_ts = time.time()
        logger.info(f"Da'at: Ningún modelo premium disponible → {self._MODELO_GRATUITO}")
        return self._MODELO_GRATUITO

    def pensar_codigo(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """Usa el MEJOR modelo disponible. Para regex y código."""
        modelo = self.detectar_modelo_disponible()
        return self._pensar_con_modelo(mensaje, contexto, modelo, temperature=0.1)

    def pensar_general(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """Usa SIEMPRE el modelo gratuito. Para conversación no-código."""
        return self._pensar_con_modelo(mensaje, contexto, self._MODELO_GRATUITO, temperature=0.3)

    def pensar(self, mensaje: str, contexto: list[dict] | None = None) -> str | None:
        """
        Envía un mensaje a Copilot Chat API y retorna la respuesta.
        Retorna None si no está autenticado o hay error.
        Mantiene compatibilidad — usa gpt-4o por defecto.
        """
        return self._pensar_con_modelo(mensaje, contexto, "gpt-4o", temperature=0.3)

    def _pensar_con_modelo(
        self,
        mensaje: str,
        contexto: list[dict] | None,
        modelo: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str | None:
        """Método interno: envía request con modelo específico."""
        token = self._obtener_copilot_token()
        if not token:
            logger.warning("Copilot: sin token, no se puede pensar")
            return None

        messages = []
        if contexto:
            messages.extend(contexto)
        messages.append({"role": "user", "content": mensaje})

        try:
            resp = httpx.post(
                _CHAT_URL,
                json={
                    "messages": messages,
                    "model": modelo,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Editor-Version": "Computadora/1.0",
                    "Copilot-Integration-Id": "vscode-chat",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            respuesta = data["choices"][0]["message"]["content"]
            logger.info(f"Copilot ({modelo}) respondió ({len(respuesta)} chars)")
            return respuesta

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self._copilot_token = None
                logger.warning("Copilot: token expirado, reintentando...")
                token = self._obtener_copilot_token()
                if token:
                    return self._pensar_con_modelo(mensaje, contexto, modelo, temperature, max_tokens)
            logger.error(f"Copilot: error HTTP {e.response.status_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Copilot: error en pensar: {e}")
            return None


# Instancia singleton (thread-safe FP-036)
_instancia: CerebroCopilot | None = None
_instancia_lock = __import__('threading').Lock()


def obtener_cerebro_copilot() -> CerebroCopilot:
    """Retorna la instancia singleton del cerebro Copilot (thread-safe FP-036)."""
    global _instancia
    if _instancia is None:
        with _instancia_lock:
            if _instancia is None:
                _instancia = CerebroCopilot()
    return _instancia


