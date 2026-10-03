"""
רוח האדם (Ruaj HaAdam) — Espíritu del Humano. Detección de emoción por voz.
RF-250: Heurísticas de pitch (F0), energía RMS y velocidad de habla.
Clasifica en 5 estados: calma, alegría, estrés, enojo, tristeza.

Sin dependencias ML — usa scipy para pitch y numpy para energía.

Dependencia opcional:
  - scipy: para autocorrelación (extracción de pitch)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

try:
    from scipy.signal import correlate
    _SCIPY_DISPONIBLE = True
except ImportError:
    correlate = None  # type: ignore[assignment]
    _SCIPY_DISPONIBLE = False

# Rangos de pitch (Hz) para voz masculina adulta (ajustar si es necesario)
_PITCH_BAJO = 100    # Hz — voz relajada/triste
_PITCH_MEDIO = 150   # Hz — normal
_PITCH_ALTO = 220    # Hz — excitado/enojado

# Rangos de energía RMS normalizados (0-1)
_RMS_BAJO = 0.02
_RMS_ALTO = 0.08

# Velocidad de habla (sílabas/seg aprox, estimado por palabras/duración)
_VELOCIDAD_LENTA = 2.0   # palabras/seg
_VELOCIDAD_RAPIDA = 4.5


def _extraer_pitch(audio: np.ndarray, sr: int) -> float:
    """Extrae F0 (pitch fundamental) por autocorrelación.

    Retorna frecuencia en Hz, o 0.0 si no se puede determinar.
    """
    if not _SCIPY_DISPONIBLE or len(audio) < sr // 4:
        return 0.0

    # Autocorrelación
    corr = correlate(audio, audio, mode="full")
    corr = corr[len(corr) // 2:]

    # Buscar primer pico después del lag mínimo (pitch máx ~400 Hz)
    lag_min = sr // 400
    lag_max = sr // 70   # pitch mín ~70 Hz

    if lag_max > len(corr):
        lag_max = len(corr)
    if lag_min >= lag_max:
        return 0.0

    segmento = corr[lag_min:lag_max]
    if len(segmento) == 0:
        return 0.0

    pico = int(np.argmax(segmento)) + lag_min
    if pico == 0:
        return 0.0

    return float(sr / pico)


def _extraer_rms(audio: np.ndarray) -> float:
    """Energía RMS normalizada."""
    if len(audio) == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))
    # Normalizar asumiendo audio float32 en [-1, 1]
    return min(rms, 1.0)


def analizar_emocion_voz(
    audio: np.ndarray,
    sr: int = 16000,
    n_palabras: int = 0,
    duracion_seg: float = 0.0,
) -> dict[str, Any]:
    """Analiza la emoción del hablante a partir del audio crudo.

    Args:
        audio: numpy array float32, mono, normalizado [-1, 1]
        sr: sample rate
        n_palabras: número de palabras transcritas (para velocidad)
        duracion_seg: duración del segmento en segundos

    Returns:
        dict con: emocion (str), confianza (float 0-1), detalles (dict)
    """
    pitch = _extraer_pitch(audio, sr)
    rms = _extraer_rms(audio)

    # Velocidad de habla
    velocidad = 0.0
    if duracion_seg > 0.3 and n_palabras > 0:
        velocidad = n_palabras / duracion_seg

    # Clasificación por heurísticas combinadas
    emocion = "calma"
    confianza = 0.4  # base

    if pitch > 0:
        if pitch > _PITCH_ALTO and rms > _RMS_ALTO:
            if velocidad > _VELOCIDAD_RAPIDA:
                emocion = "enojo"
                confianza = 0.7
            else:
                emocion = "alegría"
                confianza = 0.6
        elif pitch > _PITCH_ALTO and rms <= _RMS_ALTO:
            emocion = "estrés"
            confianza = 0.55
        elif pitch < _PITCH_BAJO and rms < _RMS_BAJO:
            emocion = "tristeza"
            confianza = 0.55
        elif pitch < _PITCH_BAJO and rms > _RMS_ALTO:
            emocion = "calma"
            confianza = 0.5
        else:
            emocion = "calma"
            confianza = 0.45

    detalles = {
        "pitch_hz": round(pitch, 1),
        "rms": round(rms, 4),
        "velocidad_palabras_seg": round(velocidad, 2),
        "scipy_disponible": _SCIPY_DISPONIBLE,
    }

    logger.debug(f"Emoción voz detectada: {emocion} (confianza={confianza:.2f}, pitch={pitch:.0f}Hz, rms={rms:.4f})")
    return {"emocion": emocion, "confianza": confianza, "detalles": detalles}


