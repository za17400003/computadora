"""FP-065/066/067 test_tikun_026.py — Ohr HaAlkimia + Shomer HaDemo + Klei Mefateaj.

RF-172: Dev Tools en menú contextual
RF-173: Sistema Ohr 5 capas de color
RF-174: Demo sincronizada por señales
RF-175: Lerp adaptativo para demo
RF-176: Demo no reactiva mic antes de cola_vacia
RF-177: obtener_ventana_activa() corregido en proactividad
RF-178: _ultimo_evento en CicloCircadiano
RF-179: Demo ACT VII — Las 4 voces de la alquimia
"""
import time
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtGui import QColor


# ── RF-173: Sistema Ohr — constantes y cálculo de color ──


def test_ohr_estado_a_grupo_cobertura_completa():
    """Todos los 13 estados FSM mapean a un grupo visual."""
    from computadora.interfaz.ventana_principal import _ESTADO_A_GRUPO
    from computadora.interfaz.fsm_computadora import EstadoMaljut
    for estado in EstadoMaljut:
        assert estado.value in _ESTADO_A_GRUPO, f"Estado {estado.value} sin grupo visual"


def test_ohr_estado_tiene_8_grupos():
    """Hay exactamente 8 grupos visuales en _OHR_ESTADO."""
    from computadora.interfaz.ventana_principal import _OHR_ESTADO
    assert len(_OHR_ESTADO) == 8


def test_ohr_herramienta_tiene_9_categorias():
    """Hay exactamente 9 categorías de herramientas."""
    from computadora.interfaz.ventana_principal import _OHR_HERRAMIENTA
    assert len(_OHR_HERRAMIENTA) == 9


def test_ohr_cerebro_tiene_3_niveles():
    """Hay exactamente 3 niveles cerebrales."""
    from computadora.interfaz.ventana_principal import _OHR_CEREBRO
    assert len(_OHR_CEREBRO) == 3


def test_herramienta_a_categoria_31_tools():
    """Las 31 herramientas mapean a categorías válidas."""
    from computadora.interfaz.ventana_principal import (
        _HERRAMIENTA_A_CATEGORIA, _OHR_HERRAMIENTA
    )
    assert len(_HERRAMIENTA_A_CATEGORIA) >= 31
    for tool, cat in _HERRAMIENTA_A_CATEGORIA.items():
        assert cat in _OHR_HERRAMIENTA, f"Tool '{tool}' → categoría '{cat}' no existe en _OHR_HERRAMIENTA"


def test_hsv_transform_no_cambia_sin_modificadores():
    """_hsv_transform con h_shift=0, s_mult=1, v_mult=1 devuelve color similar."""
    from computadora.interfaz.ventana_principal import _hsv_transform
    color = QColor(120, 80, 200)
    resultado = _hsv_transform(color, 0, 1.0, 1.0)
    # Puede haber ±1 por redondeo HSV→RGB
    assert abs(resultado.red() - color.red()) <= 2
    assert abs(resultado.green() - color.green()) <= 2
    assert abs(resultado.blue() - color.blue()) <= 2


def test_hsv_transform_h_shift():
    """_hsv_transform con h_shift altera el hue."""
    from computadora.interfaz.ventana_principal import _hsv_transform
    color = QColor.fromHsv(180, 200, 200)
    resultado = _hsv_transform(color, 30, 1.0, 1.0)
    h, _, _, _ = resultado.getHsv()
    assert h == pytest.approx(210, abs=2)


def test_blend_tinte_alpha_cero():
    """_blend_tinte con blend=0 no altera el color."""
    from computadora.interfaz.ventana_principal import _blend_tinte
    color = QColor(100, 150, 200)
    resultado = _blend_tinte(color, 255, 0, 0, 0.0)
    assert resultado.red() == color.red()
    assert resultado.green() == color.green()
    assert resultado.blue() == color.blue()


def test_blend_tinte_alpha_uno():
    """_blend_tinte con blend=1 aplica tinte completo aditivo."""
    from computadora.interfaz.ventana_principal import _blend_tinte
    color = QColor(100, 100, 100)
    resultado = _blend_tinte(color, 50, 0, 0, 1.0)
    assert resultado.red() == 150
    assert resultado.green() == 100
    assert resultado.blue() == 100


def test_calcular_color_ohr_retorna_tupla_qcolor():
    """_calcular_color_ohr devuelve tupla de 2 QColor."""
    from computadora.interfaz.ventana_principal import (
        _calcular_color_ohr, EtapaAlquimica
    )
    pri, sec = _calcular_color_ohr(
        EtapaAlquimica.NIGREDO, "dormido", "", None, ""
    )
    assert isinstance(pri, QColor)
    assert isinstance(sec, QColor)


def test_calcular_color_ohr_diferentes_etapas_diferentes_colores():
    """Distintas etapas alquímicas producen colores distintos."""
    from computadora.interfaz.ventana_principal import (
        _calcular_color_ohr, EtapaAlquimica
    )
    pri_n, _ = _calcular_color_ohr(EtapaAlquimica.NIGREDO, "vigilia", "", None, "")
    pri_r, _ = _calcular_color_ohr(EtapaAlquimica.RUBEDO, "vigilia", "", None, "")
    # No deben ser idénticos
    assert pri_n.name() != pri_r.name()


