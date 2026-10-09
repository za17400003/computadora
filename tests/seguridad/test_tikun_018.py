"""Tikún Ciclo 18 — C1: Shlijut (thread-safety demo) + C2: Tikún HaSefer (docs)"""
import sys, os, re, importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

resultados = []
def check(id, desc, fn):
    try:
        ok, detalle = fn()
        resultados.append((id, desc, ok, detalle))
        print(f"{'PASS' if ok else 'FAIL'} {id}: {desc} — {detalle}")
    except Exception as e:
        resultados.append((id, desc, False, str(e)))
        print(f"FAIL {id}: {desc} — {e}")

# ─── C1: Thread-safety — QTimer.singleShot eliminado de hilos demo ───

def test_no_qtimer_in_demo_memoria():
    src = open("computadora/interfaz/ventana_principal.py", "r", encoding="utf-8").read()
    match = re.search(r'def _demo_narrar_memoria_gevura\(self\)(.*?)(?=\n    def )', src, re.DOTALL)
    if not match:
        return False, "Method not found"
    body = match.group(1)
    has_signal = "_demo_herramienta_signal.emit" in body
    has_timer = "QTimer.singleShot" in body
    if has_signal and not has_timer:
        return True, "Uses signal, no QTimer"
    return False, f"signal={has_signal}, QTimer={has_timer}"

def test_no_qtimer_in_demo_rostro():
    src = open("computadora/interfaz/ventana_principal.py", "r", encoding="utf-8").read()
    match = re.search(r'def _demo_reconocimiento_facial\(self\)(.*?)(?=\n    def )', src, re.DOTALL)
    if not match:
        return False, "Method not found"
    body = match.group(1)
    has_signal = "_demo_herramienta_signal.emit" in body
    has_timer = "QTimer.singleShot" in body
    if has_signal and not has_timer:
        return True, "Uses signal, no QTimer"
    return False, f"signal={has_signal}, QTimer={has_timer}"

def test_demo_herramienta_signal_exists():
    src = open("computadora/interfaz/ventana_principal.py", "r", encoding="utf-8").read()
    ok = "_demo_herramienta_signal = pyqtSignal(str, str)" in src
    return ok, "pyqtSignal declared" if ok else "NOT found"

def test_demo_ejecutar_herramienta_uses_signal():
    src = open("computadora/interfaz/ventana_principal.py", "r", encoding="utf-8").read()
    match = re.search(r'def _demo_ejecutar_herramienta\(self.*?\)(.*?)(?=\n    def )', src, re.DOTALL)
    if not match:
        return False, "Method not found"
    body = match.group(1)
    return "_demo_herramienta_signal.emit" in body, "Uses signal"

check("C1-01", "demo_consultar_memoria uses signal not QTimer", test_no_qtimer_in_demo_memoria)
check("C1-02", "demo_reconocimiento_facial uses signal not QTimer", test_no_qtimer_in_demo_rostro)
check("C1-03", "_demo_herramienta_signal declared", test_demo_herramienta_signal_exists)
check("C1-04", "_demo_ejecutar_herramienta uses signal (B4)", test_demo_ejecutar_herramienta_uses_signal)

# ─── C2: Docs correctness ───

def test_workflow_escucha_path():
    src = open("DEVELOPMENT_WORKFLOW.md", "r", encoding="utf-8").read()
    ok = "computadora.voz.escucha" in src and "computadora.oidos.escucha" not in src
    return ok, "computadora.voz.escucha correct" if ok else "Still wrong"

def test_workflow_personalidad_path():
    src = open("DEVELOPMENT_WORKFLOW.md", "r", encoding="utf-8").read()
    ok = "computadora.memoria.personalidad" in src and "computadora.personalidad.personalidad" not in src
    return ok, "computadora.memoria.personalidad correct" if ok else "Still wrong"

def test_workflow_orbe_path():
    src = open("DEVELOPMENT_WORKFLOW.md", "r", encoding="utf-8").read()
    ok = "computadora.interfaz.ventana_principal" in src and "computadora.gui.ventana_principal" not in src
    return ok, "computadora.interfaz.ventana_principal correct" if ok else "Still wrong"

def test_sdd_whisper_exception():
    src = open("SDD.md", "r", encoding="utf-8").read()
    return "Whisper: 60s/180s" in src, "Whisper exception documented"

def test_modules_import_correctly():
    for m in ['computadora.voz.escucha', 'computadora.memoria.personalidad', 'computadora.interfaz.ventana_principal']:
        importlib.import_module(m)
    return True, "All 3 modules import OK"

check("C2-01", "Escucha path corrected", test_workflow_escucha_path)
check("C2-02", "Personalidad path corrected", test_workflow_personalidad_path)
check("C2-03", "Orbe path corrected", test_workflow_orbe_path)
check("C2-04", "SDD watchdog Whisper exception", test_sdd_whisper_exception)
check("C2-05", "Corrected modules import OK", test_modules_import_correctly)

total = len(resultados)
passed = sum(1 for r in resultados if r[2])
print(f"\n{'='*50}\nRESULTADO: {passed} PASS / {total-passed} FAIL / {total} TOTAL")

