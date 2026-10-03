"""
FP-145 WI-XXX: Gilgul Audit Logging — Registro de decisiones de consentimiento facial.

Sefirá: GEVURÁ (Registro/Juicio) + MALKUTH (Manifestación registrada)
Alquimia: RUBEDO (Manifestación = Auditoría permanente)

Registra TODAS las decisiones de Gilgul (consentimiento facial) en archivo JSONL.
Formato: Una línea JSON por decisión, timestamp + decisión + resultado.
"""

from pathlib import Path
from datetime import datetime
import json
import hashlib
from typing import Literal
from loguru import logger


class RegistroConsentimientoFacial:
    """
    Registra decisiones de Gilgul en JSONL para auditoría y debugging.
    
    Archivo: datos/GILGUL_AUDIT.jsonl (una línea JSON por decisión)
    
    Estructura por línea:
    {
        "timestamp": "2025-04-23T12:05:30.123456",
        "decision": "continue|session_skip|always_skip|cancelled",
        "resultado": "success|timeout|error",
        "detalles": "mensaje de resultado",
        "user_hash": "sha256_hash_del_usuario",
        "session_id": "id_unico_de_sesion",
        "version": "1.0"
    }
    """
    
    # Archivo JSONL para auditoría
    AUDIT_FILE = Path(__file__).resolve().parent.parent.parent / "datos" / "GILGUL_AUDIT.jsonl"
    
    # Tipos de decisión
    DECISION_CONTINUE = "continue"
    DECISION_SESSION_SKIP = "session_skip"
    DECISION_ALWAYS_SKIP = "always_skip"
    DECISION_CANCELLED = "cancelled"
    
    # Resultados
    RESULTADO_SUCCESS = "success"
    RESULTADO_TIMEOUT = "timeout"
    RESULTADO_ERROR = "error"
    RESULTADO_SKIPPED = "skipped"
    
    def __init__(self, session_id: str = ""):
        """Inicializa auditoría con un ID de sesión único."""
        self.session_id = session_id or self._generar_session_id()
        self.user_hash = self._generar_user_hash()
        logger.info(f"RegistroConsentimientoFacial: Sesión {self.session_id} iniciada")
    
    def registrar_decision(
        self,
        decision: Literal["continue", "session_skip", "always_skip", "cancelled"],
        resultado: Literal["success", "timeout", "error", "skipped"] = "success",
        detalles: str = ""
    ) -> bool:
        """
        Registra una decisión de Gilgul en el audit trail.
        
        Args:
            decision: Tipo de decisión tomada por el usuario
            resultado: Resultado de la acción (success/error/etc)
            detalles: Mensaje adicional de contexto
        
        Returns:
            True si se registró exitosamente, False si hubo error
        """
        try:
            # Crear directorio de datos si no existe
            self.AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear entrada de auditoría
            entrada = {
                "timestamp": datetime.now().isoformat(timespec="microseconds"),
                "decision": decision,
                "resultado": resultado,
                "detalles": detalles,
                "user_hash": self.user_hash,
                "session_id": self.session_id,
                "version": "1.0"
            }
            
            # Escribir línea JSON al archivo (append mode)
            with open(self.AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
            
            logger.info(
                f"RegistroConsentimientoFacial: Registrado decision={decision} resultado={resultado}"
            )
            return True
        
        except Exception as e:
            logger.error(f"RegistroConsentimientoFacial: Error registrando decisión: {e}")
            return False
    
    def registrar_facial_registration_suceso(self, nombre_corto: str, nombre_completo: str) -> bool:
        """Registra que el registro facial fue exitoso."""
        return self.registrar_decision(
            decision=self.DECISION_CONTINUE,
            resultado=self.RESULTADO_SUCCESS,
            detalles=f"Facial registration exitoso: {nombre_corto} ({nombre_completo})"
        )
    
    def registrar_facial_registration_error(self, error_msg: str) -> bool:
        """Registra que hubo error en registro facial."""
        return self.registrar_decision(
            decision=self.DECISION_CONTINUE,
            resultado=self.RESULTADO_ERROR,
            detalles=f"Facial registration error: {error_msg}"
        )
    
    def registrar_session_skip(self, razon: str = "Usuario eligió saltarla esta sesión") -> bool:
        """Registra que fue saltada solo esta sesión."""
        return self.registrar_decision(
            decision=self.DECISION_SESSION_SKIP,
            resultado=self.RESULTADO_SUCCESS,
            detalles=razon
        )
    
    def registrar_always_skip(self, razon: str = "Usuario eligió siempre saltarla") -> bool:
        """Registra que fue guardada preferencia de siempre saltarla."""
        return self.registrar_decision(
            decision=self.DECISION_ALWAYS_SKIP,
            resultado=self.RESULTADO_SUCCESS,
            detalles=razon
        )
    
    def registrar_dialog_cancelled(self) -> bool:
        """Registra que dialog fue cerrado sin decisión."""
        return self.registrar_decision(
            decision=self.DECISION_CANCELLED,
            resultado=self.RESULTADO_SKIPPED,
            detalles="Dialog cerrado sin decisión"
        )
    
    def registrar_preferencia_guardada(self) -> bool:
        """Registra que se encontró preferencia guardada, se saltó dialog."""
        return self.registrar_decision(
            decision=self.DECISION_ALWAYS_SKIP,
            resultado=self.RESULTADO_SKIPPED,
            detalles="Preferencia 'siempre saltarla' encontrada, dialog saltado"
        )
    
    @staticmethod
    def _generar_session_id() -> str:
        """Genera un ID único para esta sesión."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    @staticmethod
    def _generar_user_hash() -> str:
        """Genera hash del usuario actual (privacidad)."""
        import getpass
        username = getpass.getuser()
        return hashlib.sha256(username.encode()).hexdigest()[:16]
    
    @staticmethod
    def obtener_estadisticas() -> dict:
        """
        Lee el archivo JSONL y retorna estadísticas agregadas.
        
        Returns:
            Dict con conteos por decision/resultado
        """
        if not RegistroConsentimientoFacial.AUDIT_FILE.exists():
            return {
                "total_registros": 0,
                "decisiones": {},
                "resultados": {}
            }
        
        try:
            decisiones = {}
            resultados = {}
            total = 0
            
            with open(RegistroConsentimientoFacial.AUDIT_FILE, "r", encoding="utf-8") as f:
                for linea in f:
                    if linea.strip():
                        try:
                            entrada = json.loads(linea)
                            total += 1
                            
                            # Contar decisiones
                            dec = entrada.get("decision", "unknown")
                            decisiones[dec] = decisiones.get(dec, 0) + 1
                            
                            # Contar resultados
                            res = entrada.get("resultado", "unknown")
                            resultados[res] = resultados.get(res, 0) + 1
                        except json.JSONDecodeError:
                            pass
            
            return {
                "total_registros": total,
                "decisiones": decisiones,
                "resultados": resultados,
                "archivo": str(RegistroConsentimientoFacial.AUDIT_FILE)
            }
        except Exception as e:
            logger.error(f"RegistroConsentimientoFacial: Error leyendo estadísticas: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generar_reporte_auditoria() -> str:
        """Genera un reporte formateado de la auditoría."""
        stats = RegistroConsentimientoFacial.obtener_estadisticas()
        
        reporte = "╔════════════════════════════════════════════════════════════╗\n"
        reporte += "║ AUDITORÍA GILGUL — Registro de Decisiones de Consentimiento ║\n"
        reporte += "╚════════════════════════════════════════════════════════════╝\n\n"
        
        if stats.get("error"):
            return reporte + f"Error: {stats['error']}\n"
        
        reporte += f"Total registros: {stats['total_registros']}\n"
        reporte += f"Archivo: {stats.get('archivo', 'No encontrado')}\n\n"
        
        if stats['decisiones']:
            reporte += "DECISIONES:\n"
            reporte += "───────────────────────────────────────────────────────────\n"
            for decision, count in sorted(stats['decisiones'].items()):
                reporte += f"  {decision:20s}: {count:3d}\n"
        
        if stats['resultados']:
            reporte += "\nRESULTADOS:\n"
            reporte += "───────────────────────────────────────────────────────────\n"
            for resultado, count in sorted(stats['resultados'].items()):
                reporte += f"  {resultado:20s}: {count:3d}\n"
        
        return reporte


# Instancia global
_registro_global = None

def obtener_registro_consentimiento(session_id: str = "") -> RegistroConsentimientoFacial:
    """Obtiene o crea la instancia global de auditoría."""
    global _registro_global
    if _registro_global is None:
        _registro_global = RegistroConsentimientoFacial(session_id)
    return _registro_global

def reiniciar_registro_consentimiento(session_id: str = "") -> RegistroConsentimientoFacial:
    """Reinicia la instancia de auditoría (para nuevas sesiones)."""
    global _registro_global
    _registro_global = RegistroConsentimientoFacial(session_id)
    return _registro_global


