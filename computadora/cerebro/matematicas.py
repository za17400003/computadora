"""
computadora/cerebro/matematicas.py — Iluminación de Cálculos Internos de Computadora

Módulo de Transparencia Matemática (WI-283) — Todos los cálculos internos 
reportan su fórmula, valores y resultado para auditabilidad EMET.

Regla: Toda operación numérica que afecte decisiones dCOMPUTADORA debe dejar
un rastro de "por qué" — matemática iluminada, no caja negra.

"Ilumina a Computadora en sus matemáticas" = hacer visible el razonamiento numérico.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass, asdict
from enum import Enum

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_AUDIT_MAT_DIR = _DATOS_DIR / "auditoria_matematica"
_AUDIT_MAT_DIR.mkdir(parents=True, exist_ok=True)


class TipoOperacion(Enum):
    """Categorización de operaciones matemáticas audibles."""
    RECONOCIMIENTO_FACIAL = "facial_recognition"
    ALERTA_SISTEMA = "system_alert"
    PROACTIVIDAD = "proactivity_score"
    CIRCADIANO = "circadian_phase"
    EMOCIONAL = "emotion_inference"
    VALIDACIÓN_EMET = "emet_validation"


@dataclass
class CalcoAuditado:
    """Registro de una operación matemática con trazabilidad completa."""
    timestamp: str  # ISO format
    tipo_operacion: str  # TipoOperacion.value
    sector: str  # "facial", "monitor_sistema", "motor_proactividad", etc.
    formula: str  # Descripción legible de la fórmula (ej: "||A - B||_2 = distancia euclidiana")
    valores: Dict[str, Any]  # {variable → valor} utilizado en el cálculo
    resultado: Any  # Resultado numérico o booleano
    confianza: float = 1.0  # 0..1 qué tan seguro es este cálculo
    contexto: str = ""  # Notas adicionales (ej: "sin propietario en frame")
    iluminacion_url: str = ""  # Ref a link para ver más detalles (opcional)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a dict para JSON."""
        return asdict(self)


