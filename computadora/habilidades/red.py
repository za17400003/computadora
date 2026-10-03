"""
הוד (Hod) — Esplendor. Adaptador de Red.
KliRed — Escaneo ARP, ping, WoL. Sensor de red de la Computadora.

Dependencias opcionales:
  - scapy: para ARP scan (requiere admin en Windows)
  - wakeonlan: para Wake-on-LAN
  Sin ellas, funciona con ping básico.
"""

from __future__ import annotations

import ipaddress
import platform
import re
import socket
import subprocess
import warnings
from typing import Any

from loguru import logger

from computadora.nucleo.kli import DispositivoKli, EstadoKli

# Importaciones opcionales
# Silenciar warnings de Scapy (libpcap en Windows)
warnings.filterwarnings("ignore", category=UserWarning, module="scapy")
warnings.filterwarnings("ignore", message=".*libpcap.*")

_SCAPY_DISPONIBLE = False

def _cargar_scapy() -> bool:
    """Carga scapy solo cuando sea necesario y seguro."""
    global _SCAPY_DISPONIBLE
    if _SCAPY_DISPONIBLE:
        return True
    if platform.system().lower() == "windows":
        logger.debug("Scapy deshabilitado en Windows para evitar WinPcap Bad Memory Block")
        return False
    try:
        from scapy.all import ARP, Ether, srp  # type: ignore[import-untyped]
        globals()["ARP"] = ARP
        globals()["Ether"] = Ether
        globals()["srp"] = srp
        _SCAPY_DISPONIBLE = True
        return True
    except Exception as e:
        logger.debug(f"Scapy import falló: {e}")
        _SCAPY_DISPONIBLE = False
        return False

try:
    import wakeonlan as _wol  # type: ignore[import-untyped]
    _WOL_DISPONIBLE = True
except ImportError:
    _WOL_DISPONIBLE = False


# ═══════════════════════════════════════════════
# UTILIDADES INTERNAS
# ═══════════════════════════════════════════════

def _ping(ip: str, timeout: int = 2) -> bool:
    """Ping a una IP. Retorna True si responde."""
    # Validar IP antes de pasar a subprocess (OWASP A03:2021)
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        logger.warning(f"IP inválida rechazada: {ip!r}")
        return False
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", param, "1", "-w", str(timeout * 1000), ip],
            capture_output=True, timeout=timeout + 3,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _arp_scan(red: str = "192.168.1.0/24", timeout: int = 3) -> list[dict[str, str]]:
    """ARP scan con scapy. Requiere admin."""
    if not _cargar_scapy():
        return []
    # Validar formato de red (OWASP A03:2021)
    try:
        ipaddress.ip_network(red, strict=False)
    except ValueError:
        logger.warning(f"Red inválida rechazada: {red!r}")
        return []
    try:
        # Silenciar warnings de Scapy durante el scan
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", message=".*libpcap.*")
            paquete = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=red)
            resultado, _ = srp(paquete, timeout=timeout, verbose=False)
        dispositivos = []
        for _, recibido in resultado:
            ip = recibido.psrc
            mac = recibido.hwsrc
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except (socket.herror, socket.gaierror):
                hostname = ""
            dispositivos.append({"ip": ip, "mac": mac, "hostname": hostname})
        return dispositivos
    except Exception as e:
        # Silenciar warning: solo log debug si falta admin
        logger.debug(f"ARP scan falló (¿sin admin?): {e}")
        return []


def _enviar_wol(mac: str) -> bool:
    """Envía paquete Wake-on-LAN."""
    if not _WOL_DISPONIBLE:
        logger.warning("wakeonlan no instalado")
        return False
    mac_limpia = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(mac_limpia) != 12:
        logger.error(f"MAC inválida: {mac}")
        return False
    try:
        _wol.send_magic_packet(mac)
        logger.info(f"WoL enviado a {mac}")
        return True
    except Exception as e:
        logger.error(f"WoL falló: {e}")
        return False


# ═══════════════════════════════════════════════
# KliRed — Adaptador de Red
# ═══════════════════════════════════════════════

class KliRed(DispositivoKli):
    """Sensor de red local de la Computadora.

    Capacidades:
      - ARP scan (con scapy) o listado básico
      - Ping a IPs específicas
      - Wake-on-LAN
    """

    def __init__(self, red: str = "192.168.1.0/24"):
        super().__init__(id_kli="red_local", nombre="Red Local")
        self._red = red
        self._dispositivos_cache: list[dict[str, str]] = []

    def conectar(self) -> bool:
        self._estado = EstadoKli.CONECTADO
        logger.info(f"KliRed conectado (red={self._red})")
        return True

    def desconectar(self) -> None:
        self._dispositivos_cache.clear()
        self._estado = EstadoKli.DESCONECTADO

    def leer_ohr(self) -> dict[str, Any]:
        """Escanea la red y retorna dispositivos encontrados."""
        dispositivos = _arp_scan(self._red)
        if dispositivos:
            self._dispositivos_cache = dispositivos
            return {
                "tipo": "scan_arp",
                "dispositivos": dispositivos,
                "total": len(dispositivos),
                "scapy": True,
            }
        return {
            "tipo": "sin_scan",
            "dispositivos": [],
            "total": 0,
            "scapy": False,
            "nota": "scapy no disponible o sin permisos admin",
        }

    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Comandos: ping, wol, scan."""
        if comando == "ping":
            ip = kwargs.get("ip", "")
            if not ip:
                return {"error": "Falta parámetro 'ip'"}
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                return {"error": f"IP inválida: {ip!r}"}
            ok = _ping(ip)
            return {"ip": ip, "alcanzable": ok}

        if comando == "wol":
            mac = kwargs.get("mac", "")
            if not mac:
                return {"error": "Falta parámetro 'mac'"}
            ok = _enviar_wol(mac)
            return {"mac": mac, "enviado": ok}

        if comando == "scan":
            return self.leer_ohr()

        return {"error": f"Comando desconocido: {comando!r}"}

    @property
    def dispositivos_cache(self) -> list[dict[str, str]]:
        return list(self._dispositivos_cache)


