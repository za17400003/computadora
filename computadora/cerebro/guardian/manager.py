# -*- coding: utf-8 -*-

"""
GuardianManager — Gestor Centralizado de Guardian (State Pattern)

Propósito: Una sola clase responsable de:
  1. Validar feature flag antes de activación
  2. Mantener estado centralizado (no boolean esparcido)
  3. Emitir eventos para que otros módulos reaccionen
  4. Thread-safe con locks

Antes (MAL):
  - _modo_guardian boolean en CerebroComputadora
  - Activaciones desde 4+ lugares sin coordinación
  - Feature flag no validado centralmente

Ahora (BIEN):
  - GuardianManager clase única (responsabilidad concentrada)
  - Feature flag validado en UNA ubicación
  - Estado en enum (no boolean)
  - Callbacks para state changes
"""

import threading
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional

from .states import GuardianState, es_transicion_valida
from .events import GuardianStateChangeEvent

logger = logging.getLogger(__name__)


class GuardianManager:
    """
    Gestor centralizado de Guardian (State Pattern + Feature Flag).
    
    Responsabilidades:
      - Mantener estado de Guardian (GuardianState enum)
      - Validar feature flag antes de activación
      - Permitir activación/desactivación con razonamiento
      - Emitir eventos para cambios de estado
      - Thread-safe con RLock
    
    Ejemplo de uso:
      
      manager = GuardianManager(cerebro, feature_flags)
      
      # Intentar activar
      if manager.puede_activar():
          if manager.activar(razon="sesion_bloqueada", origen="windows_lock"):
              print("Guardian activado")
      
      # Estado actual
      if manager.activo:
          print(f"Guardian está {manager.estado.value}")
      
      # Desactivar
      manager.desactivar(razon="cierre_sesion")
    """
    
    def __init__(self, cerebro, feature_flags):
        """
        Inicializa GuardianManager.
        
        Args:
            cerebro: Instancia de CerebroComputadora
            feature_flags: FeatureFlags singleton para validar guardian_activo flag
        
        Precondición:
            cerebro debe estar en estado válido
            feature_flags debe tener obtener("guardian_activo")
        
        Postcondición:
            manager está inicializado en estado INACTIVE
            listo para activación/desactivación
        """
        self._cerebro = cerebro
        self._feature_flags = feature_flags
        self._estado = GuardianState.INACTIVE
        self._lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {
            "state_change": [],
            "activation_blocked": [],
        }
        
        logger.info("🛡️ GuardianManager inicializado (inactivo)")
    
    @property
    def estado(self) -> GuardianState:
        """Estado actual de Guardian (thread-safe)."""
        with self._lock:
            return self._estado
    
    @property
    def activo(self) -> bool:
        """¿Está Guardian activo? (sinónimo: estado == ACTIVE)."""
        return self.estado == GuardianState.ACTIVE
    
    def puede_activar(self) -> bool:
        """
        ¿Está permitida la activación de Guardian?
        
        Valida feature flag: guardian_activo DEBE ser False para permitir.
        
        Returns:
            bool: True si guardian_activo == False (guardián NO debe estar activo)
        """
        flag_value = self._feature_flags.obtener("guardian_activo")
        # guardian_activo=False significa "NO debe estar activo" → SÍ se puede activar
        return flag_value is False
    
    def activar(self, razon: str, origen: str = "manual") -> bool:
        """
        Activa Guardian SÓ SI feature flag permite.
        
        Lógica:
          1. Validar feature flag guardian_activo == False
          2. Validar transición de estado es legal
          3. Cambiar estado a ACTIVE
          4. Actualizar cerebro._modo_guardian = True
          5. Emitir eventos
        
        Args:
            razon: Por qué se activa ("sesion_bloqueada", "comando_voz", etc)
            origen: Dónde viene solicitud ("windows_lock", "nlu", "manual", etc)
        
        Returns:
            bool: True si se activó, False si fue bloqueado por feature flag
        
        Postcondición:
            Si retorna True: estado == ACTIVE, cerebro._modo_guardian = True
            Si retorna False: estado sin cambiar, evento de bloqueo emitido
        """
        with self._lock:
            # VALIDACIÓN 1: Feature flag
            if not self.puede_activar():
                msg = (
                    f"⛔ Intento de activar Guardian BLOQUEADO por feature flag "
                    f"(guardian_activo=True, origen={origen})"
                )
                logger.warning(msg)
                self._emit_activation_blocked(razon, origen)
                return False
            
            # VALIDACIÓN 2: Transición legal
            if not es_transicion_valida(self._estado, GuardianState.ACTIVE):
                msg = (
                    f"⛔ Transición inválida Guardian: "
                    f"{self._estado.value} → ACTIVE (origen={origen})"
                )
                logger.error(msg)
                return False
            
            # ACTIVAR
            estado_anterior = self._estado
            self._estado = GuardianState.ACTIVE
            self._cerebro._modo_guardian = True
            
            msg = f"🛡️ Guardian ACTIVADO: {razon} (desde {origen})"
            logger.info(msg)
            
            # Emitir evento de cambio
            self._emit_state_change(estado_anterior, self._estado, razon, origen)
            return True
    
    def desactivar(self, razon: str = "cierre_sesion", origen: str = "sistema") -> bool:
        """
        Desactiva Guardian.
        
        Lógica:
          1. Validar transición de estado es legal
          2. Cambiar estado a INACTIVE
          3. Actualizar cerebro._modo_guardian = False
          4. Emitir eventos
        
        Args:
            razon: Por qué se desactiva ("cierre_sesion", "comando_voz", etc)
            origen: Dónde viene solicitud (default: "sistema")
        
        Returns:
            bool: True si se desactivó
        """
        with self._lock:
            # VALIDACIÓN: Transición legal
            if not es_transicion_valida(self._estado, GuardianState.INACTIVE):
                msg = (
                    f"⛔ Transición inválida Guardian: "
                    f"{self._estado.value} → {GuardianState.INACTIVE.value}"
                )
                logger.error(msg)
                return False
            
            # DESACTIVAR
            estado_anterior = self._estado
            self._estado = GuardianState.INACTIVE
            self._cerebro._modo_guardian = False
            
            msg = f"🛡️ Guardian DESACTIVADO: {razon}"
            logger.info(msg)
            
            # Emitir evento
            self._emit_state_change(estado_anterior, self._estado, razon, origen)
            return True
    
    def registrar_callback_state_change(self, callback: Callable) -> None:
        """
        Registra callback para ser invocado en cambios de estado.
        
        Signature del callback:
          def on_guardian_change(evento: GuardianStateChangeEvent) -> None:
              pass
        
        Args:
            callback: Función a invocar en cambios
        """
        with self._lock:
            self._callbacks["state_change"].append(callback)
    
    def registrar_callback_activation_blocked(self, callback: Callable) -> None:
        """
        Registra callback para ser invocado cuando activación es bloqueada.
        
        Signature:
          def on_activation_blocked(razon: str, origen: str) -> None:
              pass
        
        Args:
            callback: Función a invocar
        """
        with self._lock:
            self._callbacks["activation_blocked"].append(callback)
    
    def _emit_state_change(
        self, estado_anterior: GuardianState, estado_nuevo: GuardianState, 
        razon: str, origen: str
    ) -> None:
        """Emite evento de cambio de estado a todos los callbacks registrados."""
        evento = GuardianStateChangeEvent(
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            razon=razon,
            origen=origen,
            timestamp=datetime.now(),
        )
        
        for callback in self._callbacks["state_change"]:
            try:
                callback(evento)
            except Exception as e:
                logger.error(f"Error en callback state_change: {e}")
    
    def _emit_activation_blocked(self, razon: str, origen: str) -> None:
        """Emite evento cuando activación es bloqueada."""
        for callback in self._callbacks["activation_blocked"]:
            try:
                callback(razon, origen)
            except Exception as e:
                logger.error(f"Error en callback activation_blocked: {e}")


