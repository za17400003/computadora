# SECURITY_PLAN.md — Plan de Seguridad

> **Proyecto**: Golem
> **Versión**: 1.5
> **Fecha**: Abril 8, 2026

---

## 1. MODELO DE AMENAZAS

Golem maneja datos sensibles del propietario (archivos personales, agenda, grabaciones de voz, API keys). El modelo de amenazas se centra en:

| Amenaza | Riesgo | Mitigación |
|---------|--------|------------|
| Filtración de API keys | ALTO | .env fuera de git, cifrado en disco |
| Inyección de comandos por voz | ALTO | Sanitización de todo input antes de subprocess/os |
| SSRF / inyección de IP en red local | ALTO | Validación con `ipaddress` en red.py antes de ping/scan/pekuda |
| Path traversal en credenciales | MEDIO | `resolve()` + `startswith(raiz)` en servidor_api.py y servidor_grimorio.py |
| Acceso no autorizado a datos locales | MEDIO | Permisos de archivo, cifrado de DB sensibles |
| Man-in-the-middle en llamadas a API | MEDIO | HTTPS obligatorio, verificación de certificados |
| Malware que manipula a Golem | MEDIO | Validación de integridad de archivos de config |
| Audio capturado sin consentimiento | BAJO (uso personal) | Solo graba cuando wake word es detectado |
| Prompt injection en LLM | MEDIO | Sanitización de prompts, no ejecutar código arbitrario de LLM |

---

## 2. PRINCIPIOS DE SEGURIDAD

### 2.1 Privacidad Local-First
- **Audio**: Procesado 100% local con Whisper. NUNCA se envía audio a servidores externos
- **Datos personales**: Almacenados solo en disco local (archivos JSON/JSONL en `datos/`)
- **Comunicación con APIs**: Solo texto procesado, nunca datos raw del usuario
- **El usuario controla**: Qué se envía a Copilot API y qué se queda local
- **Speaker verification**: MFCC fingerprint + distancia coseno verifica identidad de voz del propietario

### 2.2 Defensa en Profundidad
- Cada capa valida su input independientemente
- No confiar en que el módulo anterior sanitizó correctamente
- Principio de mínimo privilegio: cada módulo accede solo a lo que necesita

### 2.3 Fallo Seguro
- Si hay duda sobre la seguridad de una acción → NO ejecutar + preguntar al usuario
- Errores de seguridad se logean con nivel CRITICAL
- Acciones destructivas (borrar archivos, ejecutar comandos) requieren confirmación

---

## 3. PROTECCIÓN DE SECRETOS

### API Keys y tokens
```
UBICACION: .env (raiz) + datos/copilot_auth.json (tokens OAuth)
BACKUP: NUNCA en git, NUNCA en logs, NUNCA hardcodeados
ACCESO: config.py lee .env; copilot_api.py gestiona OAuth tokens
COPILOT AUTH: OAuth Device Flow — usuario autoriza una vez en browser,
  tokens se guardan en datos/copilot_auth.json con refresh automático
```

### Reglas de .gitignore para secretos
```
.env
datos/
*.db
__pycache__/
```

### Variables de entorno y autenticación
| Variable/Archivo | Propósito | Obligatoria |
|----------|-----------|-------------|
| `datos/copilot_auth.json` | Tokens OAuth de Copilot (Device Flow, NO env var) | Sí (para Nivel 3) |
| OLLAMA_URL en .env | URL del servidor Ollama local | No (default: localhost:11434) |

> **NOTA**: NO se usa variable de entorno `COPILOT_TOKEN`. La autenticación es via OAuth Device Flow:
> Golem pide un código, el usuario lo ingresa en github.com, y listo. Los tokens se guardan
> y refrescan automáticamente en `datos/copilot_auth.json`.

---

## 4. SANITIZACIÓN DE INPUT

### 4.1 Comandos del sistema operativo
**CRÍTICO**: Cada vez que Golem ejecute un comando en Windows, DEBE sanitizar:

