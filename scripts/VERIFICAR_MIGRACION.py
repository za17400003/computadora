#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CITRINITAS: Script de Verificación post-Migración

Propósito: Verificar que no quedan instancias residuales de:
  - "Grimorio" / "grimorio" (debería ser "Enciclopedia" / "enciclopedia")
  - "Computadora" / "computadora" (debería ser "Computadora" / "computadora")

Ejecución:
  python scripts/VERIFICAR_MIGRACION.py

Retorna: exit(0) si migración completa, exit(1) si hay residuos
"""

import re
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def filtrar_archivos_python() -> List[Path]:
    """Obtiene lista de archivos .py en computadora/"""
    project_root = Path(__file__).parent.parent
    return list(project_root.glob("computadora/**/*.py"))


def buscar_patrones(contenido: str, patrones: Dict[str, str]) -> Dict[str, List[int]]:
    """
    Busca patrones en contenido.
    
    Retorna: {patrón: [líneas donde aparece]}
    """
    resultados = {}
    líneas = contenido.split("\n")
    
    for patrón in patrones:
        matches = []
        for i, línea in enumerate(líneas, 1):
            if re.search(r"\b" + patrón + r"\b", línea):
                matches.append(i)
        
        if matches:
            resultados[patrón] = matches
    
    return resultados


def verificar():
    """Verifica limpieza de terminología."""
    logger.info("🔍 Verificando migración...")
    
    # Patrones a buscar (no deberían existir)
    patrones_grimorio = {
        "Grimorio": "enciclopedia_guardian.py, escucha.py, etc",
        "grimorio": "nombres de variables/funciones",
    }
    
    patrones_computadora = {
        "Computadora": "texto descriptivo, comentarios",
        "computadora": "variables, imports",
    }
    
    archivos = filtrar_archivos_python()
    
    residuos_grimorio = {}
    residuos_computadora = {}
    
    for archivo in archivos:
        try:
            contenido = archivo.read_text(encoding="utf-8")
            
            matches_grimorio = buscar_patrones(contenido, patrones_grimorio)
            matches_computadora = buscar_patrones(contenido, patrones_computadora)
            
            if matches_grimorio:
                residuos_grimorio[archivo] = matches_grimorio
            
            if matches_computadora:
                residuos_computadora[archivo] = matches_computadora
        
        except Exception as e:
            logger.error(f"Error leyendo {archivo}: {e}")
    
    # Reportar resultados
    logger.info("\n" + "=" * 60)
    
    if residuos_grimorio:
        logger.error("❌ RESIDUOS ENCONTRADOS: Grimorio/grimorio")
        for archivo, matches in residuos_grimorio.items():
            rel_path = archivo.relative_to(archivo.parent.parent.parent)
            logger.error(f"\n  {rel_path}:")
            for patrón, líneas in matches.items():
                logger.error(f"    '{patrón}' en líneas: {líneas[:5]}{'...' if len(líneas) > 5 else ''}")
    else:
        logger.info("✅ Grimorio → Enciclopedia: COMPLETADO")
    
    if residuos_computadora:
        logger.error("❌ RESIDUOS ENCONTRADOS: Computadora/computadora")
        for archivo, matches in residuos_computadora.items():
            rel_path = archivo.relative_to(archivo.parent.parent.parent)
            logger.error(f"\n  {rel_path}:")
            for patrón, líneas in matches.items():
                logger.error(f"    '{patrón}' en líneas: {líneas[:5]}{'...' if len(líneas) > 5 else ''}")
    else:
        logger.info("✅ Computadora → Computadora: COMPLETADO")
    
    logger.info("\n" + "=" * 60)
    
    if residuos_grimorio or residuos_computadora:
        logger.error("\n❌ MIGRACION INCOMPLETA — Residuos detectados")
        return False
    
    logger.info("\n✅ MIGRACION COMPLETA — Terminología estandarizada")
    return True


if __name__ == "__main__":
    éxito = verificar()
    exit(0 if éxito else 1)
