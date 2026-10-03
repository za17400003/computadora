"""
Test para verificar que Gilgul utiliza la contraseña maestra correcta.
Valida que la contraseña haya sido actualizada de "met" a "emet".
"""

import json
from pathlib import Path


def test_gilgul_credentials_exist():
    """Verificar que el archivo de credenciales de Gilgul existe."""
    creds_path = Path(__file__).resolve().parent.parent / "datos" / "gilgul_credentials.json"
    assert creds_path.exists(), f"gilgul_credentials.json no existe en {creds_path}"


def test_gilgul_master_password_is_emet():
    """Verificar que la contraseña maestra es 'emet' (verdad)."""
    creds_path = Path(__file__).resolve().parent.parent / "datos" / "gilgul_credentials.json"
    
    with open(creds_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    
    master_password = creds.get("gilgul_access", {}).get("master_password")
    assert master_password == "emet", f"master_password debe ser 'emet', pero es '{master_password}'"


def test_gilgul_password_history_contains_legacy_met():
    """Verificar que el historial de contraseñas documenta la transición met -> emet."""
    creds_path = Path(__file__).resolve().parent.parent / "datos" / "gilgul_credentials.json"
    
    with open(creds_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    
    history = creds.get("password_history", [])
    
    # Buscar entrada de "met" (contraseña anterior)
    met_entry = None
    emet_entry = None
    
    for entry in history:
        if entry.get("password") == "met":
            met_entry = entry
        elif entry.get("password") == "emet":
            emet_entry = entry
    
    assert met_entry is not None, "Historial debe documentar la contraseña anterior 'met'"
    assert emet_entry is not None, "Historial debe documentar la nueva contraseña 'emet'"
    assert met_entry.get("reason") and "death" in met_entry["reason"].lower(), \
        "Entrada 'met' debe explicar la semántica (met = muerte)"
    assert emet_entry.get("reason") and "truth" in emet_entry["reason"].lower(), \
        "Entrada 'emet' debe explicar la semántica (emet = verdad)"


def test_gilgul_access_control_enabled():
    """Verificar que los controles de acceso están activados."""
    creds_path = Path(__file__).resolve().parent.parent / "datos" / "gilgul_credentials.json"
    
    with open(creds_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    
    access_control = creds.get("access_control", {})
    
    assert access_control.get("gilgul_requires_master") is True, \
        "gilgul_requires_master debe estar habilitado"
    assert access_control.get("double_confirmation") is True, \
        "double_confirmation debe estar habilitado"


def test_gilgul_semantic_transition_documented():
    """Verificar que la transición semántica de met -> emet está documentada."""
    creds_path = Path(__file__).resolve().parent.parent / "datos" / "gilgul_credentials.json"
    
    with open(creds_path, 'r', encoding='utf-8') as f:
        creds = json.load(f)
    
    gilgul_access = creds.get("gilgul_access", {})
    transition = gilgul_access.get("semantic_transition", "")
    
    assert "met" in transition and "emet" in transition, \
        "Debe documentar la transición de 'met' a 'emet'"
    assert "mת" in transition or "מת" in transition or "Death" in transition, \
        "Debe mencionar el significado hebreo de 'met' (muerte)"
    assert ("אמת" in transition or "truth" in transition), \
        "Debe mencionar el significado hebreo de 'emet' (verdad)"


if __name__ == "__main__":
    test_gilgul_credentials_exist()
    test_gilgul_master_password_is_emet()
    test_gilgul_password_history_contains_legacy_met()
    test_gilgul_access_control_enabled()
    test_gilgul_semantic_transition_documented()
    print("✅ Todos los tests de Gilgul pasaron.")

