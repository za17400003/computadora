"""Colector de Parámetros Completos de COMPUTADORA — Maljut en vivo.

Captura TODOS los parámetros observables durante una sesión:
- Rendimiento (latencia, CPU, memoria)
- Percepción (sensores, rostros, confianza)
- Verdad (verificaciones, bloques)
- Comunicación (comandos, respuestas)
- Integridad (archivos, caché)
- Aprendizaje (patrones, recomendaciones)

Integrable con GestorGeneraciones para materializar Maljut completo.
"""

from datetime import datetime
from dataclasses import dataclass
from threading import Lock
from typing import Optional
from loguru import logger
import psutil
import os


@dataclass
class MuestrasRendimiento:
    """Muestras de rendimiento para calcular promedio."""
    latencias_ms: list[float]  # rolling window
    cpu_porcentajes: list[float]
    memoria_mb: list[float]
    
    def agregar_muestra(self, latencia_ms: float, cpu: float, mem_mb: float,
                       ventana_max: int = 1000):
        """Agregar muestra, mantener ventana máxima."""
        self.latencias_ms.append(latencia_ms)
        self.cpu_porcentajes.append(cpu)
        self.memoria_mb.append(mem_mb)
        
        # Mantener tamaño máximo
        if len(self.latencias_ms) > ventana_max:
            self.latencias_ms = self.latencias_ms[-ventana_max:]
        if len(self.cpu_porcentajes) > ventana_max:
            self.cpu_porcentajes = self.cpu_porcentajes[-ventana_max:]
        if len(self.memoria_mb) > ventana_max:
            self.memoria_mb = self.memoria_mb[-ventana_max:]
    
    def obtener_estadisticas(self) -> dict:
        """Obtener estadísticas de muestras."""
        if not self.latencias_ms:
            return {
                "latencia_promedio_ms": 0.0,
                "latencia_maxima_ms": 0.0,
                "pico_cpu_porcentaje": 0.0,
                "pico_memoria_mb": 0.0,
            }
        
        return {
            "latencia_promedio_ms": sum(self.latencias_ms) / len(self.latencias_ms),
            "latencia_maxima_ms": max(self.latencias_ms),
            "pico_cpu_porcentaje": max(self.cpu_porcentajes),
            "pico_memoria_mb": max(self.memoria_mb),
        }


