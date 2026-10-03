# WORKFLOW OPERACIONAL — Computadora

> Fecha: Mayo 31, 2026
> Propósito: Guía compacta para realizar cambios en el proyecto de forma disciplinada.

---

## Propósito

Este documento es una guía de acción para la ingeniería del proyecto. No es teórico: es la secuencia de pasos que debe seguirse antes, durante y después de cada cambio.

---

## Inicio obligatorio

Antes de hacer cambios o tomar decisiones, lea en este orden:

1. `INDEX.md` — mapa general del repositorio
2. `SRS.md` — requisitos funcionales
3. `SDD.md` — diseño técnico y arquitectura
4. `WorkItems.md` — estado actual de las tareas
5. `WORKFLOW_OPERACIONAL.md` — proceso operativo

---

## Cuándo consultar cada documento

| Necesidad | Documento principal |
|-----------|---------------------|
| Entender qué debe hacer el sistema | `SRS.md` |
| Entender cómo está construido | `SDD.md` |
| Encontrar la tarea asociada | `WorkItems.md` |
| Ver rutas y estructura del repositorio | `INDEX.md` |
| Seguir el proceso de trabajo | `WORKFLOW_OPERACIONAL.md` |

---

## Fases de trabajo

1. **Analizar**
   - Verifique la especificación del problema.
   - Identifique el alcance y la prioridad.
   - Revise la documentación y el código existente.

2. **Diseñar**
   - Defina la solución técnica.
   - Determine los módulos y archivos afectados.
   - Asegure que el diseño sea consistente con la arquitectura actual.

3. **Implementar**
   - Cree o modifique código en las ubicaciones correctas.
   - Mantenga los cambios pequeños y reversibles.

4. **Validar**
   - Ejecute pruebas relevantes.
   - Verifique el comportamiento en el entorno real.
   - Compruebe logs y resultados.

5. **Revisar**
   - Actualice `SRS.md`, `SDD.md` y `WorkItems.md` según corresponda.
   - Documente las decisiones y lecciones aprendidas.
   - Prepare un commit claro y atómico.

---

## Ubicación de archivos

Antes de crear un archivo nuevo, determine su ubicación con el sistema de organización del proyecto:

- `computadora/` — código fuente principal
- `tests/` — pruebas
- `docs/` — documentación técnica
- `scripts/` — utilidades de soporte
- `datos/` — datos persistentes y configuraciones
- `.logs/` — registros de ejecución

Si no está seguro, consulte `scripts/FILE_LOCATION_MANAGER.py` o revise la estructura de la carpeta.

---

## Reglas básicas

- No agregue nuevos archivos en la raíz del repositorio salvo los permitidos.
- Mantenga la raíz limpia: solo documentación principal y launcher.
- Evite dependencias nuevas sin justificar.
- Prefiera claridad y simplicidad.
- Documente cada cambio en un solo punto de verdad.

---

## Validación mínima

Para cada cambio significativo:

- `git diff` debe ser revisable y razonable.
- Las pruebas deben pasar.
- `SRS.md`, `SDD.md` y `WorkItems.md` deben actualizarse si aplica.
- El comportamiento debe verificarse en el entorno de ejecución.

---

## Flujo de trabajo recomendado

1. Identifique la tarea en `WorkItems.md`.
2. Revise el requisito en `SRS.md`.
3. Revise el diseño en `SDD.md`.
4. Haga el cambio en código.
5. Ejecute pruebas.
6. Documente el resultado.
7. Cierre la tarea en `WorkItems.md`.

---

## Archivos permitidos en la raíz

- `README.md`
- `WORKFLOW_OPERACIONAL.md`
- `SRS.md`
- `SDD.md`
- `WorkItems.md`
- `iniciar_computadora.bat`
- `INDEX.md`

Todo lo demás debe ubicarse en su carpeta correspondiente.
