"""
שער מינימי (Sha'ar Minimi) — Puerta API para la app companion.
Servidor HTTP en puerto 8089 para comunicación bidireccional con Minimi.

Canales:
  1. Red local (LAN) — HTTP directo, sin auth (Minimi es parte de Computadora)
  2. Firestore — relay cuando no hay LAN (sync bidireccional via Cloud)

La Gevurá (restricción) se relaja para Minimi: es parte esencial de la Computadora,
no un agente externo. Solo se acepta tráfico de red local o Firestore.
"""

import json
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

from loguru import logger
import warnings

from computadora.seguridad.shomer_bayit import es_red_hogar

# mDNS registration (optional)
try:
    from zeroconf import Zeroconf, ServiceInfo
    _HAS_ZEROCONF = True
except ImportError:
    _HAS_ZEROCONF = False

# Firestore (optional)
try:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=FutureWarning,
            module=r"google\.api_core\._python_version_support",
        )
        import firebase_admin
        from firebase_admin import credentials, firestore
    _HAS_FIREBASE = True
except ImportError:
    _HAS_FIREBASE = False

# ─── Estado global compartido ───
_api_lock = threading.Lock()  # Protege globals contra acceso concurrente (HTTP + Firestore)
_orquestador = None
_vida_autonoma = None
_escucha_ref = None
_hilo_habla = None  # Ref al HiloHabla para TTS en comandos remotos
_config = None
_ultimo_comando: str = ""  # Último comando recibido (de cualquier canal)
_inicio_ts = time.time()

# ─── Async command results (WI-160) ───
import secrets as _secrets
_command_results: dict[str, dict] = {}  # job_id → {"estado": "pending"|"ok"|"error", "respuesta": str}
_command_results_lock = threading.Lock()
_COMMAND_TTL = 300  # Resultados expiran tras 5 minutos

# ─── Firestore listener ───
_firestore_listener = None
_firestore_db = None
_firestore_stop = threading.Event()  # Señal de parada para el hilo de Firestore

# ─── Sentinel filter (acciones de UI que no aplican en canales remotos) ───
_SENTINEL_MSGS = {
    "__DEMO_ANIMACIONES__": "Demo ejecutada en la PC, señor.",
    "__DEMO_HERRAMIENTAS__": "Demo Gevurá ejecutada en la PC, señor.",
    "__ALERTAS_OFF__": "Alertas del sistema desactivadas.",
    "__ALERTAS_ON__": "Alertas del sistema activadas.",
    "__MINIMIZAR__": "Computadora minimizada en la PC.",
}

# WI-163: Cola de acciones remotas — sentinels que deben ejecutarse en el orbe
_acciones_remotas: list[str] = []
_acciones_remotas_lock = threading.Lock()


def obtener_acciones_remotas() -> list[str]:
    """Drena y retorna la cola de acciones remotas pendientes."""
    with _acciones_remotas_lock:
        acciones = _acciones_remotas.copy()
        _acciones_remotas.clear()
    return acciones


def _filtrar_sentinel(respuesta: str) -> str:
    """Reemplaza sentinels internos por mensajes legibles para canales remotos.
    WI-163: También encola la acción sentinel para ejecución en el orbe."""
    if respuesta and respuesta in _SENTINEL_MSGS:
        with _acciones_remotas_lock:
            _acciones_remotas.append(respuesta)
        return _SENTINEL_MSGS[respuesta]
    return respuesta if respuesta else respuesta


def _es_red_local(ip: str) -> bool:
    """Verifica que la IP sea de red local (RFC 1918) o localhost."""
    if ip.startswith("127.") or ip == "::1":
        return True
    if ip.startswith("192.168.") or ip.startswith("10."):
        return True
    # 172.16.0.0 - 172.31.255.255
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2:
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    return False


