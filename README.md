# COMPUTADORA

Asistente personal de escritorio con IA para Windows 11.

Computadora escucha por micrófono, interpreta órdenes en español, ejecuta acciones en el sistema Windows y gestiona información personal de manera local.

## Requisitos

- Windows 11
- Python 3.10+
- GPU NVIDIA con CUDA (recomendado para modelos de voz y lenguaje)

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

## Inicio Rápido

- **Desde terminal**: `python -m computadora`
- **Desde la raíz del repositorio**: `iniciar computadora.bat`

## Estructura del Proyecto

- `computadora/` - Código fuente principal
- `tests/` - Pruebas unitarias y de integración
- `scripts/` - Scripts de utilidad y herramientas de soporte
- `docs/` - Documentación técnica y guías operativas
- `datos/` - Persistencia local, configuraciones y datos de runtime
- `.logs/` - Archivos de registro
- `golem/` - Código legacy y compatibilidad
- Archivos de documentación raíz: `README.md`, `WORKFLOW_OPERACIONAL.md`, `SRS.md`, `SDD.md`, `WorkItems.md`

## Ejecución

```bash
python -m computadora
```

## Stack

- **GUI**: PyQt6
- **STT**: OpenAI Whisper (local)
- **TTS**: edge-tts / pyttsx3
- **Cerebro**: Ollama local; GitHub Copilot API como escalado opcional

---

*Documento de proyecto actualizado para reflejar el estado actual y la arquitectura principal de Computadora.*
