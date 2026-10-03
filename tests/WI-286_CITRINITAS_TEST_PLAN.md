# WI-286 — Validación EMET del Balance Jesed:Gevurá en Proactividad
## CITRINITAS CICLO 2 — Test Plan

> **Fecha creación**: Abril 9, 2026
> **Pipeline**: B (Mejora UX — validación de diseño)
> **Fase**: CITRINITAS (iluminación + test plan)
> **Próxima fase**: RUBEDO (crear + ejecutar tests)

---

## Objetivo

Validar que el motor de proactividad emite un balance equilibrado entre:
- **Gevurá** (אדם מינוס): Alertas, restricciones, daños, severidades
- **Jesed** (דברים חיוביים): Sugerencias, soluciones, mejoras, oportunidades

**Target**: Ratio Jesed:Gevurá = 50:50 (±10%, i.e., 40%-60%)  
**Actual (pre-WI-284)**: ~30:70 (imbalanceado hacia alertas)  
**Esperado (post-WI-284)**: ~45%-55% (cercano a balance)

---

## Teoría de Test

### Test 1: Balance de Fondo — Simulación de Alertas

**Nombre**: `test_balance_ratio_alertas_sugerencias_puro()`

**Concepto**: Llamar a `MotorProactividad._check_alertas_sistema()` 100 veces (simulando 100 invocaciones del motor) y medir:
- Cuántas veces emitió `sugerencia_lista` con tipo "alerta" (Gevurá)
- Cuántas veces emitió `sugerencia_lista` con tipo "sugerencia_positiva" (Jesed)

```python
@pytest.fixture
def motor_sin_timers():
    """MotorProactividad sin timers automáticos (TEST CONTROLLED)."""
    motor = MotorProactividad()
    motor.detener_timers()  # Pausar checeos internos
    return motor

def test_balance_ratio_alertas_sugerencias_puro(motor_sin_timers):
    """Ratio de Gevurá vs Jesed en 100 checks de alertas."""
    
    # Captura de señales emitidas
    gavura_emitidas = []
    jesed_emitidas = []
    
    motor_sin_timers.sugerencia_lista.connect(
        lambda tipo, msg: (
            gavura_emitidas.append(msg) if tipo == "alerta" else
            jesed_emitidas.append(msg) if tipo == "sugerencia_positiva" else
            None
        )
    )
    
    # Simular 100 checks de alertas
    for _ in range(100):
        motor_sin_timers._check_alertas_sistema()
    
    # Cálculo de ratio
    total_emitidas = len(gavura_emitidas) + len(jesed_emitidas)
    assert total_emitidas > 0, "Motor no emitió nada (error crítico)"
    
    ratio_jesed = len(jesed_emitidas) / total_emitidas
    ratio_gevura = len(gavura_emitidas) / total_emitidas
    
    print(f"\n📊 BALANCE PROACTIVIDAD:")
    print(f"  Gevurá (alertas): {len(gavura_emitidas)} ({ratio_gevura*100:.1f}%)")
    print(f"  Jesed (sugerencias): {len(jesed_emitidas)} ({ratio_jesed*100:.1f}%)")
    print(f"  Target: 50% cada uno (±10%)")
    
    # Validación: ratio debe estar entre 0.40 y 0.60 (40%-60% máximo de un lado)
    assert 0.40 <= ratio_jesed <= 0.60, (
        f"Ratio Jesed fuera de rango: {ratio_jesed*100:.1f}% "
        f"(esperado 40-60%)"
    )
    assert 0.40 <= ratio_gevura <= 0.60, (
        f"Ratio Gevurá fuera de rango: {ratio_gevura*100:.1f}% "
        f"(esperado 40-60%)"
    )
```

**Criterio de éxito**: 
- ✅ Teste pasa si ratio está entre 0.40-0.60 para ambos
- ✅ Falla si pre-WI-284 (~30% Jesed) → Test falla ANTES de fix
- ✅ Pasa si post-WI-284 (~45-55% Jesed) → Test pasa DESPUÉS de fix

---

### Test 2: Mapeo Contextual — ¿Alerta → Sugerencia Apropiada?

**Nombre**: `test_mapeo_contextual_alerta_sugerencia()`

**Concepto**: Para cada TIPO de alerta (CPU/RAM/disco/inactividad), validar que la sugerencia generada sea CONTEXTUALMENTE RELEVANTE.

