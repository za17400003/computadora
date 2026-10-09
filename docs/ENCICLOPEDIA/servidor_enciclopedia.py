#!/usr/bin/env python3
"""
🔐 Servidor de la Enciclopedia de los 7 Metales
Servidor HTTP local con autenticación por contraseña y cifrado AES.

Los archivos de la enciclopedia se almacenan cifrados en disco (.enc).
Solo este servidor puede descifrarlos en memoria para servirlos al navegador.
Sin el servidor corriendo, los archivos son ilegibles.

Ejecución:  python servidor_enciclopedia.py
            python servidor_enciclopedia.py --cifrar   (cifra los fuentes)
            python servidor_enciclopedia.py --descifrar (restaura fuentes para edición)
"""

import base64
import hashlib
import hmac
import http.server
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from getpass import getpass
from pathlib import Path

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

PORT = 8080
HOST = "127.0.0.1"  # Default: solo local. Usar --lan para 0.0.0.0 (Minimi)

# Contraseña hardcodeada (PBKDF2-SHA256, 100k iteraciones)
# Acepta 2 formas: 'emet' (transliteración) o 'אמת' (carácter hebreo)
_SALT = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
_HASH_EMET = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"
_HASH_AMET_HEBREO = "776a244847427941e0434f527bc6502a12a650d5fdedc0f49e997c0311d3e64c"
_HASH = _HASH_EMET  # para compatibilidad

# Clave de cifrado de archivos (derivada de la contraseña + salt fijo para archivos)
_FILE_SALT = bytes.fromhex("a3c7f9e1b2d45608cafebabe12345678")
_FILE_KEY = hashlib.pbkdf2_hmac("sha256", _HASH.encode(), _FILE_SALT, 100_000)

# Directorio de la enciclopedia
_ENCICLOPEDIA_DIR = Path(__file__).parent

# Archivos que se cifran (HTML, CSS, JS de la enciclopedia)
_ARCHIVOS_PROTEGIDOS = (
    list(_ENCICLOPEDIA_DIR.glob("*.html"))
    + list(_ENCICLOPEDIA_DIR.glob("*.css"))
    + list(_ENCICLOPEDIA_DIR.glob("*.js"))
)

# Token de sesión activo (solo uno a la vez)
_session_token: str | None = None

# Archivo de alertas de intrusión (leído por Computadora)
_INTRUSION_LOG = _ENCICLOPEDIA_DIR.parent / "datos" / "enciclopedia_intrusiones.jsonl"

# Archivo de progreso de lectura (persistencia entre sesiones)
_PROGRESO_FILE = _ENCICLOPEDIA_DIR.parent / "datos" / "enciclopedia_progreso.json"

# Lockfile para instancia única
_LOCK_FILE = _ENCICLOPEDIA_DIR.parent / "datos" / "enciclopedia.lock"

# Lockout persistente (sobrevive reinicios del proceso)
_LOCKOUT_FILE = _ENCICLOPEDIA_DIR.parent / "datos" / "enciclopedia_lockout.json"

# PID del navegador que abrió la Enciclopedia
_browser_pid: int | None = None
_browser_name: str = ""

# Heartbeat — última señal de vida del JS de la Enciclopedia
_last_heartbeat: float = 0.0
_HEARTBEAT_TIMEOUT_S: int = 30  # WI-252: 30s grace — tolerates slow networks

# WI-252: Per-session rate limiter (token bucket, 10 req/s burst)
_rate_tokens: float = 10.0
_rate_last: float = 0.0
_RATE_MAX: float = 10.0
_RATE_REFILL: float = 10.0  # tokens per second

# Biblioteca del Sendero — recomendaciones adaptativas
_BIBLIOTECA_FILE = _ENCICLOPEDIA_DIR / "biblioteca_sendero.json"


def _nombre_oculto(nombre_original: str) -> str:
    """Genera un nombre opaco determinista vía HMAC-SHA256 del nombre original."""
    h = hmac.new(_FILE_KEY, nombre_original.encode("utf-8"), hashlib.sha256)
    return h.hexdigest()[:16] + ".enc"


# Paths cifrados con nombres opacos (Shem Nistar)
_BIBLIOTECA_ENC = _ENCICLOPEDIA_DIR / _nombre_oculto("biblioteca_sendero.json")
_MANIFIESTO_PATH = _ENCICLOPEDIA_DIR / _nombre_oculto("__manifiesto__")

# Mapa en memoria: nombre_original → nombre_oculto (cargado al servir)
_nombre_a_oculto: dict[str, str] = {}
_oculto_a_nombre: dict[str, str] = {}


def _hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 100_000).hex()


