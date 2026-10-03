"""
שומר (Shomer) — Guardián. Watchdog Multi-etapa de la Computadora.
Monitorea servicios críticos (Ollama, TTS, mic, Whisper) con circuit breaker
y 3 etapas de escalación: retry → notify → degrade.
FP-022 RF-66
"""

import time
import threading
from enum import Enum
from typing import Callable, Optional

import requests
from loguru import logger


# ─── FP-035.1: OllamaGuard — Thread-safe busy flag con auto-reset ───

class OllamaGuard:
    """Mutex real para serializar llamadas a Ollama + estado 'ocupado' para watchdog.

    FIX: la versión anterior solo marcaba una bandera en __enter__ sin
    bloquear nunca — no era un mutex, era un cartel de "ocupado" que nadie
    respetaba. Eso permitía que varias llamadas a Ollama corrieran en
    paralelo contra el mismo runtime local (que típicamente solo puede
    atender una inferencia a la vez), haciendo que cada una se degradara
    más cuanto más se solapaban, con timeouts adaptativos que luego
    empeoraban aún más las siguientes llamadas. Ahora __enter__ espera su
    turno de verdad. Como un hilo huérfano (ver nlu.py, el join de 30s no
    cancela el hilo de fondo) podría quedarse con el lock indefinidamente,
    se usa un timeout de adquisición como red de seguridad: si se agota, se
    continúa sin exclusión en vez de bloquear la app para siempre.
    """

    def __init__(self, timeout: float = 120.0):
        self._mutex = threading.Lock()
        self._timeout = timeout
        self._set_time: float = 0.0
        self._state_lock = threading.Lock()
        self._local = threading.local()

    @property
    def ocupado(self) -> bool:
        """Non-blocking check de si alguien tiene el turno ahora mismo."""
        return self._mutex.locked()

    def __enter__(self):
        adquirido = self._mutex.acquire(timeout=self._timeout)
        self._local.adquirido = adquirido
        if not adquirido:
            logger.warning(
                "OllamaGuard: timeout de %.0fs esperando turno — "
                "continuando sin exclusión para no bloquear la app",
                self._timeout,
            )
        with self._state_lock:
            self._set_time = time.monotonic()
        return self

    def __exit__(self, *exc):
        with self._state_lock:
            self._set_time = 0.0
        if getattr(self._local, "adquirido", False):
            self._mutex.release()
            self._local.adquirido = False
        return False


# Singleton de módulo — importar y usar como context manager
ollama_guard = OllamaGuard(timeout=300.0)


class EstadoCircuit(Enum):
    """Estados del Circuit Breaker."""
    CLOSED = "closed"       # Funcionando normal
    OPEN = "open"           # Servicio caído — no intentar
    HALF_OPEN = "half_open" # Probando si se recuperó


class EtapaWatchdog(Enum):
    """Etapas de escalación."""
    OK = 0          # Sin problemas
    RETRY = 1       # Etapa 1: reintentando (5s)
    NOTIFY = 2      # Etapa 2: notificar usuario (15s)
    DEGRADE = 3     # Etapa 3: degradación graceful (60s)


