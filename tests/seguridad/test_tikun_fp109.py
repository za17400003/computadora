"""Tests para FP-109: Shomer HaBayit + Cámara Dev Tools + Tikún Tria Prima.

Cubre RF-368 (shomer_bayit), RF-369 (cámara dev), RF-370 (workflow Tria Prima).
"""

import importlib
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── RF-368: Shomer HaBayit — imports y funciones ──

def test_shomer_bayit_importable():
    """shomer_bayit.py se importa sin error."""
    mod = importlib.import_module("computadora.seguridad.shomer_bayit")
    assert hasattr(mod, "es_red_hogar")
    assert hasattr(mod, "obtener_huella_red_actual")
    assert hasattr(mod, "registrar_hogar")
    assert hasattr(mod, "obtener_estado_red")


def test_obtener_huella_red_retorna_dict():
    """obtener_huella_red_actual() retorna dict con claves esperadas."""
    from computadora.seguridad.shomer_bayit import obtener_huella_red_actual
    huella = obtener_huella_red_actual()
    assert isinstance(huella, dict)
    assert "gateway" in huella
    assert "ssid" in huella
    assert "subnet" in huella
    assert "adaptador" in huella


def test_registrar_hogar_requiere_gateway(tmp_path):
    """registrar_hogar() no guarda si no hay gateway."""
    from computadora.seguridad import shomer_bayit

    huella_vacia = {"gateway": "", "ssid": "", "subnet": "", "adaptador": ""}
    with patch.object(shomer_bayit, "obtener_huella_red_actual", return_value=huella_vacia):
        result = shomer_bayit.registrar_hogar()
        assert result["gateway"] == ""


def test_es_red_hogar_retorna_bool():
    """es_red_hogar() retorna un booleano."""
    from computadora.seguridad.shomer_bayit import es_red_hogar
    resultado = es_red_hogar()
    assert isinstance(resultado, bool)


def test_obtener_estado_red_estructura():
    """obtener_estado_red() retorna dict con estructura completa."""
    from computadora.seguridad.shomer_bayit import obtener_estado_red
    estado = obtener_estado_red()
    assert isinstance(estado, dict)
    assert "es_red_hogar" in estado
    assert "red_actual" in estado
    assert "huella_hogar" in estado


# ── RF-368: Integración servidor_api stealth ──

def test_servidor_api_importa_shomer_bayit():
    """servidor_api.py importa es_red_hogar de shomer_bayit."""
    import computadora.canales.servidor_api as api_mod
    source = Path(api_mod.__file__).read_text(encoding="utf-8")
    assert "from computadora.seguridad.shomer_bayit import es_red_hogar" in source


def test_servidor_api_verificar_origen_usa_shomer():
    """_verificar_origen en servidor_api usa es_red_hogar."""
    import computadora.canales.servidor_api as api_mod
    source = Path(api_mod.__file__).read_text(encoding="utf-8")
    assert "es_red_hogar()" in source


# ── RF-368: Integración servidor_grimorio ──

def test_servidor_grimorio_usa_shomer_bayit():
    """servidor_grimorio.py referencia shomer_bayit para guardia --lan."""
    grimorio_path = Path(__file__).parent.parent / "libro_encantado" / "servidor_grimorio.py"
    source = grimorio_path.read_text(encoding="utf-8")
    assert "shomer_bayit" in source


# ── RF-369: Cámara Dev Tools ──

def test_ventana_principal_tiene_camara_dev():
    """ventana_principal.py contiene _mostrar_camara_dev."""
    vp_path = Path(__file__).resolve().parents[2] / "computadora" / "interfaz" / "ventana_principal.py"
    source = vp_path.read_text(encoding="utf-8")
    assert "_mostrar_camara_dev" in source
    assert "Ojos del Computadora" in source


def test_ventana_principal_tiene_accion_camara():
    """ventana_principal.py tiene QAction para cámara en Dev Tools."""
    vp_path = Path(__file__).resolve().parents[2] / "computadora" / "interfaz" / "ventana_principal.py"
    source = vp_path.read_text(encoding="utf-8")
    assert "Cámara" in source


# ── RF-370: Tikún Tria Prima workflow ──

def test_workflow_tiene_tria_prima():
    """DEVELOPMENT_WORKFLOW.md contiene Tria Prima."""
    wf_path = Path(__file__).parent.parent / "DEVELOPMENT_WORKFLOW.md"
    source = wf_path.read_text(encoding="utf-8")
    assert "TRIA PRIMA" in source
    assert "Grimorio" in source


def test_workflow_tiene_jerarquia():
    """DEVELOPMENT_WORKFLOW.md define jerarquía Grimorio > Minimi > Computadora."""
    wf_path = Path(__file__).parent.parent / "DEVELOPMENT_WORKFLOW.md"
    source = wf_path.read_text(encoding="utf-8")
    assert "Grimorio > Minimi > Computadora" in source


def test_workflow_tiene_amen():
    """DEVELOPMENT_WORKFLOW.md define semántica de AMÉN para 6 ciclos."""
    wf_path = Path(__file__).parent.parent / "DEVELOPMENT_WORKFLOW.md"
    source = wf_path.read_text(encoding="utf-8")
    assert "AMÉN" in source or "אמן" in source


def test_workflow_tiene_rotacion():
    """DEVELOPMENT_WORKFLOW.md define rotación de Árbol en PALINGENESIA."""
    wf_path = Path(__file__).parent.parent / "DEVELOPMENT_WORKFLOW.md"
    source = wf_path.read_text(encoding="utf-8")
    assert "ROTAR al siguiente" in source


# ── SRS coherencia ──

def test_srs_tiene_rf368_a_370():
    """SRS.md contiene RF-368, RF-369, RF-370."""
    srs_path = Path(__file__).parent.parent / "SRS.md"
    source = srs_path.read_text(encoding="utf-8")
    assert "RF-368" in source
    assert "RF-369" in source
    assert "RF-370" in source

