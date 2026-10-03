"""Transmisor de Conocimiento — Pre-boot init con lecciones de generación anterior.

Responsabilidad:
  - Leer generación anterior (.audit/generaciones/gen_*.json)
  - Extraer lecciones: qué funcionó, qué falló
  - CARGAR en memoria antes del boot
  - Usar en toma de decisiones (ej: parámetros optimizados)
"""

import json
from pathlib import Path
from typing import Optional
from loguru import logger
from computadora.generaciones.registro_generacion import GestorGeneraciones


class TransmisorConocimiento:
    """Transmite conocimiento de Gen N → Gen N+1."""
    
    def __init__(self, gestor: GestorGeneraciones):
        self.gestor = gestor
        self.lecciones_cargadas: dict = {}
        logger.info("TransmisorConocimiento inicializado")
    
    def cargar_lecciones_generacion_anterior(self) -> dict:
        """Cargar y sintetizar lecciones de la generación anterior."""
        generaciones = self.gestor.cargar_ultimas_generaciones(n=1)
        
        if not generaciones:
            logger.info("Primera generación — sin lecciones previas")
            self.lecciones_cargadas = {
                "es_primera": True,
                "lecciones": [],
                "parametros_optimizados": {},
            }
            return self.lecciones_cargadas
        
        gen_anterior = generaciones[0]
        
        lecciones = {
            "es_primera": False,
            "generacion_anterior_id": gen_anterior.generacion_id,
            "lecciones": [],
            "parametros_optimizados": {},
            "problemas_a_evitar": [],
        }
        
        # Lección 1: Errores previos
        if gen_anterior.errores_encontrados:
            lecciones["problemas_a_evitar"] = gen_anterior.errores_encontrados[-5:]  # Últimos 5
            lecciones["lecciones"].append(
                f"Se encontraron {len(gen_anterior.errores_encontrados)} errores previos — evitar repetir"
            )
        
        # Lección 2: Mejoras aplicadas
        if gen_anterior.mejoras_aplicadas:
            lecciones["lecciones"].append(
                f"Se aplicaron {len(gen_anterior.mejoras_aplicadas)} mejoras — verificar si siguen activas"
            )
        
        # Lección 3: Coherencia
        if gen_anterior.metricas:
            coh = gen_anterior.metricas.coherencia_porcentaje
            if coh < 80:
                lecciones["lecciones"].append(f"Coherencia anterior baja ({coh}%) — auditar")
                lecciones["parametros_optimizados"]["audit_intervalo_s"] = 30  # Más frecuente
            else:
                lecciones["parametros_optimizados"]["audit_intervalo_s"] = 60  # Normal
        
        # Lección 4: Uptime
        if gen_anterior.duracion_minutos:
            uptime = gen_anterior.duracion_minutos
            if uptime < 60:
                lecciones["lecciones"].append(f"Sesión anterior corta ({uptime:.1f}min) — investigar")
            lecciones["parametros_optimizados"]["expected_uptime_min"] = uptime
        
        # Lección 5: Estado final
        if gen_anterior.estado_final != "shutdown_normal":
            lecciones["lecciones"].append(
                f"Sesión anterior terminó en estado: {gen_anterior.estado_final} — verificar"
            )
            lecciones["parametros_optimizados"]["boot_cautela"] = True
        
        self.lecciones_cargadas = lecciones
        
        logger.info(f"✓ Lecciones cargadas de gen {gen_anterior.generacion_id}")
        logger.info(f"  {len(lecciones['lecciones'])} lecciones extraídas")
        
        return lecciones
    
    def obtener_parametro_optimizado(self, parametro: str, default: any = None) -> any:
        """Obtener parámetro optimizado de lecciones previas."""
        return self.lecciones_cargadas.get("parametros_optimizados", {}).get(parametro, default)
    
    def generar_reporte_lecciones(self) -> str:
        """Generar reporte legible de lecciones transmitidas."""
        lineas = [
            "=" * 80,
            "LECCIONES TRANSMITIDAS — Pre-boot Initialization",
            "=" * 80,
            "",
        ]
        
        if self.lecciones_cargadas.get("es_primera"):
            lineas.append("🌱 PRIMERA GENERACIÓN — Sistema sin historia previa")
            lineas.append("   (Próximas sesiones tendrán contexto de aprendizaje)")
        else:
            gen_id = self.lecciones_cargadas.get("generacion_anterior_id")
            lineas.append(f"📚 LECCIONES DE GENERACIÓN ANTERIOR: {gen_id}")
            lineas.append("")
            
            lecciones = self.lecciones_cargadas.get("lecciones", [])
            if lecciones:
                lineas.append("📖 LECCIONES APRENDIDAS:")
                for leccion in lecciones:
                    lineas.append(f"  • {leccion}")
            else:
                lineas.append("✅ Sin lecciones críticas — sistema funcionó bien")
            
            lineas.append("")
            
            problemas = self.lecciones_cargadas.get("problemas_a_evitar", [])
            if problemas:
                lineas.append("⚠️ PROBLEMAS A EVITAR:")
                for prob in problemas:
                    lineas.append(f"  • {prob}")
            
            lineas.append("")
            
            params = self.lecciones_cargadas.get("parametros_optimizados", {})
            if params:
                lineas.append("⚙️ PARÁMETROS OPTIMIZADOS (aplicados a esta sesión):")
                for param, valor in params.items():
                    lineas.append(f"  {param}: {valor}")
        
        lineas.append("")
        lineas.append("=" * 80)
        
        return "\n".join(lineas)
    
    def guardar_reporte(self, audit_dir: str = ".audit"):
        """Guardar reporte de lecciones."""
        reporte_file = Path(audit_dir) / "lecciones_transmitidas.md"
        reporte_file.write_text(self.generar_reporte_lecciones())
        logger.info(f"✓ Reporte de lecciones: {reporte_file}")


# Singleton global
_transmisor: TransmisorConocimiento | None = None


def obtener_transmisor_conocimiento(gestor: GestorGeneraciones) -> TransmisorConocimiento:
    """Obtener o crear transmisor global."""
    global _transmisor
    if _transmisor is None:
        _transmisor = TransmisorConocimiento(gestor)
    return _transmisor


