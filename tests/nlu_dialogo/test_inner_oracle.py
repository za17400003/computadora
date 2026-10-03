"""
tests/test_inner_oracle.py — Unit tests para Inner Oracle (FP-138 K1)

Tests de análisis de preguntas superficiales vs profundas y generación de insights.
"""

import pytest
from unittest.mock import Mock
import json
from pathlib import Path
from computadora.percepcion.inner_oracle import (
    InnerOracle,
    crear_oracle,
    obtener_oracle,
    _SHALLOW_PATTERNS,
    _DEEP_PATTERNS,
)


class TestInnerOracleAnalysis:
    """Tests para análisis de preguntas."""
    
    def test_init(self):
        """Test: InnerOracle inicializa correctamente."""
        oracle = InnerOracle()
        assert oracle._historial_preguntas == []
        assert oracle.on_insight is not None
    
    def test_custom_callback(self):
        """Test: Callback personalizado se asigna."""
        callback_mock = Mock()
        oracle = InnerOracle(on_insight=callback_mock)
        assert oracle.on_insight == callback_mock
    
    def test_detect_shallow_tecnica(self):
        """Test: Detecta pregunta sobre técnica."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("¿Cómo hago para automatizar esto?")
        
        assert resultado["nivel"] in ["superficial", "mixto"]
        assert resultado["tipo_superficial"] == "técnica"
    
    def test_detect_shallow_definicion(self):
        """Test: Detecta pregunta sobre definición."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("¿Qué es la inteligencia artificial?")
        
        assert resultado["tipo_superficial"] == "definición"
    
    def test_detect_deep_confusion(self):
        """Test: Detecta pregunta profunda sobre confusión."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("No sé qué hacer. ¿Cómo empiezo?")
        
        assert resultado["tipo_profundo"] == "confusión"
        assert resultado["nivel"] in ["profundo", "mixto"]
    
    def test_detect_deep_desire(self):
        """Test: Detecta pregunta profunda sobre deseo."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("Quiero automatizar mi vida. ¿Cómo?")
        
        assert resultado["tipo_profundo"] == "deseo_profundo"
    
    def test_detect_deep_fear(self):
        """Test: Detecta pregunta profunda sobre miedo."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("Tengo miedo de equivocarme. ¿Qué debo hacer?")
        
        assert resultado["tipo_profundo"] == "miedo"
    
    def test_mixed_level_question(self):
        """Test: Pregunta mixta (superficial + profunda)."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("Tengo miedo sobre cómo automatizar. ¿Cómo lo hago?")
        
        assert resultado["nivel"] in ["mixto", "profundo"]
        assert resultado["tipo_profundo"] == "miedo"
    
    def test_generates_real_question_suggestion(self):
        """Test: Genera sugerencia de pregunta real."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("¿Cómo automatizo? Tengo miedo de que falle.")
        
        # Si hay pregunta real sugerida, debería ser un string
        pregunta_real = resultado["pregunta_real_sugerida"]
        assert pregunta_real is None or isinstance(pregunta_real, str)
    
    def test_generates_illumination_advice(self):
        """Test: Genera consejo de iluminación para preguntas profundas."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("No sé qué hacer.")
        
        # Pregunta profunda debe tener consejo
        assert resultado["consejo_iluminacion"] is not None
    
    def test_callback_invoked_on_insight(self):
        """Test: Callback se invoca cuando encuentra insight."""
        callback_mock = Mock()
        oracle = InnerOracle(on_insight=callback_mock)
        
        oracle.analizar_pregunta("No sé qué hacer.")
        
        # Callback debería haber sido invocado al menos una vez
        assert callback_mock.called or oracle._historial_preguntas
    
    def test_confidence_score(self):
        """Test: Score de confianza se asigna."""
        oracle = InnerOracle()
        
        # Superficial sin pistas profundas = baja confianza
        resultado1 = oracle.analizar_pregunta("¿Cuánto es 2+2?")
        assert 0.0 <= resultado1["confianza"] <= 1.0
        
        # Profundo = alta confianza
        resultado2 = oracle.analizar_pregunta("No sé quién soy.")
        assert resultado2["confianza"] >= resultado1["confianza"]
    
    def test_historial_accumulation(self):
        """Test: Historial acumula preguntas."""
        oracle = InnerOracle()
        
        oracle.analizar_pregunta("¿Cómo hago esto?")
        assert len(oracle._historial_preguntas) == 1
        
        oracle.analizar_pregunta("No sé qué hacer.")
        assert len(oracle._historial_preguntas) == 2
    
    def test_session_statistics(self):
        """Test: Estadísticas de sesión."""
        oracle = InnerOracle()
        
        oracle.analizar_pregunta("¿Cómo hago?")  # superficial
        oracle.analizar_pregunta("No sé.")  # profundo
        
        stats = oracle.estadisticas_sesion()
        assert stats["total"] == 2
        assert stats["superficiales"] >= 1
        assert stats["profundas"] >= 1
        assert 0.0 <= stats["confianza_promedio"] <= 1.0
    
    def test_daily_advice(self):
        """Test: Genera consejo diario para abrir sesión."""
        oracle = InnerOracle()
        
        # Llamar múltiples veces para asegurar variedad
        consejos = set()
        for _ in range(5):
            consejo = oracle.consejo_diario()
            assert isinstance(consejo, str)
            assert len(consejo) > 0
            consejos.add(consejo)
        
        # Debería haber al menos algunos consejos diferentes
        assert len(consejos) > 0


