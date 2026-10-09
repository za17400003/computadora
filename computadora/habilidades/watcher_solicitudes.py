from loguru import logger
"""
Watcher de solicitudes dCOMPUTADORA → Copilot.

Este script monitorea datos/solicitudes/pendientes/ cada pocos segundos.
Cuando encuentra una solicitud nueva, muestra los detalles en consola
para que Copilot/el usuario la atienda.

Uso: python -m computadora.habilidades.watcher_solicitudes
O desde el Computadora: se puede ejecutar como hilo background.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

RAIZ = Path(__file__).resolve().parent.parent.parent
DIR_PENDIENTES = RAIZ / "datos" / "solicitudes" / "pendientes"
DIR_COMPLETADAS = RAIZ / "datos" / "solicitudes" / "completadas"

# Archivo de señal para que Copilot detecte solicitudes nuevas
ARCHIVO_SIGNAL = RAIZ / "datos" / "solicitudes" / "NUEVA_SOLICITUD.txt"


def revisar_pendientes():
    """Revisa y muestra solicitudes pendientes."""
    DIR_PENDIENTES.mkdir(parents=True, exist_ok=True)
    pendientes = sorted(DIR_PENDIENTES.glob("sol_*.json"))

    if not pendientes:
        return []

    solicitudes = []
    for p in pendientes:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            solicitudes.append(data)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            continue

    return solicitudes


def escribir_signal(solicitud):
    """Escribe un archivo de señal para que Copilot lo detecte."""
    contenido = (
        f"=== SOLICITUD DEL Computadora ===\n"
        f"ID: {solicitud['id']}\n"
        f"Fecha: {solicitud['timestamp']}\n"
        f"Proyecto: {solicitud['proyecto']}\n"
        f"Prioridad: {solicitud['prioridad']}\n"
        f"Requiere reinicio: {solicitud.get('requiere_reinicio', False)}\n\n"
        f"INSTRUCCIONES:\n{solicitud['instrucciones_para_copilot']}\n\n"
        f"Archivos afectados: {', '.join(solicitud.get('archivos_afectados', [])) or 'No especificados'}\n\n"
        f"--- Para completar, ejecuta en Python: ---\n"
        f"from computadora.habilidades.copilot_bridge import marcar_completada\n"
        f"marcar_completada('{solicitud['id']}', 'Descripción de lo que se hizo')\n"
    )
    ARCHIVO_SIGNAL.write_text(contenido, encoding="utf-8")


def modo_watch():
    """Loop de monitoreo continuo."""
    print(f"[Watcher] Monitoreando solicitudes en: {DIR_PENDIENTES}")
    print(f"[Watcher] Ctrl+C para detener\n")

    procesados = set()

    while True:
        solicitudes = revisar_pendientes()
        for sol in solicitudes:
            sid = sol["id"]
            if sid not in procesados:
                procesados.add(sid)
                print(f"\n{'='*60}")
                print(f"NUEVA SOLICITUD DEL Computadora: {sid}")
                print(f"{'='*60}")
                print(f"Proyecto: {sol.get('proyecto', '?')}")
                print(f"Descripción: {sol.get('descripcion_usuario', '?')}")
                print(f"Contexto: {sol.get('contexto_computadora', 'ninguno')}")
                print(f"Archivos: {', '.join(sol.get('archivos_afectados', [])) or 'No especificados'}")
                print(f"Prioridad: {sol.get('prioridad', 'normal')}")
                print(f"Reinicio: {'Sí' if sol.get('requiere_reinicio') else 'No'}")
                print(f"{'='*60}")

                # Escribir archivo signal
                escribir_signal(sol)

        time.sleep(3)


if __name__ == "__main__":
    modo_watch()


