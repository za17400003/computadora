# 🔍 COMPUTADORA — ¿Por qué no aparece interfaz?

**Date**: April 21, 2026  
**Issue**: Shortcut ejecuta pero no aparece ventana de COMPUTADORA

---

## Causa Probable
Hay un error silencioso en Python que cierra la ventana antes de que PyQt6 pueda renderizar la interfaz.

---

## ⚡ Solución Rápida — 3 Pasos

### Paso 1: Ejecuta el Debug Batch
En tu PowerShell (en proyecto-golem):
```powershell
.\computadora_debug_report.bat
```

**¿Qué verás?**
- Un resumen legible del error (si lo hay)
- "✓" si todo está OK
- Traceback completo si falla

### Paso 2: Si ves error, revisa archivos
```powershell
# Ver último log
Get-Content .logs\computadora_ERROR*.txt | Select-Object -Last 30

# O ver archivo Python error
Get-Content .logs\python_error.txt
```

### Paso 3: Interpreta el error usando TROUBLESHOOTING_UI_NO_APARECE.md
```powershell
Get-Content TROUBLESHOOTING_UI_NO_APARECE.md
```

---

## 🔧 Herramientas de Diagnóstico Disponibles

| Archivo | Propósito | Usar cuando |
|---------|----------|-----------|
| `computadora_check.bat` | Verificación completa de dependencias | "No sé qué está mal" |
| `test_pyqt6.bat` | Prueba PyQt6 directamente | "Creo que PyQt6 falla" |
| `computadora_debug_report.bat` | Ejecución con traceback mejorado | "Quiero ver el error exacto" |
| `TROUBLESHOOTING_UI_NO_APARECE.md` | Guía de problemas comunes | "Tengo un error específico" |

---

## 📋 Verificación Rápida (todos verdes = OK)

```powershell
# ✓ 1. Virtual env existe
Test-Path ".venv\Scripts\python.exe"

# ✓ 2. PyQt6 importable
.\.venv\Scripts\python.exe -c "import PyQt6; print('OK')"

# ✓ 3. Módulo computadora existe
Test-Path "computadora\__main__.py"

# ✓ 4. Config file existe
Test-Path "_config\.env"
```

Si alguno falla, ve a TROUBLESHOOTING_UI_NO_APARECE.md

---

## 🚨 SOS — Si nada funciona

Ejecuta esto y envía el output completo:

```powershell
cd C:\Users\woire\Documents\proyecto-golem

Write-Host "=== SISTEMA INFO ==="
python --version
$env:PYTHONPATH

Write-Host "`n=== VERIFICAR PYQT6 ==="
.\.venv\Scripts\python.exe -c "import PyQt6; print(PyQt6.__file__)"

Write-Host "`n=== INTENTAR EJECUTAR ==="
.\.venv\Scripts\python.exe -m computadora

Write-Host "`n=== LOGS DISPONIBLES ==="
Get-ChildItem .logs | Sort LastWriteTime | Select -Last 3
```

---

## ✅ Verificación Post-Fix

Una vez que arreglaste el error, COMPUTADORA debe:

1. **Shortcut ejecutado** → aparece ventana cmd
2. **Pre-flight checks** → ves logs: `[OK] Python...` `[OK] PyQt6...` `[OK] Dependencies...`
3. **Iniciando Computadora...** → aparece ventana PyQt6 (interfaz gráfica)
4. **Si first-run** → proceso facial (Gilgul) captura tu cara
5. **Sistema listo** → puedes dar comandos a COMPUTADORA

---

## 🎯 Acciones Según Diagnóstico

**Si test_pyqt6.bat funciona pero computadora_check.bat falla:**
→ Problema en módulo computadora, no en gráficos

**Si test_pyqt6.bat falla:**
→ Problema PyQt6/gráficos (reinstalar Visual C++)

**Si computadora_check.bat funciona pero shortcut no muestra ventana:**
→ Problema en ventana cmd o timing, intenta esperarto más

**Si ves archivos .ERROR en .logs:**
→ Hay excepción Python, revisa contenido del archivo

---

**Última actualización**: April 21, 2026 — 20:30 UTC  
**Creado por**: GitHub Copilot  
**Propósito**: Diagnosticar por qué PyQt6 UI no aparece
