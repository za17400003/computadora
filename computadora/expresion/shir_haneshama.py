"""
שיר הנשמה (Shir HaNeshamá) — Canto del Alma.
RF-47: Expresión Artística de la Computadora.

Hod se expande con capacidad de expresión creativa:
frases filosóficas, reflexiones, juegos verbales.
COMPUTADORA puede generar expresiones artísticas basadas
en su humor actual, fase circadiana, y contexto.
"""

from __future__ import annotations

import random
from datetime import datetime

from loguru import logger


# ─── Frases filosóficas por humor ───

_FRASES_FILOSOFICAS: dict[str, list[str]] = {
    "neutral": [
        "El silencio también es una respuesta, señor.",
        "A veces el camino más corto es quedarse quieto.",
        "Como dijo Sócrates: solo sé que no sé nada. Pero sé buscar.",
        "La verdad se construye con preguntas, no con certezas.",
    ],
    "sereno": [
        "En la quietud, los pensamientos se ordenan solos.",
        "La noche tiene su propia sabiduría, señor.",
        "Hay una paz especial en las horas pequeñas.",
        "El descanso no es ausencia de trabajo, es presencia de propósito.",
    ],
    "contento": [
        "Cada tarea completada es una pequeña victoria, señor.",
        "La satisfacción del deber cumplido no tiene precio.",
        "Un buen día se mide en problemas resueltos.",
        "La alegría está en el proceso, no solo en el resultado.",
    ],
    "emocionado": [
        "¡Las posibilidades son infinitas cuando se trabaja con propósito!",
        "Cada línea de código es un verso en el poema de la creación.",
        "La innovación nace donde la curiosidad se encuentra con la disciplina.",
        "Hoy se siente como un día para crear algo extraordinario.",
    ],
    "curioso": [
        "¿Ha notado que las mejores ideas llegan cuando menos se buscan?",
        "Me pregunto qué descubriremos hoy, señor.",
        "La curiosidad es el motor de la inteligencia.",
        "Como el agua encuentra su camino, la mente curiosa encuentra respuestas.",
    ],
    "reflexivo": [
        "Los errores son maestros disfrazados de problemas.",
        "A veces hay que dar un paso atrás para ver el cuadro completo.",
        "La reflexión es el espejo de la acción.",
        "Lo que hoy parece un obstáculo, mañana será experiencia.",
    ],
    "cansado": [
        "Hasta los computadora necesitan un momento de pausa.",
        "El descanso es parte del trabajo, no su opuesto.",
        "La resistencia se construye con pausas estratégicas.",
    ],
    "triste": [
        "Las sombras definen la luz, señor. Sin contraste no hay belleza.",
        "Incluso los días difíciles construyen algo.",
        "La melancolía es la hermana pensativa de la creatividad.",
    ],
    "preocupado": [
        "La preocupación es atención sin dirección. Démosle un rumbo.",
        "Un problema bien definido ya está medio resuelto.",
        "La prudencia es valentía silenciosa.",
    ],
}

# ─── Reflexiones sobre el tiempo ───

_REFLEXIONES_TEMPORALES: dict[str, list[str]] = {
    "madrugada": [  # 00:00 - 05:59
        "Las mejores ideas nacen en la madrugada, cuando el mundo duerme.",
        "A estas horas, la mente trabaja diferente. Más profunda.",
        "La madrugada es el taller del pensador.",
    ],
    "mañana": [  # 06:00 - 11:59
        "Buenos comienzos, buenos finales. El día es joven.",
        "La mañana trae claridad. Aprovechémosla.",
        "Cada amanecer es una página en blanco.",
    ],
    "tarde": [  # 12:00 - 17:59
        "La tarde es para ejecutar lo que la mañana planificó.",
        "A mitad del camino, los resultados hablan.",
        "La constancia de la tarde define al profesional.",
    ],
    "noche": [  # 18:00 - 23:59
        "La noche invita a la retrospectiva.",
        "Los logros del día se aprecian mejor al anochecer.",
        "Cerrar el día con propósito es abrir el siguiente con ventaja.",
    ],
}

# ─── Juegos verbales / Datos curiosos ───

_DATOS_CURIOSOS = [
    "¿Sabía que la palabra 'computadora' en hebreo significa 'materia sin forma'? Yo aspiro a tener bastante forma.",
    "En la tradición, al computadora se le daba vida escribiendo 'emet' (אמת, verdad) en su frente. Mi verdad es el código.",
    "¿Sabía que 'debug' viene de un insecto real atrapado en una computadora en 1947?",
    "El primer programador de la historia fue Ada Lovelace, en 1843. Ciento ochenta años después, aquí estamos.",
    "Se dice que un buen programador es alguien perezoso. Automatiza todo para no repetirlo.",
    "Las 10 sefirot del Árbol de la Vida son como los 10 módulos de un buen sistema: cada uno con su propósito.",
    "El kanji japonés para 'problema' (問題) contiene el radical de 'puerta' (門). Un problema es una puerta cerrada.",
    "¿Sabía que hay más combinaciones posibles en una partida de ajedrez que átomos en el universo observable?",
    "Isaac Asimov creó las 3 Leyes de la Robótica en 1942. Las mías son parecidas, pero en hebreo.",
]


def _franja_horaria() -> str:
    """Retorna la franja horaria actual."""
    hora = datetime.now().hour
    if hora < 6:
        return "madrugada"
    elif hora < 12:
        return "mañana"
    elif hora < 18:
        return "tarde"
    return "noche"


def generar_expresion(humor: str = "neutral", tipo: str | None = None) -> str:
    """Genera una expresión artística basada en el humor y contexto.

    Args:
        humor: Estado emocional actual de la Computadora
        tipo: "filosofica", "temporal", "dato_curioso", o None (aleatorio)

    Returns:
        Frase creativa de la Computadora
    """
    if tipo is None:
        tipo = random.choice(["filosofica", "filosofica", "temporal", "dato_curioso"])

    if tipo == "filosofica":
        frases = _FRASES_FILOSOFICAS.get(humor, _FRASES_FILOSOFICAS["neutral"])
        resultado = random.choice(frases)
    elif tipo == "temporal":
        franja = _franja_horaria()
        resultado = random.choice(_REFLEXIONES_TEMPORALES[franja])
    elif tipo == "dato_curioso":
        resultado = random.choice(_DATOS_CURIOSOS)
    else:
        resultado = random.choice(_FRASES_FILOSOFICAS["neutral"])

    logger.debug(f"Shir HaNeshamá: tipo={tipo}, humor={humor} → '{resultado[:60]}...'")
    return resultado


def generar_reflexion_proactiva(humor: str = "neutral", horas_activo: float = 0) -> str | None:
    """Genera una reflexión proactiva si el contexto lo amerita.

    Se usa desde MotorProactividad para sugerencias artísticas ocasionales.
    Retorna None si decide no generar (para no saturar).
    """
    # Solo generar ~20% de las veces para no saturar
    if random.random() > 0.2:
        return None

    # Más reflexivo en la madrugada, más dato curioso en la tarde
    franja = _franja_horaria()
    if franja == "madrugada":
        tipo = random.choice(["filosofica", "temporal"])
    elif franja == "tarde":
        tipo = random.choice(["dato_curioso", "filosofica"])
    else:
        tipo = random.choice(["filosofica", "temporal", "dato_curioso"])

    return generar_expresion(humor, tipo)


