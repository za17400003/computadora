"""Detector de Contradicciones — Identifica incoherencias.

Tipos de contradicciones detectadas:
  1. Caché expirado: ¿Datos TTL vencido?
  2. Memoria duplicada: ¿Encodings faciales duplicados?
  3. Estados inconsistentes: NLU dice X pero UI dice Y
  4. Imports rotos: Referencias a computadora.* aún presentes
  5. Archivos huérfanos: Datos sin propietario conocido
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from loguru import logger


@dataclass
class Contradiccion:
    """Reporte de contradicción detectada."""
    timestamp: str
    tipo: str  # "cache_expirado" | "duplicado" | "estado_inconsistente" | "import_roto" | "orfano"
    descripcion: str
    ubicacion: str  # Path o modulo
    edad_horas: Optional[float] = None  # Si es expirado
    severidad: str = "MEDIA"  # CRITICA | ALTA | MEDIA | BAJA
    accion_sugerida: str = "revisar"  # "borrar" | "revisar" | "consolidar"


class DetectorContradicciones:
    """Auditor que detecta contradicciones."""
    
    def __init__(self, ttl_horas: int = 24):
        self.ttl = ttl_horas
        self.contradicciones: list[Contradiccion] = []
        logger.info(f"DetectorContradicciones inicializado (TTL: {ttl_horas}h)")
    
    def detectar_cache_expirado(self, cache_dir: str = ".cache") -> list[Contradiccion]:
        """Detectar archivos de caché > TTL."""
        encontradas = []
        
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return encontradas
        
        ahora = datetime.now()
        ttl_delta = timedelta(hours=self.ttl)
        
        for file in cache_path.rglob("*"):
            if not file.is_file():
                continue
            
            edad = datetime.fromtimestamp(file.stat().st_mtime)
            diferencia = ahora - edad
            
            if diferencia > ttl_delta:
                edad_horas = diferencia.total_seconds() / 3600
                encontradas.append(Contradiccion(
                    timestamp=datetime.now().isoformat(),
                    tipo="cache_expirado",
                    descripcion=f"Caché expirado: {file.name} ({int(edad_horas)}h antiguo)",
                    ubicacion=str(file),
                    edad_horas=edad_horas,
                    severidad="BAJA",
                    accion_sugerida="borrar"
                ))
        
        return encontradas
    
    def detectar_duplicados_encoding(self, datos_dir: str = "datos") -> list[Contradiccion]:
        """Detectar encodings faciales duplicados."""
        encontradas = []
        
        # Si existe FACEREC_RECORD.json y owner_face_profile.json
        facerec_file = Path(datos_dir) / "FACEREC_RECORD.json"
        owner_file = Path(datos_dir) / "owner_face_profile.json"
        
        if facerec_file.exists() and owner_file.exists():
            try:
                facerec = json.loads(facerec_file.read_text())
                owner = json.loads(owner_file.read_text())
                
                # Si ambos tienen encoding del mismo usuario → duplicado
                if (facerec.get("nombre_corto") == owner.get("owner_name") and
                    "encoding" in facerec and "encoding" in owner):
                    encontradas.append(Contradiccion(
                        timestamp=datetime.now().isoformat(),
                        tipo="duplicado",
                        descripcion="Encoding facial duplicado en FACEREC_RECORD y owner_face_profile",
                        ubicacion=f"{facerec_file} + {owner_file}",
                        severidad="MEDIA",
                        accion_sugerida="consolidar"
                    ))
            except Exception as e:
                logger.debug(f"No se pudo detectar duplicados: {e}")
        
        return encontradas
    
    def detectar_imports_rotos(self, test_dir: str = "tests") -> list[Contradiccion]:
        """Detectar imports rotos (referencias a computadora.*)."""
        encontradas = []
        
        test_path = Path(test_dir)
        if not test_path.exists():
            return encontradas
        
        for file in test_path.rglob("*.py"):
            try:
                content = file.read_text()
                
                if "from computadora." in content or "import computadora." in content:
                    encontradas.append(Contradiccion(
                        timestamp=datetime.now().isoformat(),
                        tipo="import_roto",
                        descripcion=f"Import obsoleto detectado: computadora.* aún presente",
                        ubicacion=str(file),
                        severidad="ALTA",
                        accion_sugerida="revisar"
                    ))
            except Exception as e:
                logger.debug(f"No se pudo leer {file}: {e}")
        
        return encontradas
    
    def detectar_archivos_orfanos(self, datos_dir: str = "datos") -> list[Contradiccion]:
        """Detectar archivos de datos sin propietario conocido."""
        encontradas = []
        
        datos_path = Path(datos_dir)
        if not datos_path.exists():
            return encontradas
        
        # Archivos "válidos" conocidos
        archivos_validos = {
            "config.json",
            "owner_face_profile.json",
            "FACEREC_RECORD.json",
        }
        
        for file in datos_path.iterdir():
            if file.name not in archivos_validos and file.is_file():
                encontradas.append(Contradiccion(
                    timestamp=datetime.now().isoformat(),
                    tipo="orfano",
                    descripcion=f"Archivo huérfano sin propietario: {file.name}",
                    ubicacion=str(file),
                    severidad="BAJA",
                    accion_sugerida="revisar"
                ))
        
        return encontradas
    
    def detectar_todos(self) -> list[Contradiccion]:
        """Ejecutar TODAS las detecciones."""
        encontradas = []
        encontradas.extend(self.detectar_cache_expirado())
        encontradas.extend(self.detectar_duplicados_encoding())
        encontradas.extend(self.detectar_imports_rotos())
        encontradas.extend(self.detectar_archivos_orfanos())
        
        self.contradicciones = encontradas
        
        # Log summary
        por_severidad = {}
        for c in encontradas:
            por_severidad[c.severidad] = por_severidad.get(c.severidad, 0) + 1
        
        logger.info(f"✓ Detección completada: {len(encontradas)} contradicciones — {por_severidad}")
        
        return encontradas