def _obtener_ip_local() -> str:
    """Obtiene la IP local de la máquina en la LAN."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.debug(f"No se pudo determinar IP local: {e}")
        return "127.0.0.1"


def _estado_computadora() -> dict:
    """Construye el JSON de estado actual de la Computadora (enriquecido)."""
    estado = "dormido"
    humor = "neutro"
    escuchando = False

    if _vida_autonoma:
        estado = getattr(_vida_autonoma, "_ultimo_estado_computadora", "dormido")
        # Personalidad → humor
        _pers = getattr(_vida_autonoma, "_personalidad", None)
        if _pers:
            humor = getattr(_pers, "humor_actual", "neutro")

    if _escucha_ref:
        escuchando = getattr(_escucha_ref, "activo", False)

    uptime = int(time.time() - _inicio_ts)

    # Fase circadiana
    fase_circadiana = "desconocida"
    try:
        from computadora.nucleo.proactividad import obtener_fase_actual
        fase_circadiana = obtener_fase_actual() or "desconocida"
    except Exception as e:
        logger.debug("Error obteniendo fase circadiana: %s", e)

    # Cerebro activo (N1/N2/N3) y modelo
    cerebro_info = {"nivel": "N1", "modelo": "regex"}
    if _orquestador:
        cerebro = getattr(_orquestador, "cerebro", None)
        if cerebro:
            cerebro_info["modelo"] = getattr(cerebro, "modelo", "desconocido")
            cerebro_info["ollama_ok"] = getattr(cerebro, "ollama_disponible", False)

    # Métricas de hardware ligeras
    hw = {}
    try:
        import psutil
        hw["cpu_percent"] = psutil.cpu_percent(interval=0)
        hw["ram_percent"] = psutil.virtual_memory().percent
        proc = psutil.Process()
        hw["ram_computadora_mb"] = round(proc.memory_info().rss / (1024 * 1024), 1)
    except Exception as e:
        logger.debug("Error leyendo métricas hw: %s", e)

    from computadora import __version__

    # Enciclopedia status (for Minimi monitoring)
    enciclopedia_info = {"activo": False, "sesiones": 0}
    try:
        _prog_file = Path(__file__).parent.parent.parent / "datos" / "enciclopedia_progreso.json"
        if _prog_file.exists():
            _prog = json.loads(_prog_file.read_text("utf-8"))
            enciclopedia_info["sesiones"] = _prog.get("sessions_count", 0)
            enciclopedia_info["capitulos_leidos"] = len(_prog.get("chapters_visited", []))
            enciclopedia_info["ultimo_acceso"] = _prog.get("last_session", "")
        if _enciclopedia_proceso is not None and _enciclopedia_proceso.poll() is None:
            enciclopedia_info["activo"] = True
    except Exception as e:  # RF-167
        pass

    return {
        "activo": True,
        "estado": estado,
        "humor": humor,
        "escuchando": escuchando,
        "ultimo_comando": _ultimo_comando,
        "uptime_s": uptime,
        "version": __version__,
        "ip_local": _obtener_ip_local(),
        "fase_circadiana": fase_circadiana,
        "cerebro": cerebro_info,
        "hardware": hw,
        "enciclopedia": enciclopedia_info,
    }


class _MinimiHandler(BaseHTTPRequestHandler):
    """Handler HTTP para endpoints de Minimi."""

    def log_message(self, fmt, *args):
        """Redirige logs del servidor HTTP a loguru."""
        logger.debug(f"[API Minimi] {fmt % args}")

    def _verificar_origen(self) -> bool:
        """Verifica que la petición venga de red local + red del hogar."""
        ip_cliente = self.client_address[0]
        if not _es_red_local(ip_cliente):
            logger.warning(f"[API Minimi] Petición rechazada de IP externa: {ip_cliente}")
            self.send_error(403, "Solo red local")
            return False
        # RF-368: Shomer HaBayit — verificar que operamos desde el hogar
        if not es_red_hogar():
            logger.warning(f"[API Minimi] RED FORÁNEA — petición de {ip_cliente} bloqueada por Shomer HaBayit")
            self.send_error(403, "Red no autorizada")
            return False
        return True

    def _enviar_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if not self._verificar_origen():
            return

        if self.path == "/api/status":
            self._enviar_json(_estado_computadora())
        elif self.path == "/api/ping":
            self._enviar_json({"pong": True, "ts": int(time.time())})
        elif self.path.startswith("/api/resultado"):
            self._manejar_resultado()
        elif self.path.startswith("/api/logs"):
            self._manejar_logs()
        # WI-283: אמת Emet — manifiesto de verdad de la Computadora (Mercurio → Minimi)
        elif self.path == "/api/emet":
            self._manejar_emet()
        # WI-289: Percepción — estado de los sentidos de la Computadora
        elif self.path == "/api/percepcion":
            self._manejar_percepcion()
        # WI-289: Memoria — búsqueda episódica
        elif self.path.startswith("/api/memoria"):
            self._manejar_memoria()
        else:
            self.send_error(404, "Endpoint no encontrado")

    def do_POST(self):
        if not self._verificar_origen():
            return

        if self.path == "/api/comando":
            self._manejar_comando()
        elif self.path == "/api/enciclopedia":
            self._manejar_enciclopedia()
        elif self.path == "/api/sellar_enciclopedia":
            self._manejar_sellar_enciclopedia()
        # WI-296: Endpoint de test para Minimi — verificar autenticación
        elif self.path == "/api/test/minimi_auth":
            self._test_minimi_auth()
        else:
            self.send_error(404, "Endpoint no encontrado")

    def _manejar_comando(self):
        """Procesa un comando de Minimi."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0 or content_len > 8192:
            self._enviar_json({"respuesta": "Cuerpo vacío o muy grande", "estado": "error"}, 400)
            return

        raw = self.rfile.read(content_len)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._enviar_json({"respuesta": "JSON inválido", "estado": "error"}, 400)
            return

        comando = data.get("comando", "").strip()
        if not comando:
            self._enviar_json({"respuesta": "Comando vacío", "estado": "error"}, 400)
            return

        # Limitar longitud del comando
        if len(comando) > 1000:
            self._enviar_json({"respuesta": "Comando muy largo (máx 1000 chars)", "estado": "error"}, 400)
            return

        origen = data.get("origen", "minimi")
        logger.info(f"[API Minimi] Comando de {origen}: '{comando}'")

        with _api_lock:
            global _ultimo_comando
            _ultimo_comando = comando[:200]  # Guardar (truncado) para /api/status

        if _orquestador is None:
            self._enviar_json({"respuesta": "Orquestador no disponible", "estado": "error"}, 503)
            return

        # WI-160: Async — retornar job_id inmediato, procesar en hilo
        job_id = _secrets.token_urlsafe(16)
        with _command_results_lock:
            _command_results[job_id] = {"estado": "pending", "respuesta": "", "ts": time.time()}

        def _process():
            try:
                respuesta_cruda = _orquestador.procesar(comando)
                respuesta = _filtrar_sentinel(respuesta_cruda)
                # TTS en desktop: hablar respuestas no-sentinel por los parlantes
                if _hilo_habla and respuesta_cruda == respuesta and respuesta:
                    try:
                        _hilo_habla.hablar(respuesta)
                    except Exception as e:
                        logger.debug(f"[API Minimi] TTS remoto falló: {e}")
                with _command_results_lock:
                    _command_results[job_id] = {
                        "estado": "ok",
                        "respuesta": respuesta or "Sin respuesta",
                        "ts": time.time(),
                    }
            except Exception as e:
                logger.error(f"[API Minimi] Error procesando comando: {e}")
                with _command_results_lock:
                    _command_results[job_id] = {
                        "estado": "error",
                        "respuesta": f"Error interno: {e}",
                        "ts": time.time(),
                    }

        threading.Thread(target=_process, daemon=True).start()

        self._enviar_json({
            "estado": "accepted",
            "job_id": job_id,
        }, 202)

    def _manejar_resultado(self):
        """GET /api/resultado?id=<job_id> — Polling para resultado async de comando."""
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        job_id = (qs.get("id") or [""])[0]
        if not job_id:
            self._enviar_json({"error": "Falta parámetro id"}, 400)
            return

        # Limpiar resultados expirados
        now = time.time()
        with _command_results_lock:
            expired = [k for k, v in _command_results.items() if now - v.get("ts", 0) > _COMMAND_TTL]
            for k in expired:
                del _command_results[k]
            result = _command_results.get(job_id)

        if result is None:
            self._enviar_json({"error": "Job no encontrado o expirado"}, 404)
            return

        self._enviar_json(result)

    def _manejar_logs(self):
        """GET /api/logs?n=<lines> — Retorna las últimas N líneas del log de hoy."""
        from urllib.parse import urlparse, parse_qs
        import datetime
        qs = parse_qs(urlparse(self.path).query)
        n = min(int((qs.get("n") or ["200"])[0]), 1000)
        hoy = datetime.date.today().strftime("%Y-%m-%d")
        log_dir = Path(__file__).parent.parent.parent / "datos" / "logs"
        log_file = log_dir / f"computadora_{hoy}.log"
        if not log_file.exists():
            self._enviar_json({"lines": [], "file": str(log_file.name)})
            return
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
            tail = [l.rstrip("\n") for l in all_lines[-n:]]
            self._enviar_json({"lines": tail, "file": log_file.name, "total": len(all_lines)})
        except Exception as e:
            self._enviar_json({"error": f"Error leyendo logs: {e}"}, 500)

    def _manejar_emet(self):
        """WI-283: GET /api/emet — Manifiesto de verdad de la Computadora (Mercurio → Minimi)."""
        try:
            from computadora.nucleo.emet import generar_manifiesto
            self._enviar_json(generar_manifiesto())
        except ImportError:
            self._enviar_json({"error": "Módulo emet no disponible"}, 500)
        except Exception as e:
            logger.error("[API] Error generando manifiesto Emet: %s", e)
            self._enviar_json({"error": "Error interno"}, 500)

    def _manejar_percepcion(self):
        """WI-289: GET /api/percepcion — Estado de los sentidos de la Computadora."""
        estado = {"sentidos": {}}
        try:
            from computadora.percepcion.rostro import ReconocedorRostro
            rec = ReconocedorRostro()
            estado["sentidos"]["ayin"] = {
                "disponible": rec.disponible,
                "desc": "Visión — face_recognition + OpenCV",
            }
        except ImportError:
            estado["sentidos"]["ayin"] = {"disponible": False, "desc": "Módulo no instalado"}
        try:
            from computadora.voz.escucha import EscuchaContinua
            estado["sentidos"]["ozen"] = {
                "disponible": True,
                "desc": "Escucha — Whisper/Vosk STT",
            }
        except ImportError:
            estado["sentidos"]["ozen"] = {"disponible": False, "desc": "Módulo no instalado"}
        try:
            from computadora.voz.habla import HiloHabla
            estado["sentidos"]["peh"] = {
                "disponible": True,
                "desc": "Habla — Piper TTS",
            }
        except ImportError:
            estado["sentidos"]["peh"] = {"disponible": False, "desc": "Módulo no instalado"}
        self._enviar_json(estado)

    def _manejar_memoria(self):
        """WI-289: GET /api/memoria?q=<consulta>&dias=<N> — Búsqueda episódica."""
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        consulta = (qs.get("q") or [""])[0].strip()
        dias = min(int((qs.get("dias") or ["30"])[0]), 90)
        if not consulta:
            self._enviar_json({"error": "Parámetro 'q' requerido"}, 400)
            return
        try:
            from computadora.memoria.memoria import buscar_en_memoria
            resultado = buscar_en_memoria(consulta, dias=dias)
            self._enviar_json({"consulta": consulta, "dias": dias, "resultado": resultado})
        except ImportError:
            self._enviar_json({"error": "Módulo memoria no disponible"}, 500)
        except Exception as e:
            logger.error("[API] Error buscando en memoria: %s", e)
            self._enviar_json({"error": "Error interno"}, 500)

    def _manejar_enciclopedia(self):
        """Abre el Enciclopedia para acceso remoto desde Minimi (requiere contraseña)."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0 or content_len > 4096:
            self._enviar_json({"error": "Cuerpo vacío o muy grande"}, 400)
            return

        raw = self.rfile.read(content_len)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._enviar_json({"error": "JSON inválido"}, 400)
            return

        password = data.get("password", "")
        if not password or len(password) > 256:
            self._enviar_json({"error": "Contraseña requerida"}, 400)
            return

        # Verificar contraseña contra hash del Enciclopedia (PBKDF2-SHA256)
        if not _verificar_password_enciclopedia(password):
            logger.warning("[API Minimi] Intento de acceso al Enciclopedia con contraseña incorrecta")
            self._enviar_json({"error": "Contraseña incorrecta"}, 403)
            return

        # Iniciar Enciclopedia con acceso LAN
        resultado = _iniciar_enciclopedia_lan()
        if resultado:
            self._enviar_json(resultado)
        else:
            self._enviar_json({"error": "No se pudo iniciar el Enciclopedia"}, 500)

    def _manejar_sellar_enciclopedia(self):
        """Sellado silencioso del Enciclopedia desde Minimi."""
        global _enciclopedia_proceso, _enciclopedia_token
        if _enciclopedia_proceso is not None and _enciclopedia_proceso.poll() is None:
            _enciclopedia_proceso.terminate()
            try:
                _enciclopedia_proceso.wait(timeout=2.0)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada (enciclopedia wait): %s", e)
                _enciclopedia_proceso.kill()
            _enciclopedia_proceso = None
            _enciclopedia_token = None
            logger.info("[API Minimi] Enciclopedia sellado silenciosamente por Minimi")
        self._enviar_json({"estado": "sellado"})

    def _test_minimi_auth(self):
        """WI-296: Endpoint de test para verificar autenticación Minimi.
        POST /api/test/minimi_auth { "password": "emet" }
        Retorna información de debug para diagnosticar problemas de auth."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0 or content_len > 4096:
            self._enviar_json({
                "status": "error",
                "code": "EMPTY_BODY",
                "message": "Envía JSON con field 'password'"
            }, 400)
            return

        raw = self.rfile.read(content_len)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._enviar_json({
                "status": "error",
                "code": "JSON_INVALID",
                "message": "JSON inválido"
            }, 400)
            return

        password = data.get("password", "")
        
        # Debug info
        debug_info = {
            "status": "error",
            "code": "AUTH_FAILED",
            "password_received": password,
            "password_length": len(password),
            "password_bytes": password.encode('utf-8').hex() if password else "empty",
        }

        if not password:
            debug_info["message"] = "Contraseña vacía"
            self._enviar_json(debug_info, 400)
            return

        if len(password) > 256:
            debug_info["message"] = "Contraseña muy larga"
            self._enviar_json(debug_info, 400)
            return

        # Verificar contraseña
        if _verificar_password_enciclopedia(password):
            self._enviar_json({
                "status": "ok",
                "code": "AUTH_SUCCESS",
                "message": "Contraseña correcta",
                "password": password
            }, 200)
        else:
            # Debug: mostrar hash calculado (sin revelar hash esperado por seguridad)
            import hashlib
            _salt = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
            h = hashlib.pbkdf2_hmac("sha256", password.encode(), _salt, 100_000).hex()
            debug_info["hash_received"] = h
            debug_info["message"] = "Contraseña incorrecta"
            self._enviar_json(debug_info, 403)


