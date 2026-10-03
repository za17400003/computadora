"""
מגן דוד (Maguén David) — Escudo de seguridad para ejecución de comandos.
FP-034: Reemplaza shell=True + blocklist por shell=False + allowlist.
OWASP OS Command Injection Prevention.
"""

import os
import re
import shlex
import subprocess
from pathlib import Path

from loguru import logger

# Timeout para comandos (segundos)
_TIMEOUT = 15

# ─── Metacaracteres prohibidos en argumentos ───
_ARG_BLOCKLIST = re.compile(r'[;&|`$(){}<>\[\]!^]')

# ─── Allowlist de comandos del proyecto (ejecutar_comando) ───
# max_args: máximo de argumentos permitidos
# shell: True solo si es absolutamente necesario (ej: 'start')
COMANDOS_PROYECTO = {
    "dir": {"max_args": 5},
    "type": {"max_args": 2},
    "echo": {"max_args": 10},
    "find": {"max_args": 5},
    "findstr": {"max_args": 5},
    "tree": {"max_args": 3},
    "where": {"max_args": 3},
    "more": {"max_args": 2},
    "sort": {"max_args": 3},
    "fc": {"max_args": 4},
    "comp": {"max_args": 4},
}

# ─── Allowlist de comandos del sistema (ejecutar_comando_sistema) ───
COMANDOS_SISTEMA = {
    "systeminfo": {"max_args": 0},
    "hostname": {"max_args": 0},
    "whoami": {"max_args": 1},
    "ipconfig": {"max_args": 1},
    "tasklist": {"max_args": 4},
    "ver": {"max_args": 0},
    "netstat": {"max_args": 2},
    "nslookup": {"max_args": 2},
    "route": {"max_args": 3},
    "set": {"max_args": 1},
    "gpresult": {"max_args": 2},
    "ping": {"max_args": 4},
}

# PowerShell cmdlets solo-lectura permitidos
_PS_CMDLETS = frozenset({
    "get-process", "get-service", "get-netadapter", "get-volume",
    "get-computerinfo", "get-disk", "get-netipconfiguration",
    "get-netfirewallrule", "get-hotfix",
})

# Regex de comandos peligrosos (barrera final — nunca pasar)
_COMANDOS_PELIGROSOS = re.compile(
    r"(?:^|\s)(?:"
    r"rm\s|del\s|rmdir|format\s|shutdown|restart|logoff|"
    r"reg\s+(?:add|delete)|net\s+(?:user|localgroup)|"
    r"curl\s.*\|.*sh|wget\s.*\|.*sh|"
    r"mkfs|dd\s+if=|"
    r"certutil\s.*-urlcache|bitsadmin.*transfer|"
    r"wscript|cscript|mshta|"
    r"schtasks\s*/create|sc\s+(?:create|config|delete)|"
    r"bcdedit|bootrec|diskpart"
    r")",
    re.IGNORECASE,
)


def _validar_args(args: list[str]) -> tuple[bool, str]:
    """Rechaza argumentos con metacaracteres de shell."""
    for arg in args:
        if _ARG_BLOCKLIST.search(arg):
            return False, f"Argumento contiene caracteres no permitidos: '{arg}'"
    return True, ""


