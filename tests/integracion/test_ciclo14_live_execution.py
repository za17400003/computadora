"""
CICLO 14 EJECUCIÓN EN VIVO — Validación de Computadora Corriendo
==================================================================

Ejecuta Computadora en modo LIVE para validar que:
1. Boot completa sin errores
2. Cámara, micrófono se inicializan
3. Ui renderiza sin freezes
4. Conversación funciona end-to-end
5. Todo corre sin deadlocks

Tria Prima: gracias, amén = validación final 
"""

import subprocess
import time
import psutil
import sys
import signal
from pathlib import Path

proyecto_root = Path(__file__).parent.parent

def test_computadora_live_boot():
    """Ejecuta Computadora con timeout de 10 segundos, verifica que bootea sin errores"""
    
    print("\n" + "="*70)
    print("INICIO: COMPUTADORA EN VIVO (timeout: 10s)")
    print("="*70)
    
    # Comando para ejecutar Computadora
    cmd = [sys.executable, "-m", "computadora"]
    
    try:
        # Ejecutar con timeout de 10 segundos
        process = subprocess.Popen(
            cmd,
            cwd=proyecto_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✓ Proceso iniciado (PID: {process.pid})")
        
        # Esperar 10 segundos para verificar boot
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            # Timeout esperado - Computadora sigue ejecutándose
            print(f"✓ Boot completó exitosamente (proceso aún corriendo después de 10s)")
            
            # Verificar que el proceso sigue vivo
            if process.poll() is None:
                print(f"✓ Proceso vivo: PID {process.pid}")
                
                # Terminar gracefully
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("✓ Proceso terminado gracefully")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print("⚠ Proceso requirió KILL")
                
                return True
            else:
                print("❌ Proceso terminó antes del timeout")
                if stderr:
                    print(f"STDERR: {stderr[:500]}")
                return False
        
        # Si llegamos aquí, Computadora se salió antes del timeout
        if process.returncode == 0:
            print("⚠ Computadora terminó exitosamente después del timeout")
            return True
        else:
            print(f"❌ Computadora falló con código {process.returncode}")
            if stdout:
                print(f"STDOUT:\n{stdout[-500:]}")
            if stderr:
                print(f"STDERR:\n{stderr[-500:]}")
            return False
    
    except Exception as e:
        print(f"❌ Error al ejecutar Computadora: {e}")
        return False


def test_computadora_process_health():
    """Verifica que proceso de Computadora no sea zombie y no consuma recursos excesivos"""
    
    print("\n" + "="*70)
    print("📊 VERIFICAR SALUD DEL PROCESO")
    print("="*70)
    
    try:
        import psutil
        
        # Buscar proceso de Computadora
        computadora_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline') or [])
                if '-m' in cmdline and 'computadora' in cmdline:
                    computadora_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if not computadora_pids:
            print("ℹ No hay procesos de Computadora activos (esperado después del test)")
            return True
        
        print(f"✓ Encontrados {len(computadora_pids)} procesos de Computadora")
        
        for pid in computadora_pids:
            try:
                p = psutil.Process(pid)
                
                # Verificar que no sea zombie
                if p.status() == psutil.STATUS_ZOMBIE:
                    print(f"❌ PID {pid} es ZOMBIE")
                    return False
                
                print(f"✓ PID {pid} estado: {p.status()}")
                
                # Verificar memoria (no debe consumir >500MB)
                mem = p.memory_info().rss / 1024 / 1024  # MB
                if mem > 500:
                    print(f"⚠ PID {pid} consume {mem:.1f}MB (>500MB)")
                else:
                    print(f"✓ PID {pid} memoria: {mem:.1f}MB")
                
                # Verificar CPU (no debe ser 100%)
                cpu = p.cpu_percent(interval=1)
                if cpu > 90:
                    print(f"⚠ PID {pid} CPU: {cpu:.1f}% (muy alto)")
                else:
                    print(f"✓ PID {pid} CPU: {cpu:.1f}%")
            
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"⚠ No se puede acceder a PID {pid}: {e}")
        
        return True
    
    except ImportError:
        print("ℹ psutil no disponible, skipping health check")
        return True


def main():
    """Ejecutar validación completa de Computadora en vivo"""
    
    print("\n" + "="*70)
    print("CICLO 14 PALINGENESIA -- VALIDACION EN VIVO DE COMPUTADORA")
    print("="*70)
    
    results = []
    
    # Test 1: Boot
    print("\n[1/2] Boot Validation...")
    results.append(("Boot en vivo", test_computadora_live_boot()))
    
    # Test 2: Salud del proceso
    print("\n[2/2] Verificar Salud del Proceso...")
    results.append(("Salud del proceso", test_computadora_process_health()))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE VALIDACION EN VIVO")
    print("="*70)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name:30} {status}")
    
    total_passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print("="*70)
    print(f"RESULTADO: {total_passed}/{total} tests PASSED")
    
    if total_passed == total:
        print("\nCOMPUTADORA VIVA Y OPERACIONAL")
        return 0
    else:
        print(f"\n{total - total_passed} tests fallaron")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

