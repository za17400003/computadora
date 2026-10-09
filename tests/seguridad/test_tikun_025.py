"""FP-062/063/064 test_tikun_025.py — Devré HaComputadora + Shomer Emet + Sha'ar HaMaljut.

RF-169: Automejoración por workflow (Copilot → recitar → aprobar)
RF-170: Watchdog grace period (falsos positivos al arranque)
RF-171: Demo en menú contextual (clic derecho)
"""
import re
import time
import types
from unittest.mock import MagicMock, patch

import pytest


# ── RF-170: Watchdog Grace Period ──


def test_watchdog_grace_period_init():
    """ServicioMonitoreado inicializa _gracia_hasta 30s en el futuro."""
    from computadora.interfaz.watchdog import ServicioMonitoreado
    ahora = time.monotonic()
    svc = ServicioMonitoreado("test", lambda: True)
    assert svc._gracia_hasta > ahora
    assert svc._gracia_hasta - ahora == pytest.approx(30, abs=2)


def test_watchdog_grace_period_ultimo_ok_futuro():
    """_ultimo_ok está en el futuro durante la gracia para evitar RETRY."""
    from computadora.interfaz.watchdog import ServicioMonitoreado
    ahora = time.monotonic()
    svc = ServicioMonitoreado("test", lambda: True)
    assert svc._ultimo_ok > ahora


def test_watchdog_check_durante_gracia_retorna_ok():
    """Durante el grace period, check() retorna True sin ejecutar el check real."""
    from computadora.interfaz.watchdog import ServicioMonitoreado, EtapaWatchdog
    check_llamado = {"count": 0}
    def fake_check():
        check_llamado["count"] += 1
        return False  # Siempre falla
    svc = ServicioMonitoreado("test", fake_check)
    # Check durante gracia
    resultado = svc.check()
    assert resultado is True
    assert check_llamado["count"] == 0  # No se llamó al check real
    assert svc.etapa == EtapaWatchdog.OK


def test_watchdog_check_post_gracia_ejecuta_real():
    """Después del grace period, check() ejecuta el check real."""
    from computadora.interfaz.watchdog import ServicioMonitoreado
    svc = ServicioMonitoreado("test", lambda: True)
    svc._gracia_hasta = time.monotonic() - 1  # Gracia ya pasó
    svc._ultimo_ok = time.monotonic() - 1
    resultado = svc.check()
    assert resultado is True


def test_watchdog_no_retry_en_primer_heartbeat():
    """Simular primer heartbeat: no debe haber RETRY si grace period activo."""
    from computadora.interfaz.watchdog import ServicioMonitoreado, EtapaWatchdog
    svc = ServicioMonitoreado("test", lambda: True)
    # Simular 10s de delay (como si fuera el primer heartbeat)
    svc.check()
    assert svc.etapa == EtapaWatchdog.OK  # No RETRY


# ── RF-171: Demo en Menú Contextual ──


def test_menu_contextual_tiene_demo_animaciones():
    """El menú contextual (clic derecho) incluye la opción de demo."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    src = inspect.getsource(OrbeComputadora._mostrar_menu)
    assert "Mar'é HaMaljut" in src or "מראה המלכות" in src


def test_menu_contextual_tiene_separador():
    """El menú tiene un separador antes de las acciones destructivas."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    src = inspect.getsource(OrbeComputadora._mostrar_menu)
    assert "addSeparator" in src


def test_menu_contextual_orden_items():
    """El orden es: Kabbalah → Demo → Gilgul → [sep] → Borrar."""
    import inspect
    from computadora.interfaz.ventana_principal import OrbeComputadora
    src = inspect.getsource(OrbeComputadora._mostrar_menu)
    idx_kabbalah = src.find("Kabbalah")
    idx_demo = src.find("Mar'é HaMaljut") if "Mar'é HaMaljut" in src else src.find("מראה המלכות")
    idx_gilgul = src.find("Gilgul")
    idx_borrar = src.find("Borrar la Palabra")
    assert idx_kabbalah < idx_demo < idx_gilgul < idx_borrar


# ── RF-169: Automejoración — Regex ──


def test_regex_automejora_basico():
    """_RE_AUTOMEJORA captura variantes básicas."""
    from computadora.cerebro.nlu import _RE_AUTOMEJORA
    casos = [
        ("mejórate", True),
        ("mejorate", True),
        ("automejorar", True),
        ("automejora", True),
        ("mejora tu código", True),
        ("modifica tu cerebro", True),
        ("cambia tu código", True),
        ("hazte mejor", True),
        ("hazte más inteligente", True),
        ("evoluciona", True),
        ("optimízate", True),
        ("arrégla te", True),  # Match: arrégla te
        ("hola mundo", False),
    ]
    for texto, esperado in casos:
        m = _RE_AUTOMEJORA.match(texto.strip())
        assert bool(m) == esperado, f"'{texto}' debió ser match={esperado}"


