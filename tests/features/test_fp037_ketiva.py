"""
Tests para FP-037 כְּתִיבָה אָטוֹמִית Ketivá Atomit — Escritura Atómica (RF-100)
Verifica: io_seguro existe, función atómica funciona, todos los módulos usan escribir_json_atomico.
"""
import sys, os, json, tempfile, ast
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
# 1. MÓDULO io_seguro EXISTE Y FUNCIONA
# ═══════════════════════════════════════════════

check("FP37-01", "io_seguro.py existe",
      lambda: (
          os.path.isfile(os.path.join(os.path.dirname(__file__), '..', 'golem', 'utilidades', 'io_seguro.py')),
          "Encontrado"
      ))

check("FP37-02", "escribir_json_atomico importable",
      lambda: (
          (lambda: (__import__('golem.utilidades.io_seguro', fromlist=['escribir_json_atomico']), True)[-1])(),
          "Import OK"
      ))

def _test_atomico_basico():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "test.json")
        datos = {"clave": "valor", "num": 42}
        escribir_json_atomico(ruta, datos)
        with open(ruta, encoding="utf-8") as f:
            leido = json.load(f)
        return leido == datos, f"Escrito y leído correctamente: {leido}"

check("FP37-03", "escribir_json_atomico escribe y lee correctamente", _test_atomico_basico)

def _test_atomico_subdirectorio():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "sub", "dir", "test.json")
        escribir_json_atomico(ruta, [1, 2, 3])
        with open(ruta, encoding="utf-8") as f:
            leido = json.load(f)
        return leido == [1, 2, 3], "Crea subdirectorios automáticamente"

check("FP37-04", "escribir_json_atomico crea subdirectorios", _test_atomico_subdirectorio)

def _test_atomico_sobreescritura():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "test.json")
        escribir_json_atomico(ruta, {"v": 1})
        escribir_json_atomico(ruta, {"v": 2})
        with open(ruta, encoding="utf-8") as f:
            leido = json.load(f)
        return leido == {"v": 2}, f"Sobreescritura funciona: {leido}"

check("FP37-05", "escribir_json_atomico sobreescribe correctamente", _test_atomico_sobreescritura)

def _test_atomico_indent():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "test.json")
        escribir_json_atomico(ruta, {"a": 1}, indent=4)
        with open(ruta, encoding="utf-8") as f:
            contenido = f.read()
        return '    "a"' in contenido, "indent=4 respetado"

check("FP37-06", "escribir_json_atomico respeta parámetro indent", _test_atomico_indent)

def _test_atomico_unicode():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "test.json")
        datos = {"nombre": "José", "emoji": "🔮"}
        escribir_json_atomico(ruta, datos)
        with open(ruta, encoding="utf-8") as f:
            leido = json.load(f)
        return leido == datos, f"Unicode preservado: {leido}"

check("FP37-07", "escribir_json_atomico preserva Unicode", _test_atomico_unicode)

def _test_atomico_no_deja_tmp():
    from computadora.utilidades.io_seguro import escribir_json_atomico
    with tempfile.TemporaryDirectory() as td:
        ruta = os.path.join(td, "test.json")
        escribir_json_atomico(ruta, {"ok": True})
        archivos = os.listdir(td)
        return archivos == ["test.json"], f"Solo test.json presente: {archivos}"

check("FP37-08", "escribir_json_atomico no deja archivos temporales", _test_atomico_no_deja_tmp)

# ═══════════════════════════════════════════════
# 2. TODOS LOS MÓDULOS USAN escribir_json_atomico
# ═══════════════════════════════════════════════

# Lista completa de módulos que deben usar escribir_json_atomico
MODULOS_ATOMICOS = [
    ("golem/interfaz/ventana_principal.py", "_guardar_evolucion"),
    ("golem/habilidades/auto_update.py", "_guardar_log"),
    ("golem/memoria/aprendizaje.py", "_guardar"),
    ("golem/habilidades/sistema.py", "_guardar_recordatorios"),
    ("golem/habilidades/copilot_bridge.py", "crear_solicitud"),
    ("golem/habilidades/copilot_bridge.py", "completar_solicitud"),
    ("golem/memoria/memoria.py", "_sample"),
    ("golem/memoria/memoria.py", "_guardar_temporal"),
    ("golem/cerebro/modelo_discovery.py", "_guardar_cache"),
    ("golem/cerebro/copilot_api.py", "_guardar_tokens"),
    ("golem/cerebro/nivel1_aprendido.py", "_guardar"),
    ("golem/nucleo/actualizador.py", "_guardar_estado"),
    ("golem/nucleo/ciclo_circadiano.py", "_guardar_perfil"),
    ("golem/nucleo/proactividad.py", "_check_patron_repetido"),
    ("golem/habilidades/agenda.py", "_guardar_json"),
    ("golem/interfaz/vida_autonoma.py", "_guardar_heatmap"),
    ("golem/voz/escucha.py", "_guardar_wake_variant"),
    ("golem/voz/escucha.py", "_save_owner_profile"),
    ("golem/voz/escucha.py", "_guardar_personas"),
    ("golem/nucleo/meta_workflow.py", "_guardar_registro"),
    ("golem/nucleo/meta_workflow.py", "emitir_auditoria"),
    ("golem/cerebro/nlu.py", "_guardar_stats_uso"),
    ("golem/habilidades/baseline_sistema.py", "_guardar"),
]

base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

for i, (mod_path, fn_name) in enumerate(MODULOS_ATOMICOS):
    full_path = os.path.join(base, mod_path.replace('/', os.sep))
    def _make_check(fp=full_path, fn=fn_name):
        def _check():
            with open(fp, encoding='utf-8') as f:
                src = f.read()
            return 'escribir_json_atomico' in src, \
                   f"Usa escribir_json_atomico" if 'escribir_json_atomico' in src else "NO usa escribir_json_atomico"
        return _check
    check(f"FP37-{9+i:02d}", f"{mod_path} ({fn_name}) usa escribir_json_atomico", _make_check())

# ═══════════════════════════════════════════════
# 3. NO QUEDAN ESCRITURAS NO-ATÓMICAS EN golem/
# ═══════════════════════════════════════════════

def _buscar_writes_no_atomicos():
    """Busca write_text(json.dumps y json.dump(..., f( en golem/ excluyendo io_seguro.py."""
    import re
    patron = re.compile(r'write_text\(json\.dumps|json\.dump\(.*,\s*f[,\)]')
    hallazgos = []
    for root, dirs, files in os.walk(os.path.join(base, 'golem')):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            if 'io_seguro.py' in fname:
                continue
            with open(fpath, encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    if patron.search(line):
                        rel = os.path.relpath(fpath, base)
                        hallazgos.append(f"{rel}:{lineno}")
    if hallazgos:
        return False, f"Encontradas {len(hallazgos)} escrituras no-atómicas: {', '.join(hallazgos)}"
    return True, "0 escrituras no-atómicas encontradas (excluyendo io_seguro.py)"

check("FP37-32", "No quedan escrituras JSON no-atómicas en golem/", _buscar_writes_no_atomicos)

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
print("\n" + "=" * 60)
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
failed = total - passed
print(f"FP-037 Ketivá Atomit: {passed}/{total} PASS, {failed} FAIL")
if failed:
    print("FALLOS:")
    for id, desc, ok, det in resultados:
        if not ok:
            print(f"  {id}: {desc} — {det}")
print("=" * 60)

if __name__ == "__main__":
    sys.exit(0 if failed == 0 else 1)

