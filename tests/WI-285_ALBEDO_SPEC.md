# WI-285 — Integración Completa de LogicaTransparente en Módulos Críticos
## ALBEDO CICLO 2 — Especificación Puntual de Cambios

> **Fecha creación**: Abril 9, 2026
> **Pipeline**: D (Arquitectura — Post CICLO 1 WI-283 RUBEDO)
> **Fase**: ALBEDO (clasificación y especificación de cambios exactos)
> **Próxima fase**: CITRINITAS (test plan)

---

## Objetivo

Integrar las funciones helper de `LogicaTransparente` (creadas en WI-283 RUBEDO) en los módulos que calculan matemáticas del Golem, para que cada operación sea **registrada y auditable**.

**Resultado**: Cuando usuario pregunta "¿qué calculaste?", Golem puede responder con trazabilidad completa.

---

## Cambios a Nivel de Código

### CAMBIO 1: `golem/percepcion/rostro.py` — Integrar `registrar_facial()`

**Ubicación**: Función `analizar_frame()`, líneas ~145-180  
**Razón**: Aquí se calcula la distancia facial (confianza) — es la MATEMÁTICA del reconocimiento facial

#### Líneas PRE-CAMBIO:
```python
# línea ~155
dist = float(fr.face_distance([self._encoding_propietario], enc)[0])
if dist <= _UMBRAL_PROPIETARIO:
    self.propietario_detectado.emit()
    return {"resultado": "propietario", "distancia": dist, "locations": locations}

# línea ~162
if self._conocidos:
    nombres = list(self._conocidos.keys())
    conocidos_enc = [self._conocidos[n] for n in nombres]
    dists = fr.face_distance(conocidos_enc, enc)
    min_idx = int(np.argmin(dists))
    if dists[min_idx] <= _UMBRAL_CONOCIDO:
        nombre = nombres[min_idx]
        self.persona_detectada.emit(nombre)
        return {"resultado": "conocido", "nombre": nombre, "distancia": float(dists[min_idx]), "locations": locations}
```

#### Líneas POST-CAMBIO:
```python
# Agregar import at top of file:
# from golem.cerebro.matematicas import registrar_facial

# línea ~155
dist = float(fr.face_distance([self._encoding_propietario], enc)[0])

# NUEVO: registrar el cálculo en LogicaTransparente
confianza = 1.0 - dist  # Convertir distancia a confianza (0-1)
registrar_facial(
    distancia=dist,
    pitch=1.0,  # TODO: extraer del video en futura fase
    lighting="normal",  # TODO: estimar del frame actual
    confianza=confianza
)

if dist <= _UMBRAL_PROPIETARIO:  
    self.propietario_detectado.emit()
    return {"resultado": "propietario", "distancia": dist, "locations": locations}

# línea ~162
if self._conocidos:
    nombres = list(self._conocidos.keys())
    conocidos_enc = [self._conocidos[n] for n in nombres]
    dists = fr.face_distance(conocidos_enc, enc)
    min_idx = int(np.argmin(dists))
    
    # NUEVO: registrar antes de emitir
    dist_conocido = float(dists[min_idx])
    confianza_conocido = 1.0 - dist_conocido
    registrar_facial(
        distancia=dist_conocido,
        pitch=1.0,  # TODO
        lighting="normal",  # TODO
        confianza=confianza_conocido
    )
    
    if dists[min_idx] <= _UMBRAL_CONOCIDO:
        nombre = nombres[min_idx]
        self.persona_detectada.emit(nombre)
        return {"resultado": "conocido", "nombre": nombre, "distancia": dist_conocido, "locations": locations}
```

**Criterio de éxito**: Después de `analizar_frame()`, se llama 1-2 veces a `registrar_facial()` por frame analizado.

**Estimación de líneas**: +8 líneas de código + 1 línea import = +9 líneas netas

---

### CAMBIO 2: `golem/habilidades/monitor_sistema.py` — Integrar `registrar_alerta_sistema()`

