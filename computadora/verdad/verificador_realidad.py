"""Verificador de Realidad — EMET viva en tiempo de ejecución.

Verifica:
  1. ¿Coinciden sensor + API en interpretación?
  2. ¿Reporta usuario algo que contradice realidad?
  3. ¿Es el dato verificable o es DUDA?
  4. Si incoherencia: bloquear acción, reportar verdad
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from loguru import logger


@dataclass
class VerificacionResultado:
    """Resultado de verificación de verdad."""
    timestamp: str
    aseveracion: str  # "Usuario es Propietario" | "Lluvia detectada" etc
    estado: str  # "VERDAD" | "FALSO" | "DUDA"
    confianza: float  # 0.0-1.0
    evidencia: list[str]  # ["sensor A dice X", "API B dice Y"]
    bloqueante: bool  # Si True, acción debe bloquearse
    razon_bloqueo: Optional[str] = None


class VerificadorRealidad:
    """Verificador de verdad en runtime."""
    
    def __init__(self, audit_dir: str = ".audit"):
        self.audit_dir = audit_dir
        self.verificaciones: list[VerificacionResultado] = []
        logger.info("VerificadorRealidad inicializado")
    
    # Mismo umbral que computadora/percepcion/rostro.py (_UMBRAL_PROPIETARIO).
    # Debe mantenerse sincronizado: ambos comparan la misma distancia de encoding facial.
    UMBRAL_DISTANCIA_PROPIETARIO = 0.50

    def verificar_usuario_propietario(self, usuario_id: str, distancia_facial: float) -> VerificacionResultado:
        """Verificar: ¿Es el usuario realmente el propietario?

        Fuentes de verdad:
          1. Distancia de encoding facial (rostro.py, face_recognition.face_distance;
             MENOR distancia = mejor coincidencia — NO es una confianza)
          2. datos/owner_face_profile.json tiene un perfil registrado

        Args:
            usuario_id: identificador del usuario detectado.
            distancia_facial: distancia de encoding devuelta por rostro.py
                (rango típico 0.0-1.0, <= UMBRAL_DISTANCIA_PROPIETARIO = coincide).
        """
        from pathlib import Path

        confianza = 1.0 - min(max(distancia_facial, 0.0), 1.0)
        evidencia = [f"Distancia de encoding facial: {distancia_facial:.2f} (confianza: {confianza:.2f})"]

        perfil_file = Path("datos/owner_face_profile.json")

        if not perfil_file.exists():
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Usuario {usuario_id} es propietario",
                estado="DUDA",
                confianza=0.5,
                evidencia=evidencia + ["owner_face_profile.json no existe (posible primer boot, sin enrolamiento)"],
                bloqueante=False,
            )
        elif distancia_facial <= self.UMBRAL_DISTANCIA_PROPIETARIO:
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Usuario {usuario_id} es propietario",
                estado="VERDAD",
                confianza=confianza,
                evidencia=evidencia + [f"Distancia <= {self.UMBRAL_DISTANCIA_PROPIETARIO} (coincide)"],
                bloqueante=False,
            )
        else:
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Usuario {usuario_id} es propietario",
                estado="FALSO",
                confianza=confianza,
                evidencia=evidencia + [f"Distancia > {self.UMBRAL_DISTANCIA_PROPIETARIO} (no coincide)"],
                bloqueante=True,
                razon_bloqueo="Face match insuficiente — rechazar como propietario",
            )

        self.verificaciones.append(resultado)
        return resultado
    
    def verificar_estado_sensor(self, sensor_tipo: str, valor_reportado: float, 
                                valor_esperado: float, tolerancia: float = 0.1) -> VerificacionResultado:
        """Verificar: ¿Es el valor del sensor consistente con expectativa?
        
        Args:
            sensor_tipo: "temperatura" | "humedad" | "luz" etc
            valor_reportado: Lo que dice el sensor
            valor_esperado: Lo que esperamos (ej: 25°C normal ambiente)
            tolerancia: Rango aceptable (ej: ±0.1 = ±10%)
        """
        diferencia = abs(valor_reportado - valor_esperado)
        max_diferencia = valor_esperado * tolerancia if valor_esperado != 0 else tolerancia
        
        if diferencia <= max_diferencia:
            estado = "VERDAD"
            bloqueante = False
        else:
            estado = "FALSO"
            bloqueante = True  # Anomalía en sensor = acción debe bloquearse
        
        confianza = 1.0 - min(diferencia / max_diferencia, 1.0) if max_diferencia > 0 else 1.0
        
        resultado = VerificacionResultado(
            timestamp=datetime.now().isoformat(),
            aseveracion=f"Sensor {sensor_tipo} reporta {valor_reportado}",
            estado=estado,
            confianza=confianza,
            evidencia=[
                f"Valor reportado: {valor_reportado}",
                f"Valor esperado: {valor_esperado}",
                f"Diferencia: {diferencia:.2f} (tolerancia: {max_diferencia:.2f})"
            ],
            bloqueante=bloqueante,
            razon_bloqueo=f"Anomalía en sensor {sensor_tipo}: diferencia {diferencia:.2f} > tolerancia" 
                          if bloqueante else None
        )
        
        self.verificaciones.append(resultado)
        return resultado
    
    def guardar_verificaciones(self):
        """Guardar log de verificaciones."""
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(self.audit_dir) / f"verdad_{timestamp}.log"
        
        lines = [
            "=" * 80,
            f"LOG DE VERIFICACIONES DE VERDAD — {datetime.now().isoformat()}",
            "=" * 80,
            "",
        ]
        
        bloqueantes = [v for v in self.verificaciones if v.bloqueante]
        
        for v in self.verificaciones:
            icon = "✓" if v.estado == "VERDAD" else "✗" if v.estado == "FALSO" else "?"
            lines.append(f"[{icon} {v.estado:6}] {v.aseveracion}")
            lines.append(f"    Confianza: {v.confianza:.2f} | Bloqueante: {v.bloqueante}")
            for ev in v.evidencia:
                lines.append(f"    • {ev}")
            if v.razon_bloqueo:
                lines.append(f"    ⚠️  BLOQUEO: {v.razon_bloqueo}")
            lines.append("")
        
        if bloqueantes:
            lines.append("=" * 80)
            lines.append(f"⚠️ {len(bloqueantes)} VERIFICACIONES BLOQUEANTES")
            lines.append("=" * 80)
        
        report_file.write_text("\n".join(lines))
        logger.info(f"✓ Verificaciones guardadas: {report_file}")


