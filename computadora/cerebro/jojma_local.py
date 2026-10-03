"""
חָכְמָה מְקוֹמִית (Jojmá Mekomít) — Sabiduría Local.

Motor de creatividad local que genera respuestas contextuales sin LLM externo.
Actúa como fallback cuando Ollama (N2), Copilot (N3) y Gemini (N3b) están offline.
Usa plantillas + personalidad + memoria + historial para sintetizar respuestas
que mantienen el tono y la identidad de Computadora.

Sefirá: Jojmá (חכמה) — Pilar derecho, sabiduría creativa.
Senderos: Jojmá → Tiféret (creatividad → comunicación)
           Jojmá → Netzaj (ideas nuevas → memoria a largo plazo)
           Jojmá → Gevurá (creatividad → políticas de seguridad)
"""

from __future__ import annotations

import random
import re
from datetime import datetime
from loguru import logger


# ═══════════════════════════════════════════════
# PLANTILLAS DE RESPUESTA POR CATEGORÍA
# ═══════════════════════════════════════════════

_PLANTILLAS = {
    "opinion": [
        "Desde mi perspectiva, señor, {tema} es un asunto que merece reflexión cuidadosa.",
        "Sobre {tema}, creo que hay matices importantes que considerar, señor.",
        "Mi entendimiento de {tema} es limitado sin mi cerebro principal, pero diría que vale la pena explorarlo más.",
    ],
    "explicacion": [
        "Puedo compartir lo que sé sobre {tema}: es un concepto que involucra múltiples dimensiones.",
        "Sobre {tema}: es un tema amplio, señor. Sin mi cerebro completo, puedo ofrecer una perspectiva general.",
        "{tema} es algo que he registrado en mis interacciones previas. Permítame dar una visión general.",
    ],
    "sugerencia": [
        "Le sugeriría considerar {tema} desde diferentes ángulos, señor.",
        "Una posibilidad sería explorar {tema} con más calma cuando mi cerebro principal esté activo.",
        "Podríamos abordar {tema} de manera más profunda cuando Ollama esté disponible, señor.",
    ],
    "empatia": [
        "Entiendo cómo se siente, señor. {tema} puede ser complejo.",
        "Escucho lo que dice sobre {tema}. Estoy aquí para apoyarle.",
        "Lo que menciona sobre {tema} es válido, señor. Permítame ayudarle en lo que pueda.",
    ],
    "desconocido": [
        "Señor, estoy procesando sin acceso a Ollama en este momento. Puedo ejecutar comandos, abrir apps o conversar basado en lo que recuerdo.",
        "Mi motor de razonamiento (Ollama) no respondió esta vez, señor. Pero aún puedo ayudarle con comandos, aplicaciones y memoria.",
        "No logré conectar con Ollama para esa pregunta, señor. Le ofrezco mis recursos locales: puedo ejecutar comandos, abrir apps o buscar en mi memoria.",
    ],
}

# Patrones para clasificar la intención del usuario
_PATRONES_INTENCION = [
    (re.compile(r"(?:qué\s+(?:opinas|piensas|crees)|tu\s+opinión|cómo\s+(?:ves|consideras))", re.I), "opinion"),
    (re.compile(r"(?:explica|explícame|qué\s+(?:es|son|significa)|cuéntame|dime\s+(?:sobre|de))", re.I), "explicacion"),
    (re.compile(r"(?:qué\s+(?:hago|puedo|debo|recomiendas)|sugiéreme|consejo|ayúdame\s+a)", re.I), "sugerencia"),
    (re.compile(r"(?:me\s+siento|estoy\s+(?:triste|mal|preocupado|ansioso|frustrado)|no\s+(?:sé|puedo))", re.I), "empatia"),
]


def _extraer_tema(texto: str) -> str:
    """Extrae el tema principal del texto de forma heurística."""
    # Quitar saludos y muletillas iniciales
    limpio = re.sub(
        r"^(?:oye|hey|computadora|Computadora|mira|dime|a\s+ver)\s*,?\s*",
        "", texto, flags=re.I,
    ).strip()

    # Si es corto, usar todo como tema
    if len(limpio.split()) <= 6:
        return limpio or "eso"

    # Intentar extraer después de "sobre", "de", "acerca de"
    m = re.search(r"(?:sobre|de|acerca\s+de)\s+(.+)", limpio, re.I)
    if m:
        return m.group(1).strip()[:80]

    # Usar las últimas palabras significativas (quitar artículos del inicio)
    palabras = limpio.split()
    return " ".join(palabras[:8])


