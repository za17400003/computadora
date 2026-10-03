#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CITRINITAS: Script de Final-Pass para Paths Antiguos

Propósito: Reemplazar rutas de módulo antiguas:
  - golem/ → computadora/
  - golem. → computadora. (importes dentro de strings)

Ejecución:
  python scripts/MIGRAR_PATHS_ANTIGUOS.py
"""

from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def filtrar_archivos() -> list:
    """Obtiene todos archivos Python."""
    project_root = Path(__file__).parent.parent
    return list(project_root.glob("computadora/**/*.py"))


def migrar():
    """Reemplaza paths antiguos."""
    logger.info("🔄 FINAL-PASS: Reemplazando paths antiguos golem/ → computadora/...")
    
    archivos = filtrar_archivos()
    total_cambios = 0
    archivos_modificados = 0
    
    for archivo in archivos:
        try:
            contenido = archivo.read_text(encoding="utf-8")
            original = contenido
            
            # Reemplazos específicos
            contenido = contenido.replace('golem/', 'computadora/')
            contenido = contenido.replace("golem/", "computadora/")
            contenido = contenido.replace('golem.', 'computadora.')
            contenido = contenido.replace("golem.", "computadora.")
            
            if contenido != original:
                cambios = (
                    len(original.split('golem/')) - len(contenido.split('golem/')) +
                    len(original.split('golem.')) - len(contenido.split('golem.'))
                )
                
                archivo.write_text(contenido, encoding="utf-8")
                total_cambios += cambios
                archivos_modificados += 1
                logger.info(f"✅ {archivo.relative_to(archivo.parent.parent.parent)} [{cambios} cambios]")
        
        except Exception as e:
            logger.error(f"Error: {e}")
    
    logger.info(f"\n✅ FINAL-PASS completado:")
    logger.info(f"   Cambios: {total_cambios}")
    
    return True


if __name__ == "__main__":
    migrar()
