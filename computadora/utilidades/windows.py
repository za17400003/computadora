"""
Contexto de Pantalla — Los Ojos de Computadora.

Monitorea la ventana activa del escritorio via Win32 API.
Solo lee títulos de ventana (privacidad). NO captura contenido de pantalla.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import re
import time
from collections import deque
from dataclasses import dataclass
from threading import Thread, Event
from typing import NamedTuple

from loguru import logger

# ═══════════════════════════════════════════════
# WIN32 FUNCTION SIGNATURES (64-bit safe)
# Sin restype/argtypes, ctypes trunca HWND a c_int
# (32-bit) → sign-extension → access violation
# ═══════════════════════════════════════════════
_user32 = ctypes.windll.user32
_user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
_user32.IsWindow.restype = ctypes.wintypes.BOOL
_user32.IsWindow.argtypes = [ctypes.wintypes.HWND]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
_user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
_user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]

_kernel32 = ctypes.windll.kernel32
_kernel32.OpenProcess.restype = ctypes.wintypes.HANDLE
_kernel32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
_kernel32.CloseHandle.restype = ctypes.wintypes.BOOL
_kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
_kernel32.QueryFullProcessImageNameW.restype = ctypes.wintypes.BOOL
_kernel32.QueryFullProcessImageNameW.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
    ctypes.wintypes.LPWSTR, ctypes.POINTER(ctypes.wintypes.DWORD),
]


# ═══════════════════════════════════════════════
# TIPOS
# ═══════════════════════════════════════════════

class VentanaInfo(NamedTuple):
    titulo: str
    proceso: str
    hwnd: int


@dataclass
class _EntradaHistorial:
    titulo: str
    proceso: str
    timestamp: float


# ═══════════════════════════════════════════════
# PATRONES DE DETECCIÓN
# ═══════════════════════════════════════════════

_RE_ERROR = re.compile(
    r'\b(error|exception|crash|fault|failed|failure|traceback|unhandled|fatal)\b',
    re.IGNORECASE,
)

_MAPA_APPS = {
    'chrome': 'Google Chrome',
    'firefox': 'Firefox',
    'msedge': 'Microsoft Edge',
    'code': 'Visual Studio Code',
    'explorer': 'Explorador de archivos',
    'notepad': 'Bloc de notas',
    'discord': 'Discord',
    'spotify': 'Spotify',
    'steam': 'Steam',
    'telegram': 'Telegram',
    'whatsapp': 'WhatsApp',
    'excel': 'Excel',
    'winword': 'Word',
    'powerpnt': 'PowerPoint',
    'devenv': 'Visual Studio',
    'idea64': 'IntelliJ IDEA',
    'windowsterminal': 'Terminal de Windows',
    'powershell': 'PowerShell',
    'cmd': 'Símbolo del sistema',
}


# ═══════════════════════════════════════════════
# CONTEXTO DE PANTALLA
# ═══════════════════════════════════════════════

class ContextoPantalla:
    """Monitorea la ventana activa y actividad del usuario via Win32."""

    def __init__(self):
        self._titulo_actual: str = ""
        self._proceso_actual: str = ""
        self._hwnd_actual: int = 0
        self._historial: deque[_EntradaHistorial] = deque(maxlen=20)
        self._ultimo_cambio: float = time.time()
        self._cambios_recientes: deque[float] = deque(maxlen=20)

        self._detener = Event()
        self._hilo = Thread(target=self._loop_actualizar, daemon=True, name="ContextoPantalla")
        self._hilo.start()
        logger.info("ContextoPantalla iniciado — COMPUTADORA tiene ojos")

    def detener(self):
        self._detener.set()

    # ─── API pública ────────────────────────────

    def obtener_ventana_activa(self) -> VentanaInfo:
        return VentanaInfo(self._titulo_actual, self._proceso_actual, self._hwnd_actual)

    def detectar_estres(self) -> bool:
        """True si >5 cambios de ventana en los últimos 10 segundos."""
        ahora = time.time()
        recientes = sum(1 for t in self._cambios_recientes if ahora - t < 10.0)
        return recientes > 5

    def detectar_inactividad(self, umbral_min: float = 15.0) -> bool:
        """True si no hay cambios de ventana en >umbral_min minutos."""
        return (time.time() - self._ultimo_cambio) > (umbral_min * 60)

    def detectar_error_en_pantalla(self) -> str | None:
        """Retorna el título si contiene palabras de error, None si no."""
        if self._titulo_actual and _RE_ERROR.search(self._titulo_actual):
            return self._titulo_actual
        return None

    def descripcion_contexto(self) -> str:
        """Resumen legible: 'Estás en Chrome mirando GitHub'."""
        if not self._titulo_actual:
            return "No puedo ver qué estás haciendo"

        app_nombre = _MAPA_APPS.get(self._proceso_actual.lower().replace('.exe', ''), '')
        if app_nombre:
            titulo_limpio = self._titulo_actual
            # Quitar el nombre de la app del título si ya está
            for sufijo in [f' - {app_nombre}', f' — {app_nombre}', f' | {app_nombre}']:
                titulo_limpio = titulo_limpio.replace(sufijo, '')
            if titulo_limpio and titulo_limpio != self._titulo_actual:
                return f"Estás en {app_nombre} mirando {titulo_limpio.strip()}"
            return f"Estás en {app_nombre}"

        if self._titulo_actual:
            return f"Estás en una ventana: {self._titulo_actual[:60]}"
        return "Escritorio"

    def segundos_desde_ultimo_cambio(self) -> float:
        return time.time() - self._ultimo_cambio

    # ─── Loop interno ───────────────────────────

    def _loop_actualizar(self):
        while not self._detener.is_set():
            try:
                self._actualizar()
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            self._detener.wait(2.0)

    def _actualizar(self):
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return

        # Título
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        titulo = buf.value

        # Proceso
        proceso = ""
        try:
            pid = ctypes.wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                h_proc = ctypes.windll.kernel32.OpenProcess(0x0410, False, pid.value)  # QUERY_INFO | VM_READ
                if h_proc:
                    try:
                        exe_buf = ctypes.create_unicode_buffer(260)
                        size = ctypes.wintypes.DWORD(260)
                        ctypes.windll.kernel32.QueryFullProcessImageNameW(h_proc, 0, exe_buf, ctypes.byref(size))
                        proceso = os.path.basename(exe_buf.value) if exe_buf.value else ""
                    finally:
                        ctypes.windll.kernel32.CloseHandle(h_proc)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Detectar cambios
        if titulo != self._titulo_actual:
            ahora = time.time()
            self._ultimo_cambio = ahora
            self._cambios_recientes.append(ahora)
            self._historial.append(_EntradaHistorial(titulo, proceso, ahora))

        self._titulo_actual = titulo
        self._proceso_actual = proceso
        self._hwnd_actual = hwnd

    # ─── Detección de media activa (FP-044) ───

    _RE_MEDIA_TITULO = re.compile(
        r'youtube|netflix|spotify|prime\s*video|disney\+?|twitch|vlc|plex|hbo'
        r'|crunchyroll|media\s*player|reproductor'
        r'|steam|epic\s*games|geforce|xbox|playstation|gog\s*galaxy',
        re.IGNORECASE,
    )
    _PROCESOS_MEDIA = frozenset({
        'spotify.exe', 'vlc.exe', 'wmplayer.exe', 'msedge.exe',
        'chrome.exe', 'firefox.exe', 'brave.exe', 'opera.exe',
        # RF-296: Gaming platforms
        'steam.exe', 'steamwebhelper.exe', 'epicgameslauncher.exe',
        'galaxyclient.exe', 'gog galaxy.exe',
    })

    def hay_media_activa(self) -> bool:
        """True si la ventana activa parece reproducir media (YouTube, Spotify, etc.)."""
        titulo = self._titulo_actual
        proceso = self._proceso_actual.lower()
        if not titulo:
            return False
        if self._RE_MEDIA_TITULO.search(titulo):
            return True
        # Spotify como proceso aunque no esté en primer plano con título media
        if proceso == 'spotify.exe':
            return True
        return False


