"""Analizador de Patrones — Extrae insights del feedback.

Detecta:
  1. Qué preguntas/acciones repite usuario (patrón de comportamiento)
  2. Qué respuestas fueron útiles (correlación)
  3. Qué módulos fallan frecuentemente (estadística de confiabilidad)
  4. Horarios donde rendimiento cae (temporal)
  5. Tendencias: ¿Sistema mejorando o empeorando?
"""

from datetime import datetime
from collections import Counter, defaultdict
from loguru import logger
from computadora.mejora.colector_feedback import ColectorFeedback, EventoFeedback


class AnalizadorPatrones:
    """Extractor de patrones del feedback."""
    
    def __init__(self, colector: ColectorFeedback):
        self.colector = colector
        logger.info("AnalizadorPatrones inicializado")
    
    def analizar_modulos_fallidos(self) -> dict[str, dict]:
        """Detectar qué módulos fallan frecuentemente."""
        confiabilidad = defaultdict(lambda: {"total": 0, "éxitos": 0, "fallos": 0})
        
        for evento in self.colector.eventos:
            if evento.modulo_origen:
                modulo = evento.modulo_origen
                confiabilidad[modulo]["total"] += 1
                
                # Valor > 0.5 = éxito
                if evento.valor > 0.5:
                    confiabilidad[modulo]["éxitos"] += 1
                else:
                    confiabilidad[modulo]["fallos"] += 1
        
        # Calcular porcentaje de éxito
        for modulo in confiabilidad:
            total = confiabilidad[modulo]["total"]
            if total > 0:
                confiabilidad[modulo]["porcentaje_éxito"] = (
                    confiabilidad[modulo]["éxitos"] / total * 100
                )
        
        return dict(confiabilidad)
    
    def analizar_tendencia_temporal(self) -> dict:
        """Detectar si sistema mejora o empeora con el tiempo."""
        if len(self.colector.eventos) < 10:
            return {"estado": "datos_insuficientes"}
        
        # Dividir en primeros y últimos 10%
        n = len(self.colector.eventos)
        primeros = self.colector.eventos[:n // 10]
        ultimos = self.colector.eventos[-n // 10:]
        
        valor_promedio_primeros = sum(e.valor for e in primeros) / len(primeros)
        valor_promedio_ultimos = sum(e.valor for e in ultimos) / len(ultimos)
        
        cambio = valor_promedio_ultimos - valor_promedio_primeros
        
        if cambio > 0.1:
            tendencia = "mejorando"
        elif cambio < -0.1:
            tendencia = "empeorando"
        else:
            tendencia = "estable"
        
        return {
            "tendencia": tendencia,
            "cambio": cambio,
            "valor_inicial": valor_promedio_primeros,
            "valor_actual": valor_promedio_ultimos,
        }
    
    def analizar_features_no_usados(self) -> list[str]:
        """Detectar features que no se usan (bajo engagement)."""
        no_usados = []
        
        eventos_uso = [e for e in self.colector.eventos if e.tipo == "uso"]
        features_count = Counter(e.modulo_origen for e in eventos_uso)
        
        for feature, count in features_count.items():
            # Si menos de 1% de uso → probablemente no se usa
            if count < len(eventos_uso) * 0.01:
                no_usados.append(feature)
        
        return no_usados
    
    def analizar_latencia_promedio(self) -> dict:
        """Detectar latencia promedio por módulo."""
        latencias = defaultdict(list)
        
        for evento in self.colector.eventos:
            if evento.tipo == "sistema_implícito" and evento.contexto:
                latencia = evento.contexto.get("latencia_ms")
                if latencia:
                    latencias[evento.modulo_origen].append(latencia)
        
        # Calcular promedios
        promedios = {}
        for modulo, lats in latencias.items():
            promedios[modulo] = {
                "latencia_promedio_ms": sum(lats) / len(lats),
                "latencia_min_ms": min(lats),
                "latencia_max_ms": max(lats),
                "n_muestras": len(lats),
            }
        
        return promedios
    
    def generar_resumen(self) -> str:
        """Generar resumen legible de patrones."""
        resumen = []
        
        resumen.append("=" * 80)
        resumen.append(f"ANÁLISIS DE PATRONES — {datetime.now().isoformat()}")
        resumen.append("=" * 80)
        resumen.append("")
        
        # Confiabilidad de módulos
        modulos = self.analizar_modulos_fallidos()
        resumen.append("📊 CONFIABILIDAD POR MÓDULO:")
        for modulo, stats in sorted(modulos.items(), key=lambda x: x[1].get("porcentaje_éxito", 0)):
            pct = stats.get("porcentaje_éxito", 0)
            resumen.append(f"  {modulo}: {pct:.1f}% ({stats['éxitos']}/{stats['total']})")
        resumen.append("")
        
        # Tendencia
        tendencia = self.analizar_tendencia_temporal()
        resumen.append("📈 TENDENCIA TEMPORAL:")
        resumen.append(f"  Estado: {tendencia.get('tendencia', 'N/A')}")
        resumen.append(f"  Cambio: {tendencia.get('cambio', 0):.2f}")
        resumen.append("")
        
        # Features no usados
        no_usados = self.analizar_features_no_usados()
        if no_usados:
            resumen.append("⚠️ FEATURES POSIBLEMENTE NO USADOS:")
            for f in no_usados:
                resumen.append(f"  - {f}")
            resumen.append("")
        
        # Latencias
        latencias = self.analizar_latencia_promedio()
        if latencias:
            resumen.append("⏱️ LATENCIA PROMEDIO (ms):")
            for modulo, stats in latencias.items():
                resumen.append(f"  {modulo}: {stats['latencia_promedio_ms']:.1f}ms " +
                             f"(min: {stats['latencia_min_ms']:.1f}, max: {stats['latencia_max_ms']:.1f})")
            resumen.append("")
        
        resumen.append("=" * 80)
        
        return "\n".join(resumen)


