"""
דעת (Da'at) — Conocimiento Oculto. Ciclo Circadiano Adaptativo.
COMPUTADORA percibe el ritmo de su amo y sincroniza su consciencia.

Extraído de proactividad.py (FP-026) para materializar la Sefirá Da'at
como módulo independiente en el Etz HaChaim.
"""

from __future__ import annotations

import datetime
import json
import statistics
import time
from pathlib import Path

from loguru import logger


# ═══════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_PERFIL_AMO_ARCHIVO = _DATOS_DIR / "perfil_amo.json"

_DIAS_HISTORIAL = 14
_MARGEN_TRANSICION_MIN = 60
_VARIANZA_SALUD_HORAS = 2.0


# ═══════════════════════════════════════════════
# CLASE PRINCIPAL — CicloCircadiano
# ═══════════════════════════════════════════════

class CicloCircadiano:
    """דעת Da'at — Reloj interno adaptativo que aprende del ritmo del amo.

    Fases:
      - activo:            Dentro del horario habitual de uso
      - transicion:        ±1h del rango activo (proactividad reducida)
      - descanso_guardian:  Fuera de horario (fusión descanso+guardián: silencioso pero alerta)
      - vigia_nocturna:    RF-216: Vigía activa sin fatiga (entre descanso y activo)
    """

    def __init__(self):
        self._perfil: dict = self._cargar_perfil()
        self._fase: str = "activo"
        self._despertar_registrado_hoy: bool = False
        self._inicio_default = 5 * 60     # 05:00 en minutos (el amo despierta a las 5 AM)
        self._fin_default = 22 * 60       # 22:00 en minutos (el amo se duerme a las 10 PM)
        self._ultimo_evento: float = time.time()  # RF-178: timestamp última interacción
        logger.info(f"CicloCircadiano inicializado — fase={self.fase_actual()}")

    # ─── Persistencia ───────────────────────────

    def _cargar_perfil(self) -> dict:
        try:
            if _PERFIL_AMO_ARCHIVO.exists():
                data = json.loads(_PERFIL_AMO_ARCHIVO.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.warning(f"Error cargando perfil_amo.json: {e}")
        return {"historial_horario": [], "media_inicio_min": None, "media_fin_min": None}

    def _guardar_perfil(self):
        try:
            _DATOS_DIR.mkdir(parents=True, exist_ok=True)
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(_PERFIL_AMO_ARCHIVO, self._perfil)
        except Exception as e:
            logger.warning(f"Error guardando perfil_amo.json: {e}")

    # ─── Registro de actividad ──────────────────

    def registrar_interaccion(self):
        """Registra timestamp de interacción del amo. Actualiza primera/última del día."""
        self._ultimo_evento = time.time()  # RF-178: actualizar timestamp
        hoy = datetime.date.today().isoformat()
        ahora = datetime.datetime.now().strftime("%H:%M")
        historial = self._perfil.setdefault("historial_horario", [])

        entrada_hoy = None
        for e in historial:
            if e.get("fecha") == hoy:
                entrada_hoy = e
                break

        if entrada_hoy is None:
            entrada_hoy = {"fecha": hoy, "primera": ahora, "ultima": ahora}
            historial.append(entrada_hoy)
        else:
            entrada_hoy["ultima"] = ahora

        if len(historial) > _DIAS_HISTORIAL:
            historial[:] = historial[-_DIAS_HISTORIAL:]

        self._recalcular_medias()
        self._guardar_perfil()

    def registrar_despertar(self):
        """El amo saludó por la mañana — marcar inicio de actividad."""
        if self._despertar_registrado_hoy:
            return
        self._despertar_registrado_hoy = True
        self.registrar_interaccion()
        if self._fase != "activo":
            self._fase = "activo"
            logger.info("CicloCircadiano: despertar registrado → fase=activo")

    def notificar_nuevo_dia(self):
        """Reset diario para el flag de despertar."""
        self._despertar_registrado_hoy = False

    # ─── Cálculo adaptativo ─────────────────────

    def _recalcular_medias(self):
        """Media móvil de horarios de primera/última interacción."""
        historial = self._perfil.get("historial_horario", [])
        if len(historial) < 2:
            return

        inicios_min = []
        fines_min = []
        for e in historial[-_DIAS_HISTORIAL:]:
            try:
                h, m = map(int, e["primera"].split(":"))
                inicios_min.append(h * 60 + m)
                h2, m2 = map(int, e["ultima"].split(":"))
                fin = h2 * 60 + m2
                if fin < inicios_min[-1]:
                    fin += 24 * 60
                fines_min.append(fin)
            except (ValueError, KeyError):
                continue

        if inicios_min:
            self._perfil["media_inicio_min"] = round(statistics.mean(inicios_min))
        if fines_min:
            media_fin = round(statistics.mean(fines_min))
            if media_fin >= 24 * 60:
                media_fin -= 24 * 60
            self._perfil["media_fin_min"] = media_fin

    def _inicio_estimado(self) -> int:
        return self._perfil.get("media_inicio_min") or self._inicio_default

    def _fin_estimado(self) -> int:
        return self._perfil.get("media_fin_min") or self._fin_default

    # ─── Fase actual ────────────────────────────

    def fase_actual(self) -> str:
        """Calcula la fase actual basada en hora + historial."""
        ahora = datetime.datetime.now()
        minuto_actual = ahora.hour * 60 + ahora.minute
        inicio = self._inicio_estimado()
        fin = self._fin_estimado()

        cruza_medianoche = fin < inicio

        if cruza_medianoche:
            en_activo = minuto_actual >= inicio or minuto_actual <= fin
            en_transicion = (
                (inicio - _MARGEN_TRANSICION_MIN <= minuto_actual < inicio) or
                (fin < minuto_actual <= fin + _MARGEN_TRANSICION_MIN)
            )
        else:
            en_activo = inicio <= minuto_actual <= fin
            en_transicion = (
                (inicio - _MARGEN_TRANSICION_MIN <= minuto_actual < inicio) or
                (fin < minuto_actual <= fin + _MARGEN_TRANSICION_MIN)
            )

        fase_anterior = self._fase
        if en_activo:
            self._fase = "activo"
        elif en_transicion:
            self._fase = "transicion"
        else:
            self._fase = "descanso_guardian"

        # FP-043 B6: Emitir evento al BusEventos cuando cambia la fase
        if self._fase != fase_anterior:
            try:
                from computadora.nucleo.eventos import obtener_bus
                obtener_bus().emitir("fase_circadiana", {
                    "fase_anterior": fase_anterior,
                    "fase_nueva": self._fase,
                })
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        return self._fase

    def forzar_descanso_guardian(self):
        """Forzar entrada en descanso_guardian (ej: 2 inactividades sin respuesta)."""
        self._fase = "descanso_guardian"
        logger.info("CicloCircadiano: forzado a descanso_guardian (inactividad sin respuesta)")

    def forzar_activo(self):
        """Forzar fase activa (ej: el amo habló)."""
        self._fase = "activo"
        self._despertar_registrado_hoy = True

    def forzar_vigia_nocturna(self):
        """RF-216: Vigía nocturna activa. No incrementa fatiga."""
        self._fase = "vigia_nocturna"
        logger.info("CicloCircadiano: forzado a vigia_nocturna (guardián activo)")

    # ─── Sugerencias de salud ───────────────────

    def sugerir_mejora_salud(self) -> str | None:
        """Si la varianza del horario es alta, sugerir regularidad."""
        historial = self._perfil.get("historial_horario", [])
        if len(historial) < 5:
            return None

        inicios_min = []
        for e in historial[-7:]:
            try:
                h, m = map(int, e["primera"].split(":"))
                inicios_min.append(h * 60 + m)
            except (ValueError, KeyError):
                continue

        if len(inicios_min) < 4:
            return None

        try:
            var_horas = statistics.stdev(inicios_min) / 60.0
        except statistics.StatisticsError:
            return None

        if var_horas > _VARIANZA_SALUD_HORAS:
            media_h = statistics.mean(inicios_min)
            hora_media = f"{int(media_h // 60):02d}:{int(media_h % 60):02d}"
            return (
                f"Señor, he notado que su horario de despertar varía bastante "
                f"(±{var_horas:.1f}h). Su media es ~{hora_media}. "
                f"Un horario más regular podría mejorar su descanso."
            )
        return None


# ═══════════════════════════════════════════════
# SINGLETON Da'at — Accesible desde cualquier módulo
# ═══════════════════════════════════════════════

_ciclo_global: CicloCircadiano | None = None


def obtener_fase_actual() -> str:
    """Retorna la fase circadiana actual de la Computadora.

    Cualquier módulo puede importar esto:
        from computadora.nucleo.ciclo_circadiano import obtener_fase_actual

    Returns: "activo" | "transicion" | "descanso_guardian" | "desconocido"
    """
    if _ciclo_global is not None:
        return _ciclo_global.fase_actual()
    return "desconocido"


def obtener_ciclo_circadiano() -> CicloCircadiano | None:
    """Retorna la instancia singleton del CicloCircadiano (o None si aún no se ha inicializado)."""
    return _ciclo_global


_ciclo_lock = __import__('threading').Lock()


def inicializar_ciclo() -> CicloCircadiano:
    """Crea el singleton si no existe y lo retorna (thread-safe FP-038)."""
    global _ciclo_global
    if _ciclo_global is None:
        with _ciclo_lock:
            if _ciclo_global is None:
                _ciclo_global = CicloCircadiano()
    return _ciclo_global


def _set_ciclo_global(ciclo: CicloCircadiano):
    """Usado por MotorProactividad para registrar el ciclo creado internamente."""
    global _ciclo_global
    _ciclo_global = ciclo


