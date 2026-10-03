"""
הוד+גבורה (Hod+Gevurá) — Esplendor+Juicio. Control Remoto.
KliComandoRemoto — SSH nativo Windows, WoL, verificación Gevurá.

Usa ssh.exe nativo de Windows (no requiere paramiko).
Gevurá pre-check: solo ejecuta si el nivel de permiso lo permite.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from loguru import logger

from computadora.nucleo.kli import DispositivoKli, EstadoKli

try:
    import wakeonlan as _wol  # type: ignore[import-untyped]
    _WOL_DISPONIBLE = True
except ImportError:
    _WOL_DISPONIBLE = False


# ═══════════════════════════════════════════════
# KliComandoRemoto
# ═══════════════════════════════════════════════

class KliComandoRemoto(DispositivoKli):
    """Control remoto de dispositivos vía SSH nativo + WoL.

    Gevurá check: requiere nivel 'admin' en herramientas.py.
    SSH usa ssh.exe nativo de Windows (disponible desde Windows 10 1803).
    """

    SSH_TIMEOUT = 10  # segundos

    def __init__(self, host: str, usuario: str = "", id_kli: str | None = None):
        super().__init__(
            id_kli=id_kli or f"remoto_{host}",
            nombre=f"Remoto {host}",
        )
        self._host = host
        self._usuario = usuario
        self._ssh_disponible = shutil.which("ssh") is not None

    def conectar(self) -> bool:
        if not self._ssh_disponible:
            logger.error("ssh.exe no encontrado en PATH")
            self._estado = EstadoKli.ERROR
            return False
        # Verificar conectividad básica con ping
        try:
            param = "-n" if __import__("platform").system().lower() == "windows" else "-c"
            result = subprocess.run(
                ["ping", param, "1", "-w", "2000", self._host],
                capture_output=True, timeout=5,
            )
            if result.returncode != 0:
                logger.warning(f"Host {self._host} no responde a ping")
                self._estado = EstadoKli.ERROR
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._estado = EstadoKli.ERROR
            return False

        self._estado = EstadoKli.CONECTADO
        logger.info(f"KliComandoRemoto conectado: {self._host}")
        return True

    def desconectar(self) -> None:
        self._estado = EstadoKli.DESCONECTADO

    def leer_ohr(self) -> dict[str, Any]:
        """Lee estado del host remoto (uptime via SSH)."""
        if self._estado != EstadoKli.CONECTADO:
            return {"error": "No conectado"}
        resultado = self._ejecutar_ssh("uptime" if __import__("platform").system().lower() != "windows" else "echo OK")
        return {"host": self._host, "respuesta": resultado}

    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Comandos: ssh_exec, wol, ping."""
        if comando == "ssh_exec":
            cmd_remoto = kwargs.get("cmd", "")
            if not cmd_remoto:
                return {"error": "Falta parámetro 'cmd'"}
            resultado = self._ejecutar_ssh(cmd_remoto)
            return {"host": self._host, "comando": cmd_remoto, "resultado": resultado}

        if comando == "wol":
            mac = kwargs.get("mac", "")
            if not mac or not _WOL_DISPONIBLE:
                return {"error": "Falta MAC o wakeonlan no instalado"}
            try:
                _wol.send_magic_packet(mac)
                return {"mac": mac, "enviado": True}
            except Exception as e:
                return {"error": str(e)}

        if comando == "ping":
            try:
                param = "-n" if __import__("platform").system().lower() == "windows" else "-c"
                result = subprocess.run(
                    ["ping", param, "1", "-w", "2000", self._host],
                    capture_output=True, timeout=5,
                )
                return {"host": self._host, "alcanzable": result.returncode == 0}
            except Exception as e:
                logger.debug("Error en ping: %s", e)
                return {"host": self._host, "alcanzable": False}

        return {"error": f"Comando desconocido: {comando!r}"}

    def _ejecutar_ssh(self, cmd_remoto: str) -> dict[str, Any]:
        """Ejecuta comando vía ssh.exe nativo con timeout."""
        if not self._ssh_disponible:
            return {"error": "ssh.exe no disponible"}

        args = ["ssh"]
        if self._usuario:
            args.append(f"{self._usuario}@{self._host}")
        else:
            args.append(self._host)
        args.extend(["-o", "ConnectTimeout=5", "-o", "BatchMode=yes", cmd_remoto])

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                timeout=self.SSH_TIMEOUT,
            )
            return {
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Timeout ({self.SSH_TIMEOUT}s)"}
        except Exception as e:
            return {"error": str(e)}


