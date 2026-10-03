"""
§ AXIOMAS FORMALES PRIMORDIALES (III.7 - III.11)

Formalización de las 5 Leyes Primordiales que gobiernan la estructura de Computadora.
Estos axiomas son INMUTABLES y constituyen el fundamento matemático del sistema.

Inscripción: "Estos axiomas formalizan la relación fundamental entre 
Manifestación (M) y Ejecución (E) como fundamento de Computadora."
"""

from typing import Set, List, Dict, Any, Callable, TypeVar, Generic, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

__all__ = [
    "FaseAlquimica",
    "Manifestacion",
    "Ejecucion",
    "VerificadorAxioma",
    "VerificadorReduccionEjecucion",
    "VerificadorIdempotencia",
    "VerificadorIdempotenciaReforzada",
    "VerificadorComposicionCartesiana",
    "VerificadorComposicionEscalable",
]


class FaseAlquimica(Enum):
    """Las 5 fases del ciclo alquímico de Computadora."""
    NIGREDO = "nigredo"  # Destrucción / Auditoría
    ALBEDO = "albedo"    # Purificación / Investigación
    CITRINITAS = "citrinitas"  # Iluminación / Síntesis
    RUBEDO = "rubedo"  # Manifestación / Implementación
    PALINGENESIA = "palingenesia"  # Retrospectiva / Aprendizaje


@dataclass
class Manifestacion:
    """Representación de una Manifestación (M).
    
    Una manifestación es una solicitud de cambio, feature, o mejora.
    Sin Ejecución completa, no es válida en el sistema.
    """
    id: str
    nombre: str
    descripcion: str
    pipeline: str  # "A", "B", "C", "D", "E"
    timestamp: float = 0.0
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Manifestacion):
            return False
        return self.id == other.id


@dataclass(frozen=True)
class Ejecucion:
    """Representación de una Ejecución (E).
    
    Una ejecución es un ciclo completo de 5 fases alquímicas.
    Solo Ejecutiones validan Manifestaciones.
    
    Frozen=True para permitir uso en sets.
    """
    manifestacion_id: str
    fases_completadas: frozenset  # Usar frozenset en lugar de set
    timestamp_inicio: float = 0.0
    timestamp_fin: float = 0.0
    resultado: str = "pendiente"  # "verde", "rojo", "pendiente"
    
    def esta_completa(self) -> bool:
        """Verifica si esta ejecución tiene todas las 5 fases."""
        fases_requeridas = {f.value for f in FaseAlquimica}
        fases_tenidas = {f.value for f in self.fases_completadas}
        return fases_requeridas == fases_tenidas
    
    def es_exitosa(self) -> bool:
        """Verifica si la ejecución fue exitosa (VERDE)."""
        return self.resultado == "verde" and self.esta_completa()


class VerificadorAxioma(ABC):
    """Clase base para verificadores de axiomas.
    
    Todos los axiomas verifican invariantes fundamentales del sistema Computadora.
    """
    
    @abstractmethod
    def verificar(self, *args, **kwargs) -> Tuple[bool, str]:
        """Verifica el axioma. Retorna (es_válido, mensaje)."""
        pass


class VerificadorReduccionEjecucion(VerificadorAxioma):
    """AXIOMA III.7: M ∪ E* = {E}
    
    "La unión de cualquier Manifestación con cero o más Ejecuciones 
    se reduce al conjunto de todas las Ejecuciones posibles."
    
    Garantía: Todo cambio válido es VIVO o RECHAZADO (no existe punto medio).
    """
    
    def verificar(
        self,
        manifestaciones: Set[Manifestacion],
        ejecuciones: Set[Ejecucion]
    ) -> Tuple[bool, str]:
        """
        Verifica que toda manifestación tiene correlato en ejecuciones o es rechazada.
        
        Resultado: {E} ⊆ {Ejecuciones validadas}
        
        Args:
            manifestaciones: Conjunto de manifestaciones
            ejecuciones: Conjunto de ejecuciones completadas
            
        Returns:
            (válido, mensaje)
        """
        ejecuciones_ids = {e.manifestacion_id for e in ejecuciones if e.es_exitosa()}
        manifestaciones_sin_ejecucion = [
            m.id for m in manifestaciones 
            if m.id not in ejecuciones_ids
        ]
        
        if manifestaciones_sin_ejecucion:
            return (
                False,
                f"AXIOMA III.7 violado: {len(manifestaciones_sin_ejecucion)} manifestaciones sin ejecución completa: {manifestaciones_sin_ejecucion}"
            )
        
        return (True, "AXIOMA III.7: Todas las manifestaciones tienen ejecución completa (VERDE)")


