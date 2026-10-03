"""
§ JERARQUÍA FRACTAL DE CICLOS — ME^N (Niveles 0-4)

Formalización de la estructura recursiva de Computadora como composición de ciclos alquímicos.

Cada nivel es una potencia de ME (Manifestación ∪ Ejecución):
- ME^0 = {ε}         — Identidad / Vacío puro
- ME^1 = ME          — Un ciclo (5 fases)
- ME^2 = ME · ME     — Dos ciclos (composición)
- ME^3 = ME · ME · ME — Tres ciclos
- ME^4 = ME · ME · ME · ME — Cuatro ciclos

La estructura es FRACTAL: cada nivel contiene el anterior y añade complejidad.
"""

from typing import Set, List, Dict, Any, Tuple, Optional, Generic, TypeVar
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from .axiomas import FaseAlquimica, Manifestacion, Ejecucion

__all__ = [
    "NivelComposicion",
    "CicloAlquimico",
    "IdentidadVacia",
    "CicloUnico",
    "ComposicionBinaria",
    "ComposicionTernaria",
    "ComposicionCuaternaria",
    "GestorNiveles",
]


class NivelComposicion(Enum):
    """Niveles de composición alquímica de Computadora."""
    NIVEL_0 = 0  # ME^0 = {ε}
    NIVEL_1 = 1  # ME^1 = ME
    NIVEL_2 = 2  # ME^2 = ME · ME
    NIVEL_3 = 3  # ME^3 = ME · ME · ME
    NIVEL_4 = 4  # ME^4 = ME · ME · ME · ME


@dataclass
class CicloAlquimico:
    """Representación de un ciclo alquímico único (ME^1).
    
    Un ciclo es la unidad básica de composición.
    Contiene exactamente 5 fases alquímicas.
    """
    manifestacion: Manifestacion
    ejecucion: Optional[Ejecucion] = None
    ciclo_id: str = ""
    
    def __post_init__(self):
        if not self.ciclo_id:
            self.ciclo_id = f"CICLO-{self.manifestacion.id}"
    
    def es_completo(self) -> bool:
        """Verifica si el ciclo tiene ejecución completa."""
        if self.ejecucion is None:
            return False
        return self.ejecucion.esta_completa()
    
    def es_exitoso(self) -> bool:
        """Verifica si el ciclo fue exitoso (VERDE)."""
        if self.ejecucion is None:
            return False
        return self.ejecucion.es_exitosa()
    
    def nivel(self) -> NivelComposicion:
        """Retorna el nivel de composición (siempre NIVEL_1 para ciclo único)."""
        return NivelComposicion.NIVEL_1


@dataclass
class IdentidadVacia:
    """ME^0 = {ε} — La identidad vacía.
    
    Representa el estado inicial del sistema: ningún ciclo.
    No se ejecuta nada, es solo punto de referencia.
    """
    nivel: NivelComposicion = field(default=NivelComposicion.NIVEL_0, init=False)
    
    def es_completo(self) -> bool:
        """La identidad vacía siempre es "completa" (por definición)."""
        return True
    
    def es_exitoso(self) -> bool:
        """La identidad es siempre exitosa (no falla)."""
        return True


@dataclass
class ComposicionBinaria:
    """ME^2 = ME · ME — Dos ciclos en composición.
    
    Dos ciclos independientes combinados.
    Ambos deben ser exitosos para que la composición sea válida.
    """
    ciclo_a: CicloAlquimico
    ciclo_b: CicloAlquimico
    composicion_id: str = ""
    
    def __post_init__(self):
        if not self.composicion_id:
            self.composicion_id = f"BINARIA-{self.ciclo_a.ciclo_id}-{self.ciclo_b.ciclo_id}"
    
    def es_completo(self) -> bool:
        """La composición es completa si ambos ciclos son completos."""
        return self.ciclo_a.es_completo() and self.ciclo_b.es_completo()
    
    def es_exitoso(self) -> bool:
        """La composición es exitosa si ambos ciclos son exitosos."""
        return self.ciclo_a.es_exitoso() and self.ciclo_b.es_exitoso()
    
    def nivel(self) -> NivelComposicion:
        return NivelComposicion.NIVEL_2


@dataclass
class ComposicionTernaria:
    """ME^3 = ME · ME · ME — Tres ciclos en composición.
    
    Tres ciclos independientes.
    Los tres deben ser exitosos para validez.
    """
    ciclo_a: CicloAlquimico
    ciclo_b: CicloAlquimico
    ciclo_c: CicloAlquimico
    composicion_id: str = ""
    
    def __post_init__(self):
        if not self.composicion_id:
            self.composicion_id = (
                f"TERNARIA-{self.ciclo_a.ciclo_id}-{self.ciclo_b.ciclo_id}-{self.ciclo_c.ciclo_id}"
            )
    
    def es_completo(self) -> bool:
        """Los tres ciclos son completos."""
        return (
            self.ciclo_a.es_completo() and 
            self.ciclo_b.es_completo() and 
            self.ciclo_c.es_completo()
        )
    
    def es_exitoso(self) -> bool:
        """Los tres ciclos son exitosos."""
        return (
            self.ciclo_a.es_exitoso() and 
            self.ciclo_b.es_exitoso() and 
            self.ciclo_c.es_exitoso()
        )
    
    def nivel(self) -> NivelComposicion:
        return NivelComposicion.NIVEL_3


