"""
לשון הלב Lashón HaLev — Perfil Idioléctico del Amo (RF-233)
Sefirá: Netzaj (נצח) — Persistencia + Tiféret (תפארת) — Equilibrio conversacional
Sendero 24: Netzaj↔Tiféret — la persistencia alimenta el equilibrio.

Aprende cómo habla el amo: muletillas, estilo de petición, longitud,
verbos imperativos, bigramas frecuentes, temas recurrentes.
Genera un hint compacto (~40 tokens) para inyectar en el system prompt
de Ollama, mejorando comprensión y fluidez con cada interacción.
"""
from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from pathlib import Path

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_PERFIL_PATH = _DATOS_DIR / "perfil_linguistico.json"

# ── Muletillas comunes en español mexicano ──
_RE_MULETILLAS = re.compile(
    r"\b(oye|mira|dale|este|pues|bueno|o\s+sea|"
    r"la\s+neta|la\s+verdad|sabes|fíjate|onda|"
    r"ajá|verdad|entonces|neta|como\s+que|"
    r"tipo|ándale|órale|va|sale|simón|nel|"
    r"chido|nah|wey|güey|no\s+mames|chale)\b",
    re.IGNORECASE,
)

# ── Verbos imperativos (órdenes directas) ──
_RE_IMPERATIVOS = re.compile(
    r"\b(abre|cierra|busca|pon|quita|hazme|haz|dime|muéstrame|"
    r"ejecuta|corre|instala|borra|crea|modifica|cambia|edita|"
    r"lee|escribe|sube|baja|activa|desactiva|apaga|prende|"
    r"encuentra|analiza|revisa|checa|agrega|añade|elimina)\b",
    re.IGNORECASE,
)

# ── Clasificación de estilo de petición ──
_RE_CORTES = re.compile(
    r"\b(podr[ií]as|ser[ií]a\s+posible|te\s+importar[ií]a|"
    r"por\s+favor|cuando\s+puedas|si\s+no\s+es\s+mucha?\s+molestia|"
    r"me\s+har[ií]as\s+el\s+favor)\b",
    re.IGNORECASE,
)
_RE_IMPLICITO = re.compile(
    r"\b(necesito|quiero|me\s+gustar[ií]a|estaría\s+bien|"
    r"no\s+estar[ií]a\s+mal|sería\s+bueno)\b",
    re.IGNORECASE,
)

# ── Temas por keywords ──
_TEMAS_KEYWORDS: dict[str, list[str]] = {
    "tecnología": ["código", "programar", "python", "script", "bug", "error", "servidor", "api", "git"],
    "sistema": ["archivo", "carpeta", "disco", "ram", "cpu", "proceso", "windows", "volumen"],
    "personal": ["familia", "mamá", "papá", "hermano", "amigo", "novia", "salud", "dormir"],
    "entretenimiento": ["película", "música", "juego", "serie", "video", "youtube", "canción"],
    "trabajo": ["proyecto", "tarea", "deadline", "reunión", "cliente", "jefe", "oficina"],
    "computadora": ["computadora", "copilot", "mejorar", "tikun", "demo", "orbe", "voz", "escucha"],
}

# Stopwords para no contaminar bigramas
_STOPWORDS = frozenset(
    "de la el los las un una unos unas del al a en con por para que es y o no"
    " si se su lo le me te mi tu nos les el ella ellos yo tú él".split()
)

_MAX_INTERACCIONES = 50


