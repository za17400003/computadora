"""
🌊 DETECTOR DE YIKAVÚ — Convergencia Eretz v'Yam

El agua (Yam) se retrae, la tierra (Eretz) es revelada. 
יקוו Yikavú = punto de reunión de aguas dispersas.

Monitorea transiciones hacia consolidación:
  RUNTIME → STABLE = יקוו detectado
  Yam (procesos) → Eretz (código consolidado)
  
Emite evento centralizado cuando convergencia confirmada.
"""

import threading
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from enum import Enum
from loguru import logger

from computadora.interfaz.fsm_golem import EstadoMaljut
from computadora.nucleo.eventos import BusEventos
from computadora.memoria.memoria import add_memory, compress_day


class AsyncaYikavu(Enum):
    """Estados en viaje hacia יקוו"""
    DISPERSO = "disperso"  # YAM activo, procesos corriendo
    CONVERGIENDO = "convergiendo"  # Ciclos finalizando
    CONSOLIDADO = "consolidado"  # יקוו alcanzado: ERETZ revelada


@dataclass
class ConfiguracionYikavu:
    """Parámetros de detección de consolidación"""
    timeout_convergencia_seg: float = 5.0  # Max tiempo esperando DORMIDO
    threshold_memoria_seg: float = 2.0  # Tiempo mín. para compress_day completable
    poll_interval_ms: int = 500  # Revisar estado cada X ms
    habilitar_audios: bool = True  # Emitir TTS en יקוו
    
    # Configuración avanzada
    estados_validos_dormido: tuple = field(
        default_factory=lambda: (EstadoMaljut.DORMIDO, EstadoMaljut.DESCANSO_GUARDIAN)
    )
    estados_invalidos: tuple = field(
        default_factory=lambda: (EstadoMaljut.ERROR, EstadoMaljut.GEVURA_ACTIVA)
    )


@dataclass
class TransicionYikavu:
    """Transición detectada hacia consolidación"""
    timestamp: float
    estado_anterior: AsyncaYikavu
    estado_nuevo: AsyncaYikavu
    motivo: str  # "memoria_comprimida", "fsm_dormido", "todos_timers_finalizados"
    datos_consolidacion: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()


