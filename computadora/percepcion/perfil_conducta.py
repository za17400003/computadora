"""
דרך האדם (Dérej HaAdam) — Camino del Humano. Perfil de conducta.
RF-252: Registra patrones temporales de interacción para construir
un perfil conductual del propietario (horarios, frecuencia, duración,
estado emocional habitual por franja).

Persistencia: datos/perfil_conducta.json
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parents[2] / "datos"
_PERFIL_PATH = _DATOS_DIR / "perfil_conducta.json"

# Franjas horarias del día
_FRANJAS = {
    "madrugada": (0, 6),
    "mañana": (6, 12),
    "tarde": (12, 18),
    "noche": (18, 24),
}


def _franja_actual(hora: int) -> str:
    for nombre, (inicio, fin) in _FRANJAS.items():
        if inicio <= hora < fin:
            return nombre
    return "noche"


class PerfilConducta:
    """Acumula y analiza patrones de interacción del propietario."""

    def __init__(self) -> None:
        self._interacciones: list[dict[str, Any]] = []
        self._resumen: dict[str, Any] = {}
        self._cargar()

    def _cargar(self) -> None:
        if _PERFIL_PATH.exists():
            try:
                data = json.loads(_PERFIL_PATH.read_text("utf-8"))
                self._interacciones = data.get("interacciones", [])
                self._resumen = data.get("resumen", {})
                # Limitar historial a últimas 500 interacciones
                if len(self._interacciones) > 500:
                    self._interacciones = self._interacciones[-500:]
                logger.info(f"Perfil de conducta cargado: {len(self._interacciones)} interacciones")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error cargando perfil de conducta: {e}")

    def _guardar(self) -> None:
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "interacciones": self._interacciones[-500:],
            "resumen": self._resumen,
        }
        _PERFIL_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def registrar_interaccion(
        self,
        tipo: str = "voz",
        duracion_seg: float = 0.0,
        emocion: str = "calma",
        n_palabras: int = 0,
    ) -> None:
        """Registra una interacción del propietario."""
        ts = time.time()
        lt = time.localtime(ts)
        entrada = {
            "ts": ts,
            "tipo": tipo,
            "hora": lt.tm_hour,
            "dia_semana": lt.tm_wday,  # 0=lunes
            "franja": _franja_actual(lt.tm_hour),
            "duracion_seg": round(duracion_seg, 1),
            "emocion": emocion,
            "n_palabras": n_palabras,
        }
        self._interacciones.append(entrada)
        self._actualizar_resumen()
        self._guardar()

    def _actualizar_resumen(self) -> None:
        """Calcula estadísticas del perfil."""
        if not self._interacciones:
            self._resumen = {}
            return

        # Conteo por franja
        por_franja: dict[str, int] = defaultdict(int)
        # Emoción predominante por franja
        emociones_franja: dict[str, list[str]] = defaultdict(list)
        # Interacciones por día de la semana
        por_dia: dict[int, int] = defaultdict(int)
        duraciones: list[float] = []

        for ix in self._interacciones:
            franja = ix.get("franja", "noche")
            por_franja[franja] += 1
            emociones_franja[franja].append(ix.get("emocion", "calma"))
            por_dia[ix.get("dia_semana", 0)] += 1
            dur = ix.get("duracion_seg", 0.0)
            if dur > 0:
                duraciones.append(dur)

        # Franja más activa
        franja_favorita = max(por_franja, key=por_franja.get) if por_franja else "noche"  # type: ignore[arg-type]

        # Emoción predominante por franja
        emocion_por_franja = {}
        for franja, emociones in emociones_franja.items():
            if emociones:
                conteo: dict[str, int] = defaultdict(int)
                for e in emociones:
                    conteo[e] += 1
                emocion_por_franja[franja] = max(conteo, key=conteo.get)  # type: ignore[arg-type]

        self._resumen = {
            "total_interacciones": len(self._interacciones),
            "franja_favorita": franja_favorita,
            "por_franja": dict(por_franja),
            "por_dia_semana": dict(por_dia),
            "emocion_por_franja": emocion_por_franja,
            "duracion_promedio_seg": round(sum(duraciones) / len(duraciones), 1) if duraciones else 0.0,
        }

    def obtener_resumen(self) -> dict[str, Any]:
        """Retorna resumen del perfil conductual."""
        return dict(self._resumen)

    def obtener_contexto_actual(self) -> dict[str, Any]:
        """Retorna contexto conductual para el momento actual.

        Útil para inyectar en el system prompt de Ollama.
        """
        lt = time.localtime()
        franja = _franja_actual(lt.tm_hour)
        emocion_habitual = self._resumen.get("emocion_por_franja", {}).get(franja, "calma")
        actividad_franja = self._resumen.get("por_franja", {}).get(franja, 0)
        total = self._resumen.get("total_interacciones", 0)

        return {
            "franja_actual": franja,
            "emocion_habitual_franja": emocion_habitual,
            "actividad_franja": actividad_franja,
            "total_interacciones": total,
            "es_franja_favorita": franja == self._resumen.get("franja_favorita"),
        }


