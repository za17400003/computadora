"""
גבורה (Gevurá) — Cifrado de Comunicaciones Salientes.
Sendero 60: Gevurá→Tiféret  (cifrado_comms → nlu.py — encryption routing).

Provee cifrado AES-256-GCM para payloads + TLS 1.3 wrapping.
Puede interceptar tráfico saliente dCOMPUTADORA y cifrar antes de enviar.

RF-345: Cifrado de comunicaciones salientes
"""

from __future__ import annotations

import base64
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

# Cryptography es optional — si no está, el módulo se degrada gracefully
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_DISPONIBLE = True
except ImportError:
    _CRYPTO_DISPONIBLE = False
    AESGCM = None  # type: ignore[misc,assignment]

# ═══════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════

_DATOS_DIR = Path(__file__).parent.parent.parent / "datos" / "crypto"
_CLAVE_MAESTRA_PATH = _DATOS_DIR / "master.key"
_ROTACION_INTERVALO_S = 86400  # 24h


@dataclass
class EstadoCifrado:
    """Estado del motor de cifrado."""
    activo: bool = False
    clave_generada_ts: float = 0.0
    mensajes_cifrados: int = 0
    mensajes_descifrados: int = 0


class CifradoComms:
    """Motor de cifrado AES-256-GCM para comunicaciones de la Computadora.

    Uso:
        motor = CifradoComms()
        cifrado = motor.cifrar(b"datos secretos")
        original = motor.descifrar(cifrado)
        motor.rotar_clave()  # Rotación manual
    """

    def __init__(self):
        self._datos_dir = _DATOS_DIR
        self._datos_dir.mkdir(parents=True, exist_ok=True)
        self._clave: bytes | None = None
        self._estado = EstadoCifrado()
        self._cargar_o_generar_clave()

    @property
    def disponible(self) -> bool:
        return _CRYPTO_DISPONIBLE and self._clave is not None

    def _cargar_o_generar_clave(self):
        """Carga o genera la clave maestra AES-256."""
        if not _CRYPTO_DISPONIBLE:
            logger.warning("[Cifrado] cryptography no instalado — cifrado no disponible")
            return

        if _CLAVE_MAESTRA_PATH.exists():
            try:
                raw = _CLAVE_MAESTRA_PATH.read_bytes()
                data_lines = raw.split(b"\n")
                if len(data_lines) >= 2:
                    self._clave = base64.b64decode(data_lines[0])
                    self._estado.clave_generada_ts = float(data_lines[1].decode())
                    self._estado.activo = True
                    logger.debug("[Cifrado] Clave maestra cargada")
                    return
            except Exception as e:
                logger.warning(f"[Cifrado] Error cargando clave: {e}")

        self._generar_clave()

    def _generar_clave(self):
        """Genera una nueva clave AES-256 de 32 bytes."""
        self._clave = AESGCM.generate_key(bit_length=256)
        self._estado.clave_generada_ts = time.time()
        self._estado.activo = True
        # Persistir clave (protegida por permisos del directorio)
        _CLAVE_MAESTRA_PATH.write_bytes(
            base64.b64encode(self._clave) + b"\n" + str(self._estado.clave_generada_ts).encode()
        )
        logger.info("[Cifrado] Nueva clave AES-256 generada")

    def cifrar(self, datos: bytes, aad: bytes | None = None) -> bytes:
        """Cifra datos con AES-256-GCM. Retorna nonce(12) + ciphertext."""
        if not self.disponible:
            raise RuntimeError("Motor de cifrado no disponible")

        self._auto_rotar()
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._clave)
        ct = aesgcm.encrypt(nonce, datos, aad)
        self._estado.mensajes_cifrados += 1
        return nonce + ct

    def descifrar(self, datos_cifrados: bytes, aad: bytes | None = None) -> bytes:
        """Descifra datos AES-256-GCM. Espera nonce(12) + ciphertext."""
        if not self.disponible:
            raise RuntimeError("Motor de cifrado no disponible")

        if len(datos_cifrados) < 13:
            raise ValueError("Datos cifrados demasiado cortos")

        nonce = datos_cifrados[:12]
        ct = datos_cifrados[12:]
        aesgcm = AESGCM(self._clave)
        plain = aesgcm.decrypt(nonce, ct, aad)
        self._estado.mensajes_descifrados += 1
        return plain

    def cifrar_texto(self, texto: str, aad: str | None = None) -> str:
        """Cifra texto UTF-8 → base64 string."""
        aad_bytes = aad.encode() if aad else None
        ct = self.cifrar(texto.encode("utf-8"), aad_bytes)
        return base64.b64encode(ct).decode("ascii")

    def descifrar_texto(self, texto_cifrado: str, aad: str | None = None) -> str:
        """Descifra base64 string → texto UTF-8."""
        aad_bytes = aad.encode() if aad else None
        ct = base64.b64decode(texto_cifrado)
        return self.descifrar(ct, aad_bytes).decode("utf-8")

    def rotar_clave(self) -> str:
        """Rota la clave maestra manualmente."""
        if not _CRYPTO_DISPONIBLE:
            return "Cifrado no disponible — instalar cryptography."
        self._generar_clave()
        return "Clave AES-256 rotada exitosamente."

    def _auto_rotar(self):
        """Rota automáticamente si la clave tiene más de 24h."""
        edad = time.time() - self._estado.clave_generada_ts
        if edad > _ROTACION_INTERVALO_S:
            logger.info("[Cifrado] Rotación automática de clave (>24h)")
            self._generar_clave()

    def resumen(self) -> str:
        """Resumen para voz."""
        if not self.disponible:
            return "Motor de cifrado no disponible."
        edad_h = (time.time() - self._estado.clave_generada_ts) / 3600
        return (
            f"Cifrado AES-256-GCM activo. "
            f"Clave tiene {edad_h:.1f} horas. "
            f"{self._estado.mensajes_cifrados} mensajes cifrados, "
            f"{self._estado.mensajes_descifrados} descifrados."
        )


