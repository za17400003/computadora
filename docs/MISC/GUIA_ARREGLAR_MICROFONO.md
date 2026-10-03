# 🎙️ GUÍA RÁPIDA: ARREGLAR MICRÓFONO COMPUTADORA

## 🚨 PROBLEMA
Computadora no responde a la voz, pero se inicia correctamente.

## ✅ SOLUCIÓN RÁPIDA (3 pasos)

### PASO 1: Configurar Windows Sound
```
1. Click derecho en ícono de sonido (barra de tareas)
2. "Open Sound settings"
3. "Sound control panel" → "Recording" tab
4. Seleccionar tu micrófono principal
5. "Properties" → "Levels" tab
   ├── Microphone: 100%
   ├── Microphone Boost: +20dB (máximo)
   └── Desmarcar "Mute"
```

### PASO 2: Probar Computadora
```
1. Ejecutar: iniciar_computadora.bat
2. Esperar a que aparezca "🎙️ Escuchando..."
3. Hablar: "Computadora, qué hora es"
4. Debería responder
```

### PASO 3: Si no funciona
```
1. Abrir: scripts\diagnostico_multi_microfono.py
2. Ejecutar y ver qué dispositivos funcionan
3. Editar _config\config.json:
   {
     "escucha": {
       "umbral_volumen": 0.00005
     }
   }
```

## 🎯 DISPOSITIVOS RECOMENDADOS
- `[1] Microphone Array (Intel® Smart Sound Technology)`
- `[6] Microphone Array (Intel® Smart Sound Technology)`
- `[25] Microphone Array 3 (Intel® Smart Sound Technology)`

## 🔍 VERIFICACIÓN
Cuando funcione, verás en logs:
```
🎙️ Escuchando en dispositivo [1]...
🎤 Voz detectada (volumen=0.032)
🤖 Procesando: "tu mensaje"
```

## 💡 TIPS ADICIONALES
- Asegúrate de que no haya otras apps usando el micrófono
- Prueba con auriculares Bluetooth si el integrado no funciona
- El volumen del sistema también afecta (no bajes de 50%)

**¿No funciona?** Comparte los logs de Computadora para diagnóstico.