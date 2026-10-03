"""Comparador de Generaciones MALJUT — Evolución completa de COMPUTADORA.

Compara Gen N vs Gen N-1 en TODOS los parámetros observables:
  - Coherencia (auditoría)
  - Rendimiento (latencia, CPU, memoria)
  - Percepción (sensores, rostros)
  - Verdad (verificaciones, bloques)
  - Comunicación (comandos, respuestas)
  - Integridad (purga, caché)
  - Aprendizaje (patrones, confianza)

Genera reporte detallado de evolución por categoría.
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from loguru import logger
from computadora.generaciones.registro_generacion import (
    RegistroGeneracion,
    MetricasGeneracion,
    GestorGeneraciones,
)


@dataclass
class ParámetroEvolucion:
    """Evolución de un parámetro individual."""
    nombre: str
    categoría: str  # Coherencia, Rendimiento, Percepción, etc.
    anterior: float | int | str
    actual: float | int | str
    delta: Optional[float] = None  # cambio numérico
    tendencia: str = "estable"  # mejora | regresión | estable
    porcentaje_cambio: Optional[float] = None
    bloqueante: bool = False  # si es crítico
    
    def to_dict(self) -> dict:
        """Convertir a dict."""
        return {
            "nombre": self.nombre,
            "categoría": self.categoría,
            "anterior": self.anterior,
            "actual": self.actual,
            "delta": self.delta,
            "tendencia": self.tendencia,
            "porcentaje_cambio": self.porcentaje_cambio,
            "bloqueante": self.bloqueante,
        }


class ComparadorGeneracionesMaljut:
    """Comparador completo de generaciones en Maljut (lo observable)."""
    
    def __init__(self, gestor: GestorGeneraciones):
        self.gestor = gestor
        logger.info("ComparadorGeneracionesMaljut inicializado (Maljut mode)")
    
    def comparar_ultimas(self) -> dict:
        """Comparar generación actual vs anterior en TODOS los parámetros."""
        generaciones = self.gestor.cargar_ultimas_generaciones(n=2)
        
        if len(generaciones) < 2:
            return {
                "estado": "insuficientes_datos",
                "generaciones_disponibles": len(generaciones)
            }
        
        gen_anterior = generaciones[-2]
        gen_actual = generaciones[-1]
        
        return self._comparar_completo(gen_anterior, gen_actual)
    
    def _comparar_completo(self, gen_anterior: RegistroGeneracion, 
                           gen_actual: RegistroGeneracion) -> dict:
        """Comparación exhaustiva en 7 categorías de Maljut."""
        comparacion = {
            "gen_anterior_id": gen_anterior.generacion_id,
            "gen_actual_id": gen_actual.generacion_id,
            "timestamp": datetime.now().isoformat(),
            "categorías": {},
            "tendencia_general": "desconocida",
            "salud_sistema": "desconocida",  # Excelente | Buena | Normal | Débil | Crítica
            "recomendación": "mantener_monitoreo",
        }
        
        if not gen_anterior.metricas or not gen_actual.metricas:
            logger.warning("Métricas incompletas para comparación")
            return comparacion
        
        # Comparar por categoría
        categorías = {
            "Coherencia": self._comparar_coherencia,
            "Rendimiento": self._comparar_rendimiento,
            "Percepción": self._comparar_percepción,
            "Verdad": self._comparar_verdad,
            "Comunicación": self._comparar_comunicación,
            "Integridad": self._comparar_integridad,
            "Aprendizaje": self._comparar_aprendizaje,
        }
        
        for categoria, comparador in categorías.items():
            comparacion["categorías"][categoria] = comparador(
                gen_anterior.metricas, gen_actual.metricas
            )
        
        # Calcular salud general
        comparacion["salud_sistema"] = self._calcular_salud(comparacion["categorías"])
        comparacion["tendencia_general"] = self._calcular_tendencia(comparacion["categorías"])
        
        # Recomendación
        if comparacion["salud_sistema"] == "Crítica":
            comparacion["recomendación"] = "investigar_inmediato"
        elif comparacion["tendencia_general"] == "mejorando":
            comparacion["recomendación"] = "mantener_dirección"
        elif comparacion["tendencia_general"] == "empeorando":
            comparacion["recomendación"] = "ajustar_parámetros"
        
        return comparacion
    
    def _comparar_coherencia(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Coherencia (Keter)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Coherencia General", "Coherencia",
            ant.coherencia_porcentaje, act.coherencia_porcentaje,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Auditorías Ejecutadas", "Coherencia",
            ant.auditorias_ejecutadas, act.auditorias_ejecutadas,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Incoherencias Detectadas", "Coherencia",
            ant.incoherencias_detectadas, act.incoherencias_detectadas,
            es_mejor_mayor=False  # Menos = mejor
        ))
        
        params.append(self._calc_evolucion(
            "Incoherencias Resueltas", "Coherencia",
            ant.incoherencias_resueltas, act.incoherencias_resueltas,
            es_mejor_mayor=True
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_rendimiento(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Rendimiento (físico, observable)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Uptime (minutos)", "Rendimiento",
            ant.uptime_minutos, act.uptime_minutos,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Latencia Promedio (ms)", "Rendimiento",
            ant.latencia_promedio_ms, act.latencia_promedio_ms,
            es_mejor_mayor=False  # Menos latencia = mejor
        ))
        
        params.append(self._calc_evolucion(
            "Latencia Máxima (ms)", "Rendimiento",
            ant.latencia_maxima_ms, act.latencia_maxima_ms,
            es_mejor_mayor=False
        ))
        
        params.append(self._calc_evolucion(
            "Pico CPU (%)", "Rendimiento",
            ant.pico_cpu_porcentaje, act.pico_cpu_porcentaje,
            es_mejor_mayor=False
        ))
        
        params.append(self._calc_evolucion(
            "Pico Memoria (MB)", "Rendimiento",
            ant.pico_memoria_mb, act.pico_memoria_mb,
            es_mejor_mayor=False
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_percepción(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Percepción (sensores, rostros)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Rostros Detectados", "Percepción",
            ant.rostros_detectados, act.rostros_detectados,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Confianza Facial Promedio", "Percepción",
            ant.confianza_facial_promedio, act.confianza_facial_promedio,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Sensores Operacionales", "Percepción",
            ant.sensores_operacionales, act.sensores_operacionales,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Dispositivos Audio Activos", "Percepción",
            ant.dispositivos_audio_activos, act.dispositivos_audio_activos,
            es_mejor_mayor=True
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_verdad(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Verdad (EMET - verificación)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Verificaciones Exitosas", "Verdad",
            ant.verificaciones_exitosas, act.verificaciones_exitosas,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Verificaciones Fallidas", "Verdad",
            ant.verificaciones_fallidas, act.verificaciones_fallidas,
            es_mejor_mayor=False
        ))
        
        params.append(self._calc_evolucion(
            "Bloques por Incoherencia", "Verdad",
            ant.bloques_por_incoherencia, act.bloques_por_incoherencia,
            es_mejor_mayor=False, critico=True  # Menos bloques = mejor
        ))
        
        params.append(self._calc_evolucion(
            "Contradicciones Detectadas", "Verdad",
            ant.contradicciones_detectadas, act.contradicciones_detectadas,
            es_mejor_mayor=False
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_comunicación(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Comunicación (NLU/TTS)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Comandos Procesados", "Comunicación",
            ant.comandos_procesados, act.comandos_procesados,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Tasa Éxito Comandos", "Comunicación",
            ant.tasa_exito_comandos, act.tasa_exito_comandos,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Comandos Fallidos", "Comunicación",
            ant.comandos_fallidos, act.comandos_fallidos,
            es_mejor_mayor=False
        ))
        
        params.append(self._calc_evolucion(
            "Respuestas Generadas", "Comunicación",
            ant.respuestas_generadas, act.respuestas_generadas,
            es_mejor_mayor=True
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_integridad(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Integridad (purga, caché)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Archivos Purgados", "Integridad",
            ant.archivos_purgados, act.archivos_purgados,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Caché Limpiado (MB)", "Integridad",
            ant.cache_limpiado_mb, act.cache_limpiado_mb,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Duplicados Encontrados", "Integridad",
            ant.duplicados_encontrados, act.duplicados_encontrados,
            es_mejor_mayor=False
        ))
        
        params.append(self._calc_evolucion(
            "Duplicados Consolidados", "Integridad",
            ant.duplicados_consolidados, act.duplicados_consolidados,
            es_mejor_mayor=True
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _comparar_aprendizaje(self, ant: MetricasGeneracion, act: MetricasGeneracion) -> dict:
        """Comparar categoria Aprendizaje (mejora continua)."""
        params = []
        
        params.append(self._calc_evolucion(
            "Patrones Detectados", "Aprendizaje",
            ant.patrones_detectados, act.patrones_detectados,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Recomendaciones Generadas", "Aprendizaje",
            ant.recomendaciones_generadas, act.recomendaciones_generadas,
            es_mejor_mayor=True
        ))
        
        params.append(self._calc_evolucion(
            "Recomendaciones Aplicadas", "Aprendizaje",
            ant.recomendaciones_aplicadas, act.recomendaciones_aplicadas,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Confianza Sistema Promedio", "Aprendizaje",
            ant.confianza_sistema_promedio, act.confianza_sistema_promedio,
            es_mejor_mayor=True, critico=True
        ))
        
        params.append(self._calc_evolucion(
            "Features Usados", "Aprendizaje",
            ant.features_usados, act.features_usados,
            es_mejor_mayor=True
        ))
        
        return {
            "parámetros": [p.to_dict() for p in params],
            "mejoras": sum(1 for p in params if p.tendencia == "mejora"),
            "regresiones": sum(1 for p in params if p.tendencia == "regresión"),
        }
    
    def _calc_evolucion(self, nombre: str, categoría: str, 
                        anterior: float | int, actual: float | int,
                        es_mejor_mayor: bool = True,
                        critico: bool = False) -> ParámetroEvolucion:
        """Calcular evolución de un parámetro."""
        delta = actual - anterior
        
        if anterior == 0:
            porcentaje = 100.0 if actual > 0 else 0.0
        else:
            porcentaje = (delta / anterior) * 100 if anterior != 0 else 0.0
        
        # Determinar tendencia
        if delta == 0:
            tendencia = "estable"
        elif (delta > 0 and es_mejor_mayor) or (delta < 0 and not es_mejor_mayor):
            tendencia = "mejora"
        else:
            tendencia = "regresión"
        
        return ParámetroEvolucion(
            nombre=nombre,
            categoría=categoría,
            anterior=anterior,
            actual=actual,
            delta=delta,
            tendencia=tendencia,
            porcentaje_cambio=porcentaje,
            bloqueante=critico and tendencia == "regresión",
        )
    
    def _calcular_salud(self, categorías: dict) -> str:
        """Calcular salud general del sistema."""
        total_mejoras = sum(cat["mejoras"] for cat in categorías.values())
        total_regresiones = sum(cat["regresiones"] for cat in categorías.values())
        
        if total_regresiones > 3:
            return "Crítica"
        elif total_regresiones > 1:
            return "Débil"
        elif total_regresiones > 0:
            return "Normal"
        elif total_mejoras > 5:
            return "Excelente"
        else:
            return "Buena"
    
    def _calcular_tendencia(self, categorías: dict) -> str:
        """Calcular tendencia general."""
        total_mejoras = sum(cat["mejoras"] for cat in categorías.values())
        total_regresiones = sum(cat["regresiones"] for cat in categorías.values())
        
        if total_mejoras > total_regresiones:
            return "mejorando"
        elif total_regresiones > total_mejoras:
            return "empeorando"
        else:
            return "estable"
    
    def generar_reporte_completo(self, comparacion: dict) -> str:
        """Generar reporte completo en Maljut."""
        lineas = [
            "=" * 100,
            f"MALJUT — EVOLUCIÓN COMPLETA DE COMPUTADORA",
            f"Timestamp: {comparacion.get('timestamp')}",
            "=" * 100,
            "",
            f"Gen Anterior: {comparacion['gen_anterior_id']}",
            f"Gen Actual:   {comparacion['gen_actual_id']}",
            f"Salud Sistema: {comparacion['salud_sistema'].upper()}",
            f"Tendencia: {comparacion['tendencia_general'].upper()}",
            f"Recomendación: {comparacion['recomendación']}",
            "",
        ]
        
        for categoría, datos in comparacion["categorías"].items():
            lineas.append(f"📊 {categoría.upper()} (+{datos['mejoras']}/-{datos['regresiones']})")
            lineas.append("-" * 100)
            
            for param in datos["parámetros"]:
                símbolo = "↑" if param["tendencia"] == "mejora" else ("↓" if param["tendencia"] == "regresión" else "→")
                bloqueante = "[!] " if param["bloqueante"] else ""
                
                lineas.append(
                    f"  {bloqueante}{símbolo} {param['nombre']:<40} "
                    f"Anterior: {param['anterior']:<10} Actual: {param['actual']:<10} "
                    f"Δ{param['delta']:+.1f} ({param['porcentaje_cambio']:+.0f}%)"
                )
            
            lineas.append("")
        
        lineas.append("=" * 100)
        lineas.append("RESUMEN: Sistema observado en Maljut (lo materializado)")
        lineas.append("=" * 100)
        
        return "\n".join(lineas)


