"""
dialogo_or_choshech.py — Ciclo de Diálogo Or v'Choshech

Implementa el ciclo alternado entre Tiféret (Cerebro) y Yesoid (Memoria)
manifestado como diálogo audible hasta que el sistema alcanza Choshech (reposo).

Or Yashar (אור ישר): Luz descendente - Tiféret emite pensamientos
Or Chozer (אור חוזר): Luz ascendente - Yesoid aporta recuerdos
Choshech (חושך): Oscuridad - Término en estado DORMIDO

FP-119 Implementation | WI-295
"""

import threading
import time
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
from loguru import logger

try:
    from PyQt6.QtCore import QThread, pyqtSignal
except ImportError:
    # Fallback para testing sin PyQt
    class QThread:
        pass
    
    def pyqtSignal(*args, **kwargs):
        return None


class EstadoDialogo(Enum):
    """Estados del diálogo Or v'Choshech"""
    PARADO = "parado"           # No iniciado
    EJECUTANDO = "ejecutando"   # Loop activo
    EN_ESPERA = "en_espera"     # Esperando respuesta del usuario
    CHOSHECH = "choshech"       # Silencio final (reposo)
    ERROR = "error"             # Estado de error


@dataclass
class CicloDialogo:
    """Datos de un ciclo Or Yashar ↔ Or Chozer"""
    numero: int
    tipo: str                   # "tifera" | "yesoid"
    timestamp: float
    entrada: str                # Tema/pregunta
    salida: str                 # Respuesta/recuerdo
    duracion_ms: int            # Tiempo de procesamiento