```python
def test_mapeo_contextual_alerta_sugerencia(motor_sin_timers):
    """Verificar que cada alerta genera sugerencia contextual correcta."""
    
    # MOCK: Simular diferentes condiciones de alerta
    test_cases = [
        ("CPU", "CPU al 92% sostenido por 30 segundos", 
         ["Ejecutar análisis", "procesos", "Priorizar", "Limpiar"]),  # Keywords esperados
        
        ("RAM", "RAM al 88% (excluyendo mi propio consumo)", 
         ["Cerrar", "aplicaciones", "Liberar", "caché", "memoria"]),
        
        ("DISCO", "Disco C: solo 8% libre", 
         ["Identificar", "archivos", "temporales", "Generar", "reporte", "Defragmentación"]),
        
        ("INACTIVIDAD", "Hasn't moved in 15 minutes", 
         ["Despertar", "completamente", "Activar", "modo", "activo"]),
    ]
    
    for alert_type, alert_msg, expected_keywords in test_cases:
        # Emular que _generar_sugerencia_balanceadora() recibe alerta
        sugerencia = motor_sin_timers._generar_sugerencia_balanceadora(alert_msg)
        
        # Validar que la sugerencia contiene al menos UNA keyword relevante
        tiene_keyword = any(kw.lower() in sugerencia.lower() for kw in expected_keywords)
        assert tiene_keyword, (
            f"Sugerencia para {alert_type} NO es contextual:\n"
            f"  Alerta: {alert_msg}\n"
            f"  Sugerencia: {sugerencia}\n"
            f"  Keywords esperados: {expected_keywords}"
        )
        
        print(f"  ✅ {alert_type}: '{sugerencia}' es contextual")
```

**Criterio de éxito**:
- ✅ Cada caso pasa si sugerencia tiene keywords relevantes
- ✅ Cubre 4 tipos de alertas principales

---

### Test 3: Consistencia — Ratio Estable en Múltiples Runs

**Nombre**: `test_balance_ratio_estable_multiples_runs()`

**Concepto**: Ejecutar el test de ratio 5 veces e validar que el resultado es CONSISTENTE (no fluctúa salvajemente).

```python
def test_balance_ratio_estable_multiples_runs(motor_sin_timers):
    """Verificar que el ratio de Jesed:Gevurá es consistente entre runs."""
    
    ratios_jesed = []
    
    for run in range(5):
        gavura_count = 0
        jesed_count = 0
        
        def contar_emisiones(tipo, msg):
            nonlocal gavura_count, jesed_count
            if tipo == "alerta":
                gavura_count += 1
            elif tipo == "sugerencia_positiva":
                jesed_count += 1
        
        motor_sin_timers.sugerencia_lista.connect(contar_emisiones)
        
        for _ in range(50):  # 50 checks por run
            motor_sin_timers._check_alertas_sistema()
        
        total = gavura_count + jesed_count
        if total > 0:
            ratio = jesed_count / total
            ratios_jesed.append(ratio)
            print(f"  Run {run+1}: Ratio Jesed = {ratio*100:.1f}%")
    
    # Validar consistencia: std dev < 10%
    import statistics
    if len(ratios_jesed) > 1:
        std_dev = statistics.stdev(ratios_jesed)
        print(f"  Desviación estándar: {std_dev*100:.1f}%")
        assert std_dev < 0.10, (
            f"Ratio no es estable: std_dev={std_dev*100:.1f}% "
            f"(esperado <10%)"
        )
```

**Criterio de éxito**:
- ✅ Todos los runs muestran ratio similar (std dev < 10%)

---

### Test 4: Integración con Monitor — Real System Alerts

**Nombre**: `test_integracion_monitor_alerta_sugerencia()`

**Concepto**: Usar `MonitorSistema` real (no MOCK) para generar alertas auténticas, verificar que cada una produce sugerencia.