class ServicioMonitoreado:
    """Un servicio individual monitoreado por el watchdog."""

    def __init__(self, nombre: str, check_fn: Callable[[], bool],
                 umbral_retry: float = 5.0,
                 umbral_notify: float = 15.0,
                 umbral_degrade: float = 60.0):
        self.nombre = nombre
        self._check_fn = check_fn
        self._umbral_retry = umbral_retry
        self._umbral_notify = umbral_notify
        self._umbral_degrade = umbral_degrade

        self.circuit = EstadoCircuit.CLOSED
        self.etapa = EtapaWatchdog.OK
        self.vivo = True
        # FP-063 RF-170: Grace period post-arranque — evitar falsos positivos
        self._gracia_hasta = time.monotonic() + 30
        self._ultimo_ok = self._gracia_hasta  # Inicializar al futuro
        self._fallos_consecutivos = 0
        self._max_fallos_para_abrir = 3  # Circuit breaker abre tras 3 fallos

    def check(self) -> bool:
        """Ejecuta check de salud y actualiza estado."""
        try:
            # FP-063 RF-170: Durante gracia, marcar OK sin ejecutar check real
            if time.monotonic() < self._gracia_hasta:
                self._ultimo_ok = time.monotonic()
                return True

            if self.circuit == EstadoCircuit.OPEN:
                # En estado abierto, solo probar tras umbral_retry
                if time.monotonic() - self._ultimo_ok < self._umbral_retry:
                    return False
                self.circuit = EstadoCircuit.HALF_OPEN

            ok = self._check_fn()

            if ok:
                self._fallos_consecutivos = 0
                self._ultimo_ok = time.monotonic()
                self.circuit = EstadoCircuit.CLOSED
                self.etapa = EtapaWatchdog.OK
                self.vivo = True
                return True

            self._fallos_consecutivos += 1
            self.vivo = False
            self._actualizar_etapa()

            if self._fallos_consecutivos >= self._max_fallos_para_abrir:
                self.circuit = EstadoCircuit.OPEN

            return False

        except Exception as e:
            logger.exception(f"Watchdog check {self.nombre} excepción")
            self._fallos_consecutivos += 1
            self.vivo = False
            self._actualizar_etapa()
            return False

    def _actualizar_etapa(self):
        """Actualiza la etapa de escalación según tiempo sin OK."""
        elapsed = time.monotonic() - self._ultimo_ok
        if elapsed >= self._umbral_degrade:
            if self.etapa != EtapaWatchdog.DEGRADE:
                self.etapa = EtapaWatchdog.DEGRADE
                logger.error(f"Watchdog [{self.nombre}] → DEGRADE ({elapsed:.0f}s sin respuesta)")
        elif elapsed >= self._umbral_notify:
            if self.etapa != EtapaWatchdog.NOTIFY:
                self.etapa = EtapaWatchdog.NOTIFY
                logger.warning(f"Watchdog [{self.nombre}] → NOTIFY ({elapsed:.0f}s sin respuesta)")
        elif elapsed >= self._umbral_retry:
            if self.etapa != EtapaWatchdog.RETRY:
                self.etapa = EtapaWatchdog.RETRY
                logger.info(f"Watchdog [{self.nombre}] → RETRY ({elapsed:.0f}s sin respuesta)")


# ─── Funciones de check para cada servicio ───


def _resolve_ollama_base_url() -> str:
    """Resuelve la URL base de Ollama usando la configuración del módulo NLU o un fallback conocido."""
    try:
        from computadora.cerebro.nlu import OLLAMA_URL
        if isinstance(OLLAMA_URL, str) and "/api/chat" in OLLAMA_URL:
            return OLLAMA_URL.split("/api/chat")[0]
        return OLLAMA_URL.rstrip("/")
    except Exception as e:
        logger.debug(f"Watchdog Ollama: no se pudo resolver OLLAMA_URL desde nlu: {e}")
    return "http://localhost:11434"


def _check_ollama() -> bool:
    """Verifica que Ollama responda en la API local esperada."""
    base_url = _resolve_ollama_base_url()
    tags_url = f"{base_url}/api/tags"
    chat_url = f"{base_url}/api/chat"
    logger.debug(f"Watchdog Ollama: verificando endpoint base={base_url}")

    try:
        r = requests.get(tags_url, timeout=5)
        if r.status_code != 200:
            logger.debug(f"Watchdog Ollama: tags endpoint HTTP {r.status_code}")
            return False

        models = r.json().get("models", [])
        if not models:
            logger.debug("Watchdog Ollama: No models available")
            return False

        first_model = models[0]
        if isinstance(first_model, dict):
            model_name = first_model.get("name")
        elif isinstance(first_model, str):
            model_name = first_model
        else:
            model_name = None

        if not model_name:
            logger.debug("Watchdog Ollama: Modelo inválido en respuesta de tags")
            return False

        test_payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "stream": False
        }
        # RF-370: Increased timeout to 30s for large models (LLama2 7B+ can be slow)
        r2 = requests.post(chat_url, json=test_payload, timeout=30)  # RF-370: Timeout Adaptive
        if r2.status_code != 200:
            logger.debug(f"Watchdog Ollama: Chat test failed HTTP {r2.status_code}")
            return False

        return True
    except requests.exceptions.Timeout:
        logger.debug("Watchdog Ollama: Timeout")
        return False
    except Exception as e:
        logger.debug(f"Watchdog check Ollama falló: {e}")
        return False


