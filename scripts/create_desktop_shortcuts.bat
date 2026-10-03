@echo off
REM ============================================================
REM CREATE DESKTOP SHORTCUTS
REM Run this script once to create shortcuts on your desktop
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Creating Desktop Shortcuts
echo ============================================================
echo.

REM Get paths
set "PROJECT_ROOT=%~dp0.."
set "DESKTOP=%USERPROFILE%\Desktop"

REM Normalize paths
cd /d "!PROJECT_ROOT!"
set "PROJECT_ROOT=!CD!"

echo Project Root: !PROJECT_ROOT!
echo Desktop: !DESKTOP!
echo.

REM Create shortcut scripts
echo Creating shortcut 1/2: Computadora (Current)...
(
    echo @echo off
    echo cd /d "!PROJECT_ROOT!"
    echo call .venv\Scripts\activate.bat
    echo python -m computadora
) > "!DESKTOP!\Computadora (Current).bat"

echo Created: !DESKTOP!\Computadora (Current).bat
echo.

echo Creating shortcut 2/2: Golem Legacy (Documentation)...
(
    echo @echo off
    echo cd /d "!PROJECT_ROOT!"
    echo call "_legacy_reference\ver_documentacion_legacy.bat"
) > "!DESKTOP!\Golem Legacy (Documentation).bat"

echo Created: !DESKTOP!\Golem Legacy (Documentation).bat
echo.

echo ============================================================
echo ✅ SHORTCUTS CREATED ON DESKTOP
echo ============================================================
echo.
echo You can now use:
echo   1. "Computadora (Current).bat" ← Use this for daily work
echo   2. "Golem Legacy (Documentation).bat" ← Reference only
echo.
echo To create Visual Shortcuts (with icons):
echo   1. Right-click on desktop
echo   2. New → Shortcut
echo   3. Location: !DESKTOP!\Computadora (Current).bat
echo   4. Name: Computadora (Current)
echo   5. Click Finish
echo.
echo Repeat for: Golem Legacy (Documentation)
echo.
pause
