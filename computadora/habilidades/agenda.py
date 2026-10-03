"""
Habilidades de organización personal — Tareas y Notas.
CRUD por voz: agregar, listar, completar, eliminar.
Persistencia en datos/tareas.json y datos/notas.json.
"""

import datetime
import json
import uuid
from pathlib import Path

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_TAREAS_ARCHIVO = _DATOS_DIR / "tareas.json"
_NOTAS_ARCHIVO = _DATOS_DIR / "notas.json"


def _cargar_json(archivo: Path) -> list[dict]:
    if archivo.exists():
        try:
            return json.loads(archivo.read_text(encoding="utf-8"))
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return []
    return []


def _guardar_json(archivo: Path, datos: list[dict]):
    archivo.parent.mkdir(parents=True, exist_ok=True)
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(archivo, datos)


# ═══════════════════════════════════════════════
# TAREAS
# ═══════════════════════════════════════════════

def agregar_tarea(descripcion: str) -> str:
    """Agrega una nueva tarea pendiente."""
    if not descripcion or not descripcion.strip():
        return "Error: La descripción de la tarea no puede estar vacía"

    tareas = _cargar_json(_TAREAS_ARCHIVO)
    tarea = {
        "id": uuid.uuid4().hex[:8],
        "descripcion": descripcion.strip(),
        "completada": False,
        "creada": datetime.datetime.now().isoformat(),
    }
    tareas.append(tarea)
    _guardar_json(_TAREAS_ARCHIVO, tareas)

    logger.info(f"Tarea agregada: {tarea['descripcion']}")
    return f"Tarea agregada: '{tarea['descripcion']}'"


def listar_tareas() -> str:
    """Lista todas las tareas pendientes."""
    tareas = _cargar_json(_TAREAS_ARCHIVO)
    pendientes = [t for t in tareas if not t.get("completada")]

    if not pendientes:
        return "No hay tareas pendientes"

    lineas = []
    for i, t in enumerate(pendientes, 1):
        lineas.append(f"{i}. {t['descripcion']}")
    return f"Tareas pendientes ({len(pendientes)}):\n" + "\n".join(lineas)


def completar_tarea(descripcion: str) -> str:
    """Marca una tarea como completada (busca por texto parcial o número)."""
    tareas = _cargar_json(_TAREAS_ARCHIVO)
    pendientes = [t for t in tareas if not t.get("completada")]

    if not pendientes:
        return "No hay tareas pendientes para completar"

    # Intentar por número
    try:
        idx = int(descripcion) - 1
        if 0 <= idx < len(pendientes):
            pendientes[idx]["completada"] = True
            pendientes[idx]["completada_en"] = datetime.datetime.now().isoformat()
            _guardar_json(_TAREAS_ARCHIVO, tareas)
            logger.info(f"Tarea completada: {pendientes[idx]['descripcion']}")
            return f"Tarea completada: '{pendientes[idx]['descripcion']}'"
    except (ValueError, TypeError):
        pass

    # Buscar por texto parcial
    desc_l = descripcion.lower().strip()
    for t in pendientes:
        if desc_l in t["descripcion"].lower():
            t["completada"] = True
            t["completada_en"] = datetime.datetime.now().isoformat()
            _guardar_json(_TAREAS_ARCHIVO, tareas)
            logger.info(f"Tarea completada: {t['descripcion']}")
            return f"Tarea completada: '{t['descripcion']}'"

    return f"No encontré una tarea pendiente que coincida con '{descripcion}'"


def eliminar_tarea(descripcion: str) -> str:
    """Elimina una tarea (busca por texto parcial o número)."""
    tareas = _cargar_json(_TAREAS_ARCHIVO)
    pendientes = [t for t in tareas if not t.get("completada")]

    if not pendientes:
        return "No hay tareas para eliminar"

    # Intentar por número
    target_id = None
    try:
        idx = int(descripcion) - 1
        if 0 <= idx < len(pendientes):
            target_id = pendientes[idx]["id"]
    except (ValueError, TypeError):
        pass

    # Buscar por texto parcial
    if not target_id:
        desc_l = descripcion.lower().strip()
        for t in pendientes:
            if desc_l in t["descripcion"].lower():
                target_id = t["id"]
                break

    if target_id:
        nombre = next(t["descripcion"] for t in tareas if t["id"] == target_id)
        tareas = [t for t in tareas if t["id"] != target_id]
        _guardar_json(_TAREAS_ARCHIVO, tareas)
        logger.info(f"Tarea eliminada: {nombre}")
        return f"Tarea eliminada: '{nombre}'"

    return f"No encontré una tarea que coincida con '{descripcion}'"


# ═══════════════════════════════════════════════
# NOTAS RÁPIDAS
# ═══════════════════════════════════════════════