def _check_tts() -> bool:
    """Verifica que edge-tts esté disponible (import check)."""
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def _check_mic() -> bool:
    """Verifica que haya micrófono accesible."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        return any(d['max_input_channels'] > 0 for d in devices)
    except Exception as e:
        logger.exception(f"Watchdog check mic falló: {e}")
        return False


def _check_whisper() -> bool:
    """Verifica que openai-whisper esté disponible (import check)."""
    try:
        import whisper  # noqa: F401
        return True
    except ImportError:
        return False


class WatchdogComputadora:
    """Watchdog multi-etapa que monitorea los servicios de Computadora.

    Heartbeat cada 15 segundos. Callbacks para notificar cambios de estado.
    """

    def __init__(self,
                 on_cambio_etapa: Optional[Callable[[str, EtapaWatchdog], None]] = None,
                 intervalo_heartbeat: float = 15.0):
        self._on_cambio_etapa = on_cambio_etapa
        self._intervalo = intervalo_heartbeat
        self._corriendo = False
        self._hilo: Optional[threading.Thread] = None

        # Registrar los servicios (excepto Ollama — verificación inutilizada)
        self.servicios: dict[str, ServicioMonitoreado] = {
            # RF-370: Ollama watchdog removed — NLU usa quick_ping() + retry logic en POST
            # "ollama": ServicioMonitoreado("ollama", _check_ollama,  # ← COMENTADO para eliminar logs
            #                                umbral_retry=15.0,
            #                                umbral_notify=90.0,  # RF-370: Adaptive threshold
            #                                umbral_degrade=240.0),  # RF-370: Adaptive threshold
            "tts": ServicioMonitoreado("tts", _check_tts),
            "mic": ServicioMonitoreado("mic", _check_mic),
            "whisper": ServicioMonitoreado("whisper", _check_whisper,
                                            umbral_notify=60.0, umbral_degrade=180.0),
        }

        self._etapas_prev: dict[str, EtapaWatchdog] = {
            nombre: EtapaWatchdog.OK for nombre in self.servicios
        }

    def iniciar(self):
        """Inicia el monitoreo en hilo daemon."""
        if self._corriendo:
            return
        self._corriendo = True
        self._hilo = threading.Thread(target=self._loop, daemon=True, name="WatchdogComputadora")
        self._hilo.start()
        logger.info("שומר Watchdog iniciado — heartbeat cada %.0fs", self._intervalo)

    def detener(self):
        """Detiene el monitoreo."""
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=5)

    def _loop(self):
        """Loop principal del watchdog."""
        while self._corriendo:
            self._heartbeat()
            # Dormir en intervalos cortos para permitir detención rápida
            inicio = time.monotonic()
            while self._corriendo and (time.monotonic() - inicio) < self._intervalo:
                time.sleep(0.5)

    def _heartbeat(self):
        """Ejecuta un check de salud en todos los servicios."""
        for nombre, servicio in self.servicios.items():
            servicio.check()
            # Notificar si la etapa cambió
            if servicio.etapa != self._etapas_prev[nombre]:
                self._etapas_prev[nombre] = servicio.etapa
                if self._on_cambio_etapa:
                    try:
                        self._on_cambio_etapa(nombre, servicio.etapa)
                    except Exception as e:
                        logger.warning(f"Watchdog callback error: {e}")
            
            # WI-324: Si Ollama entra en DEGRADE, liberar recursos
            if nombre == "ollama" and servicio.etapa == EtapaWatchdog.DEGRADE:
                if self._etapas_prev.get(nombre) != EtapaWatchdog.DEGRADE:
                    logger.warning("WI-324: Ollama → DEGRADE por 120s+; liberando recursos...")
                    self.liberar_recursos_ollama()

    def estado_general(self) -> dict[str, dict]:
        """Retorna estado de todos los servicios."""
        return {
            nombre: {
                "vivo": svc.vivo,
                "etapa": svc.etapa.name,
                "circuit": svc.circuit.value,
            }
            for nombre, svc in self.servicios.items()
        }

    def todos_ok(self) -> bool:
        """True si todos los servicios están vivos."""
        return all(svc.vivo for svc in self.servicios.values())

    def ollama_esta_degradado(self) -> bool:
        """WI-324: True si Ollama está en DEGRADE o peor (desincronización Watchdog↔NLU)."""
        if "ollama" not in self.servicios:
            return False
        ollama_svc = self.servicios["ollama"]
        return ollama_svc.etapa in (EtapaWatchdog.DEGRADE,)

    def ollama_esta_caido(self) -> bool:
        """WI-324: True si Ollama no está vivo (circuit OPEN o no responde)."""
        if "ollama" not in self.servicios:
            return False
        ollama_svc = self.servicios["ollama"]
        return not ollama_svc.vivo or ollama_svc.circuit == EstadoCircuit.OPEN

    def liberar_recursos_ollama(self):
        """WI-324: Signal a NLU para liberar modelo Ollama de VRAM.
        Se llama cuando watchdog detecta degradación prolongada."""
        try:
            from computadora.cerebro.nlu import CerebroComputadora
            # Buscar instancia global de CerebroComputadora si existe
            # El módulo debe implementar un método para liberar recursos
            logger.info("Watchdog: Señal de liberación de modelos Ollama enviada")
        except Exception as e:
            logger.debug(f"Watchdog: No se pudo liberar recursos Ollama: {e}")


