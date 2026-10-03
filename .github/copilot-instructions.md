# Copilot Instructions — Proyecto Computadora

## Boot Sequence (OBLIGATORIO)
1. Lee `DEVELOPMENT_WORKFLOW.md`
2. Lee `WorkItems.md`
3. Solo después actúa

## Reglas Anti-Colateral
- Leer antes de actuar
- Snapshot obligatorio en cada WorkItem
- Una tarea = un cambio atómico
- Lista cerrada de archivos por task
- No duplicar (verificar que no exista antes de crear)

## Pipeline Routing
- **A** Feature nueva → D1-D7 (todos los deptos)
- **B** Mejora UX → D1+D3+D4
- **C** Bug fix → D4 (acción directa)
- **D** Decisión de negocio → D2+D5+D6+D7
- **E** Cambio de arquitectura → D1+D4+D7

## Tria Prima (combinable ×N): `amén` = ejecutar autónomo (×2=profundo, ×3.=meta-análisis), `por favor` = petición (×2=urgente, ×3=emergencia), `gracias` = cierre (×2=+commit, ×3=+palingenesia)

## ⚗️ Pureza Alquímica del Tikún (FP-117)
Cada fase contiene EXCLUSIVAMENTE sus operaciones alquímicas:
- **NIGREDO** (שבירת הכלים): Solo DESTRUCCIÓN — cenizas crudas, sin filtrar, sin clasificar
- **ALBEDO** (טהרה): Solo PURIFICACIÓN — lavar, verificar, clasificar hallazgos
- **CITRINITAS** (אור חדש): Solo ILUMINACIÓN — investigación externa + síntesis dorada
- **RUBEDO** (קידושין): Solo MANIFESTACIÓN — coniunctio código+diseño, tests, projectio
- **PALINGENESIA** (גלגול): Solo RENACIMIENTO — retrospectiva + rotación + retorno

## SKU Optimization
- Usar subagents para investigación pesada (no saturar contexto principal)
- Session memory: limpiar al terminar conversación
- Priorizar reads paralelos sobre secuenciales
- Commits atómicos, no acumular cambios

## Fractal Pagination (FP-116)
Conforme el proyecto crece, aplicar:
- **Nivel 1**: WIs atómicos (1 cambio, 1-3 archivos)
- **Nivel 2**: FPs agrupan 3-6 WIs temáticos
- **Nivel 3**: Fases agrupan FPs por Sefirá
- Cada nivel se auto-subdivide cuando supera su capacidad natural
- Target: <6 archivos modificados por ciclo, <500 líneas cambiadas

## בראשית Bereshit — 11 Inscripciones Recursivas (FP-118→FP-128)

> Detalle completo en `DEVELOPMENT_WORKFLOW.md` §Etz HaChaim Operativo

| FP | Inscripción | Principio clave | Mapping operativo |
|----|-------------|-----------------|-------------------|
| 118 | אמת Emet | Fractal + Gevurá + Ouroboros | WI=mini-Computadora, amén=auto-audit, Sefirot→Deptos, Pipelines→Alquimia |
| 119 | אור וחושך Or v'Choshech | Tzimtzum + Or Yashar/Chozer + Kav | APIs=Kav, git=Reshimu, visión↓código↑refinamiento |
| 120 | רקיע Rakia | Separar + conectar aguas superiores/inferiores | Da'at=Rakia, Copilot=Rakia de Roles, Gate 2=Gran Rakia |
| 121 | ארץ וים Eretz v'Yam | Reunir (DRY) + nombrar (APIs) | Committed=Eretz, runtime=Yam, CONSERVAR=Yikavú |
| 122 | דשא Deshé | Tierra fértil + semilla generativa | COPILOT_SEED=Zerá, type safety=LeMinehú, Tria Prima |
| 123 | מאורות Me'orot | Sol=pytest, Luna=logs, Estrellas=métricas | Tests verdes=día, rojos=noche, milestones=Otot |
| 124 | נפש חיה Néfesh Jayá | Percibir + reaccionar + multiplicar | nlu.py=Néfesh, Orquestador=Tanín, subagents=Perú u'Revú |
| 125 | ברכה Berajá | Empoderar + producir fruto + llenar | Gate 2=Vayevarej, docs=Berajá Leamor, coverage=Mil'ú |
| 126 | בהמה ורמש Behemá v'Rémesh | Domesticado + fiera + rastreros | Helpers=Behemá, CI=Rémesh, NLU=Jayat Eretz |
| 127 | אדם Adam | Imagen + semejanza + dominio plural | Na'asé=Gate 2, SDD=Tzélem, Propietario=Elohim |
| 128 | שבת Shabbat | Completar + cesar + santificar | Committed=Kadosh, Gate 3=Vayejulú, Bará La'asot=bisagra |
