# 🎯 GUÍA ULTRA-DETALLADA - COPIAR TRANSCRIPCIÓN DE YOUTUBE

## OBJETIVO
Copiar la TRANSCRIPCIÓN del video en los 5 idiomas disponibles.

---

## VIDEO
- **URL**: https://www.youtube.com/watch?v=Apv4cRO0DWo
- **Título**: "Esto es el fin"
- **Idiomas disponibles**: 5 (Español, Alemán, Inglés, Japonés, Portugués)

---

## INSTRUCCIONES PASO A PASO

### 🔵 PASO 1: Abre YouTube en navegador
```
1. Navega a: https://www.youtube.com/watch?v=Apv4cRO0DWo
2. Espera que el video cargue completamente (5-10 segundos)
3. Verás el reproductor de video en el centro
```

---

### 🔵 PASO 2: Busca el botón "MOSTRAR TRANSCRIPCIÓN"

**Ubicación exacta:**
```
┌─────────────────────────────────────┐
│         REPRODUCTOR VIDEO           │
│                                     │
│  [Play] ████████░░░░░░░░ (barra)   │
│                                     │
│  BOTÓN "..." (tres puntos)          │
│  → Esquina INFERIOR DERECHA         │
│  → Al lado de los controles         │
│  → Verás: [CC] [⚙] [...] [<] [>]   │
│                                     │
│  ☝ CLICK AQUÍ en los 3 puntos (...)│
│                                     │
└─────────────────────────────────────┘
```

**Si no ves el reproductor completo:**
- Expande navegador a pantalla completa (F11)
- O presiona 'f' en el video para modo pantalla completa

---

### 🔵 PASO 3: Menú contextual aparecerá

**Verás un menú vertical como este:**
```
┌─────────────────────────────┐
│ Mostrar transcripción   ← AQUÍ
│ Mostrar estadísticas        │
│ Información técnica         │
│ ...más opciones...          │
└─────────────────────────────┘
```

**CLICK en: "Mostrar transcripción"**

---

### 🔵 PASO 4: Panel derecho aparecerá

**Un PANEL aparecerá a la DERECHA del video:**
```
LADO IZQUIERDO          │ LADO DERECHO
[REPRODUCTOR VIDEO]     │ ┌─────────────────┐
                        │ │ TRANSCRIPCIÓN   │
                        │ │                 │
                        │ │ [Español ▼]     │ ← SELECTOR IDIOMA
                        │ │                 │
                        │ │ 0:00            │
                        │ │ [Primera línea  │
                        │ │  del video]     │
                        │ │                 │
                        │ │ 0:05            │
                        │ │ [Segunda línea] │
                        │ │                 │
                        │ │ ...más texto... │
                        │ └─────────────────┘
```

---

### 🔵 PASO 5: COPIA TODO EL TEXTO

**Opción A: Copiar TODO (recomendado)**
```
1. En el panel DERECHO, busca el botón "⋮" (3 puntos vertical)
   → Está en la esquina superior del panel
   
2. CLICK en él
   
3. Verás opción: "Copiar"
   
4. CLICK en "Copiar"
   
5. TODO el texto de la transcripción está en tu portapapeles
```

**Opción B: Seleccionar manualmente (si no hay botón copiar)**
```
1. En el panel derecho, CTRL+A (selecciona todo)
2. CTRL+C (copia)
3. Listo
```

---

### 🔵 PASO 6: Abre editor de texto

```
1. Abre Notepad:
   - Windows: Presiona Win, escribe "Notepad", presiona Enter
   
2. O abre VSCode:
   - Windows: Presiona Win, escribe "VSCode", presiona Enter
   
3. O usa cualquier editor de texto
```

---

### 🔵 PASO 7: Pega el contenido

```
1. En el editor abierto, presiona CTRL+V
2. Se pegará TODO el contenido de la transcripción
3. Verás algo así:

   0:00
   Aquí es donde empieza el video
   Texto de la transcripción...
   
   0:05
   Más texto del video
   
   ... y así sucesivamente
```

---

### 🔵 PASO 8: Guarda con nombre correcto

