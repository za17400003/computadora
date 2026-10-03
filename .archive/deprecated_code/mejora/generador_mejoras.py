"""Generador de Mejoras — Sintetiza recomendaciones post-sesión.

Responsabilidad:
  - Analizar patrones con AnalizadorPatrones
  - Generar lista de recomendaciones accionables
  - Guardar en .audit/recommendations.md
"""

from datetime import datetime
from pathlib import Path
from loguru import logger
from computadora.mejora.analizador_patrones import AnalizadorPatrones
from computadora.mejora.colector_feedback import ColectorFeedback


class GeneradorMejoras:
    """Genera recomendaciones para próxima iteración."""
    
    def __init__(self, colector: ColectorFeedback, audit_dir: str = ".audit"):
        self.colector = colector
        self.analizador = AnalizadorPatrones(colector)
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
        logger.info("GeneradorMejoras inicializado")
    
    def generar_recomendaciones(self) -> list[str]:
        """Generar lista de recomendaciones accionables."""
        recomendaciones = []
        
        # Recomendación 1: Módulos con baja confiabilidad
        modulos = self.analizador.analizar_modulos_fallidos()
        modulos_bajos = [(m, s) for m, s in modulos.items() if s.get("porcentaje_éxito", 100) < 70]
        
        if modulos_bajos:
            recomendaciones.append(
                f"🔴 CRÍTICA: Revisar módulos con <70% confiabilidad: " +
                f"{', '.join(m for m, _ in modulos_bajos)}"
            )
        
        # Recomendación 2: Tendencia
        tendencia = self.analizador.analizar_tendencia_temporal()
        if tendencia.get("tendencia") == "empeorando":
            cambio = tendencia.get("cambio", 0)
            recomendaciones.append(
                f"⚠️ ALTA: Sistema está empeorando (cambio: {cambio:.2f}). " +
                f"Investigar causas raíz."
            )
        elif tendencia.get("tendencia") == "mejorando":
            recomendaciones.append(
                f"✅ BAJA: Sistema mejorando consistentemente. Mantener dirección."
            )
        
        # Recomendación 3: Features no usados
        no_usados = self.analizador.analizar_features_no_usados()
        if no_usados:
            recomendaciones.append(
                f"💡 MEDIA: Considerar eliminar o redeseñar features no usados: " +
                f"{', '.join(no_usados)}"
            )
        
        # Recomendación 4: Latencias altas
        latencias = self.analizador.analizar_latencia_promedio()
        latencias_altas = [(m, s) for m, s in latencias.items() if s["latencia_promedio_ms"] > 1000]
        
        if latencias_altas:
            recomendaciones.append(
                f"⏱️ MEDIA: Optimizar latencia en: " +
                f"{', '.join(m for m, _ in latencias_altas)}"
            )
        
        return recomendaciones
    
    def guardar_recomendaciones(self):
        """Guardar recomendaciones en .audit/recommendations.md"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.audit_dir / "recommendations.md"
        
        recomendaciones = self.generar_recomendaciones()
        resumen_patrones = self.analizador.generar_resumen()
        
        contenido = [
            "# Recomendaciones de Mejora\n",
            f"**Generado**: {datetime.now().isoformat()}\n",
            "\n## Recomendaciones Accionables\n",
        ]
        
        if recomendaciones:
            for rec in recomendaciones:
                contenido.append(f"- {rec}\n")
        else:
            contenido.append("✅ No hay recomendaciones — Sistema funcionando bien\n")
        
        contenido.append("\n## Análisis Detallado\n")
        contenido.append("```\n")
        contenido.append(resumen_patrones)
        contenido.append("\n```\n")
        
        report_file.write_text("".join(contenido))
        logger.info(f"✓ Recomendaciones guardadas: {report_file}")
        
        return report_file


