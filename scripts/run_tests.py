#!/usr/bin/env python
"""
Script para ejecutar los tests y mostrar outputs.
"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_balance_proactividad.py", 
     "-xvs", "--tb=short"],
    cwd=".",
    capture_output=False
)
sys.exit(result.returncode)
