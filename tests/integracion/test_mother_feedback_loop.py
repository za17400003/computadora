"""
tests/test_mother_feedback_loop.py — Unit tests para Mother Feedback Loop (FP-137 C1)

Tests de captura de eventos, detección de patrones y sincronización bidireccional.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from computadora.nucleo.mother_feedback_loop import (
    UserEvent,
    FeedbackResult,
    MotherFeedback,
    BidirectionalSync,
    crear_mother_feedback,
    obtener_mother_feedback,
    crear_sync,
)


class TestUserEvent:
    """Tests para estructura UserEvent."""
    
    def test_user_event_creation(self):
        """Test: UserEvent se crea correctamente."""
        evento = UserEvent(
            timestamp=1000.0,
            platform="computadora",
            accion="voz_query",
            contexto="inicio",
            emocion_detectada="alegría",
            resultado="exitoso",
            confianza_usuario=0.8,
        )
        
        assert evento.platform == "computadora"
        assert evento.accion == "voz_query"
        assert evento.confianza_usuario == 0.8


class TestMotherFeedback:
    """Tests para MotherFeedback."""
    
    def test_init(self):
        """Test: MotherFeedback inicializa."""
        mother = MotherFeedback()
        assert mother._historial_eventos == []
        assert mother._patrones_detectados == {}
    
    def test_custom_callback(self):
        """Test: Callback personalizado se asigna."""
        callback_mock = Mock()
        mother = MotherFeedback(on_feedback=callback_mock)
        assert mother.on_feedback == callback_mock
    
    def test_capturar_evento_simple(self):
        """Test: Captura evento simple."""
        mother = MotherFeedback()
        
        resultado = mother.capturar_evento(
            accion="voz_query",
            platform="computadora",
            contexto="inicio",
            confianza=0.9,
        )
        
        assert len(mother._historial_eventos) == 1
        assert resultado.evento_original.accion == "voz_query"
    
    def test_patron_detection_repetition(self):
        """Test: Detecta patrón tras repetición."""
        mother = MotherFeedback()
        
        # Capturar mismo evento 3 veces
        for i in range(3):
            mother.capturar_evento(
                accion="autocompletado",
                platform="computadora",
                contexto="búsqueda",
            )
        
        # Tercera captura debería detectar patrón
        resultado = mother.capturar_evento(
            accion="autocompletado",
            platform="computadora",
            contexto="búsqueda",
        )
        
        assert resultado.patron_detectado is not None
        assert resultado.confianza_mejorada > 0.0
    
    def test_emocion_recurrente_insight(self):
        """Test: Detecta emoción recurrente y genera insight."""
        callback_mock = Mock()
        mother = MotherFeedback(on_feedback=callback_mock)
        
        # Capturar eventos con emoción negativa
        mother.capturar_evento(
            accion="búsqueda_avanzada",
            platform="computadora",
            emocion="frustración",
        )
        
        resultado2 = mother.capturar_evento(
            accion="búsqueda_avanzada",
            platform="computadora",
            emocion="frustración",
        )
        
        # Segunda captura con misma emoción debería generar insight
        assert resultado2.insight is not None or callback_mock.called
    
    def test_platform_sync_confidence(self):
        """Test: Aumenta confianza cuando mismo patrón en ambas plataformas."""
        mother = MotherFeedback()
        
        # Capturar acción en Computadora
        mother.capturar_evento(
            accion="timer_iniciado",
            platform="computadora",
            contexto="reloj",
        )
        
        # Capturar en Minimi
        resultado = mother.capturar_evento(
            accion="timer_iniciado",
            platform="minimi",
            contexto="reloj",
        )
        
        # Debe aumentar confianza por sincronía
        assert resultado.confianza_mejorada >= 0.15
    
    def test_session_statistics(self):
        """Test: Calcula estadísticas de sesión."""
        mother = MotherFeedback()
        
        mother.capturar_evento("accion1", platform="computadora")
        mother.capturar_evento("accion2", platform="minimi")
        mother.capturar_evento("accion1", platform="computadora")
        
        stats = mother.estadisticas_sesion()
        
        assert stats["total_eventos"] == 3
        assert stats["eventos_computadora"] == 2
        assert stats["eventos_minimi"] == 1
        assert stats["sincronia_bidireccional"] is True
    
    def test_recomendacion_diaria(self):
        """Test: Genera recomendación diaria."""
        mother = MotherFeedback()
        
        # Crear patrón fuerte
        for i in range(5):
            mother.capturar_evento(
                accion="meditacion",
                platform="computadora",
                contexto="manana",
            )
        
        recomendacion = mother.recomendacion_diaria()
        
        # Debería generar recomendación para patrón fuerte
        assert recomendacion is not None
        assert "meditacion" in recomendacion.lower()
    
    def test_callback_invoked_on_insight(self):
        """Test: Callback se invoca cuando hay insight."""
        callback_mock = Mock()
        mother = MotherFeedback(on_feedback=callback_mock)
        
        # Generar patrón repetido con insight
        for i in range(3):
            mother.capturar_evento("accion_x", platform="computadora")
        
        # Callback debería haber sido invocado
        assert callback_mock.called or resultado.insight is not None


class TestBidirectionalSync:
    """Tests para BidirectionalSync."""
    
    def test_init(self):
        """Test: BidirectionalSync inicializa."""
        sync = BidirectionalSync()
        assert sync._ultima_sincronizacion == 0.0
        assert sync._sync_interval == 300.0
    
    def test_sincronizar_vacio(self):
        """Test: Sincronización con eventos vacíos."""
        sync = BidirectionalSync()
        
        resultado = sync.sincronizar([], {})
        
        assert resultado["sincronizado"] is True
        assert resultado["eventos_procesados"] == 0
    
    def test_sincronizar_enriquece_eventos(self):
        """Test: Sincronización enriquece confianza de eventos."""
        sync = BidirectionalSync()
        
        evento = UserEvent(
            timestamp=1000.0,
            platform="minimi",
            accion="voz",
            contexto="inicio",
            confianza_usuario=0.5,
        )
        
        patrones_computadora = {
            "voz@inicio": {"hits": 5},
        }
        
        resultado = sync.sincronizar([evento], patrones_computadora)
        
        assert resultado["sincronizado"] is True
        assert resultado["patrones_enriquecidos"] == 1
    
    def test_throttle_sync(self):
        """Test: Throttle evita sincronizaciones frecuentes."""
        sync = BidirectionalSync()
        
        # Primera sincronización
        resultado1 = sync.sincronizar([], {})
        assert resultado1["sincronizado"] is True
        
        # Segunda sincronización inmediata (debería estar throttled)
        resultado2 = sync.sincronizar([], {})
        assert resultado2["sincronizado"] is False


class TestMotherFeedbackIntegration:
    """Smoke tests de integración."""
    
    def test_import_classes(self):
        """Test: Clases se pueden importar."""
        from computadora.nucleo.mother_feedback_loop import (
            MotherFeedback,
            BidirectionalSync,
        )
        assert MotherFeedback is not None
        assert BidirectionalSync is not None
    
    def test_global_singleton_factory(self):
        """Test: Factory crea singleton."""
        mother1 = crear_mother_feedback()
        assert mother1 is not None
        
        mother2 = obtener_mother_feedback()
        assert mother1 is mother2
    
    def test_sync_singleton_factory(self):
        """Test: Sync factory crea singleton."""
        sync1 = crear_sync()
        assert sync1 is not None
        
        sync2 = crear_sync()
        assert sync1 is sync2


def test_full_workflow_mother_feedback():
    """Test: Flujo completo de captura → procesamiento → insight."""
    callback_mock = Mock()
    mother = MotherFeedback(on_feedback=callback_mock)
    
    # Simular sesión de usuario
    # Acción 1: Usuario usa búsqueda (feliz)
    mother.capturar_evento(
        accion="busqueda",
        platform="computadora",
        contexto="inicio",
        emocion="alegría",
        confianza=0.8,
    )
    
    # Acción 2: Repite búsqueda (confundido)
    resultado2 = mother.capturar_evento(
        accion="busqueda",
        platform="computadora",
        contexto="init",  # contexto ligeramente diferente
        emocion="confusión",
        confianza=0.6,
    )
    
    # Acción 3: En Minimi, repite busqueda (exitoso)
    resultado3 = mother.capturar_evento(
        accion="busqueda",
        platform="minimi",
        contexto="inicio",
        emocion="alegría",
        confianza=0.9,
    )
    
    # Verificaciones
    stats = mother.estadisticas_sesion()
    assert stats["total_eventos"] == 3
    assert stats["sincronia_bidireccional"] is True
    
    # Debería haber mejorado confianza
    assert resultado3.confianza_mejorada > 0.0


def test_full_workflow_bidirectional_sync():
    """Test: Sincronización bidireccional PC ↔ Móvil."""
    madre = crear_mother_feedback()
    sync = crear_sync()
    
    # Computadora PC aprende patrón
    for i in range(5):
        madre.capturar_evento("meditación", platform="computadora", contexto="mañana")
    
    # Minimi Android captura evento similar
    eventos_minimi = [
        UserEvent(
            timestamp=1000.0 + i,
            platform="minimi",
            accion="meditación",
            contexto="mañana",
            confianza_usuario=0.5,
        )
        for i in range(2)
    ]
    
    # Sincronizar
    patrones_computadora = madre._patrones_detectados
    resultado_sync = sync.sincronizar(eventos_minimi, patrones_computadora)
    
    assert resultado_sync["sincronizado"] is True
    assert resultado_sync["patrones_enriquecidos"] > 0

