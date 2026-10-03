"""
WI-308: PC Uptime Tracking Between Sessions

Detecta y registra cuando la PC se reinicia, calculando "lagunas" 
(interrupciones) entre sesiones de Computadora.

Funcionalidad:
1. Obtiene boot time real del sistema (psutil.boot_time())
2. Compara con última sesión registrada
3. Detecta si PC se reinició → laguna temporal
4. Registra en consciencia_temporal.json
5. Expone API para consultas de continuidad

Uso:
    tracker = TrackingTemporalPC()
    laguna = tracker.detectar_laguna()
    if laguna:
        print(f"PC se reinició hace {laguna.duration}. Memoria puede estar incompleta.")
    
    tracker.registrar_sesion_nueva()
"""

from __future__ import annotations

import datetime
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import psutil
from loguru import logger


_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_CONSCIENCIA_TEMPORAL_PATH = _DATOS_DIR / "consciencia_temporal.json"


@dataclass
class Laguna:
    """Período de tiempo donde Computadora estuvo offline."""
    inicio: datetime.datetime  # Última actividad antes del reinicio
    fin: datetime.datetime      # Primer reinicio detectado
    duracion: datetime.timedelta
    causa: str  # "reinicio_pc" | "apagado_pc" | "crash"
    
    def __str__(self) -> str:
        horas = self.duracion.total_seconds() / 3600
        return f"{self.causa}: {horas:.1f} horas ({self.duracion})"


