"""
Tests para FP-036 טָהֳרַת הַקּוֹד Tohorat HaCode — Purificación del Código (RF-99)
Verifica: dead code eliminado, silent excepts con logging, singletons con Lock,
BLOQUE 2 eliminado, OWASP documentado.
"""
import sys, os, inspect, re, ast, threading
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
# 1. DEAD CODE ELIMINADO (herramientas.py)
# ═══════════════════════════════════════════════
herr_path = os.path.join(os.path.dirname(__file__), '..', 'golem', 'habilidades', 'herramientas.py')
with open(herr_path, encoding='utf-8') as f:
    herr_src = f.read()

check("FP36-01", "COMANDOS_BLOQUEADOS eliminado de herramientas.py",
      lambda: (
          'COMANDOS_BLOQUEADOS' not in herr_src,
          "No encontrado (correcto)" if 'COMANDOS_BLOQUEADOS' not in herr_src else "AÚN EXISTE"
      ))

check("FP36-02", "COMANDOS_SISTEMA_INFO eliminado de herramientas.py",
      lambda: (
          'COMANDOS_SISTEMA_INFO' not in herr_src,
          "No encontrado (correcto)" if 'COMANDOS_SISTEMA_INFO' not in herr_src else "AÚN EXISTE"
      ))

check("FP36-03", "_PING_RE eliminado de herramientas.py",
      lambda: (
          '_PING_RE' not in herr_src,
          "No encontrado (correcto)" if '_PING_RE' not in herr_src else "AÚN EXISTE"
      ))

check("FP36-04", "_SHELL_METACHAR_RE eliminado de herramientas.py",
      lambda: (
          '_SHELL_METACHAR_RE' not in herr_src,
          "No encontrado (correcto)" if '_SHELL_METACHAR_RE' not in herr_src else "AÚN EXISTE"
      ))

check("FP36-05", "_sanitizar_comando eliminado de herramientas.py",
      lambda: (
          '_sanitizar_comando' not in herr_src,
          "No encontrado (correcto)" if '_sanitizar_comando' not in herr_src else "AÚN EXISTE"
      ))

check("FP36-06", "_es_comando_sistema_permitido eliminado de herramientas.py",
      lambda: (
          '_es_comando_sistema_permitido' not in herr_src,
          "No encontrado (correcto)" if '_es_comando_sistema_permitido' not in herr_src else "AÚN EXISTE"
      ))

# Verify delegations still work
check("FP36-07", "ejecutar_comando() sigue existiendo",
      lambda: (
          'def ejecutar_comando(' in herr_src,
          "Función presente" if 'def ejecutar_comando(' in herr_src else "FALTA"
      ))

check("FP36-08", "ejecutar_comando_sistema() sigue existiendo",
      lambda: (
          'def ejecutar_comando_sistema(' in herr_src,
          "Función presente" if 'def ejecutar_comando_sistema(' in herr_src else "FALTA"
      ))

# ═══════════════════════════════════════════════
# 2. SILENT EXCEPTS → LOGGING (habla.py)
# ═══════════════════════════════════════════════
habla_path = os.path.join(os.path.dirname(__file__), '..', 'golem', 'voz', 'habla.py')
with open(habla_path, encoding='utf-8') as f:
    habla_src = f.read()

# Count bare "except Exception:\n            pass" (indented) — should be 0 in _calcular_audio_adaptativo
def check_no_silent_in_audio():
    # Find _calcular_audio_adaptativo method body
    match = re.search(r'def _calcular_audio_adaptativo.*?(?=\n    def |\nclass |\Z)', habla_src, re.DOTALL)
    if not match:
        return False, "Método no encontrado"
    body = match.group()
    silent = body.count('except Exception:\n            pass')
    return silent == 0, f"{silent} silent excepts en _calcular_audio_adaptativo"

check("FP36-09", "habla.py: 0 silent excepts en _calcular_audio_adaptativo",
      check_no_silent_in_audio)

def check_no_silent_in_interrumpir():
    match = re.search(r'def interrumpir.*?(?=\n    def |\nclass |\Z)', habla_src, re.DOTALL)
    if not match:
        return False, "Método no encontrado"
    body = match.group()
    silent = body.count('except Exception:\n                pass')
    return silent == 0, f"{silent} silent excepts en interrumpir"

check("FP36-10", "habla.py: 0 silent excepts en interrumpir",
      check_no_silent_in_interrumpir)

check("FP36-11", "habla.py: logger.debug en audio adaptativo",
      lambda: (
          'logger.debug' in habla_src,
          "logger.debug presente" if 'logger.debug' in habla_src else "FALTA"
      ))

# ═══════════════════════════════════════════════
# 3. SILENT EXCEPTS → LOGGING (__main__.py)
# ═══════════════════════════════════════════════
main_path = os.path.join(os.path.dirname(__file__), '..', 'golem', '__main__.py')
with open(main_path, encoding='utf-8') as f:
    main_src = f.read()

