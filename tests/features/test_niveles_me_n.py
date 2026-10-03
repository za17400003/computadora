"""
Tests para la jerarquía fractal ME^N (Niveles 0-4).

Valida que cada nivel de composición se comporta correctamente.
"""

import pytest
from computadora.fundacion import (
    FaseAlquimica,
    Manifestacion,
    Ejecucion,
    NivelComposicion,
    CicloAlquimico,
    IdentidadVacia,
    ComposicionBinaria,
    ComposicionTernaria,
    ComposicionCuaternaria,
    GestorNiveles,
    obtener_gestor_niveles,
)


def crear_ejecucion_exitosa(manifestacion_id: str) -> Ejecucion:
    """Helper: crea una ejecución completada y exitosa."""
    return Ejecucion(
        manifestacion_id=manifestacion_id,
        fases_completadas=frozenset(FaseAlquimica),
        resultado="verde"
    )


class TestNivel0:
    """ME^0 = {ε} — Identidad Vacía"""
    
    def test_identidad_vacia_siempre_completa(self):
        """La identidad vacía siempre está completa (por definición)."""
        epsilon = IdentidadVacia()
        assert epsilon.es_completo()
        assert epsilon.nivel == NivelComposicion.NIVEL_0
    
    def test_identidad_vacia_siempre_exitosa(self):
        """La identidad vacía es siempre exitosa."""
        epsilon = IdentidadVacia()
        assert epsilon.es_exitoso()


class TestNivel1:
    """ME^1 = ME — Un ciclo alquímico único"""
    
    def test_ciclo_sin_ejecucion_no_completo(self):
        """Ciclo sin ejecución no está completo."""
        m = Manifestacion(id="WI-001", nombre="Test", descripcion="", pipeline="C")
        ciclo = CicloAlquimico(manifestacion=m, ejecucion=None)
        
        assert not ciclo.es_completo()
        assert not ciclo.es_exitoso()
        assert ciclo.nivel() == NivelComposicion.NIVEL_1
    
    def test_ciclo_con_ejecucion_exitosa(self):
        """Ciclo con ejecución exitosa es completo y exitoso."""
        m = Manifestacion(id="WI-001", nombre="Test", descripcion="", pipeline="C")
        e = crear_ejecucion_exitosa("WI-001")
        ciclo = CicloAlquimico(manifestacion=m, ejecucion=e)
        
        assert ciclo.es_completo()
        assert ciclo.es_exitoso()
        assert ciclo.nivel() == NivelComposicion.NIVEL_1


class TestNivel2:
    """ME^2 = ME · ME — Composición Binaria (dos ciclos)"""
    
    def test_composicion_binaria_ambos_exitosos(self):
        """Composición binaria: ambos ciclos exitosos → composición exitosa."""
        m1 = Manifestacion(id="WI-291", nombre="Minimi", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-292", nombre="Tests", descripcion="", pipeline="C")
        
        e1 = crear_ejecucion_exitosa("WI-291")
        e2 = crear_ejecucion_exitosa("WI-292")
        
        ciclo_a = CicloAlquimico(manifestacion=m1, ejecucion=e1)
        ciclo_b = CicloAlquimico(manifestacion=m2, ejecucion=e2)
        
        composicion = ComposicionBinaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b)
        
        assert composicion.es_completo()
        assert composicion.es_exitoso()
        assert composicion.nivel() == NivelComposicion.NIVEL_2
    
    def test_composicion_binaria_uno_falla(self):
        """Composición binaria: si uno falla → composición falla."""
        m1 = Manifestacion(id="WI-291", nombre="Minimi", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-292", nombre="Tests", descripcion="", pipeline="C")
        
        e1 = crear_ejecucion_exitosa("WI-291")
        e2 = Ejecucion(
            manifestacion_id="WI-292",
            fases_completadas=frozenset({FaseAlquimica.NIGREDO}),
            resultado="rojo"
        )
        
        ciclo_a = CicloAlquimico(manifestacion=m1, ejecucion=e1)
        ciclo_b = CicloAlquimico(manifestacion=m2, ejecucion=e2)
        
        composicion = ComposicionBinaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b)
        
        assert not composicion.es_completo()
        assert not composicion.es_exitoso()


