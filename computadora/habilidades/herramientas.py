"""
יסוד (Yesod) — Fundamento.
Sistema de Herramientas dCOMPUTADORA — Inspirado en OpenClaw.
Filtro final antes de la manifestación: cada acción pasa por los
Sellos de Yesod antes de llegar a Maljut (el mundo visible).

Seguridad:
- Solo opera dentro de RAIZ_PROYECTO (Círculo de Salomón).
- Comandos peligrosos bloqueados (Sellos de Yesod).
- Lectura de archivos limitada en tamaño.
- Errores se registran en aprendizaje.py (Sigilo de Contención).
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger

# ═══════════════════════════════════════════════
# CONFIGURACIÓN DE SEGURIDAD
# ═══════════════════════════════════════════════

# Raíz del proyecto — COMPUTADORA SOLO puede operar aquí
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

# Tamaño máximo de lectura (caracteres)
MAX_LECTURA = 15_000

# Timeout para comandos (segundos)
TIMEOUT_COMANDO = 30

# גבורה Gevurá — Gestor de permisos singleton (lazy init, thread-safe FP-036)
import threading as _threading

_gestor_permisos = None
_gestor_permisos_lock = _threading.Lock()


def _obtener_gestor_permisos():
    """Lazy init del GestorPermisos para evitar imports circulares."""
    global _gestor_permisos
    if _gestor_permisos is None:
        with _gestor_permisos_lock:
            if _gestor_permisos is None:
                from computadora.nucleo.permisos import GestorPermisos
                _gestor_permisos = GestorPermisos()
    return _gestor_permisos


# Extensiones de archivos que NO se deben tocar
EXTENSIONES_PROTEGIDAS = {".exe", ".dll", ".sys", ".bat", ".cmd", ".ps1", ".reg"}


def _ruta_segura(ruta_str: str) -> Path:
    """
    Resuelve una ruta y verifica que esté dentro de RAIZ_PROYECTO.
    Lanza ValueError si intenta escapar.
    """
    # Sanitizar rutas Linux que el LLM pequeño puede generar
    ruta_str = ruta_str.strip()
    if ruta_str.startswith(("/home/", "/usr/", "/tmp/", "/root/", "/var/", "/etc/")):
        # El LLM generó una ruta Linux — convertir a raíz del proyecto
        logger.warning(f"Ruta Linux detectada '{ruta_str}', usando '.' en su lugar")
        ruta_str = "."

    # Si es ruta relativa, resolver desde RAIZ_PROYECTO
    ruta = Path(ruta_str)
    if not ruta.is_absolute():
        ruta = RAIZ_PROYECTO / ruta

    ruta = ruta.resolve()

    if not str(ruta).startswith(str(RAIZ_PROYECTO)):
        raise ValueError(
            f"Acceso denegado: '{ruta}' está fuera del proyecto. "
            f"Solo puedo operar dentro de '{RAIZ_PROYECTO}'"
        )

    return ruta


# ═══════════════════════════════════════════════
# HERRAMIENTAS DISPONIBLES
# ═══════════════════════════════════════════════


def leer_archivo(ruta: str, linea_inicio: int = 0, linea_fin: int = 0) -> str:
    """
    Lee el contenido de un archivo.
    Si linea_inicio y linea_fin se especifican, lee solo ese rango (1-indexed).
    """
    ruta_p = _ruta_segura(ruta)

    if not ruta_p.exists():
        return f"Error: El archivo '{ruta}' no existe."
    if not ruta_p.is_file():
        return f"Error: '{ruta}' no es un archivo."

    try:
        contenido = ruta_p.read_text(encoding="utf-8", errors="replace")

        if linea_inicio > 0 and linea_fin > 0:
            lineas = contenido.splitlines()
            inicio = max(0, linea_inicio - 1)
            fin = min(len(lineas), linea_fin)
            seleccion = lineas[inicio:fin]
            texto = "\n".join(f"{i+inicio+1:4d} | {l}" for i, l in enumerate(seleccion))
        else:
            lineas = contenido.splitlines()
            texto = "\n".join(f"{i+1:4d} | {l}" for i, l in enumerate(lineas))

        if len(texto) > MAX_LECTURA:
            texto = texto[:MAX_LECTURA] + f"\n... (truncado, {len(contenido)} caracteres total)"

        logger.info(f"Leído: {ruta} ({len(contenido)} chars)")
        return texto

    except Exception as e:
        return f"Error leyendo '{ruta}': {e}"


def escribir_archivo(ruta: str, contenido: str) -> str:
    """
    Escribe contenido a un archivo. Crea directorios intermedios si faltan.
    """
    ruta_p = _ruta_segura(ruta)

    if ruta_p.suffix in EXTENSIONES_PROTEGIDAS:
        return f"Error: No puedo escribir archivos con extensión '{ruta_p.suffix}'."

    try:
        ruta_p.parent.mkdir(parents=True, exist_ok=True)
        existia = ruta_p.exists()
        ruta_p.write_text(contenido, encoding="utf-8")
        accion = "Actualizado" if existia else "Creado"
        logger.info(f"{accion}: {ruta} ({len(contenido)} chars)")
        return f"{accion} exitosamente: {ruta}"

    except Exception as e:
        return f"Error escribiendo '{ruta}': {e}"


def editar_archivo(ruta: str, buscar: str, reemplazar: str) -> str:
    """
    Busca una cadena exacta en un archivo y la reemplaza.
    Solo reemplaza la primera ocurrencia.
    """
    ruta_p = _ruta_segura(ruta)

    if not ruta_p.exists():
        return f"Error: El archivo '{ruta}' no existe."

    if ruta_p.suffix in EXTENSIONES_PROTEGIDAS:
        return f"Error: No puedo editar archivos con extensión '{ruta_p.suffix}'."

    try:
        contenido = ruta_p.read_text(encoding="utf-8")

        if buscar not in contenido:
            return (
                f"Error: No encontré la cadena exacta a reemplazar en '{ruta}'. "
                "Verifica que el texto a buscar sea exacto (incluyendo espacios e indentación)."
            )

        nuevo = contenido.replace(buscar, reemplazar, 1)
        ruta_p.write_text(nuevo, encoding="utf-8")
        logger.info(f"Editado: {ruta} (reemplazo aplicado)")
        return f"Editado exitosamente: {ruta}"

    except Exception as e:
        return f"Error editando '{ruta}': {e}"


def listar_directorio(ruta: str = ".") -> str:
    """Lista el contenido de un directorio con tipos y tamaños."""
    ruta_p = _ruta_segura(ruta)

    if not ruta_p.exists():
        return f"Error: El directorio '{ruta}' no existe."
    if not ruta_p.is_dir():
        return f"Error: '{ruta}' no es un directorio."

    try:
        entradas = sorted(ruta_p.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        # Filtrar ruido
        ocultos = {".venv", "__pycache__", ".git", "node_modules", ".mypy_cache"}
        entradas = [e for e in entradas if e.name not in ocultos]

        ruta_rel = ruta_p.relative_to(RAIZ_PROYECTO) if ruta_p != RAIZ_PROYECTO else Path(".")
        lineas = [f"Directorio: {ruta_rel}/"]
        for entrada in entradas:
            if entrada.is_dir():
                n_hijos = sum(1 for _ in entrada.iterdir()) if entrada.exists() else 0
                lineas.append(f"  [DIR]  {entrada.name}/  ({n_hijos} items)")
            else:
                tamano = entrada.stat().st_size
                if tamano < 1024:
                    tam_str = f"{tamano}B"
                elif tamano < 1024 * 1024:
                    tam_str = f"{tamano // 1024}KB"
                else:
                    tam_str = f"{tamano // (1024*1024)}MB"
                lineas.append(f"  [FILE] {entrada.name}  ({tam_str})")

        resultado = "\n".join(lineas) if lineas else "(directorio vacío)"
        logger.info(f"Listado: {ruta} ({len(entradas)} entradas)")
        return resultado

    except Exception as e:
        return f"Error listando '{ruta}': {e}"


def buscar_en_codigo(patron: str, ruta: str = ".") -> str:
    """
    Busca un patrón (texto o regex) en los archivos del proyecto.
    Retorna las coincidencias con archivo y línea.
    """
    ruta_p = _ruta_segura(ruta)

    extensiones_codigo = {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ini"}
    resultados = []
    max_resultados = 30

    try:
        regex = re.compile(patron, re.IGNORECASE)
    except re.error:
        # Si no es regex válido, buscar como texto literal
        regex = re.compile(re.escape(patron), re.IGNORECASE)

    try:
        for archivo in ruta_p.rglob("*"):
            if len(resultados) >= max_resultados:
                break
            if not archivo.is_file():
                continue
            if archivo.suffix not in extensiones_codigo:
                continue
            # Ignorar directorios de entorno y cache
            partes = archivo.parts
            if any(p in (".venv", "__pycache__", ".git", "node_modules") for p in partes):
                continue

            try:
                contenido = archivo.read_text(encoding="utf-8", errors="replace")
                for num, linea in enumerate(contenido.splitlines(), 1):
                    if regex.search(linea):
                        ruta_rel = archivo.relative_to(RAIZ_PROYECTO)
                        resultados.append(f"{ruta_rel}:{num}: {linea.strip()}")
                        if len(resultados) >= max_resultados:
                            break
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                continue

        if resultados:
            texto = "\n".join(resultados)
            logger.info(f"Búsqueda '{patron}': {len(resultados)} coincidencias")
            return texto
        else:
            return f"Sin coincidencias para '{patron}'"

    except Exception as e:
        return f"Error buscando '{patron}': {e}"


def _necesita_elevacion(resultado) -> bool:
    """Detecta si un comando falló por falta de permisos de administrador."""
    if resultado.returncode == 0:
        return False
    stderr = (resultado.stderr or "").lower()
    indicadores = (
        "access is denied", "acceso denegado", "se requiere elevación",
        "elevation required", "requires elevation", "run as administrator",
        "ejecutar como administrador", "no tiene permisos", "permission denied",
        "privilegio", "privilege", "0x80070005",
    )
    return any(ind in stderr for ind in indicadores)


def _ejecutar_elevado(comando: str) -> str:
    """Reintenta un comando con elevación UAC usando ShellExecuteW(runas)."""
    import ctypes
    import ctypes.wintypes
    try:
        logger.info(f"Solicitando elevación UAC para: {comando}")
        # RF-167: argtypes/restype para Win32 64-bit
        _shell32 = ctypes.windll.shell32
        _shell32.ShellExecuteW.argtypes = [
            ctypes.wintypes.HWND, ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR,
            ctypes.wintypes.LPCWSTR, ctypes.c_int,
        ]
        _shell32.ShellExecuteW.restype = ctypes.wintypes.HINSTANCE
        ret = _shell32.ShellExecuteW(
            None, "runas", "cmd.exe", f"/c {comando}", str(RAIZ_PROYECTO), 1
        )
        # ShellExecuteW retorna >32 si fue exitoso
        if ret > 32:
            return "Comando ejecutado con permisos de administrador. Se solicitó elevación al usuario."
        else:
            return f"Error: No se pudo elevar permisos (código: {ret}). El usuario pudo haber cancelado la solicitud."
    except Exception as e:
        return f"Error al solicitar elevación: {e}"


def ejecutar_comando(comando: str) -> str:
    """
    Ejecuta un comando de shell dentro del directorio del proyecto.
    FP-034: Delegado a comando_seguro.py (allowlist + shell=False).
    """
    from computadora.habilidades.comando_seguro import ejecutar_comando_seguro
    return ejecutar_comando_seguro(comando, RAIZ_PROYECTO)


def ejecutar_comando_sistema(comando: str) -> str:
    """
    Ejecuta un comando del SO fuera del sandbox del proyecto.
    FP-034: Delegado a comando_seguro.py (allowlist + shell=False).
    """
    from computadora.habilidades.comando_seguro import ejecutar_comando_sistema_seguro
    return ejecutar_comando_sistema_seguro(comando)


# ═══════════════════════════════════════════════
# CONFIGURACIÓN GENERAL DEL GUARDIÁN (Nueva)
# ═══════════════════════════════════════════════

def configurar_guardian(
    hora_activacion: str = None,
    inactividad_minutos: int = None,
    visión_nocturna: bool = None,
    registrar_eventos: bool = None
) -> str:
    """Configura los parámetros del Guardián (שומר Shomer).
    
    Args:
        hora_activacion (str, optional): Hora para auto-activar guardián (formato: "HH:MM", ej: "21:00")
        inactividad_minutos (int, optional): Minutos sin actividad antes de activar guardián (ej: 5)
        visión_nocturna (bool, optional): Activar visión nocturna con cámara
        registrar_eventos (bool, optional): Registrar eventos detectados mientras vigila
    
    Returns:
        str: Confirmación de configuración actualizada
    """
    import json
    from pathlib import Path
    
    try:
        # Cargar config actual
        config_path = RAIZ_PROYECTO / "_config" / "config.json"
        if not config_path.exists():
            return "Error: archivo config.json no encontrado."
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Asegurar que existe la sección guardian
        if 'guardian' not in config:
            config['guardian'] = {}
        
        # Actualizar parámetros si se proporcionan
        cambios = []
        
        if hora_activacion is not None:
            # Validar formato HH:MM
            if not _validar_formato_hora(hora_activacion):
                return f"Error: formato de hora inválido '{hora_activacion}'. Usa HH:MM (ej: 21:00)"
            config['guardian']['hora_activacion_automatica'] = hora_activacion
            cambios.append(f"Hora de activación: {hora_activacion}")
        
        if inactividad_minutos is not None:
            if not isinstance(inactividad_minutos, int) or inactividad_minutos <= 0:
                return f"Error: timeout de inactividad debe ser un número positivo. Recibido: {inactividad_minutos}"
            config['guardian']['timeout_inactividad_minutos'] = inactividad_minutos
            cambios.append(f"Timeout de inactividad: {inactividad_minutos} minutos")
        
        if visión_nocturna is not None:
            config['guardian']['visión_nocturna'] = bool(visión_nocturna)
            estado = "activada" if visión_nocturna else "desactivada"
            cambios.append(f"Visión nocturna: {estado}")
        
        if registrar_eventos is not None:
            config['guardian']['registrar_eventos'] = bool(registrar_eventos)
            estado = "activado" if registrar_eventos else "desactivado"
            cambios.append(f"Registro de eventos: {estado}")
        
        # Guardar config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        if cambios:
            logger.info(f"🛡️ Guardián configurado: {', '.join(cambios)}")
            return f"Configuración del guardián actualizada:\n" + "\n".join([f"✓ {c}" for c in cambios])
        else:
            return "No se proporcionaron cambios. Uso: configurar_guardian(hora_activacion='21:00', inactividad_minutos=5, ...)"
    
    except Exception as e:
        logger.error(f"Error configurando guardián: {e}")
        return f"Error al guardar configuración: {e}"


def _validar_formato_hora(hora_str: str) -> bool:
    """Valida formato HH:MM."""
    import re
    if not re.match(r'^\d{2}:\d{2}$', hora_str):
        return False
    horas, minutos = map(int, hora_str.split(':'))
    return 0 <= horas < 24 and 0 <= minutos < 60


def estado_guardian() -> str:
    """Retorna el estado actual de configuración del guardián."""
    import json
    from pathlib import Path
    
    try:
        config_path = RAIZ_PROYECTO / "_config" / "config.json"
        if not config_path.exists():
            return "Error: archivo config.json no encontrado."
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        guardian_cfg = config.get('guardian', {})
        
        estado = "🛡️ Configuración actual del Guardián:\n"
        estado += f"  • Activación automática: {guardian_cfg.get('hora_activacion_automatica', 'N/A')}\n"
        estado += f"  • Timeout de inactividad: {guardian_cfg.get('timeout_inactividad_minutos', 'N/A')} minutos\n"
        estado += f"  • Visión nocturna: {'✓ Activa' if guardian_cfg.get('visión_nocturna', False) else '✗ Inactiva'}\n"
        estado += f"  • Registro de eventos: {'✓ Activo' if guardian_cfg.get('registrar_eventos', False) else '✗ Inactivo'}"
        
        return estado
    
    except Exception as e:
        logger.error(f"Error obteniendo estado del guardián: {e}")
        return f"Error al leer configuración: {e}"


# ═══════════════════════════════════════════════
# REGISTRO DE HERRAMIENTAS
# ═══════════════════════════════════════════════

HERRAMIENTAS = {
    "leer_archivo": {
        "funcion": leer_archivo,
        "descripcion": "Lee el contenido de un archivo. Args: ruta (str), linea_inicio (int, opcional), linea_fin (int, opcional)",
    },
    "escribir_archivo": {
        "funcion": escribir_archivo,
        "descripcion": "Escribe/crea un archivo con el contenido dado. Args: ruta (str), contenido (str)",
    },
    "editar_archivo": {
        "funcion": editar_archivo,
        "descripcion": "Busca una cadena exacta en un archivo y la reemplaza. Args: ruta (str), buscar (str), reemplazar (str)",
    },
    "listar_directorio": {
        "funcion": listar_directorio,
        "descripcion": "Lista el contenido de un directorio. Args: ruta (str, default='.')",
    },
    "buscar_en_codigo": {
        "funcion": buscar_en_codigo,
        "descripcion": "Busca un patrón en los archivos del código fuente. Args: patron (str), ruta (str, default='.')",
    },
    "ejecutar_comando": {
        "funcion": ejecutar_comando,
        "descripcion": "Ejecuta un comando de shell en el directorio del proyecto. Args: comando (str)",
    },
    "ejecutar_comando_sistema": {
        "funcion": ejecutar_comando_sistema,
        "descripcion": "Ejecuta un comando de consulta del SO (systeminfo, tasklist, ipconfig, etc). Solo comandos de lectura. Args: comando (str)",
    },
    "buscar_en_internet": {
        "funcion": None,  # Se importa después para evitar circular
        "descripcion": "Busca información en internet. Args: consulta (str)",
    },
    "solicitar_a_copilot": {
        "funcion": None,  # Se importa después
        "descripcion": "Envía una solicitud a Copilot/IDE para modificar código (tuyo o de otro proyecto). Args: descripcion (str), proyecto (str, default='computadora'), archivos_afectados (str, opcional), contexto (str, opcional), prioridad (str, default='normal')",
    },
    "verificar_respuesta": {
        "funcion": None,
        "descripcion": "Verifica si Copilot completó una solicitud de código. Args: solicitud_id (str, opcional)",
    },
    "listar_solicitudes": {
        "funcion": None,
        "descripcion": "Lista solicitudes de código pendientes. Sin args.",
    },
    # Sistema / JARVIS features
    "abrir_aplicacion": {
        "funcion": None,
        "descripcion": "Abre una aplicación de Windows por nombre. Args: nombre (str)",
    },
    "cerrar_aplicacion": {
        "funcion": None,
        "descripcion": "Cierra una aplicación por nombre de proceso. Args: nombre (str)",
    },
    "controlar_volumen": {
        "funcion": None,
        "descripcion": "Control de volumen del sistema. Args: accion (subir/bajar/mute/unmute/max/min)",
    },
    "leer_portapapeles": {
        "funcion": None,
        "descripcion": "Lee el contenido del portapapeles. Sin args.",
    },
    "escribir_portapapeles": {
        "funcion": None,
        "descripcion": "Escribe texto al portapapeles. Args: texto (str)",
    },
    "obtener_fecha_hora": {
        "funcion": None,
        "descripcion": "Retorna fecha y hora actual. Sin args.",
    },
    "obtener_info_sistema": {
        "funcion": None,
        "descripcion": "Retorna información básica del sistema (RAM, disco, batería). Sin args.",
    },
    "crear_recordatorio": {
        "funcion": None,
        "descripcion": "Crea un recordatorio. Args: mensaje (str), minutos (str o number)",
    },
    "listar_recordatorios": {
        "funcion": None,
        "descripcion": "Lista recordatorios pendientes. Sin args.",
    },
    "diagnostico_sistema": {
        "funcion": None,
        "descripcion": "Retorna un diagnóstico rápido del estado del sistema (Ollama, audio, perfil de voz, herramientas).",
    },
    "tomar_captura_pantalla": {
        "funcion": None,
        "descripcion": "Toma una captura de pantalla completa. Args opcionales: nombre (str)",
    },
    "buscar_archivos": {
        "funcion": None,
        "descripcion": "Busca archivos por nombre en una carpeta (recursivo). Args: nombre (str), carpeta (str, opcional)",
    },
    "agregar_tarea": {
        "funcion": None,
        "descripcion": "Agrega una tarea pendiente. Args: descripcion (str)",
    },
    "listar_tareas": {
        "funcion": None,
        "descripcion": "Lista todas las tareas pendientes. Sin args.",
    },
    "completar_tarea": {
        "funcion": None,
        "descripcion": "Marca una tarea como completada. Args: descripcion (str, texto parcial o número)",
    },
    "eliminar_tarea": {
        "funcion": None,
        "descripcion": "Elimina una tarea. Args: descripcion (str, texto parcial o número)",
    },
    "agregar_nota": {
        "funcion": None,
        "descripcion": "Guarda una nota rápida con timestamp. Args: contenido (str)",
    },
    "listar_notas": {
        "funcion": None,
        "descripcion": "Lista las notas guardadas (últimas 20). Sin args.",
    },
    "eliminar_nota": {
        "funcion": None,
        "descripcion": "Elimina una nota. Args: descripcion (str, texto parcial o número)",
    },
    "monitoreo_sistema": {
        "funcion": None,
        "descripcion": "Reporte completo del estado del sistema (CPU, RAM, disco, GPU, red, procesos). Sin args.",
    },
    "estado_rapido_sistema": {
        "funcion": None,
        "descripcion": "Estado rápido del sistema en una línea (CPU, RAM, disco). Sin args.",
    },
    "contexto_pantalla": {
        "funcion": None,
        "descripcion": "Describe qué está haciendo el usuario (ventana activa, app). Sin args.",
    },
    # Meta-Workflow: gestión multi-proyecto (כתר Keter — supervisión)
    "listar_proyectos": {
        "funcion": None,
        "descripcion": "Lista todos los proyectos registrados con su estado. Sin args.",
    },
    "auditar_proyecto": {
        "funcion": None,
        "descripcion": "Audita un proyecto: WorkItems pendientes, docs faltantes. Args: nombre (str)",
    },
    "resumen_proyectos": {
        "funcion": None,
        "descripcion": "Resumen general de todos los proyectos registrados. Sin args.",
    },
    "registrar_proyecto": {
        "funcion": None,
        "descripcion": "Registra un directorio como proyecto gestionado. Args: ruta (str), nombre (str, opcional)",
    },
    "consultar_memoria": {
        "funcion": None,
        "descripcion": "Busca en la memoria de días anteriores por palabras clave. Args: consulta (str), dias (int, opcional, default 30)",
    },
    "listar_tareas_diferidas": {
        "funcion": None,
        "descripcion": "Lista tareas que el usuario dejó 'para después'. Sin args.",
    },
    "completar_tarea_diferida": {
        "funcion": None,
        "descripcion": "Marca como completada una tarea diferida. Args: descripcion (str, texto parcial o número)",
    },
    "agregar_tarea_diferida": {
        "funcion": None,
        "descripcion": "Agrega una tarea diferida/pendiente para después. Args: descripcion (str), tipo (str: 'indefinida' o 'con_recordatorio')",
    },
    "info_entorno": {
        "funcion": None,
        "descripcion": "Reporte completo del entorno de ejecución (OS, CPU, RAM, disco, GPU, red, Ollama). Sin args.",
    },
    # RF-133: Demo visual como herramienta para N2 (balance Keter)
    "demo_visual": {
        "funcion": lambda **kw: "__DEMO_ANIMACIONES__",
        "descripcion": "Ejecuta la demostración visual completa dCOMPUTADORA (demo Maljut). Sin args.",
    },
    # RF-206: Herramientas Kli HaHarjavá (FP-075)
    "escanear_red": {
        "funcion": None,
        "descripcion": "Escanea la red local y lista dispositivos (IP, MAC, hostname). Sin args.",
    },
    "ver_camara": {
        "funcion": None,
        "descripcion": "Captura un frame de la cámara y detecta movimiento. Sin args.",
    },
    "control_remoto": {
        "funcion": None,
        "descripcion": "Envía comando SSH o WoL a dispositivo remoto. Args: host, cmd (opcional), mac (opcional).",
    },
    # WI-260: Confirmación conversacional (el LLM la usa naturalmente)
    "confirmar": {
        "funcion": lambda respuesta="Sí.", **kw: respuesta,
        "descripcion": "Responde al usuario con una confirmación simple. Úsala cuando solo necesitas afirmar, negar o responder brevemente sin ejecutar otra acción. Args: respuesta (str)",
    },    # Configuración General del Guardián (שומר — Nueva herramienta)
    "configurar_guardian": {
        "funcion": configurar_guardian,
        "descripcion": "Configura parámetros del Guardián (hora de activación automática, timeout de inactividad, visión nocturna, registro de eventos). Args: hora_activacion (str, ej: '21:00'), inactividad_minutos (int), visión_nocturna (bool), registrar_eventos (bool)",
    },
    "estado_guardian": {
        "funcion": estado_guardian,
        "descripcion": "Muestra la configuración actual del Guardián. Sin args.",
    },}


# RF-242: Flag para modo demo Gevurá (bypassa confirmación individual)
_DEMO_MODO_GEVURA: bool = False

# גבורה Gevurá — Niveles de permiso por herramienta
_NIVELES_PERMISO: dict[str, str] = {
    # Lectura / consulta → auto-aprobado
    "confirmar": "info",  # WI-260: auto-aprobado (solo texto)
    "obtener_fecha_hora": "info", "obtener_info_sistema": "info",
    "leer_portapapeles": "info", "listar_tareas": "info",
    "listar_notas": "info", "listar_recordatorios": "info",
    "contexto_pantalla": "info", "listar_proyectos": "info",
    "resumen_proyectos": "info", "consultar_memoria": "info",
    "listar_tareas_diferidas": "info", "info_entorno": "info",
    "estado_rapido_sistema": "info", "monitoreo_sistema": "info",
    "buscar_en_internet": "info", "auditar_proyecto": "info",
    # Acciones moderadas → confirmación del usuario
    "abrir_aplicacion": "accion", "cerrar_aplicacion": "accion",
    "controlar_volumen": "accion", "escribir_portapapeles": "accion",
    "crear_recordatorio": "accion", "tomar_captura_pantalla": "accion",
    "buscar_archivos": "accion", "agregar_tarea": "accion",
    "completar_tarea": "accion", "eliminar_tarea": "accion",
    "agregar_nota": "accion", "eliminar_nota": "accion",
    "agregar_tarea_diferida": "accion", "completar_tarea_diferida": "accion",
    "registrar_proyecto": "accion",
    # Copilot / AI → acción (implica procesar externamente)
    "solicitar_a_copilot": "accion", "verificar_respuesta": "accion",
    "listar_solicitudes": "info",
    "demo_visual": "info",  # RF-133: auto-aprobado (no peligroso)
    # RF-206: Herramientas Kli (FP-075)
    "escanear_red": "accion",
    "ver_camara": "info",
    "control_remoto": "admin",
    # Sistema peligroso → admin
    "diagnostico_sistema": "admin",
    # Configuración del Guardián (שומר)
    "estado_guardian": "info",  # Solo lectura
    "configurar_guardian": "accion",  # Requiere confirmación
}


def ejecutar_herramienta(nombre: str, args: dict[str, Any], *, orden_directa: bool = False) -> str:
    """
    Ejecuta una herramienta por nombre con los argumentos dados.
    Retorna el resultado como string.
    גבורה — Cada ejecución pasa por GestorPermisos antes de actuar.
    FP-042: orden_directa=True auto-aprueba nivel "accion" (comando directo del usuario).
    """
    if nombre not in HERRAMIENTAS:
        herramientas_disponibles = ", ".join(HERRAMIENTAS.keys())
        return f"Error: Herramienta '{nombre}' no existe. Disponibles: {herramientas_disponibles}"

    # גבורה Gevurá — Check de permisos ANTES de ejecutar
    nivel_permiso = _NIVELES_PERMISO.get(nombre, "accion")
    # RF-242: En modo demo Gevurá, bypass de confirmación
    if _DEMO_MODO_GEVURA:
        logger.debug("Gevurá demo: bypass permiso para '%s'", nombre)
    else:
        try:
            gestor = _obtener_gestor_permisos()
            if not gestor.solicitar(nombre, nivel_permiso, orden_directa=orden_directa):
                logger.warning(f"Gevurá: permiso denegado para '{nombre}' (nivel={nivel_permiso})")
                try:
                    from computadora.nucleo.eventos import obtener_bus
                    obtener_bus().emitir("permiso_solicitado", {
                        "accion": nombre, "nivel": nivel_permiso, "resultado": "denegado",
                    })
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                return f"Permiso denegado para '{nombre}'. El usuario no autorizó la acción."
        except Exception as e:
            logger.debug(f"Gevurá: error en check de permisos ({e}), permitiendo por defecto")

    herramienta = HERRAMIENTAS[nombre]
    funcion = herramienta["funcion"]

    # Import lazy de módulos para evitar circular
    if funcion is None:
        if nombre == "buscar_en_internet":
            from computadora.habilidades.web import buscar_en_internet as _buscar
            HERRAMIENTAS["buscar_en_internet"]["funcion"] = _buscar
            funcion = _buscar
        elif nombre == "solicitar_a_copilot":
            from computadora.habilidades.copilot_bridge import solicitar_a_copilot as _sol
            HERRAMIENTAS["solicitar_a_copilot"]["funcion"] = _sol
            funcion = _sol
        elif nombre == "verificar_respuesta":
            from computadora.habilidades.copilot_bridge import verificar_respuesta as _ver
            HERRAMIENTAS["verificar_respuesta"]["funcion"] = _ver
            funcion = _ver
        elif nombre == "listar_solicitudes":
            from computadora.habilidades.copilot_bridge import listar_solicitudes_pendientes as _lsp
            HERRAMIENTAS["listar_solicitudes"]["funcion"] = _lsp
            funcion = _lsp
        elif nombre in ("abrir_aplicacion", "cerrar_aplicacion", "controlar_volumen", "leer_portapapeles", "escribir_portapapeles", "obtener_fecha_hora", "obtener_info_sistema", "crear_recordatorio", "listar_recordatorios", "diagnostico_sistema", "tomar_captura_pantalla", "buscar_archivos"):
            from computadora.habilidades.sistema import (
                abrir_aplicacion as _abrir,
                cerrar_aplicacion as _cerrar,
                controlar_volumen as _vol,
                leer_portapapeles as _lp,
                escribir_portapapeles as _wp,
                obtener_fecha_hora as _fh,
                obtener_info_sistema as _info,
                crear_recordatorio as _crea_rec,
                listar_recordatorios as _list_rec,
                tomar_captura_pantalla as _captura,
                buscar_archivos as _buscar_arch,
            )
            mapping = {
                "abrir_aplicacion": _abrir,
                "cerrar_aplicacion": _cerrar,
                "controlar_volumen": _vol,
                "leer_portapapeles": _lp,
                "escribir_portapapeles": _wp,
                "obtener_fecha_hora": _fh,
                "obtener_info_sistema": _info,
                "crear_recordatorio": _crea_rec,
                "listar_recordatorios": _list_rec,
                "tomar_captura_pantalla": _captura,
                "buscar_archivos": _buscar_arch,
            }
            # Añadir diagnóstico si lo solicita
            try:
                from computadora.habilidades.sistema import diagnostico_sistema as _diag
                mapping["diagnostico_sistema"] = _diag
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
            HERRAMIENTAS[nombre]["funcion"] = mapping[nombre]
            funcion = mapping[nombre]
        elif nombre in ("agregar_tarea", "listar_tareas", "completar_tarea", "eliminar_tarea", "agregar_nota", "listar_notas", "eliminar_nota"):
            from computadora.habilidades.agenda import (
                agregar_tarea as _at,
                listar_tareas as _lt,
                completar_tarea as _ct,
                eliminar_tarea as _et,
                agregar_nota as _an,
                listar_notas as _ln,
                eliminar_nota as _en,
            )
            agenda_mapping = {
                "agregar_tarea": _at,
                "listar_tareas": _lt,
                "completar_tarea": _ct,
                "eliminar_tarea": _et,
                "agregar_nota": _an,
                "listar_notas": _ln,
                "eliminar_nota": _en,
            }
            HERRAMIENTAS[nombre]["funcion"] = agenda_mapping[nombre]
            funcion = agenda_mapping[nombre]
        elif nombre in ("monitoreo_sistema", "estado_rapido_sistema"):
            from computadora.habilidades.monitor_sistema import monitoreo_sistema as _mon, estado_rapido_sistema as _est
            HERRAMIENTAS["monitoreo_sistema"]["funcion"] = _mon
            HERRAMIENTAS["estado_rapido_sistema"]["funcion"] = _est
            funcion = _mon if nombre == "monitoreo_sistema" else _est
        elif nombre == "contexto_pantalla":
            from computadora.utilidades.windows import ContextoPantalla as _CP
            _ctx = _CP()
            def _desc_ctx(**kw):
                return _ctx.descripcion_contexto()
            HERRAMIENTAS["contexto_pantalla"]["funcion"] = _desc_ctx
            funcion = _desc_ctx
        elif nombre in ("listar_proyectos", "auditar_proyecto", "resumen_proyectos", "registrar_proyecto"):
            from computadora.nucleo.meta_workflow import MetaWorkflow as _MW
            _mw = _MW()
            mw_mapping = {
                "listar_proyectos": lambda **kw: _mw.listar_proyectos(),
                "auditar_proyecto": lambda **kw: _mw.auditar_proyecto(kw.get("nombre", "")),
                "resumen_proyectos": lambda **kw: _mw.resumen_general(),
                "registrar_proyecto": lambda **kw: _mw.registrar_proyecto(kw.get("ruta", ""), kw.get("nombre", "")),
            }
            for k, v in mw_mapping.items():
                HERRAMIENTAS[k]["funcion"] = v
            funcion = mw_mapping[nombre]
        elif nombre == "consultar_memoria":
            from computadora.memoria.memoria import buscar_en_memoria as _bem
            HERRAMIENTAS["consultar_memoria"]["funcion"] = lambda **kw: _bem(kw.get("consulta", ""), dias=int(kw.get("dias", 30)))
            funcion = HERRAMIENTAS["consultar_memoria"]["funcion"]
        elif nombre in ("listar_tareas_diferidas", "completar_tarea_diferida", "agregar_tarea_diferida"):
            from computadora.habilidades.agenda import (
                listar_tareas_diferidas as _ltd,
                completar_tarea_diferida as _ctd,
                agregar_tarea_diferida as _atd,
            )
            HERRAMIENTAS["listar_tareas_diferidas"]["funcion"] = lambda **kw: _ltd()
            HERRAMIENTAS["completar_tarea_diferida"]["funcion"] = lambda **kw: _ctd(kw.get("descripcion", ""))
            HERRAMIENTAS["agregar_tarea_diferida"]["funcion"] = lambda **kw: _atd(kw.get("descripcion", ""), tipo=kw.get("tipo", "indefinida"))
            td_mapping = {
                "listar_tareas_diferidas": HERRAMIENTAS["listar_tareas_diferidas"]["funcion"],
                "completar_tarea_diferida": HERRAMIENTAS["completar_tarea_diferida"]["funcion"],
                "agregar_tarea_diferida": HERRAMIENTAS["agregar_tarea_diferida"]["funcion"],
            }
            funcion = td_mapping[nombre]
        elif nombre == "info_entorno":
            from computadora.nucleo.entorno import EntornoSistema as _ES
            _ent = _ES()
            HERRAMIENTAS["info_entorno"]["funcion"] = lambda **kw: _ent.resumen_completo()
            funcion = HERRAMIENTAS["info_entorno"]["funcion"]
        # RF-298: Lazy imports para red y visión (FP-080)
        elif nombre == "escanear_red":
            from computadora.habilidades.red import KliRed as _KR
            _kr = _KR()
            HERRAMIENTAS["escanear_red"]["funcion"] = lambda **kw: _kr.leer_ohr()
            funcion = HERRAMIENTAS["escanear_red"]["funcion"]
        elif nombre == "ver_camara":
            from computadora.nucleo.kli import GestorKelim
            from computadora.habilidades.vision import KliCamara as _KC

            def _ver_camara(**kw):
                gestor = GestorKelim.instancia()
                camaras = [k for k in gestor.listar() if k["id"] == "camara_local"]
                if camaras:
                    cam_info = camaras[0]
                    # FIX: antes, si la cámara ya estaba REGISTRADA en el gestor
                    # compartido (p.ej. por el Guardián), esta rama la conectaba
                    # para leer un frame pero nunca la desconectaba — dejando la
                    # cámara encendida tras una consulta puntual. Ahora se
                    # restaura al estado que tenía ANTES de esta llamada, igual
                    # que ya se hacía para la conexión creada ad-hoc más abajo.
                    ya_estaba_conectada = cam_info["estado"] == "CONECTADO"
                    if not ya_estaba_conectada:
                        if not gestor.conectar("camara_local"):
                            return "Error: No se pudo conectar con la cámara local"
                    resultado = gestor.leer("camara_local")
                    if not ya_estaba_conectada:
                        gestor.desconectar("camara_local")
                else:
                    _kc = _KC()
                    if not _kc.conectar():
                        return "Error: No se pudo conectar con la cámara local"
                    resultado = _kc.leer_ohr()
                    _kc.desconectar()
                if isinstance(resultado, dict) and "error" in resultado:
                    return resultado["error"]
                return resultado

            HERRAMIENTAS["ver_camara"]["funcion"] = _ver_camara
            funcion = _ver_camara

    try:
        # יסוד — Emitir evento de inicio
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("herramienta_iniciada", {"nombre": nombre, "args": args})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        resultado = funcion(**args)

        # יסוד — Emitir evento de completado
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("herramienta_completada", {
                "nombre": nombre,
                "resultado": str(resultado)[:200],
                "ok": not (isinstance(resultado, str) and resultado.startswith("Error")),
            })
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # גבורה+יסוד — Sigilo de Contención: registrar errores para aprendizaje
        if isinstance(resultado, str) and resultado.startswith("Error"):
            try:
                from computadora.memoria.aprendizaje import MemoriaErrores
                _mem = MemoriaErrores()
                _mem.registrar_error(
                    contexto=f"herramienta:{nombre}",
                    accion=f"{nombre}({args})"[:200],
                    error=resultado[:300],
                )
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
        return resultado
    except TypeError as e:
        # יסוד — Emitir error
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("herramienta_error", {"nombre": nombre, "error": str(e)[:200]})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        # גבורה+יסוד — Registrar error de argumentos
        try:
            from computadora.memoria.aprendizaje import MemoriaErrores
            MemoriaErrores().registrar_error(
                contexto=f"herramienta:{nombre}",
                accion=f"{nombre}({args})"[:200],
                error=f"TypeError: {e}"[:300],
            )
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return f"Error: Argumentos incorrectos para '{nombre}': {e}"
    except Exception as e:
        logger.error(f"Error ejecutando herramienta '{nombre}': {e}")
        # יסוד — Emitir error
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("herramienta_error", {"nombre": nombre, "error": str(e)[:200]})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        # גבורה+יסוד — Registrar excepción inesperada
        try:
            from computadora.memoria.aprendizaje import MemoriaErrores
            MemoriaErrores().registrar_error(
                contexto=f"herramienta:{nombre}",
                accion=f"{nombre}({args})"[:200],
                error=f"{type(e).__name__}: {e}"[:300],
            )
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return f"Error ejecutando '{nombre}': {e}"


def obtener_descripcion_herramientas() -> str:
    """Genera la descripción de todas las herramientas para el system prompt."""
    lineas = []
    for nombre, info in HERRAMIENTAS.items():
        lineas.append(f"- {nombre}: {info['descripcion']}")
    return "\n".join(lineas)


# ═══════════════════════════════════════════════
# TOOL-CALLING NATIVO DE OLLAMA (WI tool-calling nativo)
# ═══════════════════════════════════════════════
#
# Ollama (>=0.3 con modelos que declaran capability "tools", confirmado en
# vivo con qwen2.5:3b-instruct) acepta un parámetro `tools` en el payload de
# /api/chat con el mismo formato que la Chat Completions API de OpenAI:
#   {"type": "function", "function": {"name", "description", "parameters": <JSON Schema>}}
# Esto es MUCHO más confiable que pedirle al modelo por texto que emita un
# bloque ```tool — el modelo pequeño a veces narra en prosa en vez de seguir
# la convención textual. generar_tools_ollama() construye ese schema a
# partir del registro HERRAMIENTAS, parseando el patrón de texto libre
# "Args: nombre (tipo[, opcional])" que ya usan las descripciones. Es
# best-effort: una herramienta con descripción atípica obtiene un schema
# laxo (sin properties estrictas) en vez de romper — Ollama/el modelo puede
# seguir mandando los argumentos que considere y ejecutar_herramienta() los
# recibe igual vía **kwargs.

_TOOLS_OLLAMA_CACHE: list[dict] | None = None

_RE_ARG_SEGMENTO = re.compile(
    r"^\s*([A-Za-zÁÉÍÓÚÑáéíóúñ_]\w*)\s*(?:\((.*)\))?\s*$"
)


def _partir_args_top_level(cuerpo: str) -> list[str]:
    """Divide 'a (x), b (y, z), c' por comas de nivel superior (ignora
    comas dentro de paréntesis, p.ej. "default='a, b'")."""
    partes: list[str] = []
    profundidad = 0
    actual = ""
    for ch in cuerpo:
        if ch == "(":
            profundidad += 1
        elif ch == ")":
            profundidad = max(0, profundidad - 1)
        if ch == "," and profundidad == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += ch
    if actual.strip():
        partes.append(actual)
    return partes


def _parsear_args_descripcion(descripcion: str) -> tuple[dict, list]:
    """
    Extrae un JSON Schema aproximado (properties/required) del patrón de
    texto libre usado en HERRAMIENTAS[...]['descripcion']:
    "Args: nombre (tipo), nombre2 (tipo, opcional)...", "Sin args.", etc.

    Heurística de tipo (best-effort, nunca falla — ante duda usa "string"):
      - 'bool' en el detalle → "boolean"
      - palabra 'int' en el detalle → "integer"
      - cualquier otro caso (incluido 'str', enums tipo 'subir/bajar', o
        sin paréntesis) → "string"
    Un argumento se marca opcional (fuera de 'required') si su detalle
    contiene 'opcional' o 'default'.
    """
    propiedades: dict = {}
    requeridos: list = []

    desc_lower = descripcion.lower()
    if "sin args" in desc_lower or "sin arg" in desc_lower:
        return propiedades, requeridos

    m = re.search(r"args?[^:]*:\s*(.+)", descripcion, re.IGNORECASE)
    if not m:
        return propiedades, requeridos

    cuerpo = m.group(1)
    for parte in _partir_args_top_level(cuerpo):
        parte = parte.strip().rstrip(".").strip()
        if not parte:
            continue
        mm = _RE_ARG_SEGMENTO.match(parte)
        if not mm:
            continue
        nombre_arg = mm.group(1)
        detalle = (mm.group(2) or "").lower()

        if "bool" in detalle:
            tipo = "boolean"
        elif re.search(r"\bint\b", detalle):
            tipo = "integer"
        else:
            tipo = "string"

        es_opcional = ("opcional" in detalle) or ("default" in detalle)
        propiedades[nombre_arg] = {"type": tipo}
        if not es_opcional:
            requeridos.append(nombre_arg)

    return propiedades, requeridos


def generar_tools_ollama(forzar_regeneracion: bool = False) -> list[dict]:
    """
    Construye la lista `tools` en formato nativo de Ollama a partir del
    registro HERRAMIENTAS. Se cachea en un módulo-global tras la primera
    construcción (el costo real es parseo de strings, trivial, pero se
    evita reconstruir en cada iteración del loop de tool-use).

    buscar_en_internet usa un schema explícito y limpio (en vez del
    best-effort genérico) porque es la herramienta más crítica para el
    usuario ahora mismo — confirmado en vivo contra qwen2.5:3b-instruct
    con exactamente este schema.
    """
    global _TOOLS_OLLAMA_CACHE
    if _TOOLS_OLLAMA_CACHE is not None and not forzar_regeneracion:
        return _TOOLS_OLLAMA_CACHE

    tools: list[dict] = []
    for nombre, info in HERRAMIENTAS.items():
        descripcion = info.get("descripcion", "") or ""

        if nombre == "buscar_en_internet":
            parametros = {
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": (
                            "La consulta de búsqueda (ej: 'dólar precio actual', "
                            "'clima en Buenos Aires', 'noticias de hoy')"
                        ),
                    }
                },
                "required": ["consulta"],
            }
        else:
            propiedades, requeridos = _parsear_args_descripcion(descripcion)
            parametros = {
                "type": "object",
                "properties": propiedades,
                "required": requeridos,
            }
            if not propiedades:
                # Schema laxo — sin args detectados (o "Sin args."). Permite
                # que el modelo mande lo que considere necesario sin que el
                # schema estricto bloquee argumentos no anticipados;
                # ejecutar_herramienta() los recibe igual vía **kwargs.
                parametros["additionalProperties"] = True

        tools.append({
            "type": "function",
            "function": {
                "name": nombre,
                "description": descripcion,
                "parameters": parametros,
            },
        })

    _TOOLS_OLLAMA_CACHE = tools
    return tools


