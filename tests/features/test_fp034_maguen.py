"""
Tests FP-034: מגן דוד (Maguén David) — Escudo de seguridad para comandos.
RF-97: Allowlist + shell=False reemplaza shell=True + blocklist.
"""
import sys, os
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


# ─── Import tests ───

check("FP34-01", "Import comando_seguro", lambda: (
    __import__('computadora.habilidades.comando_seguro') is not None,
    "módulo importable"
))

check("FP34-02", "Import ejecutar_comando_seguro", lambda: (
    callable(getattr(__import__('computadora.habilidades.comando_seguro',
        fromlist=['ejecutar_comando_seguro']), 'ejecutar_comando_seguro')),
    "función callable"
))

check("FP34-03", "Import ejecutar_comando_sistema_seguro", lambda: (
    callable(getattr(__import__('computadora.habilidades.comando_seguro',
        fromlist=['ejecutar_comando_sistema_seguro']), 'ejecutar_comando_sistema_seguro')),
    "función callable"
))

# ─── Allowlist tests ───

from computadora.habilidades.comando_seguro import (
    COMANDOS_PROYECTO, COMANDOS_SISTEMA, _PS_CMDLETS,
    _COMANDOS_PELIGROSOS, _ARG_BLOCKLIST, _validar_args,
    ejecutar_comando_seguro, ejecutar_comando_sistema_seguro,
)
from pathlib import Path

CWD = Path(__file__).resolve().parent.parent

check("FP34-04", "COMANDOS_PROYECTO tiene >= 10 entradas", lambda: (
    len(COMANDOS_PROYECTO) >= 10,
    f"{len(COMANDOS_PROYECTO)} comandos en allowlist"
))

check("FP34-05", "COMANDOS_SISTEMA tiene >= 10 entradas", lambda: (
    len(COMANDOS_SISTEMA) >= 10,
    f"{len(COMANDOS_SISTEMA)} comandos en allowlist"
))

check("FP34-06", "_PS_CMDLETS es frozenset con cmdlets read-only", lambda: (
    isinstance(_PS_CMDLETS, frozenset) and "get-process" in _PS_CMDLETS,
    f"{len(_PS_CMDLETS)} cmdlets"
))

# ─── Blocklist / metachar rejection ───

check("FP34-07", "_ARG_BLOCKLIST rechaza ;", lambda: (
    _ARG_BLOCKLIST.search(";arg") is not None,
    "semicolon blocked"
))

check("FP34-08", "_ARG_BLOCKLIST rechaza |", lambda: (
    _ARG_BLOCKLIST.search("arg|otro") is not None,
    "pipe blocked"
))

check("FP34-09", "_ARG_BLOCKLIST rechaza $", lambda: (
    _ARG_BLOCKLIST.search("$VAR") is not None,
    "dollar blocked"
))

check("FP34-10", "_ARG_BLOCKLIST rechaza backtick", lambda: (
    _ARG_BLOCKLIST.search("`cmd`") is not None,
    "backtick blocked"
))

check("FP34-11", "_validar_args acepta args limpios", lambda: (
    _validar_args(["archivo.txt", "C:\\ruta"])[0] is True,
    "args válidos OK"
))

check("FP34-12", "_validar_args rechaza metacaracteres", lambda: (
    _validar_args(["archivo;rm -rf"])[0] is False,
    "metachar rechazado"
))

# ─── Comandos peligrosos ───

check("FP34-13", "Regex bloquea 'rm -rf /'", lambda: (
    _COMANDOS_PELIGROSOS.search("rm -rf /") is not None,
    "bloqueado"
))

check("FP34-14", "Regex bloquea 'shutdown /s'", lambda: (
    _COMANDOS_PELIGROSOS.search("shutdown /s") is not None,
    "bloqueado"
))

check("FP34-15", "Regex bloquea 'format C:'", lambda: (
    _COMANDOS_PELIGROSOS.search("format C:") is not None,
    "bloqueado"
))