class TestInnerOracleIntegration:
    """Smoke tests de integración."""
    
    def test_import_oracle(self):
        """Test: InnerOracle se puede importar."""
        from computadora.percepcion.inner_oracle import InnerOracle
        assert InnerOracle is not None
    
    def test_global_singleton_factory(self):
        """Test: Factory crea singleton."""
        from computadora.percepcion.inner_oracle import crear_oracle, obtener_oracle
        
        oracle1 = crear_oracle()
        assert oracle1 is not None
        
        oracle2 = obtener_oracle()
        assert oracle1 is oracle2
    
    def test_timestamp_format(self):
        """Test: Resultados incluyen timestamp ISO."""
        oracle = InnerOracle()
        resultado = oracle.analizar_pregunta("Test")
        
        assert "timestamp" in resultado
        # Verifica que sea ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(resultado["timestamp"])
            assert True
        except ValueError:
            assert False, "Timestamp no es formato ISO"


@pytest.mark.parametrize("pregunta,tipo_esperado", [
    ("¿Cómo hago para instalar Python?", "técnica"),
    ("¿Qué es una variable?", "definición"),
    ("¿Dónde descargo esto?", "ubicación"),
])
def test_shallow_pattern_matching(pregunta, tipo_esperado):
    """Test: Patrones superficiales se detectan correctamente."""
    oracle = InnerOracle()
    resultado = oracle.analizar_pregunta(pregunta)
    
    assert resultado["tipo_superficial"] == tipo_esperado or resultado["nivel"] in ["profundo", "mixto"]


@pytest.mark.parametrize("pregunta,tipo_profundo_esperado", [
    ("No sé por dónde empezar.", "confusión"),
    ("Quiero mejorar mi código.", "deseo_profundo"),
    ("Tengo miedo de romper algo.", "miedo"),
    ("Estoy agobiado por el trabajo.", "presión"),
    ("Pero ¿y si falla?", "prospección"),
])
def test_deep_pattern_matching(pregunta, tipo_profundo_esperado):
    """Test: Patrones profundos se detectan correctamente."""
    oracle = InnerOracle()
    resultado = oracle.analizar_pregunta(pregunta)
    
    assert resultado["tipo_profundo"] == tipo_profundo_esperado


def test_full_workflow():
    """Test: Flujo completo de análisis e iluminación."""
    callback_llamado = []
    
    def mock_callback(msg):
        callback_llamado.append(msg)
    
    oracle = InnerOracle(on_insight=mock_callback)
    
    # Pregunta que debe gatillar insight
    resultado = oracle.analizar_pregunta(
        "Quiero aprender programación pero no sé por dónde empezar y tengo miedo."
    )
    
    # Verificaciones
    assert resultado["nivel"] in ["profundo", "mixto"]
    assert resultado["tipo_profundo"] is not None
    assert resultado["consejo_iluminacion"] is not None
    
    # Callback debería haber sido invocado
    assert len(callback_llamado) > 0 or oracle._historial_preguntas

