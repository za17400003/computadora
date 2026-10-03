# RUBEDO: Plan Post-Ronda 2

## Escenarios Posibles

### Escenario A: HIT EN RONDA 2 ✅
**Acción inmediata:**
1. Documentar candidato ganador
2. Verificar hit manualmente (`pikepdf.open('resiste-protected.pdf', password='X')`)
3. Commit atómico: "RUBEDO-RONDA2-HIT-[candidato]"
4. Palingenesia completa

### Escenario B: 0 HITS EN RONDA 2 ❌
**Diagnóstico (orden de prioridad):**

#### B1: Validación correcta pero contraseña no existe
- Script probó 59,681 candidatos sin error
- Conclusión: Contraseña NO está en diccionario
- **Próximo paso**: Ronda 3 con validación shadow_hash

#### B2: Bug en validación (contraseña probada pero no detectada)
- Script completa pero validación incorrecta
- Síntomas: ✓ Log muestra prueba, pero no "HIT"
- **Diagnóstico**: Revisar líneas críticas del script:
  - `pikepdf.open()` timeout/error handling
  - `_verificar_contraseña()` lógica
  - Encoding issues (utf-8 vs latin-1)
- **Fix**: Revalidar manualmente top 100 candidatos

#### B3: Encoding mismatch
- PDF usa latin-1, diccionario usa utf-8
- Síntomas: Caracteres especiales fallando silenciosamente
- **Fix**: Transcode candidatos antes de prueba

### Escenario C: Script Crash ⚠️
- Timeout, memory error, unicode error
- **Fix**: Aumentar timeout, reducir batch size
- **Fallback**: Modo secuencial sin tqdm

---

## Métricas Post-Ronda 2

| Métrica | Valor Esperado | Acción |
|---------|---|---|
| Tiempo total | 13-16 min | Registrar |
| Candidatos probados | 59,681 | ✓ |
| Promedio pwd/s | 65-75 | Acelerable |
| Hits | 0 o 1 | ↓ |
| Errores | 0 | ↓ |

---

## Timeline Ronda 3 (si aplica)

**Inicio**: Inmediato post-Ronda 2  
**Objetivo**: Validación hash-based  
**Diccionario**: candidatos_ronda3_shadow.txt (TBD)  
**Método**: Shadow hash validation sin desencriptación  
**ETA**: 5-10 min por método  

---

## Decision Tree

```
┌─ Ronda 2 Completa (59,681 pruebas)
├─ ¿HIT encontrado?
│  ├─ SÍ → Verificar manualmente → Commit RUBEDO-HIT → PALINGENESIA
│  └─ NO → ¿Error en logs?
│     ├─ SÍ → Diagnosticar (B2/B3) → Fix → Ronda 2 Rerun
│     └─ NO → Escenario B1 → Ronda 3 Shadow Hash
└─ ¿Crash?
   ├─ SÍ → Diagnosticar (timeout/memory) → Ronda 2 Rerun (batch)
   └─ NO → Continuar
```

---

## Notas Críticas

- **Audio 5 pista explícita**: "EMPIEZA CON UVE" → Candidatos V están en Ronda 2
- **VERDAD/VIDA probadas línea 9K**: Sin hits = probablemente incorrecto
- **Próximo candidato crítico**: Línea 57K (verdad/vida minúsculas)
- **Si Ronda 2 = 0**: Requiere Ronda 3 + análisis deeper (quizás composición de frases)
