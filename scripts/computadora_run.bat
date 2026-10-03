@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM  COMPUTADORA (antes Golem) — Launcher Simple y Rápido
REM  Ejecuta: python -m computadora (que es la interfaz visual de Golem)
REM ════════════════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ── Configuración ──
set PYTHONPATH=%CD%
set PYTHONIOENCODING=utf-8

REM ── Verificación rápida ──
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment no encontrado
    echo Ejecuta: python -m venv .venv
    pause
    exit /b 1
)

if not exist "_config\.env" (
    echo [ERROR] Archivo _config\.env no encontrado
    echo Copia: _config\.env.example a _config\.env
    pause
    exit /b 1
)

REM ── Crear directorio de logs ──
if not exist ".logs" mkdir .logs

REM ── Ejecutar COMPUTADORA (interfaz visual Golem) ──
echo Iniciando COMPUTADORA...
.venv\Scripts\python.exe -m computadora

REM ── Al terminar, mostrar un mensaje y cerrar ──
echo.
echo Computadora ha terminado.
pause
