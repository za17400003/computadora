"""🔐 Session Lock Listener Singleton — Global Guard contra doble-init

Evita que SessionLockListener se inicialice dos veces:
- Una vez en __main__.py (FP-135 TRINITY)
- Una vez en CerebroComputadora.__init__ (nlu.py)

Mantiene instancia global y se registra con atexit automáticamente.
"""

from typing import Optional, Callable
from loguru import logger

# Singleton global
_SESSION_LOCK_INSTANCE: Optional[object] = None
_SESSION_LOCK_INITIALIZED: bool = False


def get_session_lock_listener() -> Optional[object]:
    """Obtener instancia global de SessionLockListener.
    
    Retorna:
        SessionLockListener instancia si existe, None si no.
    """
    global _SESSION_LOCK_INSTANCE
    return _SESSION_LOCK_INSTANCE


def is_session_lock_initialized() -> bool:
    """¿Ya se inicializó SessionLockListener?
    
    Retorna:
        True si ya fue inicializado (evitar doble-init)
    """
    global _SESSION_LOCK_INITIALIZED
    return _SESSION_LOCK_INITIALIZED


def initialize_session_lock_singleton(
    on_lock: Optional[Callable] = None,
    on_unlock: Optional[Callable] = None,
) -> Optional[object]:
    """Inicializar SessionLockListener SOLO UNA VEZ (guard global).
    
    Args:
        on_lock: Callback cuando Windows+L detectado
        on_unlock: Callback cuando sesión desbloquea
    
    Retorna:
        SessionLockListener instancia, o None si ya existe o error.
    """
    global _SESSION_LOCK_INSTANCE, _SESSION_LOCK_INITIALIZED
    
    if _SESSION_LOCK_INITIALIZED:
        logger.debug("🔐 SessionLockListener: Ya inicializado previamente — usando instancia global")
        return _SESSION_LOCK_INSTANCE
    
    try:
        from computadora.utilidades.session_lock_listener import iniciar_session_lock_listener
        
        logger.info("🔐 SessionLockListener: Inicializando (singleton guard activo)...")
        _SESSION_LOCK_INSTANCE = iniciar_session_lock_listener(
            on_lock=on_lock,
            on_unlock=on_unlock,
        )
        _SESSION_LOCK_INITIALIZED = True
        
        logger.info("✅ SessionLockListener: Inicializado exitosamente (singleton)")
        return _SESSION_LOCK_INSTANCE
    
    except ImportError:
        logger.warning("⚠️  SessionLockListener: pywin32 no disponible (no Windows?)")
        _SESSION_LOCK_INITIALIZED = True  # Marcar como intentado aunque falló
        return None
    
    except Exception as e:
        logger.warning(f"⚠️  SessionLockListener: Error de inicialización: {e}")
        _SESSION_LOCK_INITIALIZED = True  # Marcar como intentado aunque falló
        return None


def shutdown_session_lock_singleton() -> None:
    """Detener SessionLockListener al salir de la aplicación."""
    global _SESSION_LOCK_INSTANCE
    
    if _SESSION_LOCK_INSTANCE is None:
        return
    
    try:
        from computadora.utilidades.session_lock_listener import detener_session_lock_listener
        detener_session_lock_listener()
        logger.debug("🔐 SessionLockListener: Detenido correctamente")
    except Exception as e:
        logger.debug(f"⚠️  SessionLockListener shutdown: {e}")
    finally:
        _SESSION_LOCK_INSTANCE = None


