# -*- coding: utf-8 -*-

"""
Eventos de Guardian — Señales de cambio de estado

Propósito: Permitir que otros módulos reaccionen a cambios de Guardian sin acoplamiento directo.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from .states import GuardianState


@dataclass
class GuardianStateChangeEvent:
    """
    Evento emitido cuando Guardian cambia de estado.
    
    Attributes:
        estado_anterior: Estado previo
        estado_nuevo: Nuevo estado
        razon: Por qué cambió ("sesion_bloqueada", "comando_voz", "cierre", etc)
        origen: Dónde viene el cambio ("windows_lock", "nlu", "manual", etc)
        timestamp: Cuándo ocurrió
    """
    
    estado_anterior: GuardianState
    estado_nuevo: GuardianState
    razon: str
    origen: str
    timestamp: datetime
    
    def __str__(self) -> str:
        """Representación legible."""
        return (
            f"🛡️ Guardian: {self.estado_anterior.value} → {self.estado_nuevo.value} "
            f"(razon={self.razon}, origen={self.origen})"
        )