# ─── Enciclopedia remoto ───

_enciclopedia_proceso = None
_enciclopedia_token: str | None = None
_GRIMORIO_PORT = 8080


def _verificar_password_enciclopedia(password: str) -> bool:
    """Verifica la contraseña contra el hash PBKDF2 del Enciclopedia.
    Acepta 'emet' (transliteración) o 'אמת' (carácter hebreo)."""
    import hashlib
    import hmac as _hmac
    _salt = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
    _hash_emet = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"
    _hash_amet_hebreo = "776a244847427941e0434f527bc6502a12a650d5fdedc0f49e997c0311d3e64c"
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), _salt, 100_000).hex()
    return _hmac.compare_digest(h, _hash_emet) or _hmac.compare_digest(h, _hash_amet_hebreo)


def _iniciar_enciclopedia_lan() -> dict | None:
    """Inicia el servidor del Enciclopedia con --lan --servir si no está corriendo."""
    global _enciclopedia_proceso, _enciclopedia_token
    import subprocess
    import secrets

    # Si ya está corriendo, devolver URL existente
    if _enciclopedia_proceso is not None and _enciclopedia_proceso.poll() is None:
        if _enciclopedia_token is None:
            # Token perdido (crash/reinicio externo) — forzar reinicio
            _enciclopedia_proceso.terminate()
            try:
                _enciclopedia_proceso.wait(timeout=2.0)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada (enciclopedia restart): %s", e)
                _enciclopedia_proceso.kill()
            _enciclopedia_proceso = None
            return _iniciar_enciclopedia_lan()
        ip = _obtener_ip_local()
        return {
            "url": f"http://{ip}:{_GRIMORIO_PORT}/index.html",
            "token": _enciclopedia_token,
            "estado": "ya_activo"
        }

    try:
        raiz = Path(__file__).parent.parent.parent
        enciclopedia_script = raiz / "libro_encantado" / "servidor_enciclopedia.py"
        if not enciclopedia_script.exists():
            logger.error("[API Minimi] servidor_enciclopedia.py no encontrado")
            return None

        # Pre-generar token de sesión para pasarlo a Minimi
        _enciclopedia_token = secrets.token_urlsafe(32)

        # Lanzar como subprocess con --servir --lan --no-browser (sin pedir password)
        import sys, os as _os
        python_exe = sys.executable
        env = _os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        _enciclopedia_proceso = subprocess.Popen(
            [python_exe, str(enciclopedia_script), "--servir", "--lan", "--no-browser",
             f"--token={_enciclopedia_token}"],
            cwd=str(raiz),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )

        # Esperar a que el servidor arranque (polling progresivo)
        import time as _time
        for _ in range(6):
            _time.sleep(0.5)
            if _enciclopedia_proceso.poll() is not None:
                break

        if _enciclopedia_proceso.poll() is not None:
            stderr_out = _enciclopedia_proceso.stderr.read().decode("utf-8", errors="replace")
            logger.error(f"[API Minimi] Enciclopedia terminó prematuramente: {stderr_out[:500]}")
            _enciclopedia_proceso = None
            return None

        ip = _obtener_ip_local()
        logger.info(f"[API Minimi] Enciclopedia iniciado en http://{ip}:{_GRIMORIO_PORT} (PID {_enciclopedia_proceso.pid})")
        return {
            "url": f"http://{ip}:{_GRIMORIO_PORT}/index.html",
            "token": _enciclopedia_token,
            "estado": "ok"
        }
    except Exception as e:
        logger.error(f"[API Minimi] Error iniciando Enciclopedia: {e}")
        return None


