#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CITRINITAS: Script de Migración Golem → Computadora

Propósito: Reemplazar todas instancias de "Golem/golem" por "Computadora/computadora"
en el código Python, manteniendo case-sensitivity y evitando falsas coincidencias.

Auditoría previa: 241 instancias encontradas.

CUIDADO: 
  - Firestore collections("golem") → collections("computadora")
  - Imports: from golem.* → from computadora.* (YA CAMBIADO en estructura)
  - No cambiar comentarios esotéricos que referencenan "Golem" como concepto mitológico

Ejecución:
  cd proyecto-golem
  python scripts/MIGRAR_GOLEM_COMPUTADORA.py

Validación posterior:
  python scripts/VERIFICAR_MIGRACION.py
"""

import re
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def crear_reemplazos() -> List[Tuple[str, str]]:
    """
    Define lista de reemplazos ordenados por especificidad.
    
    Retorna: Lista de tuples (viejo, nuevo) para aplicar en orden
    """
    return [
        # Firestore collections (crítico)
        ('collection("golem")', 'collection("computadora")'),
        ("collection('golem')", "collection('computadora')"),
        
        # Clases y nombres compuestos
        ("class OrbeGolem", "class OrbeComputadora"),
        ("OrbeGolem", "OrbeComputadora"),
        
        # Variables y atributos
        ("_orbe_golem", "_orbe_computadora"),
        ("orbe_golem", "orbe_computadora"),
        
        # Texto descriptivo (evitar cambiar conceptos esotéricos)
        # Solo strings obvios de interfaz/API
        ('"Golem minimizado', '"Computadora minimizada'),
        ('del Golem', 'de la Computadora'),
        ('del golem', 'de la computadora'),
        ('Golem se', 'Computadora se'),
        ('golem se', 'computadora se'),
        
        # URLs y prefijos
        ("PREFIJO_LEGADO = \"golem ", "PREFIJO_LEGADO = \"computadora "),
        
        # Genéricos (últimos, para no interferir con específicos)
        (" Golem", " Computadora"),
        (" golem", " computadora"),
    ]


def filtrar_archivos_python() -> List[Path]:
    """Obtiene lista de archivos .py en computadora/"""
    project_root = Path(__file__).parent.parent
    py_files = list(project_root.glob("computadora/**/*.py"))
    logger.info(f"📁 Encontrados {len(py_files)} archivos Python")
    return py_files


def aplicar_reemplazos(contenido: str, reemplazos: List[Tuple[str, str]]) -> Tuple[str, int]:
    """Aplica reemplazos manteniendo context."""
    resultado = contenido
    cambios = 0
    
    for viejo, nuevo in reemplazos:
        if viejo == nuevo:
            continue
        
        matches = resultado.count(viejo)
        if matches > 0:
            resultado = resultado.replace(viejo, nuevo)
            cambios += matches
            logger.debug(f"  {viejo} → {nuevo} [{matches}x]")
    
    return resultado, cambios


def migrar():
    """Ejecuta migración Golem → Computadora."""
    logger.info("🔄 Iniciando migración Golem → Computadora...")
    logger.warning("⚠️  Cuidado: Verificar que cambios en comments sean intencionales")
    
    reemplazos = crear_reemplazos()
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
    
    logger.info(f"\n✅ Migración completada:")
    logger.info(f"   Archivos modificados: {archivos_modificados}")
    logger.info(f"   Total cambios: {total_cambios}")
    
    return total_cambios > 0


if __name__ == "__main__":
    éxito = migrar()
    exit(0 if éxito else 1)