class TrackingTemporalPC:
    """Rastreador de continuidad temporal entre sesiones."""
    
    def __init__(self):
        self._boot_time_actual = self._obtener_boot_time()
        self._historial = self._cargar_historial()
        self._ultima_sesion = self._obtener_ultima_sesion()
        self._laguna_detectada: Optional[Laguna] = None
        
        # Al inicializar, detectar si PC se reinició
        if self._boot_time_cambio():
            self._procesar_reinicio()
    
    def _obtener_boot_time(self) -> datetime.datetime:
        """Obtiene timestamp de último boot de la PC."""
        try:
            boot_timestamp = psutil.boot_time()
            return datetime.datetime.fromtimestamp(boot_timestamp)
        except Exception as e:
            logger.error(f"Error obteniendo boot_time: {e}")
            # Fallback: asumir que se inició hace poco
            return datetime.datetime.now() - datetime.timedelta(seconds=60)
    
    def _cargar_historial(self) -> dict:
        """Carga consciencia_temporal.json."""
        try:
            if _CONSCIENCIA_TEMPORAL_PATH.exists():
                data = json.loads(
                    _CONSCIENCIA_TEMPORAL_PATH.read_text(encoding="utf-8")
                )
                return data
        except Exception as e:
            logger.warning(f"Error cargando consciencia_temporal.json: {e}")
        
        # Default: historial vacío
        return {"sesiones": [], "boot_pc_historico": []}
    
    def _obtener_ultima_sesion(self) -> Optional[dict]:
        """Obtiene la última sesión registrada."""
        sesiones = self._historial.get("sesiones", [])
        if sesiones:
            return sesiones[-1]
        return None
    
    def _boot_time_cambio(self) -> bool:
        """¿El boot time actual es diferente del registrado?"""
        if not self._ultima_sesion:
            return False
        
        boot_registrado_str = self._ultima_sesion.get("boot_pc")
        if not boot_registrado_str:
            return True
        
        try:
            boot_registrado = datetime.datetime.fromisoformat(boot_registrado_str)
            # Permitir pequeño margen (5 minutos) por reloj del sistema
            diff = abs((self._boot_time_actual - boot_registrado).total_seconds())
            return diff > 300
        except Exception:
            return True
    
    def _procesar_reinicio(self) -> None:
        """Procesa detección de reinicio de PC."""
        if not self._ultima_sesion:
            logger.info("WI-308: Primera sesión registrada, no hay laguna")
            return
        
        desactivacion_str = self._ultima_sesion.get("desactivacion")
        if not desactivacion_str:
            # Última sesión fue forzada (crash o shutdown sin cierre graceful)
            causa = "crash_o_shutdown_no_graceful"
            fin_laguna = self._boot_time_actual
        else:
            try:
                fin_laguna_dt = datetime.datetime.fromisoformat(desactivacion_str)
                fin_laguna = fin_laguna_dt
                causa = "reinicio_o_apagado_pc"
            except Exception:
                fin_laguna = self._boot_time_actual
                causa = "error_parseando_desactivacion"
        
        inicio_laguna = self._boot_time_actual
        duracion = fin_laguna - inicio_laguna
        
        self._laguna_detectada = Laguna(
            inicio=inicio_laguna,
            fin=fin_laguna,
            duracion=duracion,
            causa=causa
        )
        
        logger.warning(f"WI-308: Laguna detectada: {self._laguna_detectada}")
    
    def detectar_laguna(self) -> Optional[Laguna]:
        """
        Retorna la laguna detectada al inicializar, si existe.
        Usa esto para notificar al usuario o ajustar comportamiento post-reinicio.
        """
        return self._laguna_detectada
    
    def registrar_sesion_nueva(self, notas: Optional[str] = None) -> None:
        """Registra activación de nueva sesión."""
        ahora = datetime.datetime.now()
        nueva_sesion = {
            "activacion": ahora.isoformat(),
            "desactivacion": None,
            "duracion_s": 0,
            "boot_pc": self._boot_time_actual.isoformat(),
            "notas": notas or ""
        }
        
        sesiones = self._historial.get("sesiones", [])
        sesiones.append(nueva_sesion)
        self._historial["sesiones"] = sesiones
        
        # Actualizar histórico de boots únicos
        boot_historico = self._historial.get("boot_pc_historico", [])
        boot_str = self._boot_time_actual.isoformat()
        if boot_str not in boot_historico:
            boot_historico.append(boot_str)
        self._historial["boot_pc_historico"] = boot_historico
        
        self._guardar_historial()
        logger.info(f"WI-308: Nueva sesión registrada @ {ahora.isoformat()}")
    
    def cerrar_sesion(self) -> None:
        """Cierra la sesión actual (se llama en shutdown)."""
        sesiones = self._historial.get("sesiones", [])
        if sesiones and sesiones[-1].get("desactivacion") is None:
            ahora = datetime.datetime.now()
            inicio_str = sesiones[-1]["activacion"]
            sesiones[-1]["desactivacion"] = ahora.isoformat()
            
            # Calcular duración
            try:
                inicio = datetime.datetime.fromisoformat(inicio_str)
                duracion_s = int((ahora - inicio).total_seconds())
                sesiones[-1]["duracion_s"] = duracion_s
            except Exception:
                pass
            
            self._historial["sesiones"] = sesiones
            self._guardar_historial()
            logger.info(f"WI-308: Sesión cerrada @ {ahora.isoformat()}")
    
    def obtener_estadisticas(self) -> dict:
        """Estadísticas de uptime."""
        sesiones = self._historial.get("sesiones", [])
        total_sesiones = len(sesiones)
        total_tiempo_s = sum(s.get("duracion_s", 0) for s in sesiones)
        
        boots_unicos = len(self._historial.get("boot_pc_historico", []))
        
        return {
            "total_sesiones": total_sesiones,
            "total_tiempo_segundos": total_tiempo_s,
            "total_tiempo_horas": total_tiempo_s / 3600,
            "boots_unicos": boots_unicos,
            "ultima_activacion": sesiones[-1].get("activacion") if sesiones else None,
            "boot_actual": self._boot_time_actual.isoformat(),
            "laguna_detectada": bool(self._laguna_detectada),
            "laguna_descripcion": str(self._laguna_detectada) if self._laguna_detectada else None
        }
    
    def _guardar_historial(self) -> None:
        """Persiste consciencia_temporal.json."""
        try:
            _DATOS_DIR.mkdir(parents=True, exist_ok=True)
            _CONSCIENCIA_TEMPORAL_PATH.write_text(
                json.dumps(self._historial, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error guardando consciencia_temporal.json: {e}")


# Singleton global
_tracker_global: Optional[TrackingTemporalPC] = None


def obtener_tracker() -> TrackingTemporalPC:
    """Obtiene o crea el tracker singleton."""
    global _tracker_global
    if _tracker_global is None:
        _tracker_global = TrackingTemporalPC()
    return _tracker_global


def detectar_laguna_session() -> Optional[Laguna]:
    """Conveniencia: detecta laguna en la sesión actual."""
    return obtener_tracker().detectar_laguna()


def registrar_sesion_nueva(notas: Optional[str] = None) -> None:
    """Conveniencia: registra nueva sesión."""
    obtener_tracker().registrar_sesion_nueva(notas)


def cerrar_sesion_actual() -> None:
    """Conveniencia: cierra sesión (llamar en shutdown)."""
    obtener_tracker().cerrar_sesion()


def estadisticas_uptime() -> dict:
    """Conveniencia: obtiene estadísticas."""
    return obtener_tracker().obtener_estadisticas()
