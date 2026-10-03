"""Módulo de Auditoría Viva — Sistema observándose a sí mismo.

CONCEPTO ESOTÉRICO: Keter (Corona) — Visión holística del sistema.

RESPONSABILIDAD PRAGMÁTICA:
  - Verificar coherencia EN VIVO (no post-mortem)
  - Detectar incoherencias: nombres, imports, fases, estados
  - Reportar a .audit/coherencia_TIMESTAMP.log
  - Ejecutar cada 60 segundos durante operación normal
"""

from computadora.auditoria.verificador_coherencia import (
    VerificadorCoherencia,
    CoherenciaReport,
)
from computadora.auditoria.reportador_auditoria import ReportadorAuditoria

__all__ = [
    "VerificadorCoherencia",
    "CoherenciaReport",
    "ReportadorAuditoria",
]


