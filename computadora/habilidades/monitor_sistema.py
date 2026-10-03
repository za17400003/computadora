"""
Monitor de Sistema en Tiempo Real — El Diagnóstico de Computadora.

Monitorea CPU, RAM, disco, GPU, red y procesos.
Proporciona snapshots bajo demanda y alertas cuando se exceden umbrales.
"""

from __future__ import annotations

import os
import subprocess
import time
from collections import deque
from threading import Thread, Event

import psutil
from loguru import logger

# WI-285: Integración de LogicaTransparente para auditoría matemática de alertas del sistema
try:
    from computadora.cerebro.matematicas import registrar_alerta_sistema
    _MATEMATICAS_DISPONIBLE = True
except ImportError:
    _MATEMATICAS_DISPONIBLE = False

# PID del proceso actual de Computadora
_GOLEM_PID = os.getpid()
# Nombres de procesos propios (Computadora + Ollama)
_PROCESOS_PROPIOS = frozenset({'python.exe', 'python3.exe', 'pythonw.exe', 'llm_server.exe', 'ollama.exe'})

# Procesos conocidos de alto consumo (no alertar como anómalos)
_PROCESOS_CONOCIDOS = frozenset({
    # Navegadores
    'chrome', 'firefox', 'msedge', 'opera', 'brave',
    # IDEs / VS Code (Electron multi-proceso)
    'code', 'code - insiders', 'codehelper', 'extensionhost',
    'electron', 'vscodium', 'devenv',
    # Gaming
    'steam', 'epicgames', 'riotclient',
    # Windows core
    'explorer', 'dwm', 'csrss', 'svchost', 'system', 'ntoskrnl',
    'lsass', 'services', 'smss', 'wininit', 'winlogon',
    'taskhostw', 'runtimebroker', 'applicationframehost',
    'shellexperiencehost', 'startmenuexperiencehost',
    'systemsettings', 'sihost', 'ctfmon', 'conhost', 'dllhost',
    'fontdrvhost', 'dashost', 'unsecapp',
    # Memoria / Compresión
    'memcompression', 'memory compression', 'vmmem',
    'registry', 'idle',
    # Computadora ecosystem (safety net)
    'lollama', 'ollama', 'lm_server',
    # WMI / Management
    'wmiprvse', 'wmiapsrv', 'msdtc', 'vdsldr', 'perfmon',
    'taskmgr', 'mmc', 'eventvwr',
    # Windows services
    'searchhost', 'searchindexer', 'searchprotocolhost',
    'widgets', 'windowsterminal', 'powershell', 'pwsh', 'cmd',
    'spoolsv', 'audiodg', 'audioses',
    # Seguridad / Defender
    'antimalware', 'msmpeng', 'mssense', 'securityhealthservice',
    'securityhealthsystray', 'sgrmbroker', 'smartscreen',
    # Actualizaciones
    'wuauclt', 'windowsupdate', 'musnotification', 'usoclient',
    'trustedinstaller', 'tiworker',
    # Networking
    'iphlpsvc', 'networkservice', 'localservice', 'lsaiso',
    # GPU / Display
    'nvcontainer', 'nvdisplay.container', 'nvidia share',
    'amdrsserv', 'amddvr', 'igfxem', 'igfxtray',
    # Apps comunes
    'discord', 'spotify', 'vlc', 'obs',
    'onedrive', 'teams', 'outlook', 'excel', 'word',
    # Android Studio / IntelliJ
    'studio64', 'idea64', 'java', 'kotlin', 'gradle',
    'adb', 'emulator', 'qemu-system',
    # OEM services (Dell/Alienware, HP, Lenovo)
    'awcc', 'awcc.background.server', 'awccservice',
    'alienwarealienFXservice', 'dell supportassist',
    'supportassistservice', 'dellsupportassistservice',
    'hpcommrecovery', 'lenovovantage',
    # Ollama + instaladores Windows (GEVURAH FIX - no son sospechosos)
    'ollama', 'llm_server',  # variantes Ollama
    'msiexec', 'installer', 'setup', 'winrar', '7z', 'bandizip',  # instaladores
    'mmc', 'devmgmt', 'services', 'compmgmt',  # herramientas admin
    'dotnet', 'dotnethost', 'mscoree', 'clr', 'coreclr',  # .NET runtime
    'git', 'gitdash', 'tortoisegit', 'gitextensions',  # vcs
    'rustup', 'cargo', 'rust',  # rust toolchain
    'node', 'npm', 'yarn', 'nodejs',  # nodejs
    'python', 'pythonw',  # python (ya está pero asegurar)
})


