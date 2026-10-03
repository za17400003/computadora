"""
🛡️ Guardián del Enciclopedia — Vigilante de intrusiones y acceso (שמירה Shmirah)

Monitorea el archivo de eventos del Enciclopedia (enciclopedia_intrusiones.jsonl).
Detecta:
  - acceso_denegado: Alguien falló 3 veces la contraseña → alerta de intrusión
  - acceso_concedido: El amo abrió el Enciclopedia → COMPUTADORA lo sabe

Notifica a Computadora vía BusEventos para que reaccione con voz y emoción.

Uso:
    from computadora.canales.enciclopedia_guardian import EnciclopediaGuardian
    guardian = EnciclopediaGuardian(personalidad)
    guardian.iniciar()  # Lanza hilo daemon
"""

import json
import threading
from pathlib import Path

from loguru import logger

from computadora.nucleo.eventos import obtener_bus

_INTRUSION_LOG = Path(__file__).parent.parent.parent / "datos" / "enciclopedia_intrusiones.jsonl"
_POLL_INTERVAL = 3  # segundos entre verificaciones


class EnciclopediaGuardian:
    """Vigila eventos del Enciclopedia y alerta a COMPUTADORA."""

    def __init__(self, personalidad=None):
        self._personalidad = personalidad
        self._detener = threading.Event()
        self._ultima_linea = 0
        self._hilo: threading.Thread | None = None
        # Inicializar offset al estado actual del archivo
        if _INTRUSION_LOG.exists():
            with open(_INTRUSION_LOG, "r", encoding="utf-8") as f:
                self._ultima_linea = sum(1 for _ in f)

    def iniciar(self):
        """Inicia vigilancia en hilo daemon."""
        self._hilo = threading.Thread(
            target=self._vigilar, daemon=True, name="EnciclopediaGuardian"
        )
        self._hilo.start()
        logger.info("🛡️ EnciclopediaGuardian activo — vigilando el Enciclopedia")

    def detener(self):
        self._detener.set()

    def _vigilar(self):
        """Loop principal: revisa nuevas líneas en el archivo de eventos."""
        while not self._detener.is_set():
            try:
                self._revisar_eventos()
            except Exception as e:
                logger.error(f"EnciclopediaGuardian error: {e}")
            self._detener.wait(_POLL_INTERVAL)

    def _revisar_eventos(self):
        if not _INTRUSION_LOG.exists():
            return

        with open(_INTRUSION_LOG, "r", encoding="utf-8") as f:
            lineas = f.readlines()

        nuevas = lineas[self._ultima_linea:]
        self._ultima_linea = len(lineas)

        for linea in nuevas:
            linea = linea.strip()
            if not linea:
                continue
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                continue

            tipo = evento.get("evento")
            if tipo == "acceso_denegado":
                self._procesar_intrusion(evento)
            elif tipo == "acceso_concedido":
                self._procesar_apertura(evento)

    def _procesar_intrusion(self, alerta: dict):
        ts = alerta.get("ts", "desconocido")
        intentos = alerta.get("intentos", 3)

        logger.warning(
            f"🚨 INTRUSIÓN DETECTADA — {intentos} intentos fallidos al Enciclopedia [{ts}]"
        )

        bus = obtener_bus()
        bus.emitir("intrusion_enciclopedia", alerta)

        if self._personalidad:
            self._personalidad.registrar_intrusion_enciclopedia(intentos)

    def _procesar_apertura(self, evento: dict):
        ts = evento.get("ts", "desconocido")

        logger.info(f"📖 Enciclopedia abierto por el amo [{ts}]")

        bus = obtener_bus()
        bus.emitir("enciclopedia_abierto", evento)

        if self._personalidad:
            self._personalidad.registrar_apertura_enciclopedia()


