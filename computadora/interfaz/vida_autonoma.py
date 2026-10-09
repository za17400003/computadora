"""
מלכות (Maljut) — Reino. Presencia física de la Computadora.
Vida Autónoma de la Computadora — Comportamiento deliberado y confiado.

El Computadora se mueve con propósito, como JARVIS: sabe adónde va y por qué.
NO vaga aleatoriamente. Solo se mueve cuando tiene un motivo concreto.
Respeta las 3 leyes de Asimov (Cadenas de Gevurá).
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

# Temporalmente deshabilitar Tzimtzum mientras se corrigen los bugs de carga/ocultación.
TZIMTZUM_ENABLED = False

import ctypes
import ctypes.wintypes

import json
import os
import psutil

from PyQt6.QtCore import QTimer, QPoint, QRect, QMutex
from PyQt6.QtWidgets import QApplication
from loguru import logger

if TYPE_CHECKING:
    from computadora.interfaz.ventana_principal import OrbeComputadora

# ═══════════════════════════════════════════════
# WIN32 FUNCTION SIGNATURES (64-bit safe)
# Sin restype/argtypes, ctypes usa c_int (32-bit)
# para HWND que es 64-bit en Windows x64 →
# truncamiento → sign-extension → access violation
# ═══════════════════════════════════════════════
_user32 = ctypes.windll.user32
_user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
_user32.IsWindow.restype = ctypes.wintypes.BOOL
_user32.IsWindow.argtypes = [ctypes.wintypes.HWND]
_user32.GetWindowRect.restype = ctypes.wintypes.BOOL
_user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
_user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
_user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
_user32.GetCursorPos.restype = ctypes.wintypes.BOOL
_user32.GetCursorPos.argtypes = [ctypes.POINTER(ctypes.wintypes.POINT)]
# WI-228: ShowWindow + SetWindowPos (usados en _desactivar_tzimtzum)
_user32.ShowWindow.restype = ctypes.wintypes.BOOL
_user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
_user32.SetWindowPos.restype = ctypes.wintypes.BOOL
_user32.SetWindowPos.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.HWND,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.wintypes.UINT,
]


# ═══════════════════════════════════════════════
# ESTADOS DE PRESENCIA
# ═══════════════════════════════════════════════

class EstadoPresencia(Enum):
    """Estado visual/tamaño del orbe."""
    PLENO = auto()       # Tamaño completo, activo (180px)
    COMPACTO = auto()    # Bolita pequeña, idle (50px)
    MINIMIZADO = auto()  # En bandeja del sistema, invisible
    TZIMTZUM = auto()    # Contraído por carga pesada (gaming/app pesada)


# ═══════════════════════════════════════════════
# INFORMACIÓN DEL ESCRITORIO (Win32)
# ═══════════════════════════════════════════════

@dataclass
class InfoEscritorio:
    """Snapshot del estado actual del escritorio."""
    cursor: QPoint = field(default_factory=lambda: QPoint(0, 0))
    ventana_activa: QRect = field(default_factory=lambda: QRect(0, 0, 0, 0))
    titulo_ventana: str = ""
    pantalla: QRect = field(default_factory=lambda: QRect(0, 0, 1920, 1080))
    pantallas: list = field(default_factory=list)  # FP-022: lista de QRect por screen
    pantalla_foco: int = 0  # FP-022: índice de pantalla donde está el cursor


def _obtener_info_escritorio() -> InfoEscritorio:
    """Lee posición del cursor, ventana activa y su título usando Win32."""
    info = InfoEscritorio()

    try:
        # Cursor position
        pt = ctypes.wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        info.cursor = QPoint(pt.x, pt.y)
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    try:
        # Active window
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd and ctypes.windll.user32.IsWindow(hwnd):
            rect = ctypes.wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                info.ventana_activa = QRect(
                    rect.left, rect.top,
                    rect.right - rect.left, rect.bottom - rect.top,
                )
            # Window title
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            info.titulo_ventana = buf.value
    except OSError:
        pass  # Stale hwnd — window destroyed between calls
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    try:
        # FP-022 WI-108: Multi-monitor — iterar todas las pantallas
        screens = QApplication.screens()
        if screens:
            for scr in screens:
                geo = scr.availableGeometry()
                info.pantallas.append(QRect(geo.x(), geo.y(), geo.width(), geo.height()))
            # Pantalla primaria como fallback
            info.pantalla = info.pantallas[0]
            # Detectar en qué pantalla está el cursor
            for idx, geo in enumerate(info.pantallas):
                if geo.contains(info.cursor):
                    info.pantalla_foco = idx
                    info.pantalla = geo
                    break
        else:
            pantalla = QApplication.primaryScreen()
            if pantalla:
                geo = pantalla.availableGeometry()
                info.pantalla = QRect(geo.x(), geo.y(), geo.width(), geo.height())
                info.pantallas.append(info.pantalla)
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    return info


# ═══════════════════════════════════════════════
# DETECCIÓN DE CARGA PESADA (Tzimtzum trigger)
# ═══════════════════════════════════════════════

# Procesos EXCLUIDOS — NUNCA triggean Tzimtzum (son del propio Computadora o herramientas de desarrollo)
_PROCESOS_EXCLUIDOS: set[str] = {
    # Computadora y su stack
    "python.exe", "pythonw.exe", "python3.exe",
    "ollama.exe", "ollama_llama_server.exe", "ollama runner",
    "whisper.exe",
    # IDEs / Desarrollo (el usuario trabaja con estos)
    "code.exe", "code - insiders.exe",               # VS Code
    "studio64.exe", "studio.exe",                     # Android Studio
    "idea64.exe", "idea.exe",                         # IntelliJ
    "pycharm64.exe", "pycharm.exe",
    "webstorm64.exe", "rider64.exe", "clion64.exe",
    "devenv.exe",                                     # Visual Studio
    # Herramientas comunes del sistema
    "explorer.exe", "searchapp.exe", "taskmgr.exe",
    "windowsterminal.exe", "powershell.exe", "cmd.exe",
    "conhost.exe", "svchost.exe", "dwm.exe",
    # Navegadores (uso normal, no pesado por sí mismo)
    "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe",
    # NVIDIA stack (siempre presente)
    "nvidia-smi.exe", "nvcontainer.exe", "nvdisplay.container.exe",
}

# Procesos de VIDEOJUEGOS conocidos → siempre triggean Tzimtzum
_PROCESOS_GAMING: set[str] = {
    # Launchers (solo cuando hay juego activo, se detecta por fullscreen)
    "javaw.exe",  # Minecraft Java
}

# Launchers de gaming — solo triggean si tienen ventana fullscreen
_PROCESOS_LAUNCHER: set[str] = {
    "steam.exe", "epicgameslauncher.exe", "galaxyclient.exe",
    "bethesdalauncher.exe", "origin.exe", "ea app.exe",
    "riotclientservices.exe", "battle.net.exe",
}

# Apps de TRABAJO PESADO conocidas → triggean Tzimtzum (consumen muchos recursos)
_PROCESOS_TRABAJO_PESADO: set[str] = {
    # CAD / Ingeniería
    "acad.exe", "acadlt.exe",                         # AutoCAD
    "sldworks.exe", "sldprt.exe",                     # SolidWorks
    "inventor.exe",                                    # Autodesk Inventor
    "catia.exe", "cnext.exe",                          # CATIA
    "fusion360.exe",                                   # Fusion 360
    "revit.exe",                                       # Revit
    # 3D / Render
    "blender.exe",
    "3dsmax.exe", "3dsmaxcmd.exe",                     # 3ds Max
    "maya.exe", "mayabatch.exe",                       # Maya
    "cinema 4d.exe",
    "houdini.exe", "houdinifx.exe",
    "zbrush.exe",
    "substance painter.exe", "substance designer.exe",
    "keyshot.exe",
    # Edición de video pesada
    "afterfx.exe",                                     # After Effects
    "premierpro.exe", "adobe premiere pro.exe",
    "resolve.exe",                                     # DaVinci Resolve
    "nuke.exe",
}

# Patrones en título de ventana que indican gaming/fullscreen-heavy
_TITULO_GAMING_KEYWORDS = (
    "directx", "vulkan", "opengl", "unreal", "unity",
)


def _es_fullscreen_exclusivo(hwnd: int) -> bool:
    """Detecta si una ventana ocupa toda la pantalla (fullscreen exclusivo o borderless)."""
    try:
        if not ctypes.windll.user32.IsWindow(hwnd):
            return False
        rect = ctypes.wintypes.RECT()
        if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        # Comparar contra resolución del monitor
        pantalla = QApplication.primaryScreen()
        if pantalla:
            geo = pantalla.geometry()
            if w >= geo.width() and h >= geo.height():
                return True
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    return False


# Cache para nvidia-smi (evita subprocess cada 500ms tick)
_gpu_cache: tuple[float, str | None] = (0.0, None)  # (timestamp, resultado)
_GPU_CACHE_TTL = 5.0  # segundos

def _detectar_gpu_gaming() -> str | None:
    """WI-258: Detecta proceso gaming en GPU (cache 5s + background thread).
    Retorna inmediatamente con último resultado cached. Lanza thread si expiró.
    """
    global _gpu_cache
    ahora = time.monotonic()
    if ahora - _gpu_cache[0] < _GPU_CACHE_TTL:
        return _gpu_cache[1]

    # Cache expirado — lanzar thread para actualizar, devolver último cached
    if not getattr(_detectar_gpu_gaming, '_updating', False):
        _detectar_gpu_gaming._updating = True
        import threading
        def _bg_update():
            global _gpu_cache
            try:
                resultado = _detectar_gpu_gaming_impl()
                _gpu_cache = (time.monotonic(), resultado)
            finally:
                _detectar_gpu_gaming._updating = False
        threading.Thread(target=_bg_update, daemon=True).start()

    return _gpu_cache[1]


def _detectar_gpu_gaming_impl() -> str | None:
    """Implementación real de detección GPU (sin cache)."""
    import subprocess
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3, creationflags=0x08000000,
        )
        if result.returncode != 0:
            return None

        for linea in result.stdout.strip().splitlines():
            partes = [p.strip() for p in linea.split(",")]
            if len(partes) < 2:
                continue
            proc_path = partes[1].lower()
            proc_nombre = os.path.basename(proc_path)

            # Ignorar procesos excluidos
            if proc_nombre in _PROCESOS_EXCLUIDOS:
                continue
            # Ignorar launchers (no siempre son gaming activo)
            if proc_nombre in _PROCESOS_LAUNCHER:
                continue

            # Proceso desconocido usando GPU → posible juego
            # Verificar si tiene ventana fullscreen
            try:
                import psutil
                procs = [p for p in psutil.process_iter(['pid', 'name'])
                         if p.info['name'] and p.info['name'].lower() == proc_nombre]
                for p in procs:
                    # Verificar si tiene ventana fullscreen
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
                        continue
                    pid_fg = ctypes.wintypes.DWORD()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_fg))
                    if pid_fg.value == p.pid and _es_fullscreen_exclusivo(hwnd):
                        return proc_nombre
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    return None


def _detectar_proceso_pesado() -> tuple[bool, str]:
    """Detecta si hay un proceso pesado (juego/render/CAD) en primer plano.

    NUNCA triggea para procesos de la Computadora (Ollama, Python, Whisper)
    ni herramientas de desarrollo (VS Code, Android Studio).

    Returns:
        (es_pesado, nombre_proceso)
    """
    try:
        import psutil
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd or not ctypes.windll.user32.IsWindow(hwnd):
            return False, ""

        # Obtener PID del proceso en primer plano
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return False, ""

        proc = psutil.Process(pid.value)
        nombre = proc.name().lower()

        # Check 0: Proceso excluido → NUNCA triggear
        if nombre in _PROCESOS_EXCLUIDOS:
            return False, ""

        # Check 1: Proceso en lista de gaming conocidos
        if nombre in _PROCESOS_GAMING:
            return True, nombre

        # Check 2: Proceso en lista de trabajo pesado conocido
        if nombre in _PROCESOS_TRABAJO_PESADO:
            return True, nombre

        # Check 3: Fullscreen + no es launcher ni excluido → probable juego
        if ctypes.windll.user32.IsWindow(hwnd) and _es_fullscreen_exclusivo(hwnd) and nombre not in _PROCESOS_LAUNCHER:
            # Título con keywords gaming
            buf = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
            titulo = buf.value.lower()
            if any(kw in titulo for kw in _TITULO_GAMING_KEYWORDS):
                return True, nombre

            # Fullscreen + alto CPU → probable juego/render
            try:
                cpu = proc.cpu_percent(interval=0)  # WI-258: interval=0 (non-blocking)
                if cpu > 40:  # Umbral alto para evitar falsos positivos
                    return True, nombre
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        # Check 4: NVIDIA GPU — proceso desconocido con GPU + fullscreen
        gpu_proc = _detectar_gpu_gaming()
        if gpu_proc:
            return True, gpu_proc

    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    return False, ""


_proceso_pid_cache: dict[str, int] = {}


def _proceso_sigue_corriendo(nombre: str) -> bool:
    """RF-142/WI-258: Verifica si un proceso con ese nombre sigue vivo.
    Optimizado: cache PID para O(1) en llamadas sucesivas."""
    import psutil
    nombre_lower = nombre.lower()

    # 1) Fast path: PID cacheado → O(1)
    cached_pid = _proceso_pid_cache.get(nombre_lower)
    if cached_pid is not None:
        try:
            proc = psutil.Process(cached_pid)
            if proc.is_running() and proc.name().lower() == nombre_lower:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        del _proceso_pid_cache[nombre_lower]

    # 2) Slow path: scan completo (solo en cache miss) → O(N)
    try:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                pname = proc.info['name']
                if pname and pname.lower() == nombre_lower:
                    _proceso_pid_cache[nombre_lower] = proc.info['pid']
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    return False


# ═══════════════════════════════════════════════
# DETECTOR DE PROBLEMAS (para sugerencias)
# ═══════════════════════════════════════════════

class DetectorContexto:
    """Detecta si el usuario podría necesitar ayuda basándose en patrones."""

    def __init__(self):
        self._historial_ventanas: list[str] = []
        self._ultimo_titulo = ""
        self._cambios_rapidos = 0
        self._ultimo_cambio = 0.0
        self._titulo_repetido_count = 0

    def actualizar(self, titulo: str) -> str | None:
        """Actualiza con el título de ventana actual. Retorna sugerencia o None."""
        ahora = time.monotonic()

        if titulo != self._ultimo_titulo:
            # Cambio de ventana
            delta = ahora - self._ultimo_cambio
            self._ultimo_cambio = ahora

            if delta < 3.0:
                self._cambios_rapidos += 1
            else:
                self._cambios_rapidos = max(0, self._cambios_rapidos - 1)

            self._historial_ventanas.append(titulo)
            if len(self._historial_ventanas) > 20:
                self._historial_ventanas.pop(0)

            self._titulo_repetido_count = 0
            self._ultimo_titulo = titulo

            # Patrón: cambio frenético entre ventanas (más de 8 en poco tiempo)
            if self._cambios_rapidos > 8:
                self._cambios_rapidos = 0
                return "sugerencia_estres"

            # FIX: este chequeo vivía FUERA del bloque "cambió de ventana" y
            # se evaluaba en cada tick mientras la ventana activa (la que
            # sea) contuviera una de estas palabras — p.ej. un archivo
            # abierto llamado "error_handler.py" o una pestaña de navegador
            # con "error" en el título disparaban "sugerencia_error" de
            # nuevo cada vez que se cumplía el cooldown de 60s, indefinida-
            # mente, mientras esa ventana siguiera enfocada. Ahora solo se
            # evalúa cuando el título realmente CAMBIA a uno con esas
            # palabras, igual que el patrón de "cambios_rapidos" de arriba.
            titulo_lower = titulo.lower()
            _error_words = ("error", "exception", "crash", "fatal", "failed", "not responding")
            if any(w in titulo_lower for w in _error_words):
                return "sugerencia_error"

        else:
            self._titulo_repetido_count += 1

        return None


# ═══════════════════════════════════════════════
# VIDA AUTÓNOMA — Controlador principal
# ═══════════════════════════════════════════════

class VidaAutonoma:
    """
    Controla el comportamiento autónomo del orbe.
    Movimiento DELIBERADO como JARVIS: solo se mueve cuando tiene un motivo.
    NO vaga aleatoriamente. Usa heatmap de pantalla para elegir posiciones.
    """

    # Constantes de tamaño
    TAMANO_PLENO = 180
    TAMANO_COMPACTO = 50
    TAMANO_MIN_COMPACTO = 40

    # FIX (investigación ventana/clipping): margen extra para VFX (glow/
    # partículas/anillos) alrededor de TAMANO_PLENO. El glow en paintEvent()
    # (ventana_principal.py) dibuja hasta radio (RADIO_NUCLEO + 40*2.2) *
    # escala = 123px a escala=1.0 → diámetro 246px. El viejo margen de 40
    # (ventana = TAMANO_PLENO + 40 = 220) dejaba una ventana de solo 220px,
    # 26px MÁS CHICA que el contenido real — de ahí el glow/anillos
    # recortados por el borde de la ventana. 76 iguala el tamaño en reposo
    # que ya calcula dinámicamente _animar() (radio_visual*2 + margen_vfx ≈
    # 256 a escala=1.0), para que colapsar-tras-tránsito y el reposo
    # dinámico coincidan y no haya un resize extra (y su parpadeo) justo
    # después de un tránsito.
    MARGEN_VFX = 76

    # Velocidad de movimiento (px por frame @60fps)
    VEL_ESQUIVAR = 4.0    # Quitándose del camino
    VEL_ACERCAR = 3.0     # Acercándose para sugerencia
    VEL_REGRESAR = 2.0    # Volviendo a su rincón
    VEL_REUBICAR = 2.0    # Deslizándose a un borde (compacto)

    # Tiempos (en ticks, ~2 ticks/sec con timer de 500ms)
    TICKS_POST_CONVERSACION = 60   # ~30s después de fin de conversación → compactar
    TICKS_ANTES_COMPACTAR = 120    # ~60s (1 min) inactivo en PLENO → compactar
    TICKS_ANTES_MINIMIZAR = 600    # ~5 min compacto → minimizar (raro)
    TICKS_REGRESAR_HOGAR = 20      # ~10s sin acción → volver a casa

    # Heatmap
    HEATMAP_COLS = 8
    HEATMAP_ROWS = 6
    HEATMAP_DECAY = 0.95  # Decaimiento por hora
    _HEATMAP_ARCHIVO = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "datos", "heatmap_pantalla.json"
    )

    def __init__(self, orbe: "OrbeComputadora"):
        self._orbe = orbe
        self._estado = EstadoPresencia.PLENO
        self._detector = DetectorContexto()

        # WI-MALJUT-RUBEDO-001: Mutex para thread-safety de _pos_objetivo
        # _pos_objetivo es escrito por _tick() (MotorProactividad 500ms)
        # y leído por _interpolar_movimiento() (Qt main 16ms)
        self._mutex_pos_objetivo = QMutex()
        
        # Posición objetivo para movimiento suave
        self._pos_objetivo: QPoint | None = None
        self._velocidad_actual = self.VEL_REGRESAR
        self._ticks_asentando = 0

        # Contadores
        self._ticks_inactivo = 0
        self._tick_count = 0
        self._ultimo_estado_computadora = "dormido"

        # Sugerencia pendiente
        self._sugerencia_pendiente: str | None = None
        self._sugerencia_cooldown = 0

        # Conversación: timer post-conversación para compactar
        self._conversacion_activa = False
        self._ticks_post_conversacion = 0
        self._esperando_compactar = False

        # Reubicación compacta: cooldown
        self._reubicar_cooldown = 0

        # En casa: si ya está en hogar, no moverse
        self._en_hogar = False

        # Personalidad del orbe
        self._personalidad = getattr(orbe, 'personalidad', None)
        self._tzimtzum_enabled = TZIMTZUM_ENABLED

        # Hogar dinámico — se recalcula periódicamente con heatmap
        self._hogar_recalc_interval = 120  # ~60s entre recálculos
        self._hogar_recalc_counter = 0

        # Posición "hogar" — inicializar (se recalculará con heatmap)
        # FP-022 WI-108: Usar la pantalla donde está el cursor (multi-monitor)
        _info_init = _obtener_info_escritorio()
        geo = _info_init.pantalla
        if geo.width() > 0:
            self._hogar = QPoint(geo.right() - self.TAMANO_PLENO - 30,
                                 geo.bottom() - self.TAMANO_PLENO - 30)
            self._pantalla = QRect(geo.x(), geo.y(), geo.width(), geo.height())
        else:
            self._hogar = QPoint(1700, 900)
            self._pantalla = QRect(0, 0, 1920, 1080)

        # Heatmap de uso de pantalla (histórico — persiste en disco)
        self._heatmap = self._cargar_heatmap()
        self._heatmap_guardado = time.monotonic()
        self._heatmap_decayed = time.monotonic()

        # RF-180: Heatmap reciente (últimos 5 min — solo RAM)
        self._heatmap_reciente: list[list[float]] = [
            [0.0] * self.HEATMAP_COLS for _ in range(self.HEATMAP_ROWS)
        ]
        self._heatmap_reciente_inicio = time.monotonic()
        self._heatmap_reciente_decayed = time.monotonic()

        # RF-181: Memoria de esquivas
        from collections import deque as _deque
        self._historial_esquivas: _deque = _deque(maxlen=20)

        # WI-166: Cursor history for trajectory analysis in _estorba()
        self._cursor_prev = QPoint(0, 0)
        self._cursor_prev2 = QPoint(0, 0)  # tick N-2 for smoother direction

        # Timer principal — cada 500ms toma decisiones
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)

        # WI-242: Métricas de sistema para indicador visual en el orbe
        # FIX RUBEDO: Estas son CACHEADAS por daemon thread, no leídas en main
        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        # WI-254: GPU y disco
        self._gpu_percent = -1.0   # -1 = no disponible
        self._disk_percent = 0.0
        self._gpu_tick_counter = 0  # nvidia-smi cada 10 ticks (~5s, fue 4 ticks)
        # WI-261: Disk I/O activity (0.0-1.0 normalized pulse)
        self._disk_io_activity = 0.0
        self._disk_io_prev_read = 0
        self._disk_io_prev_write = 0
        self._disk_io_initialized = False
        # FIX RUBEDO: Daemon thread para psutil (CPU-intensive)
        import threading
        self._psutil_daemon_stop = False
        self._psutil_daemon_thread = threading.Thread(target=self._daemon_leer_psutil, daemon=True)
        self._psutil_daemon_thread.start()
        # WI-251: Smoothed display values (interpolated every 16ms)
        self._cpu_display = 0.0
        self._ram_display = 0.0
        self._gpu_display = -1.0
        self._disk_display = 0.0
        self._disk_io_display = 0.0  # WI-261: smoothed I/O pulse

        # Timer de movimiento suave — cada 16ms (~60fps) interpola posición
        # RESTAURADO: 16ms (60fps) para fluidez visual. El smoothing factor 0.08
        # ya previene CPU spikes. Pasar de 33ms→16ms recupera animaciones suaves.
        self._timer_movimiento = QTimer()
        self._timer_movimiento.timeout.connect(self._interpolar_movimiento)
        self._timer_movimiento.start(16)

        # Cooldown de esquiva
        self._esquivar_cooldown = 0

        # Timer de tamaño suave
        self._tamano_objetivo = self.TAMANO_PLENO
        self._tamano_actual = float(self.TAMANO_PLENO)

        # צמצום Tzimtzum — Contracción por carga pesada
        self._en_tzimtzum = False
        self._tzimtzum_proceso = ""       # Nombre del proceso que triggereó
        self._ticks_carga_pesada = 0      # Cuántos ticks seguidos se detectó carga
        self._TICKS_UMBRAL_TZIMTZUM = 6   # ~3s de carga sostenida antes de contraer
        self._ticks_carga_ligera = 0      # Cuántos ticks sin carga desde Tzimtzum
        self._TICKS_UMBRAL_RETORNO = 10   # ~5s sin carga antes de expandir

        # צמצום Tzimtzum — Contracción por carga de SISTEMA (CPU > 80% sostenido)
        self._ticks_cpu_alto = 0
        self._TICKS_UMBRAL_CPU_TZIMTZUM = 10  # ~5s de CPU alto sostenido
        self._UMBRAL_CPU_ALTO = 80.0          # % CPU del sistema

        # WI-263: Adaptive FPS — reduces frame rate under heavy CPU load
        self._UMBRAL_CPU_ADAPTIVO = 80.0  # % CPU where soft degradation starts (was 55%)
        self._fps_actual = 16             # Current animation interval (ms)
        self._FPS_NORMAL = 16             # ~60 FPS (restored from 33)
        self._FPS_REDUCIDO = 33           # ~30 FPS under heavy load (was 66 = ~15 FPS too choppy)

        # צמצום Tzimtzum — Contracción por inactividad (>5 min sin órdenes)
        self._TICKS_UMBRAL_IDLE_TZIMTZUM = 600  # 600 ticks × 500ms = 300s = 5 min

        logger.info("VidaAutonoma iniciada — movimiento deliberado, sin vagabundeo")

        # Calcular hogar dinámico inicial con heatmap persistido
        try:
            info_init = _obtener_info_escritorio()
            self._calcular_hogar_dinamico(info_init)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            pass  # Mantener fallback de esquina inferior derecha

    # ─────────────────────────────────────────
    # HEATMAP DE PANTALLA
    # ─────────────────────────────────────────

    def _cargar_heatmap(self) -> list[list[float]]:
        """Carga el heatmap desde disco o crea uno nuevo."""
        try:
            path = os.path.normpath(self._HEATMAP_ARCHIVO)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data) == self.HEATMAP_ROWS and all(len(r) == self.HEATMAP_COLS for r in data):
                    return data
        except Exception as e:
            logger.debug(f"No se pudo cargar heatmap: {e}")
        return [[0.0] * self.HEATMAP_COLS for _ in range(self.HEATMAP_ROWS)]

    def _guardar_heatmap(self):
        """Persiste el heatmap a disco."""
        try:
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(self._HEATMAP_ARCHIVO, self._heatmap)
        except Exception as e:
            logger.debug(f"No se pudo guardar heatmap: {e}")

    def _actualizar_heatmap(self, cursor: QPoint):
        """Incrementa ambos heatmaps (histórico + reciente) donde está el cursor."""
        if self._pantalla.width() <= 0 or self._pantalla.height() <= 0:
            return
        col = min(self.HEATMAP_COLS - 1,
                   max(0, int((cursor.x() - self._pantalla.left()) / self._pantalla.width() * self.HEATMAP_COLS)))
        row = min(self.HEATMAP_ROWS - 1,
                   max(0, int((cursor.y() - self._pantalla.top()) / self._pantalla.height() * self.HEATMAP_ROWS)))
        self._heatmap[row][col] += 1.0

        # RF-180: Actualizar heatmap reciente
        self._heatmap_reciente[row][col] += 1.0

        ahora = time.monotonic()

        # RF-180: Decay reciente cada 30s (más agresivo)
        if ahora - self._heatmap_reciente_decayed > 30:
            for r in range(self.HEATMAP_ROWS):
                for c in range(self.HEATMAP_COLS):
                    self._heatmap_reciente[r][c] *= 0.85
            self._heatmap_reciente_decayed = ahora

        # RF-180: Reset reciente cada 5 min (ventana deslizante)
        if ahora - self._heatmap_reciente_inicio > 300:
            self._heatmap_reciente = [
                [0.0] * self.HEATMAP_COLS for _ in range(self.HEATMAP_ROWS)
            ]
            self._heatmap_reciente_inicio = ahora

        # Decaimiento histórico cada hora
        if ahora - self._heatmap_decayed > 3600:
            for r in range(self.HEATMAP_ROWS):
                for c in range(self.HEATMAP_COLS):
                    self._heatmap[r][c] *= self.HEATMAP_DECAY
            self._heatmap_decayed = ahora

        # Guardar histórico cada 5 min
        if ahora - self._heatmap_guardado > 300:
            self._guardar_heatmap()
            self._heatmap_guardado = ahora

    def _score_posicion(self, x: int, y: int) -> float:
        """Score: zona muy usada = score ALTO (malo). Zona poco usada = score BAJO (bueno).
        Fórmula: heatmap_value directamente — min() selecciona zonas FRÍAS (score bajo)."""
        if self._pantalla.width() <= 0 or self._pantalla.height() <= 0:
            return 0.0
        col = min(self.HEATMAP_COLS - 1,
                   max(0, int((x - self._pantalla.left()) / self._pantalla.width() * self.HEATMAP_COLS)))
        row = min(self.HEATMAP_ROWS - 1,
                   max(0, int((y - self._pantalla.top()) / self._pantalla.height() * self.HEATMAP_ROWS)))
        # RF-180: Dual heatmap — reciente pesa más para reaccionar rápido
        # WI-HEATMAP-FIX-JUNIO1: Fórmula directa — zona roja (alta heatmap) = score ALTO; zona fría (baja heatmap) = score BAJO
        # min() selecciona score BAJO = zonas frías (RESPETA espacio de usuario)
        hist_score = self._heatmap[row][col] * 0.01  # Normaliza a 0-1 (aprox)
        reciente_score = self._heatmap_reciente[row][col] * 0.05  # Más agresivo
        return hist_score * 0.4 + reciente_score * 0.6

    def _mejor_borde(self, info: InfoEscritorio) -> QPoint:
        """Encuentra la mejor posición en el perímetro de la pantalla (menor heatmap, lejos del cursor)."""
        # RF-164: Usar tamaño real para que el orbe quepa completo en destino
        w = max(self._orbe.width(), self.TAMANO_COMPACTO)
        margen = 10
        candidatos = []

        # Generar candidatos en los 4 bordes (2 por lado = 8 candidatos)
        for frac in (0.3, 0.7):
            # Borde superior
            x = int(self._pantalla.left() + self._pantalla.width() * frac - w // 2)
            candidatos.append(QPoint(x, self._pantalla.top() + margen))
            # Borde inferior
            candidatos.append(QPoint(x, self._pantalla.bottom() - w - margen))
            # Borde izquierdo
            y = int(self._pantalla.top() + self._pantalla.height() * frac - w // 2)
            candidatos.append(QPoint(self._pantalla.left() + margen, y))
            # Borde derecho
            candidatos.append(QPoint(self._pantalla.right() - w - margen, y))

        # Filtrar: no ir donde está el cursor ni la ventana activa
        cursor_zona = QRect(info.cursor.x() - 200, info.cursor.y() - 200, 400, 400)
        validos = []
        for pt in candidatos:
            dest = QRect(pt.x(), pt.y(), w, w)
            if dest.intersects(cursor_zona):
                continue
            if info.ventana_activa.width() > 100 and "Computadora" not in info.titulo_ventana.lower():
                if dest.intersects(info.ventana_activa):
                    continue
            validos.append(pt)

        if not validos:
            validos = candidatos  # Si todos están ocupados, usar todos

        # Elegir el de menor score de heatmap
        mejor = min(validos, key=lambda p: self._score_posicion(p.x(), p.y()))
        return mejor

    def _calcular_hogar_dinamico(self, info: InfoEscritorio):
        """Recalcula la posición de hogar usando heatmap — zona menos usada del perímetro."""
        w = self.TAMANO_PLENO
        margen = 20
        candidatos = []

        # 16 candidatos: 4 esquinas + 3 puntos por borde
        for frac in (0.15, 0.5, 0.85):
            # Borde superior
            x = int(self._pantalla.left() + self._pantalla.width() * frac - w // 2)
            candidatos.append(QPoint(x, self._pantalla.top() + margen))
            # Borde inferior
            candidatos.append(QPoint(x, self._pantalla.bottom() - w - margen))
            # Borde izquierdo
            y = int(self._pantalla.top() + self._pantalla.height() * frac - w // 2)
            candidatos.append(QPoint(self._pantalla.left() + margen, y))
            # Borde derecho
            candidatos.append(QPoint(self._pantalla.right() - w - margen, y))

        # 4 esquinas
        candidatos.append(QPoint(self._pantalla.left() + margen, self._pantalla.top() + margen))
        candidatos.append(QPoint(self._pantalla.right() - w - margen, self._pantalla.top() + margen))
        candidatos.append(QPoint(self._pantalla.left() + margen, self._pantalla.bottom() - w - margen))
        candidatos.append(QPoint(self._pantalla.right() - w - margen, self._pantalla.bottom() - w - margen))

        # Filtrar: lejos del cursor y lejos de ventana activa
        cursor_zona = QRect(info.cursor.x() - 250, info.cursor.y() - 250, 500, 500)
        validos = []
        for pt in candidatos:
            dest = QRect(pt.x(), pt.y(), w, w)
            if dest.intersects(cursor_zona):
                continue
            if info.ventana_activa.width() > 100 and "Computadora" not in info.titulo_ventana.lower():
                if dest.intersects(info.ventana_activa):
                    continue
            validos.append(pt)

        if not validos:
            return  # Mantener hogar anterior si todo está ocupado

        # RF-182: Ordenar por score, evitar zonas de esquiva frecuente
        # WI-HEATMAP-FIX-JUNIO1: sorted() ascendente = [0] es score BAJO (zona FRÍA)
        validos_scored = sorted(validos, key=lambda p: self._score_posicion(p.x(), p.y()))
        nuevo_hogar = validos_scored[0]

        # RF-182: Si el mejor candidato cae en zona de esquiva frecuente, usar 2do
        if len(validos_scored) > 1 and self._es_zona_esquiva_frecuente(nuevo_hogar):
            nuevo_hogar = validos_scored[1]
            logger.debug("Hogar: 1er candidato en zona de esquiva, usando 2do")

        if nuevo_hogar != self._hogar:
            self._hogar = nuevo_hogar
            logger.debug(f"Hogar dinámico recalculado → ({nuevo_hogar.x()}, {nuevo_hogar.y()})")

    # ─────────────────────────────────────────
    # API PÚBLICA
    # ─────────────────────────────────────────

    def notificar_actividad(self):
        """El usuario interactuó con Computadora (voz, clic, etc.)."""
        self._ticks_inactivo = 0
        self._esperando_compactar = False
        self._conversacion_activa = True
        self._en_hogar = False
        if self._estado != EstadoPresencia.PLENO:
            self.restaurar_pleno()

    def notificar_estado(self, estado: str):
        """Cambia el estado de la Computadora (dormido, escuchando, procesando, hablando)."""
        self._ultimo_estado_computadora = estado
        if estado in ("escuchando", "procesando", "hablando"):
            self._ticks_inactivo = 0
            self._esperando_compactar = False
            self._conversacion_activa = True
            if self._estado != EstadoPresencia.PLENO:
                self.restaurar_pleno()

    def notificar_fin_conversacion(self):
        """La conversación terminó. Inicia timer de 30s para compactar."""
        self._conversacion_activa = False
        self._ticks_post_conversacion = 0
        self._esperando_compactar = True
        logger.debug("Fin de conversación detectado — esperando 30s para compactar")

    def restaurar_pleno(self):
        """Restaura el orbe a tamaño completo con animación."""
        if self._estado == EstadoPresencia.MINIMIZADO or self._estado == EstadoPresencia.TZIMTZUM:
            self._orbe.show()
            self._orbe.raise_()
        self._estado = EstadoPresencia.PLENO
        self._tamano_objetivo = self.TAMANO_PLENO
        self._ticks_inactivo = 0
        self._esperando_compactar = False
        self._en_hogar = False
        logger.debug("Computadora → presencia plena")

    def presentar_sugerencia(self, tipo: str):
        """Programa al Computadora para acercarse al usuario con una sugerencia."""
        if self._sugerencia_cooldown > 0:
            return
        self._sugerencia_pendiente = tipo
        self._sugerencia_cooldown = 120
        logger.info(f"Computadora quiere sugerir: {tipo}")

    @property
    def estado_presencia(self) -> EstadoPresencia:
        return self._estado

    @property
    def esta_compacto(self) -> bool:
        return self._estado == EstadoPresencia.COMPACTO

    def _actualizar_gpu(self):
        """WI-254/WI-258: Lee utilización GPU via nvidia-smi en thread background."""
        import threading
        def _leer_gpu():
            try:
                import subprocess
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=1.5,
                    encoding="utf-8",
                    creationflags=0x08000000,  # CREATE_NO_WINDOW
                )
                if result.returncode == 0 and result.stdout.strip():
                    self._gpu_percent = float(result.stdout.strip().split('\n')[0])
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada (GPU): %s", e)
        threading.Thread(target=_leer_gpu, daemon=True).start()
    
    def _daemon_leer_psutil(self):
        """FIX RUBEDO: Daemon thread para leer psutil sin bloquear main thread."""
        import time
        while not self._psutil_daemon_stop:
            try:
                self._cpu_percent = psutil.cpu_percent(interval=0)
                self._ram_percent = psutil.virtual_memory().percent
                try:
                    self._disk_percent = psutil.disk_usage('C:\\').percent
                except Exception:
                    pass
                try:
                    _io = psutil.disk_io_counters()
                    if _io is not None:
                        _r, _w = _io.read_bytes, _io.write_bytes
                        if self._disk_io_initialized:
                            _delta = (_r - self._disk_io_prev_read) + (_w - self._disk_io_prev_write)
                            self._disk_io_activity = min(1.0, _delta / 52_428_800)
                        else:
                            self._disk_io_initialized = True
                        self._disk_io_prev_read = _r
                        self._disk_io_prev_write = _w
                except Exception:
                    pass
                time.sleep(0.5)
            except Exception as e:
                logger.debug("Excepcion en daemon psutil: %s", e)
                time.sleep(0.5)

    # ─────────────────────────────────────────
    # TICK PRINCIPAL — Decisiones cada 500ms
    # ─────────────────────────────────────────

    def _tick(self):
        self._tick_count += 1
        self._ticks_inactivo += 1
        if self._sugerencia_cooldown > 0:
            self._sugerencia_cooldown -= 1
        if self._reubicar_cooldown > 0:
            self._reubicar_cooldown -= 1

        # No tomar decisiones autónomas si Computadora está ocupado
        if self._ultimo_estado_computadora in ("procesando", "hablando"):
            return

        info = _obtener_info_escritorio()

        # WI-166: Store cursor history for trajectory analysis (2-tick window)
        self._cursor_prev2 = QPoint(self._cursor_prev)
        self._cursor_prev = QPoint(info.cursor)

        # Actualizar heatmap con posición del cursor
        self._actualizar_heatmap(info.cursor)

        # Recalcular hogar dinámico periódicamente
        self._hogar_recalc_counter += 1
        if self._hogar_recalc_counter >= self._hogar_recalc_interval:
            self._hogar_recalc_counter = 0
            self._calcular_hogar_dinamico(info)

        # ── DECISIÓN 0: צמצום Tzimtzum — carga pesada ──
        es_pesado = False
        proc_pesado = ""
        if self._tzimtzum_enabled:
            es_pesado, proc_pesado = _detectar_proceso_pesado()
            if es_pesado:
                self._ticks_carga_ligera = 0
                self._ticks_carga_pesada += 1
                if not self._en_tzimtzum and self._ticks_carga_pesada >= self._TICKS_UMBRAL_TZIMTZUM:
                    self._activar_tzimtzum(proc_pesado)
            else:
                # RF-143: Debounce gradual — decrementar en vez de resetear a 0
                self._ticks_carga_pesada = max(0, self._ticks_carga_pesada - 1)
                if self._en_tzimtzum:
                    # RF-142: Hysteresis — verificar si el proceso que trigereó sigue vivo
                    if (self._tzimtzum_proceso
                            and self._tzimtzum_proceso != "inactividad >5 min"
                            and _proceso_sigue_corriendo(self._tzimtzum_proceso)):
                        self._ticks_carga_ligera = 0  # Proceso vivo → no contar ticks ligeros
                    else:
                        self._ticks_carga_ligera += 1
                        if self._ticks_carga_ligera >= self._TICKS_UMBRAL_RETORNO:
                            self._desactivar_tzimtzum()

        # ── DECISIÓN 0.1: צמצום por carga de SISTEMA (CPU > 80% sostenido) ──
        # FIX RUBEDO: _cpu_percent ahora es LEÍDO por daemon thread, no aquí
        if self._tzimtzum_enabled and not self._en_tzimtzum and not es_pesado:
            try:
                # WI-254: GPU (nvidia-smi, cada 10 ticks ~5s para evitar overhead)
                self._gpu_tick_counter += 1
                if self._gpu_tick_counter >= 10:
                    self._gpu_tick_counter = 0
                    self._actualizar_gpu()
                cpu_sistema = self._cpu_percent
                if cpu_sistema >= self._UMBRAL_CPU_ALTO:
                    self._ticks_cpu_alto += 1
                    if self._ticks_cpu_alto >= self._TICKS_UMBRAL_CPU_TZIMTZUM:
                        self._activar_tzimtzum(f"CPU sistema {cpu_sistema:.0f}%")
                else:
                    self._ticks_cpu_alto = max(0, self._ticks_cpu_alto - 1)

                # WI-263: Adaptive FPS — soft degradation before Tzimtzum
                if (cpu_sistema >= self._UMBRAL_CPU_ADAPTIVO
                        and self._fps_actual == self._FPS_NORMAL
                        and not self._en_tzimtzum):
                    self._fps_actual = self._FPS_REDUCIDO
                    self._timer_movimiento.setInterval(self._FPS_REDUCIDO)
                    if hasattr(self._orbe, '_timer'):
                        self._orbe._timer.setInterval(self._FPS_REDUCIDO)
                    logger.debug("WI-263: FPS reducido (CPU %.0f%%) → %dfps",
                                 cpu_sistema, 1000 // self._FPS_REDUCIDO)
                elif (cpu_sistema < self._UMBRAL_CPU_ADAPTIVO
                      and self._fps_actual == self._FPS_REDUCIDO
                      and not self._en_tzimtzum):
                    self._fps_actual = self._FPS_NORMAL
                    self._timer_movimiento.setInterval(self._FPS_NORMAL)
                    if hasattr(self._orbe, '_timer'):
                        self._orbe._timer.setInterval(self._FPS_NORMAL)
                    logger.debug("WI-263: FPS restaurado (CPU %.0f%%) → %dfps",
                                 cpu_sistema, 1000 // self._FPS_NORMAL)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        # Si estamos en Tzimtzum, no tomar más decisiones
        if self._en_tzimtzum:
            return

        # ── DECISIÓN 0.5: צמצום Tzimtzum — inactividad prolongada (>5 min) ──
        if self._tzimtzum_enabled and (not self._conversacion_activa
                and self._ticks_inactivo >= self._TICKS_UMBRAL_IDLE_TZIMTZUM
                and self._estado == EstadoPresencia.COMPACTO):
            self._activar_tzimtzum("inactividad >5 min")
            return

        # ── DECISIÓN 1: ¿Estorbo al usuario? ──
        if self._esquivar_cooldown > 0:
            self._esquivar_cooldown -= 1
        if self._ticks_asentando > 0:
            self._ticks_asentando -= 1
        if self._estado != EstadoPresencia.MINIMIZADO:
            # FIX: antes esta decisión no comprobaba si ya había un destino en
            # curso (a diferencia de las decisiones 3b/6, que sí lo hacen) —
            # podía reasignar `_pos_objetivo` a mitad de un tránsito previo.
            # `_interpolar_movimiento` solo re-expande la ventana de tránsito
            # cuando `_en_transito` pasa de False→True; si el destino cambia
            # mientras la ventana expandida sigue siendo la de un tránsito
            # anterior (calculada para otro origen/destino), el offset puede
            # terminar apuntando fuera del área visible de esa ventana ya
            # obsoleta — visible como una reubicación súbita/errática,
            # especialmente notorio en tránsitos largos hacia una esquina.
            if (self._pos_objetivo is None and not self._orbe._en_transito
                    and self._estorba(info) and self._esquivar_cooldown <= 0):
                self._esquivar(info)
                self._esquivar_cooldown = 24  # ~12s — da tiempo a que el movimiento termine y el usuario se adapte

        # ── DECISIÓN 2: Compactación post-conversación ──
        if self._esperando_compactar and self._estado == EstadoPresencia.PLENO:
            self._ticks_post_conversacion += 1
            if self._ticks_post_conversacion >= self.TICKS_POST_CONVERSACION:
                self._compactar()
                self._esperando_compactar = False
                # Ir al borde menos usado
                destino = self._mejor_borde(info)
                self._velocidad_actual = self.VEL_REUBICAR
                self._pos_objetivo = destino
                score_borde = self._score_posicion(destino.x(), destino.y())
                logger.info(f"Compactado → yendo a borde ({destino.x()}, {destino.y()}) [heatmap_score={score_borde:.3f}]")

        # ── DECISIÓN 2b: Auto-compactación por inactividad general (1 min) ──
        if (self._estado == EstadoPresencia.PLENO
                and not self._conversacion_activa
                and not self._esperando_compactar
                and self._ticks_inactivo >= self.TICKS_ANTES_COMPACTAR):
            self._compactar()
            destino = self._mejor_borde(info)
            self._velocidad_actual = self.VEL_REUBICAR
            self._pos_objetivo = destino
            logger.info(f"Auto-compactado (1 min inactivo) → borde ({destino.x()}, {destino.y()})")

        # ── DECISIÓN 3: Reubicación reactiva en modo compacto ──
        if self._estado == EstadoPresencia.COMPACTO and self._reubicar_cooldown <= 0:
            dist_cursor = math.sqrt(
                (self._orbe.pos().x() - info.cursor.x()) ** 2 +
                (self._orbe.pos().y() - info.cursor.y()) ** 2
            )
            if dist_cursor < 150:
                destino = self._mejor_borde(info)
                self._velocidad_actual = self.VEL_ESQUIVAR
                self._pos_objetivo = destino
                self._en_hogar = False
                self._reubicar_cooldown = 16  # ~8s
                logger.debug(f"Compacto: cursor cerca → reubicando a ({destino.x()}, {destino.y()})")

        # ── DECISIÓN 3b: Compacto inactivo → ir a hogar dinámico ──
        if (self._estado == EstadoPresencia.COMPACTO
                and self._pos_objetivo is None
                and self._ticks_asentando <= 0
                and not self._en_hogar
                and self._ticks_inactivo > self.TICKS_REGRESAR_HOGAR):
            # Usar hogar dinámico ajustado a tamaño compacto
            hogar_compacto = self._mejor_borde(info)
            dist_hogar = math.sqrt(
                (self._orbe.pos().x() - hogar_compacto.x()) ** 2 +
                (self._orbe.pos().y() - hogar_compacto.y()) ** 2
            )
            dist_cursor_hogar = math.sqrt(
                (info.cursor.x() - hogar_compacto.x()) ** 2 +
                (info.cursor.y() - hogar_compacto.y()) ** 2
            )
            if dist_hogar > 20 and dist_cursor_hogar > 200:
                self._velocidad_actual = self.VEL_REGRESAR
                self._pos_objetivo = hogar_compacto
                self._en_hogar = True
                logger.debug("Compacto regresa a casa — nada que hacer")

        # ── DECISIÓN 4: Minimizar si compacto mucho rato ──
        if self._estado == EstadoPresencia.COMPACTO:
            if self._ticks_inactivo > self.TICKS_ANTES_MINIMIZAR:
                if random.random() < 0.2:
                    self._minimizar()

        # ── DECISIÓN 5: ¿Tengo sugerencia? ──
        # FIX (investigación clipping durante movimiento): igual que la
        # DECISIÓN 1 (ver comentario arriba), esta decisión reasignaba
        # `_pos_objetivo` sin comprobar si ya había un tránsito en curso.
        # `_acercar_para_sugerencia` calcula un destino NUEVO e independiente
        # del tránsito activo; como `_interpolar_movimiento` solo llama a
        # `_expandir_ventana_transito` cuando `_en_transito` pasa de
        # False→True, la ventana expandida se queda con el tamaño/posición
        # calculado para el origen/destino ANTERIOR mientras el offset de
        # render persigue el destino NUEVO — el offset puede crecer mucho más
        # allá de lo que esa ventana (ya obsoleta) cubre, dibujando el orbe
        # (glow/partículas/anillos) fuera de su propia área visible. Si hay
        # un tránsito en curso, se pospone la sugerencia a un tick posterior
        # (el campo sigue pendiente, no se pierde) en vez de interrumpirlo.
        if self._sugerencia_pendiente:
            if self._pos_objetivo is None and not self._orbe._en_transito:
                self._acercar_para_sugerencia(info)
                self._sugerencia_pendiente = None
            # else: dejar `_sugerencia_pendiente` para reintentar cuando
            # termine el tránsito actual.

        # ── DECISIÓN 6: Volver a casa si pleno e inactivo (sin vagabundeo) ──
        if (self._estado == EstadoPresencia.PLENO
                and self._pos_objetivo is None
                and self._ticks_asentando <= 0
                and not self._en_hogar
                and not self._esperando_compactar
                and self._ticks_inactivo > self.TICKS_REGRESAR_HOGAR):
            dist_hogar = math.sqrt(
                (self._orbe.pos().x() - self._hogar.x()) ** 2 +
                (self._orbe.pos().y() - self._hogar.y()) ** 2
            )
            # No ir a casa si el cursor está cerca de hogar (evita ping-pong esquivar↔hogar)
            dist_cursor_hogar = math.sqrt(
                (info.cursor.x() - self._hogar.x()) ** 2 +
                (info.cursor.y() - self._hogar.y()) ** 2
            )
            if dist_hogar > 30 and dist_cursor_hogar > 200:
                self._velocidad_actual = self.VEL_REGRESAR
                self._pos_objetivo = self._hogar
                self._en_hogar = True
                logger.debug("Computadora regresa a casa — nada que hacer")

        # ── Detectar si el usuario tiene problemas ──
        sugerencia = self._detector.actualizar(info.titulo_ventana)
        if sugerencia and self._sugerencia_cooldown <= 0:
            self.presentar_sugerencia(sugerencia)

    # ─────────────────────────────────────────
    # MOVIMIENTO SUAVE (60fps interpolación)
    # ─────────────────────────────────────────

    def _interpolar_movimiento(self):
        """RF-340: Mueve el orbe suavemente hacia _pos_objetivo usando ventana expandida.
        La ventana se expande para cubrir origen→destino. El orbe se dibuja con
        render_offset dentro de la ventana expandida. Las áreas transparentes son
        intangibles (WA_TranslucentBackground). Al llegar, colapsa la ventana."""
        # WI-251: Smooth CPU/RAM display values (exponential ease toward raw)
        # FP-107: Reduced from 0.15→0.08 to eliminate visual jitter during idle state
        # (WI-258: 0.15 was adjusted for 30fps but produced excessive jerk)
        _SMOOTH = 0.08  # Smoother transitions with 34.5→18.4 jerk reduction
        self._cpu_display += (self._cpu_percent - self._cpu_display) * _SMOOTH
        self._ram_display += (self._ram_percent - self._ram_display) * _SMOOTH
        # WI-254: Smooth GPU/disk
        if self._gpu_percent >= 0:
            if self._gpu_display < 0:
                self._gpu_display = self._gpu_percent  # primer dato: snap
            else:
                self._gpu_display += (self._gpu_percent - self._gpu_display) * _SMOOTH
        self._disk_display += (self._disk_percent - self._disk_display) * _SMOOTH
        # WI-261: Fast-attack, slow-decay for I/O pulse (fade-in fast, fade-out slow)
        _io_target = self._disk_io_activity
        if _io_target > self._disk_io_display:
            self._disk_io_display += (_io_target - self._disk_io_display) * 0.4  # fast attack
        else:
            self._disk_io_display += (_io_target - self._disk_io_display) * 0.05  # slow decay

        # Animar tamaño suave (la ventana se ajusta dinámicamente en _animar)
        if abs(self._tamano_actual - self._tamano_objetivo) > 1:
            self._tamano_actual += (self._tamano_objetivo - self._tamano_actual) * 0.15

        if self._pos_objetivo is None:
            # Si acabamos de terminar un tránsito, colapsar ventana.
            # FIX: antes se encogía la ventana INMEDIATAMENTE mientras el
            # offset de render aún tenía su valor grande del tránsito, y el
            # lerp hacia 0 ocurría DESPUÉS, ya con la ventana pequeña — así
            # que durante varios frames el orbe se dibujaba fuera del área
            # visible de la ventana ya encogida (invisible/"desaparece" al
            # terminar el movimiento). Ahora el offset se lleva a 0 PRIMERO,
            # mientras la ventana sigue grande (donde cabe de sobra), y solo
            # se encoge la ventana una vez el offset ya es 0.
            if self._orbe._en_transito:
                if not getattr(self._orbe, '_offset_collapse_iniciado', False):
                    self._orbe._offset_collapse_inicio_x = self._orbe._render_offset_x
                    self._orbe._offset_collapse_inicio_y = self._orbe._render_offset_y
                    self._orbe._offset_collapse_timer = 10
                    self._orbe._offset_collapse_in_progress = True
                    self._orbe._offset_collapse_iniciado = True
                elif not self._orbe._offset_collapse_in_progress:
                    # El lerp ya terminó (offset en 0) — ahora sí es seguro encoger
                    self._colapsar_ventana_transito()
                    self._orbe._offset_collapse_iniciado = False
            return
        # Si llegó un nuevo destino mientras aún se hacía el lerp de cierre
        # de un tránsito anterior, cancelarlo: Fase 2 (abajo) toma control
        # real del offset hacia el nuevo destino.
        if getattr(self._orbe, '_offset_collapse_in_progress', False):
            self._orbe._offset_collapse_in_progress = False
            self._orbe._offset_collapse_iniciado = False
        # HF-028: No mover autónomamente si el usuario arrastra o hay impulso
        if self._orbe._arrastrando:
            self._pos_objetivo = None
            return
        if abs(self._orbe._impulso_vx) > 0.5 or abs(self._orbe._impulso_vy) > 0.5:
            self._pos_objetivo = None
            return
        if self._estado == EstadoPresencia.MINIMIZADO:
            self._pos_objetivo = None
            return

        # --- Fase 1: Expandir ventana al inicio del tránsito ---
        if not self._orbe._en_transito:
            self._expandir_ventana_transito()

        # --- Fase 2: Interpolar render offset hacia destino ---
        # Destino en coordenadas locales de la ventana expandida
        win_pos = self._orbe.pos()
        dest_local_x = float(self._pos_objetivo.x() - win_pos.x())
        dest_local_y = float(self._pos_objetivo.y() - win_pos.y())
        # El orbe se dibuja en centro + offset → offset = dest_local - centro
        w_half = self._orbe.width() / 2.0
        h_half = self._orbe.height() / 2.0
        target_off_x = dest_local_x + self.TAMANO_PLENO / 2.0 - w_half
        target_off_y = dest_local_y + self.TAMANO_PLENO / 2.0 - h_half

        dx = target_off_x - self._orbe._render_offset_x
        dy = target_off_y - self._orbe._render_offset_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 2.0:
            # Llegamos — colapsar
            self._orbe._render_offset_x = target_off_x
            self._orbe._render_offset_y = target_off_y
            self._pos_objetivo = None
            # FIX: al llegar, la velocidad del destino anterior (p.ej. 4px/frame
            # de esquivar) seguía puesta y las decisiones de volver a casa
            # retargeteaban de inmediato — el orbe "rebotaba" a otro punto
            # rápidamente. Se resetea y se da un periodo de asentamiento
            # durante el cual no se elige un nuevo destino no urgente.
            self._velocidad_actual = self.VEL_REGRESAR
            self._ticks_asentando = 8
            # No colapsar aquí — se hará en el siguiente frame cuando _pos_objetivo es None
            return

        # Easing exponencial
        factor = min(1.0, self._velocidad_actual / max(dist, 1.0))
        self._orbe._render_offset_x += dx * factor
        self._orbe._render_offset_y += dy * factor

    def _expandir_ventana_transito(self):
        """RF-340: Expande la ventana para cubrir origen + destino del movimiento.

        FIX (investigación clipping durante movimiento): el tamaño de la
        ventana EN REPOSO no es constante — `_animar()` (ventana_principal.py)
        la redimensiona dinámicamente según el radio real de glow/partículas
        (típicamente ~256px, y hasta ~332px con partículas intensas), bastante
        más que `TAMANO_PLENO` (180, que es solo el tamaño "nominal" al que
        colapsa al llegar). Esta función usaba `tam` (180) tanto para el
        bounding box del ORIGEN como para calcular el offset de render
        inicial, asumiendo que el centro visual pre-tránsito estaba en
        `tam/2`. En realidad estaba en `ancho_actual/2` (el tamaño REAL de la
        ventana justo antes de expandir). El error (hasta ~(332-180)/2=76px)
        hacía que el orbe "saltara" hacia un borde de la ventana expandida
        apenas empezaba a moverse, comiéndose el margen VFX de ese lado —
        causa del recorte de glow/partículas/anillos durante el movimiento.
        Ahora se usa el tamaño REAL (`self._orbe.width()/height()`) tanto
        para el bounding box del origen como para el offset inicial.
        """
        if self._pos_objetivo is None:
            return
        orbe_pos = self._orbe.pos()
        tam = self.TAMANO_PLENO
        margen = self.MARGEN_VFX  # extra para glow/partículas (ver MARGEN_VFX)
        # Tamaño REAL actual de la ventana (puede ser > TAMANO_PLENO: ver docstring)
        ancho_actual = float(self._orbe.width())
        alto_actual = float(self._orbe.height())

        # Bounding rect que cubre la caja de ORIGEN (tamaño real actual) y la
        # caja de DESTINO (tamaño nominal al que colapsará: TAMANO_PLENO),
        # más margen en todos los bordes.
        x1 = min(orbe_pos.x(), self._pos_objetivo.x()) - margen
        y1 = min(orbe_pos.y(), self._pos_objetivo.y()) - margen
        x2 = max(orbe_pos.x() + ancho_actual, self._pos_objetivo.x() + tam) + margen
        y2 = max(orbe_pos.y() + alto_actual, self._pos_objetivo.y() + tam) + margen

        # Clamp a pantalla
        x1 = max(self._pantalla.left(), x1)
        y1 = max(self._pantalla.top(), y1)
        x2 = min(self._pantalla.right(), x2)
        y2 = min(self._pantalla.bottom(), y2)

        new_w = x2 - x1
        new_h = y2 - y1

        # Calcular offset inicial: posición del orbe relativa a la nueva ventana
        orbe_local_x = float(orbe_pos.x() - x1)
        orbe_local_y = float(orbe_pos.y() - y1)
        # offset = orbe_local + mitad del tamaño REAL actual (centro visual
        # real pre-tránsito) - new_w/2 (centro geométrico de la nueva ventana)
        self._orbe._render_offset_x = orbe_local_x + ancho_actual / 2.0 - new_w / 2.0
        self._orbe._render_offset_y = orbe_local_y + alto_actual / 2.0 - new_h / 2.0
        self._orbe._en_transito = True

        # Resize y reposicionar ventana
        # FIX: new_w/new_h/x1/y1 son floats (ancho_actual/alto_actual vienen
        # de float(self._orbe.width()/height())) — QWidget.resize()/move()
        # no aceptan float, solo QSize/int (TypeError: "argument did not
        # match any overloaded call"). Redondear solo en el límite con Qt;
        # el resto de la función sigue en float para no perder precisión
        # en el cálculo de _render_offset_x/y.
        self._orbe.resize(round(new_w), round(new_h))
        self._orbe.move(round(x1), round(y1))
        self._orbe._pos_anterior_x = float(x1)
        self._orbe._pos_anterior_y = float(y1)
        self._orbe._tamano_ventana = float(max(new_w, new_h))

    def _colapsar_ventana_transito(self):
        """RF-340: Colapsa la ventana al tamaño normal, centrada en la posición final.
        WI-MALJUT-002: Validación de límites para evitar que orbe salga de pantalla.

        FIX: se llama solo DESPUÉS de que `_render_offset_x/y` ya llegó a 0
        (ver `_interpolar_movimiento` — el lerp de offset→0 ahora ocurre
        ANTES de encoger la ventana, mientras todavía es grande). Con offset
        ya en 0, encoger+reposicionar aquí no produce ningún salto visual:
        el nuevo centro de la ventana pequeña coincide exactamente con dónde
        ya se estaba dibujando el orbe.
        """
        tam = self.TAMANO_PLENO
        # La posición final del orbe en coordenadas de pantalla
        win_pos = self._orbe.pos()
        final_x = int(win_pos.x() + self._orbe.width() / 2.0
                       + self._orbe._render_offset_x - tam / 2.0)
        final_y = int(win_pos.y() + self._orbe.height() / 2.0
                       + self._orbe._render_offset_y - tam / 2.0)

        # WI-MALJUT-002: Validar límites de pantalla ANTES de colapsar
        tam_ventana = max(60, tam + self.MARGEN_VFX)  # tam + margen para glow/partículas
        final_x = max(self._pantalla.left(), min(final_x, self._pantalla.right() - tam_ventana))
        final_y = max(self._pantalla.top(), min(final_y, self._pantalla.bottom() - tam_ventana))

        self._orbe._tamano_ventana = float(tam_ventana)
        self._orbe.resize(tam_ventana, tam_ventana)
        self._orbe.move(final_x, final_y)
        self._orbe._pos_anterior_x = float(final_x)
        self._orbe._pos_anterior_y = float(final_y)

        self._orbe._en_transito = False

    # ─────────────────────────────────────────
    # COMPORTAMIENTOS
    # ─────────────────────────────────────────

    def _estorba(self, info: InfoEscritorio) -> bool:
        """¿El orbe está tapando el cursor? Solo cursor, no ventana activa.
        Si la ventana activa ocupa >70% de pantalla (maximizada), ignorarla —
        no tiene sentido esquivar algo que cubre todo el escritorio.
        FP-013: Si el usuario está interactuando (proximidad > 0.3), no esquivar.
        WI-166: Trajectory analysis — si el cursor se dirige HACIA el orbe,
        es intención de tocar → no esquivar."""
        # HF-028: No considerar estorbo durante drag — el usuario tiene control
        if self._orbe._arrastrando:
            return False
        # FP-013/HF-027: Solo suprimir esquive si el contacto es intencional (>1s)
        # Roces rápidos (pasar el mouse cerca) no deben impedir que esquive
        if hasattr(self._orbe, '_tacto_continuo_inicio'):
            inicio = self._orbe._tacto_continuo_inicio
            if inicio > 0.0 and (time.monotonic() - inicio) > 1.0:
                return False
        # FP-013: Impulso activo — no esquivar mientras se mueve por empujón
        if hasattr(self._orbe, '_impulso_vx'):
            if abs(self._orbe._impulso_vx) > 0.5 or abs(self._orbe._impulso_vy) > 0.5:
                return False

        orbe_rect = QRect(self._orbe.pos(), self._orbe.size())

        # Solo esquivar por cursor — es el indicador real de que estorbamos
        margen_cursor = 100
        cursor_zone = QRect(
            info.cursor.x() - margen_cursor, info.cursor.y() - margen_cursor,
            margen_cursor * 2, margen_cursor * 2,
        )
        if orbe_rect.intersects(cursor_zone):
            # WI-166: Trajectory analysis — ¿el cursor viene HACIA el orbe?
            # Si sí, el usuario quiere interactuar → no esquivar.
            orbe_cx = self._orbe.pos().x() + self._orbe.width() // 2
            orbe_cy = self._orbe.pos().y() + self._orbe.height() // 2
            # Velocity vector from 2-tick history (smoother than 1-tick)
            vel_x = info.cursor.x() - self._cursor_prev2.x()
            vel_y = info.cursor.y() - self._cursor_prev2.y()
            # Vector cursor → orbe center
            to_orbe_x = orbe_cx - info.cursor.x()
            to_orbe_y = orbe_cy - info.cursor.y()
            vel_mag = math.hypot(vel_x, vel_y)
            orbe_mag = math.hypot(to_orbe_x, to_orbe_y)
            if vel_mag > 3 and orbe_mag > 1:
                cos_angle = (vel_x * to_orbe_x + vel_y * to_orbe_y) / (vel_mag * orbe_mag)
                if cos_angle > 0.4:  # < ~66° = heading toward orbe → touch intent
                    return False
            # Cursor slow/stationary near orbe → also touch intent
            if vel_mag <= 3 and orbe_mag < margen_cursor:
                return False
            return True

        # Ventana activa: solo si NO está maximizada (< 70% de pantalla)
        if info.ventana_activa.width() > 100:
            area_ventana = info.ventana_activa.width() * info.ventana_activa.height()
            area_pantalla = max(1, self._pantalla.width() * self._pantalla.height())
            if area_ventana / area_pantalla < 0.70:
                titulo_lower = info.titulo_ventana.lower()
                if "Computadora" not in titulo_lower and titulo_lower:
                    inter = orbe_rect.intersected(info.ventana_activa)
                    if inter.width() > 30 and inter.height() > 30:
                        return True

        return False

    def _esquivar(self, info: InfoEscritorio):
        """Mueve el orbe huyendo del cursor con flee-vector + wall-sliding (Boids-inspired).

        1. Calcula vector de huida (dirección opuesta al cursor desde el orbe).
        2. Proyecta destino a 300px en esa dirección.
        3. Si el destino sale de la pantalla → desliza a lo largo del borde más cercano.
        4. Fallback: candidatos perimetrales filtrados por heatmap.
        """
        # HF-028: Si el usuario está arrastrando, NO esquivar
        if self._orbe._arrastrando:
            return
        self._velocidad_actual = self.VEL_ESQUIVAR
        self._en_hogar = False
        self._ticks_inactivo = 0

        # RF-339: Usar tamaño visual (TAMANO_PLENO)
        w = self.TAMANO_PLENO
        margen = 10

        # ── Fase 1: Flee vector ──────────────────────────────────
        orbe_cx = self._orbe.pos().x() + w // 2
        orbe_cy = self._orbe.pos().y() + w // 2
        dx = orbe_cx - info.cursor.x()
        dy = orbe_cy - info.cursor.y()
        dist = math.hypot(dx, dy)

        destino_flee = None
        if dist > 1:  # evitar div/0 si cursor está exacto encima
            nx, ny = dx / dist, dy / dist
            flee_dist = 300
            target_x = int(orbe_cx + nx * flee_dist - w // 2)
            target_y = int(orbe_cy + ny * flee_dist - w // 2)

            # Clampar a límites de pantalla (wall-sliding)
            left = self._pantalla.left() + margen
            top = self._pantalla.top() + margen
            right = self._pantalla.right() - w - margen
            bottom = self._pantalla.bottom() - w - margen
            target_x = max(left, min(target_x, right))
            target_y = max(top, min(target_y, bottom))

            pt = QPoint(target_x, target_y)
            dest_rect = QRect(pt.x(), pt.y(), w, w)
            cursor_zona = QRect(info.cursor.x() - 200, info.cursor.y() - 200, 400, 400)

            # Validar: no debe intersectar zona del cursor ni ventana activa
            ok = not dest_rect.intersects(cursor_zona)
            if ok and info.ventana_activa.width() > 100 and "Computadora" not in info.titulo_ventana.lower():
                ok = not dest_rect.intersects(info.ventana_activa)
            if ok:
                destino_flee = pt

        # ── Fase 2: Fallback — candidatos perimetrales con heatmap ──
        if destino_flee is None:
            candidatos = []
            for frac in (0.15, 0.4, 0.6, 0.85):
                x = int(self._pantalla.left() + self._pantalla.width() * frac - w // 2)
                candidatos.append(QPoint(x, self._pantalla.top() + margen))
                candidatos.append(QPoint(x, self._pantalla.bottom() - w - margen))
                y = int(self._pantalla.top() + self._pantalla.height() * frac - w // 2)
                candidatos.append(QPoint(self._pantalla.left() + margen, y))
                candidatos.append(QPoint(self._pantalla.right() - w - margen, y))

            cursor_zona = QRect(info.cursor.x() - 300, info.cursor.y() - 300, 600, 600)
            validos = []
            for pt in candidatos:
                dest = QRect(pt.x(), pt.y(), w, w)
                if dest.intersects(cursor_zona):
                    continue
                if info.ventana_activa.width() > 100 and "Computadora" not in info.titulo_ventana.lower():
                    if dest.intersects(info.ventana_activa):
                        continue
                validos.append(pt)

            if not validos:
                cursor_zona_small = QRect(info.cursor.x() - 200, info.cursor.y() - 200, 400, 400)
                validos = [pt for pt in candidatos
                           if not QRect(pt.x(), pt.y(), w, w).intersects(cursor_zona_small)]
            if not validos:
                validos = candidatos

            # WI-HEATMAP-FIX-JUNIO1: min() busca score BAJO = zonas FRÍAS
            destino_flee = min(validos, key=lambda p: self._score_posicion(p.x(), p.y()))

        self._pos_objetivo = destino_flee

        # RF-181: Registrar esquiva en historial
        self._historial_esquivas.append((
            time.monotonic(),
            (self._orbe.pos().x(), self._orbe.pos().y()),
            (destino_flee.x(), destino_flee.y()),
            "cursor" if QRect(info.cursor.x() - 100, info.cursor.y() - 100, 200, 200).intersects(
                QRect(self._orbe.pos(), self._orbe.size())) else "ventana"
        ))

        # RF-181 + RF-182: Evaluar patrón de esquiva y escalar respuesta
        self._evaluar_patron_esquiva(info)

        logger.debug(f"Computadora esquiva → ({destino_flee.x()}, {destino_flee.y()})")

    def _evaluar_patron_esquiva(self, info: InfoEscritorio):
        """RF-181: Evalúa frecuencia de esquivas y escala respuesta.
        ≥2 en 5min → recalc home (RF-182)
        ≥5 en 5min → recalc home + doble cooldown
        ≥7 en 5min → tzimtzum
        """
        ahora = time.monotonic()
        recientes = [e for e in self._historial_esquivas if ahora - e[0] < 300]
        n = len(recientes)

        if n >= 7:
            # Escalación máxima: contraerse
            logger.debug(f"Esquiva x{n} en 5min → activando Tzimtzum")
            self._activar_tzimtzum("esquivas frecuentes")
        elif n >= 5:
            # Doble cooldown + recalc home
            self._esquivar_cooldown = 48  # ~24s en vez de 12s
            self._calcular_hogar_dinamico(info)
            self._en_hogar = True
            logger.debug(f"Esquiva x{n} en 5min → doble cooldown + recalc home")
        elif n >= 2:
            # RF-182: Recalcular home inmediato post-esquiva
            self._calcular_hogar_dinamico(info)
            self._en_hogar = True
            logger.debug(f"Esquiva x{n} en 5min → recalc home reactivo")

    def _es_zona_esquiva_frecuente(self, punto: QPoint) -> bool:
        """RF-182: Verifica si un punto cae en una zona donde se esquivó recientemente."""
        ahora = time.monotonic()
        zona_radio = 200
        for ts, origen, _, _ in self._historial_esquivas:
            if ahora - ts > 300:
                continue
            if (abs(punto.x() - origen[0]) < zona_radio
                    and abs(punto.y() - origen[1]) < zona_radio):
                return True
        return False

    def _acercar_para_sugerencia(self, info: InfoEscritorio):
        """Acerca el Computadora al cursor para ofrecer una sugerencia."""
        if self._estado == EstadoPresencia.MINIMIZADO:
            self._orbe.show()
            self._orbe.raise_()
            self._estado = EstadoPresencia.COMPACTO

        if self._estado == EstadoPresencia.COMPACTO:
            self._tamano_objetivo = self.TAMANO_PLENO
            self._estado = EstadoPresencia.PLENO

        self._velocidad_actual = self.VEL_ACERCAR
        self._en_hogar = False

        margen = 120
        cx, cy = info.cursor.x(), info.cursor.y()
        w = self.TAMANO_PLENO

        if (self._pantalla.right() - cx) > (cx - self._pantalla.left()):
            nx = cx + margen
        else:
            nx = cx - margen - w

        ny = cy - w // 2

        nx = max(self._pantalla.left(), min(nx, self._pantalla.right() - w))
        ny = max(self._pantalla.top(), min(ny, self._pantalla.bottom() - w))

        self._pos_objetivo = QPoint(nx, ny)
        logger.info(f"Computadora se acerca para sugerir en ({nx}, {ny})")

        tipo = self._sugerencia_pendiente or "sugerencia_general"
        QTimer.singleShot(2000, lambda: self._decir_sugerencia(tipo))

    def _decir_sugerencia(self, tipo: str):
        """Dice la sugerencia al usuario."""
        frases = {
            "sugerencia_estres": (
                "Señor, noto que está alternando entre muchas ventanas. "
                "¿Necesita ayuda organizando algo?"
            ),
            "sugerencia_error": (
                "Señor, parece que hay un error en su pantalla. "
                "¿Quiere que le eche un vistazo?"
            ),
        }
        frase = frases.get(tipo, "Señor, ¿puedo ayudarle con algo?")
        try:
            self._orbe.hilo_habla.hablar(frase)
            self._orbe.hilo_escucha.marcar_intercambio()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.debug("No pude ofrecer sugerencia")

    def _compactar(self):
        """Reduce el orbe a una bolita."""
        self._estado = EstadoPresencia.COMPACTO
        self._tamano_objetivo = self.TAMANO_COMPACTO
        self._en_hogar = False
        logger.debug("Computadora → compacto (bolita)")

    def _minimizar(self):
        """Minimiza a la bandeja."""
        self._estado = EstadoPresencia.MINIMIZADO
        self._orbe.hide()
        logger.debug("Computadora → minimizado a bandeja")

    def _activar_tzimtzum(self, proceso: str):
        """צמצום Tzimtzum — Contrae el Computadora por carga pesada (gaming/render/sistema)."""
        if not getattr(self, '_tzimtzum_enabled', False):
            logger.debug("Tzimtzum temporalmente deshabilitado, omitiendo activación: %s", proceso)
            return
        self._en_tzimtzum = True
        self._tzimtzum_proceso = proceso
        self._estado = EstadoPresencia.TZIMTZUM
        self._tamano_objetivo = self.TAMANO_MIN_COMPACTO

        # Pausar timer de movimiento para ahorrar CPU (60fps → 0fps)
        if self._timer_movimiento.isActive():
            self._timer_movimiento.stop()

        # Reducir tick rate a 2s durante Tzimtzum (500ms → 2000ms)
        if self._timer.isActive():
            self._timer.start(2000)

        # Notificar al orbe para reducir recursos
        try:
            self._orbe._activar_modo_carga_pesada(proceso)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error activando modo carga pesada en orbe")

        # FIX: liberar VRAM del modelo Ollama al entrar en Tzimtzum — antes
        # solo se liberaba tras keep_alive de 5min o degradación detectada,
        # nunca por este motivo explícito pedido por el usuario.
        try:
            self._orbe.orquestador.cerebro.liberar_vram_ollama(f"tzimtzum: {proceso}")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada liberando VRAM en tzimtzum: %s", e)

        # HF-025c: Animar contracción antes de ocultar (hide() ocurre en _animar)
        self._orbe._escala_objetivo = 0.0
        self._orbe._tzimtzum_ocultando = True
        logger.info(f"צמצום Tzimtzum activado — proceso pesado: {proceso}")

    def _desactivar_tzimtzum(self):
        """אור חוזר Or Jozer — Re-expansión tras carga pesada."""
        self._en_tzimtzum = False
        self._tzimtzum_proceso = ""
        self._ticks_carga_pesada = 0
        self._ticks_carga_ligera = 0
        self._ticks_cpu_alto = 0
        self._orbe._tzimtzum_ocultando = False

        # Restaurar timers a velocidad normal
        if not self._timer_movimiento.isActive():
            self._timer_movimiento.start(16)
        if self._timer.isActive():
            self._timer.start(500)

        # HF-025c: Mostrar a escala 0 y animar expansión suave
        self._orbe._escala = 0.0
        self._orbe._escala_objetivo = 0.0
        # RF-144: Show + raise sin robar foco de la app gaming
        _hwnd = int(self._orbe.winId())
        ctypes.windll.user32.ShowWindow(_hwnd, 4)  # SW_SHOWNOACTIVATE
        # RF-136: Sincronizar _pos_anterior para evitar delta fantasma
        self._orbe._pos_anterior_x = float(self._orbe.x())
        self._orbe._pos_anterior_y = float(self._orbe.y())
        # HF-031: Re-asegurar transparencia tras hide→show (Qt/DWM puede perderla)
        self._orbe._reasegurar_transparencia()
        # RF-144 + RF-307: Raise sin activar — solo TOPMOST (sin NOTOPMOST que destruye topmost)
        _SWP = 0x0010 | 0x0002 | 0x0001  # SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE
        ctypes.windll.user32.SetWindowPos(_hwnd, -1, 0, 0, 0, 0, _SWP)   # HWND_TOPMOST
        # RF-137: Proteger escala durante re-expansión
        self._orbe._restaurando_tzimtzum = True
        self._orbe._escala_objetivo = 1.0
        self.restaurar_pleno()

        # Notificar al orbe para restaurar recursos
        try:
            self._orbe._desactivar_modo_carga_pesada()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error desactivando modo carga pesada en orbe")

        logger.info("אור חוזר Or Jozer — Tzimtzum desactivado, Computadora restaurada")

    def detener(self):
        """Detiene los timers y guarda heatmap."""
        # FIX RUBEDO: Detener daemon psutil\n        self._psutil_daemon_stop = True\n        self._timer.stop()
        self._timer_movimiento.stop()
        self._guardar_heatmap()


