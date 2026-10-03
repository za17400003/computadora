# 🔧 TROUBLESHOOTING — Interfaz de COMPUTADORA no aparece

## Síntoma
Ejecutas `Computadora.lnk` pero no ves interfaz gráfica.

---

## Diagnóstico Rápido

### Paso 1: Ejecuta el debug script
En tu terminal PowerShell:
```powershell
cd C:\Users\woire\Documents\proyecto-golem
.\computadora_check.bat
```

Esto mostrará:
- ✓ Si Python está disponible
- ✓ Si PyQt6 se puede importar
- ✓ Si el módulo `computadora` existe
- ✓ Los logs más recientes (si se crearon)

### Paso 2: Prueba PyQt6 directamente
```powershell
.\test_pyqt6.bat
```

Si ves una ventana pequeña que dice "✓ COMPUTADORA PyQt6 Funciona Correctamente" → **PyQt6 OK**

Si ves error → Ve al **Problema #1** abajo.

### Paso 3: Revisa los logs
```powershell
Get-ChildItem .logs -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | % {Get-Content $_.FullName}
```

Busca líneas que digan `[ERROR]` o `Traceback`.

---

## Problemas Comunes y Soluciones

### Problema #1: PyQt6 falla en test_pyqt6.py
**Síntoma**: `QApplication: Could not find the platform plugin` o `ModuleNotFoundError`

**Causa**: PyQt6 no está instalado correctamente o falta Visual C++ Runtime

**Soluciones**:
```powershell
# Opción A: Reinstalar PyQt6
.\.venv\Scripts\pip install --force-reinstall PyQt6

# Opción B: Si eso no funciona, instala Visual C++ Redistributable
# Descargalo de: https://support.microsoft.com/en-us/help/2977003/
```

### Problema #2: `No such module computadora`
**Síntoma**: Debug script dice `computadora/__main__.py NO encontrado`

**Causa**: Estructura de carpetas incorrecta

**Solución**:
```powershell
# Verifica que exista:
ls computadora/__main__.py
ls computadora/config.py
ls computadora/interfaz/ventana_principal.py
```

Si faltan = clona/restaura proyecto desde git.

### Problema #3: `_config\.env not found`
**Síntoma**: Batch dice "ERROR: _config\.env no encontrado"

**Causa**: Archivo de configuración no copiado

**Solución**:
```powershell
# Copia archivo de ejemplo
cp _config\.env.example _config\.env

# Edítalo si necesitas cambios (puedes dejar defaults)
notepad _config\.env
```

### Problema #4: Logs muestran `Error en iniciar_interfaz()`
**Síntoma**: Debug script muestra imports OK pero luego error en `iniciar_interfaz`

**Causa**: Posiblemente headless mode o error en UI

**Solución**: 
```powershell
# Abre log más reciente y busca la línea de error:
(Get-ChildItem .logs -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName | % {Get-Content $_}

# Luego copia el error completo y comparte con developer
```

### Problema #5: Process se ejecuta pero ventana no aparece
**Síntoma**: Debug dice "Python ejecutándose" pero no ves ventana

**Causa**: Ventana minimizada o detrás de otras ventanas

**Solución**:
```powershell
# Busca en taskbar o usa Alt+Tab para navegar ventanas
# También revisa si hay proceso "Computadora" en Task Manager

Get-Process python | Where-Object {$_.ProcessName -eq "python"} | Format-Table Name, Id, Memory
```

---

## Reporte de Error Completo

Si nada funciona, ejecuta esto y copia el output:

```powershell
cd C:\Users\woire\Documents\proyecto-golem

# Mostrar versión Python
.\\.venv\Scripts\python.exe --version

# Intentar ejecutar con traceback
.\\.venv\Scripts\python.exe -m computadora 2>&1 | Tee-Object -FilePath "debug_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Ver el log
Get-Content "debug_*.log" | Select-Object -Last 50
```

Copia la salida completa de esos comandos y comparte.

---

## Estado Esperado

Cuando funciona, deberías ver:
1. Ventana cmd aparece
2. Logs muestran: `[OK] Python encontrado` → `[OK] Dependencias...` → `[OK] Ollama...`
3. Logs muestran: `Iniciando Computadora...`
4. **Luego aparece ventana PyQt6 con la interfaz de COMPUTADORA**
5. Si es first-run: también verás proceso facial (Gilgul)

---

## Contacto / Siguiente Paso

- Si debug muestra `[OK]` en todo → Hay bug en UI (reportar)
- Si debug falla en imports → Hay problema dependencias (reinstalar)
- Si debug falla en PyQt6 test → Sistema no tiene soporte gráfico (modo CLI)
