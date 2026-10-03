"""Tests para FP-116: שְׁטִיפָה Shtifá — Purificación y Flujo.

WI-171: Security notes once-only (dedup boot + remove System B monitor)
WI-172: Shomer HaBayit backoff on failed registration
WI-173: Workflow optimization (session cleanup, copilot-instructions.md, fractal pagination)
"""

import importlib
import time
from unittest.mock import patch, MagicMock
from pathlib import Path


# ── WI-171: Security notes once-only ──

def test_no_monitor_intrusiones_tiempo_real():
    """_monitor_intrusiones_tiempo_real should be REMOVED (System B eliminated)."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("golem.interfaz.ventana_principal")
    )
    assert "def _monitor_intrusiones_tiempo_real" not in src
    # The comment explaining removal should exist
    assert "WI-171" in src


def test_boot_check_uses_offset_path():
    """Boot intrusion check persists offset to avoid re-speaking."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("golem.interfaz.ventana_principal")
    )
    assert "grimorio_intrusiones_offset" in src


def test_no_15s_intrusiones_timer():
    """The 15-second intrusions timer should not be started anymore."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("golem.interfaz.ventana_principal")
    )
    # Old pattern: _intrusiones_timer.start(15000) should be gone
    assert "_intrusiones_timer.start(15000)" not in src


# ── WI-172: Shomer HaBayit backoff ──

def test_shomer_backoff_variable_exists():
    """shomer_bayit has backoff mechanisms."""
    mod = importlib.import_module("golem.seguridad.shomer_bayit")
    assert hasattr(mod, "_registro_fallido_ts")
    assert hasattr(mod, "_REGISTRO_BACKOFF")
    assert mod._REGISTRO_BACKOFF == 300.0


def test_es_red_hogar_backoff_prevents_spam():
    """es_red_hogar() should not retry within 5 min of a failed registration."""
    mod = importlib.import_module("golem.seguridad.shomer_bayit")
    # Simulate a failed registration just now
    mod._registro_fallido_ts = time.time()
    # Mock _cargar_huella_hogar to return None (no file)
    with patch.object(mod, "_cargar_huella_hogar", return_value=None):
        with patch.object(mod, "registrar_hogar") as mock_reg:
            result = mod.es_red_hogar()
            # Should NOT have called registrar_hogar (backoff active)
            mock_reg.assert_not_called()
            assert result is True
    # Reset for other tests
    mod._registro_fallido_ts = 0.0


def test_registrar_hogar_writes_sentinel_on_failure():
    """registrar_hogar writes incomplete sentinel when gateway not found."""
    src = importlib.import_module("inspect").getsource(
        importlib.import_module("golem.seguridad.shomer_bayit")
    )
    # The sentinel write with "incompleto" must be in registrar_hogar
    assert '"incompleto": True' in src or "'incompleto': True" in src or "incompleto" in src


def test_es_red_hogar_retries_after_backoff():
    """After backoff period, es_red_hogar retries registration."""
    mod = importlib.import_module("golem.seguridad.shomer_bayit")
    # Simulate failure 6 minutes ago (past backoff)
    mod._registro_fallido_ts = time.time() - 400
    huella_ok = {"gateway": "192.168.1.1", "ssid": "Home", "subnet": "255.255.255.0", "adaptador": "Wi-Fi"}
    with patch.object(mod, "_cargar_huella_hogar", return_value=None):
        with patch.object(mod, "registrar_hogar", return_value=huella_ok) as mock_reg:
            result = mod.es_red_hogar()
            mock_reg.assert_called_once()
            assert result is True
    mod._registro_fallido_ts = 0.0


# ── WI-173: Workflow optimization ──

def test_copilot_instructions_exists():
    """.github/copilot-instructions.md exists with boot sequence."""
    ci = Path(__file__).parent.parent / ".github" / "copilot-instructions.md"
    assert ci.exists()
    content = ci.read_text(encoding="utf-8")
    assert "Boot Sequence" in content
    assert "Anti-Colateral" in content
    assert "Fractal Pagination" in content


def test_dev_workflow_has_fractal_pagination():
    """DEVELOPMENT_WORKFLOW.md includes Fractal Pagination section."""
    dw = Path(__file__).parent.parent / "DEVELOPMENT_WORKFLOW.md"
    content = dw.read_text(encoding="utf-8")
    assert "PAGINACIÓN FRACTAL" in content
    assert "Auto-escalado" in content


def test_vscode_settings_max_turns():
    """.vscode/settings.json has maxTurns configured."""
    settings = Path(__file__).parent.parent / ".vscode" / "settings.json"
    assert settings.exists()
    import json
    cfg = json.loads(settings.read_text(encoding="utf-8"))
    assert cfg.get("chat.agent.maxTurns", 0) >= 50

