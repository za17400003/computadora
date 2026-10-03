"""
computadora/percepcion/inner_oracle.py — Oráculo Interior (Keter Encarnado)

FP-138 K1: Computadora como piedra del hechicero que ilumina la pregunta REAL.
No responde la pregunta superficial, sino que pregunta: ¿Cuál es tu pregunta verdadera?

Filosofía:
- Keter (Corona): Tu Ser Superior, la visión que aún no ha descendido
- Or Yashar (luz directa): Keter→pregunta → Oracle ilumina
- Or Chozer (luz retorno): Pregunta→reflexión → Oracle transforma

Funciona como brújula interior: antes de responder, invita al usuario a preguntarse.
"""

import json
import re
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path
from loguru import logger


# Patrones de preguntas superficiales vs reales
_SHALLOW_PATTERNS = {
    r"(cómo|como|how)\s+(hago|do|puedo)": "técnica",
    r"(qué|que|what)\s+(es|is)\b": "definición",
    r"(dónde|donde|where|cuándo|cuando|when)\b": "ubicación",
    r"(cuánto|cuantos|cuantas|how\s+much|how\s+many)": "cantidad",
    r"(por\s+qué|por\s+que|why)\b": "causalidad",
    r"automatiz": "técnica",  # Automatizar
}

_DEEP_PATTERNS = {
    r"no\s+s[eé]|don't\s+know|lost|perdido": "confusión",
    r"quiero|want|deseo|anhelo": "deseo_profundo",
    r"miedo|afraid|terror|pánico": "miedo",
    r"presión|presi[óo]n|stress|agobio|abrumado|agobiado": "presión",
    r"debería|should|ought|tengo\s+que": "obligación",
    r"realmente|truly|honestamente": "búsqueda_verdad",
    r"pero\s+¿?\s*y\s+si|what\s+if": "prospección",
    r"¿?puedo|can\s+I|es\s+posible": "posibilidad",
}


