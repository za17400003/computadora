"""
Gestion de Procesos - Pool de procesos para evitar huerfanos.

RF-298: Gestion Recursos Terminales - Procesos Huérfanos + Duplicados
"""

import subprocess
import threading
import time
from typing import List, Optional
from loguru import logger


class GestorProcesos:
    """Pool de procesos con cleanup automatico."""

    def __init__(self):
        self._procesos: List[subprocess.Popen] = []
        self._lock = threading.Lock()
        # Cleanup automatico cada 60s
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def lanzar(self, args: List[str], **kwargs) -> subprocess.Popen:
        """Lanza proceso y lo registra para cleanup."""
        with self._lock:
            proceso = subprocess.Popen(args, **kwargs)
            self._procesos.append(proceso)
            logger.debug(f"Proceso registrado: PID {proceso.pid}")
            return proceso

    def _cleanup_loop(self):
        """Loop de cleanup cada 60s."""
        while True:
            time.sleep(60)
            self._limpiar_terminados()

    def _limpiar_terminados(self):
        """Remueve procesos terminados de la lista."""
        with self._lock:
            vivos = []
            for p in self._procesos:
                if p.poll() is None:
                    vivos.append(p)
                else:
                    logger.debug(f"Proceso limpiado: PID {p.pid} (exit {p.returncode})")
            self._procesos = vivos

    def terminar_todos(self):
        """Termina todos los procesos vivos."""
        with self._lock:
            for p in self._procesos:
                if p.poll() is None:
                    try:
                        p.terminate()
                        logger.info(f"Proceso terminado: PID {p.pid}")
                    except Exception as e:
                        logger.warning(f"Error terminando PID {p.pid}: {e}")
            self._procesos.clear()


# Singleton global
_gestor_procesos: Optional[GestorProcesos] = None


def obtener_gestor_procesos() -> GestorProcesos:
    """Obtiene el gestor global de procesos."""
    global _gestor_procesos
    if _gestor_procesos is None:
        _gestor_procesos = GestorProcesos()
    return _gestor_procesos

