@echo off
cd /d "%~dp0"
python -c "from computadora.interfaz.ventana_principal import OrbeComputadora; print('✓ Importacion exitosa')"
pause
