"""
COMPUTADORA — Asistente personal de escritorio con IA

§ FUNDACIÓN — Axiomas Primordiales III.7-III.11 + Jerarquía ME^N (Niveles 0-4)
Los axiomas formales y la jerarquía fractal gobiernan toda manifestación y ejecución.
"""

from computadora.fundacion import (
    FaseAlquimica,
    Manifestacion,
    Ejecucion,
    obtener_axiomas,
    NivelComposicion,
    CicloAlquimico,
    IdentidadVacia,
    ComposicionBinaria,
    ComposicionTernaria,
    ComposicionCuaternaria,
    obtener_gestor_niveles,
)

__version__ = "0.2.0"
__nombre__ = "COMPUTADORA"
__axiomas__ = obtener_axiomas()
__niveles__ = obtener_gestor_niveles()

__all__ = [
    "FaseAlquimica",
    "Manifestacion",
    "Ejecucion",
    "obtener_axiomas",
    "NivelComposicion",
    "CicloAlquimico",
    "IdentidadVacia",
    "ComposicionBinaria",
    "ComposicionTernaria",
    "ComposicionCuaternaria",
    "obtener_gestor_niveles",
]


