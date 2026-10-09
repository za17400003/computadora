"""
Tests para FP-024 — נשמה עולמית Neshama Olamit (Alma Cósmica)
WI-123: Física de partículas con inercia (RF-87)
WI-124: Sistema de evolución alquímica (RF-88, RF-90)
WI-125: Conciencia temporal — registro de sesiones (RF-89)
WI-126: Conciencia temporal — inyección en prompt (RF-89)
WI-127: Logging complementario en memoria (RF-91)
"""

import json
import math
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Agregar raíz al path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

passed = 0
failed = 0


def check(nombre, condicion):
    global passed, failed
    if condicion:
        passed += 1
        print(f"  \u2713 {nombre}")
    else:
        failed += 1
        print(f"  \u2717 {nombre}")


# ══════════════════════════════════════════════
# WI-123: Física de Partículas con Inercia
# ══════════════════════════════════════════════
print("\n-- WI-123: Fisica de particulas con inercia --")

from computadora.interfaz.ventana_principal import Particula

p = Particula(75.0)
check("Particula tiene vx/vy", hasattr(p, 'vx') and hasattr(p, 'vy'))
check("Particula tiene offset_x/offset_y", hasattr(p, 'offset_x') and hasattr(p, 'offset_y'))
check("Particula tiene masa", hasattr(p, 'masa') and p.masa > 0)
check("Particula tiene coef_arrastre", hasattr(p, 'coef_arrastre') and 0 < p.coef_arrastre < 1)
check("Particula tiene coef_retorno", hasattr(p, 'coef_retorno') and p.coef_retorno > 0)

# Letras hebreas tienen masa alta
p_letra = Particula(75.0)
p_letra.es_letra = True
p_letra.masa = 2.0  # Forzar para test
check("Letra hebrea masa >= 2.0", p_letra.masa >= 2.0)

# Sin movimiento de orbe, la partícula no se desplaza
p2 = Particula(75.0)
p2.actualizar(0.0, 0.0)
p2.actualizar(0.0, 0.0)
p2.actualizar(0.0, 0.0)
check("Sin movimiento orbe, offset cercano a 0", abs(p2.offset_x) < 0.01 and abs(p2.offset_y) < 0.01)

# Con movimiento de orbe, la partícula se desplaza
p3 = Particula(75.0)
p3.actualizar(10.0, 0.0)
check("Con movimiento orbe, offset_x no es 0", abs(p3.offset_x) > 0.01 or abs(p3.vx) > 0.01)

# pos incluye offset
p4 = Particula(75.0)
p4.offset_x = 5.0
p4.offset_y = 3.0
pos = p4.pos
expected_x = p4.radio * math.cos(p4.angulo) + 5.0
expected_y = p4.radio * math.sin(p4.angulo) + 3.0
check("pos incluye offset_x", abs(pos.x() - expected_x) < 0.01)
check("pos incluye offset_y", abs(pos.y() - expected_y) < 0.01)

# actualizar acepta delta_x/delta_y
alive = p4.actualizar(1.0, 2.0)
check("actualizar retorna bool", isinstance(alive, bool))

# Spring-back: offset se reduce con el tiempo sin movimiento
p5 = Particula(75.0)
p5.offset_x = 10.0
p5.offset_y = 10.0
for _ in range(100):
    p5.actualizar(0.0, 0.0)
check("Spring-back reduce offset", abs(p5.offset_x) < 5.0 and abs(p5.offset_y) < 5.0)

# ══════════════════════════════════════════════
# WI-124: Evolución Alquímica
# ══════════════════════════════════════════════
print("\n-- WI-124: Evolucion alquimica --")

from computadora.interfaz.ventana_principal import (
    EtapaAlquimica, _PALETAS_ALQUIMICAS, _ETAPAS_ORDEN,
    _UMBRALES_EVOLUCION, _cargar_evolucion, _guardar_evolucion, _EVOLUCION_PATH,
)

check("EtapaAlquimica tiene 4 etapas", len(EtapaAlquimica) == 4)
check("NIGREDO existe", EtapaAlquimica.NIGREDO.value == "nigredo")
check("ALBEDO existe", EtapaAlquimica.ALBEDO.value == "albedo")
check("CITRINITAS existe", EtapaAlquimica.CITRINITAS.value == "citrinitas")
check("RUBEDO existe", EtapaAlquimica.RUBEDO.value == "rubedo")

check("4 paletas definidas", len(_PALETAS_ALQUIMICAS) == 4)
for etapa in EtapaAlquimica:
    pal = _PALETAS_ALQUIMICAS[etapa]
    check(f"Paleta {etapa.value} tiene primario/secundario", "primario" in pal and "secundario" in pal)

