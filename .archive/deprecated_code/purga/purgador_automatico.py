"""Purgador Automático — Ejecuta limpieza de contradicciones.

Responsabilidad:
  - Ejecutar DetectorContradicciones
  - Limpiar automáticamente según acción_sugerida
  - Reportar qué se limpió y por qué
  - Registrar cambios para auditoría (revertible)
"""

import shutil
from datetime import datetime
from pathlib import Path
from loguru import logger
from computadora.purga.detector_contradicciones import (
    DetectorContradicciones,
    Contradiccion,
)


class RegistroPurga:
    """Registro de operaciones de purga (para reversión futura)."""
    
    def __init__(self, timestamp: str, archivo: str, accion: str, razon: str):
        self.timestamp = timestamp
        self.archivo = archivo
        self.accion = accion  # "borrado" | "consolidado" | "marcado"
        self.razon = razon
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "archivo": self.archivo,
            "accion": self.accion,
            "razon": self.razon,
        }


class PurgadorAutomatico:
    """Ejecuta limpieza automática de contradicciones."""
    
    def __init__(self, audit_dir: str = ".audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(exist_ok=True)
        self.detector = DetectorContradicciones()
        self.operaciones: list[RegistroPurga] = []
        logger.info("PurgadorAutomatico inicializado")
    
    def purgar_todos(self, dry_run: bool = False) -> tuple[int, int]:
        """Ejecutar purga COMPLETA.
        
        Args:
            dry_run: Si True, solo reportar sin ejecutar
        
        Returns:
            (cantidad_operaciones, errores)
        """
        contradicciones = self.detector.detectar_todos()
        
        operaciones = 0
        errores = 0
        
        for c in contradicciones:
            try:
                if c.accion_sugerida == "borrar":
                    if not dry_run:
                        self._borrar_archivo(c)
                    operaciones += 1
                    
                elif c.accion_sugerida == "consolidar":
                    if not dry_run:
                        self._consolidar(c)
                    operaciones += 1
                    
                elif c.accion_sugerida == "revisar":
                    # Solo marcar, no borrar
                    logger.warning(f"REVISAR MANUAL: {c.descripcion}")
                    operaciones += 1
                    
            except Exception as e:
                logger.error(f"Error purgando {c.ubicacion}: {e}")
                errores += 1
        
        if dry_run:
            logger.info(f"[DRY RUN] Hubiera purgado: {operaciones} items, {errores} errores")
        else:
            logger.info(f"✓ Purga completada: {operaciones} items limpiados, {errores} errores")
        
        self.guardar_reporte()
        
        return operaciones, errores
    
    def _borrar_archivo(self, contradiccion: Contradiccion):
        """Borrar archivo marcado."""
        path = Path(contradiccion.ubicacion)
        
        if not path.exists():
            logger.warning(f"Archivo ya no existe: {path}")
            return
        
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            
            logger.info(f"✓ Borrado: {path}")
            
            operacion = RegistroPurga(
                timestamp=datetime.now().isoformat(),
                archivo=str(path),
                accion="borrado",
                razon=contradiccion.descripcion
            )
            self.operaciones.append(operacion)
            
        except Exception as e:
            logger.error(f"No se pudo borrar {path}: {e}")
            raise
    
    def _consolidar(self, contradiccion: Contradiccion):
        """Consolidar duplicados (ej: encoding facial)."""
        logger.info(f"⚠ CONSOLIDACIÓN PENDIENTE MANUAL: {contradiccion.descripcion}")
        logger.info(f"  Ubicación: {contradiccion.ubicacion}")
        
        operacion = RegistroPurga(
            timestamp=datetime.now().isoformat(),
            archivo=contradiccion.ubicacion,
            accion="marcado_consolidacion_pendiente",
            razon=contradiccion.descripcion
        )
        self.operaciones.append(operacion)
    
    def guardar_reporte(self):
        """Guardar reporte en .audit/purga_TIMESTAMP.log"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.audit_dir / f"purga_{timestamp}.log"
        
        lines = [
            "=" * 80,
            f"REPORTE DE PURGA — {datetime.now().isoformat()}",
            "=" * 80,
            "",
        ]
        
        if self.operaciones:
            for op in self.operaciones:
                lines.append(f"[{op.accion:30}] {op.archivo}")
                lines.append(f"  Razón: {op.razon}")
                lines.append("")
        else:
            lines.append("(No hay operaciones registradas)")
        
        lines.append("=" * 80)
        
        report_file.write_text("\n".join(lines))
        logger.info(f"✓ Reporte guardado: {report_file}")