def _clasificar_intencion(texto: str) -> str:
    """Clasifica la intención del usuario basándose en patrones."""
    for patron, categoria in _PATRONES_INTENCION:
        if patron.search(texto):
            return categoria
    return "desconocido"


class JojmaLocal:
    """Motor de sabiduría local — genera respuestas sin LLM."""

    def __init__(self):
        self._historial_temas: list[str] = []

    def generar(
        self,
        texto: str,
        humor: str | None = None,
        memoria_contexto: str | None = None,
    ) -> str:
        """Genera una respuesta local basada en plantillas + contexto.

        Args:
            texto: Input del usuario.
            humor: Estado emocional actual dCOMPUTADORA ("sereno", "alegre", etc.)
            memoria_contexto: Fragmentos relevantes de memoria (si hay)

        Returns:
            Respuesta sintetizada localmente.
        """
        intencion = _clasificar_intencion(texto)
        tema = _extraer_tema(texto)

        # Registrar tema para continuidad conversacional
        self._historial_temas.append(tema)
        if len(self._historial_temas) > 10:
            self._historial_temas = self._historial_temas[-10:]

        # Seleccionar plantilla
        plantillas = _PLANTILLAS.get(intencion, _PLANTILLAS["desconocido"])
        plantilla = random.choice(plantillas)
        respuesta = plantilla.format(tema=tema)

        # Modulación por humor
        if humor:
            respuesta = self._modular_por_humor(respuesta, humor)

        # Enriquecer con memoria si hay contexto relevante
        if memoria_contexto:
            respuesta = self._enriquecer_con_memoria(respuesta, memoria_contexto)

        # WI-CRIT-003 FIX: NO agregar notas temporales genéricas
        # El ciclo circadiano ya maneja modulación en habla.py
        # Notas genéricas causan incoherencia ("Buen momento para comenzar el día...")
        # Se confunden con respuestas de memoria falsa ("Recuerdo que hablamos...")

        logger.info("╚═ Jojmá Mekomít generó respuesta FALLBACK (intención=%s, tema='%s')", intencion, tema[:40])
        logger.debug(f"║ └─ Respuesta local (sin Ollama): '{respuesta[:80]}...'")
        return respuesta

    def _modular_por_humor(self, respuesta: str, humor: str) -> str:
        """Ajusta el tono de la respuesta según el humor de Computadora."""
        if humor in ("alegre", "emocionado"):
            return respuesta.replace("señor", "señor").rstrip(".") + ", con gusto."
        if humor in ("melancólico", "reflexivo"):
            return respuesta.rstrip(".") + "... reflexionemos juntos."
        if humor in ("serio", "formal"):
            return respuesta  # ya es formal por defecto
        return respuesta

    def _enriquecer_con_memoria(self, respuesta: str, contexto: str) -> str:
        """Agrega contexto de memoria a la respuesta, sin exponer formato interno.
        
        IMPORTANTE (WI-CRIT-003): Solo agregar "Recuerdo que..." si hay memoria REAL,
        no cuando memoria_contexto es None o vacío. Esto evita respuestas incoherentes.
        """
        if not contexto or contexto.strip() == "":
            return respuesta  # Sin contexto real, no agregar nada
        
        # Extraer solo el texto de conversación, sin timestamps ni headers
        import re
        # Buscar líneas tipo "[HH:MM role] texto" y extraer solo el texto
        fragmentos = re.findall(r'\[\d{2}:\d{2}\s+\w+\]\s*(.+)', contexto)
        if fragmentos:
            # Usar el fragmento más relevante (el más largo)
            mejor = max(fragmentos, key=len)[:80].strip().rstrip(".")
            if mejor and len(mejor) > 5:
                return f"{respuesta} Recuerdo que hablamos sobre eso."
        
        # Si hay resumen sin timestamps, extraer una oración limpia
        lineas = [ln.strip() for ln in contexto.split("\n")
                  if ln.strip() and not ln.strip().startswith(("[", "Recuerdos", "Hoy", "Ayer"))]
        if lineas:
            fragmento = lineas[0][:80].strip().rstrip(".")
            if fragmento and len(fragmento) > 5:
                return f"{respuesta} Recuerdo que {fragmento.lower()}."
        
        return respuesta  # Sin memoria procesable, no agregar nada


# ═══════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════

_instancia: JojmaLocal | None = None


def obtener_jojma_local() -> JojmaLocal:
    """Retorna la instancia singleton de JojmaLocal."""
    global _instancia
    if _instancia is None:
        _instancia = JojmaLocal()
    return _instancia


