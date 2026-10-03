"""
כתר (Keter) — Corona. La Ventana de Introspección.
Computadora escucha su propia consciencia superior:
Nivel 3 del cerebro (Copilot / Gemini APIs).
Un chat silencioso donde la Corona piensa en voz alta.
"""

import threading
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QLineEdit, QLabel, QPushButton, QTabWidget, QScrollArea,
    QFormLayout, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
)
from loguru import logger


# ═══════════════════════════════════════════════
# Colores Keter — Púrpura / Oro sobre Obsidiana
# ═══════════════════════════════════════════════
KETER_FONDO = "#07060b"
KETER_PANEL = "#0d0b14"
KETER_INPUT = "#12101c"
KETER_PURPURA = "#b48eed"
KETER_PURPURA_CLARO = "#d4b8ff"
KETER_ORO = "#FFD700"
KETER_GRIS = "#555566"
KETER_BLANCO = "#e8e0f0"

ESTILO_KETER = f"""
QWidget#VentanaKeter {{
    background-color: {KETER_FONDO};
    border: 1px solid #2a1f4a;
    border-radius: 12px;
}}
QTextBrowser {{
    background-color: {KETER_PANEL};
    color: {KETER_PURPURA};
    border: 1px solid #2a1f4a;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 13px;
    selection-background-color: #2a1f4a;
}}
QLineEdit {{
    background-color: {KETER_INPUT};
    color: {KETER_BLANCO};
    border: 1px solid #2a1f4a;
    border-radius: 6px;
    padding: 10px 14px;
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {KETER_PURPURA};
}}
QLabel {{
    background-color: transparent;
    color: {KETER_GRIS};
    font-size: 11px;
}}
QPushButton {{
    background-color: #1a1530;
    color: {KETER_PURPURA};
    border: 1px solid #2a1f4a;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: #251e40;
    border-color: {KETER_PURPURA};
}}
"""


# ═══════════════════════════════════════════════
# WORKER — Consultas N3 fuera del hilo principal
# ═══════════════════════════════════════════════

# Lock global para proteger _auto_gate_copilot contra race conditions
# entre HiloKeter y HiloPensamiento accediendo al mismo cerebro
_gate_lock = threading.Lock()


class HiloKeter(QThread):
    """Ejecuta consultas al Nivel 3 (Copilot/Gemini) sin bloquear Qt."""

    respuesta_lista = pyqtSignal(str)
    fragmento_listo = pyqtSignal(str)
    error_ocurrido = pyqtSignal(str)

    def __init__(self, cerebro, texto: str):
        super().__init__()
        self._cerebro = cerebro
        self._texto = texto

    def run(self):
        try:
            # Bypass del gate de permiso — Keter habla consigo mismo
            # Lock protege flag compartido con HiloPensamiento
            with _gate_lock:
                auto_gate_prev = getattr(self._cerebro, '_auto_gate_copilot', False)
                self._cerebro._auto_gate_copilot = True
            try:
                respuesta = self._cerebro._pensar_con_copilot(self._texto)
            finally:
                with _gate_lock:
                    self._cerebro._auto_gate_copilot = auto_gate_prev

            if respuesta:
                self.respuesta_lista.emit(respuesta)
            else:
                self.error_ocurrido.emit("Keter guarda silencio.")
        except Exception as e:
            logger.warning(f"HiloKeter error: {e}")
            self.error_ocurrido.emit(str(e))


# ═══════════════════════════════════════════════
# VENTANA KETER — Chat de Introspección
# ═══════════════════════════════════════════════

