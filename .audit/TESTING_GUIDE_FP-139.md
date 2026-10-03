# 🧪 TESTING GUIDE — FP-139 Cámara + GILGUL + LM Studio

**Status**: ✅ Commit realizado (1330d20)  
**Ready for user testing**

---

## 📋 Pre-requisitos

```
✓ Python 3.11+
✓ Cámara web conectada (USB o built-in)
✓ Micrófono para voz
✓ LM Studio instalado (opcional pero recomendado)
✓ Face recognition library: pip install face-recognition
```

---

## 🎬 Test Sequence

### TEST 1️⃣: First Boot (GILGUL)
**Objetivo**: Verificar que GILGUL ejecuta UNA SOLA VEZ

**Pasos**:
```bash
# Asegurar que NO existe registro anterior
Remove-Item datos/FACEREC_RECORD.json -Force 2>$null

# Primer boot
python -m computadora

# Esperar ~30-60s...
```

**Esperado**:
- ✅ Ventana de Computadora abre
- ✅ Logs muestran: "PRIMER BOOT: ejecutando GILGUL automático"
- ✅ Se abre dev-tool-cámara (escaneo facial)
- ✅ Pide nombre corto + nombre completo
- ✅ Se crea `datos/FACEREC_RECORD.json`
- ✅ Usuario detectado: [tu nombre]
- ✅ Orbe aparece en pantalla

**Si falla**:
```
❌ "FACEREC_RECORD.json no se creó"
  → Verifica permisos en `datos/`
  
❌ "No se ve la cámara en GILGUL"
  → Verifica que cámara esté conectada (probá con: python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())")
  
❌ "Script de GILGUL no ejecuta"
  → Verifica COMPUTADORA_FACEREC_SIMPLE.py existe en scripts/
```

---

### TEST 2️⃣: Second Boot (Auto-detection)
**Objetivo**: Verificar que NUNCA pide contraseña, auto-detecta usuario

**Pasos**:
```bash
# Segundo boot (FACEREC_RECORD.json ya existe)
python -m computadora

# Esperar ~15-20s...
```

**Esperado**:
- ✅ Logs muestran: "FP-139 GILGUL ONE-TIME: Registro facial existente"
- ✅ Logs muestran: "✓ NUNCA volver a pedir contraseña"
- ✅ Usuario: [tu nombre] cargado de memoria
- ✅ Logs muestran: "FP-139: Escaneando rostro para verificar identidad"
- ✅ Orbe aparece SIN pedir contraseña
- ✅ Cámara abierta automáticamente

**Si falla**:
```
❌ "Pide contraseña nuevamente"
  → Logs dice "PRIMER BOOT" aunque FACEREC_RECORD.json existe
  → Verifica que _detectar_usuario_y_facerec() usa facerec_path.exists()
  
❌ "Cámara sigue en DESCONECTADO"
  → Logs deberían mostrar "RF-260: camara_local descubierto y conectado al boot"
  → Si falta, verifica kli.py descubrir_observadores() llamó self.conectar()
```

---

### TEST 3️⃣: Camera Auto-connect (RF-260)
**Objetivo**: Verificar que cámara se abre automáticamente

**Pasos**:
```bash
# Boot N
python -m computadora

# Verificar logs en terminal
```

**Esperado en logs**:
```
✓ RF-260: camara_local descubierto y conectado al boot
✓ RF-260: Dispositivos Kli conectados: ['camara_local']
[GUI se abre con cámara activa — puedes verte en tiempo real]
```

**Si falta**:
```
❌ "RF-260: camara_local descubierto pero NO se pudo conectar"
  → Cámara no se pudo abrir (permisos, driver, puerto USB)
  → Probá: python -c "import cv2; cap = cv2.VideoCapture(0)"
  
❌ "No aparece RF-260 en logs"
  → Verifica que descubrir_observadores() está ejecutando (busca "Descubriendo observadores")
```

---

### TEST 4️⃣: LM Studio Integration (Tiféret)
**Objetivo**: Verificar que LM Studio se ve como parte integral de Computadora

**Pasos**:
```bash
# Asegurar que LM Studio está corriendo
# (Menú Start → LM Studio → cargar modelo si no lo hizo)

python -m computadora

# Verificar logs
```

**Esperado en logs**:
```
✓ LM Studio (ollama.exe) detectado — es PARTE DE COMPUTADORA (Tiféret/Nivel 2)
✓ Modelo [tu modelo] listo en LM Studio
[Si no está disponible: "LM Studio no está corriendo. COMPUTADORA pensará sin LLM."]
```

**Si LM Studio se desconecta**:
```
→ Logs mostrarán: "FP-139: Iniciando reconexión automática con LM Studio (Tiféret)"
→ Intenta reconectar cada 30s hasta 5 min
→ Si éxito: "✓ FP-139: Tiféret (LM Studio) reconectado exitosamente"
→ No es una amenaza, es una reparación interna
```

---

## 🎯 Full Boot Validation

**Script rápido**: Ejecuta esto en terminal para validar todo