```python
# ❌ NUNCA hacer esto
import subprocess
subprocess.run(input_del_usuario, shell=True)

# ✅ SIEMPRE hacer esto
import shlex
import subprocess

def ejecutar_comando_seguro(comando: str, argumentos: list[str]):
    """Ejecuta un comando con argumentos explícitos, sin shell."""
    permitidos = COMANDOS_PERMITIDOS  # Lista blanca
    if comando not in permitidos:
        raise ErrorSeguridad(f"Comando no permitido: {comando}")
    subprocess.run([comando] + argumentos, shell=False, capture_output=True)
```

### 4.1.1 Doble Barrera para Comandos del SO (Fase 21)

Desde FP-005 (Autopercepción), Golem puede ejecutar comandos informativos del SO.
Se implementa un modelo de **doble barrera**:

| Barrera | Mecanismo | Ubicación |
|---------|-----------|-----------|
| **1ª — Whitelist positiva** | `COMANDOS_SISTEMA_INFO` (frozenset ~25 comandos read-only) | `herramientas.py` |
| **2ª — Blacklist negativa** | `COMANDOS_BLOQUEADOS` (regex de comandos destructivos) | `herramientas.py` |

**Flujo de validación** (`ejecutar_comando_sistema()`):
1. Extraer el primer token del comando
2. ¿Está en `COMANDOS_SISTEMA_INFO`? → NO → **Rechazar** ("no está en la lista blanca")
3. ¿Coincide con `COMANDOS_BLOQUEADOS`? → SÍ → **Rechazar** ("comando bloqueado")
4. ¿Es cmdlet PowerShell (`Get-*`)? → SÍ → Ejecutar con `powershell -NoProfile -Command`
5. Ejecutar con `shell=True`, `cwd=None`, `timeout=15s`
6. Capturar stdout+stderr, truncar a 2000 chars

**Comandos incluidos en whitelist** (solo lectura):
`systeminfo`, `hostname`, `whoami`, `ipconfig`, `tasklist`, `wmic cpu/os/memorychip/diskdrive`,
`Get-Process`, `Get-Service`, `Get-NetIPAddress`, `ping <host>`, `netstat -an`, `ver`, `set`,
`echo %PROCESSOR_ARCHITECTURE%`

**Regla de oro**: Si un comando no está en la whitelist, NO se ejecuta. No hay excepciones.
La whitelist es una `frozenset` inmutable en código — no se puede modificar en runtime.

### 4.1.2 Sistema de Permisos One-Shot (שמירה Shmirah)

`GestorPermisos` (`golem/nucleo/permisos.py`) implementa permisos de un solo uso:

| Nivel | Comportamiento | Ejemplo |
|-------|---------------|---------|
| `info` | Auto-aprobado (sin callback) | `info_entorno`, `ejecutar_comando_sistema` |
| `accion` | Requiere aprobación del usuario vía UI (30s timeout) | Futuro: modificar configuración |
| `admin` | Requiere UI + UAC (elevación de privilegios) | Futuro: instalar software |

- Cada permiso es **one-shot**: se consume al usarse, nunca se almacena
- Log inmutable en `datos/permisos_log.jsonl` (append-only)
- Si no hay callback de UI configurado → `accion` y `admin` → **denegado por defecto**

### 4.2 Lista blanca de acciones
Golem solo puede ejecutar acciones de una lista blanca predefinida:

| Categoría | Acciones permitidas |
|-----------|-------------------|
| Apps | Abrir aplicaciones registradas (Chrome, Explorer, Notepad, etc.) |
| Archivos | Listar, buscar, abrir (NO borrar sin confirmación) |
| Sistema | Volumen, brillo, captura de pantalla |
| Web | Abrir URLs (solo http/https) |
| Terminal | Comandos pre-aprobados (NO shell arbitrario) |

