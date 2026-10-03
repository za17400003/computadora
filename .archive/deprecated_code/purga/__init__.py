"""Módulo de Purga — Nigredo continua, limpiar lo corrupto.

CONCEPTO ESOTÉRICO: Nigredo — Destilación y purificación de la materia prima.

RESPONSABILIDAD PRAGMÁTICA:
  - Detectar contradicciones y obsolescencia
  - Limpiar automáticamente: caché expirado, duplicados, estados rotos
  - Ejecutar manual O cron cada 6 horas
  - Reportar a .audit/purga_TIMESTAMP.log
"""

from computadora.purga.detector_contradicciones import (
    DetectorContradicciones,
    Contradiccion,
)
from computadora.purga.purgador_automatico import PurgadorAutomatico

__all__ = [
    "DetectorContradicciones",
    "Contradiccion",
    "PurgadorAutomatico",
]


