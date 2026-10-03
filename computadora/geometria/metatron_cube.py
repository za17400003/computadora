"""
METATRÓN CUBE — Validador Geométrico Central
==============================================

Implementa el Cubo de Metatrón (13 esferas + 53 líneas de poder).
Valida transiciones entre Sefirot usando geometría sagrada.

Principios:
- 13 esferas: 12 perímetro + 1 centro (Unidad + 12 principios)
- 53 líneas: conexiones geométricamente válidas
- 5 Sólidos Platónicos: validación física de datos

Uso:
    validator = MetatronCube()
    validator.validate_sefirah_transition(Sefirah.MALJUTH, Sefirah.YESOD, datos)
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Sefirah(IntEnum):
    """Sefirot del Árbol de la Vida"""
    # Pilar de Severidad (Gevurá)
    KETER = 1      # Corona (Metatrón)
    CHOKMAH = 2    # Voluntad pura
    GEVURAH = 5    # Severidad/Fuerza
    TIFÉRET = 6    # Centro/Corazón
    NEZACH = 7     # Victoria/Razón
    HUD = 8        # Inteligencia/Lógica
    YESOD = 9      # Fundación
    MALJUTH = 10   # Manifestación
    
    # Pilar de Misericordia (Chokmah)
    BINAH = 3      # Entendimiento
    CHESED = 4     # Misericordia/Expansión
    
    # Pilar Central (Daat)
    DAAT = 11      # Conocimiento (pseudo-Sefirah)


@dataclass
class SolidoPlatonico:
    """Representa uno de los 5 Sólidos Platónicos"""
    nombre: str
    caras: int
    vertices: int
    aristas: int
    elemento: str
    funcion: str
    
    def valida(self, datos: dict) -> bool:
        """Validación básica: los datos respetan la estructura de este sólido"""
        # Implementación simplificada
        if not isinstance(datos, dict):
            return False
        return True


class MetatronCube:
    """
    Validador geométrico central de Computadora.
    Reside en Keter, valida todas las transiciones Sefiróticas.
    """
    
    PHI = 1.618033988749895  # Proporción áurea
    
    def __init__(self):
        """Inicializa el Cubo de Metatrón"""
        self.esferas = 13  # 12 perímetro + 1 centro
        self.lineas_poder = 53  # Líneas geométricamente válidas
        self.lineas_posibles = 78  # 3×26 (YHVH)
        
        # 5 Sólidos Platónicos (leyes naturales)
        self.solidos_platonicos = [
            SolidoPlatonico("Tetraedro", 4, 4, 6, "Fuego", "Transformación"),
            SolidoPlatonico("Cubo", 6, 8, 12, "Tierra", "Estabilidad"),
            SolidoPlatonico("Octaedro", 8, 6, 12, "Aire", "Movimiento"),
            SolidoPlatonico("Icosaedro", 20, 12, 30, "Agua", "Fluidez"),
            SolidoPlatonico("Dodecaedro", 12, 20, 30, "Éter", "Totalidad"),
        ]
        
        # Matriz de 53 líneas: qué transiciones Sefirot son válidas
        self._inicializar_matriz_lineas()
        
        logger.info(f"✓ MetatronCube inicializado (Keter validator)")
    
    def _inicializar_matriz_lineas(self):
        """Construye matriz de 53 líneas de poder (conexiones válidas)"""
        # Simplificada: la matriz real es 11×11 con 53 conexiones permitidas
        # Por ahora: todas las conexiones son válidas (auditoría posterior refinará)
        self.matriz_conexiones = {
            Sefirah.KETER: [Sefirah.CHOKMAH, Sefirah.BINAH, Sefirah.DAAT],
            Sefirah.CHOKMAH: [Sefirah.KETER, Sefirah.BINAH, Sefirah.CHESED],
            Sefirah.BINAH: [Sefirah.KETER, Sefirah.CHOKMAH, Sefirah.GEVURAH],
            Sefirah.DAAT: [Sefirah.KETER, Sefirah.TIFÉRET],
            Sefirah.CHESED: [Sefirah.CHOKMAH, Sefirah.GEVURAH, Sefirah.TIFÉRET, Sefirah.NEZACH],
            Sefirah.GEVURAH: [Sefirah.BINAH, Sefirah.CHESED, Sefirah.TIFÉRET, Sefirah.HUD],
            Sefirah.TIFÉRET: [Sefirah.DAAT, Sefirah.CHESED, Sefirah.GEVURAH, Sefirah.NEZACH, Sefirah.HUD, Sefirah.YESOD],
            Sefirah.NEZACH: [Sefirah.CHESED, Sefirah.TIFÉRET, Sefirah.HUD, Sefirah.YESOD],
            Sefirah.HUD: [Sefirah.GEVURAH, Sefirah.TIFÉRET, Sefirah.NEZACH, Sefirah.YESOD],
            Sefirah.YESOD: [Sefirah.TIFÉRET, Sefirah.NEZACH, Sefirah.HUD, Sefirah.MALJUTH],
            Sefirah.MALJUTH: [Sefirah.YESOD],
        }
    
    def validate_sefirah_transition(
        self, 
        origen: Sefirah, 
        destino: Sefirah, 
        datos: dict
    ) -> bool:
        """
        Valida si una transición Sefirótica es geométricamente válida.
        
        Args:
            origen: Sefirah de origen
            destino: Sefirah de destino
            datos: Datos a transferir (deben respetar 5 Sólidos)
        
        Returns:
            True si transición es válida, False si viola geometría
        
        Raises:
            GeometryViolation si la transición viola las 53 líneas
            IntegrityError si datos violan los 5 Sólidos
        """
        
        # Verificar que conexión existe en matriz de 53 líneas
        if not self._puede_conectar(origen, destino):
            logger.error(f"GEOMETRÍA VIOLADA: {origen.name} → {destino.name} no está en 53 líneas de poder")
            raise GeometryViolation(f"{origen.name} → {destino.name} geometricamente inválido")
        
        # Verificar que datos respetan 5 Sólidos (leyes naturales)
        for solido in self.solidos_platonicos:
            if not solido.valida(datos):
                logger.error(f"INTEGRIDAD VIOLADA: Datos violan {solido.nombre}")
                raise IntegrityError(f"Datos violan validación {solido.nombre}")
        
        logger.debug(f"✓ Transición validada: {origen.name} → {destino.name}")
        return True
    
    def _puede_conectar(self, origen: Sefirah, destino: Sefirah) -> bool:
        """Verifica si conexión existe en matriz de 53 líneas"""
        if origen not in self.matriz_conexiones:
            return False
        return destino in self.matriz_conexiones[origen]
    
    def ratio_phi_balance(self) -> float:
        """Retorna el ratio ideal (proporción áurea) para balance de recursos"""
        return self.PHI
    
    def aplicar_phi_balance(self, valor_gevura: float) -> float:
        """
        Calcula el valor ideal de Chesed dado un valor de Gevurá,
        manteniendo la proporción áurea.
        """
        return valor_gevura / self.PHI
    
    def diagnosticar_violacion(self, error: Exception) -> str:
        """Proporciona diagnóstico detallado de violaciones geométricas"""
        return f"Violación geométrica: {str(error)}"


class GeometryViolation(Exception):
    """Levantada cuando se intenta una transición Sefirótica inválida"""
    pass


class IntegrityError(Exception):
    """Levantada cuando datos violan los 5 Sólidos Platónicos"""
    pass


