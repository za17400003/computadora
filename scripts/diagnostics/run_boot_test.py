"""
Boot real de Computadora - Test final
"""

import subprocess
import sys
import time

print('='*70)
print('CICLO 14 - BOOT REAL DE COMPUTADORA')
print('='*70)

cmd = [sys.executable, '-m', 'computadora']
print(f'Comando: {" ".join(cmd)}')

try:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f'PID: {process.pid}')
    print('Esperando 10 segundos...')
    
    try:
        stdout, stderr = process.communicate(timeout=10)
        print('Proceso termino antes del timeout')
        print(f'Return code: {process.returncode}')
        if stdout:
            print(f'STDOUT:\n{stdout[:300]}')
        if stderr:
            print(f'STDERR:\n{stderr[:300]}')
    except subprocess.TimeoutExpired:
        print('*** TIMEOUT - COMPUTADORA SIGUE EJECUTANDOSE ***')
        process.terminate()
        try:
            process.wait(timeout=3)
            print('Proceso terminado')
        except:
            process.kill()
            print('Proceso terminado por KILL')
        print('\n=== RESULTADO: EXITO ===')
        print('Computadora booteo y ejecuto sin crash')
        
except Exception as e:
    print(f'Error: {e}')
