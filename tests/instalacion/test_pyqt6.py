#!/usr/bin/env python
"""Test PyQt6 en Windows - Verifique si interfaz gráfica está disponible"""

import os
import sys
import pytest


def test_pyqt6_available():
    if sys.platform != 'win32' and not os.environ.get('DISPLAY'):
        pytest.skip('Entorno sin display gráfico')

    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle('COMPUTADORA — Test PyQt6')
    window.setGeometry(100, 100, 400, 200)

    label = QLabel('✓ COMPUTADORA PyQt6 Funciona Correctamente')
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)

    window.show()
    assert window.isVisible()
    app.processEvents()
    app.quit()
