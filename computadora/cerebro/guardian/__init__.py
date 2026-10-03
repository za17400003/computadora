# -*- coding: utf-8 -*-

"""
🛡️ Módulo Guardian — Gestor Centralizado de Protección

Propósito: Centralizar toda la lógica de Guardian en una sola clase con State Pattern.

Antes (FRAGMENTADO):
  - _activar_guardian() en nlu.py
  - _modo_guardian boolean en cerebro
  - _activar_guardian_por_bloqueo() en listeners
  - activar_guardian() en flujos_guardian.py

Ahora (CENTRALIZADO):
  - GuardianManager clase única (State Pattern)
  - GuardianState enum con estados válidos
  - Feature flag validation en UNA ubicación
  - Signal/event para cambios de estado

Uso:
  from computadora.cerebro.guardian import GuardianManager
  
  manager = GuardianManager(cerebro, feature_flags)
  if manager.activar(razon="sesion_bloqueada", origen="windows_lock"):
      print("Guardian activado")
  else:
      print("Guardian bloqueado por feature flag")
"""

from .manager import GuardianManager, GuardianState
from .events import GuardianStateChangeEvent

__all__ = [
    "GuardianManager",
    "GuardianState",
    "GuardianStateChangeEvent",
]


