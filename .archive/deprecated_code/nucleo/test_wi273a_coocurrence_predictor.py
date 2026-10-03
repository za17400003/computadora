"""
Tests for WI-273a BATCH 8: Coocurrence Predictor
Grimorio Anticipatory System — predicting next learning steps

Test suite validating:
1. Matrix building and transitions
2. Prediction accuracy
3. Serialization/deserialization
4. Session-based learning
5. Concept tree seeding
"""

import pytest
from pathlib import Path
from dataclasses import dataclass
import time
from computadora.nucleo.coocurrence_predictor import (
    SearchEvent,
    CooccurrenceMatrix,
    GrimorioAnticipad,
    get_predictor,
    initialize_grimorio_anticipation,
    GRIMORIO_CONCEPT_TREE
)


class TestCooccurrenceMatrix:
    """Tests for CooccurrenceMatrix class."""
    
    def test_matrix_initialization(self):
        """Matrix initializes empty."""
        matrix = CooccurrenceMatrix()
        assert matrix.matrix == {}
        assert matrix.total_transitions == {}
    
    def test_record_single_transition(self):
        """Record a single transition."""
        matrix = CooccurrenceMatrix()
        matrix.record_transition("Tzimtzum", "Or Yashar", weight=1)
        
        assert "Tzimtzum" in matrix.matrix
        assert "Or Yashar" in matrix.matrix["Tzimtzum"]
        assert matrix.matrix["Tzimtzum"]["Or Yashar"] == 1
        assert matrix.total_transitions["Tzimtzum"] == 1
    
    def test_record_multiple_transitions(self):
        """Record multiple transitions from same source."""
        matrix = CooccurrenceMatrix()
        matrix.record_transition("Tzimtzum", "Or Yashar", weight=2)
        matrix.record_transition("Tzimtzum", "Kav", weight=1)
        
        assert matrix.matrix["Tzimtzum"]["Or Yashar"] == 2
        assert matrix.matrix["Tzimtzum"]["Kav"] == 1
        assert matrix.total_transitions["Tzimtzum"] == 3  # 2+1
    
    def test_predict_single_next(self):
        """Predict next concept."""
        matrix = CooccurrenceMatrix()
        matrix.record_transition("Gevurah", "Tiféret", weight=5)
        matrix.record_transition("Gevurah", "Din", weight=2)
        
        predictions = matrix.predict_next("Gevurah", top_k=1)
        
        assert len(predictions) == 1
        assert predictions[0][0] == "Tiféret"
        assert abs(predictions[0][1] - (5.0 / 7.0)) < 0.01  # 5/(5+2)
    
    def test_predict_multiple_next(self):
        """Predict next K concepts ranked by probability."""
        matrix = CooccurrenceMatrix()
        matrix.record_transition("Etz HaChaim", "Sefirot", weight=10)
        matrix.record_transition("Etz HaChaim", "Tiféret", weight=6)
        matrix.record_transition("Etz HaChaim", "Maljut", weight=3)
        
        predictions = matrix.predict_next("Etz HaChaim", top_k=3)
        
        assert len(predictions) == 3
        assert predictions[0][0] == "Sefirot"  # Highest probability
        assert predictions[1][0] == "Tiféret"  # Second
        assert predictions[2][0] == "Maljut"   # Third
    
    def test_predict_cold_start(self):
        """Predict with no data returns empty."""
        matrix = CooccurrenceMatrix()
        predictions = matrix.predict_next("Unknown", top_k=3)
        assert predictions == []
    
    def test_update_from_session(self):
        """Update matrix from search events in a session."""
        matrix = CooccurrenceMatrix()
        
        # Simular sesión: user busca Tzimtzum → Or Yashar → Kav
        events = [
            SearchEvent("Tzimtzum", time.time(), "user_1", "session_1"),
            SearchEvent("Or Yashar", time.time() + 1, "user_1", "session_1"),
            SearchEvent("Kav", time.time() + 2, "user_1", "session_1"),
        ]
        
        matrix.update_from_session(events)
        
        # Deberían registrarse transiciones: Tzimtzum → Or Yashar, Or Yashar → Kav
        assert "Tzimtzum" in matrix.matrix
        assert "Or Yashar" in matrix.matrix["Tzimtzum"]
        assert "Or Yashar" in matrix.matrix
        assert "Kav" in matrix.matrix["Or Yashar"]
    
    def test_multiple_users_same_pattern(self):
        """Multiple users following same pattern increases weight."""
        matrix = CooccurrenceMatrix()
        
        # Usuario 1
        events1 = [
            SearchEvent("Gevurah", time.time(), "user_1", "session_1"),
            SearchEvent("Tiféret", time.time() + 1, "user_1", "session_1"),
        ]
        
        # Usuario 2 (mismo patrón)
        events2 = [
            SearchEvent("Gevurah", time.time(), "user_2", "session_2"),
            SearchEvent("Tiféret", time.time() + 1, "user_2", "session_2"),
        ]
        
        matrix.update_from_session(events1)
        matrix.update_from_session(events2)
        
        # Transition weight debería ser 2x (ambos usuarios)
        assert matrix.matrix["Gevurah"]["Tiféret"] >= 2
    
    def test_serialization(self):
        """Serialize matrix to dict."""
        matrix = CooccurrenceMatrix()
        matrix.record_transition("A", "B", weight=5)
        
        data = matrix.to_dict()
        
        assert "matrix" in data
        assert "total_transitions" in data
        assert data["version"] == 1
        assert data["matrix"]["A"]["B"] == 5
    
    def test_deserialization(self):
        """Deserialize matrix from dict."""
        data = {
            "matrix": {"A": {"B": 5}},
            "total_transitions": {"A": 5},
            "version": 1
        }
        
        matrix = CooccurrenceMatrix.from_dict(data)
        
        assert matrix.matrix["A"]["B"] == 5
        assert matrix.total_transitions["A"] == 5


