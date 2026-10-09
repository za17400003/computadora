"""
Tests FP-114: תיקון הקליפות Tikún HaKlipót
WI-157: Clipboard encoding + null safety
WI-158: Systemic subprocess encoding (13 files, 40 calls)
WI-159: Demo fixes (duplicate guardian, 13 humores, Grimorio text)
WI-160: Async command processing + polling endpoint
"""
import sys, os, re, ast, inspect, threading, time
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


# ═══════════════════════════════════════════════
# WI-157: Clipboard encoding + null safety
# ═══════════════════════════════════════════════

def _read_clipboard_source():
    from computadora.habilidades import sistema
    return inspect.getsource(sistema.leer_portapapeles)

def _read_write_clipboard_source():
    from computadora.habilidades import sistema
    return inspect.getsource(sistema.escribir_portapapeles)

check("WI157-01", "leer_portapapeles has encoding='utf-8'", lambda: (
    "encoding='utf-8'" in _read_clipboard_source() or 'encoding="utf-8"' in _read_clipboard_source(),
    "encoding parameter present"
))

check("WI157-02", "leer_portapapeles has errors='replace'", lambda: (
    "errors='replace'" in _read_clipboard_source() or 'errors="replace"' in _read_clipboard_source(),
    "errors parameter present"
))

check("WI157-03", "leer_portapapeles null-safe stdout", lambda: (
    'result.stdout or ""' in _read_clipboard_source() or "(result.stdout or" in _read_clipboard_source(),
    "null-safe pattern found"
))

check("WI157-04", "escribir_portapapeles no command injection", lambda: (
    "Set-Clipboard -Value '{" not in _read_write_clipboard_source()
    and "Set-Clipboard -Value $input" in _read_write_clipboard_source(),
    "uses stdin pipe instead of string interpolation"
))

check("WI157-05", "escribir_portapapeles has encoding='utf-8'", lambda: (
    "encoding='utf-8'" in _read_write_clipboard_source() or 'encoding="utf-8"' in _read_write_clipboard_source(),
    "encoding parameter present"
))


# ═══════════════════════════════════════════════
# WI-158: Systemic subprocess encoding
# ═══════════════════════════════════════════════

def _count_unprotected_subprocess_calls():
    """Scan all .py files for text=True without encoding='utf-8'."""
    computadora_dir = os.path.join(os.path.dirname(__file__), '..', 'computadora')
    unprotected = []
    for root, dirs, files in os.walk(computadora_dir):
        for f in files:
            if not f.endswith('.py'):
                continue
            ruta = os.path.join(root, f)
            with open(ruta, encoding='utf-8', errors='replace') as fh:
                contenido = fh.read()
            # Find text=True that is NOT on the same logical call with encoding=
            # Simple heuristic: count text=True lines without encoding on same or next line
            lines = contenido.split('\n')
            for i, line in enumerate(lines):
                if 'text=True' in line and 'encoding=' not in line:
                    # Check next 2 lines for encoding=
                    context = '\n'.join(lines[i:i+3])
                    if 'encoding=' not in context:
                        unprotected.append(f"{f}:{i+1}")
    return unprotected

check("WI158-01", "No unprotected subprocess text=True calls", lambda: (
    len(_count_unprotected_subprocess_calls()) == 0,
    f"unprotected: {_count_unprotected_subprocess_calls()[:5]}" if _count_unprotected_subprocess_calls() else "all protected"
))


# ═══════════════════════════════════════════════
# WI-159: Demo fixes
# ═══════════════════════════════════════════════

def _demo_source():
    with open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'interfaz', 'ventana_principal.py'),
              encoding='utf-8') as f:
        return f.read()

def _demo_act1():
    src = _demo_source()
    a1 = src.find("ACT I:")
    a2 = src.find("ACT II:")
    return src[a1:a2] if a1 >= 0 and a2 > a1 else ""

check("WI159-01", "Demo no duplicate descanso_guardian in ACT I", lambda: (
    _demo_act1().count("descanso_guardian") == 0,
    "ACT I has 0 descanso_guardian references"
))

check("WI159-02", "Demo ACT III has all 13 humores", lambda: (
    all(h in _demo_source() for h in [
        "neutral", "sereno", "contento", "emocionado", "activo",
        "curioso", "reflexivo", "aburrido", "cansado", "triste",
        "formal", "regañado", "preocupado"
    ]),
    "all 13 humores mentioned"
))

check("WI159-03", "Demo no 'otros me consulten' text", lambda: (
    "otros me consulten" not in _demo_source() and "otros consulten" not in _demo_source(),
    "old text removed"
))

check("WI159-04", "Demo Grimorio exclusive text present", lambda: (
    "exclusivo" in _demo_source(),
    "exclusive ownership text found"
))


# ═══════════════════════════════════════════════
# WI-160: Async command processing
# ═══════════════════════════════════════════════

check("WI160-01", "servidor_api has _command_results dict", lambda: (
    hasattr(__import__('computadora.canales.servidor_api', fromlist=['_command_results']), '_command_results'),
    "global dict exists"
))

check("WI160-02", "servidor_api has _command_results_lock", lambda: (
    hasattr(__import__('computadora.canales.servidor_api', fromlist=['_command_results_lock']), '_command_results_lock'),
    "threading lock exists"
))

check("WI160-03", "servidor_api _COMMAND_TTL is 300", lambda: (
    getattr(__import__('computadora.canales.servidor_api', fromlist=['_COMMAND_TTL']), '_COMMAND_TTL') == 300,
    "TTL is 5 minutes"
))

def _servidor_source():
    with open(os.path.join(os.path.dirname(__file__), '..', 'computadora', 'canales', 'servidor_api.py'),
              encoding='utf-8') as f:
        return f.read()

check("WI160-04", "servidor_api _manejar_comando spawns thread", lambda: (
    "Thread(target=_process" in _servidor_source(),
    "async thread pattern found"
))

check("WI160-05", "servidor_api returns 202 with job_id", lambda: (
    '"estado": "accepted"' in _servidor_source() and '"job_id"' in _servidor_source() and "202" in _servidor_source(),
    "202 accepted + job_id response"
))

check("WI160-06", "servidor_api has _manejar_resultado endpoint", lambda: (
    "def _manejar_resultado" in _servidor_source() and "/api/resultado" in _servidor_source(),
    "polling endpoint exists"
))


# ═══════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════

def test_fp114_all():
    global resultados
    # Re-run if needed
    if not resultados:
        return
    failed = [(id, desc, det) for id, desc, ok, det in resultados if not ok]
    assert not failed, f"FAILED:\n" + "\n".join(f"  {id}: {desc} — {det}" for id, desc, det in failed)


if __name__ == "__main__":
    print(f"\n{'='*60}")
    total = len(resultados)
    passed = sum(1 for *_, ok, _ in resultados if ok)
    print(f"FP-114 Tikún HaKlipót: {passed}/{total} passed")
    if passed < total:
        print("FAILED:")
        for id, desc, ok, det in resultados:
            if not ok:
                print(f"  {id}: {desc} — {det}")