# ─── mDNS Registration ───

_zeroconf_instance = None
_service_info = None


def _registrar_mdns(puerto: int):
    """Registra servicio _computadora._tcp en mDNS para auto-discovery."""
    global _zeroconf_instance, _service_info

    if not _HAS_ZEROCONF:
        logger.info("[API Minimi] zeroconf no instalado — mDNS deshabilitado")
        return

    try:
        ip_local = _obtener_ip_local()
        ip_bytes = socket.inet_aton(ip_local)

        _service_info = ServiceInfo(
            "_computadora._tcp.local.",
            "Computadora._computadora._tcp.local.",
            addresses=[ip_bytes],
            port=puerto,
            properties={"version": "0.1.0", "platform": "windows"},
        )
        _zeroconf_instance = Zeroconf()
        _zeroconf_instance.register_service(_service_info)
        logger.info(f"[API Minimi] mDNS registrado: _computadora._tcp en {ip_local}:{puerto}")
    except Exception as e:
        logger.warning(f"[API Minimi] Error registrando mDNS: {e}")


def _desregistrar_mdns():
    """Limpia el registro mDNS al cerrar."""
    global _zeroconf_instance, _service_info
    if _zeroconf_instance and _service_info:
        try:
            _zeroconf_instance.unregister_service(_service_info)
            _zeroconf_instance.close()
        except Exception as e:
            logger.debug(f"[API Minimi] Error desregistrando mDNS: {e}")
        _zeroconf_instance = None
        _service_info = None