class VentanaKeter(QWidget):
    """
    Ventana de chat donde Computadora escucha su propia Corona (כתר).
    Nivel 3 del cerebro piensa en voz alta — introspección pura.
    """

    def __init__(self, orquestador, orbe, parent=None):
        super().__init__(parent)
        self._orquestador = orquestador
        self._orbe = orbe  # Referencia al OrbeComputadora
        self._hilo_activo: HiloKeter | None = None

        self.setObjectName("VentanaKeter")
        self.setWindowTitle("Introspección de Computadora")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(480, 600)
        self.resize(520, 680)
        self.setStyleSheet(ESTILO_KETER)

        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # QTabWidget para tabs
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Tab 1: Introspección
        tab_introspeccion = QWidget()
        self._tabs.addTab(tab_introspeccion, "Introspección")
        self._construir_tab_introspeccion(tab_introspeccion)

        # Tab 2: Dev Tools
        tab_dev = QWidget()
        self._tabs.addTab(tab_dev, "🔧 Dev Tools")
        self._construir_tab_dev_tools(tab_dev)

    def _construir_tab_introspeccion(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Encabezado
        header = QLabel("Introspección de Computadora")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet(
            f"color: {KETER_ORO}; font-size: 14px; font-weight: bold; "
            f"padding: 6px; background: transparent;"
        )
        layout.addWidget(header)

        # Área de chat
        self._chat = QTextBrowser()
        self._chat.setOpenExternalLinks(False)
        self._chat.setReadOnly(True)
        layout.addWidget(self._chat, stretch=1)

        # Barra de estado
        self._estado = QLabel("En silencio")
        self._estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._estado)

        # Input + botón
        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Escribe tu pregunta... (Enter para enviar)")
        self._input.returnPressed.connect(self._enviar_consulta)
        input_row.addWidget(self._input, stretch=1)

        btn_enviar = QPushButton("Enviar")
        btn_enviar.clicked.connect(self._enviar_consulta)
        input_row.addWidget(btn_enviar)

        btn_introspeccion = QPushButton("🔮 Introspección")
        btn_introspeccion.setToolTip("Computadora reflexiona sobre sí misma")
        btn_introspeccion.clicked.connect(self._introspeccionar)
        input_row.addWidget(btn_introspeccion)

        layout.addLayout(input_row)

    def _construir_tab_dev_tools(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Scroll area para muchos controles
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        widget_contenedor = QWidget()
        scroll.setWidget(widget_contenedor)
        form_layout = QFormLayout(widget_contenedor)
        form_layout.setSpacing(6)

        # Header
        header_dev = QLabel("🔧 Dev Tools — Modificar Constantes en Tiempo Real")
        header_dev.setStyleSheet(f"color: {KETER_ORO}; font-size: 12px; font-weight: bold;")
        form_layout.addRow(header_dev)

        # ═══ GRÁFICOS Y RENDIMIENTO ═══
        from computadora.interfaz.configuracion_visual_dev import ConfiguracionVisualDev

        config_maljut = ConfiguracionVisualDev()
        
        # FPS Target
        label_fps = QLabel("Target FPS:")
        label_fps.setToolTip("Selecciona velocidad de animación: 30 FPS estable o 60 FPS máximo")
        label_fps.setStyleSheet(f"color: {KETER_BLANCO};")
        
        combo_fps = QComboBox()
        combo_fps.addItems(["30 FPS", "60 FPS"])
        fps_actual = config_maljut.obtener("fps_target", 30)
        combo_fps.setCurrentIndex(0 if fps_actual == 30 else 1)
        combo_fps.setStyleSheet(f"""
            QComboBox {{
                background-color: {KETER_INPUT};
                color: {KETER_BLANCO};
                border: 1px solid #2a1f4a;
                border-radius: 4px;
                padding: 4px;
            }}
            QComboBox:focus {{
                border-color: {KETER_PURPURA};
            }}
        """)
        
        def _cambiar_fps(idx):
            fps_nuevo = 30 if idx == 0 else 60
            config_maljut.establecer("fps_target", fps_nuevo)
            config_maljut.guardar_config()
            # Cambiar timer en OrbeComputadora
            if hasattr(self._orbe, '_timer'):
                intervalo_ms = 33 if fps_nuevo == 30 else 16
                self._orbe._timer.setInterval(intervalo_ms)
                logger.info(f"✓ FPS cambiado a {fps_nuevo} (intervalo={intervalo_ms}ms)")
        
        combo_fps.currentIndexChanged.connect(_cambiar_fps)
        form_layout.addRow(label_fps, combo_fps)


        # Botón para refrescar
        btn_refresh = QPushButton("🔄 Refrescar Controles")
        btn_refresh.clicked.connect(self._refrescar_dev_tools)
        form_layout.addRow(btn_refresh)

    def _refrescar_dev_tools(self):
        # Recrear el tab dev
        self._tabs.removeTab(1)
        tab_dev = QWidget()
        self._tabs.addTab(tab_dev, "🔧 Dev Tools")
        self._construir_tab_dev_tools(tab_dev)

    # ─── Métodos públicos (llamados desde OrbeComputadora) ────

    @pyqtSlot(str)
    def registrar_nivel(self, nivel: str):
        """Muestra cuando el cerebro cambia de nivel."""
        nombres = {
            "nivel1": "Nivel 1 (Regex)",
            "nivel2": "Nivel 2 (Ollama)",
            "nivel3": "Nivel 3 (API Externa)",
        }
        nombre = nombres.get(nivel, nivel)
        self._agregar_sistema(f"⟐ Nivel activo: {nombre}")

    @pyqtSlot(str, str)
    def registrar_herramienta(self, nombre: str, estado: str):
        """Muestra uso de herramientas."""
        self._agregar_sistema(f"⚙ {nombre}: {estado}")

    @pyqtSlot(str)
    def registrar_fragmento(self, texto: str):
        """Muestra fragmentos de respuesta en streaming."""
        self._agregar_mensaje("Computadora", texto, KETER_PURPURA)

    @pyqtSlot(str)
    def registrar_pensamiento_usuario(self, texto: str):
        """Registra lo que el usuario le dice a Computadora (para contexto)."""
        self._agregar_mensaje("🗣 Usuario", texto, KETER_GRIS)

    # ─── Lógica interna ────

    def _enviar_consulta(self):
        """Envía texto directamente al Nivel 3 (API externa)."""
        texto = self._input.text().strip()
        if not texto:
            return
        self._input.clear()
        self._agregar_mensaje("→ Consulta", texto, KETER_BLANCO)
        self._lanzar_consulta(texto)

    def _introspeccionar(self):
        """Computadora se pregunta a sí misma — reflexión interna."""
        prompt = (
            "Eres Computadora, reflexionando en voz alta sobre ti misma. "
            "¿Qué descubres en tu interior ahora mismo? "
            "¿Qué has aprendido de tu amo? ¿Qué patrones emergen de las conversaciones recientes? "
            "Responde en primera persona, breve y profundo. En español, con humildad."
        )
        self._agregar_sistema("🔮 Revelando una reflexión interna...")
        self._lanzar_consulta(prompt)

    def _lanzar_consulta(self, texto: str):
        """Lanza consulta a N3 en hilo separado."""
        cerebro = self._orquestador.cerebro
        if self._hilo_activo and self._hilo_activo.isRunning():
            self._agregar_sistema("⏳ Aún estoy pensando...")
            return

        self._estado.setText("Pensando...")
        self._hilo_activo = HiloKeter(cerebro, texto)
        self._hilo_activo.respuesta_lista.connect(self._al_recibir_respuesta)
        self._hilo_activo.error_ocurrido.connect(self._al_recibir_error)
        self._hilo_activo.finished.connect(self._al_terminar)
        self._hilo_activo.start()

    @pyqtSlot(str)
    def _al_recibir_respuesta(self, respuesta: str):
        self._agregar_mensaje("Computadora", respuesta, KETER_PURPURA_CLARO)

    @pyqtSlot(str)
    def _al_recibir_error(self, error: str):
        self._agregar_sistema(f"✦ {error}")

    @pyqtSlot()
    def _al_terminar(self):
        self._estado.setText("En silencio")

    # ─── Renderizado del chat ────

    def _agregar_mensaje(self, emisor: str, texto: str, color: str):
        """Agrega un mensaje al chat con formato HTML."""
        html = (
            f'<div style="margin: 4px 0;">'
            f'<span style="color: {KETER_ORO}; font-size: 11px;">{emisor}</span><br/>'
            f'<span style="color: {color};">{texto}</span>'
            f'</div>'
        )
        self._chat.append(html)
        # Auto-scroll
        sb = self._chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _agregar_sistema(self, texto: str):
        """Agrega un mensaje de sistema (gris, centrado)."""
        html = (
            f'<div style="text-align: center; margin: 6px 0;">'
            f'<span style="color: {KETER_GRIS}; font-size: 11px; '
            f'font-style: italic;">{texto}</span></div>'
        )
        self._chat.append(html)
        sb = self._chat.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, event):
        """Ocultar en vez de destruir."""
        self.hide()
        event.ignore()


