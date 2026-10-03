#!/usr/bin/env python3
"""
SOLUCIÓN OPERACIONAL: Sistema de ubicación de archivos PRE-CREACIÓN

Este módulo se importa en cada script que crea archivos para:
1. PRE-determinar la ubicación correcta
2. ADVERTIR si intenta crear en raíz
3. MOVER automáticamente si termina en raíz
"""

from pathlib import Path
from typing import Optional, Literal

class FileLocationManager:
    """Gestor centralizado de ubicaciones de archivos."""
    
    # Mapeo: patrón de nombre → directorio
    LOCATION_MAP = {
        # Scripts de diagnóstico
        'NIGREDO': 'scripts/diagnostics',
        'VALIDAR': 'scripts/diagnostics',
        'PROFILER': 'scripts/diagnostics',
        'SOLUCION': 'scripts/diagnostics',
        'VERIFICACION': 'scripts/diagnostics',
        'diagnose': 'scripts/diagnostics',
        'diagnóstico': 'scripts/diagnostics',
        'audit': 'scripts/diagnostics',
        'monitor': 'scripts/diagnostics',
        'check_': 'scripts/diagnostics',
        'rubedo': 'scripts/diagnostics',
        'FIX_': 'scripts/diagnostics',
        
        # Tests
        'test_': 'tests',
        
        # Documentación - Reports
        'RESUMEN': 'docs/REPORTS',
        'PALINGENESIA': 'docs/REPORTS',
        'AUDITORIA': 'docs/REPORTS',
        
        # Documentación - Referencias
        'WORKFLOW': 'docs/REFERENCE',
        'DESARROLLO': 'docs/REFERENCE',
        'REORGANIZACION': 'docs/REFERENCE',
        'DEUDA_TECNICA': 'docs/REFERENCE',
        
        # Documentación - Miscelánea
        'ARCHIVAL': 'docs/MISC',
        'SESION': 'docs/MISC',
        'META_': 'docs/MISC',
        'ANALISIS': 'docs/MISC',
    }
    
    # Blancalist - archivos que SÍ pueden estar en raíz
    WHITELIST_RAIZ = {
        'iniciar computadora.bat',
        'INDEX.md',
        'README.md',
        'WorkItems.md',
        'WORKFLOW_OPERACIONAL.md',
        'SRS.md',
        'SDD.md',
    }
    
    @classmethod
    def get_location(cls, filename: str) -> str:
        """
        PRE-determina ubicación de archivo ANTES de crearlo.
        
        Returns: ruta de directorio (ej: 'scripts/diagnostics' o 'docs/REPORTS')
        """
        # Si está en blancalist, permitir raíz
        if filename in cls.WHITELIST_RAIZ:
            return '.'
        
        # Buscar patrón en nombre
        filename_upper = filename.upper()
        for pattern, location in cls.LOCATION_MAP.items():
            if pattern.lower() in filename_upper.lower():
                return location
        
        # Por extensión
        if filename.endswith('.py'):
            return 'scripts/diagnostics'
        elif filename.endswith('.md'):
            return 'docs/REFERENCE'
        elif filename.endswith('.json'):
            return 'scripts/diagnostics'
        elif filename.endswith('.txt'):
            return '.logs'
        
        # Default seguro
        return 'docs/MISC'
    
    @classmethod
    def ensure_directory(cls, location: str) -> Path:
        """Crear directorio si no existe."""
        path = Path(location)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @classmethod
    def create_file(cls, filename: str, content: str, warn: bool = True) -> Path:
        """
        Crear archivo en ubicación correcta.
        
        Args:
            filename: nombre del archivo
            content: contenido
            warn: mostrar advertencia si intenta crear en raíz
        
        Returns: Path del archivo creado
        """
        location = cls.get_location(filename)
        
        if warn and location == '.':
            print(f'⚠️  ADVERTENCIA: Creando "{filename}" en raíz')
        
        dir_path = cls.ensure_directory(location)
        file_path = dir_path / filename
        
        print(f'✓ Creando: {file_path}')
        file_path.write_text(content, encoding='utf-8')
        
        return file_path
    
    @classmethod
    def move_if_in_root(cls, filename: str) -> Optional[Path]:
        """
        Si archivo existe en raíz PERO debe estar en otro lado, moverlo.
        Útil como POST-PROCESSOR.
        
        Returns: Path del archivo si fue movido, None si ya estaba bien
        """
        root_path = Path(filename)
        if not root_path.exists():
            return None
        
        location = cls.get_location(filename)
        
        if location == '.':
            return None  # Debe estar en raíz, ok
        
        # Mover a ubicación correcta
        dest_dir = cls.ensure_directory(location)
        dest_path = dest_dir / filename
        
        print(f'↗️  Moviendo: {filename} → {location}/')
        root_path.rename(dest_path)
        
        return dest_path


# Ejemplo de uso:
if __name__ == '__main__':
    # PRE-crear con ubicación automática
    loc = FileLocationManager.get_location('NIGREDO_TEST.py')
    print(f'Archivo "NIGREDO_TEST.py" → {loc}/')
    
    loc = FileLocationManager.get_location('test_algo.py')
    print(f'Archivo "test_algo.py" → {loc}/')
    
    loc = FileLocationManager.get_location('DEUDA_TECNICA.md')
    print(f'Archivo "DEUDA_TECNICA.md" → {loc}/')
    
    loc = FileLocationManager.get_location('INDEX.md')
    print(f'Archivo "INDEX.md" → {loc}/ (blancalist)')
