"""
Configuración del tema visual del orbe en Dev Tools.
- FPS configurable (30/60)
- Gestión de temas visuales (añadir/eliminar temas registrados dinámicamente)
- Persistencia de configuración

Nota 2026-10-02: se eliminó la detección de GPU y el selector Legacy/
Ferrofluido — el ferrofluido se descartó por completo, queda un solo tema
real (ClasicoTheme). El nombre del archivo persistido y la clave JSON
"maljut_tipo" se conservan sin cambios para no invalidar configuraciones
de instalaciones existentes.
"""

import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QListWidget, QInputDialog
)
from loguru import logger

from computadora.interfaz.tema_visual import TemaVisualTipo


class ConfiguracionVisualDev:
    """Gestiona configuración persistente del tema visual."""

    def __init__(self):
        self.config_path = Path(__file__).resolve().parent.parent.parent / "datos" / "maljut_dev_config.json"
        self.config = self._cargar_config()

    def _cargar_config(self) -> dict:
        """Carga configuración desde archivo o retorna defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    if 'custom_themes' not in cfg:
                        cfg['custom_themes'] = []
                    return cfg
            except Exception as e:
                logger.warning(f"No se pudo cargar maljut_dev_config.json: {e}")

        return {
            "maljut_tipo": TemaVisualTipo.CLASICO.value,
            "fps_target": 30,  # 30 o 60
            "custom_themes": [],
        }

    def guardar_config(self) -> bool:
        """Guarda configuración a archivo."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Configuración visual guardada: {self.config}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando maljut_dev_config.json: {e}")
            return False

    def obtener(self, clave: str, default=None):
        """Obtiene un valor de configuración."""
        return self.config.get(clave, default)

    def establecer(self, clave: str, valor):
        """Establece un valor en configuración."""
        self.config[clave] = valor

    def tipo_tema(self) -> TemaVisualTipo:
        """Retorna el tipo de tema visual configurado."""
        tipo_str = self.config.get("maljut_tipo", TemaVisualTipo.CLASICO.value)
        return TemaVisualTipo.from_str(tipo_str)

    def fps_configurado(self) -> int:
        """Retorna FPS configurado (30 o 60)."""
        fps = self.config.get("fps_target", 30)
        return max(30, min(60, int(fps)))


