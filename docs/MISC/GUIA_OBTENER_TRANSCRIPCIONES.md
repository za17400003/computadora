# 🎬 GUÍA RÁPIDA - OBTENER TRANSCRIPCIONES YOUTUBE

## El Problema
YouTube protege sus transcripciones. Los descargadores automáticos (yt-dlp, youtube-transcript-api) encuentran bloqueos de seguridad.

## La Solución: COPIAR MANUAL (100% confiable)

### Paso 1: Abre el video
- URL: https://www.youtube.com/watch?v=Apv4cRO0DWo
- Título: "Esto es el fin"

### Paso 2: Abre la transcripción en YouTube
1. Mientras reproducción de video
2. Click en el botón **"..." (tres puntos)** en esquina inferior derecha del reproductor
3. Selecciona **"Mostrar transcripción"** (o "Show transcript" en inglés)
4. Un panel aparecerá a la DERECHA con el texto

### Paso 3: Cambia entre idiomas
- En el panel de transcripción hay un **selector de idiomas**
- Ahí puedes cambiar entre:
  - Español (MX) ← ORIGINAL
  - Deutsch/Alemán
  - English (GB)
  - 日本語 (Japonés)
  - Português (Brasileño)

### Paso 4: Copia la transcripción
1. En el panel de transcripción, busca el botón **"⋮"** (tres puntos vertical)
2. Click en él
3. Selecciona **"Copiar"** o **"Copy"**
4. El TEXTO COMPLETO se copia al portapapeles

### Paso 5: Guarda en archivo
1. Abre Notepad o VSCode
2. Pega el contenido (Ctrl+V)
3. Guarda en proyecto-computadora con estos nombres:
   - `transcripcion_es.txt` (español - ORIGINAL)
   - `transcripcion_de.txt` (alemán)
   - `transcripcion_en.txt` (inglés)
   - `transcripcion_ja.txt` (japonés)
   - `transcripcion_pt.txt` (portugués)

### Paso 6: Busca la contraseña
Ejecuta en terminal:
```powershell
cd c:\Users\woire\Documents\proyecto-computadora
python scripts/ANALIZAR_Y_DESENCRIPTAR.py
```

El script:
- Cargará las 5 transcripciones
- Buscará palabras que empiezan con V
- Extraerá "el comienzo" (primeras líneas)
- Intentará desencriptar el PDF
- Mostrará la contraseña si la encuentra

---

## ⏱️ Tiempo Estimado
- Copiar 5 transcripciones: **10-15 minutos**
- Ejecutar análisis: **1-2 segundos**
- Total: **~15 minutos**

## 💡 Pistas Importantes
- El video tiene DIFERENTES contenido en cada idioma
- Los 5 idiomas son parte de un PUZZLE
- La contraseña comienza con **V**
- La contraseña es una frase que "utilizamos desde el comienzo"
- "El comienzo" probablemente significa: **primeras líneas del video**

## ⚙️ Troubleshooting

### P: No veo el botón "Mostrar transcripción"
**R:** 
- No todos los videos tienen transcripción
- Intenta cambiar el idioma de YouTube (esquina inferior izq.)
- Si aparece "Transcripción automática" está OK

### P: La transcripción está vacía
**R:**
- YouTube a veces carga lentamente
- Espera 5 segundos
- Refresca la página (F5)
- Intenta otro idioma primero

### P: No encuentro los 3 puntos (⋮)
**R:**
- Deben estar en el panel DERECHO de transcripción
- Si no ves panel, YouTube puede estar en versión antigua
- Intenta en navegador incógnito (Ctrl+Shift+N)

### P: El script no encuentra los archivos
**R:**
- Verifica que los archivos estén en la raíz: `c:\Users\woire\Documents\proyecto-computadora\`
- NO en carpeta `scripts/`
- Revisa nombres exactos sin mayúsculas

---

## 📊 Estado Actual

| Idioma | Archivo | Estado |
|--------|---------|--------|
| Español (MX) | transcripcion_es.txt | ❌ PENDIENTE |
| Alemán | transcripcion_de.txt | ❌ PENDIENTE |
| Inglés (GB) | transcripcion_en.txt | ❌ PENDIENTE |
| Japonés | transcripcion_ja.txt | ❌ PENDIENTE |
| Portugués (BR) | transcripcion_pt.txt | ❌ PENDIENTE |

---

## 📝 Comandos Útiles

```powershell
# Verificar qué transcripciones existen
ls transcripcion_*.txt

# Contar líneas en una transcripción
(Get-Content transcripcion_es.txt).Count

# Ver primeras líneas
Get-Content transcripcion_es.txt -Head 5
```

---

## 🎯 Objetivo Final

1. ✅ Obtener 5 transcripciones manualmente
2. ✅ Guardarlas con nombres correctos en proyecto-computadora/
3. ✅ Ejecutar ANALIZAR_Y_DESENCRIPTAR.py
4. ✅ Script encuentra contraseña automáticamente
5. ✅ Abre PDF y ve qué hay dentro

**Una vez tengas las transcripciones, todo es automático. ¡El script hará el trabajo!**
