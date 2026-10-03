# computadora/utilidad/hardware_optimizer.py
import psutil
import threading
import time
from typing import Dict, List, Callable
from computadora.metatron import MetatronOrquestador

class HardwareOptimizer:
    def __init__(self, metatron: MetatronOrquestador):
        self.metatron = metatron
        self._cpu_count = psutil.cpu_count()
        self._has_gpu = self._detect_gpu()
        self._task_assignments: Dict[str, str] = {}  # task -> device
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _detect_gpu(self) -> bool:
        try:
            import GPUtil
            return len(GPUtil.getGPUs()) > 0
        except ImportError:
            return False

    def assign_task(self, task_name: str, task_func: Callable, priority: str = 'normal') -> str:
        """Assign task to optimal hardware based on priority and availability"""
        if priority == 'high' and self._has_gpu:
            device = 'gpu'
        elif priority == 'low':
            device = 'cpu_low'
        else:
            device = 'cpu_high'

        self._task_assignments[task_name] = device
        self.metatron.registrar_metrica(f'task_{task_name}_device', device)
        return device

    def get_system_load(self) -> Dict[str, float]:
        """Get current system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent

        load = {
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'cpu_available': 100 - cpu_percent,
            'ram_available': 100 - ram_percent
        }

        if self._has_gpu:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    load['gpu_percent'] = gpus[0].load * 100
                    load['gpu_available'] = 100 - (gpus[0].load * 100)
            except:
                load['gpu_percent'] = 0
                load['gpu_available'] = 100

        return load

    def optimize_for_load(self) -> Dict[str, bool]:
        """Optimize system based on current load"""
        load = self.get_system_load()
        optimizations = {}

        # CPU optimization
        if load['cpu_percent'] > 80:
            optimizations['reduce_fps'] = True
            optimizations['disable_animations'] = True
        elif load['cpu_percent'] > 60:
            optimizations['reduce_fps'] = True
            optimizations['disable_animations'] = False
        else:
            optimizations['reduce_fps'] = False
            optimizations['disable_animations'] = False

        # RAM optimization
        if load['ram_percent'] > 90:
            optimizations['aggressive_gc'] = True
        else:
            optimizations['aggressive_gc'] = False

        # Register optimizations
        for opt, enabled in optimizations.items():
            self.metatron.registrar_metrica(f'optimization_{opt}', 1 if enabled else 0)

        return optimizations

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            load = self.get_system_load()
            for metric, value in load.items():
                self.metatron.registrar_metrica(f'hardware_{metric}', value)

            self.optimize_for_load()
            time.sleep(2)  # Monitor every 2 seconds

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self._monitoring = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)

