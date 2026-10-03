"""Tests FP-078: Yadáyim HaGolem — Manos Demostrativas Completas (RF-292/293/294)."""
import sys, os, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_rf292_demo2_tiene_cerrar_aplicacion():
    """RF-292: Demo 2 incluye paso cerrar_aplicacion(notepad)."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    # Buscar dentro de _demo_pasos de _demo_herramientas (el self._demo_pasos = [ ... ])
    idx = src.find("def _demo_herramientas")
    bloque = src[idx:idx+3000]
    assert "cerrar_aplicacion" in bloque, "Demo 2 debe cerrar notepad"
    assert "notepad" in bloque


def test_rf293_demo_captura_y_mostrar_existe():
    """RF-293: Método _demo_captura_y_mostrar existe."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "def _demo_captura_y_mostrar" in src


def test_rf293_demo_captura_usa_startfile():
    """RF-293: _demo_captura_y_mostrar abre imagen con os.startfile."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_captura_y_mostrar")
    assert idx != -1, "_demo_captura_y_mostrar debe existir"
    bloque = src[idx:idx+2000]
    assert "os.startfile" in bloque
    assert "tomar_captura_pantalla" in bloque


def test_rf294_demo_narrar_memoria_gevura_existe():
    """RF-294: Método _demo_narrar_memoria_gevura existe."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "def _demo_narrar_memoria_gevura" in src


def test_rf294_no_busca_literal_recuerdo():
    """RF-294: Demo 2 ya no busca literal 'recuerdo' sino 'señor'."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_narrar_memoria_gevura")
    bloque = src[idx:idx+800]
    assert '"señor"' in bloque or "'señor'" in bloque
    assert '"recuerdo"' not in bloque


def test_rf294_usa_calcular_tiempo_activo():
    """RF-294: _demo_narrar_memoria_gevura usa calcular_tiempo_activo."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_narrar_memoria_gevura")
    bloque = src[idx:idx+800]
    assert "calcular_tiempo_activo" in bloque


def test_rf292_demo2_pasos_orden():
    """RF-292: Los pasos de Demo 2 van: abrir→cerrar→captura→buscar→memoria→diagnostico."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_herramientas")
    bloque = src[idx:idx+4500]
    pos_abrir = bloque.find("abrir_aplicacion")
    pos_cerrar = bloque.find("cerrar_aplicacion")
    pos_captura = bloque.find("_demo_captura_y_mostrar")
    pos_memoria = bloque.find("_demo_narrar_memoria_gevura")
    assert pos_abrir > 0 and pos_cerrar > 0 and pos_captura > 0 and pos_memoria > 0
    assert pos_abrir < pos_cerrar < pos_captura < pos_memoria