check("FP34-16", "Regex bloquea 'certutil -urlcache'", lambda: (
    _COMANDOS_PELIGROSOS.search("certutil -urlcache") is not None,
    "bloqueado"
))

# ─── Functional: ejecutar_comando_seguro ───

check("FP34-17", "Comando permitido 'hostname' rechazado en proyecto (no está en PROYECTO)", lambda: (
    "no está en la lista" in ejecutar_comando_seguro("hostname", CWD),
    "hostname no es comando de proyecto"
))

check("FP34-18", "Comando vacío retorna error", lambda: (
    "Error" in ejecutar_comando_seguro("", CWD),
    "vacío rechazado"
))

def _test_injection():
    r = ejecutar_comando_seguro("echo test;whoami", CWD)
    blocked = "no permitidos" in r or "bloqueado" in r or "Error" in r
    return blocked, f"resultado: {r[:60]}"

check("FP34-19", "Comando con metachar en args rechazado", _test_injection)

check("FP34-20", "Comando peligroso bloqueado", lambda: (
    "bloqueado por seguridad" in ejecutar_comando_seguro("rm -rf /", CWD),
    "peligroso rechazado"
))

check("FP34-21", "Demasiados args rechazado", lambda: (
    "Demasiados argumentos" in ejecutar_comando_seguro("type a b c d e", CWD),
    f"max_args={COMANDOS_PROYECTO['type']['max_args']} enforced"
))

# ─── Functional: ejecutar_comando_sistema_seguro ───

def _test_hostname():
    r = ejecutar_comando_sistema_seguro("hostname")
    return "Error" not in r and len(r.strip()) > 0, f"retornó: {r.strip()[:50]}"

check("FP34-22", "hostname funciona via sistema seguro", _test_hostname)

def _test_sistema_no_permitido():
    r = ejecutar_comando_sistema_seguro("dir C:\\")
    return "no está en mi lista" in r, "dir rechazado como comando sistema"

check("FP34-23", "Comando no-allowlisted rechazado en sistema", _test_sistema_no_permitido)

def _test_sistema_peligroso():
    r = ejecutar_comando_sistema_seguro("shutdown /s /t 0")
    return "bloqueado por seguridad" in r, "shutdown bloqueado"

check("FP34-24", "Comando peligroso bloqueado en sistema", _test_sistema_peligroso)

# ─── Integración: herramientas.py delega a comando_seguro ───

check("FP34-25", "herramientas.ejecutar_comando delega a comando_seguro", lambda: (
    "ejecutar_comando_seguro" in
        open(os.path.join(CWD, "computadora", "habilidades", "herramientas.py"),
             encoding="utf-8").read(),
    "import presente en herramientas.py"
))

check("FP34-26", "herramientas.ejecutar_comando_sistema delega a comando_seguro", lambda: (
    "ejecutar_comando_sistema_seguro" in
        open(os.path.join(CWD, "computadora", "habilidades", "herramientas.py"),
             encoding="utf-8").read(),
    "import presente en herramientas.py"
))

# ─── shell=False verification ───

def _test_no_shell_true():
    with open(os.path.join(CWD, "computadora", "habilidades", "comando_seguro.py"),
              encoding="utf-8") as f:
        src = f.read()
    # Buscar shell=True como keyword argument real (no en comentarios ni docstrings)
    lines = [l for l in src.splitlines()
             if "shell=True" in l and not l.strip().startswith("#")
             and not l.strip().startswith('"""') and not l.strip().startswith("FP-")]
    return len(lines) == 0, f"{len(lines)} líneas con shell=True" if lines else "sin shell=True en código"

check("FP34-27", "comando_seguro.py NO usa shell=True", _test_no_shell_true)

# ─── Summary ───
total = len(resultados)
passed = sum(1 for r in resultados if r[2])
print(f"\n{'='*50}\nRESULTADO FP-034: {passed} PASS / {total-passed} FAIL / {total} TOTAL")

if __name__ == "__main__":
    sys.exit(0 if passed == total else 1)

