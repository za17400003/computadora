"""
FP-144 WI-XXX: Diálogo de consentimiento explícito para registro facial.

Aparece en primer boot cuando FACEREC_RECORD.json NO existe.
Usuario elige: registrar ahora, saltarla esta sesión, o siempre saltarla.
"""

from pathlib import Path
from typing import Literal
import json

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QMessageBox, QTextEdit
)
from loguru import logger


class DialogoConsentimientoFacial(QDialog):
    """
    Dialog para solicitar consentimiento explícito sobre registro facial.
    
    Flujo:
    1. Si FACEREC_RECORD.json existe → no mostrar dialog
    2. Si no existe + user nunca dijo "siempre saltarla" → mostrar dialog
    3. Si "siempre saltarla" fue guardado → usar silenciosamente
    
    Opciones:
    - "Registrar cara ahora": Ejecuta facial registration script (CONTINUE)
    - "Saltarla esta sesión": Usa --skip-facerec para boot actual (SESSION_SKIP)
    - "Siempre saltarla": Guarda en config, nunca preguntar (ALWAYS_SKIP)
    """
    
    # Resultado posibles
    CONTINUE = "continue"           # User wants to register
    SESSION_SKIP = "session_skip"   # Skip only this session
    ALWAYS_SKIP = "always_skip"     # Save preference, never ask again
    CANCELLED = "cancelled"         # Dialog closed without decision
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_choice = self.CANCELLED
        self._setup_ui()
        self._load_styles()
        
        logger.info("DialogoConsentimientoFacial: Creado")
    
    def _setup_ui(self):
        """Configura la interfaz del dialog."""
        self.setWindowTitle("Registro facial")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # ─── Título ───
        title = QLabel("Registro facial de Computadora")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # ─── Explicación ───
        explanation = QTextEdit()
        explanation.setReadOnly(True)
        explanation.setPlainText(
            "COMPUTADORA necesita registrar tu rostro para identificarte en futuros boots.\n\n"
            
            "¿Por qué pasa esto cada vez?\n"
            "Cada vez que enciendes COMPUTADORA, ella 'renace' limpia, "
            "sin memoria del último ciclo.\n\n"
            
            "Para verificar tu identidad sin pedirte contraseña cada vez, "
            "usa registro facial de Windows (Face Recognition).\n\n"
            
            "¿Qué hará COMPUTADORA con tu rostro?\n"
            "• Solo se almacenará localmente en tu computadora\n"
            "• No se envía a servidores externos\n"
            "• Solo se usa para verificación al boot\n"
            "• Puedes borrar el registro en cualquier momento\n\n"
            
            "¿Qué quieres hacer?"
        )
        explanation.setMaximumHeight(280)
        layout.addWidget(explanation)
        
        # ─── Botones ───
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Botón 1: Registrar ahora
        btn_register = QPushButton("✓ Registrar cara ahora")
        btn_register.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        btn_register.setMinimumHeight(50)
        btn_register.setStyleSheet(
            "QPushButton { "
            "background-color: #2ecc71; color: white; border-radius: 6px; "
            "border: 2px solid #27ae60; "
            "} "
            "QPushButton:hover { background-color: #27ae60; } "
        )
        btn_register.clicked.connect(self._on_register)
        buttons_layout.addWidget(btn_register)
        
        # Botón 2: Saltarla esta sesión
        btn_skip_session = QPushButton("→ Saltarla esta sesión")
        btn_skip_session.setFont(QFont("Segoe UI", 11))
        btn_skip_session.setMinimumHeight(50)
        btn_skip_session.setStyleSheet(
            "QPushButton { "
            "background-color: #3498db; color: white; border-radius: 6px; "
            "border: 2px solid #2980b9; "
            "} "
            "QPushButton:hover { background-color: #2980b9; } "
        )
        btn_skip_session.clicked.connect(self._on_skip_session)
        buttons_layout.addWidget(btn_skip_session)
        
        # Botón 3: Siempre saltarla
        btn_always_skip = QPushButton("⊘ Siempre saltarla (guardar preferencia)")
        btn_always_skip.setFont(QFont("Segoe UI", 11))
        btn_always_skip.setMinimumHeight(50)
        btn_always_skip.setStyleSheet(
            "QPushButton { "
            "background-color: #e74c3c; color: white; border-radius: 6px; "
            "border: 2px solid #c0392b; "
            "} "
            "QPushButton:hover { background-color: #c0392b; } "
        )
        btn_always_skip.clicked.connect(self._on_always_skip)
        buttons_layout.addWidget(btn_always_skip)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def _load_styles(self):
        """Aplica estilos al dialog."""
        self.setStyleSheet(
            "QDialog { background-color: #1e1e1e; color: #ffffff; } "
            "QTextEdit { background-color: #2d2d2d; color: #e0e0e0; border: 1px solid #444; }"
            "QLabel { color: #ffffff; } "
        )
    
    def _on_register(self):
        """Usuario elige registrar cara ahora."""
        logger.info("DialogoConsentimientoFacial: Usuario eligió REGISTRAR cara ahora")
        try:
            from computadora.utilidad.registro_consentimiento_facial import obtener_registro_consentimiento
            auditoria = obtener_registro_consentimiento()
            auditoria.registrar_decision(
                decision="continue",
                resultado="success",
                detalles="Usuario eligió registrar cara ahora"
            )
        except Exception as e:
            logger.debug(f"DialogoConsentimientoFacial: Error registrando auditoría: {e}")
        
        self.result_choice = self.CONTINUE
        self.accept()
    
    def _on_skip_session(self):
        """Usuario elige saltarla solo esta sesión."""
        logger.info("DialogoConsentimientoFacial: Usuario eligió SALTAR solo esta sesión")
        try:
            from computadora.utilidad.registro_consentimiento_facial import obtener_registro_consentimiento
            auditoria = obtener_registro_consentimiento()
            auditoria.registrar_decision(
                decision="session_skip",
                resultado="success",
                detalles="Usuario eligió saltarla solo esta sesión"
            )
        except Exception as e:
            logger.debug(f"DialogoConsentimientoFacial: Error registrando auditoría: {e}")
        
        self.result_choice = self.SESSION_SKIP
        self.accept()
    
    def _on_always_skip(self):
        """Usuario elige siempre saltarla (guardar preferencia)."""
        # Confirmación
        reply = QMessageBox.question(
            self,
            "Confirmar decisión",
            "¿Estás seguro de que quieres SIEMPRE saltarla?\n\n"
            "Tendrás que registrar tu rostro manualmente si cambias de opinión.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("DialogoConsentimientoFacial: Usuario eligió SIEMPRE SALTARLA")
            try:
                from computadora.utilidad.registro_consentimiento_facial import obtener_registro_consentimiento
                auditoria = obtener_registro_consentimiento()
                auditoria.registrar_decision(
                    decision="always_skip",
                    resultado="success",
                    detalles="Usuario confirmó siempre saltarla (guardado en _config/gilgul_config.json)"
                )
            except Exception as e:
                logger.debug(f"DialogoConsentimientoFacial: Error registrando auditoría: {e}")
            
            self.result_choice = self.ALWAYS_SKIP
            self._save_always_skip_preference()
            self.accept()
    
    def _save_always_skip_preference(self):
        """Guarda preferencia de 'siempre saltarla' en config."""
        try:
            config_dir = Path(__file__).resolve().parent.parent.parent / "_config"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = config_dir / "gilgul_config.json"
            config_data = {}
            
            if config_file.exists():
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            
            config_data["always_skip_facial_registration"] = True
            config_data["timestamp_saved"] = str(__import__("datetime").datetime.now().isoformat())
            
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"DialogoConsentimientoFacial: Preferencia guardada en {config_file}")
        except Exception as e:
            logger.error(f"DialogoConsentimientoFacial: Error guardando preferencia: {e}")