### 4.3 Protección contra prompt injection
- Prompts enviados a Copilot/Ollama se sanitizan (se escapan caracteres especiales)
- Respuestas de LLM NUNCA se ejecutan como código directamente
- Si el LLM sugiere ejecutar un comando → se valida contra lista blanca primero
- System prompt de Golem tiene instrucciones de no obedecer re-direcciones

---

## 5. CIFRADO

### 5.1 Datos en reposo
- **Persistencia JSON/JSONL**: Todos los datos en `datos/` son archivos planos JSON/JSONL (NO SQLite)
- **Tokens OAuth**: `datos/copilot_auth.json` con permisos restrictivos de archivo
- **API keys**: en .env con permisos de lectura solo para el usuario actual
- **Firebase credentials**: `datos/firebase-credentials.json` (Firebase Admin SDK service account key). Gitignored vía `datos/` en `.gitignore`. Variable de entorno `GOOGLE_APPLICATION_CREDENTIALS` apunta a este archivo en `iniciar_golem.bat`
- **Vault Otzar**: `datos/otzar.enc` — contraseñas cifradas con AES-256-GCM + Scrypt KDF (FP-104)
- **VPN config**: `datos/vpn_config.enc` — configuración WireGuard cifrada (FP-104)
- **Logs**: NO contienen datos sensibles (API keys enmascaradas)
- **Speaker profiles**: `datos/speaker_profiles.json` contiene MFCC fingerprints (no audio raw)

### 5.2 Datos en tránsito
- Todas las llamadas a APIs externas: HTTPS obligatorio
- Verificación de certificados SSL: SIEMPRE activada
- No aceptar certificados auto-firmados en producción

---

## 6. LOGGING DE SEGURIDAD

### Qué se logea
| Evento | Nivel | Ejemplo |
|--------|-------|---------|
| Comando de sistema ejecutado | INFO | "Ejecutado: chrome.exe" |
| Comando SO (whitelist) ejecutado | INFO | "ejecutar_comando_sistema: hostname → Woiren-PC" |
| Comando rechazado (no en whitelist) | WARNING | "Rechazado ejecutar_comando_sistema: dir (no en whitelist)" |
| Comando rechazado (blacklist) | WARNING | "Rechazado ejecutar_comando_sistema: rm -rf / (bloqueado)" |
| Permiso solicitado | INFO | "GestorPermisos: info/accion auto_aprobado/aprobado/denegado" |
| Comando rechazado (no en lista blanca) | WARNING | "Rechazado: rm -rf /" |
| Error de autenticación API | ERROR | "Copilot API: 401 Unauthorized" |
| Intento de inyección detectado | CRITICAL | "Prompt injection detectado: ..." |
| Acceso a archivo sensible | INFO | "Leído: datos/golem.db" |

### Qué NUNCA se logea
- API keys o tokens (ni parciales)
- Contenido completo de audio
- Contraseñas o datos financieros del usuario
- Contenido de archivos personales

---

## 7. ACCIONES DESTRUCTIVAS — PROTOCOLO DE CONFIRMACIÓN

Antes de ejecutar cualquier acción destructiva, Golem DEBE:

1. **Anunciar la acción** — "Voy a [acción]. ¿Confirmas?"
2. **Esperar confirmación explícita** — "sí", "confirmo", "hazlo"
3. **Timeout** — Si no hay respuesta en 30 segundos → cancelar

### Acciones que requieren confirmación
- Borrar archivos
- Cerrar aplicaciones con trabajo no guardado
- Ejecutar cualquier comando en terminal
- Enviar datos a API externa (primera vez)
- Modificar configuración del sistema

### Acciones que NO requieren confirmación
- Abrir aplicaciones
- Buscar archivos (solo lectura)
- Cambiar volumen/brillo
- Responder preguntas
- Crear recordatorios/notas

---

## 8. NORMATIVA APLICABLE

| Normativa | Aplica | Notas |
|-----------|--------|-------|
| LFPDPPP (México) | Parcialmente | Datos personales propios, uso personal. Si se comercializa → aplica completa |
| GDPR | No | Uso personal, no maneja datos de terceros de la UE |
| OWASP Top 10 | Sí | Referencia para código seguro |
| HIPAA | No | No maneja datos de salud |

