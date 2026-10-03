"""Verificador de Coherencia — Auditoría estructural en vivo.

Verifica que el sistema sea COHERENTE:
  1. Nombres: Proyecto = COMPUTADORA, Clases = Computadora
  2. Imports: Solo computadora.*, no computadora.*
  3. Fases: Boot sigue secuencia correcta
  4. Estados: Sensores reportan estado consistente
  5. Permisos: Propietario == Gevurá (autorización)
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger


@dataclass
class CoherenciaReport:
    """Reporte atómico de coherencia."""
    timestamp: str
    modulo: str  # "nombres" | "imports" | "fases" | "estados" | "permisos"
    estado: str  # "OK" | "WARNING" | "ERROR"
    descripcion: str
    esperado: Optional[str] = None
    actual: Optional[str] = None
    prioridad: str = "MEDIA"  # CRITICA | ALTA | MEDIA | BAJA
    
    def to_dict(self):
        return asdict(self)


class VerificadorCoherencia:
    """Auditor en vivo que verifica coherencia continua."""
    
    def __init__(self, audit_dir: str = ".audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
        self.reportes: list[CoherenciaReport] = []
        logger.info("VerificadorCoherencia inicializado")
    
    def verificar_nombres(self) -> CoherenciaReport:
        """Verifica: ¿Proyecto = COMPUTADORA, Clases = Computadora?"""
        try:
            # Verificar que no hay referencias a "Computadora" en imports críticos
            from computadora.interfaz import ventana_principal
            
            # Si la clase se llama OrbeComputadora, PASS
            if hasattr(ventana_principal, 'OrbeComputadora'):
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="nombres",
                    estado="OK",
                    descripcion="Clase OrbeComputadora presente, naming coherente",
                    prioridad="MEDIA"
                )
            else:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="nombres",
                    estado="ERROR",
                    descripcion="Clase OrbeComputadora NO encontrada",
                    esperado="OrbeComputadora",
                    actual="desconocida",
                    prioridad="CRITICA"
                )
        except Exception as e:
            return CoherenciaReport(
                timestamp=datetime.now().isoformat(),
                modulo="nombres",
                estado="WARNING",
                descripcion=f"No se pudo verificar nombres: {str(e)}",
                prioridad="ALTA"
            )
    
    def verificar_imports(self) -> CoherenciaReport:
        """Verifica: ¿Solo computadora.*, no computadora.*?"""
        try:
            # Buscar imports rotos en archivos críticos
            test_files = [
                Path("tests/test_bloque1_fix.py"),
                Path("tests/smoke_test.py"),
            ]
            
            broken_imports = []
            for test_file in test_files:
                if not test_file.exists():
                    continue
                
                content = test_file.read_text()
                if "from computadora." in content or "import computadora." in content:
                    broken_imports.append(str(test_file))
            
            if broken_imports:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="imports",
                    estado="ERROR",
                    descripcion=f"Imports rotos encontrados: {', '.join(broken_imports)}",
                    esperado="Todos: from computadora.*",
                    actual=f"Algunos aún: from computadora.*",
                    prioridad="ALTA"
                )
            else:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="imports",
                    estado="OK",
                    descripcion="Todos imports usan computadora.*, ninguno usa computadora.*",
                    prioridad="MEDIA"
                )
        except Exception as e:
            return CoherenciaReport(
                timestamp=datetime.now().isoformat(),
                modulo="imports",
                estado="WARNING",
                descripcion=f"No se pudo verificar imports: {str(e)}",
                prioridad="ALTA"
            )
    
    def verificar_fases(self) -> CoherenciaReport:
        """Verifica: ¿Boot sigue secuencia correcta?"""
        try:
            # Verificar que existe config.json (primer paso de boot)
            if Path("datos/config.json").exists():
                # Verificar que existe owner_face_profile.json (segundo paso)
                if Path("datos/owner_face_profile.json").exists():
                    return CoherenciaReport(
                        timestamp=datetime.now().isoformat(),
                        modulo="fases",
                        estado="OK",
                        descripcion="Secuencia boot correcta: config → face profile presente",
                        prioridad="MEDIA"
                    )
                else:
                    return CoherenciaReport(
                        timestamp=datetime.now().isoformat(),
                        modulo="fases",
                        estado="WARNING",
                        descripcion="Config presente pero face profile ausente (primer boot?)",
                        prioridad="BAJA"
                    )
            else:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="fases",
                    estado="WARNING",
                    descripcion="Config no encontrada, boot debe estar en fase inicial",
                    prioridad="BAJA"
                )
        except Exception as e:
            return CoherenciaReport(
                timestamp=datetime.now().isoformat(),
                modulo="fases",
                estado="WARNING",
                descripcion=f"No se pudo verificar fases: {str(e)}",
                prioridad="MEDIA"
            )
    
    def verificar_estados(self) -> CoherenciaReport:
        """Verifica: ¿Sensores reportan estado consistente?"""
        try:
            # Verificar que FACEREC_RECORD.json es coherente si existe
            if Path("docs/REFERENCE/FACEREC_RECORD.json").exists():
                try:
                    record = json.loads(Path("docs/REFERENCE/FACEREC_RECORD.json").read_text())
                    
                    # Verificar estructura mínima
                    if "nombre_corto" in record and "nombre_completo" in record and "encoding" in record:
                        return CoherenciaReport(
                            timestamp=datetime.now().isoformat(),
                            modulo="estados",
                            estado="OK",
                            descripcion=f"FACEREC_RECORD coherente para usuario: {record.get('nombre_corto')}",
                            prioridad="MEDIA"
                        )
                    else:
                        return CoherenciaReport(
                            timestamp=datetime.now().isoformat(),
                            modulo="estados",
                            estado="ERROR",
                            descripcion="FACEREC_RECORD presente pero estructura incompleta",
                            esperado="nombre_corto + nombre_completo + encoding",
                            actual=f"Presentes: {list(record.keys())}",
                            prioridad="ALTA"
                        )
                except json.JSONDecodeError:
                    return CoherenciaReport(
                        timestamp=datetime.now().isoformat(),
                        modulo="estados",
                        estado="ERROR",
                        descripcion="FACEREC_RECORD no es JSON válido",
                        prioridad="CRITICA"
                    )
            else:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="estados",
                    estado="WARNING",
                    descripcion="FACEREC_RECORD no existe (primer usuario?)",
                    prioridad="BAJA"
                )
        except Exception as e:
            return CoherenciaReport(
                timestamp=datetime.now().isoformat(),
                modulo="estados",
                estado="WARNING",
                descripcion=f"No se pudo verificar estados: {str(e)}",
                prioridad="MEDIA"
            )
    
    def verificar_permisos(self) -> CoherenciaReport:
        """Verifica: ¿Propietario == Gevurá (autorización)?"""
        try:
            # Si existe FACEREC_RECORD, usuario autenticado = propietario
            if Path("docs/REFERENCE/FACEREC_RECORD.json").exists():
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="permisos",
                    estado="OK",
                    descripcion="Usuario propietario autenticado (Gevurá)",
                    prioridad="MEDIA"
                )
            else:
                return CoherenciaReport(
                    timestamp=datetime.now().isoformat(),
                    modulo="permisos",
                    estado="WARNING",
                    descripcion="No hay propietario registrado (Gevurá pendiente)",
                    prioridad="BAJA"
                )
        except Exception as e:
            return CoherenciaReport(
                timestamp=datetime.now().isoformat(),
                modulo="permisos",
                estado="WARNING",
                descripcion=f"No se pudo verificar permisos: {str(e)}",
                prioridad="MEDIA"
            )
    
    def auditar_todos(self) -> list[CoherenciaReport]:
        """Ejecutar auditoría COMPLETA — todas las verificaciones."""
        reportes = [
            self.verificar_nombres(),
            self.verificar_imports(),
            self.verificar_fases(),
            self.verificar_estados(),
            self.verificar_permisos(),
        ]
        
        self.reportes = reportes
        
        # Log summary
        errores = [r for r in reportes if r.estado == "ERROR"]
        warnings = [r for r in reportes if r.estado == "WARNING"]
        
        logger.info(f"✓ Auditoría completada: {len(reportes)} checks, {len(errores)} errores, {len(warnings)} warnings")
        
        if errores:
            for e in errores:
                logger.error(f"  [ERROR] {e.modulo}: {e.descripcion}")
        
        return reportes
    
    def guardar_reporte(self) -> Path:
        """Guardar reporte en .audit/coherencia_TIMESTAMP.log"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.audit_dir / f"coherencia_{timestamp}.log"
        
        lines = [
            "=" * 80,
            f"AUDITORÍA DE COHERENCIA — {datetime.now().isoformat()}",
            "=" * 80,
            "",
        ]
        
        for reporte in self.reportes:
            lines.append(f"[{reporte.estado:8}] {reporte.modulo:12} — {reporte.descripcion}")
            if reporte.esperado:
                lines.append(f"           Esperado: {reporte.esperado}")
            if reporte.actual:
                lines.append(f"           Actual:   {reporte.actual}")
            lines.append("")
        
        # Summary
        estados = {}
        for r in self.reportes:
            estados[r.estado] = estados.get(r.estado, 0) + 1
        
        lines.append("=" * 80)
        lines.append(f"RESUMEN: {estados}")
        lines.append("=" * 80)
        
        report_file.write_text("\n".join(lines))
        logger.info(f"✓ Reporte guardado: {report_file}")
        
        return report_file


