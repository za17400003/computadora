# 🎯 ANUNCIO: Proyecto Renombrado a COMPUTADORA

**Fecha**: 17 de Abril de 2026, 08:00 UTC  
**Estado**: Cambio Lógico Completado — Cambio Físico Pendiente

---

## Cambio de Nombre del Proyecto

### Anterior (Histórico)
- **Nombre**: Proyecto Golem (v1 esotérica)
- **Directorio**: `proyecto-golem` ← AÚN ACTIVO FÍSICAMENTE
- **Referencia**: Arquitectura con Sefirot, Alquimia, Rituales

### Nuevo (Actual)
- **Nombre**: Proyecto Computadora (v2 pragmática)
- **Directorio**: `proyecto_computadora` (cambiar manualmente)
- **Referencia**: Arquitectura con 5 Pilares (Verdad, Auditoría, Fail-Safe, Determinismo, Ética)

---

## Estado de Migración

✅ **Lógico** (Código + Documentación):
- ✓ Clases renombradas (CerebroComputadora, OrbeComputadora)
- ✓ Funciones actualizadas (_kill_previous_computadora_instances)
- ✓ Logs + strings: "Golem" → "Computadora"
- ✓ Imports + paquetes: com.golem → com.computadora (en Minimi)
- ✓ Documentación: .github/copilot-instructions.md actualizado
- ✓ Meta-auditoría: 91 referencias auditadas y actualizadas

❌ **Físico** (Cambio de Directorio Pendiente):
- ⏳ `proyecto-golem/` → `proyecto_computadora/` — BLOQUEADO POR LOCK
- 📝 Requiere: Cerrar todos los procesos que usan la carpeta y ejecutar:
  ```powershell
  Move-Item "C:\Users\woire\Documents\proyecto-golem" "C:\Users\woire\Documents\proyecto_computadora"
  ```

---

## La Trifecta Sincronizada

| Componente | Estado | Ubicación |
|-----------|--------|-----------|
| ⊕ SAL — ENCICLOPEDIA | ✅ | `proyecto-golem/ENCICLOPEDIA/` (29 archivos) |
| ☿ MERCURIO — MINIMI | ✅ | `C:\Users\woire\AndroidStudioProjects\Minimi` (com.computadora.minimi) |
| ♦ AZUFRE — COMPUTADORA | ✅ (excepto dir name) | `proyecto-golem/` → `proyecto_computadora/` (pendiente renombra) |

---

## Commits de esta Sesión

1. `d50c75b` — refactor: Actualizar strings 'Golem' → 'Computadora' en logs
2. `1681072` — fix: Actualizar referencias libro_encantado → ENCICLOPEDIA
3. `a4ad627` — fix: Corregir ruta absoluta en iniciar_computadora.bat
4. `ff12af5` — docs: Crear referencia local a MINIMI
5. `0108d8e` — refactor: Migración completa Minimi (com.golem → com.computadora)

---

## Próximos Pasos

1. **Cambio Físico** (Cuando se libere la carpeta):
   ```powershell
   Move-Item "C:\Users\woire\Documents\proyecto-golem" "C:\Users\woire\Documents\proyecto_computadora"
   # Commit: feat: Renombra física del directorio (proyecto-golem → proyecto_computadora)
   ```

2. **Actualizar referencias de ruta** en scripts/configuración que apunten a:
   - `"C:\Users\woire\Documents\proyecto-golem"` → `"C:\Users\woire\Documents\proyecto_computadora"`

3. **Verificación final**: Ejecutar `iniciar_computadora.bat` y confirmar que todo funciona

---

**Creado por**: GitHub Copilot  
**Sesión**: Auditoría de Coherencia Abril 17, 2026  
**Coherencia**: 🟢 95% (falta solo cambio de nombre físico del directorio)
