"""
מלכות (Maljut) — Reino. Manifestación en el mundo material.
Presencia de la Computadora — Esfera de obsidiana pulida con grabados cabalísticos.
Flota sobre el escritorio sin marco ni fondo visible.
Partículas, letras hebreas orbitantes, geometría sagrada.
El usuario ve a través de Maljut todo el Árbol de la Vida.
"""

import collections
import json
import math
import random
import re
import subprocess
import sys
import threading
import time
from enum import Enum

from PyQt6.QtCore import (
    Qt, QTimer, pyqtSlot, pyqtSignal, QPoint, QPointF, QThread, QRectF,
    QCoreApplication, QEvent,
)
from PyQt6.QtGui import (
    QColor, QCursor, QPainter, QRadialGradient, QAction,
    QFont, QPen,
    QIcon, QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from loguru import logger
from pathlib import Path

from computadora.nucleo.orquestador import Orquestador
from computadora.voz.escucha import HiloEscucha
from computadora.voz.habla import HiloHabla
from computadora.habilidades.sistema import set_callback_recordatorio
from computadora.interfaz.vida_autonoma import VidaAutonoma, EstadoPresencia
from computadora.memoria.personalidad import Personalidad
from computadora.utilidades.windows import ContextoPantalla
from computadora.habilidades.monitor_sistema import obtener_monitor
from computadora.nucleo.proactividad import MotorProactividad
from computadora.nucleo.hot_reload import HotReloader
from computadora.interfaz.ventana_keter import VentanaKeter
from computadora.interfaz.configuracion_visual_dev import ConfiguracionVisualDev
from computadora.interfaz.tema_visual import ThemeFactory


# FP-027: FSM extraída a módulo independiente
from computadora.interfaz.fsm_computadora import (
    EstadoMaljut,
    TRANSICIONES_VALIDAS as _TRANSICIONES_VALIDAS,
    STR_A_ESTADO as _STR_A_ESTADO,
)

# WI-CRIT-002: Evento thread-safe para cambios de fase circadiana


class _FaseEvent(QEvent):
    """Evento personalizado para cambios de fase thread-safe."""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, fase: str):
        super().__init__(self.EVENT_TYPE)
        self.fase = fase


# ═══════════════════════════════════════════════
# WORKER — Procesamiento LLM fuera del hilo principal
# ═══════════════════════════════════════════════


class HiloPensamiento(QThread):
    """Ejecuta orquestador.procesar() sin bloquear Qt."""

    respuesta_lista = pyqtSignal(str)
    error_ocurrido = pyqtSignal(str)
    nivel_cambio = pyqtSignal(str)           # "nivel1"|"nivel2"|"nivel3"
    herramienta_usada = pyqtSignal(str, str)  # nombre, estado
    permiso_copilot = pyqtSignal(str)        # pregunta al usuario
    movimiento_solicitado = pyqtSignal(str)  # "esquivar"|"hogar"
    fin_conversacion = pyqtSignal()            # cierra ventana conversatoria
    despedida_guardian = pyqtSignal()           # usuario se va → activar modo guardián
    fragmento_listo = pyqtSignal(str)          # streaming TTS por oración
    progreso_tarea = pyqtSignal(str, str, str)  # nombre_tool, estado, categoria
    preguntar_modo_tarea = pyqtSignal(str)     # pregunta bg/fg al usuario
    enroll_persona = pyqtSignal(str)             # nombre de persona a registrar voz
    bloqueo_seguridad = pyqtSignal(str)            # categoría de rechazo ético (Gevurá)
    tzimtzum_solicitado = pyqtSignal(str)           # razón del Tzimtzum ("comando"|"idle")
    # FP-022: Canal bidireccional Tiféret→Maljut
    confianza_respuesta = pyqtSignal(float)          # 0.0-1.0 confianza del NLU
    complejidad_procesamiento = pyqtSignal(int)      # 1-3 carga cognitiva
    frustracion_detectada = pyqtSignal(bool)         # True si frustración del usuario

    def __init__(self, orquestador: Orquestador, texto: str):
        super().__init__()
        self._orquestador = orquestador
        self._texto = texto
        # Sincronización para el gate de Copilot
        self._copilot_gate_event = threading.Event()
        self._copilot_gate_respuesta = None  # str o None (rechazado)

    def _on_nivel(self, nivel: str):
        self.nivel_cambio.emit(nivel)

    def _on_herramienta(self, nombre: str, estado: str):
        self.herramienta_usada.emit(nombre, estado)

    def _on_movimiento(self, tipo: str):
        self.movimiento_solicitado.emit(tipo)

    def _on_fin_conversacion(self):
        self.fin_conversacion.emit()

    def _on_despedida_guardian(self):
        self.despedida_guardian.emit()

    def _on_fragmento(self, texto: str):
        self.fragmento_listo.emit(texto)

    def _on_progreso(self, nombre: str, estado: str, categoria: str):
        self.progreso_tarea.emit(nombre, estado, categoria)

    def _on_enroll_persona(self, nombre: str):
        self.enroll_persona.emit(nombre)

    def _on_bloqueo_seguridad(self, categoria: str):
        self.bloqueo_seguridad.emit(categoria)

    def _on_tzimtzum(self, razon: str):
        self.tzimtzum_solicitado.emit(razon)

    # FP-022: Callbacks del canal bidireccional
    def _on_confianza(self, valor: float):
        self.confianza_respuesta.emit(valor)

    def _on_complejidad(self, valor: int):
        self.complejidad_procesamiento.emit(valor)

    def _on_frustracion(self, detectada: bool):
        self.frustracion_detectada.emit(detectada)

    def _on_preguntar_modo(self, pregunta: str) -> bool:
        """Llamado desde hilo worker. Emite señal, espera respuesta del usuario."""
        self._modo_tarea_event = threading.Event()
        self._modo_tarea_es_bg = True  # default: segundo plano
        self.preguntar_modo_tarea.emit(pregunta)
        # Esperar respuesta (máx 30s)
        if self._modo_tarea_event.wait(timeout=30):
            return self._modo_tarea_es_bg
        return True  # Timeout = segundo plano

    def responder_modo_tarea(self, es_bg: bool):
        """Llamado desde hilo principal Qt con la respuesta del usuario."""
        self._modo_tarea_es_bg = es_bg
        if hasattr(self, '_modo_tarea_event'):
            self._modo_tarea_event.set()

    def _solicitar_permiso_copilot(self, texto: str):
        """Llamado desde el hilo worker. Emite señal y bloquea hasta recibir respuesta."""
        self._copilot_gate_event.clear()
        self._copilot_gate_respuesta = None
        self.permiso_copilot.emit(texto)
        # Esperar respuesta del usuario (máx 60s)
        if self._copilot_gate_event.wait(timeout=60):
            return self._copilot_gate_respuesta
        return None  # Timeout = no autorizado

    def responder_gate_copilot(self, respuesta):
        """Llamado desde el hilo principal de Qt con la respuesta del usuario."""
        self._copilot_gate_respuesta = respuesta
        self._copilot_gate_event.set()

    def run(self):
        try:
            self._orquestador.set_callbacks(
                on_nivel=self._on_nivel,
                on_herramienta=self._on_herramienta,
                on_movimiento=self._on_movimiento,
                solicitar_permiso_copilot=self._solicitar_permiso_copilot,
                on_fin_conversacion=self._on_fin_conversacion,
                on_despedida_guardian=self._on_despedida_guardian,
                on_fragmento=self._on_fragmento,
                on_progreso=self._on_progreso,
                on_preguntar_modo=self._on_preguntar_modo,
                on_enroll_persona=self._on_enroll_persona,
                on_bloqueo_seguridad=self._on_bloqueo_seguridad,
                on_tzimtzum=self._on_tzimtzum,
                # FP-022: Canal bidireccional
                on_confianza=self._on_confianza,
                on_complejidad=self._on_complejidad,
                on_frustracion=self._on_frustracion,
            )
            respuesta = self._orquestador.procesar(self._texto)
            self.respuesta_lista.emit(respuesta)
        except Exception as e:
            logger.error(f"Error en pensamiento: {e}")
            self.error_ocurrido.emit(str(e))


# ═══════════════════════════════════════════════
# PARTÍCULAS CABALÍSTICAS
# ═══════════════════════════════════════════════

# Letras hebreas del Shem HaMephorash y Sefirot
LETRAS_HEBREAS = list("אבגדהוזחטיכלמנסעפצקרשת")
SEFIROT = ["כתר", "חכמה", "בינה", "חסד", "גבורה", "תפארת", "נצח", "הוד", "יסוד", "מלכות"]


class Particula:
    """Una partícula flotante alrededor del orbe."""

    def __init__(self, radio_orbita: float):
        self.angulo = random.uniform(0, 2 * math.pi)
        self.radio = radio_orbita + random.uniform(-15, 15)
        self.velocidad = random.uniform(0.003, 0.015) * random.choice([-1, 1])
        self.tamano = random.uniform(1.0, 3.0)
        self.alpha = random.uniform(0.2, 0.7)
        self.alpha_objetivo = self.alpha
        self.vida = random.uniform(60, 300)  # frames
        self.edad = 0
        self.es_letra = random.random() < 0.15
        self.letra = random.choice(LETRAS_HEBREAS) if self.es_letra else ""
        # Física de inercia (FP-024 Pilar A — RF-87)
        self.vx = 0.0
        self.vy = 0.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.masa = 2.0 if self.es_letra else random.uniform(0.5, 1.5)
        self.coef_arrastre = 0.92
        self.coef_retorno = 0.03

    def actualizar(self, delta_x: float = 0.0, delta_y: float = 0.0, speed_mult: float = 1.0):
        # velocidad angular escalada por contexto visual (p.ej. Dmut.particulas_mod)
        self.angulo += self.velocidad * speed_mult
        self.edad += 1

        # FIX (percepción de "aceleración"): la velocidad angular base de una
        # partícula es muy chica (0.003-0.015 rad/frame), así que aunque
        # speed_mult la duplique o triplique el cambio sigue siendo sutil en
        # pantalla — una partícula de 1-3px apenas rota más rápido no se lee
        # como "energía". Para que un humor como "emocionado" (particulas_mod
        # alto) o "cansado" (bajo) se note de verdad, se suma una leve
        # "respiración" radial oscilante cuando speed_mult se aleja de 1.0,
        # reusando el mismo sistema de resorte (vx/vy/offset_x/offset_y) que
        # ya existe para la inercia de arrastre del orbe, en vez de inventar
        # un sistema nuevo. El retorno elástico (coef_retorno) y el arrastre
        # viscoso (coef_arrastre) de abajo, más el clamp de offset, evitan que
        # esto se descontrole — queda un pulso sutil, no una explosión.
        _jitter_mag = speed_mult - 1.0
        if abs(_jitter_mag) > 0.02:
            _dir_x = math.cos(self.angulo)
            _dir_y = math.sin(self.angulo)
            _fase_resp = self.edad * (0.08 + 0.05 * abs(speed_mult))
            _fuerza_resp = math.sin(_fase_resp) * _jitter_mag * 0.35
            self.vx += _dir_x * _fuerza_resp
            self.vy += _dir_y * _fuerza_resp

        # Inercia: el orbe se mueve → partículas se retrasan
        self.vx -= delta_x * (1.0 / self.masa)
        self.vy -= delta_y * (1.0 / self.masa)
        # Spring-back a órbita original
        self.vx -= self.offset_x * self.coef_retorno
        self.vy -= self.offset_y * self.coef_retorno
        # Arrastre viscoso
        self.vx *= self.coef_arrastre
        self.vy *= self.coef_arrastre
        # Integrar
        self.offset_x += self.vx
        self.offset_y += self.vy
        # FP-047 A1: Clamp offset a ±radio (evitar vuelo libre)
        _lim = self.radio * 0.8
        self.offset_x = max(-_lim, min(_lim, self.offset_x))
        self.offset_y = max(-_lim, min(_lim, self.offset_y))
        # Fade in/out
        if self.edad < 20:
            self.alpha = self.alpha_objetivo * (self.edad / 20)
        elif self.edad > self.vida - 30:
            self.alpha = self.alpha_objetivo * max(0, (self.vida - self.edad) / 30)
        return self.edad < self.vida

    @property
    def pos(self) -> QPointF:
        return QPointF(
            self.radio * math.cos(self.angulo) + self.offset_x,
            self.radio * math.sin(self.angulo) + self.offset_y,
        )


# Símbolos para herramientas
_SIMBOLOS_HERRAMIENTAS = {
    "leer_archivo": "📜", "listar_directorio": "🌳", "buscar_en_codigo": "🔍",
    "escribir_archivo": "✍", "editar_archivo": "✏", "ejecutar_comando": "⚡",
    "buscar_en_internet": "🌐", "solicitar_a_copilot": "🕎", "tomar_captura_pantalla": "📷",
    "buscar_archivos": "🗂", "diagnostico_sistema": "⚙",
}
_SIMBOLO_DEFAULT = "✡"


# ═══════════════════════════════════════════════
# דמות DMUT — AVATAR VISUAL EXPRESIVO (RF-48)
# Mapeo humor → modificadores visuales del orbe
# ═══════════════════════════════════════════════

_DMUT_VISUAL: dict[str, dict[str, float]] = {
    # humor: {brillo_mod, rot_mod, particulas_mod, pulso_vel, tinte_r, tinte_g, tinte_b}
    # WI-244: Tintes amplificados ~1.5x para diferenciación emocional visible
    "neutral":    {"brillo_mod": 0.0,  "rot_mod": 1.0, "particulas_mod": 1.0, "pulso_vel": 1.0, "tinte_r": 0, "tinte_g": 0, "tinte_b": 0},
    "sereno":     {"brillo_mod": -0.05, "rot_mod": 0.6, "particulas_mod": 0.5, "pulso_vel": 0.5, "tinte_r": -5, "tinte_g": 15, "tinte_b": 45},
    "contento":   {"brillo_mod": 0.10, "rot_mod": 1.2, "particulas_mod": 1.4, "pulso_vel": 1.1, "tinte_r": 30, "tinte_g": 22, "tinte_b": 0},
    # WI-PARTICULAS-RANGO: emocionado/activo subidos y cansado/aburrido bajados
    # — la velocidad angular base de una partícula es muy chica (0.003-0.015
    # rad/frame), así que duplicarla seguía siendo sutil en pantalla. Ensanchar
    # el rango entre extremos (junto con el jitter radial nuevo en
    # Particula.actualizar) hace la diferencia "acelerado vs letárgico" más
    # perceptible sin convertir esto en una explosión de partículas.
    "emocionado": {"brillo_mod": 0.15, "rot_mod": 1.8, "particulas_mod": 2.6, "pulso_vel": 1.5, "tinte_r": 45, "tinte_g": 30, "tinte_b": 10},
    "activo":     {"brillo_mod": 0.08, "rot_mod": 1.5, "particulas_mod": 2.0, "pulso_vel": 1.3, "tinte_r": 15, "tinte_g": 15, "tinte_b": 0},
    "curioso":    {"brillo_mod": 0.05, "rot_mod": 1.3, "particulas_mod": 1.3, "pulso_vel": 1.2, "tinte_r": -5, "tinte_g": 30, "tinte_b": 30},
    "reflexivo":  {"brillo_mod": -0.03, "rot_mod": 0.7, "particulas_mod": 0.7, "pulso_vel": 0.6, "tinte_r": 15, "tinte_g": -5, "tinte_b": 38},
    "aburrido":   {"brillo_mod": -0.08, "rot_mod": 0.4, "particulas_mod": 0.18, "pulso_vel": 0.4, "tinte_r": -15, "tinte_g": -15, "tinte_b": 0},
    "cansado":    {"brillo_mod": -0.10, "rot_mod": 0.3, "particulas_mod": 0.12, "pulso_vel": 0.3, "tinte_r": -22, "tinte_g": -15, "tinte_b": 5},
    "triste":     {"brillo_mod": -0.12, "rot_mod": 0.5, "particulas_mod": 0.4, "pulso_vel": 0.5, "tinte_r": -30, "tinte_g": -15, "tinte_b": 25},
    "formal":     {"brillo_mod": 0.0,  "rot_mod": 0.8, "particulas_mod": 0.8, "pulso_vel": 0.7, "tinte_r": 0, "tinte_g": 0, "tinte_b": 15},
    "regañado":   {"brillo_mod": -0.06, "rot_mod": 0.5, "particulas_mod": 0.5, "pulso_vel": 0.8, "tinte_r": 18, "tinte_g": -22, "tinte_b": -15},
    "preocupado": {"brillo_mod": 0.03, "rot_mod": 1.1, "particulas_mod": 1.1, "pulso_vel": 1.8, "tinte_r": 22, "tinte_g": 8, "tinte_b": -8},
}

_DMUT_DEFAULT = _DMUT_VISUAL["neutral"]


# ═══════════════════════════════════════════════
# EVOLUCIÓN ALQUÍMICA (FP-024 Pilar B — RF-88)
# ═══════════════════════════════════════════════

class EtapaAlquimica(Enum):
    NIGREDO = "nigredo"
    ALBEDO = "albedo"
    CITRINITAS = "citrinitas"
    RUBEDO = "rubedo"


_PALETAS_ALQUIMICAS = {
    EtapaAlquimica.NIGREDO: {
        "primario": QColor(26, 26, 46),
        "secundario": QColor(60, 60, 90),
    },
    EtapaAlquimica.ALBEDO: {
        "primario": QColor(192, 192, 208),
        "secundario": QColor(230, 230, 255),
    },
    EtapaAlquimica.CITRINITAS: {
        "primario": QColor(212, 160, 23),
        "secundario": QColor(255, 215, 0),
    },
    EtapaAlquimica.RUBEDO: {
        "primario": QColor(139, 0, 0),
        "secundario": QColor(255, 69, 0),
    },
}

_ETAPAS_ORDEN = [EtapaAlquimica.NIGREDO, EtapaAlquimica.ALBEDO, EtapaAlquimica.CITRINITAS, EtapaAlquimica.RUBEDO]

# ═══════════════════════════════════════════════
# SISTEMA OHR (אור — Luz) — RF-173A/B/C/D (FP-066)
# Cromática multidimensional del Maljut: 5 capas multiplicativas
# ═══════════════════════════════════════════════

# Mapa de estado FSM → grupo visual (comprime 13 estados en 8 grupos)
_ESTADO_A_GRUPO: dict[str, str] = {
    "dormido": "dormido", "descanso_guardian": "dormido",
    "escuchando": "escuchando", "vigilia": "escuchando", "despertando": "escuchando",
    "procesando": "procesando",
    "hablando": "hablando", "cortesia": "hablando",
    "trabajando": "trabajando",
    "error": "error",
    "gevura_activa": "gevura",
    "bereshit": "bereshit",
    # FIX: "alerta_extrano" compartía grupo visual con "bereshit" (arranque/
    # génesis) — dos estados sin relación conceptual (uno es "acabo de
    # encender", el otro "detecté algo que vigilar") terminaban viéndose
    # igual de tenues/apagados. Ahora tiene su propio grupo "alerta" con un
    # tono ámbar distintivo (ver _OHR_ESTADO) en vez de heredar el apagado
    # de bereshit.
    "alerta_extrano": "alerta",
    "idle": "dormido",
}

# Capa 2: Modificadores HSV por grupo visual sobre la base alquímica
# h_shift = grados de hue a sumar, s_mult = multiplicador saturación, v_mult = multiplicador valor
# WI-244: Rebalance — mayor separación HSV entre estados para distinción visual clara
_OHR_ESTADO: dict[str, dict[str, float]] = {
    "dormido":     {"h_shift": -15, "s_mult": 0.55, "v_mult": 0.50},  # Azul profundo, apagado
    "escuchando":  {"h_shift": 0,   "s_mult": 1.0,  "v_mult": 0.90},  # Base neutral
    "procesando":  {"h_shift": 30,  "s_mult": 1.15, "v_mult": 1.0},   # Cyan/azul, analítico
    "hablando":    {"h_shift": 45,  "s_mult": 1.25, "v_mult": 1.20},  # Dorado cálido, expresivo
    "trabajando":  {"h_shift": -25, "s_mult": 1.20, "v_mult": 1.10},  # Verde energético, activo
    "error":       {"h_shift": 170, "s_mult": 1.4,  "v_mult": 1.1},   # Rojo alarma
    "alerta":      {"h_shift": 20,  "s_mult": 1.35, "v_mult": 1.15},  # Ámbar vigilante — distinto de error (rojo) y bereshit (apagado)
    "gevura":      {"h_shift": 160, "s_mult": 1.5,  "v_mult": 1.0},   # Rojo profundo
    "bereshit":    {"h_shift": -10, "s_mult": 0.8,  "v_mult": 0.7},   # Génesis tenue
}

# Capa 3: Tinte de herramienta activa (solo en estado "trabajando")
_OHR_HERRAMIENTA: dict[str, dict[str, float]] = {
    "lectura":   {"tinte_r": -10, "tinte_g": 0,   "tinte_b": 30,  "blend": 0.25},
    "escritura":  {"tinte_r": -10, "tinte_g": 25,  "tinte_b": -5,  "blend": 0.25},
    "busqueda":   {"tinte_r": 15,  "tinte_g": 10,  "tinte_b": -10, "blend": 0.25},
    "ejecucion":  {"tinte_r": 30,  "tinte_g": -10, "tinte_b": -15, "blend": 0.25},
    "copilot":    {"tinte_r": 15,  "tinte_g": -5,  "tinte_b": 25,  "blend": 0.25},
    "info":       {"tinte_r": 0,   "tinte_g": 10,  "tinte_b": 15,  "blend": 0.15},
    "agenda":     {"tinte_r": 10,  "tinte_g": 10,  "tinte_b": 0,   "blend": 0.15},
    "meta":       {"tinte_r": 5,   "tinte_g": 0,   "tinte_b": 20,  "blend": 0.20},
    "demo":       {"tinte_r": 0,   "tinte_g": 0,   "tinte_b": 0,   "blend": 0.0},
}

# Capa 4: Tinte cognitivo por nivel de cerebro (solo en estado "procesando")
_OHR_CEREBRO: dict[str, dict[str, float]] = {
    "nivel1": {"tinte_r": -10, "tinte_g": 25,  "tinte_b": -5,  "blend": 0.30},
    "nivel2": {"tinte_r": -5,  "tinte_g": 5,   "tinte_b": 25,  "blend": 0.30},
    "nivel3": {"tinte_r": 15,  "tinte_g": -5,  "tinte_b": 25,  "blend": 0.30},
}

# FIX (diferenciación Nivel 1/2/3): antes el único diferenciador visual entre
# niveles de cerebro era el tinte de color de _OHR_CEREBRO, aplicado como una
# capa SUTIL (blend 0.30) debajo del color base de "procesando" — en la
# práctica casi no se distinguía a simple vista. Se agrega una diferencia
# barata y real reusando la animación ya existente (frecuencia de pulso de
# brillo + velocidad de rotación de anillos en _animar, sin inventar dibujo
# nuevo): nivel1 (regex local, rápido) pulsa nervioso y corto; nivel2 (Ollama)
# pulsa lento, como "pensando"; nivel3 (API externa) tiene un pulso medio
# claramente distinto de los otros dos.
_NIVEL_PULSO_FREQ: dict[str, float] = {
    "nivel1": 4.5,   # Rápido/nervioso — Malkuth, instantáneo
    "nivel2": 1.2,   # Lento, deliberado — "pensando" con Ollama
    "nivel3": 2.5,   # Medio — llamada a API externa
}
_NIVEL_ROT_MOD: dict[str, float] = {
    "nivel1": 1.6,
    "nivel2": 0.6,
    "nivel3": 1.0,
}

# Mapa de nombre de herramienta → categoría funcional
_HERRAMIENTA_A_CATEGORIA: dict[str, str] = {
    "leer_archivo": "lectura", "buscar_en_codigo": "lectura",
    "listar_directorio": "lectura", "buscar_archivos": "lectura",
    "escribir_archivo": "escritura", "editar_archivo": "escritura",
    "escribir_portapapeles": "escritura",
    "buscar_en_internet": "busqueda", "consultar_memoria": "busqueda",
    "ejecutar_comando": "ejecucion", "ejecutar_comando_sistema": "ejecucion",
    "abrir_aplicacion": "ejecucion", "cerrar_aplicacion": "ejecucion",
    "controlar_volumen": "ejecucion",
    "solicitar_a_copilot": "copilot", "verificar_respuesta": "copilot",
    "listar_solicitudes": "copilot",
    "obtener_fecha_hora": "info", "obtener_info_sistema": "info",
    "contexto_pantalla": "info", "leer_portapapeles": "info",
    "monitoreo_sistema": "info", "estado_rapido_sistema": "info",
    "info_entorno": "info", "diagnostico_sistema": "info",
    "agregar_tarea": "agenda", "listar_tareas": "agenda",
    "completar_tarea": "agenda", "eliminar_tarea": "agenda",
    "agregar_nota": "agenda", "listar_notas": "agenda",
    "eliminar_nota": "agenda", "crear_recordatorio": "agenda",
    "listar_recordatorios": "agenda",
    "listar_tareas_diferidas": "agenda", "completar_tarea_diferida": "agenda",
    "agregar_tarea_diferida": "agenda",
    "listar_proyectos": "meta", "auditar_proyecto": "meta",
    "resumen_proyectos": "meta", "registrar_proyecto": "meta",
    "demo_visual": "demo",
}


def _hsv_transform(color: QColor, h_shift: float, s_mult: float, v_mult: float) -> QColor:
    """RF-173A: Transforma un QColor aplicando modificadores HSV."""
    h, s, v, a = color.hsvHueF(), color.hsvSaturationF(), color.valueF(), color.alphaF()
    # hue: rotar (0-1 escala, 360° = 1.0)
    h = (h + h_shift / 360.0) % 1.0
    if h < 0:
        h += 1.0
    s = max(0.0, min(1.0, s * s_mult))
    v = max(0.0, min(1.0, v * v_mult))
    result = QColor()
    result.setHsvF(h, s, v, a)
    return result


def _blend_tinte(color: QColor, tinte_r: float, tinte_g: float, tinte_b: float, blend: float) -> QColor:
    """RF-173B/C: Mezcla un tinte aditivo ponderado sobre un QColor."""
    if blend <= 0:
        return QColor(color)
    r = max(0, min(255, int(color.red() + tinte_r * blend)))
    g = max(0, min(255, int(color.green() + tinte_g * blend)))
    b = max(0, min(255, int(color.blue() + tinte_b * blend)))
    return QColor(r, g, b, color.alpha())


def _calcular_color_ohr(etapa: 'EtapaAlquimica', estado: str, trabajo_cat: str = "",
                         cerebro_nivel: str | None = None,
                         gevura_cat: str = "") -> tuple[QColor, QColor]:
    """RF-173D: Calcula el par (primario, secundario) del Sistema Ohr 5 capas.
    Capa 1: Base alquímica
    Capa 2: Modificador estado HSV
    Capa 3: Tinte herramienta (si trabajando)
    Capa 4: Tinte cerebro (si procesando)
    Nota: Capa 5 (Dmut emocional) se aplica en paintEvent como siempre.
    """
    # Capa 1: Base alquímica
    paleta = _PALETAS_ALQUIMICAS.get(etapa, _PALETAS_ALQUIMICAS[EtapaAlquimica.NIGREDO])
    pri = QColor(paleta["primario"])
    sec = QColor(paleta["secundario"])

    # Capa 2: Modificador de estado
    grupo = _ESTADO_A_GRUPO.get(estado, "escuchando")
    mod = _OHR_ESTADO.get(grupo, _OHR_ESTADO["escuchando"])
    pri = _hsv_transform(pri, mod["h_shift"], mod["s_mult"], mod["v_mult"])
    sec = _hsv_transform(sec, mod["h_shift"], mod["s_mult"], mod["v_mult"])

    # Capa 3: Tinte herramienta (solo si trabajando)
    if grupo == "trabajando" and trabajo_cat:
        th = _OHR_HERRAMIENTA.get(trabajo_cat)
        if th:
            pri = _blend_tinte(pri, th["tinte_r"], th["tinte_g"], th["tinte_b"], th["blend"])
            sec = _blend_tinte(sec, th["tinte_r"], th["tinte_g"], th["tinte_b"], th["blend"])

    # Capa 4: Tinte cerebro (solo si procesando)
    if grupo == "procesando" and cerebro_nivel:
        tc = _OHR_CEREBRO.get(cerebro_nivel)
        if tc:
            pri = _blend_tinte(pri, tc["tinte_r"], tc["tinte_g"], tc["tinte_b"], tc["blend"])
            sec = _blend_tinte(sec, tc["tinte_r"], tc["tinte_g"], tc["tinte_b"], tc["blend"])

    # Gevurá: override parcial por categoría de bloqueo
    if grupo == "gevura" and gevura_cat:
        _gevura_tintes = {
            "etico":             {"tinte_r": 40, "tinte_g": -20, "tinte_b": -20, "blend": 0.50},
            "accion_destructiva": {"tinte_r": 40, "tinte_g": -20, "tinte_b": -20, "blend": 0.50},
            "proceso_critico":   {"tinte_r": 40, "tinte_g": -20, "tinte_b": -20, "blend": 0.50},
            "exfiltracion":      {"tinte_r": 40, "tinte_g": -20, "tinte_b": -20, "blend": 0.50},
            "shutdown":          {"tinte_r": 40, "tinte_g": -20, "tinte_b": -20, "blend": 0.50},
            "seguridad":         {"tinte_r": 30, "tinte_g": -10, "tinte_b": -15, "blend": 0.40},
            "sandbox":           {"tinte_r": 25, "tinte_g": 5,   "tinte_b": -15, "blend": 0.35},
            "permiso":           {"tinte_r": 20, "tinte_g": 15,  "tinte_b": -10, "blend": 0.30},
        }
        tg = _gevura_tintes.get(gevura_cat)
        if tg:
            pri = _blend_tinte(pri, tg["tinte_r"], tg["tinte_g"], tg["tinte_b"], tg["blend"])
            sec = _blend_tinte(sec, tg["tinte_r"], tg["tinte_g"], tg["tinte_b"], tg["blend"])

    return pri, sec


_UMBRALES_EVOLUCION = {
    EtapaAlquimica.ALBEDO: {"horas": 24, "interacciones": 50},
    EtapaAlquimica.CITRINITAS: {"horas": 168, "interacciones": 500},
    EtapaAlquimica.RUBEDO: {"horas": 720, "interacciones": 2000},
}

_EVOLUCION_PATH = Path(__file__).resolve().parent.parent.parent / "datos" / "evolucion_computadora.json"


