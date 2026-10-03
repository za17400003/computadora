"""
Habilidades de control del sistema — Estilo JARVIS.
Abre apps, controla volumen, lee portapapeles, fecha/hora, clima,
recordatorios, información del sistema.
"""

import datetime
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

from loguru import logger

from computadora.nucleo.gestor_procesos import obtener_gestor_procesos


# ═══════════════════════════════════════════════
# CONTROL DE APLICACIONES
# ═══════════════════════════════════════════════

# Mapa de alias comunes a ejecutables de Windows
_APPS_CONOCIDAS = {
    "navegador": "start msedge",
    "edge": "start msedge",
    "chrome": "start chrome",
    "firefox": "start firefox",
    "explorador": "start explorer",
    "explorador de archivos": "start explorer",
    "archivos": "start explorer",
    "explorer": "start explorer",
    "mis documentos": 'start explorer "%USERPROFILE%\\Documents"',
    "documentos": 'start explorer "%USERPROFILE%\\Documents"',
    "descargas": 'start explorer "%USERPROFILE%\\Downloads"',
    "mis descargas": 'start explorer "%USERPROFILE%\\Downloads"',
    "imágenes": 'start explorer "%USERPROFILE%\\Pictures"',
    "imagenes": 'start explorer "%USERPROFILE%\\Pictures"',
    "mis imágenes": 'start explorer "%USERPROFILE%\\Pictures"',
    "fotos": 'start explorer "%USERPROFILE%\\Pictures"',
    "mis fotos": 'start explorer "%USERPROFILE%\\Pictures"',
    "videos": 'start explorer "%USERPROFILE%\\Videos"',
    "mis videos": 'start explorer "%USERPROFILE%\\Videos"',
    "música": 'start explorer "%USERPROFILE%\\Music"',
    "musica": 'start explorer "%USERPROFILE%\\Music"',
    "escritorio": 'start explorer "%USERPROFILE%\\Desktop"',
    "bloc de notas": "start notepad",
    "notepad": "start notepad",
    "calculadora": "start calc",
    "terminal": "start wt",
    "powershell": "start powershell",
    "cmd": "start cmd",
    "vscode": "start code",
    "code": "start code",
    "android studio": 'start "" "C:\\Program Files\\Android\\Android Studio\\bin\\studio64.exe"',
    "spotify": "start spotify:",
    "paint": "start mspaint",
    "word": "start winword",
    "excel": "start excel",
    "configuracion": "start ms-settings:",
    "configuración": "start ms-settings:",
    "settings": "start ms-settings:",
    "task manager": "start taskmgr",
    "administrador de tareas": "start taskmgr",
}


