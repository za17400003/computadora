Objetivo de `tests/`

Este directorio está en proceso de reorganización para agrupar pruebas por dominios funcionales.

Estructura propuesta:
- core/
- nlu_dialogo/
- voz_audio/
- hardware_rendimiento/
- seguridad/
- integracion/
- instalacion/
- features/
- otros/

Se proporciona un script `scripts/migrate_tests_to_groups.py` que realiza un análisis y sugiere movimientos (modo dry-run por defecto).