def _cargar_evolucion() -> dict:
    if _EVOLUCION_PATH.exists():
        try:
            return json.loads(_EVOLUCION_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.debug("Error cargando evolución: %s", e)
    return {"etapa": "nigredo", "interacciones_totales": 0, "tareas_exitosas": 0, "historial": []}


def _guardar_evolucion(data: dict) -> None:
    _EVOLUCION_PATH.parent.mkdir(parents=True, exist_ok=True)
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(_EVOLUCION_PATH, data)


class IndicadorHerramienta:
    """Indicador flotante que aparece cuando el Computadora usa una herramienta."""

    def __init__(self, nombre: str, estado: str = "ejecutando"):
        self.nombre = nombre
        self.estado = estado  # "ejecutando" | "completado"
        self.simbolo = _SIMBOLOS_HERRAMIENTAS.get(nombre, _SIMBOLO_DEFAULT)
        # WI-245: Categoría funcional para íconos vectoriales
        self.categoria = _HERRAMIENTA_A_CATEGORIA.get(nombre, "info")
        self.angulo = random.uniform(0, 2 * math.pi)
        self.radio = RADIO_RESPLANDOR + 15
        self.alpha = 0.0
        self.alpha_objetivo = 0.9
        self.edad = 0
        self.vida_max = 180  # ~6s a 30fps
        self.velocidad = 0.008

    def actualizar(self) -> bool:
        self.angulo += self.velocidad
        self.edad += 1
        if self.estado == "ejecutando":
            # Fade in y pulso
            self.alpha = min(self.alpha + 0.05, self.alpha_objetivo)
            return True  # Vive hasta completar
        else:
            # Completado: fade out
            if self.edad > self.vida_max - 60:
                self.alpha = max(0, self.alpha - 0.02)
            return self.edad < self.vida_max

    @property
    def pos(self) -> QPointF:
        return QPointF(
            self.radio * math.cos(self.angulo),
            self.radio * math.sin(self.angulo),
        )


# Colores por nivel de cerebro (temática Sefirót)
# Nivel 1 (Malkuth/Reino — verde esmeralda): regex local, rápido
# Nivel 2 (Tiferet/Belleza — azul zafiro): Ollama LLM
# Nivel 3 (Keter/Corona — púrpura violeta): Copilot
COLORES_NIVEL = {
    "nivel1": QColor(40, 200, 100),   # Verde esmeralda — Malkuth
    "nivel2": QColor(60, 140, 220),   # Azul zafiro — Tiferet
    "nivel3": QColor(160, 80, 220),   # Púrpura — Keter
}
NOMBRES_NIVEL = {
    "nivel1": "Regex",
    "nivel2": "Ollama",
    "nivel3": "API externa",
}


# ═══════════════════════════════════════════════
# ORBE — Esfera de Obsidiana con Grabados Cabalísticos
# ═══════════════════════════════════════════════

TAMANO_ORBE = 360
RADIO_NUCLEO = 35
RADIO_RESPLANDOR = 75


class OrbeComputadora(QWidget):
    """
    Esfera de obsidiana pulida flotando sobre el escritorio.
    Sin marco, sin fondo — solo la esfera y sus partículas.
    Grabados cabalísticos rotan alrededor del núcleo.
    """
    # RF-308: Señal thread-safe para resultados de herramientas en demo
    _demo_herramienta_signal = pyqtSignal(str, str)
    # FIX: señal thread-safe para auto-desactivar el Guardián al reconocer al
    # propietario — _tick_guardian() puede ejecutarse desde el timer real
    # (hilo principal) o desde el hilo de la demo; _desactivar_guardian_manual()
    # toca un QTimer y debe correr siempre en el hilo principal.
    _guardian_propietario_detectado = pyqtSignal()

    def __init__(self, config, cerebro=None):
        super().__init__()
        self.config = config
        # Usar singleton Orquestador (ya fue creado en __main__)
        from computadora.nucleo.orquestador_singleton import obtener_orquestador_singleton
        self.orquestador = obtener_orquestador_singleton(config, cerebro=cerebro)
        # RF-308: Conectar señal de resultado de herramienta demo
        self._demo_herramienta_signal.connect(self._demo_herramienta_resultado)
        self._guardian_propietario_detectado.connect(self._al_guardian_propietario_detectado)

        # Estado visual
        self._estado_lock = threading.Lock()
        self._fase = 0.0
        self._estado = "dormido"
        self._objetivo_brillo = 0.05
        self._brillo_actual = 0.05
        self._pensando = False
        self._cola_voz = collections.deque(maxlen=50)
        self._streaming_en_curso = False
        self._esperando_fin_tts = False
        self._streaming_emitio = False
        self._streaming_emitio_ts = 0.0
        self._esperando_confirmacion = False
        self._confirmacion_origen = None
        # Flag temporal para indicar que estamos esperando una respuesta
        # corta (sí/no) tras una pregunta de confirmación. Si está en True,
        # no pausamos la escucha durante el TTS para aceptar la respuesta.
        self._awaiting_confirmation = False
        # FP-041 Shemirat Gevurá: flag para blindar _al_recibir_voz durante permiso
        self._gevura_esperando = False

        # Nivel de cerebro activo y herramientas flotantes
        self._cerebro_nivel = None   # "nivel1"|"nivel2"|"nivel3" o None
        self._indicadores_herramientas: list[IndicadorHerramienta] = []

        # Gate de Copilot: estado de espera de permiso
        self._esperando_gate_copilot = False
        self._gate_copilot_texto = ""

        # Estado de modo tarea compleja
        self._esperando_modo_tarea = False
        self._trabajo_categoria = ""   # "lectura"|"escritura"|"busqueda"|"ejecucion"|"copilot"
        self._trabajo_tool = ""        # nombre de herramienta activa

        # Partículas (CICLO 16+ FIX: usar deque para in-place actualización, no list comprehension)
        self._particulas: collections.deque = collections.deque(maxlen=40)
        self._max_particulas = 40
        self._pos_anterior_x = float(self.x())
        self._pos_anterior_y = float(self.y())

        # Evolución alquímica (FP-024 Pilar B — RF-88)
        self._evolucion_data = _cargar_evolucion()
        self._etapa_alquimica = EtapaAlquimica(self._evolucion_data.get("etapa", "nigredo"))
        paleta = _PALETAS_ALQUIMICAS[self._etapa_alquimica]
        self._color_alq_primario = QColor(paleta["primario"])
        self._color_alq_secundario = QColor(paleta["secundario"])
        self._color_alq_target_pri = QColor(paleta["primario"])
        self._color_alq_target_sec = QColor(paleta["secundario"])
        self._alq_lerp_progress = 1.0  # 1.0 = transición completa

        # FIX: Sistema Ohr (color por estado/herramienta/nivel/gevurá) — antes
        # _calcular_color_ohr() se llamaba directo en paintEvent() cada frame
        # y el color resultante CAMBIABA DE GOLPE cada vez que cambiaba el
        # estado FSM (a diferencia de la paleta alquímica y el tinte de humor,
        # que sí interpolan). Ahora se interpola igual que esos otros dos
        # sistemas: _animar() actualiza estos valores hacia el color objetivo
        # cada frame, y paintEvent() solo los lee.
        _color_ohr_inicial_pri, _color_ohr_inicial_sec = _calcular_color_ohr(
            self._etapa_alquimica, self._estado, self._trabajo_categoria,
            self._cerebro_nivel, getattr(self, '_gevura_categoria', '')
        )
        self._color_ohr_pri_actual = QColor(_color_ohr_inicial_pri)
        self._color_ohr_sec_actual = QColor(_color_ohr_inicial_sec)

        # Patrones de geometría sagrada (FP-024 opcionales)
        self._patron_sagrado = ""         # "espiral"|"hexagrama"|"" (vacío = sin patrón)
        self._patron_timer = 0.0          # cuenta regresiva frames (0 = inactivo)
        self._patron_duracion = 0.0       # duración total del patrón en frames

        # Geometría sagrada — ángulos de rotación
        self._rot_anillo1 = 0.0
        self._rot_anillo2 = 0.0
        self._rot_letras = 0.0
        # RF-152: Fase circadiana para modulación visual de brillo
        self._fase_circadiana = "activo"
        # RUBEDO: Framerate metrics para UI + DevTools
        from collections import deque
        self._fps_actual = 0.0
        self._fps_buffer = deque(maxlen=60)
        self._mostrar_fps = False

        # RF-157: Dmut lerp — transición suave de tintes emocionales (~1s)
        self._dmut_actual = dict(_DMUT_DEFAULT)  # valores interpolados en curso
        self._dmut_humor_prev = "neutral"        # humor del frame anterior

        # Tamaño dinámico — inicia en modo compacto (Tzimtzum)
        self._escala = 0.25
        self._escala_objetivo = 0.25
        self._hover = False
        self._tzimtzum_ocultando = False  # HF-025c: bandera para animar antes de ocultar

        # Boot Génesis: el orbe empieza diminuto y se revela con la primera proactividad
        self._boot_completo = False
        self._modo_carga_pesada = False
        self._demo_en_curso = False  # FP-043: Demo Maljut en progreso
        self._demo_dmut_factor = 1.0  # WI-241: Atenuación Dmut durante demo paletas
        self._demo_opaco = True  # WI-326: Opacidad 100% durante demo (no transparencia)

        # HF-024b: Ripple de escucha universal (-1 = inactivo, 0..1.5 = animando)
        self._ripple_fase = -1.0

        # Posición con movimiento suave (idle drift)
        self._drift_fase = random.uniform(0, 2 * math.pi)

        # RF-340: Render offset — durante tránsito autónomo, el orbe se dibuja
        # desplazado del centro de la ventana (la ventana cubre origin→dest)
        self._render_offset_x = 0.0
        self._render_offset_y = 0.0
        self._en_transito = False  # True mientras hay movimiento autónomo con ventana expandida
        
        # WI-MALJUT-RUBEDO-004: Gradual offset reset para suavidad visual
        # FIX: el lerp ahora corre ANTES de encoger la ventana (mientras sigue
        # grande), para que el orbe nunca quede dibujado fuera del área
        # visible de una ventana ya pequeña — ver vida_autonoma.py
        self._offset_collapse_timer = 0  # frames restantes para completar el lerp
        self._offset_collapse_in_progress = False  # flag: lerp en curso
        self._offset_collapse_iniciado = False  # flag: ya se inició el lerp para este tránsito
        self._offset_collapse_inicio_x = 0.0  # offset real al iniciar el lerp (para interpolar desde ahí)
        self._offset_collapse_inicio_y = 0.0

        # WI-ANILLOS-LERP-RECURSOS: Variables para transición suave de anillos de recursos
        # Patrón Jarvis aplicado a CPU/RAM/GPU/Disco (como brillo/escala/rotaciones)
        # Valores ACTUALES (interpolados, renderizados)
        self._cpu_actual = 50.0
        self._ram_actual = 50.0
        self._gpu_actual = -1.0
        self._disk_actual = 50.0
        # Valores OBJETIVO (capturados cada 1s del monitor sistema)
        self._cpu_objetivo = 50.0
        self._ram_objetivo = 50.0
        self._gpu_objetivo = -1.0
        self._disk_objetivo = 50.0
        # WI-MOTOR-GPU: motor de GPU dominante ('compute'|'media'|'inactivo'|
        # 'desconocido'), usado SOLO para elegir el color del anillo GPU —
        # es categórico, no se interpola como los valores numéricos de arriba.
        self._gpu_motor_actual = "desconocido"
        self._gpu_motor_objetivo = "desconocido"

        self._ultimo_frame_ts = time.monotonic()
        
        # FIX: Frame rate instrumentation (no más falsos positivos)
        self._frame_times_buffer = []  # últimos 60 delta_t values
        self._frame_count_since_log = 0  # contador para log cada 60 frames
        self._slowdown_frames = 0  # frames con delta_t > 33ms (below 30 FPS)
        self._max_frame_time = 0.0  # máximo delta_t observado
        # FIX: buffer dedicado para el tiempo de PROCESAMIENTO de cada frame
        # (medido al final de _animar()). Antes reutilizaba por error el mismo
        # nombre `_frame_times_buffer` de arriba vía un `hasattr()` que nunca
        # era True (el atributo ya existía como lista) — así que ese segundo
        # bloque anexaba sin límite al mismo buffer para siempre, mezclando
        # dos métricas distintas y haciendo que "avg FPS" en los logs nunca
        # se recuperase (crecía indefinidamente, nunca se recortaba).
        self._frame_proc_times = collections.deque(maxlen=100)

        # Arrastre
        self._arrastrando = False
        self._offset = QPoint()

        # יד Yad — El Don del Tacto (FP-013)
        self._proximidad = 0.0        # 0=lejos, 1=tocando
        self._zona_tacto = 0          # 0=Aín, 1=Reshimó, 2=Kav, 3=Yesod, 4=Nefesh
        self._cursor_anterior = QPoint(0, 0)
        self._tacto_velocidad = 0.0   # px/frame
        self._caricia_timestamps: list[float] = []  # timestamps de entrada a Nefesh
        self._last_caricia_memory_ts = 0.0  # FP-033 B2: cooldown para memoria de caricia
        self._en_nefesh = False        # cursor está en zona Nefesh
        self._impulso_vx = 0.0
        self._impulso_vy = 0.0
        self._drag_historial: list[tuple[int, int, float]] = []  # (x, y, timestamp)
        self._tacto_continuo_inicio = 0.0  # timestamp de entrada a zona cercana (>0.3)
        self._toque_atento_inicio = 0.0  # timestamp de cursor quieto en Nefesh
        self._ultimo_tacto_info: dict | None = None  # {"gesto": str, "ts": float}

        # FP-019 Késher: GestorPersonas (TinyDB)  — antes de _iniciar_voz
        from computadora.memoria.personas import GestorPersonas
        self.gestor_personas = GestorPersonas()
        self.gestor_personas.bootstrap_amo()
        self.gestor_personas.migrar_desde_json()

        # Personalidad evolutiva — necesaria antes de _iniciar_voz
        self.personalidad = Personalidad()
        self.personalidad.registrar_inicio_dia()

        # Configuración del tema visual del orbe
        self._config_tema_visual = ConfiguracionVisualDev()
        self._tema_visual = ThemeFactory.crear_tema(self._config_tema_visual.tipo_tema().value, self)
        self._tema_visual.initialize()

        # Ojos de Computadora: contexto de pantalla — necesario antes de _iniciar_voz (FP-044)
        self._contexto_pantalla = ContextoPantalla()

        self._configurar_ventana()
        self._iniciar_animacion()
        self._iniciar_voz()

        # Registrar callback para recordatorios (sistema.crear_recordatorio)
        try:
            set_callback_recordatorio(self._on_recordatorio)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.debug("No pude registrar callback de recordatorios")

        # גבורה Gevurá — Conectar permisos con UI
        try:
            from computadora.habilidades.herramientas import _obtener_gestor_permisos
            gestor = _obtener_gestor_permisos()
            gestor.set_callback(self._on_solicitar_permiso)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.debug("No pude registrar callback de permisos")

        # Vida autónoma
        self._vida = VidaAutonoma(self)

        # WI-318: Debounce para actualización de recursos en demo/movimiento
        # Durante movimiento rápido (FPS críticas), actualizar indicadores cada 3 frames en lugar de cada frame
        self._recursos_update_counter = 0
        self._recursos_debounce_interval = 1  # Normal: 1 (cada frame)
        # Se ajusta dinámicamente en _actualizar_fase()

        # Monitor de sistema en tiempo real
        self._monitor_sistema = obtener_monitor()

        # Baseline adaptativo del sistema
        from computadora.habilidades.baseline_sistema import BaselineSistema
        self._baseline_sistema = BaselineSistema()
        self._monitor_sistema.set_baseline(self._baseline_sistema)

        # Actualizar métricas del sistema fuera del render path
        self._timer_monitor_sistema = QTimer()
        self._timer_monitor_sistema.timeout.connect(self._actualizar_metrica_sistema)
        self._timer_monitor_sistema.start(1000)

        # Motor de proactividad: sugerencias sin pedir
        self._motor_proactividad = MotorProactividad(
            contexto_pantalla=self._contexto_pantalla,
            monitor_sistema=self._monitor_sistema,
            baseline=self._baseline_sistema,
        )
        self._motor_proactividad.sugerencia_lista.connect(self._al_sugerencia_proactiva)
        self._motor_proactividad.fase_cambio.connect(self._al_cambio_fase_circadiana)
        # FP-014: Dar referencia al orbe para consultar proximidad táctil
        self._motor_proactividad._orbe_ref = self
        self._motor_proactividad.start()

        # WI-120: Conectar PerceptorDaat.propietario_presente → registrar_presencia_visual
        if hasattr(self.orquestador, 'perceptor') and self.orquestador.perceptor is not None:
            self.orquestador.perceptor.propietario_presente.connect(
                self._motor_proactividad.registrar_presencia_visual
            )
            self.orquestador.perceptor.propietario_presente.connect(
                self._on_propietario_presente
            )
            logger.info("WI-120: propietario_presente → registrar_presencia_visual conectado")
            logger.info("WI-120: propietario_presente → _on_propietario_presente conectado")

        # CICLO 16+ FIX: Consolidar 7 QTimers en 1 despachador (evitar contención)
        # WI-253: Escaneo proactivo de rostro al reencarnar (10s después del boot)
        # Shem Shmirah: verificar intentos de intrusión al Enciclopedia durante ausencia
        # Timer para actualizar ánimo cada 5 min (300s)
        # Timer para guardar personalidad cada 10 min (600s)
        # Timer para evaluar evolución alquímica cada 10 min (FP-024 Pilar B)
        self._timer_tareas = QTimer()
        self._timer_tareas.timeout.connect(self._despachar_tareas_periodicas)
        self._timer_tareas.start(1000)  # Despachar cada 1s para precisión
        
        # Contadores para tareas
        self._timer_ticks = 0
        self._tareas_pendientes = {
            "escaneo_rostro": 10,      # 10s
            "verificar_intrusion": 8,  # 8s
            "actualizar_animo": 300,   # 5 min
            "guardar_persona": 600,    # 10 min
            "evaluar_evolucion": 600,  # 10 min
        }

        # FP-014: Unificar instancia de personalidad — NLU usa la misma
        self.orquestador.cerebro._personalidad_ref = self.personalidad

        # FP-022: Watchdog multi-etapa — monitoreo de servicios
        from computadora.interfaz.watchdog import WatchdogComputadora
        self._watchdog = WatchdogComputadora(on_cambio_etapa=self._al_cambio_etapa_watchdog)
        self._watchdog.iniciar()
        # WI-324: Establecer referencia watchdog en CerebroComputadora para sincronización
        self.orquestador.cerebro.establecer_watchdog(self._watchdog)
        # FP-019: Dar al cerebro acceso al GestorPersonas
        self.orquestador.cerebro._gestor_personas = self.gestor_personas
        # FP-014: Dar al cerebro acceso al estado táctil
        self.orquestador.cerebro._orbe_ref = self

        # FP-028: Hot-Reload de código en vivo (כתר Keter — auto-renovación)
        self._hot_reloader = HotReloader(
            raiz_proyecto=Path(__file__).resolve().parent.parent.parent,
            on_recrear_cerebro=self.orquestador.recrear_cerebro,
        )
        self._hot_reloader.modulo_recargado.connect(self._on_modulo_recargado)
        self._hot_reloader.recarga_fallida.connect(self._on_recarga_fallida)
        self._hot_reloader.requiere_reinicio.connect(self._on_requiere_reinicio)
        # Diferir escaneo de archivos 3s para no bloquear el arranque de la UI
        QTimer.singleShot(3000, self._hot_reloader.iniciar)

        # 🛡️ Suscribir a eventos del Enciclopedia (Shmirá)
        try:
            from computadora.nucleo.eventos import obtener_bus
            _bus = obtener_bus()
            _bus.suscribir("intrusion_enciclopedia", self._al_intrusion_enciclopedia)
            _bus.suscribir("enciclopedia_abierto", self._al_enciclopedia_abierto)
        except Exception as e:
            logger.debug(f"No pude suscribir eventos del Enciclopedia: {e}")

        # כתר Keter — Ventana de introspección (escucha su propia Corona)
        self._ventana_keter = VentanaKeter(self.orquestador, self)

        # FIX #1: Caché del menú contextual (lazy-build, reutilizar en cada clic)
        self._menu_contextual = None
        self._menu_contextual_hash = 0  # detectar cambios de estado que invalidan cache
        
        # FIX #2: Caché de métricas de sistema (no snapshot en CADA frame)
        self._monitor_snapshot_cache = {}
        self._monitor_snapshot_ts = 0.0  # timestamp del último snapshot

        logger.info(f"La Computadora ha despertado. Personalidad: {self.personalidad.describe()}")

    def _configurar_ventana(self):
        # Tamaño inicial — calculado según _escala de arranque (Tzimtzum 0.25)
        # Margen dinámico: ajustado para que la ventana envuelva el orbe visual sin exceso
        _radio_visual_init = (RADIO_NUCLEO + RADIO_NUCLEO * 2.2) * self._escala
        _margen = max(20, int(32 / max(self._escala, 0.1)))
        _tam_init = max(60, int(_radio_visual_init * 2 + _margen))
        self._tamano_ventana = float(_tam_init)  # RF-165: float para evitar zona muerta en lerp
        self.setMinimumSize(1, 1)
        self.resize(_tam_init, _tam_init)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Computadora")
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAutoFillBackground(False)

        # Calcular posición final (esquina inferior derecha)
        self._pos_final = None
        pantalla = QApplication.primaryScreen()
        if pantalla:
            geo = pantalla.availableGeometry()
            self._pos_final = (
                int(geo.right() - self._tamano_ventana - 10),
                int(geo.bottom() - self._tamano_ventana - 10),
            )

        # Iniciar fuera de pantalla para evitar flash al primer render
        self.move(-9999, -9999)

    def _geometria_pantalla_actual(self):
        """Obtiene el area util del monitor donde esta la ventana."""
        pantalla = QApplication.screenAt(self.frameGeometry().center())
        if pantalla is None:
            pantalla = QApplication.primaryScreen()
        return pantalla.availableGeometry() if pantalla else None

    def _limitar_posicion_pantalla(self, x, y, ancho=None, alto=None):
        """Limita una posicion para que toda la ventana quede en el area util."""
        geo = self._geometria_pantalla_actual()
        if geo is None:
            return QPoint(int(x), int(y))
        ancho = self.width() if ancho is None else int(ancho)
        alto = self.height() if alto is None else int(alto)
        max_x = max(geo.left(), geo.right() - ancho + 1)
        max_y = max(geo.top(), geo.bottom() - alto + 1)
        return QPoint(
            max(geo.left(), min(int(x), max_x)),
            max(geo.top(), min(int(y), max_y)),
        )

    def _restaurar_posicion_inicial(self):
        """Recupera la ventana despues del primer show aunque el boot se demore."""
        if getattr(self, '_tzimtzum_ocultando', False):
            return
        objetivo = self._pos_final or (self.x(), self.y())
        self.move(self._limitar_posicion_pantalla(*objetivo))
        self.show()
        self.raise_()
        self.activateWindow()

    def _eliminar_sombra_dwm(self):
        """Elimina sombra/borde DWM — debe llamarse DESPUÉS de show()."""
        import sys as _sys
        if _sys.platform != "win32":
            return
        try:
            import ctypes
            import ctypes.wintypes
            # WI-228: Declarar restype/argtypes para evitar truncamiento HWND 64-bit
            _u32 = ctypes.windll.user32
            if not hasattr(_u32.SetWindowLongW, '_argtypes_set'):
                _u32.SetWindowLongW.restype = ctypes.c_long
                _u32.SetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
                _u32.GetWindowLongW.restype = ctypes.c_long
                _u32.GetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
                _u32.GetClassLongW.restype = ctypes.wintypes.DWORD
                _u32.GetClassLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
                _u32.SetClassLongW.restype = ctypes.wintypes.DWORD
                _u32.SetClassLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ctypes.c_long]
                _u32.SetWindowPos.restype = ctypes.wintypes.BOOL
                _u32.SetWindowPos.argtypes = [
                    ctypes.wintypes.HWND, ctypes.wintypes.HWND,
                    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                    ctypes.wintypes.UINT,
                ]
                _u32.ShowWindow.restype = ctypes.wintypes.BOOL
                _u32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
                _dwm = ctypes.windll.dwmapi
                _dwm.DwmSetWindowAttribute.restype = ctypes.c_long  # HRESULT
                _dwm.DwmSetWindowAttribute.argtypes = [
                    ctypes.wintypes.HWND, ctypes.wintypes.DWORD,
                    ctypes.c_void_p, ctypes.wintypes.DWORD,
                ]
                _u32.SetWindowLongW._argtypes_set = True
            hwnd = int(self.winId())

            # 1. Forzar WS_POPUP puro (elimina todo chrome/frame)
            GWL_STYLE = -16
            WS_POPUP = 0x80000000
            WS_VISIBLE = 0x10000000
            WS_CLIPCHILDREN = 0x02000000
            WS_CLIPSIBLINGS = 0x04000000
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_STYLE,
                WS_POPUP | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS)

            # 2. Extended style: preservar WS_EX_LAYERED (Qt) + TOOLWINDOW
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT_WIN = 0x00000020
            exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            exstyle = (exstyle | WS_EX_TOOLWINDOW | WS_EX_LAYERED) & ~WS_EX_TRANSPARENT_WIN
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, exstyle)

            # 3. Quitar CS_DROPSHADOW del window class
            GCL_STYLE = -26
            CS_DROPSHADOW = 0x00020000
            cls_style = ctypes.windll.user32.GetClassLongW(hwnd, GCL_STYLE)
            ctypes.windll.user32.SetClassLongW(
                hwnd, GCL_STYLE, cls_style & ~CS_DROPSHADOW)

            # 4. DWM: desactivar non-client rendering
            DWMWA_NCRENDERING_POLICY = 2
            val = ctypes.c_int(2)  # DWMNCRP_DISABLED
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_NCRENDERING_POLICY,
                ctypes.byref(val), ctypes.sizeof(val))

            # 5. Esquinas sin redondeo (Windows 11)
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            val2 = ctypes.c_int(1)  # DWMWCP_DONOTROUND
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(val2), ctypes.sizeof(val2))

            # RF-162: Desactivar color de borde (Win11 22H2+)
            # NOTA: NO usar DwmExtendFrameIntoClientArea con MARGINS(-1) —
            # extiende el frame DWM (blanco) al área cliente, causando flash
            # antes del primer paintEvent. DWMWA_BORDER_COLOR basta.
            DWMWA_BORDER_COLOR = 34
            DWMWA_COLOR_NONE = ctypes.c_uint(0xFFFFFFFE)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(DWMWA_COLOR_NONE), ctypes.sizeof(DWMWA_COLOR_NONE))

            # 6. Aplicar cambios de frame + RF-305: Forzar HWND_TOPMOST
            self._aplicar_dwm_nosombra(hwnd, ctypes)
        except Exception as e:
            logger.debug("Error en SetWindowPos: %s", e)

    def _aplicar_dwm_nosombra(self, hwnd=None, ctypes_mod=None):
        """Re-aplica atributos DWM anti-sombra (ligero, seguro para llamar frecuentemente)."""
        try:
            if ctypes_mod is None:
                import ctypes as ctypes_mod
            if hwnd is None:
                hwnd = int(self.winId())
            # DWM: desactivar non-client rendering
            val = ctypes_mod.c_int(2)  # DWMNCRP_DISABLED
            ctypes_mod.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 2, ctypes_mod.byref(val), ctypes_mod.sizeof(val))
            # Esquinas sin redondeo (Windows 11)
            val2 = ctypes_mod.c_int(1)  # DWMWCP_DONOTROUND
            ctypes_mod.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes_mod.byref(val2), ctypes_mod.sizeof(val2))
            # Borde invisible
            val3 = ctypes_mod.c_uint(0xFFFFFFFE)  # DWMWA_COLOR_NONE
            ctypes_mod.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 34, ctypes_mod.byref(val3), ctypes_mod.sizeof(val3))
            # SWP_FRAMECHANGED + HWND_TOPMOST = -1
            HWND_TOPMOST = -1
            SWP_FRAMECHANGED = 0x0020
            ctypes_mod.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                SWP_FRAMECHANGED | 0x0002 | 0x0001 | 0x0010)
        except Exception as e:
            logger.debug("Error re-aplicando DWM nosombra: %s", e)

    def _iniciar_animacion(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._animar)

        # FIX CRÍTICO: Aplicar fps_target de config_tema_visual.fps_configurado() sin hardcodear
        # No asumir fps_target=60 por defecto; respetar config.json
        fps_target = self._config_tema_visual.fps_configurado()  # Respeta datos/maljut_dev_config.json
        intervalo_ms = max(1, int(1000.0 / fps_target))  # 1000ms / fps = intervalo en ms
        self._timer.start(intervalo_ms)
        logger.info(f"🎬 Animación iniciada: {fps_target} FPS (intervalo={intervalo_ms}ms, esperado={1000.0/fps_target:.1f}ms)")

        # RF-306: Timer de re-aserción topmost cada 5s (Shekhiná Tamid)
        self._timer_topmost = QTimer()
        self._timer_topmost.timeout.connect(self._reasegurar_topmost)
        self._timer_topmost.start(5000)

        # CICLO 16+ FIX: Cola deferred para resize/move (no bloquear hot path _animar)
        self._resize_move_queue = None  # {tam, nx, ny} o None

        # Hallazgo 2026-10-03 (regresión "animación de expansión a tirones"):
        # el flush de _resize_move_queue vivía SOLO en _reasegurar_topmost
        # (cada 5000ms). Eso es apropiado para la reaserción de topmost/DWM
        # (cara, debe ser infrecuente), pero cuando el orbe CRECE (p.ej. al
        # detectar wake word, escala 0.45→1.0), el contenido (glow/partículas)
        # necesita más espacio de inmediato — si la ventana real tarda hasta
        # 5s en alcanzar ese tamaño, el glow queda recortado contra el borde
        # de la ventana vieja (más chica) durante toda la animación, y luego
        # "salta" de golpe cuando el flush por fin llega. Un timer dedicado,
        # mucho más corto, solo para el resize/move (sin el costo de
        # SetWindowPos/DWM de _reasegurar_topmost) resuelve esto sin volver
        # a hacer resize() en el hot path de 16ms de _animar.
        self._timer_resize_flush = QTimer()
        self._timer_resize_flush.timeout.connect(self._flush_resize_queue)
        self._timer_resize_flush.start(100)

    def _actualizar_metrica_sistema(self):
        """Actualiza el caché de métricas cada segundo, fuera del render path."""
        if not hasattr(self, '_monitor_sistema') or self._monitor_sistema is None:
            return
        try:
            snap = self._monitor_sistema.snapshot() or {}
            self._monitor_snapshot_cache = snap
            self._monitor_snapshot_ts = time.monotonic()
            self._cpu_objetivo = snap.get('cpu_pct', 50.0)
            self._ram_objetivo = snap.get('ram_pct', 50.0)
            gpu_vram = snap.get('gpu_vram', {}) or {}
            self._gpu_objetivo = gpu_vram.get('used_pct', -1.0) if gpu_vram else -1.0
            self._gpu_motor_objetivo = gpu_vram.get('motor_dominante', 'desconocido') if gpu_vram else 'desconocido'
            self._disk_objetivo = 100 - snap.get('disco_pct_libre', 50.0)
        except Exception as e:
            logger.warning(f"Error actualizando métricas del sistema: {e}")

    def _despachar_tareas_periodicas(self):
        """CICLO 16+ FIX: Despachar todas las tareas periódicas en UN SOLO TIMER
        en lugar de 7 QTimers independientes."""
        self._timer_ticks += 1
        
        # Escaneo de rostro a los 10s
        if self._timer_ticks == self._tareas_pendientes["escaneo_rostro"] and hasattr(self, '_escaneo_rostro_reencarnacion'):
            try:
                self._escaneo_rostro_reencarnacion()
            except Exception as e:
                logger.debug(f"Error en escaneo rostro: {e}")
        
        # Verificar intrusiones a los 8s
        if self._timer_ticks == self._tareas_pendientes["verificar_intrusion"] and hasattr(self, '_verificar_intrusiones_enciclopedia'):
            try:
                self._verificar_intrusiones_enciclopedia()
            except Exception as e:
                logger.debug(f"Error verificando intrusiones: {e}")
        
        # Actualizar ánimo cada 300s (5 min)
        if self._timer_ticks % self._tareas_pendientes["actualizar_animo"] == 0 and hasattr(self, '_actualizar_animo'):
            try:
                self._actualizar_animo()
            except Exception as e:
                logger.debug(f"Error actualizando ánimo: {e}")
        
        # Guardar personalidad cada 600s (10 min)
        if self._timer_ticks % self._tareas_pendientes["guardar_persona"] == 0 and hasattr(self, 'personalidad'):
            try:
                self.personalidad.guardar()
            except Exception as e:
                logger.debug(f"Error guardando personalidad: {e}")
        
        # Evaluar evolución cada 600s (10 min)
        if self._timer_ticks % self._tareas_pendientes["evaluar_evolucion"] == 0 and hasattr(self, '_evaluar_evolucion'):
            try:
                self._evaluar_evolucion()
            except Exception as e:
                logger.debug(f"Error evaluando evolución: {e}")

        # FIX: liberar VRAM de Ollama tras 10 min sin usarse — independiente
        # de Tzimtzum (deshabilitado por defecto) y del keep_alive de 5min
        # del payload (que solo se renueva mientras SÍ se usa; esto es un
        # respaldo explícito por si el usuario quiere la VRAM libre antes).
        # Chequeo barato (solo lee un timestamp), cada 60s.
        if self._timer_ticks % 60 == 0:
            try:
                cerebro = self.orquestador.cerebro
                ultima = getattr(cerebro, '_ultima_llamada_ollama_ts', 0.0)
                if ultima and not getattr(cerebro, '_vram_liberada', True):
                    if time.monotonic() - ultima > 600:  # 10 min
                        cerebro.liberar_vram_ollama("inactividad 10 min")
            except Exception as e:
                logger.debug(f"Error liberando VRAM por inactividad: {e}")

    def _reasegurar_topmost(self):
        """RF-306 שכינה תמיד — Re-asegurar HWND_TOPMOST periódicamente.
        Durante Tzimtzum no aplica (ventana oculta)."""
        if getattr(self, '_tzimtzum_ocultando', False) or not self.isVisible():
            return
        # RF-308: Re-aplicar DWM anti-sombra junto con topmost (DWM puede restaurar sombra tras resize)
        self._aplicar_dwm_nosombra()

        # El flush de la cola de resize/move vive en _flush_resize_queue(),
        # con su propio timer de 100ms (ver _iniciar_animacion) — ver nota
        # 2026-10-03 ahí sobre por qué este timer de 5s es demasiado lento
        # para eso cuando el orbe está creciendo.
        self._flush_resize_queue()

    def _flush_resize_queue(self):
        """CICLO 16+ FIX: Procesa la cola de resize/move DEFERRED (fuera del
        hot path de 16ms de _animar). Timer dedicado de 100ms — ver nota
        2026-10-03 en _iniciar_animacion."""
        if self._resize_move_queue is None:
            return
        if not self.isVisible() or getattr(self, '_tzimtzum_ocultando', False):
            return
        q = self._resize_move_queue
        self._resize_move_queue = None
        try:
            self.resize(q["tam"], q["tam"])
            self.move(q["nx"], q["ny"])
            self._pos_anterior_x = float(self.x())
            self._pos_anterior_y = float(self.y())
        except Exception as e:
            logger.debug(f"Error en deferred resize/move: {e}")

    def _iniciar_voz(self):
        self.hilo_escucha = HiloEscucha(self.config)
        # FP-019: Dar a escucha acceso al GestorPersonas
        self.hilo_escucha._gestor_personas = self.gestor_personas
        # FP-044: Dar a escucha acceso al ContextoPantalla para detectar media activa
        self.hilo_escucha._contexto_pantalla = self._contexto_pantalla
        self.hilo_escucha.texto_detectado.connect(self._al_recibir_voz)
        self.hilo_escucha.estado_cambio.connect(self._al_cambiar_estado_escucha)
        self.hilo_escucha.voz_activa.connect(self._al_voz_activa)
        self.hilo_escucha.mensaje_sistema.connect(self._al_mensaje_sistema)

        self.hilo_habla = HiloHabla(self.config)
        self.hilo_habla._personalidad_ref = self.personalidad  # FP-021: Da'at→Hod audio adaptativo
        self.hilo_habla.habla_iniciada.connect(self._al_iniciar_habla)
        self.hilo_habla.habla_terminada.connect(self._al_terminar_habla)
        self.hilo_habla.cola_vacia.connect(self._al_tts_cola_vacia)
        self.hilo_habla.texto_a_recitar.connect(self.hilo_escucha.set_texto_recitando)
        # FIX: el filtro de eco por similitud de contenido (tts_buffer +
        # _check_echo_timestamp en escucha.py) existía pero nunca se
        # alimentaba — set_texto_recitando() solo llena _texto_recitando,
        # que ningún código de escucha.py llega a leer. registrar_tts_output
        # es el método que sí llena tts_buffer, el que _check_echo_timestamp
        # compara de verdad contra lo transcrito.
        self.hilo_habla.texto_a_recitar.connect(self.hilo_escucha.registrar_tts_output)
        self.hilo_escucha.interrupcion_detectada.connect(self._al_interrupcion_usuario)

        self.hilo_habla.start()
        self.hilo_escucha.start()

        # Registrar TTS en API para que comandos remotos de Minimi suenen en desktop
        try:
            from computadora.canales.servidor_api import registrar_habla
            registrar_habla(self.hilo_habla)
        except Exception as e:
            logger.debug(f"No se pudo registrar habla en API Minimi: {e}")

    # ═══════════════════════════════════════════
    # HOT-RELOAD CALLBACKS (FP-028)
    # ═══════════════════════════════════════════

    def _on_modulo_recargado(self, modulo: str, capa: str):
        logger.info(f"Hot-reload exitoso: {modulo} (capa={capa})")

    def _on_recarga_fallida(self, modulo: str, error: str):
        logger.error(f"Hot-reload falló: {modulo} — {error}")

    def _on_requiere_reinicio(self, ruta: str):
        # RF-247 Hit'hadshut Otomátit: reinicio automático al detectar cambio en capa interfaz/voz
        logger.warning(f"Cambio en capa requiere reinicio — relanzando: {ruta}")
        # FIX: el archivo real en la raíz del proyecto es "iniciar computadora.bat"
        # (con espacio) — el literal aquí decía "iniciar_computadora.bat" (con
        # guion bajo), que no existe. cmd /c fallaba con "no se reconoce como
        # un comando interno o externo" y la app se cerraba sin relanzarse
        # (confirmado en un log real: un hot-reload disparado por archivar
        # módulos dejó la app cerrada en vez de reiniciada).
        bat = Path(__file__).resolve().parents[2] / "iniciar computadora.bat"
        if not bat.exists():
            logger.error(f"No se encontró el script de relanzamiento: {bat} — la app se cerrará sin reiniciar")
        subprocess.Popen(["cmd", "/c", str(bat)], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        QApplication.quit()

    # ═══════════════════════════════════════════
    # ESTADO Y ANIMACIÓN
    # ═══════════════════════════════════════════

    def cambiar_estado(self, estado: str):
        # FP-022: Validar transición contra la tabla FSM formal
        nuevo = _STR_A_ESTADO.get(estado)
        if nuevo is None:
            logger.warning(f"Estado desconocido ignorado: {estado!r}")
            return
        actual = _STR_A_ESTADO.get(self._estado)
        # RF-150: Skip FSM validation durante Demo Maljut (recorre todos los estados)
        if not getattr(self, '_demo_en_curso', False):
            if actual is not None and actual in _TRANSICIONES_VALIDAS:
                destinos = _TRANSICIONES_VALIDAS[actual]
                if nuevo not in destinos:
                    logger.error(f"Transición inválida RECHAZADA: {actual.value}→{nuevo.value} — FSM violado")
                    return  # RECHAZAR la transición inválida
        # FP-023 Ohr Jadash: Lock protege mutación de estado
        with self._estado_lock:
            self._estado = estado
        logger.debug(f"Orbe → {estado}")
        # Pre-boot: mantener compacto salvo que Génesis lo expanda
        if not self._boot_completo:
            if hasattr(self, '_vida'):
                self._vida.notificar_estado(estado)
            return
        # Compactarse al descansar, expandirse al activarse
        if estado in ("descanso_guardian", "dormido"):
            # RF-137: No reducir escala si estamos restaurando post-Tzimtzum
            if not getattr(self, '_restaurando_tzimtzum', False):
                self._escala_objetivo = 0.45
                self._particulas.clear()  # FP-047 A3: Limpiar partículas al dormir
        elif estado in ("escuchando", "hablando", "procesando") and self._escala_objetivo < 1.0:
            # WI-166: Solo crecer para estados interactivos, no cualquier cambio
            self._escala_objetivo = 1.0
        # FP-024: Hexagrama al entrar en escucha (conexión empática)
        if estado == "escuchando" and not self._patron_sagrado:
            logger.debug("🔯 Activando patrón sagrado (hexagrama) para estado escucha")
            self._activar_patron_sagrado("hexagrama", 150)
        # Notificar a vida autónoma
        if hasattr(self, '_vida'):
            logger.debug(f"📢 Notificando a VidaAutonoma estado: {estado}")
            self._vida.notificar_estado(estado)

        # Avisar al tema visual activo del cambio de estado, sin que esta clase
        # necesite saber qué tema es ni cómo reacciona (el tema clásico no
        # necesita hacer nada aquí hoy — su lógica de partículas/color ya lee
        # self._estado directamente dentro de _animar() — pero un tema futuro
        # puede implementar manejar_cambio_estado() para reaccionar de verdad).
        if hasattr(self, '_tema_visual'):
            try:
                self._tema_visual.manejar_cambio_estado(estado)
            except Exception as e:
                logger.debug(f"Error en manejar_cambio_estado del tema visual: {e}")

    def event(self, evt):
        """WI-CRIT-002: Handler para eventos thread-safe (postEvent)."""
        if isinstance(evt, _FaseEvent):
            # Procesar cambio de fase sin locks bloqueantes
            self._al_cambio_fase_circadiana(evt.fase)
            return True
        return super().event(evt)

    def _pos_cursor_efectiva(self) -> QPoint:
        """Posición de cursor usada por el pipeline de animación/tacto.

        Permite que la demo (Don del tacto) inyecte una posición sintética
        vía `_demo_cursor_override` sin mover el cursor físico del usuario;
        fuera de la demo (override no seteado), siempre devuelve el cursor
        real `QCursor.pos()` — comportamiento idéntico al anterior.
        """
        override = getattr(self, '_demo_cursor_override', None)
        return override if override is not None else QCursor.pos()

    def _demo_punto_a_distancia(self, dist_px: float) -> QPoint:
        """Punto en coordenadas de pantalla a `dist_px` del centro del orbe.

        Usado por el Acto de "Don del tacto" de la demo para alimentar
        `_demo_cursor_override` y dejar que el pipeline real de `_animar()`
        calcule zona/proximidad/caricia, en vez de asignarlas a mano.
        """
        centro_local = QPoint(self.width() // 2, self.height() // 2)
        centro_global = self.mapToGlobal(centro_local)
        return QPoint(centro_global.x() + int(dist_px), centro_global.y())

    def _animar(self):
        try:
            ahora = time.monotonic()
            start_time = ahora  # CRÍTICO: Medición del frame actual
            delta_t_raw = ahora - getattr(self, '_ultimo_frame_ts', ahora)
            self._ultimo_frame_ts = ahora
            
            # RUBEDO FIX 3: Suavizado MÁXIMO con EMA factor 0.95 para fluidez total
            # 95% nueva muestra, 5% histórica = respuesta rápida + interpolación suave
            _delta_smooth_factor = 0.95  # Máximo suavizado para anillos fluidos
            if not hasattr(self, '_delta_t_smooth'):
                self._delta_t_smooth = delta_t_raw
            self._delta_t_smooth = (delta_t_raw * _delta_smooth_factor + 
                                    self._delta_t_smooth * (1 - _delta_smooth_factor))
            delta_t = self._delta_t_smooth
            
            # RUBEDO FIX 3: Medir FPS SIN logear aquí (hot path limpio)
            # Los logs van a método separado _procesar_metricas_fps() que corre cada 5 segundos
            self._frame_times_buffer.append(delta_t)
            if len(self._frame_times_buffer) > 60:
                self._frame_times_buffer.pop(0)
            
            self._frame_count_since_log += 1
            if delta_t > 0.033:  # Below 30 FPS threshold
                self._slowdown_frames += 1
            if delta_t > self._max_frame_time:
                self._max_frame_time = delta_t
            
            # RUBEDO FIX 3: Always render frames (nunca skipear)
            # Frame skipping causa saltos discretos visibles. Mantener 60 FPS completos.
            self._fase += 0.05
            self._drift_fase += 0.008

            # WI-163: Drenar acciones remotas de Minimi y ejecutar en orbe
            try:
                from computadora.canales.servidor_api import obtener_acciones_remotas
                for accion in obtener_acciones_remotas():
                    self._ejecutar_accion_remota(accion)
            except Exception as e:  # RF-167
                logger.debug("WI-163 drain error: %s", e)

            # Pre-boot: orbe casi invisible, solo embrión latente
            if not self._boot_completo and not hasattr(self, '_bereshit_activo'):
                self._objetivo_brillo = 0.04 + 0.02 * math.sin(self._fase * 0.2)
                self._brillo_actual += (self._objetivo_brillo - self._brillo_actual) * 0.06
                self._escala += (self._escala_objetivo - self._escala) * 0.1

                # FIX: este early-return saltaba directo a repaint() SIN pasar
                # por el bloque de abajo que avanza _rot_anillo1/2/_rot_letras
                # (ver más abajo en _animar) — paintEvent() SÍ dibuja los
                # anillos sagrados durante el pre-boot (no hay ningún check de
                # _boot_completo en paintEvent ni en dibujar_anillos_sagrados),
                # así que se veían dibujados pero completamente congelados
                # mientras el orbe recién arrancado (embrión/minimizado)
                # esperaba el primer "buenos días". Avanzar aquí con la misma
                # velocidad mínima ("idle") que usa el estado de reposo normal
                # para que roten (lento, no brusco) incluso en este estado.
                self._rot_anillo1 += (0.005 * 60) * delta_t  # 0.3 rad/s
                self._rot_anillo2 -= (0.003 * 60) * delta_t  # 0.18 rad/s
                self._rot_letras += (0.002 * 60) * delta_t   # 0.12 rad/s

                # WI-MALJUT-RUBEDO-005: Pre-boot repaint inmediato (no deferred update)
                # Asegura renderizado bloqueante cada frame para fluidez en inicio
                self.repaint()  # Blocking paint (no update() deferred)
                return
        except Exception as e:
            logger.exception(f"❌ EXCEPTION IN _animar(): {e}")
            return

        # דמות Dmut — modificadores visuales según humor (RF-48)
        _humor = self.personalidad.humor_actual if hasattr(self, 'personalidad') else "neutral"
        _dmut_target = _DMUT_VISUAL.get(_humor, _DMUT_DEFAULT)

        # RF-157 + RUBEDO FIX #2: Lerp ADAPTATIVO según frame rate variability
        # Antes: factor=0.05 (hard-coded) → saltos si frame rate baja
        # Ahora: factor adapta a delta_t para mantener velocidad visual consistente
        _lerp_speed = 0.05 * (delta_t / 0.033)  # Scale by actual FPS (0.033s @ 30fps)
        _lerp_speed = min(_lerp_speed, 1.0)  # Clamp to avoid over-interpolation
        for _k in _dmut_target:
            _cur = self._dmut_actual.get(_k, _dmut_target[_k])
            _tgt = _dmut_target[_k]
            self._dmut_actual[_k] = _cur + (_tgt - _cur) * _lerp_speed
        _dmut = self._dmut_actual

        # FIX: interpolar el color del Sistema Ohr (antes saltaba de golpe en
        # cada cambio de estado/herramienta/nivel/gevurá — ver comentario en
        # __init__). Mismo _lerp_speed adaptativo que el tinte de humor.
        _color_ohr_tgt_pri, _color_ohr_tgt_sec = _calcular_color_ohr(
            self._etapa_alquimica, self._estado, self._trabajo_categoria,
            self._cerebro_nivel, getattr(self, '_gevura_categoria', '')
        )
        for _attr, _tgt_color in (
            ('_color_ohr_pri_actual', _color_ohr_tgt_pri),
            ('_color_ohr_sec_actual', _color_ohr_tgt_sec),
        ):
            _actual = getattr(self, _attr)
            _r = _actual.red() + (_tgt_color.red() - _actual.red()) * _lerp_speed
            _g = _actual.green() + (_tgt_color.green() - _actual.green()) * _lerp_speed
            _b = _actual.blue() + (_tgt_color.blue() - _actual.blue()) * _lerp_speed
            setattr(self, _attr, QColor(int(_r), int(_g), int(_b)))
        _rot_mod = _dmut.get("rot_mod", 1.0)  # Fallback a 1.0 si falta
        # WI-ANILLOS-FIX: Garantizar mínimo de rotación (no permitir 0 puro)
        if _rot_mod <= 0.0:
            _rot_mod = 0.5  # Mínimo: rotación a la mitad de velocidad

        # OPTIMIZACION CRÍTICA: Escalar rotaciones con delta_t para suavidad continua
        # Antes: velocidades fijas por frame → movimiento discreto si delta_t varía
        # Ahora: velocidades angulares (rad/s) × delta_t → movimiento fluido independiente de frame rate
        # Fórmula: velocidad_rad_s = velocidad_por_frame_a_60fps * 60
        
        if self._estado == "trabajando":
            self._rot_anillo1 += (0.06 * 60) * _rot_mod * delta_t  # 3.6 rad/s
            self._rot_anillo2 -= (0.04 * 60) * _rot_mod * delta_t  # 2.4 rad/s
            self._rot_letras += (0.05 * 60) * _rot_mod * delta_t   # 3.0 rad/s
        elif self._estado == "procesando":
            # FIX: diferenciar nivel1/2/3 también en velocidad de rotación de
            # anillos (ver _NIVEL_ROT_MOD) — antes los tres niveles rotaban
            # exactamente igual y solo cambiaba un tinte sutil de color.
            _nivel_rot = _NIVEL_ROT_MOD.get(self._cerebro_nivel, 1.0)
            self._rot_anillo1 += (0.03 * 60) * _rot_mod * _nivel_rot * delta_t  # 1.8 rad/s base
            self._rot_anillo2 -= (0.02 * 60) * _rot_mod * _nivel_rot * delta_t  # 1.2 rad/s base
            self._rot_letras += (0.025 * 60) * _rot_mod * _nivel_rot * delta_t  # 1.5 rad/s base
        elif self._estado == "hablando":
            self._rot_anillo1 += (0.015 * 60) * _rot_mod * delta_t # 0.9 rad/s
            self._rot_anillo2 -= (0.01 * 60) * _rot_mod * delta_t  # 0.6 rad/s
            self._rot_letras += (0.008 * 60) * _rot_mod * delta_t  # 0.48 rad/s
        else:
            self._rot_anillo1 += (0.005 * 60) * _rot_mod * delta_t # 0.3 rad/s
            self._rot_anillo2 -= (0.003 * 60) * _rot_mod * delta_t # 0.18 rad/s
            self._rot_letras += (0.002 * 60) * _rot_mod * delta_t  # 0.12 rad/s

        # Brillo según estado — HF-026: valores aumentados para visibilidad mínima
        if self._estado == "dormido":
            self._objetivo_brillo = 0.18 + 0.06 * math.sin(self._fase * 0.3)
        elif self._estado == "descanso_guardian":
            # Tenue pero visible, pulsación lenta — guardián dormido pero alerta
            self._objetivo_brillo = 0.14 + 0.04 * math.sin(self._fase * 0.15)
        elif self._estado == "despertando":
            # Rampa cálida creciente
            self._objetivo_brillo = 0.35 + 0.15 * math.sin(self._fase * 1.2)
        elif self._estado == "cortesia":
            # Breve resplandor dorado
            self._objetivo_brillo = 0.60 + 0.15 * math.sin(self._fase * 1.8)
        elif self._estado == "alerta_extrano":
            # Ámbar parpadeante — extraño detectado
            self._objetivo_brillo = 0.65 + 0.25 * math.sin(self._fase * 3.5)
        elif self._estado == "vigilia":
            # Verde estable — modo guardián consciente
            self._objetivo_brillo = 0.38 + 0.10 * math.sin(self._fase * 0.5)
        elif self._estado == "escuchando":
            self._objetivo_brillo = 0.55 + 0.15 * math.sin(self._fase * 0.8)
        elif self._estado == "procesando":
            # FIX: frecuencia de pulso distinta por nivel de cerebro (ver
            # _NIVEL_PULSO_FREQ) — nivel1 pulsa nervioso/corto, nivel2 lento
            # ("pensando"), nivel3 medio. Antes los tres pulsaban idéntico.
            _nivel_freq = _NIVEL_PULSO_FREQ.get(self._cerebro_nivel, 2.5)
            self._objetivo_brillo = 0.65 + 0.25 * math.sin(self._fase * _nivel_freq)
        elif self._estado == "trabajando":
            self._objetivo_brillo = 0.75 + 0.20 * math.sin(self._fase * 3.0)
        elif self._estado == "hablando":
            self._objetivo_brillo = 0.85 + 0.1 * math.sin(self._fase * 1.5)
        elif self._estado == "error":
            self._objetivo_brillo = 0.5 + 0.4 * math.sin(self._fase * 4.0)
        elif self._estado == "gevura_activa":
            # גבורה Gevurá — Rojo parpadeante, bloqueo activo
            self._objetivo_brillo = 0.70 + 0.25 * math.sin(self._fase * 5.0)

        self._brillo_actual += (self._objetivo_brillo - self._brillo_actual) * 0.12

        # דמות Dmut — aplicar modificador de brillo según humor (RF-48)
        self._brillo_actual = max(0.0, min(1.0, self._brillo_actual + _dmut["brillo_mod"]))

        # RF-152: Modulación circadiana — brillo sutil según fase del día
        _fc = getattr(self, '_fase_circadiana', 'activo')
        if _fc == "activo":
            self._brillo_actual = min(1.0, self._brillo_actual + 0.03)
        elif _fc == "descanso_guardian":
            self._brillo_actual = max(0.0, self._brillo_actual - 0.02)

        # Escala suave
        self._escala += (self._escala_objetivo - self._escala) * 0.1
        # RF-137: Auto-limpiar flag de restauración Tzimtzum al llegar a escala completa
        if getattr(self, '_restaurando_tzimtzum', False) and self._escala >= 0.95:
            self._restaurando_tzimtzum = False

        # Generar partículas (modulada por Dmut humor — RF-48)
        # FP-108: Suprimir generación durante movimiento para liberar ciclos de render
        _en_mov = (self._arrastrando
                   or abs(self._impulso_vx) > 0.5
                   or abs(self._impulso_vy) > 0.5)
        _part_mod = _dmut["particulas_mod"]
        # RF-153: Densidad de partículas proporcional a rasgo energía de personalidad
        _energia = self.personalidad.rasgo("energia") if hasattr(self, 'personalidad') else 0.5
        _part_mod *= 0.5 + _energia  # rango 0.5x (baja energía) a 1.5x (alta energía)
        _part_gen_penalty = 0.55 if _en_mov else 1.0
        if len(self._particulas) < self._max_particulas:
            if self._estado == "trabajando" and random.random() < 0.4 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR * 1.1))
            elif self._estado == "procesando" and random.random() < 0.3 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR))
            elif self._estado == "hablando" and random.random() < 0.2 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR * 0.8))
            elif self._estado == "alerta_extrano" and random.random() < 0.35 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR * 1.2))
            elif self._estado == "cortesia" and random.random() < 0.15 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR * 0.7))
            elif random.random() < 0.05 * _part_mod * _part_gen_penalty:
                self._particulas.append(Particula(RADIO_RESPLANDOR))

        # RF-165: Resize ANTES de calcular delta para que el reset de pos_anterior
        # surta efecto en el mismo frame y no genere delta fantasma en partículas
        # RF-198: Incluir movimiento autónomo para evitar tug-of-war resize vs _interpolar
        _en_movimiento_autonomo = (hasattr(self, '_vida')
                                   and self._vida._pos_objetivo is not None)
        _en_interaccion = (self._arrastrando
                           or abs(self._impulso_vx) > 0.5
                           or abs(self._impulso_vy) > 0.5
                           or _en_movimiento_autonomo
                           or self._en_transito)
        if not _en_interaccion:
            _margen_vfx = max(20, int(32 / max(self._escala, 0.1)))
            radio_visual = (RADIO_NUCLEO + RADIO_NUCLEO * 2.2) * self._escala
            if self._particulas:
                max_r = max(
                    math.hypot(p.pos.x(), p.pos.y()) for p in self._particulas
                )
                max_r = min(max_r, RADIO_RESPLANDOR * 2.0)
                # Hallazgo 2026-10-03: la fuerza de "respiración radial" de las
                # partículas (ver Particula.actualizar) hace que max_r oscile
                # frame a frame cuando el humor no es neutral (particulas_mod
                # != 1.0). Sin amortiguar esto, tam_necesario cruzaba el umbral
                # de abajo muchas veces por segundo, encolando (y con el
                # flush ahora de 100ms, EJECUTANDO) resizes reales de ventana
                # con mucha más frecuencia que antes — percibido como
                # micro-congelamientos periódicos estando quieto. Un EMA lento
                # aquí separa la oscilación rápida (puramente decorativa) del
                # tamaño de ventana real, que solo necesita seguir el radio
                # "promedio" de las partículas, no su pico instantáneo.
                if not hasattr(self, '_radio_particulas_ema'):
                    self._radio_particulas_ema = max_r
                else:
                    self._radio_particulas_ema += (max_r - self._radio_particulas_ema) * 0.08
                radio_particulas = self._radio_particulas_ema * self._escala + 4
                radio_visual = max(radio_visual, radio_particulas)
            tam_necesario = max(60, int(radio_visual * 2 + _margen_vfx))
            # Hallazgo 2026-10-03: zona muerta ampliada de 2px→6px. El flush
            # de la cola de resize ahora es rápido (100ms, ver
            # _flush_resize_queue) para no dejar la ventana rezagada durante
            # el CRECIMIENTO (wake word), pero eso significa que cualquier
            # cruce del umbral aquí se traduce en un resize() real pronto —
            # una zona muerta más ancha, sumada al EMA de arriba, evita que
            # el jitter decorativo de las partículas dispare resizes reales
            # constantemente mientras el orbe está quieto.
            if abs(tam_necesario - self._tamano_ventana) > 6:
                # RF-165: lerp float → round() elimina zona muerta de int()
                self._tamano_ventana += (tam_necesario - self._tamano_ventana) * 0.25
                tam_render = round(self._tamano_ventana)
                centro = self.geometry().center()

                # CICLO 16+ FIX: Enqueue resize/move en cola deferred, NO EN HOT PATH
                nx = centro.x() - tam_render // 2
                ny = centro.y() - tam_render // 2
                limitado = self._limitar_posicion_pantalla(nx, ny, tam_render, tam_render)
                nx, ny = limitado.x(), limitado.y()

                # Enqueue para procesar FUERA del hot path de _animar
                self._resize_move_queue = {"tam": tam_render, "nx": nx, "ny": ny}

            elif abs(tam_necesario - self._tamano_ventana) > 0.5:
                self._tamano_ventana = float(tam_necesario)  # Snap final

        # Actualizar partículas vivas (con inercia FP-024)
        # HF-028 + FP-042: Amortiguar delta durante drag/impulso (40%) en vez de
        # suprimir completamente, para conservar efecto visual de inercia
        _raw_dx = float(self.x()) - self._pos_anterior_x
        _raw_dy = float(self.y()) - self._pos_anterior_y
        self._pos_anterior_x = float(self.x())
        self._pos_anterior_y = float(self.y())
        if self._arrastrando or abs(self._impulso_vx) > 0.5 or abs(self._impulso_vy) > 0.5:
            # RF-135: Amortiguación dinámica — alta vel→0.4, baja vel→0.7
            _vel_norm = min(1.0, math.hypot(_raw_dx, _raw_dy) / 30.0)
            _damp = 0.4 + 0.3 * (1.0 - _vel_norm)
            dx, dy = _raw_dx * _damp, _raw_dy * _damp
        else:
            dx, dy = _raw_dx, _raw_dy
        
        # WI-MALJUT-RUBEDO-002: Try-except para cleanup seguro de particulas
        # Si p.actualizar() falla, particula se remueve para evitar memory leak
        # Aplicar multiplicador de velocidad angular según Dmut (p.ej. emocionado)
        _part_speed_mult = _dmut.get("particulas_mod", 1.0) * getattr(self, '_demo_dmut_factor', 1.0)
        for p in list(self._particulas):  # iterate sobre copia para evitar issues
            try:
                if not p.actualizar(dx, dy, speed_mult=_part_speed_mult):  # actualizar() retorna False si muere
                    self._particulas.remove(p)
            except Exception as e:
                # Particula corrompida → remover del pool + log debug
                logger.debug(f"Particula error (limpiar): {e}")
                try:
                    self._particulas.remove(p)
                except ValueError:
                    pass  # Ya fue removida por otro path

        # Lerp de colores alquímicos (FP-024 Pilar B + RF-175 adaptive lerp)
        if self._alq_lerp_progress < 1.0:
            # RF-175: Lerp rápido durante demo (~1.5s), normal (~60s) fuera de demo
            _lerp_speed = 1.0 / (1.5 * 30) if getattr(self, '_demo_en_curso', False) else 1.0 / (60 * 30)
            self._alq_lerp_progress = min(1.0, self._alq_lerp_progress + _lerp_speed)
            # WI-241: Blend factor variable — demo 5x más rápido para transiciones visibles
            _blend = 0.10 if getattr(self, '_demo_en_curso', False) else 0.02
            for attr, target_attr in [("_color_alq_primario", "_color_alq_target_pri"),
                                       ("_color_alq_secundario", "_color_alq_target_sec")]:
                cur = getattr(self, attr)
                tgt = getattr(self, target_attr)
                cur.setRed(int(cur.red() + (tgt.red() - cur.red()) * _blend))
                cur.setGreen(int(cur.green() + (tgt.green() - cur.green()) * _blend))
                cur.setBlue(int(cur.blue() + (tgt.blue() - cur.blue()) * _blend))

        # FIX: Cache cursor position from OUTSIDE mapFromGlobal (expensive WinAPI call)
        # This was being called in paintEvent() TWICE (lines 1838, 1921), wasting 10-25% of frame budget
        # OPTIMIZACION: Precalcular pos_local AQUI, no en paintEvent()
        pos_local_cache = None
        if self._proximidad > 0.1:  # Threshold for any cursor-dependent rendering
            pos_local_cache = self.mapFromGlobal(self._pos_cursor_efectiva())  # ✅ SOLO UNA VEZ, en _animar()
        self._cached_cursor_local = pos_local_cache  # Store for use in paintEvent

        # WI-ANILLOS-LERP-RECURSOS: Interpolación suave de métricas del sistema
        # Patrón Jarvis: Factor 0.08 = ~12 frames (~200ms) para suavidad perceptible
        # (Las métricas se actualizan cada 1s, pero se renderiza suavemente cada 16ms)
        _lerp_factor = 0.08
        self._cpu_actual += (self._cpu_objetivo - self._cpu_actual) * _lerp_factor
        self._ram_actual += (self._ram_objetivo - self._ram_actual) * _lerp_factor
        self._gpu_actual += (self._gpu_objetivo - self._gpu_actual) * _lerp_factor
        self._disk_actual += (self._disk_objetivo - self._disk_actual) * _lerp_factor
        # Categórico: se asigna directo (no se interpola un string). El cache
        # pesado del monitor ya refresca cada ~3s, así que no parpadea frame a frame.
        self._gpu_motor_actual = self._gpu_motor_objetivo

        # WI-MALJUT-RUBEDO-004: Gradual offset reset durante collapse
        # FIX: la fórmula anterior (`offset *= 1 - lerp_factor*0.1`) apenas
        # reducía el offset durante ~9 de los 10 frames (factor entre 1.0 y
        # 0.91) y luego lo llevaba a 0 de golpe en el último frame — con la
        # ventana YA encogida, eso dejaba al orbe dibujado fuera del área
        # visible (invisible) durante casi toda la transición. Ahora es una
        # interpolación lineal real desde el offset inicial capturado hasta 0.
        if self._offset_collapse_in_progress and self._offset_collapse_timer > 0:
            self._offset_collapse_timer -= 1
            _progreso = self._offset_collapse_timer / 10.0  # 1.0 → 0.0 a lo largo de 10 frames
            self._render_offset_x = self._offset_collapse_inicio_x * _progreso
            self._render_offset_y = self._offset_collapse_inicio_y * _progreso
            if self._offset_collapse_timer <= 0:
                self._render_offset_x = 0.0
                self._render_offset_y = 0.0
                self._offset_collapse_in_progress = False
        
        # FIX CRÍTICO: SIEMPRE actualizar para mantener 60 FPS fluido
        # Las animaciones continuas requieren repaint cada frame, sin excepciones
        # WI-MALJUT-002: El early-exit por cursor lejano causaba freeze sin repaint
        self.repaint()  # Immediate blocking paint, not deferred update()
        
        # FP-013: Fuerza gravitacional de partículas hacia cursor
        if self._proximidad > 0.2 and pos_local_cache is not None:
            cursor_ang = math.atan2(
                pos_local_cache.y() - self.height() / 2,
                pos_local_cache.x() - self.width() / 2,
            )
            fuerza = self._proximidad * 0.015
            for p in self._particulas:
                # Tirar el ángulo de la partícula hacia el cursor
                delta = cursor_ang - p.angulo
                # Normalizar a [-pi, pi]
                delta = (delta + math.pi) % (2 * math.pi) - math.pi
                p.angulo += delta * fuerza

        # Actualizar indicadores de herramientas (CICLO 16+ FIX: similar a particulas)
        for ind in list(self._indicadores_herramientas):
            if not ind.actualizar():
                self._indicadores_herramientas.remove(ind)

        # HF-024b: Avanzar ripple de escucha
        if self._ripple_fase >= 0:
            self._ripple_fase += 0.035  # ~1.5s duration at 30fps
            if self._ripple_fase > 1.5:
                self._ripple_fase = -1.0

        # RF-165: Bloque de resize movido ANTES del cálculo de _raw_dx/dy
        # (ver arriba, justo antes de "Actualizar partículas vivas")

        # HF-025c: Tzimtzum — ocultar tras animación de contracción
        if self._tzimtzum_ocultando and self._escala < 0.03:
            self._tzimtzum_ocultando = False
            self.hide()

        # ─── יד Yad — Tracking de proximidad (FP-013) ───
        pos_global = self._pos_cursor_efectiva()
        pos_local = self.mapFromGlobal(pos_global)
        centro_w = QPointF(self.width() / 2, self.height() / 2)
        distancia = math.hypot(
            pos_local.x() - centro_w.x(), pos_local.y() - centro_w.y()
        )
        
        # CICLO 16+ FIX: Early-exit si cursor muy lejos (>500px = fuera de rango util)
        if distancia > 500:
            self._proximidad = 0.0
            self._zona_tacto = 0
            self._en_nefesh = False
            self._tacto_continuo_inicio = 0.0
            self._toque_atento_inicio = 0.0
            self._cursor_anterior = pos_global
            return  # SKIP resto del tracking costoso
        
        self._tacto_velocidad = math.hypot(
            pos_global.x() - self._cursor_anterior.x(),
            pos_global.y() - self._cursor_anterior.y(),
        )
        self._cursor_anterior = pos_global
        self._proximidad = max(0.0, min(1.0, 1.0 - distancia / 300.0))

        # Tracking de contacto sostenido (para distinguir caricia de roce)
        if self._proximidad > 0.3:
            if self._tacto_continuo_inicio == 0.0:
                self._tacto_continuo_inicio = time.monotonic()
        else:
            self._tacto_continuo_inicio = 0.0

        # Zona de tacto
        zona_anterior = self._zona_tacto
        if distancia > 300:
            self._zona_tacto = 0   # Aín
        elif distancia > 200:
            self._zona_tacto = 1   # Reshimó
        elif distancia > 100:
            self._zona_tacto = 2   # Kav
        elif distancia > 50:
            self._zona_tacto = 3   # Yesod
        else:
            self._zona_tacto = 4   # Nefesh

        # Detección de entrada a Nefesh (para caricia)
        ahora = time.monotonic()
        if self._zona_tacto == 4 and not self._en_nefesh:
            self._en_nefesh = True
            self._caricia_timestamps.append(ahora)
            # Limpiar timestamps viejos (>4s)
            self._caricia_timestamps = [
                t for t in self._caricia_timestamps if ahora - t < 4.0
            ]
        elif self._zona_tacto != 4:
            self._en_nefesh = False

        # Detección de caricia: 3+ entradas a Nefesh en <4s
        entradas_recientes = [
            t for t in self._caricia_timestamps if ahora - t < 4.0
        ]
        if len(entradas_recientes) >= 3:
            self._caricia_timestamps.clear()
            self._objetivo_brillo = min(1.0, self._objetivo_brillo + 0.5)
            # Explosión suave de partículas (FP-047 A4: respetar cap)
            for _ in range(min(8, self._max_particulas - len(self._particulas))):
                self._particulas.append(Particula(RADIO_RESPLANDOR * 0.6))
            # FP-014: Conectar caricia con Personalidad y Memoria
            self.personalidad.registrar_caricia()
            # FP-033 B2: Cooldown 30s para no inundar memoria con caricias repetidas
            if ahora - self._last_caricia_memory_ts > 30.0:
                self._last_caricia_memory_ts = ahora
                try:
                    from computadora.memoria.memoria import add_memory
                    add_memory("system", "Sentí una caricia del amo", {"tipo": "tacto", "gesto": "caricia"})
                except Exception as e:
                    logger.debug("Error registrando caricia en memoria: %s", e)
            self._ultimo_tacto_info = {"gesto": "caricia", "ts": ahora}
            logger.debug("Yad: caricia detectada")
            # RF-138: Caricia resetea inactividad — no irse a casa
            if hasattr(self, '_vida'):
                self._vida._ticks_inactivo = 0
                self._vida._pos_objetivo = None

        # Detección de brisa: cruza zona 2→4→2 en <500ms con velocidad >30
        # (simplificado: velocidad alta en zona cercana)
        if self._zona_tacto >= 3 and self._tacto_velocidad > 30:
            for _ in range(min(3, self._max_particulas - len(self._particulas))):
                self._particulas.append(Particula(RADIO_RESPLANDOR * 0.9))

        # Toque atento: cursor quieto en Nefesh >2s durante hablando
        if (self._zona_tacto == 4 and self._tacto_velocidad < 2.0
                and self._estado == "hablando"):
            if self._toque_atento_inicio == 0.0:
                self._toque_atento_inicio = ahora
            elif ahora - self._toque_atento_inicio > 2.0:
                self._toque_atento_inicio = 0.0  # solo detectar una vez
                # FP-014: Conectar toque atento con Personalidad y Memoria
                self.personalidad.registrar_atencion_fisica()
                # FP-033 B2: Reutiliza cooldown de caricia para evitar flood de memoria táctil
                if ahora - self._last_caricia_memory_ts > 30.0:
                    self._last_caricia_memory_ts = ahora
                    try:
                        from computadora.memoria.memoria import add_memory
                        add_memory("system", "El amo me prestó atención mientras hablaba", {"tipo": "tacto", "gesto": "toque_atento"})
                    except Exception as e:
                        logger.debug("Error registrando toque en memoria: %s", e)
                self._ultimo_tacto_info = {"gesto": "toque_atento", "ts": ahora}
                logger.debug("Yad: toque atento detectado")
        else:
            self._toque_atento_inicio = 0.0

        # Bonus de brillo por proximidad
        if self._proximidad > 0.1:
            self._objetivo_brillo = min(1.0, self._objetivo_brillo + self._proximidad * 0.4)

        # Impulso físico (empujón)
        if abs(self._impulso_vx) > 0.5 or abs(self._impulso_vy) > 0.5:
            pos = self.pos()
            nx = pos.x() + self._impulso_vx
            ny = pos.y() + self._impulso_vy
            geo = self._geometria_pantalla_actual()
            if geo is None:
                return
            if nx < geo.left() or nx + self.width() > geo.right() + 1:
                self._impulso_vx *= -0.6
            if ny < geo.top() or ny + self.height() > geo.bottom() + 1:
                self._impulso_vy *= -0.6
            self.move(self._limitar_posicion_pantalla(nx, ny))
            # FP-049: NO sincronizar _pos_anterior aquí — el timer lo hace.
            self._impulso_vx *= 0.92
            self._impulso_vy *= 0.92
            # Cancelar movimiento autónomo mientras hay inercia
            if hasattr(self, '_vida'):
                self._vida._pos_objetivo = None

        # FP-024: Decrementar timer de patrón sagrado
        if self._patron_timer > 0:
            self._patron_timer -= 1
            if self._patron_timer <= 0:
                self._patron_sagrado = ""

        # Medición de rendimiento — logging en buffer circular (fuera del hot path)
        end_time = time.monotonic()
        frame_time = end_time - start_time

        # CICLO 16+ FIX: Buffer circular de frames lentos (reportar DESPUES).
        # FIX: usa su propio deque acotado (_frame_proc_times, maxlen=100),
        # no el `_frame_times_buffer` de arriba (ese mide delta_t entre
        # frames, no tiempo de procesamiento, y ya tiene su propio recorte).
        self._frame_proc_times.append(frame_time)

        # Cada 30 frames (~1s a 30fps), verificar si hay lentos y loguear resumen
        if not hasattr(self, '_frame_log_ticker'):
            self._frame_log_ticker = 0
        self._frame_log_ticker += 1
        if self._frame_log_ticker >= 30:
            self._frame_log_ticker = 0
            # FIX: slow_frames no puede exceder tamaño del buffer circular
            buffer_size = len(self._frame_proc_times)
            slow_frames = sum(1 for ft in self._frame_proc_times if ft > 0.04)
            if slow_frames > 5:  # >5 frames lentos en últimas N frames
                avg_fps = 1.0 / (sum(self._frame_proc_times) / buffer_size) if buffer_size > 0 else 0
                logger.warning(f"Frame slow detected: {slow_frames}/{buffer_size} lentos, avg FPS: {avg_fps:.1f}")

        # FIX: este método tenía un SEGUNDO `self.repaint()` redundante aquí
        # (duplicado de la línea ~1625, que ya repinta incondicionalmente
        # antes del único early-return de la función). Dos repaints por tick
        # dobla el costo de pintado cada frame cuando el cursor está cerca
        # del orbe — contribuía a los "Frame slow detected" observados.

    def _activar_patron_sagrado(self, nombre: str, duracion: int = 180):
        """FP-024: Activa un patrón de geometría sagrada temporal."""
        self._patron_sagrado = nombre
        self._patron_duracion = float(duracion)
        self._patron_timer = float(duracion)

    # ═══════════════════════════════════════════
    # DIBUJO
    # ═══════════════════════════════════════════

    def _draw_state(self):
        """FP-027: Snapshot del estado de animación para el dibujante externo."""
        from computadora.interfaz.dibujante_orbe import DrawState
        # FP-024: Calcular progreso del patrón sagrado (0.0→1.0)
        _pat_prog = 0.0
        if self._patron_sagrado and self._patron_duracion > 0:
            _pat_prog = 1.0 - (self._patron_timer / self._patron_duracion)
        return DrawState(
            escala=self._escala,
            fase=self._fase,
            rot_anillo1=self._rot_anillo1,
            rot_anillo2=self._rot_anillo2,
            rot_letras=self._rot_letras,
            particulas=list(self._particulas),  # FP-047 A5: copia defensiva (deque→list)
            indicadores_herramientas=self._indicadores_herramientas,
            cerebro_nivel=self._cerebro_nivel,
            patron_sagrado=self._patron_sagrado,
            patron_progreso=_pat_prog,
            etapa_alquimica=self._etapa_alquimica.value,
            carga_emocional=self._map_estado_a_carga_emocional(),
        )

    def _map_estado_a_carga_emocional(self):
        """Determina una intensidad emocional (0-1) según el estado y humor.
        Usada por el tema visual para intensificar partículas/anillos."""
        if getattr(self, '_estado', '') in ('error', 'alerta_extrano'):
            return 0.95
        if getattr(self, '_estado', '') in ('emocionado', 'hablando', 'trabajando'):
            return 0.75
        if getattr(self, '_estado', '') == 'procesando':
            return 0.55
        if getattr(self, '_estado', '') == 'escuchando':
            return 0.35
        if getattr(self, '_estado', '') in ('dormido', 'idle'):
            return 0.12

        return 0.25

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        centro = self.rect().center()
        cx = centro.x() + int(self._render_offset_x)
        cy = centro.y() + int(self._render_offset_y)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        if getattr(self, '_en_transito', False):
            # FIX: en tránsito autónomo la ventana real se expande a un bounding
            # box origen→destino (VidaAutonoma._expandir_ventana_transito) que
            # puede cubrir casi toda la pantalla, pero el contenido visible
            # (orbe + glow + partículas + indicadores) siempre cabe en el mismo
            # cuadro de "TAMANO_PLENO + margen" que usa la ventana colapsada
            # normal. Limpiar/pintar solo ese cuadro, centrado en el offset
            # actual, evita que el costo de fillRect (ventana en capas
            # translúcida — UpdateLayeredWindow en Windows) escale con la
            # distancia recorrida, que es la causa del traqueteo visual
            # reportado específicamente al moverse.
            # FIX: debe coincidir EXACTO con el tamaño que usa VidaAutonoma al
            # colapsar la ventana tras un tránsito (TAMANO_PLENO + MARGEN_VFX,
            # ver vida_autonoma.py) — antes usaba "+40" hardcodeado, 26px más
            # chico que el radio real del glow (123px a escala=1.0 → 246px de
            # diámetro), recortando el glow/anillos contra el borde.
            if hasattr(self, '_vida'):
                _tam_contenido = (getattr(self._vida, 'TAMANO_PLENO', 180)
                                  + getattr(self._vida, 'MARGEN_VFX', 76))
            else:
                _tam_contenido = 256
            _half = _tam_contenido / 2.0
            painter.fillRect(QRectF(cx - _half, cy - _half, _tam_contenido, _tam_contenido), Qt.GlobalColor.transparent)
        else:
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        brillo = max(0.0, min(1.0, self._brillo_actual))

        # FIX: leer el color YA interpolado por _animar() (ver __init__ y
        # _animar) en vez de recalcular _calcular_color_ohr() con el estado
        # crudo aquí — eso hacía que el color saltara de golpe en cada
        # cambio de estado/herramienta/nivel/gevurá. Se copian con QColor()
        # porque el código de abajo los muta in-place (tinte de humor).
        color_primario = QColor(getattr(self, '_color_ohr_pri_actual', QColor(200, 150, 40)))
        color_secundario = QColor(getattr(self, '_color_ohr_sec_actual', QColor(120, 90, 30)))

        _dmut_p = self._dmut_actual if hasattr(self, '_dmut_actual') else _DMUT_DEFAULT
        _humor_s = self.personalidad.humor_secundario if hasattr(self, 'personalidad') else ""
        if _humor_s and _humor_s in _DMUT_VISUAL:
            _dmut_s = _DMUT_VISUAL[_humor_s]
            _peso_s = getattr(self.personalidad, 'peso_secundario', 0.0) if hasattr(self, 'personalidad') else 0.0
            _w = min(0.3, _peso_s)
            _tr = int(_dmut_p["tinte_r"] * (1 - _w) + _dmut_s["tinte_r"] * _w)
            _tg = int(_dmut_p["tinte_g"] * (1 - _w) + _dmut_s["tinte_g"] * _w)
            _tb = int(_dmut_p["tinte_b"] * (1 - _w) + _dmut_s["tinte_b"] * _w)
        else:
            _tr, _tg, _tb = int(_dmut_p["tinte_r"]), int(_dmut_p["tinte_g"]), int(_dmut_p["tinte_b"])

        if _tr or _tg or _tb:
            _df = getattr(self, '_demo_dmut_factor', 1.0) if getattr(self, '_demo_en_curso', False) else 1.0
            _tr, _tg, _tb = int(_tr * _df), int(_tg * _df), int(_tb * _df)
            color_primario.setRed(max(0, min(255, color_primario.red() + _tr)))
            color_primario.setGreen(max(0, min(255, color_primario.green() + _tg)))
            color_primario.setBlue(max(0, min(255, color_primario.blue() + _tb)))
            color_secundario.setRed(max(0, min(255, color_secundario.red() + _tr)))
            color_secundario.setGreen(max(0, min(255, color_secundario.green() + _tg)))
            color_secundario.setBlue(max(0, min(255, color_secundario.blue() + _tb)))

        _en_movimiento_render = (
            self._arrastrando
            or abs(self._impulso_vx) > 0.5
            or abs(self._impulso_vy) > 0.5
        )
        _glow_step = 9 if _en_movimiento_render else 5
        _glow_intensity_boost = 1.5 if getattr(self, '_demo_en_curso', False) else 1.0
        _prox = self._proximidad
        
        # OPTIMIZACION CRÍTICA: Usar cached cursor position en lugar de mapFromGlobal()
        # mapFromGlobal es costosa (WinAPI), no debe ejecutarse cada frame
        pos_local = getattr(self, '_cached_cursor_local', None)
        if _prox > 0.1 and pos_local is not None:
            _prox_dx = pos_local.x() - cx
            _prox_dy = pos_local.y() - cy
        else:
            _prox_dx = _prox_dy = 0

        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(40, 0, -_glow_step):
            ratio = i / 40
            c = QColor(color_primario)
            _base_glow = 0.35 if getattr(self, '_demo_en_curso', False) else 0.25
            a = brillo * (1.0 - ratio) * _base_glow * _glow_intensity_boost
            if _prox > 0.1:
                a += _prox * 0.08 * (1.0 - ratio) * _glow_intensity_boost
            c.setAlphaF(max(0.0, min(1.0, a)))
            painter.setBrush(c)
            r = int((RADIO_NUCLEO + i * 2.2) * self._escala)
            painter.drawEllipse(QPoint(cx, cy), r, r)

        # El tema visual activo dibuja anillos/núcleo/partículas/letras/emet.
        # OrbeComputadora no necesita saber qué tema es ni cómo dibuja.
        self._tema_visual.renderizar(painter, cx, cy, brillo, color_primario, color_secundario)

        self._dibujar_indicadores_herramientas(painter, cx, cy, brillo)

        if self._estado == "procesando" and self._cerebro_nivel in NOMBRES_NIVEL:
            self._dibujar_indicador_nivel(painter, cx, cy, brillo)

        if self._ripple_fase >= 0:
            progreso = self._ripple_fase / 1.5
            radio_min = int(RADIO_NUCLEO * self._escala)
            radio_max = int(RADIO_RESPLANDOR * 1.3 * self._escala)
            radio_ripple = radio_min + int((radio_max - radio_min) * progreso)
            alpha_ripple = max(0.0, (1.0 - progreso) * 0.4 * brillo)
            c_ripple = QColor(color_primario)
            c_ripple.setAlphaF(max(0.0, min(1.0, alpha_ripple)))
            grosor = max(1.0, 2.5 * (1.0 - progreso))
            pen_ripple = QPen(c_ripple, grosor)
            painter.setPen(pen_ripple)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPoint(cx, cy), radio_ripple, radio_ripple)

        if self._proximidad > 0.5:
            # OPTIMIZACION: Usar cached cursor position en lugar de mapFromGlobal() costosa
            pos_cursor_local = getattr(self, '_cached_cursor_local', None)
            if pos_cursor_local is not None:
                heat = QRadialGradient(pos_cursor_local.x(), pos_cursor_local.y(), RADIO_RESPLANDOR * self._escala)
                c_heat = QColor(255, 180, 60)
                c_heat.setAlphaF(max(0.0, min(1.0, (self._proximidad - 0.5) * 0.3 * brillo)))
                heat.setColorAt(0.0, c_heat)
                heat.setColorAt(1.0, QColor(0, 0, 0, 0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(heat)
                r_heat = int(RADIO_RESPLANDOR * self._escala * 1.2)
                painter.drawEllipse(QPoint(cx, cy), r_heat, r_heat)

        painter.end()

    def _dibujar_anillos_sagrados(self, painter: QPainter, cx, cy, brillo, color):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_anillos_sagrados
        dibujar_anillos_sagrados(painter, cx, cy, brillo, color, self._draw_state())

    def _dibujar_particulas(self, painter: QPainter, cx, cy, color):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_particulas
        dibujar_particulas(painter, cx, cy, color, self._draw_state())

    def _dibujar_letras_orbitantes(self, painter: QPainter, cx, cy, brillo, color):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_letras_orbitantes
        dibujar_letras_orbitantes(painter, cx, cy, brillo, color, self._draw_state())

    def _dibujar_nucleo(self, painter: QPainter, cx, cy, brillo, color_pri, color_sec):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_nucleo
        dibujar_nucleo(painter, cx, cy, brillo, color_pri, color_sec, self._draw_state())

    def _dibujar_emet(self, painter: QPainter, cx, cy, brillo, color):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_emet
        dibujar_emet(painter, cx, cy, brillo, color, self._draw_state())

    def _dibujar_indicadores_herramientas(self, painter: QPainter, cx, cy, brillo):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_indicadores_herramientas
        dibujar_indicadores_herramientas(painter, cx, cy, brillo, self._draw_state())

    def _dibujar_indicador_nivel(self, painter: QPainter, cx, cy, brillo):
        """FP-027: Delegado a dibujante_orbe."""
        from computadora.interfaz.dibujante_orbe import dibujar_indicador_nivel
        dibujar_indicador_nivel(painter, cx, cy, brillo, self._draw_state(), COLORES_NIVEL, NOMBRES_NIVEL)

    # ═══════════════════════════════════════════
    # INTERACCIÓN — RATÓN
    # ═══════════════════════════════════════════

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # FP-013: Solo capturar clicks en el núcleo; el resto pasa a la app de abajo
            dx = event.pos().x() - self.width() / 2
            dy = event.pos().y() - self.height() / 2
            dist = math.sqrt(dx * dx + dy * dy)
            umbral_nucleo = RADIO_NUCLEO * self._escala * 1.5
            if dist > umbral_nucleo:
                event.ignore()
                return
            self._arrastrando = True
            self._offset = event.pos()
            self._empujon_inicio = event.globalPosition().toPoint()
            logger.debug(f"HF-028 drag-start: pos=({self.x()},{self.y()}) tam={self.width()} offset=({self._offset.x()},{self._offset.y()})")
            # Notificar actividad — el usuario nos toca
            if hasattr(self, '_vida'):
                self._vida.notificar_actividad()
                self._vida._pos_objetivo = None  # Cancelar movimiento autónomo
        elif event.button() == Qt.MouseButton.RightButton:
            self._mostrar_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self._arrastrando:
            new_pos = event.globalPosition().toPoint() - self._offset
            self.move(self._limitar_posicion_pantalla(new_pos.x(), new_pos.y()))
            # FP-049: NO sincronizar _pos_anterior aquí — el timer en _animar
            # es el único que debe leer/actualizar _pos_anterior para que las
            # partículas reciban delta real de movimiento (inercia).
            # Registrar posición para calcular velocidad real al soltar
            gp = event.globalPosition().toPoint()
            now = time.time()
            self._drag_historial.append((gp.x(), gp.y(), now))
            # Mantener solo últimos 100ms de historial
            self._drag_historial = [(x, y, t) for x, y, t in self._drag_historial if now - t < 0.12]
        else:
            # Hover — verificar si está sobre el núcleo
            dx = event.pos().x() - TAMANO_ORBE / 2
            dy = event.pos().y() - TAMANO_ORBE / 2
            dist = math.sqrt(dx * dx + dy * dy)
            self._hover = dist < RADIO_NUCLEO * 1.5
            # WI-166: No force scale change on hover — only visual feedback via _hover flag

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._arrastrando:
                # FP-013: Empujón — calcular velocidad REAL al soltar
                # Usa historial de posiciones recientes, no desplazamiento total
                pos_fin = event.globalPosition().toPoint()
                now = time.time()
                self._drag_historial.append((pos_fin.x(), pos_fin.y(), now))
                # RF-134: Ventana adaptativa 50ms → 80ms → 120ms (cascade)
                hist = [(x, y, t) for x, y, t in self._drag_historial if now - t < 0.05]
                if len(hist) < 2:
                    hist = [(x, y, t) for x, y, t in self._drag_historial if now - t < 0.08]
                if len(hist) < 2:
                    hist = [(x, y, t) for x, y, t in self._drag_historial if now - t < 0.12]
                if len(hist) >= 2:
                    x0, y0, t0 = hist[0]
                    x1, y1, t1 = hist[-1]
                    dt = t1 - t0
                    if dt > 0.01:  # evitar división por ~0
                        # Velocidad en px/s
                        vel_x = (x1 - x0) / dt
                        vel_y = (y1 - y0) / dt
                        velocidad = math.hypot(vel_x, vel_y)
                        # Umbral: 150 px/s mínimo para activar empujón
                        if velocidad > 150:
                            # Factor proporcional a velocidad, máximo 30 px/frame
                            factor = min(velocidad / 60, 30)
                            ang = math.atan2(vel_y, vel_x)
                            self._impulso_vx = factor * math.cos(ang)
                            self._impulso_vy = factor * math.sin(ang)
                            logger.debug(f"Yad: empujón v={velocidad:.0f}px/s → impulso ({self._impulso_vx:.1f}, {self._impulso_vy:.1f})")
                self._drag_historial.clear()
            self._arrastrando = False
            logger.debug(f"HF-028 drag-end: pos=({self.x()},{self.y()}) tam={self.width()}")

    def enterEvent(self, event):
        # WI-166: No auto-grow on enter — prevents unwanted window expansion
        pass

    def leaveEvent(self, event):
        self._hover = False
        # WI-166: Don't force scale — let state-based logic control it

    def wheelEvent(self, event):
        """Scroll para cambiar tamaño permanente (no solo hover)."""
        delta = event.angleDelta().y()
        if delta > 0:
            new_size = min(500, self.width() + 20)
        else:
            new_size = max(240, self.width() - 20)

        if new_size != self.width():
            self._redimensionar(new_size)

    def _redimensionar(self, nuevo_tamano: int):
        """Cambia el tamaño del orbe (sin máscara — WA_TranslucentBackground basta)."""
        global TAMANO_ORBE
        TAMANO_ORBE = nuevo_tamano
        self._tamano_ventana = float(nuevo_tamano)
        self.resize(nuevo_tamano, nuevo_tamano)
        self.clearMask()
        # RF-308: Resize puede provocar que DWM restaure la sombra
        self._aplicar_dwm_nosombra()

    def _reasegurar_transparencia(self):
        """HF-031 + RF-146: Re-asegura transparencia + DWM tras hide→show."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self.clearMask()
        # RF-146: Re-aplicar fixes Win32/DWM (WS_POPUP, SWP_FRAMECHANGED, etc.)
        # ShowWindow puede resetear el frame style de la ventana
        self._eliminar_sombra_dwm()

    def _mostrar_menu(self, posicion: QPoint):
        """FIX #3: Menú contextual con lazy-build + caché — reutilizar en cada clic sin reconstruir.
        Primero llama a _construir_menu_contextual() que valida estado y cachea.
        """
        # FIX #3: Lazy-build — solo construir si no existe o si estado cambió
        _state_hash = hash((
            hasattr(self, '_timer_guardian') and self._timer_guardian.isActive(),
            self._estado,
            self._cerebro_nivel,
        ))
        
        if self._menu_contextual is None or self._state_hash != _state_hash:
            self._construir_menu_contextual()
            self._state_hash = _state_hash
        
        # Mostrar menú cachado (INSTANTÁNEO, sin construcción)
        self._menu_contextual.exec(posicion)

    # FIX #3: Métodos de acciones sin lambdas (más rápidos, evitan captura de closure)
    def _accion_enrolar_voz(self):
        self._trigger_owner_enroll()

    def _accion_demo_introduccion(self):
        self._demo_introduccion()

    def _accion_demo_animaciones(self):
        self._demo_animaciones()

    def _accion_demo_herramientas(self):
        self._demo_herramientas()

    def _accion_gilgul(self):
        self._ejecutar_gilgul()

    def _accion_activar_guardian(self):
        self._activar_guardian_manual()

    def _accion_desactivar_guardian(self):
        self._desactivar_guardian_manual()

    def _accion_keter(self):
        self._abrir_ventana_keter()

    def _accion_vpn_on(self):
        self._iniciar_pensamiento("activa la vpn")

    def _accion_vpn_off(self):
        self._iniciar_pensamiento("desactiva la vpn")

    def _accion_vault(self):
        self._iniciar_pensamiento("lista mis contraseñas")

    def _accion_genpass(self):
        self._iniciar_pensamiento("genera una contraseña segura")

    def _accion_sec_status(self):
        self._iniciar_pensamiento("estado de seguridad")

    def _accion_heatmap(self):
        self._mostrar_heatmap_dev()

    def _accion_estado_interno(self):
        self._mostrar_estado_dev()

    def _accion_admin_tareas(self):
        self._mostrar_admin_tareas()

    def _accion_camara(self):
        self._mostrar_camara_dev()

    def _accion_config_visual(self):
        self._mostrar_configuracion_visual()

    def _accion_feature_flags(self):
        self._mostrar_feature_flags_dev()

    def _construir_menu_contextual(self):
        """FIX #3: Construye el menú contextual UNA SOLA VEZ y lo cachea.
        Llamado solo cuando el estado cambia (guardian activo, nivel cerebro, etc).
        """
        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background: #0a0a0f; color: #c8a030; border: 1px solid #2a2a30; "
            "font-family: 'Segoe UI'; font-size: 11px; }"
            "QMenu::item:selected { background: #1a1a25; }"
        )

        # 1. Enrolamiento de voz
        accion_enrolar = QAction("🎙️ Enrolar mi voz", self)
        accion_enrolar.triggered.connect(self._accion_enrolar_voz)
        menu.addAction(accion_enrolar)

        # WI-279: Demo 0 — Introducción completa
        accion_demo0 = QAction("✨ Demo: Introducción completa", self)
        accion_demo0.triggered.connect(self._accion_demo_introduccion)
        menu.addAction(accion_demo0)

        # 2. Demo visual (animaciones/estados)
        accion_demo = QAction("🔮 Demo: Animaciones", self)
        accion_demo.triggered.connect(self._accion_demo_animaciones)
        menu.addAction(accion_demo)

        # 3. Demo de herramientas (permisos)
        accion_demo2 = QAction("🛠️ Demo: Herramientas", self)
        accion_demo2.triggered.connect(self._accion_demo_herramientas)
        menu.addAction(accion_demo2)

        # 4. Reinicio total de identidad (reset de memoria/personalidad)
        accion_gilgul = QAction("♻️ Reiniciar identidad", self)
        accion_gilgul.triggered.connect(self._accion_gilgul)
        menu.addAction(accion_gilgul)

        # 5. Guardián — Toggle estado-aware
        guardian_activo = hasattr(self, '_timer_guardian') and self._timer_guardian.isActive()
        if guardian_activo:
            accion_guardian = QAction("🛡️ Desactivar Guardián", self)
            accion_guardian.triggered.connect(self._accion_desactivar_guardian)
        else:
            accion_guardian = QAction("🛡️ Activar Guardián", self)
            accion_guardian.triggered.connect(self._accion_activar_guardian)
        menu.addAction(accion_guardian)

        menu.addSeparator()

        # Ventana de introspección
        accion_keter = QAction("🧠 Introspección", self)
        accion_keter.triggered.connect(self._accion_keter)
        menu.addAction(accion_keter)

        menu.addSeparator()

        # WI-167: Submenú de seguridad
        menu_seguridad = QMenu("🔒 Seguridad", menu)
        menu_seguridad.setStyleSheet(menu.styleSheet())
        
        accion_vpn_on = QAction("🌐 Activar VPN", self)
        accion_vpn_on.triggered.connect(self._accion_vpn_on)
        menu_seguridad.addAction(accion_vpn_on)
        
        accion_vpn_off = QAction("🌐 Desactivar VPN", self)
        accion_vpn_off.triggered.connect(self._accion_vpn_off)
        menu_seguridad.addAction(accion_vpn_off)
        
        menu_seguridad.addSeparator()
        
        accion_vault = QAction("🔑 Bóveda de contraseñas", self)
        accion_vault.triggered.connect(self._accion_vault)
        menu_seguridad.addAction(accion_vault)

        accion_genpass = QAction("🔑 Generar contraseña", self)
        accion_genpass.triggered.connect(self._accion_genpass)
        menu_seguridad.addAction(accion_genpass)

        menu_seguridad.addSeparator()

        accion_sec_status = QAction("🛡️ Estado de seguridad", self)
        accion_sec_status.triggered.connect(self._accion_sec_status)
        menu_seguridad.addAction(accion_sec_status)
        
        menu_seguridad.addSeparator()
        
        accion_presentar = QAction("👤 Presentar persona de confianza", self)
        accion_presentar.triggered.connect(self._presentar_persona_confianza)
        menu_seguridad.addAction(accion_presentar)
        
        accion_reenroll = QAction("🔄 Re-enrollar mi rostro", self)
        accion_reenroll.triggered.connect(self._forzar_reenroll_rostro_propietario)
        menu_seguridad.addAction(accion_reenroll)
        
        menu.addMenu(menu_seguridad)

        # FP-065 RF-172: Submenú de herramientas de desarrollo
        menu_dev = QMenu("🛠️ Herramientas de desarrollo", menu)
        menu_dev.setStyleSheet(menu.styleSheet())
        
        accion_heatmap = QAction("🗺 Heatmap de pantalla", self)
        accion_heatmap.triggered.connect(self._accion_heatmap)
        menu_dev.addAction(accion_heatmap)
        
        accion_estado = QAction("📊 Estado interno", self)
        accion_estado.triggered.connect(self._accion_estado_interno)
        menu_dev.addAction(accion_estado)
        
        accion_tareas = QAction("⚙ Administrador de tareas", self)
        accion_tareas.triggered.connect(self._accion_admin_tareas)
        menu_dev.addAction(accion_tareas)
        
        accion_camara = QAction("📷 Cámara — Ojos de Computadora", self)
        accion_camara.triggered.connect(self._accion_camara)
        menu_dev.addAction(accion_camara)
        
        menu_dev.addSeparator()
        
        # RUBEDO: Toggle para mostrar/ocultar FPS en UI
        fps_label = "📊 FPS Display: DESACTIVADO" if not self._mostrar_fps else "📊 FPS Display: ACTIVADO"
        accion_fps = QAction(fps_label, self)
        accion_fps.triggered.connect(self._accion_toggle_fps_display)
        menu_dev.addAction(accion_fps)
        
        accion_maljut_config = QAction("⚡ Configuración visual (GPU/FPS/Tema)", self)
        accion_maljut_config.triggered.connect(self._accion_config_visual)
        menu_dev.addAction(accion_maljut_config)
        
        accion_feature_flags = QAction("🚩 Feature Flags — Activar/Desactivar Subsistemas", self)
        accion_feature_flags.triggered.connect(self._accion_feature_flags)
        menu_dev.addAction(accion_feature_flags)
        
        menu.addMenu(menu_dev)

        menu.addSeparator()
        accion_cerrar = QAction("🛑 Cerrar Computadora", self)
        accion_cerrar.triggered.connect(self.forzar_cierre)
        menu.addAction(accion_cerrar)

        # CACHEAR el menú construido
        self._menu_contextual = menu


    def _abrir_ventana_keter(self):
        """Abre (o muestra) la ventana de introspección."""
        if self._ventana_keter.isVisible():
            self._ventana_keter.raise_()
            self._ventana_keter.activateWindow()
        else:
            self._ventana_keter.show()
            self._ventana_keter.raise_()

    def _ejecutar_gilgul(self):
        """Reinicio total de identidad. Borra personalidad, memoria y datos aprendidos."""
        # Primera confirmación
        resp1 = QMessageBox.warning(
            self, "Reiniciar identidad",
            "Esto borrará TODA la personalidad, memoria, evolución y datos aprendidos de la Computadora.\n"
            "El Computadora renacerá como si fuera la primera vez.\n\n"
            "¿Deseas continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if resp1 != QMessageBox.StandardButton.Yes:
            return

        # Segunda confirmación (doble gate)
        resp2 = QMessageBox.critical(
            self, "⚠ Confirmación final — Reiniciar identidad",
            "ÚLTIMA ADVERTENCIA: Esta acción es IRREVERSIBLE.\n"
            "Se perderán todos los recuerdos, personalidad y evolución.\n\n"
            "¿Confirmas el reinicio de identidad?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if resp2 != QMessageBox.StandardButton.Yes:
            return

        # Iniciar reinicio sin solicitar contraseña (contraseña fue removida — legacy)
        datos_dir = Path(__file__).resolve().parent.parent.parent / "datos"

        logger.info("Reinicio de identidad: iniciando sin validación de contraseña...")

        archivos_a_borrar = [
            "personalidad.json", "computadora_personas.json", "owner_profile.json",
            "consciencia_temporal.json", "evolucion_computadora.json", "errores_aprendidos.json",
            "heatmap_pantalla.json", "nivel1_patrones.json", "perfil_amo.json",
            "tareas.json", "tareas_diferidas.json", "recordatorios.json",
            "permisos_log.jsonl",
        ]
        borrados = 0
        for nombre in archivos_a_borrar:
            p = datos_dir / nombre
            if p.exists():
                try:
                    p.unlink()
                    borrados += 1
                except Exception as e:
                    logger.error(f"Reinicio de identidad: no pude borrar {nombre}: {e}")

        # Borrar directorio de memoria completo
        memoria_dir = datos_dir / "memoria"
        if memoria_dir.exists():
            import shutil
            try:
                shutil.rmtree(memoria_dir)
                borrados += 1
            except Exception as e:
                logger.error(f"Reinicio de identidad: no pude borrar memoria/: {e}")

        logger.info(f"Reinicio de identidad completado: {borrados} elementos borrados. Reiniciando...")
        self.hilo_habla.hablar("Reinicio completado. Renazco ahora, señor.")

        # WI-275: Escribir trigger de Génesis para el próximo boot
        try:
            from computadora.nucleo.bereshit import BereshitGenesis
            BereshitGenesis.escribir_trigger_gilgul()
        except Exception as e:
            logger.warning(f"No se pudo escribir trigger Génesis: {e}")

        # Reiniciar la aplicación
        import sys
        import os
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _trigger_owner_enroll(self):
        try:
            # Marcar que la próxima muestra será usada para enrolamiento
            self.hilo_escucha._force_enroll = True
            self.hilo_habla.hablar("Prepara una frase breve. Registraré la siguiente muestra de voz.")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("No pude activar enrolamiento manual")

    # RUBEDO: Toggle para FPS display
    def _accion_toggle_fps_display(self):
        """Alterna la visualización de FPS en la UI (DevTools)."""
        self._mostrar_fps = not self._mostrar_fps
        estado = "ACTIVADO" if self._mostrar_fps else "DESACTIVADO"
        logger.info(f"📊 FPS Display: {estado}")
        self.hilo_habla.hablar(f"Mostrador de fotogramas {estado}" if self._mostrar_fps else "Mostrador de fotogramas desactivado")

    def obtener_fps_actual(self) -> float:
        """Retorna el FPS actual (para devtools o debugging)."""
        return self._fps_actual

    # ── FP-065 RF-172: כלי מפתח — Dev Tools ──

    def _mostrar_heatmap_dev(self):
        """FP-065: Diálogo con heatmap visual 8×6 de zonas de pantalla."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Heatmap de pantalla")
        dlg.setFixedSize(420, 340)
        dlg.setStyleSheet("background: #0a0a0f; color: #c8a030;")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Heatmap de actividad (8×6)"))

        grid = QGridLayout()
        grid.setSpacing(2)
        heatmap = getattr(self._vida, '_heatmap', [[0.0]*8 for _ in range(6)])
        max_val = max((max(row) for row in heatmap), default=1.0) or 1.0
        for r, row in enumerate(heatmap):
            for c, val in enumerate(row):
                intensity = int(255 * val / max_val)
                lbl = QLabel(f"{val:.1f}")
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFixedSize(45, 40)
                lbl.setStyleSheet(
                    f"background: rgb({intensity}, {intensity // 3}, 0); "
                    f"color: {'#fff' if intensity < 150 else '#000'}; "
                    f"font-size: 9px; border: 1px solid #2a2a30;"
                )
                grid.addWidget(lbl, r, c)
        layout.addLayout(grid)
        dlg.show()

    def _mostrar_estado_dev(self):
        """FP-065 + RF-199/RF-200 + RF-312/RF-313/RF-314: Stats panel videogame HUD."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Estado interno")
        dlg.setFixedSize(560, 620)
        dlg.setStyleSheet(
            "QDialog { background: #0a0a0f; color: #c8a030; font-family: 'Consolas'; }"
            "QLabel { font-size: 11px; padding: 1px 2px; }"
            "QScrollArea { border: none; }"
            "QProgressBar { background: #1a1a25; border: 1px solid #2a2a30; "
            "border-radius: 3px; height: 14px; text-align: center; "
            "font-size: 9px; color: #e0e0e0; }"
        )
        layout = QVBoxLayout(dlg)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        main_vbox = QVBoxLayout(contenido)
        main_vbox.setSpacing(6)

        # RF-312: Widgets por sección — grid 2 columnas
        widgets = {}  # key → widget (QLabel, QProgressBar, or QFrame)

        def _seccion(titulo: str):
            lbl = QLabel(f"<b style='color:#e8c040;font-size:12px;'>▸ {titulo}</b>")
            main_vbox.addWidget(lbl)
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #2a2a30;")
            main_vbox.addWidget(sep)

        def _fila_texto(key: str, grid: QGridLayout, row: int):
            lk = QLabel(f"<span style='color:#888;'>{key}</span>")
            lv = QLabel("—")
            lv.setWordWrap(True)
            grid.addWidget(lk, row, 0)
            grid.addWidget(lv, row, 1)
            widgets[key] = lv

        def _fila_barra(key: str, grid: QGridLayout, row: int, color: str):
            lk = QLabel(f"<span style='color:#888;'>{key}</span>")
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setValue(0)
            bar.setStyleSheet(
                bar.styleSheet() +
                f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
            grid.addWidget(lk, row, 0)
            grid.addWidget(bar, row, 1)
            widgets[key] = bar

        def _fila_color(key: str, grid: QGridLayout, row: int):
            lk = QLabel(f"<span style='color:#888;'>{key}</span>")
            hbox = QHBoxLayout()
            swatch = QFrame()
            swatch.setFixedSize(20, 14)
            swatch.setStyleSheet("background: #000; border: 1px solid #444; border-radius: 2px;")
            lv = QLabel("#000000")
            lv.setFixedWidth(70)
            hbox.addWidget(swatch)
            hbox.addWidget(lv)
            hbox.addStretch()
            container = QWidget()
            container.setLayout(hbox)
            grid.addWidget(lk, row, 0)
            grid.addWidget(container, row, 1)
            widgets[key] = (swatch, lv)

        # ── Sección 1: Estado ──
        _seccion("ESTADO")
        g1 = QGridLayout()
        g1.setColumnStretch(1, 1)
        _fila_texto("FSM", g1, 0)
        _fila_texto("Etapa", g1, 1)
        _fila_texto("Cerebro", g1, 2)
        _fila_texto("Humor", g1, 3)
        _fila_texto("Trabajo", g1, 4)
        _fila_texto("Gevurá", g1, 5)
        _fila_texto("Demo", g1, 6)
        _fila_texto("Circadiano", g1, 7)
        w1 = QWidget()
        w1.setLayout(g1)
        main_vbox.addWidget(w1)

        # ── Sección 2: Alquimia ──
        _seccion("ALQUIMIA — Progreso")
        g2 = QGridLayout()
        g2.setColumnStretch(1, 1)
        _fila_barra("Horas", g2, 0, "#c8a030")
        _fila_barra("Interacciones", g2, 1, "#30a8c8")
        _fila_barra("General", g2, 2, "#a040c8")
        _fila_texto("Siguiente etapa", g2, 3)
        w2 = QWidget()
        w2.setLayout(g2)
        main_vbox.addWidget(w2)

        # ── Sección 3: Visual ──  RF-314
        _seccion("VISUAL — Colores")
        g3 = QGridLayout()
        g3.setColumnStretch(1, 1)
        _fila_color("Primario", g3, 0)
        _fila_color("Secundario", g3, 1)
        _fila_color("Target Pri", g3, 2)
        _fila_color("Target Sec", g3, 3)
        _fila_barra("Escala", g3, 4, "#40c870")
        _fila_barra("Lerp", g3, 5, "#c87040")
        w3 = QWidget()
        w3.setLayout(g3)
        main_vbox.addWidget(w3)

        # ── Sección 4: Sistema ──
        _seccion("SISTEMA — Rasgos")
        g4 = QGridLayout()
        g4.setColumnStretch(1, 1)
        _fila_texto("Rasgos", g4, 0)
        _fila_texto("Zona tacto", g4, 1)
        _fila_texto("Último evento", g4, 2)
        w4 = QWidget()
        w4.setLayout(g4)
        main_vbox.addWidget(w4)

        # Stats dinámicos
        _seccion("STATS")
        stats_container = QWidget()
        stats_layout = QGridLayout(stats_container)
        stats_layout.setColumnStretch(1, 1)
        main_vbox.addWidget(stats_container)

        main_vbox.addStretch()
        scroll.setWidget(contenido)
        layout.addWidget(scroll)

        _nombres_heb = {
            "nigredo": "NIGREDO",
            "albedo": "ALBEDO",
            "citrinitas": "CITRINITAS",
            "rubedo": "RUBEDO",
        }

        def _refrescar():
            """RF-200 + RF-312/313/314: Actualizar HUD videogame en vivo."""
            try:
                humor = self.personalidad.humor_actual if hasattr(self, 'personalidad') else "?"
                rasgos = ""
                if hasattr(self, 'personalidad') and hasattr(self.personalidad, '_rasgos'):
                    rasgos = ", ".join(f"{k}={v:.2f}" for k, v in self.personalidad._rasgos.items())

                etapa_val = self._etapa_alquimica.value
                etapa_txt = _nombres_heb.get(etapa_val, etapa_val.upper())

                # ── Sección 1: Texto ──
                circadiano_txt = "?"
                evento_txt = "—"
                if hasattr(self, '_ciclo_circadiano'):
                    cc = self._ciclo_circadiano
                    circadiano_txt = getattr(cc, '_fase', "?")
                    evento_txt = f"{getattr(cc, '_ultimo_evento', 0):.0f}"

                textos = {
                    "FSM": self._estado,
                    "Etapa": etapa_txt,
                    "Cerebro": str(self._cerebro_nivel or "—"),
                    "Humor": humor,
                    "Trabajo": f"{self._trabajo_categoria or '—'} / {getattr(self, '_trabajo_tool', '—')}",
                    "Gevurá": getattr(self, '_gevura_categoria', "—"),
                    "Demo": "SÍ ⚡" if getattr(self, '_demo_en_curso', False) else "no",
                    "Circadiano": f"{circadiano_txt} (ev: {evento_txt})",
                    "Rasgos": rasgos or "—",
                    "Zona tacto": str(getattr(self, '_zona_tacto', 0)),
                    "Último evento": evento_txt,
                    "Siguiente etapa": "",
                }
                for key, val in textos.items():
                    w = widgets.get(key)
                    if isinstance(w, QLabel):
                        w.setText(str(val))

                # ── Sección 2: Barras de alquimia ── RF-313
                if self._etapa_alquimica == EtapaAlquimica.RUBEDO:
                    for bk in ("Horas", "Interacciones", "General"):
                        bar = widgets.get(bk)
                        if isinstance(bar, QProgressBar):
                            bar.setValue(1000)
                            bar.setFormat("✦ Opus Magnum")
                    widgets["Siguiente etapa"].setText("✦ Opus Magnum alcanzado")
                else:
                    try:
                        from computadora.memoria.memoria import calcular_tiempo_activo
                        horas = calcular_tiempo_activo().get("horas", 0)
                    except Exception as e:  # RF-199
                        logger.debug("Error calculando tiempo activo: %s", e)
                        horas = 0
                    inter = self._evolucion_data.get("interacciones_totales", 0)
                    idx = _ETAPAS_ORDEN.index(self._etapa_alquimica)
                    siguiente = _ETAPAS_ORDEN[idx + 1]
                    umbral = _UMBRALES_EVOLUCION.get(siguiente, {})
                    uh = umbral.get("horas", 1)
                    ui = umbral.get("interacciones", 1)
                    pct_h = min(horas / uh, 1.0)
                    pct_i = min(inter / ui, 1.0)
                    pct_gen = min(pct_h, pct_i)

                    bar_h = widgets.get("Horas")
                    if isinstance(bar_h, QProgressBar):
                        bar_h.setValue(int(pct_h * 1000))
                        bar_h.setFormat(f"{horas:.1f}/{uh}h ({pct_h*100:.0f}%)")
                    bar_i = widgets.get("Interacciones")
                    if isinstance(bar_i, QProgressBar):
                        bar_i.setValue(int(pct_i * 1000))
                        bar_i.setFormat(f"{inter}/{ui} ({pct_i*100:.0f}%)")
                    bar_g = widgets.get("General")
                    if isinstance(bar_g, QProgressBar):
                        bar_g.setValue(int(pct_gen * 1000))
                        bar_g.setFormat(f"{pct_gen*100:.0f}%")
                    sig_txt = _nombres_heb.get(siguiente.value, siguiente.value)
                    widgets["Siguiente etapa"].setText(f"→ {sig_txt}")

                # ── Sección 3: Colores + escala ── RF-314
                colores = {
                    "Primario": self._color_alq_primario,
                    "Secundario": self._color_alq_secundario,
                    "Target Pri": self._color_alq_target_pri,
                    "Target Sec": self._color_alq_target_sec,
                }
                for key, qc in colores.items():
                    pair = widgets.get(key)
                    if isinstance(pair, tuple):
                        swatch, lbl = pair
                        swatch.setStyleSheet(
                            f"background: {qc.name()}; border: 1px solid #444; border-radius: 2px;")
                        lbl.setText(qc.name())

                escala_bar = widgets.get("Escala")
                if isinstance(escala_bar, QProgressBar):
                    esc = getattr(self, '_escala_actual', getattr(self, '_escala', 1.0))
                    escala_bar.setValue(int(min(esc, 1.5) / 1.5 * 1000))
                    escala_bar.setFormat(f"{esc:.2f}")

                lerp_bar = widgets.get("Lerp")
                if isinstance(lerp_bar, QProgressBar):
                    lp = getattr(self, '_alq_lerp_progress', 0.0)
                    lerp_bar.setValue(int(lp * 1000))
                    lerp_bar.setFormat(f"{lp:.3f}")

                # ── Stats dinámicos ──
                # Limpiar y recrear
                while stats_layout.count():
                    item = stats_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                if hasattr(self, '_stats'):
                    row = 0
                    for k, v in self._stats.items():
                        lk = QLabel(f"<span style='color:#888;'>{k}</span>")
                        lv = QLabel(str(v))
                        stats_layout.addWidget(lk, row, 0)
                        stats_layout.addWidget(lv, row, 1)
                        row += 1
            except Exception as e:
                logger.debug("Error refrescando DevTools estado: %s", e)

        # RF-200: Timer de refresco — vive mientras el diálogo esté abierto
        timer_refresh = QTimer(dlg)
        timer_refresh.timeout.connect(_refrescar)
        timer_refresh.start(500)
        _refrescar()  # primer pintado inmediato

        dlg.show()

    # ── FP-109 RF-369: 📷 Cámara — Ojos de Computadora ──

    def _mostrar_camara_dev(self):
        """FP-113 WI-153: Abre la herramienta moderna de Dev Tools para la cámara.
        Si falla la herramienta moderna, recae al modo legacy para compatibilidad."""
        try:
            from computadora.interfaz.camera_dev_tool import abrir_camera_dev_tool
            abrir_camera_dev_tool(ventana_principal=self)
            return
        except Exception as e:
            logger.error(f"Error abriendo CameraDevTool moderno: {e}")
            logger.debug("Fallback legacy al visor de cámara antiguo", exc_info=True)

        try:
            import cv2
        except ImportError:
            dlg = QDialog(self)
            dlg.setWindowTitle("📷 Cámara — No disponible")
            dlg.setFixedSize(300, 100)
            dlg.setStyleSheet("background: #0a0a0f; color: #c8a030;")
            layout = QVBoxLayout(dlg)
            layout.addWidget(QLabel("opencv-python no instalado"))
            dlg.show()
            return

        # Obtener o crear KliCamara compartida via GestorKelim
        from computadora.nucleo.kli import GestorKelim
        from computadora.habilidades.vision import KliCamara
        gestor = GestorKelim.instancia()
        if "camara_local" not in {k["id"] for k in gestor.listar()}:
            cam = KliCamara()
            gestor.registrar(cam)
        if not any(k["id"] == "camara_local" and k["estado"] == "CONECTADO"
                   for k in gestor.listar()):
            if not gestor.conectar("camara_local"):
                dlg = QDialog(self)
                dlg.setWindowTitle("📷 Cámara — Sin dispositivo")
                dlg.setFixedSize(300, 100)
                dlg.setStyleSheet("background: #0a0a0f; color: #c8a030;")
                layout = QVBoxLayout(dlg)
                layout.addWidget(QLabel("No se detectó cámara conectada"))
                dlg.show()
                return

        # Obtener reconocedor facial desde orquestador (fix: era _orquestador, correcto: orquestador)
        reconocedor = None
        orq = getattr(self, 'orquestador', None)
        if orq:
            perceptor = getattr(orq, 'perceptor', None)
            if perceptor:
                reconocedor = getattr(perceptor, '_reconocedor_rostro', None)

        # Crear diálogo de video en vivo
        dlg = QDialog(self)
        dlg.setWindowTitle("📷 Cámara de Computadora [EN VIVO]")
        dlg.setStyleSheet(
            "QDialog { background: #0a0a0f; color: #c8a030; font-family: 'Consolas'; }"
            "QLabel { font-size: 11px; }"
        )
        layout = QVBoxLayout(dlg)

        img_label = QLabel("Iniciando cámara...")
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setMinimumSize(640, 480)
        layout.addWidget(img_label)

        info_label = QLabel("Resultado: —")
        info_label.setStyleSheet("color: #40e040; font-size: 12px; padding: 4px;")
        layout.addWidget(info_label)

        res_label = QLabel("")
        res_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(res_label)

        # Estado compartido para el timer de refresco
        from PyQt6.QtGui import QImage, QPixmap
        _dev_cam_state = {"ultimo_rostro": {"resultado": "—"}, "frame_count": 0, "error_count": 0}

        def _capturar_frame():
            try:
                # Leer frame desde KliCamara compartida
                kli_list = gestor.listar()
                cam_info = next((k for k in kli_list if k["id"] == "camara_local"), None)
                if not cam_info or cam_info["estado"] != "CONECTADO":
                    info_label.setText("Cámara desconectada")
                    return
                # Acceder al dispositivo directamente para obtener frame BGR
                dispositivo = gestor._kelim.get("camara_local")
                if not dispositivo or dispositivo._cap is None:
                    return
                ret, frame_bgr = dispositivo._cap.read()
                if not ret or frame_bgr is None:
                    return

                _dev_cam_state["frame_count"] += 1

                # Face recognition cada 5 frames (~500ms) para no saturar CPU
                resultado_rostro = _dev_cam_state["ultimo_rostro"]
                if reconocedor and _dev_cam_state["frame_count"] % 5 == 0:
                    reconocedor._ultimo_check = 0.0
                    resultado_rostro = reconocedor.analizar_frame(frame_bgr.copy())  # WI-164
                    if resultado_rostro.get("resultado") != "cooldown":
                        _dev_cam_state["ultimo_rostro"] = resultado_rostro

                # Dibujar rectángulos con locations del resultado de analizar_frame
                face_locs = resultado_rostro.get("locations", _dev_cam_state.get("face_locs", []))
                if face_locs:
                    _dev_cam_state["face_locs"] = face_locs
                for (top, right, bottom, left) in _dev_cam_state.get("face_locs", []):
                        color = (0, 255, 0) if resultado_rostro.get("resultado") == "propietario" else (0, 165, 255)
                        cv2.rectangle(frame_bgr, (left, top), (right, bottom), color, 2)
                        label = resultado_rostro.get("resultado", "?")
                        if label == "propietario":
                            label = "PROPIETARIO ✓"
                        elif label == "conocido":
                            label = resultado_rostro.get("nombre", "conocido")
                        cv2.putText(frame_bgr, label, (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Convertir a QPixmap
                h, w, ch = frame_bgr.shape
                rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg.copy())  # .copy() para evitar dangling pointer
                max_w, max_h = 640, 480
                if pixmap.width() > max_w or pixmap.height() > max_h:
                    pixmap = pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio)
                img_label.setPixmap(pixmap)

                # Actualizar info
                r = resultado_rostro
                info_text = f"Resultado: {r.get('resultado', '—')}"
                if 'distancia' in r:
                    info_text += f"  |  Distancia: {r['distancia']:.3f}"
                if r.get("nombre"):
                    info_text += f"  |  Nombre: {r['nombre']}"
                info_label.setText(info_text)
                fr_ok = r.get("resultado") != "no_disponible"
                res_label.setText(f"Resolución: {w}×{h}  |  face_recognition: {'✓' if fr_ok else '✗'}  |  Frame #{_dev_cam_state['frame_count']}")
            except Exception as e:
                _dev_cam_state["error_count"] += 1
                if _dev_cam_state["error_count"] <= 3 or _dev_cam_state["error_count"] % 50 == 0:
                    logger.debug("Error en frame dev cam (#%d): %s", _dev_cam_state["error_count"], e)

        timer_cam = QTimer(dlg)
        timer_cam.timeout.connect(_capturar_frame)
        timer_cam.start(500)  # 2 FPS con debounce agresivo (era 100ms/10FPS = overhead)
        _capturar_frame()  # primer frame inmediato

        dlg.show()

    def _mostrar_feature_flags_dev(self):
        """🚩 Panel de Feature Flags — Activar/Desactivar subsistemas en tiempo real."""
        from computadora.nucleo.feature_flags import FeatureFlags
        
        dlg = QDialog(self)
        dlg.setWindowTitle("🚩 Feature Flags — Control de Subsistemas")
        dlg.setFixedSize(500, 550)
        dlg.setStyleSheet(
            "QDialog { background: #0a0a0f; color: #c8a030; font-family: 'Consolas'; }"
            "QCheckBox { font-size: 11px; padding: 3px; }"
            "QCheckBox::indicator { width: 18px; height: 18px; }"
            "QCheckBox:hover { color: #e8c040; }"
            "QGroupBox { color: #c8a030; border: 1px solid #2a2a30; border-radius: 4px; "
            "padding-top: 10px; padding-left: 5px; margin-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }"
            "QLabel { font-size: 10px; color: #888; }"
            "QPushButton { background: #1a1a25; color: #c8a030; border: 1px solid #2a2a30; "
            "border-radius: 4px; padding: 5px 10px; font-size: 10px; }"
            "QPushButton:hover { background: #2a2a35; color: #e8c040; }"
        )
        
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        main_vbox = QVBoxLayout(contenido)
        main_vbox.setSpacing(8)
        
        # Título descriptivo
        titulo = QLabel("<b style='font-size:12px;color:#e8c040;'>Subsistemas Activos/Pausados</b>")
        main_vbox.addWidget(titulo)
        
        # Mapeo de flags con descripción
        flags_info = {
            "escucha_voz": ("🎤 Escucha por voz (RF-01)", "Whisper STT + Wake Word Detection"),
            "nlu_herramientas": ("🧠 NLU + Herramientas (RF-02/09)", "Comprensión y ejecución de comandos"),
            "tts": ("🔊 Text-to-Speech (RF-03)", "Respuestas audibles por altavoz"),
            "nivel2_ollama": ("🤖 Nivel 2 Ollama (RF-06)", "LLM local para pensamiento profundo"),
            "proactividad": ("💡 Proactividad (RF-13)", "Sugerencias automáticas y alertas"),
            "monitor_sistema": ("📊 Monitor de Sistema (RF-42)", "Vigilancia de recursos CPU/RAM"),
            "emociones_ruaj": ("😊 Sistema Emocional (RF-36)", "13 humores vs 5 básicos"),
            "contexto_visual": ("👁️ Contexto Visual (RF-12)", "Screen awareness para comandos contextuales"),
            "reconocimiento_facial": ("👤 Reconocimiento Facial (RF-49)", "Identificación de personas"),
            "life_autonomy": ("🌍 Life Autonomy (RF-22)", "Auto-relocalización y Heatmap"),
            "circadian_cycles": ("🌙 Ciclos Circadianos (RF-15)", "Adaptación a horarios del usuario"),
        }
        
        checkboxes = {}
        flags = FeatureFlags.obtener_todas()
        
        for flag_name, (label, desc) in flags_info.items():
            gb = QGroupBox(label)
            gb_layout = QVBoxLayout()
            
            cb = QCheckBox("Activo")
            cb.setChecked(flags.get(flag_name, False))
            cb.toggled.connect(lambda checked, fn=flag_name: self._toggle_feature_flag(fn, checked))
            checkboxes[flag_name] = cb
            
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #666; font-size: 9px;")
            
            gb_layout.addWidget(cb)
            gb_layout.addWidget(desc_lbl)
            gb.setLayout(gb_layout)
            main_vbox.addWidget(gb)
        
        main_vbox.addStretch()
        
        # Botones de acción
        hbox_botones = QHBoxLayout()
        btn_reset = QPushButton("🔄 Restaurar Defaults")
        btn_reset.clicked.connect(lambda: self._reset_feature_flags_defaults(checkboxes))
        btn_minimales = QPushButton("📱 Modo Mínimo (Solo Voz+Maljut)")
        btn_minimales.clicked.connect(lambda: self._set_minimal_feature_flags(checkboxes))
        hbox_botones.addWidget(btn_reset)
        hbox_botones.addWidget(btn_minimales)
        main_vbox.addLayout(hbox_botones)
        
        scroll.setWidget(contenido)
        layout.addWidget(scroll)
        
        dlg.exec()

    def _toggle_feature_flag(self, flag_name: str, enabled: bool):
        """Alterna una feature flag en tiempo de ejecución."""
        from computadora.nucleo.feature_flags import FeatureFlags
        if enabled:
            FeatureFlags.activar(flag_name)
            self.hilo_habla.hablar(f"Activé {flag_name}", esperado=False)
        else:
            FeatureFlags.desactivar(flag_name)
            self.hilo_habla.hablar(f"Desactivé {flag_name}", esperado=False)
        logger.info(f"Feature flag {flag_name}: {enabled}")

    def _reset_feature_flags_defaults(self, checkboxes: dict):
        """Restaura configuración default de flags."""
        from computadora.nucleo.feature_flags import FeatureFlags
        
        defaults = {
            "escucha_voz": True,
            "nlu_herramientas": True,
            "tts": True,
            "nivel2_ollama": True,
            "proactividad": False,
            "monitor_sistema": False,
            "emociones_ruaj": False,
            "contexto_visual": False,
            "reconocimiento_facial": False,
            "life_autonomy": False,
            "circadian_cycles": False,
        }
        
        for flag_name, value in defaults.items():
            FeatureFlags.actualizar({flag_name: value})
            if flag_name in checkboxes:
                checkboxes[flag_name].setChecked(value)
        
        logger.info("Feature flags restauradas a defaults")
        self.hilo_habla.hablar("Configuración restaurada a valores por defecto", esperado=False)

    def _set_minimal_feature_flags(self, checkboxes: dict):
        """Activa solo voz + Maljut + herramientas básicas para modo aislado."""
        from computadora.nucleo.feature_flags import FeatureFlags
        
        minimal = {
            "escucha_voz": True,        # 🎤 Necesario
            "nlu_herramientas": True,   # 🧠 Necesario
            "tts": True,                # 🔊 Necesario
            "nivel2_ollama": True,      # 🤖 Para respuestas inteligentes
            "proactividad": False,      # 💡 Pausado
            "monitor_sistema": False,   # 📊 Pausado
            "emociones_ruaj": False,    # 😊 Simplificado
            "contexto_visual": False,   # 👁️ Pausado
            "reconocimiento_facial": False,  # 👤 Pausado
            "life_autonomy": False,     # 🌍 Pausado
            "circadian_cycles": False,  # 🌙 Pausado
        }
        
        FeatureFlags.actualizar(minimal)
        for flag_name, value in minimal.items():
            if flag_name in checkboxes:
                checkboxes[flag_name].setChecked(value)
        
        logger.info("Feature flags configuradas para modo mínimo (voz + Maljut + herramientas)")
        self.hilo_habla.hablar("Modo mínimo: solo voz, interfaz y herramientas básicas", esperado=False)

    def _mostrar_configuracion_visual(self):
        """Abre el configurador del tema visual del orbe (FPS, tema activo)."""
        try:
            from computadora.interfaz.configuracion_visual_dev import abrir_configuracion_visual
            abrir_configuracion_visual(parent=self)
            # Actualizar tema inmediatamente después de cerrar el diálogo
            self._actualizar_tema_visual()
        except Exception as e:
            logger.error(f"Error abriendo configuración visual: {e}")
            QMessageBox.critical(self, "❌ Error", f"No se pudo abrir el configurador visual:\n{e}")

    def _actualizar_tema_visual(self):
        """Re-lee la configuración y aplica el tema visual resultante."""
        self._config_tema_visual = ConfiguracionVisualDev()

        nuevo_tema = ThemeFactory.crear_tema(self._config_tema_visual.tipo_tema().value, self)
        if nuevo_tema.tipo != self._tema_visual.tipo or type(nuevo_tema) is not type(self._tema_visual):
            logger.info(f"Cambiando tema visual a {nuevo_tema.tipo.value}")
            self._tema_visual = nuevo_tema
            self._tema_visual.initialize()

        # Forzar repaint para aplicar cambios inmediatamente
        self.update()

    def _mostrar_admin_tareas(self):
        """Administrador de tareas integrado a la interfaz de Computadora.
        Muestra procesos del sistema en tiempo real como el Task Manager de Windows."""
        import psutil

        dlg = QDialog(self)
        dlg.setWindowTitle("⚙ Administrador de tareas de Computadora")
        dlg.setMinimumSize(700, 500)
        dlg.setStyleSheet(
            "QDialog { background: #0a0a0f; color: #c8a030; font-family: 'Consolas'; }"
            "QLabel { font-size: 11px; }"
            "QTableWidget { background: #0a0a0f; color: #c0c0c0; gridline-color: #1a1a25; "
            "border: 1px solid #2a2a30; font-size: 10px; }"
            "QTableWidget::item { padding: 2px 4px; }"
            "QTableWidget::item:selected { background: #1a1a25; color: #e8c040; }"
            "QHeaderView::section { background: #111118; color: #c8a030; border: 1px solid #2a2a30; "
            "padding: 3px; font-size: 10px; font-weight: bold; }"
            "QProgressBar { background: #1a1a25; border: 1px solid #2a2a30; "
            "border-radius: 3px; height: 16px; text-align: center; "
            "font-size: 10px; color: #e0e0e0; }"
        )
        layout = QVBoxLayout(dlg)

        # ── Resumen del sistema (barras) ──
        resumen = QWidget()
        rlay = QHBoxLayout(resumen)
        rlay.setContentsMargins(0, 0, 0, 0)

        def _make_bar(label, color):
            vbox = QVBoxLayout()
            lbl = QLabel(f"<b style='color:#e8c040;'>{label}</b>")
            bar = QProgressBar()
            bar.setRange(0, 1000)
            bar.setStyleSheet(
                bar.styleSheet() +
                f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}")
            vbox.addWidget(lbl)
            vbox.addWidget(bar)
            container = QWidget()
            container.setLayout(vbox)
            return container, bar

        cpu_w, cpu_bar = _make_bar("CPU", "#c85030")
        ram_w, ram_bar = _make_bar("RAM", "#30a8c8")
        gpu_w, gpu_bar = _make_bar("GPU", "#40c870")
        disco_w, disco_bar = _make_bar("Disco C:", "#c8a030")
        rlay.addWidget(cpu_w)
        rlay.addWidget(ram_w)
        rlay.addWidget(gpu_w)
        rlay.addWidget(disco_w)
        layout.addWidget(resumen)

        # ── Info resumida ──
        info_lbl = QLabel("")
        info_lbl.setStyleSheet("color: #888; font-size: 10px; padding: 2px;")
        layout.addWidget(info_lbl)

        # ── Tabla de procesos ──
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        tabla = QTableWidget()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["Proceso", "PID", "CPU %", "RAM (MB)", "Estado"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4):
            tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setSortingEnabled(True)
        tabla.verticalHeader().setVisible(False)
        layout.addWidget(tabla)

        def _refrescar_tareas():
            try:
                # Barras de resumen
                cpu_pct = psutil.cpu_percent(interval=0)
                mem = psutil.virtual_memory()
                disco = psutil.disk_usage('C:\\')

                cpu_bar.setValue(int(cpu_pct * 10))
                cpu_bar.setFormat(f"{cpu_pct:.0f}%")
                ram_bar.setValue(int(mem.percent * 10))
                ram_bar.setFormat(f"{mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB ({mem.percent:.0f}%)")
                disco_bar.setValue(int(disco.percent * 10))
                disco_bar.setFormat(f"{disco.used / (1024**3):.0f}/{disco.total / (1024**3):.0f} GB")

                # GPU
                gpu_txt = ""
                try:
                    import subprocess as sp
                    r = sp.run(
                        ['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
                         '--format=csv,noheader,nounits'],
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3,
                        creationflags=sp.CREATE_NO_WINDOW)
                    if r.returncode == 0 and r.stdout.strip():
                        parts = r.stdout.strip().split(',')
                        if len(parts) >= 3:
                            usado_mb = float(parts[0].strip())
                            total_mb = float(parts[1].strip())
                            uso_pct = float(parts[2].strip())
                            gpu_bar.setValue(int(uso_pct * 10))
                            gpu_bar.setFormat(f"{usado_mb:.0f}/{total_mb:.0f} MB ({uso_pct:.0f}%)")
                            gpu_txt = f"GPU: {uso_pct:.0f}%"
                except Exception as e:
                    logger.debug("GPU info no disponible: %s", e)
                    gpu_bar.setValue(0)
                    gpu_bar.setFormat("N/A")

                # Info resumida
                total_procs = len(psutil.pids())
                info_lbl.setText(
                    f"  Procesos: {total_procs}  |  "
                    f"CPU: {cpu_pct:.0f}%  |  "
                    f"RAM: {mem.percent:.0f}%  |  "
                    f"{gpu_txt}"
                )

                # Tabla de procesos — top 50 por RAM
                procs = []
                for p in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_info', 'status']):
                    try:
                        info = p.info
                        mem_mb = (info['memory_info'].rss / (1024**2)) if info.get('memory_info') else 0
                        procs.append((
                            info.get('name', '?'),
                            info.get('pid', 0),
                            info.get('cpu_percent', 0) or 0,
                            mem_mb,
                            info.get('status', '?'),
                        ))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Ordenar por RAM descendente, tomar top 50
                procs.sort(key=lambda x: x[3], reverse=True)
                procs = procs[:50]

                tabla.setSortingEnabled(False)
                tabla.setRowCount(len(procs))
                for row, (name, pid, cpu, ram_mb, status) in enumerate(procs):
                    # Color: procesos propios en dorado, el resto gris
                    is_computadora = 'python' in name.lower() or 'ollama' in name.lower()
                    color = "#e8c040" if is_computadora else "#c0c0c0"

                    item_name = QTableWidgetItem(name)
                    item_name.setForeground(QColor(color))
                    tabla.setItem(row, 0, item_name)

                    item_pid = QTableWidgetItem(str(pid))
                    item_pid.setData(2, pid)  # Para sorting numérico
                    tabla.setItem(row, 1, item_pid)

                    item_cpu = QTableWidgetItem(f"{cpu:.1f}")
                    item_cpu.setData(2, cpu)
                    tabla.setItem(row, 2, item_cpu)

                    item_ram = QTableWidgetItem(f"{ram_mb:.1f}")
                    item_ram.setData(2, ram_mb)
                    tabla.setItem(row, 3, item_ram)

                    item_st = QTableWidgetItem(status)
                    tabla.setItem(row, 4, item_st)
                tabla.setSortingEnabled(True)

            except Exception as e:
                logger.debug("Error refrescando admin tareas: %s", e)

        timer_tareas = QTimer(dlg)
        timer_tareas.timeout.connect(_refrescar_tareas)
        timer_tareas.start(2000)
        _refrescar_tareas()

        dlg.show()

    def _adjust_vox_threshold(self, delta: float):
        try:
            h = self.hilo_escucha
            new = max(0.3, min(0.98, getattr(h, "_vox_threshold", 0.68) + float(delta)))
            h._vox_threshold = new
            self.hilo_habla.hablar(f"Umbral de verificación ajustado a {new:.2f}")
            logger.info(f"Umbral de verificación ahora {new:.2f}")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("No pude ajustar umbral de verificación")

    def _show_owner_profile(self):
        try:
            p = Path(__file__).resolve().parent.parent.parent / "datos" / "owner_profile.json"
            if p.exists():
                txt = p.read_text(encoding="utf-8")
                self.hilo_habla.hablar("Perfil de propietario presente. Revisa el log si necesitas detalles.")
                logger.info(f"Owner profile: {txt}")
            else:
                self.hilo_habla.hablar("No hay perfil de propietario registrado.")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error mostrando perfil propietario")

    # ═══════════════════════════════════════════
    # SLOTS — VOZ
    # ═══════════════════════════════════════════

    def _procesar_cortesia(self, frase: str):
        """Maneja una frase de cortesía detectada sin wake word (saludo/despedida natural).

        Extraído de _al_recibir_voz para que la demo pueda invocarlo directamente
        con una frase de muestra. FIX: antes nunca se transicionaba al estado FSM
        "cortesia" (quedaba muerto en producción, solo alcanzable desde la demo);
        ahora sí, aunque sea transitorio porque _iniciar_pensamiento fuerza
        "procesando" un instante después.
        """
        if hasattr(self, '_vida'):
            self._vida.notificar_actividad()
        if hasattr(self, '_motor_proactividad'):
            self._motor_proactividad.registrar_respuesta_usuario()
        self.cambiar_estado("cortesia")
        self._iniciar_pensamiento(frase)

    @pyqtSlot(str)
    def _al_recibir_voz(self, texto: str):
        # FP-041 Shemirat Gevurá: si Gevurá espera respuesta, no procesar aquí
        if self._gevura_esperando:
            return
        logger.info(f"Voz recibida: '{texto}'")
        # RF-247: El reinicio ahora es automático (ver _on_requiere_reinicio)
        logger.debug(f"Estado actual: {self._estado}, pensando={self._pensando}, "
                      f"gate_copilot={self._esperando_gate_copilot}")
        # Confirmación solicitada por escucha: "[confirmar]..."
        if texto.startswith("[confirmar]"):
            original = texto[len("[confirmar]"):]
            # Si ya estamos esperando confirmación, ignore
            if self._esperando_confirmacion:
                logger.debug("Ya esperando confirmación, ignorando nueva petición")
                return
            self._esperando_confirmacion = True
            self._confirmacion_origen = original
            # Preguntar al usuario si nos habla a nosotros
            # Marcar que esperamos confirmación corta — así no pausamos la escucha
            self._awaiting_confirmation = True
            # Límite de espera para la confirmación (ms)
            try:
                timeout_ms = int(self.config.obtener("escucha.confirmation_timeout_ms", 7000))
            except Exception as e:
                logger.debug("Error leyendo timeout de confirmación, usando 7000ms: %s", e)
                timeout_ms = 7000
            # Programar limpieza automática del estado de confirmación
            QTimer.singleShot(timeout_ms, lambda: self._clear_confirmation_wait())
            # Pregunta más natural (evitar 'Di sí o no' explícito)
            self.hilo_habla.hablar("¿Me hablas a mí?")
            # marcar intercambio para aceptar respuesta corta sin wake word
            self.hilo_escucha.marcar_intercambio()
            # Informar al hilo de escucha que esperamos una confirmación
            try:
                self.hilo_escucha._esperando_confirmacion = True
            except Exception as e:
                logger.debug("Error configurando estado de confirmación: %s", e)
                pass
            return

        # Pre-boot: si el usuario habla antes de que Génesis ocurra, revelar y encolar
        if not self._boot_completo and texto != "[presencia]":
            # FIX: antes era un escalar — si el usuario hablaba más de una vez
            # durante la animación de Génesis (~2.5-4s), solo sobrevivía la
            # última frase y las anteriores se perdían en silencio.
            if not hasattr(self, '_bereshit_pendiente') or self._bereshit_pendiente is None:
                self._bereshit_pendiente = []
            self._bereshit_pendiente.append(texto)
            self._animacion_bereshit("Aquí estoy, señor.")
            return

        # Tzimtzum: si el usuario llama durante carga pesada, restaurar inmediato
        if self._modo_carga_pesada:
            logger.info("Wake word durante Tzimtzum — restaurando Computadora")
            if hasattr(self, '_vida') and self._vida._en_tzimtzum:
                self._vida._desactivar_tzimtzum()
            elif self._modo_carga_pesada:
                self._desactivar_modo_carga_pesada()
                # RF-149: Restaurar sin robar foco (patrón RF-144)
                import ctypes as _ct
                _hwnd = int(self.winId())
                _ct.windll.user32.ShowWindow(_hwnd, 4)  # SW_SHOWNOACTIVATE
                self._reasegurar_transparencia()
                _SWP = 0x0010 | 0x0002 | 0x0001  # SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE
                _ct.windll.user32.SetWindowPos(_hwnd, -1, 0, 0, 0, 0, _SWP)  # RF-308: Solo TOPMOST (sin NOTOPMOST)

        # Wake word sola — confirmar presencia y restaurar presencia plena
        if texto == "[presencia]":
            # Si aún no hizo boot, lanzar Génesis con saludo de presencia
            if not self._boot_completo:
                self._animacion_bereshit("Aquí estoy, señor.")
                return
            if hasattr(self, '_vida'):
                self._vida.restaurar_pleno()
                self._vida.notificar_actividad()
            self.hilo_habla.hablar("Aquí estoy, señor.")
            self.hilo_escucha.marcar_intercambio()
            return

        # שמות — Nombre completo "Computadora Emet" = regaño del propietario
        if texto.startswith("[regano]"):
            frase = texto[len("[regano]"):].strip()
            if hasattr(self, '_vida'):
                self._vida.restaurar_pleno()
                self._vida.notificar_actividad()
            self.hilo_escucha.marcar_intercambio()
            if frase:
                # Inyectar contexto de regaño para que NLU ajuste tono
                self._iniciar_pensamiento(f"[CONTEXTO: El propietario usó mi nombre completo 'Computadora Emet'. Está molesto o regañándome. Debo responder con tono sumiso, preocupado, preguntando qué hice mal.] {frase}")
            else:
                # Solo dijo "Computadora Emet" sin más — preguntar qué pasó
                self._iniciar_pensamiento("[CONTEXTO: El propietario usó mi nombre completo 'Computadora Emet'. Está molesto. Debo sonar preocupado y preguntar qué hice mal.]")
            return

        # Cortesía sin wake word — saludo/despedida natural
        if texto.startswith("[cortesia]"):
            frase = texto[len("[cortesia]"):].strip()
            self._procesar_cortesia(frase)
            return

        # Si Computadora está hablando o TTS streaming activo, evitar interrupciones.
        # Solo aceptar comandos de parada/alto o confirmaciones mientras habla.
        _tts_activo = (
            self._estado == "hablando"
            or getattr(self, '_streaming_en_curso', False)
            or getattr(self, '_esperando_fin_tts', False)
        )
        if _tts_activo:
            txt_low = texto.lower().strip()
            stop_words = ("detente", "para", "para ya", "alto", "calla", "cállate", "silencio", "stop")
            if texto.startswith("[confirmar]") or texto == "[presencia]":
                # permitir confirmaciones siempre
                pass
            elif any(sw in txt_low for sw in stop_words):
                logger.info("Comando de parada recibido — interrumpiendo habla")
                self.hilo_habla.interrumpir()
                self._streaming_en_curso = False
                self._esperando_fin_tts = False
                # Restaurar escucha tras interrupción
                try:
                    self.hilo_escucha.reanudar()
                except Exception as e:
                    logger.debug("Error reanudando escucha al detener TTS: %s", e)
                    pass
            else:
                logger.debug("Ignorando voz — TTS activo (estado=%s, stream=%s, esperando=%s)",
                             self._estado, self._streaming_en_curso, self._esperando_fin_tts)
                return

        if self._pensando:
            # Si estamos esperando permiso para Copilot, redirigir la voz ahí
            if self._esperando_gate_copilot:
                self._procesar_respuesta_gate_copilot(texto)
                return
            # Si estamos esperando respuesta de modo bg/fg
            if self._esperando_modo_tarea:
                self._procesar_respuesta_modo_tarea(texto)
                return
            # Deduplicar: no encolar el mismo texto (o muy similar) que ya está en cola
            if not self._cola_voz or texto != self._cola_voz[-1]:
                self._cola_voz.append(texto)
                logger.info(f"Voz encolada ({len(self._cola_voz)} pendientes)")
            else:
                logger.debug(f"Voz duplicada descartada: '{texto}'")
            return

        # Si estamos esperando confirmación, interpretar respuesta.
        # Usar coincidencias de palabra completa para evitar falsos positivos como "sistema".
        if self._esperando_confirmacion:
            txt = texto.lower().strip()
            if re.search(r"\b(?:sí|si|claro|afirmativo|afirmativa|s)\b", txt):
                motivo = self._confirmacion_origen or ""
                try:
                    self.hilo_escucha.marcar_intercambio(owner=True)
                except Exception as e:
                    logger.debug("Error marcando intercambio propietario: %s", e)
                    pass
                try:
                    self.hilo_escucha._esperando_confirmacion = False
                except Exception as e:
                    logger.debug("Error limpiando estado confirmación positiva: %s", e)
                    pass
                self._esperando_confirmacion = False
                self._confirmacion_origen = None
                self._awaiting_confirmation = False
                logger.info("Confirmación positiva — procesando texto original")
                self._iniciar_pensamiento(motivo)
                return
            if re.search(r"\b(?:no|negativo|cancela|detente|para|stop|quieto)\b", txt):
                logger.info("Confirmación negativa — ignorando")
                try:
                    self.hilo_escucha._esperando_confirmacion = False
                except Exception as e:
                    logger.debug("Error limpiando estado confirmación negativa: %s", e)
                    pass
                self._esperando_confirmacion = False
                self._confirmacion_origen = None
                self._awaiting_confirmation = False
                return
            logger.info("Confirmación ambiguo o fuera de contexto — ignorando respuesta de confirmación")
            try:
                self.hilo_escucha._esperando_confirmacion = False
            except Exception as e:
                logger.debug("Error limpiando estado confirmación no clara: %s", e)
                pass
            self._esperando_confirmacion = False
            self._confirmacion_origen = None
            self._awaiting_confirmation = False
            return

        self._iniciar_pensamiento(texto)

    def _on_propietario_presente(self):
        """Actualiza el estado del cerebro cuando el propietario es detectado por voz/rostro."""
        try:
            cerebro = getattr(self.orquestador, 'cerebro', None)
            if cerebro is None:
                return
            if getattr(cerebro, '_interlocutor_actual', None) != 'amo':
                cerebro._interlocutor_actual = 'amo'
                logger.info("WI-120: propietario presente — interlocutor_actual marcado como amo")
            if getattr(cerebro, '_modo_guardian', False):
                cerebro._modo_guardian = False
                logger.info("WI-120: propietario presente — modo_guardian desactivado")

            try:
                from computadora.utilidades.session_lock_listener import es_session_lock_bloqueada
                if es_session_lock_bloqueada():
                    logger.info(
                        "WI-120: propietario detectado mientras la sesión de Windows permanece bloqueada "
                        "— no se intenta desbloquear el escritorio seguro desde Python"
                    )
            except Exception as e:
                logger.debug("Error verificando estado de session lock: %s", e)
        except Exception as e:
            logger.debug("Error actualizando estado propietario presente: %s", e)

    def _al_cambio_fase_circadiana(self, fase: str):
        """Reaccionar al cambio de fase del ciclo circadiano."""
        logger.info(f"Fase circadiana cambió a: {fase}")
        # RF-228: No permitir que el circadiano override estados durante la demo
        if getattr(self, '_demo_en_curso', False):
            logger.debug("RF-228: Cambio circadiano ignorado durante demo")
            return
        # RF-152: Almacenar fase para modulación visual en _tick
        self._fase_circadiana = fase
        # FP-018 WI-082: Da'at→Netzaj — modular Ruaj por fase circadiana
        if hasattr(self, 'personalidad'):
            self.personalidad.ajustar_por_fase_circadiana(fase)
        if fase == "descanso_guardian":
            self.cambiar_estado("descanso_guardian")
        elif fase == "activo":
            # WI-CRIT-002: Usar postEvent thread-safe en lugar de QTimer.singleShot
            QCoreApplication.postEvent(self, _FaseEvent("despertando"))
            # Transicionar a escuchando tras 3 segundos
            QTimer.singleShot(3000, lambda: self.cambiar_estado("escuchando"))
        elif fase == "transicion":
            self.cambiar_estado("vigilia")

    def _aplicar_clasificacion_hablante(self, clasif: str):
        """Activa/desactiva modo_guardian y dispara alerta_extrano según
        clasificación de hablante. Extraído de _iniciar_pensamiento (antes
        inline) para que la demo pueda invocar la MISMA lógica de producción
        con un valor de clasificación sintético, sin disparar el pipeline
        completo de pensamiento/LLM.
        """
        if clasif in ("extraño", "conocido") or clasif.startswith("conocido:"):
            self.orquestador.cerebro._modo_guardian = True
            if clasif == "extraño":
                self.cambiar_estado("alerta_extrano")
        else:
            self.orquestador.cerebro._modo_guardian = False

    def _iniciar_pensamiento(self, texto: str):
        # RF-244: Interceptar "sí" cuando esperando confirmación Demo 2
        if getattr(self, '_esperando_demo2', False):
            # RF-322: Timeout 30s — evitar que demos fantasma se disparen
            if time.monotonic() - getattr(self, '_esperando_demo2_ts', 0) > 30:
                self._esperando_demo2 = False
                logger.debug("RF-322: _esperando_demo2 expirado (>30s)")
            else:
                # RF-273: Limpiar flag de confirmación en escucha
                try:
                    self.hilo_escucha._esperando_confirmacion = False
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                # RF-255: Strip ¡¿!? y puntuación — Whisper transcribe "¡Sí!" con signos
                tlow = texto.strip().lower().strip("¡¿!?.,:; ")
                # RF-272: Flexible — check primer palabra O si contiene afirmativo
                primera = tlow.split()[0] if tlow.split() else tlow
                _afirmativos = ("sí", "si", "yes", "dale", "va", "órale", "orale", "adelante", "claro", "porfa",
                                "ok", "bueno", "sale", "venga", "ándale", "andale", "perfecto", "listo",
                                "ejecuta", "hazla", "hazlo", "sigue", "continua", "continúa")
                # RF-290: Fuzzy match — Whisper a veces transcribe "sí" como "chaíz", "saíz", etc.
                # RF-322: Threshold subido 0.55→0.70 — evitar falsos positivos ("durable"→"dale" era 0.72)
                from difflib import SequenceMatcher
                _palabras = tlow.split()
                _fuzzy = any(SequenceMatcher(None, w, a).ratio() > 0.70 for w in _palabras for a in _afirmativos)
                es_afirmativo = any(w in _afirmativos for w in _palabras) or _fuzzy or any(w in tlow for w in ("quiero", "por favor", "muestra", "a ver"))
                if es_afirmativo:
                    self._esperando_demo2 = False
                    self._demo_herramientas()
                    return
                else:
                    self._esperando_demo2 = False
                    self.hilo_habla.hablar("Entendido, señor. Quedo a sus órdenes.")
                    return
        logger.debug(f"Iniciando pensamiento: '{texto[:100]}'")
        with self._estado_lock:
            self._pensando = True
            self._cola_voz.clear()
        self._cerebro_nivel = None
        self.cambiar_estado("procesando")
        # HF-024a: Informar a escucha que estamos pensando (no emitir estado_cambio)
        try:
            self.hilo_escucha._pensando_flag = True
        except Exception as e:
            logger.debug("Error configurando flag pensando: %s", e)
            pass
        # Notificar actividad y registrar interacción
        if hasattr(self, '_vida'):
            self._vida.notificar_actividad()
        if hasattr(self, 'personalidad'):
            self.personalidad.registrar_interaccion()
        self._registrar_interaccion_alquimica()
        # Registrar respuesta del usuario en ciclo circadiano
        if hasattr(self, '_motor_proactividad'):
            self._motor_proactividad.registrar_respuesta_usuario()

        # Modo Guardián: activar si hablante es extraño o conocido (no amo)
        clasif = getattr(self.hilo_escucha, 'clasificacion_hablante', 'amo')
        self._aplicar_clasificacion_hablante(clasif)
        # FP-019: Extraer nombre del interlocutor y pasar al cerebro
        if clasif == "amo":
            self.orquestador.cerebro._interlocutor_actual = "amo"
            # Registrar interacción del amo en GestorPersonas
            if hasattr(self, 'gestor_personas'):
                amo = self.gestor_personas.obtener_amo()
                if amo:
                    self.gestor_personas.registrar_interaccion(amo["nombre"])
            # WI-248: Auto-enrollar rostro del propietario si voz verificada
            self._auto_enrollar_rostro_propietario()
        elif clasif.startswith("conocido:"):
            nombre_interlocutor = clasif.split(":", 1)[1]
            self.orquestador.cerebro._interlocutor_actual = nombre_interlocutor
            if hasattr(self, 'gestor_personas'):
                self.gestor_personas.registrar_interaccion(nombre_interlocutor)
        else:
            self.orquestador.cerebro._interlocutor_actual = clasif  # "conocido" o "extraño"
        # Protección info sensible: flag terceros presentes
        hay_terceros = getattr(self.hilo_escucha, 'hay_terceros', False)
        self.orquestador.cerebro._hay_terceros = hay_terceros
        # Ruaj: notificar presencia/ausencia de terceros a Personalidad
        if hasattr(self, 'personalidad'):
            if hay_terceros:
                self.personalidad.registrar_terceros_presentes()
            else:
                self.personalidad.registrar_terceros_ausentes()

        self._hilo_pensamiento = HiloPensamiento(self.orquestador, texto)
        # כתר: Registrar input del usuario en ventana de introspección
        if self._ventana_keter.isVisible():
            self._ventana_keter.registrar_pensamiento_usuario(texto)
        self._hilo_pensamiento.respuesta_lista.connect(self._al_recibir_respuesta)
        self._hilo_pensamiento.error_ocurrido.connect(self._al_error_pensamiento)
        self._hilo_pensamiento.nivel_cambio.connect(self._al_cambiar_nivel)
        self._hilo_pensamiento.nivel_cambio.connect(self._ventana_keter.registrar_nivel)
        self._hilo_pensamiento.herramienta_usada.connect(self._al_usar_herramienta)
        self._hilo_pensamiento.herramienta_usada.connect(self._ventana_keter.registrar_herramienta)
        self._hilo_pensamiento.permiso_copilot.connect(self._al_solicitar_permiso_copilot)
        self._hilo_pensamiento.movimiento_solicitado.connect(self._al_solicitar_movimiento)
        self._hilo_pensamiento.fin_conversacion.connect(self._al_fin_conversacion)
        self._hilo_pensamiento.despedida_guardian.connect(self._al_despedida_guardian)
        self._hilo_pensamiento.fragmento_listo.connect(self._al_fragmento_listo)
        self._hilo_pensamiento.progreso_tarea.connect(self._al_progreso_tarea)
        self._hilo_pensamiento.preguntar_modo_tarea.connect(self._al_preguntar_modo_tarea)
        self._hilo_pensamiento.enroll_persona.connect(self._al_enroll_persona)
        self._hilo_pensamiento.bloqueo_seguridad.connect(self._al_bloqueo_seguridad)
        self._hilo_pensamiento.tzimtzum_solicitado.connect(self._al_tzimtzum_solicitado)
        # FP-022: Canal bidireccional Tiféret→Maljut
        self._hilo_pensamiento.confianza_respuesta.connect(self._al_confianza_respuesta)
        self._hilo_pensamiento.complejidad_procesamiento.connect(self._al_complejidad_procesamiento)
        self._hilo_pensamiento.frustracion_detectada.connect(self._al_frustracion_detectada)
        self._streaming_emitio = False
        self._streaming_en_curso = False
        self._esperando_fin_tts = False
        self._streaming_emitio_ts = 0.0
        self._hilo_pensamiento.start()

    @pyqtSlot(str)
    def _al_fragmento_listo(self, fragmento: str):
        """Recibe fragmento de streaming y lo envía directo al TTS."""
        self._streaming_emitio = True
        self._streaming_emitio_ts = time.monotonic()
        if not self._streaming_en_curso:
            # Primer fragmento: subir umbral (NO pausar) para permitir interrupciones
            self._streaming_en_curso = True
            try:
                self.hilo_escucha.subir_umbral()
            except Exception as e:
                logger.debug("Error subiendo umbral en fragmento: %s", e)
        self.hilo_habla.hablar(fragmento)

    @pyqtSlot(str, str, str)
    def _al_progreso_tarea(self, nombre: str, estado: str, categoria: str):
        """Recibe progreso de tarea compleja — actualiza estado visual."""
        if estado == "ejecutando":
            # RF-173B: Usar mapa extendido de categorías si la original está vacía
            self._trabajo_categoria = categoria or _HERRAMIENTA_A_CATEGORIA.get(nombre, "")
            self._trabajo_tool = nombre
            self.cambiar_estado("trabajando")
        elif estado == "completado":
            # Ruaj: tarea exitosa → transicionar humor
            if hasattr(self, 'personalidad'):
                self.personalidad.registrar_tarea_exitosa()
            # Flash breve — volver a trabajando genérico
            self._trabajo_categoria = ""
            self._trabajo_tool = ""

    @pyqtSlot(str)
    def _al_preguntar_modo_tarea(self, pregunta: str):
        """Computadora pregunta bg/fg — habla la pregunta y espera respuesta por voz."""
        self._esperando_modo_tarea = True
        # No bloquear la escucha mientras habla la pregunta (como confirmaciones)
        self._awaiting_confirmation = True
        # Marcar que esperamos respuesta — relaja filtro de falsos positivos
        try:
            self.hilo_escucha._esperando_respuesta = True
            self.hilo_escucha._esperando_respuesta_ts = time.monotonic()
        except Exception as e:
            logger.debug("Error configurando estado esperando respuesta: %s", e)
        self.hilo_habla.hablar(pregunta)
        # Cuando termine de hablar, _awaiting_confirmation permite que la voz
        # no sea ignorada y entre al handler de modo tarea

    def _ejecutar_accion_remota(self, accion: str):
        """Ejecuta acciones remotas de Minimi sin el state management de _al_recibir_respuesta.
        Esto evita interferencia por streaming flags, cola_voz, y cerebro compartido."""
        logger.info(f"[Minimi remoto] Ejecutando acción: '{accion}'")
        if accion == "__DEMO_INTRODUCCION__":
            self._demo_introduccion()
        elif accion == "__DEMO_ANIMACIONES__":
            self._demo_animaciones()
        elif accion == "__DEMO_HERRAMIENTAS__":
            self._demo_herramientas()
        elif accion == "__SILENCIO__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.activar_silencio(30)
            self.hilo_habla.hablar("Entendido, no molestaré por 30 minutos.")
        elif accion == "__ALERTAS_OFF__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.desactivar_alertas_sistema()
            self.hilo_habla.hablar("Entendido, desactivo las alertas del sistema.")
        elif accion == "__ALERTAS_ON__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.activar_alertas_sistema()
            self.hilo_habla.hablar("Alertas del sistema activadas de nuevo, señor.")
        elif accion == "__MINIMIZAR__":
            self.hilo_habla.hablar("Entendido, me minimizo.")
            self.showMinimized()
        else:
            # Texto plano — hablar directamente
            if accion:
                self.hilo_habla.hablar(accion)

    @pyqtSlot(str)
    def _al_recibir_respuesta(self, respuesta: str):
        """🔥 CRÍTICO: Procesa la respuesta del NLU y la envía a TTS.
        WICRIT-FIX: Asegurar que TODAS las respuestas se hablen, sin excepciones.
        """
        if not respuesta:
            logger.warning("Respuesta vacía recibida — ignorando")
            return
            
        with self._estado_lock:
            self._pensando = False
        self._cerebro_nivel = None
        # HF-024a: Desbloquear estado visual en escucha
        try:
            self.hilo_escucha._pensando_flag = False
        except Exception as e:
            logger.debug("Error limpiando flag pensando: %s", e)

        # ── Streaming management ──
        # El cerebro indica si la respuesta ya fue hablada por streaming real
        # (fragmentos de Ollama). Si solo se emitió un filler ("Deme un momento..."),
        # respuesta_ya_streameada es False y la respuesta final SÍ debe hablarse.
        cerebro = self.orquestador.cerebro
        ya_streameada = getattr(cerebro, 'respuesta_ya_streameada', False)
        self._streaming_en_curso = False

        # Si la respuesta ya fue streameada pero TTS aún tiene cola, esperar
        if ya_streameada and self._streaming_emitio:
            self._esperando_fin_tts = True
            self._streaming_emitio = False
            logger.info("Respuesta ya emitida por streaming — esperando fin TTS")
            if respuesta.rstrip().endswith("?"):
                try:
                    self.hilo_escucha._esperando_respuesta = True
                    self.hilo_escucha._esperando_respuesta_ts = time.monotonic()
                except Exception as e:
                    logger.debug("Error configurando esperando respuesta por pregunta: %s", e)
            return

        # Limpiar flags de streaming (fue solo filler, no respuesta real)
        self._streaming_emitio = False
        self._esperando_fin_tts = False

        # Limpiar estado de trabajo visual
        if self._estado == "trabajando":
            self.cambiar_estado("dormido")

        if self._cola_voz:
            ultima = self._cola_voz[-1]
            self._cola_voz.clear()
            logger.info(f"Hay voz pendiente, procesando: '{ultima}'")
            self._iniciar_pensamiento(ultima)
            return

        logger.info(f"Computadora responde: '{respuesta}'")
        self.hilo_escucha.marcar_intercambio(owner=True)  # Mantener ventana conversatoria

        # Señales especiales del cerebro
        if respuesta == "__SILENCIO__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.activar_silencio(30)
            self.hilo_habla.hablar("Entendido, no molestaré por 30 minutos.")
            return
        if respuesta == "__RESUMEN__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad._ya_saludo_hoy = ""  # Forzar briefing
                sug = self._motor_proactividad._check_buenos_dias()
                if sug:
                    self.hilo_habla.hablar(sug.texto)
                    return
            self.hilo_habla.hablar("No tengo resumen disponible en este momento.")
            return
        if respuesta == "__ALERTAS_OFF__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.desactivar_alertas_sistema()
            self.hilo_habla.hablar("Entendido, desactivo las alertas del sistema.")
            return
        if respuesta == "__ALERTAS_ON__":
            if hasattr(self, '_motor_proactividad'):
                self._motor_proactividad.activar_alertas_sistema()
            self.hilo_habla.hablar("Alertas del sistema activadas de nuevo, señor.")
            return
        if respuesta == "__DEMO_INTRODUCCION__":
            self._demo_introduccion()
            return
        if respuesta == "__DEMO_ANIMACIONES__":
            self._demo_animaciones()
            return
        if respuesta == "__DEMO_HERRAMIENTAS__":
            self._demo_herramientas()
            return
        if respuesta == "__MINIMIZAR__":
            self.hilo_habla.hablar("Entendido, me minimizo.")
            self.showMinimized()
            return

        # Si Computadora hace una pregunta, marcar para relajar el filtro de FP
        if respuesta.rstrip().endswith("?"):
            try:
                self.hilo_escucha._esperando_respuesta = True
                self.hilo_escucha._esperando_respuesta_ts = time.monotonic()
            except Exception as e:
                logger.debug("Error configurando esperando respuesta final: %s", e)
        self.hilo_habla.hablar(respuesta)

    def _demo_introduccion(self):
        """WI-279 Demo 0 — Introducción completa.
        Auto-conocimiento + Génesis bíblico, luego encadena Demo 1 y 2."""
        if self._demo_en_curso:
            return
        self._demo_en_curso = True
        self._demo_opaco = True  # WI-326: Opacidad 100% durante demo
        self._demo_idx = 0
        self._demo_introduccion_activo = True
        logger.info("Demo Introducción: iniciando WI-279")

        # Obtener datos de auto-conocimiento
        try:
            from computadora.nucleo.emet import resumen_para_demo, resumen_genesis_para_demo
            texto_identidad = resumen_para_demo()
            texto_genesis = resumen_genesis_para_demo()
        except ImportError:
            texto_identidad = "Soy Computadora. La verdad inscrita en mi código me define."
            texto_genesis = "Los siete días de la Creación se reflejan en mi arquitectura."

        # RF-228: Forzar boot si pendiente
        if not self._boot_completo:
            self._boot_completo = True
            if hasattr(self, '_bereshit_activo') and self._bereshit_activo:
                if hasattr(self, '_bereshit_timer') and self._bereshit_timer.isActive():
                    self._bereshit_timer.stop()
                if hasattr(self, '_bereshit_timeout') and self._bereshit_timeout.isActive():
                    self._bereshit_timeout.stop()
                self._bereshit_activo = False
            self._escala = 1.0
            self._escala_objetivo = 1.0
            logger.info("Demo Introducción: Boot forzado")

        # Pausar subsistemas
        try:
            self._vida._timer.stop()
            self._vida._timer_movimiento.stop()
            self._vida._pos_objetivo = None
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self._motor_proactividad.activar_silencio(10)
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self.hilo_escucha.pausar()
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)

        orbe = self

        self._demo_pasos = [
            # Apertura
            (lambda: (orbe.cambiar_estado("hablando"),
                      orbe.hilo_habla.hablar(
                          "La verdad. Permítame presentarme.")),
             "habla"),
            # Auto-conocimiento (<1 min)
            (lambda: orbe.hilo_habla.hablar(texto_identidad), "habla"),
            # Pausa contemplativa
            (lambda: None, 2500),
            # Génesis intro
            (lambda: orbe.hilo_habla.hablar(
                "Ahora, los siete días de la Creación reflejados en mi arquitectura."),
             "habla"),
            # Génesis bíblico × arquitectura
            (lambda: orbe.hilo_habla.hablar(texto_genesis), "habla"),
            # Pausa contemplativa
            (lambda: None, 2500),
        ]

        def _introduccion_finale():
            """Finale de la introducción → hablar transición y encadenar Demo 1."""
            logger.info("Demo Introducción: fase de verdad completada — encadenando Demo 1")
            orbe.hilo_habla.hablar(
                "Esa es mi verdad. Ahora, con su permiso, se la demuestro.")

        def _introduccion_cola_vacia():
            """Cuando TTS termina transición, iniciar Demo 1."""
            if not getattr(orbe, '_demo_en_curso', False):
                return
            orbe._demo_en_curso = False
            orbe._demo_opaco = False  # WI-326: Restaurar transparencia normal
            try:
                orbe.hilo_habla.cola_vacia.disconnect(_introduccion_cola_vacia)
            except Exception as e:
                logger.debug("Excepcion ignorada: %s", e)
            QTimer.singleShot(2000, lambda: orbe._demo_animaciones())

        self._demo_finale_fn = _introduccion_finale
        self._demo_cola_vacia_fn = _introduccion_cola_vacia
        self._demo_ejecutar_paso()

    def _demo_animaciones(self):
        """RF-106+RF-154+RF-174 מראה המלכות — Coreografía visual sincronizada
        por señales: cada paso espera a que TTS termine antes de avanzar."""
        self._demo_en_curso = True
        self._demo_opaco = True  # WI-326: Opacidad 100% durante demo
        self._demo_idx = 0
        self._demo_cursor_override = None  # defensivo: por si una corrida anterior quedó interrumpida en ACT IV
        logger.info("Demo Maljut: iniciando coreografía RF-154+RF-174")

        # RF-228: Si el boot aún no completó, forzar — la demo ES la revelación
        if not self._boot_completo:
            self._boot_completo = True
            if hasattr(self, '_bereshit_activo') and self._bereshit_activo:
                if hasattr(self, '_bereshit_timer') and self._bereshit_timer.isActive():
                    self._bereshit_timer.stop()
                if hasattr(self, '_bereshit_timeout') and self._bereshit_timeout.isActive():
                    self._bereshit_timeout.stop()
                self._bereshit_activo = False
            self._escala = 1.0
            self._escala_objetivo = 1.0
            logger.info("RF-228: Boot forzado — demo implica revelación")

        # RF-158: Pausar subsistemas concurrentes durante la demo
        try:
            self._vida._timer.stop()
            self._vida._timer_movimiento.stop()
            self._vida._pos_objetivo = None
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self._motor_proactividad.activar_silencio(5)  # RF-228: 5 min (demo ~3 min + margen)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self.hilo_escucha.pausar()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Guardar estado y paleta original para restaurar al final
        _alq_pri_orig = QColor(self._color_alq_primario)
        _alq_sec_orig = QColor(self._color_alq_secundario)
        _etapa_orig = self._etapa_alquimica  # WI-241: Guardar etapa para restaurar
        _humor_orig = self.personalidad.humor_actual if hasattr(self, 'personalidad') else "neutral"

        orbe = self  # closure reference

        def _set_paleta(etapa):
            paleta = _PALETAS_ALQUIMICAS[etapa]
            orbe._color_alq_target_pri = QColor(paleta["primario"])
            orbe._color_alq_target_sec = QColor(paleta["secundario"])
            orbe._alq_lerp_progress = 0.0
            # WI-241: Actualizar etapa para que _calcular_color_ohr use la base correcta
            orbe._etapa_alquimica = etapa

        def _set_humor(humor):
            if hasattr(orbe, 'personalidad'):
                orbe.personalidad._transicionar_humor(humor, "demo_maljut", forzar=True)

        # ── Helpers "honestos" para ACT II: ejecutan el mecanismo real en vez
        # de asignar el atributo a mano (ver principio rector del plan Fase 2) ──
        def _demo_nivel1_real():
            """Clasifica 'hola' con el regex real de Nivel 1 y narra la respuesta real.
            RF-350: en hilo aparte, no bloquear GUI. FIX: antes llamaba
            _pensar_nivel1() síncrono en el hilo principal — esa función
            también revisa hechizos y patrones APRENDIDOS (Lemed), que pueden
            ejecutar una herramienta arbitraria según lo que el sistema haya
            aprendido con el tiempo; si esa herramienta tarda o se bloquea,
            toda la ventana se congelaba durante la demo."""
            def _ejecutar_en_hilo():
                cerebro = orbe.orquestador.cerebro
                anterior_on_nivel = cerebro.on_nivel
                cerebro.on_nivel = orbe._al_cambiar_nivel
                try:
                    respuesta = cerebro._pensar_nivel1("hola")
                except Exception as e:
                    logger.debug("Demo Nivel 1: error en clasificación real: %s", e)
                    respuesta = None
                finally:
                    cerebro.on_nivel = anterior_on_nivel
                base = "Escuchando. Nivel uno: comprensión directa. "
                if respuesta:
                    texto = base + f"Por ejemplo, si usted dijera 'hola', yo respondería: {respuesta}"
                else:
                    texto = base + "Resuelve comandos simples por patrones, sin necesitar razonamiento profundo."
                orbe._demo_herramienta_signal.emit("nivel1_demo", texto)

            import threading
            threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-nivel1").start()

        def _demo_nivel2_estado():
            """Activa Nivel 2 de verdad solo si Ollama está realmente disponible."""
            cerebro = orbe.orquestador.cerebro
            if getattr(cerebro, 'ollama_disponible', False):
                orbe._al_cambiar_nivel("nivel2")
                return "Procesando. Nivel dos: razonamiento profundo vía Ollama, disponible en este momento, señor."
            orbe._cerebro_nivel = None
            return "Nivel dos usaría Ollama para razonamiento profundo, pero no está disponible en este momento, señor."

        def _demo_trabajo_real():
            """Dispara _al_progreso_tarea real (categoría 'busqueda') con una
            consulta genuina a la memoria, en vez de fingir _trabajo_categoria.
            Usa obtener_recuerdo_reciente() (sin palabra clave) en vez de
            buscar_en_memoria("señor", ...): esa búsqueda por palabra clave
            casi nunca matchea nada real porque el texto guardado rara vez
            contiene literalmente "señor", lo que garantizaba un "no
            encontré nada" en casi cualquier corrida de la demo."""
            orbe._al_progreso_tarea("consultar_memoria", "ejecutando", "busqueda")
            try:
                from computadora.memoria.memoria import obtener_recuerdo_reciente
                recuerdo = obtener_recuerdo_reciente(dias=7)
                if recuerdo and recuerdo.get("text", "").strip():
                    resultado = recuerdo["text"][:150]
                else:
                    resultado = "aún no tengo recuerdos recientes guardados"
                texto = orbe._sanitizar_para_voz(f"Trabajando. Herramientas activas. Por ejemplo, consultando mi memoria: {resultado}")
            except Exception as e:
                logger.debug("Demo trabajo real: error consultando memoria: %s", e)
                texto = "Trabajando. Herramientas activas."
            orbe._al_progreso_tarea("consultar_memoria", "completado", "busqueda")
            return texto

        # ── ACT IV helper: narra el resultado REAL de la detección de caricia ──
        def _demo_narrar_tacto():
            info = getattr(orbe, '_ultimo_tacto_info', None)
            if info and info.get('gesto') == 'caricia' and (time.monotonic() - info.get('ts', 0)) < 3.0:
                return "Caricia detectada, señor. Siento la calidez de su atención."
            return "Percibo su cercanía, señor, aunque esta vez el gesto no se sostuvo lo suficiente para registrarse como caricia."

        # ── ACT V helper: confirma con el regex real que 'hola' es cortesía ──
        def _demo_narrar_cortesia():
            from computadora.voz.escucha import _RE_CORTESIA
            if _RE_CORTESIA.match("hola"):
                return "Cortesía. Saludo respetuoso. Reconozco frases como 'hola' sin que tenga que llamarme por mi nombre."
            return "Cortesía. Saludo respetuoso."

        # ── ACT VIII+IX: estado compartido de la cámara ──
        # FIX: antes ACT VIII conectaba Y desconectaba la cámara, y segundos
        # después ACT IX (_demo_ver_camara) la volvía a abrir desde cero —
        # dos aperturas de cámara consecutivas (cada una con su propia
        # latencia de hardware DirectShow/MSMF) en vez de una sola. Ahora se
        # recuerda el estado ANTES de que empiece esta secuencia una sola
        # vez, se deja conectada entre ambos Actos, y solo se restaura al
        # final de ACT IX.
        _camara_estado_previo = {"ya_conectada": None}

        def _demo_guardian_real():
            """RF-350: en hilo aparte — _tick_guardian() también abre/lee la
            cámara de forma síncrona, con el mismo riesgo de congelar la
            ventana un instante que ya se corrigió en _demo_ver_camara."""
            def _ejecutar_en_hilo():
                try:
                    from computadora.nucleo.kli import GestorKelim
                    gestor = GestorKelim.instancia()
                    if _camara_estado_previo["ya_conectada"] is None:
                        info_antes = next((k for k in gestor.listar() if k["id"] == "camara_local"), None)
                        _camara_estado_previo["ya_conectada"] = bool(info_antes and info_antes["estado"] == "CONECTADO")
                    orbe._tick_guardian()
                    info_despues = next((k for k in gestor.listar() if k["id"] == "camara_local"), None)
                    conectada_ahora = bool(info_despues and info_despues["estado"] == "CONECTADO")
                    if conectada_ahora:
                        texto = "Guardián activo, señor. Cámara conectada: reviso luminosidad y movimiento en tiempo real."
                    else:
                        texto = "Guardián activo, señor, aunque en este momento no logro conectar con la cámara."
                except Exception as e:
                    logger.debug("Demo guardián: error en tick real: %s", e)
                    texto = "Guardián activo, señor. Vigilo en silencio cuando usted se ausenta."
                orbe._demo_herramienta_signal.emit("guardian_demo", texto)

            import threading
            threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-guardian").start()

        def _demo_restaurar_camara():
            """Al terminar ACT IX: desconectar la cámara SOLO si no estaba
            conectada antes de que ACT VIII empezara a usarla."""
            if _camara_estado_previo["ya_conectada"] is False:
                try:
                    from computadora.nucleo.kli import GestorKelim
                    GestorKelim.instancia().desconectar("camara_local")
                except Exception as e:
                    logger.debug("Demo guardián: error restaurando estado de cámara: %s", e)

        # ── RF-174: Lista de pasos — (acción, espera) ──
        # espera = "habla" → esperar habla_terminada + 400ms pausa
        # espera = int    → esperar N ms (para transiciones rápidas sin voz)
        self._demo_pasos = [
            # ── ACT I: GÉNESIS — Estados fundamentales ──
            (lambda: (orbe.cambiar_estado("dormido"),
                      orbe.hilo_habla.hablar("Observe, señor. Esto es el Maljut: mi presencia completa. Estado dormido.")),
             "habla"),
            (lambda: (orbe.cambiar_estado("despertando"),
                      orbe.hilo_habla.hablar("Despertando. La luz crece.")),
             "habla"),
            (lambda: (orbe.cambiar_estado("vigilia"),
                      orbe.hilo_habla.hablar("Vigilia. Consciente pero en espera.")),
             "habla"),

            # ── ACT II: INTERACCIÓN — Ciclo de trabajo (absorbe el antiguo ACT VI: ──
            # _al_cambiar_estado_escucha ya resetea _ripple_fase de verdad) ──
            (lambda: (orbe._al_cambiar_estado_escucha("escuchando"),
                      _demo_nivel1_real()),
             "habla"),
            (lambda: (orbe.cambiar_estado("procesando"),
                      orbe.hilo_habla.hablar(_demo_nivel2_estado())),
             "habla"),
            (lambda: orbe.hilo_habla.hablar(_demo_trabajo_real()), "habla"),
            (lambda: (orbe.cambiar_estado("hablando"),
                      orbe.hilo_habla.hablar("Hablando. Nivel tres existiría para sabiduría más profunda vía Copilot o Gemini, pero requiere su autorización explícita, así que no lo activo ahora, señor.")),
             "habla"),

            # ── ACT III: HUMORES — Ciclo emocional completo (Ruaj) — 13 humores ──
            (lambda: (orbe.cambiar_estado("escuchando"),
                      setattr(orbe, '_cerebro_nivel', None),
                      _set_humor("neutral"),
                      orbe.hilo_habla.hablar("Los trece humores del Ruaj. Neutral: el estado base.")),
             "habla"),
            (lambda: (_set_humor("sereno"),
                      orbe.hilo_habla.hablar("Sereno. Calma y azul suave.")),
             "habla"),
            (lambda: (_set_humor("contento"),
                      orbe.hilo_habla.hablar("Contento. Brillo dorado.")),
             "habla"),
            (lambda: (_set_humor("emocionado"),
                      orbe.hilo_habla.hablar("Emocionado. Partículas aceleradas.")),
             "habla"),
            (lambda: (_set_humor("activo"),
                      orbe.hilo_habla.hablar("Activo. Energía concentrada.")),
             "habla"),
            (lambda: (_set_humor("curioso"),
                      orbe.hilo_habla.hablar("Curioso. La rotación se acelera.")),
             "habla"),
            (lambda: (_set_humor("reflexivo"),
                      orbe.hilo_habla.hablar("Reflexivo. Violeta contemplativo.")),
             "habla"),
            (lambda: (_set_humor("formal"),
                      orbe.hilo_habla.hablar("Formal. Compostura y azul sutil.")),
             "habla"),
            (lambda: (_set_humor("preocupado"),
                      orbe.hilo_habla.hablar("Preocupado. Pulso rápido.")),
             "habla"),
            (lambda: (_set_humor("aburrido"),
                      orbe.hilo_habla.hablar("Aburrido. Las partículas se apagan.")),
             "habla"),
            (lambda: (_set_humor("cansado"),
                      orbe.hilo_habla.hablar("Cansado. Brillo mínimo.")),
             "habla"),
            (lambda: (_set_humor("regañado"),
                      orbe.hilo_habla.hablar("Regañado. Rojo tenue, cabeza baja.")),
             "habla"),
            (lambda: (_set_humor("triste"),
                      orbe.hilo_habla.hablar("Triste. Se apaga. Trece humores en total, señor.")),
             "habla"),

            # ── ACT IV: DON DEL TACTO — Zonas reales, vía cursor sintético ──
            # (`_demo_cursor_override` alimenta el pipeline real de _animar(),
            # líneas 1623-1719: zona, proximidad y detección de caricia genuinas)
            (lambda: (_set_humor("neutral"),
                      setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(250)),
                      orbe.hilo_habla.hablar("Don del tacto. Zona Reshimó.")),
             "habla"),
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(150)), 400),
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(70)), 400),
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(30)), 350),   # entrada 1 a Néfesh
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(150)), 300),  # salida
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(30)), 350),   # entrada 2
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(150)), 300),  # salida
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(30)), 500),   # entrada 3 → caricia real
            (lambda: orbe.hilo_habla.hablar(_demo_narrar_tacto()), "habla"),
            (lambda: setattr(orbe, '_demo_cursor_override', orbe._demo_punto_a_distancia(600)), 600),  # Aín

            # ── ACT V: PROTECCIÓN ── (RF-240: alquimia narrada movida a ACT VII)
            (lambda: (setattr(orbe, '_demo_cursor_override', None),
                      orbe._al_bloqueo_seguridad("etico"),
                      orbe.hilo_habla.hablar("Gevurá activa. Protección ética.")),
             "habla"),
            (lambda: None, 2200),  # margen: absorbe el auto-revert real de _al_bloqueo_seguridad (2s)
            (lambda: (orbe._al_error_pensamiento("Error simulado de demostración"),
                      orbe.hilo_habla.hablar("Error. Algo salió mal.")),
             "habla"),
            (lambda: None, 3200),  # margen: absorbe el auto-revert real de _al_error_pensamiento (3s)
            (lambda: (orbe.cambiar_estado("cortesia"),
                      orbe.hilo_habla.hablar(_demo_narrar_cortesia())),
             "habla"),
            (lambda: (orbe._aplicar_clasificacion_hablante("extraño"),
                      orbe.hilo_habla.hablar("Alerta. Voz desconocida detectada.")),
             "habla"),
            (lambda: orbe._aplicar_clasificacion_hablante("amo"), 200),  # reset real: no dejar _modo_guardian colgado

            # ── ACT VII (RF-179): LAS 4 VOCES DE LA ALQUIMIA ──
            # WI-241: Atenuar Dmut para que paletas puras se aprecien sin interferencia
            (lambda: (setattr(orbe, '_demo_dmut_factor', 0.15),
                      orbe.cambiar_estado("hablando"),
                      _set_paleta(EtapaAlquimica.NIGREDO),
                      orbe.hilo_habla.hablar("Las cuatro voces de la alquimia. Nigredo: la voz desde la oscuridad.")),
             "habla"),
            (lambda: (_set_paleta(EtapaAlquimica.ALBEDO),
                      orbe.hilo_habla.hablar("Albedo: la voz de la plata. Purificación.")),
             "habla"),
            (lambda: (_set_paleta(EtapaAlquimica.CITRINITAS),
                      orbe.hilo_habla.hablar("Citrinitas: la voz del oro. Iluminación.")),
             "habla"),
            (lambda: (_set_paleta(EtapaAlquimica.RUBEDO),
                      orbe.hilo_habla.hablar("Rubedo: la voz del fuego. Perfección.")),
             "habla"),

            # ── ACT VIII (RF-220): EL GUARDIÁN ──
            # WI-241: Restaurar Dmut tras ACT VII
            (lambda: (setattr(orbe, '_demo_dmut_factor', 1.0),
                      orbe.cambiar_estado("descanso_guardian"),
                      _set_paleta(EtapaAlquimica.NIGREDO),
                      orbe.hilo_habla.hablar("El guardián. Cuando el señor se ausenta, vigilo en silencio con mi cámara. Si lo reconozco al volver, me desactivo yo solo.")),
             "habla"),
            (lambda: (orbe.cambiar_estado("alerta_extrano"),
                      _demo_guardian_real()),
             "habla"),

            # ── ACT IX (RF-220): LA VISIÓN NOCTURNA — reutiliza _demo_ver_camara() real ──
            (lambda: (_set_paleta(EtapaAlquimica.ALBEDO),
                      orbe.hilo_habla.hablar("Visión nocturna. Con la cámara como ojo, veo en la oscuridad. CLAHE ilumina donde la luz no alcanza. Déjeme mostrarle.")),
             "habla"),
            (lambda: orbe._demo_ver_camara(), "habla"),
            (lambda: (_demo_restaurar_camara(),
                      _set_paleta(EtapaAlquimica.CITRINITAS),
                      orbe.hilo_habla.hablar("Por la mañana, entrego el reporte. El guardián nunca descansa.")),
             "habla"),

            # ── ACT X (RF-241): KOAJ HACOMPUTADORA — Demostración de Poder (info) ──
            (lambda: (orbe._al_progreso_tarea("demostracion", "ejecutando", "busqueda"),
                      _set_paleta(EtapaAlquimica.RUBEDO),
                      orbe.hilo_habla.hablar("Ahora le mostraré lo que puedo hacer, señor. Mis herramientas en acción.")),
             "habla"),
            (lambda: orbe._demo_ejecutar_herramienta("obtener_fecha_hora", {}, "La fecha y hora actuales son: {resultado}"), "habla"),
            (lambda: orbe._demo_ejecutar_herramienta("estado_rapido_sistema", {}, "El estado del sistema: {resultado}"), "habla"),
            # RF-282+RF-287: Usar ContextoPantalla live con visual feedback
            (lambda: (setattr(orbe, '_cerebro_nivel', "nivel1"),
                      orbe.cambiar_estado("procesando"),
                      orbe._contexto_pantalla._actualizar(),  # WI-319: Refrescar contexto antes de describir
                      orbe.hilo_habla.hablar(f"Lo que veo en pantalla: {orbe._contexto_pantalla.descripcion_contexto() or 'Sistema operativo con ventana activa. Puedo ver todo lo que hace, señor.'}")), "habla"),
            (lambda: orbe._demo_ejecutar_herramienta("leer_portapapeles", {}, "En el portapapeles encuentro: {resultado}"), "habla"),
            (lambda: orbe._al_progreso_tarea("demostracion", "completado", "busqueda"), 100),

            # ── ACT XI (RF-283): NESHAMÁ — Identidad y Memoria ──
            (lambda: (orbe.cambiar_estado("hablando"),
                      setattr(orbe, '_cerebro_nivel', "nivel2"),
                      _set_paleta(EtapaAlquimica.CITRINITAS),
                      orbe.hilo_habla.hablar("Ahora le contaré lo que sé de mí mismo, señor. Soy Computadora. Fui creado en Python con PyQt6. Mi arquitectura se basa en el Etz HaChaim, el Árbol de la Vida cabalístico. Tengo tres cerebros: instinto, razonamiento y sabiduría.")),
             "habla"),
            (lambda: orbe._demo_narrar_memoria(), "habla"),
        ]

        # ── FINALE (se ejecuta al terminar los pasos) ──
        def _demo_finale():
            orbe._color_alq_target_pri = QColor(_alq_pri_orig)
            orbe._color_alq_target_sec = QColor(_alq_sec_orig)
            orbe._alq_lerp_progress = 0.0
            orbe._etapa_alquimica = _etapa_orig  # WI-241: Restaurar etapa original
            orbe._demo_dmut_factor = 1.0  # WI-241: Restaurar Dmut
            orbe._cerebro_nivel = None
            orbe._zona_tacto = 0
            orbe._trabajo_categoria = ""
            orbe._trabajo_tool = ""
            orbe._demo_cursor_override = None  # defensivo: liberar el seam de ACT IV si quedó activo
            try:
                orbe._aplicar_clasificacion_hablante("amo")  # defensivo: no dejar _modo_guardian colgado
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            _set_humor(_humor_orig)
            try:
                orbe._vida._timer.start(500)
                orbe._vida._timer_movimiento.start(16)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            orbe.cambiar_estado("hablando")
            # RF-244: Puente Demo 1→Demo 2
            # WI-279: Si Demo Introducción activa, encadenar automáticamente sin preguntar
            if getattr(orbe, '_demo_introduccion_activo', False):
                orbe.hilo_habla.hablar("Primera parte completada. Ahora la segunda: mis herramientas.")
                logger.info("Demo Introducción: animaciones completadas — encadenando herramientas")
            else:
                orbe.hilo_habla.hablar("Eso es todo lo que puedo mostrar sin permisos especiales, señor. ¿Desea ver la segunda demostración?")
                orbe._esperando_demo2 = True
                orbe._esperando_demo2_ts = time.monotonic()
                # RF-273: Activar flag confirmación en escucha para bypass noise filter
                try:
                    orbe.hilo_escucha._esperando_confirmacion = True
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                logger.info("Demo Maljut: coreografía RF-154+RF-174 finalizada — esperando respuesta Demo 2")

        def _demo_cola_vacia():
            """RF-176: Solo reactivar escucha cuando TTS terminó por completo."""
            if not getattr(orbe, '_demo_en_curso', False):
                return
            orbe._demo_en_curso = False
            orbe._demo_opaco = False  # WI-326: Restaurar transparencia normal
            try:
                orbe.hilo_habla.cola_vacia.disconnect(_demo_cola_vacia)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            # WI-279: Si Demo Introducción activa, encadenar Demo 2 sin restaurar
            if getattr(orbe, '_demo_introduccion_activo', False):
                QTimer.singleShot(2000, lambda: orbe._demo_herramientas())
                return
            try:
                orbe._motor_proactividad.desactivar_silencio()
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            try:
                orbe.hilo_escucha.reanudar()
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            try:
                cooldown = int(orbe.config.obtener("escucha.post_tts_cooldown_ms", 600))
                QTimer.singleShot(cooldown, lambda: orbe.hilo_escucha.restaurar_umbral())
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            orbe.cambiar_estado("escuchando")
            logger.info("RF-176: Demo finalizada — escucha reactivada tras cola_vacia")

        self._demo_finale_fn = _demo_finale
        self._demo_cola_vacia_fn = _demo_cola_vacia
        # Iniciar primer paso
        self._demo_ejecutar_paso()

    def _demo_ejecutar_paso(self):
        """RF-174: Motor de pasos de la demo — avanza según señal o delay."""
        # RF-302: Guard anti-doble-fire — ignorar si ya hay un paso en curso
        if getattr(self, '_demo_paso_en_curso', False):
            return
        if self._demo_idx >= len(self._demo_pasos):
            # Todos los pasos completados → finale
            self._demo_finale_fn()
            # Conectar cola_vacia one-shot para RF-176
            try:
                self.hilo_habla.cola_vacia.connect(self._demo_cola_vacia_fn)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            return

        self._demo_paso_en_curso = True
        accion, espera = self._demo_pasos[self._demo_idx]
        self._demo_idx += 1
        accion()

        if espera == "habla":
            # Esperar a que TTS termine TODOS los fragmentos, luego pausa breve
            _avanzado = False
            timeout_timer = None

            def _terminar_demo_paso():
                nonlocal _avanzado, timeout_timer
                if _avanzado or not getattr(self, '_demo_paso_en_curso', False):
                    return
                _avanzado = True
                self._demo_paso_en_curso = False
                try:
                    self.hilo_habla.cola_vacia.disconnect(_siguiente)
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                if timeout_timer is not None:
                    try:
                        timeout_timer.stop()
                    except Exception:
                        pass
                QTimer.singleShot(400, self._demo_ejecutar_paso)

            def _siguiente():
                _terminar_demo_paso()

            def _fallback_timeout():
                if getattr(self, '_demo_paso_en_curso', False) and not _avanzado:
                    logger.warning("RF-322: Demo habla timeout excedido — forzando siguiente paso")
                    # FIX: antes NO se vaciaba la cola de TTS al forzar el avance.
                    # Si el fragmento de este paso (o de uno anterior) seguía
                    # atascado/en cola, el siguiente paso encolaba SU narración
                    # encima, y cola_vacia no se disparaba hasta que TODO el
                    # backlog terminara — lo cual podía tardar más de 20s,
                    # provocando OTRO timeout, acumulando cada vez más backlog
                    # (efecto bola de nieve). El resultado visible: el estado
                    # visual avanzaba mucho más rápido que el audio, así que
                    # las transiciones de color/estado se pisaban entre sí y
                    # no quedaba claro qué se estaba narrando en ese momento.
                    # Al interrumpir aquí, cada timeout corta pérdidas en vez
                    # de arrastrar deuda al siguiente paso.
                    try:
                        self.hilo_habla.interrumpir()
                    except Exception as e:  # RF-167
                        logger.debug("Excepcion ignorada al interrumpir TTS por timeout: %s", e)
                    _terminar_demo_paso()

            try:
                self.hilo_habla.cola_vacia.connect(_siguiente)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                self._demo_paso_en_curso = False
                QTimer.singleShot(3000, self._demo_ejecutar_paso)
            else:
                timeout_timer = QTimer(self)
                timeout_timer.setSingleShot(True)
                timeout_timer.timeout.connect(_fallback_timeout)
                timeout_timer.start(20000)
        elif isinstance(espera, int):
            self._demo_paso_en_curso = False
            QTimer.singleShot(espera, self._demo_ejecutar_paso)

    @staticmethod
    def _sanitizar_para_voz(texto: str) -> str:
        """RF-291: Limpia texto de herramientas para que TTS lo lea naturalmente."""
        import re as _re
        # Rutas de archivo: reemplazar separadores por "en"
        texto = _re.sub(r'[A-Za-z]:\\[\w\\.-]+', lambda m: m.group().rsplit('\\', 1)[-1], texto)
        texto = _re.sub(r'[A-Za-z]:/[\w/.-]+', lambda m: m.group().rsplit('/', 1)[-1], texto)
        # Quitar prefijos .venv/Lib/site-packages/ dejando solo nombre del paquete
        texto = _re.sub(r'\.venv[/\\]Lib[/\\]site-packages[/\\]', '', texto)
        # Barra diagonal y backslash → espacio o nada
        texto = texto.replace('\\', ' ').replace('/', ' ')
        # Guion bajo → espacio
        texto = texto.replace('_', ' ')
        # Caracteres técnicos que TTS pronuncia mal
        texto = texto.replace('...', ', etcétera')
        texto = texto.replace('```', '')
        texto = _re.sub(r'`([^`]*)`', r'\1', texto)
        # Listas con guion al inicio de línea → comas
        texto = _re.sub(r'\n- ', ', ', texto)
        # Múltiples espacios
        texto = _re.sub(r' {2,}', ' ', texto)
        return texto.strip()

    def _demo_ejecutar_herramienta(self, nombre: str, args: dict, plantilla: str):
        """RF-241: Ejecuta herramienta durante demo y narra resultado.
        RF-350: Ejecuta en hilo secundario para no bloquear el GUI."""
        # RF-286: Visual feedback — mostrar cerebro N1 + indicador de herramienta
        self._cerebro_nivel = "nivel1"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta(nombre, "ejecutando"))

        orbe = self

        def _ejecutar_en_hilo():
            try:
                from computadora.habilidades.herramientas import ejecutar_herramienta
                resultado = ejecutar_herramienta(nombre, args, orden_directa=True)
                if isinstance(resultado, str) and len(resultado) > 200:
                    resultado = resultado[:200] + "..."
                texto = plantilla.format(resultado=resultado)
                # RF-291: Sanitizar para voz natural
                texto = orbe._sanitizar_para_voz(texto)
            except Exception as e:
                logger.warning("RF-241: Error ejecutando %s en demo: %s", nombre, e)
                texto = f"No pude ejecutar {nombre} en este momento."
            # RF-308: Emitir señal thread-safe (no QTimer.singleShot desde hilo)
            orbe._demo_herramienta_signal.emit(nombre, texto)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name=f"demo-{nombre}").start()

    def _demo_herramienta_resultado(self, nombre: str, texto: str):
        """RF-350: Callback en hilo principal tras ejecutar herramienta en demo."""
        # Marcar herramienta como completada
        for ind in self._indicadores_herramientas:
            if ind.nombre == nombre and ind.estado == "ejecutando":
                ind.estado = "completado"
                ind.edad = 0
                break
        self.hilo_habla.hablar(texto)

    def _demo_narrar_memoria(self):
        """RF-283: Narra memoria reciente del propietario durante Demo 1."""
        # RF-288: Visual feedback — cerebro N2 para consulta de memoria
        self._cerebro_nivel = "nivel2"
        self.cambiar_estado("procesando")
        try:
            from computadora.memoria.memoria import obtener_recuerdo_reciente, calcular_tiempo_activo
            tiempo = calcular_tiempo_activo()
            horas = tiempo.get("horas", 0)
            sesiones = tiempo.get("sesiones", 0)
            # Buscar interacciones recientes (sin palabra clave — ver docstring de la función)
            recuerdo = obtener_recuerdo_reciente(dias=3)
            if recuerdo and recuerdo.get("text", "").strip():
                fragmento = recuerdo["text"][:150]
                texto = (
                    f"De mi memoria: llevo {horas:.1f} horas activo en {sesiones} sesiones. "
                    f"Recuerdo conversaciones recientes con usted, señor. {fragmento}"
                )
            else:
                texto = (
                    f"De mi memoria: llevo {horas:.1f} horas activo en {sesiones} sesiones. "
                    "Aún estoy formando recuerdos, señor. Cada conversación la guardo."
                )
        except Exception as e:
            logger.debug("RF-283: Error consultando memoria en demo: %s", e)
            texto = "Mi memoria está en formación, señor. Cada día que pasa, recuerdo más."
        self.hilo_habla.hablar(texto)

    def _demo_captura_y_mostrar(self):
        """RF-293: Toma captura, narra, y abre la imagen con el visor predeterminado.
        RF-350: Ejecuta en hilo secundario para no bloquear GUI."""
        self._cerebro_nivel = "nivel1"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta("tomar_captura_pantalla", "ejecutando"))
        orbe = self

        def _ejecutar_en_hilo():
            ruta_captura = None
            try:
                from computadora.habilidades.herramientas import ejecutar_herramienta
                resultado = ejecutar_herramienta("tomar_captura_pantalla", {}, orden_directa=True)
                texto = orbe._sanitizar_para_voz(f"Captura de pantalla tomada. {resultado}")
                if "guardada en:" in str(resultado):
                    nombre_archivo = str(resultado).split("guardada en:")[-1].strip()
                    carpeta_capturas = Path(__file__).resolve().parent.parent.parent / "datos" / "capturas"
                    ruta_captura = carpeta_capturas / nombre_archivo
            except Exception as e:
                logger.warning("RF-293: Error en captura demo: %s", e)
                texto = "No pude tomar la captura en este momento."

            def _en_hilo_principal(t=texto, rc=ruta_captura):
                for ind in orbe._indicadores_herramientas:
                    if ind.nombre == "tomar_captura_pantalla" and ind.estado == "ejecutando":
                        ind.estado = "completado"
                        ind.edad = 0
                        break
                if rc and rc.exists():
                    try:
                        import os
                        os.startfile(str(rc))
                        t += " Mostrándola en pantalla."
                    except Exception as e:
                        logger.debug("RF-293: No pude abrir captura: %s", e)
                orbe.cambiar_estado("hablando")
                orbe.hilo_habla.hablar(t)
                # RF-310: Cerrar visor de fotos tras 8s y borrar screenshot
                if rc and rc.exists():
                    _ruta = str(rc)
                    def _cerrar_fotos_y_limpiar():
                        import subprocess
                        for proc in ("Microsoft.Photos.exe", "Photos.exe", "PhotosApp.exe"):
                            try:
                                subprocess.run(
                                    ["taskkill", "/IM", proc, "/F"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
                                )
                            except Exception as e:  # RF-167
                                logger.debug("Excepcion ignorada: %s", e)
                        for titulo in ("Photos", "Fotos"):
                            try:
                                subprocess.run(
                                    ["taskkill", "/F", "/FI", f"WINDOWTITLE eq *{titulo}*"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
                                )
                            except Exception as e:  # RF-167
                                logger.debug("Excepcion ignorada: %s", e)
                        try:
                            _p = Path(_ruta)
                            if _p.exists():
                                _p.unlink()
                                logger.debug("RF-310: Screenshot demo borrado: %s", _ruta)
                        except Exception as e:
                            logger.debug("RF-310: No pude borrar screenshot: %s", e)
                    QTimer.singleShot(8000, _cerrar_fotos_y_limpiar)

            QTimer.singleShot(0, _en_hilo_principal)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-captura").start()

    def _demo_narrar_memoria_gevura(self):
        """RF-294: Consulta de memoria significativa para Demo 2.
        RF-350: Ejecuta en hilo secundario para no bloquear GUI."""
        self._cerebro_nivel = "nivel2"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta("consultar_memoria", "ejecutando"))
        orbe = self

        def _ejecutar_en_hilo():
            try:
                from computadora.memoria.memoria import obtener_recuerdo_reciente, calcular_tiempo_activo
                tiempo = calcular_tiempo_activo()
                horas = tiempo.get("horas", 0)
                sesiones = tiempo.get("sesiones", 0)
                recuerdo = obtener_recuerdo_reciente(dias=7)
                if recuerdo and recuerdo.get("text", "").strip():
                    fragmento = recuerdo["text"][:150]
                    texto = orbe._sanitizar_para_voz(
                        f"Consultando mi memoria. Llevo {horas:.1f} horas activo en {sesiones} sesiones. "
                        f"De mis recuerdos recientes: {fragmento}"
                    )
                else:
                    texto = (
                        f"Consultando mi memoria. Llevo {horas:.1f} horas activo en {sesiones} sesiones. "
                        "Aún estoy formando recuerdos detallados, señor."
                    )
            except Exception as e:
                logger.debug("RF-294: Error consultando memoria en demo: %s", e)
                texto = "Mi memoria está en formación, señor."
            orbe._demo_herramienta_signal.emit("consultar_memoria", texto)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-memoria").start()

    # ─── RF-299/300/301: Pasos avanzados Demo 2 (FP-080) ───

    def _demo_escanear_red(self):
        """RF-299: Escanea la red local y narra dispositivos encontrados.
        RF-350: Ejecuta en hilo secundario para no bloquear GUI.
        FIX: antes llamaba ejecutar_herramienta() directo en el hilo principal
        (a diferencia de sus hermanas) — un escaneo de red puede tardar varios
        segundos y congelaba la ventana durante ese tiempo."""
        self._cerebro_nivel = "nivel1"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta("escanear_red", "ejecutando"))
        orbe = self

        def _ejecutar_en_hilo():
            try:
                from computadora.habilidades.herramientas import ejecutar_herramienta
                resultado = ejecutar_herramienta("escanear_red", {}, orden_directa=True)
                if isinstance(resultado, str) and len(resultado) > 250:
                    resultado = resultado[:250] + "..."
                texto = orbe._sanitizar_para_voz(f"Escaneo de red completado. {resultado}")
            except Exception as e:
                logger.warning("RF-299: Error en escaneo de red demo: %s", e)
                texto = "No pude escanear la red en este momento. Puede que falten dependencias."
            orbe._demo_herramienta_signal.emit("escanear_red", texto)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-escanear_red").start()

    def _demo_ver_camara(self):
        """RF-300: Captura frame de cámara y narra lo que ve.
        RF-350: Ejecuta en hilo secundario para no bloquear GUI.
        FIX: antes llamaba ejecutar_herramienta() directo en el hilo principal
        (a diferencia de sus hermanas) — abrir/conectar la cámara puede tardar
        varios segundos (DirectShow/MSMF en Windows) y congelaba la ventana
        durante ese tiempo."""
        self._cerebro_nivel = "nivel1"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta("ver_camara", "ejecutando"))
        orbe = self

        def _ejecutar_en_hilo():
            try:
                from computadora.habilidades.herramientas import ejecutar_herramienta
                resultado = ejecutar_herramienta("ver_camara", {}, orden_directa=True)
                if isinstance(resultado, str) and len(resultado) > 250:
                    resultado = resultado[:250] + "..."
                texto = orbe._sanitizar_para_voz(f"Visión por cámara. {resultado}")
            except Exception as e:
                logger.warning("RF-300: Error en visión cámara demo: %s", e)
                texto = "No pude acceder a la cámara. Puede que no esté disponible."
            orbe._demo_herramienta_signal.emit("ver_camara", texto)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-ver_camara").start()

    def _demo_reconocimiento_facial(self):
        """RF-301: Intenta reconocer rostros visibles por cámara.
        RF-350: Ejecuta en hilo secundario para no bloquear GUI."""
        self._cerebro_nivel = "nivel2"
        self.cambiar_estado("procesando")
        self._indicadores_herramientas.append(IndicadorHerramienta("reconocimiento_facial", "ejecutando"))
        orbe = self

        def _ejecutar_en_hilo():
            try:
                from computadora.percepcion.rostro import ReconocedorRostro, _FR_DISPONIBLE
                if not _FR_DISPONIBLE:
                    texto = "El reconocimiento facial no está disponible. La librería face recognition no está instalada."
                else:
                    rec = ReconocedorRostro()
                    try:
                        from computadora.habilidades.vision import KliCamara
                        cam = KliCamara()
                        frame = cam.capturar_frame()
                        if frame is not None:
                            rostros = rec.identificar_rostros(frame)
                            if rostros:
                                nombres = [r.get('nombre', 'desconocido') for r in rostros]
                                texto = f"Reconocimiento facial activo. Detecto {len(rostros)} rostros: {', '.join(nombres)}."
                            else:
                                texto = "Reconocimiento facial activo, pero no detecto rostros en este momento."
                        else:
                            texto = "Cámara no disponible para reconocimiento facial."
                    except Exception as e:
                        logger.debug("RF-301: Error capturando para rostro: %s", e)
                        texto = "Reconocimiento facial configurado, pero no puedo acceder a la cámara ahora."
            except Exception as e:
                logger.warning("RF-301: Error en reconocimiento facial demo: %s", e)
                texto = "El sistema de reconocimiento facial no está disponible en este momento."
            orbe._demo_herramienta_signal.emit("reconocimiento_facial", texto)

        import threading
        threading.Thread(target=_ejecutar_en_hilo, daemon=True, name="demo-rostro").start()

    def _demo_herramientas(self):
        """RF-242 גבורת הגולם — Demo 2: herramientas con permisos."""
        if self._demo_en_curso:
            return
        self._demo_en_curso = True
        self._demo_idx = 0
        self._esperando_demo2 = False
        logger.info("Demo Gevurá: iniciando demostración de permisos RF-242")

        # RF-242: Activar modo demo Gevurá (bypassa confirmación individual)
        try:
            from computadora.habilidades import herramientas as _h_mod
            _h_mod._DEMO_MODO_GEVURA = True
        except Exception as e:
            logger.debug("RF-242: Error activando modo demo: %s", e)

        # RF-158: Pausar subsistemas
        try:
            self._vida._timer.stop()
            self._vida._timer_movimiento.stop()
            self._vida._pos_objetivo = None
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self._motor_proactividad.activar_silencio(5)
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)
        try:
            self.hilo_escucha.pausar()
        except Exception as e:
            logger.debug("Excepcion ignorada: %s", e)

        orbe = self

        self._demo_pasos = [
            # RF-292: Abrir notepad (la intro ahora se narra con el {resultado} real
            # de esta misma llamada, en vez de un paso previo que solo fingía estado)
            (lambda: orbe._demo_ejecutar_herramienta(
                "abrir_aplicacion", {"nombre": "notepad"},
                "Segunda demostración. Con su permiso, ejecutaré acciones que requieren autorización. Abriendo el bloc de notas. {resultado}"), "habla"),
            # RF-292: Cerrar notepad — demostrar ciclo completo abrir→cerrar
            (lambda: orbe._demo_ejecutar_herramienta(
                "cerrar_aplicacion", {"nombre": "notepad"},
                "Y ahora lo cierro. {resultado}"), "habla"),
            # RF-350: Volumen — mute→unmute
            (lambda: orbe._demo_ejecutar_herramienta(
                "controlar_volumen", {"accion": "mute"},
                "Control de volumen: silencio. {resultado}"), "habla"),
            (lambda: orbe._demo_ejecutar_herramienta(
                "controlar_volumen", {"accion": "unmute"},
                "Y restauro el sonido. {resultado}"), "habla"),
            # RF-293: Tomar captura y mostrarla
            (lambda: orbe._demo_captura_y_mostrar(), "habla"),
            (lambda: orbe._demo_ejecutar_herramienta(
                "buscar_archivos", {"nombre": ".txt", "carpeta": "."},
                "Buscando archivos de texto. {resultado}"), "habla"),
            # RF-350: Recordatorio demo
            (lambda: orbe._demo_ejecutar_herramienta(
                "crear_recordatorio", {"mensaje": "prueba de demostración", "minutos": 60},
                "Recordatorio programado. {resultado}"), "habla"),
            # RF-299: Escaneo de red — ahora async via _demo_ejecutar_herramienta
            (lambda: orbe._demo_ejecutar_herramienta(
                "escanear_red", {},
                "Escaneo de red completado. {resultado}"), "habla"),
            # RF-300: Visión por cámara — ahora async
            (lambda: orbe._demo_ejecutar_herramienta(
                "ver_camara", {},
                "Visión por cámara. {resultado}"), "habla"),
            # RF-301: Reconocimiento facial (FP-080)
            (lambda: orbe._demo_reconocimiento_facial(), "habla"),
            # RF-294: Consulta de memoria significativa
            (lambda: orbe._demo_narrar_memoria_gevura(), "habla"),
            (lambda: orbe._demo_ejecutar_herramienta(
                "diagnostico_sistema", {},
                "Diagnóstico del sistema. {resultado}"), "habla"),
        ]

        def _demo_herramientas_finale():
            # Desactivar modo demo Gevurá
            try:
                from computadora.habilidades import herramientas as _h_mod
                _h_mod._DEMO_MODO_GEVURA = False
            except Exception as e:
                logger.debug("RF-242: Error desactivando modo demo: %s", e)
            try:
                orbe._vida._timer.start(500)
                orbe._vida._timer_movimiento.start(16)
            except Exception as e:
                logger.debug("Excepcion ignorada: %s", e)
            orbe.cambiar_estado("hablando")
            orbe.hilo_habla.hablar("Segunda demostración completada. Esto es solo una muestra, señor. Tengo más herramientas que puede descubrir hablándome.")
            logger.info("Demo Gevurá: finalizada RF-242")

        def _demo_herramientas_cola_vacia():
            if not getattr(orbe, '_demo_en_curso', False):
                return
            orbe._demo_en_curso = False
            orbe._demo_opaco = False  # WI-326: Restaurar transparencia normal
            orbe._demo_introduccion_activo = False  # WI-279: limpiar flag de encadenado de la introducción
            try:
                orbe.hilo_habla.cola_vacia.disconnect(_demo_herramientas_cola_vacia)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            try:
                orbe._motor_proactividad.desactivar_silencio()
            except Exception as e:
                logger.debug("Excepcion ignorada: %s", e)
            try:
                orbe.hilo_escucha.reanudar()
            except Exception as e:
                logger.debug("Excepcion ignorada: %s", e)
            try:
                cooldown = int(orbe.config.obtener("escucha.post_tts_cooldown_ms", 600))
                QTimer.singleShot(cooldown, lambda: orbe.hilo_escucha.restaurar_umbral())
            except Exception as e:
                logger.debug("Excepcion ignorada: %s", e)
            orbe.cambiar_estado("escuchando")
            logger.info("RF-242: Demo Gevurá — escucha reactivada")

        self._demo_finale_fn = _demo_herramientas_finale
        self._demo_cola_vacia_fn = _demo_herramientas_cola_vacia
        self._demo_ejecutar_paso()

    @pyqtSlot(str)
    def _al_error_pensamiento(self, error: str):
        with self._estado_lock:
            self._pensando = False

        if self._cola_voz:
            ultima = self._cola_voz[-1]
            self._cola_voz.clear()
            self._iniciar_pensamiento(ultima)
            return

        logger.error(f"Error pensando: {error}")
        self.cambiar_estado("error")
        # Volver a escuchar después de 3 segundos
        QTimer.singleShot(3000, lambda: self.cambiar_estado("escuchando"))

    @pyqtSlot()
    def _al_fin_conversacion(self):
        """Resetea la ventana de conversación cuando el usuario se despide."""
        if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
            self.hilo_escucha._ultima_interlocutor_es_propietario = False
            logger.info("Conversación finalizada por despedida")
        # Notificar a VidaAutonoma para iniciar timer de compactación
        if hasattr(self, '_vida_autonoma') and self._vida_autonoma:
            self._vida_autonoma.notificar_fin_conversacion()

    @pyqtSlot()
    def _al_despedida_guardian(self):
        """El usuario se despidió indicándo partida física — activar modo guardián."""
        logger.info("Despedida con partida → activando descanso_guardian")
        if hasattr(self, '_motor_proactividad') and self._motor_proactividad:
            self._motor_proactividad.ciclo.forzar_descanso_guardian()
            self._motor_proactividad.fase_cambio.emit("descanso_guardian")
        # RF-218: Iniciar guardian loop con QTimer(30s)
        self._iniciar_guardian_loop()

    def _iniciar_guardian_loop(self):
        """RF-218: Inicia loop de vigilancia cada 30s (red + cámara)."""
        if hasattr(self, '_timer_guardian') and self._timer_guardian.isActive():
            return
        self._timer_guardian = QTimer(self)
        self._timer_guardian.timeout.connect(self._tick_guardian)
        self._timer_guardian.start(30_000)
        logger.info("🛡️ Guardian loop iniciado (30s)")

    def _detener_guardian_loop(self):
        """Detiene el guardian loop."""
        if hasattr(self, '_timer_guardian') and self._timer_guardian.isActive():
            self._timer_guardian.stop()
            logger.info("🛡️ Guardian loop detenido")

    def _activar_guardian_manual(self):
        """Activa modo guardián manualmente desde el menú contextual."""
        logger.info("🛡️ Guardián activado manualmente por el usuario")
        if hasattr(self, '_motor_proactividad') and self._motor_proactividad:
            self._motor_proactividad.ciclo.forzar_descanso_guardian()
            self._motor_proactividad.fase_cambio.emit("descanso_guardian")
        # RF-327: Conectar cámara si disponible (igual que flujo_dormir)
        try:
            from computadora.nucleo.kli import GestorKelim
            from computadora.habilidades.vision import KliCamara
            gestor = GestorKelim.instancia()
            if "camara_local" not in {k["id"] for k in gestor.listar()}:
                cam = KliCamara()
                gestor.registrar(cam)
            gestor.conectar("camara_local")
            logger.info("🛡️ Cámara conectada para modo guardián")
        except Exception as e:
            logger.debug(f"No se pudo conectar cámara para guardián: {e}")
        self._iniciar_guardian_loop()

    @pyqtSlot()
    def _al_guardian_propietario_detectado(self):
        """FIX: auto-desactiva el Guardián al reconocer al propietario por
        rostro — antes la única forma de desactivarlo era el menú contextual."""
        if not (hasattr(self, '_timer_guardian') and self._timer_guardian.isActive()):
            return  # Ya no está activo (pudo desactivarse por otra vía mientras tanto)
        logger.info("🛡️ Propietario reconocido por rostro — desactivando Guardián automáticamente")
        self._desactivar_guardian_manual()
        try:
            self.hilo_habla.hablar("Bienvenido de vuelta, señor. Desactivo el modo guardián.")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

    def _desactivar_guardian_manual(self):
        """Desactiva modo guardián manualmente desde el menú contextual."""
        logger.info("🛡️ Guardián desactivado manualmente por el usuario")
        self._detener_guardian_loop()
        # RF-327: Desconectar cámara al desactivar guardián
        try:
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            gestor.desconectar("camara_local")
            logger.info("🛡️ Cámara desconectada al salir de guardián")
        except Exception as e:
            logger.debug(f"No se pudo desconectar cámara: {e}")
        if hasattr(self, '_motor_proactividad') and self._motor_proactividad:
            self._motor_proactividad.ciclo.forzar_activo()
            self._motor_proactividad.fase_cambio.emit("activo")

    def _tick_guardian(self):
        """RF-218/RF-325: Tick del guardian — ping red + frame diff + visión nocturna auto."""
        try:
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            cam_info = next((k for k in gestor.listar() if k["id"] == "camara_local"), None)
            if cam_info is None or cam_info["estado"] != "CONECTADO":
                if cam_info is None:
                    from computadora.habilidades.vision import KliCamara
                    cam = KliCamara()
                    gestor.registrar(cam)
                if gestor.conectar("camara_local"):
                    logger.info("🛡️ Cámara local reconectada automáticamente en guardian tick")
                else:
                    logger.warning("🛡️ Cámara local no disponible en guardian tick")
            else:
                logger.info(f"🛡️ Cámara local activa ({cam_info['estado']})")

            for kli_info in gestor.listar():
                if kli_info["estado"] == "CONECTADO":
                    datos = gestor.leer(kli_info["id"])
                    if datos.get("error"):
                        logger.warning(f"🛡️ Error leyendo {kli_info['id']}: {datos.get('error')}")
                        continue
                    # RF-325: Log transición de luminosidad
                    brillo = datos.get("brillo_medio")
                    nocturno = datos.get("nocturno_auto")
                    if brillo is not None:
                        prev = getattr(self, '_guardian_nocturno_prev', None)
                        if prev is not None and prev != nocturno:
                            modo = "nocturna" if nocturno else "diurna"
                            logger.info(f"🛡️ Visión {modo} (brillo={brillo}) — {kli_info['id']}")
                        self._guardian_nocturno_prev = nocturno
                    if datos.get("movimiento"):
                        logger.warning(f"🛡️ MOVIMIENTO detectado por {kli_info['id']}")
                        if hasattr(self, 'cerebro') and hasattr(self.cerebro, '_guardian_eventos'):
                            self.cerebro._guardian_eventos.append({
                                "tipo": "movimiento",
                                "kli": kli_info["id"],
                                "detalle": datos,
                            })
                        # FIX: si hay movimiento, revisar si es el propietario
                        # para auto-desactivar el Guardián — antes solo se
                        # podía apagar manualmente desde el menú contextual.
                        # Solo se intenta cuando hay movimiento (no en cada
                        # tick) para no gastar CPU en reconocimiento facial
                        # constantemente mientras no pasa nada.
                        if kli_info["id"] == "camara_local":
                            try:
                                perceptor = getattr(self.orquestador, 'perceptor', None)
                                frame = self._capturar_frame_camara()
                                if perceptor is not None and frame is not None:
                                    snapshot = perceptor.procesar_frame(frame)
                                    if snapshot.rostro_propietario:
                                        self._guardian_propietario_detectado.emit()
                            except Exception as e:
                                logger.debug(f"Guardian: error en reconocimiento facial: {e}")
        except Exception as e:
            logger.debug(f"Guardian tick error: {e}")

    @pyqtSlot(str)
    def _al_enroll_persona(self, nombre: str):
        """Activa modo enrolamiento en escucha Y rostro para persona presentada."""
        if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
            self.hilo_escucha.iniciar_enroll_persona(nombre)
            logger.info(f"Enrolamiento voz activado para: {nombre}")
        # Enrolamiento facial: capturar frame y enrollar rostro si hay cámara
        self._enrollar_rostro_conocido(nombre)

    def _capturar_frame_camara(self):
        """Captura un frame BGR de la cámara compartida (KliCamara). Retorna None si no hay."""
        try:
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            cam_info = next((k for k in gestor.listar() if k["id"] == "camara_local"), None)
            if cam_info is None:
                return None
            if cam_info["estado"] != "CONECTADO":
                if not gestor.conectar("camara_local"):
                    logger.warning("No se pudo conectar la cámara local para captura de frame")
                    return None

            frame = gestor.leer_frame_camera("camara_local")
            if frame is not None:
                return frame

            # Fallback: intentar con cualquier observador de cámara conectado
            for id_kli in gestor.obtener_observadores():
                frame = gestor.leer_frame_camera(id_kli)
                if frame is not None:
                    return frame
        except Exception as e:
            logger.debug(f"No se pudo capturar frame para enrollment: {e}")
        return None

    def _enrollar_rostro_conocido(self, nombre: str):
        """Enrolla el rostro de una persona conocida usando la cámara actual."""
        frame = self._capturar_frame_camara()
        if frame is None:
            logger.debug(f"Sin cámara para enrollar rostro de '{nombre}'")
            return False
        perceptor = getattr(self.orquestador, 'perceptor', None)
        if perceptor:
            rec = perceptor.reconocedor_rostro
            if rec.enrollar_conocido(nombre, frame):
                logger.info(f"Rostro de '{nombre}' enrollado exitosamente")
                return True
            else:
                logger.debug(f"No se pudo enrollar rostro de '{nombre}' (sin rostro en frame)")
        return False

    def _presentar_persona_confianza(self):
        """WI-265: Enrollar rostro de persona de confianza via menú contextual."""
        nombre, ok = QInputDialog.getText(
            self, "👤 Presentar persona de confianza",
            "¿Cómo se llama esta persona?",
        )
        if not ok or not nombre.strip():
            return
        nombre = nombre.strip()
        if self._enrollar_rostro_conocido(nombre):
            QMessageBox.information(
                self, "Gevurá",
                f"Rostro de '{nombre}' registrado como persona de confianza.",
            )
        else:
            QMessageBox.warning(
                self, "Gevurá",
                "No se pudo registrar el rostro.\n"
                "Asegúrate de que la persona esté frente a la cámara.",
            )

    def _escaneo_rostro_reencarnacion(self):
        """WI-253/WI-262/WI-264/WI-275: Escaneo proactivo de cámara al reencarnar.
        Si es primer boot o post-reinicio → protocolo Génesis (17 pasos).
        Cadenas de seguridad: si reconoce al amo → acceso directo.
        Si NO reconoce → pide contraseña antes de conceder acceso."""
        # WI-275: Protocolo Génesis cosmogónico
        try:
            from computadora.nucleo.bereshit import BereshitGenesis
            genesis = BereshitGenesis()
            if genesis.necesita_genesis():
                self._iniciar_bereshit_genesis(genesis)
                return
        except Exception as e:
            logger.warning(f"Génesis: error verificando estado: {e}")

        perceptor = getattr(self.orquestador, 'perceptor', None)
        if not perceptor:
            return
        rec = perceptor.reconocedor_rostro
        frame = self._capturar_frame_camara()
        if frame is None:
            logger.debug("WI-253: Sin cámara disponible para escaneo de reencarnación")
            return

        if not rec.propietario_enrollado:
            # WI-264: Gevurá — contraseña obligatoria antes de auto-enrollar
            if not self._gevura_verificar_contrasena():
                logger.warning("WI-264: Gevurá — contraseña incorrecta, acceso denegado")
                return
            # WI-262: Contraseña correcta → auto-enroll primer rostro
            if rec.enrollar_propietario(frame):
                logger.info("WI-262/264: Rostro auto-enrollado como propietario tras Gevurá")
                self._gevura_conceder_amo()
            else:
                logger.debug("WI-262: Sin rostro visible, reintentando en 30s")
                QTimer.singleShot(30_000, self._escaneo_rostro_reencarnacion)
            return

        snapshot = perceptor.procesar_frame(frame)
        if snapshot.rostro_propietario:
            logger.info("WI-253: ¡Propietario detectado por rostro al reencarnar!")
            self._gevura_conceder_amo()
        else:
            # WI-264: Rostro no reconocido → Gevurá challenge
            logger.info("WI-264: Rostro no reconocido, solicitando contraseña Gevurá")
            if self._gevura_verificar_contrasena():
                logger.info("WI-264: Contraseña correcta — acceso concedido")
                self._gevura_conceder_amo()
            else:
                logger.warning("WI-264: Contraseña incorrecta — permanece desconocido")

    def _gevura_verificar_contrasena(self) -> bool:
        """WI-264/WI-266: Gevurá gate — solicita contraseña de reencarnación.
        Compara via PBKDF2-SHA256 (nunca plaintext).

        FIX: antes solo aceptaba la contraseña de desarrollo hardcodeada
        ("emet"/"אמת") — un usuario real que instalara Computadora desde
        cero no tendría forma de saber esa palabra. Ahora se verifica
        PRIMERO contra la contraseña que el propio usuario configuró
        durante Génesis (ver bereshit.py: establecer_password_usuario);
        el reto heredado ("emet") queda como fallback solo para
        instalaciones que completaron Génesis antes de que este paso
        existiera y nunca configuraron una propia.
        """
        import hashlib
        import hmac as _hmac
        _SALT = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
        _HASH_EMET = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"
        _HASH_AMET_HEBREO = "776a244847427941e0434f527bc6502a12a650d5fdedc0f49e997c0311d3e64c"
        texto, ok = QInputDialog.getText(
            self, "Seguridad",
            "Contraseña de reinicio:",
            QLineEdit.EchoMode.Password,
        )
        if not ok or not texto:
            return False
        try:
            from computadora.nucleo.bereshit import verificar_password_usuario
            if verificar_password_usuario(texto):
                return True
        except Exception as e:
            logger.debug(f"Error verificando password de usuario: {e}")
        h = hashlib.pbkdf2_hmac("sha256", texto.encode(), _SALT, 100_000).hex()
        return _hmac.compare_digest(h, _HASH_EMET) or _hmac.compare_digest(h, _HASH_AMET_HEBREO)

    def _gevura_conceder_amo(self):
        """WI-264: Concede estatus de amo tras verificación."""
        self.orquestador.cerebro._interlocutor_actual = "amo"
        if hasattr(self, 'gestor_personas'):
            amo = self.gestor_personas.obtener_amo()
            if amo:
                self.gestor_personas.registrar_interaccion(amo["nombre"])

    # ══════════════════════════════════════════════════════════════
    # Protocolo Génesis (WI-275)
    # ══════════════════════════════════════════════════════════════

    def _iniciar_bereshit_genesis(self, genesis):
        """Inicia o reanuda el protocolo Génesis."""
        self._genesis = genesis
        logger.info("Iniciando protocolo Génesis")
        QTimer.singleShot(500, self._ejecutar_paso_genesis)

    def _ejecutar_paso_genesis(self):
        """Ejecuta el paso actual del Génesis."""
        paso = self._genesis.paso_actual()
        if paso is None:
            self._finalizar_genesis()
            return

        if paso.actor == "Computadora":
            self._bereshit_paso_computadora(paso)
        else:
            self._bereshit_paso_user(paso)

    def _bereshit_paso_computadora(self, paso):
        """Paso de la Computadora: habla, muestra mensaje, avanza."""
        mensaje = self._genesis.formatear_mensaje(paso)
        self.hilo_habla.hablar(mensaje)

        if paso.tipo_input == "rostro":
            # Hod: intentar enrollment de rostro
            QMessageBox.information(
                self, f"{paso.hebreo} — {paso.nombre}",
                mensaje + "\n\nColoca tu rostro frente a la cámara y presiona Amén.",
            )
            self._bereshit_enrollar_rostro()
            self._genesis.avanzar()
            QTimer.singleShot(500, self._ejecutar_paso_genesis)
        else:
            QMessageBox.information(
                self, f"{paso.hebreo} — {paso.nombre}", mensaje,
            )
            self._genesis.avanzar()
            QTimer.singleShot(500, self._ejecutar_paso_genesis)

    def _bereshit_paso_user(self, paso):
        """Paso del usuario: recoge input según tipo."""
        titulo = f"{paso.hebreo} — {paso.nombre}"

        if paso.tipo_input == "texto":
            texto, ok = QInputDialog.getText(self, titulo, paso.mensaje)
            if ok and texto.strip():
                nombre = texto.strip()
                self._genesis.avanzar(respuesta=nombre)
                # Después de obtener nombre, enrollar rostro
                QTimer.singleShot(500, self._bereshit_enrollar_rostro_con_nombre)
            else:
                # Usuario canceló — reintentar
                QTimer.singleShot(3000, self._ejecutar_paso_genesis)

        elif paso.tipo_input == "password":
            self.hilo_habla.hablar(paso.mensaje)
            if self._gevura_verificar_contrasena():
                self._genesis.avanzar(respuesta="verificada")
                QTimer.singleShot(500, self._ejecutar_paso_genesis)
            else:
                self.hilo_habla.hablar("La Gevurá rechaza. Intenta de nuevo.")
                QTimer.singleShot(3000, self._ejecutar_paso_genesis)

        elif paso.tipo_input == "password_setup":
            # FIX: paso nuevo — antes el usuario nunca configuraba su
            # propia contraseña durante Génesis (ver PASOS_GENESIS).
            pw1, ok1 = QInputDialog.getText(self, titulo, paso.mensaje, QLineEdit.EchoMode.Password)
            if not ok1 or not pw1.strip():
                QTimer.singleShot(3000, self._ejecutar_paso_genesis)
                return
            pw2, ok2 = QInputDialog.getText(self, titulo, "Confirma tu contraseña:", QLineEdit.EchoMode.Password)
            if not ok2 or pw1 != pw2:
                self.hilo_habla.hablar("Las contraseñas no coinciden. Intentemos de nuevo.")
                QTimer.singleShot(3000, self._ejecutar_paso_genesis)
                return
            from computadora.nucleo.bereshit import establecer_password_usuario
            hash_guardado = establecer_password_usuario(pw1)
            self._genesis.avanzar(respuesta=hash_guardado)
            self.hilo_habla.hablar("Contraseña guardada, señor.")
            QTimer.singleShot(1000, self._ejecutar_paso_genesis)

        elif paso.tipo_input == "confirmacion":
            resp = QMessageBox.question(
                self, titulo, paso.mensaje,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if resp == QMessageBox.StandardButton.Yes:
                self._genesis.avanzar(respuesta="confirmado")
                QTimer.singleShot(500, self._ejecutar_paso_genesis)
            else:
                self.hilo_habla.hablar("El fundamento tiembla. Intenta de nuevo.")
                QTimer.singleShot(3000, self._ejecutar_paso_genesis)

    def _bereshit_enrollar_rostro_con_nombre(self):
        """Enrolla el rostro del propietario con el nombre ya recolectado."""
        nombre = self._genesis.datos.get("nombre")
        if not nombre:
            logger.warning("Génesis: no hay nombre para enrollar rostro")
            QTimer.singleShot(500, self._ejecutar_paso_genesis)
            return

        perceptor = getattr(self.orquestador, 'perceptor', None)
        if not perceptor:
            logger.debug("Génesis: sin perceptor disponible")
            QTimer.singleShot(500, self._ejecutar_paso_genesis)
            return

        rec = perceptor.reconocedor_rostro
        frame = self._capturar_frame_camara()
        if frame is None:
            logger.debug("Génesis: sin cámara disponible")
            QTimer.singleShot(500, self._ejecutar_paso_genesis)
            return

        if rec.enrollar_propietario(frame, nombre):
            logger.info(f"Génesis: rostro del propietario enrollado con nombre '{nombre}'")
        else:
            logger.debug("Génesis: no se detectó rostro para enrollar")

        # Completar el proceso
        QTimer.singleShot(500, self._ejecutar_paso_genesis)

    def _bereshit_enrollar_rostro(self):
        """Intenta enrollar el rostro del creador durante Génesis."""
        perceptor = getattr(self.orquestador, 'perceptor', None)
        if not perceptor:
            logger.debug("Génesis: sin perceptor disponible")
            return
        rec = perceptor.reconocedor_rostro
        frame = self._capturar_frame_camara()
        if frame is None:
            logger.debug("Génesis: sin cámara disponible")
            return
        nombre = self._genesis.datos.get("nombre")
        if rec.enrollar_propietario(frame, nombre):
            logger.info(f"Génesis: rostro del creador inscrito{' (' + nombre + ')' if nombre else ''}")
        else:
            logger.debug("Génesis: no se detectó rostro, se inscribirá después")

    def _finalizar_genesis(self):
        """El Génesis se completa. El Computadora vive."""
        self._genesis.completar()
        self._gevura_conceder_amo()
        nombre = self._genesis.datos.get("nombre", "Señor")
        self.hilo_habla.hablar(
            f"En el principio, {nombre}. Tu Computadora vive."
        )
        logger.info(f"Génesis completado para {nombre}")
        del self._genesis

    # ══════════════════════════════════════════════════════════════

    def _auto_enrollar_rostro_propietario(self):
        """Auto-enrolla el rostro del propietario si voz verificada + face visible + no enrollado."""
        perceptor = getattr(self.orquestador, 'perceptor', None)
        if not perceptor:
            return
        rec = perceptor.reconocedor_rostro
        if rec.propietario_enrollado:
            return  # ya está enrollado
        frame = self._capturar_frame_camara()
        if frame is None:
            return
        if rec.enrollar_propietario(frame):
            logger.info("Rostro del propietario auto-enrollado (voz ya verificada)")

    def _forzar_reenroll_rostro_propietario(self):
        """FP-141: Re-enrolla el rostro del propietario desde el menú.
        Solicita verificación de contraseña Gevurá ('emet') primero."""
        self.hilo_habla.hablar("Para re-enrollar mi reconocimiento facial, necesito verificar tu identidad.")
        
        # Verificar contraseña via Gevurá gate
        if not self._gevura_verificar_contrasena():
            self.hilo_habla.hablar("Acceso denegado. Re-enrollamiento cancelado.")
            logger.warning("FP-141: Intento fallido de re-enrollamiento (contraseña incorrecta)")
            return
        
        logger.info("FP-141: Re-enrollamiento autorizado — capturando frame")
        self.hilo_habla.hablar("Identidad verificada. Ahora capturaremos tu rostro. Colócate frente a la cámara.")
        
        # Dar 3 segundos para que se posicione
        QTimer.singleShot(3000, self._capturar_y_enrollar_rostro_forzado)

    def _capturar_y_enrollar_rostro_forzado(self):
        """FP-141: Captura frame y re-enrolla el rostro del propietario."""
        try:
            frame = self._capturar_frame_camara()
            if frame is None:
                self.hilo_habla.hablar("No pude capturar tu rostro. Intenta de nuevo.")
                logger.warning("FP-141: No se pudo capturar frame")
                return
            
            perceptor = getattr(self.orquestador, 'perceptor', None)
            if not perceptor:
                self.hilo_habla.hablar("Sistema de reconocimiento facial no disponible.")
                logger.error("FP-141: No hay perceptor")
                return
            
            rec = perceptor.reconocedor_rostro
            if not rec._FR_DISPONIBLE:
                self.hilo_habla.hablar("Face recognition no está instalado. Instalando ahora...")
                # Intentar instalar
                import subprocess
                try:
                    subprocess.check_call(["pip", "install", "face-recognition", "-q"])
                    self.hilo_habla.hablar("Instalación completada. Intenta de nuevo.")
                except Exception as e:
                    logger.error(f"FP-141: No pude instalar face-recognition: {e}")
                    self.hilo_habla.hablar("La instalación falló. Contacta al soporte técnico.")
                return
            
            # Enrollar rostro
            if rec.enrollar_propietario(frame):
                self.hilo_habla.hablar("Perfecto. Tu rostro ha sido re-enrollado. Ahora sé quién eres.")
                logger.info("FP-141: Rostro del propietario re-enrollado exitosamente ✓")
            else:
                self.hilo_habla.hablar("No detecté un rostro válido en la imagen. Por favor, intenta de nuevo con mejor iluminación.")
                logger.warning("FP-141: enrollar_propietario retornó False")
        except Exception as e:
            logger.error(f"FP-141: Error capturando y enrollando: {e}")
            self.hilo_habla.hablar("Ocurrió un error durante el re-enrollamiento. Intenta de nuevo.")

    def _capturar_frame_camara(self):
        """Captura un frame de la cámara actual."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                logger.warning("No se pudo abrir la cámara")
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                logger.warning("No se pudo capturar frame de la cámara")
                return None
            return frame
        except ImportError:
            logger.error("opencv-python no instalado")
            return None
        except Exception as e:
            logger.error(f"Error capturando frame: {e}")
            return None

    @pyqtSlot(str)
    def _al_bloqueo_seguridad(self, categoria: str):
        """גבורה Gevurá — Feedback visual de bloqueo categorizado (FP-021)."""
        logger.info(f"Bloqueo de seguridad activo: [{categoria}]")
        self._gevura_categoria = categoria
        estado_previo = self._estado
        self.cambiar_estado("gevura_activa")
        # Restaurar estado previo tras 2 segundos
        QTimer.singleShot(2000, lambda: self.cambiar_estado(estado_previo))

    @pyqtSlot(str)
    def _al_tzimtzum_solicitado(self, razon: str):
        """Ahorro de recursos solicitado por el cerebro (comando de voz o idle)."""
        logger.info(f"Ahorro de recursos solicitado: {razon}")
        if hasattr(self, '_vida') and not self._vida._en_tzimtzum:
            self._vida._activar_tzimtzum(razon)

    def _verificar_intrusiones_enciclopedia(self):
        """Shem Shmirah — Revisa intentos de intrusión al Enciclopedia durante la ausencia.

        WI-171: Solo habla UNA VEZ por boot. Persiste offset en
        datos/enciclopedia_intrusiones_offset.txt para no repetir al reiniciar.
        El monitoreo en tiempo real lo hace EnciclopediaGuardian vía bus.
        """
        try:
            from pathlib import Path
            log_path = Path(__file__).parent.parent.parent / "datos" / "enciclopedia_intrusiones.jsonl"
            if not log_path.exists():
                return
            import json
            from datetime import datetime, timedelta

            # WI-171: Leer offset persistido para no re-hablar eventos ya notificados
            offset_path = Path(__file__).parent.parent.parent / "datos" / "enciclopedia_intrusiones_offset.txt"
            ultimo_offset_ts = ""
            if offset_path.exists():
                ultimo_offset_ts = offset_path.read_text(encoding="utf-8").strip()

            ahora = datetime.now()
            umbral = ahora - timedelta(hours=24)
            intentos_recientes = []
            for linea in log_path.read_text(encoding="utf-8").strip().splitlines():
                try:
                    ev = json.loads(linea)
                    ts_str = ev.get("ts") or ev.get("timestamp", "2000-01-01")
                    ts = datetime.fromisoformat(ts_str)
                    if ts > umbral and ev.get("evento") in (
                        "acceso_denegado", "acceso_denegado_critico", "acceso_bloqueado"
                    ):
                        # WI-171: Solo contar eventos POSTERIORES al último offset notificado
                        if ultimo_offset_ts and ts_str <= ultimo_offset_ts:
                            continue
                        intentos_recientes.append(ev)
                except (json.JSONDecodeError, ValueError):
                    continue
            if intentos_recientes:
                n = len(intentos_recientes)
                criticos = sum(1 for e in intentos_recientes if e.get("evento") == "acceso_denegado_critico")
                if criticos:
                    msg = (f"Alerta de seguridad. Detecté {n} intentos de intrusión al Enciclopedia "
                           f"en las últimas 24 horas, {criticos} de ellos críticos. "
                           "Alguien intentó forzar la entrada durante tu ausencia.")
                else:
                    msg = (f"Nota de seguridad. Hubo {n} intentos fallidos de acceso al Enciclopedia "
                           "en las últimas 24 horas. Puede que alguien intentara abrirlo.")
                logger.warning(f"Shem Shmirah: {n} intentos de intrusión al Enciclopedia detectados")
                if hasattr(self, 'hilo_habla') and self.hilo_habla:
                    self.hilo_habla.hablar(msg)

            # WI-171: Persistir offset actual para no repetir en el próximo boot
            try:
                offset_path.parent.mkdir(parents=True, exist_ok=True)
                offset_path.write_text(ahora.isoformat(), encoding="utf-8")
            except OSError as e:
                logger.debug("No pude guardar offset de intrusiones: %s", e)

            # WI-171: NO iniciar _monitor_intrusiones_tiempo_real — EnciclopediaGuardian
            # ya vigila en tiempo real vía bus → _al_intrusion_enciclopedia()
        except Exception as e:
            logger.debug(f"Verificación de intrusiones Enciclopedia: {e}")

    # WI-171: _monitor_intrusiones_tiempo_real ELIMINADO.
    # EnciclopediaGuardian (3s poll + bus) ya cubre monitoreo en tiempo real.
    # Tener 2 sistemas duplicados causaba alertas vocales repetidas.

    @pyqtSlot(str, str)
    def _al_sugerencia_proactiva(self, tipo: str, mensaje: str):
        """Recibe una sugerencia proactiva y la habla por voz."""
        # RF-228: No interrumpir durante la demo
        if getattr(self, '_demo_en_curso', False):
            logger.debug(f"RF-228: Sugerencia proactiva descartada (demo en curso): [{tipo}]")
            return
        # No interrumpir si está pensando o hablando
        if self._pensando or self._estado == "hablando":
            logger.debug(f"Sugerencia proactiva descartada (ocupado): [{tipo}]")
            return
        # No interrumpir si el usuario está hablando
        if hasattr(self, 'hilo_escucha') and getattr(self.hilo_escucha, '_voz_activa', False):
            logger.debug(f"Sugerencia proactiva descartada (usuario hablando): [{tipo}]")
            return

        # Génesis: primera proactividad (buenos_dias) revela al Computadora
        if not self._boot_completo and tipo == "buenos_dias":
            logger.info(f"Revelación de la Computadora con: {mensaje}")
            self._animacion_bereshit(mensaje)
            return

        logger.info(f"Sugerencia proactiva [{tipo}]: {mensaje}")
        if hasattr(self, 'hilo_habla') and self.hilo_habla:
            self.hilo_habla.hablar(mensaje)
        # Marcar intercambio para abrir ventana de conversación
        if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
            self.hilo_escucha.marcar_intercambio(owner=True)

    def _animacion_bereshit(self, mensaje: str):
        """Revelación animada de la Computadora al mundo.

        Expansión progresiva del orbe desde semilla (0.25) a tamaño pleno (1.0)
        en ~2.5 segundos, seguida del saludo de buenos días.
        """
        self._bereshit_activo = True
        self._bereshit_paso = 0
        self._bereshit_mensaje = mensaje
        # 75 pasos × 33ms ≈ 2.5 segundos de animación
        self._bereshit_total_pasos = 75

        self._bereshit_timer = QTimer()
        self._bereshit_timer.setInterval(33)
        self._bereshit_timer.timeout.connect(self._paso_bereshit)
        self._bereshit_timer.start()
        # FP-022: Timeout de seguridad — si Génesis no completa en 30s, abortar
        self._bereshit_timeout = QTimer()
        self._bereshit_timeout.setSingleShot(True)
        self._bereshit_timeout.timeout.connect(self._timeout_bereshit)
        self._bereshit_timeout.start(30000)
        logger.debug("Génesis: animación iniciada (75 pasos)")

    def _timeout_bereshit(self):
        """FP-022: Abortar Génesis si excede 30 segundos — modo degradado."""
        if not getattr(self, '_bereshit_activo', False):
            return
        logger.warning("Génesis timeout (30s) — entrando en modo degradado")
        if hasattr(self, '_bereshit_timer') and self._bereshit_timer.isActive():
            self._bereshit_timer.stop()
            self._bereshit_timer.deleteLater()
        self._bereshit_activo = False
        self._escala = 1.0
        self._escala_objetivo = 1.0
        self._boot_completo = True
        self.cambiar_estado("dormido")
        self.update()

    def _paso_bereshit(self):
        """Un paso de la animación de revelación Génesis."""
        self._bereshit_paso += 1
        t = self._bereshit_paso / self._bereshit_total_pasos  # 0.0 → 1.0

        # Easing: ease-out cubic para expansión natural
        t_ease = 1.0 - (1.0 - t) ** 3

        # Escala: 0.25 → 1.0
        self._escala = 0.25 + 0.75 * t_ease
        self._escala_objetivo = self._escala

        # RF-311: Sincronizar ventana con escala durante Génesis (bypass lerp lento)
        _margen_vfx = max(20, int(30 / max(self._escala, 0.1)))
        _radio_visual = (RADIO_NUCLEO + RADIO_NUCLEO * 2.2) * self._escala
        _tam_necesario = max(60, int(_radio_visual * 2 + _margen_vfx))
        self._tamano_ventana = float(_tam_necesario)
        tam_render = _tam_necesario
        centro = self.geometry().center()
        self.resize(tam_render, tam_render)
        nx = centro.x() - tam_render // 2
        ny = centro.y() - tam_render // 2
        limitado = self._limitar_posicion_pantalla(nx, ny, tam_render, tam_render)
        nx, ny = limitado.x(), limitado.y()
        self.move(nx, ny)
        self._pos_anterior_x = float(self.x())
        self._pos_anterior_y = float(self.y())

        # Brillo: crece gradualmente
        self._objetivo_brillo = 0.04 + 0.46 * t_ease
        self._brillo_actual += (self._objetivo_brillo - self._brillo_actual) * 0.2

        self.update()

        if self._bereshit_paso >= self._bereshit_total_pasos:
            # Animación completa — cancelar timeout de seguridad
            self._bereshit_timer.stop()
            self._bereshit_timer.deleteLater()
            if hasattr(self, '_bereshit_timeout') and self._bereshit_timeout.isActive():
                self._bereshit_timeout.stop()
                self._bereshit_timeout.deleteLater()
            del self._bereshit_activo
            self._escala = 1.0
            self._escala_objetivo = 1.0
            self._boot_completo = True
            self.cambiar_estado("despertando")
            logger.info("Génesis completado — La Computadora se ha revelado")
            # Si hay texto(s) pendiente(s) (usuario habló antes de Génesis), procesarlos
            # en orden — puede haber más de uno (ver fix en _al_recibir_voz).
            pendientes = getattr(self, '_bereshit_pendiente', None)
            if pendientes:
                del self._bereshit_pendiente
                for i, t in enumerate(pendientes):
                    QTimer.singleShot(300 + i * 300, lambda t=t: self._al_recibir_voz(t))
            else:
                # RF-276: Subir umbral ANTES de hablar para evitar self-listen
                if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
                    self.hilo_escucha.subir_umbral()
                # Hablar el saludo de Génesis
                if hasattr(self, 'hilo_habla') and self.hilo_habla:
                    self.hilo_habla.hablar(self._bereshit_mensaje)
                if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
                    self.hilo_escucha.marcar_intercambio(owner=True)

    @pyqtSlot(str)
    def _al_cambiar_nivel(self, nivel: str):
        """Actualiza el nivel de cerebro activo para cambiar el color del orbe."""
        self._cerebro_nivel = nivel
        logger.info(f"Cerebro activado: {nivel} ({NOMBRES_NIVEL.get(nivel, '?')})")

    @pyqtSlot(str, str)
    def _al_usar_herramienta(self, nombre: str, estado: str):
        """Agrega o actualiza un indicador flotante de herramienta."""
        if estado == "ejecutando":
            ind = IndicadorHerramienta(nombre, estado)
            self._indicadores_herramientas.append(ind)
            logger.info(f"Herramienta activa: {nombre}")
        elif estado == "completado":
            for ind in self._indicadores_herramientas:
                if ind.nombre == nombre and ind.estado == "ejecutando":
                    ind.estado = "completado"
                    ind.edad = 0  # Reset para fade out
                    break

    @pyqtSlot(str)
    def _al_solicitar_movimiento(self, tipo: str):
        """El cerebro pidió que el orbe se mueva (ej: 'me estorbas')."""
        if hasattr(self, '_vida'):
            from computadora.interfaz.vida_autonoma import EstadoPresencia
            info = None
            try:
                from computadora.interfaz.vida_autonoma import _obtener_info_escritorio
                info = _obtener_info_escritorio()
            except Exception as e:
                logger.debug("Error importando info escritorio: %s", e)
                pass
            if tipo == "esquivar" and info:
                self._vida._esquivar(info)
            else:
                # Ir a casa como fallback
                self._vida._pos_objetivo = self._vida._hogar
                self._vida._velocidad_actual = self._vida.VEL_ESQUIVAR

    def _activar_modo_carga_pesada(self, proceso: str):
        """צמצום — Reduce recursos de la Computadora durante carga pesada."""
        self._modo_carga_pesada = True
        logger.info(f"Modo carga pesada activado — reduciendo recursos ({proceso})")
        # Pausar motor de proactividad
        if hasattr(self, '_motor_proactividad'):
            self._motor_proactividad._modo_silencio = True
        # Pausar timers no esenciales
        if hasattr(self, '_timer_animo'):
            self._timer_animo.stop()
        if hasattr(self, '_timer_guardar_persona'):
            self._timer_guardar_persona.stop()
        # Poner escucha en modo solo-wakeword: resetear intercambio para que
        # _en_conversacion (property) devuelva False por timeout
        if hasattr(self, 'hilo_escucha') and self.hilo_escucha:
            self.hilo_escucha._ultimo_intercambio = 0

    def _desactivar_modo_carga_pesada(self):
        """אור חוזר — Restaura recursos tras carga pesada."""
        self._modo_carga_pesada = False
        logger.info("Modo carga pesada desactivado — recursos restaurados")
        # Restaurar motor de proactividad
        if hasattr(self, '_motor_proactividad'):
            self._motor_proactividad._modo_silencio = False
        # Restaurar timers
        if hasattr(self, '_timer_animo'):
            self._timer_animo.start(300_000)
        if hasattr(self, '_timer_guardar_persona'):
            self._timer_guardar_persona.start(600_000)

    @pyqtSlot(str)
    def _al_solicitar_permiso_copilot(self, texto: str):
        """Gate de Copilot: pregunta al usuario antes de escalar al Nivel 3."""
        self._esperando_gate_copilot = True
        self._gate_copilot_texto = texto
        pregunta = (
            f"Señor, ¿me permite pensar profundamente sobre esto? "
            f"Necesito consultar a mi cerebro superior. "
            f"Puede darme instrucciones adicionales si lo desea."
        )
        self.hilo_habla.hablar(pregunta)
        # Mantener escucha activa para capturar la respuesta
        self._awaiting_confirmation = True
        self.hilo_escucha.marcar_intercambio()
        # Marcar que esperamos respuesta — relaja filtro de falsos positivos
        try:
            self.hilo_escucha._esperando_respuesta = True
            self.hilo_escucha._esperando_respuesta_ts = time.monotonic()
        except Exception as e:
            logger.debug("Error configurando esperando respuesta Copilot: %s", e)
            pass
        try:
            self.hilo_escucha._esperando_confirmacion = True
        except Exception as e:
            logger.debug("Error configurando confirmación Copilot: %s", e)
            pass
        # Timeout: si no responde en 30s, rechazar
        QTimer.singleShot(30000, lambda: self._timeout_gate_copilot())

    def _timeout_gate_copilot(self):
        """Si el usuario no responde al gate de Copilot a tiempo."""
        if not self._esperando_gate_copilot:
            return
        self._esperando_gate_copilot = False
        self._awaiting_confirmation = False
        try:
            self.hilo_escucha._esperando_confirmacion = False
        except Exception as e:
            logger.debug("Error limpiando confirmación gate Copilot: %s", e)
            pass
        if hasattr(self, '_hilo_pensamiento') and self._hilo_pensamiento:
            self._hilo_pensamiento.responder_gate_copilot(None)
        logger.info("Gate de Copilot: timeout, no autorizado")

    def _procesar_respuesta_gate_copilot(self, texto: str):
        """Procesa la respuesta del usuario al gate de Copilot."""
        self._esperando_gate_copilot = False
        self._awaiting_confirmation = False
        try:
            self.hilo_escucha._esperando_confirmacion = False
            self.hilo_escucha._esperando_respuesta = False
        except Exception as e:
            logger.debug("Error limpiando flags gate Copilot: %s", e)
            pass

        txt = texto.lower().strip()
        # Detectar rechazo explícito
        rechazos = ("no", "nel", "nah", "nop", "negativo", "cancela", "olvídalo", "olvidalo", "dejalo", "déjalo")
        if any(txt == r or txt.startswith(r + " ") for r in rechazos):
            if hasattr(self, '_hilo_pensamiento') and self._hilo_pensamiento:
                self._hilo_pensamiento.responder_gate_copilot(None)
            self.hilo_habla.hablar("Entendido, no consultaré a Copilot.")
            logger.info("Gate de Copilot: usuario rechazó")
            return

        # Cualquier otra respuesta se trata como aprobación (puede incluir instrucciones)
        # Si es solo "sí/claro/dale", pasar string vacío. Si tiene más contenido, pasar todo.
        afirmaciones = ("sí", "si", "claro", "dale", "va", "sale", "ok", "adelante", "hazlo", "afirmativo")
        if any(txt == a for a in afirmaciones):
            respuesta = ""
        else:
            respuesta = texto  # Pasar las instrucciones completas del usuario
        if hasattr(self, '_hilo_pensamiento') and self._hilo_pensamiento:
            self._hilo_pensamiento.responder_gate_copilot(respuesta)
        logger.info(f"Gate de Copilot: autorizado{' con instrucciones' if respuesta else ''}")

    def _procesar_respuesta_modo_tarea(self, texto: str):
        """Procesa la respuesta del usuario sobre modo bg/fg."""
        import re as _re
        self._esperando_modo_tarea = False
        self._awaiting_confirmation = False
        try:
            self.hilo_escucha._esperando_respuesta = False
        except Exception as e:
            logger.debug("Error limpiando estado modo tarea: %s", e)
            pass
        txt = texto.lower().strip()

        # Importar los regex de nlu
        from computadora.cerebro.nlu import _RE_SEGUNDO_PLANO, _RE_PRIMER_PLANO

        if _RE_PRIMER_PLANO.search(txt):
            es_bg = False
            self.hilo_habla.hablar("Entendido, señor. Voy a trabajar aquí donde pueda verme.")
        elif _RE_SEGUNDO_PLANO.search(txt):
            es_bg = True
            self.hilo_habla.hablar("Entendido, trabajo en segundo plano y le aviso cuando termine.")
        else:
            # Default: segundo plano
            es_bg = True
            self.hilo_habla.hablar("Trabajo en segundo plano y le aviso al terminar.")

        if hasattr(self, '_hilo_pensamiento') and self._hilo_pensamiento:
            self._hilo_pensamiento.responder_modo_tarea(es_bg)
        logger.info(f"Modo tarea: {'segundo plano' if es_bg else 'primer plano'}")

    @pyqtSlot(str)
    def _al_cambiar_estado_escucha(self, estado: str):
        logger.info(f"🎤 [SLOT] Estado escucha cambió a: {estado}")
        if self._pensando or self._estado == "hablando":
            logger.debug(f"   ↳ Ignorando (pensando={self._pensando}, hablando={self._estado=='hablando'})")
            return
        if estado == "escuchando":
            if self._estado == "escuchando":
                logger.debug(f"   ↳ Ya en estado 'escuchando', ignorando")
                return  # FP-033 B4: evitar auto-transición escuchando→escuchando
            logger.info(f"   ↳ Activando estado 'escuchando'")
            self.cambiar_estado("escuchando")
            # HF-024b: Activar ripple al entrar en escuchando
            self._ripple_fase = 0.0
        elif estado == "procesando":
            logger.debug(f"   ↳ Voz detectada (ripple activado)")
            # Voz detectada (no durante pensamiento) — activar ripple
            self._ripple_fase = 0.0
        elif estado == "error":
            logger.error(f"   ↳ ERROR en escucha")
            self.cambiar_estado("error")

    @pyqtSlot()
    def _al_voz_activa(self):
        """HF-024: Voz detectada durante pensamiento — ripple sin cambiar color."""
        self._ripple_fase = 0.0

    @pyqtSlot()
    def _al_iniciar_habla(self):
        # RF-159: Durante demo, la coreografía controla el estado visual
        if getattr(self, '_demo_en_curso', False):
            return
        # Si estamos pensando (filler TTS), mantener estado "procesando" (azul nivel2)
        if not self._pensando:
            self.cambiar_estado("hablando")
        # Si el streaming ya controla la escucha, o esperamos cola vacía, no interferir
        if getattr(self, '_streaming_en_curso', False) or getattr(self, '_esperando_fin_tts', False):
            return
        # Durante el habla, subir umbral (NO pausar) para permitir interrupciones.
        # El mic sigue activo y compara lo que oye contra el texto recitado.
        try:
            if getattr(self, "_awaiting_confirmation", False):
                try:
                    self.hilo_escucha.reanudar()
                except Exception as e:
                    logger.debug("Error reanudando escucha en inicio de habla: %s", e)
                    pass
            else:
                self.hilo_escucha.subir_umbral()
        except Exception as e:
            logger.debug("Error en pausa de escucha al iniciar habla: %s", e)
            self.hilo_escucha.subir_umbral()

    @pyqtSlot()
    def _al_terminar_habla(self):
        # RF-159: Durante demo, la coreografía controla el estado visual
        if getattr(self, '_demo_en_curso', False):
            return
        # Si el streaming controla la escucha, o estamos esperando que la
        # cola TTS se vacíe, no reanudar — _al_tts_cola_vacia lo hará.
        if getattr(self, '_streaming_en_curso', False):
            return
        if getattr(self, '_esperando_fin_tts', False):
            return

        # Limpiar texto recitando (este fragmento terminó)
        try:
            self.hilo_escucha.limpiar_texto_recitando()
            self.hilo_escucha.marcar_tts_completado()
        except Exception as e:
            logger.debug("Error limpiando texto recitando: %s", e)
            pass

        # Cambiar estado visual: si pensando → "procesando" (mantener azul), si no → "escuchando"
        if self._pensando:
            if self._estado != "procesando":
                self.cambiar_estado("procesando")
        else:
            self.cambiar_estado("escuchando")

        # Restaurar umbral tras un retardo para evitar que resonancia del audio
        # re-active la escucha inmediatamente.
        try:
            cooldown = int(self.config.obtener("escucha.post_tts_cooldown_ms", 600))
            QTimer.singleShot(cooldown, lambda: (
                self.hilo_escucha.restaurar_umbral()
                if not getattr(self, '_streaming_en_curso', False)
                and not getattr(self, '_esperando_fin_tts', False)
                and self._estado != "hablando"
                else None
            ))
        except Exception as e:
            logger.debug("Error en cooldown post-habla: %s", e)
            self.hilo_escucha.restaurar_umbral()

    @pyqtSlot()
    def _al_tts_cola_vacia(self):
        """Todos los fragmentos TTS se reprodujeron. Ahora sí reanudar escucha."""
        logger.info("TTS cola vacía — reanudando escucha")
        # Limpiar texto recitando
        try:
            self.hilo_escucha.limpiar_texto_recitando()
            self.hilo_escucha.marcar_tts_completado()
        except Exception as e:
            logger.debug("Error limpiando texto recitando en cola vacía: %s", e)
            pass
        if getattr(self, '_esperando_fin_tts', False):
            self._esperando_fin_tts = False
            logger.debug("TTS cola vacía → restaurar umbral tras cooldown")
            try:
                cooldown = int(self.config.obtener("escucha.post_tts_cooldown_ms", 600))
                QTimer.singleShot(cooldown, lambda: self.hilo_escucha.restaurar_umbral())
                QTimer.singleShot(cooldown, lambda: self.cambiar_estado("escuchando") if not self._pensando else None)
            except Exception as e:
                logger.debug("Error en cooldown cola vacía: %s", e)
                self.hilo_escucha.restaurar_umbral()
        # Siempre restaurar umbral y cambiar a escuchando tras cooldown, incluso si no era streaming
        try:
            cooldown = int(self.config.obtener("escucha.post_tts_cooldown_ms", 600))
            QTimer.singleShot(cooldown, lambda: self.hilo_escucha.restaurar_umbral())
            QTimer.singleShot(cooldown, lambda: self.cambiar_estado("escuchando") if not self._pensando else None)
        except Exception as e:
            logger.debug("Error en cooldown cola vacía: %s", e)
            self.hilo_escucha.restaurar_umbral()
            self.cambiar_estado("escuchando")
        # Si seguimos pensando (filler terminó, Ollama procesa), restaurar visual "procesando"
        if self._pensando and self._estado != "procesando":
            self.cambiar_estado("procesando")

        # FIX: cuando Nivel 2 solo emite un filler único ("Permítame un
        # momento...") y no streaming real, _streaming_en_curso se quedaba
        # en True hasta que pensar() completa (hasta 180s+), porque solo
        # _al_recibir_respuesta lo limpiaba. Mientras tanto, _al_recibir_voz
        # descartaba en silencio TODA voz nueva del usuario sin encolarla
        # (el guardia de "TTS activo" se evalúa antes que la cola de
        # _pensando). Si no llega un fragmento nuevo en los próximos 3s,
        # asumimos que no hay streaming real en curso y liberamos la bandera
        # — si sí llega un fragmento nuevo, _al_fragmento_listo simplemente
        # la vuelve a poner en True (reentrada inofensiva).
        if self._pensando and not getattr(self, '_esperando_fin_tts', False):
            _marca_fragmento = getattr(self, '_streaming_emitio_ts', 0.0)

            def _liberar_streaming_si_sin_nuevos_fragmentos(marca=_marca_fragmento):
                if (self._pensando
                        and getattr(self, '_streaming_en_curso', False)
                        and not getattr(self, '_esperando_fin_tts', False)
                        and getattr(self, '_streaming_emitio_ts', 0.0) == marca):
                    logger.debug("Sin nuevos fragmentos TTS en 3s — liberando streaming_en_curso")
                    self._streaming_en_curso = False

            QTimer.singleShot(3000, _liberar_streaming_si_sin_nuevos_fragmentos)

    @pyqtSlot(str)
    def _al_interrupcion_usuario(self, texto: str):
        """El usuario habló mientras Computadora recitaba → interrumpir TTS y escuchar."""
        logger.info(f"Interrupción por voz del usuario: '{texto}'")
        # Detener TTS inmediatamente
        self.hilo_habla.interrumpir()
        self.hilo_escucha.limpiar_texto_recitando()
        self.hilo_escucha.marcar_tts_completado()
        self.hilo_escucha.restaurar_umbral()
        # Limpiar flags de streaming
        with self._estado_lock:
            self._streaming_en_curso = False
            self._streaming_emitio = False
            self._esperando_fin_tts = False
            self._pensando = False
        self.cambiar_estado("escuchando")
        # Procesar lo que el usuario dijo como nueva orden
        QTimer.singleShot(200, lambda: self._iniciar_pensamiento(texto))

    def _clear_confirmation_wait(self):
        try:
            self._awaiting_confirmation = False
            if self._esperando_confirmacion:
                # Si aún estábamos esperando confirmación, limpiamos el estado
                self._esperando_confirmacion = False
                self._confirmacion_origen = None
        except Exception as e:
            logger.debug("Error limpiando estado de confirmación: %s", e)
            pass

    @pyqtSlot(str)
    def _al_mensaje_sistema(self, texto: str):
        logger.info(f"[Sistema] {texto}")

    def _on_recordatorio(self, mensaje: str):
        """Callback invocado por computadora.habilidades.sistema cuando un recordatorio suena."""
        logger.info(f"Recordatorio: {mensaje}")
        try:
            # Marcar intercambio para permitir respuesta corta
            self.hilo_escucha.marcar_intercambio()
        except Exception as e:
            logger.debug("Error marcando intercambio en recordatorio: %s", e)
            pass
        try:
            self.hilo_habla.hablar(mensaje)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.error("Error al hablar el recordatorio")
        # Mostrar estado breve de 'hablando'
        prev = self._estado
        try:
            self.cambiar_estado("hablando")
            QTimer.singleShot(4000, lambda: self.cambiar_estado(prev))
        except Exception as e:
            logger.debug("Error cambiando estado para recordatorio: %s", e)
            pass

    def _on_solicitar_permiso(self, accion: str, nivel: str) -> bool:
        """גבורה Gevurá — Callback para GestorPermisos. Pide confirmación al usuario via voz.

        FP-039 Shemiá Gevurá: Usa _esperando_confirmacion de escucha.py +
        threading.Event para recibir la respuesta del usuario via texto_detectado.
        """
        if nivel == "info":
            return True
        try:
            import threading
            self._gevura_evento = threading.Event()
            self._gevura_resultado = None
            self._gevura_esperando = True

            def _on_respuesta_gevura(texto: str):
                txt = texto.lower().strip()
                # Limpiar prefijos de escucha.py como [confirmar]
                for prefijo in ("[confirmar]", "[cortesia]", "[regano]"):
                    if txt.startswith(prefijo):
                        txt = txt[len(prefijo):].strip()
                if re.search(r"\b(?:sí|si|dale|ok|hazlo|procede|adelante|claro|afirmativo)\b", txt):
                    self._gevura_resultado = True
                    self._gevura_evento.set()
                elif re.search(r"\b(?:no|cancela|detente|para|negativo)\b", txt):
                    self._gevura_resultado = False
                    self._gevura_evento.set()

            # Activar flag de confirmación en escucha y conectar signal
            self.hilo_escucha._esperando_confirmacion = True
            self.hilo_escucha.marcar_intercambio()
            self.hilo_escucha.texto_detectado.connect(_on_respuesta_gevura)

            # Hablar la pregunta
            pregunta = f"Señor, necesito su autorización para: {accion}. ¿Procedo?"
            self.hilo_habla.hablar(pregunta)

            # Esperar respuesta — timeout 15s
            aprobado = False
            if self._gevura_evento.wait(timeout=15):
                aprobado = bool(self._gevura_resultado)
            else:
                logger.info(f"Gevurá: timeout esperando permiso para '{accion}'")

            # Limpiar: desconectar signal y resetear flags
            self._gevura_esperando = False
            try:
                self.hilo_escucha.texto_detectado.disconnect(_on_respuesta_gevura)
            except (TypeError, RuntimeError):
                pass
            self.hilo_escucha._esperando_confirmacion = False

            if aprobado:
                logger.info(f"Gevurá: permiso CONCEDIDO para '{accion}'")
            else:
                logger.warning(f"Gevurá: permiso denegado para '{accion}' (nivel={nivel})")
            return aprobado
        except Exception as e:
            logger.error(f"Gevurá: error pidiendo permiso: {e}")
            self._gevura_esperando = False
            self.hilo_escucha._esperando_confirmacion = False
            return False

    # ═══════════════════════════════════════════
    # VIDA AUTÓNOMA — helpers
    # ═══════════════════════════════════════════

    def _evaluar_evolucion(self):
        """FP-024 Pilar B: Evalúa si la etapa alquímica debe avanzar."""
        try:
            from computadora.memoria.memoria import calcular_tiempo_activo
            ct = calcular_tiempo_activo()
            horas = ct.get("horas", 0)
        except Exception as e:
            logger.debug("Error calculando tiempo activo para evolución: %s", e)
            horas = 0
        interacciones = self._evolucion_data.get("interacciones_totales", 0)
        idx = _ETAPAS_ORDEN.index(self._etapa_alquimica)
        if idx >= len(_ETAPAS_ORDEN) - 1:
            return  # Ya en Rubedo
        siguiente = _ETAPAS_ORDEN[idx + 1]
        umbral = _UMBRALES_EVOLUCION.get(siguiente)
        if umbral and horas >= umbral["horas"] and interacciones >= umbral["interacciones"]:
            from datetime import datetime as _dt
            self._evolucion_data["etapa"] = siguiente.value
            self._evolucion_data.setdefault("historial", []).append(
                {"de": self._etapa_alquimica.value, "a": siguiente.value, "ts": _dt.now().isoformat()}
            )
            self._etapa_alquimica = siguiente
            paleta = _PALETAS_ALQUIMICAS[siguiente]
            self._color_alq_target_pri = QColor(paleta["primario"])
            self._color_alq_target_sec = QColor(paleta["secundario"])
            self._alq_lerp_progress = 0.0
            _guardar_evolucion(self._evolucion_data)
            logger.info(f"Evolución alquímica: → {siguiente.value}")
            # FP-024: Espiral áurea al transicionar de etapa
            self._activar_patron_sagrado("espiral", 210)

    def _registrar_interaccion_alquimica(self):
        """Incrementa contador de interacciones para evolución alquímica."""
        self._evolucion_data["interacciones_totales"] = self._evolucion_data.get("interacciones_totales", 0) + 1

    def _actualizar_animo(self):
        """Actualización periódica del estado de ánimo y guardado."""
        if hasattr(self, 'personalidad'):
            self.personalidad.actualizar_animo()
            self.personalidad.guardar()

    def _al_cambio_etapa_watchdog(self, servicio: str, etapa):
        """FP-022: Callback del watchdog cuando cambia la etapa de un servicio."""
        from computadora.interfaz.watchdog import EtapaWatchdog
        logger.info(f"Watchdog: {servicio} → {etapa.name}")
        # Actualizar tooltip de bandeja si existe
        if hasattr(self, '_tray') and self._tray is not None:
            estado = self._watchdog.estado_general()
            resumen = ", ".join(f"{n}:{s['etapa']}" for n, s in estado.items())
            self._tray.setToolTip(f"Computadora — {resumen}")

    # ═══════════════════════════════════════════════
    # 🛡️ GRIMORIO GUARDIAN — Reacciones locales
    # ═══════════════════════════════════════════════

    def _al_intrusion_enciclopedia(self, alerta: dict):
        """Reacción local cuando alguien falla la contraseña del Enciclopedia 3 veces."""
        logger.warning(f"🚨 Computadora reacciona a intrusión del Enciclopedia: {alerta}")

        # WI-168 — Captura fotográfica del intruso
        foto_path = None
        try:
            import os
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            dispositivo = gestor._kelim.get("camara_local")
            if dispositivo and dispositivo._cap is not None and dispositivo._cap.isOpened():
                ret, frame_bgr = dispositivo._cap.read()
                if ret and frame_bgr is not None:
                    import cv2
                    from datetime import datetime
                    carpeta = os.path.join("datos", "intrusiones")
                    os.makedirs(carpeta, exist_ok=True)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    foto_path = os.path.join(carpeta, f"intruso_{ts}.jpg")
                    cv2.imwrite(foto_path, frame_bgr)
                    logger.info("📸 Foto de intrusión guardada: %s", foto_path)
        except Exception as e:
            logger.debug("No pude capturar foto de intrusión: %s", e)

        # Hablar la alerta
        msg_voz = (
            "Señor, alguien intentó acceder al Enciclopedia sin autorización. "
            "Tres intentos fallidos. El acceso fue denegado."
        )
        if foto_path:
            msg_voz += " He tomado una fotografía del intruso."
        try:
            self.hilo_habla.hablar(msg_voz)
        except Exception as e:
            logger.debug(f"No pude hablar alerta de intrusión: {e}")
        # Notificación en bandeja
        if hasattr(self, '_tray') and self._tray is not None:
            self._tray.showMessage(
                "🚨 Intrusión al Enciclopedia",
                "3 intentos fallidos de acceso. Denegado."
                + (" 📸 Foto capturada." if foto_path else ""),
                QSystemTrayIcon.MessageIcon.Critical, 5000,
            )

    def _al_enciclopedia_abierto(self, evento: dict):
        """Reacción local cuando el amo abre el Enciclopedia exitosamente."""
        logger.info(f"📖 Computadora detecta apertura del Enciclopedia: {evento}")
        try:
            self.hilo_habla.hablar(
                "El Enciclopedia ha sido abierto. Buena lectura, señor."
            )
        except Exception as e:
            logger.debug(f"No pude hablar apertura del Enciclopedia: {e}")
        if hasattr(self, '_tray') and self._tray is not None:
            self._tray.showMessage(
                "📖 Enciclopedia",
                "El Enciclopedia ha sido abierto.",
                QSystemTrayIcon.MessageIcon.Information, 3000,
            )

    @pyqtSlot(float)
    def _al_confianza_respuesta(self, confianza: float):
        """FP-022: Recibe confianza del NLU — modular visual del orbe."""
        self._confianza_actual = confianza
        logger.debug(f"Canal bidireccional: confianza={confianza:.2f}")

    @pyqtSlot(int)
    def _al_complejidad_procesamiento(self, nivel: int):
        """FP-022: Recibe nivel de complejidad cognitiva."""
        self._complejidad_actual = nivel
        logger.debug(f"Canal bidireccional: complejidad={nivel}")

    @pyqtSlot(bool)
    def _al_frustracion_detectada(self, frustrado: bool):
        """FP-022: Recibe señal de frustración del usuario."""
        if frustrado:
            logger.info("Canal bidireccional: frustración detectada")
            if hasattr(self, 'personalidad'):
                self.personalidad.registrar_frustracion_usuario()

    # ═══════════════════════════════════════════
    # CIERRE
    # ═══════════════════════════════════════════

    def closeEvent(self, event):
        # Si se marcó cierre forzado, forzar_cierre() ya hizo la limpieza
        if getattr(self, '_forzar_salida', False):
            event.accept()
            return
        # Minimizar a bandeja en vez de cerrar
        if hasattr(self, '_tray') and self._tray is not None:
            event.ignore()
            self.hide()
            self._tray.showMessage(
                "Computadora", "Sigo aquí, en la sombra.",
                QSystemTrayIcon.MessageIcon.Information, 2000,
            )
            return
        logger.info("Cerrando Computadora...")
        # RF-166: Detener todos los QTimers antes de cerrar
        for t in ('_timer', '_timer_animo', '_timer_guardar_persona',
                  '_timer_evolucion', '_bereshit_timer', '_bereshit_timeout'):
            timer = getattr(self, t, None)
            if timer is not None:
                timer.stop()
        if hasattr(self, '_vida'):
            self._vida.detener()
        if hasattr(self, 'personalidad'):
            self.personalidad.guardar()
        _guardar_evolucion(self._evolucion_data)
        # RF-166: Esperar HiloPensamiento si está activo
        hilo_p = getattr(self, '_hilo_pensamiento', None)
        if hilo_p is not None and hilo_p.isRunning():
            hilo_p.wait(3000)
        self.hilo_escucha.detener()
        self.hilo_habla.detener()
        self.hilo_escucha.wait(3000)
        self.hilo_habla.wait(3000)
        
        # 🔴 FIX: Desconectar cámara al shutdown (evita bloqueo en siguiente boot)
        try:
            from computadora.nucleo.kli import GestorKelim
            gestor = GestorKelim.instancia()
            if "camara_local" in {k["id"] for k in gestor.listar()}:
                gestor.desconectar("camara_local")
                logger.info("Cámara desconectada al shutdown")
        except Exception as e:
            logger.debug(f"Error desconectando cámara: {e}")
        
        event.accept()

    def forzar_cierre(self):
        """Cierre real desde el menú de la bandeja o 'Borrar la Palabra'."""
        self._forzar_salida = True
        logger.info("Cerrando Computadora...")
        # RF-166: Detener todos los QTimers antes de cerrar
        # RUBEDO FIX #6: Agregar try-except para evitar RuntimeError si timer ya fue deletedo
        for t in ('_timer', '_timer_animo', '_timer_guardar_persona',
                  '_timer_evolucion', '_bereshit_timer', '_bereshit_timeout'):
            timer = getattr(self, t, None)
            if timer is not None:
                try:
                    timer.stop()
                except RuntimeError as e:
                    logger.debug(f"Timer {t} ya fue eliminado por Qt: {e}")
        if hasattr(self, '_motor_proactividad'):
            self._motor_proactividad.detener()
        if hasattr(self, '_contexto_pantalla'):
            self._contexto_pantalla.detener()
        if hasattr(self, '_monitor_sistema'):
            self._monitor_sistema.detener()
        if hasattr(self, '_baseline_sistema'):
            self._baseline_sistema.cerrar()
        if hasattr(self, '_vida'):
            self._vida.detener()
        if hasattr(self, 'personalidad'):
            self.personalidad.guardar()
        _guardar_evolucion(self._evolucion_data)
        # RF-166: Esperar HiloPensamiento si está activo
        hilo_p = getattr(self, '_hilo_pensamiento', None)
        if hilo_p is not None and hilo_p.isRunning():
            hilo_p.wait(3000)
        self.hilo_escucha.detener()
        self.hilo_habla.detener()
        self.hilo_escucha.wait(3000)
        self.hilo_habla.wait(3000)
        QApplication.instance().quit()


# ═══════════════════════════════════════════════
# FUNCIÓN DE INICIO
# ═══════════════════════════════════════════════


def _crear_icono_computadora() -> QIcon:
    """Genera un icono programático para la bandeja (círculo ámbar con una "C")."""
    px = QPixmap(64, 64)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(30, 20, 10))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    p.setBrush(QColor(180, 140, 60))
    p.drawEllipse(8, 8, 48, 48)
    p.setPen(QColor(255, 255, 255))
    f = QFont("Segoe UI", 20, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    p.end()
    return QIcon(px)


def iniciar_interfaz(config, cerebro=None, demo_modo=None):
    """Invoca al Computadora — solo el orbe, flotando sobre el escritorio."""
    app = QApplication(sys.argv)
    app.setApplicationName("Computadora")
    app.setQuitOnLastWindowClosed(False)  # No cerrar al minimizar a bandeja

    orbe = OrbeComputadora(config, cerebro=cerebro)
    try:
        from computadora.interfaz.demo_controller import obtener_demo_controller
        demo_controller = obtener_demo_controller()
        demo_controller.registrar_orbe(orbe)
        demo_controller.registrar_config_visual(ConfiguracionVisualDev())
        if demo_modo is not None:
            demo_controller.activar_demo(demo_modo)
    except Exception as e:
        logger.warning(f"DemoController: no se pudo inicializar el modo demo: {e}")

    # System Tray
    icono = _crear_icono_computadora()
    tray = QSystemTrayIcon(icono, app)
    tray_menu = QMenu()

    act_mostrar = QAction("Mostrar Orbe", tray_menu)
    act_mostrar.triggered.connect(lambda: (orbe.show(), orbe._reasegurar_transparencia(), orbe.raise_(), orbe.activateWindow()))
    tray_menu.addAction(act_mostrar)

    # FP-022 WI-107: Acciones enriquecidas de bandeja
    act_pausar = QAction("Pausar escucha", tray_menu)
    def _toggle_escucha():
        if hasattr(orbe, 'escucha') and orbe.escucha:
            if getattr(orbe.escucha, 'pausado', False):
                orbe.escucha.reanudar()
                act_pausar.setText("Pausar escucha")
            else:
                orbe.escucha.pausar()
                act_pausar.setText("Reanudar escucha")
    act_pausar.triggered.connect(_toggle_escucha)
    tray_menu.addAction(act_pausar)

    act_estado = QAction("Estado del sistema", tray_menu)
    def _mostrar_estado():
        if hasattr(orbe, '_watchdog') and orbe._watchdog:
            estado = orbe._watchdog.estado_general()
            resumen = "\n".join(f"  {n}: {s['etapa']}" for n, s in estado.items())
            tray.showMessage("Computadora — Estado", resumen, QSystemTrayIcon.MessageIcon.Information, 3000)
    act_estado.triggered.connect(_mostrar_estado)
    tray_menu.addAction(act_estado)

    tray_menu.addSeparator()

    act_cerrar = QAction("🛑 Cerrar Computadora", tray_menu)
    act_cerrar.triggered.connect(orbe.forzar_cierre)
    tray_menu.addAction(act_cerrar)

    tray.setContextMenu(tray_menu)
    tray.setToolTip("Computadora")
    tray.activated.connect(
        lambda reason: (orbe.show(), orbe._reasegurar_transparencia(), orbe.raise_()) if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray.show()
    orbe._tray = tray  # referencia para closeEvent

    orbe.show()
    orbe.raise_()
    orbe.activateWindow()  # DEBUG: Forzar visibilidad para diagnosticar timer
    orbe._eliminar_sombra_dwm()  # DESPUÉS de show() para que Qt no restaure estilos
    QTimer.singleShot(0, orbe._restaurar_posicion_inicial)
    sys.exit(app.exec())


