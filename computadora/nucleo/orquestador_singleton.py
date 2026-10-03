"""
Orquestador Singleton Pattern — Evita instancias múltiples

Una sola instancia de Orquestador compartida entre:
- UI Principal (ventana_principal.py)
- Canal Discord
- Canal Telegram
- API Minimi
- Watchdog
"""

import threading
from loguru import logger

_lock = threading.Lock()
_singleton_instance = None


def obtener_orquestador_singleton(config=None, cerebro=None):
    """
    Obtener o crear una única instancia de Orquestador.
    
    Primer call: DEBE proporcionar config + cerebro
    Llamadas posteriores: Se ignoran config/cerebro, retorna singleton
    """
    global _singleton_instance
    
    if _singleton_instance is None:
        with _lock:
            if _singleton_instance is None:
                if config is None or cerebro is None:
                    raise ValueError("Primera llamada a obtener_orquestador_singleton() requiere config + cerebro")
                
                from computadora.nucleo.orquestador import Orquestador
                _singleton_instance = Orquestador(config, cerebro=cerebro)
                logger.info("✓ Orquestador singleton creado (instancia UNICA)")
    
    return _singleton_instance


def reset_singleton():
    """Reset para tests"""
    global _singleton_instance
    with _lock:
        _singleton_instance = None


