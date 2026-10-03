"""
BATCH 8 — WI-273a: Coocurrence Predictor for Enciclopedia
Anticipatory knowledge system — predicting next 3 steps in learning path

Core module: computadora/nucleo/coocurrence_predictor.py
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
import time
from loguru import logger


@dataclass
class SearchEvent:
    """Evento de búsqueda en Enciclopedia."""
    concept: str
    timestamp: float
    user_id: str
    session_id: str
    clicked_concept: Optional[str] = None
    confidence: float = 1.0  # Fuerza del evento


class CooccurrenceMatrix:
    """
    Matriz NxN de coocurrencias concepto → concepto.
    
    Ejemplo:
        matrix["Tzimtzum"]["Or Yashar"] = 25  # 25 usuarios buscaron Or Yashar después
        matrix["Gevurah"]["Tiféret"] = 18
    
    Uso: predict_next("Tzimtzum") → [("Or Yashar", 0.89), ("Kav", 0.67), ...]
    """
    
    def __init__(self):
        self.matrix: Dict[str, Dict[str, int]] = {}
        self.total_transitions: Dict[str, int] = {}
        self.last_concepts: Dict[str, str] = {}  # user_id → last concept searched
    
    def record_transition(self, from_concept: str, to_concept: str, weight: int = 1):
        """Registrar transición de búsqueda: usuario fue de X a Y."""
        if from_concept not in self.matrix:
            self.matrix[from_concept] = {}
        
        self.matrix[from_concept][to_concept] = self.matrix[from_concept].get(to_concept, 0) + weight
        self.total_transitions[from_concept] = self.total_transitions.get(from_concept, 0) + weight
        
        logger.debug(f"Transition: {from_concept} → {to_concept} (weight={weight})")
    
    def predict_next(self, concept: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Predecir próximos K conceptos más probables.
        
        Returns: [(concepto, probabilidad), ...]
        Ordenado descendente por probabilidad.
        """
        if concept not in self.matrix:
            logger.debug(f"Concept '{concept}' no en matriz (cold start)")
            return []
        
        transitions = self.matrix[concept]
        total = self.total_transitions.get(concept, 1)
        
        # Calcular probabilidades Bayesianas
        predictions = [
            (target_concept, float(count) / total)
            for target_concept, count in transitions.items()
        ]
        
        # Ordenar descendente por probabilidad
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:top_k]
    
    def update_from_session(self, search_events: List[SearchEvent]):
        """Actualizar matriz desde eventos de búsqueda de una sesión."""
        # Agrupar por user_id y session_id
        by_session = {}
        for event in search_events:
            key = (event.user_id, event.session_id)
            if key not in by_session:
                by_session[key] = []
            by_session[key].append(event)
        
        # Procesar cada sesión
        for session_events in by_session.values():
            # Ordenar por timestamp
            session_events.sort(key=lambda e: e.timestamp)
            
            # Registrar transiciones consecutivas
            for i in range(len(session_events) - 1):
                from_ev = session_events[i]
                to_ev = session_events[i + 1]
                
                # Weight por confidence (si usuario hizo click, más peso)
                weight = int(from_ev.confidence * 10)  # 0-10
                
                self.record_transition(from_ev.concept, to_ev.concept, weight=weight)
    
    def to_dict(self) -> dict:
        """Serializar matriz para almacenamiento."""
        return {
            "matrix": self.matrix,
            "total_transitions": self.total_transitions,
            "version": 1
        }
    
    @staticmethod
    def from_dict(data: dict) -> "CooccurrenceMatrix":
        """Deserializar matriz."""
        predictor = CooccurrenceMatrix()
        predictor.matrix = data.get("matrix", {})
        predictor.total_transitions = data.get("total_transitions", {})
        return predictor


