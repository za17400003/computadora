"""
Tests para verificar axiomas primordiales.

Valida que los 5 axiomas (III.7-III.11) se comportan correctamente.
"""

import pytest
from computadora.fundacion import (
    FaseAlquimica,
    Manifestacion,
    Ejecucion,
    VerificadorReduccionEjecucion,
    VerificadorIdempotencia,
    VerificadorIdempotenciaReforzada,
    VerificadorComposicionCartesiana,
    VerificadorComposicionEscalable,
)


class TestAxiomaIII7:
    """AXIOMA III.7: M ∪ E* = {E} — Reducción a Ejecución"""
    
    def test_manifestacion_sin_ejecucion_invalida(self):
        """Manifestación sin ejecución debe ser rechazada."""
        verificador = VerificadorReduccionEjecucion()
        
        m = {Manifestacion(id="WI-001", nombre="Test", descripcion="Test", pipeline="C")}
        e = set()
        
        es_valido, msg = verificador.verificar(m, e)
        assert not es_valido, "Manifestación sin ejecución debe violar III.7"
        assert "violado" in msg.lower()
    
    def test_manifestacion_con_ejecucion_exitosa(self):
        """Manifestación con ejecución exitosa es válida."""
        verificador = VerificadorReduccionEjecucion()
        
        m = {Manifestacion(id="WI-001", nombre="Test", descripcion="Test", pipeline="C")}
        eA = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset({FaseAlquimica.NIGREDO, FaseAlquimica.ALBEDO, 
                               FaseAlquimica.CITRINITAS, FaseAlquimica.RUBEDO, 
                               FaseAlquimica.PALINGENESIA}),
            resultado="verde"
        )
        e = {eA}
        
        es_valido, msg = verificador.verificar(m, e)
        assert es_valido, f"Manifestación con ejecución exitosa debe ser válida: {msg}"


class TestAxiomaIII8:
    """AXIOMA III.8: M ∪ E+ = M ∪ E — Idempotencia Simple"""
    
    def test_ejecucion_unica_es_valida(self):
        """Una sola ejecución exitosa es válida."""
        verificador = VerificadorIdempotencia()
        
        e1 = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset(FaseAlquimica),
            resultado="verde"
        )
        
        es_valido, msg = verificador.verificar("WI-001", [e1])
        assert es_valido, f"Ejecución única debe ser válida: {msg}"
    
    def test_multiples_ejecuciones_exitosas_invalida(self):
        """Múltiples ejecuciones exitosas violan idempotencia."""
        verificador = VerificadorIdempotencia()
        
        e1 = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset(FaseAlquimica),
            resultado="verde"
        )
        e2 = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset(FaseAlquimica),
            resultado="verde"
        )
        
        es_valido, msg = verificador.verificar("WI-001", [e1, e2])
        assert not es_valido, f"Múltiples ejecuciones exitosas deben violar III.8: {msg}"


class TestAxiomaIII9:
    """AXIOMA III.9: M ∪ E+ = M ∪ E (Reforzado) — Fallos no acumulan"""
    
    def test_fallo_seguido_de_exito(self):
        """Patrón válido: E_roja → E_verde (nueva manifestación)."""
        verificador = VerificadorIdempotenciaReforzada()
        
        e1 = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset({FaseAlquimica.NIGREDO}),
            resultado="rojo"
        )
        e2 = Ejecucion(
            manifestacion_id="WI-001-v2",  # Nueva manifestación
            fases_completadas=frozenset(FaseAlquimica),
            resultado="verde"
        )
        
        es_valido, msg = verificador.verificar([e1, e2])
        assert es_valido, f"Patrón fallo→éxito debe ser válido: {msg}"
    
    def test_fallos_acumulan_en_misma_manifestacion(self):
        """Patrón inválido: múltiples ROJAS de la misma manifestación."""
        verificador = VerificadorIdempotenciaReforzada()
        
        e1 = Ejecucion(
            manifestacion_id="WI-001",
            fases_completadas=frozenset({FaseAlquimica.NIGREDO}),
            resultado="rojo"
        )
        e2 = Ejecucion(
            manifestacion_id="WI-001",  # MISMA manifestación
            fases_completadas=frozenset({FaseAlquimica.NIGREDO, FaseAlquimica.ALBEDO}),
            resultado="rojo"
        )
        
        es_valido, msg = verificador.verificar([e1, e2])
        assert not es_valido, f"Fallos acumulados deben violar III.9: {msg}"