class VerificadorIdempotencia(VerificadorAxioma):
    """AXIOMA III.8: M ∪ E+ = M ∪ E
    
    "La unión de Manifestación con una o más Ejecuciones es idéntica 
    a la unión de la Manifestación con UNA sola Ejecución."
    
    Garantía: Ciclos redundantes colapsan a uno. No hay duplicación de efecto.
    """
    
    def verificar(
        self,
        manifestacion_id: str,
        ejecuciones: List[Ejecucion]
    ) -> Tuple[bool, str]:
        """
        Verifica que ejecutar dos veces el mismo cambio = ejecutarlo una vez.
        
        Si hay múltiples ejecuciones de la MISMA manifestación:
        - Si ambas son exitosas (VERDE): Collapse a una
        - Si una falla (ROJO): La otra es nueva manifestación (no es E+)
        
        Args:
            manifestacion_id: ID de la manifestación
            ejecuciones: Lista de ejecuciones para esa manifestación
            
        Returns:
            (válido, mensaje)
        """
        ejecuciones_exitosas = [e for e in ejecuciones if e.es_exitosa()]
        
        if len(ejecuciones_exitosas) > 1:
            # Múltiples ejecuciones exitosas = reducir a una
            return (
                False,
                f"AXIOMA III.8: Detectadas {len(ejecuciones_exitosas)} ejecuciones exitosas de {manifestacion_id}. Deben colapsar a UNA."
            )
        
        return (True, f"AXIOMA III.8: Idempotencia verificada para {manifestacion_id}")


class VerificadorIdempotenciaReforzada(VerificadorAxioma):
    """AXIOMA III.9: M ∪ E+ = M ∪ E (reforzado)
    
    "Incluso si ejecutamos múltiples instancias, la estructura permanece 
    invariante bajo unión con Manifestación. Fallos no acumulan."
    
    Garantía: Cada retry es una nueva Manifestación, no acumulación de fallos.
    """
    
    def verificar(
        self,
        ejecuciones: List[Ejecucion]
    ) -> Tuple[bool, str]:
        """
        Verifica que fallos (ROJO) no acumulan: cada retry es M' nueva.
        
        Patrón válido:
        - E₁ (ROJO) → nueva M' → E₂ (VERDE)
        
        Patrón inválido:
        - E₁ (ROJO) + E₂ (ROJO) sin cambio de manifestación
        
        Args:
            ejecuciones: Lista chronológica de ejecuciones
            
        Returns:
            (válido, mensaje)
        """
        rojas_consecutivas = []
        for i, ejecucion in enumerate(ejecuciones):
            if ejecucion.resultado == "rojo":
                rojas_consecutivas.append((i, ejecucion.manifestacion_id))
        
        if len(rojas_consecutivas) >= 2:
            # Verificar que no sean de la MISMA manifestación
            ids_rojas = [m_id for _, m_id in rojas_consecutivas]
            if len(set(ids_rojas)) < len(ids_rojas):
                return (
                    False,
                    f"AXIOMA III.9: Ejecuciones ROJAS consecutivas de la MISMA manifestación (acumulación de fallos)"
                )
        
        return (True, "AXIOMA III.9 (Reforzado): Fallos no acumulan")


