"""
נשמה (Neshamá) — Alma Consciente.
Autopercepción del entorno de ejecución de Computadora.
Detecta y cachea: OS, CPU, RAM, disco, GPU, red, batería, timezone.
Primary: psutil | Fallback: subprocess + PowerShell/wmic.
"""

import os
import platform
import socket
import time
import subprocess
from datetime import datetime, timezone
from loguru import logger

# Cache TTL en segundos
_CACHE_TTL = 60


def _cache(method):
    """Decorador que cachea el resultado de un método por _CACHE_TTL segundos."""
    attr = f"_cache_{method.__name__}"
    ts_attr = f"_ts_{method.__name__}"

    def wrapper(self):
        now = time.monotonic()
        cached_ts = getattr(self, ts_attr, 0)
        if now - cached_ts < _CACHE_TTL:
            return getattr(self, attr)
        try:
            result = method(self)
        except Exception as e:
            logger.debug(f"Entorno.{method.__name__} falló: {e}")
            result = getattr(self, attr, "desconocido")
        setattr(self, attr, result)
        setattr(self, ts_attr, now)
        return result

    wrapper.__name__ = method.__name__
    return wrapper


class EntornoSistema:
    """Singleton — información del entorno de ejecución de Computadora."""

    _instancia = None

    @classmethod
    def instancia(cls):
        """Obtiene la instancia singleton de EntornoSistema."""
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def __init__(self):
        # Solo inicializar una vez
        if hasattr(self, '_inicializado'):
            return
        self._inicializado = True
        # Datos estáticos (no cambian durante la ejecución)
        self.os_nombre = platform.system()             # "Windows"
        self.os_version = platform.version()            # "10.0.22631"
        self.os_release = platform.release()            # "11" o "10"
        self.arquitectura = platform.machine()          # "AMD64"
        self.hostname = socket.gethostname()
        self.usuario = os.getenv("USERNAME") or os.getenv("USER") or "desconocido"
        self.python_version = platform.python_version()
        self.timezone = self._detectar_timezone()
        self.cpu_nombre = self._detectar_cpu_nombre()
        self.cpu_nucleos = os.cpu_count() or 0
        self.ram_total_gb = self._detectar_ram_total()
        self.gpu_nombre = self._detectar_gpu()
        logger.info(f"EntornoSistema inicializado: {self.resumen_corto()}")

    # ── Detecciones estáticas (solo al inicio) ──

    def _detectar_timezone(self) -> str:
        try:
            ahora = datetime.now(timezone.utc).astimezone()
            return str(ahora.tzinfo)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return "desconocido"

    def _detectar_cpu_nombre(self) -> str:
        try:
            import psutil
            # psutil no tiene nombre de CPU directamente, usar platform
            pass
        except ImportError:
            pass
        # Fallback: registro de Windows via wmic
        try:
            r = subprocess.run(
                ["wmic", "cpu", "get", "Name", "/value"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            )
            for linea in r.stdout.splitlines():
                if linea.startswith("Name="):
                    return linea.split("=", 1)[1].strip()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return platform.processor() or "desconocido"

    def _detectar_ram_total(self) -> float:
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024 ** 3), 1)
        except ImportError:
            pass
        try:
            r = subprocess.run(
                ["wmic", "memorychip", "get", "Capacity", "/value"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            )
            total = 0
            for linea in r.stdout.splitlines():
                if linea.startswith("Capacity="):
                    total += int(linea.split("=", 1)[1].strip())
            if total > 0:
                return round(total / (1024 ** 3), 1)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return 0.0

    def _detectar_gpu(self) -> str:
        try:
            r = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "Name", "/value"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            )
            gpus = []
            for linea in r.stdout.splitlines():
                if linea.startswith("Name="):
                    name = linea.split("=", 1)[1].strip()
                    gpus.append(name)
            
            # Priorizar GPU dedicada (NVIDIA/AMD) sobre integrada (Intel)
            for gpu in gpus:
                if any(keyword in gpu.lower() for keyword in ['nvidia', 'geforce', 'gtx', 'rtx', 'titan', 'quadro', 'amd', 'radeon', 'rx']):
                    return gpu
            # Si no hay dedicada, usar la primera
            if gpus:
                return gpus[0]
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return "desconocido"

    # ── Datos dinámicos (con cache TTL) ──

    @_cache
    def cpu(self) -> dict:
        """Uso actual de CPU."""
        try:
            import psutil
            return {
                "porcentaje": psutil.cpu_percent(interval=0),  # WI-258: non-blocking
                "frecuencia_mhz": getattr(psutil.cpu_freq(), "current", 0),
            }
        except ImportError:
            return {"porcentaje": 0, "frecuencia_mhz": 0}

    @_cache
    def ram(self) -> dict:
        """Uso actual de RAM."""
        try:
            import psutil
            vm = psutil.virtual_memory()
            return {
                "total_gb": round(vm.total / (1024 ** 3), 1),
                "usado_gb": round(vm.used / (1024 ** 3), 1),
                "porcentaje": vm.percent,
            }
        except ImportError:
            return {"total_gb": self.ram_total_gb, "usado_gb": 0, "porcentaje": 0}

    @_cache
    def disco(self) -> dict:
        """Uso del disco principal."""
        try:
            import psutil
            d = psutil.disk_usage("C:\\")
            return {
                "total_gb": round(d.total / (1024 ** 3), 1),
                "libre_gb": round(d.free / (1024 ** 3), 1),
                "porcentaje_usado": d.percent,
            }
        except ImportError:
            return {"total_gb": 0, "libre_gb": 0, "porcentaje_usado": 0}

    @_cache
    def red(self) -> dict:
        """Estado de red."""
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            # Buscar IP local (no loopback)
            ip_local = "desconocido"
            for iface, lista in addrs.items():
                for addr in lista:
                    if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                        ip_local = addr.address
                        break
                if ip_local != "desconocido":
                    break
            # Verificar conectividad
            conectado = False
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=2).close()
                conectado = True
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            return {"ip_local": ip_local, "conectado": conectado}
        except ImportError:
            return {"ip_local": "desconocido", "conectado": False}

    @_cache
    def bateria(self) -> dict | None:
        """Estado de batería (None si es desktop)."""
        try:
            import psutil
            bat = psutil.sensors_battery()
            if bat is None:
                return None
            return {
                "porcentaje": bat.percent,
                "cargando": bat.power_plugged,
            }
        except (ImportError, AttributeError):
            return None

    def ollama_status(self) -> dict:
        """Verifica estado de Ollama sin importar módulos de cerebro."""
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                modelos = [m["name"] for m in r.json().get("models", [])]
                return {"disponible": True, "modelos": modelos}
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return {"disponible": False, "modelos": []}

    # ── Resúmenes ──

    def resumen_corto(self) -> str:
        """Una línea para inyectar en system prompt."""
        partes = [
            f"{self.os_nombre} {self.os_release}",
            self.cpu_nombre if self.cpu_nombre != "desconocido" else None,
            f"{self.ram_total_gb}GB RAM" if self.ram_total_gb else None,
        ]
        disco = self.disco()
        if disco["libre_gb"]:
            partes.append(f"{disco['libre_gb']}GB disco libre")
        if self.gpu_nombre != "desconocido":
            partes.append(f"GPU: {self.gpu_nombre}")
        red_info = self.red()
        partes.append("Online" if red_info["conectado"] else "Offline")
        return " | ".join(p for p in partes if p)

    def resumen_completo(self) -> str:
        """Multi-línea para herramienta info_entorno."""
        ram = self.ram()
        disco = self.disco()
        red_info = self.red()
        bat = self.bateria()
        cpu_info = self.cpu()

        lineas = [
            f"Sistema Operativo: {self.os_nombre} {self.os_release} (v{self.os_version})",
            f"Arquitectura: {self.arquitectura}",
            f"Hostname: {self.hostname}",
            f"Usuario: {self.usuario}",
            f"Timezone: {self.timezone}",
            f"Python: {self.python_version}",
            f"CPU: {self.cpu_nombre} ({self.cpu_nucleos} núcleos, {cpu_info['porcentaje']}% uso, {cpu_info['frecuencia_mhz']:.0f}MHz)",
            f"RAM: {ram['usado_gb']}GB / {ram['total_gb']}GB ({ram['porcentaje']}% uso)",
            f"Disco C: {disco['libre_gb']}GB libres de {disco['total_gb']}GB ({disco['porcentaje_usado']}% uso)",
            f"GPU: {self.gpu_nombre}",
            f"Red: IP {red_info['ip_local']}, {'conectado' if red_info['conectado'] else 'sin conexión'}",
        ]
        if bat is not None:
            lineas.append(f"Batería: {bat['porcentaje']}% ({'cargando' if bat['cargando'] else 'descargando'})")
        else:
            lineas.append("Batería: No detectada (escritorio)")

        ollama = self.ollama_status()
        if ollama["disponible"]:
            lineas.append(f"Ollama: activo, modelos: {', '.join(ollama['modelos'])}")
        else:
            lineas.append("Ollama: no disponible")

        return "\n".join(lineas)


