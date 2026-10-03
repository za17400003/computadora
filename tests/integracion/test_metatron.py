"""
Tests para geometría Metatrón.
FP-139 RUBEDO FASE 5: Validación de integridad geométrica.
"""

import math
import pytest
from computadora.geometria.metatron import (
    Punto3D,
    MetatronCube,
    Merkaba,
    FlowerOfLife,
    GeometriaComputadora,
)


class TestPunto3D:
    """Tests para clase Punto3D."""
    
    def test_distancia_a_origen(self):
        """Punto a origen debe ser su magnitud."""
        p = Punto3D(3, 4, 0)
        assert abs(p.distancia_a(Punto3D(0, 0, 0)) - 5.0) < 0.001
    
    def test_distancia_entre_puntos(self):
        """Distancia entre dos puntos."""
        p1 = Punto3D(0, 0, 0)
        p2 = Punto3D(1, 1, 1)
        expected = math.sqrt(3)
        assert abs(p1.distancia_a(p2) - expected) < 0.001
    
    def test_normalizar(self):
        """Vector normalizado tiene magnitud 1."""
        p = Punto3D(3, 4, 0)
        pn = p.normalizar()
        magnitud = pn.distancia_a(Punto3D(0, 0, 0))
        assert abs(magnitud - 1.0) < 0.001
    
    def test_normalizar_cero(self):
        """Normalizar vector cero retorna cero."""
        p = Punto3D(0, 0, 0)
        pn = p.normalizar()
        assert pn.x == 0 and pn.y == 0 and pn.z == 0


class TestMetatronCube:
    """Tests para Cubo de Metatrón."""
    
    def test_inicializacion(self):
        """Cubo inicializa correctamente."""
        cube = MetatronCube(tamaño=100)
        assert cube.tamaño == 100
        assert len(cube.vertices) == 9  # 8 del cubo + 1 centro
        assert len(cube.aristas) == 12  # 12 aristas del cubo
    
    def test_vertices_en_rango(self):
        """Vértices están dentro del tamaño."""
        cube = MetatronCube(tamaño=200)
        for v in cube.vertices:
            dist = v.distancia_a(Punto3D(0, 0, 0))
            assert dist <= 200/2 + 1  # margen pequeño
    
    def test_validar_coherencia_particulas_validas(self):
        """Partículas dentro del cubo son válidas."""
        cube = MetatronCube(tamaño=200)
        particulas = [(0, 0, 0), (10, 10, 10), (-20, 20, -20)]
        assert cube.validar_coherencia(particulas) == True
    
    def test_validar_coherencia_particulas_invalidas(self):
        """Partículas fuera del cubo son inválidas."""
        cube = MetatronCube(tamaño=100)
        particulas = [(500, 500, 500)]  # Muy lejos
        assert cube.validar_coherencia(particulas) == False


class TestMerkaba:
    """Tests para Merkaba."""
    
    def test_inicializacion(self):
        """Merkaba inicializa sin protección."""
        merkaba = Merkaba(radio=50)
        assert merkaba.radio == 50
        assert merkaba.spin_rate == 0
        assert merkaba.protegido == False
    
    def test_activar_proteccion(self):
        """Activar protección aumenta spin rate."""
        merkaba = Merkaba()
        merkaba.activar_proteccion(60)
        assert merkaba.spin_rate == 60
        assert merkaba.protegido == True
    
    def test_desactivar_proteccion(self):
        """Desactivar protección detiene spin."""
        merkaba = Merkaba()
        merkaba.activar_proteccion(60)
        merkaba.desactivar_proteccion()
        assert merkaba.spin_rate == 0
        assert merkaba.protegido == False
    
    def test_actualizar_rotacion(self):
        """Actualizar avanza rotación."""
        merkaba = Merkaba()
        merkaba.activar_proteccion(60)  # 60 RPM = 1 RPS = 2π rad/s
        
        rot_inicial = merkaba.rotacion_actual
        merkaba.actualizar(1.0)  # 1 segundo
        rot_final = merkaba.rotacion_actual
        
        # Debe haber rotado ~2π radianes (una vuelta)
        assert rot_final > rot_inicial
    
    def test_vertices_tetraedro(self):
        """Tetraedro retorna 4 vértices."""
        merkaba = Merkaba(radio=50)
        vertices = merkaba.obtener_vertices_tetraedro_up()
        assert len(vertices) == 4
        
        # Todos a distancia similar del origen
        dists = [v.distancia_a(Punto3D(0, 0, 0)) for v in vertices]
        for d in dists:
            assert abs(d - 50*math.sqrt(3)) < 10  # con tolerancia


class TestFlowerOfLife:
    """Tests para Flor de la Vida."""
    
    def test_inicializacion(self):
        """Flor inicializa con 19 círculos."""
        flor = FlowerOfLife(radio_circulo=30)
        assert len(flor.centros) == 19
    
    def test_ciclos(self):
        """Flor tiene 3 ciclos."""
        flor = FlowerOfLife()
        assert flor.obtener_ciclos() == 3
    
    def test_validar_ciclo_valido(self):
        """Fases dentro de ciclos son válidas."""
        flor = FlowerOfLife()
        assert flor.validar_ciclo(0.0) == True   # Inicio crecimiento
        assert flor.validar_ciclo(0.33) == True  # Fin crecimiento
        assert flor.validar_ciclo(0.5) == True   # Medio completitud
        assert flor.validar_ciclo(1.0) == True   # Fin ciclo
    
    def test_centros_en_patron(self):
        """Centros forman patrón válido."""
        flor = FlowerOfLife(radio_circulo=30)
        # Centro en origen
        assert (0, 0) in flor.centros
        # Otros centros en rango esperado
        for x, y in flor.centros[1:]:
            dist = math.hypot(x, y)
            assert dist <= 30 * 4  # radio máximo ~120


class TestGeometriaComputadora:
    """Tests para gestor integrado."""
    
    def test_inicializacion(self):
        """Geometría inicializa correctamente."""
        geom = GeometriaComputadora()
        assert geom.cubo is not None
        assert geom.merkaba is not None
        assert geom.flor is not None
        assert geom.fase_ciclo == 0.0
    
    def test_validar_tzimtzum(self):
        """En Tzimtzum, merkaba debe estar inactivo."""
        geom = GeometriaComputadora()
        geom.merkaba.activar_proteccion()  # Merkaba activo
        
        # Validar Tzimtzum con Merkaba activo → False
        resultado = geom.validar_integridad("tzimtzum")
        assert resultado == False
    
    def test_validar_guardian(self):
        """En Guardian, merkaba se activa automáticamente."""
        geom = GeometriaComputadora()
        geom.merkaba.desactivar_proteccion()  # Merkaba inactivo
        
        # Validar Guardian con Merkaba inactivo → auto-activa
        resultado = geom.validar_integridad("guardian")
        assert resultado == True
        assert geom.merkaba.protegido == True
    
    def test_actualizar_ciclo(self):
        """Actualizar avanza fase de ciclo."""
        geom = GeometriaComputadora()
        fase_inicial = geom.fase_ciclo
        
        geom.actualizar(1.0)  # 1 segundo
        fase_final = geom.fase_ciclo
        
        assert fase_final > fase_inicial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

