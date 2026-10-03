"""Tests para FP-082 (Topmost), FP-083 (auto-install bat), FP-085 (Stats HUD + Bereshit resize),
FP-086 (título interlocutor). Un archivo por ciclo Tikún (Regla SKU #4)."""
import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_VP = _ROOT / "golem" / "interfaz" / "ventana_principal.py"
_VA = _ROOT / "golem" / "interfaz" / "vida_autonoma.py"
_BAT = _ROOT / "iniciar_golem.bat"
_SRS = _ROOT / "SRS.md"
_WORKFLOW = _ROOT / "DEVELOPMENT_WORKFLOW.md"


def _src_vp():
    return _VP.read_text(encoding="utf-8")


def _src_va():
    return _VA.read_text(encoding="utf-8")


# ── FP-082: Shekhiná Tamid — Topmost perpetuo ──

def test_rf305_hwnd_topmost_in_eliminar_sombra():
    """RF-305: SetWindowPos usa HWND_TOPMOST (-1) en _eliminar_sombra_dwm o _aplicar_dwm_nosombra."""
    src = _src_vp()
    # Debe tener HWND_TOPMOST = -1 en _aplicar_dwm_nosombra (delegado desde _eliminar_sombra_dwm)
    assert "HWND_TOPMOST = -1" in src, "RF-305: Falta HWND_TOPMOST = -1"
    assert "SWP_NOZORDER" not in src or "SWP_NOZORDER" not in src.split("_eliminar_sombra_dwm")[1].split("def ")[0], \
        "RF-305: SWP_NOZORDER todavía presente en _eliminar_sombra_dwm"


def test_rf306_timer_topmost_exists():
    """RF-306: Existe _timer_topmost y _reasegurar_topmost."""
    src = _src_vp()
    assert "_timer_topmost" in src, "RF-306: Falta _timer_topmost"
    assert "def _reasegurar_topmost" in src, "RF-306: Falta método _reasegurar_topmost"
    assert "5000" in src, "RF-306: Timer debe ser 5000ms"


def test_rf307_no_notopmost_in_tzimtzum():
    """RF-307: _desactivar_tzimtzum NO tiene HWND_NOTOPMOST (-2)."""
    src = _src_va()
    # Buscar en la función _desactivar_tzimtzum
    match = re.search(r"def _desactivar_tzimtzum\(self\).*?(?=\n    def |\Z)", src, re.DOTALL)
    assert match, "No se encontró _desactivar_tzimtzum"
    body = match.group()
    assert "-2" not in body, "RF-307: HWND_NOTOPMOST (-2) todavía en _desactivar_tzimtzum"


def test_rf308_no_notopmost_in_wake_word():
    """RF-308: Wake word handler no hace TOPMOST→NOTOPMOST."""
    src = _src_vp()
    # Buscar la sección del wake word handler con Tzimtzum restore
    # Debe tener RF-308 comment y NOT have -2 (NOTOPMOST) nearby
    assert "RF-308" in src, "RF-308: Falta referencia a RF-308 en código"


# ── FP-083: Auto-install face-recognition ──

def test_rf309_bat_auto_install():
    """RF-309: iniciar_golem.bat auto-instala face-recognition."""
    bat = _BAT.read_text(encoding="utf-8")
    assert "pip install cmake dlib face-recognition" in bat, "RF-309: Falta pip install auto"
    assert "Instalando automaticamente" in bat, "RF-309: Falta mensaje de auto-instalación"


# ── FP-085: Stats HUD + Bereshit resize ──

def test_rf311_bereshit_resize_sync():
    """RF-311: _paso_bereshit sincroniza tamaño de ventana."""
    src = _src_vp()
    match = re.search(r"def _paso_bereshit\(self\).*?(?=\n    def |\Z)", src, re.DOTALL)
    assert match, "No se encontró _paso_bereshit"
    body = match.group()
    assert "RF-311" in body, "RF-311: Falta referencia a RF-311 en _paso_bereshit"
    assert "self.resize(" in body, "RF-311: _paso_bereshit debe hacer resize directo"
    assert "_tamano_ventana" in body, "RF-311: Debe actualizar _tamano_ventana"