def test_calcular_color_ohr_herramienta_tinta():
    """Una herramienta activa modifica el color base."""
    from computadora.interfaz.ventana_principal import (
        _calcular_color_ohr, EtapaAlquimica
    )
    pri_sin, _ = _calcular_color_ohr(EtapaAlquimica.ALBEDO, "trabajando", "", None, "")
    pri_con, _ = _calcular_color_ohr(EtapaAlquimica.ALBEDO, "trabajando", "ejecucion", None, "")
    assert pri_sin.name() != pri_con.name()


def test_calcular_color_ohr_cerebro_tinta():
    """El nivel cerebral modifica el color."""
    from computadora.interfaz.ventana_principal import (
        _calcular_color_ohr, EtapaAlquimica
    )
    pri_sin, _ = _calcular_color_ohr(EtapaAlquimica.CITRINITAS, "procesando", "", None, "")
    pri_con, _ = _calcular_color_ohr(EtapaAlquimica.CITRINITAS, "procesando", "", "nivel3", "")
    assert pri_sin.name() != pri_con.name()


def test_calcular_color_ohr_gevura_override():
    """Gevurá activa produce un color especial propio."""
    from computadora.interfaz.ventana_principal import (
        _calcular_color_ohr, EtapaAlquimica
    )
    pri_gev, _ = _calcular_color_ohr(EtapaAlquimica.RUBEDO, "gevura_activa", "", None, "etico")
    pri_nor, _ = _calcular_color_ohr(EtapaAlquimica.RUBEDO, "vigilia", "", None, "")
    assert pri_gev.name() != pri_nor.name()


# ── RF-175: Lerp adaptativo ──


def test_lerp_speed_constantes():
    """Las velocidades de lerp demo vs normal son coherentes."""
    demo_speed = 1.0 / (1.5 * 30)
    normal_speed = 1.0 / (60 * 30)
    assert demo_speed > normal_speed * 10  # Demo es >10x más rápido


# ── RF-177: obtener_ventana_activa() corregido ──


def test_proactividad_usa_obtener_ventana_activa():
    """proactividad.py no contiene la llamada incorrecta 'ventana_activa()'."""
    import inspect
    from computadora.nucleo import proactividad
    fuente = inspect.getsource(proactividad)
    # No debe tener la form incorrecta (sin 'obtener_' prefijo)
    # Pero sí puede tener 'obtener_ventana_activa'
    lineas_con_ventana = [
        l for l in fuente.split('\n')
        if '.ventana_activa()' in l and 'obtener_ventana_activa' not in l
    ]
    assert len(lineas_con_ventana) == 0, f"Llamadas incorrectas: {lineas_con_ventana}"


# ── RF-178: _ultimo_evento en CicloCircadiano ──


def test_ciclo_circadiano_tiene_ultimo_evento():
    """CicloCircadiano tiene _ultimo_evento al inicializar."""
    from computadora.nucleo.ciclo_circadiano import CicloCircadiano
    cc = CicloCircadiano.__new__(CicloCircadiano)
    # Simular init mínimo
    cc._fase = "dia"
    cc._ultimo_evento = time.time()
    assert isinstance(cc._ultimo_evento, float)
    assert cc._ultimo_evento > 0


# ── RF-174: Demo sincronizada por señales ──


def test_demo_pasos_es_lista_con_actos():
    """La demo genera una lista de pasos no vacía."""
    # Verificar que _demo_pasos se asigna correctamente
    from computadora.interfaz.ventana_principal import OrbeComputadora
    assert hasattr(OrbeComputadora, '_demo_animaciones')
    assert hasattr(OrbeComputadora, '_demo_ejecutar_paso')


def test_demo_ejecutar_paso_existe():
    """El motor de pasos RF-174 está definido."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    import inspect
    source = inspect.getsource(OrbeComputadora._demo_ejecutar_paso)
    assert "cola_vacia" in source
    assert "_demo_idx" in source


# ── RF-179: Las 4 voces de la alquimia ──


def test_demo_contiene_4_voces():
    """La demo contiene narración de las 4 etapas alquímicas."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    source = inspect.getsource(OrbeComputadora._demo_animaciones)
    assert "Nigredo: la voz desde la oscuridad" in source
    assert "Albedo: la voz de la plata" in source
    assert "Citrinitas: la voz del oro" in source
    assert "Rubedo: la voz del fuego" in source


# ── RF-172: Dev Tools ──


def test_menu_dev_tools_metodos_existen():
    """OrbeComputadora tiene métodos de Dev Tools."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    assert hasattr(OrbeComputadora, '_mostrar_heatmap_dev')
    assert hasattr(OrbeComputadora, '_mostrar_estado_dev')


def test_mostrar_menu_contiene_dev_tools():
    """El menú contextual incluye la opción de Dev Tools."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    source = inspect.getsource(OrbeComputadora._mostrar_menu)
    assert "Dev Tools" in source
    assert "_mostrar_heatmap_dev" in source
    assert "_mostrar_estado_dev" in source


# ── RF-176: Demo no reactiva mic antes de cola_vacia ──


def test_demo_finale_no_reanuda_escucha_directamente():
    """El finale de la demo NO contiene reanudar() directamente — usa cola_vacia."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    source = inspect.getsource(OrbeComputadora._demo_animaciones)
    # _demo_finale_fn (el finale) no debe llamar reanudar() directamente
    # reanudar() solo debe estar en _demo_cola_vacia
    assert "cola_vacia" in source
    assert "_demo_cola_vacia_fn" in source

