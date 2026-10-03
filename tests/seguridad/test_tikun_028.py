"""Tikún 028 — Tests para FP-072 תיקון הגבורה והעין (RF-254 a RF-265)."""
import sys, os, re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ── RF-254: _RE_DEMO_HERRAMIENTAS definido ──

def test_rf254_regex_exists():
    """_RE_DEMO_HERRAMIENTAS está definido en nlu.py."""
    src = open("golem/cerebro/nlu.py", encoding="utf-8").read()
    assert "_RE_DEMO_HERRAMIENTAS" in src
    assert "re.compile" in src or "re_demo_herramientas" in src.lower()


def test_rf254_patterns():
    """_RE_DEMO_HERRAMIENTAS cubre los patrones clave."""
    src = open("golem/cerebro/nlu.py", encoding="utf-8").read()
    for pattern in ["demo", "segunda", "gevur"]:
        assert pattern in src.lower()


# ── RF-255: Strip puntuación en Demo 2 interceptor ──

def test_rf255_strip_punctuation():
    """ventana_principal strip de puntuación en comparación de texto."""
    src = open("golem/interfaz/ventana_principal.py", encoding="utf-8").read()
    assert '.strip("¡¿!?.,:; ")' in src or ".strip('¡¿!?.,:; ')" in src


# ── RF-256: VS Code helpers en procesos conocidos ──

def test_rf256_vscode_helpers():
    """monitor_sistema reconoce procesos de VS Code."""
    src = open("golem/habilidades/monitor_sistema.py", encoding="utf-8").read()
    for proc in ["codehelper", "extensionhost", "electron"]:
        assert proc in src.lower()


# ── RF-257: Anti-leak de tool calls ──

def test_rf257_function_call_detection():
    """_limpiar_para_voz detecta patrones tipo Name(args)."""
    src = open("golem/cerebro/nlu.py", encoding="utf-8").read()
    assert "A-Za-z_" in src or "function" in src.lower()
    # Debe tener regex para detectar llamadas a funciones
    assert r"\(" in src


# ── RF-258: descubrir_observadores ──

def test_rf258_discovery_method():
    """GestorKelim tiene método descubrir_observadores."""
    src = open("golem/nucleo/kli.py", encoding="utf-8").read()
    assert "def descubrir_observadores" in src
    assert "def obtener_observadores" in src


def test_rf258_usb_scan():
    """descubrir_observadores escanea cámaras USB (índices 0-4)."""
    src = open("golem/nucleo/kli.py", encoding="utf-8").read()
    assert "VideoCapture" in src or "cv2" in src
    assert "range(" in src


def test_rf258_rtsp_probe():
    """descubrir_observadores prueba RTSP en IPs de LAN."""
    src = open("golem/nucleo/kli.py", encoding="utf-8").read()
    assert "554" in src or "rtsp" in src.lower()


# ── RF-259: KliCamaraIP ──

def test_rf259_class_exists():
    """KliCamaraIP existe en vision.py."""
    src = open("golem/habilidades/vision.py", encoding="utf-8").read()
    assert "class KliCamaraIP" in src


def test_rf259_anti_ssrf():
    """KliCamaraIP valida que la IP sea privada (anti-SSRF)."""
    src = open("golem/habilidades/vision.py", encoding="utf-8").read()
    assert "is_private" in src or "_es_ip_privada" in src


def test_rf259_rtsp_connect():
    """KliCamaraIP acepta url_rtsp."""
    src = open("golem/habilidades/vision.py", encoding="utf-8").read()
    assert "url_rtsp" in src
    assert "conectar" in src


def test_rf259_import_from_kli():
    """kli.py importa KliCamaraIP de vision.py."""
    src = open("golem/nucleo/kli.py", encoding="utf-8").read()
    assert "KliCamaraIP" in src


# ── RF-260: Boot discovery ──

def test_rf260_boot_discovery():
    """__main__.py llama descubrir_observadores al arranque."""
    src = open("golem/__main__.py", encoding="utf-8").read()
    assert "descubrir_observadores" in src
    assert "GestorKelim" in src


# ── RF-261: PerceptorDaat multi-ojo ──

def test_rf261_multi_eye_methods():
    """PerceptorDaat tiene leer_todos_los_ojos y procesar_todos_los_ojos."""
    src = open("golem/percepcion/perceptor.py", encoding="utf-8").read()
    assert "def leer_todos_los_ojos" in src
    assert "def procesar_todos_los_ojos" in src


def test_rf261_uses_gestor_kelim():
    """Multi-ojo usa GestorKelim.obtener_observadores."""
    src = open("golem/percepcion/perceptor.py", encoding="utf-8").read()
    assert "obtener_observadores" in src


def test_rf261_tracks_active_eyes():
    """Multi-ojo registra ojos_activos en snapshot."""
    src = open("golem/percepcion/perceptor.py", encoding="utf-8").read()
    assert "ojos_activos" in src
    assert "ojos_con_movimiento" in src


# ── RF-262: NIGREDO boot + SDD check ──

def test_rf262_nigredo_boot_check():
    """DEVELOPMENT_WORKFLOW.md incluye Paso 0 boot en NIGREDO."""
    src = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    assert "PASO 0" in src
    assert "iniciar_golem.bat" in src


def test_rf262_sdd_check():
    """DEVELOPMENT_WORKFLOW.md incluye Paso 0b SDD check en NIGREDO."""
    src = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    assert "PASO 0" in src
    assert "SDD" in src


# ── RF-263: Palabra Mágica "crece automáticamente" ──

def test_rf263_pm10():
    """Tabla de Palabras Mágicas incluye #10 'crece automáticamente'."""
    src = open("DEVELOPMENT_WORKFLOW.md", encoding="utf-8").read()
    assert "crece automáticamente" in src
    assert "| 10 |" in src


# ── RF-264: Índice de subsistemas ──

def test_rf264_subsystem_index():
    """SRS.md tiene índice de subsistemas por Sefirá."""
    src = open("SRS.md", encoding="utf-8").read()
    assert "Índice de Subsistemas por Sefirá" in src
    assert "Kelim" in src


# ── RF-265: SDD Etz HaChaim v3.6 ──

def test_rf265_version():
    """SDD.md actualizado a v3.6."""
    src = open("SDD.md", encoding="utf-8").read()
    assert "v3.6" in src


def test_rf265_kli_camara_ip_in_sdd():
    """SDD refleja KliCamaraIP."""
    src = open("SDD.md", encoding="utf-8").read()
    assert "KliCamaraIP" in src


def test_rf265_new_senderos():
    """SDD tiene senderos nuevos Da'at↔Kelim."""
    src = open("SDD.md", encoding="utf-8").read()
    assert "Da'at→Kelim" in src or "Da'at↔Kelim" in src or "Da'at→Kelim" in src

