# DIAGNOSTICO: Loop Infinito — Dónde Está Ocurriendo?

**Problema**: "Sigue habiendo loop infinito"  
**Solución**: Identificar EXACTAMENTE dónde ocurre para poder arreglarlo

---

## Flujo Esperado (Sin Loop)

```
Usuario: Abre iniciar_computadora.bat
    ↓
[BATCH] Verifica: ¿net session funciona?
    ↓ NO (no es admin)
    → [MUESTRA MENSAJE] "Ejecuta como admin"
    → pause (espera que presiones Enter)
    → exit (cierra ventana)
    ↓ NO MÁS EJECUCIÓN (aquí es donde debería terminar)
    
[OR SI ES ADMIN]
    ↓ SÍ (es admin)
    → [BATCH] Verifica deps, LM Studio, .env
    → [BATCH] Ejecuta: .venv\Scripts\python.exe wrapper_computadora.py
    ↓
[PYTHON wrapper_computadora.py] Inicia
    ↓
[PYTHON] Importa: from computadora.__main__ import main
    ↓
[PYTHON] Ejecuta: main()
    ↓
[APP COMPUTADORA] Corre normalmente hasta que usuario cierra ventana
    ↓ FIN (aplicación termina, ventana se cierra)
```

---

## Dónde Podría Estar el Loop?

### OPCIÓN A: Loop en Batch (Relanzamiento Infinito)

**Síntoma**: La ventana del batch se abre, muestra "Ejecuta como admin", cierras, se abre nuevamente automáticamente

**Causa**: El batch intenta relanzarse a sí mismo infinitamente

**Cómo diagnosticar**: 
- Abre iniciar_computadora.bat (sin admin)
- Aparece mensaje "Ejecuta como admin"?
- Presionas Enter
- ¿Se cierra la ventana? → CORRECTO
- ¿Se abre nuevamente? → ESTO ES UN LOOP EN BATCH

**Solución aplicada**: El batch NUEVO no intenta relanzarse automáticamente. Si ves este loop, el archivo no se actualizó.

---

### OPCIÓN B: Loop en Python/Computadora (App se Relanza)

**Síntoma**: 
- Abre iniciar_computadora.bat como admin
- Muestra: "COMPUTADORA — Wrapper de ejecución"
- Importa módulo computadora correctamente
- Inicia main() ✓
- Pero luego: la ventana se cierra/relanza infinitamente

**Causa**: `computadora.__main__.main()` está intentando relanzarse a sí misma (quizás por error de importación o recurso faltante)

**Cómo diagnosticar**:
1. Abre iniciar_computadora.bat como admin
2. Mira si llegas a este punto: "✓ Importado exitosamente"
3. Mira si llegas a: "[2] Llamando main()..."
4. ¿Qué sucede después? ¿Aparece algún error? ¿Se cierra/relanza?

---

### OPCIÓN C: Loop en Verificación de Dependencias

**Síntoma**:
- Abre iniciar_computadora.bat como admin
- Ve mensajes de verificación: "Verificando Python", "Verificando .venv", etc.
- Pero luego se repite infinitamente

**Causa**: Algún comando en el batch (checking venv, installing deps) falla y se intenta de nuevo

**Cómo diagnosticar**: 
- Mira si ves: "echo [OK]" o "echo [ERROR]"
- ¿Qué es lo último que ve antes del loop?

---

## Pasos Para Diagnosticar

1. **Abre una terminal PowerShell como ADMINISTRADOR** (importante)
2. **Navega al directorio**: 
   ```powershell
   cd C:\Users\woire\Documents\proyecto-golem
   ```
3. **Ejecuta el batch directamente**:
   ```powershell
   .\iniciar_computadora.bat
   ```
4. **Observa**:
   - ¿Qué es lo ÚLTIMO que ves en pantalla?
   - ¿Se repite un mensaje? ¿Cuál?
   - ¿Aparece un error?
5. **Guarda la salida** (captura de pantalla o copia/pega el texto)

---

## Información Que Necesito

Para arreglarlo correctamente, por favor:
- ¿Cuál es el ÚLTIMO mensaje que ves antes de que se reinicie?
- ¿Se abre una ventana nueva o se relanza en la misma?
- ¿Ves algún error como "ImportError", "FileNotFoundError", etc.?
- ¿Si presionas Ctrl+C, se detiene el loop o continúa?

---

**Próximo paso**: Ejecuta el test y cuéntame exactamente qué ves.