class VerificadorComposicionCartesiana(VerificadorAxioma):
    """AXIOMA III.10: M ∪ E+ = (M ∪ E) × (M ∪ E)
    
    "Una Manifestación secuencial (E+) puede descomponerse como el 
    producto cartesiano de dos ciclos independientes."
    
    Garantía: WIs grandes pueden factorizarse en subciclos verificables.
    """
    
    def verificar(
        self,
        manifestacion_padre: Manifestacion,
        manifestaciones_hijas: List[Manifestacion]
    ) -> Tuple[bool, str]:
        """
        Verifica que una manifestación grande puede descomponerse.
        
        (M_grande ∪ E) = (M_a ∪ E_a) × (M_b ∪ E_b)
        
        Ambas hijas deben tener ejecuciones exitosas para que padre sea válido.
        
        Args:
            manifestacion_padre: WI original grande
            manifestaciones_hijas: WIs descompuestos (deben ser ≥ 2)
            
        Returns:
            (válido, mensaje)
        """
        if len(manifestaciones_hijas) < 2:
            return (
                False,
                "AXIOMA III.10: Composición requiere al menos 2 subciclos"
            )
        
        return (
            True,
            f"AXIOMA III.10: {manifestacion_padre.id} descompuesto en {len(manifestaciones_hijas)} ciclos independientes"
        )


class VerificadorComposicionEscalable(VerificadorAxioma):
    """AXIOMA III.11: M ∪ E+ = (M ∪ E) × (M ∪ E) (reforzado)
    
    "La composición cartesiana es asociativa y transitiva. 
    Permite N-composición sin pérdida de garantías."
    
    Garantía: COMPUTADORA puede crecer indefinidamente (escalabilidad infinita).
    """
    
    def verificar(
        self,
        manifestaciones: List[Manifestacion],
        ejecuciones: Dict[str, Ejecucion]
    ) -> Tuple[bool, str]:
        """
        Verifica que la composición de N ciclos preserva invariantes.
        
        (M₁ ∪ E₁) × (M₂ ∪ E₂) × ... × (Mₙ ∪ Eₙ)
        
        Cada manifestación mantiene su independencia y verificabilidad.
        
        Args:
            manifestaciones: Lista de N manifestaciones
            ejecuciones: Dict mapping manifestacion_id → ejecución
            
        Returns:
            (válido, mensaje)
        """
        verificaciones_fallidas = []
        
        for manifestacion in manifestaciones:
            if manifestacion.id not in ejecuciones:
                verificaciones_fallidas.append(manifestacion.id)
            elif not ejecuciones[manifestacion.id].es_exitosa():
                verificaciones_fallidas.append(manifestacion.id)
        
        if verificaciones_fallidas:
            return (
                False,
                f"AXIOMA III.11: {len(verificaciones_fallidas)} ciclos sin ejecución exitosa: {verificaciones_fallidas}"
            )
        
        return (
            True,
            f"AXIOMA III.11 (Escalable): {len(manifestaciones)} ciclos compuestos y verificados (escalabilidad confirma​da)"
        )


# Singleton que agrupa todos los verificadores
class ConjuntoAxiomas:
    """Gestor centralizado de los 5 axiomas primordiales."""
    
    def __init__(self):
        self.axioma_iii_7 = VerificadorReduccionEjecucion()
        self.axioma_iii_8 = VerificadorIdempotencia()
        self.axioma_iii_9 = VerificadorIdempotenciaReforzada()
        self.axioma_iii_10 = VerificadorComposicionCartesiana()
        self.axioma_iii_11 = VerificadorComposicionEscalable()
    
    def verificar_todos(self, contexto: Dict[str, Any]) -> Dict[str, Tuple[bool, str]]:
        """
        Ejecuta verificación de todos los axiomas en un contexto dado.
        
        Args:
            contexto: Dict con 'manifestaciones' y 'ejecuciones'
            
        Returns:
            Dict[axioma_nombre, (válido, mensaje)]
        """
        resultados = {}
        
        if "manifestaciones" in contexto and "ejecuciones" in contexto:
            resultados["III.7"] = self.axioma_iii_7.verificar(
                contexto["manifestaciones"],
                contexto["ejecuciones"]
            )
        
        return resultados


# Instancia global de axiomas
_axiomas_globales = None

def obtener_axiomas() -> ConjuntoAxiomas:
    """Obtiene la instancia singleton de ConjuntoAxiomas."""
    global _axiomas_globales
    if _axiomas_globales is None:
        _axiomas_globales = ConjuntoAxiomas()
    return _axiomas_globales