def agregar_nota(contenido: str) -> str:
    """Guarda una nota rápida con timestamp."""
    if not contenido or not contenido.strip():
        return "Error: El contenido de la nota no puede estar vacío"

    notas = _cargar_json(_NOTAS_ARCHIVO)
    nota = {
        "id": uuid.uuid4().hex[:8],
        "contenido": contenido.strip(),
        "creada": datetime.datetime.now().isoformat(),
    }
    notas.append(nota)
    _guardar_json(_NOTAS_ARCHIVO, notas)

    logger.info(f"Nota guardada: {nota['contenido'][:50]}")
    return f"Nota guardada: '{nota['contenido'][:80]}'"


def listar_notas() -> str:
    """Lista las notas guardadas (últimas 20)."""
    notas = _cargar_json(_NOTAS_ARCHIVO)

    if not notas:
        return "No hay notas guardadas"

    recientes = notas[-20:]
    lineas = []
    for i, n in enumerate(recientes, 1):
        fecha = datetime.datetime.fromisoformat(n["creada"]).strftime("%d/%m %H:%M")
        lineas.append(f"{i}. [{fecha}] {n['contenido'][:100]}")
    return f"Notas ({len(notas)} total):\n" + "\n".join(lineas)


def eliminar_nota(descripcion: str) -> str:
    """Elimina una nota (por número o texto parcial)."""
    notas = _cargar_json(_NOTAS_ARCHIVO)

    if not notas:
        return "No hay notas para eliminar"

    # Intentar por número (sobre las últimas 20)
    recientes = notas[-20:]
    target_id = None
    try:
        idx = int(descripcion) - 1
        if 0 <= idx < len(recientes):
            target_id = recientes[idx]["id"]
    except (ValueError, TypeError):
        pass

    # Buscar por texto parcial
    if not target_id:
        desc_l = descripcion.lower().strip()
        for n in reversed(notas):
            if desc_l in n["contenido"].lower():
                target_id = n["id"]
                break

    if target_id:
        contenido = next(n["contenido"] for n in notas if n["id"] == target_id)
        notas = [n for n in notas if n["id"] != target_id]
        _guardar_json(_NOTAS_ARCHIVO, notas)
        logger.info(f"Nota eliminada: {contenido[:50]}")
        return f"Nota eliminada: '{contenido[:80]}'"

    return f"No encontré una nota que coincida con '{descripcion}'"


# ─────────────────────────── Tareas diferidas ───────────────────────────
_DIFERIDAS_ARCHIVO = _DATOS_DIR / "tareas_diferidas.json"


def agregar_tarea_diferida(descripcion: str, tipo: str = "indefinida") -> str:
    """Agrega una tarea para 'después'. tipo: 'indefinida' o 'con_recordatorio'."""
    diferidas = _cargar_json(_DIFERIDAS_ARCHIVO)
    tarea = {
        "id": str(uuid.uuid4())[:8],
        "descripcion": descripcion.strip()[:200],
        "tipo": tipo,
        "creada": datetime.datetime.now().isoformat(),
        "completada": False,
    }
    diferidas.append(tarea)
    _guardar_json(_DIFERIDAS_ARCHIVO, diferidas)
    logger.info(f"Tarea diferida agregada: {tarea['descripcion'][:60]}")
    return f"Pendiente guardado: '{tarea['descripcion'][:80]}'"


def listar_tareas_diferidas() -> str:
    """Lista las tareas diferidas pendientes."""
    diferidas = _cargar_json(_DIFERIDAS_ARCHIVO)
    pendientes = [t for t in diferidas if not t.get("completada")]
    if not pendientes:
        return ""
    lineas = ["Tareas pendientes para después:"]
    for i, t in enumerate(pendientes[-15:], 1):
        fecha = t.get("creada", "")[:10]
        lineas.append(f"  {i}. {t['descripcion'][:80]} ({fecha})")
    return "\n".join(lineas)


def completar_tarea_diferida(descripcion: str) -> str:
    """Marca como completada una tarea diferida por número o texto."""
    diferidas = _cargar_json(_DIFERIDAS_ARCHIVO)
    pendientes = [t for t in diferidas if not t.get("completada")]
    if not pendientes:
        return "No hay tareas pendientes."
    target_id = None
    try:
        idx = int(descripcion) - 1
        if 0 <= idx < len(pendientes):
            target_id = pendientes[idx]["id"]
    except (ValueError, TypeError):
        pass
    if not target_id:
        desc_l = descripcion.lower().strip()
        for t in reversed(pendientes):
            if desc_l in t["descripcion"].lower():
                target_id = t["id"]
                break
    if target_id:
        for t in diferidas:
            if t["id"] == target_id:
                t["completada"] = True
                desc = t["descripcion"]
                break
        _guardar_json(_DIFERIDAS_ARCHIVO, diferidas)
        return f"Tarea completada: '{desc[:80]}'"
    return f"No encontré una tarea pendiente que coincida con '{descripcion}'"


