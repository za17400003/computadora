#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CITRINITAS: Script de Migración Grimorio → Enciclopedia

Propósito: Reemplazar todas instancias de "Grimorio/grimorio" por "Enciclopedia/enciclopedia"
en el código Python, manteniendo case-sensitivity.

Auditoría previa: 178 instancias encontradas.

Ejecución:
  cd proyecto-golem
  python scripts/MIGRAR_GRIMORIO_ENCICLOPEDIA.py

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
    Define lista de reemplazos ordenados por especificidad (MÁS específico primero).
    
    Retorna: Lista de tuples (viejo, nuevo) para aplicar en orden
    """
    return [
        # Clases y nombres compuestos (más específico)
        ("class GrimorioGuardian", "class EnciclopediaGuardian"),
        ("GrimorioGuardian", "EnciclopediaGuardian"),
        
        # Variables y rutas (con underscore)
        ("_INTRUSION_LOG", "_INTRUSION_LOG"),  # No cambiar — es nombre de variable
        ("grimorio_intrusiones", "enciclopedia_intrusiones"),
        ("grimorio_abierto", "enciclopedia_abierto"),
        ("grimorio_guardian", "enciclopedia_guardian"),
        ("_grimorio", "_enciclopedia"),
        
        # Texto descriptivo (case-sensitive)
        ("Grimorio", "Enciclopedia"),
        ("grimorio", "enciclopedia"),
    ]


def filtrar_archivos_python() -> List[Path]:
    """Obtiene lista de archivos .py en computadora/"""
    project_root = Path(__file__).parent.parent
    py_files = list(project_root.glob("computadora/**/*.py"))
    logger.info(f"📁 Encontrados {len(py_files)} archivos Python")
    return py_files


def aplicar_reemplazos(contenido: str, reemplazos: List[Tuple[str, str]]) -> str:
    """Aplica reemplazos manteniendo context."""
    resultado = contenido
    cambios = 0
    
    for viejo, nuevo in reemplazos:
        if viejo == nuevo:
            continue  # Saltar si es idéntico
        
        # Contar coincidencias
        matches = resultado.count(viejo)
        if matches > 0:
            resultado = resultado.replace(viejo, nuevo)
            cambios += matches
            logger.debug(f"  {viejo} → {nuevo} [{matches}x]")
    
    return resultado, cambios


def migrar():
    """Ejecuta migración Grimorio → Enciclopedia."""
    logger.info("🔄 Iniciando migración Grimorio → Enciclopedia...")
    
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