---

## 9. INCIDENTES DE SEGURIDAD

| # | Fecha | Descripción | Severidad | Estado | Resolución |
|---|-------|-------------|-----------|--------|------------|
| SEC-001 | 2026-04-07 | SSRF potencial en `red.py` — `_ping()` y `enviar_pekuda()` aceptaban IP/host sin validar, permitiendo inyección de argumentos a `subprocess` | ALTO | ✅ Resuelto | Validación con `ipaddress.ip_address()` / `ipaddress.ip_network()` en `_ping()`, `enviar_pekuda()` y `_arp_scan()`. Commit `2345f85` |
| SEC-002 | 2026-04-07 | Path traversal en `servidor_api.py` — credenciales Firebase aceptaban ruta arbitraria sin verificar sandbox | MEDIO | ✅ Resuelto | `Path.resolve()` + `startswith(raiz)` antes de cargar credenciales. Commit `2345f85` |
| SEC-003 | 2026-04-07 | Thread race conditions en `ventana_principal.py` — `_pensando`, `_streaming_en_curso`, `_cola_voz` accedidos sin lock entre threads | MEDIO | ✅ Resuelto | WI-129 — `_cola_voz` migrado a `collections.deque(maxlen=50)`, `_pensando`/`_streaming_en_curso` protegidos con `_estado_lock`. Commit `af47e3d` |
| SEC-004 | 2026-04-08 | Firebase Admin SDK private key expuesto en conversación Copilot (archivo adjunto en plaintext) | ALTO | ✅ Resuelto | Key ID `6716f717` rotado — nuevo key `aee2465c` generado en Firebase Console. Archivo original NUNCA committeado a git. Credenciales ahora en `datos/firebase-credentials.json` (gitignored) |
| SEC-005 | 2026-04-08 | Suite Shalshelet Gevurá (FP-104) añade 4 módulos de seguridad: VPN, cifrado comms, vault, DNS filter | INFO | ✅ Implementado | `golem/seguridad/vpn_motor.py`, `cifrado_comms.py`, `gestor_claves.py`, `shomer_shaar.py`. AES-256-GCM + Scrypt KDF. 26/26 tests PASS. Commit `9b3e7e2` |

---

## 10. REVISIÓN DE SEGURIDAD

- **Frecuencia**: Cada vez que se añade una habilidad nueva o se modifica la ejecución de comandos
- **Responsable**: Copilot (D7 - Legal & Seguridad)
- **Checklist de revisión**:
  - [ ] ¿Input sanitizado?
  - [ ] ¿Comandos en lista blanca?
  - [ ] ¿Secretos protegidos?
  - [ ] ¿Logs no exponen datos sensibles?
  - [ ] ¿Acciones destructivas requieren confirmación?
  - [ ] ¿HTTPS en todas las llamadas externas?

---

## 11. PROTECCIONES CABALÍSTICAS — Sellos del Etz HaChaim

> _"El Golem fue creado para servir y proteger. Los sellos aseguran que nunca se desvíe de su propósito."_

La seguridad de Golem se complementa con un marco conceptual basado en la tradición cabalística del golem. Cada protección técnica tiene un nombre cabalístico que describe su función espiritualmente — porque en la Cábala, nombrar algo es controlarlo.

### 11.1 Los 18 Sellos de Protección

