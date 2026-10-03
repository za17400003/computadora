"""Feature Flags para Computadora — Control de funcionalidad de subsistemas.

Este módulo centraliza el control de qué subsistemas de Computadora están 
activos o pausados, permitiendo pruebas aisladas de RFs específicos.

Las flags se cargan desde config.json y pueden modificarse en tiempo de ejecución.
"""

from loguru import logger
from computadora.config import Configuracion


class FeatureFlags:
    """Gestor singleton para feature flags del sistema."""
    
    _instancia = None
    _flags_cache = {}
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia
    
    def _inicializar(self):
        """Carga flags desde configuración."""
        config = Configuracion()
        self._flags_cache = config.obtener("feature_flags", {})
        
        # Flags por defecto (en caso de que falten en config.json)
        self._defaults = {
            "escucha_voz": True,
            "nlu_herramientas": True,
            "tts": True,
            "nivel2_ollama": True,
            "proactividad": False,
            "monitor_sistema": False,
            "emociones_ruaj": False,
            "contexto_visual": False,
            "reconocimiento_facial": False,
            "life_autonomy": False,
            "circadian_cycles": False,
            "guardian_activo": False,  # WI-AUDIO: Guardian desactivado temporalmente
        }
        
        # Completar flags faltantes con defaults
        for key, default_val in self._defaults.items():
            if key not in self._flags_cache:
                self._flags_cache[key] = default_val
        
        logger.info(f"🚩 Feature Flags inicializados: {self._flags_cache}")
    
    @classmethod
    def obtener(cls, nombre: str) -> bool:
        """Obtiene el estado de una flag."""
        instancia = cls()
        valor = instancia._flags_cache.get(nombre, instancia._defaults.get(nombre, False))
        return bool(valor)
    
    @classmethod
    def activar(cls, nombre: str):
        """Activa una flag en tiempo de ejecución."""
        instancia = cls()
        instancia._flags_cache[nombre] = True
        logger.info(f"🚩 Feature flag ACTIVADA: {nombre}")
    
    @classmethod
    def desactivar(cls, nombre: str):
        """Desactiva una flag en tiempo de ejecución."""
        instancia = cls()
        instancia._flags_cache[nombre] = False
        logger.info(f"🚩 Feature flag DESACTIVADA: {nombre}")
    
    @classmethod
    def obtener_todas(cls) -> dict:
        """Obtiene todas las flags."""
        instancia = cls()
        return dict(instancia._flags_cache)
    
    @classmethod
    def actualizar(cls, nuevas_flags: dict):
        """Actualiza múltiples flags."""
        instancia = cls()
        instancia._flags_cache.update(nuevas_flags)
        logger.info(f"🚩 Flags actualizadas: {nuevas_flags}")


# Alias conveniente para uso rápido
def obtener_flag(nombre: str) -> bool:
    """Obtiene el estado de una flag de forma rápida."""
    return FeatureFlags.obtener(nombre)


