"""
שמירה (Shmirah) — Custodia.
Gestor de permisos one-shot de la Computadora.
Cada permiso se consume al usarse. NO se almacenan permisos permanentes.
Log inmutable en datos/permisos_log.jsonl.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "datos" / "permisos_log.jsonl"


class GestorPermisos:
    """Sistema de permisos one-shot para acciones del sistema."""

    def __init__(self):
        self._callback_pedir_permiso = None
        self._lock = threading.Lock()

    def set_callback(self, fn):
        """Inyecta callback de la UI para pedir permisos interactivos.
        fn(accion: str, nivel: str) -> bool
        """
        self._callback_pedir_permiso = fn

    def solicitar(self, accion: str, nivel: str = "info", *, orden_directa: bool = False) -> bool:
        """
        Solicita permiso para una acción.
        - nivel "info": auto-aprobado (solo lectura)
        - nivel "accion": requiere confirmación del usuario via UI
        - nivel "admin": requiere confirmación + posible UAC
        FP-042: orden_directa=True auto-aprueba "accion" (el usuario dio la orden directamente).
        Retorna True si aprobado, False si denegado/timeout.
        """
        if nivel not in ("info", "accion", "admin"):
            logger.warning(f"Nivel de permiso inválido: {nivel}")
            self._registrar(accion, nivel, "denegado_nivel_invalido")
            return False

        # Info es auto-aprobado (solo-lectura)
        if nivel == "info":
            self._registrar(accion, nivel, "auto_aprobado")
            return True

        # FP-042 Pekudá Yeshirá: orden directa auto-aprueba "accion"
        if orden_directa and nivel == "accion":
            self._registrar(accion, nivel, "auto_aprobado_orden_directa")
            return True

        # Accion y admin requieren confirmación del usuario
        if self._callback_pedir_permiso is None:
            logger.warning(f"Permiso '{nivel}' solicitado sin callback UI: {accion}")
            self._registrar(accion, nivel, "denegado_sin_ui")
            return False

        try:
            # Timeout: 30 segundos para que el usuario responda
            resultado = [None]
            evento = threading.Event()

            def _pedir():
                try:
                    resultado[0] = self._callback_pedir_permiso(accion, nivel)
                except Exception as e:
                    logger.error(f"Error en callback de permiso: {e}")
                    resultado[0] = False
                finally:
                    evento.set()

            hilo = threading.Thread(target=_pedir, daemon=True)
            hilo.start()
            aprobado = evento.wait(timeout=30.0) and resultado[0] is True

            if not aprobado:
                self._registrar(accion, nivel, "denegado_usuario" if evento.is_set() else "timeout")
                return False

            self._registrar(accion, nivel, "aprobado")
            return True

        except Exception as e:
            logger.error(f"Error solicitando permiso: {e}")
            self._registrar(accion, nivel, f"error: {e}")
            return False

    def _registrar(self, accion: str, nivel: str, resultado: str):
        """Log inmutable de cada solicitud de permiso."""
        entrada = {
            "ts": datetime.now().isoformat(),
            "accion": accion[:200],
            "nivel": nivel,
            "resultado": resultado,
        }
        try:
            with self._lock:
                _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug(f"Error escribiendo log de permisos: {e}")


