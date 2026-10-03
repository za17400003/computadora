"""
FP-139 RUBEDO FASE 5: Integración de Geometría Sagrada — Metatrón.

Validación geométrica + protección + ciclos naturales.
Basado en METATRON_CITRINITAS_PROPUESTA.md
"""

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from loguru import logger


@dataclass
class Punto3D:
    """Punto en espacio 3D."""
    x: float
    y: float
    z: float
    
    def distancia_a(self, otro: "Punto3D") -> float:
        """Calcula distancia euclidiana a otro punto."""
        return math.sqrt((self.x - otro.x)**2 + (self.y - otro.y)**2 + (self.z - otro.z)**2)
    
    def normalizar(self) -> "Punto3D":
        """Retorna vector normalizado."""
        d = self.distancia_a(Punto3D(0, 0, 0))
        if d < 0.0001:
            return Punto3D(0, 0, 0)
        return Punto3D(self.x / d, self.y / d, self.z / d)


class MetatronCube:
    """
    Cubo de Metatrón — Validador de coherencia geométrica.
    
    Contiene los 5 sólidos platónicos. Valida que partículas/comportamientos
    respeten simetría fundamental.
    """
    
    def __init__(self, tamaño: float = 100.0):
        self.tamaño = tamaño
        self.vertices = self._generar_vertices()
        self.aristas = self._generar_aristas()
    
    def _generar_vertices(self) -> List[Punto3D]:
        """Genera 13 vértices del Cubo de Metatrón (Sólidos Platónicos).
        
        FP-156: 13 esferas = 8 cubo + 4 tetraedro + 1 centro
        """
        t = self.tamaño / 2.0
        phi = (1.0 + math.sqrt(5.0)) / 2.0  # Proporción áurea
        
        # 8 vértices del cubo
        vertices = [
            Punto3D(-t, -t, -t), Punto3D(t, -t, -t),
            Punto3D(t, t, -t), Punto3D(-t, t, -t),
            Punto3D(-t, -t, t), Punto3D(t, -t, t),
            Punto3D(t, t, t), Punto3D(-t, t, t),
        ]
        
        # 4 vértices del tetraedro estelado (icosaedro interior)
        r = t * 0.618  # Sección áurea
        tetra = [
            Punto3D(r, r, r), Punto3D(r, -r, -r),
            Punto3D(-r, r, -r), Punto3D(-r, -r, r),
        ]
        vertices.extend(tetra)
        
        # 1 vértice centro 
        vertices.append(Punto3D(0, 0, 0))
        
        return vertices
    
    def _generar_aristas(self) -> List[Tuple[int, int]]:
        """Genera 53 líneas del Cubo de Metatrón.
        
        FP-156: 12 cubo + 24 cuadrados internos + 12 estrella + 5 radiales = 53
        """
        aristas = []
        
        # 12 aristas del cubo exterior (índices 0-7)
        cubo = [
            (0,1), (1,2), (2,3), (3,0),  # base
            (4,5), (5,6), (6,7), (7,4),  # techo
            (0,4), (1,5), (2,6), (3,7),  # verticales
        ]
        aristas.extend(cubo)
        
        # 24 aristas: cada vertice del cubo -> cada vertice del tetraedro (8*4/2=16 únicas)
        tetra_inds = [8, 9, 10, 11]
        for i in range(8):
            for j in tetra_inds:
                aristas.append((i, j))
        
        # Centro (índice 12) -> cada vertice del cubo (8) + tetraedro (4) = 12
        for i in range(12):
            aristas.append((i, 12))
        
        return list(set(aristas))  # Eliminar duplicados
    
    def obtener_vertices_numpy(self) -> np.ndarray:
        """Retorna vértices como array numpy (para OpenGL)."""
        return np.array([[v.x, v.y, v.z] for v in self.vertices], dtype=np.float32)
    
    def obtener_aristas_pares(self) -> np.ndarray:
        """Retorna aristas como pares de índices numpy."""
        return np.array(self.aristas, dtype=np.int32)
    
    def validar_coherencia(self, particulas: List[Tuple[float, float, float]]) -> bool:
        """
        Valida que partículas respeten simetría del cubo.
        
        Retorna True si coherente, False si hay anomalías.
        """
        if not particulas:
            return True
        
        # Verificación simple: distancia máxima debe ser <= tamaño
        for x, y, z in particulas:
            dist = math.hypot(math.hypot(x, y), z)
            if dist > self.tamaño / 2.0 + 10:  # margen de tolerancia
                logger.warning(f"Partícula fuera de cubo: dist={dist:.2f} > {self.tamaño/2+10:.2f}")
                return False
        
        return True


