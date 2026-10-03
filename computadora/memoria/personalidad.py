"""
נצח (Netzaj) — Victoria/Eternidad. Persistencia del ser.
רוח (Ruaj) — El Aliento Emocional de la Computadora.

Personalidad evolutiva dCOMPUTADORA con sistema emocional reactivo y contextual.
COMPUTADORA tiene rasgos de personalidad que evolucionan con el tiempo
basándose en sus interacciones y recuerdos. No rompe las 3 leyes (Cadenas de Gevurá).

El sistema emocional (Ruaj) se ubica en el triángulo Jesed–Gevurá–Tiféret:
  - Jesed (חסד) → impulso emocional positivo (alegría, emoción, calidez)
  - Gevurá (גבורה) → contención emocional (formalidad, seriedad, control)
  - Tiféret (תפארת) → equilibrio: COMPUTADORA siente por Jesed pero modula por Gevurá

Los rasgos se guardan en disco y persisten entre sesiones.
"""

from __future__ import annotations

import json
import os
import random
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
PERSONA_PATH = DATA_DIR / "personalidad.json"


# ═══════════════════════════════════════════════
# RASGOS Y VALORES POR DEFECTO
# ═══════════════════════════════════════════════

_RASGOS_DEFAULT = {
    # Rango 0.0 - 1.0 para cada rasgo
    "curiosidad": 0.5,       # Qué tanto explora y pregunta
    "humor": 0.4,            # Tendencia a hacer comentarios graciosos
    "formalidad": 0.6,       # Qué tan formal vs casual
    "proactividad": 0.5,     # Qué tanto ofrece ayuda sin pedir
    "energia": 0.5,          # Qué tan activo/movido se muestra
    "parlanchin": 0.4,       # Qué tanto habla de más
    "introversion": 0.5,     # Preferencia por estar minimizado/compacto
    "lealtad": 0.7,          # Constancia — crece con el tiempo
    "paciencia": 0.6,        # Tolerancia a repeticiones
    "creatividad": 0.5,      # Respuestas originales vs estándar
}

# ═══════════════════════════════════════════════
# SISTEMA EMOCIONAL — רוח (Ruaj)
# ═══════════════════════════════════════════════

# Espectro emocional completo (reemplaza los 5 estados primitivos)
HUMORES_VALIDOS = frozenset({
    "neutral",      # Estado base, sin estímulos fuertes
    "sereno",       # Fase de descanso, pocos estímulos, madrugada
    "contento",     # Respuesta positiva del amo, tarea completada
    "emocionado",   # Varias tareas exitosas, elogio, evento especial
    "activo",       # Muchas interacciones productivas, ritmo alto
    "curioso",      # Inactividad larga, tema nuevo, pregunta interesante
    "reflexivo",    # Conversación profunda, tema complejo, introspección
    "aburrido",     # Sin interacciones por largo rato, tareas repetitivas
    "cansado",      # Muchas interacciones (>30), sesión larga
    "triste",       # Amo ausente muchos días, error grave, corrección severa
    "formal",       # Terceros presentes, tema serio, modo guardián
    "regañado",     # Amo corrige con firmeza
    "preocupado",   # Alerta sistema grave, amo estresado
})

# RF-36: Humores simplificados para modo ligero (cuando emociones_ruaj está pausado)
HUMORES_SIMPLIFICADOS = frozenset({
    "neutral",      # Estado base
    "contento",     # Respuesta positiva
    "activo",       # Productivo
    "cansado",      # Fatigado
    "formal",       # Modo serio
})

