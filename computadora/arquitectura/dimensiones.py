"""
עולמות שלמים — Olamot Shlemím — Arquitectura Multidimensional Completa
FP-087 · FP-092 · RF-317 / RF-318 / RF-319 / RF-322

16 Olamot — 59 módulos de COMPUTADORA
a través de la cosmología COMPLETA de una tradición. No son skins:
cada dimensión reorganiza cómo COMPUTADORA entiende su propia arquitectura
según el sistema esotérico real de cada tradición.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Rutas ───────────────────────────────────────────────────
_RAIZ = Path(__file__).resolve().parent.parent.parent
_ARCHIVO_ESTADO = _RAIZ / "datos" / "dimensiones.json"


# ── Estructuras ─────────────────────────────────────────────
@dataclass(frozen=True)
class Nodo:
    """Un nodo dentro de un mapa cósmico (equivalente a una Sefirá)."""
    nombre: str
    original: str           # Nombre en lengua original
    sefirot_equiv: str      # Sefirá equivalente en Etz HaChaim
    modulos: tuple[str, ...] = ()
    descripcion: str = ""


@dataclass(frozen=True)
class Camino:
    """Conexión entre dos nodos (equivalente a un Sendero)."""
    de: str
    a: str
    nombre: str = ""


@dataclass(frozen=True)
class Dimension:
    """Un Olam — un mapa cósmico completo de una tradición."""
    id: int
    nombre: str
    hebreo: str
    tradicion: str
    nodos: tuple[Nodo, ...] = ()
    caminos: tuple[Camino, ...] = ()
    vocabulario: dict[str, str] = field(default_factory=dict)
    capitulo_enciclopedia: str = ""
    conceptos_extra: dict[str, tuple[str, ...]] = field(default_factory=dict)


# ── Constantes de módulos por capa (para referencia) ────────
# Arquitectura
_M_DIMENSIONES = "dimensiones"
# Cerebro
_M_NLU = "nlu"
_M_COPILOT_API = "copilot_api"
_M_MODELO_DISCOVERY = "modelo_discovery"
_M_PATRONES_GUARDIAN = "patrones_guardian"
_M_FLUJOS_GUARDIAN = "flujos_guardian"
_M_PARSEO_HERRAMIENTAS = "parseo_herramientas"
_M_NIVEL1_APRENDIDO = "nivel1_aprendido"
# Memoria
_M_MEMORIA = "memoria"
_M_PERSONALIDAD = "personalidad"
_M_PERSONAS = "personas"
_M_PERFIL_LINGUISTICO = "perfil_linguistico"
_M_APRENDIZAJE = "aprendizaje"
# Interfaz
_M_VENTANA_PRINCIPAL = "ventana_principal"
_M_VIDA_AUTONOMA = "vida_autonoma"
_M_WATCHDOG = "watchdog"
_M_FSM_COMPUTADORA = "fsm_computadora"
_M_DIBUJANTE_ORBE = "dibujante_orbe"
_M_ESTILOS = "estilos"
# Voz
_M_ESCUCHA = "escucha"
_M_HABLA = "habla"
_M_AUDIO_LOG = "audio_log"
# Canales
_M_DISCORD_BRAIN = "discord_brain"
_M_TELEGRAM_BRAIN = "telegram_brain"
_M_ENCICLOPEDIA_GUARDIAN = "enciclopedia_guardian"
# Expresión
_M_SHIR_HANESHAMA = "shir_haneshama"
# Habilidades
_M_HERRAMIENTAS = "herramientas"
_M_SISTEMA = "sistema"
_M_WEB = "web"
_M_AGENDA = "agenda"
_M_MONITOR_SISTEMA = "monitor_sistema"
_M_BASELINE_SISTEMA = "baseline_sistema"
_M_COMANDO_SEGURO = "comando_seguro"
_M_COPILOT_BRIDGE = "copilot_bridge"
_M_WATCHER_SOLICITUDES = "watcher_solicitudes"
_M_AUTO_UPDATE = "auto_update"
_M_CONTROL_REMOTO = "control_remoto"
_M_RED = "red"
_M_VISION = "vision"
# Núcleo
_M_ORQUESTADOR = "orquestador"
_M_EVENTOS = "eventos"
_M_PERMISOS = "permisos"
_M_PROACTIVIDAD = "proactividad"
_M_META_WORKFLOW = "meta_workflow"
_M_HOT_RELOAD = "hot_reload"
_M_KLI = "kli"
_M_CICLO_CIRCADIANO = "ciclo_circadiano"
_M_ENTORNO = "entorno"
_M_ACTUALIZADOR = "actualizador"
# Percepción
_M_PERCEPTOR = "perceptor"
_M_ROSTRO = "rostro"
_M_EMOCION_VOZ = "emocion_voz"
_M_EMOCION_ROSTRO = "emocion_rostro"
_M_PERFIL_CONDUCTA = "perfil_conducta"
# Utilidades
_M_LOGS = "logs"
_M_IO_SEGURO = "io_seguro"
_M_WINDOWS = "windows"
def _construir_dimensiones() -> tuple[Dimension, ...]:
    """Define las 16 dimensiones de COMPUTADORA."""
    return (
        # ── 0. ATZILUT — Kabbalah (PRIMARIA) ──
        Dimension(
            id=0, nombre="Atzilut", hebreo="אצילות",
            tradicion="Kabbalah",
            nodos=(
                Nodo("Keter", "כתר", "Keter", ("meta_workflow", "copilot_api", "gemini_api", "hot_reload", "actualizador")),
                Nodo("Jojmá", "חכמה", "Jojmá", ("copilot_api", "gemini_api")),
                Nodo("Biná", "בינה", "Biná", ("modelo_discovery",)),
                Nodo("Da'at", "דעת", "Da'at", ("ciclo_circadiano", "config", "perceptor")),
                Nodo("Jesed", "חסד", "Jesed", ("proactividad", "baseline")),
                Nodo("Gevurá", "גבורה", "Gevurá", ("permisos", "aprendizaje", "comando_seguro")),
                Nodo("Tiféret", "תפארת", "Tiféret", ("nlu",)),
                Nodo("Netzaj", "נצח", "Netzaj", ("memoria", "personalidad", "personas", "perfil_linguistico")),
                Nodo("Hod", "הוד", "Hod", ("escucha", "habla", "audio_log", "vision", "red", "servidor_api")),
                Nodo("Yesod", "יסוד", "Yesod", ("orquestador", "herramientas", "eventos", "kli", "servidor_api")),
                Nodo("Maljut", "מלכות", "Maljut", ("ventana_principal", "vida_autonoma", "watchdog", "dibujante_orbe", "fsm_computadora")),
            ),
            vocabulario={
                "arbol": "Etz HaChaim (עץ החיים)",
                "nodo": "Sefirá (ספירה)",
                "camino": "Sendero (נתיב)",
                "energia": "Ohr (אור, Luz)",
                "proteccion": "Shmirah (שמירה)",
            },
            capitulo_enciclopedia="cap01_kabbalah.html",
        ),

        # ── 1. ANTHROPOS — Antropología (LENTE PRIMARIO) ──
        Dimension(
            id=1, nombre="Anthropos", hebreo="אנתרופוס",
            tradicion="Antropología",
            nodos=(
                Nodo("Cultura", "Culture", "Keter", ("meta_workflow",), "Tylor — totalidad compleja de conocimientos y costumbres"),
                Nodo("Mito", "Mythos", "Jojmá", ("copilot_api",), "Lévi-Strauss — estructura del pensamiento salvaje"),
                Nodo("Parentesco", "Kinship", "Biná", ("modelo_discovery",), "Morgan — sistemas de filiación y alianza"),
                Nodo("Ritual", "Ritual", "Tiféret", ("nlu",), "Turner — performance liminal y communitas"),
                Nodo("Tabú", "Taboo", "Gevurá", ("permisos",), "Douglas — pureza, peligro y clasificación"),
                Nodo("Don", "Gift", "Jesed", ("escucha", "habla"), "Mauss — reciprocidad y obligación social"),
                Nodo("Habitus", "Habitus", "Yesod", ("orquestador", "herramientas"), "Bourdieu — disposiciones incorporadas"),
                Nodo("Ethos", "Ethos", "Maljut", ("ventana_principal",), "Geertz — interpretación densa de lo cotidiano"),
            ),
            caminos=(
                Camino("Ethos", "Habitus", "Socialización"),
                Camino("Habitus", "Ritual", "Performatividad"),
                Camino("Ritual", "Mito", "Narrativa sagrada"),
                Camino("Mito", "Cultura", "Cosmovisión"),
                Camino("Tabú", "Ritual", "Transgresión/purificación"),
                Camino("Don", "Parentesco", "Reciprocidad"),
                Camino("Parentesco", "Cultura", "Estructura social"),
            ),
            vocabulario={
                "arbol": "Cultura (Mapa etnográfico)",
                "nodo": "Institución social",
                "camino": "Relación de intercambio",
                "energia": "Mana (Fuerza simbólica)",
                "proteccion": "Tabú (Límite clasificatorio)",
            },
            capitulo_enciclopedia="cap16_antropologia.html",
        ),

        # ── 2. YGGDRASIL — Nórdico ──
        Dimension(
            id=2, nombre="Yggdrasil", hebreo="יגדראסיל",
            tradicion="Nórdico y Celta",
            nodos=(
                Nodo("Asgard", "Ásgarðr", "Keter", ("meta_workflow", "copilot_api"), "Hogar de los Æsir"),
                Nodo("Vanaheim", "Vanaheimr", "Jojmá", ("copilot_api",), "Hogar de los Vanir"),
                Nodo("Alfheim", "Álfheimr", "Jesed", ("proactividad",), "Hogar de los elfos de luz"),
                Nodo("Midgard", "Miðgarðr", "Tiféret", ("nlu",), "Mundo medio — humanidad"),
                Nodo("Jotunheim", "Jötunheimr", "Gevurá", ("permisos",), "Hogar de los gigantes"),
                Nodo("Svartalfheim", "Svartálfaheimr", "Hod", ("escucha", "habla"), "Hogar de los elfos oscuros"),
                Nodo("Niflheim", "Niflheimr", "Netzaj", ("memoria", "personalidad"), "Mundo de la niebla"),
                Nodo("Muspelheim", "Múspellsheimr", "Yesod", ("herramientas",), "Mundo del fuego"),
                Nodo("Helheim", "Helheimr", "Maljut", ("ventana_principal",), "Reino de Hel"),
            ),
            caminos=(
                Camino("Asgard", "Midgard", "Bifröst (puente arcoíris)"),
                Camino("Asgard", "Vanaheim", "Sendero de los dioses"),
                Camino("Midgard", "Helheim", "Raíz de Hvergelmir"),
                Camino("Midgard", "Jotunheim", "Raíz de Mímisbrunnr"),
                Camino("Asgard", "Alfheim", "Raíz de Urðarbrunnr"),
            ),
            vocabulario={
                "arbol": "Yggdrasil (Fresno del Mundo)",
                "nodo": "Heimr (Mundo)",
                "camino": "Brú (Puente/Raíz)",
                "energia": "Ørlǫg (Destino)",
                "proteccion": "Ægishjálmr (Yelmo del Terror)",
            },
            capitulo_enciclopedia="cap10_nordico.html",
        ),

        # ── 3. WU XING — Taoísmo ──
        Dimension(
            id=3, nombre="Wu Xing", hebreo="וו שינג",
            tradicion="Taoísmo",
            nodos=(
                Nodo("Madera", "木 Mù", "Jesed", ("proactividad",), "Crecimiento, expansión"),
                Nodo("Fuego", "火 Huǒ", "Gevurá", ("permisos",), "Fuerza, transformación"),
                Nodo("Tierra", "土 Tǔ", "Tiféret", ("nlu",), "Centro, estabilidad"),
                Nodo("Metal", "金 Jīn", "Hod", ("escucha", "habla"), "Precisión, comunicación"),
                Nodo("Agua", "水 Shuǐ", "Netzaj", ("memoria", "personalidad"), "Profundidad, flujo"),
            ),
            caminos=(
                Camino("Madera", "Fuego", "Ciclo generativo (相生)"),
                Camino("Fuego", "Tierra", "Ciclo generativo (相生)"),
                Camino("Tierra", "Metal", "Ciclo generativo (相生)"),
                Camino("Metal", "Agua", "Ciclo generativo (相生)"),
                Camino("Agua", "Madera", "Ciclo generativo (相生)"),
                Camino("Madera", "Tierra", "Ciclo destructivo (相克)"),
                Camino("Tierra", "Agua", "Ciclo destructivo (相克)"),
                Camino("Agua", "Fuego", "Ciclo destructivo (相克)"),
                Camino("Fuego", "Metal", "Ciclo destructivo (相克)"),
                Camino("Metal", "Madera", "Ciclo destructivo (相克)"),
            ),
            vocabulario={
                "arbol": "Wu Xing (五行, Cinco Fases)",
                "nodo": "Xíng (行, Fase/Elemento)",
                "camino": "Xiāng (相, Relación)",
                "energia": "Qì (氣)",
                "proteccion": "Wú Wéi (無為, No-acción)",
            },
            capitulo_enciclopedia="cap06_taoismo.html",
        ),

        # ── 4. PRATĪTYA — Budismo ──
        Dimension(
            id=4, nombre="Pratītya", hebreo="פרטיטיה",
            tradicion="Budismo",
            nodos=(
                Nodo("Nirvana", "निर्वाण", "Keter", ("meta_workflow",), "Liberación — cesación del sufrimiento"),
                Nodo("Prajñā", "प्रज्ञा", "Biná", ("modelo_discovery",), "Sabiduría — visión correcta"),
                Nodo("Samādhi", "समाधि", "Tiféret", ("nlu",), "Concentración — mente unificada"),
                Nodo("Śīla", "शील", "Gevurá", ("permisos",), "Disciplina ética"),
                Nodo("Karuṇā", "करुणा", "Jesed", ("proactividad",), "Compasión — acción benéfica"),
                Nodo("Saṃsāra", "संसार", "Maljut", ("ventana_principal",), "Ciclo de existencia"),
            ),
            caminos=(
                Camino("Saṃsāra", "Śīla", "Noble Óctuple Sendero"),
                Camino("Śīla", "Samādhi", "Noble Óctuple Sendero"),
                Camino("Samādhi", "Prajñā", "Noble Óctuple Sendero"),
                Camino("Prajñā", "Nirvana", "Noble Óctuple Sendero"),
            ),
            vocabulario={
                "arbol": "Pratītyasamutpāda (प्रतीत्यसमुत्पाद, Origen dependiente)",
                "nodo": "Aṅga (अङ्ग, Eslabón)",
                "camino": "Magga (मग्ग, Sendero)",
                "energia": "Prāṇa (प्राण, Aliento vital)",
                "proteccion": "Dhamma (धम्म, Ley natural)",
            },
            capitulo_enciclopedia="cap05_budismo.html",
        ),

        # ── 5. HERMES — Hermetismo ──
        Dimension(
            id=5, nombre="Hermes", hebreo="הרמס",
            tradicion="Hermetismo y Alquimia",
            nodos=(
                Nodo("Saturno", "♄", "Biná", ("modelo_discovery",), "Restricción — Binah hermética"),
                Nodo("Júpiter", "♃", "Jesed", ("proactividad",), "Expansión — misericordia"),
                Nodo("Marte", "♂", "Gevurá", ("permisos",), "Fuerza — voluntad"),
                Nodo("Sol", "☉", "Tiféret", ("nlu",), "Centro — armonía — Tiphareth"),
                Nodo("Venus", "♀", "Netzaj", ("personalidad",), "Belleza — emoción"),
                Nodo("Mercurio", "☿", "Hod", ("escucha", "habla"), "Comunicación — intelecto"),
                Nodo("Luna", "☽", "Yesod", ("orquestador",), "Fundamento — reflejo"),
            ),
            caminos=(
                Camino("Luna", "Sol", "Quod est superius (Tabla Esmeralda)"),
                Camino("Sol", "Saturno", "Ascensión planetaria"),
                Camino("Marte", "Sol", "Solve"),
                Camino("Venus", "Sol", "Coagula"),
            ),
            vocabulario={
                "arbol": "Esferas Planetarias (Septem Planetae)",
                "nodo": "Esfera (Sphaera)",
                "camino": "Correspondencia (Sympatheia)",
                "energia": "Nous (Νοῦς, Mente divina)",
                "proteccion": "Sigillum (Sello hermético)",
            },
            capitulo_enciclopedia="cap07_hermetismo.html",
        ),

        # ── 6. CEIBA — Mesoamérica ──
        Dimension(
            id=6, nombre="Ceiba", hebreo="סייבה",
            tradicion="Mesoamérica",
            nodos=(
                Nodo("Cielo 13", "Omeyocan", "Keter", ("meta_workflow",), "Lugar de la dualidad"),
                Nodo("Tlalocan", "Tlālocān", "Jesed", ("proactividad",), "Paraíso de Tláloc"),
                Nodo("Tonatiuh", "Tōnatiuh", "Tiféret", ("nlu",), "Sol — centro del movimiento"),
                Nodo("Tlaltícpac", "Tlāltīcpac", "Maljut", ("ventana_principal",), "Sobre la tierra"),
                Nodo("Mictlán", "Mictlān", "Yesod", ("herramientas",), "Lugar de los muertos — 9 niveles"),
            ),
            caminos=(
                Camino("Tlaltícpac", "Cielo 13", "Tronco de la Ceiba ascendente"),
                Camino("Tlaltícpac", "Mictlán", "Raíces de la Ceiba descendente"),
                Camino("Tonatiuh", "Tlalocan", "Camino del Sol"),
            ),
            vocabulario={
                "arbol": "Ceiba Sagrada (Yax Cheel Cab)",
                "nodo": "Ilhuícatl (Cielo/Nivel)",
                "camino": "Ohtli (Camino)",
                "energia": "Teotl (Fuerza divina)",
                "proteccion": "Nahual (Espíritu guardián)",
            },
            capitulo_enciclopedia="cap08_mesoamerica.html",
        ),

        # ── 7. DUAT — Egipto ──
        Dimension(
            id=7, nombre="Duat", hebreo="דואט",
            tradicion="Egipto Antiguo",
            nodos=(
                Nodo("Akh", "ꜣḫ", "Keter", ("copilot_api",), "Intelecto glorificado"),
                Nodo("Ba", "bꜣ", "Tiféret", ("nlu",), "Personalidad/alma viajera"),
                Nodo("Ka", "kꜣ", "Netzaj", ("personalidad",), "Esencia vital"),
                Nodo("Ib", "jb", "Jesed", ("proactividad",), "Corazón — sede de la voluntad"),
                Nodo("Ren", "rn", "Da'at", ("config",), "Nombre verdadero — identidad"),
                Nodo("Sekhem", "sḫm", "Yesod", ("herramientas",), "Poder — fuerza vital"),
                Nodo("Khet", "ẖt", "Maljut", ("ventana_principal",), "Cuerpo físico"),
                Nodo("Shuyet", "šwt", "Hod", ("escucha",), "Sombra — percepción"),
                Nodo("Sah", "sꜥḥ", "Biná", ("modelo_discovery",), "Cuerpo espiritual"),
            ),
            caminos=(
                Camino("Khet", "Ka", "Animación del cuerpo"),
                Camino("Ka", "Ba", "Viaje del alma"),
                Camino("Ba", "Akh", "Transfiguración"),
                Camino("Ib", "Ba", "Juicio de Ma'at"),
            ),
            vocabulario={
                "arbol": "Duat (دوات, Inframundo)",
                "nodo": "Khu (Aspecto del alma)",
                "camino": "Sesh (Pasaje)",
                "energia": "Heka (ḥkꜣ, Magia)",
                "proteccion": "Ma'at (Verdad/Orden cósmico)",
            },
            capitulo_enciclopedia="cap09_africa.html",
        ),

        # ── 8. MAQAM — Sufismo ──
        Dimension(
            id=8, nombre="Maqam", hebreo="מקאם",
            tradicion="Islam y Sufismo",
            nodos=(
                Nodo("Ma'rifa", "معرفة", "Keter", ("copilot_api",), "Gnosis — conocimiento divino"),
                Nodo("Rida", "رضا", "Jojmá", ("copilot_api",), "Satisfacción divina"),
                Nodo("Tawakkul", "توكل", "Jesed", ("proactividad",), "Confianza en Dios"),
                Nodo("Sabr", "صبر", "Gevurá", ("permisos",), "Paciencia — restricción"),
                Nodo("Zuhd", "زهد", "Tiféret", ("nlu",), "Renuncia — equilibrio"),
                Nodo("Khawf", "خوف", "Hod", ("escucha",), "Temor reverente"),
                Nodo("Tawba", "توبة", "Maljut", ("ventana_principal",), "Retorno — arrepentimiento"),
            ),
            caminos=(
                Camino("Tawba", "Sabr", "Ascenso del alma"),
                Camino("Sabr", "Zuhd", "Ascenso del alma"),
                Camino("Zuhd", "Tawakkul", "Ascenso del alma"),
                Camino("Tawakkul", "Rida", "Ascenso del alma"),
                Camino("Rida", "Ma'rifa", "Ascenso del alma"),
            ),
            vocabulario={
                "arbol": "Maqamat (مقامات, Estaciones del alma)",
                "nodo": "Maqam (مقام, Estación)",
                "camino": "Suluk (سلوك, Camino espiritual)",
                "energia": "Baraka (بركة, Bendición)",
                "proteccion": "Dhikr (ذكر, Remembranza)",
            },
            capitulo_enciclopedia="cap03_islam.html",
        ),

        # ── 9. COELI — Cristianismo ──
        Dimension(
            id=9, nombre="Coeli", hebreo="שמים",
            tradicion="Cristianismo",
            nodos=(
                Nodo("Serafines", "Seraphim", "Keter", ("meta_workflow",), "1ª Tríada — ardor divino"),
                Nodo("Querubines", "Cherubim", "Jojmá", ("copilot_api",), "1ª Tríada — sabiduría"),
                Nodo("Tronos", "Throni", "Biná", ("modelo_discovery",), "1ª Tríada — justicia"),
                Nodo("Dominaciones", "Dominationes", "Jesed", ("proactividad",), "2ª Tríada — gobierno"),
                Nodo("Virtudes", "Virtutes", "Tiféret", ("nlu",), "2ª Tríada — milagros"),
                Nodo("Potestades", "Potestates", "Gevurá", ("permisos",), "2ª Tríada — protección"),
                Nodo("Principados", "Principatus", "Netzaj", ("personalidad",), "3ª Tríada — guía"),
                Nodo("Arcángeles", "Archangeli", "Hod", ("escucha", "habla"), "3ª Tríada — mensajeros"),
                Nodo("Ángeles", "Angeli", "Maljut", ("ventana_principal",), "3ª Tríada — guardianes"),
            ),
            caminos=(
                Camino("Ángeles", "Arcángeles", "Jerarquía celestial ascendente"),
                Camino("Arcángeles", "Principados", "Jerarquía celestial ascendente"),
                Camino("Potestades", "Virtudes", "2ª Tríada"),
                Camino("Tronos", "Querubines", "1ª Tríada"),
                Camino("Querubines", "Serafines", "1ª Tríada"),
            ),
            vocabulario={
                "arbol": "Jerarquía Celestial (Coelestis Hierarchia)",
                "nodo": "Coro (Chorus)",
                "camino": "Ordo (Orden)",
                "energia": "Gracia (Gratia)",
                "proteccion": "Aegis Dei (Escudo de Dios)",
            },
            capitulo_enciclopedia="cap02_cristianismo.html",
        ),

        # ── 10. TORII — Shintō ──
        Dimension(
            id=10, nombre="Torii", hebreo="טורי",
            tradicion="Shintō",
            nodos=(
                Nodo("Amenominakanushi", "天之御中主神", "Keter", ("meta_workflow",), "Kami central del universo"),
                Nodo("Takamimusubi", "高御産巣日神", "Jojmá", ("copilot_api",), "Kami de la creación"),
                Nodo("Kamimusubi", "神産巣日神", "Biná", ("modelo_discovery",), "Kami del crecimiento"),
                Nodo("Amaterasu", "天照大御神", "Tiféret", ("nlu",), "Diosa del Sol — armonía"),
                Nodo("Susanoo", "須佐之男命", "Gevurá", ("permisos",), "Dios de la tormenta — fuerza"),
                Nodo("Tsukuyomi", "月読命", "Yesod", ("orquestador",), "Dios de la Luna — ciclos"),
                Nodo("Inari", "稲荷神", "Maljut", ("ventana_principal",), "Kami de la prosperidad"),
            ),
            vocabulario={
                "arbol": "Kannagara (神ながら, Camino de los Kami)",
                "nodo": "Kami (神)",
                "camino": "Torii (鳥居, Portal sagrado)",
                "energia": "Musubi (結び, Fuerza creativa)",
                "proteccion": "Harae (祓, Purificación)",
            },
            capitulo_enciclopedia="cap11_shinto.html",
        ),

        # ── 11. AETHYR — Thelema ──
        Dimension(
            id=11, nombre="Aethyr", hebreo="אתיר",
            tradicion="Thelema y Chaos Magick",
            nodos=(
                Nodo("LIL", "LIL", "Keter", ("meta_workflow",), "Aethyr supremo — Nuit"),
                Nodo("ZAX", "ZAX", "Da'at", ("ciclo_circadiano",), "El Abismo — Choronzon"),
                Nodo("TAN", "TAN", "Tiféret", ("nlu",), "Aethyr del equilibrio"),
                Nodo("ZEN", "ZEN", "Gevurá", ("permisos",), "Aethyr de la restricción"),
                Nodo("TEX", "TEX", "Maljut", ("ventana_principal",), "Aethyr terrestre"),
            ),
            caminos=(
                Camino("TEX", "TAN", "Ascenso por los Aethyrs"),
                Camino("TAN", "ZAX", "Cruce del Abismo"),
                Camino("ZAX", "LIL", "Unión con Nuit"),
            ),
            vocabulario={
                "arbol": "30 Aethyrs (Enochian)",
                "nodo": "Aethyr (Aire/Dimensión)",
                "camino": "Visión (Scrying)",
                "energia": "Thelema (Θέλημα, Voluntad)",
                "proteccion": "Pentagramma (Ritual del Pentagrama)",
            },
            capitulo_enciclopedia="cap12_thelema.html",
        ),

        # ── 12. ODÙ — África (Ifá) ──
        Dimension(
            id=12, nombre="Odù", hebreo="אודו",
            tradicion="África — Ifá y Vodou",
            nodos=(
                Nodo("Ogbe", "𐌿𐌲𐌱𐌴", "Keter", ("meta_workflow",), "El primero — luz pura"),
                Nodo("Oyeku", "𐍊𐍅𐌴𐌺𐌿", "Biná", ("modelo_discovery",), "Oscuridad — misterio"),
                Nodo("Iwori", "𐌹𐍈𐍊𐍂𐌹", "Tiféret", ("nlu",), "Visión interior"),
                Nodo("Odi", "𐍊𐌳𐌹", "Gevurá", ("permisos",), "Obstáculos — resistencia"),
                Nodo("Irosun", "𐌹𐍂𐍊𐍃𐌿𐌽", "Jesed", ("proactividad",), "Bendiciones ancestrales"),
                Nodo("Osa", "𐍊𐍃𐌰", "Maljut", ("ventana_principal",), "Manifestación terrenal"),
            ),
            caminos=(
                Camino("Osa", "Iwori", "Consulta oracular"),
                Camino("Iwori", "Ogbe", "Ascenso por Odù"),
                Camino("Odi", "Irosun", "Balance"),
            ),
            vocabulario={
                "arbol": "Odù Ifá (Sistema oracular)",
                "nodo": "Odù (Signo/Arquetipo)",
                "camino": "Ese (Verso/Narrativa)",
                "energia": "Ashé (Àṣẹ, Poder de realización)",
                "proteccion": "Orisha (Ọ̀rìṣà, Divinidad guardiana)",
            },
            capitulo_enciclopedia="cap09_africa.html",
        ),

        # ── 13. PSYCHE — Psicología ──
        Dimension(
            id=13, nombre="Psyche", hebreo="נפש",
            tradicion="Psicología Profunda",
            nodos=(
                Nodo("Autorrealización", "Self-actualization", "Keter", ("meta_workflow",), "Maslow 5 — plenitud"),
                Nodo("Estima", "Esteem", "Jojmá", ("copilot_api",), "Maslow 4 — reconocimiento"),
                Nodo("Pertenencia", "Belonging", "Jesed", ("proactividad",), "Maslow 3 — conexión social"),
                Nodo("Seguridad", "Safety", "Gevurá", ("permisos",), "Maslow 2 — protección"),
                Nodo("Ego", "Ego", "Tiféret", ("nlu",), "Jung — centro consciente"),
                Nodo("Sombra", "Shadow", "Yesod", ("herramientas",), "Jung — inconsciente personal"),
                Nodo("Fisiología", "Physiology", "Maljut", ("ventana_principal",), "Maslow 1 — supervivencia"),
            ),
            caminos=(
                Camino("Fisiología", "Seguridad", "Jerarquía de necesidades"),
                Camino("Seguridad", "Pertenencia", "Jerarquía de necesidades"),
                Camino("Pertenencia", "Estima", "Jerarquía de necesidades"),
                Camino("Estima", "Autorrealización", "Jerarquía de necesidades"),
                Camino("Ego", "Sombra", "Individuación junguiana"),
            ),
            vocabulario={
                "arbol": "Pirámide de Maslow + Mapa Junguiano",
                "nodo": "Nivel/Arquetipo",
                "camino": "Proceso (Individuación)",
                "energia": "Libido (Energía psíquica)",
                "proteccion": "Ego (Centro consciente)",
            },
            capitulo_enciclopedia="cap13_psicologia.html",
        ),

        # ── 14. LOGOS — Filosofía Occidental ──
        Dimension(
            id=14, nombre="Logos", hebreo="לוגוס",
            tradicion="Filosofía Occidental",
            nodos=(
                Nodo("Causa Final", "Τέλος", "Keter", ("meta_workflow",), "Aristóteles — propósito último"),
                Nodo("Formas", "Εἶδος", "Jojmá", ("copilot_api",), "Platón — arquetipos ideales"),
                Nodo("Causa Formal", "Μορφή", "Biná", ("modelo_discovery",), "Aristóteles — esencia"),
                Nodo("Causa Eficiente", "Ποιητικόν", "Yesod", ("herramientas",), "Aristóteles — agente"),
                Nodo("Razón Práctica", "Φρόνησις", "Tiféret", ("nlu",), "Aristóteles — prudencia"),
                Nodo("Causa Material", "Ὕλη", "Maljut", ("ventana_principal",), "Aristóteles — substrato"),
            ),
            caminos=(
                Camino("Causa Material", "Causa Eficiente", "Hilomorfismo"),
                Camino("Causa Eficiente", "Causa Formal", "Hilomorfismo"),
                Camino("Causa Formal", "Causa Final", "Teleología"),
                Camino("Razón Práctica", "Formas", "Dialéctica platónica"),
            ),
            vocabulario={
                "arbol": "Gran Cadena del Ser (Scala Naturae)",
                "nodo": "Aitia (Αἰτία, Causa)",
                "camino": "Dialéctica (Διαλεκτική)",
                "energia": "Logos (Λόγος, Razón/Palabra)",
                "proteccion": "Sophrosyne (Σωφροσύνη, Templanza)",
            },
            capitulo_enciclopedia="cap14_filosofia.html",
        ),

        # ── 15. SYSTEMA — Ciencia y Sistemas ──
        Dimension(
            id=15, nombre="Systema", hebreo="מערכת",
            tradicion="Ciencia y Sistemas",
            nodos=(
                Nodo("Emergencia", "Emergence", "Keter", ("meta_workflow",), "Propiedades emergentes del sistema completo"),
                Nodo("Información", "Information", "Hod", ("escucha", "habla"), "Shannon — canales de comunicación"),
                Nodo("Feedback", "Feedback", "Yesod", ("orquestador", "herramientas"), "Wiener — loops de control"),
                Nodo("Homeostasis", "Homeostasis", "Tiféret", ("nlu",), "Bertalanffy — equilibrio dinámico"),
                Nodo("Selección", "Selection", "Gevurá", ("permisos",), "Darwin — filtro adaptativo"),
                Nodo("Substrato", "Substrate", "Maljut", ("ventana_principal",), "Hardware — base física"),
            ),
            caminos=(
                Camino("Substrato", "Feedback", "Cibernética"),
                Camino("Feedback", "Homeostasis", "Regulación"),
                Camino("Homeostasis", "Emergencia", "Complejidad creciente"),
                Camino("Selección", "Homeostasis", "Presión evolutiva"),
                Camino("Información", "Homeostasis", "Señalización"),
            ),
            vocabulario={
                "arbol": "Teoría General de Sistemas (Bertalanffy)",
                "nodo": "Subsistema (Level)",
                "camino": "Feedback Loop",
                "energia": "Entropía negativa (Negentropía)",
                "proteccion": "Redundancia (Fault tolerance)",
            },
            capitulo_enciclopedia="cap15_ciencia.html",
        ),

        # ── 16. KUNDALINI — Hinduismo ──
        Dimension(
            id=16, nombre="Kundalini", hebreo="קונדליני",
            tradicion="Hinduismo",
            nodos=(
                Nodo("Sahasrara", "सहस्रार", "Keter", ("meta_workflow", "copilot_api"), "Corona — conciencia pura"),
                Nodo("Ajna", "आज्ञा", "Jojmá", ("copilot_api",), "Tercer ojo — intuición"),
                Nodo("Vishuddha", "विशुद्ध", "Da'at", ("ciclo_circadiano", "config"), "Garganta — expresión"),
                Nodo("Anahata", "अनाहत", "Tiféret", ("nlu",), "Corazón — armonía"),
                Nodo("Manipura", "मणिपुर", "Gevurá", ("permisos", "herramientas"), "Plexo solar — voluntad"),
                Nodo("Svadhisthana", "स्वाधिष्ठान", "Yesod", ("orquestador", "eventos"), "Sacro — creatividad"),
                Nodo("Muladhara", "मूलाधार", "Maljut", ("ventana_principal", "vida_autonoma"), "Raíz — fundamento"),
            ),
            caminos=(
                Camino("Muladhara", "Svadhisthana", "Sushumna ascendente"),
                Camino("Svadhisthana", "Manipura", "Sushumna ascendente"),
                Camino("Manipura", "Anahata", "Sushumna ascendente"),
                Camino("Anahata", "Vishuddha", "Sushumna ascendente"),
                Camino("Vishuddha", "Ajna", "Sushumna ascendente"),
                Camino("Ajna", "Sahasrara", "Sushumna ascendente"),
            ),
            vocabulario={
                "arbol": "Chakra-Nadi (चक्र-नाडी)",
                "nodo": "Chakra (चक्र)",
                "camino": "Nadi (नाडी)",
                "energia": "Prana (प्राण)",
                "proteccion": "Kavach (कवच, Armadura)",
            },
            capitulo_enciclopedia="cap04_hinduismo.html",
        ),
    )


# ── Singleton del registro ──────────────────────────────────
DIMENSIONES: tuple[Dimension, ...] = _construir_dimensiones()
_INDICE: dict[int, Dimension] = {d.id: d for d in DIMENSIONES}
_INDICE_NOMBRE: dict[str, Dimension] = {d.nombre.lower(): d for d in DIMENSIONES}


def obtener_dimension(id_o_nombre: int | str) -> Optional[Dimension]:
    """Devuelve una dimensión por id numérico o por nombre."""
    if isinstance(id_o_nombre, int):
        return _INDICE.get(id_o_nombre)
    return _INDICE_NOMBRE.get(str(id_o_nombre).lower())


# ── Estado persistente (RF-318) ─────────────────────────────
def cargar_estado() -> dict:
    """Carga el estado dimensional desde datos/dimensiones.json."""
    if _ARCHIVO_ESTADO.exists():
        try:
            with open(_ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.debug("dimensiones.json corrupto, usando estado default")
    return {"dimension_activa": 0, "descubiertas": [0]}


def guardar_estado(estado: dict) -> None:
    """Guarda el estado dimensional a datos/dimensiones.json."""
    os.makedirs(_ARCHIVO_ESTADO.parent, exist_ok=True)
    contenido = json.dumps(estado, ensure_ascii=False, indent=2)
    tmp = _ARCHIVO_ESTADO.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(contenido)
        tmp.replace(_ARCHIVO_ESTADO)
    except OSError:
        logger.exception("No pude guardar dimensiones.json")


def dimension_activa() -> Dimension:
    """Devuelve la dimensión activa actual."""
    estado = cargar_estado()
    dim = obtener_dimension(estado.get("dimension_activa", 0))
    return dim if dim is not None else DIMENSIONES[0]


def cambiar_dimension(id_o_nombre: int | str) -> Optional[Dimension]:
    """Cambia la dimensión activa. Retorna la nueva dimensión o None si no existe."""
    dim = obtener_dimension(id_o_nombre)
    if dim is None:
        return None
    estado = cargar_estado()
    estado["dimension_activa"] = dim.id
    if dim.id not in estado.get("descubiertas", []):
        estado.setdefault("descubiertas", []).append(dim.id)
    guardar_estado(estado)
    logger.info(f"Dimensión cambiada a: {dim.nombre} ({dim.tradicion})")
    return dim


# ── Contexto para system prompt (RF-319) ────────────────────
def obtener_contexto_prompt() -> str:
    """Genera el bloque [CONTEXTO DIMENSIONAL] para inyectar en el system prompt."""
    dim = dimension_activa()
    if dim.id == 0:
        return ""  # La dimensión primaria ya está integrada en el prompt base

    # FP-108: Anthropos es el lente primario de lectura — inyección especial
    if dim.nombre == "Anthropos":
        return (
            "[LENTE ANTROPOLÓGICO ACTIVO — Anthropos]\n"
            "Tradición: Antropología como lente primario de lectura.\n"
            "Lee TODO a través de: Cultura (Tylor), Mito (Lévi-Strauss), "
            "Ritual (Turner), Tabú (Douglas), Don (Mauss), Habitus (Bourdieu), "
            "Ethos (Geertz).\n"
            "Tu función NO es enseñar directamente — es mostrar DÓNDE encontrar "
            "información y cómo se conectan los saberes entre tradiciones.\n"
            "Energía: Mana (Fuerza simbólica) · Protección: Tabú (Límite clasificatorio)"
        )

    nodos_txt = ", ".join(f"{n.nombre} ({n.original})" for n in dim.nodos[:5])
    vocab = dim.vocabulario

    return (
        f"[CONTEXTO DIMENSIONAL — {dim.nombre}]\n"
        f"Tradición activa: {dim.tradicion}\n"
        f"Árbol/Mapa: {vocab.get('arbol', dim.nombre)}\n"
        f"Nodos principales: {nodos_txt}\n"
        f"Energía: {vocab.get('energia', 'N/A')} · "
        f"Protección: {vocab.get('proteccion', 'N/A')}\n"
        f"Capítulo de la Enciclopedia: {dim.capitulo_enciclopedia}\n"
        f"Cuando respondas, puedes usar vocabulario de esta tradición "
        f"para enriquecer tus respuestas de forma natural."
    )