class DialogoOrVChoshech(QThread):
    """
    Ciclo de diálogo alternado entre Tiféret (Cerebro) y Yesoid (Memoria).
    
    Manifestación arquitectónica de Or v'Choshech:
    - Or Yashar: Tiféret sintetiza respuesta (luz descendente)
    - Or Chozer: Yesoid aporta contexto (luz ascendente)
    - Choshech: Cuando FSM→DORMIDO o timeout, el ciclo se extingue
    
    Signals Qt:
    - iniciado: Se inicia el diálogo
    - ciclo_completado: Se completa un ciclo (T o me)
    - finalizado: Diálogo llega a Choshech
    - error_dialogo: Error durante ejecución
    """
    
    # Signals Qt
    iniciado = pyqtSignal()
    ciclo_completado = pyqtSignal(CicloDialogo)
    finalizado = pyqtSignal(int)  # Número total de ciclos
    error_dialogo = pyqtSignal(str)  # Mensaje de error
    
    # Constantes
    AUDIBLE_TIFERA = "T"         # /t/ or "Tiféret"
    AUDIBLE_MEMORIA = "me"       # /me/ or "Yesoid"
    MAX_CICLOS = 12              # Máximo de ciclos antes de saturación
    TIMEOUT_ESPERA = 2.0         # Segundos esperando síntesis TTS
    
    def __init__(
        self,
        cerebro: "CerebroComputadora",
        memoria: object,
        hilo_habla: "HiloHabla",
        fsm: "FSM",
        max_ciclos: int = 12,
        callback_ciclo: Optional[Callable] = None,
    ):
        """
        Args:
            cerebro: Instancia de CerebroComputadora (Tiféret)
            memoria: Objeto de memoria (Yesoid)
            hilo_habla: HiloHabla para TTS
            fsm: FSM para monitorear estado DORMIDO
            max_ciclos: Máximo de ciclos antes de terminar
            callback_ciclo: Función opcional llamada en cada ciclo completado
        """
        super().__init__()
        
        self.cerebro = cerebro
        self.memoria = memoria
        self.hilo_habla = hilo_habla
        self.fsm = fsm
        
        self.max_ciclos = max_ciclos
        self.callback_ciclo = callback_ciclo
        
        self.estado = EstadoDialogo.PARADO
        self.ciclos_completados: list[CicloDialogo] = []
        self.tema_actual = ""
        self._lock = threading.Lock()
        self._should_stop = False
    
    def start_dialogo(self, tema_inicial: str) -> None:
        """
        Inicia el ciclo de diálogo.
        
        Args:
            tema_inicial: Pregunta o tema semilla para el diálogo
        """
        if self.estado not in (EstadoDialogo.PARADO, EstadoDialogo.CHOSHECH):
            logger.warning(f"No se puede iniciar diálogo en estado {self.estado}")
            return
        
        with self._lock:
            self.tema_actual = tema_inicial
            self._should_stop = False
            self.ciclos_completados.clear()
        
        self.start()  # Inicia QThread
    
    def stop_dialogo(self) -> None:
        """Detiene el diálogo gracefully"""
        with self._lock:
            self._should_stop = True
    
    def run(self) -> None:
        """
        Ciclo principal de Or v'Choshech.
        
        Ejecución en QThread separado:
        1. Alterna Tiféret (ciclos pares) ↔ Yesoid (ciclos impares)
        2. Cada lado sintetiza "T" o "me" audiblemente
        3. Se retroalimentan: salida de T → entrada de Yesoid
        4. Termina cuando FSM→DORMIDO o MAX_CICLOS o usuario detiene
        """
        try:
            logger.info(f"🌀 Iniciando Or v'Choshech sobre tema: {self.tema_actual}")
            self.iniciado.emit()
            
            with self._lock:
                self.estado = EstadoDialogo.EJECUTANDO
            
            ciclo = 0
            while ciclo < self.max_ciclos:
                # Revisar si debe detener
                with self._lock:
                    if self._should_stop:
                        logger.info("📍 Or v'Choshech detenido por usuario")
                        break
                
                # Revisar si FSM alcanzó DORMIDO (Choshech)
                try:
                    if hasattr(self.fsm, 'estado'):
                        estado_actual = str(self.fsm.estado).lower()
                        if 'dormido' in estado_actual or 'sleep' in estado_actual:
                            logger.info("🌙 FSM alcanzó DORMIDO — Or v'Choshech termina (Choshech)")
                            break
                except Exception as e:
                    logger.warning(f"No se pudo revisar FSM: {e}")
                
                # TIFÉRET (Or Yashar - Luz Descendente)
                if ciclo % 2 == 0:
                    ciclo_data = self._ejecutar_tifera(ciclo)
                    if ciclo_data:
                        self.ciclos_completados.append(ciclo_data)
                        if self.callback_ciclo:
                            self.callback_ciclo(ciclo_data)
                        self.ciclo_completado.emit(ciclo_data)
                        self.tema_actual = ciclo_data.salida
                
                # YESOID (Or Chozer - Luz Ascendente)
                else:
                    ciclo_data = self._ejecutar_yesoid(ciclo)
                    if ciclo_data:
                        self.ciclos_completados.append(ciclo_data)
                        if self.callback_ciclo:
                            self.callback_ciclo(ciclo_data)
                        self.ciclo_completado.emit(ciclo_data)
                        self.tema_actual = ciclo_data.salida
                
                ciclo += 1
                
                # Pequeña pausa entre ciclos
                time.sleep(0.1)
            
            # CHOSHECH — Silencio final
            logger.info("🌑 Alcanzando Choshech (חושך)")
            with self._lock:
                self.estado = EstadoDialogo.CHOSHECH
            
            # Síntesis final opcional (silencio)
            try:
                self.hilo_habla.hablar("[Silencio final]")
                time.sleep(1.0)  # Esperar a que termine
            except Exception as e:
                logger.warning(f"Error en síntesis final: {e}")
            
            logger.info(f"✅ Or v'Choshech completado en {ciclo} ciclos")
            self.finalizado.emit(ciclo)
        
        except Exception as e:
            logger.error(f"❌ Error en Or v'Choshech: {e}", exc_info=True)
            self.error_dialogo.emit(str(e))
            with self._lock:
                self.estado = EstadoDialogo.ERROR
    
    def _ejecutar_tifera(self, numero_ciclo: int) -> Optional[CicloDialogo]:
        """
        Ejecuta fase Tiféret (Or Yashar - Luz Descendente).
        
        Tiféret sintetiza respuesta al tema actual.
        Salida: "T: {respuesta}"
        """
        try:
            timestamp = time.time()
            logger.debug(f"  [Ciclo {numero_ciclo}] 📌 TIФERA — pensando en: {self.tema_actual[:40]}")
            
            # Obtener respuesta de Tiféret (Cerebro)
            respuesta = self.cerebro.pensar(self.tema_actual)
            
            # Almacenar en memoria como "tifera"
            if hasattr(self.memoria, 'add_memory'):
                self.memoria.add_memory("tifera", respuesta)
            
            # Síntesis audible: "T" + respuesta
            audio_text = f"{self.AUDIBLE_TIFERA}: {respuesta[:100]}"
            self.hilo_habla.hablar(audio_text)
            
            # Esperar síntesis
            time.sleep(self.TIMEOUT_ESPERA)
            
            duracion_ms = int((time.time() - timestamp) * 1000)
            ciclo_data = CicloDialogo(
                numero=numero_ciclo,
                tipo="tifera",
                timestamp=timestamp,
                entrada=self.tema_actual,
                salida=respuesta,
                duracion_ms=duracion_ms
            )
            
            logger.debug(f"  ✓ Tiféret respondió ({duracion_ms}ms)")
            return ciclo_data
        
        except Exception as e:
            logger.error(f"Error en Tiféret: {e}")
            return None
    
    def _ejecutar_yesoid(self, numero_ciclo: int) -> Optional[CicloDialogo]:
        """
        Ejecuta fase Yesoid (Or Chozer - Luz Ascendente).
        
        Yesoid busca recuerdos relevantes al tema actual.
        Salida: "me: {resumen de memorias}"
        """
        try:
            timestamp = time.time()
            logger.debug(f"  [Ciclo {numero_ciclo}] 🧠 YESOID — buscando recuerdos sobre: {self.tema_actual[:40]}")
            
            # Buscar recuerdos relevantes
            recuerdos = []
            if hasattr(self.memoria, 'buscar_en_memoria'):
                recuerdos = self.memoria.buscar_en_memoria(self.tema_actual)
            
            # Resumir top-3 recuerdos
            resumen_memoria = ""
            if recuerdos:
                textos = [m.get('text', str(m))[:50] for m in recuerdos[:3]]
                resumen_memoria = " | ".join(textos)
            else:
                resumen_memoria = "(Sin recuerdos previos)"
            
            # Almacenar búsqueda en memoria
            if hasattr(self.memoria, 'add_memory'):
                self.memoria.add_memory("yesoid", resumen_memoria)
            
            # Síntesis audible: "me" + resumen
            audio_text = f"{self.AUDIBLE_MEMORIA}: {resumen_memoria[:100]}"
            self.hilo_habla.hablar(audio_text)
            
            # Esperar síntesis
            time.sleep(self.TIMEOUT_ESPERA)
            
            duracion_ms = int((time.time() - timestamp) * 1000)
            ciclo_data = CicloDialogo(
                numero=numero_ciclo,
                tipo="yesoid",
                timestamp=timestamp,
                entrada=self.tema_actual,
                salida=resumen_memoria,
                duracion_ms=duracion_ms
            )
            
            logger.debug(f"  ✓ Yesoid encontró recuerdos ({duracion_ms}ms)")
            return ciclo_data
        
        except Exception as e:
            logger.error(f"Error en Yesoid: {e}")
            return None
    
    def get_ciclos(self) -> list[CicloDialogo]:
        """Retorna lista de ciclos completados"""
        with self._lock:
            return self.ciclos_completados.copy()
    
    def get_estado(self) -> EstadoDialogo:
        """Retorna estado actual del diálogo"""
        with self._lock:
            return self.estado


