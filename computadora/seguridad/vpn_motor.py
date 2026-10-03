"""
גבורה (Gevurá) — Motor VPN WireGuard local.
Sendero 59: Gevurá→Yesod  (vpn_motor → red — kill switch).

Wrapper sobre WireGuard CLI:
  - Crear / destruir túnel
  - Kill Switch vía WFP (Windows Filtering Platform)
  - Split Tunneling (excluir IPs locales)
  - Stats de tráfico

Dependencias externas:
  - WireGuard instalado + wg.exe en PATH (o en C:\\Program Files\\WireGuard\\)
  - Archivo de config .conf en datos/wg/

RF-344: Motor VPN WireGuard local
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

# ═══════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════

_DATOS_DIR = Path(__file__).parent.parent.parent / "datos" / "wg"
_CONFIG_PATH = _DATOS_DIR / "computadora_vpn.conf"
_STATE_PATH = _DATOS_DIR / "vpn_state.json"

# Buscar wg.exe en ubicaciones conocidas
_WG_PATHS = [
    Path("C:/Program Files/WireGuard/wg.exe"),
    Path("C:/Program Files (x86)/WireGuard/wg.exe"),
]


def _find_wg() -> Path | None:
    """Encuentra el ejecutable wg.exe."""
    # Primero intentar PATH
    import shutil
    wg = shutil.which("wg")
    if wg:
        return Path(wg)
    for p in _WG_PATHS:
        if p.exists():
            return p
    return None


def _find_wireguard() -> Path | None:
    """Encuentra wireguard.exe (servicio/tunnel manager)."""
    import shutil
    wg = shutil.which("wireguard")
    if wg:
        return Path(wg)
    for base in _WG_PATHS:
        candidate = base.parent / "wireguard.exe"
        if candidate.exists():
            return candidate
    return None


# ═══════════════════════════════════════════════
# ESTADO
# ═══════════════════════════════════════════════

@dataclass
class VpnEstado:
    """Estado del túnel VPN."""
    activa: bool = False
    interfaz: str = "computadora_vpn"
    endpoint: str = ""
    bytes_tx: int = 0
    bytes_rx: int = 0
    ultimo_handshake: float = 0.0
    kill_switch: bool = False
    desde_ts: float = 0.0


class VpnMotor:
    """Motor VPN WireGuard para el Computadora.

    Uso:
        motor = VpnMotor()
        motor.activar()                # Levanta el túnel
        motor.desactivar()             # Baja el túnel
        motor.esta_activa() -> bool
        motor.stats() -> VpnEstado
        motor.activar_kill_switch()    # Bloquea todo tráfico fuera del túnel
    """

    def __init__(self):
        self._wg = _find_wg()
        self._wireguard = _find_wireguard()
        self._estado = VpnEstado()
        self._datos_dir = _DATOS_DIR
        self._datos_dir.mkdir(parents=True, exist_ok=True)
        self._cargar_estado()

    @property
    def disponible(self) -> bool:
        """WireGuard está instalado y hay config."""
        return self._wg is not None and _CONFIG_PATH.exists()

    def _cargar_estado(self):
        """Carga estado persistente."""
        if _STATE_PATH.exists():
            try:
                data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
                self._estado.kill_switch = data.get("kill_switch", False)
            except (json.JSONDecodeError, OSError):
                pass

    def _guardar_estado(self):
        """Persiste estado."""
        _STATE_PATH.write_text(
            json.dumps({"kill_switch": self._estado.kill_switch}, ensure_ascii=False),
            encoding="utf-8",
        )

    def activar(self) -> str:
        """Levanta el túnel VPN WireGuard."""
        if not self.disponible:
            msg = "WireGuard no disponible (wg.exe no encontrado o falta configuración)"
            logger.warning(f"[VPN] {msg}")
            return msg

        if self.esta_activa():
            return "La VPN ya está activa."

        try:
            # WireGuard service: instalar y arrancar el túnel
            result = subprocess.run(
                [str(self._wireguard or "wireguard"), "/installtunnelservice",
                 str(_CONFIG_PATH)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            )
            if result.returncode != 0:
                # Fallback: usar wg-quick si está disponible
                result = subprocess.run(
                    ["wg-quick", "up", str(_CONFIG_PATH)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                )
            if result.returncode == 0:
                self._estado.activa = True
                self._estado.desde_ts = time.time()
                logger.info("[VPN] Túnel WireGuard activado")
                if self._estado.kill_switch:
                    self._aplicar_kill_switch()
                return "VPN activada. Todo el tráfico pasa por el túnel cifrado."
            else:
                error = result.stderr[:200] if result.stderr else "Error desconocido"
                logger.error(f"[VPN] Error activando: {error}")
                return f"Error activando VPN: {error}"

        except FileNotFoundError:
            return "wireguard.exe no encontrado — ¿está instalado WireGuard?"
        except subprocess.TimeoutExpired:
            return "Timeout activando VPN — el servicio no respondió."
        except Exception as e:
            logger.error(f"[VPN] Excepción: {e}")
            return f"Error: {e}"

    def desactivar(self) -> str:
        """Baja el túnel VPN."""
        if not self.esta_activa():
            return "La VPN no está activa."

        try:
            interfaz = self._estado.interfaz
            result = subprocess.run(
                [str(self._wireguard or "wireguard"), "/uninstalltunnelservice", interfaz],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            )
            if result.returncode != 0:
                subprocess.run(
                    ["wg-quick", "down", str(_CONFIG_PATH)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
                )
            self._estado.activa = False
            self._estado.desde_ts = 0.0
            if self._estado.kill_switch:
                self._remover_kill_switch()
            logger.info("[VPN] Túnel WireGuard desactivado")
            return "VPN desactivada."
        except Exception as e:
            logger.error(f"[VPN] Error desactivando: {e}")
            return f"Error desactivando VPN: {e}"

    def esta_activa(self) -> bool:
        """Verifica si el túnel WireGuard está activo consultando wg show."""
        if not self._wg:
            return False
        try:
            result = subprocess.run(
                [str(self._wg), "show", self._estado.interfaz],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            )
            activa = result.returncode == 0 and "interface" in result.stdout.lower()
            self._estado.activa = activa
            return activa
        except Exception as e:  # RF-167
            self._estado.activa = False
            return False

    def stats(self) -> VpnEstado:
        """Obtiene estadísticas del túnel activo."""
        if not self.esta_activa():
            return self._estado

        try:
            result = subprocess.run(
                [str(self._wg), "show", self._estado.interfaz, "dump"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    # Línea de peer: public_key, preshared_key, endpoint, allowed_ips,
                    #                latest_handshake, transfer_rx, transfer_tx, ...
                    parts = lines[1].split("\t")
                    if len(parts) >= 7:
                        self._estado.endpoint = parts[2]
                        self._estado.bytes_rx = int(parts[5]) if parts[5].isdigit() else 0
                        self._estado.bytes_tx = int(parts[6]) if parts[6].isdigit() else 0
                        hs = parts[4]
                        self._estado.ultimo_handshake = float(hs) if hs.isdigit() else 0.0
        except Exception as e:
            logger.debug(f"[VPN] Error leyendo stats: {e}")

        return self._estado

    def activar_kill_switch(self) -> str:
        """Activa Kill Switch: bloquea todo tráfico que no pase por el túnel."""
        self._estado.kill_switch = True
        self._guardar_estado()
        if self.esta_activa():
            self._aplicar_kill_switch()
            return "Kill Switch activado — sin VPN no hay internet."
        return "Kill Switch configurado — se activará al conectar la VPN."

    def desactivar_kill_switch(self) -> str:
        """Desactiva Kill Switch."""
        self._estado.kill_switch = False
        self._guardar_estado()
        self._remover_kill_switch()
        return "Kill Switch desactivado."

    def _aplicar_kill_switch(self):
        """Aplica reglas WFP para bloquear tráfico fuera del túnel."""
        try:
            # Usar netsh para crear regla de firewall que bloquea todo excepto WireGuard
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 "name=GolemVPN_KillSwitch", "dir=out", "action=block",
                 "enable=yes", "profile=any", "localport=any",
                 "remoteport=any", "protocol=any"],
                capture_output=True, timeout=10,
            )
            # Permitir tráfico por la interfaz WireGuard
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "add", "rule",
                 "name=GolemVPN_Allow", "dir=out", "action=allow",
                 "enable=yes", "profile=any",
                 f"localip=any", "protocol=any",
                 "interfacetype=any"],  # WireGuard interface
                capture_output=True, timeout=10,
            )
            logger.info("[VPN] Kill Switch WFP aplicado")
        except Exception as e:
            logger.error(f"[VPN] Error aplicando Kill Switch: {e}")

    def _remover_kill_switch(self):
        """Remueve las reglas WFP del Kill Switch."""
        try:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule",
                 "name=GolemVPN_KillSwitch"],
                capture_output=True, timeout=10,
            )
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule",
                 "name=GolemVPN_Allow"],
                capture_output=True, timeout=10,
            )
            logger.info("[VPN] Kill Switch WFP removido")
        except Exception as e:
            logger.debug(f"[VPN] Error removiendo Kill Switch: {e}")

    def split_tunneling_excluir(self, ips: list[str]) -> str:
        """Configura Split Tunneling: excluye IPs del túnel (ej: LAN local)."""
        # Validar IPs
        import ipaddress
        validas = []
        for ip in ips:
            try:
                ipaddress.ip_network(ip, strict=False)
                validas.append(ip)
            except ValueError:
                logger.warning(f"[VPN] IP inválida para split tunneling: {ip!r}")

        if not validas:
            return "No se proporcionaron IPs válidas."

        try:
            for net in validas:
                subprocess.run(
                    ["route", "add", net, "0.0.0.0"],
                    capture_output=True, timeout=5,
                )
            logger.info(f"[VPN] Split tunneling: excluidas {validas}")
            return f"Split tunneling: {len(validas)} redes excluidas del túnel."
        except Exception as e:
            return f"Error configurando split tunneling: {e}"

    def resumen(self) -> str:
        """Resumen textual del estado VPN para voz."""
        if not self.disponible:
            return "Motor VPN no disponible — WireGuard no está instalado."
        if not self.esta_activa():
            return "VPN desactivada."
        st = self.stats()
        uptime = int(time.time() - st.desde_ts) if st.desde_ts else 0
        mins = uptime // 60
        mb_rx = st.bytes_rx / (1024 * 1024)
        mb_tx = st.bytes_tx / (1024 * 1024)
        ks = " Kill Switch activo." if st.kill_switch else ""
        return (
            f"VPN activa hace {mins} minutos. "
            f"Recibidos {mb_rx:.1f} MB, enviados {mb_tx:.1f} MB. "
            f"Endpoint: {st.endpoint}.{ks}"
        )