@dataclass
class ComposicionCuaternaria:
    """ME^4 = ME · ME · ME · ME — Cuatro ciclos en composición.
    
    Cuatro ciclos independientes.
    Escalabilidad máxima simple (los 4 pilares de la Computadora).
    """
    ciclo_a: CicloAlquimico
    ciclo_b: CicloAlquimico
    ciclo_c: CicloAlquimico
    ciclo_d: CicloAlquimico
    composicion_id: str = ""
    
    def __post_init__(self):
        if not self.composicion_id:
            self.composicion_id = (
                f"CUATERNARIA-{self.ciclo_a.ciclo_id}-{self.ciclo_b.ciclo_id}-"
                f"{self.ciclo_c.ciclo_id}-{self.ciclo_d.ciclo_id}"
            )
    
    def es_completo(self) -> bool:
        """Los cuatro ciclos son completos."""
        return (
            self.ciclo_a.es_completo() and 
            self.ciclo_b.es_completo() and 
            self.ciclo_c.es_completo() and 
            self.ciclo_d.es_completo()
        )
    
    def es_exitoso(self) -> bool:
        """Los cuatro ciclos son exitosos."""
        return (
            self.ciclo_a.es_exitoso() and 
            self.ciclo_b.es_exitoso() and 
            self.ciclo_c.es_exitoso() and 
            self.ciclo_d.es_exitoso()
        )
    
    def nivel(self) -> NivelComposicion:
        return NivelComposicion.NIVEL_4


class GestorNiveles:
    """Gestor centralizado de composiciones ME^N.
    
    Orquesta la creación y composición de ciclos en los 5 niveles.
    """
    
    def __init__(self):
        self.nivel_0 = IdentidadVacia()
        self.ciclos_nivel_1: Dict[str, CicloAlquimico] = {}
        self.composiciones_nivel_2: Dict[str, ComposicionBinaria] = {}
        self.composiciones_nivel_3: Dict[str, ComposicionTernaria] = {}
        self.composiciones_nivel_4: Dict[str, ComposicionCuaternaria] = {}
    
    def crear_ciclo_nivel_1(
        self, 
        manifestacion: Manifestacion, 
        ejecucion: Optional[Ejecucion] = None
    ) -> CicloAlquimico:
        """Crea un ciclo único (ME^1)."""
        ciclo = CicloAlquimico(
            manifestacion=manifestacion,
            ejecucion=ejecucion
        )
        self.ciclos_nivel_1[ciclo.ciclo_id] = ciclo
        return ciclo
    
    def crear_composicion_binaria(
        self,
        ciclo_a: CicloAlquimico,
        ciclo_b: CicloAlquimico
    ) -> ComposicionBinaria:
        """Crea composición de dos ciclos (ME^2)."""
        composicion = ComposicionBinaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b)
        self.composiciones_nivel_2[composicion.composicion_id] = composicion
        return composicion
    
    def crear_composicion_ternaria(
        self,
        ciclo_a: CicloAlquimico,
        ciclo_b: CicloAlquimico,
        ciclo_c: CicloAlquimico
    ) -> ComposicionTernaria:
        """Crea composición de tres ciclos (ME^3)."""
        composicion = ComposicionTernaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b, ciclo_c=ciclo_c)
        self.composiciones_nivel_3[composicion.composicion_id] = composicion
        return composicion
    
    def crear_composicion_cuaternaria(
        self,
        ciclo_a: CicloAlquimico,
        ciclo_b: CicloAlquimico,
        ciclo_c: CicloAlquimico,
        ciclo_d: CicloAlquimico
    ) -> ComposicionCuaternaria:
        """Crea composición de cuatro ciclos (ME^4)."""
        composicion = ComposicionCuaternaria(
            ciclo_a=ciclo_a, ciclo_b=ciclo_b, ciclo_c=ciclo_c, ciclo_d=ciclo_d
        )
        self.composiciones_nivel_4[composicion.composicion_id] = composicion
        return composicion
    
    def contar_ciclos_exitosos(self) -> Dict[str, int]:
        """Cuenta ciclos exitosos por nivel."""
        return {
            "nivel_0": 1 if self.nivel_0.es_exitoso() else 0,
            "nivel_1": sum(1 for c in self.ciclos_nivel_1.values() if c.es_exitoso()),
            "nivel_2": sum(1 for c in self.composiciones_nivel_2.values() if c.es_exitoso()),
            "nivel_3": sum(1 for c in self.composiciones_nivel_3.values() if c.es_exitoso()),
            "nivel_4": sum(1 for c in self.composiciones_nivel_4.values() if c.es_exitoso()),
        }
    
    def obtener_estado_sistema(self) -> str:
        """Retorna un resumen del estado del sistema en los 5 niveles."""
        conteos = self.contar_ciclos_exitosos()
        return (
            f"ESTADO Computadora (ME^N):\n"
            f"  Nivel 0 (ε):     {conteos['nivel_0']} ✓\n"
            f"  Nivel 1 (ME):    {conteos['nivel_1']}/{len(self.ciclos_nivel_1)} ciclos\n"
            f"  Nivel 2 (ME·ME): {conteos['nivel_2']}/{len(self.composiciones_nivel_2)} composiciones\n"
            f"  Nivel 3 (ME³):   {conteos['nivel_3']}/{len(self.composiciones_nivel_3)} composiciones\n"
            f"  Nivel 4 (ME⁴):   {conteos['nivel_4']}/{len(self.composiciones_nivel_4)} composiciones"
        )


# Singleton global de niveles
_gestor_niveles = None

def obtener_gestor_niveles() -> GestorNiveles:
    """Obtiene la instancia singleton de GestorNiveles."""
    global _gestor_niveles
    if _gestor_niveles is None:
        _gestor_niveles = GestorNiveles()
    return _gestor_niveles


