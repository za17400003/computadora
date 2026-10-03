"""
יסוד (Yesod) — Sistema de eventos pub/sub para comunicación entre módulos.
Singleton global: todos los módulos comparten la misma instancia.

Eventos estándar:
  - herramienta_iniciada   {nombre, args}
  - herramienta_completada {nombre, resultado, ok}
  - herramienta_error      {nombre, error}
  - permiso_solicitado     {accion, nivel, resultado}
  - keter_auditoria        {tipo, reporte}
  - fase_circadiana        {fase_anterior, fase_nueva}
"""

from typing import Callable, Any
from loguru import logger


class BusEventos:
    """Pub/Sub desacoplado. Thread-safe para callbacks ligeros."""

    def __init__(self):
        self._suscriptores: dict[str, list[Callable]] = {}

    def suscribir(self, evento: str, callback: Callable):
        self._suscriptores.setdefault(evento, []).append(callback)
        logger.debug(f"BusEventos: +suscripción '{evento}'")

    def emitir(self, evento: str, datos: Any = None):
        for callback in self._suscriptores.get(evento, []):
            try:
                callback(datos)
            except Exception as e:
                logger.error(f"BusEventos: error en callback '{evento}': {e}")

    def desuscribir(self, evento: str, callback: Callable):
        if evento in self._suscriptores:
            self._suscriptores[evento] = [
                cb for cb in self._suscriptores[evento] if cb != callback
            ]

    @property
    def stats(self) -> dict:
        """Resumen de eventos y suscriptores activos."""
        return {ev: len(cbs) for ev, cbs in self._suscriptores.items() if cbs}


# ═══════════════════════════════════════════════
# SINGLETON — Instancia global única
# ═══════════════════════════════════════════════

_bus_global: BusEventos | None = None
_bus_global_lock = __import__('threading').Lock()


def obtener_bus() -> BusEventos:
    """Retorna la instancia singleton del BusEventos (thread-safe FP-038)."""
    global _bus_global
    if _bus_global is None:
        with _bus_global_lock:
            if _bus_global is None:
                _bus_global = BusEventos()
                logger.info("BusEventos singleton inicializado")
    return _bus_global