```python
def test_integracion_monitor_alerta_sugerencia():
    """Validar que MonitorSistema + MotorProactividad generan alertas balanceadas."""
    
    monitor = MonitorSistema()
    motor = MotorProactividad()
    motor.set_monitor(monitor)  # Conectar
    
    alertas_emitidas = []
    sugerencias_emitidas = []
    
    motor.sugerencia_lista.connect(
        lambda tipo, msg: (
            alertas_emitidas.append(msg) if tipo == "alerta" else
            sugerencias_emitidas.append(msg) if tipo == "sugerencia_positiva" else
            None
        )
    )
    
    # Ejecutar motor 10 veces (capturará alertas reales del sistema)
    for _ in range(10):
        motor._check_alertas_sistema()
    
    total = len(alertas_emitidas) + len(sugerencias_emitidas)
    if total > 0:
        ratio_jesed = len(sugerencias_emitidas) / total
        print(f"\n📊 SISTEMA REAL - Balance:")
        print(f"  Alertas: {len(alertas_emitidas)} ({(1-ratio_jesed)*100:.1f}%)")
        print(f"  Sugerencias: {len(sugerencias_emitidas)} ({ratio_jesed*100:.1f}%)")
        
        # Validación RELAJADA para sistema real (puede haber alertas reales)
        # Target: como mínimo 30% sugerencias (i.e., no 100% alertas)
        assert ratio_jesed >= 0.30, (
            f"Sistema muy alarmista: solo {ratio_jesed*100:.1f}% sugerencias "
            f"(mínimo 30% requerido)"
        )
    
    monitor.detener()
```

**Criterio de éxito**:
- ✅ Si hay alertas, al menos 30% de emisiones son sugerencias positivas

---

## Plan de Pytest Suite

**Archivo**: `tests/test_balance_proactividad.py` (crear)

**Contenido**:
```python
import pytest
from unittest.mock import MagicMock, patch
from golem.nucleo.proactividad import MotorProactividad
from golem.habilidades.monitor_sistema import MonitorSistema

# 4 tests enumerados arriba + fixtures

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
```

**Ejecución**:
```bash
# ANTES de WI-285 RUBEDO: tests deben FALLAR
pytest tests/test_balance_proactividad.py -v

# DESPUÉS de WI-285 RUBEDO: tests deben PASAR
pytest tests/test_balance_proactividad.py -v
```

---

## KPIs de PALINGENESIA (WI-286 fase final)

| KPI | Pre-WI-285 | Post-WI-285 (Target) | Métrica |
|-----|-----------|-----|---------|
| Ratio Jesed:Gevurá | 30-70 | 45-55 | % de sugerencias en 100 checks |
| Test 1 Pass Rate | ❌ Falla | ✅ Pasa | Assert 0.40 <= ratio <= 0.60 |
| Test 2 Pass Rate | ❌ Falla | ✅ Pasa | 4/4 casos contextuales OK |
| Test 3 Pass Rate | ❌ Falla | ✅ Pasa | Std dev < 10% entre runs |
| Test 4 Pass Rate | ⚠️ Variable | ✅ Pasa | Ratio >= 30% en sistema real |

---

## Notas de Implementación

**Para WI-286 RUBEDO (crear tests)**:
1. Crear archivo `tests/test_balance_proactividad.py` de cero
2. Implementar 4 test functions exactamente como especificado arriba
3. Usar `unittest.mock` para simular `MonitorSistema` (no ejecutar sistema real en setup)
4. Fixture `motor_sin_timers` debe pausar threads automáticos
5. Cada test debe ser independiente (no compartir estado)
6. Documentación: cada test tiene docstring explicando qué valida

**Para ejecutar PRE-implementación (como verificación)**:
```bash
# Debe FALLAR (porque sugerencias_balanceadora aún no está completamente integrada)
pytest tests/test_balance_proactividad.py::test_balance_ratio_alertas_sugerencias_puro -v
```

**Para ejecutar POST-implementación**:
```bash
# Debe PASAR todos 4
pytest tests/test_balance_proactividad.py -v
```

---

## Recursos Conectados

- **WI-283 RUBEDO**: `LogicaTransparente` módulo creado
- **WI-284 RUBEDO**: `_generar_sugerencia_balanceadora()` implementado
- **WI-285 RUBEDO** (próximo): Integración en rostro.py + monitor_sistema.py
- **WI-286 CITRINITAS** (este doc): Test plan de validación
- **WI-286 RUBEDO** (próximo): Crear + ejecutar tests

---

**Firmado**: GitHub Copilot (CEO/CTO)  
**Timestamp**: 2026-04-09 ~18:00 UTC  
**Ritual**: Iluminación de lo Oculto → Precisión de Medida → Alquimia confirmada
