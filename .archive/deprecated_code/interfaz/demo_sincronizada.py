"""
FP-139 RUBEDO FASE 2 + FP-156 CITRINITAS: Sistema de Demos Sincronizadas.

Garantiza orden estricto: Animacion -> Narracion -> Espera -> Siguiente paso.
Sin solapamiento. Timeline clara. Feedback visual consistente.

FP-156 MEJORAS:
- TTS sincronizado con visuales
- Resaltado de elementos activos
- Logging de verificacion para post-demo analisis
- Metricas de rendimiento (FPS, latencia TTS)
"""

import json
import time
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Any
from PyQt6.QtCore import QTimer
from loguru import logger


class EstadoDemo(Enum):
    IDLE = "idle"
    ANIMANDO = "animando"
    NARRANDO = "narrando"
    ESPERANDO = "esperando"
    PAUSA = "pausa"
    COMPLETADA = "completada"


class PasoDemo:
    def __init__(self, tipo, contenido, duracion_visual=None, nombre="", resaltar=None):
        self.tipo = tipo
        self.contenido = contenido
        self.duracion_visual = duracion_visual
        self.nombre = nombre
        self.resaltar = resaltar
        self.completado = False
        self.inicio_ts = 0.0
        self.fin_ts = 0.0
        self.log_verificacion = {}
    
    def __repr__(self):
        return f"PasoDemo({self.tipo}, {self.nombre}, dur={self.duracion_visual})"