# __main__.py kill function: the bare "pass" should now have comments
check("FP36-12", "__main__.py: pass con comentario en ancestros",
      lambda: (
          'pass  # psutil puede fallar' in main_src,
          "Comentado" if 'pass  # psutil puede fallar' in main_src else "Sin comentario"
      ))

check("FP36-13", "__main__.py: pass con comentario en kill",
      lambda: (
          'pass  # Proceso ya termin' in main_src,
          "Comentado" if 'pass  # Proceso ya termin' in main_src else "Sin comentario"
      ))

# ═══════════════════════════════════════════════
# 4. SINGLETONS CON LOCK (thread-safe)
# ═══════════════════════════════════════════════
check("FP36-14", "herramientas.py: _gestor_permisos_lock existe",
      lambda: (
          '_gestor_permisos_lock' in herr_src,
          "Lock presente" if '_gestor_permisos_lock' in herr_src else "FALTA"
      ))

check("FP36-15", "herramientas.py: double-checked locking pattern",
      lambda: (
          'with _gestor_permisos_lock:' in herr_src,
          "Pattern presente" if 'with _gestor_permisos_lock:' in herr_src else "FALTA"
      ))

# monitor_sistema.py
monitor_path = os.path.join(os.path.dirname(__file__), '..', 'golem', 'habilidades', 'monitor_sistema.py')
with open(monitor_path, encoding='utf-8') as f:
    monitor_src = f.read()

check("FP36-16", "monitor_sistema.py: _monitor_global_lock existe",
      lambda: (
          '_monitor_global_lock' in monitor_src,
          "Lock presente" if '_monitor_global_lock' in monitor_src else "FALTA"
      ))

# copilot_api.py
copilot_path = os.path.join(os.path.dirname(__file__), '..', 'golem', 'cerebro', 'copilot_api.py')
with open(copilot_path, encoding='utf-8') as f:
    copilot_src = f.read()

check("FP36-17", "copilot_api.py: _instancia_lock existe",
      lambda: (
          '_instancia_lock' in copilot_src,
          "Lock presente" if '_instancia_lock' in copilot_src else "FALTA"
      ))

# sistema.py
sistema_path = os.path.join(os.path.dirname(__file__), '..', 'golem', 'habilidades', 'sistema.py')
with open(sistema_path, encoding='utf-8') as f:
    sistema_src = f.read()

check("FP36-18", "sistema.py: _callback_recordatorio_lock existe",
      lambda: (
          '_callback_recordatorio_lock' in sistema_src,
          "Lock presente" if '_callback_recordatorio_lock' in sistema_src else "FALTA"
      ))

# ═══════════════════════════════════════════════
# 5. BLOQUE 2 ELIMINADO (test_srs_coherencia.py)
# ═══════════════════════════════════════════════
test_srs_path = os.path.join(os.path.dirname(__file__), 'test_srs_coherencia.py')
with open(test_srs_path, encoding='utf-8') as f:
    test_srs_src = f.read()

check("FP36-19", "BLOQUE 2: no contiene 'verificar si ya existen'",
      lambda: (
          'verificar si ya existen' not in test_srs_src,
          "Eliminado" if 'verificar si ya existen' not in test_srs_src else "AÚN EXISTE"
      ))

check("FP36-20", "BLOQUE 2: no contiene desfase('RF-39'",
      lambda: (
          "desfase(\"RF-39\"" not in test_srs_src,
          "Eliminado" if "desfase(\"RF-39\"" not in test_srs_src else "AÚN EXISTE"
      ))

check("FP36-21", "BLOQUE 2: nota de eliminación presente",
      lambda: (
          'Eliminado en FP-036' in test_srs_src,
          "Nota presente" if 'Eliminado en FP-036' in test_srs_src else "FALTA"
      ))

# ═══════════════════════════════════════════════
# 6. OWASP DOCUMENTADO (sistema.py)
# ═══════════════════════════════════════════════
check("FP36-22", "sistema.py: OWASP A03:2021 documentado en shell=True",
      lambda: (
          'OWASP A03:2021' in sistema_src,
          "Referencia presente" if 'OWASP A03:2021' in sistema_src else "FALTA"
      ))

# ═══════════════════════════════════════════════
# 7. IMPORTS NO ROTOS
# ═══════════════════════════════════════════════
check("FP36-23", "herramientas.py importa sin error",
      lambda: (
          __import__('golem.habilidades.herramientas') is not None,
          "Import OK"
      ))

check("FP36-24", "comando_seguro.py importa sin error",
      lambda: (
          __import__('golem.habilidades.comando_seguro') is not None,
          "Import OK"
      ))

# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
print(f"\n{'='*50}\nRESULTADO: {passed} PASS / {total-passed} FAIL / {total} TOTAL")

if __name__ == "__main__":
    sys.exit(0 if passed == total else 1)

