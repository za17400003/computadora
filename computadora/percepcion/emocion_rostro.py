"""
תפארת הפרצוף (Tiferet HaPertsuf) — Belleza del Rostro.
RF-251: Detección de emoción facial usando deepface o FER.
7 emociones Ekman: alegría, tristeza, enojo, miedo, sorpresa, asco, neutral.

Dependencia opcional:
  - deepface: análisis facial profundo (pip install deepface)
  - fer: Facial Expression Recognition (pip install fer) — alternativa ligera
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from loguru import logger

# Intentar importar backends en orden de preferencia
_BACKEND: str | None = None

try:
    from fer import FER
    _detector_fer: FER | None = None
    _BACKEND = "fer"
except ImportError:
    FER = None  # type: ignore[assignment,misc]

if _BACKEND is None:
    try:
        from deepface import DeepFace
        _BACKEND = "deepface"
    except ImportError:
        DeepFace = None  # type: ignore[assignment,misc]

# Mapeo de emociones inglés → español
_EMOCION_MAP = {
    "happy": "alegría",
    "sad": "tristeza",
    "angry": "enojo",
    "fear": "miedo",
    "surprise": "sorpresa",
    "disgust": "asco",
    "neutral": "neutral",
}

# Intervalo mínimo entre análisis (segundos) — FER es costoso en CPU
_INTERVALO_MIN = 3.0


class AnalizadorEmocionRostro:
    """Analiza emociones faciales a partir de frames BGR."""

    def __init__(self) -> None:
        self._ultimo_analisis: float = 0.0
        self._ultima_emocion: dict[str, Any] = {"emocion": "neutral", "confianza": 0.0}
        self._fer_detector: Any = None
        if _BACKEND == "fer" and FER is not None:
            try:
                self._fer_detector = FER(mtcnn=False)  # mtcnn=False → usa Haar (más rápido)
                logger.info("AnalizadorEmocionRostro inicializado con FER (Haar)")
            except Exception as e:
                logger.warning(f"Error inicializando FER: {e}")
                self._fer_detector = None

    @staticmethod
    def disponible() -> bool:
        return _BACKEND is not None

    @staticmethod
    def backend() -> str | None:
        return _BACKEND

    def analizar(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        """Analiza la emoción dominante en el frame.

        Retorna dict con: emocion (str español), confianza (float 0-1), todas (dict).
        Respeta intervalo mínimo entre análisis.
        """
        ahora = time.monotonic()
        if (ahora - self._ultimo_analisis) < _INTERVALO_MIN:
            return self._ultima_emocion

        self._ultimo_analisis = ahora

        if _BACKEND == "fer" and self._fer_detector is not None:
            return self._analizar_fer(frame_bgr)
        elif _BACKEND == "deepface":
            return self._analizar_deepface(frame_bgr)

        return {"emocion": "neutral", "confianza": 0.0, "backend": None}

    def _analizar_fer(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        try:
            resultados = self._fer_detector.detect_emotions(frame_bgr)
            if not resultados:
                return {"emocion": "neutral", "confianza": 0.0, "backend": "fer"}
            # Tomar el rostro con mayor score
            mejor = max(resultados, key=lambda r: max(r.get("emotions", {}).values(), default=0))
            emociones = mejor.get("emotions", {})
            if not emociones:
                return {"emocion": "neutral", "confianza": 0.0, "backend": "fer"}

            emocion_en = max(emociones, key=emociones.get)  # type: ignore[arg-type]
            confianza = emociones[emocion_en]
            emocion_es = _EMOCION_MAP.get(emocion_en, emocion_en)

            resultado = {
                "emocion": emocion_es,
                "confianza": round(confianza, 3),
                "todas": {_EMOCION_MAP.get(k, k): round(v, 3) for k, v in emociones.items()},
                "backend": "fer",
            }
            self._ultima_emocion = resultado
            return resultado
        except Exception as e:
            logger.debug(f"Error en análisis FER: {e}")
            return {"emocion": "neutral", "confianza": 0.0, "backend": "fer", "error": str(e)}

    def _analizar_deepface(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        try:
            resultados = DeepFace.analyze(  # type: ignore[union-attr]
                frame_bgr,
                actions=["emotion"],
                enforce_detection=False,
                silent=True,
            )
            if isinstance(resultados, list):
                resultados = resultados[0] if resultados else {}

            emociones = resultados.get("emotion", {})
            emocion_en = resultados.get("dominant_emotion", "neutral")
            confianza = emociones.get(emocion_en, 0.0) / 100.0  # deepface usa 0-100

            emocion_es = _EMOCION_MAP.get(emocion_en, emocion_en)
            resultado = {
                "emocion": emocion_es,
                "confianza": round(confianza, 3),
                "todas": {_EMOCION_MAP.get(k, k): round(v / 100, 3) for k, v in emociones.items()},
                "backend": "deepface",
            }
            self._ultima_emocion = resultado
            return resultado
        except Exception as e:
            logger.debug(f"Error en análisis DeepFace: {e}")
            return {"emocion": "neutral", "confianza": 0.0, "backend": "deepface", "error": str(e)}


