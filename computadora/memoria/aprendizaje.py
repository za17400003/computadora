"""
גבורה+יסוד — Sigilo de Contención (חותם הכלה). Sello #10.
Aprendizaje de Errores — Memoria de fallos y lecciones aprendidas.

COMPUTADORA sella sus errores para no repetirlos. Cada fallo se registra,
cada lección se inyecta en el prompt de Ollama (Biná → Tiféret).
"""

import json
import os
import time
from loguru import logger


ARCHIVO_ERRORES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "datos", "errores_aprendidos.json"
)
MAX_REGISTROS = 100


class MemoriaErrores:
    """Registra errores y lecciones aprendidas para no repetirlos."""

    def __init__(self):
        self._errores: list[dict] = self._cargar()

    def registrar_error(self, contexto: str, accion: str, error: str, correccion: str = ""):
        """Registra un error con contexto."""
        registro = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "contexto": contexto[:200],
            "accion_fallida": accion[:200],
            "error": error[:300],
            "correccion": correccion[:200],
            "leccion": "",
        }

        # Si hay corrección, generar lección automática
        if correccion:
            registro["leccion"] = f"Cuando intento '{accion[:50]}': {correccion[:150]}"

        self._errores.append(registro)

        # FIFO: mantener máximo MAX_REGISTROS
        if len(self._errores) > MAX_REGISTROS:
            self._errores = self._errores[-MAX_REGISTROS:]

        self._guardar()
        logger.debug(f"Error registrado: {accion[:50]} → {error[:50]}")

    def registrar_correccion(self, correccion: str):
        """El usuario corrigió a Computadora — asociar con el último error."""
        if not self._errores:
            # No hay error previo, registrar como lección genérica
            self._errores.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M"),
                "contexto": "corrección del usuario",
                "accion_fallida": "",
                "error": "",
                "correccion": correccion[:200],
                "leccion": correccion[:200],
            })
        else:
            ultimo = self._errores[-1]
            ultimo["correccion"] = correccion[:200]
            ultimo["leccion"] = correccion[:200]

        self._guardar()
        logger.debug(f"Corrección registrada: {correccion[:50]}")

    def consultar_relevantes(self, accion_actual: str, n: int = 5) -> list[dict]:
        """Busca errores pasados relevantes a la acción actual."""
        if not self._errores or not accion_actual:
            return []

        palabras = set(accion_actual.lower().split())
        scored = []
        for e in self._errores:
            if not e.get("leccion") and not e.get("correccion"):
                continue
            texto_error = f"{e.get('accion_fallida', '')} {e.get('contexto', '')}".lower()
            palabras_error = set(texto_error.split())
            coincidencias = len(palabras & palabras_error)
            if coincidencias > 0:
                scored.append((coincidencias, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:n]]

    def generar_hint_prompt(self, accion_actual: str) -> str:
        """Genera texto para inyectar en el prompt de Ollama."""
        relevantes = self.consultar_relevantes(accion_actual, n=3)
        if not relevantes:
            return ""

        lecciones = []
        for e in relevantes:
            leccion = e.get("leccion") or e.get("correccion", "")
            if leccion:
                lecciones.append(f"- {leccion}")

        if not lecciones:
            return ""

        return "LECCIONES APRENDIDAS (errores pasados, no repetir):\n" + "\n".join(lecciones)

    @property
    def total_errores(self) -> int:
        return len(self._errores)

    def _cargar(self) -> list[dict]:
        """Carga el registro de errores."""
        try:
            path = os.path.normpath(ARCHIVO_ERRORES)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f"No se pudo cargar errores: {e}")
        return []

    def _guardar(self):
        """Persiste el registro de errores."""
        try:
            path = os.path.normpath(ARCHIVO_ERRORES)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(path, self._errores)
        except Exception as e:
            logger.debug(f"No se pudo guardar errores: {e}")