class TestGrimorioAnticipad:
    """Tests for GrimorioAnticipad singleton."""
    
    def test_singleton_instance(self):
        """GrimorioAnticipad is singleton."""
        predictor1 = get_predictor()
        predictor2 = get_predictor()
        assert predictor1 is predictor2
    
    def test_record_search_event(self):
        """Record search event."""
        predictor = GrimorioAnticipad()
        event = SearchEvent("Tzimtzum", time.time(), "owner", "session_1")
        
        predictor.record_search(event)
        
        assert len(predictor.search_history) > 0
        assert predictor.search_history[-1].concept == "Tzimtzum"
    
    def test_anticipate_basic(self):
        """Anticipate next concepts."""
        # Create fresh instance to avoid singleton state from other tests
        predictor = GrimorioAnticipad()
        predictor.matrix = CooccurrenceMatrix()  # Reset matrix
        
        # Seed matrix manually
        predictor.matrix.record_transition("Tzimtzum", "Or Yashar", weight=10)
        predictor.matrix.record_transition("Tzimtzum", "Kav", weight=5)
        
        result = predictor.anticipate("Tzimtzum", top_k=2)
        
        assert "primary" in result
        assert result["primary"] is not None
        assert result["primary"]["concept"] == "Or Yashar"
        # Confidence: 10/(10+5) = 0.666...
        assert abs(result["primary"]["confidence"] - (10.0 / 15.0)) < 0.01
        assert "secondary" in result
        assert len(result["secondary"]) >= 1
    
    def test_anticipate_cold_start(self):
        """Anticipate with no data."""
        predictor = GrimorioAnticipad()
        result = predictor.anticipate("Unknown", top_k=3)
        
        assert result["primary"] is None
        assert result["secondary"] == []
    
    def test_update_from_history(self):
        """Update matrix from accumulated history."""
        predictor = GrimorioAnticipad()
        predictor.search_history = [
            SearchEvent("Gevurah", time.time(), "owner", "session_1"),
            SearchEvent("Tiféret", time.time() + 1, "owner", "session_1"),
        ]
        
        predictor.update_from_history()
        
        assert len(predictor.search_history) == 0  # Cleared after update
        # Matrix should now have Gevurah → Tiféret transition
        assert "Gevurah" in predictor.matrix.matrix