# ─── Firestore Relay ───

def _iniciar_firestore_relay(config):
    """Inicia el relay Firestore para sincronización remota con Minimi."""
    global _firestore_db, _firestore_listener

    if not _HAS_FIREBASE:
        logger.info("[API Minimi] firebase-admin no instalado — Firestore deshabilitado")
        return

    # Buscar credenciales de service account
    raiz = Path(__file__).parent.parent.parent
    cred_path = config.obtener("firestore.credenciales", "") if config else ""
    if not cred_path:
        # Buscar archivo por defecto
        for nombre in ("firebase-credentials.json", "datos/firebase-credentials.json"):
            candidato = raiz / nombre
            if candidato.exists():
                cred_path = str(candidato)
                break

    if not cred_path or not Path(cred_path).exists():
        logger.info("[API Minimi] Sin credenciales Firebase — Firestore deshabilitado")
        return

    # Validar que el path de credenciales esté dentro del proyecto (OWASP A01:2021)
    cred_resolved = Path(cred_path).resolve()
    if not str(cred_resolved).startswith(str(raiz.resolve())):
        logger.warning(f"[API Minimi] Credenciales fuera del proyecto rechazadas: {cred_path}")
        return

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        _firestore_db = firestore.client()

        # Escribir estado inicial
        _actualizar_firestore_estado()

        # Escuchar comandos entrantes de Minimi
        doc_ref = _firestore_db.collection("computadora").document("comando_minimi")
        _firestore_listener = doc_ref.on_snapshot(_on_firestore_comando)

        # Actualizar estado periódicamente
        t = threading.Thread(target=_firestore_estado_loop, daemon=True)
        t.start()

        logger.info("[API Minimi] Firestore relay activo")
    except Exception as e:
        logger.warning(f"[API Minimi] Error iniciando Firestore: {e}")


