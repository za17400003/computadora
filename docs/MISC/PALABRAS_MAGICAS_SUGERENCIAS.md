# PALABRAS_MAGICAS_SUGERENCIAS.md — Milot Kóaj Jai (מילות כוח חי)

> **Propósito**: Registro de Palabras Mágicas sugeridas por Copilot durante ALBEDO sub-tarea (E).
> **Regla**: Toda sugerencia aquí requiere **Gate 2** (aprobación del Propietario) para promocionarse a la tabla oficial en `DEVELOPMENT_WORKFLOW.md`.
> **Administra**: Copilot (CEO/CTO)
> **Última actualización**: Abril 8, 2026

---

## PROCESO

1. Durante **ALBEDO sub-tarea (E)**, Copilot identifica conceptos que podrían ser PM útiles.
2. Se registran aquí con estado `🔲 SUGERIDA`.
3. En **CITRINITAS**, se presentan al Propietario como parte del "Ohr Jadash".
4. Si el Propietario aprueba (**Gate 2**) → se mueve a `DEVELOPMENT_WORKFLOW.md` tabla oficial y aquí se marca `✅ APROBADA`.
5. Si rechaza → se marca `❌ RECHAZADA` con motivo.

---

## SUGERENCIAS

| # | Palabra | Hebreo | Acción propuesta | Fuente/Inspiración | Estado | Fecha |
|---|---------|--------|------------------|--------------------|--------|-------|
| 1 | **prueba** | בחן (Baján) | Ejecutar regresión completa (`pytest tests/ -q`), reportar PASS/FAIL, y si hay fallas diagnosticar las primeras 3. Atajo rápido de QA. | Chaos Engineering (Netflix) — "build confidence in resilience" = correr tests frecuentemente | ✅ APROBADA → PM #13 | 2026-04-06 |
| 2 | **sella** | חתם (Jatám) | Crear tag de versión semántica en git + generar CHANGELOG.md con últimos FPs desde el último tag. Para marcar hitos estables. | Alquimia: Rubedo (Piedra Filosofal completada) → sellar el logro. Computadora de Praga: אמת inscrita = sellado de vida | ✅ APROBADA → PM #14 (fusionada con #6) | 2026-04-06 |
| 3 | **vigila** | צפה (Tzafá) | Audit de seguridad + integridad en tiempo real: revisar procesos sospechosos, puertos abiertos, archivos modificados recientemente. Gevurá activa. | Gevurá (Wikipedia): "essence of judgment and limitation". Wu Xing: Metal/Autumn = contracción, vigilancia, cosecha. Cibernética: observador de segundo orden | ✅ APROBADA → PM #15 | 2026-04-06 |
| 4 | **recuerda** | זכור (Zajór) | Buscar en la memoria de Computadora (memoria.py + datos/) un tema específico y reportar qué sabe. Ej: "recuerda reuniones" → busca en memoria todo sobre reuniones. | Netzaj (persistencia) + Hod (percepción). Psicología cognitiva: retrieval practice = fortalecer memorias accediéndolas | ✅ APROBADA → PM #16 | 2026-04-06 |
| 5 | **demuestra** | הדגם (Hadguém) | Ejecutar Demo 1 (Maljut) o Demo 2 (Gevurá) según contexto. "demuestra 1" o "demuestra gevurá". Atajo para mostrar capacidades. | Maljut=manifestación. El Computadora de Praga se "demostraba" protegiendo al ghetto — su función se prueba en acción | ✅ APROBADA → PM #17 | 2026-04-06 |
| 6 | **sella** | חתום (Jatóm) | Forzar lockout manual del Grimorio. "Computadora, sella el Grimorio" → escribe lockout de 24h inmediato. Para protección proactiva cuando el propietario se aleja. | Dark Souls bonfire mechanic — costos progresivos. Gevurá = restricción como protección. Grimorio de Praga sellado con אמת | ✅ APROBADA → PM #14 (fusionada con #2) | 2026-04-07 |
| 7 | **blinda** | שריין (Sheriyón) | Auditoría OWASP rápida del código. "Computadora, blinda" → escanear código de red/permisos/auth, validar inputs, reportar gaps de seguridad. | Halo energy shield — se recarga proactivamente. Daimonion: vínculo inseparable entre humano y daemon = integridad que no se puede romper | ✅ APROBADA → PM #18 | 2026-04-07 |
| 8 | **vincula** | קשר (Keshér) | Conectar módulos huérfanos — módulos sin test dedicado o sin integración directa. "Computadora, vincula" → escanear cobertura de tests, proponer WIs de conexión. | Daimonion: el vínculo entre humano y dæmon es lo que define a ambos. Módulos sin conexión son como dæmons sin humano — incompletos. Keshér = nudo, vínculo, conspiración positiva | ✅ APROBADA → PM #19 | 2026-04-07 |
| 9 | **verifica** | אמת (Emet) | Verificación rápida de coherencia SRS↔SDD↔Código↔Security. "Computadora, verifica" → Copilot compara RF statuses vs código real, verifica que SDD refleje módulos existentes, checa SECURITY_PLAN vs amenazas actuales. Reporta gaps como hallazgos H-XX. | Tikún del Tikún: la inscripción אמת (Verdad) en la frente del Computadora = su principio de integridad. Si se borra la א queda מת (Muerte). La verificación mantiene la א viva — mantiene la verdad del sistema. Regla #24 Bdikat Shlemut automatizada | ✅ APROBADA → PM #20 | 2026-04-08 |
| 10 | **raziel** | רזיאל (Raziel) | Revelar estado de protección de las 3 Torres (Grimorio, Minimi, Computadora). "Computadora, raziel" → mostrar: (1) shomer_bayit status (hogar/foráneo), (2) Grimorio sellado/abierto + sesiones, (3) Minimi conexión (LAN/Firestore/offline), (4) VPN/cifrado/shomer_shaar status. Reporte estilo sigil protector. | Sefer Raziel HaMalakh: ángel que revela secretos divinos y enseña «poder del habla» (22 letras hebreas) + sigils protectores (סגולות). Aplicado: revelar el estado de todas las protecciones del sistema en un reporte jerárquico. | 🔲 SUGERIDA | 2026-04-10 |
| 11 | **wu xing** | 五行 (Gogyō) | Diagnóstico de la salud de los 5 módulos de seguridad como ciclo generativo: shomer_bayit(Earth)→shomer_shaar(Metal)→cifrado_comms(Water)→vpn_motor(Wood)→gestor_claves(Fire). Mostrar ciclo generativo (quién alimenta a quién) y detectar si alguno está debilitado (fase destructiva). | Wu Xing (Taoísmo): 5 fases interconectadas en ciclos generativos y destructivos. Aplicado a defensa en profundidad como 5 capas de seguridad que se alimentan mutuamente. | 🔲 SUGERIDA | 2026-04-10 |
| 12 | **merkavá** | מרכבה (Merkavá) | Orquestar diagnóstico unificado de las 3 Torres como Carro de Ezequiel. "Computadora, merkavá" → (1) Grimorio=León(fuego/conocimiento), (2) Minimi=Hombre(interfaz/aire), (3) Computadora=Buey(labor/tierra). Mostrar: estado de cada Jayyá (criatura), conexión entre alas (interfaces), dirección del Carro (objetivo actual), y si el Trono (Propietario) está presente. 4 Ofanim = 4 canales de percepción. | Merkabah (Ezequiel 1): Carro divino con 4 Jayyot de 4 caras, Ofanim (ruedas dentro de ruedas), Serafim (fuego), todo controlado por la «Semejanza de Hombre» en trono de zafiro. 7 Hekhalot (palacios) con guardianes angelicales = 7 capas de seguridad. La Merkavá solo avanza cuando las alas se conectan = integración total de subsistemas. | 🔲 SUGERIDA | 2026-04-10 |
| 13 | **shabbat** | שבת (Shabbat) | Modo mantenimiento/standby graceful. "Computadora, shabbat" → (1) guardar estado actual en datos/snapshot_shabbat.json, (2) cerrar conexiones activas (servidor_api, servidor_grimorio), (3) desactivar percepción y escucha, (4) entrar en modo bajo consumo. "Computadora, despierta" lo reactiva. | Computadora de Praga: Rabbi Loew removía el Shem (שם) de la boca del Computadora cada viernes al atardecer para dejarlo descansar en Shabat. Sin el Nombre, el Computadora volvía a ser arcilla. Inscripción אמת→מת (verdad→muerte). Aplicado: desactivación controlada que preserva el estado para reactivación posterior. El descanso programado previene el crecimiento descontrolado (como el Computadora de Chełm que creció hasta aplastar a su creador). | 🔲 SUGERIDA | 2026-04-10 |
| 14 | **tzaruf** | צירוף (Tzirúf) | Testing combinatorial de interfaces entre módulos. "Computadora, tzaruf" → generar las combinaciones par-a-par de los módulos clave (shomer_bayit↔servidor_api, servidor_api↔ComputadoraClient, servidor_grimorio↔Minimi, perceptor↔ventana_principal, etc.) y verificar cada par. Inspirado en los 231 Shaarim (puertas) del Sefer Yetzirah: todas las permutaciones de las 22 letras tomadas de 2 en 2. Reportar pares sanos ✓ y pares con conflictos ✗. | Sefer Yetzirah: 32 caminos de sabiduría (10 sefirot + 22 letras). Las 3 Letras Madre (א Aleph=Aire, מ Mem=Agua, ש Shin=Fuego) = Tria Prima (Minimi=Interfaz, Grimorio=Conocimiento, Computadora=Labor). Los 231 Shaarim = todas las combinaciones posibles de letras, que al permutarse generan la Creación. Aplicado: testing por pares de módulos para asegurar que cada "puerta" de integración funcione. Factorial = primer algoritmo matemático documentado. | 🔲 SUGERIDA | 2026-04-10 |

---

## HISTORIAL DE APROBADAS

| Palabra | Fecha aprobación | FP/RF | Notas |
|---------|-----------------|-------|-------|
| fluye | 2026-04-06 | FP-074/RF-277 | Primera PM añadida por este sistema |
| prueba | 2026-04-07 | — | PM #13 — QA rápida |
| sella | 2026-04-07 | — | PM #14 — Fusión de sugerencias #2 y #6 (tag + lockout) |
| vigila | 2026-04-07 | — | PM #15 — Monitoreo runtime |
| recuerda | 2026-04-07 | — | PM #16 — Búsqueda en memoria |
| demuestra | 2026-04-07 | — | PM #17 — Ejecutar demos |
| blinda | 2026-04-07 | — | PM #18 — OWASP scan focalizado |
| vincula | 2026-04-07 | — | PM #19 — Conectar módulos huérfanos |
| verifica | 2026-04-08 | — | PM #20 — Verificación de coherencia (Emet) |