def test_regex_automejora_captura_detalle():
    """_RE_AUTOMEJORA captura el detalle después del verbo."""
    from computadora.cerebro.nlu import _RE_AUTOMEJORA
    m = _RE_AUTOMEJORA.match("mejora tu código para que hables más rápido")
    assert m
    assert "más rápido" in (m.group(1) or "")


# ── RF-169: Automejoración — Detección de Proposals ──


def test_detectar_gate_proposal_valida():
    """_detectar_gate_proposal identifica una proposal con formato correcto."""
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    respuesta = (
        "PROPUESTA: Mejorar velocidad TTS\n"
        "DESCRIPCION: Optimizar el pipeline de habla para reducir latencia.\n"
        "ARCHIVOS: computadora/voz/habla.py\n"
        "RIESGO: bajo\n"
        "VEREDICTO: GO"
    )
    es_proposal, datos = cerebro._detectar_gate_proposal(respuesta)
    assert es_proposal is True
    assert datos["nombre"] == "Mejorar velocidad TTS"
    assert "GO" in datos["veredicto"]


def test_detectar_gate_proposal_no_go():
    """_detectar_gate_proposal reconoce NO-GO."""
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    respuesta = "PROPUESTA: Borrar todo\nVEREDICTO: NO-GO"
    es_proposal, datos = cerebro._detectar_gate_proposal(respuesta)
    assert es_proposal is True
    assert "NO" in datos["veredicto"]


def test_detectar_gate_proposal_texto_libre():
    """_detectar_gate_proposal rechaza texto sin formato de proposal."""
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    respuesta = "No entendí bien tu solicitud. ¿Puedes ser más específico?"
    es_proposal, datos = cerebro._detectar_gate_proposal(respuesta)
    assert es_proposal is False


# ── RF-169: Automejoración — Recitación en Voz ──


def test_recitar_proposal_voz_genera_prosa():
    """_recitar_proposal_voz genera texto legible sin markdown."""
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    datos = {
        "nombre": "Optimizar respuestas",
        "descripcion": "Reducir latencia en **respuestas** de nivel 2.",
        "archivos": "`nlu.py`, `habla.py`",
        "riesgo": "bajo",
        "veredicto": "GO",
    }
    texto = cerebro._recitar_proposal_voz(datos)
    assert "Optimizar respuestas" in texto
    assert "**" not in texto  # Sin markdown
    assert "`" not in texto  # Sin backticks
    assert "proceder" in texto


# ── RF-169: Automejoración — Aprobación ──


def test_procesar_aprobacion_sin_pendiente():
    """Sin automejoración pendiente retorna None."""
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    cerebro._automejora_pendiente = None
    assert cerebro._procesar_aprobacion_automejora("sí") is None


def test_procesar_aprobacion_rechazo():
    """Rechazar limpia el pendiente y devuelve mensaje."""
    import threading
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    cerebro._automejora_pendiente = {"nombre": "test", "veredicto": "GO"}
    cerebro._automejora_respuesta_copilot = "..."
    cerebro.historial = []
    cerebro._msg_timestamps = []
    cerebro._max_hist = 50
    cerebro._historial_lock = threading.Lock()
    resp = cerebro._procesar_aprobacion_automejora("no quiero")
    assert resp is not None
    assert "no se aplicará" in resp.lower() or "entendido" in resp.lower()
    assert cerebro._automejora_pendiente is None


def test_procesar_aprobacion_acepta():
    """Aceptar crea solicitud a Copilot."""
    import threading
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro = CerebroComputadora.__new__(CerebroComputadora)
    cerebro._automejora_pendiente = {
        "nombre": "Mejora Test",
        "descripcion": "Una mejora de prueba",
        "archivos": "test.py",
        "veredicto": "GO",
    }
    cerebro._automejora_respuesta_copilot = "PROPUESTA: test\nVEREDICTO: GO"
    cerebro.historial = []
    cerebro._msg_timestamps = []
    cerebro._max_hist = 50
    cerebro._historial_lock = threading.Lock()

    with patch("computadora.habilidades.copilot_bridge.solicitar_a_copilot") as mock_sol:
        mock_sol.return_value = "Solicitud sol_test creada."
        resp = cerebro._procesar_aprobacion_automejora("dale")

    assert resp is not None
    assert "aprobado" in resp.lower() or "solicitud" in resp.lower()
    mock_sol.assert_called_once()
    assert cerebro._automejora_pendiente is None


# ── RF-170: _check_whisper docstring ──


def test_check_whisper_docstring_actualizada():
    """_check_whisper tiene la docstring mejorada."""
    from computadora.interfaz.watchdog import _check_whisper
    assert "import" in (_check_whisper.__doc__ or "").lower() or "instanciación" in (_check_whisper.__doc__ or "").lower()

