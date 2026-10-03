#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST EN VIVO: Ejecuta HiloEscucha en background y monitorea
- Inicia HiloEscucha.run()
- Espera a que cargue Whisper
- Intenta capturar audio y transcribir
- Verifica que los signals se emitan
"""

import sys
import time
import logging
from pathlib import Path
from PyQt6.QtCore import QCoreApplication

# Setup logging con colores
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_hilo_escucha_run():
    """Ejecuta HiloEscucha en vivo y monitorea emision de signals"""
    logger.info("=" * 70)
    logger.info("🎧 TEST EN VIVO: Ejecutar HiloEscucha.run()")
    logger.info("=" * 70)
    
    try:
        # Crear QApp para que QThread funcione
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication(sys.argv)
        
        from computadora.config import Configuracion
        from computadora.voz.escucha import HiloEscucha
        import threading
        
        config = Configuracion()
        hilo = HiloEscucha(config)
        
        # Conectar signals para monitoreo
        signals_recibidos = []
        
        def on_texto_detectado(texto):
            msg = f"✅ TEXTO DETECTADO: '{texto}'"
            logger.info(msg)
            signals_recibidos.append(("texto", texto))
        
        def on_estado_cambio(estado):
            msg = f"📊 ESTADO: {estado}"
            logger.info(msg)
            signals_recibidos.append(("estado", estado))
        
        def on_voz_activa():
            msg = f"🎤 VOZ ACTIVA DETECTADA"
            logger.info(msg)
            signals_recibidos.append(("voz_activa", None))
        
        def on_mensaje_sistema(msg):
            logger.info(f"ℹ️  SISTEMA: {msg}")
            signals_recibidos.append(("mensaje", msg))
        
        hilo.texto_detectado.connect(on_texto_detectado)
        hilo.estado_cambio.connect(on_estado_cambio)
        hilo.voz_activa.connect(on_voz_activa)
        hilo.mensaje_sistema.connect(on_mensaje_sistema)
        
        logger.info("✅ Signals conectados. Iniciando HiloEscucha...")
        hilo.start()
        
        logger.info("\n" + "=" * 70)
        logger.info("⏳ Esperando a que Whisper cargue (máx 30s)...")
        logger.info("=" * 70)
        logger.info("🎤 Hablando ahora... Di: 'computadora, ¿qué hora es?'")
        logger.info("=" * 70 + "\n")
        
        # Esperar hasta 30 segundos para detectar algo
        start_time = time.time()
        timeout = 30
        
        while (time.time() - start_time) < timeout:
            app.processEvents()  # Procesar Qt events
            
            # Verificar si recibimos algo
            if signals_recibidos:
                logger.info(f"\n✅ SE RECIBIERON {len(signals_recibidos)} SIGNAL(ES)")
                for sig_type, sig_data in signals_recibidos:
                    logger.info(f"   - {sig_type}: {sig_data}")
                break
            
            time.sleep(0.1)
        
        # Detener hilo
        elapsed = time.time() - start_time
        logger.info(f"\n⏹️  Deteniendo HiloEscucha (transcurrieron {elapsed:.1f}s)...")
        hilo._activo = False
        hilo.wait(5000)  # Esperar máx 5s
        
        if len(signals_recibidos) == 0:
            logger.warning("\n⚠️  NO SE RECIBIERON SIGNALS en 30 segundos")
            logger.warning("   Posibles causas:")
            logger.warning("   1. No hablaste o volumen muy bajo")
            logger.warning("   2. Whisper aún cargando (toma >15s en CPU)")
            logger.warning("   3. El hilo no inició correctamente")
            logger.warning("   4. Error silencioso en _bucle_escucha()")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.exception("Stack trace:")
        return False

def main():
    try:
        success = test_hilo_escucha_run()
        if success:
            logger.info("\n🎉 TEST PASSED — HiloEscucha está funcionando")
        else:
            logger.error("\n❌ TEST FAILED — Revisa los logs arriba")
        return success
    except KeyboardInterrupt:
        logger.info("\n⏹️  Interrumpido por usuario")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