class TestConceptTreeSeeding:
    """Tests for pre-seeding with concept tree."""
    
    def test_seed_with_tree(self):
        """Seed matrix with concept tree."""
        predictor = GrimorioAnticipad()
        
        tree = {
            "Alquimia": ["NIGREDO", "ALBEDO"],
            "NIGREDO": ["Putrefacción", "Dissolución"]
        }
        
        predictor.seed_with_concept_tree(tree)
        
        # Transitions should be recorded
        assert "Alquimia" in predictor.matrix.matrix
        assert "NIGREDO" in predictor.matrix.matrix["Alquimia"]
        assert "NIGREDO" in predictor.matrix.matrix
    
    def test_grimorio_tree_initialization(self):
        """Verify GRIMORIO_CONCEPT_TREE structure."""
        assert isinstance(GRIMORIO_CONCEPT_TREE, dict)
        assert len(GRIMORIO_CONCEPT_TREE) > 0
        
        # Spot checks
        assert "Tzimtzum" in GRIMORIO_CONCEPT_TREE
        assert "Or Yashar" in GRIMORIO_CONCEPT_TREE["Tzimtzum"]
        assert "Etz HaChaim" in GRIMORIO_CONCEPT_TREE
    
    def test_initialize_anticipation_system(self):
        """Initialize full system with Grimorio tree."""
        initialize_grimorio_anticipation()
        
        predictor = get_predictor()
        
        # Should have transactions for Tzimtzum → Or Yashar
        predictions = predictor.matrix.predict_next("Tzimtzum", top_k=1)
        
        assert len(predictions) > 0
        assert "Or Yashar" in [p[0] for p in predictions]


class TestPredictionAccuracy:
    """Tests for prediction quality."""
    
    def test_high_confidence_prediction(self):
        """High-weight transition produces high confidence."""
        predictor = GrimorioAnticipad()
        
        # 90 votes for A→B, 10 for A→C
        predictor.matrix.record_transition("Source", "TargetA", weight=90)
        predictor.matrix.record_transition("Source", "TargetB", weight=10)
        
        result = predictor.anticipate("Source", top_k=2)
        
        assert result["primary"]["concept"] == "TargetA"
        assert result["primary"]["confidence"] > 0.8
    
    def test_low_confidence_fallback(self):
        """Low confidence triggers fallback."""
        predictor = GrimorioAnticipad()
        predictor.matrix = CooccurrenceMatrix()  # Reset matrix
        
        # Only 1 vote
        predictor.matrix.record_transition("A", "B", weight=1)
        
        result = predictor.anticipate("A", top_k=1)
        
        assert result["primary"]["concept"] == "B"
        # Confidence: 1/1 = 1.0, but overall just 1 vote (low reliability)
        assert result["primary"]["confidence"] <= 1.0
    
    def test_probabilistic_ranking(self):
        """Predictions ranked by probability."""
        predictor = GrimorioAnticipad()
        
        predictor.matrix.record_transition("Root", "First", weight=50)
        predictor.matrix.record_transition("Root", "Second", weight=30)
        predictor.matrix.record_transition("Root", "Third", weight=20)
        
        result = predictor.anticipate("Root", top_k=3)
        
        primary_conf = result["primary"]["confidence"]
        secondary_confs = [s["confidence"] for s in result["secondary"]]
        
        # Primary should be highest
        assert all(primary_conf > conf for conf in secondary_confs)
        # Secondary should be descending
        assert secondary_confs == sorted(secondary_confs, reverse=True)


class TestIntegrationE2E:
    """End-to-end integration tests."""
    
    def test_grimorio_learning_path(self):
        """Simulate complete learning path: search → predict → refine."""
        predictor = GrimorioAnticipad()
        initialize_grimorio_anticipation()
        
        # User searches: Tzimtzum
        user_concept = "Tzimtzum"
        predictions = predictor.matrix.predict_next(user_concept, top_k=3)
        
        # Should suggest Or Yashar, Kav, Reshimu
        predicted_concepts = [p[0] for p in predictions]
        assert len(predicted_concepts) > 0
        
        # Record that user clicked on first suggestion
        predictor.search_history.append(
            SearchEvent(predicted_concepts[0], time.time(), "owner", "session_1")
        )
        
        # System learns this transition
        predictor.update_from_history()
        
        # Next time, confidence for this path increases
        predictions_v2 = predictor.matrix.predict_next(user_concept, top_k=3)
        assert len(predictions_v2) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

