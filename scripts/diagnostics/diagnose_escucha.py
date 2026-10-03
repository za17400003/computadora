#!/usr/bin/env python3
"""
Diagnóstico NIGREDO de Escucha: Verifica que HiloEscucha pueda capturar y procesar audio.
(Versión mini — sin GUI)
"""

import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from computadora.voz.escucha import HiloEscucha
from computadora.config import Configuracion
from loguru import logger

# Configurar logging
logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss.SSS} | {level: <8} | {message}")

def test_hiloescucha():
    """Test de HiloEscucha sin GUI."""
    print("[TEST HILOESCUCHA - DIAGNOSTICO NIGREDO]")
    print()
    
    # 1. Cargar configuración
    print("[1] Cargando Configuracion...")
    try:
        cfg = Configuracion()
        dispositivo = cfg.obtener("escucha.dispositivo", 1)
        print(f"    OK Dispositivo: {dispositivo}")
    except Exception as e:
        print(f"    ERROR: {e}")
        return False
    
    print()
    
    # 2. Crear instancia de HiloEscucha
    print("[2] Instanciando HiloEscucha...")
    try:
        hilo = HiloEscucha(cfg)
        print("    OK Instancia creada")
    except Exception as e:
        print(f"    ERROR: {e}")
        return False
    
    print()
    
    # 3. Conectar signals (mock)
    print("[3] Configurando signals (mock)...")
    
    estado_recibido = []
    
    def on_estado_cambio(estado):
        logger.info(f"[SIGNAL] Estado escucha cambio a: {estado}")
        estado_recibido.append(estado)
    
    try:
        hilo.estado_cambio.connect(on_estado_cambio)
        print("    OK Signal conectado: estado_cambio")
    except Exception as e:
        print(f"    WARNING (esperado sin Qt): {e}")
    
    print()
    
    # 4. Iniciar hilo y escuchar 5 segundos
    print("[4] Iniciando HiloEscucha por 5 segundos...")
    print("    (Di 'Computadora' o 'Hola' cerca del microfono)...")
    
    try:
        hilo.start()
        print("    OK HiloEscucha iniciado")
    except Exception as e:
        print(f"    ERROR al iniciar: {e}")
        return False
    
    # Esperar 5 segundos
    time.sleep(5)
    
    print()
    
    # 5. Detener hilo
    print("[5] Deteniendo HiloEscucha...")
    try:
        hilo.detener()
        print("    OK Hilo detenido (via detener())")
    except Exception as e:
        print(f"    WARNING al detener: {e}")
    
    # QThread no tiene join(), pero esperar un poco
    time.sleep(1)
    
    print()
    print("========================================")
    print("RESULTADO:")
    print(f"  Estado recibido: {estado_recibido}")
    print(f"  Escucha funcionando: {'OK Si' if estado_recibido else 'WARNING Revisar (senal no emitida)'}")
    print("========================================")
    
    return True

if __name__ == "__main__":
    try:
        test_hiloescucha()
    except KeyboardInterrupt:
        print("\n[Detenido por usuario]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