class PerfilLinguistico:
    """Modelo dinámico adaptativo del idiolecto del amo."""

    def __init__(self):
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        self._perfil = self._cargar()
        logger.info(
            f"PerfilLinguistico: {self._perfil.get('interacciones_analizadas', 0)} "
            f"interacciones previas"
        )

    # ── Persistencia ──

    def _cargar(self) -> dict:
        if _PERFIL_PATH.exists():
            try:
                return json.loads(_PERFIL_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"PerfilLinguistico: error cargando → reset: {e}")
        return self._perfil_vacio()

    @staticmethod
    def _perfil_vacio() -> dict:
        return {
            "muletillas": {},
            "estilo_predominante": "directo",
            "longitud_media_palabras": 0.0,
            "bigramas_top": [],
            "temas_frecuentes": {},
            "verbos_imperativos": {},
            "interacciones_analizadas": 0,
            "ultima_optimizacion": None,
            "_longitud_acum": 0.0,
        }

    def _guardar(self):
        try:
            _DATOS_DIR.mkdir(parents=True, exist_ok=True)
            tmp = _PERFIL_PATH.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self._perfil, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(_PERFIL_PATH)
        except Exception as e:
            logger.warning(f"PerfilLinguistico: error guardando: {e}")

    # ── Análisis por interacción ──

    def registrar_interaccion(self, texto_usuario: str):
        """Analiza un input del amo y acumula estadísticas."""
        if not texto_usuario or len(texto_usuario) < 3:
            return

        texto = texto_usuario.strip()
        palabras = texto.split()
        n_palabras = len(palabras)

        # 1. Muletillas
        for m in _RE_MULETILLAS.finditer(texto):
            key = m.group(1).lower().strip()
            self._perfil["muletillas"][key] = self._perfil["muletillas"].get(key, 0) + 1

        # 2. Verbos imperativos
        for m in _RE_IMPERATIVOS.finditer(texto):
            key = m.group(1).lower()
            self._perfil["verbos_imperativos"][key] = (
                self._perfil["verbos_imperativos"].get(key, 0) + 1
            )

        # 3. Longitud media (media móvil incremental)
        n = self._perfil["interacciones_analizadas"]
        acum = self._perfil.get("_longitud_acum", 0.0)
        acum += n_palabras
        self._perfil["_longitud_acum"] = acum
        self._perfil["longitud_media_palabras"] = round(acum / (n + 1), 1)

        # 4. Estilo de petición
        if _RE_CORTES.search(texto):
            estilo = "cortés"
        elif _RE_IMPLICITO.search(texto):
            estilo = "implícito"
        else:
            estilo = "directo"
        # Acumular votos
        votos = self._perfil.get("_estilos_votos", {"directo": 0, "cortés": 0, "implícito": 0})
        votos[estilo] = votos.get(estilo, 0) + 1
        self._perfil["_estilos_votos"] = votos
        self._perfil["estilo_predominante"] = max(votos, key=votos.get)

        # 5. Bigramas (excluyendo stopwords)
        tokens = [w.lower() for w in palabras if w.lower() not in _STOPWORDS and len(w) > 2]
        bigramas_nuevos = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        bigramas_acum = Counter(dict(self._perfil.get("_bigramas_counter", {})))
        bigramas_acum.update(bigramas_nuevos)
        self._perfil["_bigramas_counter"] = dict(bigramas_acum)
        self._perfil["bigramas_top"] = [
            list(bg) for bg in bigramas_acum.most_common(10)
        ]

        # 6. Temas
        texto_lower = texto.lower()
        for tema, keywords in _TEMAS_KEYWORDS.items():
            if any(kw in texto_lower for kw in keywords):
                self._perfil["temas_frecuentes"][tema] = (
                    self._perfil["temas_frecuentes"].get(tema, 0) + 1
                )

        self._perfil["interacciones_analizadas"] = n + 1

        # Guardar cada 5 interacciones (no en cada una para no saturar disco)
        if (n + 1) % 5 == 0:
            self._guardar()

    # ── Generación de hint para Ollama ──

    def generar_hint_linguistico(self) -> str | None:
        """Genera bloque compacto (~40 tokens) para system_msgs.

        Retorna None si no hay datos suficientes (<10 interacciones).
        """
        n = self._perfil.get("interacciones_analizadas", 0)
        if n < 10:
            return None

        partes = [f"IDIOLECTO AMO ({n} muestras):"]

        # Estilo
        estilo = self._perfil.get("estilo_predominante", "directo")
        partes.append(f"Estilo: {estilo}.")

        # Longitud media
        lng = self._perfil.get("longitud_media_palabras", 0)
        if lng > 0:
            partes.append(f"Frases ~{lng:.0f} palabras.")

        # Top 3 muletillas
        muletillas = self._perfil.get("muletillas", {})
        if muletillas:
            top3 = sorted(muletillas, key=muletillas.get, reverse=True)[:3]
            partes.append(f"Muletillas: {', '.join(top3)}.")

        # Top 3 imperativos
        imperativos = self._perfil.get("verbos_imperativos", {})
        if imperativos:
            top3 = sorted(imperativos, key=imperativos.get, reverse=True)[:3]
            partes.append(f"Verbos frecuentes: {', '.join(top3)}.")

        # Top 2 temas
        temas = self._perfil.get("temas_frecuentes", {})
        if temas:
            top2 = sorted(temas, key=temas.get, reverse=True)[:2]
            partes.append(f"Temas: {', '.join(top2)}.")

        return " ".join(partes)

    # ── Optimización Tikún ──

    def optimizar_en_tikun(self) -> str:
        """Llamado por meta_workflow durante ciclo Tikún.

        Compacta estadísticas, recalcula promedios, emite resumen.
        """
        n = self._perfil.get("interacciones_analizadas", 0)
        if n < 5:
            return "PerfilLinguístico: <5 interacciones, sin datos para optimizar."

        # Podar muletillas con <2 ocurrencias
        muletillas = self._perfil.get("muletillas", {})
        self._perfil["muletillas"] = {k: v for k, v in muletillas.items() if v >= 2}

        # Podar imperativos con <2 ocurrencias
        imperativos = self._perfil.get("verbos_imperativos", {})
        self._perfil["verbos_imperativos"] = {k: v for k, v in imperativos.items() if v >= 2}

        # Podar bigramas con <2 ocurrencias
        bigramas = self._perfil.get("_bigramas_counter", {})
        self._perfil["_bigramas_counter"] = {k: v for k, v in bigramas.items() if v >= 2}
        counter = Counter(self._perfil["_bigramas_counter"])
        self._perfil["bigramas_top"] = [list(bg) for bg in counter.most_common(10)]

        # Podar temas con <2 ocurrencias
        temas = self._perfil.get("temas_frecuentes", {})
        self._perfil["temas_frecuentes"] = {k: v for k, v in temas.items() if v >= 2}

        self._perfil["ultima_optimizacion"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._guardar()

        # Resumen
        top_muletilla = max(self._perfil["muletillas"], key=self._perfil["muletillas"].get) if self._perfil["muletillas"] else "ninguna"
        top_tema = max(self._perfil["temas_frecuentes"], key=self._perfil["temas_frecuentes"].get) if self._perfil["temas_frecuentes"] else "ninguno"

        resumen = (
            f"PerfilLinguístico optimizado: {n} interacciones, "
            f"estilo={self._perfil['estilo_predominante']}, "
            f"muletilla top='{top_muletilla}', "
            f"tema top='{top_tema}', "
            f"longitud media={self._perfil['longitud_media_palabras']:.1f} palabras."
        )
        logger.info(resumen)
        return resumen

    def flush(self):
        """Fuerza escritura a disco."""
        self._guardar()