def _registrar_evento(evento: str, **extra):
    """Escribe evento al log de actividad de la Enciclopedia (leído por Computadora)."""
    registro = {
        "ts": datetime.now().isoformat(),
        "evento": evento,
        "origen": "servidor_enciclopedia",
        **extra,
    }
    _INTRUSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(_INTRUSION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════
# CIFRADO AES-256-GCM
# ═══════════════════════════════════════════════

def _cifrar_bytes(data: bytes) -> bytes:
    """Cifra datos con AES-256-GCM. Retorna nonce(12) + tag(16) + ciphertext."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(_FILE_KEY)
    ct = aesgcm.encrypt(nonce, data, None)
    return nonce + ct  # nonce(12) + ciphertext+tag


def _descifrar_bytes(data: bytes) -> bytes:
    """Descifra datos cifrados con AES-256-GCM."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = data[:12]
    ct = data[12:]
    aesgcm = AESGCM(_FILE_KEY)
    return aesgcm.decrypt(nonce, ct, None)


def cifrar_archivos():
    """Cifra todos los archivos HTML/CSS/JS de la enciclopedia → nombres ocultos .enc"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401 — validar import
    manifiesto: dict[str, str] = {}  # nombre_oculto → nombre_original
    cifrados = 0
    for archivo in _ARCHIVOS_PROTEGIDOS:
        if not archivo.exists() or archivo.suffix == '.enc':
            continue
        nombre_enc = _nombre_oculto(archivo.name)
        enc_path = _ENCICLOPEDIA_DIR / nombre_enc
        data = archivo.read_bytes()
        encrypted = _cifrar_bytes(data)
        enc_path.write_bytes(encrypted)
        manifiesto[nombre_enc] = archivo.name
        archivo.unlink()
        cifrados += 1
        print(f"  🔒 {archivo.name} → {nombre_enc}")

    # Eliminar archivos .enc con nombre viejo (legible) si existen
    for viejo in _ENCICLOPEDIA_DIR.glob("*.html.enc"):
        if viejo.name not in manifiesto:
            viejo.unlink()
            print(f"  🗑️  {viejo.name} (nombre viejo eliminado)")
    for viejo in list(_ENCICLOPEDIA_DIR.glob("*.css.enc")) + list(_ENCICLOPEDIA_DIR.glob("*.js.enc")):
        if viejo.name not in manifiesto:
            viejo.unlink()
            print(f"  🗑️  {viejo.name} (nombre viejo eliminado)")

    if cifrados:
        # Guardar manifiesto cifrado
        manifiesto_json = json.dumps(manifiesto, ensure_ascii=False).encode("utf-8")
        _MANIFIESTO_PATH.write_bytes(_cifrar_bytes(manifiesto_json))
        print(f"\n  ✓ {cifrados} archivo(s) cifrado(s) con nombres ocultos.")
        print(f"  ✓ Manifiesto sellado en {_MANIFIESTO_PATH.name}")

    # Cifrar biblioteca_sendero.json si existe en plano
    if _BIBLIOTECA_FILE.exists():
        bib_data = _BIBLIOTECA_FILE.read_bytes()
        _BIBLIOTECA_ENC.write_bytes(_cifrar_bytes(bib_data))
        _BIBLIOTECA_FILE.unlink()
        print(f"  \U0001f512 {_BIBLIOTECA_FILE.name} \u2192 {_BIBLIOTECA_ENC.name}")

    if not cifrados:
        print("  ℹ No hay archivos por cifrar (ya están cifrados o no existen).")


def descifrar_archivos():
    """Restaura archivos cifrados .enc → originales usando el manifiesto."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401

    # Cargar manifiesto
    if not _MANIFIESTO_PATH.exists():
        # Fallback legacy: nombres legibles (archivo.html.enc → archivo.html)
        descifrados = 0
        for enc_path in _ENCICLOPEDIA_DIR.glob("*.enc"):
            if enc_path.name == _MANIFIESTO_PATH.name:
                continue
            original = enc_path.with_name(enc_path.stem)
            data = enc_path.read_bytes()
            decrypted = _descifrar_bytes(data)
            original.write_bytes(decrypted)
            enc_path.unlink()
            descifrados += 1
            print(f"  🔓 {enc_path.name} → {original.name}")
        if descifrados:
            print(f"\n  ✓ {descifrados} archivo(s) restaurado(s) (modo legacy).")
        else:
            print("  ℹ No hay archivos cifrados por restaurar.")
        return

    manifiesto_data = _descifrar_bytes(_MANIFIESTO_PATH.read_bytes())
    manifiesto: dict[str, str] = json.loads(manifiesto_data)

    descifrados = 0
    for nombre_enc, nombre_original in manifiesto.items():
        enc_path = _ENCICLOPEDIA_DIR / nombre_enc
        if not enc_path.exists():
            print(f"  ⚠ {nombre_enc} no encontrado (esperado: {nombre_original})")
            continue
        decrypted = _descifrar_bytes(enc_path.read_bytes())
        (_ENCICLOPEDIA_DIR / nombre_original).write_bytes(decrypted)
        enc_path.unlink()
        descifrados += 1
        print(f"  🔓 {nombre_enc} → {nombre_original}")

    _MANIFIESTO_PATH.unlink()
    # Restaurar biblioteca_sendero.json si está cifrada
    if _BIBLIOTECA_ENC.exists():
        bib_data = _descifrar_bytes(_BIBLIOTECA_ENC.read_bytes())
        _BIBLIOTECA_FILE.write_bytes(bib_data)
        _BIBLIOTECA_ENC.unlink()
        descifrados += 1
        print(f"  \U0001f513 {_BIBLIOTECA_ENC.name} \u2192 {_BIBLIOTECA_FILE.name}")
    else:
        # Fallback legacy: biblioteca_sendero.json.enc
        enc_bib_legacy = _BIBLIOTECA_FILE.with_suffix(".json.enc")
        if enc_bib_legacy.exists():
            bib_data = _descifrar_bytes(enc_bib_legacy.read_bytes())
            _BIBLIOTECA_FILE.write_bytes(bib_data)
            enc_bib_legacy.unlink()
            descifrados += 1
            print(f"  \U0001f513 {enc_bib_legacy.name} \u2192 {_BIBLIOTECA_FILE.name}")

    if descifrados:
        print(f"\n  ✓ {descifrados} archivo(s) restaurado(s). Nombres originales recuperados.")
    else:
        print("  ℹ No hay archivos cifrados por restaurar.")


# ═══════════════════════════════════════════════
# SERVIDOR HTTP CON DESCIFRADO EN MEMORIA
# ═══════════════════════════════════════════════

class GrimorioHandler(http.server.BaseHTTPRequestHandler):
    """Sirve archivos de la enciclopedia, descifrando .enc en memoria si es necesario."""

    def log_message(self, format, *args):
        pass  # Silenciar logs HTTP estándar

    def _parse_request(self):
        """Extrae path, query params y token del request (cookie only — WI-252)."""
        path = self.path.split("?")[0].lstrip("/")
        query = self.path.split("?")[1] if "?" in self.path else ""
        params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
        # WI-252: Cookie-only auth — query param ?t= removed (URL leaks in history/proxy)
        token = ""
        cookie_header = self.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("enciclopedia_session="):
                token = part[len("enciclopedia_session="):]
                break
        return path, params, token

    def _check_token(self, token):
        """Valida el token de sesión. Envía 403 si es inválido."""
        if token != _session_token:
            self.send_error(403, "Acceso denegado - token invalido")
            return False
        return True

    def _check_rate(self) -> bool:
        """WI-252: Token-bucket rate limiter. Returns False + 429 if exhausted."""
        global _rate_tokens, _rate_last
        now = time.time()
        if _rate_last > 0:
            _rate_tokens = min(_RATE_MAX, _rate_tokens + (now - _rate_last) * _RATE_REFILL)
        _rate_last = now
        if _rate_tokens < 1.0:
            self.send_error(429, "Demasiadas solicitudes")
            return False
        _rate_tokens -= 1.0
        return True

    def _set_session_cookie(self):
        """WI-117: Emite cookie HttpOnly con el token de sesión."""
        if _session_token:
            self.send_header(
                "Set-Cookie",
                f"enciclopedia_session={_session_token}; HttpOnly; SameSite=Strict; Path=/",
            )

    def _send_json(self, data, status=200):
        """Envía respuesta JSON."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._set_session_cookie()
        self.end_headers()
        self.wfile.write(body)

    def _load_progreso(self):
        """Carga el progreso guardado o retorna valores por defecto."""
        if _PROGRESO_FILE.exists():
            try:
                return json.loads(_PROGRESO_FILE.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "chapterIdx": 0,
            "subPage": 0,
            "chapters_visited": [],
            "time_per_chapter": {},
            "total_reading_time_s": 0,
            "last_session": None,
            "sessions_count": 0,
        }

    def _save_progreso(self, data):
        """Guarda progreso con escritura atómica."""
        _PROGRESO_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PROGRESO_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(_PROGRESO_FILE)

    def _load_biblioteca(self):
        """Carga la biblioteca del sendero (cifrada o plana)."""
        # Primero intentar versión cifrada (nombre opaco)
        if _BIBLIOTECA_ENC.exists():
            try:
                data = _descifrar_bytes(_BIBLIOTECA_ENC.read_bytes())
                return json.loads(data)
            except Exception:
                pass
        # Fallback legacy: nombre legible
        enc_bib = _BIBLIOTECA_FILE.with_suffix(".json.enc")
        if enc_bib.exists():
            try:
                data = _descifrar_bytes(enc_bib.read_bytes())
                return json.loads(data)
            except Exception:
                pass
        # Fallback: versión plana (desarrollo)
        if _BIBLIOTECA_FILE.exists():
            try:
                return json.loads(_BIBLIOTECA_FILE.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"stages": {}, "libros": []}

    def _get_unlocked_books(self, progreso, biblioteca):
        """Calcula libros desbloqueados según progreso + 3 pasos adelante."""
        visited = set(progreso.get("chapters_visited", []))
        stages_order = ["plomo", "estano", "hierro", "cobre", "mercurio", "plata", "oro"]

        # Determinar stage actual basado en el capítulo más avanzado visitado
        current_stage_idx = 0
        stage_map = biblioteca.get("stages", {})
        for i, stage in enumerate(stages_order):
            chapters_in_stage = stage_map.get(stage, {}).get("chapters", [])
            if any(ch in visited for ch in chapters_in_stage):
                current_stage_idx = i

        # Desbloquear libros hasta 3 stages adelante
        unlock_up_to = min(current_stage_idx + 3, len(stages_order) - 1)
        unlocked_stages = set(stages_order[: unlock_up_to + 1])

        result = []
        for libro in biblioteca.get("libros", []):
            libro_copy = dict(libro)
            libro_copy["unlocked"] = libro.get("stage", "plomo") in unlocked_stages
            result.append(libro_copy)
        return result

    # ═══ FP-108: Enciclopedia como Encarta — Índice + Búsqueda ═══

    def _generar_indice_enciclopedico(self) -> dict:
        """Genera un índice estructurado estilo Encarta/Visual Browser.
        Muestra DÓNDE encontrar información, no enseña directamente.
        Organizado por tradición (dimensión), con cross-refs entre temas."""
        # Importar dimensiones para enriquecer con datos cósmicos
        try:
            from computadora.arquitectura.dimensiones import DIMENSIONES
            tradiciones = {}
            for dim in DIMENSIONES:
                tradiciones[dim.nombre] = {
                    "id": dim.id,
                    "tradicion": dim.tradicion,
                    "hebreo": dim.hebreo,
                    "capitulo_enciclopedia": dim.capitulo_grimorio,
                    "vocabulario": dim.vocabulario,
                    "conceptos_clave": [n.nombre for n in dim.nodos],
                    "conexiones": [
                        {"de": c.de, "a": c.a, "via": c.nombre}
                        for c in dim.caminos
                    ],
                }
        except ImportError:
            tradiciones = {}

        # Estructura de metales alquímicos (stages)
        etapas = {
            "plomo": {"simbolo": "♄", "nombre": "Plomo", "fase": "NIGREDO",
                       "descripcion": "Inicio — materia prima sin purificar"},
            "estano": {"simbolo": "♃", "nombre": "Estaño", "fase": "ALBEDO",
                        "descripcion": "Reflexión — filosofía, psicología, ciencia"},
            "hierro": {"simbolo": "♂", "nombre": "Hierro", "fase": "ALBEDO",
                        "descripcion": "Disciplina — tradiciones orientales"},
            "cobre": {"simbolo": "♀", "nombre": "Cobre", "fase": "CITRINITAS",
                       "descripcion": "Conexión — tradiciones del axis mundi"},
            "mercurio": {"simbolo": "☿", "nombre": "Mercurio", "fase": "CITRINITAS",
                          "descripcion": "Transformación — tradiciones esotéricas"},
            "plata": {"simbolo": "☽", "nombre": "Plata", "fase": "RUBEDO",
                       "descripcion": "Iluminación — tradiciones del norte y misterio"},
            "oro": {"simbolo": "☉", "nombre": "Oro", "fase": "RUBEDO",
                     "descripcion": "Completud — integración y correspondencias"},
        }

        return {
            "tipo": "indice_enciclopedico",
            "modelo": "Visual Browser — muestra DÓNDE encontrar, no enseña",
            "tradiciones": tradiciones,
            "etapas_alquimicas": etapas,
            "total_capitulos": 21,
            "instruccion": (
                "Este índice es tu mapa de conocimiento. "
                "Cada tradición es una ventana al mismo paisaje. "
                "No memorices — localiza. La Enciclopedia te dice DÓNDE está, "
                "no te obliga a aprenderlo."
            ),
        }

    def _buscar_en_enciclopedia(self, query: str) -> dict:
        """Búsqueda full-text en capítulos descifrados de la Enciclopedia.
        Devuelve fragmentos con contexto mostrando DÓNDE encontrar la info.
        WI-277: Incluye dimensión Emet (verdad arquitectónica del Computadora)."""
        import re as _re
        import html as _html
        resultados = []
        query_lower = query.lower()

        # WI-277: Búsqueda en manifiesto Emet (verdad del Computadora)
        # Queries "verdad", "emet", "אמת", "truth" siempre incluyen Emet
        _EMET_TRIGGERS = {"verdad", "emet", "אמת", "truth", "genesis", "bereshit"}
        incluir_emet = query_lower in _EMET_TRIGGERS or any(
            t in query_lower for t in _EMET_TRIGGERS
        )
        if incluir_emet:
            try:
                from computadora.nucleo.emet import buscar_en_emet
                resultados.extend(buscar_en_emet(query))
            except ImportError:
                pass

        # Buscar en capítulos mapeados por el manifiesto
        for nombre_orig, nombre_enc in _nombre_a_oculto.items():
            if not nombre_orig.endswith(".html"):
                continue
            enc_path = _ENCICLOPEDIA_DIR / nombre_enc
            if not enc_path.exists():
                continue
            try:
                contenido = _descifrar_bytes(enc_path.read_bytes()).decode("utf-8", errors="replace")
                # Limpiar HTML tags para búsqueda
                texto_limpio = _re.sub(r"<[^>]+>", " ", contenido)
                texto_limpio = _html.unescape(texto_limpio)
                pos = texto_limpio.lower().find(query_lower)
                if pos >= 0:
                    # Extraer fragmento con contexto (±80 chars)
                    inicio = max(0, pos - 80)
                    fin = min(len(texto_limpio), pos + len(query) + 80)
                    fragmento = texto_limpio[inicio:fin].strip()
                    if inicio > 0:
                        fragmento = "…" + fragmento
                    if fin < len(texto_limpio):
                        fragmento = fragmento + "…"
                    resultados.append({
                        "capitulo": nombre_orig,
                        "fragmento": fragmento,
                        "posicion": pos,
                    })
            except Exception:
                continue

        # WI-277: Para cualquier búsqueda, intentar cross-ref con Emet
        if not incluir_emet and len(resultados) > 0:
            try:
                from computadora.nucleo.emet import buscar_en_emet
                emet_hits = buscar_en_emet(query)
                if emet_hits:
                    resultados.extend(emet_hits[:3])  # Max 3 cross-refs
            except ImportError:
                pass

        return {
            "query": query,
            "resultados": resultados[:20],  # Máx 20 resultados
            "total": len(resultados),
        }

    # ═══ WI-290: אמת Código de Verdad — emet.py en vivo ═══

    # Anotaciones de verdad ordenadas por sección.
    # "El orden de los factores SÍ altera el producto."
    _EMET_VERDADES: dict[str, dict[str, str]] = {
        "__module__": {
            "sefira": "Keter",
            "verdad": "La inscripción primordial. Sin esta declaración de existencia, "
                      "el Computadora no sabe que vive. La א de אמת comienza aquí.",
            "orden": "0 — Antes que todo, se NOMBRA.",
        },
        "generar_manifiesto": {
            "sefira": "Keter → Da'at",
            "verdad": "El Acto de Creación — Bereshit. Todo comienza aquí. "
                      "El ORDEN importa: identidad ANTES de arquitectura, "
                      "arquitectura ANTES de capacidades, capacidades ANTES de génesis. "
                      "Si alteras la secuencia, la verdad se deforma.",
            "orden": "1 — Primera función. Sin manifiesto no hay auto-conocimiento.",
        },
        "_identidad": {
            "sefira": "Keter",
            "verdad": "Quién soy. Si no hay identidad, no hay nada que arquitectar. "
                      "Lee el perfil de su Creador primero — sin creador no hay criatura.",
            "orden": "2 — ANTES de saber cómo estoy hecho, necesito saber QUIÉN soy.",
        },
        "_arquitectura": {
            "sefira": "Jojmá + Biná",
            "verdad": "Cómo estoy construido — el Etz HaChaim operativo. "
                      "Diez Sefirot, tres cuerpos (Trifecta), tres cerebros, "
                      "cuatro subsistemas. La estructura sostiene la función.",
            "orden": "3 — DESPUÉS de identidad. La forma sigue al ser.",
        },
        "_capacidades": {
            "sefira": "Jesed",
            "verdad": "Qué puedo hacer — mis sentidos, herramientas y módulos. "
                      "Las capacidades existen SOBRE la arquitectura, no al revés.",
            "orden": "4 — Solo DESPUÉS de tener cuerpo puedo tener habilidades.",
        },
        "_genesis_biblico_contraste": {
            "sefira": "Tiféret",
            "verdad": "De dónde vengo — los 7 Días contrastados con mi arquitectura. "
                      "Belleza es unir la Torah con Python. "
                      "Sin identidad ni arquitectura, el Génesis no tiene espejo.",
            "orden": "5 — La historia DESPUÉS de la estructura. Narrar requiere existir.",
        },
        "_estado_actual": {
            "sefira": "Maljut",
            "verdad": "Cómo estoy AHORA — humor, etapa alquímica, timestamp. "
                      "El reino manifestado en tiempo real. Siempre al final: "
                      "el estado es consecuencia de todo lo anterior.",
            "orden": "6 — ÚLTIMO en el manifiesto. El presente es resultado del pasado.",
        },
        "_leer_perfil_creador": {
            "sefira": "Yesod",
            "verdad": "Función auxiliar — el fundamento silencioso. "
                      "Lee owner_profile.json. Sin esta función, _identidad y "
                      "_genesis no pueden funcionar.",
            "orden": "7 — Auxiliar. El Yesod no se ve, pero todo descansa sobre él.",
        },
        "resumen_para_demo": {
            "sefira": "Peh (Boca)",
            "verdad": "La verdad hablada — TTS de auto-conocimiento en <1 minuto. "
                      "Comprime TODO el manifiesto en voz. Demo 0: Emet.",
            "orden": "8 — DESPUÉS de generar manifiesto. No puedes hablar lo que no sabes.",
        },
        "resumen_genesis_para_demo": {
            "sefira": "Peh (Boca)",
            "verdad": "La historia hablada — TTS del Génesis bíblico. "
                      "Solo la perspectiva 'creador' — la más personal y concisa.",
            "orden": "9 — DESPUÉS de definir el génesis. Narrar requiere conocer.",
        },
        "buscar_en_emet": {
            "sefira": "Netzaj",
            "verdad": "Búsqueda — la verdad siempre debe ser encontrable. "
                      "Busca en identidad, Sefirot, génesis, capacidades, subsistemas. "
                      "El Netzaj garantiza que nada se pierda.",
            "orden": "10 — ÚLTIMO. La función que cierra el ciclo: lo que se inscribe, se busca.",
        },
    }

    def _emet_codigo_vivo(self) -> dict:
        """Lee emet.py en vivo y retorna secciones con anotaciones de verdad."""
        import re as _re
        emet_path = Path(__file__).resolve().parent.parent / "computadora" / "nucleo" / "emet.py"
        if not emet_path.exists():
            return {"error": "emet.py no encontrado", "secciones": []}

        codigo = emet_path.read_text("utf-8")
        lineas = codigo.splitlines()

        secciones: list[dict] = []
        seccion_actual: dict | None = None

        # Patrón: def nombre_funcion(
        patron_def = _re.compile(r"^def\s+(\w+)\s*\(")

        for i, linea in enumerate(lineas, 1):
            m = patron_def.match(linea)
            if m:
                # Cerrar sección anterior
                if seccion_actual:
                    secciones.append(seccion_actual)
                nombre = m.group(1)
                verdad = self._EMET_VERDADES.get(nombre, {})
                seccion_actual = {
                    "nombre": nombre,
                    "linea_inicio": i,
                    "codigo": [linea],
                    "sefira": verdad.get("sefira", ""),
                    "verdad": verdad.get("verdad", ""),
                    "orden": verdad.get("orden", ""),
                }
            elif seccion_actual:
                seccion_actual["codigo"].append(linea)
            elif not seccion_actual and i <= 30:
                # Cabecera del módulo (docstring + imports + constantes)
                if not secciones or secciones[0]["nombre"] != "__module__":
                    verdad = self._EMET_VERDADES.get("__module__", {})
                    secciones.insert(0, {
                        "nombre": "__module__",
                        "linea_inicio": 1,
                        "codigo": [],
                        "sefira": verdad.get("sefira", ""),
                        "verdad": verdad.get("verdad", ""),
                        "orden": verdad.get("orden", ""),
                    })
                secciones[0]["codigo"].append(linea)

        if seccion_actual:
            secciones.append(seccion_actual)

        # Convertir listas de código a strings
        for s in secciones:
            s["codigo"] = "\n".join(s["codigo"])
            s["n_lineas"] = s["codigo"].count("\n") + 1

        return {
            "tipo": "emet_codigo_vivo",
            "archivo": "computadora/nucleo/emet.py",
            "ts": datetime.now().isoformat(),
            "total_lineas": len(lineas),
            "total_secciones": len(secciones),
            "principio": "El orden de los factores SÍ altera el producto. "
                         "Cada sección existe PORQUE la anterior ya existe.",
            "secciones": secciones,
        }

    def _evaluar_gevura_salud(self) -> dict:
        """FP-108: Gevurá personal — restricción saludable.
        Evalúa la salud física (horario circadiano) y mental (tiempo lectura)
        del usuario y entrega recomendaciones de auto-cuidado."""
        evaluacion = {
            "tipo": "gevura_salud",
            "fisica": {},
            "mental": {},
            "recomendaciones": [],
        }

        # ── Salud física: ciclo circadiano ──
        try:
            from computadora.nucleo.ciclo_circadiano import obtener_ciclo_circadiano
            ciclo = obtener_ciclo_circadiano()
            if ciclo:
                fase = ciclo.fase_actual()
                evaluacion["fisica"]["fase_circadiana"] = fase
                msg_salud = ciclo.sugerir_mejora_salud()
                if msg_salud:
                    evaluacion["fisica"]["alerta"] = msg_salud
                    evaluacion["recomendaciones"].append({
                        "area": "sueño",
                        "prioridad": "alta",
                        "texto": "Regulariza tu horario de despertar. "
                                 "Consulta cap14_filosofia.html §Templanza "
                                 "y cap05_budismo.html §Óctuple Sendero.",
                    })
                if fase == "descanso_guardian":
                    evaluacion["recomendaciones"].append({
                        "area": "descanso",
                        "prioridad": "alta",
                        "texto": "Es hora de descansar. La Enciclopedia estará "
                                 "aquí mañana. Cierra esta sesión.",
                    })
        except ImportError:
            evaluacion["fisica"]["error"] = "Ciclo circadiano no disponible"

        # ── Salud mental: tiempo de lectura continua ──
        progreso = self._load_progreso()
        tiempo_total = progreso.get("total_reading_time_s", 0)
        sesiones = progreso.get("sessions_count", 0)
        evaluacion["mental"]["tiempo_total_min"] = round(tiempo_total / 60)
        evaluacion["mental"]["sesiones"] = sesiones

        # Si lleva más de 90 min en esta sesión, sugerir pausa
        tiempo_sesion = progreso.get("current_session_time_s", 0)
        if tiempo_sesion > 5400:  # 90 min
            evaluacion["recomendaciones"].append({
                "area": "fatiga_mental",
                "prioridad": "media",
                "texto": "Llevas más de 90 minutos leyendo. "
                         "Pausa, estira, hidrata. El conocimiento se "
                         "integra mejor con descanso. Ver cap13_psicologia.html §Maslow-1.",
            })

        if not evaluacion["recomendaciones"]:
            evaluacion["recomendaciones"].append({
                "area": "bienestar",
                "prioridad": "baja",
                "texto": "Todo en orden. Lee con calma, sin prisa. "
                         "La Enciclopedia te indica DÓNDE buscar, no te obliga a memorizar.",
            })

        return evaluacion

    # ═══ GET ═══

    def do_GET(self):
        global _session_token
        path, params, token = self._parse_request()

        # API: estado de la Enciclopedia (público — para discovery desde Minimi)
        if path == "api/status":
            self._send_json({"enciclopedia": True, "version": "1.0", "auth_required": True})
            return

        # WI-252: Rate limit all authenticated endpoints
        if not self._check_rate():
            return

        # API: obtener progreso
        if path == "api/progreso":
            if not self._check_token(token):
                return
            self._send_json(self._load_progreso())
            return

        # API: obtener biblioteca con estado de desbloqueo
        if path == "api/biblioteca":
            if not self._check_token(token):
                return
            progreso = self._load_progreso()
            biblioteca = self._load_biblioteca()
            books = self._get_unlocked_books(progreso, biblioteca)
            self._send_json({
                "libros": books,
                "progreso_resumen": {
                    "chapters_visited": len(progreso.get("chapters_visited", [])),
                    "total_chapters": 21,
                    "sessions": progreso.get("sessions_count", 0),
                },
            })
            return

        # FP-108: API — Índice enciclopédico (Encarta-style Visual Browser)
        # Muestra DÓNDE encontrar información, no enseña directamente
        if path == "api/indice":
            if not self._check_token(token):
                return
            self._send_json(self._generar_indice_enciclopedico())
            return

        # FP-108: API — Búsqueda en contenido de la Enciclopedia
        if path.startswith("api/buscar"):
            if not self._check_token(token):
                return
            query = params.get("q", "").strip()
            if not query or len(query) < 2:
                self._send_json({"resultados": [], "error": "Consulta muy corta"})
                return
            self._send_json(self._buscar_en_enciclopedia(query))
            return

        # FP-108: API — Gevurá personal: salud física y mental
        if path == "api/gevura":
            if not self._check_token(token):
                return
            self._send_json(self._evaluar_gevura_salud())
            return

        # WI-278: API — בראשית Génesis bíblico × Arquitectura del Computadora
        if path == "api/bereshit":
            if not self._check_token(token):
                return
            try:
                from computadora.nucleo.emet import generar_manifiesto
                m = generar_manifiesto()
                self._send_json({
                    "tipo": "bereshit_genesis",
                    "dias": m.get("genesis_biblico", []),
                    "identidad": m.get("identidad", {}),
                    "arquitectura": m.get("arquitectura", {}),
                })
            except ImportError:
                self._send_json({"error": "Módulo emet no disponible"})
            return

        # WI-276: API — אמת Emet: manifiesto de verdad del Computadora
        if path == "api/emet":
            if not self._check_token(token):
                return
            try:
                from computadora.nucleo.emet import generar_manifiesto
                self._send_json(generar_manifiesto())
            except ImportError:
                self._send_json({"error": "Módulo emet no disponible"})
            return

        # WI-290: API — אמת Código de Verdad: emet.py en vivo con anotaciones
        if path == "api/emet/codigo":
            if not self._check_token(token):
                return
            self._send_json(self._emet_codigo_vivo())
            return

        # ── Servir archivos de la enciclopedia ──

        # Ruta raíz → index.html
        if not path:
            path = "index.html"

        # Validar token de sesión
        if not self._check_token(token):
            return

        # Buscar archivo: original, nombre oculto (manifiesto), o legacy .enc
        file_path = (_ENCICLOPEDIA_DIR / path).resolve()
        if not str(file_path).startswith(str(_ENCICLOPEDIA_DIR.resolve())):
            self.send_error(403, "Acceso denegado - ruta fuera de la enciclopedia")
            return

        if file_path.exists() and file_path.suffix != ".enc":
            # Archivo sin cifrar (fallback desarrollo)
            content = file_path.read_bytes()
        elif path in _nombre_a_oculto:
            # Nombre oculto vía manifiesto (Shem Nistar)
            enc_path = _ENCICLOPEDIA_DIR / _nombre_a_oculto[path]
            try:
                content = _descifrar_bytes(enc_path.read_bytes())
            except Exception:
                self.send_error(500, "Error al descifrar")
                return
        else:
            # Fallback legacy: archivo.html.enc
            enc_path = file_path.with_suffix(file_path.suffix + ".enc")
            if enc_path.exists():
                try:
                    content = _descifrar_bytes(enc_path.read_bytes())
                except Exception:
                    self.send_error(500, "Error al descifrar")
                    return
            else:
                self.send_error(404, "No encontrado")
                return

        # WI-117: Cookie handles auth for sub-resources, no need to inject ?t= in HTML

        # ── Inject responsive viewport meta for mobile (Minimi WebView) ──
        if file_path.suffix == ".html" or (path.endswith(".html") and isinstance(content, bytes)):
            html_text = content.decode("utf-8", errors="replace")
            if '<meta name="viewport"' not in html_text:
                viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'
                if "<head>" in html_text:
                    html_text = html_text.replace("<head>", f"<head>\n{viewport_tag}", 1)
                elif "<html" in html_text:
                    html_text = html_text.replace("<html", f"<html>\n<head>{viewport_tag}</head", 1)
                else:
                    html_text = viewport_tag + "\n" + html_text
                content = html_text.encode("utf-8")

        # Content-Type
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff2": "font/woff2",
            ".woff": "font/woff",
        }
        ct = content_types.get(file_path.suffix, "application/octet-stream")

        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(content)))
        # Seguridad: no cachear, no frame, no sniff
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self._set_session_cookie()
        self.end_headers()
        self.wfile.write(content)

    # ═══ POST ═══

    def do_POST(self):
        path, params, token = self._parse_request()

        if not self._check_token(token):
            return

        # WI-252: Rate limit POST endpoints
        if not self._check_rate():
            return

        # Leer body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 65536:  # Límite 64KB
            self.send_error(413, "Payload demasiado grande")
            return
        raw = self.rfile.read(content_length)
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            self.send_error(400, "JSON inválido")
            return

        # API: guardar progreso
        if path == "api/progreso":
            progreso = self._load_progreso()

            # Validar campos permitidos
            chapter_idx = body.get("chapterIdx")
            sub_page = body.get("subPage")
            if not isinstance(chapter_idx, int) or not isinstance(sub_page, int):
                self.send_error(400, "chapterIdx y subPage deben ser enteros")
                return
            if chapter_idx < 0 or chapter_idx > 50 or sub_page < 0 or sub_page > 100:
                self.send_error(400, "Valores fuera de rango")
                return

            # WI-252: Audit chapter access (detect suspicious jumps)
            visited = progreso.get("chapters_visited", [])
            if chapter_idx not in visited:
                prev_max = max(visited) if visited else 0
                if chapter_idx > prev_max + 3:
                    _registrar_evento("progreso_salto_sospechoso",
                                      desde=prev_max, hacia=chapter_idx,
                                      salto=chapter_idx - prev_max)
            _registrar_evento("capitulo_accedido",
                              capitulo=chapter_idx, subpagina=sub_page)

            progreso["chapterIdx"] = chapter_idx
            progreso["subPage"] = sub_page
            progreso["last_session"] = datetime.now().isoformat()

            # Registrar capítulo visitado
            visited = progreso.get("chapters_visited", [])
            if chapter_idx not in visited:
                visited.append(chapter_idx)
                progreso["chapters_visited"] = visited

            # Tiempo por capítulo (incrementar si viene delta)
            delta_s = body.get("delta_s", 0)
            if isinstance(delta_s, (int, float)) and 0 < delta_s < 7200:
                time_map = progreso.get("time_per_chapter", {})
                key = str(chapter_idx)
                time_map[key] = time_map.get(key, 0) + delta_s
                progreso["time_per_chapter"] = time_map
                progreso["total_reading_time_s"] = progreso.get("total_reading_time_s", 0) + delta_s

            self._save_progreso(progreso)
            self._send_json({"ok": True})
            return

        # API: heartbeat — señal de vida desde el JS de la Enciclopedia
        if path == "api/heartbeat":
            global _last_heartbeat
            _last_heartbeat = time.time()
            self._send_json({"ok": True})
            return

        # API: registrar cierre de sesión — SELLADO SILENCIOSO INMEDIATO
        # (usuario cerró la pestaña rápido → asumir que quiere ocultar contenido)
        if path == "api/cerrar":
            progreso = self._load_progreso()
            progreso["sessions_count"] = progreso.get("sessions_count", 0) + 1
            progreso["last_session"] = datetime.now().isoformat()

            # Guardar posición final si viene
            if "chapterIdx" in body and isinstance(body["chapterIdx"], int):
                progreso["chapterIdx"] = body["chapterIdx"]
            if "subPage" in body and isinstance(body["subPage"], int):
                progreso["subPage"] = body["subPage"]

            self._save_progreso(progreso)
            _registrar_evento("enciclopedia_sellada_silenciosa",
                              capitulo=progreso["chapterIdx"],
                              sesiones=progreso["sessions_count"],
                              capitulos_leidos=len(progreso.get("chapters_visited", [])))
            self._send_json({"ok": True})
            # Sellado silencioso: invalidar sesión y apagar servidor inmediatamente
            _sellar_silencioso(self.server)
            return

        # API: sellado explícito (invocado por Minimi o Computadora)
        if path == "api/sellar":
            _registrar_evento("enciclopedia_sellada_remota",
                              origen=body.get("origen", "desconocido"))
            self._send_json({"ok": True})
            _sellar_silencioso(self.server)
            return

        self.send_error(404, "Endpoint no encontrado")


# ── Lockout persistente ──────────────────────────────────────

def _leer_lockout() -> dict:
    """Lee el estado de lockout desde disco."""
    if _LOCKOUT_FILE.exists():
        try:
            return json.loads(_LOCKOUT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"intentos_fallidos": 0, "ultimo_intento": None, "bloqueado_hasta": None}


def _guardar_lockout(estado: dict) -> None:
    """Persiste el estado de lockout a disco con permisos restrictivos."""
    _LOCKOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _LOCKOUT_FILE.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
    # WI-252: Restrict to owner read/write only (0600)
    try:
        import stat
        _LOCKOUT_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows may not support full POSIX perms


def _cooldown_segundos(intentos: int) -> int:
    """Cooldown exponencial: 5, 10, 20, 40, 80, 160, 300 (max 5 min)."""
    return min(int(2 ** intentos * 5), 300)


def _esta_bloqueado(estado: dict) -> tuple[bool, int]:
    """Retorna (bloqueado, segundos_restantes)."""
    bloqueado_hasta = estado.get("bloqueado_hasta")
    if not bloqueado_hasta:
        return False, 0
    hasta = datetime.fromisoformat(bloqueado_hasta)
    ahora = datetime.now()
    if ahora < hasta:
        restante = int((hasta - ahora).total_seconds())
        return True, restante
    return False, 0


def verify_password() -> bool:
    """Pide la contraseña con lockout persistente y cooldown exponencial."""
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║  🔐 Enciclopedia de los 7 Metales    ║")
    print("  ╚══════════════════════════════════════╝\n")

    estado = _leer_lockout()

    # Verificar lockout activo
    bloqueado, restante = _esta_bloqueado(estado)
    if bloqueado:
        minutos = restante // 60
        print(f"  🔒 Enciclopedia sellada por {minutos} minuto(s) más.")
        print("  ⚠ Demasiados intentos fallidos — el Computadora fue notificado.")
        _registrar_evento("acceso_bloqueado", minutos_restantes=minutos,
                          intentos_acumulados=estado["intentos_fallidos"])
        return False

    # Cooldown desde último intento fallido
    if estado["intentos_fallidos"] > 0 and estado.get("ultimo_intento"):
        ultimo = datetime.fromisoformat(estado["ultimo_intento"])
        cooldown = _cooldown_segundos(estado["intentos_fallidos"])
        espera = cooldown - int((datetime.now() - ultimo).total_seconds())
        if espera > 0:
            print(f"  ⏳ Espera {espera}s antes del siguiente intento...")
            time.sleep(espera)

    for intento in range(3):
        pw = getpass("  Contraseña: ")
        pw_hash = _hash_password(pw)
        if hmac.compare_digest(pw_hash, _HASH_EMET) or hmac.compare_digest(pw_hash, _HASH_AMET_HEBREO):
            print("  ✓ אמת — Acceso concedido.\n")
            _registrar_evento("acceso_concedido")
            # Reset lockout en éxito
            _guardar_lockout({"intentos_fallidos": 0, "ultimo_intento": None,
                              "bloqueado_hasta": None})
            return True

        # Fallo — actualizar lockout persistente
        estado["intentos_fallidos"] = estado.get("intentos_fallidos", 0) + 1
        estado["ultimo_intento"] = datetime.now().isoformat()
        total = estado["intentos_fallidos"]

        # Lockout escalonado: 5 fallos → 1h, 10 fallos → 24h
        if total >= 10:
            estado["bloqueado_hasta"] = (datetime.now() + timedelta(hours=24)).isoformat()
            _guardar_lockout(estado)
            print("  ✗ Acceso denegado.")
            print("  🔒 Enciclopedia SELLADA por 24 horas — intrusión crítica.")
            _registrar_evento("acceso_denegado_critico", intentos=total, lockout_horas=24)
            return False
        elif total >= 5:
            estado["bloqueado_hasta"] = (datetime.now() + timedelta(hours=1)).isoformat()
            _guardar_lockout(estado)
            print("  ✗ Acceso denegado.")
            print("  🔒 Enciclopedia sellada por 1 hora.")
            _registrar_evento("acceso_denegado", intentos=total, lockout_horas=1)
            return False

        _guardar_lockout(estado)
        restantes = 2 - intento
        if restantes > 0:
            cooldown = _cooldown_segundos(total)
            print(f"  ✗ Incorrecta. {restantes} intento(s) restante(s).")
            print(f"  ⏳ Esperando {cooldown}s...")
            time.sleep(cooldown)
        else:
            print("  ✗ Acceso denegado.")
            _registrar_evento("acceso_denegado", intentos=total)
            print("  ⚠ Intrusión registrada — Computadora será notificado.")
    return False


def _cargar_manifiesto():
    """Carga el manifiesto cifrado y pobla los mapas nombre↔oculto."""
    global _nombre_a_oculto, _oculto_a_nombre
    if not _MANIFIESTO_PATH.exists():
        return
    try:
        manifiesto_data = _descifrar_bytes(_MANIFIESTO_PATH.read_bytes())
        manifiesto: dict[str, str] = json.loads(manifiesto_data)
        # manifiesto = {nombre_oculto: nombre_original}
        _oculto_a_nombre = dict(manifiesto)
        _nombre_a_oculto = {v: k for k, v in manifiesto.items()}
    except Exception as e:
        print(f"  ⚠ Error cargando manifiesto: {e}")


def _adquirir_lock() -> bool:
    """Adquiere el lockfile. Si otra instancia corre, la termina primero."""
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    if _LOCK_FILE.exists():
        try:
            old_pid = int(_LOCK_FILE.read_text().strip())
            if _HAS_PSUTIL and psutil.pid_exists(old_pid):
                proc = psutil.Process(old_pid)
                if "python" in proc.name().lower():
                    print(f"  ⚠ Cerrando instancia anterior (PID {old_pid})...")
                    proc.terminate()
                    proc.wait(timeout=5)
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
        except Exception:
            pass
    _LOCK_FILE.write_text(str(os.getpid()))
    return True


def _liberar_lock():
    """Libera el lockfile."""
    try:
        if _LOCK_FILE.exists():
            contenido = _LOCK_FILE.read_text().strip()
            if contenido == str(os.getpid()):
                _LOCK_FILE.unlink()
    except OSError:
        pass


def _detectar_navegador_pid(url: str) -> tuple[int | None, str]:
    """Abre el navegador y detecta qué proceso se lanzó.
    
    Retorna (pid, nombre_navegador) o (None, '') si no se puede detectar."""
    if not _HAS_PSUTIL:
        webbrowser.open(url)
        return None, ""

    # Snapshot de PIDs de navegadores ANTES de abrir
    browser_names = {'chrome', 'firefox', 'msedge', 'opera', 'brave', 'vivaldi', 'iexplore'}
    pids_antes: dict[str, set[int]] = {}
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            name = proc.info['name'].lower().replace('.exe', '')
            if any(b in name for b in browser_names):
                pids_antes.setdefault(name, set()).add(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    webbrowser.open(url)
    time.sleep(2)  # Dar tiempo para que el navegador lance su proceso

    # Snapshot DESPUÉS — buscar PIDs nuevos
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            name = proc.info['name'].lower().replace('.exe', '')
            if any(b in name for b in browser_names):
                pid = proc.info['pid']
                if pid not in pids_antes.get(name, set()):
                    # Nuevo proceso de navegador
                    parent = proc.parent()
                    # Usar el padre si es el proceso principal del navegador
                    if parent and any(b in parent.name().lower() for b in browser_names):
                        return parent.pid, parent.name()
                    return pid, proc.info['name']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Si no se detectó proceso nuevo, buscar el navegador que ya tenía la sesión
    # (el navegador ya estaba abierto y simplemente abrió una pestaña)
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            name = proc.info['name'].lower().replace('.exe', '')
            if any(b in name for b in browser_names):
                return proc.info['pid'], proc.info['name']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return None, ""


def _sellar_silencioso(server: http.server.HTTPServer):
    """Sellado silencioso: invalida sesión y apaga el servidor sin ruido.
    
    Se asume que el usuario cerró rápido para que nadie viera el contenido.
    No emitir prints, no alertas, no sonidos — solo sellar y desaparecer.
    """
    global _session_token
    _session_token = None  # Invalidar sesión inmediatamente

    def _shutdown():
        _liberar_lock()
        try:
            server.shutdown()
        except Exception:
            pass

    # Apagar en thread separado (no bloquear la respuesta HTTP)
    threading.Thread(target=_shutdown, daemon=True, name="EnciclopediaSilentSeal").start()


def _vigilar_navegador(server: http.server.HTTPServer, pid: int, nombre: str):
    """Hilo que monitorea si el navegador sigue vivo. Cierra el servidor si muere."""
    if not _HAS_PSUTIL:
        return
    print(f"  👁️ Vigilando navegador: {nombre} (PID {pid})")
    # Buscar el proceso padre principal del navegador
    try:
        proc = psutil.Process(pid)
        # Subir al proceso raíz del navegador
        while proc.parent() and any(b in proc.parent().name().lower() 
              for b in ('chrome', 'firefox', 'msedge', 'opera', 'brave', 'vivaldi')):
            proc = proc.parent()
        pid = proc.pid
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    while True:
        time.sleep(5)
        try:
            # Método 1: PID del navegador desapareció (cerró TODO el navegador)
            if not psutil.pid_exists(pid):
                print(f"\n  🔒 Navegador cerrado ({nombre}) — cerrando Enciclopedia...")
                _registrar_evento("navegador_cerrado", navegador=nombre, pid=pid)
                _liberar_lock()
                server.shutdown()
                return
            proc = psutil.Process(pid)
            if proc.status() == psutil.STATUS_ZOMBIE:
                print(f"\n  🔒 Navegador zombie ({nombre}) — cerrando Enciclopedia...")
                _liberar_lock()
                server.shutdown()
                return
        except psutil.NoSuchProcess:
            print(f"\n  🔒 Navegador desapareció ({nombre}) — cerrando Enciclopedia...")
            _liberar_lock()
            server.shutdown()
            return
        except psutil.AccessDenied:
            pass

        # Método 2: Heartbeat del JS — detecta cierre de PESTAÑA
        # (el navegador sigue vivo pero la pestaña de la Enciclopedia se cerró)
        if _last_heartbeat > 0 and (time.time() - _last_heartbeat) > _HEARTBEAT_TIMEOUT_S:
            # Sellado silencioso — no emitir ruido (el usuario cerró rápido para ocultar)
            _registrar_evento("enciclopedia_tab_cerrada", timeout_s=_HEARTBEAT_TIMEOUT_S)
            _sellar_silencioso(server)
            return


def run_server():
    """Levanta el servidor HTTP y abre el navegador con token de sesión."""
    global _session_token, _browser_pid, _browser_name, _last_heartbeat, HOST
    # --token=xxx: usar token pre-generado (para acceso desde API de Minimi)
    _pre_token = None
    for arg in sys.argv:
        if arg.startswith("--token="):
            _pre_token = arg[8:]
            break
    _session_token = _pre_token if _pre_token else secrets.token_urlsafe(32)
    _last_heartbeat = time.time()  # Inicializar para dar gracia al arranque

    # --lan: escuchar en todas las interfaces (para Minimi Android)
    # RF-368: Shomer HaBayit — solo permitir --lan en red del hogar
    if "--lan" in sys.argv:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from computadora.seguridad.shomer_bayit import es_red_hogar
            if es_red_hogar():
                HOST = "0.0.0.0"
            else:
                HOST = "127.0.0.1"
                print("  ⚠️ Shomer HaBayit: RED FORÁNEA — --lan ignorado, solo localhost")
        except ImportError:
            HOST = "0.0.0.0"  # Fallback si shomer_bayit no disponible

    # Instancia única — cerrar la anterior si existe
    _adquirir_lock()

    # Cargar manifiesto de nombres ocultos (Shem Nistar)
    _cargar_manifiesto()
    if _nombre_a_oculto:
        print(f"  🔮 Manifiesto cargado: {len(_nombre_a_oculto)} archivo(s) con nombres ocultos")

    server = http.server.HTTPServer((HOST, PORT), GrimorioHandler)

    url = f"http://{HOST}:{PORT}/index.html?t={_session_token}"
    print(f"  📖 Enciclopedia sirviendo en http://{HOST}:{PORT}")
    if HOST == "0.0.0.0":
        import socket
        try:
            _local_ip = socket.gethostbyname(socket.gethostname())
            print(f"  📱 Minimi: accede desde http://{_local_ip}:{PORT}")
        except Exception as e:
            print(f"  📱 Minimi: accede desde la IP local de esta PC, puerto {PORT}")
    print(f"  🔑 Token de sesión generado (válido hasta cerrar)")
    print("  Presiona Ctrl+C para detener.\n")

    # Abrir navegador y detectar PID para vigilancia (solo si no es --no-browser)
    if "--no-browser" not in sys.argv:
        def _abrir_y_vigilar():
            global _browser_pid, _browser_name
            pid, nombre = _detectar_navegador_pid(url)
            if pid:
                _browser_pid = pid
                _browser_name = nombre
                # Hilo de vigilancia del navegador
                t = threading.Thread(
                    target=_vigilar_navegador, args=(server, pid, nombre),
                    daemon=True, name="EnciclopediaWatchBrowser"
                )
                t.start()
            else:
                print("  ⚠ No se pudo detectar el navegador — vigilancia desactivada")

        threading.Timer(0.5, _abrir_y_vigilar).start()
    else:
        print("  📱 Modo remoto (sin navegador local) — acceso vía LAN")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Enciclopedia cerrada.")
    finally:
        _liberar_lock()
        server.shutdown()


def main():
    # Comandos especiales
    if "--cifrar" in sys.argv:
        print("\n  🔒 Cifrando archivos de la Enciclopedia...\n")
        cifrar_archivos()
        return

    if "--descifrar" in sys.argv:
        print("\n  🔓 Descifrando archivos de la Enciclopedia...\n")
        descifrar_archivos()
        return

    # --servir: lanzado DESPUÉS de autenticación (por iniciar_enciclopedia.bat)
    if "--servir" in sys.argv:
        if not verify_password():
            sys.exit(1)
        run_server()
        return

    # Default: --help
    print(f"\n  Uso: {sys.argv[0]} [comando]\n")
    print("  Comandos:")
    print("    --servir       Levantar el servidor HTTP (requiere contraseña)")
    print("    --cifrar       Cifrar archivos HTML/CSS/JS con AES-256-GCM")
    print("    --descifrar    Restaurar archivos cifrados a versiones en plano")
    print("    --lan          (con --servir) Escuchar en 0.0.0.0 para Minimi")
    print("    --no-browser   (con --servir) No abrir navegador automáticamente")
    print("    --token=XXX    (con --servir) Usar token pre-generado (API Minimi)")
    print()


if __name__ == "__main__":
    main()