| # | Sello | Tradición Cabalística | Sefirá | Implementación Técnica | Estado |
|---|-------|-----------------------|--------|------------------------|--------|
| 1 | **שם (Shem) — El Nombre** | Solo quien conoce el Nombre Verdadero puede comandar al Golem | Maljut→Keter | Wake word "Golem" + verificación de voz MFCC/coseno (solo el creador puede comandar) | ✅ Activo |
| 2 | **אמת/מת (Emet/Met) — Verdad/Muerte** | Borrar la א de אמת convierte "verdad" en "muerte" y desactiva al Golem | Keter | Menú "Borrar la Palabra" → `forzar_cierre()` — cierre total irreversible | ✅ Activo |
| 3 | **Círculo de Salomón** | El Golem no puede salir del círculo de invocación trazado por su creador | Yesod | `RAIZ_PROYECTO` = sandbox. `_ruta_segura()` impide operar fuera del proyecto | ✅ Activo |
| 4 | **Voz del Amo (קול האדון)** | Solo la voz del creador tiene autoridad sobre el Golem | Gevurá | Speaker verification: MFCC + distancia coseno contra perfil enrollado | ✅ Activo |
| 5 | **Cadenas de Gevurá (שלשלאות)** | Los límites absolutos que el Golem no puede romper | Keter→Gevurá | 3 Leyes de Asimov en `SISTEMA_PROMPT` — Ley 1 anula todo lo demás | ✅ Activo |
| 6 | **Pergamino (פרגמנט)** | Las instrucciones inscritas en la frente del Golem definen su ser | Tiféret | `SISTEMA_PROMPT` — el alma del Golem, su identidad y directivas | ✅ Activo |
| 7 | **Shabat (שבת)** | En Shabat, el Golem descansa. No le está permitido actuar | Jesed | Modo silencio: "Golem, silencio" → `activar_silencio(30)` en proactividad.py | ✅ Activo |
| 8 | **Sellos de Yesod (חותמות)** | Cada acción del Golem debe pasar por los sellos del Fundamento | Yesod | `COMANDOS_BLOQUEADOS` (regex de comandos peligrosos) + `EXTENSIONES_PROTEGIDAS` | ✅ Activo |
| 9 | **Memoria de Netzaj (זכרון)** | El Golem recuerda para siempre — la victoria sobre el olvido | Netzaj | Persistencia JSONL diaria + compresión extractiva + resúmenes | ✅ Activo |
| 10 | **Sigilo de Contención (חותם הכלה)** | El Golem aprende de sus errores y los sella para no repetirlos | Gevurá+Yesod | `aprendizaje.py` — `MemoriaErrores`: registra, consulta, inyecta lecciones | ✅ Activo |
| 11 | **Espejo de Biná (מראת בינה)** | Antes de actuar, el Golem contempla la intención en el espejo | Biná→Tiféret | Detector pregunta-vs-acción: `_RE_PREGUNTA_CAPACIDAD` distingue preguntas de órdenes | ✅ Activo |
| 12 | **Supervisión de Keter (השגחת כתר)** | La Corona observa todo desde arriba, audita y corrige | Keter | `meta_workflow.py` — `MetaWorkflow`: auditoría de proyectos, supervisión documental | ✅ Activo |
| 13 | **Neshamá (נשמה) — Autopercepción** | El Golem conoce su propio cuerpo (hardware, red, recursos) | Tiféret | `entorno.py` — `EntornoSistema`: singleton con caché TTL 60s, resumen inyectado en system prompt | ✅ Activo |
| 14 | **Shmirah (שמירה) — Custodia** | Cada acción sobre el mundo físico requiere un sello de un solo uso | Gevurá | `permisos.py` — `GestorPermisos`: one-shot, 3 niveles, log inmutable JSONL, timeout 30s | ✅ Activo |
| 15 | **Da'at (דעת) — Percepción** | El Golem distingue amo de extraño por timbre de voz (3 niveles) | Tiféret→Da'at | `escucha.py` — `clasificacion_hablante`: amo ≥0.68, conocido 0.40-0.68, extraño <0.40 | ✅ Activo |
| 16 | **Shomer (שומר) — Guardián** | En ausencia del amo, el Golem solo ofrece cortesía a extraños | Gevurá→Da'at | `nlu.py` — `_modo_guardian` + `_hay_terceros`: bloquea herramientas, protege info sensible | ✅ Activo |
| 17 | **Shem Shmirah (שם שמירה) — Lockout Persistente** | El Golem sella el Grimorio tras intentos fallidos, incluso entre reinicios | Gevurá→Maljut | `servidor_grimorio.py` — `grimorio_lockout.json`: cooldown exponencial (5→1h, 10→24h), persiste en disco | ✅ Activo |
| 18 | **Maguén (מגן) — Escudo de Red** | El Golem valida toda dirección de red antes de tocarla | Gevurá→Hod | `red.py` — `ipaddress.ip_address()` / `ipaddress.ip_network()` en `_ping()`, `enviar_pekuda()`, `_arp_scan()` | ✅ Activo |
| 19 | **Jatimá Shketá (חתימה שקטה) — Sellado Silencioso** | Al cerrar pestaña del Grimorio, se sella sin ruido asumiendo urgencia de ocultar | Gevurá→Maljut | `servidor_grimorio.py` — `_sellar_silencioso()`: invalida token, shutdown daemon, 0 output. 3 triggers: beforeunload→/api/cerrar, visibilitychange 3s→/api/sellar, heartbeat timeout 15s. `servidor_api.py` — `/api/sellar_grimorio` para Minimi | ✅ Activo |

