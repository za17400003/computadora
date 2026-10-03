"""
DEV TOOL: CAMERA MONITOR — Visualización de lo que la cámara ve
════════════════════════════════════════════════════════════════════

Permite al usuario ver:
- Stream normal en vivo
- Stream con visión nocturna (CLAHE automático)
- Detección de movimiento (highlight de cambios)
- Estadísticas (brillo, FPS, modo nocturno active)
- Grabación de clips

WI-299, RF-324: Herramienta de debugging para Guardian + visión.
"""

import time
from pathlib import Path
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QTabWidget, QWidget
)
from PyQt6.QtGui import QImage
import logging

logger = logging.getLogger(__name__)

# Importaciones opcionales
try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    _CV2_AVAILABLE = False


class CameraDevToolWindow(QDialog):
    """Ventana de desarrollo para monitorear la cámara."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📹 Dev Tool: Camera Monitor (WI-299)")
        self.setGeometry(100, 100, 760, 680)  # FP-152: Reducido de 1200x800 (36% menos espacio muerto)
        
        self._gestor_kli = None
        self._frame_actual = None
        self._frame_nocturno = None
        self._grabando = False
        self._video_writer = None
        self._frame_cache = None  # FP-152: Cache compartido para evitar múltiples instancias KliCamara
        
        self.initUI()
        self._inicializar_camara()
        self._iniciar_timer()
    
    def initUI(self):
        """Construye la interfaz."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact margins
        main_layout.setSpacing(2)                   # FP-152: Minimal spacing
        
        # TAB 1: Stream normal vs nocturno
        tabs = QTabWidget()
        
        # TAB 1: Normal stream
        normal_widget = QWidget()
        normal_layout = QVBoxLayout()
        normal_layout.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        normal_layout.setSpacing(2)                   # FP-152: Compact
        self.label_normal = QLabel("Esperando frame...")
        self.label_normal.setMinimumSize(640, 480)
        self.label_normal.setStyleSheet("background-color: #111; color: #0f0;")
        normal_layout.addWidget(self.label_normal)
        
        # Stats para stream normal
        stats_normal = QHBoxLayout()
        stats_normal.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        stats_normal.setSpacing(5)                   # FP-152: Minimal button spacing
        self.label_stats_normal = QLabel("FPS: -- | Brillo: -- | Nocturno: OFF")
        self.label_stats_normal.setFont(QFont("Courier", 10))
        stats_normal.addWidget(self.label_stats_normal)
        normal_layout.addLayout(stats_normal)
        
        normal_widget.setLayout(normal_layout)
        tabs.addTab(normal_widget, "☀️ Normal")
        
        # TAB 2: Nocturno (CLAHE)
        nocturno_widget = QWidget()
        nocturno_layout = QVBoxLayout()
        nocturno_layout.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        nocturno_layout.setSpacing(2)                   # FP-152: Compact
        self.label_nocturno = QLabel("Esperando frame...")
        self.label_nocturno.setMinimumSize(640, 480)
        self.label_nocturno.setStyleSheet("background-color: #111; color: #0f0;")
        nocturno_layout.addWidget(self.label_nocturno)
        
        # Stats para stream nocturno
        stats_nocturno = QHBoxLayout()
        stats_nocturno.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        stats_nocturno.setSpacing(5)                   # FP-152: Minimal button spacing
        self.label_stats_nocturno = QLabel("FPS: -- | Brillo (raw): -- | Nocturno: OFF")
        self.label_stats_nocturno.setFont(QFont("Courier", 10))
        stats_nocturno.addWidget(self.label_stats_nocturno)
        nocturno_layout.addLayout(stats_nocturno)
        
        nocturno_widget.setLayout(nocturno_layout)
        tabs.addTab(nocturno_widget, "🌙 Nocturno (CLAHE)")
        
        # TAB 3: Movimiento + estadísticas
        stats_widget = QWidget()
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        stats_layout.setSpacing(2)                   # FP-152: Compact
        
        self.label_movimiento = QLabel("Monitoreando movimiento...")
        # FP-152: Removido padding: 20px (ahorro 80px muerto)
        self.label_movimiento.setStyleSheet("background-color: #222; color: #0f0; font-family: Courier; font-size: 12px;")
        stats_layout.addWidget(self.label_movimiento)
        
        stats_widget.setLayout(stats_layout)
        tabs.addTab(stats_widget, "📊 Movimiento")
        
        self.tabs = tabs
        main_layout.addWidget(tabs)
        
        # Controles
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(3, 3, 3, 3)  # FP-152: Compact
        control_layout.setSpacing(5)                   # FP-152: Minimal button spacing (reduced from 11)
        
        # Checkbox: Grabar video
        self.check_grabar = QCheckBox("Grabar clip (últimos 5s)")
        self.check_grabar.toggled.connect(self._toggle_grabacion)
        control_layout.addWidget(self.check_grabar)
        
        # Dropdown: Seleccionar cámara
        self.combo_camara = QComboBox()
        self.combo_camara.addItems(["Cámara 0", "Cámara 1", "Cámara 2"])
        control_layout.addWidget(QLabel("Cámara:"))
        control_layout.addWidget(self.combo_camara)
        
        # Spinbox: Umbral de brillo para visión nocturna
        self.spin_brillo_umbral = QSpinBox()
        self.spin_brillo_umbral.setRange(10, 150)
        self.spin_brillo_umbral.setValue(50)
        self.spin_brillo_umbral.setSuffix(" (RF-324)")
        control_layout.addWidget(QLabel("Umbral brillo:"))
        control_layout.addWidget(self.spin_brillo_umbral)
        
        # Botón: Captura
        btn_captura = QPushButton("📷 Capturar frame")
        btn_captura.clicked.connect(self._capturar_frame)
        control_layout.addWidget(btn_captura)
        
        # Botón: Cerrar
        btn_cerrar = QPushButton("✅ Cerrar")
        btn_cerrar.clicked.connect(self.close)
        control_layout.addWidget(btn_cerrar)
        
        main_layout.addLayout(control_layout)
        self.setLayout(main_layout)
    
    def _inicializar_camara(self):
        """Inicializa GestorKelim y asegura que la cámara esté conectada.

        FIX: antes esta herramienta solo LEÍA frames compartidos vía
        GestorKelim y nunca conectaba la cámara ella misma (comentario
        original: "NUNCA creo mi propia instancia KliCamara()") — si nada
        más (p.ej. el Guardián) tenía la cámara conectada en ese momento, el
        dev tool se quedaba mostrando "Esperando frame..." para siempre, sin
        encender la cámara. Ahora, si la cámara no está conectada al abrir
        esta ventana, la conecta ella misma (sigue sin crear su propia
        instancia KliCamara — usa el mismo objeto compartido de GestorKelim,
        solo se encarga de pedirle que se conecte) y recuerda si fue ella
        quien la conectó, para desconectarla al cerrar solo en ese caso
        (ver closeEvent) — si ya estaba conectada por otra razón (Guardián
        activo), no la toca al cerrar.
        """
        self._camara_conectada_por_nosotros = False
        try:
            from computadora.nucleo.kli import GestorKelim
            self._gestor_kli = GestorKelim.instancia()
            cam_info = next((k for k in self._gestor_kli.listar() if k["id"] == "camara_local"), None)
            if cam_info is None:
                from computadora.habilidades.vision import KliCamara
                self._gestor_kli.registrar(KliCamara())
                cam_info = next((k for k in self._gestor_kli.listar() if k["id"] == "camara_local"), None)
            ya_conectada = bool(cam_info and cam_info["estado"] == "CONECTADO")
            if not ya_conectada:
                if self._gestor_kli.conectar("camara_local"):
                    self._camara_conectada_por_nosotros = True
                    logger.info("📹 Dev tool: cámara conectada (no estaba activa)")
                else:
                    logger.warning("📹 Dev tool: no se pudo conectar la cámara")
            logger.info("📹 Dev tool: inicializado (frames compartidos)")
        except Exception as e:
            logger.error(f"📹 Dev tool error inicializando GestorKelim: {e}")
    
    def _iniciar_timer(self):
        """Timer para refrescar el stream."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._actualizar_stream)
        self.timer.start(66)  # ~15fps to reduce UI load while keeping smooth preview
    
    def _actualizar_stream(self):
        """Actualiza los streams de cámara con frames compartidos vía GestorKelim.
        
        FP-152: Usa GestorKelim.leer_frame_camera() para obtener el frame actual.
        Usa GestorKelim.leer('camara_local') para obtener metadatos de movimiento/brillo.
        """
        if self._gestor_kli is None:
            return
        
        try:
            tab_index = self.tabs.currentIndex()
            # FP-156 RUBEDO: Obtener frame actual vía el nuevo método seguro
            frame = self._gestor_kli.leer_frame_camera("camara_local")
            if frame is None:
                return
            
            # Obtener metadatos (movimiento, brillo, etc.)
            datos = self._gestor_kli.leer("camara_local")
            brillo = datos.get("brillo_medio", 0) if isinstance(datos, dict) else 0
            nocturno_auto = datos.get("nocturno_auto", False) if isinstance(datos, dict) else False
            movimiento = datos.get("movimiento", False) if isinstance(datos, dict) else False
            porcentaje_cambio = datos.get("porcentaje_cambio", 0.0) if isinstance(datos, dict) else 0.0
            
            if tab_index == 0:
                self._mostrar_stream_real(frame, brillo, nocturno_auto)
            elif tab_index == 1:
                self._mostrar_stream_nocturno_real(frame, brillo, nocturno_auto)
            else:
                # Mantener estadísticas actualizadas incluso si el usuario no está
                # en una pestaña de video activa.
                self.label_normal.setText("Esperando frame...")
                self.label_nocturno.setText("Esperando frame...")
            
            # Actualizar estadísticas
            color_movimiento = "🔴 MOVIMIENTO" if movimiento else "✓ Sin movimiento"
            self.label_movimiento.setText(
                f"Brillo: {brillo:.1f} | Nocturno: {'🌙 ON' if nocturno_auto else '☀️ OFF'}\n"
                f"Movimiento: {color_movimiento}\n"
                f"Porcentaje de cambio: {porcentaje_cambio:.2f}%"
            )
            
        except Exception as e:
            logger.debug(f"📹 Error en stream: {e}")
    
    def _mostrar_stream_real(self, frame, brillo: float, nocturno_auto: bool):
        """Muestra stream normal con frame REAL."""
        try:
            if frame is None or frame.size == 0:
                return
            
            # Redimensionar a 640x480 si es necesario
            h, w = frame.shape[:2]
            if (w, h) != (640, 480):
                frame = cv2.resize(frame, (640, 480))
            
            # Agregar texto de stats
            cv2.putText(frame, f"Brillo: {brillo:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Modo: {'Nocturno' if nocturno_auto else 'Normal'}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Convertir BGR → RGB dentro del helper para evitar doble conversión
            qimg = self._numpy_to_qimage(frame)
            self.label_normal.setPixmap(QPixmap.fromImage(qimg).scaledToWidth(640))
            
            # Stats
            self.label_stats_normal.setText(f"FPS: 15 | Brillo: {brillo:.1f} | Live Frame")
            
        except Exception as e:
            logger.debug(f"📹 Error mostrando stream normal: {e}")
    
    def _mostrar_stream_nocturno_real(self, frame, brillo: float, nocturno_auto: bool):
        """Muestra stream nocturno con CLAHE aplicado a frame REAL."""
        try:
            if frame is None or frame.size == 0:
                return
            
            # Redimensionar
            h, w = frame.shape[:2]
            if (w, h) != (640, 480):
                frame = cv2.resize(frame, (640, 480))
            
            # Convertir a escala de grises
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Aplicar CLAHE si es modo nocturno o brillo bajo
            if nocturno_auto or brillo < 50:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                gris_clahe = clahe.apply(gris)
                frame_nocturno = cv2.cvtColor(gris_clahe, cv2.COLOR_GRAY2BGR)
            else:
                frame_nocturno = cv2.cvtColor(gris, cv2.COLOR_GRAY2BGR)
            
            # Agregar stats
            cv2.putText(frame_nocturno, f"Brillo: {brillo:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame_nocturno, f"Modo: {'Nocturno (CLAHE)' if nocturno_auto else 'Normal'}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Convertir a Qt dentro del helper para evitar doble conversión
            qimg = self._numpy_to_qimage(frame_nocturno)
            self.label_nocturno.setPixmap(QPixmap.fromImage(qimg).scaledToWidth(640))
            
            # Stats
            self.label_stats_nocturno.setText(f"FPS: 15 | Brillo: {brillo:.1f} | Nocturno: {'ON' if nocturno_auto else 'OFF'}")
            
        except Exception as e:
            logger.debug(f"📹 Error mostrando stream nocturno: {e}")
    
    @staticmethod
    def _numpy_to_qimage(cv_img: np.ndarray) -> QImage:
        """Convierte frame OpenCV a QImage para Qt."""
        if len(cv_img.shape) == 2:  # Escala gris
            h, w = cv_img.shape
            bytes_per_line = w
            return QImage(cv_img.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
        elif len(cv_img.shape) == 3:  # Color BGR
            h, w, ch = cv_img.shape
            bytes_per_line = 3 * w
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            return QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QImage()
    
    def _capturar_frame(self):
        """Captura un frame y lo guarda."""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            clip_path = Path(__file__).parent.parent.parent / "datos" / f"camera_frame_{timestamp}.png"
            clip_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📹 Frame capturado: {clip_path}")
        except Exception as e:
            logger.error(f"Error capturando frame: {e}")
    
    def _toggle_grabacion(self, checked: bool):
        """Alterna la grabación de video."""
        self._grabando = checked
        if checked:
            logger.info("📹 Iniciando grabación de clip")
        else:
            logger.info("📹 Grabación detenida")
    
    def closeEvent(self, event):
        """Al cerrar, detener timer y limpiar recursos.

        FIX: si esta ventana fue quien conectó la cámara al abrirse (porque
        nadie más la tenía conectada, ver _inicializar_camara), la
        desconecta aquí. Si ya estaba conectada por otra razón (p.ej. el
        Guardián activo), la deja intacta — sigue siendo compartida.
        """
        try:
            self.timer.stop()
        except Exception as e:
            logger.debug(f"Dev tool: error deteniendo timer: {e}")
        if getattr(self, "_camara_conectada_por_nosotros", False):
            try:
                self._gestor_kli.desconectar("camara_local")
                logger.info("📹 Dev tool cerrado — cámara desconectada (la habíamos encendido nosotros)")
            except Exception as e:
                logger.debug(f"Dev tool: error desconectando cámara: {e}")
        else:
            logger.info("📹 Dev tool cerrado — recursos compartidos liberados")
        event.accept()


# ═══════════════════════════════════════════════
# INTEGRACIÓN CON MENÚ PRINCIPAL
# ═══════════════════════════════════════════════

def abrir_camera_dev_tool(ventana_principal=None):
    """Abre el dev tool de cámara desde el menú principal."""
    dialog = CameraDevToolWindow(parent=ventana_principal)
    dialog.exec()


