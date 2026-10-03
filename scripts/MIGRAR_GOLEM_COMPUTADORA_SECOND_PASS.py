#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CITRINITAS: Script de Second-Pass para Residuos Golem

Propósito: Capturar residuos que el primer script no modificó:
  - Imports: "from golem" → "from computadora"
  - Docstrings: "Golem" → "Computadora" (excepto conceptos esotéricos)
  - Variables string: "golem" → "computadora"

Ejecución:
  python scripts/MIGRAR_GOLEM_COMPUTADORA_SECOND_PASS.py
"""

import re
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def crear_reemplazos_agresivos() -> List[Tuple[str, str]]:
    """Reemplazos más agresivos para capturar residuos."""
    return [
        # Imports (lo más probable)
        ('from golem.', 'from computadora.'),
        ('import golem.', 'import computadora.'),
        ('import golem', 'import computadora'),
        
        # Strings en código (docstrings, comentarios)
        ('"golem ', '"computadora '),
        ("'golem ", "'computadora "),
        ('# golem', '# computadora'),
        
        # Paths y referencias
        ('path/golem', 'path/computadora'),
        ('golem_', 'computadora_'),
        
        # Genéricos finales
        (r' golem\b', ' computadora'),  # Regex
    ]


def filtrar_archivos_python() -> List[Path]:
    """Obtiene lista de archivos .py en computadora/"""
    project_root = Path(__file__).parent.parent
    py_files = list(project_root.glob("computadora/**/*.py"))
    logger.info(f"📁 Encontrados {len(py_files)} archivos Python")
    return py_files


def aplicar_reemplazos(contenido: str, reemplazos: List[Tuple[str, str]]) -> Tuple[str, int]:
    """Aplica reemplazos."""
    resultado = contenido
    cambios = 0
    
    for viejo, nuevo in reemplazos:
        # Verificar si es regex
        if viejo.startswith(r'\b') or viejo.startswith(r'\w'):
            try:
                pattern = re.compile(viejo)
                matches = pattern.findall(resultado)
                if matches:
                    resultado = pattern.sub(nuevo, resultado)
                    cambios += len(matches)
                    logger.debug(f"  REGEX: {viejo} → {nuevo} [{len(matches)}x]")
            except Exception as e:
                logger.warning(f"Error en regex {viejo}: {e}")
        else:
            # String literal
            matches_count = resultado.count(viejo)
            if matches_count > 0:
                resultado = resultado.replace(viejo, nuevo)
                cambios += matches_count
                logger.debug(f"  {viejo} → {nuevo} [{matches_count}x]")
    
    return resultado, cambios


def migrar():
    """Ejecuta second-pass de migración."""
    logger.info("🔄 SECOND-PASS: Migrando residuos Golem → Computadora...")
    
    reemplazos = crear_reemplazos_agresivos()
    archivos = filtrar_archivos_python()
    
    total_cambios = 0
    archivos_modificados = 0
    
    for archivo in archivos:
        try:
            contenido_original = archivo.read_text(encoding="utf-8")
            contenido_nuevo, cambios = aplicar_reemplazos(contenido_original, reemplazos)
            
            if cambios > 0:
                archivo.write_text(contenido_nuevo, encoding="utf-8")
                total_cambios += cambios
                archivos_modificados += 1
                logger.info(f"✅ {archivo.relative_to(archivo.parent.parent.parent)} [{cambios} cambios]")
        
        except Exception as e:
            logger.error(f"❌ Error en {archivo}: {e}")
    
    logger.info(f"\n✅ SECOND-PASS completado:")
    logger.info(f"   Archivos modificados: {archivos_modificados}")
    logger.info(f"   Total cambios: {total_cambios}")
    
    return total_cambios > 0


if __name__ == "__main__":
    éxito = migrar()
    exit(0 if éxito else 1)
