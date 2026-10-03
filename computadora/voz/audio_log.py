"""
Registro de eventos de audio — todos los sonidos detectados, incluyendo falsos positivos.
Archivo: datos/memoria/audio_log.jsonl
"""

import json
import datetime
from pathlib import Path

from loguru import logger

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "datos" / "memoria"
_LOG_FILE = _LOG_DIR / "audio_log.jsonl"


def registrar_evento(
    texto: str,
    clasificacion: str,
    duracion: float = 0.0,
    volumen: float = 0.0,
    no_speech_prob: float = 0.0,
    descartado: bool = False,
    motivo_descarte: str = "",
):
    """Registra un evento de audio en el log JSONL.

    clasificacion: "habla_propietario", "habla_otro", "ruido_corto",
                   "falso_positivo", "ruido_ambiente", "confirmacion"
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    evento = {
        "ts": datetime.datetime.now().isoformat(),
        "texto": texto[:200] if texto else "",
        "clasificacion": clasificacion,
        "duracion_s": round(duracion, 2),
        "volumen": round(volumen, 4),
        "no_speech_prob": round(no_speech_prob, 3),
        "descartado": descartado,
        "motivo": motivo_descarte,
    }
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.debug(f"Error escribiendo audio_log: {e}")


def resumen_audio_reciente(minutos: int = 30) -> str:
    """Resume los eventos de audio de los últimos N minutos."""
    if not _LOG_FILE.exists():
        return ""
    desde = datetime.datetime.now() - datetime.timedelta(minutes=minutos)
    eventos = []
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    ev = json.loads(linea)
                    ts = datetime.datetime.fromisoformat(ev["ts"])
                    if ts >= desde:
                        eventos.append(ev)
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                    continue
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
        return ""

    if not eventos:
        return ""

    # Contar por clasificación
    conteo = {}
    for ev in eventos:
        cls = ev.get("clasificacion", "desconocido")
        conteo[cls] = conteo.get(cls, 0) + 1

    lineas = [f"En los últimos {minutos} minutos he detectado:"]
    _ETIQUETAS = {
        "habla_propietario": "Habla suya",
        "habla_otro": "Habla de otra persona",
        "ruido_corto": "Ruidos cortos",
        "falso_positivo": "Falsos positivos filtrados",
        "ruido_ambiente": "Ruido ambiental",
        "confirmacion": "Confirmaciones",
    }
    for cls, n in conteo.items():
        etiqueta = _ETIQUETAS.get(cls, cls)
        lineas.append(f"  - {etiqueta}: {n}")

    # Últimas 5 detecciones con texto
    con_texto = [ev for ev in eventos if ev.get("texto")]
    if con_texto:
        lineas.append("Últimas detecciones:")
        for ev in con_texto[-5:]:
            hora = ev["ts"][11:16]
            lineas.append(f"  [{hora}] {ev['clasificacion']}: \"{ev['texto'][:60]}\"")

    return "\n".join(lineas)