class TestNivel3:
    """ME^3 = ME · ME · ME — Composición Ternaria (tres ciclos)"""
    
    def test_composicion_ternaria_todos_exitosos(self):
        """Composición ternaria: los tres ciclos exitosos → composición exitosa."""
        m1 = Manifestacion(id="WI-291", nombre="Minimi", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-292", nombre="Tests", descripcion="", pipeline="C")
        m3 = Manifestacion(id="WI-293", nombre="Ollama", descripcion="", pipeline="C")
        
        e1 = crear_ejecucion_exitosa("WI-291")
        e2 = crear_ejecucion_exitosa("WI-292")
        e3 = crear_ejecucion_exitosa("WI-293")
        
        ciclo_a = CicloAlquimico(manifestacion=m1, ejecucion=e1)
        ciclo_b = CicloAlquimico(manifestacion=m2, ejecucion=e2)
        ciclo_c = CicloAlquimico(manifestacion=m3, ejecucion=e3)
        
        composicion = ComposicionTernaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b, ciclo_c=ciclo_c)
        
        assert composicion.es_completo()
        assert composicion.es_exitoso()
        assert composicion.nivel() == NivelComposicion.NIVEL_3
    
    def test_composicion_ternaria_uno_falla(self):
        """Composición ternaria: si uno falla → composición falla."""
        m1 = Manifestacion(id="WI-291", nombre="Minimi", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-292", nombre="Tests", descripcion="", pipeline="C")
        m3 = Manifestacion(id="WI-293", nombre="Ollama", descripcion="", pipeline="C")
        
        e1 = crear_ejecucion_exitosa("WI-291")
        e2 = Ejecucion(
            manifestacion_id="WI-292",
            fases_completadas=frozenset({FaseAlquimica.NIGREDO}),
            resultado="rojo"
        )
        e3 = crear_ejecucion_exitosa("WI-293")
        
        ciclo_a = CicloAlquimico(manifestacion=m1, ejecucion=e1)
        ciclo_b = CicloAlquimico(manifestacion=m2, ejecucion=e2)
        ciclo_c = CicloAlquimico(manifestacion=m3, ejecucion=e3)
        
        composicion = ComposicionTernaria(ciclo_a=ciclo_a, ciclo_b=ciclo_b, ciclo_c=ciclo_c)
        
        assert not composicion.es_completo()
        assert not composicion.es_exitoso()


class TestNivel4:
    """ME^4 = ME · ME · ME · ME — Composición Cuaternaria (cuatro ciclos)"""
    
    def test_composicion_cuaternaria_todos_exitosos(self):
        """Composición cuaternaria: los cuatro ciclos exitosos → composición exitosa."""
        ids = ["WI-A", "WI-B", "WI-C", "WI-D"]
        manifestaciones = [
            Manifestacion(id=mid, nombre=f"Ciclo{i}", descripcion="", pipeline="C")
            for i, mid in enumerate(ids)
        ]
        
        ejecuciones = [crear_ejecucion_exitosa(mid) for mid in ids]
        ciclos = [
            CicloAlquimico(manifestacion=m, ejecucion=e)
            for m, e in zip(manifestaciones, ejecuciones)
        ]
        
        composicion = ComposicionCuaternaria(
            ciclo_a=ciclos[0], ciclo_b=ciclos[1], 
            ciclo_c=ciclos[2], ciclo_d=ciclos[3]
        )
        
        assert composicion.es_completo()
        assert composicion.es_exitoso()
        assert composicion.nivel() == NivelComposicion.NIVEL_4
    
    def test_composicion_cuaternaria_uno_falla(self):
        """Composición cuaternaria: si uno falla → composición falla."""
        ids = ["WI-A", "WI-B", "WI-C", "WI-D"]
        manifestaciones = [
            Manifestacion(id=mid, nombre=f"Ciclo{i}", descripcion="", pipeline="C")
            for i, mid in enumerate(ids)
        ]
        
        ejecuciones = [
            crear_ejecucion_exitosa(mid) if i < 2 else 
            Ejecucion(manifestacion_id=mid, 
                     fases_completadas=frozenset({FaseAlquimica.NIGREDO}), 
                     resultado="rojo")
            for i, mid in enumerate(ids)
        ]
        ciclos = [
            CicloAlquimico(manifestacion=m, ejecucion=e)
            for m, e in zip(manifestaciones, ejecuciones)
        ]
        
        composicion = ComposicionCuaternaria(
            ciclo_a=ciclos[0], ciclo_b=ciclos[1], 
            ciclo_c=ciclos[2], ciclo_d=ciclos[3]
        )
        
        assert not composicion.es_completo()
        assert not composicion.es_exitoso()


class TestGestorNiveles:
    """GestorNiveles — Orquestación de los 5 niveles"""
    
    def test_crear_ciclo_nivel_1(self):
        """Crear y registrar un ciclo en nivel 1."""
        gestor = GestorNiveles()
        m = Manifestacion(id="WI-001", nombre="Test", descripcion="", pipeline="C")
        e = crear_ejecucion_exitosa("WI-001")
        
        ciclo = gestor.crear_ciclo_nivel_1(m, e)
        
        assert ciclo.ciclo_id in gestor.ciclos_nivel_1
        assert ciclo.es_exitoso()
    
    def test_crear_composicion_nivel_2(self):
        """Crear composición binaria."""
        gestor = GestorNiveles()
        
        m1 = Manifestacion(id="WI-A", nombre="A", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-B", nombre="B", descripcion="", pipeline="C")
        
        c1 = gestor.crear_ciclo_nivel_1(m1, crear_ejecucion_exitosa("WI-A"))
        c2 = gestor.crear_ciclo_nivel_1(m2, crear_ejecucion_exitosa("WI-B"))
        
        comp = gestor.crear_composicion_binaria(c1, c2)
        
        assert comp.composicion_id in gestor.composiciones_nivel_2
        assert comp.es_exitoso()
    
    def test_crear_composicion_nivel_3(self):
        """Crear composición ternaria."""
        gestor = GestorNiveles()
        
        ciclos = []
        for i, mid in enumerate(["WI-A", "WI-B", "WI-C"]):
            m = Manifestacion(id=mid, nombre=f"C{i}", descripcion="", pipeline="C")
            ciclos.append(gestor.crear_ciclo_nivel_1(m, crear_ejecucion_exitosa(mid)))
        
        comp = gestor.crear_composicion_ternaria(ciclos[0], ciclos[1], ciclos[2])
        
        assert comp.composicion_id in gestor.composiciones_nivel_3
        assert comp.es_exitoso()
    
    def test_crear_composicion_nivel_4(self):
        """Crear composición cuaternaria."""
        gestor = GestorNiveles()
        
        ciclos = []
        for i, mid in enumerate(["WI-A", "WI-B", "WI-C", "WI-D"]):
            m = Manifestacion(id=mid, nombre=f"C{i}", descripcion="", pipeline="C")
            ciclos.append(gestor.crear_ciclo_nivel_1(m, crear_ejecucion_exitosa(mid)))
        
        comp = gestor.crear_composicion_cuaternaria(ciclos[0], ciclos[1], ciclos[2], ciclos[3])
        
        assert comp.composicion_id in gestor.composiciones_nivel_4
        assert comp.es_exitoso()
    
    def test_contar_ciclos_exitosos(self):
        """Contar ciclos exitosos en todos los niveles."""
        gestor = GestorNiveles()
        
        # Crear ciclos nivel 1
        m1 = Manifestacion(id="WI-001", nombre="Test1", descripcion="", pipeline="C")
        m2 = Manifestacion(id="WI-002", nombre="Test2", descripcion="", pipeline="C")
        
        c1 = gestor.crear_ciclo_nivel_1(m1, crear_ejecucion_exitosa("WI-001"))
        c2 = gestor.crear_ciclo_nivel_1(m2, crear_ejecucion_exitosa("WI-002"))
        
        # Crear composición nivel 2
        comp2 = gestor.crear_composicion_binaria(c1, c2)
        
        conteos = gestor.contar_ciclos_exitosos()
        
        assert conteos["nivel_0"] == 1
        assert conteos["nivel_1"] == 2
        assert conteos["nivel_2"] == 1
        assert conteos["nivel_3"] == 0
        assert conteos["nivel_4"] == 0
    
    def test_obtener_estado_sistema(self):
        """Obtener estado completo del sistema."""
        gestor = GestorNiveles()
        estado = gestor.obtener_estado_sistema()
        
        assert "ESTADO GOLEM" in estado
        assert "Nivel 0" in estado
        assert "Nivel 1" in estado
        assert "Nivel 4" in estado


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

