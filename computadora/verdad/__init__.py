"""Módulo de Verdad — Verificación de EMET (אמת) en vivo.

CONCEPTO ESOTÉRICO: EMET (Verdad) — Lo que ES, verificable en runtime.

RESPONSABILIDAD PRAGMÁTICA:
  - Verificar que sensor + API + user report = COHERENTES
  - Si hay contradicción: NO MENTIR, reportar incoherencia
  - Si incoherencia CRÍTICA: BLOQUEAR acción (sistema no puede ejecutar si es falso)
  - Output: .audit/verdad_TIMESTAMP.log
"""

from computadora.verdad.verificador_realidad import (
    VerificadorRealidad,
    VerificacionResultado,
)
from computadora.verdad.verificador_coherencia_interna import (
    VerificadorCoherenciaInterna,
)

__all__ = [
    "VerificadorRealidad",
    "VerificacionResultado",
    "VerificadorCoherenciaInterna",
]


