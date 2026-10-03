"""Colector de Feedback — Captura experiencia del usuario en vivo.

Tipos de feedback capturados:
  1. Usuario explícito: "Eso fue útil" / "Eso fue inútil"
  2. Sistema implícito: latencia, precisión, errores
  3. Sensores: confianza de reconocimiento, calidad de audio
  4. Uso: qué features se usan, cuáles no
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from loguru import logger


@dataclass
class EventoFeedback:
    """Evento atómico de feedback."""
    timestamp: str
    tipo: str  # "usuario_explícito" | "sistema_implícito" | "sensor" | "uso"
    descripcion: str
    valor: Any  # 1.0=excelente, 0.0=pésimo, etc
    modulo_origen: Optional[str] = None
    usuario_id: Optional[str] = None
    contexto: Optional[dict] = None  # datos adicionales


class ColectorFeedback:
    """Captor de feedback en vivo."""
    
    def __init__(self, feedback_file: str = ".audit/feedback.json", max_eventos: int = 1000):
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(exist_ok=True)
        self.max_eventos = max_eventos
        self.eventos: list[EventoFeedback] = []
        self._cargar_feedback()
        logger.info(f"ColectorFeedback inicializado ({len(self.eventos)} eventos previos)")
    
    def _cargar_feedback(self):
        """Cargar feedback del archivo (rolling window últimas N)."""
        if not self.feedback_file.exists():
            self.eventos = []
            return
        
        try:
            datos = json.loads(self.feedback_file.read_text())
            # Mantener solo últimas max_eventos
            self.eventos = [EventoFeedback(**e) for e in datos[-self.max_eventos:]]
        except Exception as e:
            logger.warning(f"No se pudo cargar feedback previo: {e}")
            self.eventos = []
    
    def registrar_usuario_explicito(self, descripcion: str, valor: float, modulo: str, usuario_id: str):
        """Registrar feedback explícito del usuario."""
        evento = EventoFeedback(
            timestamp=datetime.now().isoformat(),
            tipo="usuario_explícito",
            descripcion=descripcion,
            valor=valor,  # 1.0 = útil, 0.0 = inútil
            modulo_origen=modulo,
            usuario_id=usuario_id,
        )
        self.eventos.append(evento)
        self._guardar()
    
    def registrar_sistema_implicito(self, descripcion: str, latencia_ms: float, precision: float, modulo: str):
        """Registrar feedback implícito del sistema."""
        # Feedback basado en latencia: >2000ms = malo
        valor_latencia = 1.0 - min(latencia_ms / 2000.0, 1.0)
        valor_total = (valor_latencia + precision) / 2.0
        
        evento = EventoFeedback(
            timestamp=datetime.now().isoformat(),
            tipo="sistema_implícito",
            descripcion=descripcion,
            valor=valor_total,
            modulo_origen=modulo,
            contexto={"latencia_ms": latencia_ms, "precision": precision}
        )
        self.eventos.append(evento)
        self._guardar()
    
    def registrar_sensor(self, descripcion: str, confianza: float, sensor: str):
        """Registrar feedback de sensores."""
        evento = EventoFeedback(
            timestamp=datetime.now().isoformat(),
            tipo="sensor",
            descripcion=descripcion,
            valor=confianza,  # 0.0-1.0
            modulo_origen=f"sensor_{sensor}",
        )
        self.eventos.append(evento)
        self._guardar()
    
    def registrar_uso(self, descripcion: str, feature: str, usado: bool):
        """Registrar uso de features."""
        evento = EventoFeedback(
            timestamp=datetime.now().isoformat(),
            tipo="uso",
            descripcion=descripcion,
            valor=1.0 if usado else 0.0,
            modulo_origen=feature,
            contexto={"usado": usado}
        )
        self.eventos.append(evento)
        self._guardar()
    
    def _guardar(self):
        """Guardar feedback en archivo."""
        if len(self.eventos) > self.max_eventos:
            self.eventos = self.eventos[-self.max_eventos:]
        
        datos = [asdict(e) for e in self.eventos]
        self.feedback_file.write_text(json.dumps(datos, indent=2))