class VentanaConfiguracionVisual(QDialog):
    """Ventana de Dev Tools para configurar el tema visual y el rendimiento."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_mgr = ConfiguracionVisualDev()
        # Registrar temas personalizados desde config
        try:
            from computadora.interfaz.tema_visual import ThemeFactory
            for t in self.config_mgr.config.get('custom_themes', []):
                ThemeFactory.registrar_tema(t)
        except Exception:
            pass

        self.setWindowTitle("⚙️ Configuración Visual — Dev Tools")
        self.setGeometry(200, 200, 600, 350)
        self._crear_ui()
        self._cargar_valores()

    def _crear_ui(self):
        """Crea la interfaz."""
        layout = QVBoxLayout()

        # === SECCIÓN 1: Rendimiento ===
        group_perf = QGroupBox("Rendimiento")
        layout_perf = QVBoxLayout()

        row_fps = QHBoxLayout()
        row_fps.addWidget(QLabel("Target FPS:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30", "60"])
        self.combo_fps.setCurrentText(str(self.config_mgr.fps_configurado()))
        row_fps.addWidget(self.combo_fps)
        row_fps.addStretch()
        layout_perf.addLayout(row_fps)

        group_perf.setLayout(layout_perf)
        layout.addWidget(group_perf)

        # === SECCIÓN 2: Gestión de Temas ===
        group_themes = QGroupBox("Gestión de Temas")
        layout_themes = QVBoxLayout()

        layout_themes.addWidget(QLabel("Tema activo: Clásico (orbe de partículas)"))

        self.lista_temas = QListWidget()
        layout_themes.addWidget(self.lista_temas)

        row_theme_buttons = QHBoxLayout()
        btn_add_theme = QPushButton("➕ Añadir tema")
        btn_remove_theme = QPushButton("➖ Eliminar tema")
        btn_add_theme.clicked.connect(self._on_add_theme)
        btn_remove_theme.clicked.connect(self._on_remove_theme)
        row_theme_buttons.addWidget(btn_add_theme)
        row_theme_buttons.addWidget(btn_remove_theme)
        row_theme_buttons.addStretch()
        layout_themes.addLayout(row_theme_buttons)

        group_themes.setLayout(layout_themes)
        layout.addWidget(group_themes)

        # === BOTONES ===
        layout_botones = QHBoxLayout()
        btn_guardar = QPushButton("💾 Guardar y Aplicar")
        btn_guardar.clicked.connect(self.guardar_config)
        btn_cancelar = QPushButton("✕ Cancelar")
        btn_cancelar.clicked.connect(self.reject)

        layout_botones.addWidget(btn_guardar)
        layout_botones.addWidget(btn_cancelar)
        layout.addLayout(layout_botones)

        self.setLayout(layout)

    def _cargar_valores(self):
        """Carga valores guardados desde config_mgr."""
        self.combo_fps.setCurrentText(str(self.config_mgr.fps_configurado()))

        try:
            from computadora.interfaz.tema_visual import ThemeFactory
            self.lista_temas.clear()
            for t in ThemeFactory.listar_temas():
                self.lista_temas.addItem(t)
        except Exception:
            pass

    def _on_add_theme(self):
        """Añade un tema personalizado simple (nombre)."""
        text, ok = QInputDialog.getText(self, "Añadir Tema", "Nombre del nuevo tema:")
        if not ok or not text:
            return
        name = str(text).strip()
        if not name:
            return
        try:
            from computadora.interfaz.tema_visual import ThemeFactory
            if ThemeFactory.registrar_tema(name):
                self.lista_temas.addItem(name)
                QMessageBox.information(self, "✅ Tema creado", f"Tema '{name}' creado correctamente")
            else:
                QMessageBox.warning(self, "⚠️ No creado", f"No se pudo crear el tema '{name}'. Puede ser builtin o inválido.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error creando tema: {e}")

    def _on_remove_theme(self):
        """Elimina el tema seleccionado si no es builtin (ClasicoTheme)."""
        sel = self.lista_temas.currentItem()
        if not sel:
            QMessageBox.warning(self, "⚠️ Selección requerida", "Selecciona un tema para eliminar.")
            return
        name = sel.text()
        try:
            from computadora.interfaz.tema_visual import ThemeFactory
            if ThemeFactory.es_builtin(name):
                QMessageBox.information(self, "🔒 Tema protegido", f"El tema '{name}' es el predeterminado y no puede eliminarse.")
                return
            if ThemeFactory.eliminar_tema(name):
                self.lista_temas.takeItem(self.lista_temas.row(sel))
                QMessageBox.information(self, "✅ Eliminado", f"Tema '{name}' eliminado")
            else:
                QMessageBox.warning(self, "⚠️ No eliminado", f"No se pudo eliminar '{name}'")
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error eliminando tema: {e}")

    def guardar_config(self):
        """Guarda la configuración."""
        fps_anterior = self.config_mgr.fps_configurado()
        nuevo_fps = int(self.combo_fps.currentText())
        self.config_mgr.establecer("fps_target", nuevo_fps)

        # Persistir temas personalizados en config
        try:
            from computadora.interfaz.tema_visual import ThemeFactory
            custom = ThemeFactory.listar_custom()
            self.config_mgr.establecer('custom_themes', custom)
        except Exception:
            pass

        if self.config_mgr.guardar_config():
            if fps_anterior != nuevo_fps:
                QMessageBox.information(
                    self, "✅ Configuración Guardada",
                    f"FPS: {nuevo_fps}\n\n⚠️ Reinicia COMPUTADORA para aplicar cambios de rendimiento"
                )
            else:
                QMessageBox.information(self, "✅ Configuración Guardada", "Tema aplicado inmediatamente")
            self.accept()
        else:
            QMessageBox.critical(self, "❌ Error", "No se pudo guardar la configuración")


def abrir_configuracion_visual(parent=None):
    """Abre el diálogo de configuración del tema visual."""
    dialog = VentanaConfiguracionVisual(parent=parent)
    dialog.exec()
