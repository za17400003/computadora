"""Reportador de Auditoría — Ejecuta auditoría periódicamente.

Responsabilidad:
  - Ejecutar VerificadorCoherencia cada N segundos
  - Guardar reportes en .audit/
  - Alertar si hay incoherencias CRÍTICAS
"""

import threading
import time
from loguru import logger
from computadora.auditoria.verificador_coherencia import VerificadorCoherencia


class ReportadorAuditoria:
    """Ejecutor periódico de auditorías."""
    
    def __init__(self, intervalo_segundos: int = 60, audit_dir: str = ".audit"):
        self.intervalo = intervalo_segundos
        self.verificador = VerificadorCoherencia(audit_dir=audit_dir)
        self.thread: threading.Thread | None = None
        self.activo = False
        logger.info(f"ReportadorAuditoria inicializado (intervalo: {intervalo_segundos}s)")
    
    def iniciar(self):
        """Iniciar auditoría periódica en thread daemon."""
        if self.activo:
            logger.warning("Auditoría ya activa")
            return
        
        self.activo = True
        self.thread = threading.Thread(
            target=self._loop_auditoria,
            daemon=True,
            name="ReportadorAuditoria"
        )
        self.thread.start()
        logger.info("✓ Auditoría periódica iniciada")
    
    def detener(self):
        """Detener auditoría periódica."""
        self.activo = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("✓ Auditoría periódica detenida")
    
    def _loop_auditoria(self):
        """Loop interno: ejecutar auditoría cada N segundos."""
        contador = 0
        while self.activo:
            try:
                contador += 1
                reportes = self.verificador.auditar_todos()
                
                # Guardar cada 10 auditorías
                if contador % 10 == 0:
                    self.verificador.guardar_reporte()
                
                # Alertar si hay CRÍTICA
                criticas = [r for r in reportes if r.prioridad == "CRITICA"]
                if criticas:
                    logger.critical(f"⚠ {len(criticas)} incoherencias CRÍTICAS detectadas")
                    for c in criticas:
                        logger.critical(f"  → {c.modulo}: {c.descripcion}")
                
                time.sleep(self.intervalo)
            except Exception as e:
                logger.error(f"Error en loop de auditoría: {e}")
                time.sleep(self.intervalo)


# Singleton global
_reportador: ReportadorAuditoria | None = None


def obtener_reportador(intervalo: int = 60) -> ReportadorAuditoria:
    """Obtener o crear reportador global."""
    global _reportador
    if _reportador is None:
        _reportador = ReportadorAuditoria(intervalo_segundos=intervalo)
    return _reportador


def iniciar_auditoria():
    """Iniciar auditoría periódica (llamar en boot)."""
    reportador = obtener_reportador()
    reportador.iniciar()


def detener_auditoria():
    """Detener auditoría periódica (llamar en shutdown)."""
    global _reportador
    if _reportador:
        _reportador.detener()


