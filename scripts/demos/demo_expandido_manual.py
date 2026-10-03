#!/usr/bin/env python3
"""
Demo manual para verificar las demos expandidas.
Arranca la interfaz y ejecuta Demo 0, Demo 1 y Demo 2.
"""
import sys
from pathlib import Path

from loguru import logger


def main() -> int:
    proyecto_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(proyecto_root))

    logger.info("═" * 80)
    logger.info("DEMOS EXPANDIDAS DE COMPUTADORA")
    logger.info("═" * 80)
    logger.info(f"Ruta del proyecto: {proyecto_root}")

    try:
        from computadora.config import Configuracion
        from computadora.interfaz.ventana_principal import OrbeComputadora
        from computadora.cerebro.nlu import CerebroComputadora
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        logger.info("✓ Importes exitosos")

        config = Configuracion()
        logger.info("✓ Configuración creada")

        modelo = config.obtener("ollama.modelo", "deepseek-r1:1.5b")
        cerebro = CerebroComputadora(modelo=modelo)
        logger.info(f"✓ Cerebro creado (modelo: {modelo})")

        app = QApplication(sys.argv)
        logger.info("✓ Aplicación Qt creada")

        orbe = OrbeComputadora(config, cerebro=cerebro)
        logger.info("✓ Orbe Computadora creada")
        orbe.show()
        logger.info("✓ Ventana visible")

        def start_demo_introduccion():
            logger.info("\n>>> Iniciando Demo 0 (EMET — LA VERDAD)")
            orbe._demo_introduccion()

        def start_demo_animaciones():
            logger.info("\n>>> Iniciando Demo 1 (MALJUT — MANIFESTACIÓN VISUAL)")
            orbe._demo_animaciones()

        def start_demo_herramientas():
            logger.info("\n>>> Iniciando Demo 2 (GEVURÁ — HERRAMIENTAS Y PODER)")
            orbe._demo_herramientas()

        timer_demo0 = QTimer()
        timer_demo0.setSingleShot(True)
        timer_demo0.timeout.connect(start_demo_introduccion)
        timer_demo0.start(2000)

        timer_demo1 = QTimer()
        timer_demo1.setSingleShot(True)
        timer_demo1.timeout.connect(start_demo_animaciones)
        timer_demo1.start(65000)

        timer_demo2 = QTimer()
        timer_demo2.setSingleShot(True)
        timer_demo2.timeout.connect(start_demo_herramientas)
        timer_demo2.start(130000)

        logger.info("Sistema listo. Las demostraciones se ejecutarán automáticamente.")
        return app.exec()
    except Exception as error:
        logger.error(f"✗ Error fatal: {error}", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())