# ═══════════════════════════════════════════════
# MONITOR DE SISTEMA
# ═══════════════════════════════════════════════

class MonitorSistema:
    """Monitoreo continuo de recursos del sistema."""

    def __init__(self):
        self._umbrales = {
            'cpu_pct': 90,
            'ram_pct': 85,
            'disco_pct': 10,  # % libre mínimo
        }
        self._historial_cpu: deque[float] = deque(maxlen=60)
        self._ultimo_snapshot: dict = {}
        self._detener = Event()
        self._baseline = None  # Se inyecta después con set_baseline()

        # Cache de campos costosos (iteración de TODOS los procesos + subprocess
        # nvidia-smi). Se recalcula en el hilo de background (_loop_muestreo),
        # NUNCA de forma síncrona desde snapshot() — snapshot() se llama cada
        # segundo desde el hilo de UI (ventana_principal.py) y antes bloqueaba
        # el render ~1s con 4 barridos completos de psutil.process_iter() +
        # un subprocess.run() nuevo. Ver hallazgo 2026-10-02.
        self._cache_pesado: dict = {}
        self._cache_pesado_ts: float = 0.0
        # Hallazgo 2026-10-03: 5s en vez de 3s — además de que ahora es 1 sola
        # llamada a nvidia-smi (ver _obtener_gpu), espaciar más los refrescos
        # reduce aún más la probabilidad de que coincidan con el sondeo de
        # 1000ms del Administrador de Tareas (pestaña Rendimiento/GPU) y
        # generen contención en el driver NVIDIA/NVML.
        self._cache_pesado_intervalo = 5.0  # segundos entre refrescos costosos

        # RF-42: Feature flag para pausar monitor de sistema
        self._monitor_pausado = False
        try:
            from computadora.nucleo.feature_flags import obtener_flag
            if not obtener_flag("monitor_sistema"):
                logger.info("RF-42 Monitor de Sistema PAUSADO por feature flag")
                self._monitor_pausado = True
        except Exception as e:
            logger.debug(f"Feature flag check error (no crítico): {e}")

        # Hilo de muestreo de CPU (1 lectura/s)
        self._hilo = Thread(target=self._loop_muestreo, daemon=True, name="MonitorSistema")
        self._hilo.start()
        if not self._monitor_pausado:
            logger.info("MonitorSistema iniciado — COMPUTADORA vigila la salud del sistema")

    def set_baseline(self, baseline) -> None:
        """Inyecta el BaselineSistema para umbrales dinámicos."""
        self._baseline = baseline

    def detener(self):
        self._detener.set()

    # ─── API pública ────────────────────────────

    def snapshot(self) -> dict:
        """Estado actual completo del sistema.

        Los campos baratos (CPU/RAM/disco/red totales) se leen frescos vía
        psutil — son O(1), no iteran procesos. Los campos costosos (RAM
        propia, top procesos, GPU) vienen del cache que refresca el hilo de
        background cada ~3s (ver _actualizar_cache_pesado); este método NUNCA
        itera procesos ni lanza subprocess directamente, para poder llamarse
        cada segundo desde el hilo de UI sin bloquear el render.
        """
        try:
            mem = psutil.virtual_memory()
            disco = psutil.disk_usage('C:\\')
            net = psutil.net_io_counters()
            pesado = self._cache_pesado

            snap = {
                'cpu_pct': self.cpu_promedio(5) if self._historial_cpu else psutil.cpu_percent(interval=0),  # WI-258: non-blocking
                'ram_usada_gb': round(mem.used / (1024**3), 1),
                'ram_total_gb': round(mem.total / (1024**3), 1),
                'ram_pct': mem.percent,
                'ram_propia_mb': pesado.get('ram_propia_mb', 0.0),
                'ram_ajena_pct': pesado.get('ram_ajena_pct', mem.percent),
                'disco_libre_gb': round(disco.free / (1024**3), 1),
                'disco_total_gb': round(disco.total / (1024**3), 1),
                'disco_pct_libre': round(100 - disco.percent, 1),
                'red_enviado_mb': round(net.bytes_sent / (1024**2), 1),
                'red_recibido_mb': round(net.bytes_recv / (1024**2), 1),
                'gpu_vram': pesado.get('gpu_vram', {}),
                'top_cpu': pesado.get('top_cpu', []),
                'top_ram': pesado.get('top_ram', []),
            }
            self._ultimo_snapshot = snap
            return snap
        except Exception as e:
            logger.error(f"Error en snapshot: {e}")
            return self._ultimo_snapshot or {}

    def _actualizar_cache_pesado(self) -> None:
        """Recalcula los campos costosos UNA sola vez y los cachea.

        Llamado solo desde _loop_muestreo (hilo de background), nunca desde
        snapshot(). Antes, snapshot() llamaba ram_propia_mb() y luego
        ram_sin_propios() (que internamente volvía a llamar ram_propia_mb()):
        dos barridos completos de psutil.process_iter() para el mismo dato.
        Aquí se calcula una sola vez y se deriva ram_ajena_pct del mismo valor.
        """
        try:
            propia_mb = self.ram_propia_mb()
            mem = psutil.virtual_memory()
            propia_bytes = propia_mb * (1024 ** 2)
            uso_ajeno = max(0.0, mem.used - propia_bytes)
            ram_ajena_pct = round((uso_ajeno / mem.total) * 100, 1) if mem.total else mem.percent
            self._cache_pesado = {
                'ram_propia_mb': propia_mb,
                'ram_ajena_pct': ram_ajena_pct,
                'top_cpu': self.top_procesos(5, 'cpu'),
                'top_ram': self.top_procesos(3, 'memory'),
                'gpu_vram': self._obtener_gpu(),
            }
            self._cache_pesado_ts = time.monotonic()
        except Exception as e:  # RF-167
            logger.debug(f"Error actualizando cache pesado: {e}")

    def cpu_promedio(self, segundos: int = 30) -> float:
        """CPU promedio en los últimos N segundos."""
        if not self._historial_cpu:
            return 0.0
        muestra = list(self._historial_cpu)[-segundos:]
        return round(sum(muestra) / len(muestra), 1) if muestra else 0.0

    def _es_proceso_propio(self, proc: psutil.Process) -> bool:
        """Identifica si un proceso pertenece a Computadora o a Ollama."""
        try:
            nombre = proc.name().lower()
            if nombre in _PROCESOS_PROPIOS:
                return True
            # Cualquier variante de Ollama runner
            if 'lm_' in nombre or 'llm_' in nombre:
                return True
            # Hijos del proceso Computadora actual
            if proc.ppid() == _GOLEM_PID:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False

    def ram_propia_mb(self) -> float:
        """RAM total consumida por procesos propios (Computadora + Ollama) en MB."""
        total_bytes = 0
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                if self._es_proceso_propio(proc):
                    mem_info = proc.info.get('memory_info')
                    if mem_info:
                        total_bytes += mem_info.rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return round(total_bytes / (1024 ** 2), 1)

    def ram_sin_propios(self) -> float:
        """RAM% del sistema excluyendo el consumo de Computadora+Ollama."""
        try:
            mem = psutil.virtual_memory()
            propia_bytes = self.ram_propia_mb() * (1024 ** 2)
            uso_ajeno = mem.used - propia_bytes
            if uso_ajeno < 0:
                uso_ajeno = 0
            return round((uso_ajeno / mem.total) * 100, 1)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return psutil.virtual_memory().percent

    def hay_alerta(self) -> str | None:
        """Retorna descripción de alerta si algún umbral se excede, None si todo está bien.
        
        Para RAM, excluye el consumo propio de Computadora+Ollama para evitar
        alertas causadas por el propio pensamiento de la Computadora."""
        alertas = []

        # CPU sostenida
        cpu_30s = self.cpu_promedio(30)
        cpu_anomalo = cpu_30s > self._umbrales['cpu_pct']
        if self._baseline and self._baseline.tiene_datos_suficientes():
            cpu_anomalo = self._baseline.es_anomalo('cpu_pct', cpu_30s)
        if cpu_anomalo:
            # WI-285: Registrar cálculo de CPU en LogicaTransparente
            if _MATEMATICAS_DISPONIBLE:
                try:
                    registrar_alerta_sistema(
                        tipo_alerta="cpu",
                        valor=cpu_30s,
                        umbral=self._umbrales['cpu_pct'],
                        es_sospechoso=True,
                        contexto="CPU sostenida >30s"
                    )
                except Exception as e:
                    logger.debug(f"Error registrando alerta CPU: {e}")
            alertas.append(f"CPU al {cpu_30s:.0f}% sostenido por 30 segundos")

        # RAM (excluyendo procesos propios)
        try:
            ram_ajena_pct = self.ram_sin_propios()
            ram_anomalo = ram_ajena_pct > self._umbrales['ram_pct']
            if self._baseline and self._baseline.tiene_datos_suficientes():
                ram_anomalo = self._baseline.es_anomalo('ram_pct', ram_ajena_pct)
            if ram_anomalo and self._ram_es_entorno_normal():
                ram_anomalo = False
            if ram_anomalo:
                # WI-285: Registrar cálculo de RAM en LogicaTransparente
                if _MATEMATICAS_DISPONIBLE:
                    try:
                        registrar_alerta_sistema(
                            tipo_alerta="ram",
                            valor=ram_ajena_pct,
                            umbral=self._umbrales['ram_pct'],
                            es_sospechoso=True,
                            contexto="RAM ajena alta (excluyendo procesos propios)"
                        )
                    except Exception as e:
                        logger.debug(f"Error registrando alerta RAM: {e}")
                alertas.append(f"RAM al {ram_ajena_pct:.0f}% (excluyendo mi propio consumo)")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Disco
        try:
            disco = psutil.disk_usage('C:\\')
            disco_libre_pct = round(100 - disco.percent, 1)
            if disco_libre_pct < self._umbrales['disco_pct']:
                # WI-285: Registrar cálculo de disco en LogicaTransparente
                if _MATEMATICAS_DISPONIBLE:
                    try:
                        registrar_alerta_sistema(
                            tipo_alerta="disco",
                            valor=disco_libre_pct,
                            umbral=self._umbrales['disco_pct'],
                            es_sospechoso=True,
                            contexto="Espacio disco bajo en C:\\"
                        )
                    except Exception as e:
                        logger.debug(f"Error registrando alerta disco: {e}")
                alertas.append(f"Disco C: solo {disco_libre_pct:.0f}% libre")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        if alertas:
            return ". ".join(alertas)

        # Si no hay alertas por umbrales, verificar procesos anómalos
        diag = self.diagnosticar_proceso_anomalo()
        if diag:
            # WI-285: Registrar proceso anómalo en LogicaTransparente
            if _MATEMATICAS_DISPONIBLE:
                try:
                    registrar_alerta_sistema(
                        tipo_alerta="proceso_anomalo",
                        valor=diag,
                        umbral="N/A",
                        es_sospechoso=True,
                        contexto="Proceso desconocido con consumo alto"
                    )
                except Exception as e:
                    logger.debug(f"Error registrando alerta proceso: {e}")
            return f"Proceso sospechoso: {diag}"

        return None

    def _ram_es_entorno_normal(self) -> bool:
        """Detecta si el consumo alto de RAM proviene del entorno habitual de trabajo.

        Revisa los 5 procesos que más RAM consumen (excl. propios).
        Si TODOS son procesos conocidos → es el entorno normal del propietario,
        no hay que alertar.
        """
        try:
            procs: list[tuple[str, float]] = []
            for p in psutil.process_iter(['name', 'memory_percent']):
                try:
                    info = p.info
                    nombre = info.get('name', '')
                    if not nombre:
                        continue
                    if self._es_proceso_propio(p):
                        continue
                    mem_pct = info.get('memory_percent', 0) or 0
                    if mem_pct > 0.1:
                        procs.append((nombre, mem_pct))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            procs.sort(key=lambda x: x[1], reverse=True)
            top5 = procs[:5]
            if not top5:
                return False

            for nombre, _ in top5:
                nombre_lower = nombre.lower().replace('.exe', '')
                nombre_compacto = nombre_lower.replace(' ', '')
                es_conocido = any(
                    k in nombre_lower or k.replace(' ', '') in nombre_compacto
                    for k in _PROCESOS_CONOCIDOS
                )
                if not es_conocido:
                    return False
            return True
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return False

    def reporte_completo(self) -> str:
        """Reporte legible para respuesta por voz."""
        snap = self.snapshot()
        if not snap:
            return "No pude obtener información del sistema"

        partes = [
            f"CPU al {snap['cpu_pct']:.0f}%",
            f"RAM: {snap['ram_usada_gb']:.1f} de {snap['ram_total_gb']:.1f} gigas ({snap['ram_pct']:.0f}%)",
            f"Disco C: {snap['disco_libre_gb']:.1f} gigas libres de {snap['disco_total_gb']:.1f}",
        ]

        gpu = snap.get('gpu_vram')
        if gpu:
            partes.append(f"GPU: {gpu}")

        # Top procesos
        top = snap.get('top_cpu', [])
        if top:
            nombres_top = ", ".join(p[0] for p in top[:3])
            partes.append(f"Los procesos más pesados son: {nombres_top}")

        # Estado general
        alerta = self.hay_alerta()
        if alerta:
            partes.append(f"Alerta: {alerta}")
        else:
            partes.append("Todo está en orden")

        return ". ".join(partes)

    def diagnosticar_proceso_anomalo(self) -> str | None:
        """Identifica procesos con consumo anómalo de recursos.
        
        Compara top 5 RAM contra tabla de procesos conocidos.
        Proceso desconocido >2GB RAM o >50% CPU por >60s → alerta específica.
        Retorna descripción o None si todo es normal."""
        try:
            anomalias = []
            for proc in psutil.process_iter(['name', 'memory_info', 'cpu_percent', 'create_time']):
                try:
                    info = proc.info
                    nombre = info.get('name', '')
                    if not nombre:
                        continue
                    # Ignorar procesos propios
                    if self._es_proceso_propio(proc):
                        continue

                    mem_info = info.get('memory_info')
                    rss_gb = (mem_info.rss / (1024**3)) if mem_info else 0
                    cpu_pct = info.get('cpu_percent', 0) or 0

                    nombre_lower = nombre.lower()
                    # Variante sin espacios para matching robusto
                    nombre_compacto = nombre_lower.replace(' ', '').replace('.exe', '')

                    # ¿Es proceso conocido? (substring match + match sin espacios)
                    es_conocido = any(
                        k in nombre_lower or k.replace(' ', '') in nombre_compacto
                        for k in _PROCESOS_CONOCIDOS
                    )

                    # WI-257: Normalizar CPU% por número de cores
                    # psutil devuelve CPU per-core (ej: 338% = 3.4 cores)
                    n_cores = os.cpu_count() or 1
                    cpu_norm = cpu_pct / n_cores * 100 if n_cores > 1 else cpu_pct

                    # Proceso desconocido con alto consumo
                    if not es_conocido:
                        if rss_gb > 2.0:
                            anomalias.append(
                                f"{nombre} consume {rss_gb:.1f}GB de RAM (desconocido)"
                            )
                        elif cpu_pct > 50:
                            anomalias.append(
                                f"{nombre} usa {cpu_norm:.0f}% de CPU (desconocido)"
                            )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if anomalias:
                return ". ".join(anomalias[:3])  # Máximo 3 anomalías
        except Exception as e:
            logger.debug(f"Error en diagnóstico procesos: {e}")
        return None

    def top_procesos(self, n: int = 5, por: str = 'cpu') -> list[tuple[str, float]]:
        """Top N procesos por CPU o memoria."""
        try:
            attr = 'cpu_percent' if por == 'cpu' else 'memory_percent'
            procs = []
            for p in psutil.process_iter(['name', attr]):
                try:
                    info = p.info
                    val = info.get(attr, 0) or 0
                    if val > 0.1:
                        procs.append((info['name'], round(val, 1)))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            procs.sort(key=lambda x: x[1], reverse=True)
            return procs[:n]
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return []

    # ─── Internos ───────────────────────────────

    def _loop_muestreo(self):
        """Muestrea CPU adaptativamente: 2s normal, 5s en idle."""
        # Si monitoreo pausado, esperar sin hacer nada
        if self._monitor_pausado:
            while not self._detener.is_set():
                time.sleep(10)
            return
        
        while not self._detener.is_set():
            try:
                cpu = psutil.cpu_percent(interval=0)
                self._historial_cpu.append(cpu)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            # Refrescar cache costoso (procesos + GPU) cada _cache_pesado_intervalo,
            # en este hilo de background — nunca en el hilo de UI.
            ahora = time.monotonic()
            if ahora - self._cache_pesado_ts >= self._cache_pesado_intervalo:
                self._actualizar_cache_pesado()
            # Adaptativo: si CPU promedio < 20% → muestrear menos frecuente
            promedio = sum(self._historial_cpu) / len(self._historial_cpu) if self._historial_cpu else 50
            intervalo = 5.0 if promedio < 20 else 2.0
            self._detener.wait(intervalo)

    def _obtener_gpu(self) -> dict:
        """Intenta obtener info de GPU via nvidia-smi.

        Hallazgo 2026-10-03 (reporte de usuario: stutter ~1s con Task Manager
        abierto): esta función antes lanzaba DOS subprocess.run() de
        nvidia-smi secuenciales (uno para VRAM/uso, otro para encoder/decoder
        vía _obtener_motor_gpu_dominante). Cada nvidia-smi.exe debe inicializar
        NVML y hablar con el driver NVIDIA — si otro proceso (p.ej. el
        Administrador de Tareas con la pestaña Rendimiento/GPU abierta, que
        sondea el mismo driver cada 1000ms) está consultándolo al mismo
        tiempo, nvidia-smi puede volverse notablemente más lento por
        contención interna del driver/NVML. Duplicar las llamadas duplicaba
        esa ventana de contención cada _cache_pesado_intervalo (~3s), desde
        el hilo de background. Ahora se pide TODO en una sola llamada con
        --query-gpu, reduciendo a la mitad el número de procesos nvidia-smi
        lanzados por ciclo.
        """
        try:
            result = subprocess.run(
                ['nvidia-smi',
                 '--query-gpu=memory.used,memory.total,utilization.gpu,'
                 'utilization.encoder,utilization.decoder',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = [p.strip() for p in result.stdout.strip().split(',')]
                if len(parts) >= 3:
                    usado = float(parts[0])
                    total = float(parts[1])
                    uso = float(parts[2])
                    used_pct = (usado / total) * 100 if total > 0 else 0

                    # WI-MOTOR-GPU: clasificación opcional de motor dominante
                    # (3D/compute vs NVENC/NVDEC). No todos los drivers/GPUs
                    # exponen utilization.encoder/decoder — si faltan o no
                    # parsean, se deja "desconocido" sin tumbar la lectura de
                    # VRAM/uso (que siempre funciona con los 3 primeros campos).
                    motor = "desconocido"
                    if len(parts) >= 5:
                        try:
                            encoder_pct = float(parts[3])
                            decoder_pct = float(parts[4])
                            media_pct = max(encoder_pct, decoder_pct)
                            # NVENC/NVDEC son bloques de hardware separados del
                            # motor de shaders/compute: si su actividad iguala
                            # o supera la utilización "general" reportada, la
                            # carga dominante es de video, no de render/compute.
                            if media_pct > 5.0 and media_pct >= uso:
                                motor = "media"
                            elif uso > 5.0:
                                motor = "compute"
                            else:
                                motor = "inactivo"
                        except ValueError:
                            pass

                    return {'used_pct': used_pct, 'usage_pct': uso, 'motor_dominante': motor}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return {}


# ═══════════════════════════════════════════════
# FUNCIONES HERRAMIENTA (para registro en herramientas.py)
# ═══════════════════════════════════════════════

_monitor_global: MonitorSistema | None = None
_monitor_global_lock = __import__('threading').Lock()


def obtener_monitor() -> MonitorSistema:
    """Obtiene o crea la instancia global del monitor (thread-safe FP-036)."""
    global _monitor_global
    if _monitor_global is None:
        with _monitor_global_lock:
            if _monitor_global is None:
                _monitor_global = MonitorSistema()
    return _monitor_global


def monitoreo_sistema() -> str:
    """Herramienta: reporte completo del sistema."""
    return obtener_monitor().reporte_completo()


def estado_rapido_sistema() -> str:
    """Herramienta: snapshot rápido en una línea."""
    m = obtener_monitor()
    snap = m.snapshot()
    if not snap:
        return "Sin datos"
    return f"CPU {snap['cpu_pct']:.0f}% | RAM {snap['ram_pct']:.0f}% | Disco {snap['disco_pct_libre']:.0f}% libre"


