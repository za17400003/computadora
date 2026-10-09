"""Tests Tikún 030 — FP-075: Shomer HaIdkún VeHaDemo (RF-280 a RF-285)."""
import sys, os, re, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── RF-280: HotReloader debounce ──

def test_rf280_hotreloader_has_debounce_timer():
    """HotReloader tiene _reinicio_pendientes y _reinicio_timer."""
    src = open("computadora/nucleo/hot_reload.py", encoding="utf-8").read()
    assert "_reinicio_pendientes" in src
    assert "_reinicio_timer" in src
    assert "10_000" in src or "10000" in src  # 10 seconds


def test_rf280_debounce_accumulates():
    """requiere_reinicio no se emite inline — se acumula."""
    src = open("computadora/nucleo/hot_reload.py", encoding="utf-8").read()
    # El bloque CAPAS_REINICIO_MANUAL ya no hace emit directo
    # Busca el patrón: append + start en vez de emit directo
    assert "_reinicio_pendientes.append" in src
    assert "_reinicio_timer.start()" in src


def test_rf280_emitir_debounced_method():
    """Existe _emitir_reinicio_debounced."""
    src = open("computadora/nucleo/hot_reload.py", encoding="utf-8").read()
    assert "def _emitir_reinicio_debounced" in src


# ── RF-281: Retry non-streaming ──

def test_rf281_retry_nonstreaming_before_fallback():
    """nlu.py retries non-streaming when streaming returns None."""
    src = open("computadora/cerebro/nlu.py", encoding="utf-8").read()
    # RF-281 comment should be present
    assert "RF-281" in src
    assert "reintentando non-streaming" in src


# ── RF-282: Demo 1 contexto_pantalla live ──

def test_rf282_demo1_uses_live_context():
    """Demo 1 uses self._contexto_pantalla.descripcion_contexto() directly."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    # Should NOT call ejecutar_herramienta("contexto_pantalla"...)
    assert 'ejecutar_herramienta("contexto_pantalla"' not in src
    # Should call descripcion_contexto directly in demo
    assert "orbe._contexto_pantalla.descripcion_contexto()" in src


# ── RF-283: Demo 1 ACT XI Neshamá ──

def test_rf283_demo1_has_act_xi():
    """Demo 1 includes ACT XI with identity narration."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "ACT XI" in src
    assert "NESHAMÁ" in src or "Neshamá" in src


def test_rf283_demo_narrar_memoria_method():
    """_demo_narrar_memoria method exists."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert "def _demo_narrar_memoria" in src
    assert "buscar_en_memoria" in src
    assert "calcular_tiempo_activo" in src


# ── RF-284: Demo 2 buscar_archivos args fix ──

def test_rf284_buscar_archivos_correct_args():
    """Demo 2 passes correct args to buscar_archivos."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    # Old wrong args should not exist
    assert '"patron"' not in src or '"patron": "*.txt"' not in src
    # New correct args
    assert '"nombre": ".txt"' in src


# ── RF-285: escanear_red replaced ──

def test_rf285_escanear_red_en_demo_fp080():
    """FP-080 RF-299: Demo 2 now includes escanear_red (supersedes RF-285)."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_herramientas")
    assert idx > 0
    demo_section = src[idx:idx+4000]
    assert "escanear_red" in demo_section


def test_rf285_consultar_memoria_in_demo2():
    """Demo 2 uses memory narration (RF-294 replaced consultar_memoria with _demo_narrar_memoria_gevura)."""
    src = open("computadora/interfaz/ventana_principal.py", encoding="utf-8").read()
    idx = src.find("def _demo_herramientas")
    assert idx > 0
    demo_section = src[idx:idx+4000]
    assert "_demo_narrar_memoria_gevura" in demo_section

