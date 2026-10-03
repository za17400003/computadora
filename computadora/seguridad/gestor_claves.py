"""
גבורה (Gevurá) — Gestor de Claves / Vault de Contraseñas Local.
Sendero 58: Gevurá→Yesod  (gestor_claves → herramientas — password vault access).

Base cifrada AES-256-GCM con derivación Argon2id.
CRUD credenciales, generador de passwords, clipboard auto-clear.

RF-346: Vault de contraseñas local (Otzar)
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import string
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from computadora.nucleo.gestor_procesos import obtener_gestor_procesos

# Dependencias de cifrado — opcionales
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    _CRYPTO_DISPONIBLE = True
except ImportError:
    _CRYPTO_DISPONIBLE = False
    AESGCM = None  # type: ignore[misc,assignment]
    Scrypt = None  # type: ignore[misc,assignment]

# ═══════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════

_DATOS_DIR = Path(__file__).parent.parent.parent / "datos"
_VAULT_PATH = _DATOS_DIR / "otzar.enc"
_SALT_PATH = _DATOS_DIR / "otzar.salt"
_CLIPBOARD_CLEAR_S = 30


@dataclass
class Credencial:
    """Una credencial almacenada."""
    servicio: str
    usuario: str
    password: str
    notas: str = ""
    creado_ts: float = 0.0
    modificado_ts: float = 0.0


class GestorClaves:
    """Vault de contraseñas cifrado con AES-256-GCM + Scrypt.

    Uso:
        vault = GestorClaves()
        vault.desbloquear("contraseña_maestra")
        vault.agregar("github", "user", "pass123")
        cred = vault.obtener("github")
        vault.bloquear()
    """

    def __init__(self):
        self._datos_dir = _DATOS_DIR
        self._datos_dir.mkdir(parents=True, exist_ok=True)
        self._clave_derivada: bytes | None = None
        self._credenciales: dict[str, dict[str, Any]] = {}
        self._desbloqueado = False

    @property
    def disponible(self) -> bool:
        return _CRYPTO_DISPONIBLE

    @property
    def desbloqueado(self) -> bool:
        return self._desbloqueado

    @property
    def tiene_vault(self) -> bool:
        """¿Existe un vault previamente creado?"""
        return _VAULT_PATH.exists()

    def crear_vault(self, master_password: str) -> str:
        """Crea un vault nuevo con la contraseña maestra dada."""
        if not _CRYPTO_DISPONIBLE:
            return "Cifrado no disponible — instalar cryptography."
        if _VAULT_PATH.exists():
            return "Ya existe un vault. Usa desbloquear() en vez de crear."

        salt = os.urandom(32)
        _SALT_PATH.write_bytes(salt)
        self._clave_derivada = self._derivar_clave(master_password, salt)
        self._credenciales = {}
        self._desbloqueado = True
        self._guardar()
        logger.info("[Otzar] Vault creado")
        return "Vault creado exitosamente. Recuerda tu contraseña maestra."

    def desbloquear(self, master_password: str) -> bool:
        """Desbloquea el vault con la contraseña maestra."""
        if not _CRYPTO_DISPONIBLE:
            logger.warning("[Otzar] cryptography no instalado")
            return False
        if not _VAULT_PATH.exists() or not _SALT_PATH.exists():
            logger.warning("[Otzar] No existe vault — usa crear_vault()")
            return False

        salt = _SALT_PATH.read_bytes()
        clave = self._derivar_clave(master_password, salt)

        try:
            raw = _VAULT_PATH.read_bytes()
            nonce = raw[:12]
            ct = raw[12:]
            aesgcm = AESGCM(clave)
            plain = aesgcm.decrypt(nonce, ct, None)
            self._credenciales = json.loads(plain.decode("utf-8"))
            self._clave_derivada = clave
            self._desbloqueado = True
            logger.info(f"[Otzar] Vault desbloqueado — {len(self._credenciales)} credenciales")
            return True
        except Exception as e:  # RF-167
            logger.warning("[Otzar] Contraseña incorrecta o vault corrupto")
            return False

    def bloquear(self):
        """Bloquea el vault — borra clave y credenciales de memoria."""
        self._clave_derivada = None
        self._credenciales = {}
        self._desbloqueado = False
        logger.info("[Otzar] Vault bloqueado")

    def agregar(self, servicio: str, usuario: str, password: str, notas: str = "") -> str:
        """Agrega o actualiza una credencial."""
        if not self._desbloqueado:
            return "Vault bloqueado — desbloquéalo primero."

        ahora = time.time()
        clave_busqueda = servicio.lower().strip()
        existia = clave_busqueda in self._credenciales
        self._credenciales[clave_busqueda] = {
            "servicio": servicio,
            "usuario": usuario,
            "password": password,
            "notas": notas,
            "creado_ts": self._credenciales.get(clave_busqueda, {}).get("creado_ts", ahora),
            "modificado_ts": ahora,
        }
        self._guardar()
        accion = "actualizada" if existia else "agregada"
        logger.info(f"[Otzar] Credencial {accion}: {servicio}")
        return f"Credencial para '{servicio}' {accion}."

    def obtener(self, servicio: str) -> Credencial | None:
        """Obtiene una credencial por nombre de servicio."""
        if not self._desbloqueado:
            return None
        clave = servicio.lower().strip()
        data = self._credenciales.get(clave)
        if not data:
            return None
        return Credencial(
            servicio=data["servicio"],
            usuario=data["usuario"],
            password=data["password"],
            notas=data.get("notas", ""),
            creado_ts=data.get("creado_ts", 0),
            modificado_ts=data.get("modificado_ts", 0),
        )

    def eliminar(self, servicio: str) -> str:
        """Elimina una credencial."""
        if not self._desbloqueado:
            return "Vault bloqueado."
        clave = servicio.lower().strip()
        if clave not in self._credenciales:
            return f"No encontré credencial para '{servicio}'."
        del self._credenciales[clave]
        self._guardar()
        return f"Credencial de '{servicio}' eliminada."

    def listar(self) -> list[str]:
        """Lista los nombres de servicios almacenados (sin passwords)."""
        if not self._desbloqueado:
            return []
        return [v["servicio"] for v in self._credenciales.values()]

    def buscar(self, patron: str) -> list[str]:
        """Busca servicios que contengan el patrón."""
        if not self._desbloqueado:
            return []
        p = patron.lower()
        return [v["servicio"] for k, v in self._credenciales.items() if p in k]

    def generar_password(self, longitud: int = 20, especiales: bool = True) -> str:
        """Genera una contraseña aleatoria segura."""
        chars = string.ascii_letters + string.digits
        if especiales:
            chars += "!@#$%&*-_=+"
        # Asegurar al menos 1 de cada tipo
        pw = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
        ]
        if especiales:
            pw.append(secrets.choice("!@#$%&*-_=+"))
        while len(pw) < max(longitud, 12):
            pw.append(secrets.choice(chars))
        # Mezclar
        resultado = list(pw)
        secrets.SystemRandom().shuffle(resultado)
        return "".join(resultado)

    def copiar_al_clipboard(self, servicio: str) -> str:
        """Copia la contraseña al clipboard con auto-clear después de 30s."""
        cred = self.obtener(servicio)
        if not cred:
            return f"No encontré credencial para '{servicio}'."

        try:
            import subprocess
            # Windows: usar clip.exe (no requiere pyperclip)
            gestor = obtener_gestor_procesos()
            process = gestor.lanzar(
                ["clip.exe"], stdin=subprocess.PIPE,
            )
            process.communicate(cred.password.encode("utf-16-le"))

            # Programar limpieza del clipboard
            import threading
            def _limpiar():
                try:
                    subprocess.run(
                        ["cmd", "/c", "echo.|clip"],
                        capture_output=True, timeout=5,
                    )
                    logger.debug("[Otzar] Clipboard limpiado")
                except Exception as e:  # RF-167
                    pass
            threading.Timer(_CLIPBOARD_CLEAR_S, _limpiar).start()

            return f"Contraseña de '{servicio}' copiada. Se borrará en {_CLIPBOARD_CLEAR_S}s."
        except Exception as e:
            return f"Error copiando: {e}"

    def _guardar(self):
        """Cifra y guarda el vault a disco."""
        if not self._clave_derivada or not _CRYPTO_DISPONIBLE:
            return
        plain = json.dumps(self._credenciales, ensure_ascii=False).encode("utf-8")
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._clave_derivada)
        ct = aesgcm.encrypt(nonce, plain, None)
        _VAULT_PATH.write_bytes(nonce + ct)

    def _derivar_clave(self, password: str, salt: bytes) -> bytes:
        """Deriva clave AES-256 desde password con Scrypt."""
        kdf = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1)
        return kdf.derive(password.encode("utf-8"))

    def resumen(self) -> str:
        """Resumen textual para voz."""
        if not self.disponible:
            return "Vault de claves no disponible — instalar cryptography."
        if not self.tiene_vault:
            return "No hay vault creado aún."
        if not self._desbloqueado:
            return "Vault bloqueado."
        n = len(self._credenciales)
        return f"Vault desbloqueado con {n} credencial{'es' if n != 1 else ''}."