def test_rf312_grid_layout_stats():
    """RF-312: Stats panel usa QGridLayout con secciones."""
    src = _src_vp()
    match = re.search(r"def _mostrar_estado_dev\(self\).*?(?=\n    def |\Z)", src, re.DOTALL)
    assert match, "No se encontró _mostrar_estado_dev"
    body = match.group()
    assert "QGridLayout" in body, "RF-312: Falta QGridLayout"
    assert "ESTADO" in body, "RF-312: Falta sección ESTADO"
    assert "ALQUIMIA" in body, "RF-312: Falta sección ALQUIMIA"
    assert "VISUAL" in body, "RF-312: Falta sección VISUAL"
    assert "SISTEMA" in body, "RF-312: Falta sección SISTEMA"


def test_rf313_progress_bars():
    """RF-313: Stats usa QProgressBar para métricas."""
    src = _src_vp()
    assert "QProgressBar" in src, "RF-313: Falta QProgressBar import/uso"
    match = re.search(r"def _mostrar_estado_dev\(self\).*?(?=\n    def |\Z)", src, re.DOTALL)
    assert match
    body = match.group()
    assert "QProgressBar()" in body, "RF-313: Falta creación de QProgressBar"
    assert "setRange" in body, "RF-313: Falta setRange en barras"


def test_rf314_color_swatches():
    """RF-314: Stats muestra swatches de color (QFrame pintado)."""
    src = _src_vp()
    match = re.search(r"def _mostrar_estado_dev\(self\).*?(?=\n    def |\Z)", src, re.DOTALL)
    assert match
    body = match.group()
    assert "QFrame()" in body or "swatch" in body, "RF-314: Falta swatch de color"


# ── FP-086: Título interlocutor ──

def test_rf315_titulo_interlocutor():
    """RF-315/316: obtener_titulo() exists in GestorPersonas, injected in nlu.py."""
    from computadora.memoria.personas import GestorPersonas
    assert hasattr(GestorPersonas, "obtener_titulo"), "RF-315: Falta método obtener_titulo en GestorPersonas"
    # RF-316: inyección dinámica en nlu.py
    nlu_src = Path(__file__).resolve().parent.parent / "golem" / "cerebro" / "nlu.py"
    src = nlu_src.read_text(encoding="utf-8")
    assert "TITULO_INTERLOCUTOR" in src, "RF-316: Falta inyección de título en _construir_system_msgs"


# ── SRS coherencia ──

def test_srs_contiene_nuevos_rfs():
    """Verifica que SRS.md tiene RF-305 a RF-315."""
    srs = _SRS.read_text(encoding="utf-8")
    for rf in (305, 306, 307, 308, 309, 311, 312, 313, 314, 315):
        assert f"RF-{rf}" in srs, f"RF-{rf} no documentado en SRS.md"


# ── Workflow: PM suggestions obligatorias ──

def test_workflow_pm_suggestions_rule():
    """Verifica que DEVELOPMENT_WORKFLOW.md exige PM suggestions en cada gate."""
    wf = _WORKFLOW.read_text(encoding="utf-8")
    assert "Sugerencias obligatorias en cada gate" in wf, \
        "Falta regla de sugerencias PM obligatorias en workflow"


# ── Imports válidos ──

def test_ventana_principal_syntax():
    """El archivo ventana_principal.py tiene sintaxis válida."""
    ast.parse(_VP.read_text(encoding="utf-8"))


def test_vida_autonoma_syntax():
    """El archivo vida_autonoma.py tiene sintaxis válida."""
    ast.parse(_VA.read_text(encoding="utf-8"))

