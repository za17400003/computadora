"""
שומר הבית (Shomer HaBayit) — Guardián del Hogar.
RF-368: Detecta si Computadora opera desde la red del hogar o una red foránea.

Almacena una huella de la red hogar (gateway, subnet, SSID si disponible).
Cuando la red actual NO coincide con la huella, activa modo stealth:
  - Restringe servidores a localhost-only
  - Emite alerta al propietario
  - Bloquea servicios expuestos a 0.0.0.0

Sendero 60: Gevurá→Maljut (seguridad → manifestación restringida).
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parents[2] / "datos"
_HUELLA_HOGAR = _DATOS_DIR / "red_hogar.json"

# WI-172: Backoff para evitar spam cuando el registro falla (sin gateway)
_registro_fallido_ts: float = 0.0
_REGISTRO_BACKOFF: float = 300.0  # 5 minutos entre reintentos


def _ejecutar_cmd(cmd: list[str], timeout: int = 5) -> str:
    """Ejecuta un comando y retorna stdout. Silencia errores."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.debug(f"Shomer HaBayit cmd error ({cmd[0]}): {e}")
        return ""


def obtener_huella_red_actual() -> dict[str, Any]:
    """Captura huella de la red actual: gateway, subnet, SSID."""
    huella: dict[str, Any] = {
        "gateway": "",
        "ssid": "",
        "subnet": "",
        "adaptador": "",
    }

    # Gateway por defecto (Windows)
    salida = _ejecutar_cmd(["cmd", "/c", "ipconfig"])
    if salida:
        # Buscar gateway
        gw_match = re.search(r"Default Gateway[.\s]*:\s*([\d.]+)", salida)
        if gw_match:
            huella["gateway"] = gw_match.group(1)
        # Buscar subnet mask
        sm_match = re.search(r"Subnet Mask[.\s]*:\s*([\d.]+)", salida)
        if sm_match:
            huella["subnet"] = sm_match.group(1)
        # Buscar adaptador activo
        adapter_match = re.findall(
            r"(Wireless LAN adapter|Ethernet adapter)\s+([^:]+):", salida
        )
        if adapter_match:
            huella["adaptador"] = adapter_match[0][1].strip()

    # SSID (WiFi)
    salida_wifi = _ejecutar_cmd(["cmd", "/c", "netsh", "wlan", "show", "interfaces"])
    if salida_wifi:
        ssid_match = re.search(r"SSID\s*:\s*(.+)", salida_wifi)
        if ssid_match:
            ssid = ssid_match.group(1).strip()
            # Evitar capturar BSSID
            if not ssid.startswith("BSSID"):
                huella["ssid"] = ssid

    return huella


def registrar_hogar() -> dict[str, Any]:
    """Registra la red actual como red del hogar. Debe ejecutarse una vez."""
    huella = obtener_huella_red_actual()
    if not huella["gateway"]:
        # WI-274: Solo warn la primera vez, debug en reintentos
        _ya_sentinel = _HUELLA_HOGAR.exists()
        (logger.debug if _ya_sentinel else logger.warning)(
            "Shomer HaBayit: no se detectó gateway — no se puede registrar hogar"
        )
        # WI-172: Escribir sentinel incompleto para evitar retry spam
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        _HUELLA_HOGAR.write_text(
            json.dumps({**huella, "incompleto": True}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return huella
    _DATOS_DIR.mkdir(parents=True, exist_ok=True)
    _HUELLA_HOGAR.write_text(json.dumps(huella, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Shomer HaBayit: red del hogar registrada — GW={huella['gateway']}, SSID={huella['ssid']}")
    return huella


def _cargar_huella_hogar() -> dict[str, Any] | None:
    """Carga la huella del hogar desde disco."""
    if not _HUELLA_HOGAR.exists():
        return None
    try:
        return json.loads(_HUELLA_HOGAR.read_text("utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Shomer HaBayit: error leyendo huella hogar: {e}")
        return None


def es_red_hogar() -> bool:
    """Retorna True si la red actual coincide con la huella del hogar.

    Criterios de coincidencia (al menos 2 de 3 deben coincidir):
    - Gateway idéntico
    - SSID idéntico (si ambos disponibles)
    - Subnet idéntica
    Si no hay huella registrada, retorna True y registra automáticamente.
    """
    hogar = _cargar_huella_hogar()
    if hogar is None or hogar.get("incompleto"):
        global _registro_fallido_ts
        # WI-172/WI-274: Backoff exponencial — silenciar spam cuando no hay gateway
        elapsed = time.time() - _registro_fallido_ts
        if _registro_fallido_ts > 0 and elapsed < _REGISTRO_BACKOFF:
            return True  # Asumir hogar durante backoff (silencioso)
        logger.debug("Shomer HaBayit: sin huella registrada — reintentando registro de red hogar")
        resultado = registrar_hogar()
        if not resultado.get("gateway"):
            _registro_fallido_ts = time.time()
        return True

    actual = obtener_huella_red_actual()
    coincidencias = 0
    checks = 0

    # Gateway (peso mayor)
    if hogar.get("gateway") and actual.get("gateway"):
        checks += 1
        if hogar["gateway"] == actual["gateway"]:
            coincidencias += 1

    # SSID
    if hogar.get("ssid") and actual.get("ssid"):
        checks += 1
        if hogar["ssid"] == actual["ssid"]:
            coincidencias += 1

    # Subnet
    if hogar.get("subnet") and actual.get("subnet"):
        checks += 1
        if hogar["subnet"] == actual["subnet"]:
            coincidencias += 1

    # Si no hay suficientes checks, confiar en gateway solo
    if checks == 0:
        logger.warning("Shomer HaBayit: sin datos para comparar — asumiendo hogar")
        return True

    en_hogar = coincidencias >= min(2, checks)
    if not en_hogar:
        logger.warning(
            f"Shomer HaBayit: RED FORÁNEA DETECTADA — "
            f"coincidencias={coincidencias}/{checks}, "
            f"GW actual={actual.get('gateway')}, SSID actual={actual.get('ssid')}"
        )
    else:
        logger.debug(f"Shomer HaBayit: en red del hogar ({coincidencias}/{checks} coincidencias)")

    return en_hogar


def obtener_estado_red() -> dict[str, Any]:
    """Retorna estado completo para diagnóstico: huella hogar + actual + coincidencia."""
    hogar = _cargar_huella_hogar()
    actual = obtener_huella_red_actual()
    return {
        "hogar_registrado": hogar is not None,
        "huella_hogar": hogar or {},
        "red_actual": actual,
        "es_red_hogar": es_red_hogar(),
    }


