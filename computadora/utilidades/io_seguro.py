"""
FP-037 כְּתִיבָה אָטוֹמִית Ketivá Atomit — Escritura Atómica de Datos (RF-100)

Función para escritura atómica de JSON a disco usando tempfile + os.replace.
Previene corrupción si el proceso crashea mid-write.
Patrón canónico tomado de personalidad.py (FP-023 WI-111).
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def escribir_json_atomico(ruta: Path | str, datos: Any, *, indent: int = 2, ensure_ascii: bool = False) -> None:
    """Escribe datos JSON a disco de forma atómica.

    Usa tempfile.mkstemp() + os.replace() para garantizar que el archivo
    final siempre es válido, incluso si el proceso crashea mid-write.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=str(ruta.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=ensure_ascii, indent=indent)
        os.replace(tmp_path, str(ruta))
    except BaseException:
        # Limpiar temp file si algo falla
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


