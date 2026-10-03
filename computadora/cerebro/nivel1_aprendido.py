"""
לֶמֶד (Lemed) — Letra del Aprendizaje.
Flujo ascendente en el Etz HaChaim: Tiféret/Keter → Malkut.

Gestiona patrones aprendidos de Nivel 2 (Ollama) y Nivel 3 (Copilot)
que se promueven a Nivel 1 (regex) para respuesta instantánea.
Persistidos en datos/nivel1_patrones.json.
"""

import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from loguru import logger

from computadora.habilidades.herramientas import RAIZ_PROYECTO

_PATRONES_PATH = Path(RAIZ_PROYECTO) / "datos" / "nivel1_patrones.json"

# Patrones regex peligrosos que causan backtracking catastrófico (ReDoS)
_REGEX_PELIGROSOS = re.compile(
    r"(\.\*){2}|(\.\+)\+|\([\.\+\*]+\)\+|\\[0-9]|\(\?\!|\(\?\<"
)

# Palabras funcionales que NO deben ser tokens de regex
_STOPWORDS = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "en", "a", "al", "por", "para", "con",
    "que", "qué", "como", "cómo", "es", "son", "está", "me",
    "mi", "tu", "su", "se", "le", "lo", "ya", "no", "sí",
    "y", "o", "pero", "más", "muy", "bien", "mal",
})

# Tipos de respuesta que se pueden promover
TIPOS_RESPUESTA = frozenset({
    "saludo", "atencion", "tool_simple", "dato_fijo", "conversacional",
})

# Herramientas "simples" que N1 puede ejecutar sin riesgo
_TOOLS_SIMPLES = frozenset({
    "abrir_aplicacion", "cerrar_aplicacion", "controlar_volumen",
    "obtener_fecha_hora", "leer_portapapeles", "tomar_captura_pantalla",
    "buscar_en_internet", "info_entorno",
})