def _actualizar_firestore_estado():
    """Publica el estado de la Computadora en Firestore."""
    if not _firestore_db:
        return
    try:
        estado = _estado_computadora()
        estado["timestamp"] = firestore.SERVER_TIMESTAMP
        _firestore_db.collection("computadora").document("estado").set(estado)
    except Exception as e:
        logger.debug(f"[API Minimi] Error actualizando Firestore: {e}")


def _firestore_estado_loop():
    """Actualiza el estado en Firestore cada 15 segundos."""
    while not _firestore_stop.is_set():
        _firestore_stop.wait(15)
        if not _firestore_stop.is_set():
            _actualizar_firestore_estado()


def _on_firestore_comando(doc_snapshot, changes, read_time):
    """Callback cuando Minimi escribe un comando en Firestore."""
    for doc in doc_snapshot:
        data = doc.to_dict()
        if not data:
            continue
        comando = data.get("comando", "").strip()
        procesado = data.get("procesado", False)
        if not comando or procesado:
            continue

        logger.info(f"[API Minimi/Firestore] Comando remoto: '{comando}'")

        if _orquestador is None:
            respuesta = "Orquestador no disponible"
        else:
            try:
                respuesta = _orquestador.procesar(comando) or "Sin respuesta"
                respuesta = _filtrar_sentinel(respuesta)
            except Exception as e:
                respuesta = f"Error: {e}"
                logger.error(f"[API Minimi/Firestore] Error: {e}")

        # Escribir respuesta de vuelta
        try:
            _firestore_db.collection("computadora").document("comando_minimi").set({
                "comando": comando,
                "respuesta": respuesta,
                "procesado": True,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            logger.debug(f"[API Minimi/Firestore] Error escribiendo respuesta: {e}")


# ─── Punto de entrada principal ───

_servidor_http = None


def registrar_habla(habla_ref):
    """Registra el HiloHabla para TTS en desktop durante comandos remotos de Minimi."""
    global _hilo_habla
    _hilo_habla = habla_ref
    logger.info("[API Minimi] HiloHabla registrado para TTS remoto")


def iniciar_servidor_api(config, orquestador, vida_autonoma=None, escucha=None):
    """
    Inicia el servidor API para Minimi en un thread daemon.

    Args:
        config: Configuracion de Computadora
        orquestador: Instancia del Orquestador (para procesar comandos)
        vida_autonoma: Ref a VidaAutonoma (para estado/humor)
        escucha: Ref al módulo de escucha (para saber si está activo)
    """
    global _orquestador, _vida_autonoma, _escucha_ref, _config, _servidor_http

    with _api_lock:
        _orquestador = orquestador
        _vida_autonoma = vida_autonoma
        _escucha_ref = escucha
        _config = config

    puerto = int(config.obtener("api.puerto_minimi", 8089))

    def _run():
        global _servidor_http
        try:
            # RF-368: Shomer HaBayit — si NO estamos en red hogar, bind solo localhost
            bind_addr = "0.0.0.0" if es_red_hogar() else "127.0.0.1"
            _servidor_http = HTTPServer((bind_addr, puerto), _MinimiHandler)
            ip_local = _obtener_ip_local()
            if bind_addr == "127.0.0.1":
                logger.warning(f"[API Minimi] MODO STEALTH — solo localhost:{puerto} (red foránea)")
            else:
                logger.info(f"[API Minimi] Servidor HTTP en {ip_local}:{puerto}")

            # Registrar en mDNS
            _registrar_mdns(puerto)

            # Iniciar Firestore relay
            _iniciar_firestore_relay(config)

            _servidor_http.serve_forever()
        except OSError as e:
            logger.error(f"[API Minimi] No se pudo iniciar en puerto {puerto}: {e}")
        except Exception as e:
            logger.error(f"[API Minimi] Error fatal: {e}")

    t = threading.Thread(target=_run, name="ServidorAPIMiNimi", daemon=True)
    t.start()
    logger.info(f"[API Minimi] Thread iniciado — puerto {puerto}")
    return t


def detener_servidor_api():
    """Detiene el servidor API limpiamente."""
    global _servidor_http, _firestore_listener, _enciclopedia_proceso

    # WI-239: Escribir activo=False en Firestore ANTES de parar el relay
    if _firestore_db:
        try:
            _firestore_db.collection("computadora").document("estado").set(
                {"activo": False, "timestamp": firestore.SERVER_TIMESTAMP},
                merge=True
            )
            logger.info("[API Minimi] Firestore: activo=False escrito al apagar")
        except Exception as e:
            logger.debug(f"[API Minimi] Error escribiendo activo=False: {e}")

    _firestore_stop.set()  # Señalar al hilo Firestore que pare
    _desregistrar_mdns()
    if _firestore_listener:
        try:
            _firestore_listener.unsubscribe()
        except Exception as e:
            logger.debug(f"[API Minimi] Error cerrando Firestore listener: {e}")
    if _enciclopedia_proceso is not None and _enciclopedia_proceso.poll() is None:
        _enciclopedia_proceso.terminate()
        logger.info("[API Minimi] Enciclopedia remoto detenido")
        _enciclopedia_proceso = None
    if _servidor_http:
        _servidor_http.shutdown()
        logger.info("[API Minimi] Servidor detenido")


