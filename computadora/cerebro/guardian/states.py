# -*- coding: utf-8 -*-

"""
Estados de Guardian — Definición de transiciones válidas

Máquina de estados para Guardian usando Enum.
"""

from enum import Enum


class GuardianState(Enum):
    """
    Estados posibles de Guardian.
    
    Transiciones válidas:
      INACTIVE → ACTIVE (activación)
      ACTIVE → INACTIVE (desactivación)
      INACTIVE → SESSION_LOCKED (sistema bloqueado)
      SESSION_LOCKED → INACTIVE (sesión desbloqueada)
    """
    
    INACTIVE = "inactivo"
    """Guardian desactivado — sistema acepta cualquier voz."""
    
    ACTIVE = "activo"
    """Guardian activado — requiere autenticación del propietario."""
    
    SESSION_LOCKED = "sesion_bloqueada"
    """Windows+L activado — Guardian en modo bloqueado temporal."""
    
    TRANSITIONING = "transicionando"
    """En transición entre estados (temporal)."""
    
    def __str__(self) -> str:
        """Representación legible."""
        return self.value


# Transiciones válidas (para validar cambios de estado)
TRANSICIONES_VALIDAS = {
    GuardianState.INACTIVE: {GuardianState.ACTIVE, GuardianState.SESSION_LOCKED, GuardianState.TRANSITIONING},
    GuardianState.ACTIVE: {GuardianState.INACTIVE, GuardianState.TRANSITIONING},
    GuardianState.SESSION_LOCKED: {GuardianState.INACTIVE, GuardianState.TRANSITIONING},
    GuardianState.TRANSITIONING: {GuardianState.INACTIVE, GuardianState.ACTIVE, GuardianState.SESSION_LOCKED},
}


def es_transicion_valida(estado_actual: GuardianState, estado_nuevo: GuardianState) -> bool:
    """
    Valida si transición de estado es legal.
    
    Args:
        estado_actual: Estado actual
        estado_nuevo: Estado propuesto
    
    Returns:
        bool: True si transición es válida
    """
    return estado_nuevo in TRANSICIONES_VALIDAS.get(estado_actual, set())