**Ubicación**: Función `hay_alerta()`, líneas ~200-260  
**Razón**: Aquí se calculan las 4 alertas del sistema (CPU, RAM, disco, procesos anómalos)

#### Líneas PRE-CAMBIO (resumen):
```python
def hay_alerta(self) -> str | None:
    alertas = []
    
    # 1. CPU sostenida
    cpu_30s = self.cpu_promedio(30)
    cpu_anomalo = cpu_30s > self._umbrales['cpu_pct']
    ...
    if cpu_anomalo:
        alertas.append(f"CPU al {cpu_30s:.0f}% sostenido por 30 segundos")
    
    # 2. RAM (excluyendo procesos propios)
    ram_ajena_pct = self.ram_sin_propios()
    ram_anomalo = ram_ajena_pct > self._umbrales['ram_pct']
    ...
    if ram_anomalo:
        alertas.append(f"RAM al {ram_ajena_pct:.0f}% (excluyendo mi propio consumo)")
    
    # 3. Disco
    disco = psutil.disk_usage('C:\\')
    disco_libre_pct = ...
    if disco_libre_pct < self._umbrales['disco_pct']:
        alertas.append(f"Disco C: solo {disco_libre_pct:.0f}% libre")
    
    if alertas:
        return ". ".join(alertas)
    
    # 4. Procesos anómalos
    diag = self.diagnosticar_proceso_anomalo()
    if diag:
        return f"Proceso sospechoso: {diag}"
    
    return None
```

#### Líneas POST-CAMBIO:
```python
# Agregar import at top of file:
# from golem.cerebro.matematicas import registrar_alerta_sistema

def hay_alerta(self) -> str | None:
    alertas = []
    
    # 1. CPU sostenida
    cpu_30s = self.cpu_promedio(30)
    cpu_anomalo = cpu_30s > self._umbrales['cpu_pct']
    if self._baseline and self._baseline.tiene_datos_suficientes():
        cpu_anomalo = self._baseline.es_anomalo('cpu_pct', cpu_30s)
    
    # NUEVO: registrar cálculo de CPU
    if cpu_anomalo:
        registrar_alerta_sistema(
            tipo_alerta="cpu",
            valor=cpu_30s,
            umbral=self._umbrales['cpu_pct'],
            es_sospechoso=True,
            contexto="CPU sostenida >30s"
        )
        alertas.append(f"CPU al {cpu_30s:.0f}% sostenido por 30 segundos")
    
    # 2. RAM (excluyendo procesos propios)
    try:
        ram_ajena_pct = self.ram_sin_propios()
        ram_anomalo = ram_ajena_pct > self._umbrales['ram_pct']
        if self._baseline and self._baseline.tiene_datos_suficientes():
            ram_anomalo = self._baseline.es_anomalo('ram_pct', ram_ajena_pct)
        if ram_anomalo and self._ram_es_entorno_normal():
            ram_anomalo = False
        
        # NUEVO: registrar cálculo de RAM
        if ram_anomalo:
            registrar_alerta_sistema(
                tipo_alerta="ram",
                valor=ram_ajena_pct,
                umbral=self._umbrales['ram_pct'],
                es_sospechoso=True,
                contexto="RAM ajena alta (excluyendo procesos propios)"
            )
            alertas.append(f"RAM al {ram_ajena_pct:.0f}% (excluyendo mi propio consumo)")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    
    # 3. Disco
    try:
        disco = psutil.disk_usage('C:\\')
        disco_libre_pct = round(100 - disco.percent, 1)
        
        # NUEVO: registrar cálculo de disco
        if disco_libre_pct < self._umbrales['disco_pct']:
            registrar_alerta_sistema(
                tipo_alerta="disco",
                valor=disco_libre_pct,
                umbral=self._umbrales['disco_pct'],
                es_sospechoso=True,
                contexto="Espacio disco bajo en C:\\"
            )
            alertas.append(f"Disco C: solo {disco_libre_pct:.0f}% libre")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    
    if alertas:
        return ". ".join(alertas)
    
    # 4. Procesos anómalos
    diag = self.diagnosticar_proceso_anomalo()
    if diag:
        # NUEVO: registrar proceso anómalo
        registrar_alerta_sistema(
            tipo_alerta="proceso_anomalo",
            valor=diag,  # string con diagnóstico
            umbral="N/A",  # heurístico, sin umbral fijo
            es_sospechoso=True,
            contexto="Proceso desconocido con consumo alto"
        )
        return f"Proceso sospechoso: {diag}"
    
    return None
```

