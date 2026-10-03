"""Tikún 027 — Tests para FP-068 (RF-180/181/182) + FP-069 (Regla #21)."""
import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── RF-180: Dual heatmap ──

def test_rf180_heatmap_reciente_exists():
    """VidaAutonoma tiene _heatmap_reciente como atributo."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "_heatmap_reciente" in src
    assert "self._heatmap_reciente:" in src or "self._heatmap_reciente =" in src


def test_rf180_heatmap_reciente_init():
    """_heatmap_reciente se inicializa como lista 8x6 de ceros."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "HEATMAP_COLS for _ in range(self.HEATMAP_ROWS)" in src
    assert "_heatmap_reciente_inicio" in src


def test_rf180_dual_score():
    """_score_posicion combina histórico*0.4 + reciente*0.6."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "* 0.4" in src and "* 0.6" in src
    assert "heatmap_reciente" in src


def test_rf180_reciente_decay_30s():
    """Heatmap reciente decae cada 30s con factor 0.85."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "*= 0.85" in src or "* 0.85" in src


def test_rf180_reciente_reset_5min():
    """Heatmap reciente se resetea cada 5 min (ventana deslizante)."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "_heatmap_reciente_inicio" in src
    assert "> 300" in src  # 300 seconds = 5 min


def test_rf180_actualizar_heatmap_dual():
    """_actualizar_heatmap incrementa ambos heatmaps."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    # Debe haber dos incrementos: histórico y reciente
    idx1 = src.index("self._heatmap[row][col] += 1.0")
    idx2 = src.index("self._heatmap_reciente[row][col] += 1.0")
    assert idx1 < idx2


# ── RF-181: Memoria de esquivas + escalación ──

def test_rf181_historial_esquivas_deque():
    """_historial_esquivas es una deque(maxlen=20)."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "_historial_esquivas" in src
    assert "deque(maxlen=20)" in src


def test_rf181_esquivar_registra():
    """_esquivar() registra evento en _historial_esquivas."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    # Buscar append dentro de _esquivar
    idx_esquivar = src.index("def _esquivar(")
    idx_next_def = src.index("\n    def ", idx_esquivar + 1)
    bloque = src[idx_esquivar:idx_next_def]
    assert "_historial_esquivas.append(" in bloque


def test_rf181_evaluar_patron_exists():
    """_evaluar_patron_esquiva() está definida."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "def _evaluar_patron_esquiva(self, info" in src


def test_rf181_escalacion_3_niveles():
    """La escalación tiene 3 umbrales: ≥2, ≥5, ≥7."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _evaluar_patron_esquiva")
    bloque = src[idx:idx+1200]
    assert "n >= 7" in bloque
    assert "n >= 5" in bloque
    assert "n >= 2" in bloque


def test_rf181_escalacion_tzimtzum():
    """≥7 esquivas en 5min activa tzimtzum."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _evaluar_patron_esquiva")
    bloque = src[idx:idx+1200]
    assert "_activar_tzimtzum" in bloque
    assert "esquivas frecuentes" in bloque


def test_rf181_escalacion_doble_cooldown():
    """≥5 esquivas → cooldown 48 (~24s)."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _evaluar_patron_esquiva")
    bloque = src[idx:idx+1200]
    assert "cooldown = 48" in bloque


def test_rf181_esquiva_razon():
    """La esquiva registra razón (cursor o ventana)."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _esquivar(")
    idx_next = src.index("\n    def ", idx + 1)
    bloque = src[idx:idx_next]
    assert '"cursor"' in bloque
    assert '"ventana"' in bloque


# ── RF-182: Home reactivo post-esquiva ──

def test_rf182_recalc_home_post_esquiva():
    """≥2 esquivas en 5min → _calcular_hogar_dinamico() inmediato."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _evaluar_patron_esquiva")
    bloque = src[idx:idx+1200]
    assert "_calcular_hogar_dinamico(info)" in bloque
    # En hogar se setea a True
    assert "_en_hogar = True" in bloque


def test_rf182_zona_esquiva_frecuente():
    """_es_zona_esquiva_frecuente() está definida y verifica radio."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    assert "def _es_zona_esquiva_frecuente(self, punto" in src
    idx = src.index("def _es_zona_esquiva_frecuente")
    bloque = src[idx:idx+400]
    assert "zona_radio" in bloque
    assert "200" in bloque


def test_rf182_hogar_evita_zona_esquiva():
    """_calcular_hogar_dinamico usa 2do candidato si 1ro cae en zona esquiva."""
    src = open("golem/interfaz/vida_autonoma.py", encoding="utf-8").read()
    idx = src.index("def _calcular_hogar_dinamico")
    idx_next = src.index("\n    def ", idx + 1)
    bloque = src[idx:idx_next]
    assert "_es_zona_esquiva_frecuente" in bloque
    assert "validos_scored[1]" in bloque


# ── FP-069: Regla #21 Zikrón HaCitrinitas ──

def test_fp069_regla_21_exists():
    """Regla #21 existe en DEVELOPMENT_WORKFLOW.md."""
    wf = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    assert "| **21**" in wf
    assert "Zikrón HaCitrinitas" in wf


def test_fp069_session_memory_reference():
    """Regla #21 menciona citrinitas_proposals.md en session memory."""
    wf = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    assert "citrinitas_proposals.md" in wf


def test_fp069_re_enter_rule():
    """Regla #21 requiere leer propuestas al re-entrar a CITRINITAS."""
    wf = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    idx = wf.index("| **21**")
    bloque = wf[idx:idx+1500]
    assert "RE-ENTRAR" in bloque or "re-entrar" in bloque.lower()
    assert "NUNCA partir de cero" in bloque

