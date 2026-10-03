"""
computadora/utilidades/session_lock_listener.py — WM_SESSIONLOCK Detector

Monitorea eventos de bloqueo de sesión Windows (Ctrl+Alt+Del, Win+L, Sleep).
Cuando detecta bloqueo → callback para activar modo guardián.
"""

import ctypes
import ctypes.wintypes
from threading import Thread, Event
from typing import Callable, Optional
from loguru import logger


# Win32 Event Hook Constants
EVENT_SYSTEM_FOREGROUND = 3
EVENT_SYSTEM_LOCKSCREEN = 19
EVENT_SYSTEM_DESKTOPSWITCH = 7

# Win32 Function signatures
_user32 = ctypes.windll.user32
_user32.SetWinEventHook.restype = ctypes.c_void_p  # HWINEVENTHOOK handle
_user32.SetWinEventHook.argtypes = [
    ctypes.wintypes.UINT,  # eventMin
    ctypes.wintypes.UINT,  # eventMax
    ctypes.wintypes.HANDLE,  # hmodWinEventHook
    ctypes.c_void_p,  # lpfnWinEventHook (callback)
    ctypes.wintypes.DWORD,  # idProcess
    ctypes.wintypes.DWORD,  # idThread
    ctypes.wintypes.UINT,  # dwFlags
]

_user32.UnhookWinEvent.restype = ctypes.wintypes.BOOL
_user32.UnhookWinEvent.argtypes = [ctypes.c_void_p]  # HWINEVENTHOOK

_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]

_user32.GetClassNameW.restype = ctypes.c_int
_user32.GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]

# Event hook flags
EVENT_HOOK_OUT_OF_CONTEXT = 0


class SessionLockListener:
    """
    Escucha eventos de bloqueo de sesión Windows.
    
    Cuando se detecta bloqueo (Win+L, Ctrl+Alt+Del, Sleep) → callback
    Tipicamente, callback activa modo_guardian en NLU.
    """
    
    def __init__(self, on_lock: Optional[Callable[[], None]] = None,
                 on_unlock: Optional[Callable[[], None]] = None):
        """
        Args:
            on_lock: Callback cuando sesión se bloquea
            on_unlock: Callback cuando sesión se desbloquea
        """
        self.on_lock = on_lock or (lambda: None)
        self.on_unlock = on_unlock or (lambda: None)
        
        self._hook_handle: Optional[ctypes.c_void_p] = None
        self._is_locked = False
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        
        # Keep reference to callback (prevent garbage collection)
        self._callback_ref = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p,  # HWINEVENTHOOK
            ctypes.wintypes.UINT,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD
        )(self._win_event_hook)
    
    def start(self):
        """Inicia listener en thread daemon."""
        if self._hook_handle is not None:
            return  # Already running
        
        self._stop_event.clear()
        self._thread = Thread(target=self._run_listener, daemon=True, name="SessionLockListener")
        self._thread.start()
        logger.info("SessionLockListener iniciado — COMPUTADORA vigila bloqueos de sesión")
    
    def stop(self):
        """Detiene listener."""
        self._stop_event.set()
        
        if self._hook_handle:
            try:
                _user32.UnhookWinEvent(self._hook_handle)
                self._hook_handle = None
            except Exception as e:
                logger.warning(f"Error unhooking: {e}")
        
        if self._thread:
            self._thread.join(timeout=2.0)

    def esta_bloqueada(self) -> bool:
        """Retorna True si la sesión Windows está actualmente bloqueada."""
        return self._is_locked

    def _run_listener(self):
        """Corre el event loop en thread separado."""
        try:
            # Hook para detectar cambios de focus + lock screen
            self._hook_handle = _user32.SetWinEventHook(
                EVENT_SYSTEM_FOREGROUND,
                EVENT_SYSTEM_DESKTOPSWITCH,
                None,
                self._callback_ref,
                0,  # idProcess (0 = all)
                0,  # idThread (0 = all)
                EVENT_HOOK_OUT_OF_CONTEXT
            )
            
            if not self._hook_handle:
                logger.error("SetWinEventHook failed")
                return
            
            logger.info("SessionLockListener hook instalado")
            
            # Keep thread alive until stopped
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=1.0)
        
        except Exception as e:
            logger.error(f"SessionLockListener error: {e}")
        finally:
            if self._hook_handle:
                try:
                    _user32.UnhookWinEvent(self._hook_handle)
                    self._hook_handle = None
                except Exception as e:
                    logger.debug(f"Error unhooking Win32 event: {e}")
    
    def _win_event_hook(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        """Callback invocado por Win32 cuando ocurre evento monitoreado."""
        try:
            # Obtener título de ventana
            title_buf = ctypes.create_unicode_buffer(256)
            _user32.GetWindowTextW(hwnd, title_buf, 256)
            title = title_buf.value or ""
            
            # Obtener clase de ventana (ayuda a detectar lock screen)
            class_buf = ctypes.create_unicode_buffer(256)
            _user32.GetClassNameW(hwnd, class_buf, 256)
            wnd_class = class_buf.value or ""
            
            # Detectar lock screen
            # En Windows, la lock screen suele tener clase "MessageBoxW" o estar en modo "DeskBand"
            # También detectar si el título contiene "Lock" o si es un escritorio oscuro
            is_lock_screen = (
                "WorkerW" in wnd_class or  # Desktop worker (lock screen)
                "DeskBand" in wnd_class or
                title.lower() in ["", "desktop", "windows secure desktop", "screensaver"] or
                hwnd == 0  # Background/desktop
            )
            
            if is_lock_screen and not self._is_locked:
                logger.info("🔒 Sesión BLOQUEADA — Modo Guardián ACTIVADO")
                self._is_locked = True
                self.on_lock()
            
            elif not is_lock_screen and self._is_locked:
                logger.info("🔓 Sesión DESBLOQUEADA — Modo Guardián DESACTIVADO")
                self._is_locked = False
                self.on_unlock()
        
        except Exception as e:
            logger.debug(f"Hook callback error (ignorado): {e}")


# Singleton instance para acceso global
_session_listener: Optional[SessionLockListener] = None


def iniciar_session_lock_listener(on_lock: Optional[Callable] = None,
                                   on_unlock: Optional[Callable] = None) -> SessionLockListener:
    """
    Crea e inicia listener global.
    
    Args:
        on_lock: Callback al bloquear sesión
        on_unlock: Callback al desbloquear
    
    Returns:
        SessionLockListener instance
    """
    global _session_listener
    
    if _session_listener is not None:
        logger.warning("SessionLockListener ya está activo")
        return _session_listener
    
    _session_listener = SessionLockListener(on_lock=on_lock, on_unlock=on_unlock)
    _session_listener.start()
    return _session_listener


def detener_session_lock_listener():
    """Detiene listener global."""
    global _session_listener
    
    if _session_listener:
        _session_listener.stop()
        _session_listener = None
        logger.info("SessionLockListener detenido")


def obtener_session_lock_listener() -> Optional[SessionLockListener]:
    """Obtiene instancia global (si existe)."""
    return _session_listener


def es_session_lock_bloqueada() -> bool:
    """Retorna True si la sesión Windows está bloqueada actualmente."""
    listener = obtener_session_lock_listener()
    return bool(listener and listener.esta_bloqueada())


