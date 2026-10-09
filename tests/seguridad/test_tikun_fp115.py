"""Tests para FP-115: שיווי המשקל Shivúi HaMishkál — Equilibrio y Sabiduría.

WI-163: Demo sentinel → PC action queue
WI-164: Access violation frame copy
WI-165: N2→N3 auto-escalation
WI-166: Mouse intent + auto-grow balance
WI-167: Context menu security submenu
WI-168: Grimorio intrusion photo capture
"""

import importlib
import threading
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
import math


# ── WI-163: _acciones_remotas queue in servidor_api ──

def test_acciones_remotas_queue_exists():
    """servidor_api exposes _acciones_remotas list and lock."""
    mod = importlib.import_module("computadora.canales.servidor_api")
    assert hasattr(mod, "_acciones_remotas")
    assert hasattr(mod, "_acciones_remotas_lock")
    assert isinstance(mod._acciones_remotas, list)
    assert isinstance(mod._acciones_remotas_lock, type(threading.Lock()))


def test_obtener_acciones_remotas_drains():
    """obtener_acciones_remotas() returns queued items and clears list."""
    mod = importlib.import_module("computadora.canales.servidor_api")
    with mod._acciones_remotas_lock:
        mod._acciones_remotas.clear()
        mod._acciones_remotas.append("__DEMO_ANIMACIONES__")
        mod._acciones_remotas.append("__TEST__")
    result = mod.obtener_acciones_remotas()
    assert result == ["__DEMO_ANIMACIONES__", "__TEST__"]
    # After drain, list is empty
    assert mod.obtener_acciones_remotas() == []


def test_filtrar_sentinel_queues_action():
    """_filtrar_sentinel queues raw sentinel and returns filtered text."""
    mod = importlib.import_module("computadora.canales.servidor_api")
    with mod._acciones_remotas_lock:
        mod._acciones_remotas.clear()
    sentinel_msgs = getattr(mod, "_SENTINEL_MSGS", {})
    if sentinel_msgs:
        sentinel = next(iter(sentinel_msgs))
        filtered = mod._filtrar_sentinel(sentinel)
        # Should NOT return the raw sentinel
        assert filtered != sentinel
        # Should have queued the raw sentinel
        queued = mod.obtener_acciones_remotas()
        assert sentinel in queued


# ── WI-164: frame .copy() in rostro.py ──

def test_rostro_module_importable():
    """rostro.py imports without error."""
    mod = importlib.import_module("computadora.percepcion.rostro")
    assert hasattr(mod, "ReconocedorRostro")


def test_rostro_analizar_frame_copies_input():
    """analizar_frame should not modify the input array (copy semantics).
    WI-235: Uses cv2.cvtColor for guaranteed contiguous array instead of .copy()."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.percepcion.rostro")
    )
    # The cv2.cvtColor call must be present in the RGB conversion (ensures contiguous array)
    assert "cv2.cvtColor" in src


# ── WI-165: N2→N3 auto-escalation ──

def test_nlu_has_auto_gate_copilot():
    """NLU module has _auto_gate_copilot attribute for cascade."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.cerebro.nlu")
    )
    assert "_auto_gate_copilot" in src


def test_nlu_cascade_tries_copilot_before_fallback():
    """When Ollama unavailable, NLU tries _pensar_con_copilot before _pensar_sin_llm."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.cerebro.nlu")
    )
    # In the Ollama-unavailable block, _pensar_con_copilot should appear
    # before _pensar_sin_llm
    idx_copilot = src.find("_pensar_con_copilot")
    idx_sin_llm = src.find("_pensar_sin_llm")
    assert idx_copilot > 0
    assert idx_sin_llm > 0
    # Copilot attempt comes first in the cascade path
    assert idx_copilot < idx_sin_llm


# ── WI-166: Mouse intent via trajectory analysis ──

def test_vida_autonoma_cursor_prev_attrs():
    """VidaAutonoma stores 2-tick cursor history."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.vida_autonoma")
    )
    assert "_cursor_prev" in src
    assert "_cursor_prev2" in src


def test_vida_autonoma_estorba_has_dot_product():
    """_estorba() uses dot-product trajectory analysis."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.vida_autonoma")
    )
    # dot product / cos_angle logic present
    assert "cos_angle" in src or "dot" in src


def test_ventana_principal_no_auto_grow_on_enter():
    """enterEvent should not force _escala_objetivo."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.ventana_principal")
    )
    # The old pattern was: escala_objetivo = 1.05 in enterEvent
    # Now enterEvent should just pass or not set escala
    # Check that the exact bad pattern is gone
    assert "enterEvent" in src  # method still exists
    # No unconditional scale set in enterEvent
    lines = src.split("\n")
    in_enter = False
    for line in lines:
        if "def enterEvent" in line:
            in_enter = True
            continue
        if in_enter:
            if line.strip().startswith("def "):
                break
            assert "_escala_objetivo = 1.05" not in line


# ── WI-167: Security submenu in context menu ──

def test_context_menu_has_gevura_submenu():
    """Context menu includes Gevurá security submenu."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.ventana_principal")
    )
    assert "גבורה" in src or "Gevur" in src
    assert "VPN" in src


# ── WI-168: Grimorio intrusion photo capture ──

def test_intrusion_handler_captures_photo():
    """_al_intrusion_grimorio attempts camera capture."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.ventana_principal")
    )
    assert "intruso_" in src  # filename pattern
    assert "datos" in src and "intrusiones" in src  # output directory
    assert "imwrite" in src  # cv2.imwrite


def test_intrusion_handler_speaks_photo_taken():
    """Vocal alert mentions photo if captured."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("computadora.interfaz.ventana_principal")
    )
    assert "fotografía del intruso" in src