class Merkaba:
    """
    Merkaba — Vehículo de luz + protección.
    
    Dos tetraedros interpenetrados (uno up, uno down) = spinner de protección.
    Spin rate = velocidad de rotación (RPM).
    """
    
    def __init__(self, radio: float = 50.0, spin_rate: float = 0.0):
        self.radio = radio
        self.spin_rate = spin_rate  # Revoluciones por minuto
        self.rotacion_actual = 0.0  # Radianes (0-2π)
        self.protegido = False
    
    def activar_proteccion(self, spin_rate: float = 60.0):
        """Inicia spinner de protección."""
        self.spin_rate = spin_rate
        self.protegido = True
        logger.info(f"Merkaba protección ACTIVADA: {spin_rate} RPM")
    
    def desactivar_proteccion(self):
        """Detiene spinner."""
        self.spin_rate = 0.0
        self.protegido = False
        logger.info("Merkaba protección desactivada")
    
    def actualizar(self, delta_tiempo: float):
        """Actualiza rotación basado en delta tiempo (segundos)."""
        if self.spin_rate > 0:
            # Calcular radianes por segundo
            rad_por_seg = (self.spin_rate / 60.0) * 2 * math.pi
            self.rotacion_actual = (self.rotacion_actual + rad_por_seg * delta_tiempo) % (2 * math.pi)
    
    def obtener_vertices_tetraedro_up(self) -> List[Punto3D]:
        """Vértices del tetraedro ascendente rotado."""
        cos_r = math.cos(self.rotacion_actual)
        sin_r = math.sin(self.rotacion_actual)
        
        vertices_base = [
            Punto3D(1, 1, 1),
            Punto3D(1, -1, -1),
            Punto3D(-1, 1, -1),
            Punto3D(-1, -1, 1),
        ]
        
        # Rotar alrededor de Z
        rotados = []
        for v in vertices_base:
            x_nuevo = v.x * cos_r - v.y * sin_r
            y_nuevo = v.x * sin_r + v.y * cos_r
            z_nuevo = v.z
            rotados.append(Punto3D(x_nuevo * self.radio, y_nuevo * self.radio, z_nuevo * self.radio))
        
        return rotados


class FlowerOfLife:
    """
    Flor de la Vida — Patrón de ciclos naturales.
    
    19 círculos solapados. Representa crecimiento, completitud, ciclos.
    """
    
    def __init__(self, radio_circulo: float = 30.0):
        self.radio_circulo = radio_circulo
        self.centros = self._generar_centros()
    
    def _generar_centros(self) -> List[Tuple[float, float]]:
        """Genera posiciones de 19 círculos de la Flor de la Vida."""
        centros = []
        # 1 círculo central
        centros.append((0, 0))
        
        # 6 círculos alrededor (hexágono)
        for i in range(6):
            ang = (2 * math.pi * i) / 6
            x = self.radio_circulo * 2 * math.cos(ang)
            y = self.radio_circulo * 2 * math.sin(ang)
            centros.append((x, y))
        
        # 12 círculos en segunda onda
        for i in range(12):
            ang = (2 * math.pi * i) / 12
            radio_onda2 = self.radio_circulo * 3.5
            x = radio_onda2 * math.cos(ang)
            y = radio_onda2 * math.sin(ang)
            centros.append((x, y))
        
        return centros
    
    def obtener_ciclos(self) -> int:
        """Retorna número de ciclos (siempre 3 para Flor de la Vida)."""
        return 3
    
    def validar_ciclo(self, fase_actual: float) -> bool:
        """
        Valida si la fase actual (0.0-1.0) es válida en ciclo natural.
        
        Retorna True si coherente con ritmo natural.
        """
        # Fases naturales del ciclo: crecimiento, completitud, descanso
        fases_validas = [
            (0.0, 0.33),    # Crecimiento (Yesod)
            (0.33, 0.66),   # Completitud (Tiféret)
            (0.66, 1.0),    # Descanso (Maljut)
        ]
        
        for inicio, fin in fases_validas:
            if inicio <= fase_actual <= fin:
                return True
        
        return False


class GeometriaComputadora:
    """
    Gestor integrado de geometría sagrada.
    
    Coordina Metatrón + Merkaba + Flor de la Vida.
    """
    
    def __init__(self):
        self.cubo = MetatronCube(tamaño=200.0)
        self.merkaba = Merkaba(radio=50.0)
        self.flor = FlowerOfLife(radio_circulo=30.0)
        self.fase_ciclo = 0.0  # 0.0-1.0
    
    def validar_integridad(self, estado_orbe: str) -> bool:
        """
        Validación geométrica integral.
        
        Retorna True si todo coherente.
        """
        # Validación simple: según estado
        if estado_orbe == "tzimtzum":
            # En Tzimtzum, merkaba debe estar inactivo
            if self.merkaba.protegido:
                logger.warning("Inconsistencia: Tzimtzum pero Merkaba activo")
                return False
        
        elif estado_orbe == "guardian":
            # En Guardian, merkaba debe estar activo
            if not self.merkaba.protegido:
                logger.warning("Inconsistencia: Guardian pero Merkaba inactivo")
                # Auto-corrección
                self.merkaba.activar_proteccion()
        
        return True
    
    def actualizar(self, delta_tiempo: float):
        """Actualiza estado de geometría (rotaciones, ciclos)."""
        self.merkaba.actualizar(delta_tiempo)
        
        # Actualizar fase de ciclo (Flor de la Vida)
        self.fase_ciclo = (self.fase_ciclo + delta_tiempo * 0.1) % 1.0