class Nivel1Aprendido:
    """Gestor de patrones aprendidos para Nivel 1 (Malkut)."""

    UMBRAL_N2 = 0.7
    UMBRAL_N3 = 0.8
    MAX_PATRONES = 200

    def __init__(self):
        self._patrones: list[dict] = []
        self._compilados: dict[str, re.Pattern] = {}  # id → compiled regex
        self._cargar()

    # ── Persistencia ──

    def _cargar(self):
        """Carga patrones del archivo JSON."""
        try:
            if _PATRONES_PATH.exists():
                with open(_PATRONES_PATH, "r", encoding="utf-8") as f:
                    self._patrones = json.load(f)
                self._compilar_activos()
                logger.info(
                    f"Lemed: {len(self._patrones)} patrones cargados, "
                    f"{len(self._compilados)} activos"
                )
            else:
                self._patrones = []
                logger.info("Lemed: Sin patrones previos — aprendizaje desde cero")
        except Exception as e:
            logger.warning(f"Lemed: Error cargando patrones: {e}")
            self._patrones = []

    def _guardar(self):
        """Persiste patrones a JSON."""
        try:
            _PATRONES_PATH.parent.mkdir(parents=True, exist_ok=True)
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(_PATRONES_PATH, self._patrones)
        except Exception as e:
            logger.warning(f"Lemed: Error guardando patrones: {e}")

    def _compilar_activos(self):
        """Compila regex de patrones activos."""
        self._compilados.clear()
        for p in self._patrones:
            if p.get("activo") and p.get("regex"):
                try:
                    self._compilados[p["id"]] = re.compile(
                        p["regex"], re.IGNORECASE
                    )
                except re.error:
                    p["activo"] = False
                    logger.warning(f"Lemed: Regex inválido desactivado: {p['id']}")

    # ── Búsqueda ──

    def buscar_match(self, texto: str) -> dict | None:
        """Busca texto contra patrones activos. Retorna patrón o None."""
        texto_limpio = texto.strip()
        for pid, compiled in self._compilados.items():
            try:
                if compiled.search(texto_limpio):
                    patron = self._obtener(pid)
                    if patron:
                        return patron
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                continue
        return None

    # ── Registro de candidatos ──

    def registrar_candidato(
        self,
        texto_original: str,
        respuesta: str,
        nivel_origen: str,
        tool_info: dict | None = None,
    ):
        """Registra un candidato a patrón aprendido.

        Args:
            texto_original: Input del usuario
            respuesta: Respuesta generada por N2/N3
            nivel_origen: "nivel2" o "nivel3"
            tool_info: Si fue tool call, {"tool": nombre, "args": {}}
        """
        # Verificar si ya existe un patrón similar
        if self._patron_similar_existe(texto_original):
            logger.debug(f"Lemed: Patrón similar ya existe para '{texto_original[:50]}'")
            return

        # FP-016 Da'at: Intentar regex via Keter primero, fallback local
        regex = self._generar_regex_con_keter(texto_original)
        if regex:
            logger.info(f"Lemed: Regex via Keter → '{regex}'")
        else:
            regex = self._generar_regex_seguro(texto_original)
            if regex:
                logger.debug(f"Lemed: Regex template-based (fallback) → '{regex}'")

        if not regex:
            return

        if not self._validar_regex(regex):
            return

        # Determinar tipo de respuesta
        if tool_info:
            tipo = "tool_simple"
            template = tool_info
        elif len(respuesta.split()) < 15:
            tipo = "conversacional"
            template = respuesta
        else:
            logger.debug(f"Lemed: Respuesta demasiado larga para promover")
            return

        patron = {
            "id": str(uuid.uuid4())[:8],
            "regex": regex,
            "tipo_respuesta": tipo,
            "template_respuesta": template,
            "origen": nivel_origen,
            "confianza": 0.5,
            "activaciones": 0,
            "creado": datetime.now().isoformat(),
            "ejemplo_original": texto_original[:200],
            "activo": False,
        }

        self._patrones.append(patron)
        self._limpiar_exceso()
        self._guardar()
        logger.info(
            f"Lemed: Candidato registrado — '{texto_original[:50]}' → "
            f"tipo={tipo}, origen={nivel_origen}, regex='{regex}'"
        )

    # ── Retroalimentación ──

    def registrar_exito(self, patron_id: str):
        """Incrementa confianza de un patrón tras activación exitosa."""
        patron = self._obtener(patron_id)
        if not patron:
            return

        patron["confianza"] = round(min(1.0, patron["confianza"] + 0.1), 2)
        patron["activaciones"] += 1

        umbral = (
            self.UMBRAL_N3 if patron["origen"] == "nivel3" else self.UMBRAL_N2
        )
        if not patron["activo"] and patron["confianza"] >= umbral:
            patron["activo"] = True
            self._compilar_activos()
            logger.info(
                f"Lemed: Patrón PROMOVIDO a N1 — '{patron['ejemplo_original'][:50]}' "
                f"(confianza={patron['confianza']:.1f})"
            )

        self._guardar()

    def registrar_fallo(self, patron_id: str):
        """Decrementa confianza tras corrección del usuario."""
        patron = self._obtener(patron_id)
        if not patron:
            return

        patron["confianza"] = round(max(0.0, patron["confianza"] - 0.3), 2)

        if patron["confianza"] < 0.2:
            patron["activo"] = False
            if patron["id"] in self._compilados:
                del self._compilados[patron["id"]]
            logger.warning(
                f"Lemed: Patrón DESACTIVADO — '{patron['ejemplo_original'][:50]}' "
                f"(confianza={patron['confianza']:.1f})"
            )

        self._guardar()

    # ── Generación de regex ──

    def _generar_regex_con_keter(self, texto: str) -> str | None:
        """FP-016 Da'at: Pide a Copilot un regex mejorado.

        Usa pensar_codigo() (mejor modelo disponible).
        El prompt es controlado — texto truncado, sin metacaracteres.
        Retorna None si Copilot no disponible o regex inválido.
        """
        try:
            from computadora.cerebro.copilot_api import obtener_cerebro_copilot
            copilot = obtener_cerebro_copilot()

            if not copilot.esta_autenticado():
                return None

            # Sanitizar: truncar y limpiar
            texto_limpio = texto.strip()[:100]

            prompt = (
                "Genera UN regex Python (re.IGNORECASE) que matchee variaciones naturales de esta frase en español: "
                f"'{texto_limpio}'\n\n"
                "Reglas:\n"
                "- Usa \\b para word boundaries\n"
                "- Usa .* o \\s+ entre tokens (NO greedy excessivo)\n"
                "- Incluye variaciones con/sin acentos\n"
                "- NO uses (.*)+ ni (.+)+ ni backreferences\n"
                "- NO uses lookahead/lookbehind\n"
                "- Responde SOLO con el regex, sin explicación, sin backticks, sin comillas"
            )

            respuesta = copilot.pensar_codigo(prompt)
            if not respuesta:
                return None

            # Limpiar respuesta: quitar backticks, comillas, whitespace
            regex = respuesta.strip()
            regex = regex.strip('`').strip('"').strip("'").strip()
            # Si viene envuelto en r"..." o similar
            if regex.startswith('r"') or regex.startswith("r'"):
                regex = regex[2:-1]
            # Quitar líneas extra (solo primera línea)
            regex = regex.split('\n')[0].strip()

            if not regex or len(regex) > 300:
                return None

            # Validar seguridad
            if not self._validar_regex(regex):
                logger.warning(f"Lemed: Regex de Keter rechazado por validación: {regex}")
                return None

            # Test match: debe matchear el texto original
            try:
                if not re.search(regex, texto, re.IGNORECASE):
                    logger.warning(f"Lemed: Regex de Keter no matchea texto original: {regex}")
                    return None
            except re.error:
                return None

            return regex

        except Exception as e:
            logger.debug(f"Lemed: Keter no disponible para regex: {e}")
            return None

    def _generar_regex_seguro(self, texto: str) -> str | None:
        """Genera regex basado en tokens clave del texto.

        NO usa LLM. Extrae tokens significativos y los combina
        con word boundaries (\b) y espacios flexibles (\s+).
        """
        palabras = re.findall(r"[a-záéíóúñü]+", texto.lower())
        # Filtrar stopwords y palabras muy cortas
        tokens = [p for p in palabras if p not in _STOPWORDS and len(p) > 2]

        if not tokens:
            return None

        if len(tokens) == 1:
            # Patrón de una sola palabra clave
            return rf"\b{re.escape(tokens[0])}\b"

        if len(tokens) == 2:
            # Dos tokens: ambos deben estar presentes (en cualquier orden)
            t1, t2 = tokens
            return rf"\b{re.escape(t1)}\b.*\b{re.escape(t2)}\b"

        # 3+ tokens: tomar los 3 más largos (más distintitvos)
        tokens_sorted = sorted(tokens, key=len, reverse=True)[:3]
        # Ordenar por aparición original
        tokens_final = sorted(
            tokens_sorted,
            key=lambda t: texto.lower().index(t),
        )
        parts = [rf"\b{re.escape(t)}\b" for t in tokens_final]
        return r".*".join(parts)

    def _validar_regex(self, pattern: str) -> bool:
        """Valida que un regex sea compilable y seguro."""
        # Check anti-ReDoS
        if _REGEX_PELIGROSOS.search(pattern):
            logger.warning(f"Lemed: Regex rechazado (ReDoS risk): {pattern}")
            return False

        # Longitud razonable
        if len(pattern) > 300:
            logger.warning(f"Lemed: Regex rechazado (demasiado largo): {len(pattern)}")
            return False

        try:
            re.compile(pattern, re.IGNORECASE)
            return True
        except re.error as e:
            logger.warning(f"Lemed: Regex inválido: {pattern} — {e}")
            return False

    # ── Utilidades internas ──

    def _obtener(self, patron_id: str) -> dict | None:
        for p in self._patrones:
            if p["id"] == patron_id:
                return p
        return None

    def _patron_similar_existe(self, texto: str) -> bool:
        """Verifica si ya existe un patrón que matchee este texto."""
        for _, compiled in self._compilados.items():
            try:
                if compiled.search(texto.strip()):
                    return True
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                continue
        # También verificar candidatos no activos
        for p in self._patrones:
            if p.get("ejemplo_original", "").lower() == texto.lower().strip():
                return True
        return False

    def _limpiar_exceso(self):
        """Elimina patrones excedentes (FIFO por menos usado)."""
        if len(self._patrones) <= self.MAX_PATRONES:
            return

        # Ordenar por activaciones ascendente, luego por fecha más vieja
        self._patrones.sort(
            key=lambda p: (p.get("activaciones", 0), p.get("creado", ""))
        )
        # Eliminar los menos usados
        exceso = len(self._patrones) - self.MAX_PATRONES
        eliminados = self._patrones[:exceso]
        self._patrones = self._patrones[exceso:]

        # Recompilar activos
        self._compilar_activos()
        logger.info(f"Lemed: {len(eliminados)} patrones eliminados por FIFO")


