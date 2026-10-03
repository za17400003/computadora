# computadora/metatron.py
from enum import Enum
from typing import Dict, List, Optional
import time
import threading
import psutil
from loguru import logger

class EstadoSistema(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


class MetatronOrquestador:
    """Orquestador del sistema Metatrón.
    
    WI-314: Implementado como singleton thread-safe para evitar thread explosion.
    Cada instancia creaba su propio _health_monitor thread. Ahora solo hay UNO.
    """
    _instance = None
    _instance_lock = threading.Lock()
    _health_thread_started = False

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        # Evitar reinicialización (mantiene estado entre llamadas)
        if self._initialized:
            return
        self._initialized = True

        self.estado_actual = EstadoSistema.IDLE
        self.metricas = {
            'latencia_whisper': [],
            'latencia_lm': [],
            'latencia_tts': [],
            'cpu_usage': 0,
            'gpu_usage': 0,
            'fps_orbe': 0,
            'errores': []
        }
        self._lock = threading.Lock()

        # WI-314: Solo iniciar UN health_thread en toda la vida del proceso
        if not MetatronOrquestador._health_thread_started:
            MetatronOrquestador._health_thread_started = True
            self._health_thread = threading.Thread(target=self._health_monitor, daemon=True)
            self._health_thread.start()
            logger.debug("MetatronOrquestador: health_monitor thread iniciado (único)")

    def set_estado(self, nuevo_estado: EstadoSistema, duracion=None):
        with self._lock:
            self.estado_actual = nuevo_estado
            if duracion:
                threading.Timer(duracion, lambda: self.set_estado(EstadoSistema.IDLE)).start()

    def registrar_metrica(self, nombre: str, valor: float):
        with self._lock:
            if nombre in self.metricas:
                if isinstance(self.metricas[nombre], list):
                    self.metricas[nombre].append(valor)
                    if len(self.metricas[nombre]) > 10:
                        self.metricas[nombre].pop(0)
                else:
                    self.metricas[nombre] = valor

    def _health_monitor(self):
        while True:
            try:
                self.metricas['cpu_usage'] = psutil.cpu_percent()
                self._evaluar_balance()
            except Exception:
                pass  # No romper el loop por errores de psutil
            time.sleep(5)

    def _evaluar_balance(self):
        # Placeholder - se implementa en fases posteriores
        pass

    def health_check(self) -> bool:
        checks = [
            self.metricas['cpu_usage'] < 95,
            len(self.metricas['errores']) < 5,
            all(lat < 3.0 for lat in self.metricas['latencia_whisper'][-3:]) if self.metricas['latencia_whisper'] else True,
            all(lat < 5.0 for lat in self.metricas['latencia_lm'][-3:]) if self.metricas['latencia_lm'] else True,
        ]
        return all(checks)


# WI-314: Función helper para tests que necesitan instancias limpias
def reset_metatron_singleton():
    """Resetea el singleton MetatronOrquestador (solo para tests)."""
    MetatronOrquestador._instance = None
    MetatronOrquestador._health_thread_started = False

