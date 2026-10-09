"""
Tests para ciclo Tikún #2 — FP-038 Ne'ilat Yejidim (RF-101)
Verifica threading.Lock en 3 singletons restantes.
"""
import sys, os, ast
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

base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def _check_lock_in_file(rel_path, lock_name):
    with open(os.path.join(base, rel_path), encoding='utf-8') as f:
        src = f.read()
    return lock_name in src, f"{'Encontrado' if lock_name in src else 'NO encontrado'}"

def _check_double_checked(rel_path, func_name):
    """Verifica patrón: if X is None: with lock: if X is None:"""
    with open(os.path.join(base, rel_path), encoding='utf-8') as f:
        src = f.read()
    # Find the function and check for nested if+with+if
    in_func = False
    with_count = 0
    none_checks = 0
    for line in src.splitlines():
        if f'def {func_name}' in line:
            in_func = True
            with_count = 0
            none_checks = 0
        elif in_func:
            if line.strip().startswith('def '):
                break
            if 'is None' in line:
                none_checks += 1
            if 'with ' in line and 'lock' in line.lower():
                with_count += 1
    ok = with_count >= 1 and none_checks >= 2
    return ok, f"with_lock={with_count}, none_checks={none_checks}"

# eventos.py
check("T2-01", "eventos.py: _bus_global_lock existe",
      lambda: _check_lock_in_file("computadora/nucleo/eventos.py", "_bus_global_lock"))
check("T2-02", "eventos.py: double-checked locking en obtener_bus",
      lambda: _check_double_checked("computadora/nucleo/eventos.py", "obtener_bus"))

# ciclo_circadiano.py
check("T2-03", "ciclo_circadiano.py: _ciclo_lock existe",
      lambda: _check_lock_in_file("computadora/nucleo/ciclo_circadiano.py", "_ciclo_lock"))
check("T2-04", "ciclo_circadiano.py: double-checked locking en inicializar_ciclo",
      lambda: _check_double_checked("computadora/nucleo/ciclo_circadiano.py", "inicializar_ciclo"))

# memoria.py
check("T2-05", "memoria.py: _compressor_lock existe",
      lambda: _check_lock_in_file("computadora/memoria/memoria.py", "_compressor_lock"))
check("T2-06", "memoria.py: lock en start_daily_compressor",
      lambda: (lambda: (
          'with _compressor_lock' in open(os.path.join(base, "computadora/memoria/memoria.py"), encoding='utf-8').read(),
          "with _compressor_lock presente"
      ))())

# Imports OK
def _import_ok(mod):
    try:
        __import__(mod)
        return True, "Import OK"
    except Exception as e:
        return False, str(e)

check("T2-07", "eventos.py importa sin error",
      lambda: _import_ok('computadora.nucleo.eventos'))
check("T2-08", "ciclo_circadiano.py importa sin error",
      lambda: _import_ok('computadora.nucleo.ciclo_circadiano'))
check("T2-09", "memoria.py importa sin error",
      lambda: _import_ok('computadora.memoria.memoria'))

# Regression: FP-036 locks still present
check("T2-10", "herramientas.py: _gestor_permisos_lock (FP-036)",
      lambda: _check_lock_in_file("computadora/habilidades/herramientas.py", "_gestor_permisos_lock"))
check("T2-11", "monitor_sistema.py: _monitor_global_lock (FP-036)",
      lambda: _check_lock_in_file("computadora/habilidades/monitor_sistema.py", "_monitor_global_lock"))
check("T2-12", "copilot_api.py: _instancia_lock (FP-036)",
      lambda: _check_lock_in_file("computadora/cerebro/copilot_api.py", "_instancia_lock"))

print(f"\n{'='*60}")
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
print(f"Tikún #2 (FP-038): {passed}/{total} PASS, {total-passed} FAIL")
print("=" * 60)
if __name__ == "__main__":
    sys.exit(0 if passed == total else 1)

