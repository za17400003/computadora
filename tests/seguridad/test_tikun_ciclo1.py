"""
Test para VentanaKeter — FP-105 Or HaGanuz — Ciclo Tikún 1.
Verifica imports, estructura de clases, señales y constantes.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_ventana_keter_import():
    """Módulo importa sin error."""
    from computadora.interfaz import ventana_keter  # noqa: F401


def test_clases_existen():
    """VentanaKeter y HiloKeter existen."""
    from computadora.interfaz.ventana_keter import VentanaKeter, HiloKeter
    assert VentanaKeter is not None
    assert HiloKeter is not None


def test_constantes_keter():
    """Constantes de color Keter definidas."""
    from computadora.interfaz.ventana_keter import (
        KETER_FONDO, KETER_PANEL, KETER_INPUT,
        KETER_PURPURA, KETER_ORO, KETER_GRIS,
    )
    assert KETER_FONDO.startswith("#")
    assert KETER_PANEL.startswith("#")
    assert KETER_INPUT.startswith("#")
    assert KETER_PURPURA.startswith("#")
    assert KETER_ORO == "#FFD700"
    assert KETER_GRIS.startswith("#")


def test_estilo_keter():
    """ESTILO_KETER contiene reglas CSS para los widgets."""
    from computadora.interfaz.ventana_keter import ESTILO_KETER
    assert "QTextBrowser" in ESTILO_KETER
    assert "QLineEdit" in ESTILO_KETER
    assert "QPushButton" in ESTILO_KETER
    assert "VentanaKeter" in ESTILO_KETER


def test_gate_lock_existe():
    """_gate_lock existe para thread-safety."""
    from computadora.interfaz.ventana_keter import _gate_lock
    import threading
    assert isinstance(_gate_lock, type(threading.Lock()))


def test_hilo_keter_signals():
    """HiloKeter tiene las señales esperadas."""
    from computadora.interfaz.ventana_keter import HiloKeter
    assert hasattr(HiloKeter, "respuesta_lista")
    assert hasattr(HiloKeter, "fragmento_listo")
    assert hasattr(HiloKeter, "error_ocurrido")


def test_ventana_keter_slots_definidos():
    """VentanaKeter tiene los slots públicos esperados."""
    from computadora.interfaz.ventana_keter import VentanaKeter
    assert callable(getattr(VentanaKeter, "registrar_nivel", None))
    assert callable(getattr(VentanaKeter, "registrar_herramienta", None))
    assert callable(getattr(VentanaKeter, "registrar_fragmento", None))
    assert callable(getattr(VentanaKeter, "registrar_pensamiento_usuario", None))

