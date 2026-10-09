@echo off
cd /d "c:\Users\woire\Documents\proyecto-computadora"
python -m pytest tests\test_balance_proactividad.py -xvs --tb=short
pause