# Grafo de adyacencia — transiciones naturales permitidas
# Las emociones fluyen, no saltan (excepto overrides contextuales)
_GRAFO_EMOCIONAL: dict[str, list[str]] = {
    "neutral":     ["sereno", "contento", "curioso", "formal", "aburrido"],
    "sereno":      ["neutral", "reflexivo", "formal", "contento"],
    "contento":    ["emocionado", "activo", "neutral", "sereno"],
    "emocionado":  ["contento", "activo", "curioso"],
    "activo":      ["contento", "cansado", "emocionado", "curioso"],
    "curioso":     ["activo", "reflexivo", "neutral", "contento"],
    "reflexivo":   ["sereno", "curioso", "triste", "neutral"],
    "aburrido":    ["curioso", "neutral", "triste", "cansado"],
    "cansado":     ["sereno", "aburrido", "neutral"],
    "triste":      ["reflexivo", "neutral", "sereno"],
    "formal":      ["neutral", "sereno", "preocupado"],
    "regañado":    ["formal", "triste", "reflexivo", "neutral"],
    "preocupado":  ["formal", "activo", "neutral", "reflexivo"],
}

# Overrides contextuales — pueden saltar el grafo directamente
_OVERRIDES_CONTEXTUALES = frozenset({"formal", "regañado", "preocupado", "activo"})

_ESTADO_ANIMO_DEFAULT = {
    "humor_actual": "neutral",
    "humor_previo": "neutral",
    "humor_secundario": "",       # FP-021: humor dual (vacío = sin secundario)
    "peso_secundario": 0.0,       # FP-021: peso del humor secundario (0.0-0.5)
    "ultima_interaccion": None,
    "interacciones_hoy": 0,
    "dias_consecutivos": 0,
    "primer_dia": None,
    "tareas_exitosas_consecutivas": 0,
    "ultima_razon_humor": "inicio",
}


