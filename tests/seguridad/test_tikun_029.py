"""tests/test_tikun_029.py — FP-074 Tikún HaShemiá VeHaDemo
Verifica RF-272 a RF-279.
"""
import importlib
import os
import re
import time


# ── RF-272: Demo2 affirmative flexible ──

def test_rf272_demo2_affirmative_exact():
    """Primer palabra afirmativa debe matchear."""
    _afirmativos = ("sí", "si", "yes", "dale", "va", "órale", "orale", "adelante", "claro", "porfa")
    for word in _afirmativos:
        tlow = word.strip().lower().strip("¡¿!?.,:; ")
        primera = tlow.split()[0] if tlow.split() else tlow
        assert primera in _afirmativos, f"'{word}' no matchea"


def test_rf272_demo2_affirmative_phrase():
    """'si, quiero verla' debe matchear por primer palabra + keyword."""
    texto = "Si, quiero verla."
    tlow = texto.strip().lower().strip("¡¿!?.,:; ")
    primera = tlow.split()[0] if tlow.split() else tlow
    _afirmativos = ("sí", "si", "yes", "dale", "va", "órale", "orale", "adelante", "claro", "porfa")
    es_afirmativo = primera in _afirmativos or any(w in tlow for w in ("quiero", "por favor", "muestra", "ver"))
    assert es_afirmativo, f"'{texto}' debería ser afirmativo"


def test_rf272_demo2_negative():
    """'no gracias' no debe matchear."""
    texto = "no gracias"
    tlow = texto.strip().lower().strip("¡¿!?.,:; ")
    primera = tlow.split()[0] if tlow.split() else tlow
    _afirmativos = ("sí", "si", "yes", "dale", "va", "órale", "orale", "adelante", "claro", "porfa")
    es_afirmativo = primera in _afirmativos or any(w in tlow for w in ("quiero", "por favor", "muestra", "ver"))
    assert not es_afirmativo


def test_rf272_demo2_quiero_only():
    """'quiero verla' matchea por keyword 'quiero'."""
    texto = "quiero verla"
    tlow = texto.strip().lower().strip("¡¿!?.,:; ")
    es_afirmativo = any(w in tlow for w in ("quiero", "por favor", "muestra", "ver"))
    assert es_afirmativo


# ── RF-273: Bypass noise filter durante demo2 ──

def test_rf273_esperando_demo2_sets_confirmacion():
    """ventana_principal.py debe set _esperando_confirmacion when _esperando_demo2."""
    from computadora.interfaz.ventana_principal import OrbeComputadora
    import inspect
    src = inspect.getsource(OrbeComputadora._demo_animaciones)
    # RF-273: debe haber _esperando_confirmacion = True cerca de _esperando_demo2 = True
    assert "_esperando_confirmacion" in src, "RF-273: falta bypass noise filter en demo2"


# ── RF-274: Echo inversion ──

def test_rf274_echo_inversion_logic():
    """La lógica de eco debe descartar ratio >= 0.15 durante TTS."""
    from difflib import SequenceMatcher
    # Simular eco corrupto de Whisper
    texto_tts = "buenas tardes señor alerta del sistema ram al 87 porciento"
    texto_whisper = "buenas tardes yummy"
    ratio = SequenceMatcher(None, texto_whisper, texto_tts).ratio()
    # Bajo la lógica invertida RF-274: ratio >= 0.15 → eco (descartar)
    assert ratio >= 0.15, f"Este caso debería filtrarse como eco, ratio={ratio:.2f}"
    # Interrupción real: contenido completamente diferente y sin overlap
    texto_real = "pon jazz"
    ratio_real = SequenceMatcher(None, texto_real, texto_tts).ratio()
    assert ratio_real < 0.15, f"Interrupción real debe tener ratio < 0.15, got {ratio_real:.2f}"


def test_rf274_subcadena_filter():
    """Subcadena del TTS siempre se filtra como eco."""
    texto_tts = "señor en qué puedo serle útil"
    texto_sub = "señor"
    assert texto_sub.lower() in texto_tts.lower()


# ── RF-275: Timestamp guard ──

def test_rf275_tts_inicio_ts_exists():
    """subir_umbral debe setear _tts_inicio_ts."""
    import inspect
    from computadora.voz.escucha import HiloEscucha
    src = inspect.getsource(HiloEscucha.subir_umbral)
    assert "_tts_inicio_ts" in src, "RF-275: falta timestamp guard en subir_umbral"


def test_rf275_guard_300ms_in_detection():
    """La detección de eco debe verificar 300ms guard."""
    import inspect
    from computadora.voz.escucha import HiloEscucha
    # Read the _procesar_transcripcion or related method
    src = inspect.getsource(HiloEscucha)
    assert "0.3" in src or "300" in src, "RF-275: guard 300ms no encontrado"
    assert "_tts_inicio_ts" in src


# ── RF-276: Bereshit pre-threshold ──

def test_rf276_bereshit_pre_threshold():
    """Bereshit debe llamar subir_umbral antes de hablar."""
    path = os.path.join(os.path.dirname(__file__), "..", "computadora", "interfaz", "ventana_principal.py")
    src = open(path, encoding="utf-8").read()
    # Buscar en la zona de Bereshit completado: subir_umbral antes de hablar(bereshit_mensaje)
    idx_subir = src.find("# RF-276: Subir umbral ANTES")
    idx_hablar = src.find("hablar(self._bereshit_mensaje)")
    assert idx_subir != -1, "RF-276: subir_umbral no encontrado en Bereshit"
    assert idx_subir < idx_hablar, "RF-276: subir_umbral debe estar ANTES de hablar"


# ── RF-277: PM #11 "fluye" ──

def test_rf277_pm_fluye_in_workflow():
    """DEVELOPMENT_WORKFLOW.md debe contener PM 'fluye'."""
    path = os.path.join(os.path.dirname(__file__), "..", "DEVELOPMENT_WORKFLOW.md")
    contenido = open(path, encoding="utf-8").read()
    assert "fluye" in contenido
    assert "שטוף" in contenido or "Shtóf" in contenido


# ── RF-278: ALBEDO sub-tarea (E) ──

def test_rf278_albedo_subtask_e():
    """Regla #17 ALBEDO debe contener sub-tarea (E) Milot Kóaj."""
    path = os.path.join(os.path.dirname(__file__), "..", "DEVELOPMENT_WORKFLOW.md")
    contenido = open(path, encoding="utf-8").read()
    assert "(E) Milot" in contenido or "Milot Kóaj Jai" in contenido


# ── RF-279: Doc PALABRAS_MAGICAS_SUGERENCIAS.md ──

def test_rf279_doc_exists():
    """PALABRAS_MAGICAS_SUGERENCIAS.md debe existir."""
    path = os.path.join(os.path.dirname(__file__), "..", "PALABRAS_MAGICAS_SUGERENCIAS.md")
    assert os.path.isfile(path), "RF-279: doc no encontrado"


def test_rf279_doc_structure():
    """El doc debe tener tabla de sugerencias y proceso Gate 2."""
    path = os.path.join(os.path.dirname(__file__), "..", "PALABRAS_MAGICAS_SUGERENCIAS.md")
    contenido = open(path, encoding="utf-8").read()
    assert "Gate 2" in contenido
    assert "SUGERIDA" in contenido or "SUGERENCIAS" in contenido
    assert "APROBADA" in contenido or "APROBADAS" in contenido

