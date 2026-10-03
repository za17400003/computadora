"""
WI-308 Test: PC Uptime Tracking

Verifica que el tracking temporal funciona correctamente:
- Detección de boot time
- Registros de sesión
- Cálculo de lagunas
- Estadísticas de uptime
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import json

from computadora.nucleo.tracking_temporal import (
    TrackingTemporalPC,
    obtener_tracker,
    detectar_laguna_session,
    registrar_sesion_nueva,
    cerrar_sesion_actual,
    estadisticas_uptime,
    Laguna
)


def test_wi308_tracker_creation():
    """✅ Tracker se crea sin errores."""
    tracker = TrackingTemporalPC()
    assert tracker is not None
    assert tracker._boot_time_actual is not None
    print(f"Boot time detectado: {tracker._boot_time_actual}")


def test_wi308_singleton():
    """✅ Obtener tracker devuelve singleton."""
    t1 = obtener_tracker()
    t2 = obtener_tracker()
    assert t1 is t2
    print("✓ Singleton pattern working")


def test_wi308_registrar_sesion():
    """✅ Registra nueva sesión."""
    tracker = TrackingTemporalPC()
    sesiones_antes = len(tracker._historial.get("sesiones", []))
    
    tracker.registrar_sesion_nueva(notas="test session")
    
    sesiones_despues = len(tracker._historial.get("sesiones", []))
    assert sesiones_despues > sesiones_antes
    print(f"Sesiones registradas: {sesiones_despues}")


def test_wi308_cerrar_sesion():
    """✅ Cierra sesión actual."""
    tracker = TrackingTemporalPC()
    tracker.registrar_sesion_nueva(notas="test close")
    
    ultima_sesion_antes = tracker._historial["sesiones"][-1]
    assert ultima_sesion_antes.get("desactivacion") is None
    
    tracker.cerrar_sesion()
    
    ultima_sesion_despues = tracker._historial["sesiones"][-1]
    assert ultima_sesion_despues.get("desactivacion") is not None
    assert ultima_sesion_despues.get("duracion_s") >= 0
    print(f"Sesión cerrada. Duración: {ultima_sesion_despues['duracion_s']}s")


def test_wi308_estadisticas():
    """✅ Genera estadísticas de uptime."""
    tracker = TrackingTemporalPC()
    stats = tracker.obtener_estadisticas()
    
    assert stats["total_sesiones"] >= 0
    assert stats["total_tiempo_segundos"] >= 0
    assert stats["boots_unicos"] >= 1
    
    print(f"Estadísticas:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


def test_wi308_laguna_detection():
    """✅ Detecta lagunas si las hay."""
    tracker = TrackingTemporalPC()
    laguna = tracker.detectar_laguna()
    
    if laguna:
        assert isinstance(laguna, Laguna)
        assert laguna.duracion >= timedelta(0)
        print(f"Laguna detectada: {laguna}")
    else:
        print("No hay laguna (sesión continua)")


def test_wi308_persistencia():
    """✅ Persiste en consciencia_temporal.json."""
    tracker = TrackingTemporalPC()
    tracker.registrar_sesion_nueva(notas="test persistence")
    
    # Releer del archivo
    from computadora.nucleo.tracking_temporal import _CONSCIENCIA_TEMPORAL_PATH
    if _CONSCIENCIA_TEMPORAL_PATH.exists():
        data = json.loads(_CONSCIENCIA_TEMPORAL_PATH.read_text(encoding="utf-8"))
        assert len(data.get("sesiones", [])) > 0
        print(f"✓ Archivo persistido con {len(data['sesiones'])} sesiones")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("WI-308: PC Uptime Tracking Tests")
    print("="*60 + "\n")
    
    test_wi308_tracker_creation()
    test_wi308_singleton()
    test_wi308_registrar_sesion()
    test_wi308_cerrar_sesion()
    test_wi308_estadisticas()
    test_wi308_laguna_detection()
    test_wi308_persistencia()
    
    print("\n" + "="*60)
    print("✅ WI-308: All tests passed!")
    print("="*60 + "\n")