class TestAxiomaIII10:
    """AXIOMA III.10: M ∪ E+ = (M ∪ E) × (M ∪ E) — Composición Cartesiana"""
    
    def test_descomposicion_en_subciclos(self):
        """WI grande puede descomponerse en 2+ subciclos."""
        verificador = VerificadorComposicionCartesiana()
        
        m_padre = Manifestacion(id="WI-287", nombre="Investigación Minimi", 
                               descripcion="Grande", pipeline="C")
        m_hijas = [
            Manifestacion(id="WI-287a", nombre="Buscar", 
                         descripcion="Buscar en git", pipeline="C"),
            Manifestacion(id="WI-287b", nombre="Integrar", 
                         descripcion="Integrar resultados", pipeline="C"),
        ]
        
        es_valido, msg = verificador.verificar(m_padre, m_hijas)
        assert es_valido, f"Descomposición válida debe ser aceptada: {msg}"
    
    def test_descomposicion_require_al_menos_dos(self):
        """Descomposición requiere ≥ 2 subciclos."""
        verificador = VerificadorComposicionCartesiana()
        
        m_padre = Manifestacion(id="WI-287", nombre="Test", 
                               descripcion="Test", pipeline="C")
        m_hijas = [
            Manifestacion(id="WI-287a", nombre="Solo", 
                         descripcion="Solo uno", pipeline="C"),
        ]
        
        es_valido, msg = verificador.verificar(m_padre, m_hijas)
        assert not es_valido, f"Un solo subciclo debe ser rechazado: {msg}"


class TestAxiomaIII11:
    """AXIOMA III.11: M ∪ E+ = (M ∪ E) × (M ∪ E) (Reforzado) — Escalabilidad"""
    
    def test_n_ciclos_compuestos_validos(self):
        """N ciclos pueden componerse mientras todos sean exitosos."""
        verificador = VerificadorComposicionEscalable()
        
        manifestaciones = [
            Manifestacion(id="WI-291", nombre="Minimi", descripcion="...", pipeline="C"),
            Manifestacion(id="WI-292", nombre="Tests", descripcion="...", pipeline="C"),
            Manifestacion(id="WI-293", nombre="Ollama", descripcion="...", pipeline="C"),
        ]
        
        ejecuciones = {
            "WI-291": Ejecucion(
                manifestacion_id="WI-291",
                fases_completadas=frozenset(FaseAlquimica),
                resultado="verde"
            ),
            "WI-292": Ejecucion(
                manifestacion_id="WI-292",
                fases_completadas=frozenset(FaseAlquimica),
                resultado="verde"
            ),
            "WI-293": Ejecucion(
                manifestacion_id="WI-293",
                fases_completadas=frozenset(FaseAlquimica),
                resultado="verde"
            ),
        }
        
        es_valido, msg = verificador.verificar(manifestaciones, ejecuciones)
        assert es_valido, f"3 ciclos válidos deben componerse: {msg}"
    
    def test_n_ciclos_con_fallo_invalido(self):
        """Si uno falla, composición es inválida."""
        verificador = VerificadorComposicionEscalable()
        
        manifestaciones = [
            Manifestacion(id="WI-291", nombre="Minimi", descripcion="...", pipeline="C"),
            Manifestacion(id="WI-292", nombre="Tests", descripcion="...", pipeline="C"),
            Manifestacion(id="WI-293", nombre="Ollama", descripcion="...", pipeline="C"),
        ]
        
        ejecuciones = {
            "WI-291": Ejecucion(
                manifestacion_id="WI-291",
                fases_completadas=frozenset(FaseAlquimica),
                resultado="verde"
            ),
            "WI-292": Ejecucion(
                manifestacion_id="WI-292",
                fases_completadas=frozenset({FaseAlquimica.NIGREDO}),
                resultado="rojo"
            ),
            # WI-293 sin ejecución
        }
        
        es_valido, msg = verificador.verificar(manifestaciones, ejecuciones)
        assert not es_valido, f"Con 1+ fallos, composición debe ser inválida: {msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