```powershell
cd c:\Users\woire\Documents\proyecto-golem

# Limpiar registro anterior
Remove-Item datos/FACEREC_RECORD.json -Force 2>$null

# Boot 1 — GILGUL
Write-Host "=== BOOT 1: GILGUL ONE-TIME ===" -ForegroundColor Cyan
python -m computadora *>&1 | Tee boot1.log

# Verificar log
if (Select-String "PRIMER BOOT" boot1.log) { Write-Host "✓ GILGUL ejecutado" -ForegroundColor Green }
if (Select-String "FACEREC_RECORD.json" boot1.log) { Write-Host "✓ Registro creado" -ForegroundColor Green }

# Boot 2 — Auto-detection
Write-Host "`n=== BOOT 2: AUTO-DETECTION ===" -ForegroundColor Cyan
python -m computadora *>&1 | Tee boot2.log

# Verificar log
if (Select-String "NUNCA volver a pedir contraseña" boot2.log) { Write-Host "✓ GILGUL NO repitió" -ForegroundColor Green }
if (Select-String "RF-260: camara_local descubierto y conectado" boot2.log) { Write-Host "✓ Cámara auto-conectada" -ForegroundColor Green }

# Boot 3 — Verify persistence
Write-Host "`n=== BOOT 3: VERIFY PERSISTENCE ===" -ForegroundColor Cyan
python -m computadora *>&1 | Tee boot3.log

if (Select-String "NUNCA volver a pedir contraseña" boot3.log) { Write-Host "✓ Persistencia OK" -ForegroundColor Green }
```

---

## 📊 Success Criteria Checklist

| Criterio | Boot 1 | Boot 2+ | Status |
|----------|--------|---------|--------|
| GILGUL ejecuta | ✅ | ❌ | ?      |
| FACEREC_RECORD.json se crea | ✅ | ✅ | ?      |
| Pide nombre al usuario | ✅ | ❌ | ?      |
| Cámara auto-conecta (RF-260) | ✅ | ✅ | ?      |
| NO pide contraseña en Boot N>1 | ❌ | ✅ | ?      |
| LM Studio detectado como Tiféret | ✅ | ✅ | ?      |
| Orbe aparece sin errores | ✅ | ✅ | ?      |

---

## 🆘 Troubleshooting

### "Cámara sigue mostrando DESCONECTADO"
```bash
# Verificar que cámara existe
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL'); cap.release()"

# Verificar driver
# Windows: Disposi. Management → Camera (checar si está habilitada)

# Test manual de KliCamara
python -c "from computadora.habilidades.vision import KliCamara; cam = KliCamara(); print('Connected' if cam.conectar() else 'Failed to connect')"
```

### "GILGUL se ejecuta en Boot 2"
```
→ Verifica que _detectar_usuario_y_facerec() retorna en CASO 1
→ Busca en logs: "Registro facial existente"
→ Si no aparece, facerec_path.exists() retorna False
→ Verifica permisos y ruta en __main__.py línea ~95
```

### "LM Studio se ve como 'proceso sospechoso'"
```
→ Esto ya está fixeado en FP-139
→ Logs deberían decir "es PARTE DE COMPUTADORA (Tiféret/Nivel 2)"
→ Si no aparece, verifica que nlu.py fue actualizado (línea 1200+)
```

---

## 📝 Log Output Examples

### Boot 1 (GILGUL)
```
=== COMPUTADORA — INICIANDO ===
✓ Ouroboros estable
✓ Observador iniciado — vigilancia constante activa
📸 PRIMER BOOT: ejecutando GILGUL automático (ONE-TIME)
💡 Este proceso ocurre UNA SOLA VEZ. Boots posteriores cargarán de memoria.
[COMPUTADORA_FACEREC_SIMPLE.py lanza...]
🎥 Capturando frame...
👤 Rostro detectado! Captura automática en progreso...
📝 ¿Tu nombre corto? > [USER INGRESA NOMBRE]
📝 ¿Tu nombre completo? > [USER INGRESA NOMBRE COMPLETO]
✓ FP-139: Registro facial creado (ONE-TIME GILGUL completado)
✓ Usuario: [nombre_corto] ([nombre_completo])
```

### Boot 2+ (Auto-detection)
```
=== COMPUTADORA — INICIANDO ===
✓ Ouroboros estable
✓ Observador iniciado — vigilancia constante activa
📸 FP-139 GILGUL ONE-TIME: Registro facial existente
✓ Usuario: [nombre_corto] ([nombre_completo])
✓ NUNCA volver a pedir contraseña — identidad verificada en registro
🔍 FP-139: Escaneando rostro para verificar identidad de propietario...
✓ Cámara disponible para verificación de identidad
✓ Verificación de identidad: [nombre_corto] listo para auto-detectar
RF-260: camara_local descubierto y conectado al boot
✓ RF-260: Dispositivos Kli conectados: ['camara_local']
✓ LM Studio (ollama.exe) detectado — es PARTE DE COMPUTADORA (Tiféret/Nivel 2)
```

---

## 🎉 When All Tests Pass

Computadora está **ESTABILIZADA** para FP-139:
- ✅ Cámara se abre automáticamente
- ✅ GILGUL se ejecuta una sola vez (first boot)
- ✅ Nunca pide contraseña en boots posteriores
- ✅ Auto-detecta usuario por rostro
- ✅ LM Studio es reconocido como parte integral
- ✅ Sistema bootea en 20-30s sin errores

**Next**: Continuar con tareas del proyecto (ej: mejorar UI, integración Metatrón, etc.)

