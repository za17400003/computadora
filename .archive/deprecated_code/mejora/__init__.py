"""Módulo de Mejora — Citrinitas continua, síntesis y optimización.

CONCEPTO ESOTÉRICO: Citrinitas — Iluminación, síntesis externa, investigación.

RESPONSABILIDAD PRAGMÁTICA:
  - Recolectar feedback del usuario
  - Analizar patrones (qué repite, qué falla, qué funciona)
  - Generar recomendaciones para próxima iteración
  - Output: .audit/feedback.json + .audit/recommendations.md
"""

from computadora.mejora.colector_feedback import (
    ColectorFeedback,
    EventoFeedback,
)
from computadora.mejora.analizador_patrones import AnalizadorPatrones
from computadora.mejora.generador_mejoras import GeneradorMejoras

__all__ = [
    "ColectorFeedback",
    "EventoFeedback",
    "AnalizadorPatrones",
    "GeneradorMejoras",
]


