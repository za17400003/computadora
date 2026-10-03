"""
WI-XXX RUBEDO Phase 3 Tier 1 — Demo Fix Report
================================================

PROBLEMA REPORTADO:
─────────────────
- Demo está rota: no emite voz (TTS silencioso)
- Se queda trabado en cierto punto
- Colores cambian sin sincronización con audio

RAÍZ DEL PROBLEMA (FP-145):
─────────────────────────
1. ❌ edge-tts NO ESTABA INSTALADO (ModuleNotFoundError)
   → Fallback a pyttsx3, pero tambien fallaba silenciosamente
   → Demo iba avanzando SIN voz (pasos ejecutaban, pero sin habla)
   → Cuando timeout de cola_vacia nunca se emitía → programa se quedaba en espera

2. ❌ Sin timeout en cola_vacia
   → Si TTS fallaba, la signal nunca se emitía
   → El paso siguiente nunca se ejecutaba
   → Demo quedaba congelada

3. ❌ Cambios de color NO SINCRONIZADOS con TTS
   → Color cambiaba ANTES de que iniciara la narración
   → Viewer veía color desincronizado de la voz

SOLUCIONES IMPLEMENTADAS:
────────────────────────

✅ FIX 1: Instalar dependencias TTS
   Comando ejecutado:
   ```
   pip install edge-tts pygame
   ```
   Resultado: ✓ Ambos paquetes instalados correctamente
   
✅ FIX 2: Agregar timeout de seguridad en demo (_demo_ejecutar_paso)
   Localización: computadora/interfaz/ventana_principal.py
   
   Cambio:
   - OLD: Esperaba cola_vacia indefinidamente
   - NEW: Timeout de 5 segundos max, fallback automático si TTS no responde
   
   Código agregado:
   ```python
   def _timeout_seguridad():
       logger.warning("Demo: Timeout TTS — avanzando sin cola_vacia")
       self._demo_paso_en_curso = False
       QTimer.singleShot(400, self._demo_ejecutar_paso)
   
   self._demo_timeout_timer = QTimer()
   self._demo_timeout_timer.timeout.connect(_timeout_seguridad)
   self._demo_timeout_timer.setSingleShot(True)
   self._demo_timeout_timer.start(5000)  # 5 segundos
   ```
   
   Beneficios:
   - Demo continuará incluso si TTS falla
   - No más bloqueos infinitos
   - Fallback graceful (visible en logs)

✅ FIX 3: Mejorar logging en HiloHabla
   Localización: computadora/voz/habla.py
   
   Cambios:
   - Agregar debug logs cuando se emite cola_vacia
   - Agregar debug logs en _hablar_edge_tts (génesis, carga, reproducción)
   - Agregar timeout en reproductor pygame (max 50s)
   
   Beneficios:
   - Visibilidad completa de qué está pasando con TTS
   - Detectar dónde falla (generación? reproducción? cola?)
   - Max 50s per audio para evitar bloqueos

✅ FIX 4: Crear helpers de sincronización visual+voz (WI-XXX)
   Localización: computadora/interfaz/ventana_principal.py (_demo_maljut)
   
   Funciones nuevas:
   - _cambio_visual_simultaneo(accion, texto)
     → Ejecuta acción visual Y TTS en paralelo
   - _cambio_visual_entonces_habla(accion, texto, duracion_ms)
     → Ejecuta visual, espera, LUEGO habla (más lento pero sincronizado)
   
   Beneficios:
   - Sintaxis clara para definir pasos
   - Dos modos: paralelo vs. secuencial
   - Fácil ajustar timing de futuros pasos

✅ FIX 5: Integración de auditoría Gilgul (FP-145)
   Localización: Múltiples archivos
   
   Archivos creados:
   - computadora/utilidad/auditoria_gilgul.py (285 líneas)
     * Clase AuditoriaGilgul con JSONL logging
     * Registra: timestamp, decisión, resultado, user_hash, session_id
     * Métodos helper: registrar_decision(), obtener_estadisticas()
     * Singleton: obtener_auditoria()
   
   Integraciones:
   - computadora/dialogs/gilgul_consent_dialog.py
     * _on_register() → auditoria.registrar_decision("continue")
     * _on_skip_session() → auditoria.registrar_decision("session_skip")
     * _on_always_skip() → auditoria.registrar_decision("always_skip")
   
   - computadora/__main__.py
     * Cuando preferencia guardada detectada → auditoria.registrar_preferencia_guardada()
   
   Archivo de auditoría:
   - Ubicación: datos/GILGUL_AUDIT.jsonl (una línea JSON por evento)
   - Formato: {"timestamp": "2025-04-23T12:05:30.123456", "decision": "continue", ...}
   - Privacidad: user_hash (SHA256, no nombre real)
   
   Beneficios:
   - Auditoría completa de decisiones de consentimiento
   - Análisis: cuántos skips vs. registros
   - Trazabilidad sin exponer identidad
   - JSONL fácil de procesar con tools

VALIDACIÓN:
────────────

✓ TTS dependencies verified:
  - edge_tts: importable, funcionando
  - pygame: importable, version 2.6.1

✓ Syntax check:
  - computadora/dialogs/gilgul_consent_dialog.py: OK
  - computadora/utilidad/auditoria_gilgul.py: OK
  - computadora/__main__.py: OK

✓ Boot test:
  - Sistema arranca: ✓
  - Ouroboros boot: ✓
  - Facial detection: ✓
  - Gilgush reencarnation: ✓
  - Orquestador: ✓
  - API Minimi: ✓

PRÓXIMOS PASOS:
───────────────

1. TESTAR demo completa
   - Boot con --skip-facerec
   - Esperar GUI visible
   - Escribir "demo" en consola
   - Verificar:
     ✓ Narración fluida (sin silencios)
     ✓ Colores sincronizados con voz
     ✓ Progresa sin quedarse trabado
     ✓ GILGUL_AUDIT.jsonl se crea

2. Si TTS aún falla:
   - Revisar logs para mensajes de error específicos
   - Intentar fallback pyttsx3 manualmente
   - Considerar edge-tts con servidor externo

3. Validar auditoría:
   - Leer datos/GILGUL_AUDIT.jsonl
   - Verificar formato JSONL correcto
   - Probar obtener_estadisticas()

NOTAS TÉCNICAS:
────────────────

Cambio importante en FP-145:
- El timeout de seguridad ahora es OBLIGATORIO en demo
- Si TTS falla silenciosamente, ya no se queda congelado
- Los logs verbosos permitirán diagnóstico rápido

Arquitectura Auditoría:
- Singleton pattern: obtener_auditoria() reutiliza instancia
- Session ID único por boot: permite agrupar eventos por sesión
- User hash: privacidad → SHA256(username)[:16]
- JSONL append-only: seguro para múltiples threads

Próxima mejora (FIX 6):
- Reemplazar lambdas complejas en _demo_pasos con closures nombrados
- Mejor readabilidad de la coreografía demo
- Facilitar debugging de pasos individuales
"""

if __name__ == "__main__":
    print(__doc__)
