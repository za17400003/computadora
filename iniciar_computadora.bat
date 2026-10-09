@echo off
REM ════════════════════════════════════════════════════════════════════
REM  COMPUTADORA — Launcher Directo (Siempre como Administrador)
REM  Ejecuta directamente: python -m computadora
REM ════════════════════════════════════════════════════════════════════

setlocal
cd /d "%~dp0"

REM ── Verificar si estamos como administrador ──
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    goto :noadmin
)

:noadmin
REM ── No somos admin, relanzar como administrador ──
echo.
echo ════════════════════════════════════════════════════════════
echo  COMPUTADORA requiere permisos de administrador
echo ════════════════════════════════════════════════════════════
echo.
echo Solicitando elevación de privilegios...
echo.

powershell -Command "Start-Process '%~f0' -Verb RunAs"
exit /b 0

:admin
REM ── Somos admin, ejecutar COMPUTADORA ──
echo.
echo ════════════════════════════════════════════════════════════
echo              🖥️ COMPUTADORA INICIANDO
echo ════════════════════════════════════════════════════════════
echo.

REM FIX: antes esto solo avisaba y se detenía si faltaba el entorno
REM virtual — en una instalación recién descargada SIEMPRE falta, así que
REM el primer arranque jamás funcionaba sin que el usuario supiera
REM ejecutar manualmente "python -m venv .venv" por su cuenta. Ahora lo
REM crea e instala las dependencias automáticamente la primera vez.
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ════════════════════════════════════════════════════════════
    echo  Primera vez — creando entorno virtual e instalando Computadora
    echo  (esto puede tardar varios minutos, solo ocurre una vez)
    echo ════════════════════════════════════════════════════════════
    echo.

    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se encontro "python" en el PATH del sistema.
        echo Instala Python 3.10+ desde https://www.python.org/downloads/ y vuelve a intentar.
        pause
        exit /b 1
    )

    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual .venv
        pause
        exit /b 1
    )

    echo Instalando dependencias (requirements.txt)...
    .venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    if exist "requirements.txt" (
        .venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
        if errorlevel 1 (
            echo [AVISO] Algunas dependencias de requirements.txt fallaron al instalar.
            echo Computadora intentara instalar lo que falte automaticamente al arrancar.
        )
    ) else (
        echo [AVISO] No se encontro requirements.txt — Computadora instalara lo necesario al arrancar.
    )
    echo.
    echo Entorno virtual listo.
    echo.
)

if not exist "_config\.env" (
    echo [ERROR] _config\.env no existe
    pause
    exit /b 1
)

REM Ejecutar COMPUTADORA directamente
echo Iniciando COMPUTADORA...
.venv\Scripts\python.exe -m computadora

REM Si llega aquí, COMPUTADORA terminó
echo.
echo COMPUTADORA ha terminado.
pause