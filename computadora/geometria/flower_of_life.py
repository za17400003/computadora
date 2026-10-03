"""
FLOR DE LA VIDA — Optimización de Recursos
===========================================

Implementa la Flor de la Vida (19 círculos, empaquetamiento hexagonal).
Optimiza distribución de recursos usando razón áurea Φ.

Estructura:
- 19 círculos (1 central + 6 primera capa + 12 segunda capa)
- Empaquetamiento hexagonal: máxima densidad, mínimo desperdicio
- Ratio Φ: proporción áurea para balance natural

Uso:
    flower = FlowerOfLife()
    flower.balance_recursos(cpu_pct=75, ram_pct=62, net_pct=45)
    items_optimizados = flower.hexagonal_packing(items_list)
"""

import logging
from typing import List, Any, Tuple

logger = logging.getLogger(__name__)


class FlowerOfLife:
    """
    Optimizador de recursos usando geometría sagrada.
    Mantiene recursos en balance Φ (proporción áurea).
    """
    
    PHI = 1.618033988749895  # Proporción áurea
    CIRCULOS = 19  # 1 + 6 + 12
    
    def __init__(self):
        """Inicializa la Flor de la Vida"""
        self.phi = self.PHI
        self.circulos = self.CIRCULOS
        
        logger.info(f"✓ Flor de la Vida inicializada (Φ={self.phi:.6f})")
    
    def balance_recursos(self, cpu_pct: float, ram_pct: float, net_pct: float) -> Tuple[bool, dict]:
        """
        Mantiene recursos en balance usando razón áurea.
        
        Ideal:
        - RAM ≈ CPU / Φ
        - NET ≈ (CPU + RAM) * Φ / 5
        
        Args:
            cpu_pct: CPU usage percentage
            ram_pct: RAM usage percentage
            net_pct: Network usage percentage
        
        Returns:
            (is_balanced, adjustment_dict)
        """
        # Calcular ideales
        ideal_ram = cpu_pct / self.phi
        ideal_net = (cpu_pct + ram_pct) * self.phi / 5
        
        # Tolerancia: ±10%
        tolerancia = 0.1
        
        ram_ok = abs(ram_pct - ideal_ram) <= (ideal_ram * tolerancia)
        net_ok = abs(net_pct - ideal_net) <= (ideal_net * tolerancia)
        cpu_ok = cpu_pct < 90  # CPU no debe superar 90%
        
        is_balanced = ram_ok and net_ok and cpu_ok
        
        adjustments = {
            'cpu': {'actual': cpu_pct, 'ok': cpu_ok},
            'ram': {'actual': ram_pct, 'ideal': ideal_ram, 'ok': ram_ok},
            'net': {'actual': net_pct, 'ideal': ideal_net, 'ok': net_ok},
            'phi_ratio': self.phi,
        }
        
        if is_balanced:
            logger.debug(f"✓ Recursos en balance Φ (CPU:{cpu_pct}% RAM:{ram_pct}% NET:{net_pct}%)")
        else:
            logger.warning(f"⚠ Recursos desbalanceados - reajuste requerido")
            for resource, status in adjustments.items():
                if resource != 'phi_ratio' and not status.get('ok', True):
                    logger.debug(f"  {resource}: {status}")
        
        return is_balanced, adjustments
    
    def hexagonal_packing(self, items: List[Any]) -> List[Any]:
        """
        Empaqueta items usando estructura hexagonal (Flor de la Vida).
        Ordena por relevancia manteniendo máxima densidad.
        
        Args:
            items: Lista de items a empaquetar
        
        Returns:
            Items reordenados en patrón hexagonal
        """
        if not items:
            return items
        
        # Simplificada: agrupar en ciclos hexagonales
        # Estructura: 1 central + 6 en círculo 1 + 12 en círculo 2
        
        packed = []
        
        # Separar items por "prioridad" (puede ser atributo o índice)
        if len(items) <= 1:
            return items
        elif len(items) <= 7:
            # Cabe en primer ciclo
            packed.append(items[0])  # Centro
            packed.extend(items[1:7])  # Perímetro 1
            packed.extend(items[7:])  # Perímetro 2 (si hay)
        else:
            # Llena estructura completa
            packed.append(items[0])  # Centro
            packed.extend(items[1:7])  # 6 en círculo 1
            packed.extend(items[7:19])  # 12 en círculo 2
            packed.extend(items[19:])  # Overflow (si hay)
        
        logger.debug(f"✓ {len(items)} items empaquetados en patrón hexagonal")
        return packed
    
    def ratio_optimo(self, recurso_a: float) -> float:
        """
        Calcula el ratio óptimo para otro recurso manteniendo Φ.
        """
        return recurso_a * self.phi
    
    def densidad_hexagonal(self, area: float) -> int:
        """
        Calcula cuántos items caben en un área dado empaquetamiento hexagonal.
        """
        # Aproximación: 0.9069 es densidad máxima de círculos en hexágono
        MAX_DENSITY = 0.9069
        return int(area * MAX_DENSITY)
    
    def diagnosticar_balance(self, cpu: float, ram: float, net: float) -> str:
        """
        Diagnóstico detallado del balance de recursos.
        """
        is_balanced, adjustments = self.balance_recursos(cpu, ram, net)
        
        report = "FLOR DE LA VIDA — Balance de Recursos\n"
        report += f"Estado: {'✓ BALANCEADO' if is_balanced else '⚠ DESBALANCEADO'}\n"
        report += f"Proporción áurea (Φ): {self.phi:.6f}\n\n"
        
        report += f"CPU: {cpu:.1f}% {'✓' if adjustments['cpu']['ok'] else '⚠'}\n"
        report += f"RAM: {ram:.1f}% (ideal: {adjustments['ram']['ideal']:.1f}%) {'✓' if adjustments['ram']['ok'] else '⚠'}\n"
        report += f"NET: {net:.1f}% (ideal: {adjustments['net']['ideal']:.1f}%) {'✓' if adjustments['net']['ok'] else '⚠'}\n"
        
        return report