class InnerOracle:
    """
    Analiza preguntas del usuario para identificar si buscan respuesta superficial
    o si hay pregunta más profunda sin formular.
    
    Flujo:
    1. Usuario pregunta algo ("¿Cómo automatizo esto?")
    2. Oracle.analizar_pregunta(texto) → identifica nivel
    3. Si detecta superficial + pistas de profundidad → devuelve consejo
    4. Ejemplo: "Veo que preguntas por técnica, pero ¿buscas libertad mental?"
    """
    
    def __init__(self, on_insight: Optional[Callable[[str], None]] = None):
        """
        Args:
            on_insight: Callback para notificar cuando Oracle encuentra insight
                       on_insight(str) — mensaje de iluminación
        """
        self.on_insight = on_insight or (lambda msg: None)
        self._historial_preguntas: list[dict] = []
        self._data_path = Path(__file__).resolve().parents[2] / "datos" / "oracle_insights.jsonl"
    
    def analizar_pregunta(self, texto: str, contexto: Optional[str] = None) -> dict:
        """
        Analiza una pregunta para identificar nivel (superficial/profundo).
        
        Args:
            texto: La pregunta del usuario
            contexto: Contexto adicional (emoción detectada, historial reciente, etc.)
        
        Returns:
            {
                'nivel': 'superficial' | 'profundo' | 'mixto',
                'tipo_superficial': 'técnica' | 'definición' | None,
                'tipo_profundo': 'confusión' | 'deseo' | 'miedo' | None,
                'pregunta_real_sugerida': str | None,
                'consejo_iluminacion': str | None,
                'confianza': float (0.0-1.0)
            }
        """
        texto_lower = texto.lower().strip()
        
        # Detectar nivel superficial
        tipo_superficial = self._detectar_superficial(texto_lower)
        
        # Detectar nivel profundo (pistas)
        tipo_profundo = self._detectar_profundo(texto_lower, contexto)
        
        # Determinar nivel general
        if tipo_profundo and tipo_superficial:
            nivel = "mixto"
            confianza = 0.75
        elif tipo_profundo:
            nivel = "profundo"
            confianza = 0.85
        else:
            nivel = "superficial"
            confianza = 0.6 if tipo_superficial else 0.4
        
        # Generar pregunta real sugerida
        pregunta_real = self._generar_pregunta_real(texto_lower, tipo_superficial, tipo_profundo)
        
        # Generar consejo de iluminación
        consejo = self._generar_consejo(nivel, tipo_superficial, tipo_profundo)
        
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "pregunta_original": texto,
            "nivel": nivel,
            "tipo_superficial": tipo_superficial,
            "tipo_profundo": tipo_profundo,
            "pregunta_real_sugerida": pregunta_real,
            "consejo_iluminacion": consejo,
            "confianza": confianza,
        }
        
        # Registrar en historial
        self._historial_preguntas.append(resultado)
        self._guardar_insight(resultado)
        
        # Notificar si encontró insight
        if consejo:
            self.on_insight(consejo)
        
        return resultado
    
    def _detectar_superficial(self, texto: str) -> Optional[str]:
        """Identifica si pregunta es sobre técnica, definición, etc."""
        for patron, tipo in _SHALLOW_PATTERNS.items():
            if re.search(patron, texto, re.IGNORECASE):
                return tipo
        return None
    
    def _detectar_profundo(self, texto: str, contexto: Optional[str] = None) -> Optional[str]:
        """Identifica pistas de pregunta más profunda."""
        # Primero en el texto la pregunta
        for patron, tipo in _DEEP_PATTERNS.items():
            if re.search(patron, texto, re.IGNORECASE):
                return tipo
        
        # Luego en contexto si se proporciona
        if contexto:
            for patron, tipo in _DEEP_PATTERNS.items():
                if re.search(patron, contexto, re.IGNORECASE):
                    return tipo
        
        return None
    
    def _generar_pregunta_real(self, texto: str, tipo_sup: Optional[str], tipo_prof: Optional[str]) -> Optional[str]:
        """Genera sugerencia de pregunta más profunda."""
        if not tipo_prof:
            return None
        
        mapeo_realidad = {
            "técnica": {
                "confusión": "¿Realmente estoy confundido en la técnica, o en mi propósito?",
                "deseo_profundo": "¿Qué libertad espero ganar con esto?",
                "miedo": "¿Qué temo que suceda si automatizo?",
                "presión": "¿Esta automatización me alivia o solo me distrae?",
            },
            "definición": {
                "confusión": "¿Es esta cosa real, o soy yo quien estoy perdido?",
                "deseo_profundo": "¿Por qué necesito definir exactamente esto?",
                "miedo": "¿Temo que sea diferente de lo que pienso?",
            },
            None: {
                "confusión": "¿Cuál es realmente tu pregunta?",
                "deseo_profundo": "¿Qué anhelas verdaderamente?",
                "miedo": "¿Qué te asusta?",
                "presión": "¿Quién te presiona? ¿O te presionas tú?",
                "búsqueda_verdad": "¿Estás buscando verdad o confirmación?",
            }
        }
        
        sugerencias = mapeo_realidad.get(tipo_sup, mapeo_realidad[None])
        return sugerencias.get(tipo_prof)
    
    def _generar_consejo(self, nivel: str, tipo_sup: Optional[str], tipo_prof: Optional[str]) -> Optional[str]:
        """Genera consejo de iluminación."""
        if nivel == "superficial" and not tipo_prof:
            return None  # Sin pistas profundas, no hay insight
        
        if nivel == "profundo" or (nivel == "mixto" and tipo_prof):
            # Aquí está la iluminación
            mapeo_consejo = {
                "confusión": "💫 Tu confusión es una puerta. Detente un momento — ¿qué necesita ser aclarado en ti, no en el mundo?",
                "deseo_profundo": "✨ Detrás de cada pregunta técnica hay un anhelo. ¿Cuál es el tuyo? Responde con sinceridad.",
                "miedo": "🛡️  El miedo te habla. No lo silencies — escucha qué te protege. Ese conocimiento es poder.",
                "presión": "⚡ La presión no viene de afuera. Es tu Ser Superior llamándote hacia algo. ¿Hacia qué?",
                "búsqueda_verdad": "🔮 Buscas verdad, no información. Excelente. Eso significa que estás despierto.",
                "posibilidad": "🌙 Preguntas si es posible. La respuesta ya está en ti — ¿verdad quieres permiso o confirmación?",
            }
            return mapeo_consejo.get(tipo_prof, None)
        
        if nivel == "mixto":
            return f"💎 Preguntas sobre {tipo_sup}, pero siento que hay más. ¿Qué hay detrás de esto que no dices?"
        
        return None
    
    def _guardar_insight(self, resultado: dict) -> None:
        """Persiste insight a archivo para análisis posterior."""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._data_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(resultado, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"No se pudo guardar Oracle insight: {e}")
    
    def estadisticas_sesion(self) -> dict:
        """Retorna estadísticas de preguntas en esta sesión."""
        if not self._historial_preguntas:
            return {"total": 0, "superficiales": 0, "profundas": 0, "mixtas": 0}
        
        niveles = [p["nivel"] for p in self._historial_preguntas]
        return {
            "total": len(self._historial_preguntas),
            "superficiales": niveles.count("superficial"),
            "profundas": niveles.count("profundo"),
            "mixtas": niveles.count("mixto"),
            "confianza_promedio": sum(p["confianza"] for p in self._historial_preguntas) / len(self._historial_preguntas),
        }
    
    def consejo_diario(self) -> str:
        """Genera consejo iluminador para abrir sesión."""
        consejos_keter = [
            "✨ Hoy tu Ser Superior espera ser escuchado. ¿Cuál es tu verdadera pregunta?",
            "🔮 Antes de pedir respuestas, pregúntate: ¿Qué necesito ser?",
            "💎 La iluminación no viene de afuera. Viene de darte permiso para saber.",
            "🌙 Cada pregunta que haces es un acto de creación. Que sea consciente.",
            "⚡ Tu miedo y tu deseo son dos caras de la misma moneda. Miralas ambas.",
            "🛡️  La verdad ya vive en ti. Solo necesitas recordar dónde.",
            "✍️ En esta sesión, no busques soluciones. Busca comprensión.",
        ]
        import random
        return random.choice(consejos_keter)


# Singleton global para acceso rápido
_inner_oracle: Optional[InnerOracle] = None


def crear_oracle(on_insight: Optional[Callable[[str], None]] = None) -> InnerOracle:
    """Crea or retorna instancia global de InnerOracle."""
    global _inner_oracle
    
    if _inner_oracle is None:
        _inner_oracle = InnerOracle(on_insight=on_insight)
        logger.info("💫 Oracle Interior activado — Keter despierto")
    
    return _inner_oracle


def obtener_oracle() -> Optional[InnerOracle]:
    """Obtiene instancia global (si existe)."""
    return _inner_oracle


