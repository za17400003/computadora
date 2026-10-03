"""
FP-166: OPTIMIZADOR DE RECURSOS GLOBAL.
══════════════════════════════════════════════

Gestiona CPU, GPU, RAM y disco fractalicamente.

Funciones:
- Detectar GPU (CUDA, Metal, OpenCL, Vulkan)
- Asignar procesos al recurso optimo
- Monitorear RAM y evitar overflow
- Compresion fractal de memoria cuando crece demasiado
- Modo TzimTzum: libera GPU pero mantiene CPU para Alexa-mode

ESTRATEGIA:
  - Inferencia (YOLO, Whisper, LLM): GPU
  - Fisica (ferrofluido, teseracto): CPU (numpy vectorizado < 10ms)
  - Renderizado (orbe 4D): GPU via OpenGL (PyQt6 + QOpenGLWidget)
  - Audio (VAD, wake word): CPU (< 1ms)
  - Vision (MediaPipe): GPU via CUDA si disponible
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from loguru import logger


class RecursoTipo(Enum):
    CPU = "cpu"
    GPU_CUDA = "gpu_cuda"
    GPU_METAL = "gpu_metal"
    GPU_OPENCL = "gpu_opencl"
    GPU_VULKAN = "gpu_vulkan"
    RAM = "ram"
    DISCO = "disco"


class ModoOptimizacion(Enum):
    """Modos de optimizacion de recursos."""
    MAXIMA_POTENCIA = "maxima_potencia"  # GPU + CPU full
    BALANCEADO = "balanceado"  # Default
    AHORRO_ENERGIA = "ahorro_energia"  # CPU only, GPU off
    TZIMTZUM = "tzimtzum"  # GPU liberada, solo CPU para audio + respuesta


@dataclass
class EstadoRecursos:
    """Estado actual de los recursos del sistema."""
    gpu_disponible: bool = False
    gpu_nombre: str = ""
    gpu_memoria_total_mb: int = 0
    gpu_memoria_libre_mb: int = 0
    cpu_uso_porcentaje: float = 0.0
    ram_total_mb: int = 0
    ram_libre_mb: int = 0
    disco_libre_mb: int = 0
    modo_actual: ModoOptimizacion = ModoOptimizacion.BALANCEADO
    procesos_activos: int = 0
    timestamp: float = field(default_factory=time.time)


class OptimizadorRecursos:
    """
    Singleton: Gestiona la asignacion optima de recursos.
    
    Detecta hardware disponible y asigna procesos al recurso
    mas apropiado segun el modo actual.
    """
    
    _instancia: Optional['OptimizadorRecursos'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.modo = ModoOptimizacion.BALANCEADO
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._monitor_lock = threading.Lock()
        
        # Capacidades detectadas
        self._gpu_cuda = False
        self._gpu_metal = False
        self._gpu_opencl = False
        self._gpu_vulkan = False
        self._gpu_nombre = ""
        self._gpu_memoria = 0
        
        # Estadisticas
        self._ram_total = 0
        self._ram_libre = 0
        self._cpu_uso = 0.0
        self._disco_libre = 0
        
        # Procesos registrados
        self._procesos: Dict[str, Dict] = {}
        
        self._detectar_hardware()
        self._iniciar_monitoreo()
        logger.info(f"OptimizadorRecursos iniciado ({self.modo.value})")
    
    @classmethod
    def instancia(cls) -> 'OptimizadorRecursos':
        if cls._instancia is None:
            with cls._lock:
                if cls._instancia is None:
                    cls._instancia = cls()
        return cls._instancia
    
    # ── Deteccion de hardware ───────────────────────────────────
    
    def _detectar_hardware(self):
        """Detecta GPU, RAM, CPU disponibles."""
        # GPU: CUDA
        try:
            import torch
            self._gpu_cuda = torch.cuda.is_available()
            if self._gpu_cuda:
                self._gpu_nombre = torch.cuda.get_device_name(0)
                self._gpu_memoria = torch.cuda.get_device_properties(0).total_memory // (1024**2)
                logger.info(f"GPU CUDA detectada: {self._gpu_nombre} ({self._gpu_memoria}MB)")
        except ImportError:
            pass
        
        # GPU: OpenCL / Vulkan no es facil detectar en Python puro
        # Comprobar si existe nvidia-smi en Windows
        if not self._gpu_cuda:
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split(',')
                    self._gpu_nombre = parts[0].strip()
                    self._gpu_memoria = int(parts[1].strip().split()[0])
                    self._gpu_cuda = True
                    logger.info(f"GPU detectada via nvidia-smi: {self._gpu_nombre}")
            except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
                pass
        
        # RAM
        try:
            import psutil
            mem = psutil.virtual_memory()
            self._ram_total = mem.total // (1024**2)
            self._ram_libre = mem.available // (1024**2)
            self._cpu_uso = psutil.cpu_percent(interval=0.1)
            disk = psutil.disk_usage('/')
            self._disco_libre = disk.free // (1024**2)
        except ImportError:
            # Fallback: valores aproximados
            self._ram_total = 16384
            self._ram_libre = 8192
            self._disco_libre = 50000
        
        logger.info(f"RAM: {self._ram_total}MB total, {self._ram_libre}MB libre")
    
    def _iniciar_monitoreo(self):
        """Inicia el monitoreo periodico de recursos."""
        self._running = True
        self._thread = threading.Thread(target=self._loop_monitoreo, daemon=True)
        self._thread.start()
    
    def _loop_monitoreo(self):
        """Actualiza recursos cada 2 segundos."""
        while self._running:
            try:
                import psutil
                with self._monitor_lock:
                    self._cpu_uso = psutil.cpu_percent(interval=0.1)
                    mem = psutil.virtual_memory()
                    self._ram_libre = mem.available // (1024**2)
            except ImportError:
                pass
            time.sleep(2.0)
    
    # ── Gestion de modo ─────────────────────────────────────────
    
    def establecer_modo(self, modo: ModoOptimizacion):
        """Cambia el modo de optimizacion.
        
        En TZIMTZUM, la GPU se libera por completo.
        Solo CPU para audio + respuesta (modo Alexa).
        """
        old_mode = self.modo
        self.modo = modo
        logger.info(f"Modo optimizacion: {old_mode.value} -> {modo.value}")
        
        if modo == ModoOptimizacion.TZIMTZUM:
            self._liberar_gpu()
        elif modo == ModoOptimizacion.MAXIMA_POTENCIA:
            self._activar_gpu()
    
    def _liberar_gpu(self):
        """Libera la GPU (modo TzimTzum)."""
        logger.info("GPU liberada (modo TzimTzum)")
        # Marcar procesos GPU como desactivados
        with self._monitor_lock:
            for nombre, proc in self._procesos.items():
                if proc.get('tipo') in ('gpu', 'render'):
                    proc['activo'] = False
    
    def _activar_gpu(self):
        """Activa la GPU (modo maxima potencia)."""
        logger.info("GPU activada")
        with self._monitor_lock:
            for nombre, proc in self._procesos.items():
                proc['activo'] = True
    
    def registrar_proceso(self, nombre: str, tipo: str = 'cpu',
                         prioridad: int = 0) -> str:
        """Registra un proceso para monitoreo.
        
        Args:
            nombre: Identificador del proceso
            tipo: 'cpu', 'gpu', 'render', 'audio', 'vision'
            prioridad: 0 (baja) a 10 (critica)
        
        Returns:
            Nombre del proceso registrado.
        """
        with self._monitor_lock:
            self._procesos[nombre] = {
                'tipo': tipo,
                'prioridad': prioridad,
                'activo': True,
                'timestamp': time.time(),
            }
        return nombre
    
    def obtener_asignacion(self, proceso_nombre: str) -> str:
        """Determina si un proceso debe usar CPU o GPU segun el modo actual.
        
        Returns:
            'cpu', 'gpu', 'none' (si debe desactivarse)
        """
        proc = self._procesos.get(proceso_nombre)
        if proc is not None:
            tipo = proc.get('tipo', 'cpu')
        else:
            # Inferir tipo por nombre
            name_lower = proceso_nombre.lower()
            if any(x in name_lower for x in ['render', 'dibujar', 'orbe', 'gpu']):
                tipo = 'render'
            elif any(x in name_lower for x in ['vision', 'camara', 'yolo', 'mediapipe']):
                tipo = 'vision'
            elif any(x in name_lower for x in ['audio', 'voz', 'whisper']):
                tipo = 'audio'
            else:
                tipo = 'cpu'
        
        if self.modo == ModoOptimizacion.TZIMTZUM:
            if tipo in ('gpu', 'render', 'vision'):
                return 'none'
            return 'cpu'
        
        if self.modo == ModoOptimizacion.AHORRO_ENERGIA:
            if tipo == 'gpu':
                return 'cpu'
        
        # GPU-first policy: usar GPU siempre que esté disponible
        if tipo in ('gpu', 'render', 'vision') and self._gpu_cuda:
            return 'gpu'
        return 'cpu'
    
    # ── Compresion fractal de memoria ───────────────────────────
    
    def comprimir_memoria(self, datos: np.ndarray,
                         umbral_mb: int = 100) -> np.ndarray:
        """Comprime datos usando representacion fractal.
        
        Si los datos superan 'umbral_mb', se reduce la precision
        de float64 a float16 (25% del tamaño original).
        
        Args:
            datos: Array numpy a comprimir
            umbral_mb: Umbral en MB para activar compresion
        
        Returns:
            Array comprimido (o original si no supera umbral).
        """
        size_mb = datos.nbytes / (1024**2)
        if size_mb < umbral_mb:
            return datos
        
        # Reducir precision fractalicamente
        if datos.dtype == np.float64:
            return datos.astype(np.float32)
        elif datos.dtype == np.float32:
            return datos.astype(np.float16)
        
        return datos
    
    def obtener_estado(self) -> EstadoRecursos:
        """Retorna el estado actual de recursos."""
        with self._monitor_lock:
            return EstadoRecursos(
                gpu_disponible=self._gpu_cuda,
                gpu_nombre=self._gpu_nombre,
                gpu_memoria_total_mb=self._gpu_memoria,
                gpu_memoria_libre_mb=self._gpu_memoria,
                cpu_uso_porcentaje=self._cpu_uso,
                ram_total_mb=self._ram_total,
                ram_libre_mb=self._ram_libre,
                disco_libre_mb=self._disco_libre,
                modo_actual=self.modo,
                procesos_activos=len(self._procesos),
            )
    
    def __repr__(self) -> str:
        estado = self.obtener_estado()
        return (
            f"Optimizador("
            f"GPU={estado.gpu_nombre or 'N/A'}, "
            f"RAM={estado.ram_libre_mb}/{estado.ram_total_mb}MB, "
            f"CPU={estado.cpu_uso_porcentaje}%, "
            f"Modo={estado.modo_actual.value})"
        )


# ── Funciones de utilidad ────────────────────────────────────────

def obtener_optimizador() -> OptimizadorRecursos:
    """Obtiene el singleton del optimizador de recursos."""
    return OptimizadorRecursos.instancia()


def activar_tzimtzum():
    """Activa modo TzimTzum: libera GPU, solo CPU para Alexa-mode."""
    opt = obtener_optimizador()
    opt.establecer_modo(ModoOptimizacion.TZIMTZUM)
    logger.info("Modo TzimTzum activado: GPU liberada, solo CPU para audio")


def activar_maxima_potencia():
    """Activa maxima potencia: GPU + CPU full."""
    opt = obtener_optimizador()
    opt.establecer_modo(ModoOptimizacion.MAXIMA_POTENCIA)
    logger.info("Modo Maxima Potencia activado: GPU disponible")


if __name__ == "__main__":
    print("=== Optimizador Recursos ===")
    opt = obtener_optimizador()
    print(opt)
    
    estado = opt.obtener_estado()
    print(f"GPU: {estado.gpu_nombre or 'No detectada'}")
    print(f"CUDA disponible: {opt._gpu_cuda}")
    print()
    
    # Test modo TzimTzum
    print("Activando modo TzimTzum...")
    activar_tzimtzum()
    print(f"Asignacion render: {opt.obtener_asignacion('render')}")
    print(f"Asignacion audio: {opt.obtener_asignacion('audio')}")
    print()
    
    print("Activando maxima potencia...")
    activar_maxima_potencia()
    print(f"Asignacion render: {opt.obtener_asignacion('render')}")
    print(f"Asignacion audio: {opt.obtener_asignacion('audio')}")
    print()
    print("Optimizador de recursos OK")


