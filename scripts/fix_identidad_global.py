#!/usr/bin/env python3
"""
RUBEDO Phase 2: Reemplazar todas las referencias "Golem"→"Computadora" en código
Este script implementa auto-remediación sistemática de identidad de proyecto.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
COMPUTADORA_DIR = PROJECT_ROOT / "computadora"

# Mapeo de replacements (old → new)
REPLACEMENTS = [
    # Comentarios y docstrings
    (r"Cerebro del Golem", "Cerebro de COMPUTADORA"),
    (r"Cerebro de Golem", "Cerebro de COMPUTADORA"),
    (r"reencarnación del Golem", "reencarnación de COMPUTADORA"),
    (r"Protocolo de reinicio\s+para golem", "Protocolo de reinicio para computadora"),
    (r"reinicie para todos los conjuntos y subconjuntos de golem", 
     "reinicie para todos los conjuntos y subconjuntos de computadora"),
    (r"Módulo de voz de Golem", "Módulo de voz de COMPUTADORA"),
    (r"Módulo de habla.*Golem", "Módulo de habla de COMPUTADORA"),
    (r"Canales de comunicación externos de Golem", "Canales de comunicación externos de COMPUTADORA"),
    (r"Vigila eventos del Grimorio y alerta a Golem", "Vigila eventos del Grimorio y alerta a COMPUTADORA"),
    (r"el Grimorio → Golem", "el Grimorio → COMPUTADORA"),
    (r"Golem lo sabe", "COMPUTADORA lo sabe"),
    (r"Golem no ha respondido", "COMPUTADORA no ha respondido"),
    (r"Golem minimizado", "COMPUTADORA minimizada"),
    (r"Reactivación:.*Golem, despierta", 'Reactivación: "Computadora, despierta"'),
    (r"Canal Telegram.*Golem", "Canal Telegram → COMPUTADORA"),
    (r"📡 Telegram.*Golem:", "📡 Telegram → COMPUTADORA:"),
    (r"Minimi es parte de Golem", "Minimi es parte de COMPUTADORA"),
    (r"parte esencial del Golem", "parte esencial de COMPUTADORA"),
    (r"Manifiesto de verdad del Golem", "Manifiesto de verdad de COMPUTADORA"),
    (r"sentidos del Golem", "sentidos de COMPUTADORA"),
    (r"Estado actual del Golem", "Estado actual de COMPUTADORA"),
    (r"Configuraci.n global de Golem", "Configuración global de COMPUTADORA"),
    (r"Estado del Golem", "Estado de COMPUTADORA"),
    (r"Ciclo infinito del Golem", "Ciclo infinito de COMPUTADORA"),
    (r"Ciclo infinito de COMPUTADORA", "Ciclo infinito de COMPUTADORA"),  # Normalizar duplicado
    (r"Ayin HaGolem", "Ayin HaComputadora"),
    (r"RF-258.*Ayin HaComputadora", "RF-258 Ayin HaComputadora"),
    
    # Variables y nombres
    (r"ram_golem_mb", "ram_computadora_mb"),
    (r"_ultimo_estado_golem", "_ultimo_estado_computadora"),
    (r"estado_golem", "estado_computadora"),
    (r"_estado_golem\(\)", "_estado_computadora()"),
    (r"def _estado_golem", "def _estado_computadora"),
    (r"_modo_guardian\b", "_modo_guardiana"),  # Femenino para Computadora
    
    # Firestore collections
    (r'collection\("golem"\)', 'collection("computadora")'),
    (r'collection\(\s*"golem"\s*\)', 'collection("computadora")'),
    
    # mDNS services
    (r'"_golem\._tcp"', '"_computadora._tcp"'),
    (r"'_golem\._tcp'", "'_computadora._tcp'"),
    (r"_golem\._tcp\.local\.", "_computadora._tcp.local."),
    (r"Golem\._golem\._tcp\.local\.", "COMPUTADORA._computadora._tcp.local."),
    
    # Logger/imports
    (r"from golem import", "from computadora import"),
    (r"import golem\b", "import computadora"),
    (r'logging\.getLogger\("golem_shim"\)', 'logging.getLogger("computadora_app")'),
    (r"logger\.getLogger\(\s*['\"]golem", 'logger.getLogger("computadora'),
    
    # Mensajes de usuario
    (r"Configuraci.n cargada: whisper", "Configuración cargada: whisper"),  # UTF-8 fix
    (r"=== GOLEM INICIANDO ===", "=== COMPUTADORA INICIANDO ==="),
    (r"=== GOLEM FINALIZADO ===", "=== COMPUTADORA FINALIZADO ==="),
    
    # Documentos esotéricos internos (comentarios)
    (r"golem/arquitectura.*Metamodelo.*del Golem", "computadora/arquitectura — Metamodelo de COMPUTADORA"),
    (r"Olamot.*59 módulos de Golem", "Olamot — 59 módulos de COMPUTADORA"),
    (r"cómo el Golem entiende", "cómo COMPUTADORA entiende"),
    (r"Define las 16 dimensiones del Golem", "Define las 16 dimensiones de COMPUTADORA"),
]

def fix_file(filepath: Path) -> tuple[bool, int]:
    """
    Aplica replacements a un archivo individual.
    Return: (éxito, número de cambios)
    """
    if not filepath.is_file() or filepath.suffix != ".py":
        return False, 0
    
    try:
        content = filepath.read_text("utf-8")
        original = content
        
        for old_pattern, new_text in REPLACEMENTS:
            content = re.sub(old_pattern, new_text, content, flags=re.IGNORECASE | re.MULTILINE)
        
        if content != original:
            filepath.write_text(content, "utf-8")
            cambios = len([1 for o, n in REPLACEMENTS if re.search(o, original)])
            return True, cambios
        
        return True, 0
    except Exception as e:
        print(f"ERROR en {filepath}: {e}")
        return False, 0

def main():
    """Aplica fixes a todos los archivos Python en computadora/"""
    if not COMPUTADORA_DIR.exists():
        print(f"ERROR: {COMPUTADORA_DIR} no existe")
        return 1
    
    py_files = list(COMPUTADORA_DIR.rglob("*.py"))
    print(f"\n📝 Procesando {len(py_files)} archivos Python...")
    
    total_cambios = 0
    for filepath in py_files:
        exito, cambios = fix_file(filepath)
        if exito and cambios > 0:
            relpath = filepath.relative_to(PROJECT_ROOT)
            print(f"  ✓ {relpath}: {cambios} replacements")
            total_cambios += cambios
    
    print(f"\n✅ Completado: {total_cambios} cambios totales")
    return 0

if __name__ == "__main__":
    sys.exit(main())