class ColectorParametrosCompletos:
    """Colector singleton de parámetros completos en vivo."""
    
    def __init__(self):
        self._lock = Lock()
        self.inicio = datetime.now()
        
        # Rendimiento
        self.muestras_rendimiento = MuestrasRendimiento([], [], [])
        
        # Percepción
        self.rostros_detectados = 0
        self.rostros_no_detectados = 0
        self.confianzas_faciales: list[float] = []  # rolling window
        self.dispositivos_audio_activos = 0
        self.dispositivos_audio_fallidos = 0
        self.sensores_totales = 0
        self.sensores_operacionales = 0
        
        # Verdad
        self.verificaciones_exitosas = 0
        self.verificaciones_fallidas = 0
        self.bloques_por_incoherencia = 0
        self.contradicciones_detectadas = 0
        
        # Comunicación
        self.comandos_procesados = 0
        self.comandos_exitosos = 0
        self.comandos_fallidos = 0
        self.respuestas_generadas = 0
        self.tokens_usados = 0
        
        # Integridad
        self.archivos_purgados = 0
        self.cache_limpiado_mb = 0.0
        self.duplicados_encontrados = 0
        self.duplicados_consolidados = 0
        
        # Aprendizaje
        self.patrones_detectados = 0
        self.recomendaciones_generadas = 0
        self.recomendaciones_aplicadas = 0
        self.features_usados = 0
        self.features_no_usados = 0
        self.confianzas_sistema: list[float] = []  # rolling window
        
        # Coherencia
        self.auditorias_ejecutadas = 0
        self.incoherencias_detectadas = 0
        self.incoherencias_resueltas = 0
        self.coherencia_porcentaje = 100.0
        
        logger.info("ColectorParametrosCompletos inicializado (Maljut captura viva)")
    
    # ===== RENDIMIENTO =====
    def registrar_muestra_rendimiento(self, latencia_ms: float = 0.0):
        """Registrar muestra de rendimiento actual."""
        with self._lock:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.01)
                mem_percent = psutil.virtual_memory().percent
                mem_mb = psutil.virtual_memory().used / (1024 ** 2)
                
                self.muestras_rendimiento.agregar_muestra(latencia_ms, cpu_percent, mem_mb)
            except Exception as e:
                logger.warning(f"Error registrando rendimiento: {e}")
    
    # ===== PERCEPCIÓN =====
    def registrar_rostro_detectado(self, confianza: float = 0.0):
        """Registrar detección exitosa de rostro."""
        with self._lock:
            self.rostros_detectados += 1
            if confianza > 0:
                self.confianzas_faciales.append(confianza)
                if len(self.confianzas_faciales) > 1000:
                    self.confianzas_faciales = self.confianzas_faciales[-1000:]
    
    def registrar_rostro_no_detectado(self):
        """Registrar fallo en detección."""
        with self._lock:
            self.rostros_no_detectados += 1
    
    def registrar_dispositivo_audio(self, exitoso: bool = True, cantidad: int = 1):
        """Registrar estado de dispositivos audio."""
        with self._lock:
            if exitoso:
                self.dispositivos_audio_activos += cantidad
            else:
                self.dispositivos_audio_fallidos += cantidad
    
    def actualizar_sensores(self, totales: int, operacionales: int):
        """Actualizar estado de sensores."""
        with self._lock:
            self.sensores_totales = totales
            self.sensores_operacionales = operacionales
    
    # ===== VERDAD =====
    def registrar_verificacion(self, exitosa: bool):
        """Registrar resultado de verificación EMET."""
        with self._lock:
            if exitosa:
                self.verificaciones_exitosas += 1
            else:
                self.verificaciones_fallidas += 1
    
    def registrar_bloqueo(self):
        """Registrar bloqueo por incoherencia."""
        with self._lock:
            self.bloques_por_incoherencia += 1
    
    def registrar_contradiccion(self):
        """Registrar contradicción detectada."""
        with self._lock:
            self.contradicciones_detectadas += 1
    
    # ===== COMUNICACIÓN =====
    def registrar_comando(self, exitoso: bool = True, tokens: int = 0):
        """Registrar comando procesado."""
        with self._lock:
            self.comandos_procesados += 1
            if exitoso:
                self.comandos_exitosos += 1
            else:
                self.comandos_fallidos += 1
            if tokens > 0:
                self.tokens_usados += tokens
    
    def registrar_respuesta(self, tokens: int = 0):
        """Registrar respuesta generada."""
        with self._lock:
            self.respuestas_generadas += 1
            if tokens > 0:
                self.tokens_usados += tokens
    
    # ===== INTEGRIDAD =====
    def registrar_purga(self, archivos_purgados: int = 0, cache_mb: float = 0.0,
                       duplicados: int = 0, consolidados: int = 0):
        """Registrar operación de purga."""
        with self._lock:
            self.archivos_purgados += archivos_purgados
            self.cache_limpiado_mb += cache_mb
            self.duplicados_encontrados += duplicados
            self.duplicados_consolidados += consolidados
    
    # ===== APRENDIZAJE =====
    def registrar_patron(self):
        """Registrar patrón detectado."""
        with self._lock:
            self.patrones_detectados += 1
    
    def registrar_recomendacion(self, aplicada: bool = False):
        """Registrar recomendación generada."""
        with self._lock:
            self.recomendaciones_generadas += 1
            if aplicada:
                self.recomendaciones_aplicadas += 1
    
    def actualizar_features(self, usados: int, no_usados: int):
        """Actualizar estado de features."""
        with self._lock:
            self.features_usados = usados
            self.features_no_usados = no_usados
    
    def registrar_confianza_sistema(self, confianza: float):
        """Registrar medida de confianza del sistema."""
        with self._lock:
            self.confianzas_sistema.append(confianza)
            if len(self.confianzas_sistema) > 1000:
                self.confianzas_sistema = self.confianzas_sistema[-1000:]
    
    # ===== COHERENCIA =====
    def registrar_auditoria(self, coherencia_porcentaje: float):
        """Registrar ejecución de auditoría."""
        with self._lock:
            self.auditorias_ejecutadas += 1
            self.coherencia_porcentaje = coherencia_porcentaje
    
    def registrar_incoherencia(self, resuelta: bool = False):
        """Registrar incoherencia detectada."""
        with self._lock:
            self.incoherencias_detectadas += 1
            if resuelta:
                self.incoherencias_resueltas += 1
    
    # ===== SÍNTESIS: OBTENER MÉTRICAS COMPLETAS =====
    def obtener_metricas_completas(self) -> dict:
        """Obtener todas las métricas para RegistroGeneracion."""
        with self._lock:
            uptime = (datetime.now() - self.inicio).total_seconds() / 60
            rendimiento = self.muestras_rendimiento.obtener_estadisticas()
            
            confianza_facial_promedio = (
                sum(self.confianzas_faciales) / len(self.confianzas_faciales)
                if self.confianzas_faciales else 0.0
            )
            
            tasa_exito_comandos = (
                self.comandos_exitosos / self.comandos_procesados
                if self.comandos_procesados > 0 else 0.0
            )
            
            confianza_sistema_promedio = (
                sum(self.confianzas_sistema) / len(self.confianzas_sistema)
                if self.confianzas_sistema else 0.0
            )
            
            return {
                # Coherencia
                "coherencia_porcentaje": self.coherencia_porcentaje,
                "auditorias_ejecutadas": self.auditorias_ejecutadas,
                "incoherencias_detectadas": self.incoherencias_detectadas,
                "incoherencias_resueltas": self.incoherencias_resueltas,
                
                # Rendimiento
                "uptime_minutos": uptime,
                "latencia_promedio_ms": rendimiento["latencia_promedio_ms"],
                "latencia_maxima_ms": rendimiento["latencia_maxima_ms"],
                "pico_cpu_porcentaje": rendimiento["pico_cpu_porcentaje"],
                "pico_memoria_mb": rendimiento["pico_memoria_mb"],
                
                # Percepción
                "rostros_detectados": self.rostros_detectados,
                "rostros_no_detectados": self.rostros_no_detectados,
                "confianza_facial_promedio": confianza_facial_promedio,
                "dispositivos_audio_activos": self.dispositivos_audio_activos,
                "dispositivos_audio_fallidos": self.dispositivos_audio_fallidos,
                "sensores_totales": self.sensores_totales,
                "sensores_operacionales": self.sensores_operacionales,
                
                # Verdad
                "verificaciones_exitosas": self.verificaciones_exitosas,
                "verificaciones_fallidas": self.verificaciones_fallidas,
                "bloques_por_incoherencia": self.bloques_por_incoherencia,
                "contradicciones_detectadas": self.contradicciones_detectadas,
                
                # Comunicación
                "comandos_procesados": self.comandos_procesados,
                "comandos_exitosos": self.comandos_exitosos,
                "comandos_fallidos": self.comandos_fallidos,
                "respuestas_generadas": self.respuestas_generadas,
                "tokens_usados": self.tokens_usados,
                "tasa_exito_comandos": tasa_exito_comandos,
                
                # Integridad
                "archivos_purgados": self.archivos_purgados,
                "cache_limpiado_mb": self.cache_limpiado_mb,
                "duplicados_encontrados": self.duplicados_encontrados,
                "duplicados_consolidados": self.duplicados_consolidados,
                
                # Aprendizaje
                "patrones_detectados": self.patrones_detectados,
                "recomendaciones_generadas": self.recomendaciones_generadas,
                "recomendaciones_aplicadas": self.recomendaciones_aplicadas,
                "features_usados": self.features_usados,
                "features_no_usados": self.features_no_usados,
                "confianza_sistema_promedio": confianza_sistema_promedio,
            }
    
    def resetear(self):
        """Resetear para nueva sesión."""
        with self._lock:
            self.__init__()


# Singleton global
_colector: Optional[ColectorParametrosCompletos] = None


def obtener_colector_completo() -> ColectorParametrosCompletos:
    """Obtener o crear colector global."""
    global _colector
    if _colector is None:
        _colector = ColectorParametrosCompletos()
    return _colector


