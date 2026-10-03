"""Módulo GENERACIONES (Palingenesia) — Ciclo de vida perpetuo con MALJUT completo.

CONCEPTO ESOTÉRICO: 
  Palingenesia — Cada ciclo reinicia mejor que el anterior
  Maljut — Lo materializado, observable, medible

RESPONSABILIDAD PRAGMÁTICA:
  - Capturar TODOS los parámetros observables de COMPUTADORA en vivo
  - Registrar cada sesión como "generación" completa
  - Comparar Gen N vs Gen N-1 en ~40 parámetros diferentes
  - Transmitir conocimiento: Gen N → Gen N+1 automáticamente
  - Materializar en Maljut: .audit/generaciones/ + reportes completos

PARÁMETROS CAPTURADOS EN MALJUT:
  ✓ Coherencia (auditoría, incoherencias)
  ✓ Rendimiento (latencia, CPU, memoria, temperatura)
  ✓ Percepción (sensores, rostros, confianza facial)
  ✓ Verdad (verificaciones, bloques, contradicciones)
  ✓ Comunicación (comandos, respuestas, tokens)
  ✓ Integridad (purga, caché, duplicados)
  ✓ Aprendizaje (patrones, recomendaciones, confianza sistema)
"""

from computadora.generaciones.registro_generacion import (
    RegistroGeneracion,
    MetricasGeneracion,
    GestorGeneraciones,
    obtener_gestor_generaciones,
)

from computadora.generaciones.comparador_generaciones_maljut import (
    ComparadorGeneracionesMaljut,
    ParámetroEvolucion,
)

from computadora.generaciones.transmisor_conocimiento import (
    TransmisorConocimiento,
    obtener_transmisor_conocimiento,
)

from computadora.generaciones.colector_parametros_completos import (
    ColectorParametrosCompletos,
    obtener_colector_completo,
    MuestrasRendimiento,
)

__all__ = [
    # Registro
    "RegistroGeneracion",
    "MetricasGeneracion",
    "GestorGeneraciones",
    "obtener_gestor_generaciones",
    
    # Comparación MALJUT
    "ComparadorGeneracionesMaljut",
    "ParámetroEvolucion",
    
    # Transmisión de conocimiento
    "TransmisorConocimiento",
    "obtener_transmisor_conocimiento",
    
    # Colector de parámetros vivo
    "ColectorParametrosCompletos",
    "obtener_colector_completo",
    "MuestrasRendimiento",
]