def should_show_consent_dialog() -> bool:
    """
    Retorna True si el dialog debe mostrarse.
    
    Condiciones:
    - FACEREC_RECORD.json NO existe
    - Y NO existe preferencia "siempre saltarla" en config
    """
    # Verificar si FACEREC_RECORD.json existe
    facerec_path = Path(__file__).resolve().parent.parent.parent / "datos" / "FACEREC_RECORD.json"
    if facerec_path.exists():
        logger.debug("DialogoConsentimientoFacial: FACEREC_RECORD.json existe, no mostrar dialog")
        return False
    
    # Verificar si existe preferencia "siempre saltarla"
    config_file = Path(__file__).resolve().parent.parent.parent / "_config" / "gilgul_config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            if config.get("always_skip_facial_registration", False):
                logger.info("DialogoConsentimientoFacial: Preferencia 'siempre saltarla' activa, skip dialog")
                return False
        except Exception as e:
            logger.debug(f"DialogoConsentimientoFacial: Error leyendo config: {e}")
    
    logger.info("DialogoConsentimientoFacial: Mostrando dialog de consentimiento")
    return True


def get_always_skip_preference() -> bool:
    """Retorna True si usuario ha guardado 'siempre saltarla'."""
    config_file = Path(__file__).resolve().parent.parent.parent / "_config" / "gilgul_config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("always_skip_facial_registration", False)
        except Exception as e:
            logger.debug(f"DialogoConsentimientoFacial: Error leyendo config: {e}")
    return False