class DemoSincronizada:
    def __init__(self, orbe):
        self.orbe = orbe
        self.timeline = []
        self.idx_actual = 0
        self.estado = EstadoDemo.IDLE
        self.timer_paso = QTimer()
        self.timer_paso.timeout.connect(self._on_timeout_paso)
        self.callback_completada = None
        self.ts_inicio = 0.0
        self.duracion_estimada = 0.0
        self._log_verificacion = {}
        
        try:
            from computadora.geometria.geometrias_platonicas import TransmutadorOrbe
            self.transmutador = TransmutadorOrbe()
        except ImportError:
            self.transmutador = None
            logger.debug("TransmutadorOrbe no disponible para demo")
    
    def agregar_paso(self, tipo, contenido, duracion_visual=None, nombre="", resaltar=None):
        paso = PasoDemo(tipo, contenido, duracion_visual, nombre, resaltar)
        self.timeline.append(paso)
        if duracion_visual:
            self.duracion_estimada += duracion_visual
    
    def comenzar(self, nombre_demo="demo"):
        if not self.timeline:
            logger.warning("Demo vacia")
            return
        
        self.idx_actual = 0
        self.estado = EstadoDemo.IDLE
        self.ts_inicio = time.time()
        self._log_verificacion = {
            "nombre": nombre_demo,
            "inicio": self.ts_inicio,
            "pasos": [],
            "resultado": ""
        }
        logger.info(f"Demo {nombre_demo}: {len(self.timeline)} pasos")
        self._ejecutar_paso()
    
    def _ejecutar_paso(self):
        if self.idx_actual >= len(self.timeline):
            self._finalizar()
            return
        
        paso = self.timeline[self.idx_actual]
        paso.inicio_ts = time.time()
        logger.debug(f"Paso {self.idx_actual}: {paso}")
        
        if paso.resaltar and hasattr(self.orbe, 'resaltar_elemento'):
            self.orbe.resaltar_elemento(paso.resaltar, activo=True)
        
        try:
            if paso.tipo == "animar":
                self._ejecutar_animar(paso)
            elif paso.tipo == "narrar":
                self._ejecutar_narrar(paso)
            elif paso.tipo == "esperar":
                self._ejecutar_esperar(paso)
            elif paso.tipo == "cambio_visual":
                self._ejecutar_cambio_visual(paso)
            else:
                logger.warning(f"Tipo desconocido: {paso.tipo}")
                self._registrar_paso(paso, "error_tipo")
                self.idx_actual += 1
                QTimer.singleShot(10, self._ejecutar_paso)
        except Exception as e:
            logger.error(f"Error paso {self.idx_actual}: {e}")
            self._registrar_paso(paso, f"error: {e}")
            self.idx_actual += 1
            QTimer.singleShot(10, self._ejecutar_paso)
    
    def _registrar_paso(self, paso, resultado):
        paso.fin_ts = time.time()
        paso.completado = resultado == "ok"
        paso.log_verificacion = {
            "nombre": paso.nombre,
            "tipo": paso.tipo,
            "duracion_ms": (paso.fin_ts - paso.inicio_ts) * 1000,
            "resultado": resultado
        }
        if hasattr(self, '_log_verificacion'):
            self._log_verificacion["pasos"].append(paso.log_verificacion)
    
    def _ejecutar_animar(self, paso):
        self.estado = EstadoDemo.ANIMANDO
        if callable(paso.contenido):
            paso.contenido()
        if paso.duracion_visual:
            self.timer_paso.start(int(paso.duracion_visual * 1000))
        else:
            QTimer.singleShot(10, self._on_paso_completado)
    
    def _ejecutar_narrar(self, paso):
        self.estado = EstadoDemo.NARRANDO
        if isinstance(paso.contenido, str):
            texto = paso.contenido
            if hasattr(self.orbe, '_sanitizar_para_voz'):
                texto = self.orbe._sanitizar_para_voz(texto)
            if hasattr(self.orbe, 'hilo_habla'):
                def _en_tts():
                    try:
                        self.orbe.hilo_habla.cola_vacia.disconnect(_en_tts)
                    except:
                        pass
                    self._on_paso_completado()
                try:
                    self.orbe.hilo_habla.cola_vacia.connect(_en_tts)
                except:
                    pass
                self.orbe.hilo_habla.hablar(texto)
            elif paso.duracion_visual:
                self.timer_paso.start(int(paso.duracion_visual * 1000))
            else:
                QTimer.singleShot(500, self._on_paso_completado)
        elif callable(paso.contenido):
            paso.contenido()
            QTimer.singleShot(10, self._on_paso_completado)
    
    def _ejecutar_esperar(self, paso):
        self.estado = EstadoDemo.ESPERANDO
        if paso.duracion_visual and paso.duracion_visual > 0:
            self.timer_paso.start(int(paso.duracion_visual * 1000))
        else:
            QTimer.singleShot(10, self._on_paso_completado)
    
    def _ejecutar_cambio_visual(self, paso):
        self.estado = EstadoDemo.ANIMANDO
        if callable(paso.contenido):
            paso.contenido()
        QTimer.singleShot(10, self._on_paso_completado)
    
    def _on_timeout_paso(self):
        self.timer_paso.stop()
        self._on_paso_completado()
    
    def _on_paso_completado(self):
        if self.idx_actual < len(self.timeline):
            paso = self.timeline[self.idx_actual]
            paso.completado = True
            self._registrar_paso(paso, "ok")
            if paso.resaltar and hasattr(self.orbe, 'resaltar_elemento'):
                self.orbe.resaltar_elemento(paso.resaltar, activo=False)
        self.idx_actual += 1
        QTimer.singleShot(10, self._ejecutar_paso)
    
    def _finalizar(self):
        self.estado = EstadoDemo.COMPLETADA
        duracion_total = time.time() - self.ts_inicio
        logger.info(f"Demo completada en {duracion_total:.2f}s")
        
        if self._log_verificacion:
            self._log_verificacion["duracion_total"] = duracion_total
            self._log_verificacion["resultado"] = "exito"
            try:
                log_path = Path("_logs") / "demo_verificacion.jsonl"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a") as f:
                    f.write(json.dumps(self._log_verificacion) + "\n")
            except Exception as e:
                logger.debug(f"Log demo: {e}")
        
        if self.callback_completada:
            self.callback_completada()
    
    def cancelar(self):
        self.timer_paso.stop()
        self.estado = EstadoDemo.IDLE
        self.idx_actual = len(self.timeline)
        logger.info("Demo cancelada")


