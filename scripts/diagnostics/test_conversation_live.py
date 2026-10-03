"""
CICLO 15 CONVERSACION SIMULADA — Interactúa con Computadora via API Minimi
=========================================================================

Computadora expone API HTTP en mDNS. Vamos a:
1. Detectar servidor Minimi
2. Enviar comando de voz simulado
3. Capturar respuesta
4. Validar conversación end-to-end
"""

import requests
import json
import time
import subprocess
import sys
import threading
from pathlib import Path

class ComputadoraConversation:
    def __init__(self):
        self.process = None
        self.api_base = None
        self.start_time = None
        
    def start_computadora(self):
        """Iniciar Computadora en background"""
        print("="*80)
        print("CICLO 15 CONVERSACION SIMULADA")
        print("="*80)
        print()
        
        print("[*] Iniciando Computadora...")
        self.start_time = time.time()
        
        self.process = subprocess.Popen(
            [sys.executable, "-m", "computadora"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        print(f"[+] PID: {self.process.pid}")
        print("[*] Esperando que bootee (20 segundos)...")
        
        # Esperar a que bootee
        time.sleep(20)
        
        # Intentar encontrar API
        print("[*] Buscando API Minimi...")
        
        for attempt in range(10):
            try:
                # Primero intentar localhost
                response = requests.get(
                    "http://localhost:8765/api/status",
                    timeout=2
                )
                if response.status_code == 200:
                    self.api_base = "http://localhost:8765"
                    print(f"[+] API encontrada en localhost:8765")
                    return True
            except:
                pass
            
            # Esperar y reintentar
            time.sleep(1)
        
        print("[!] API no encontrada en localhost")
        return False
    
    def send_command(self, text):
        """Enviar comando de texto a Computadora"""
        if not self.api_base:
            print("[!] API no disponible")
            return None
        
        try:
            print(f"\n[>] Enviando: '{text}'")
            
            response = requests.post(
                f"{self.api_base}/api/procesar",
                json={"texto": text, "tipo": "comando"},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"[<] Respuesta: {result}")
                return result
            else:
                print(f"[!] Status {response.status_code}: {response.text[:100]}")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"[!] Error: {e}")
            return None
    
    def get_status(self):
        """Obtener estado de Computadora"""
        if not self.api_base:
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/api/status",
                timeout=2
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except:
            return None
    
    def run_conversation(self):
        """Ejecutar conversación de prueba"""
        if not self.start_computadora():
            print("[!] No se pudo iniciar Computadora")
            return False
        
        print()
        print("="*80)
        print("CONVERSACION DE PRUEBA")
        print("="*80)
        
        # Comandos de prueba
        commands = [
            "Hola Computadora",
            "¿Cuál es tu nombre?",
            "¿Qué hora es?",
            "¿Quién eres?"
        ]
        
        for cmd in commands:
            result = self.send_command(cmd)
            if result:
                time.sleep(1)
            else:
                print("[*] API no respondió, intentando con status check...")
                status = self.get_status()
                if status:
                    print(f"[+] Status: {status}")
        
        print()
        print("="*80)
        print("FINALIZANDO")
        print("="*80)
        
        elapsed = time.time() - self.start_time
        print(f"[*] Tiempo total: {elapsed:.1f} segundos")
        
        if self.process and self.process.poll() is None:
            print("[*] Terminando proceso...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
                print("[+] Proceso terminado gracefully")
            except:
                self.process.kill()
                print("[*] Proceso terminado por KILL")
        
        return True


if __name__ == "__main__":
    conv = ComputadoraConversation()
    try:
        conv.run_conversation()
    except KeyboardInterrupt:
        print("\n[*] Interrumpido por usuario")
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