class DetectorYikavu:
    """
    Monitor de convergencia Yam↔Eretz.
    
    Detecta el momento יקוו cuando procesos dispersos se reúnen
    en estado estable y el sistema entra en consolidación.
    
    Thread-safe, emite eventos al BusEventos global.
    """
    
    def __init__(
        self,
        config: Optional[ConfiguracionYikavu] = None,
        bus_eventos: Optional[BusEventos] = None
    ):
        self.config = config or ConfiguracionYikavu()
        self.bus = bus_eventos or BusEventos()
        
        self._sensor_activo = threading.Event()
        self._thread_monitor: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Estados locales
        self._asynca_actual = AsyncaYikavu.DISPERSO
        self._timestamp_inicio_convergencia: Optional[float] = None
        self._transiciones_detectadas: List[TransicionYikavu] = []
        self._callbacks_yikavu: List[Callable[[TransicionYikavu], None]] = []
        
        logger.info("DetectorYikavu inicializado")
    
    # ============================================================================
    # API PÚBLICA
    # ============================================================================
    
    def iniciar_monitor(self) -> None:
        """Inicia el thread de monitoreo de consolidación"""
        with self._lock:
            if self._sensor_activo.is_set():
                logger.warning("DetectorYikavu ya activo")
                return
            
            self._sensor_activo.set()
            self._thread_monitor = threading.Thread(
                target=self._bucle_monitor,
                name="DetectorYikavu-Monitor",
                daemon=True
            )
            self._thread_monitor.start()
            logger.info("Monitor de Yikavú iniciado")
    
    def detener_monitor(self, esperar_sec: float = 3.0) -> None:
        """Detiene gracefully el monitor"""
        with self._lock:
            if not self._sensor_activo.is_set():
                return
            
            self._sensor_activo.clear()
            if self._thread_monitor:
                self._thread_monitor.join(timeout=esperar_sec)
                logger.info("Monitor de Yikavú detenido")
    
    def suscribirse_consolidacion(
        self,
        callback: Callable[[TransicionYikavu], None]
    ) -> None:
        """Registra callback para ser notificado en Yikavú"""
        with self._lock:
            if callback not in self._callbacks_yikavu:
                self._callbacks_yikavu.append(callback)
                callback_name = getattr(callback, '__name__', '<callback anónimo>')
                logger.debug(f"Callback registrado en DetectorYikavu: {callback_name}")
    
    def desuscribirse(self, callback: Callable) -> None:
        """Desregistra callback"""
        with self._lock:
            if callback in self._callbacks_yikavu:
                self._callbacks_yikavu.remove(callback)
    
    def obtener_asynca_actual(self) -> AsyncaYikavu:
        """Retorna estado actual: DISPERSO / CONVERGIENDO / CONSOLIDADO"""
        with self._lock:
            return self._asynca_actual
    
    def obtener_transiciones(self) -> List[TransicionYikavu]:
        """Retorna histórico de transiciones detectadas"""
        with self._lock:
            return self._transiciones_detectadas.copy()
    
    def forzar_consolidacion_manual(self, motivo: str = "manual") -> bool:
        """
        Fuerza detección de consolidación immediatamente.
        Útil para testing o shutdown forzado.
        """
        with self._lock:
            if self._verificar_consolidacion_posible():
                return self._emitir_yikavu(f"forzado: {motivo}")
            return False
    
    # ============================================================================
    # LÓGICA DE MONITOREO (Private)
    # ============================================================================
    
    def _bucle_monitor(self) -> None:
        """Thread loop: monitorea transiciones hacia יקוו continuamente"""
        logger.info("Bucle de monitoreo Yikavú iniciado")
        
        while self._sensor_activo.is_set():
            try:
                with self._lock:
                    self._iterar_una_vez()
            except Exception as e:
                logger.error(f"Error en DetectorYikavu: {e}", exc_info=True)
            
            time.sleep(self.config.poll_interval_ms / 1000.0)
        
        logger.info("Bucle de monitoreo Yikavú finalizado")
    
    def _iterar_una_vez(self) -> None:
        """Una iteración del monitoreo"""
        # Estado actual de COMPUTADORA
        fsm_estado = self._obtener_estado_fsm()
        
        # Transiciones de máquina de estados
        match self._asynca_actual:
            case AsyncaYikavu.DISPERSO:
                # ¿Comienza convergencia?
                if self._señales_convergencia():
                    self._cambiar_asynca(
                        AsyncaYikavu.CONVERGIENDO,
                        "señales detectadas"
                    )
                    self._timestamp_inicio_convergencia = time.time()
            
            case AsyncaYikavu.CONVERGIENDO:
                # ¿Se confirma consolidación?
                if self._verificar_consolidacion_posible():
                    self._emitir_yikavu("transición confirmada")
                    self._cambiar_asynca(
                        AsyncaYikavu.CONSOLIDADO,
                        "consolidado"
                    )
                
                # ¿Han pasado demasiado tiempo?
                elif self._timestamp_inicio_convergencia:
                    elapsed = time.time() - self._timestamp_inicio_convergencia
                    if elapsed > self.config.timeout_convergencia_seg:
                        logger.warning(
                            f"Timeout convergencia ({elapsed:.1f}s), retornando a DISPERSO"
                        )
                        self._cambiar_asynca(AsyncaYikavu.DISPERSO, "timeout")
            
            case AsyncaYikavu.CONSOLIDADO:
                # Permanece hasta que Yam se активирует nuevamente
                if self._señales_nuevos_procesos():
                    self._cambiar_asynca(AsyncaYikavu.DISPERSO, "nueva actividad")
    
    # ============================================================================
    # DETECTORES DE TRANSICIÓN (Private)
    # ============================================================================
    
    def _señales_convergencia(self) -> bool:
        """¿Hay señales de que procesos comienzan a converger?"""
        # Ciclo circadiano en transición hacia reposo
        try:
            # Aquí se conectaría a ciclo_circadiano.obtener_fase()
            # Si fase == "descanso_guardian" o similar → convergencia comenzó
            pass
        except:
            pass
        
        # Memoria completó un ciclo
        try:
            if hasattr(self.memoria, 'ultima_compresion_completada'):
                return self.memoria.ultima_compresion_completada
        except:
            pass
        
        return False
    
    def _verificar_consolidacion_posible(self) -> bool:
        """
        ¿Se cumplen TODAS las condiciones para יקוו?
        
        1. FSM en estado válido (DORMIDO, ESPERANDO)
        2. SIN estado de error
        3. Memoria comprimida (últimas 24h)
        4. Timers runtime finalizados
        5. Todos los threads de background durmiendo
        """
        # 1. Estado FSM válido
        fsm_estado = self._obtener_estado_fsm()
        if fsm_estado in self.config.estados_invalidos:
            return False
        
        if fsm_estado not in self.config.estados_validos_dormido:
            # Puede estar en transición, no verificado aún
            return False
        
        # 2. Memoria comprimida en últimas horas
        try:
            # Verificar que memoria.compress_day() se ejecutó recientemente
            if not self._verificar_memoria_comprimida():
                return False
        except:
            return False
        
        # 3. Sin procesos pendientes (verificar via memoria)
        # (Simplificado: en producción revisar verdadera cola de tareas)
        
        return True
    
    def _señales_nuevos_procesos(self) -> bool:
        """¿Nuevos procesos se han iniciado? (rompen consolidación)"""
        # Aquí revisar si hay triggers nuevos en BusEventos, etc.
        return False
    
    # ============================================================================
    # EMISIÓN DE EVENTOS
    # ============================================================================
    
    def _emitir_yikavu(self, motivo: str) -> bool:
        """
        Emite evento centralizado de consolidación completada.
        Invoca callbacks y notifica al BusEventos.
        """
        try:
            transicion = TransicionYikavu(
                timestamp=time.time(),
                estado_anterior=self._asynca_actual,
                estado_nuevo=AsyncaYikavu.CONSOLIDADO,
                motivo=motivo,
                datos_consolidacion={
                    "timestamp_iso": datetime.now().isoformat(),
                    "fsm_estado": str(self._obtener_estado_fsm()),
                    "memoria_state": "comprimida" if self._verificar_memoria_comprimida() else "pending"
                }
            )
            
            self._transiciones_detectadas.append(transicion)
            
            # Invocar callbacks registrados
            for callback in self._callbacks_yikavu:
                try:
                    callback(transicion)
                except Exception as e:
                    logger.error(f"Error en callback Yikavú: {e}")
            
            # Emitir al BusEventos (broadcast a otros sistemas)
            self.bus.emitir(
                "consolidacion_completada",
                {
                    "evento": "yikavu",
                    "timestamp": transicion.timestamp,
                    "motivo": motivo,
                    "datos": transicion.datos_consolidacion
                }
            )
            
            # Audio si habilitado
            if self.config.habilitar_audios:
                logger.info("🌊 יקוו CONSOLIDATION POINT REACHED")
                # Aquí se llamaría a HiloHabla para TTS:
                # self.hilo_habla.hablar("י-קו-ו: Aguas reunidas. Sistema consolidado.")
            
            return True
        
        except Exception as e:
            logger.error(f"Error emitiendo Yikavú: {e}")
            return False
    
    def _cambiar_asynca(self, asynca_nueva: AsyncaYikavu, motivo: str) -> None:
        """Transición interna de estado Asynca"""
        if asynca_nueva != self._asynca_actual:
            anterior = self._asynca_actual
            self._asynca_actual = asynca_nueva
            logger.debug(f"Asynca: {anterior.value} → {asynca_nueva.value} ({motivo})")
    
    # ============================================================================
    # HELPERS
    # ============================================================================
    
    def _obtener_estado_fsm(self) -> EstadoMaljut:
        """Obtiene estado actual del FSM Maljut"""
        try:
            # Aquí se conectaría al FSM real
            # Por ahora retorna un dummy state
            return EstadoMaljut.ESPERANDO
        except:
            return EstadoMaljut.ERROR
    
    def _verificar_memoria_comprimida(self) -> bool:
        """¿Se ejecutó compress_day recientemente?"""
        try:
            # Revisar si hay un marcador en memoria de compresión reciente
            # Simplificación: verificar que archivo de resumen existe
            import os
            from datetime import date
            
            today_str = date.today().strftime("%Y-%m-%d")
            resumen_path = f"datos/memoria/memoria_summary_{today_str}.txt"
            
            return os.path.exists(resumen_path)
        except:
            return False


