"""
CICLO 15 LIVE MONITORING — Real-time Computadora Boot + Conversation
=====================================================================

Ejecuta Computadora por ~60 segundos, captura logs en tiempo real,
valida transiciones de estado (boot → escuchando → procesando → respondiendo).
"""

import subprocess
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

class LiveComputadoraMonitor:
    def __init__(self, timeout=70):
        self.timeout = timeout
        self.process = None
        self.start_time = None
        self.boot_complete_time = None
        self.states_observed = []
        self.errors_observed = []
        self.running = True
        
    def log_event(self, level, msg, elapsed_sec=None):
        """Log event with timestamp"""
        if elapsed_sec is None:
            elapsed_sec = time.time() - self.start_time
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        marker = {
            "INFO": "[*]",
            "STATE": "[-]",
            "SUCCESS": "[+]",
            "ERROR": "[!]",
            "DEBUG": "[~]"
        }.get(level, "[?]")
        
        print(f"{marker} {timestamp} (+{elapsed_sec:.1f}s) {msg}")
    
    def monitor_output(self):
        """Read stdout/stderr in real-time"""
        try:
            while self.running and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    elapsed = time.time() - self.start_time
                    
                    # Detect state transitions
                    if "escuchando" in line.lower():
                        self.states_observed.append(("escuchando", elapsed))
                        self.log_event("STATE", f"Estado: ESCUCHANDO | {line[:60]}", elapsed)
                    elif "procesando" in line.lower():
                        self.states_observed.append(("procesando", elapsed))
                        self.log_event("STATE", f"Estado: PROCESANDO | {line[:60]}", elapsed)
                    elif "respondiendo" in line.lower():
                        self.states_observed.append(("respondiendo", elapsed))
                        self.log_event("STATE", f"Estado: RESPONDIENDO | {line[:60]}", elapsed)
                    elif "reposo" in line.lower():
                        self.states_observed.append(("reposo", elapsed))
                        self.log_event("STATE", f"Estado: REPOSO | {line[:60]}", elapsed)
                    elif "error" in line.lower() or "excepcion" in line.lower() or "traceback" in line.lower():
                        self.errors_observed.append((line, elapsed))
                        self.log_event("ERROR", f"{line[:70]}", elapsed)
                    elif "iniciado" in line.lower() or "listo" in line.lower() or "ready" in line.lower():
                        self.log_event("SUCCESS", f"Boot milestone: {line[:60]}", elapsed)
                        if not self.boot_complete_time and elapsed > 5:
                            self.boot_complete_time = elapsed
                    else:
                        self.log_event("INFO", f"{line[:70]}", elapsed)
                
                except Exception as e:
                    self.log_event("ERROR", f"Error leyendo output: {e}")
        
        except Exception as e:
            self.log_event("ERROR", f"Monitor thread error: {e}")
    
    def run(self):
        """Execute Computadora and monitor"""
        
        print("="*80)
        print("CICLO 15 - MONITOREO EN VIVO DE COMPUTADORA")
        print("Duracion: ~60 segundos")
        print("="*80)
        print()
        
        self.start_time = time.time()
        cmd = [sys.executable, "-m", "computadora"]
        self.log_event("INFO", f"Comando: {' '.join(cmd)}")
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.log_event("SUCCESS", f"Proceso iniciado (PID: {self.process.pid})")
            
            # Monitor output in separate thread
            monitor_thread = threading.Thread(target=self.monitor_output, daemon=True)
            monitor_thread.start()
            
            # Wait for timeout or process exit
            try:
                self.process.wait(timeout=self.timeout)
                elapsed = time.time() - self.start_time
                self.log_event("ERROR", f"Computadora termino antes de timeout (elapsed: {elapsed:.1f}s)", elapsed)
                return_code = self.process.returncode
                if return_code != 0:
                    self.log_event("ERROR", f"Return code: {return_code}", elapsed)
                    return False
            
            except subprocess.TimeoutExpired:
                elapsed = time.time() - self.start_time
                self.log_event("SUCCESS", f"TIMEOUT ALCANZADO - Computadora sigue ejecutandose (elapsed: {elapsed:.1f}s)", elapsed)
                
                # Terminate gracefully
                self.running = False
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    self.log_event("SUCCESS", "Proceso terminado gracefully", elapsed)
                except:
                    self.process.kill()
                    self.log_event("INFO", "Proceso terminado por KILL")
                
                monitor_thread.join(timeout=2)
                return True
        
        except Exception as e:
            self.log_event("ERROR", f"Error en run(): {e}")
            return False
        
        finally:
            self.print_summary()
    
    def print_summary(self):
        """Print monitoring summary"""
        elapsed = time.time() - self.start_time
        
        print()
        print("="*80)
        print("RESUMEN DE MONITOREO")
        print("="*80)
        print(f"Duracion total: {elapsed:.1f} segundos")
        print()
        
        if self.boot_complete_time:
            print(f"Boot completado en: ~{self.boot_complete_time:.1f}s")
        else:
            print("Boot completion marker: NO DETECTADO")
        
        print()
        print("Estados observados:")
        if self.states_observed:
            for state, when in self.states_observed:
                print(f"  - {state:15} en +{when:.1f}s")
        else:
            print("  (ninguno detectado en logs)")
        
        print()
        if self.errors_observed:
            print(f"Errores detectados: {len(self.errors_observed)}")
            for err, when in self.errors_observed[:5]:  # Show first 5
                print(f"  - +{when:.1f}s: {err[:60]}")
            if len(self.errors_observed) > 5:
                print(f"  ... y {len(self.errors_observed) - 5} mas")
        else:
            print("Errores detectados: 0")
        
        print()
        print("="*80)
        if not self.errors_observed and self.states_observed:
            print("RESULTADO: Computadora ejecuto exitosamente sin errores")
            return True
        elif self.errors_observed:
            print(f"RESULTADO: Ejecucion con {len(self.errors_observed)} error(es)")
            return False
        else:
            print("RESULTADO: Ejecucion sin eventos detectables (posible error en logging)")
            return True


if __name__ == "__main__":
    monitor = LiveComputadoraMonitor(timeout=65)
    success = monitor.run()
    sys.exit(0 if success else 1)