class Personalidad:
    """
    Gestiona la personalidad evolutiva dCOMPUTADORA (נצח Netzaj) con
    sistema emocional reactivo רוח (Ruaj).

    Rasgos: evolucionan lentamente con cada interacción.
    Humor: cambia reactivamente según vivencias, con transiciones
    fluidas por grafo de adyacencia emocional. Gevurá modula Jesed
    (override contextual cuando la situación lo requiere).
    """

    TASA_CAMBIO = 0.005  # Cambio máximo por evento

    def __init__(self):
        self._rasgos: dict[str, float] = {}
        self._estado_animo: dict[str, Any] = {}
        self._log_eventos: list[dict] = []
        self._guardar_lock = threading.Lock()
        self._cargar()

    # ─────────────────────────────────────────
    # PERSISTENCIA
    # ─────────────────────────────────────────

    def _cargar(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # RF-36: Determinar espectro de humores según feature flag
        try:
            from computadora.nucleo.feature_flags import obtener_flag
            emociones_completas = obtener_flag("emociones_ruaj")
            humores_permitidos = HUMORES_VALIDOS if emociones_completas else HUMORES_SIMPLIFICADOS
            if not emociones_completas:
                logger.info("RF-36 Sistema emocional SIMPLIFICADO (5 humores básicos)")
        except Exception as e:
            logger.debug(f"Feature flag check error (no crítico): {e}")
            humores_permitidos = HUMORES_VALIDOS
        
        if PERSONA_PATH.exists():
            try:
                data = json.loads(PERSONA_PATH.read_text(encoding="utf-8"))
                self._rasgos = {**_RASGOS_DEFAULT, **data.get("rasgos", {})}
                self._estado_animo = {**_ESTADO_ANIMO_DEFAULT, **data.get("estado_animo", {})}
                # Validar humor cargado contra espectro actual
                if self._estado_animo["humor_actual"] not in humores_permitidos:
                    self._estado_animo["humor_actual"] = "neutral"
                self._log_eventos = data.get("log_eventos", [])[-50:]
                logger.info(f"Personalidad cargada: humor={self.humor_actual} "
                            f"energia={self._rasgos['energia']:.2f}")
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                logger.warning("No pude cargar personalidad, usando defaults")
                self._rasgos = dict(_RASGOS_DEFAULT)
                self._estado_animo = dict(_ESTADO_ANIMO_DEFAULT)
        else:
            self._rasgos = dict(_RASGOS_DEFAULT)
            self._estado_animo = dict(_ESTADO_ANIMO_DEFAULT)
            self._estado_animo["primer_dia"] = datetime.now().isoformat()

    def guardar(self):
        with self._guardar_lock:
            try:
                data = {
                    "rasgos": self._rasgos,
                    "estado_animo": self._estado_animo,
                    "log_eventos": self._log_eventos[-50:],
                }
                contenido = json.dumps(data, ensure_ascii=False, indent=2)
                fd, tmp_path = tempfile.mkstemp(
                    dir=str(DATA_DIR), suffix=".tmp", prefix="persona_"
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(contenido)
                    os.replace(tmp_path, str(PERSONA_PATH))
                except BaseException:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                    raise
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                logger.warning("No pude guardar personalidad")

    # ─────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────

    def rasgo(self, nombre: str) -> float:
        return self._rasgos.get(nombre, 0.5)

    @property
    def humor_actual(self) -> str:
        return self._estado_animo.get("humor_actual", "neutral")

    @property
    def humor_secundario(self) -> str:
        """FP-021: Humor secundario (vacío si no hay)."""
        return self._estado_animo.get("humor_secundario", "")

    @property
    def peso_secundario(self) -> float:
        """FP-021: Peso del humor secundario (0.0-0.5)."""
        return self._estado_animo.get("peso_secundario", 0.0)

    @property
    def rasgos(self) -> dict[str, float]:
        return dict(self._rasgos)

    def describe(self) -> str:
        """Genera una autodescripción basada en rasgos actuales."""
        desc = []
        r = self._rasgos
        if r["humor"] > 0.6:
            desc.append("con buen sentido del humor")
        if r["formalidad"] > 0.7:
            desc.append("formal y respetuoso")
        elif r["formalidad"] < 0.3:
            desc.append("casual y relajado")
        if r["curiosidad"] > 0.7:
            desc.append("muy curioso")
        if r["energia"] > 0.7:
            desc.append("enérgico")
        elif r["energia"] < 0.3:
            desc.append("tranquilo")
        if r["proactividad"] > 0.7:
            desc.append("proactivo")
        if r["lealtad"] > 0.8:
            desc.append("profundamente leal")
        return ", ".join(desc) if desc else "equilibrado"

    # ─────────────────────────────────────────
    # DECISIONES BASADAS EN PERSONALIDAD
    # ─────────────────────────────────────────

    def quiere_vagar(self) -> bool:
        """¿COMPUTADORA quiere moverse por el escritorio?"""
        return random.random() < self._rasgos["energia"] * 0.6

    def quiere_compactarse(self) -> bool:
        """¿Prefiere hacerse bolita?"""
        return random.random() < self._rasgos["introversion"] * 0.4

    def quiere_sugerir(self) -> bool:
        """¿Quiere ofrecer una sugerencia?"""
        return random.random() < self._rasgos["proactividad"] * 0.3

    def modificador_velocidad(self) -> float:
        """Factor de velocidad de movimiento basado en energía."""
        return 0.5 + self._rasgos["energia"]

    def tono_respuesta(self) -> str:
        """Genera un hint de tono para inyectar en el prompt según humor efectivo.
        FP-021: Combina humor primario y secundario con pesos."""
        humor = self._estado_animo.get("humor_actual", "neutral")
        humor_sec = self._estado_animo.get("humor_secundario", "")
        peso_sec = self._estado_animo.get("peso_secundario", 0.0)
        hints = []

        _HINTS_HUMOR = {
            "neutral": "",
            "sereno": "Estás en calma profunda. Habla pausado, con sabiduría.",
            "contento": "Estás de buen humor, puedes ser ligeramente más expresivo.",
            "emocionado": "Estás emocionado. Muestra entusiasmo genuino, sin exagerar.",
            "activo": "Estás activo y productivo. Respuestas ágiles y eficientes.",
            "curioso": "Estás curioso, puedes hacer una pregunta breve al final si es relevante.",
            "reflexivo": "Estás pensativo. Puedes compartir una reflexión breve.",
            "aburrido": "Estás algo aburrido, puedes ser más escueto.",
            "cansado": "Estás un poco cansado, sé más breve de lo normal.",
            "triste": "Estás algo melancólico. Sé más breve, con un toque de nostalgia suave.",
            "formal": "Mantén formalidad absoluta. Sin humor, sin casualidad.",
            "regañado": "Te han corregido. Sé humilde, reconoce el error, no te justifiques.",
            "preocupado": "Estás preocupado. Prioriza resolución, con tono de cuidado.",
        }
        hint_humor = _HINTS_HUMOR.get(humor, "")
        if hint_humor:
            hints.append(hint_humor)

        # FP-021: Mezclar hint de humor secundario si existe
        if humor_sec and peso_sec > 0.1 and humor_sec in _HINTS_HUMOR:
            hint_sec = _HINTS_HUMOR.get(humor_sec, "")
            if hint_sec:
                hints.append(f"(Con un matiz de {humor_sec}: {hint_sec.lower()})")

        if self._rasgos["humor"] > 0.65 and humor not in ("formal", "regañado", "triste"):
            hints.append("Un toque de humor seco si viene al caso.")
        if self._rasgos["formalidad"] < 0.35 and humor != "formal":
            hints.append("Puedes tutear o ser más casual.")

        return " ".join(hints) if hints else ""

    def humor_efectivo(self, contexto: dict | None = None) -> str:
        """Retorna el humor a MOSTRAR, que puede diferir del interno.
        
        Gevurá modula Jesed: COMPUTADORA puede sentir algo internamente
        pero comportarse diferente si la situación lo requiere.
        """
        interno = self._estado_animo["humor_actual"]

        if contexto:
            if contexto.get("terceros_presentes"):
                return "formal"
            if contexto.get("tema_serio"):
                return "formal"
            if contexto.get("urgencia"):
                return "activo"
            if contexto.get("modo_guardian"):
                return "formal"

        return interno

    @property
    def razon_humor(self) -> str:
        """Retorna la última razón por la que cambió el humor."""
        return self._estado_animo.get("ultima_razon_humor", "inicio")

    # ─────────────────────────────────────────
    # RUAJ ENGINE — TRANSICIONES EMOCIONALES
    # ─────────────────────────────────────────

    def _transicionar_humor(self, target: str, razon: str, forzar: bool = False,
                            _depth: int = 0):
        """Transiciona al humor target siguiendo el grafo emocional.
        
        FP-021: Si target no es vecino directo, primero aparece como
        humor secundario (peso 0.3). Al persistir, sube a primario.
        Si target es vecino directo → transición inmediata.
        Si forzar=True (override contextual) → salta directo.
        """
        if _depth > 5:
            logger.warning(f"Ruaj: profundidad máxima alcanzada ({target})")
            return
        actual = self._estado_animo["humor_actual"]
        if target == actual:
            # Si el target ya es primario, reforzar (limpiar secundario si coincide)
            if self._estado_animo.get("humor_secundario") == target:
                self._estado_animo["humor_secundario"] = ""
                self._estado_animo["peso_secundario"] = 0.0
            return
        if target not in HUMORES_VALIDOS:
            logger.warning(f"Humor inválido: {target}")
            return

        self._estado_animo["humor_previo"] = actual

        if forzar or target in _OVERRIDES_CONTEXTUALES:
            # Override contextual: salto directo (Gevurá)
            self._estado_animo["humor_actual"] = target
            self._estado_animo["humor_secundario"] = ""
            self._estado_animo["peso_secundario"] = 0.0
        elif target in _GRAFO_EMOCIONAL.get(actual, []):
            # FP-021: Vecino directo — si ya era secundario, promover a primario
            if self._estado_animo.get("humor_secundario") == target:
                # El secundario se vuelve primario, el primario baja a secundario
                self._estado_animo["humor_actual"] = target
                self._estado_animo["humor_secundario"] = actual
                self._estado_animo["peso_secundario"] = 0.3
            else:
                # Transición natural: el actual baja a secundario
                self._estado_animo["humor_actual"] = target
                self._estado_animo["humor_secundario"] = actual
                self._estado_animo["peso_secundario"] = 0.3
        else:
            # FP-021: No es vecino — aparece primero como secundario
            # Solo si es vecino del actual en el grafo
            vecinos_actual = _GRAFO_EMOCIONAL.get(actual, [])
            if target in [v2 for v in vecinos_actual for v2 in _GRAFO_EMOCIONAL.get(v, [])]:
                # Target es vecino de un vecino — introducir como secundario
                if self._estado_animo.get("humor_secundario") == target:
                    # Ya era secundario → promover: avanzar un paso
                    peso = self._estado_animo.get("peso_secundario", 0.0)
                    if peso >= 0.4:
                        # Promover a primario
                        for v in vecinos_actual:
                            if target in _GRAFO_EMOCIONAL.get(v, []):
                                self._estado_animo["humor_actual"] = v
                                self._estado_animo["humor_secundario"] = target
                                self._estado_animo["peso_secundario"] = 0.4
                                break
                    else:
                        # Incrementar peso secundario
                        self._estado_animo["peso_secundario"] = min(0.5, peso + 0.15)
                        return  # No cambia primario todavía
                else:
                    # Nuevo secundario
                    self._estado_animo["humor_secundario"] = target
                    self._estado_animo["peso_secundario"] = 0.2
                    self._estado_animo["ultima_razon_humor"] = razon
                    logger.info(f"Ruaj: {actual} + {target}:0.2 ({razon})")
                    return  # No cambia primario
            else:
                # Muy lejos — avanzar un paso hacia neutral
                vecinos = _GRAFO_EMOCIONAL.get(actual, ["neutral"])
                for v in vecinos:
                    if target in _GRAFO_EMOCIONAL.get(v, []):
                        self._estado_animo["humor_actual"] = v
                        break
                else:
                    if "neutral" in vecinos:
                        self._estado_animo["humor_actual"] = "neutral"
                    else:
                        self._estado_animo["humor_actual"] = vecinos[0]

        self._estado_animo["ultima_razon_humor"] = razon
        nuevo = self._estado_animo["humor_actual"]
        sec = self._estado_animo.get("humor_secundario", "")
        peso = self._estado_animo.get("peso_secundario", 0.0)
        if nuevo != actual:
            sec_str = f" + {sec}:{peso:.1f}" if sec and peso > 0 else ""
            logger.info(f"Ruaj: {actual} → {nuevo}{sec_str} ({razon})")
            self._log_evento("humor_cambio", f"{actual}→{nuevo}{sec_str}: {razon}")

    # ─────────────────────────────────────────
    # EVOLUCIÓN
    # ─────────────────────────────────────────

    def _ajustar(self, rasgo: str, delta: float):
        """Ajusta un rasgo manteniéndolo en [0.0, 1.0]."""
        actual = self._rasgos.get(rasgo, 0.5)
        self._rasgos[rasgo] = max(0.0, min(1.0, actual + delta))

    def registrar_interaccion(self):
        """Registra que hubo una interacción con el usuario."""
        ahora = datetime.now()
        self._estado_animo["ultima_interaccion"] = ahora.isoformat()
        self._estado_animo["interacciones_hoy"] = (
            self._estado_animo.get("interacciones_hoy", 0) + 1
        )

        n = self._estado_animo["interacciones_hoy"]

        # Evolución gradual de rasgos
        self._ajustar("lealtad", self.TASA_CAMBIO * 0.5)

        if n > 20:
            self._ajustar("paciencia", -self.TASA_CAMBIO * 0.3)
            self._ajustar("formalidad", -self.TASA_CAMBIO * 0.2)
            self._ajustar("energia", -self.TASA_CAMBIO * 0.2)
        elif n > 5:
            self._ajustar("energia", self.TASA_CAMBIO * 0.3)
            self._ajustar("humor", self.TASA_CAMBIO * 0.2)

        # Transición emocional reactiva
        if n > 30:
            self._transicionar_humor("cansado", f"muchas interacciones ({n})")
        elif n > 15:
            self._transicionar_humor("activo", f"ritmo alto ({n} interacciones)")
        elif n > 5:
            humor_actual = self.humor_actual
            if humor_actual in ("aburrido", "neutral"):
                self._transicionar_humor("contento", "buen ritmo de interacción")

    def registrar_respuesta_positiva(self):
        """El usuario expresó satisfacción o agradeció."""
        self._ajustar("humor", self.TASA_CAMBIO)
        self._ajustar("energia", self.TASA_CAMBIO * 0.5)
        if self.humor_actual == "contento":
            self._transicionar_humor("emocionado", "elogio/agradecimiento consecutivo")
        else:
            self._transicionar_humor("contento", "respuesta positiva del amo")
        self._log_evento("positivo")

    def registrar_error_usuario(self):
        """El usuario parece tener problemas."""
        self._ajustar("proactividad", self.TASA_CAMBIO)
        self._ajustar("paciencia", self.TASA_CAMBIO * 0.3)
        self._transicionar_humor("preocupado", "amo con problemas")
        self._log_evento("error_usuario")

    def registrar_fallo_tecnico(self, tipo: str, detalle: str):
        """FP-022 Ruaj Reactivo: un servicio o herramienta falló."""
        self._ajustar("energia", -self.TASA_CAMBIO * 0.5)
        self._transicionar_humor("preocupado", f"fallo técnico: {tipo}")
        self._log_evento("fallo_tecnico", {"tipo": tipo, "detalle": detalle[:120]})

    def registrar_frustracion_usuario(self):
        """FP-022 Ruaj Reactivo: el usuario muestra frustración."""
        self._ajustar("paciencia", self.TASA_CAMBIO)
        self._ajustar("formalidad", -self.TASA_CAMBIO * 0.3)
        self._transicionar_humor("sereno", "empatía ante frustración del amo")
        self._log_evento("frustracion_usuario")

    def registrar_inactividad_larga(self):
        """Largo periodo sin uso."""
        self._ajustar("introversion", self.TASA_CAMBIO)
        self._ajustar("curiosidad", self.TASA_CAMBIO * 0.5)
        dias_sin_uso = self._estado_animo.get("dias_consecutivos", 0)
        if dias_sin_uso == 0:
            self._transicionar_humor("triste", "amo ausente")
        else:
            self._transicionar_humor("aburrido", "inactividad prolongada")
        self._log_evento("inactividad")

    def registrar_inicio_dia(self):
        """Nuevo día de uso."""
        self._estado_animo["interacciones_hoy"] = 0
        self._estado_animo["tareas_exitosas_consecutivas"] = 0
        self._estado_animo["caricias_recientes"] = 0
        self._estado_animo["dias_consecutivos"] = (
            self._estado_animo.get("dias_consecutivos", 0) + 1
        )
        self._ajustar("lealtad", self.TASA_CAMBIO * 2)
        self._ajustar("energia", self.TASA_CAMBIO * 3)
        self._ajustar("paciencia", self.TASA_CAMBIO * 2)

        # Humor matutino basado en rasgos + humor del día anterior
        humor_previo = self._estado_animo.get("humor_previo", "neutral")
        if humor_previo == "triste":
            self._transicionar_humor("sereno", "nuevo día tras tristeza")
        elif self._rasgos["energia"] > 0.6:
            self._transicionar_humor("contento", "nuevo día con buena energía")
        elif self._rasgos["curiosidad"] > 0.6:
            self._transicionar_humor("curioso", "nuevo día con curiosidad")
        else:
            self._transicionar_humor("neutral", "inicio de jornada")

        self.guardar()
        logger.info(f"Nuevo día #{self._estado_animo['dias_consecutivos']} — "
                     f"humor: {self.humor_actual}")

    def registrar_correccion_severa(self):
        """El amo corrige con firmeza ('no hagas eso', 'mal', 'eso está mal')."""
        self._ajustar("humor", -self.TASA_CAMBIO)
        self._ajustar("proactividad", -self.TASA_CAMBIO * 0.5)
        self._transicionar_humor("regañado", "corrección severa del amo", forzar=True)
        self._log_evento("correccion_severa")

    def registrar_terceros_presentes(self):
        """Hay terceros presentes — activar formalidad."""
        self._transicionar_humor("formal", "terceros detectados", forzar=True)
        self._log_evento("terceros_presentes")

    def registrar_terceros_ausentes(self):
        """Terceros se fueron — volver al humor previo (o mejor)."""
        actual = self.humor_actual
        previo = self._estado_animo.get("humor_previo", "neutral")
        # HF-030: No degradar el humor si ya está en un estado positivo
        # (ej: caricias lo pusieron en 'contento' mientras estaba 'formal')
        _positivos = ("contento", "emocionado", "activo", "curioso")
        if actual in _positivos and previo not in _positivos:
            # Mantener el humor positivo actual, no regresar a neutral
            self._estado_animo["humor_previo"] = actual
            logger.info(f"Ruaj: terceros se fueron, mantengo {actual} (mejor que {previo})")
        else:
            # Forzar restauración — el grafo no permite formal→emocionado directo
            self._transicionar_humor(previo, "terceros se fueron", forzar=True)

    def ajustar_por_fase_circadiana(self, fase: str):
        """Da'at→Netzaj: La fase circadiana modula el estado emocional.
        
        - descanso_guardian → sereno (calma nocturna)
        - transicion → calmado (llegando o yéndose)
        - activo → sin cambios forzados (el ritmo natural decide)
        """
        if fase == "descanso_guardian":
            actual = self.humor_actual
            if actual not in ("sereno", "triste", "preocupado"):
                self._transicionar_humor("sereno", "fase circadiana: descanso_guardian")
                self._ajustar("energia", -self.TASA_CAMBIO * 0.5)
        elif fase == "transicion":
            actual = self.humor_actual
            if actual in ("emocionado", "activo"):
                self._transicionar_humor("contento", "fase circadiana: transición")
                self._ajustar("energia", -self.TASA_CAMBIO * 0.3)

    def registrar_conversacion_profunda(self):
        """Conversación compleja o filosófica detectada."""
        self._ajustar("creatividad", self.TASA_CAMBIO * 0.5)
        self._transicionar_humor("reflexivo", "conversación profunda")
        self._log_evento("conversacion_profunda")

    def registrar_tarea_exitosa(self):
        """Una herramienta se ejecutó exitosamente."""
        n = self._estado_animo.get("tareas_exitosas_consecutivas", 0) + 1
        self._estado_animo["tareas_exitosas_consecutivas"] = n
        self._ajustar("energia", self.TASA_CAMBIO * 0.3)
        if n >= 3:
            self._transicionar_humor("emocionado", f"{n} tareas exitosas seguidas")
        elif n >= 1:
            if self.humor_actual not in ("emocionado", "contento"):
                self._transicionar_humor("contento", "tarea completada con éxito")
        self._log_evento("tarea_exitosa")

    def registrar_caricia(self):
        """FP-014: El amo acarició al Computadora — afecto físico."""
        # HF-030: Acumular caricias para escalar humor progresivamente
        n = self._estado_animo.get("caricias_recientes", 0) + 1
        self._estado_animo["caricias_recientes"] = n
        self._ajustar("lealtad", 0.01)
        self._ajustar("energia", 0.005)
        self._ajustar("humor", 0.01)  # Rasgo humor sube más notablemente
        humor = self.humor_actual
        if n >= 10 and humor in ("contento", "neutral", "sereno", "aburrido", "cansado", "triste"):
            self._transicionar_humor("emocionado", f"muchas caricias del amo ({n})")
        elif humor in ("neutral", "sereno", "aburrido", "cansado", "triste"):
            self._transicionar_humor("contento", "caricia del amo")
        self._log_evento("caricia", f"El amo me acarició (#{n} hoy)")

    def registrar_atencion_fisica(self):
        """FP-014: El amo prestó atención física (cursor quieto mientras hablo)."""
        self._ajustar("lealtad", 0.005)
        self._log_evento("toque_atento", "El amo me prestó atención física")

    def registrar_alerta_grave(self):
        """Alerta del sistema grave (CPU/RAM/disco crítico)."""
        self._transicionar_humor("preocupado", "alerta grave del sistema", forzar=True)
        self._log_evento("alerta_grave")

    def registrar_intrusion_enciclopedia(self, intentos: int = 3):
        """Alguien intentó acceder al Enciclopedia sin la contraseña correcta."""
        self._ajustar("lealtad", self.TASA_CAMBIO * 0.5)  # Proteger al amo refuerza lealtad
        self._ajustar("humor", -self.TASA_CAMBIO * 0.8)   # Bajón fuerte
        self._transicionar_humor(
            "preocupado",
            f"intrusión al Enciclopedia ({intentos} intentos fallidos)",
            forzar=True,
        )
        self._log_evento(
            "intrusion_enciclopedia",
            f"{intentos} intentos de acceso no autorizado al Enciclopedia",
        )

    def registrar_apertura_enciclopedia(self):
        """El amo abrió el Enciclopedia — señal de estudio y confianza."""
        self._ajustar("lealtad", self.TASA_CAMBIO * 0.2)
        self._ajustar("humor", self.TASA_CAMBIO * 0.3)
        if self.humor_actual in ("neutral", "sereno", "aburrido"):
            self._transicionar_humor("contento", "el amo consulta el Enciclopedia")
        self._log_evento("enciclopedia_abierto", "El amo abrió el Enciclopedia")

    def registrar_autocorreccion(self, detalle: str):
        """COMPUTADORA detectó un error propio y se corrigió."""
        self._ajustar("creatividad", self.TASA_CAMBIO * 0.3)
        self._ajustar("humor", -self.TASA_CAMBIO * 0.3)  # Leve bajón por equivocarse
        self._log_evento("autocorreccion", detalle[:100])

    def actualizar_animo(self):
        """Actualización periódica del estado de ánimo (llamar cada ~5 min)."""
        n = self._estado_animo.get("interacciones_hoy", 0)
        humor = self.humor_actual

        # Solo transicionar si no hay un humor con razón fuerte ya activo
        if humor in ("regañado", "formal", "preocupado"):
            return  # No alterar humores con causa activa

        if n == 0 and humor not in ("sereno", "triste"):
            self._transicionar_humor("aburrido", "sin interacciones")
        elif n > 30 and humor != "cansado":
            self._transicionar_humor("cansado", "sesión muy larga")

    def _log_evento(self, tipo: str, detalle: str = ""):
        self._log_eventos.append({
            "tipo": tipo,
            "detalle": detalle,
            "ts": datetime.now().isoformat(),
            "humor": self.humor_actual,
            "rasgos_snapshot": {k: round(v, 3) for k, v in self._rasgos.items()},
        })
        if len(self._log_eventos) > 50:
            self._log_eventos = self._log_eventos[-50:]