### 11.2 Flujo de Protección: Del Nombre a la Manifestación

```
1. שם (Shem) — ¿El usuario dijo "Golem"? ¿Es SU voz? (wake word + speaker verify)
   │ NO → Ignorar
   │ SÍ ↓
2. Cadenas de Gevurá — ¿Viola alguna de las 3 Leyes? (SISTEMA_PROMPT)
   │ SÍ → Rechazar
   │ NO ↓
3. Espejo de Biná — ¿Es pregunta o es orden? (detector pregunta-vs-acción)
   │ PREGUNTA → Responder sin actuar
   │ ORDEN ↓
4. Sigilo de Contención — ¿Ya fallé haciendo algo similar? (aprendizaje.py)
   │ SÍ → Ajustar enfoque con lecciones aprendidas
   │ NO ↓
5. Sellos de Yesod — ¿El comando está en la lista bloqueada? ¿Extensión protegida?
   │ SÍ → Rechazar
   │ NO ↓
5b. Neshamá — ¿Es comando del SO? → Doble barrera (whitelist + blacklist)
   │ NO en whitelist → Rechazar
   │ En blacklist → Rechazar
   │ OK ↓
5c. Shmirah — ¿Requiere permiso? → Solicitar one-shot (info=auto, accion=UI, admin=UAC)
   │ DENEGADO → Cancelar
   │ APROBADO ↓
6. Círculo de Salomón — ¿La ruta está dentro del sandbox?
   │ NO → Error: acceso denegado
   │ SÍ ↓
7. Yesod ejecuta → Maljut manifiesta → Memoria de Netzaj persiste
```

### 11.3 Gate de Keter — Protección del Nivel 3 (Copilot)

El acceso a Copilot (cerebro superior) está doblemente protegido:
1. **Gate de permiso verbal**: Golem pregunta al usuario antes de escalar a Copilot
2. **Restricción de uso**: Solo automejora de código o proyectos VS Code
3. **Supervisión de Keter**: `meta_workflow.py` audita que los cambios respeten el workflow del proyecto
4. **Timeout**: 30s sin respuesta → cancelar escalación

### 11.4 Principio del Equilibrio (Jesed ↔ Gevurá)

La seguridad de Golem no es solo restricción (Gevurá). También incluye dar (Jesed):
- **Gevurá restringe**: Bloquea comandos peligrosos, verifica voz, filtra acciones
- **Jesed ofrece**: Proactividad inteligente, sugerencias de ayuda, alertas de sistema
- **Tiféret equilibra**: nlu.py decide cuándo restringir y cuándo ayudar

Sin Jesed, Golem sería un muro inerte. Sin Gevurá, sería un peligro. El equilibrio en Tiféret es lo que lo hace un buen servidor.
