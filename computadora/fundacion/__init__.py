"""
§ FUNDACIÓN DE COMPUTADORA

Módulo de fundación que contiene:
1. Los axiomas primordiales (III.7-III.11)
2. La jerarquía fractal de ciclos (ME^N, Niveles 0-4)

Estructura de Computadora:
- Nivel 0: ε (identidad vacía)
- Nivel 1: ME (un ciclo alquímico)
- Nivel 2: ME · ME (dos ciclos)
- Nivel 3: ME · ME · ME (tres ciclos)
- Nivel 4: ME · ME · ME · ME (cuatro ciclos)

Todos los axiomas se aplican recursivamente a cada nivel.
"""

from .axiomas import (
    FaseAlquimica,
    Manifestacion,
    Ejecucion,
    VerificadorAxioma,
    VerificadorReduccionEjecucion,
    VerificadorIdempotencia,
    VerificadorIdempotenciaReforzada,
    VerificadorComposicionCartesiana,
    VerificadorComposicionEscalable,
    ConjuntoAxiomas,
    obtener_axiomas,
)

from .niveles import (
    NivelComposicion,
    CicloAlquimico,
    IdentidadVacia,
    ComposicionBinaria,
    ComposicionTernaria,
    ComposicionCuaternaria,
    GestorNiveles,
    obtener_gestor_niveles,
)

__all__ = [
    # Axiomas
    "FaseAlquimica",
    "Manifestacion",
    "Ejecucion",
    "VerificadorAxioma",
    "VerificadorReduccionEjecucion",
    "VerificadorIdempotencia",
    "VerificadorIdempotenciaReforzada",
    "VerificadorComposicionCartesiana",
    "VerificadorComposicionEscalable",
    "ConjuntoAxiomas",
    "obtener_axiomas",
    # Niveles
    "NivelComposicion",
    "CicloAlquimico",
    "IdentidadVacia",
    "ComposicionBinaria",
    "ComposicionTernaria",
    "ComposicionCuaternaria",
    "GestorNiveles",
    "obtener_gestor_niveles",
]

__version__ = "1.1.0"
__author__ = "GitHub Copilot CEO/CTO"
__description__ = "Fundación de la Computadora: Axiomas III.7-III.11 + Jerarquía ME^N (Niveles 0-4)"



