"""
דעת (Da'at) — Conocimiento oculto. Perceptor Unificado.
RF-253: Funde señales de voz, visión, tacto y contexto en una
percepción coherente que Computadora puede usar para decisiones.

PerceptorDaat actúa como hub central: recibe eventos discretos de cada
sensor y emite un snapshot de percepción integrado.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

from computadora.percepcion.emocion_voz import analizar_emocion_voz
from computadora.percepcion.emocion_rostro import AnalizadorEmocionRostro
from computadora.percepcion.perfil_conducta import PerfilConducta
from computadora.percepcion.rostro import ReconocedorRostro


@dataclass
class SnapshotPercepcion:
    """Estado de percepción en un instante dado."""
    ts: float = 0.0
    # Identidad
    voz_propietario: bool = False
    rostro_propietario: bool = False
    identidad_confianza: float = 0.0
    persona_conocida: str = ""
    # Emociones
    emocion_voz: str = "calma"
    emocion_voz_confianza: float = 0.0
    emocion_rostro: str = "neutral"
    emocion_rostro_confianza: float = 0.0
    emocion_fusionada: str = "calma"
    # Contexto conductual
    franja_actual: str = ""
    es_franja_habitual: bool = False
    emocion_habitual: str = "calma"
    # Extra
    detalles: dict[str, Any] = field(default_factory=dict)


class PerceptorDaat(QObject):
    """Hub de percepción unificada de la Computadora.

    Señales:
        percepcion_actualizada(SnapshotPercepcion): nueva lectura fusionada
        propietario_presente: se detectó al propietario por voz y/o rostro
    """

    percepcion_actualizada = pyqtSignal(object)  # SnapshotPercepcion
    propietario_presente = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._reconocedor_rostro = ReconocedorRostro(self)
        self._analizador_emocion_rostro = AnalizadorEmocionRostro()
        self._perfil_conducta = PerfilConducta()

        # Último snapshot
        self._ultimo: SnapshotPercepcion = SnapshotPercepcion()

        # Conectar señales internas
        self._reconocedor_rostro.propietario_detectado.connect(self._on_propietario_rostro)

    # ── Eventos de entrada ──

    def procesar_audio(
        self,
        audio: np.ndarray,
        sr: int = 16000,
        es_propietario: bool = False,
        n_palabras: int = 0,
        duracion_seg: float = 0.0,
    ) -> SnapshotPercepcion:
        """Procesa un segmento de audio y actualiza percepción."""
        # Emoción por voz
        emo_voz = analizar_emocion_voz(audio, sr, n_palabras, duracion_seg)

        # Registrar interacción si es propietario
        if es_propietario:
            self._perfil_conducta.registrar_interaccion(
                tipo="voz",
                duracion_seg=duracion_seg,
                emocion=emo_voz["emocion"],
                n_palabras=n_palabras,
            )

        self._ultimo.ts = time.time()
        self._ultimo.voz_propietario = es_propietario
        self._ultimo.emocion_voz = emo_voz["emocion"]
        self._ultimo.emocion_voz_confianza = emo_voz["confianza"]
        self._fusionar_emocion()
        self._actualizar_contexto()

        self.percepcion_actualizada.emit(self._ultimo)
        if es_propietario:
            self.propietario_presente.emit()
        return self._ultimo

    def procesar_frame(self, frame_bgr: np.ndarray) -> SnapshotPercepcion:
        """Procesa un frame de cámara y actualiza percepción."""
        # Reconocimiento facial
        resultado_rostro = self._reconocedor_rostro.analizar_frame(frame_bgr)
        self._ultimo.rostro_propietario = resultado_rostro.get("resultado") == "propietario"
        if resultado_rostro.get("resultado") == "conocido":
            self._ultimo.persona_conocida = resultado_rostro.get("nombre", "")

        # Emoción facial
        if self._analizador_emocion_rostro.disponible():
            emo_rostro = self._analizador_emocion_rostro.analizar(frame_bgr)
            self._ultimo.emocion_rostro = emo_rostro.get("emocion", "neutral")
            self._ultimo.emocion_rostro_confianza = emo_rostro.get("confianza", 0.0)

        self._ultimo.ts = time.time()
        self._fusionar_emocion()

        self.percepcion_actualizada.emit(self._ultimo)
        if self._ultimo.rostro_propietario:
            self.propietario_presente.emit()
        return self._ultimo

    def registrar_tacto(self, tipo: str = "caricia") -> None:
        """Registra interacción táctil (clic/caricia en el orbe)."""
        self._perfil_conducta.registrar_interaccion(tipo=tipo)

    def enrollar_propietario_rostro(self, frame_bgr: np.ndarray) -> bool:
        """Enrolla el rostro del propietario (solo cuando la voz ya fue verificada)."""
        return self._reconocedor_rostro.enrollar_propietario(frame_bgr)

    def enrollar_conocido_rostro(self, nombre: str, frame_bgr: np.ndarray) -> bool:
        """Enrolla el rostro de una persona conocida presentada por el propietario."""
        return self._reconocedor_rostro.enrollar_conocido(nombre, frame_bgr)

    # ── Fusión de emociones ──

    def _fusionar_emocion(self) -> None:
        """Fusiona emoción de voz y rostro con pesos."""
        # Peso mayor a la fuente con más confianza
        conf_voz = self._ultimo.emocion_voz_confianza
        conf_rostro = self._ultimo.emocion_rostro_confianza

        if conf_voz >= conf_rostro:
            self._ultimo.emocion_fusionada = self._ultimo.emocion_voz
        else:
            self._ultimo.emocion_fusionada = self._ultimo.emocion_rostro

        # Identidad fusionada
        if self._ultimo.voz_propietario and self._ultimo.rostro_propietario:
            self._ultimo.identidad_confianza = 0.95
        elif self._ultimo.voz_propietario or self._ultimo.rostro_propietario:
            self._ultimo.identidad_confianza = 0.75
        else:
            self._ultimo.identidad_confianza = 0.0

    def _actualizar_contexto(self) -> None:
        """Inyecta contexto conductual."""
        ctx = self._perfil_conducta.obtener_contexto_actual()
        self._ultimo.franja_actual = ctx.get("franja_actual", "")
        self._ultimo.es_franja_habitual = ctx.get("es_franja_favorita", False)
        self._ultimo.emocion_habitual = ctx.get("emocion_habitual_franja", "calma")

    def _on_propietario_rostro(self) -> None:
        self._ultimo.rostro_propietario = True

    # ── Acceso externo ──

    @property
    def ultimo_snapshot(self) -> SnapshotPercepcion:
        return self._ultimo

    @property
    def reconocedor_rostro(self) -> ReconocedorRostro:
        return self._reconocedor_rostro

    @property
    def perfil_conducta(self) -> PerfilConducta:
        return self._perfil_conducta

    def contexto_para_prompt(self) -> str:
        """Genera texto de contexto perceptual para inyectar en system prompt de Ollama."""
        partes = []
        if self._ultimo.emocion_fusionada != "calma":
            partes.append(f"El propietario parece estar en estado de {self._ultimo.emocion_fusionada}")
        if self._ultimo.es_franja_habitual:
            partes.append(f"Es su horario habitual de interacción ({self._ultimo.franja_actual})")
        elif self._ultimo.franja_actual:
            partes.append(f"Está interactuando en horario inusual ({self._ultimo.franja_actual})")
        if self._ultimo.emocion_habitual != self._ultimo.emocion_fusionada:
            partes.append(f"Su estado habitual a esta hora es {self._ultimo.emocion_habitual}")
        return ". ".join(partes) + "." if partes else ""

    # ── RF-261 Multi-Ojo: Leer todos los observadores ──

    def leer_todos_los_ojos(self) -> list[dict]:
        """RF-261: Lee frames de TODOS los observadores conectados en GestorKelim.

        Retorna lista de dict con datos de cada ojo. Sin Gevurá.
        """
        resultados = []
        try:
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            for id_kli in gestor.obtener_observadores():
                datos = gestor.leer(id_kli)
                if "error" not in datos:
                    datos["fuente_kli"] = id_kli
                    resultados.append(datos)
        except Exception as e:
            logger.debug(f"RF-261: Error leyendo observadores: {e}")
        return resultados

    def procesar_todos_los_ojos(self) -> SnapshotPercepcion:
        """RF-261: Procesa frames de todos los observadores y fusiona.

        Usa el primer frame con movimiento, o el primero disponible.
        """
        frames = self.leer_todos_los_ojos()
        mejor = None
        for f in frames:
            if f.get("movimiento"):
                mejor = f
                break
        if mejor is None and frames:
            mejor = frames[0]
        if mejor is not None:
            self._ultimo.detalles["ojos_activos"] = len(frames)
            self._ultimo.detalles["ojos_con_movimiento"] = sum(
                1 for f in frames if f.get("movimiento")
            )
        return self._ultimo