**Guarda en: `c:\Users\woire\Documents\proyecto-golem\`**

**Nombres por idioma:**
```
Español (MX):  transcripcion_es.txt
Alemán:        transcripcion_de.txt
Inglés (GB):   transcripcion_en.txt
Japonés:       transcripcion_ja.txt
Portugués:     transcripcion_pt.txt
```

**En VSCode:**
1. File → Save As (o Ctrl+Shift+S)
2. Escribe nombre completo: `transcripcion_es.txt`
3. Asegúrate que Location sea: `c:\Users\woire\Documents\proyecto-golem\`
4. Selecciona formato: "All Files"
5. SAVE

---

### 🔵 PASO 9: Cambia idioma en YouTube y REPITE

**Vuelve a YouTube (video aún está abierto)**

**En el panel de transcripción:**
```
┌─────────────────────────┐
│ [Español ▼]             │ ← CLICK AQUÍ
│ Ver otros idiomas       │
│ ├─ Deutsch              │
│ ├─ English              │
│ ├─ 日本語                │
│ └─ Português            │
└─────────────────────────┘
```

**Selecciona el siguiente idioma**

**Repite PASOS 5-8 para cada idioma:**
1. Copia (⋮ → Copiar)
2. Pega en nuevo archivo
3. Guarda con nombre correcto

---

## ⏱️ RESUMEN TIEMPOS

| Tarea | Tiempo |
|-------|--------|
| Copiar 1 transcripción | 2-3 min |
| Copiar 5 transcripciones | 10-15 min |
| Guardar archivos | 2-3 min |
| **TOTAL** | **15-20 min** |

---

## ✅ VERIFICACIÓN

Una vez termines, ejecuta esto:

```powershell
cd c:\Users\woire\Documents\proyecto-golem
python scripts/VERIFICADOR_DISPONIBILIDAD.py
```

**Deberías ver:**
```
✅ resiste-protected.pdf
✅ PyPDF2 disponible
✅ ANALIZAR_Y_DESENCRIPTAR.py
✅ transcripcion_es.txt
✅ transcripcion_de.txt
✅ transcripcion_en.txt
✅ transcripcion_ja.txt
✅ transcripcion_pt.txt
✅ TODAS LAS TRANSCRIPCIONES PRESENTES
```

---

## 🎯 PASO FINAL: EJECUTA EL ANALIZADOR

Una vez los 5 archivos estén guardados:

```powershell
python scripts/ANALIZAR_Y_DESENCRIPTAR.py
```

**El script va a:**
1. Cargar las 5 transcripciones
2. Buscar palabras que empiezan con V
3. Extraer primeras líneas ("el comienzo")
4. Intentar 100+ candidatos de contraseña
5. **ENCONTRAR LA CONTRASEÑA** 🎉

---

## 🆘 PROBLEMAS COMUNES

### P: No veo el panel de transcripción
**A:** 
- Recarga la página (F5)
- Asegúrate de estar en YouTube.com (no YouTube Kids)
- Intenta en Firefox o Chrome (no Edge)

### P: El botón "Mostrar transcripción" está gris
**A:**
- YouTube sigue cargando, espera 10 segundos
- Recarga la página completa

### P: No hay 5 idiomas disponibles
**A:**
- Este video específico tiene 5 idiomas
- Si faltan, puede estar viendo versión antigua
- Recarga con F5 o Ctrl+Shift+R (caché limpio)

### P: El archivo no guarda bien
**A:**
- Asegúrate que esté en UTF-8
- VSCode: File → Save with Encoding → UTF-8
- Nota el nombre exacto (sin mayúsculas, con minúsculas)

---

## 📧 SI NECESITAS AYUDA

Una vez tengas el contenido del video, puedes:
1. Compartir las primeras líneas de cada idioma
2. El agente creará los archivos automáticamente
3. El agente ejecutará el analizador

**¡No necesitas copiar manualmente, puedo hacerlo por ti!**

---

**¡ADELANTE! Tienes esto, son solo 15 minutos de copy-paste. 💪**
