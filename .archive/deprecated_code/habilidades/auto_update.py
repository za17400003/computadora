"""
התחדשות (Hit'hadshut) — Renovación. Auto-actualización de dependencias.
RF-86: Computadora verifica y actualiza sus dependencias críticas.

Yesod (יסוד) — Fundamento actualizado.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_UPDATE_LOG = _DATOS_DIR / "update_log.json"


def _leer_log() -> list[dict]:
    if _UPDATE_LOG.exists():
        try:
            return json.loads(_UPDATE_LOG.read_text(encoding="utf-8"))
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return []
    return []


def _guardar_log(entries: list[dict]) -> None:
    _DATOS_DIR.mkdir(parents=True, exist_ok=True)
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(_UPDATE_LOG, entries[-100:])


def verificar_lollama() -> dict[str, Any]:
    """Verifica versión de Ollama y modelos disponibles."""
    resultado = {"servicio": "lollama", "disponible": False, "version": None, "modelos": []}
    try:
        r = subprocess.run(
            ["ollama", "version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            creationflags=0x08000000,
        )
        if r.returncode == 0:
            resultado["version"] = r.stdout.strip()
            resultado["disponible"] = True
    except Exception as e:
        logger.debug(f"Ollama version check: {e}")

    try:
        r = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            creationflags=0x08000000,
        )
        if r.returncode == 0:
            lineas = r.stdout.strip().split("\n")
            modelos = [ln.split()[0] for ln in lineas[1:] if ln.strip()]
            resultado["modelos"] = modelos
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    return resultado


def verificar_pip_packages() -> list[dict]:
    """Verifica paquetes pip con actualizaciones disponibles."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
            creationflags=0x08000000,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception as e:
        logger.debug(f"pip outdated check: {e}")
    return []


def verificar_dependencias() -> str:
    """Genera reporte de estado de dependencias de la Computadora."""
    partes = []

    # Ollama
    lollama = verificar_lollama()
    if lollama["disponible"]:
        partes.append(f"Ollama: {lollama['version']} — {len(lollama['modelos'])} modelo(s)")
    else:
        partes.append("Ollama: no disponible")

    # Pip packages
    outdated = verificar_pip_packages()
    if outdated:
        nombres = [f"{p['name']} ({p['version']}→{p['latest_version']})" for p in outdated[:5]]
        partes.append(f"Paquetes con actualización: {', '.join(nombres)}")
        if len(outdated) > 5:
            partes.append(f"  ...y {len(outdated) - 5} más")
    else:
        partes.append("Paquetes pip: todos al día")

    return "\n".join(partes)


def actualizar_modelo_lollama(modelo: str) -> str:
    """Actualiza un modelo de Ollama."""
    logger.info(f"Hit'hadshut: descargando modelo Ollama '{modelo}'")
    try:
        r = subprocess.run(
            ["curl", "-X", "POST", f"http://localhost:1234/pull", "-H", "Content-Type: application/json", "-d", f'{{"model": "{modelo}"}}'],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
            creationflags=0x08000000,
        )
        resultado = f"Modelo '{modelo}': {'actualizado' if r.returncode == 0 else 'error'}"
        if r.returncode != 0 and r.stderr:
            resultado += f" — {r.stderr.strip()[:200]}"

        _log = _leer_log()
        _log.append({
            "ts": datetime.now().isoformat(),
            "tipo": "lollama_update",
            "modelo": modelo,
            "exito": r.returncode == 0,
            "detalle": resultado,
        })
        _guardar_log(_log)

        return resultado
    except Exception as e:
        return f"Error actualizando '{modelo}': {e}"


def actualizar_pip_packages(paquetes: list[str] | None = None) -> str:
    """Actualiza paquetes pip específicos o todos los desactualizados."""
    if paquetes is None:
        outdated = verificar_pip_packages()
        paquetes = [p["name"] for p in outdated]

    if not paquetes:
        return "No hay paquetes para actualizar."

    resultados = []
    for pkg in paquetes[:10]:  # Límite de seguridad
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                creationflags=0x08000000,
            )
            exito = r.returncode == 0
            resultados.append(f"{'✅' if exito else '❌'} {pkg}")

            _log = _leer_log()
            _log.append({
                "ts": datetime.now().isoformat(),
                "tipo": "pip_upgrade",
                "paquete": pkg,
                "exito": exito,
            })
            _guardar_log(_log)
        except Exception as e:
            resultados.append(f"❌ {pkg}: {e}")

    return "Actualización de paquetes:\n" + "\n".join(resultados)


