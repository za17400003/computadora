@echo off
REM ══════════════════════════════════════════════════════════════════
REM COMPUTADORA STARTUP — Ultra-simplificado (sin loops)
REM ══════════════════════════════════════════════════════════════════

chcp 65001 >nul
cd /d "%~dp0"
setlocal enabledelayedexpansion

REM FASE 1: VERIFICACIÓN DE ADMIN (una sola vez, sin relanzamiento automático)
net session >nul 2>&1
if errorlevel 1 (
    cls
    echo.
    echo ════════════════════════════════════════════════════════════
    echo  ERROR: Permisos de administrador requeridos
    echo ════════════════════════════════════════════════════════════
    echo.
    echo Por favor, ejecuta este archivo COMO ADMINISTRADOR:
    echo   1. Haz clic derecho en computadora_boot.bat
    echo   2. Selecciona "Ejecutar como administrador"
    echo   3. Haz clic en "Sí" en el diálogo de UAC
    echo.
    echo ════════════════════════════════════════════════════════════
    echo.
    pause
    exit /b 1
)

REM FASE 2: Configuración de variables
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8
if exist "%CD%\datos\firebase-credentials.json" (
    set GOOGLE_APPLICATION_CREDENTIALS=%CD%\datos\firebase-credentials.json
)
title Computadora - Verificando dependencias...

echo ══════════════════════════════════════════

echo ══════════════════════════════════════════
echo   Proyecto Computadora — Verificación de inicio
echo ══════════════════════════════════════════
echo.

:: ── 1. Verificar Python ──
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en PATH.
    echo         Descárgalo de https://www.python.org/downloads/
    exit /b 1
)
echo [OK] Python encontrado

:: ── 2. Verificar .venv ──
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Entorno virtual no encontrado. Creando .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        exit /b 1
    )
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual encontrado
)

:: ── 2b. Auto-actualizar pip ──
echo [INFO] Actualizando pip...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet >nul 2>&1
if errorlevel 1 (
    echo [WARN] No se pudo actualizar pip — continuando con versión actual
) else (
    echo [OK] pip actualizado
)

:: ── 3. Verificar e instalar dependencias de pip ──
echo [INFO] Verificando dependencias de Python...
.venv\Scripts\python.exe -c "import pkg_resources; pkg_resources.require(open('_config/requirements.txt').read().splitlines())" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias faltantes...
    .venv\Scripts\python.exe -m pip install -r _config/requirements.txt
    if errorlevel 1 (
        echo [ERROR] Falló la instalación de dependencias.
        exit /b 1
    )
    echo [OK] Dependencias instaladas
) else (
    echo [OK] Dependencias de Python completas
)

:: ── 3b. Dependencias opcionales (face-recognition) — RF-309: Auto-instalar ──
echo [INFO] Verificando dependencias opcionales...
.venv\Scripts\python.exe -c "import face_recognition" >nul 2>&1
if errorlevel 1 (
    echo [INFO] face-recognition no instalado. Instalando automaticamente...
    echo        Esto puede tardar varios minutos (compila dlib con C++^).
    set DLIB_USE_CUDA=0
    .venv\Scripts\pip install cmake dlib face-recognition >nul 2>&1
    if errorlevel 1 (
        echo [AVISO] No se pudo instalar face-recognition automaticamente.
        echo          Requiere Visual Studio Build Tools con C++ desktop workload.
        echo          Reconocimiento facial no disponible.
    ) else (
        echo [OK] face-recognition instalado correctamente
    )
) else (
    echo [OK] face-recognition disponible
)

:: ── 3c. Verificar Firebase Admin ──
.venv\Scripts\python.exe -c "import firebase_admin" >nul 2>&1
if errorlevel 1 (
    echo [INFO] firebase-admin no instalado. Instalando...
    .venv\Scripts\pip install firebase-admin >nul 2>&1
    if errorlevel 1 (
        echo [AVISO] No se pudo instalar firebase-admin. Firestore deshabilitado.
    ) else (
        echo [OK] firebase-admin instalado
    )
) else (
    echo [OK] firebase-admin disponible
)

:: ── 3d. Verificar credenciales Firebase ──
REM firebase-credentials.json es COMPLETAMENTE OPCIONAL (Firestore disabled es OK)
echo [INFO] Firebase: Opcional (usa Firestore solo si datos\firebase-credentials.json existe)

:: ── 4. Verificar Ollama (LLM local) ──
netstat -ano | findstr :1234 >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama no encontrado en puerto 1234 (OPCIONAL - Cerebro N2 fallback a N3)
    echo          Descárgalo de https://ollama.ai si deseas inteligencia local
) else (
    echo [OK] Ollama disponible en localhost:1234
)

:: ── 5. Verificar .env ──
if not exist "_config\.env" (
    echo [ERROR] Archivo _config\.env no encontrado (CRÍTICO - debe existir)
    echo          Copia _config\.env.example a _config\.env
    exit /b 1
) else (
    echo [OK] Archivo _config\.env presente
)

echo.
echo ══════════════════════════════════════════
echo   Iniciando Computadora...
echo ══════════════════════════════════════════
echo.
title Computadora - Logs

REM ── 6. Crear directorio de logs si no existe ──
if not exist ".logs" mkdir .logs

REM ── 7. Ejecutar Computadora con redirección de logs ──
set LOGFILE=.logs\computadora_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%.log
set ERRORFILE=.logs\computadora_ERROR_%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%.txt

echo [INFO] Ejecutando Computadora...
echo.

REM Capturar stdout y stderr por separado para mejor debugging
.venv\Scripts\python.exe scripts\wrapper_computadora.py >> "%LOGFILE%" 2>> "%ERRORFILE%"
set EXITCODE=%errorlevel%

REM Si hay errores, mostrar al usuario
if %EXITCODE% neq 0 (
    echo.
    echo [ERROR] COMPUTADORA terminó con error (código %EXITCODE%^)
    echo.
    if exist "%ERRORFILE%" (
        echo [DETALLES DEL ERROR]:
        type "%ERRORFILE%"
    )
)

REM ── 8. Mantener ventana abierta y mostrar logs ──
echo.
echo ══════════════════════════════════════════
echo   Computadora ha terminado
echo   Logs guardados en: %LOGFILE%
echo ══════════════════════════════════════════
echo.
echo [PULSA CUALQUIER TECLA PARA CERRAR]
pause >nul
