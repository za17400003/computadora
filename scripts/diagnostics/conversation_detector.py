"""
Detecta puerto de Computadora y hace conversación simulada
"""

import subprocess
import sys
import time
import requests
import socket
from pathlib import Path

def find_open_port(host="localhost"):
    """Encuentra puerto donde Computadora está escuchando"""
    common_ports = [
        5000, 5001, 5002, 8000, 8001, 8080, 8081, 8765, 9000, 9001,
        3000, 4000, 6000, 7000, 10000
    ]
    
    print("[*] Escaneando puertos comunes...")
    
    for port in common_ports:
        try:
            response = requests.get(
                f"http://{host}:{port}/",
                timeout=0.5
            )
            print(f"[+] PUERTO DETECTADO: {port} - Status {response.status_code}")
            return port
        except:
            pass
    
    return None

def main():
    print("="*80)
    print("CICLO 15 - CONVERSACION LIVE")
    print("="*80)
    print()
    
    # Boot Computadora
    print("[*] Iniciando Computadora...")
    process = subprocess.Popen(
        [sys.executable, "-m", "computadora"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    print(f"[+] PID: {process.pid}")
    
    # Esperar boot
    print("[*] Boot inicial (25 segundos)...")
    time.sleep(25)
    
    # Detectar puerto
    port = find_open_port()
    
    if not port:
        print("[!] No se encontro puerto activo")
        print("[*] Verificando si Computadora esta activo...")
        
        if process.poll() is None:
            print("[+] Computadora aun en ejecucion")
            print("[*] Intentando esperar mas...")
            time.sleep(10)
            port = find_open_port()
        else:
            print("[!] Computadora termino")
            stdout, stderr = process.communicate()
            if stdout:
                print(f"Output:\n{stdout[-500:]}")
    
    if port:
        print(f"\n[+] Conectando a API en puerto {port}")
        print("[*] Enviando comandos...")
        
        api = f"http://localhost:{port}"
        
        commands = ["Hola", "Cuanto es 2+2", "¿Qué hora es?"]
        
        for cmd in commands:
            try:
                print(f"\n[>] {cmd}")
                response = requests.post(
                    f"{api}/procesar",
                    json={"texto": cmd},
                    timeout=3
                )
                print(f"[<] {response.text[:100]}")
            except Exception as e:
                print(f"[!] {e}")
            
            time.sleep(1)
    
    # Cleanup
    print("\n[*] Terminando Computadora...")
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
            print("[+] Terminado")
        except:
            process.kill()
    
    print("\n[+] LISTO - Computadora ejecuto correctamente")

if __name__ == "__main__":
    main()
