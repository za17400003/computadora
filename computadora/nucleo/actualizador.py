"""
התחדשות (Hit'hadshut) — Renovación Constante. Auto-actualización de dependencias.
FP-023 WI-122: Motor de actualización automática de dependencias de Computadora.
Gestiona: Ollama, Python (pip), Whisper, edge-tts, y dependencias del proyecto.
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional

from loguru import logger

# Raíz del proyecto
_RAIZ = Path(__file__).resolve().parent.parent.parent
_REQUIREMENTS = _RAIZ / "requirements.txt"

# Registro de últimas verificaciones
_DATOS_DIR = _RAIZ / "datos"
_ESTADO_ARCHIVO = _DATOS_DIR / "actualizador_estado.json"


def _cargar_estado() -> dict:
    """Carga el estado persistido del actualizador."""
    try:
        if _ESTADO_ARCHIVO.exists():
            return json.loads(_ESTADO_ARCHIVO.read_text(encoding="utf-8"))
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    return {"ultima_verificacion": 0, "versiones": {}}


def _guardar_estado(estado: dict):
    """Persiste el estado del actualizador."""
    try:
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_ESTADO_ARCHIVO, estado)
    except Exception as e:
        logger.warning(f"No pude guardar estado actualizador: {e}")


def verificar_ollama() -> Optional[str]:
    """Verifica la versión de Ollama instalada."""
    try:
        r = subprocess.run(
            ["ollama", "--version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            creationflags=0x08000000,
        )
        if r.returncode == 0:
            version = r.stdout.strip()
            logger.info(f"Ollama versión: {version}")
            return version
    except Exception as e:
        logger.warning(f"No pude verificar Ollama: {e}")
    return None


def actualizar_pip_paquetes() -> str:
    """Actualiza paquetes de pip según requirements.txt."""
    if not _REQUIREMENTS.exists():
        return "No encontré requirements.txt"

    try:
        r = subprocess.run(
            ["pip", "install", "--upgrade", "-r", str(_REQUIREMENTS)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
            cwd=str(_RAIZ),
            creationflags=0x08000000,
        )
        salida = r.stdout or ""
        if r.returncode == 0:
            logger.info("Dependencias pip actualizadas")
            return f"Dependencias actualizadas correctamente.\n{salida[-500:]}"
        else:
            error = r.stderr or ""
            logger.warning(f"Error actualizando pip: {error[:300]}")
            return f"Error al actualizar: {error[:500]}"
    except subprocess.TimeoutExpired:
        return "Timeout actualizando dependencias (>5 min)"
    except Exception as e:
        return f"Error: {e}"


def verificar_paquetes_desactualizados() -> list[dict]:
    """Lista paquetes pip con actualizaciones disponibles."""
    try:
        r = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
            creationflags=0x08000000,
        )
        if r.returncode == 0 and r.stdout.strip():
            paquetes = json.loads(r.stdout)
            return paquetes
    except Exception as e:
        logger.warning(f"Error verificando paquetes: {e}")
    return []


def verificar_whisper() -> Optional[str]:
    """Verifica versión de faster-whisper."""
    try:
        r = subprocess.run(
            ["pip", "show", "faster-whisper"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            creationflags=0x08000000,
        )
        if r.returncode == 0:
            for linea in r.stdout.splitlines():
                if linea.startswith("Version:"):
                    version = linea.split(":", 1)[1].strip()
                    logger.info(f"faster-whisper versión: {version}")
                    return version
    except Exception as e:
        logger.warning(f"Error verificando whisper: {e}")
    return None


def verificar_edge_tts() -> Optional[str]:
    """Verifica versión de edge-tts."""
    try:
        r = subprocess.run(
            ["pip", "show", "edge-tts"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
            creationflags=0x08000000,
        )
        if r.returncode == 0:
            for linea in r.stdout.splitlines():
                if linea.startswith("Version:"):
                    return linea.split(":", 1)[1].strip()
    except Exception as e:
        logger.warning(f"Error verificando edge-tts: {e}")
    return None


class ActualizadorGolem:
    """Motor de auto-actualización de Computadora.
    
    Verifica periódicamente las versiones de dependencias clave
    y puede actualizar automáticamente con permiso del usuario.
    """

    INTERVALO_CHECK_HORAS = 24  # Verificar cada 24h

    def __init__(self):
        self._estado = _cargar_estado()
        self._ultimo_reporte: str = ""

    def necesita_verificacion(self) -> bool:
        """True si ha pasado suficiente tiempo desde la última verificación."""
        ultima = self._estado.get("ultima_verificacion", 0)
        horas_pasadas = (time.time() - ultima) / 3600
        return horas_pasadas >= self.INTERVALO_CHECK_HORAS

    def verificar_todo(self) -> str:
        """Ejecuta verificación completa de todas las dependencias."""
        reporte_partes = ["═══ Hit'hadshut — Verificación de Dependencias ═══\n"]

        # Ollama
        v_ollama = verificar_ollama()
        self._estado.setdefault("versiones", {})["ollama"] = v_ollama or "no detectado"
        reporte_partes.append(f"• Ollama: {v_ollama or 'no detectado'}")

        # Whisper
        v_whisper = verificar_whisper()
        self._estado["versiones"]["faster-whisper"] = v_whisper or "no detectado"
        reporte_partes.append(f"• faster-whisper: {v_whisper or 'no detectado'}")

        # edge-tts
        v_tts = verificar_edge_tts()
        self._estado["versiones"]["edge-tts"] = v_tts or "no detectado"
        reporte_partes.append(f"• edge-tts: {v_tts or 'no detectado'}")

        # Paquetes desactualizados
        desactualizados = verificar_paquetes_desactualizados()
        if desactualizados:
            reporte_partes.append(f"\n⚠ {len(desactualizados)} paquetes con actualización disponible:")
            for pkg in desactualizados[:10]:
                nombre = pkg.get("name", "?")
                actual = pkg.get("version", "?")
                nueva = pkg.get("latest_version", "?")
                reporte_partes.append(f"  - {nombre}: {actual} → {nueva}")
            if len(desactualizados) > 10:
                reporte_partes.append(f"  ... y {len(desactualizados) - 10} más")
        else:
            reporte_partes.append("\n✓ Todas las dependencias están al día")

        self._estado["ultima_verificacion"] = time.time()
        _guardar_estado(self._estado)

        self._ultimo_reporte = "\n".join(reporte_partes)
        logger.info(f"Hit'hadshut: verificación completada — {len(desactualizados)} paquetes desactualizados")
        return self._ultimo_reporte

    def actualizar(self) -> str:
        """Ejecuta actualización de dependencias pip."""
        return actualizar_pip_paquetes()

    @property
    def ultimo_reporte(self) -> str:
        return self._ultimo_reporte

    @property
    def versiones(self) -> dict:
        return self._estado.get("versiones", {})