**Criterio de éxito**: Cada llamada a `hay_alerta()` que detecta anormalidad registra 1-4 veces (una por tipo de alerta detectada).

**Estimación de líneas**: +18 líneas de código + 1 línea import = +19 líneas netas

---

### CAMBIO 3: `golem/nucleo/proactividad.py` — Ya Integrado en WI-284 RUBEDO

**Status**: ✅ COMPLETO (ver `_check_alertas_sistema()` líneas ~395-420)

No requiere cambios adicionales en WI-285.

---

## Resumen de Cambios

| Archivo | Función | Líneas Added | Imports Added | Registro Calls |
|---------|---------|--------------|---------------|--------|
| `rostro.py` | `analizar_frame()` | +9 | +1 | `registrar_facial()` ×1-2 por frame |
| `monitor_sistema.py` | `hay_alerta()` | +19 | +1 | `registrar_alerta_sistema()` ×1-4 por evaluación |
| `proactividad.py` | `_check_alertas_sistema()` | 0 (ya integrado) | 0 | N/A |
| **TOTAL** | — | **+28** | **+2** | — |

---

## Validación de Completitud

### Pre-Implementación Checks:
- [ ] `golem/cerebro/matematicas.py` existe y exporta `registrar_facial()` + `registrar_alerta_sistema()`
- [ ] `golem/percepcion/rostro.py` importa sin erro res
- [ ] `golem/habilidades/monitor_sistema.py` importa sin errores
- [ ] No hay circular imports

### Post-Implementación Checks:
- [ ] Ambos archivos se pueden importar sin errores
- [ ] `registrar_facial()` es llamado desde `rostro.py`
- [ ] `registrar_alerta_sistema()` es llamado desde `monitor_sistema.py`
- [ ] Logs del Golem muestran "registrar_facial/alerta_sistema en call stack" (debugging)
- [ ] `datos/auditoria_matematica/` directorio se crea automáticamente
- [ ] Exportar matemáticas: datos/auditoria_matematica/mat_audit_{ISO}.json contiene >0 registros después de 5 min ejecución

---

## Notas de Implementador

**Para WI-285 RUBEDO**:
1. No modificar lógica existente (CPU/RAM/disco checks)
2. Solo AGREGAR llamadas a `registrar_*()` — no cambiar queries ni umbrales
3. Preservar todos los comentarios existentes (line RF-167, etc.)
4. Asegurar que los `contexto=` strings sean descriptivos (usuario comprenderá después)
5. Si hay exception en `registrar_facial/alerta_sistema`, loguear pero NO romper la función principal

**Para testing**:
- Crear test mínimo: `test_integracion_matematica_rostro.py`
- Crear test mínimo: `test_integracion_matematica_alertas.py`
- Ambos verifican que llamadas a `registrar_*()` ocurren Y se exportan a JSON

---

## Recursos Conectados

- **WI-283 RUBEDO** (completado): `golem/cerebro/matematicas.py` creado
- **WI-284 RUBEDO** (completado): `_generar_sugerencia_balanceadora()` integrado en proactividad.py
- **WI-285 ALBEDO** (este doc): Especificación puntual de 2 integraciones
- **WI-286 CITRINITAS-RUBEDO** (próximo): Test plan para validación de balance

---

**Firmado**: GitHub Copilot (CEO/CTO)  
**Timestamp**: 2026-04-09 ~17:55 UTC  
**Ritual**: Alfabetas de Destrucción → Purificación → síntesis puntual
