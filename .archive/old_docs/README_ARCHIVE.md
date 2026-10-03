# Archivo Histórico — Proyecto Computadora

Este directorio contiene documentación histórica del proyecto desde fases anteriores. Los archivos aquí se mantienen para referencia y auditoría, pero **no son parte del flujo operativo actual**.

## Índice de Archivos Archivados

### Auditorías y Diagnósticos
- `ANALISIS_EXHAUSTIVO_CICLO_NIGREDO_RUBEDO.md` — Análisis destructivo (NIGREDO) y construcción (RUBEDO) completa
- `ARQUITECTURA_FINAL_SEPARACION_RESPONSABILIDADES.md` — Diseño de arquitectura con separación clara
- `AUDITORIA_SRS_RUNTIME_FINAL.md` — Auditoría de requisitos en tiempo real
- `DIAGNOSTICO_BOOT_FREEZE_FINDINGS.md` — Diagnóstico de problemas de congelación en boot
- `NIGREDO_CAMARA_AUTO_CONECTADA_CRITICA.md` — Crítica de cámara autconectada
- `NIGREDO_LATENCIA_WHISPER_CRITICA.md` — Problemas de latencia de Whisper

### Instrumentación y Análisis
- `COPILOT_CODEGRAPH_INTEGRATION.md` — Integración de CodeGraph
- `FPS_INSTRUMENTATION_INVESTIGATION.md` — Investigación de FPS
- `FIX_ANIMATION_FALSOS_POSITIVOS.md` — Fixes para falsos positivos de animación
- `FIX_REPORT_CONFIG_JSON.md` — Fixes de reportes en config.json
- `MALJUT_LEGACY_VS_FERROFLUIDO_ANALISIS.md` — Análisis de Maljut

### Operatividad y Resúmenes
- `INDICE_OPERATIVIDAD_MAYO3.md` — Índice de operatividad (Mayo 3)
- `INSTRUCCIONES_USO_OPERATIVIDAD_MAYO3.md` — Guía operativa (Mayo 3)
- `LECCIONES_APRENDIDAS_CICLO.md` — Lecciones del ciclo
- `OPERATIVIDAD_COMPLETA_MAYO3_RESUMEN.md` — Resumen de operatividad
- `RESUMEN_EJECUTIVO_FINAL.md` — Resumen ejecutivo
- `RESUMEN_EJECUTIVO_SISTEMA_DESBLOQUEADO.md` — Resumen del sistema desbloqueado
- `VALIDACION_FINAL_COMPLETA_20260521.md` — Validación final (Mayo 21)
- `VERIFICAR_ICONO_ACTIVO_GUIA.md` — Guía de verificación de icono
- `PLAN_PRUEBA_GRANULAR_FASE1.md` — Plan de prueba granular
- `WI-321_322_323_COMPLETADOS.md` — WorkItems completados

## Documentación Operativa Activa

La documentación operativa se encuentra en `/docs/`:
- `WORKFLOW_OPERACIONAL.md` — Flujo de trabajo operativo actual (Sefirot, Deptos, Tria Prima)
- `WorkItems.md` — Lista de trabajos en progreso

## Uso de Este Archivo

1. **Para referencia**: Consultar estos archivos para entender decisiones pasadas
2. **Para auditoría**: Verificar cambios históricos y evolución del proyecto
3. **Para patrón**: Analizar ciclos previos (NIGREDO, ALBEDO, CITRINITAS, RUBEDO, PALINGENESIA)

## Limpieza

Estos archivos se mantienen en git history. Si necesitas purgar completamente:
```bash
git filter-branch --tree-filter 'rm -f .archive/old_docs/*' HEAD
git push --force-with-lease
```

---
*Generado por RUBEDO Paso 3 — Reorganización de Documentación (Abril 12, 2026)*
