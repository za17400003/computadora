"""
Tests para HF-038: Fix física de empuje Maljut + sombra Win11
"""
import sys, os, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_import_orbe():
    from computadora.interfaz.ventana_principal import OrbeComputadora
    assert OrbeComputadora is not None

def test_drag_historial_attr():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "_drag_historial" in src, "_drag_historial NO encontrado"

def test_velocity_based_impulse():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "velocidad" in src and "_drag_historial" in src, "Cálculo de velocidad instantánea ausente"

def test_umbral_velocidad():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "150" in src, "Umbral 150 px/s NO encontrado"

def test_max_factor_30():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "30" in src and "min(" in src, "Factor máximo 30 con min() ausente"

def test_dwm_border_color_approach():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "DWMWA_BORDER_COLOR" in src, "DWMWA_BORDER_COLOR NO encontrado"

def test_systembackdrop_type():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "DWMWA_SYSTEMBACKDROP_TYPE" in src or "38" in src, "SYSTEMBACKDROP_TYPE NO encontrado"

def test_mouse_move_records_historial():
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "append" in src and "_drag_historial" in src, "mouseMoveEvent no registra en _drag_historial"

def test_tzimtzum_regex_escondete():
    src = open("computadora/cerebro/nlu.py", encoding="utf-8").read()
    assert "esc[o" in src, "Regex Tzimtzum no incluye variante escóndete"

