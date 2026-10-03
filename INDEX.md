# Índice Central — Proyecto COMPUTADORA

Este archivo es la guía principal de rutas y referencias del repositorio. Use este índice para encontrar rápidamente la documentación y las carpetas de trabajo.

---

## Empezar aquí

1. `WORKFLOW_OPERACIONAL.md` — proceso operativo para cambios en el proyecto
2. `SRS.md` — requisitos funcionales
3. `SDD.md` — diseño técnico y arquitectura
4. `WorkItems.md` — tareas actuales
5. `README.md` — información general y arranque

---

## Estructura básica del repositorio

```
proyecto-golem/
├── README.md
├── WORKFLOW_OPERACIONAL.md
├── SRS.md
├── SDD.md
├── WorkItems.md
├── INDEX.md
├── iniciar_computadora.bat
├── computadora/             # Código fuente principal
├── golem/                   # Código legacy / compatibilidad
├── tests/                   # Pruebas
├── docs/                    # Documentación técnica y guías
├── scripts/                 # Scripts de utilidad y soporte
├── datos/                   # Datos persistentes y configuraciones runtime
└── .logs/                   # Registros de ejecución
```

---

## Contenido clave

- `computadora/` — código principal del asistente
- `tests/` — pruebas unitarias y de integración
- `docs/` — guías, referencias y reportes
- `scripts/` — utilidades para diagnóstico y mantenimiento
- `datos/` — información persistente del sistema
- `.logs/` — archivos de registro
- `golem/` — carpeta legacy, no es el paquete principal de arranque

---

## Documentación importante

- `README.md` — descripción general, instalación y arranque
- `WORKFLOW_OPERACIONAL.md` — proceso de trabajo y validación de cambios
- `SRS.md` — qué debe hacer el sistema
- `SDD.md` — cómo está construido el sistema
- `WorkItems.md` — tareas activas y seguimiento

---

## Rutas útiles dentro de `docs/`

- `docs/GUIDES/` — guías prácticas y troubleshooting
- `docs/REFERENCE/` — referencia técnica y arquitectura
- `docs/REPORTS/` — reportes de auditoría y mejoras
- `docs/PROPOSALS/` — propuestas de mejora y nuevos requisitos

---

## Cómo usar este índice

- Si necesita entender una función, abra `SRS.md`.
- Si necesita entender la implementación, abra `SDD.md`.
- Si necesita revisar el estado del trabajo, abra `WorkItems.md`.
- Si necesita saber dónde colocar archivos nuevos, abra `WORKFLOW_OPERACIONAL.md`.

---

## Actualización

Mantenga `INDEX.md` sincronizado con la estructura real del repositorio. Si el repositorio cambia, actualice primero este archivo.
