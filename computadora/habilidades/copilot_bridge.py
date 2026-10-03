"""
Puente Computadora → Copilot/IDE.

Cuando COMPUTADORA necesita modificar código (suyo o de otros proyectos),
escribe una solicitud estructurada en datos/solicitudes/ para que
GitHub Copilot la ejecute a través de VS Code.

Flujo:
1. Computadora detecta tarea de código → llama solicitar_a_copilot()
2. Se crea un archivo .json en datos/solicitudes/pendientes/
3. Copilot (o el usuario) lee la solicitud y ejecuta los cambios
4. El resultado se escribe en datos/solicitudes/completadas/
5. Computadora lee el resultado y avisa al usuario

Para cambios en el propio Computadora, el sistema señala que se necesita reinicio.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

# Directorios de solicitudes
_RAIZ = Path(__file__).resolve().parent.parent.parent
DIR_SOLICITUDES = _RAIZ / "datos" / "solicitudes"
DIR_PENDIENTES = DIR_SOLICITUDES / "pendientes"
DIR_COMPLETADAS = DIR_SOLICITUDES / "completadas"

# Crear directorios si no existen
DIR_PENDIENTES.mkdir(parents=True, exist_ok=True)
DIR_COMPLETADAS.mkdir(parents=True, exist_ok=True)


def solicitar_a_copilot(
    descripcion: str,
    proyecto: str = "computadora",
    archivos_afectados: str = "",
    contexto: str = "",
    prioridad: str = "normal",
) -> str:
    """
    Crea una solicitud para que Copilot/IDE realice cambios de código.

    Args:
        descripcion: Qué quiere el usuario que se modifique (en sus palabras).
        proyecto: Qué proyecto afecta. "computadora" = propio, otro = ruta del proyecto externo.
        archivos_afectados: Lista de archivos relevantes separados por coma.
        contexto: Contexto adicional dCOMPUTADORA (qué leyó, qué entendió).
        prioridad: "alta", "normal", "baja".

    Returns:
        Mensaje confirmando que la solicitud fue creada.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    solicitud_id = f"sol_{timestamp}"

    es_propio = proyecto.lower().strip() in ("computadora", "propio", "mi código", "mi codigo", "")

    solicitud = {
        "id": solicitud_id,
        "timestamp": datetime.now().isoformat(),
        "estado": "pendiente",
        "descripcion_usuario": descripcion,
        "proyecto": "computadora (propio)" if es_propio else proyecto,
        "archivos_afectados": [a.strip() for a in archivos_afectados.split(",") if a.strip()],
        "contexto_golem": contexto,
        "prioridad": prioridad,
        "requiere_reinicio": es_propio,
        "instrucciones_para_copilot": (
            f"El usuario pidió al Computadora lo siguiente: {descripcion}\n"
            f"Proyecto: {'Computadora (su propio código)' if es_propio else proyecto}\n"
            f"Archivos mencionados: {archivos_afectados or 'no especificados'}\n"
            f"Contexto adicional: {contexto or 'ninguno'}\n\n"
            "ACCIÓN REQUERIDA: Implementa los cambios solicitados."
            + (" Después reinicia COMPUTADORA para aplicar." if es_propio else "")
        ),
    }

    archivo = DIR_PENDIENTES / f"{solicitud_id}.json"
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(archivo, solicitud)
    logger.info(f"Solicitud creada: {solicitud_id} → {archivo}")

    return (
        f"Solicitud {solicitud_id} creada. "
        f"Copilot la verá en datos/solicitudes/pendientes/. "
        f"{'Requiere reinicio dCOMPUTADORA después.' if es_propio else f'Proyecto: {proyecto}.'}"
    )


def verificar_respuesta(solicitud_id: str = "") -> str:
    """
    Verifica si Copilot completó alguna solicitud pendiente.
    Si no se da ID, revisa la más reciente.
    """
    # Si no hay ID, buscar la más reciente
    if not solicitud_id:
        pendientes = sorted(DIR_PENDIENTES.glob("sol_*.json"), reverse=True)
        if not pendientes:
            return "No hay solicitudes pendientes."
        solicitud_id = pendientes[0].stem

    # Buscar en completadas
    completada = DIR_COMPLETADAS / f"{solicitud_id}.json"
    if completada.exists():
        data = json.loads(completada.read_text(encoding="utf-8"))
        estado = data.get("estado", "desconocido")
        resultado = data.get("resultado", "sin detalle")
        return f"Solicitud {solicitud_id}: {estado}. {resultado}"

    # Todavía pendiente
    pendiente = DIR_PENDIENTES / f"{solicitud_id}.json"
    if pendiente.exists():
        return f"Solicitud {solicitud_id} sigue pendiente. Copilot no la ha procesado aún."

    return f"No encontré la solicitud {solicitud_id}."


def listar_solicitudes_pendientes() -> str:
    """Lista todas las solicitudes pendientes."""
    pendientes = sorted(DIR_PENDIENTES.glob("sol_*.json"))
    if not pendientes:
        return "Sin solicitudes pendientes."

    lineas = []
    for p in pendientes[-10:]:  # Últimas 10
        data = json.loads(p.read_text(encoding="utf-8"))
        desc = data.get("descripcion_usuario", "?")[:80]
        proy = data.get("proyecto", "?")
        lineas.append(f"  {p.stem}: [{proy}] {desc}")

    return f"Solicitudes pendientes ({len(pendientes)}):\n" + "\n".join(lineas)


def marcar_completada(solicitud_id: str, resultado: str = "Cambios aplicados.") -> str:
    """
    Marca una solicitud como completada (llamado por Copilot/usuario).
    Mueve el archivo de pendientes/ a completadas/.
    """
    pendiente = DIR_PENDIENTES / f"{solicitud_id}.json"
    if not pendiente.exists():
        return f"Solicitud {solicitud_id} no encontrada en pendientes."

    data = json.loads(pendiente.read_text(encoding="utf-8"))
    data["estado"] = "completada"
    data["resultado"] = resultado
    data["completada_en"] = datetime.now().isoformat()

    completada = DIR_COMPLETADAS / f"{solicitud_id}.json"
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(completada, data)
    pendiente.unlink()

    logger.info(f"Solicitud completada: {solicitud_id}")
    return f"Solicitud {solicitud_id} marcada como completada."