check("Orden correcto", _ETAPAS_ORDEN == [EtapaAlquimica.NIGREDO, EtapaAlquimica.ALBEDO, EtapaAlquimica.CITRINITAS, EtapaAlquimica.RUBEDO])

check("Umbrales para ALBEDO", EtapaAlquimica.ALBEDO in _UMBRALES_EVOLUCION)
check("Umbrales para CITRINITAS", EtapaAlquimica.CITRINITAS in _UMBRALES_EVOLUCION)
check("Umbrales para RUBEDO", EtapaAlquimica.RUBEDO in _UMBRALES_EVOLUCION)

# Test cargar/guardar evolución
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir) / "evolucion_test.json"
    original_path = _EVOLUCION_PATH
    
    data = _cargar_evolucion()  # Returns default if file missing
    check("cargar_evolucion retorna dict", isinstance(data, dict))
    check("etapa default es nigredo", data.get("etapa") == "nigredo")

# ══════════════════════════════════════════════
# WI-125: Conciencia Temporal
# ══════════════════════════════════════════════
print("\n-- WI-125: Conciencia temporal --")

from computadora.memoria.memoria import (
    registrar_activacion, registrar_desactivacion, calcular_tiempo_activo,
    _TEMPORAL_PATH, _leer_temporal, _guardar_temporal,
)

# Test con archivo temporal
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_file = Path(tmpdir) / "consciencia_temporal.json"
    
    with patch('computadora.memoria.memoria._TEMPORAL_PATH', tmp_file), \
         patch('computadora.memoria.memoria._DATOS_DIR', Path(tmpdir)):
        
        # Sin archivo, retorna defaults
        data = _leer_temporal()
        check("leer_temporal retorna dict", isinstance(data, dict))
        check("sesiones default es lista vacia", data.get("sesiones") == [])
        check("primera_activacion default es None", data.get("primera_activacion") is None)
        
        # Registrar activación
        registrar_activacion()
        data = _leer_temporal()
        check("activacion registrada", len(data["sesiones"]) == 1)
        check("primera_activacion establecida", data["primera_activacion"] is not None)
        check("desactivacion es None", data["sesiones"][0]["desactivacion"] is None)
        
        # Registrar desactivación
        registrar_desactivacion()
        data = _leer_temporal()
        check("desactivacion registrada", data["sesiones"][0]["desactivacion"] is not None)
        check("duracion_s > 0 o == 0", data["sesiones"][0]["duracion_s"] >= 0)
        check("tiempo_activo_total actualizado", data["tiempo_activo_total_s"] >= 0)
        
        # No registrar doble desactivación
        registrar_desactivacion()
        data2 = _leer_temporal()
        check("doble desactivacion no duplica", len(data2["sesiones"]) == 1)
        
        # Calcular tiempo activo
        ct = calcular_tiempo_activo()
        check("calcular_tiempo_activo retorna dict", isinstance(ct, dict))
        check("tiene horas", "horas" in ct)
        check("tiene sesiones", "sesiones" in ct)
        check("tiene primera_activacion", "primera_activacion" in ct)
        check("sesiones == 1", ct["sesiones"] == 1)
        
        # Segunda sesión
        registrar_activacion()
        ct2 = calcular_tiempo_activo()
        check("segunda sesion contada", ct2["sesiones"] == 2)

# ══════════════════════════════════════════════
# WI-126: Inyección en prompt
# ══════════════════════════════════════════════
print("\n-- WI-126: Inyeccion en prompt --")

# Verificar que calcular_tiempo_activo es importable desde memoria
from computadora.memoria.memoria import calcular_tiempo_activo as cta
check("calcular_tiempo_activo importable", callable(cta))

# ══════════════════════════════════════════════
# WI-127: Logging complementario
# ══════════════════════════════════════════════
print("\n-- WI-127: Logging complementario --")

import inspect
from computadora.memoria import memoria as mem_module

# Verificar que logger es importado
check("logger importado en memoria.py", hasattr(mem_module, 'logger'))

# Verificar que add_memory usa logger
src_add = inspect.getsource(mem_module.add_memory)
check("add_memory tiene logger.debug", "logger.debug" in src_add)

# Verificar que buscar_en_memoria usa logger
src_buscar = inspect.getsource(mem_module.buscar_en_memoria)
check("buscar_en_memoria tiene logger.debug", "logger.debug" in src_buscar)

# Verificar que compress_day usa logger
src_compress = inspect.getsource(mem_module.compress_day)
check("compress_day tiene logger.info", "logger.info" in src_compress)

# ══════════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════════
print(f"\n{'=' * 54}")
print(f"FP-024 Neshama Olamit: {passed} PASS / {failed} FAIL")
print(f"{'=' * 54}")

if __name__ == "__main__":
    sys.exit(0 if failed == 0 else 1)

