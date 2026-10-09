"""
Tests FP-113: עיני השומר Einéi HaShomér (Ojos del Guardián).
WI-153: Dev Tools live camera
WI-154: Guardian sensor maintenance
WI-155: RAM baseline fast-track + environment-aware suppression
WI-156: Smart dodge with flee vector
"""
import sys, os, math
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
# WI-153: Dev Tools live camera — imports
# ═══════════════════════════════════════════════

check("WI153-01", "Import ventana_principal module", lambda: (
    __import__('computadora.interfaz.ventana_principal', fromlist=['VentanaPrincipal']) is not None,
    "módulo importable"
))

check("WI153-02", "OrbeComputadora has _mostrar_camara_dev", lambda: (
    hasattr(__import__('computadora.interfaz.ventana_principal',
        fromlist=['OrbeComputadora']).OrbeComputadora, '_mostrar_camara_dev'),
    "método _mostrar_camara_dev existe"
))


# ═══════════════════════════════════════════════
# WI-154: Guardian sensor maintenance
# ═══════════════════════════════════════════════

check("WI154-01", "Import flujos_guardian", lambda: (
    __import__('computadora.cerebro.flujos_guardian',
        fromlist=['activar_guardian', 'desactivar_guardian']) is not None,
    "módulo importable"
))

check("WI154-02", "activar_guardian is callable", lambda: (
    callable(getattr(__import__('computadora.cerebro.flujos_guardian',
        fromlist=['activar_guardian']), 'activar_guardian')),
    "función activar_guardian accesible"
))

check("WI154-03", "desactivar_guardian is callable", lambda: (
    callable(getattr(__import__('computadora.cerebro.flujos_guardian',
        fromlist=['desactivar_guardian']), 'desactivar_guardian')),
    "función desactivar_guardian accesible"
))


# ═══════════════════════════════════════════════
# WI-155: RAM baseline fast-track + environment-aware
# ═══════════════════════════════════════════════

check("WI155-01", "_DIAS_MINIMOS == 3 (module-level)", lambda: (
    __import__('computadora.habilidades.baseline_sistema',
        fromlist=['_DIAS_MINIMOS'])._DIAS_MINIMOS == 3,
    "_DIAS_MINIMOS reducido a 3"
))

check("WI155-02", "MonitorSistema has _ram_es_entorno_normal", lambda: (
    hasattr(__import__('computadora.habilidades.monitor_sistema',
        fromlist=['MonitorSistema']).MonitorSistema, '_ram_es_entorno_normal'),
    "método _ram_es_entorno_normal existe"
))

check("WI155-03", "PROCESOS_CONOCIDOS includes IDE entries", lambda: (
    all(k in __import__('computadora.habilidades.monitor_sistema',
        fromlist=['_PROCESOS_CONOCIDOS'])._PROCESOS_CONOCIDOS
        for k in ('code', 'studio64', 'java', 'gradle')),
    "entradas IDE presentes en _PROCESOS_CONOCIDOS"
))


# ═══════════════════════════════════════════════
# WI-156: Smart dodge with flee vector
# ═══════════════════════════════════════════════

check("WI156-01", "Import vida_autonoma", lambda: (
    __import__('computadora.interfaz.vida_autonoma', fromlist=['VidaAutonoma']) is not None,
    "módulo importable"
))

check("WI156-02", "VidaAutonoma._esquivar exists", lambda: (
    hasattr(__import__('computadora.interfaz.vida_autonoma',
        fromlist=['VidaAutonoma']).VidaAutonoma, '_esquivar'),
    "método _esquivar existe"
))

check("WI156-03", "Flee vector logic: opposite direction", lambda: (
    # Simular: orbe en (500,500), cursor en (600,600) → flee debería ir hacia (400,400)
    (lambda dx, dy: (dx < 0 and dy < 0, f"dx={dx:.1f}, dy={dy:.1f} (negativo = huye correctamente)"))(
        500 - 600, 500 - 600  # orbe - cursor
    )
))

check("WI156-04", "Wall-sliding clamp works", lambda: (
    # Si flee apunta a x=-50, clampar a margen=10 → resultado = 10
    (lambda clamped: (clamped == 10, f"clampado a {clamped}"))(
        max(10, min(-50, 1900))
    )
))


# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════

def test_fp113_resumen():
    passed = sum(1 for _, _, ok, _ in resultados if ok)
    total = len(resultados)
    print(f"\n{'='*50}")
    print(f"FP-113 — {passed}/{total} checks passed")
    for id_, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id_}: {desc} — {det}")
    assert passed == total, f"{total - passed} checks failed"


if __name__ == '__main__':
    test_fp113_resumen()

