"""
WI-298: Geometrías Platónicas — Transmutación Dinámica del Orbe

Mapeo de estados computacionales a sólidos platónicos:
- ESCUCHAR (idle): Esfera (perfecta, receptiva)
- SUGERIR: Tetraedro (fuego, iniciativa)
- PROCESAR: Cubo (tierra, estabilidad)
- VER (facial): Octaedro (aire, visión)
- EJECUTAR (herramienta): Dodecaedro (síntesis de propósitos)
- CPU↑: Icosaedro (complejidad máxima)
"""

import math
from enum import Enum
from typing import Tuple, List
from dataclasses import dataclass
from loguru import logger


class SolidoPlatonico(Enum):
    """Estados de transmutación del Orbe."""
    ESFERA = "esfera"
    TETRAEDRO = "tetraedro"
    CUBO = "cubo"
    OCTAEDRO = "octaedro"
    DODECAEDRO = "dodecaedro"
    ICOSAEDRO = "icosaedro"


@dataclass
class Vertice3D:
    """Punto 3D (para renderización futura)."""
    x: float
    y: float
    z: float
    
    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


class GeneradorGeometrias:
    """Genera vértices y aristas de sólidos platónicos."""
    
    @staticmethod
    def generar_esfera(radio: float = 100, subdivisions: int = 12) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Genera aproximación de esfera (icosaedro subdividido)."""
        vertices = []
        aristas = []
        
        # Golden ratio
        phi = (1 + math.sqrt(5)) / 2
        
        # 12 vértices del icosaedro base
        coords = [
            (-1,  phi, 0), (1,  phi, 0), (-1, -phi, 0), (1, -phi, 0),
            (0, -1,  phi), (0,  1,  phi), (0, -1, -phi), (0,  1, -phi),
            (phi, 0, -1), (phi, 0,  1), (-phi, 0, -1), (-phi, 0,  1),
        ]
        
        for x, y, z in coords:
            # Normalizar y escalar
            norma = math.sqrt(x**2 + y**2 + z**2)
            vertices.append(Vertice3D(x/norma*radio, y/norma*radio, z/norma*radio))
        
        # Aristas del icosaedro (30 aristas)
        aristas_indices = [
            (0, 1), (0, 5), (0, 11), (1, 5), (1, 9), (1, 7),
            (2, 3), (2, 6), (2, 10), (3, 4), (3, 9), (3, 6),
            (4, 5), (4, 9), (4, 10), (5, 11), (6, 7), (6, 10),
            (7, 8), (7, 11), (8, 9), (8, 10), (8, 11), (2, 4),
            (2, 11), (3, 10), (4, 11), (5, 9), (6, 9), (7, 10),
        ]
        
        return vertices, aristas_indices
    
    @staticmethod
    def generar_tetraedro(radio: float = 100) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Tetraedro regular — 4 vértices, 6 aristas."""
        h = 2 * math.sqrt(2) / 3
        vertices = [
            Vertice3D(0, radio, 0),
            Vertice3D(radio * math.sqrt(8/9), -radio/3, 0),
            Vertice3D(-radio * math.sqrt(2/9), -radio/3, radio * math.sqrt(2/3)),
            Vertice3D(-radio * math.sqrt(2/9), -radio/3, -radio * math.sqrt(2/3)),
        ]
        aristas = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        return vertices, aristas
    
    @staticmethod
    def generar_cubo(radio: float = 100) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Cubo — 8 vértices, 12 aristas."""
        r = radio / math.sqrt(3)
        coords = [
            (r, r, r), (r, r, -r), (r, -r, r), (r, -r, -r),
            (-r, r, r), (-r, r, -r), (-r, -r, r), (-r, -r, -r),
        ]
        vertices = [Vertice3D(x, y, z) for x, y, z in coords]
        aristas = [
            (0, 1), (0, 2), (0, 4), (1, 3), (1, 5),
            (2, 3), (2, 6), (3, 7), (4, 5), (4, 6),
            (5, 7), (6, 7),
        ]
        return vertices, aristas
    
    @staticmethod
    def generar_octaedro(radio: float = 100) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Octaedro — 6 vértices, 12 aristas."""
        vertices = [
            Vertice3D(radio, 0, 0), Vertice3D(-radio, 0, 0),
            Vertice3D(0, radio, 0), Vertice3D(0, -radio, 0),
            Vertice3D(0, 0, radio), Vertice3D(0, 0, -radio),
        ]
        aristas = [
            (0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3),
            (1, 4), (1, 5), (2, 4), (2, 5), (3, 4), (3, 5),
        ]
        return vertices, aristas
    
    @staticmethod
    def generar_dodecaedro(radio: float = 100) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Dodecaedro — 20 vértices, 30 aristas."""
        phi = (1 + math.sqrt(5)) / 2
        inv_phi = 1 / phi
        
        # 20 vértices del dodecaedro
        # Combinaciones de (+-1, +-1, +-1) -> 8 vertices
        coords = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    coords.append((sx, sy, sz))
        
        # (0, +-inv_phi, +-phi) -> 4 vertices
        for sy in (-1, 1):
            for sz in (-1, 1):
                coords.append((0, sy * inv_phi, sz * phi))
        
        # (+-inv_phi, +-phi, 0) -> 4 vertices
        for sx in (-1, 1):
            for sy in (-1, 1):
                coords.append((sx * inv_phi, sy * phi, 0))
        
        # (+-phi, 0, +-inv_phi) -> 4 vertices
        for sx in (-1, 1):
            for sz in (-1, 1):
                coords.append((sx * phi, 0, sz * inv_phi))
        
        # Normalizar y escalar
        vertices = []
        for x, y, z in coords:
            norma = math.sqrt(x**2 + y**2 + z**2)
            vertices.append(Vertice3D(
                x / norma * radio,
                y / norma * radio,
                z / norma * radio,
            ))
        
        # Aristas (adjacencia entre vertices del dodecaedro)
        # Usamos distancia euclidiana para determinar adjacencia
        aristas = []
        for i in range(len(vertices)):
            for j in range(i + 1, len(vertices)):
                dist = math.sqrt(
                    (vertices[i].x - vertices[j].x)**2 +
                    (vertices[i].y - vertices[j].y)**2 +
                    (vertices[i].z - vertices[j].z)**2
                )
                # Si los vertices estan a distancia de arista
                edge_dist = 2.0 * radio / math.sqrt(3)  # Distancia entre vertices del dodecaedro
                if abs(dist - edge_dist) < 1.0:
                    aristas.append((i, j))
        
        return vertices, aristas
    
    @staticmethod
    def generar_icosaedro(radio: float = 100) -> Tuple[List[Vertice3D], List[Tuple[int, int]]]:
        """Icosaedro — 12 vértices, 30 aristas."""
        return GeneradorGeometrias.generar_esfera(radio, subdivisions=1)


class TransmutadorOrbe:
    """Controla transmutación dinámica del Orbe a sólidos platónicos."""
    
    MAPEO_ESTADOS = {
        "idle": SolidoPlatonico.ESFERA,
        "escuchando": SolidoPlatonico.ESFERA,
        "sugiriendo": SolidoPlatonico.TETRAEDRO,
        "procesando": SolidoPlatonico.CUBO,
        "viendo": SolidoPlatonico.OCTAEDRO,
        "ejecutando": SolidoPlatonico.DODECAEDRO,
        "cpu_alta": SolidoPlatonico.ICOSAEDRO,
    }
    
    def __init__(self):
        self.solido_actual = SolidoPlatonico.ESFERA
        self.vertices_cache: List[Vertice3D] = []
        self.aristas_cache: List[Tuple[int, int]] = []
        self.progreso_transmutacion = 0.0  # 0.0-1.0
        self.generador = GeneradorGeometrias()
        logger.info("🔮 TransmutadorOrbe inicializado (Esfera)")
    
    def obtener_solido_para_estado(self, estado: str) -> SolidoPlatonico:
        """Mapea estado de Computadora a sólido platónico."""
        return self.MAPEO_ESTADOS.get(estado, SolidoPlatonico.ESFERA)
    
    def transmutar_a(self, nuevo_estado: str, duracion_animacion: float = 0.5) -> None:
        """Inicia transmutación a nuevo sólido."""
        nuevo_solido = self.obtener_solido_para_estado(nuevo_estado)
        if nuevo_solido == self.solido_actual:
            return
        
        logger.info(f"✨ Transmutación: {self.solido_actual.value} → {nuevo_solido.value} ({duracion_animacion}s)")
        self.solido_actual = nuevo_solido
        self.progreso_transmutacion = 0.0
        
        # Generar vértices del nuevo sólido
        if nuevo_solido == SolidoPlatonico.ESFERA:
            self.vertices_cache, self.aristas_cache = self.generador.generar_esfera()
        elif nuevo_solido == SolidoPlatonico.TETRAEDRO:
            self.vertices_cache, self.aristas_cache = self.generador.generar_tetraedro()
        elif nuevo_solido == SolidoPlatonico.CUBO:
            self.vertices_cache, self.aristas_cache = self.generador.generar_cubo()
        elif nuevo_solido == SolidoPlatonico.OCTAEDRO:
            self.vertices_cache, self.aristas_cache = self.generador.generar_octaedro()
        elif nuevo_solido == SolidoPlatonico.DODECAEDRO:
            self.vertices_cache, self.aristas_cache = self.generador.generar_dodecaedro()
        elif nuevo_solido == SolidoPlatonico.ICOSAEDRO:
            self.vertices_cache, self.aristas_cache = self.generador.generar_icosaedro()
    
    def obtener_vertices(self) -> List[Vertice3D]:
        """Retorna vértices actuales."""
        return self.vertices_cache
    
    def obtener_aristas(self) -> List[Tuple[int, int]]:
        """Retorna aristas actuales."""
        return self.aristas_cache


import numpy as np


# WI-309 a WI-313: Tipos y funciones exportables para nucleo atomico

@dataclass
class PlatonicSolid:
    """Representacion de un solido platonico con sus vertices como numpy array."""
    nombre: str
    vertices: np.ndarray  # shape (N, 3)
    aristas: List[Tuple[int, int]]


_SOLIDOS_CACHE = {}


def get_solid(nombre: str) -> PlatonicSolid | None:
    """Obtiene un solido platonico por nombre.
    
    Args:
        nombre: 'tetrahedron', 'cube', 'octahedron', 'dodecahedron', 'icosahedron'
    
    Returns:
        PlatonicSolid con vertices como numpy array, o None si no existe.
    """
    if nombre in _SOLIDOS_CACHE:
        return _SOLIDOS_CACHE[nombre]
    
    gen = GeneradorGeometrias()
    radio = 100.0
    
    if nombre == 'tetrahedron':
        verts, aristas = gen.generar_tetraedro(radio)
    elif nombre == 'cube':
        verts, aristas = gen.generar_cubo(radio)
    elif nombre == 'octahedron':
        verts, aristas = gen.generar_octaedro(radio)
    elif nombre == 'dodecahedron':
        verts, aristas = gen.generar_dodecaedro(radio)
    elif nombre == 'icosahedron':
        verts, aristas = gen.generar_icosaedro(radio)
    else:
        return None
    
    vertices_array = np.array([[v.x, v.y, v.z] for v in verts])
    solido = PlatonicSolid(nombre=nombre, vertices=vertices_array, aristas=aristas)
    _SOLIDOS_CACHE[nombre] = solido
    return solido


# Lista de todos los solidos disponibles
SOLIDOS_PLATONICOS = ['tetrahedron', 'cube', 'octahedron', 'dodecahedron', 'icosahedron']


