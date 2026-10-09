"""
Tests FP-035: תשובה (Teshuvá) — 4 bugs latentes corregidos.
RF-98: OllamaGuard, sys.exit guard, emb NameError, on_permiso_copilot.
"""
import sys, os, time, threading, inspect
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

CWD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ═══════════════════════════════════════════════
# FP-035.1: OllamaGuard — Thread-safe busy flag
# ═══════════════════════════════════════════════

from computadora.interfaz.watchdog import OllamaGuard, ollama_guard

check("FP35-01", "OllamaGuard class importable", lambda: (
    OllamaGuard is not None,
    "clase disponible"
))

check("FP35-02", "ollama_guard singleton existe", lambda: (
    isinstance(ollama_guard, OllamaGuard),
    "singleton instanciado"
))

check("FP35-03", "OllamaGuard.ocupado es property", lambda: (
    isinstance(type(ollama_guard).ocupado, property),
    "property verificada"
))

check("FP35-04", "OllamaGuard inicia no-ocupado", lambda: (
    not OllamaGuard(timeout=5.0).ocupado,
    "ocupado=False al inicio"
))

def _test_context_manager():
    g = OllamaGuard(timeout=5.0)
    with g:
        dentro = g.ocupado
    fuera = g.ocupado
    return dentro and not fuera, f"dentro={dentro}, fuera={fuera}"

check("FP35-05", "Context manager __enter__/__exit__ funciona", _test_context_manager)

def _test_auto_reset():
    g = OllamaGuard(timeout=0.1)  # 100ms timeout
    g.__enter__()
    time.sleep(0.2)  # Esperar a que expire
    auto_reset = not g.ocupado  # Debe haber hecho auto-reset
    g.__exit__(None, None, None)
    return auto_reset, "auto-reset tras timeout"

check("FP35-06", "Auto-reset tras timeout", _test_auto_reset)

check("FP35-07", "OllamaGuard usa threading.Event internamente", lambda: (
    isinstance(OllamaGuard(timeout=5.0)._busy, threading.Event),
    "threading.Event"
))

check("FP35-08", "OllamaGuard usa threading.Lock internamente", lambda: (
    hasattr(OllamaGuard(timeout=5.0)._lock, 'acquire') and hasattr(OllamaGuard(timeout=5.0)._lock, 'release'),
    "Lock con acquire/release"
))

# ─── Integración: nlu.py usa `with ollama_guard:` ───

def _test_nlu_usa_ollama_guard():
    src = open(os.path.join(CWD, "computadora", "cerebro", "nlu.py"), encoding="utf-8").read()
    count = src.count("with ollama_guard:")
    return count >= 2, f"{count} usos de 'with ollama_guard:'"

check("FP35-09", "nlu.py usa 'with ollama_guard:' (>=2 veces)", _test_nlu_usa_ollama_guard)

# ═══════════════════════════════════════════════
# FP-035.2: sys.exit guard en tests
# ═══════════════════════════════════════════════

def _test_sys_exit_guarded(filepath):
    src = open(filepath, encoding="utf-8").read()
    if "sys.exit" not in src:
        return True, "no tiene sys.exit"
    has_guard = 'if __name__ == "__main__"' in src or "if __name__ == '__main__'" in src
    return has_guard, "sys.exit guardado con __name__" if has_guard else "sys.exit sin guardia"

check("FP35-10", "test_fp023_tikun.py: sys.exit guardado", lambda:
    _test_sys_exit_guarded(os.path.join(CWD, "tests", "test_fp023_tikun.py"))
)

check("FP35-11", "test_fp021_phase1.py: sys.exit guardado", lambda:
    _test_sys_exit_guarded(os.path.join(CWD, "tests", "test_fp021_phase1.py"))
)

# ═══════════════════════════════════════════════
# FP-035.3: emb extraído ANTES de checks de wake word
# ═══════════════════════════════════════════════

def _test_emb_antes_de_checks():
    src = open(os.path.join(CWD, "computadora", "voz", "escucha.py"), encoding="utf-8").read()
    pos_emb = src.find("emb = self._extraer_embedding")
    # Buscar los checks de wake word que usan emb
    pos_nombre = src.find("# nombre completo")
    pos_apellido = src.find("# apellido")
    if pos_emb < 0:
        return False, "no se encontró 'emb = self._extraer_embedding'"
    # emb debe estar ANTES de los usos
    if pos_nombre > 0 and pos_emb > pos_nombre:
        return False, f"emb (pos={pos_emb}) DESPUÉS de nombre check (pos={pos_nombre})"
    if pos_apellido > 0 and pos_emb > pos_apellido:
        return False, f"emb (pos={pos_emb}) DESPUÉS de apellido check (pos={pos_apellido})"
    return True, f"emb en pos={pos_emb}, antes de checks"

check("FP35-12", "escucha.py: emb se extrae ANTES de wake word checks", _test_emb_antes_de_checks)

# ═══════════════════════════════════════════════
# FP-035.4: solicitar_permiso_copilot (no on_permiso_copilot)
# ═══════════════════════════════════════════════

def _test_no_on_permiso_copilot():
    src = open(os.path.join(CWD, "computadora", "cerebro", "nlu.py"), encoding="utf-8").read()
    # on_permiso_copilot NO debe existir como atributo usado
    # Excluir comentarios y la propia definición
    uses = [l.strip() for l in src.splitlines()
            if "on_permiso_copilot" in l and not l.strip().startswith("#")]
    return len(uses) == 0, f"0 usos de on_permiso_copilot" if len(uses) == 0 else f"{len(uses)} usos encontrados: {uses[:3]}"

check("FP35-13", "nlu.py: NO usa on_permiso_copilot (bug original)", _test_no_on_permiso_copilot)

def _test_solicitar_permiso_existe():
    src = open(os.path.join(CWD, "computadora", "cerebro", "nlu.py"), encoding="utf-8").read()
    count = src.count("self.solicitar_permiso_copilot")
    return count >= 3, f"{count} usos de self.solicitar_permiso_copilot"

check("FP35-14", "nlu.py: usa solicitar_permiso_copilot (>=3 refs)", _test_solicitar_permiso_existe)

# ─── Summary ───
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
print(f"\n{'='*50}\nRESULTADO FP-035: {passed} PASS / {total-passed} FAIL / {total} TOTAL")

if __name__ == "__main__":
    sys.exit(0 if passed == total else 1)