class LogicaTransparente:
    """
    Motor de Auditabilidad Matemática (MAT) — Registra y expone
    el razonamiento numérico de Computadora.
    
    Uso:
        mat = LogicaTransparente()
        distancia = np.linalg.norm(enc1 - enc2)
        mat.registrar_calculo(
            tipo_operacion=TipoOperacion.RECONOCIMIENTO_FACIAL,
            sector="facial",
            formula="||encoding_propietario - encoding_frame||₂",
            valores={"enc_dist": distancia, "umbral": 0.6},
            resultado=distancia < 0.6,  # Es propietario?
            confianza=0.95
        )
        # Luego, si Ollama/usuario pregunta "¿por qué?", recuperamos con:
        razon = mat.obtener_ultimo_razonamiento("facial")
    """
    
    def __init__(self):
        self._calculos: list[CalcoAuditado] = []
        self._calculos_por_sector: Dict[str, list[CalcoAuditado]] = {}
    
    def registrar_calculo(
        self,
        tipo_operacion: TipoOperacion,
        sector: str,
        formula: str,
        valores: Dict[str, Any],
        resultado: Any,
        confianza: float = 1.0,
        contexto: str = "",
    ) -> CalcoAuditado:
        """Registra una operación matemática con trazabilidad."""
        
        calco = CalcoAuditado(
            timestamp=datetime.utcnow().isoformat(),
            tipo_operacion=tipo_operacion.value,
            sector=sector,
            formula=formula,
            valores=valores,
            resultado=resultado,
            confianza=confianza,
            contexto=contexto,
        )
        
        self._calculos.append(calco)
        
        if sector not in self._calculos_por_sector:
            self._calculos_por_sector[sector] = []
        self._calculos_por_sector[sector].append(calco)
        
        logger.debug(
            f"MAT [{sector}]: {formula} → {resultado} (conf={confianza:.2f})"
        )
        
        return calco
    
    def obtener_ultimo_razonamiento(self, sector: str) -> CalcoAuditado | None:
        """Obtiene el último cálculo de un sector para explicación."""
        calculos = self._calculos_por_sector.get(sector, [])
        return calculos[-1] if calculos else None
    
    def obtener_razonamientos(self, sector: str, limit: int = 5) -> list[CalcoAuditado]:
        """Obtiene los últimos N cálculos de un sector."""
        calculos = self._calculos_por_sector.get(sector, [])
        return calculos[-limit:]
    
    def explicar_ultimo(self, sector: str) -> str:
        """Genera texto legible del último razonamiento para Ollama/usuario."""
        calco = self.obtener_ultimo_razonamiento(sector)
        if not calco:
            return f"(No hay cálculos registrados en {sector})"
        
        valores_str = ", ".join(f"{k}={v}" for k, v in calco.valores.items())
        return (
            f"📐 {calco.sector.upper()}: {calco.formula}\n"
            f"   Valores: {valores_str}\n"
            f"   Resultado: {calco.resultado}\n"
            f"   Confianza: {calco.confianza*100:.0f}%"
            f"{f' [{calco.contexto}]' if calco.contexto else ''}"
        )
    
    def exportar_auditoria(self, nombre_archivo: str = None) -> Path:
        """Exporta toda la auditoria matemática a JSON."""
        if nombre_archivo is None:
            nombre_archivo = f"mat_audit_{datetime.utcnow().isoformat()}.json"
        
        audit_path = _AUDIT_MAT_DIR / nombre_archivo
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_calculos": len(self._calculos),
            "por_sector": {
                sector: len(calculos)
                for sector, calculos in self._calculos_por_sector.items()
            },
            "calculos": [c.to_dict() for c in self._calculos[-100:]],  # Últimos 100
        }
        
        audit_path.write_text(
            json.dumps(audit_data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        
        logger.info(f"Auditoria matemática exportada → {audit_path.name}")
        return audit_path
    
    def limpiar_sesion(self):
        """Limpia registros de la sesión actual."""
        self._calculos = []
        self._calculos_por_sector = {}
        logger.debug("Auditoria matemática limpiada")


# ═══════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ═══════════════════════════════════════════════════════════════

_logica_global: LogicaTransparente | None = None


def obtener_logica_transparente() -> LogicaTransparente:
    """Obtiene la instancia global de lógica transparente (singleton)."""
    global _logica_global
    if _logica_global is None:
        _logica_global = LogicaTransparente()
        logger.info("🔬 LogicaTransparente inicializada — Matemáticas iluminadas")
    return _logica_global


# ═══════════════════════════════════════════════════════════════
# HELPERS RÁPIDOS
# ═══════════════════════════════════════════════════════════════

def registrar_facial(
    distancia_euclidiana: float,
    umbral: float,
    es_propietario: bool,
    confianza: float = 0.95,
):
    """Helper: Registra cálculo de reconocimiento facial."""
    mat = obtener_logica_transparente()
    mat.registrar_calculo(
        tipo_operacion=TipoOperacion.RECONOCIMIENTO_FACIAL,
        sector="facial",
        formula="||encoding_frame - encoding_propietario||₂ < umbral",
        valores={"distancia": f"{distancia_euclidiana:.3f}", "umbral": umbral},
        resultado=es_propietario,
        confianza=confianza,
    )


def registrar_alerta_sistema(
    recurso: str,  # "cpu" | "ram" | "disco"
    valor_actual: float,
    umbral: float,
    es_alerta: bool,
    contexto: str = "",
):
    """Helper: Registra cálculo de alerta de sistema."""
    mat = obtener_logica_transparente()
    mat.registrar_calculo(
        tipo_operacion=TipoOperacion.ALERTA_SISTEMA,
        sector="monitor_sistema",
        formula=f"{recurso.upper()} > umbral",
        valores={"valor": valor_actual, "umbral": umbral},
        resultado=es_alerta,
        confianza=0.95,
        contexto=contexto,
    )


def registrar_proactividad(
    tipo_sugerencia: str,
    score: float,
    umbral: float,
    emite: bool,
):
    """Helper: Registra scoring de proactividad."""
    mat = obtener_logica_transparente()
    mat.registrar_calculo(
        tipo_operacion=TipoOperacion.PROACTIVIDAD,
        sector="motor_proactividad",
        formula=f"score({tipo_sugerencia}) > umbral",
        valores={"score": f"{score:.2f}", "umbral": umbral},
        resultado=emite,
        confianza=0.85,
        contexto=f"tipo={tipo_sugerencia}",
    )


