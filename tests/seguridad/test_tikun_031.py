"""Tests para FP-076 — Ohr HaKlei Mefateaj + Demo fixes."""
import sys, os, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_rf289_demo_motor_usa_cola_vacia():
    """El motor de pasos de la demo debe usar cola_vacia, no habla_terminada."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    # Dentro de _demo_ejecutar_paso, debe conectar cola_vacia
    bloque = src[src.index("def _demo_ejecutar_paso"):]
    bloque = bloque[:bloque.index("\n    def ")]
    assert "cola_vacia.connect" in bloque
    assert "habla_terminada.connect" not in bloque


def test_rf290_fuzzy_demo2_afirmativos():
    """La lista de afirmativos incluye más palabras + fuzzy match."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "SequenceMatcher" in src
    for word in ("ok", "bueno", "sale", "perfecto", "listo"):
        assert f'"{word}"' in src


def test_rf291_sanitizar_para_voz_existe():
    """El método _sanitizar_para_voz existe en la clase."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    assert hasattr(OrbeComputadora, '_sanitizar_para_voz')


def test_rf291_sanitizar_rutas():
    """_sanitizar_para_voz limpia rutas de archivo para voz natural."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    resultado = OrbeComputadora._sanitizar_para_voz(
        "Archivo: C:\\Users\\test\\.venv\\Lib\\site-packages\\paquete\\archivo.txt"
    )
    assert "barra" not in resultado.lower()
    assert "\\" not in resultado
    assert ".venv" not in resultado


def test_rf291_sanitizar_barra_diagonal():
    """_sanitizar_para_voz elimina / y \\ para que TTS no diga 'barra diagonal'."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    resultado = OrbeComputadora._sanitizar_para_voz("ruta/al/archivo")
    assert "/" not in resultado


def test_rf291_sanitizar_guion_bajo():
    """_sanitizar_para_voz reemplaza _ con espacio."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    resultado = OrbeComputadora._sanitizar_para_voz("nombre_del_archivo")
    assert "_" not in resultado
    assert "nombre del archivo" in resultado


def test_rf286_demo_ejecutar_herramienta_visual():
    """_demo_ejecutar_herramienta debe setear cerebro_nivel y IndicadorHerramienta."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    bloque = src[src.index("def _demo_ejecutar_herramienta"):]
    bloque = bloque[:bloque.index("\n    def ")]
    assert "cerebro_nivel" in bloque
    assert "IndicadorHerramienta" in bloque
    assert "procesando" in bloque


def test_rf288_demo_narrar_memoria_visual():
    """_demo_narrar_memoria debe setear cerebro_nivel=nivel2."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    bloque = src[src.index("def _demo_narrar_memoria"):]
    bloque = bloque[:bloque.index("\n    def ")]
    assert '"nivel2"' in bloque
    assert "procesando" in bloque


def test_rf287_contexto_pantalla_visual():
    """Paso de contexto_pantalla en demo debe tener procesando+nivel1."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    # Buscar el paso de contexto_pantalla
    idx = src.index("descripcion_contexto()")
    bloque = src[max(0, idx-300):idx]
    assert "nivel1" in bloque
    assert "procesando" in bloque

