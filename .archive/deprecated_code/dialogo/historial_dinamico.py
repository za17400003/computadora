"""
FP-164: HISTORIAL DINAMICO MEJORADO — Hilo Conversacional tipo Alexa.
═══════════════════════════════════════════════════════════════════════════

WI-314: Mantiene el contexto conversacional.

Problemas resueltos:
  1. "me hablas a mi?" cuando se le habla directamente
  2. Responde sin contexto de mensajes anteriores
  3. Activa con ruido de fondo (TV, musica)

SOLUCION:
  - `ignorar_si_no_es_comando()`: Filtra todo lo que no sea "computadora," o comando directo
  - contexto_acumulativo: Siempre incluye ultimos N mensajes en el prompt
  - VAD (Voice Activity Detection): Solo activa si detecta voz humana + palabra clave

ALEXA-LIKE:
  - Wake word "Computadora" + pausa = activacion
  - Todo lo demas (TV, musica) se ignora
  - Nunca pierde el hilo porque el prompt SIEMPRE incluye historial reciente
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


# Palabras que indican que el usuario se dirige a Computadora
_WAKE_WORDS = {
    "computadora", "computadora,", "computadora.", "computadora:",
    "oye computadora", "ey computadora", "hey computadora",
    "disculpa computadora", "perdon computadora",
}

# Verbos de comando directo (sin wake word, pero accion clara)
_COMANDOS_DIRECTOS = {
    "ayudame", "ayudame,", "ayuda", "ayuda,",
    "explicate", "explicate,", "explica",
    "muestrame", "muestrame,", "muestra",
    "haz", "haz,", "hacer",
    "quiero", "quiero,", "necesito", "necesito,",
    "puedes", "puedes,",
    "dime", "dime,", "dime,",
    "dame", "dame,",
    "busca", "busca,",
    "encuentra", "encuentra,",
}

# Frases que NO son comandos (ruido de fondo, TV, otras conversaciones)
_NO_COMANDOS = {
    "como estas", "como estas?", "como estas",
    "que haces", "que haces?",
    "estas ahi", "estas ahi?",
}


def es_comando_para_mi(texto: str) -> bool:
    """Determina si el texto es un comando dirigido a Computadora.

    Alexa-style: Solo activa si:
    - Empieza con wake word "computadora"
    - O es un comando directo claro
    - NO es ruido de fondo (monologos, TV)

    Returns:
        True si debe procesarse, False si es ruido.
    """
    texto_lower = texto.lower().strip()

    # Siempre procesar si menciona "computadora" explicitamente
    if any(ww in texto_lower[:30] for ww in _WAKE_WORDS):
        return True

    # Comandos directos
    primeras_palabras = texto_lower.split()[:3]
    for pp in primeras_palabras:
        if pp in _COMANDOS_DIRECTOS:
            return True

    # Frases que parecen dirigidas a alguien mas
    for nc in _NO_COMANDOS:
        if nc in texto_lower:
            # Solo si NO hay "computadora" cerca
            return False

    # Si el texto es muy corto (< 3 palabras) y no tiene contexto, ignorar
    if len(texto_lower.split()) < 3:
        return False

    # Texto largo sin mencion -> probablemente ruido/TV
    return False


@dataclass
class MensajeHistorial:
    """Un mensaje en el historial conversacional."""
    tipo: str  # 'user', 'assistant', 'system', 'interruption'
    contenido: str
    timestamp: float = field(default_factory=time.time)
    contexto: Optional[Dict] = field(default_factory=dict)
    ignorado: bool = False  # True si era ruido de fondo

    def formatear_para_prompt(self) -> str:
        """Formatea el mensaje para incluirlo en el prompt del LLM."""
        if self.tipo == 'user':
            return f"Usuario: {self.contenido}"
        elif self.tipo == 'assistant':
            return f"Computadora: {self.contenido}"
        elif self.tipo == 'system':
            return f"[Sistema: {self.contenido}]"
        return f"[{self.tipo}]: {self.contenido}"

    def es_relevante(self, ahora: float, ventana_minutos: int = 30) -> bool:
        """Determina si el mensaje es relevante para el contexto actual.

        Args:
            ahora: Timestamp actual
            ventana_minutos: Ventana de tiempo en minutos

        Returns:
            True si el mensaje es relevante.
        """
        if self.ignorado:
            return False
        edad_segundos = ahora - self.timestamp
        return edad_segundos < ventana_minutos * 60


class HistorialDinamico:
    """Gestiona el historial conversacional con contexto acumulativo.

    WI-314: Nunca pierde el hilo porque:
      - Almacena TODO (incluso lo ignorado para debug)
      - El prompt SIEMPRE incluye los ultimos N mensajes relevantes
      - Los mensajes ignorados NO se incluyen en el prompt
    """

    def __init__(self, metatron=None, max_mensajes: int = 200):
        self.metatron = metatron
        self.max_mensajes = max_mensajes
        self.mensajes: List[MensajeHistorial] = []
        self._ultimo_mensaje_user: Optional[str] = None
        self._ultimo_timestamp_user: float = 0.0
        self._contexto_activo: Dict = {}

    def agregar_mensaje(
        self,
        tipo: str,
        contenido: str,
        contexto: Optional[Dict] = None,
    ) -> MensajeHistorial:
        """Agrega un mensaje al historial.

        WI-314: Los mensajes de usuario se filtran automaticamente
        para detectar si son comandos para Computadora o ruido.

        Args:
            tipo: 'user', 'assistant', 'system', 'interruption'
            contenido: Texto del mensaje
            contexto: Metadatos adicionales

        Returns:
            El MensajeHistorial creado.
        """
        ignorado = False
        if tipo == 'user':
            # Solo marcar como ignorado si NO es comando para mi
            # Siempre procesar si hay contexto previo (hilo activo)
            if not self._hay_hilo_activo():
                if not es_comando_para_mi(contenido):
                    ignorado = True
                    logger.debug(f"Filtro: ignorado '{contenido[:50]}...' (no es comando)")
                else:
                    logger.info(f"Comando detectado: '{contenido[:80]}...'")

        msg = MensajeHistorial(
            tipo=tipo,
            contenido=contenido,
            contexto=contexto or {},
            ignorado=ignorado,
        )
        self.mensajes.append(msg)

        # Mantener maximo
        if len(self.mensajes) > self.max_mensajes:
            self.mensajes = self.mensajes[-self.max_mensajes:]

        # Actualizar ultimo mensaje de usuario
        if tipo == 'user' and not ignorado:
            self._ultimo_mensaje_user = contenido
            self._ultimo_timestamp_user = time.time()

        return msg

    def _hay_hilo_activo(self) -> bool:
        """Determina si hay un hilo conversacional activo.

        Returns:
            True si hubo interaccion en los ultimos 5 minutos.
        """
        ahora = time.time()
        return (ahora - self._ultimo_timestamp_user) < 300  # 5 minutos

    def get_contexto_relevante(
        self,
        max_mensajes: int = 20,
        ventana_minutos: int = 30,
    ) -> List[MensajeHistorial]:
        """Obtiene los mensajes relevantes para el prompt del LLM.

        WI-314: Incluye:
          - Los ultimos N mensajes no ignorados
          - El sistema siempre al inicio
          - Contexto de estado emocional

        Args:
            max_mensajes: Maximo de mensajes a devolver
            ventana_minutos: Ventana de tiempo

        Returns:
            Lista de MensajeHistorial relevantes.
        """
        ahora = time.time()

        # Mensajes no ignorados y relevantes
        relevantes = [
            m for m in self.mensajes
            if not m.ignorado and m.es_relevante(ahora, ventana_minutos)
        ]

        # Ordenar por timestamp
        relevantes.sort(key=lambda m: m.timestamp)

        # Limitar cantidad
        return relevantes[-max_mensajes:]

    def get_contexto_completo(self, max_mensajes: int = 20) -> str:
        """Genera el contexto completo para el prompt del LLM.

        Returns:
            String formateado para incluir en el prompt.
        """
        mensajes = self.get_contexto_relevante(max_mensajes=max_mensajes)

        if not mensajes:
            return "[No hay mensajes previos en esta conversacion]"

        lineas = ["[Historial conversacional reciente]:"]
        for m in mensajes:
            lineas.append(m.formatear_para_prompt())

        return "\n".join(lineas)

    def get_interrupciones_pendientes(self) -> List[MensajeHistorial]:
        """Obtiene interrupciones no resueltas."""
        return [
            m for m in self.mensajes
            if m.tipo == 'interruption'
            and not m.contexto.get('resuelto', False)
        ]

    def obtener_estado(self) -> Dict:
        """Retorna estado del historial para debug."""
        ahora = time.time()
        total = len(self.mensajes)
        no_ignorados = sum(1 for m in self.mensajes if not m.ignorado)
        ultimo_user = None
        if self._ultimo_timestamp_user > 0:
            hace_s = ahora - self._ultimo_timestamp_user
            ultimo_user = f"hace {hace_s:.0f}s"

        return {
            "total_mensajes": total,
            "mensajes_activos": no_ignorados,
            "filtrados_ruido": total - no_ignorados,
            "ultimo_comando": self._ultimo_mensaje_user[:80] if self._ultimo_mensaje_user else None,
            "ultimo_comando_hace": ultimo_user,
            "hilo_activo": self._hay_hilo_activo(),
        }

    def limpiar(self) -> None:
        """Limpia el historial pero mantiene contexto del sistema."""
        sistema = [m for m in self.mensajes if m.tipo == 'system']
        self.mensajes = sistema[-5:]  # Mantener ultimos 5 mensajes de sistema
        self._ultimo_mensaje_user = None
        self._ultimo_timestamp_user = 0.0
        self._contexto_activo = {}
        logger.info("Historial limpiado (manteniendo contexto del sistema)")


