#!/usr/bin/env python3
"""
🔍 NIGREDO AUDIT — Auditoría Automatizada de Coherencia Estructural

Ejecuta verificaciones de coherencia en:
  1. Organización de archivos (raíz limpia)
  2. Terminología (Enciclopedia vs Grimorio, Computadora vs COMPUTADORA)
  3. Referencias (links internos válidos)
  4. Duplicación de código
  5. Archivos obsoletos
  6. Mapeo esotérico↔pragmático

Uso:
  python nigredo_audit.py               # Auditoría completa
  python nigredo_audit.py --quick       # Solo errores críticos
  python nigredo_audit.py --json        # Output JSON

Inyectable: Ejecutar ANTES de cada petición en WORKFLOW
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class NigresoAudit:
    """Auditoría de coherencia estructural + terminológica"""
    
    def __init__(self, root_path="."):
        self.root = Path(root_path)
        self.errors = []
        self.warnings = []
        self.info = []
        self.timestamp = datetime.now().isoformat()
        
        # Configuración
        self.allowed_root_files = {
            "README.md", "WORKFLOW_OPERACIONAL.md", "WorkItems.md",
            "config.json", "pyproject.toml", ".gitignore", ".github",
            "DIAGNOSTICO_DESALINEACION_ESTRUCTURAL.md",
            "REMEDIACION_ESTRUCTURAL_COMPLETADA.md"
        }
        
        self.allowed_root_dirs = {
            "computadora", "tests", "ENCICLOPEDIA", "_docs", "_archive",
            ".management", ".github", "computadora", "libro_encantado", "libro_encantado_archive"
        }
        
        # Términos prohibidos en código vivo
        self.prohibited_terms = {
            "servidor_grimorio": "use 'servidor_enciclopedia' instead",
            "iniciar_grimorio": "use 'iniciar_enciclopedia' instead",
            "grimorio_guardian": "use 'enciclopedia_guardian' instead",
        }
        
        # Términos correctos esperados
        self.required_terms = {
            "servidor_enciclopedia": "ENCICLOPEDIA/servidor_enciclopedia.py",
        }
    
    def audit_root_organization(self):
        """Verificar que raíz esté limpia"""
        print("\n🔍 Auditando organización de raíz...")
        
        root_items = list(self.root.iterdir())
        for item in root_items:
            if item.name.startswith('.'):
                continue
            
            if item.is_file():
                if item.name not in self.allowed_root_files:
                    self.warnings.append(
                        f"Archivo en raíz no permitido: {item.name} "
                        f"(debería estar en _docs/ o _archive/)"
                    )
            elif item.is_dir():
                if item.name not in self.allowed_root_dirs:
                    self.warnings.append(
                        f"Directorio en raíz no permitido: {item.name}/"
                    )
        
        self.info.append(f"✅ Raíz: {len(root_items)} items analizados")
    
    def audit_terminology(self):
        """Verificar terminología coherente"""
        print("🔍 Auditando terminología...")
        
        # Archivos a escanear
        files_to_scan = [
            "_docs/COMANDOS.md",
            "_docs/ARCHITECTURE/MAPEO_ESOTERICO_PRAGMATICO.md",
            "computadora/nucleo/emet.py",
            "computadora/core/main.py",
        ]
        
        for file_path in files_to_scan:
            full_path = self.root / file_path
            if not full_path.exists():
                self.info.append(f"⏭️  Saltado (no existe): {file_path}")
                continue
            
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Buscar términos prohibidos
                for prohibited, replacement in self.prohibited_terms.items():
                    if prohibited in content.lower():
                        matches = len(re.findall(rf'\b{re.escape(prohibited)}\b', content, re.IGNORECASE))
                        self.errors.append(
                            f"{file_path}: '{prohibited}' encontrado {matches}× — {replacement}"
                        )
                
            except Exception as e:
                self.warnings.append(f"No se pudo leer {file_path}: {e}")
        
        self.info.append("✅ Terminología verificada")
    
    def audit_duplication(self):
        """Buscar archivos duplicados/obsoletos"""
        print("🔍 Auditando duplicación de código...")
        
        # Archivos que NO deben existir
        obsolete_files = [
            "ENCICLOPEDIA/servidor_grimorio.py",
            "ENCICLOPEDIA/iniciar_grimorio.bat",
            "libro_encantado/servidor_grimorio.py",
        ]
        
        for file_path in obsolete_files:
            full_path = self.root / file_path
            if full_path.exists():
                self.errors.append(f"⚠️ Archivo obsoleto encontrado: {file_path} (remover)")
        
        self.info.append("✅ Duplicación verificada")
    
    def audit_references(self):
        """Verificar referencias internas válidas"""
        print("🔍 Auditando referencias...")
        
        # Documentos que hacen referencias
        docs_to_check = [
            "_docs/COMANDOS.md",
            "REMEDIACION_ESTRUCTURAL_COMPLETADA.md",
        ]
        
        for doc in docs_to_check:
            full_path = self.root / doc
            if not full_path.exists():
                continue
            
            try:
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                
                # Buscar referencias a archivos
                # Patrón: [texto](path/file.md)
                refs = re.findall(r'\]\(([^)]+)\)', content)
                
                for ref in refs:
                    # Ignorar URLs externas
                    if ref.startswith('http'):
                        continue
                    
                    # Ignorar fragmentos
                    if ref.startswith('#'):
                        continue
                    
                    ref_path = self.root / ref
                    if not ref_path.exists():
                        self.warnings.append(
                            f"{doc}: Referencia rota → {ref}"
                        )
            
            except Exception as e:
                self.warnings.append(f"No se pudo leer {doc}: {e}")
        
        self.info.append("✅ Referencias verificadas")
    
    def audit_mappings(self):
        """Verificar mapeos esotérico↔pragmático"""
        print("🔍 Auditando mapeos...")
        
        mapping_file = self.root / "_docs/ARCHITECTURE/MAPEO_ESOTERICO_PRAGMATICO.md"
        
        if not mapping_file.exists():
            self.errors.append("Archivo crítico no encontrado: _docs/ARCHITECTURE/MAPEO_ESOTERICO_PRAGMATICO.md")
            return
        
        try:
            content = mapping_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar que contenga mapeos clave
            required_mappings = [
                "Computadora.*COMPUTADORA",
                "Grimorio.*Enciclopedia",
                "Palabra.*Mágica.*Comando",
            ]
            
            for mapping in required_mappings:
                if not re.search(mapping, content, re.IGNORECASE):
                    self.warnings.append(
                        f"Mapeo no encontrado en MAPEO_ESOTERICO_PRAGMATICO.md: {mapping}"
                    )
            
            self.info.append("✅ Mapeos verificados")
        
        except Exception as e:
            self.errors.append(f"Error leyendo mapeos: {e}")
    
    def audit_tracker(self):
        """Verificar que tracker de estado esté actualizado"""
        print("🔍 Auditando tracker...")
        
        tracker_file = self.root / ".management/TRACKER_ESTADO_TRABAJOS.md"
        
        if not tracker_file.exists():
            self.warnings.append("Tracker no encontrado: .management/TRACKER_ESTADO_TRABAJOS.md")
            return
        
        try:
            content = tracker_file.read_text(encoding='utf-8', errors='ignore')
            
            # Verificar que esté actualizado
            # (tiene timestamp reciente)
            if not re.search(r'\d{4}-\d{2}-\d{2}', content):
                self.warnings.append("Tracker sin fecha de actualización")
            
            self.info.append("✅ Tracker verificado")
        
        except Exception as e:
            self.warnings.append(f"No se pudo leer tracker: {e}")
    
    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        print("\n" + "="*60)
        print("🔍 NIGREDO AUDIT — Auditoría de Coherencia Estructural")
        print("="*60)
        
        self.audit_root_organization()
        self.audit_terminology()
        self.audit_duplication()
        self.audit_references()
        self.audit_mappings()
        self.audit_tracker()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generar reporte de auditoría"""
        report = {
            "timestamp": self.timestamp,
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "info": len(self.info)
            },
            "details": {
                "errors": self.errors,
                "warnings": self.warnings,
                "info": self.info
            },
            "status": "PASSED" if not self.errors else "FAILED"
        }
        
        return report
    
    def print_report(self, report):
        """Imprimir reporte formateado"""
        print("\n" + "="*60)
        print("📊 REPORTE NIGREDO AUDIT")
        print("="*60)
        
        summary = report["summary"]
        print(f"\n📈 Resumen:")
        print(f"  ✅ Información:   {summary['info']}")
        print(f"  ⚠️  Advertencias:  {summary['warnings']}")
        print(f"  ❌ Errores:       {summary['errors']}")
        
        if report["details"]["errors"]:
            print(f"\n❌ ERRORES (críticos):")
            for error in report["details"]["errors"]:
                print(f"   • {error}")
        
        if report["details"]["warnings"]:
            print(f"\n⚠️  ADVERTENCIAS:")
            for warning in report["details"]["warnings"]:
                print(f"   • {warning}")
        
        if report["details"]["info"]:
            print(f"\n✅ INFORMACIÓN:")
            for info in report["details"]["info"]:
                print(f"   • {info}")
        
        print(f"\n🎯 Status: {report['status']}")
        print("="*60 + "\n")
        
        return report["status"] == "PASSED"
    
    def to_json(self):
        """Exportar a JSON"""
        report = self.generate_report()
        return json.dumps(report, indent=2, ensure_ascii=False)


def main():
    """Entrada principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Auditoría NIGREDO de coherencia estructural"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output en formato JSON"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Solo errores críticos"
    )
    
    args = parser.parse_args()
    
    audit = NigresoAudit()
    report = audit.run_full_audit()
    
    if args.json:
        print(audit.to_json())
    else:
        passed = audit.print_report(report)
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
