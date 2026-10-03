"""
כתר (Keter) — Corona. Auto-renovación de Computadora.
Hot-Reload: detecta cambios en archivos .py y recarga módulos sin reiniciar.
Preserva estado crítico (Whisper en VRAM, historial, colas).
"""

import importlib
import sys
import time
from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QFileSystemWatcher, QObject, QTimer, pyqtSignal
from loguru import logger

# ═══════════════════════════════════════════════
# CLASIFICACIÓN DE CAPAS
# ═══════════════════════════════════════════════

CAPAS = {
    "cerebro":      "computadora/cerebro",
    "voz":          "computadora/voz",
    "habilidades":  "computadora/habilidades",
    "interfaz":     "computadora/interfaz",
    "memoria":      "computadora/memoria",
    "nucleo":       "computadora/nucleo",
    "expresion":    "computadora/expresion",
    "utilidades":   "computadora/utilidades",
}

# Capas que requieren reinicio manual (importlib.reload no actualiza instancias vivas)
CAPAS_REINICIO_MANUAL = {"interfaz", "voz"}


def clasificar_capa(ruta: Path) -> str | None:
    """Determina a qué capa pertenece un archivo por su ruta."""
    ruta_str = ruta.as_posix()
    for capa, prefijo in CAPAS.items():
        if prefijo in ruta_str:
            return capa
    return None


def ruta_a_modulo(ruta: Path, raiz_proyecto: Path) -> str | None:
    """Convierte ruta absoluta a nombre de módulo Python (computadora.cerebro.nlu)."""
    try:
        relativa = ruta.relative_to(raiz_proyecto)
        partes = list(relativa.with_suffix("").parts)
        if partes and partes[-1] == "__init__":
            partes.pop()
        return ".".join(partes) if partes else None
    except ValueError:
        return None


# ═══════════════════════════════════════════════
# HOT RELOADER
# ═══════════════════════════════════════════════

class HotReloader(QObject):
    """
    Vigila archivos .py del proyecto y recarga módulos cuando cambian.

    Señales:
        modulo_recargado(str, str)  — (nombre_modulo, capa)
        recarga_fallida(str, str)   — (nombre_modulo, error)
        requiere_reinicio(str)      — (ruta_archivo) para capas no recargables
    """

    modulo_recargado = pyqtSignal(str, str)    # módulo, capa
    recarga_fallida = pyqtSignal(str, str)     # módulo, error
    requiere_reinicio = pyqtSignal(str)        # ruta

    def __init__(self, raiz_proyecto: Path, on_recrear_cerebro: Callable | None = None):
        super().__init__()
        self._raiz = raiz_proyecto
        self._on_recrear_cerebro = on_recrear_cerebro
        self._watcher = QFileSystemWatcher()
        self._activo = False

        # Registro de señales para reconexión post-reload
        self._signal_registry: list[tuple] = []

        # Cooldown: evitar recargas múltiples del mismo archivo
        self._ultimo_reload: dict[str, float] = {}
        self._cooldown_seg = 1.0

        # RF-280: Debounce para reinicios — acumular cambios, reiniciar solo tras 10s de calma
        self._reinicio_pendientes: list[str] = []
        self._reinicio_timer = QTimer()
        self._reinicio_timer.setSingleShot(True)
        self._reinicio_timer.setInterval(10_000)  # 10 segundos
        self._reinicio_timer.timeout.connect(self._emitir_reinicio_debounced)

    def iniciar(self):
        """Busca todos los .py bajo computadora/ y los vigila."""
        computadora_dir = self._raiz / "computadora"
        if not computadora_dir.exists():
            logger.warning("HotReloader: directorio computadora/ no encontrado")
            return

        archivos = [str(p) for p in computadora_dir.rglob("*.py") if "__pycache__" not in str(p)]
        if archivos:
            self._watcher.addPaths(archivos)
        self._watcher.fileChanged.connect(self._on_archivo_cambiado)
        self._activo = True
        logger.info(f"HotReloader iniciado — vigilando {len(archivos)} archivos .py")

    def detener(self):
        """Deja de vigilar archivos."""
        if self._activo:
            rutas = self._watcher.files()
            if rutas:
                self._watcher.removePaths(rutas)
            self._activo = False
            logger.info("HotReloader detenido")

    def registrar_senal(self, emisor: QObject, nombre_senal: str, receptor: Callable):
        """Registra una conexión señal→slot para reconexión post-reload."""
        self._signal_registry.append((emisor, nombre_senal, receptor))

    def _on_archivo_cambiado(self, ruta_str: str):
        """Callback de QFileSystemWatcher cuando un archivo cambia."""
        ruta = Path(ruta_str)

        # Cooldown
        ahora = time.time()
        ultimo = self._ultimo_reload.get(ruta_str, 0)
        if ahora - ultimo < self._cooldown_seg:
            return
        self._ultimo_reload[ruta_str] = ahora

        # Clasificar capa
        capa = clasificar_capa(ruta)
        if capa is None:
            logger.debug(f"HotReloader: archivo fuera de capas conocidas: {ruta}")
            return

        # Capas que requieren reinicio manual — RF-280: debounce
        if capa in CAPAS_REINICIO_MANUAL:
            logger.warning(f"HotReloader: cambio en capa '{capa}' requiere reinicio — {ruta.name}")
            self._reinicio_pendientes.append(ruta_str)
            self._reinicio_timer.start()  # (re)iniciar timer — resetea los 10s
            return

        # Resolver nombre de módulo
        nombre_modulo = ruta_a_modulo(ruta, self._raiz)
        if not nombre_modulo:
            logger.debug(f"HotReloader: no pude resolver módulo para {ruta}")
            return

        # Intentar reload
        self._recargar_modulo(nombre_modulo, capa)

        # Re-añadir el archivo (QFileSystemWatcher lo quita tras cambio en algunos OS)
        if ruta_str not in self._watcher.files():
            self._watcher.addPath(ruta_str)

    def _emitir_reinicio_debounced(self):
        """RF-280: Emite señal de reinicio tras 10s sin cambios nuevos."""
        if not self._reinicio_pendientes:
            return
        archivos = list(set(self._reinicio_pendientes))
        logger.info(f"HotReloader: reinicio debounced — {len(archivos)} archivo(s) cambiaron: {[Path(a).name for a in archivos]}")
        self._reinicio_pendientes.clear()
        self.requiere_reinicio.emit(archivos[0])  # Emitir una sola vez

    def _recargar_modulo(self, nombre_modulo: str, capa: str):
        """Ejecuta importlib.reload() sobre el módulo."""
        modulo = sys.modules.get(nombre_modulo)
        if modulo is None:
            logger.debug(f"HotReloader: módulo '{nombre_modulo}' no está cargado, skip")
            return

        inicio = time.time()
        try:
            importlib.reload(modulo)
            duracion = time.time() - inicio
            logger.info(
                f"HotReloader: recargado '{nombre_modulo}' (capa={capa}) "
                f"en {duracion:.3f}s"
            )
            self.modulo_recargado.emit(nombre_modulo, capa)

            # Si es capa cerebro, recrear CerebroComputadora con callbacks frescos
            if capa == "cerebro" and self._on_recrear_cerebro:
                self._on_recrear_cerebro()

        except Exception as e:
            logger.error(f"HotReloader: ERROR recargando '{nombre_modulo}': {e}")
            self.recarga_fallida.emit(nombre_modulo, str(e))


