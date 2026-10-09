# Computadora

Asistente personal de escritorio para Windows 11, con interfaz PyQt6 y capacidades de voz. El proyecto integra reconocimiento de voz local, proveedores de lenguaje configurables y herramientas de escritorio con configuracion local.

## Funcionalidades

- Interfaz de escritorio desarrollada con PyQt6.
- Captura y transcripcion de voz con Whisper y deteccion de actividad de voz.
- Salida de voz mediante proveedores TTS configurables.
- Integracion con Ollama local y proveedores externos opcionales.
- Modulos independientes para automatizacion, memoria local y canales de comunicacion.

## Tecnologias

Python 3.10+, PyQt6, Whisper, Silero VAD, Ollama, edge-tts, pyttsx3 y herramientas de automatizacion para Windows.

## Requisitos

- Windows 11
- Python 3.10 o posterior
- Micrófono para las funciones de voz
- Ollama si se habilita el proveedor local de lenguaje
- CMake y herramientas de compilacion pueden ser necesarios para instalar dlib

## Instalacion

Desde PowerShell, en la raiz del repositorio:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item _config/.env.example _config/.env
```

Completa `_config/.env` con la configuracion que vayas a utilizar. No agregues credenciales al repositorio.

## Ejecucion

```powershell
python -m computadora
```

El launcher `iniciar_computadora.bat` tambien esta disponible en Windows y solicita elevacion de permisos. Para desarrollo, se recomienda iniciar desde la terminal con los permisos minimos necesarios.

## Pruebas

```powershell
python -m pytest -q
```

## Privacidad y estado

El proyecto es un prototipo para Windows. El almacenamiento local permanece en el dispositivo; si se habilitan integraciones externas, el texto o audio enviado a esos proveedores queda sujeto a sus politicas. Revisa la configuracion antes de usar datos personales.
