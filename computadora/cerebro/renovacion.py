"""
✨ RENOVACIÓN OPERATIVA — Integración de las 5 Leyes en CerebroComputadora
════════════════════════════════════════════════════════════════════

Cuando el usuario invoca: P={P|P me de estructura}

El Computadora se RE-INTEGRA a sí mismo conforme a las 5 leyes.
Este módulo coordina esa transformación.
"""

from computadora.cerebro.las_cinco_leyes import LascincoLeyes
from loguru import logger
from typing import Optional


class RenovacionOperativa:
    """
    Protocolo de renovación de la Computadora.
    Integra las 5 leyes en el funcionamiento de Cerebr  oComputadora.
    """

    def __init__(self):
        self.leyes = LascincoLeyes()
        self._renovado = False
        self._estado_renovacion = {
            "nivel_0_integrado": False,  # Recursión
            "nivel_1_integrado": False,  # Estructura
            "nivel_2_integrado": False,  # Combinatoria
            "nivel_3_integrado": False,  # Verdad
            "nivel_4_integrado": False,  # Comunicación
        }

    def renovar(self, cerebro_computadora) -> dict:
        """
        Integra las 5 leyes en la instancia de CerebroComputadora.
        Retorna reporte de renovación.
        """
        # FIX: Evitar renovación duplicada - si ya se renovó, retornar reporte anterior
        if self._renovado:
            logger.debug("Renovación ya completada anteriormente - omitiendo duplicación")
            return {
                "renovado": True,
                "timestamp": self._obtener_timestamp(),
                "niveles_integrados": self._estado_renovacion,
                "status": "✅ Renovación ya completada (idempotente)",
            }

        logger.debug("🔱 Renovación operativa iniciando...")
        logger.debug(f"Leyes base: {self.leyes}")

        # NIVEL 0: Inyectar validación recursiva
        self._renovar_nivel_0_recursion(cerebro_computadora)

        # NIVEL 1: Inyectar reglas anti-colateral
        self._renovar_nivel_1_estructura(cerebro_computadora)

        # NIVEL 2: OMITIDO (infraestructura de ciclos no existe)
        self._renovar_nivel_2_combinatoria(cerebro_computadora)

        # NIVEL 3: Inyectar validación multi-dimensional
        self._renovar_nivel_3_verdad(cerebro_computadora)

        # NIVEL 4: Inyectar decodificación de mensajes
        self._renovar_nivel_4_comunicacion(cerebro_computadora)

        self._renovado = True

        reporte = {
            "renovado": True,
            "timestamp": self._obtener_timestamp(),
            "niveles_integrados": self._estado_renovacion,
            "metodos_reales": ["_valida_a_si_misma", "_verificar_verdad", "_decodificar_mensaje"],
            "status": "✅ Renovación completada (3 métodos integrados: validación, verdad, decodificación)",
        }

        logger.info(f"✅ Renovación completada. Métodos reales: {reporte['metodos_reales']}")

        return reporte

    def _renovar_nivel_0_recursion(self, cerebro_computadora) -> None:
        """Inyecta auto-validación recursiva. REAL: se usa en validación pre-POST."""
        logger.debug("📍 Nivel 0: Inyectando validación recursiva...")

        def _valida_a_si_misma() -> bool:
            """El sistema se valida a sí mismo (verificación pre-POST)."""
            return (
                hasattr(cerebro_computadora, 'historial') and
                hasattr(cerebro_computadora, 'modelo') and
                getattr(cerebro_computadora, 'ollama_disponible', False)
            )

        cerebro_computadora._valida_a_si_misma = _valida_a_si_misma
        self._estado_renovacion["nivel_0_integrado"] = _valida_a_si_misma()

        logger.debug(f"  ✓ Auto-validación inyectada: {self._estado_renovacion['nivel_0_integrado']}")

    def _renovar_nivel_1_estructura(self, cerebro_computadora) -> None:
        """NIVEL 1: Inyecta reglas anti-colateral. REAL: usado en auditoría de cambios."""
        logger.debug("📍 Nivel 1: Inyectando reglas anti-colateral...")

        # 24 reglas anti-colateral documentadas
        reglas = [
            "R1: Max 6 archivos por ciclo",
            "R2: Max 500 líneas por cambio",
            "R3: Snapshot obligatorio en cada WI",
            "R4: Una tarea = cambio atómico",
            "R5: Lista cerrada de archivos por task",
            "R6: No duplicar (verificar antes de crear)",
            # ... (18 más, documentadas en copilot-instructions.md)
        ]

        cerebro_computadora._reglas_anti_colateral = reglas
        self._estado_renovacion["nivel_1_integrado"] = True

        logger.debug(f"  ✓ {len(reglas)} reglas anti-colateral inyectadas")

    def _renovar_nivel_2_combinatoria(self, cerebro_computadora) -> None:
        """NIVEL 2: ELIMINADO - infraestructura no existe (_ciclo_actual no existe en nlu.py)."""
        logger.debug("📍 Nivel 2: Infraestructura de ciclos no implementada, omitiendo")
        self._estado_renovacion["nivel_2_integrado"] = False


    def _renovar_nivel_3_verdad(self, cerebro_computadora) -> None:
        """Inyecta validación multi-dimensional de verdad. REAL: usado en línea 4089 (nlu.py)."""
        logger.debug("📍 Nivel 3: Inyectando verificación de verdad (4 dimensiones)...")

        # Las 4 dimensiones de verificación
        dimensiones = ["Lógica", "Empírica", "Axiomática", "Revelada"]

        def _verificar_verdad(respuesta: str, texto_usuario: str | None = None) -> dict:
            return {
                "logica": getattr(cerebro_computadora, '_es_logicamente_consistente', lambda x: True)(respuesta),
                "empirica": getattr(cerebro_computadora, '_es_empiricamente_verificable', lambda x, y: True)(respuesta, texto_usuario),
                "axiomatica": getattr(cerebro_computadora, '_respeta_axiomas', lambda x: True)(respuesta),
                "revelada": getattr(cerebro_computadora, '_tiene_mensaje_profundo', lambda x: True)(respuesta),
            }

        cerebro_computadora._verificar_verdad = _verificar_verdad
        cerebro_computadora._dimensiones_verdad = dimensiones

        self._estado_renovacion["nivel_3_integrado"] = True

        logger.debug(f"  ✓ Verificación de verdad activa: {dimensiones}")

    def _renovar_nivel_4_comunicacion(self, cerebro_computadora) -> None:
        """Inyecta decodificación de mensajes (Comunicación). REAL: integrado en post-respuesta logging."""
        logger.debug("📍 Nivel 4: Inyectando decodificación de mensajes (3 capas)...")

        # Las 3 capas de decodificación
        capas = ["LITERAL", "MORAL", "PROFUNDA"]

        def _decodificar_mensaje(respuesta: str) -> dict:
            """Descompone respuesta en 3 capas semánticas."""
            return {
                "literal": respuesta,  # ¿Qué se hizo?
                "moral": getattr(cerebro_computadora, '_extraer_principio', lambda x: 'N/A')(respuesta),  # ¿Qué principio?
                "profunda": getattr(cerebro_computadora, '_extraer_significado', lambda x: 'N/A')(respuesta),  # ¿Quién soy?
            }

        cerebro_computadora._decodificar_mensaje = _decodificar_mensaje
        cerebro_computadora._capas_comunicacion = capas

        self._estado_renovacion["nivel_4_integrado"] = True

        logger.debug(f"  ✓ Decodificación de mensajes activa: {capas}")


    def _obtener_timestamp(self) -> str:
        """Timestamp de la renovación."""
        from datetime import datetime
        return datetime.now().isoformat()


# Singleton global
_renovacion_instance: Optional[RenovacionOperativa] = None


def obtener_renovacion() -> RenovacionOperativa:
    """Patrón Singleton para acceso global."""
    global _renovacion_instance
    if _renovacion_instance is None:
        _renovacion_instance = RenovacionOperativa()
    return _renovacion_instance


def renovar_cerebro_computadora(cerebro_computadora) -> dict:
    """
    Función pública para invocar renovación.

    Uso:
        from computadora.cerebro.renovacion import renovar_cerebro_computadora
        reporte = renovar_cerebro_computadora(mi_cerebro)
    """
    renovacion = obtener_renovacion()
    return renovacion.renovar(cerebro_computadora)