def abrir_aplicacion(nombre: str) -> str:
    """Abre una aplicación de Windows por nombre (RF-81 hardened)."""
    # RF-81 גבורה: Sanitizar entrada contra inyección de comandos
    nombre_l = re.sub(r"[;&|`$(){}\\[\\]<>]", "", nombre).lower().strip()
    if not nombre_l:
        return "No se especificó una aplicación."

    # Buscar en alias conocidos (exacto)
    comando = _APPS_CONOCIDAS.get(nombre_l)

    # Búsqueda parcial: "explorador de archivos" contiene "explorador"
    if not comando:
        for alias, cmd in _APPS_CONOCIDAS.items():
            if alias in nombre_l or nombre_l in alias:
                comando = cmd
                logger.debug(f"Alias parcial: '{nombre_l}' → '{alias}'")
                break

    if not comando:
        # RF-81: Para apps desconocidas, usar shell=False con os.startfile
        # en lugar de shell=True con 'start' para prevenir inyección
        try:
            os.startfile(nombre_l)
            logger.info(f"Aplicación abierta via startfile: {nombre}")
            return f"Abriendo {nombre}"
        except OSError as e:
            return f"No encontré la aplicación '{nombre}': {e}"

    # Para aliases conocidos: extraer ejecutable y usar shell=False si posible
    if comando.startswith('start ""'):
        # Ruta explícita — usar shell=False
        exe_path = comando.split('""', 1)[1].strip().strip('"')
        try:
            gestor = obtener_gestor_procesos()
            gestor.lanzar(
                [exe_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Aplicación abierta (shell=False): {nombre}")
            return f"Abriendo {nombre}"
        except Exception as e:
            logger.warning(f"shell=False falló para {nombre}, fallback: {e}")

    # C3/OWASP A03:2021: Eliminar shell=True — parsear "start xxx" y usar
    # os.startfile (URIs/rutas) o shutil.which + Popen (ejecutables).
    if comando.startswith("start "):
        target = comando[len("start "):].strip().strip('"')
        # Expandir variables de entorno (%USERPROFILE%, etc.)
        target = os.path.expandvars(target)
        # Subcaso: "start explorer path" → abrir la ruta con explorer
        if target.startswith("explorer "):
            ruta = target[len("explorer "):].strip().strip('"')
            ruta = os.path.expandvars(ruta)
            try:
                os.startfile(ruta)
                logger.info(f"Ruta abierta via startfile: {nombre}")
                return f"Abriendo {nombre}"
            except OSError as e:
                return f"Error abriendo {nombre}: {e}"
        # URIs (ms-settings:, spotify:, etc.) → os.startfile
        if ":" in target and not target[1:3] == ":\\":
            try:
                os.startfile(target)
                logger.info(f"URI abierta via startfile: {nombre}")
                return f"Abriendo {nombre}"
            except OSError as e:
                return f"Error abriendo {nombre}: {e}"
        # Ejecutable conocido → shutil.which + Popen(shell=False)
        import shutil
        exe = shutil.which(target)
        if exe:
            try:
                gestor = obtener_gestor_procesos()
                gestor.lanzar(
                    [exe],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info(f"Aplicación abierta (which→shell=False): {nombre}")
                return f"Abriendo {nombre}"
            except Exception as e:
                logger.warning(f"Popen falló para {nombre}: {e}")
        # Último recurso: os.startfile (maneja "msedge", "chrome", etc.)
        try:
            os.startfile(target)
            logger.info(f"Aplicación abierta via startfile (fallback): {nombre}")
            return f"Abriendo {nombre}"
        except OSError as e:
            return f"Error abriendo {nombre}: {e}"

    return f"No encontré la aplicación '{nombre}'"


def cerrar_aplicacion(nombre: str) -> str:
    """Cierra una aplicación por nombre de proceso."""
    nombre_l = nombre.lower().strip()

    # Mapear nombres comunes a nombres de proceso
    procesos = {
        "chrome": "chrome.exe", "edge": "msedge.exe", "firefox": "firefox.exe",
        "navegador": "msedge.exe", "notepad": "notepad.exe", "bloc de notas": "notepad.exe",
        "spotify": "Spotify.exe", "vscode": "Code.exe", "code": "Code.exe",
        "word": "WINWORD.EXE", "excel": "EXCEL.EXE",
        # RF-303: UWP apps (FP-081)
        "microsoft.photos": "Microsoft.Photos.exe", "photos": "Microsoft.Photos.exe",
        "fotos": "Microsoft.Photos.exe", "visor de fotos": "Microsoft.Photos.exe",
    }
    proceso = procesos.get(nombre_l, f"{nombre_l}.exe")

    try:
        result = subprocess.run(
            ["taskkill", "/IM", proceso, "/F"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        if result.returncode == 0:
            logger.info(f"Aplicación cerrada: {nombre} ({proceso})")
            return f"{nombre} cerrado"
        else:
            return f"No pude cerrar {nombre}: {result.stderr.strip()}"
    except Exception as e:
        return f"Error cerrando {nombre}: {e}"


# ═══════════════════════════════════════════════
# CONTROL DE VOLUMEN
# ═══════════════════════════════════════════════

def controlar_volumen(accion: str) -> str:
    """Controla el volumen del sistema. Acciones: subir, bajar, mute, unmute, max, min"""
    accion_l = accion.lower().strip()

    # Usar nircmd si existe, sino PowerShell
    ps_script = ""
    if accion_l in ("subir", "up", "más", "mas"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
for ($i=0; $i -lt 5; $i++) { $wshell.SendKeys([char]175) }
"""
    elif accion_l in ("bajar", "down", "menos"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
for ($i=0; $i -lt 5; $i++) { $wshell.SendKeys([char]174) }
"""
    elif accion_l in ("mute", "silencio", "silenciar"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
$wshell.SendKeys([char]173)
"""
    elif accion_l in ("unmute", "desilenciar", "activar"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
$wshell.SendKeys([char]173)
"""
    elif accion_l in ("max", "máximo", "maximo"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
for ($i=0; $i -lt 50; $i++) { $wshell.SendKeys([char]175) }
"""
    elif accion_l in ("min", "mínimo", "minimo"):
        ps_script = """
$wshell = New-Object -ComObject WScript.Shell
for ($i=0; $i -lt 50; $i++) { $wshell.SendKeys([char]174) }
"""
    else:
        return f"Acción de volumen no reconocida: {accion}. Usa: subir, bajar, mute, unmute, max, min"

    try:
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=10,
        )
        logger.info(f"Volumen: {accion}")
        return f"Volumen: {accion}"
    except Exception as e:
        return f"Error controlando volumen: {e}"


# ═══════════════════════════════════════════════
# PORTAPAPELES
# ═══════════════════════════════════════════════

def leer_portapapeles() -> str:
    """Lee el contenido actual del portapapeles."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5,
            encoding='utf-8', errors='replace',
        )
        contenido = (result.stdout or "").strip()
        if contenido:
            logger.info(f"Portapapeles leído ({len(contenido)} chars)")
            return f"Contenido del portapapeles:\n{contenido[:2000]}"
        return "El portapapeles está vacío"
    except Exception as e:
        return f"Error leyendo portapapeles: {e}"


def escribir_portapapeles(texto: str) -> str:
    """Escribe texto al portapapeles."""
    try:
        subprocess.run(
            ["powershell", "-Command", "Set-Clipboard -Value $input"],
            input=texto, capture_output=True, text=True, timeout=5,
            encoding='utf-8', errors='replace',
        )
        logger.info(f"Portapapeles escrito ({len(texto)} chars)")
        return "Texto copiado al portapapeles"
    except Exception as e:
        return f"Error escribiendo portapapeles: {e}"


# ═══════════════════════════════════════════════
# FECHA, HORA, INFORMACIÓN
# ═══════════════════════════════════════════════

def obtener_fecha_hora() -> str:
    """Retorna fecha, hora y día de la semana."""
    ahora = datetime.datetime.now()
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    dia_semana = dias[ahora.weekday()]
    mes = meses[ahora.month - 1]

    return (
        f"Hoy es {dia_semana} {ahora.day} de {mes} de {ahora.year}. "
        f"Son las {ahora.hour}:{ahora.minute:02d}."
    )


def obtener_info_sistema() -> str:
    """Información básica del sistema: batería, RAM, disco, CPU."""
    info_partes = []

    # Uptime
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | "
             "Select-Object -ExpandProperty TotalHours"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        horas = float(result.stdout.strip())
        info_partes.append(f"Encendida hace {horas:.0f} horas")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    # RAM
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "$os = Get-CimInstance Win32_OperatingSystem; "
             "$usado = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1); "
             "$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1); "
             "\"RAM: ${usado}GB / ${total}GB\""],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        info_partes.append(result.stdout.strip())
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    # Disco
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "$d = Get-PSDrive C; "
             "$libre = [math]::Round($d.Free/1GB, 1); "
             "$total = [math]::Round(($d.Used + $d.Free)/1GB, 1); "
             "\"Disco C: ${libre}GB libres de ${total}GB\""],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        info_partes.append(result.stdout.strip())
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    # Batería
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "$b = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue; "
             "if ($b) { \"Batería: $($b.EstimatedChargeRemaining)%\" } "
             "else { \"Sin batería (escritorio)\" }"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        info_partes.append(result.stdout.strip())
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    if info_partes:
        return ". ".join(info_partes)
    return "No pude obtener info del sistema"


# ═══════════════════════════════════════════════
# RECORDATORIOS (en memoria, volátiles)
# ═══════════════════════════════════════════════

_RECORDATORIOS_ARCHIVO = Path(__file__).resolve().parent.parent.parent / "datos" / "recordatorios.json"
_recordatorios_activos: list[threading.Timer] = []


def _cargar_recordatorios() -> list[dict]:
    if _RECORDATORIOS_ARCHIVO.exists():
        try:
            return json.loads(_RECORDATORIOS_ARCHIVO.read_text(encoding="utf-8"))
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return []
    return []


def _guardar_recordatorios(recordatorios: list[dict]):
    _RECORDATORIOS_ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(_RECORDATORIOS_ARCHIVO, recordatorios)


# Callback global para cuando suene el recordatorio — se inyecta desde ventana_principal
# Thread-safe FP-036
_callback_recordatorio = None
_callback_recordatorio_lock = __import__('threading').Lock()


def set_callback_recordatorio(fn):
    global _callback_recordatorio
    with _callback_recordatorio_lock:
        _callback_recordatorio = fn


def crear_recordatorio(mensaje: str, minutos: str) -> str:
    """Crea un recordatorio que suena en N minutos."""
    try:
        mins = float(minutos)
    except (ValueError, TypeError):
        return f"Error: '{minutos}' no es un número válido de minutos"

    if mins <= 0 or mins > 1440:
        return "Error: Los minutos deben estar entre 1 y 1440 (24 horas)"

    ahora = datetime.datetime.now()
    cuando = ahora + datetime.timedelta(minutes=mins)

    # Guardar en archivo
    recordatorios = _cargar_recordatorios()
    recordatorio = {
        "mensaje": mensaje,
        "cuando": cuando.isoformat(),
        "creado": ahora.isoformat(),
    }
    recordatorios.append(recordatorio)
    _guardar_recordatorios(recordatorios)

    # Programar timer
    def _sonar():
        logger.info(f"¡Recordatorio! {mensaje}")
        if _callback_recordatorio:
            _callback_recordatorio(f"Recordatorio: {mensaje}")
        # Limpiar del archivo
        recs = _cargar_recordatorios()
        recs = [r for r in recs if r.get("cuando") != cuando.isoformat()]
        _guardar_recordatorios(recs)

    timer = threading.Timer(mins * 60, _sonar)
    timer.daemon = True
    timer.start()
    _recordatorios_activos.append(timer)

    hora_str = cuando.strftime("%H:%M")
    logger.info(f"Recordatorio creado: '{mensaje}' a las {hora_str} ({mins} min)")
    return f"Recordatorio programado: '{mensaje}' a las {hora_str} (en {mins:.0f} minutos)"


def listar_recordatorios() -> str:
    """Lista los recordatorios pendientes."""
    recordatorios = _cargar_recordatorios()
    ahora = datetime.datetime.now()

    # Filtrar los que ya pasaron
    pendientes = []
    for r in recordatorios:
        cuando = datetime.datetime.fromisoformat(r["cuando"])
        if cuando > ahora:
            diff = (cuando - ahora).total_seconds() / 60
            pendientes.append(f"- '{r['mensaje']}' en {diff:.0f} minutos ({cuando.strftime('%H:%M')})")

    if pendientes:
        return "Recordatorios pendientes:\n" + "\n".join(pendientes)
    return "No hay recordatorios pendientes"


def reprogramar_recordatorios_pendientes():
    """Re-programa timers para recordatorios que aún no han pasado. Llamar al iniciar Computadora."""
    recordatorios = _cargar_recordatorios()
    ahora = datetime.datetime.now()
    reprogramados = 0
    expirados = []

    for r in recordatorios:
        cuando = datetime.datetime.fromisoformat(r["cuando"])
        if cuando > ahora:
            diff_seg = (cuando - ahora).total_seconds()
            mensaje = r["mensaje"]

            def _sonar(msg=mensaje, iso=r["cuando"]):
                logger.info(f"¡Recordatorio! {msg}")
                if _callback_recordatorio:
                    _callback_recordatorio(f"Recordatorio: {msg}")
                recs = _cargar_recordatorios()
                recs = [rc for rc in recs if rc.get("cuando") != iso]
                _guardar_recordatorios(recs)

            timer = threading.Timer(diff_seg, _sonar)
            timer.daemon = True
            timer.start()
            _recordatorios_activos.append(timer)
            reprogramados += 1
        else:
            expirados.append(r)

    # Limpiar recordatorios expirados
    if expirados:
        recordatorios = [r for r in recordatorios if r not in expirados]
        _guardar_recordatorios(recordatorios)

    if reprogramados:
        logger.info(f"Recordatorios reprogramados al inicio: {reprogramados}")
    if expirados:
        logger.info(f"Recordatorios expirados limpiados: {len(expirados)}")


# ═══════════════════════════════════════════════
# CAPTURAS DE PANTALLA
# ═══════════════════════════════════════════════

def tomar_captura_pantalla(nombre: str = "") -> str:
    """Toma una captura de pantalla y la guarda en datos/capturas/."""
    try:
        import pyautogui

        carpeta = Path(__file__).resolve().parent.parent.parent / "datos" / "capturas"
        carpeta.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if nombre:
            # Sanitizar nombre
            nombre_safe = "".join(c for c in nombre if c.isalnum() or c in " _-").strip()[:50]
            archivo = carpeta / f"{nombre_safe}_{timestamp}.png"
        else:
            archivo = carpeta / f"captura_{timestamp}.png"

        img = pyautogui.screenshot()
        img.save(str(archivo))
        logger.info(f"Captura guardada: {archivo}")
        return f"Captura de pantalla guardada en: {archivo.name}"
    except ImportError:
        return "Error: pyautogui no está instalado. Ejecuta: pip install pyautogui"
    except Exception as e:
        return f"Error tomando captura: {e}"


# ═══════════════════════════════════════════════
# BÚSQUEDA DE ARCHIVOS
# ═══════════════════════════════════════════════

def buscar_archivos(nombre: str, carpeta: str = "") -> str:
    """Busca archivos por nombre en una carpeta (recursivo). Por defecto busca en el home del usuario."""
    if not nombre or len(nombre) < 2:
        return "Error: Proporciona un nombre de archivo de al menos 2 caracteres"

    if carpeta:
        raiz = Path(carpeta)
    else:
        raiz = Path.home()

    if not raiz.exists():
        return f"Error: La carpeta '{carpeta}' no existe"

    nombre_l = nombre.lower()
    resultados = []
    max_resultados = 20

    try:
        for archivo in raiz.rglob("*"):
            if len(resultados) >= max_resultados:
                break
            try:
                if nombre_l in archivo.name.lower():
                    resultados.append(str(archivo))
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        return f"Error: Sin permisos para buscar en '{raiz}'"

    if resultados:
        lista = "\n".join(f"- {r}" for r in resultados)
        extra = f"\n(Mostrando máximo {max_resultados} resultados)" if len(resultados) >= max_resultados else ""
        return f"Archivos encontrados con '{nombre}':\n{lista}{extra}"
    return f"No se encontraron archivos con '{nombre}' en {raiz}"


def diagnostico_sistema() -> str:
    """Retorna un diagnóstico rápido del estado del sistema y servicios.

    Comprueba Ollama, dispositivos de audio, y si existe un perfil de voz.
    """
    partes = []
    partes.append("Computadora: encendida")

    # Ollama
    try:
        import requests

        r = requests.get("http://localhost:1234/v1/models", timeout=2)
        if r.status_code == 200:
            partes.append("Ollama: disponible")
        else:
            partes.append(f"Ollama: respondió con status {r.status_code}")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
        partes.append("Ollama: no disponible (fallback activo)")

    # Audio
    try:
        import sounddevice as sd

        dispositivos = sd.query_devices()
        entradas = [d for d in dispositivos if d.get("max_input_channels", 0) > 0]
        if entradas:
            partes.append(f"Audio: {len(entradas)} dispositivo(s) de entrada detectado(s). Ejemplo: {entradas[0]['name']}")
        else:
            partes.append("Audio: no se detectaron dispositivos de entrada")
    except Exception as e:
        partes.append(f"Audio: error detectando dispositivo ({e})")

    # Perfil de voz
    try:
        owner_file = Path(__file__).resolve().parent.parent.parent / "datos" / "owner_profile.json"
        if owner_file.exists():
            op = json.loads(owner_file.read_text(encoding="utf-8"))
            cnt = op.get("count", 0)
            partes.append(f"Perfil de voz: registrado ({cnt} muestras)")
        else:
            partes.append("Perfil de voz: no registrado")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
        partes.append("Perfil de voz: error leyendo estado")

    # Herramientas
    try:
        from computadora.habilidades.herramientas import obtener_descripcion_herramientas

        partes.append("Herramientas: OK (ver descripción)")
    except Exception as e:
        partes.append(f"Herramientas: error ({e})")

    return "\n".join(partes)


