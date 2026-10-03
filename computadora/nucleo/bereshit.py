from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

_RAIZ = Path(__file__).resolve().parent.parent.parent
_DATOS_DIR = _RAIZ / "datos"
_ESTADO_PATH = _DATOS_DIR / "bereshit_genesis.json"

_IDENTITY_FILES = ["personalidad.json", "owner_profile.json"]


@dataclass
class PasoBereshit:
    numero: int
    nombre: str
    hebreo: str
    actor: str
    mensaje: str
    tipo_input: Optional[str] = None
    clave_dato: Optional[str] = None


PASOS_GENESIS: List[PasoBereshit] = [
    PasoBereshit(1, "Bereshit", "בְּרֵאשִׁית", "user", "¿Cómo te llamas? (tu nombre para que te reconozca)", "texto", "nombre"),
    # FIX: antes no existía ningún paso de tipo "password_setup" en esta
    # lista (aunque _bereshit_paso_user ya sabía manejarlo) — una
    # instalación nueva nunca configuraba su propia contraseña, así que
    # el único reto de seguridad posible (_gevura_verificar_contrasena)
    # caía siempre en la contraseña de desarrollo hardcodeada ("emet"),
    # que un usuario real no tendría forma de conocer.
    PasoBereshit(2, "Gevurah", "גְּבוּרָה", "user",
                 "Crea una contraseña de seguridad. La usaré si alguna vez no te reconozco por tu rostro.",
                 "password_setup", "password_hash"),
]


def _ensure_datos_dir() -> Path:
    _DATOS_DIR.mkdir(parents=True, exist_ok=True)
    return _DATOS_DIR


def _load_state() -> Dict[str, Any]:
    if not _ESTADO_PATH.exists():
        return {"completado": False, "paso_actual": 0, "datos": {}}
    try:
        return json.loads(_ESTADO_PATH.read_text("utf-8"))
    except Exception:
        return {"completado": False, "paso_actual": 0, "datos": {}}


def _save_state(state: Dict[str, Any]) -> None:
    _ensure_datos_dir()
    _ESTADO_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


class BereshitGenesis:
    def __init__(self):
        self._estado = _load_state()
        if "datos" not in self._estado:
            self._estado["datos"] = {}
        if "paso_actual" not in self._estado:
            self._estado["paso_actual"] = 0
        if "completado" not in self._estado:
            self._estado["completado"] = False

    def paso_actual(self) -> Optional[PasoBereshit]:
        if self._estado.get("completado", False):
            return None
        indice = int(self._estado.get("paso_actual", 0))
        if indice < 0 or indice >= len(PASOS_GENESIS):
            return None
        return PASOS_GENESIS[indice]

    def avanzar(self, respuesta: Optional[str] = None) -> None:
        paso = self.paso_actual()
        if paso is None:
            return
        if respuesta and paso.clave_dato:
            self._estado.setdefault("datos", {})[paso.clave_dato] = respuesta
        self._estado["paso_actual"] = min(len(PASOS_GENESIS), int(self._estado.get("paso_actual", 0)) + 1)
        if self._estado["paso_actual"] >= len(PASOS_GENESIS):
            self._estado["completado"] = True
        _save_state(self._estado)

    def formatear_mensaje(self, paso: PasoBereshit) -> str:
        datos = defaultdict(str, self._estado.get("datos", {}))
        try:
            return paso.mensaje.format_map(datos)
        except Exception:
            return paso.mensaje

    def necesita_genesis(self) -> bool:
        """Retorna True cuando el protocolo Génesis debe activarse.

        FIX: antes solo miraba 'trigger_gilgul' (reinicio de identidad
        explícito) — en una instalación recién descargada, sin ese flag,
        Génesis nunca se activaba y el flujo caía directo al reto de
        contraseña de Gevurá (ver _gevura_verificar_contrasena), pidiendo
        una contraseña que un usuario nuevo real no tendría forma de saber,
        en vez de preguntarle su nombre. Ahora también se activa cuando el
        protocolo nunca se completó (instalación genuinamente nueva).
        """
        if self._estado.get("trigger_gilgul", False):
            return True
        return not self._estado.get("completado", False)

    def password_configurada(self) -> bool:
        """¿El usuario ya configuró su propia contraseña en Génesis?"""
        return bool(self._estado.get("datos", {}).get("password_hash"))

    def completar(self) -> None:
        """Marca el Génesis como completado.

        FIX: también limpia 'trigger_gilgul'. Antes quedaba en true para
        siempre, así que necesita_genesis() seguía devolviendo True en cada
        arranque y el protocolo de nombre se volvía a ejecutar (visto en un
        log: "Iniciando protocolo Génesis" + "Génesis completado" al boot).
        """
        self._estado["completado"] = True
        self._estado["paso_actual"] = len(PASOS_GENESIS)
        self._estado["trigger_gilgul"] = False
        _save_state(self._estado)

    @property
    def datos(self) -> Dict[str, Any]:
        """Acceso público a los datos del Génesis."""
        return self._estado.get("datos", {})


def establecer_password_usuario(password: str) -> str:
    """Genera salt+hash PBKDF2 para una contraseña elegida por el usuario.

    Retorna 'salt_hex:hash_hex' para guardar como datos['password_hash']
    (vía BereshitGenesis.avanzar(respuesta=...)). Cada instalación obtiene
    su propio salt aleatorio — más seguro que el salt fijo compartido que
    usa el reto de desarrollo heredado (_HASH_EMET en ventana_principal.py).
    """
    salt = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()
    return f"{salt.hex()}:{h}"


def verificar_password_usuario(password: str) -> bool:
    """Verifica contra la contraseña que el usuario configuró en Génesis.

    Retorna False si nunca se configuró una (p.ej. instalaciones antiguas
    que completaron Génesis antes de que existiera este paso) — en ese
    caso el llamador debe caer de vuelta al reto heredado.
    """
    estado = _load_state()
    guardado = estado.get("datos", {}).get("password_hash", "")
    if not guardado or ":" not in guardado:
        return False
    salt_hex, hash_guardado = guardado.split(":", 1)
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()
    return hmac.compare_digest(h, hash_guardado)


def ejecutar_gilgul_boot() -> bool:
    if not _ESTADO_PATH.exists():
        return False
    try:
        estado = json.loads(_ESTADO_PATH.read_text("utf-8"))
    except Exception:
        return False
    return not estado.get("completado", False)