class EnciclopediaAnticipad:
    """
    Orquestador de predicción anticipatoria.
    Singleton que coordina predicción de próximos conceptos.
    """
    
    _instance = None
    STORAGE_PATH = Path(__file__).parent.parent.parent / "datos" / "enciclopedia_coocurrence.jsonl"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.matrix = CooccurrenceMatrix()
        self.search_history: List[SearchEvent] = []
        self._load_matrix()
        self._initialized = True
        logger.info("EnciclopediaAnticipad initialized")
    
    def _load_matrix(self):
        """Cargar matriz desde disk."""
        if not self.STORAGE_PATH.exists():
            logger.debug(f"No coocurrence matrix at {self.STORAGE_PATH}, starting fresh")
            return
        
        try:
            with open(self.STORAGE_PATH, 'r') as f:
                # JSONL format: una línea por transición
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "matrix_dump":
                        self.matrix = CooccurrenceMatrix.from_dict(data)
                        break
        except Exception as e:
            logger.warning(f"Error loading coocurrence matrix: {e}")
    
    def _save_matrix(self):
        """Guardar matriz a disk."""
        self.STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.STORAGE_PATH, 'w') as f:
                dump = self.matrix.to_dict()
                dump["type"] = "matrix_dump"
                dump["timestamp"] = time.time()
                f.write(json.dumps(dump) + "\n")
            logger.debug(f"Matrix saved to {self.STORAGE_PATH}")
        except Exception as e:
            logger.warning(f"Error saving coocurrence matrix: {e}")
    
    def record_search(self, event: SearchEvent):
        """Registrar evento de búsqueda."""
        self.search_history.append(event)
        logger.debug(f"Recorded search: {event.concept} (session={event.session_id})")
    
    def anticipate(self, concept: str, top_k: int = 3) -> Dict[str, any]:
        """
        Anticipar próximos conceptos para usuario tras buscar 'concept'.
        
        Returns:
            {
                "primary": {
                    "concept": "Or Yashar",
                    "confidence": 0.89,
                    "reasoning": "Natural continuation of Tzimtzum contraction theory"
                },
                "secondary": [
                    {"concept": "Kav", "confidence": 0.67},
                    {"concept": "Reshimu", "confidence": 0.54}
                ]
            }
        """
        predictions = self.matrix.predict_next(concept, top_k=top_k)
        
        if not predictions:
            logger.debug(f"No predictions for '{concept}'")
            return {"primary": None, "secondary": []}
        
        # Primary: primera (más probable)
        primary_concept, primary_confidence = predictions[0]
        
        # Secondary: rest
        secondary = [
            {"concept": concept, "confidence": float(conf)}
            for concept, conf in predictions[1:]
        ]
        
        result = {
            "primary": {
                "concept": primary_concept,
                "confidence": float(primary_confidence),
                "reasoning": f"Users searching {concept} typically continue with {primary_concept}"
            },
            "secondary": secondary
        }
        
        return result
    
    def update_from_history(self):
        """Actualizar matriz desde search_history."""
        if self.search_history:
            self.matrix.update_from_session(self.search_history)
            self._save_matrix()
            self.search_history = []  # Clear history
    
    def seed_with_concept_tree(self, concept_tree: Dict[str, List[str]]):
        """
        Pre-llenar matriz con árbol de conceptos conocido.
        
        Ejemplo:
            {
                "Tzimtzum": ["Or Yashar", "Kav"],
                "Or Yashar": ["Or Chozer", "Lurianic Cosmology"],
                "Etz HaChaim": ["Sefirot", "Tiféret"]
            }
        """
        for from_concept, to_concepts in concept_tree.items():
            for to_concept in to_concepts:
                self.matrix.record_transition(from_concept, to_concept, weight=5)
        
        self._save_matrix()
        logger.info(f"Seeded matrix with {len(concept_tree)} concepts")


# === PROTOTIPO CON CONCEPTOS CABALÍSTICOS ===

GRIMORIO_CONCEPT_TREE = {
    # Cosmología Luriana
    "Tzimtzum": ["Or Yashar", "Kav", "Reshimu"],
    "Or Yashar": ["Or Chozer", "Klipot"],
    "Kav": ["Tiféret", "Etz HaChaim"],
    "Reshimu": ["Imprint", "Memory of Nothing"],
    
    # Etz HaChaim fundamental
    "Etz HaChaim": ["Sefirot", "Três Pilares"],
    "Sefirot": ["Keter", "Chokmá", "Binah", "Gevurah", "Tiféret", "Maljut"],
    "Keter": ["Ain Sof", "Punto Infinito"],
    "Chokmá": ["Punto", "Flash de intuición"],
    "Binah": ["Forma", "Receptividad"],
    "Gevurah": ["Poder", "Severidad", "Din"],
    "Tiféret": ["Sol", "Centro equilibrio"],
    "Maljut": ["Reino", "Manifestación física"],
    
    # Alquimia clásica
    "Alquimia": ["NIGREDO", "ALBEDO", "CITRINITAS", "RUBEDO", "PALINGENESIA"],
    "NIGREDO": ["Putrefacción", "Dissolución"],
    "ALBEDO": ["Purificación", "Blanqueamiento"],
    "CITRINITAS": ["Amarillecimiento", "Iluminación"],
    "RUBEDO": ["Rojo", "Manifestación"],
    "PALINGENESIA": ["Renacimiento", "Retorno al origen"],
    
    # Cabalá práctica
    "Meditación": ["Vipassana", "Samadhi"],
    "Mantras": ["Mantra semilla", "Mantra guardián"],
    "Tarot": ["Arcanos Mayores", "Arcanos Menores"],
}


def get_predictor() -> EnciclopediaAnticipad:
    """Obtener singleton de EnciclopediaAnticipad."""
    return EnciclopediaAnticipad()


def initialize_enciclopedia_anticipation():
    """Inicializar predictor con conceptos conocidos."""
    predictor = get_predictor()
    predictor.seed_with_concept_tree(GRIMORIO_CONCEPT_TREE)
    logger.info("Enciclopedia anticipation system initialized with concept tree")