def ejecutar_comando_seguro(comando_raw: str, cwd: Path) -> str:
    """
    Ejecuta un comando del proyecto de forma segura.
    - Parsea en argv (sin interpretación de shell)
    - Valida contra allowlist
    - Rechaza metacaracteres en argumentos
    - shell=False siempre
    """
    comando_raw = comando_raw.strip()
    if not comando_raw:
        return "Error: Comando vacío."

    # Barrera de seguridad final
    if _COMANDOS_PELIGROSOS.search(comando_raw):
        logger.warning("Comando peligroso bloqueado: %s", comando_raw)
        return "Error: Comando bloqueado por seguridad."

    try:
        parts = shlex.split(comando_raw, posix=False)
    except ValueError as e:
        return f"Error: Comando malformado — {e}"

    if not parts:
        return "Error: Comando vacío."

    cmd_name = parts[0].lower()
    args = parts[1:]

    spec = COMANDOS_PROYECTO.get(cmd_name)
    if spec is None:
        return (
            f"Error: '{cmd_name}' no está en la lista de comandos permitidos. "
            f"Comandos disponibles: {', '.join(sorted(COMANDOS_PROYECTO))}"
        )

    if len(args) > spec["max_args"]:
        return f"Error: Demasiados argumentos para '{cmd_name}' (máx {spec['max_args']})."

    ok, msg = _validar_args(args)
    if not ok:
        return msg

    try:
        logger.info("Ejecutando (seguro): %s", parts)
        resultado = subprocess.run(
            parts,
            shell=False,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=_TIMEOUT,
            cwd=str(cwd),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        salida = ""
        if resultado.stdout:
            salida += resultado.stdout
        if resultado.stderr:
            salida += ("\n--- stderr ---\n" + resultado.stderr) if salida else resultado.stderr

        if not salida.strip():
            salida = f"(código de salida: {resultado.returncode})"

        # Truncar salida larga
        if len(salida) > 4000:
            salida = salida[:4000] + "\n... (truncado)"

        return salida

    except subprocess.TimeoutExpired:
        return f"Error: Timeout ({_TIMEOUT}s)."
    except FileNotFoundError:
        return f"Error: Comando '{cmd_name}' no encontrado en el sistema."
    except Exception as e:
        return f"Error ejecutando comando: {e}"


def ejecutar_comando_sistema_seguro(comando_raw: str) -> str:
    """
    Ejecuta un comando del SO (fuera del proyecto) de forma segura.
    Solo comandos de la allowlist (info/solo-lectura).
    PowerShell cmdlets read-only via subprocess con shell=False.
    """
    comando_raw = comando_raw.strip()
    if not comando_raw:
        return "Error: Comando vacío."

    if _COMANDOS_PELIGROSOS.search(comando_raw):
        logger.warning("Comando sistema peligroso bloqueado: %s", comando_raw)
        return "Error: Comando bloqueado por seguridad."

    cmd_lower = comando_raw.lower()

    # PowerShell cmdlets read-only
    ps_cmd = cmd_lower.split()[0] if cmd_lower.split() else ""
    if ps_cmd in _PS_CMDLETS:
        try:
            logger.info("Ejecutando PS cmdlet: %s", comando_raw)
            resultado = subprocess.run(
                ["powershell", "-NoProfile", "-Command", comando_raw],
                shell=False,
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                timeout=_TIMEOUT,
            )
            salida = resultado.stdout or f"(código: {resultado.returncode})"
            if resultado.stderr:
                salida += "\n--- stderr ---\n" + resultado.stderr
            if len(salida) > 4000:
                salida = salida[:4000] + "\n... (truncado)"
            return salida
        except subprocess.TimeoutExpired:
            return f"Error: Timeout ({_TIMEOUT}s)."
        except Exception as e:
            return f"Error ejecutando cmdlet: {e}"

    # Comandos nativos del SO
    try:
        parts = shlex.split(comando_raw, posix=False)
    except ValueError as e:
        return f"Error: Comando malformado — {e}"

    if not parts:
        return "Error: Comando vacío."

    cmd_name = parts[0].lower()
    args = parts[1:]

    spec = COMANDOS_SISTEMA.get(cmd_name)
    if spec is None:
        return (
            f"Error: '{cmd_name}' no está en mi lista de comandos de sistema permitidos. "
            f"Solo puedo ejecutar comandos de consulta del SO."
        )

    if len(args) > spec["max_args"]:
        return f"Error: Demasiados argumentos para '{cmd_name}'."

    ok, msg = _validar_args(args)
    if not ok:
        return msg

    try:
        logger.info("Ejecutando sistema (seguro): %s", parts)
        resultado = subprocess.run(
            parts,
            shell=False,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=_TIMEOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

        salida = ""
        if resultado.stdout:
            salida += resultado.stdout
        if resultado.stderr:
            salida += ("\n--- stderr ---\n" + resultado.stderr) if salida else resultado.stderr

        if not salida.strip():
            salida = f"(código de salida: {resultado.returncode})"

        if len(salida) > 4000:
            salida = salida[:4000] + "\n... (truncado)"

        return salida

    except subprocess.TimeoutExpired:
        return f"Error: Timeout ({_TIMEOUT}s)."
    except FileNotFoundError:
        return f"Error: Comando '{cmd_name}' no encontrado."
    except Exception as e:
        return f"Error ejecutando comando de sistema: {e}"


