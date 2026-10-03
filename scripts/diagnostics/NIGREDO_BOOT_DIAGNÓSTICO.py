#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NIGREDO FINAL: Simular boot completo del sistema
Detectar exactamente dónde se queda atascado
"""

import sys
import time
import logging
import traceback
from pathlib import Path

# Configurar logging MÁXIMO para ver TODO
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('boot_diagnóstico.log', encoding='utf-8', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 80)
    logger.info("🔍 BOOT COMPLETO SIMULADO — DIAGNÓSTICO FINAL")
    logger.info("=" * 80)
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        logger.info("✅ Imports Qt funciona")
        
        # Crear app sin GUI (headless)
        app = QCoreApplication([])
        logger.info("✅ QCoreApplication creada")
        
        from computadora.config import Configuracion
        logger.info("✅ Import Configuracion funciona")
        config = Configuracion()
        logger.info("✅ Configuracion inicializada")
        
        from computadora.voz.escucha import HiloEscucha
        logger.info("✅ Import HiloEscucha funciona")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎧 CREANDO Y INICIANDO HiloEscucha...")
        logger.info("=" * 80 + "\n")
        
        hilo = HiloEscucha(config)
        logger.info("✅ HiloEscucha objeto creado")
        
        # Conectar signals
        def on_texto(texto):
            logger.info(f"✅✅✅ TEXTO DETECTADO: '{texto}'")
        
        def on_estado(estado):
            logger.info(f"✅ ESTADO CAMBIÓ: {estado}")
        
        def on_voz():
            logger.info(f"✅ VOZ ACTIVA")
        
        def on_msg(msg):
            logger.info(f"ℹ️  SISTEMA: {msg}")
        
        hilo.texto_detectado.connect(on_texto)
        hilo.estado_cambio.connect(on_estado)
        hilo.voz_activa.connect(on_voz)
        hilo.mensaje_sistema.connect(on_msg)
        logger.info("✅ Signals conectados")
        
        # Iniciar hilo
        logger.info("\n" + "=" * 80)
        logger.info("🚀 INICIANDO HiloEscucha.start()...")
        logger.info("=" * 80 + "\n")
        
        hilo.start()
        logger.info("✅ HiloEscucha.start() llamado (thread iniciado)")
        
        # Esperar a que cargue
        logger.info("\n⏳ ESPERANDO A QUE WHISPER CARGUE (máx 60 segundos)...")
        logger.info("🎤 Hablando ahora: 'computadora hola'\n")
        
        start = time.time()
        found_something = False
        
        while (time.time() - start) < 60 and hilo._activo:
            app.processEvents()  # Procesar Qt events
            time.sleep(0.1)
            
            if (time.time() - start) % 10 < 0.2:  # Log cada 10 segundos
                elapsed = time.time() - start
                logger.debug(f"⏳ {elapsed:.1f}s — esperando...")
            
            # Verificar estado de Whisper
            if hilo._modelo is not None:
                logger.info(f"✅ Whisper modelo cargado: {hilo._modelo}")
                found_something = True
                break
        
        elapsed = time.time() - start
        logger.info(f"\n⏹️  {elapsed:.1f}s transcurridos\n")
        
        if hilo._modelo is None:
            logger.warning("⚠️  Whisper aún NO cargado después de 60s")
            logger.warning("   Posibles causas:")
            logger.warning("   1. Primera ejecución - descargando modelo 1.4GB")
            logger.warning("   2. Disco lento")
            logger.warning("   3. Error silencioso en _cargar_modelo()")
        else:
            logger.info("✅ WHISPER CARGADO CORRECTAMENTE")
            logger.info(f"   - Modelo: {hilo._modelo}")
        
        # Esperar un poco más por signals
        logger.info("\n⏳ ESPERANDO SIGNALS (máx 30 segundos más)...")
        logger.info("Hablando: 'computadora ¿qué hora es?'\n")
        
        start2 = time.time()
        while (time.time() - start2) < 30 and hilo._activo:
            app.processEvents()
            time.sleep(0.1)
        
        # Detener
        logger.info("\n" + "=" * 80)
        logger.info("⏹️  DETENIENDO HILO...")
        logger.info("=" * 80)
        hilo._activo = False
        hilo.wait(5000)
        logger.info("✅ Hilo detenido")
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 RESUMEN DIAGNÓSTICO")
        logger.info("=" * 80)
        logger.info(f"Whisper modelo cargado: {'SÍ ✅' if hilo._modelo else 'NO ❌'}")
        logger.info(f"Estado hilo: {hilo.isRunning()}")
        logger.info(f"Logs guardados en: boot_diagnóstico.log")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Interrumpido por usuario")
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        logger.exception("Stack trace completo:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
