"""
🪄 Hechizos de Harry Potter — Comandos de voz mágicos para Computadora.

Mapea incantaciones del universo Harry Potter a acciones reales de Computadora.
Se integra en el Nivel 1 (Néfesh/regex) como alias temáticos de commands existentes.

Cada hechizo tiene:
  - regex: patrón compilado que detecta la incantación (con variantes fonéticas de Whisper)
  - handler: función que recibe (cerebro, match) y retorna str | None
  - descripcion: para documentación y Enciclopedia

Las Maldiciones Imperdonables (Avada Kedavra, Crucio, Imperio) están BLOQUEADAS
por Gevurá — violan la Ley 1 de Asimov (nunca dañar).
"""

import re
import random
from loguru import logger

# ═══════════════════════════════════════════════════════════
# CATÁLOGO DE HECHIZOS
# ═══════════════════════════════════════════════════════════

# Estructura: (nombre, regex, handler_fn, descripcion)
# Los handlers reciben (cerebro, match_obj, texto_original) → str

def _h_lumos(cerebro, m, texto):
    """Lumos — Iluminar pantalla (brillo al máximo)."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    try:
        ejecutar_herramienta("ejecutar_comando_sistema",
            {"comando": "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)"},
            orden_directa=True)
    except Exception as e:
        logger.debug(f"Lumos: error ajustando brillo: {e}")
    return random.choice([
        "Lumos. Iluminando, señor.",
        "Lumos. Que se haga la luz.",
        "Lumos. Pantalla al máximo brillo.",
    ])


def _h_nox(cerebro, m, texto):
    """Nox — Oscurecer pantalla (brillo al mínimo)."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    try:
        ejecutar_herramienta("ejecutar_comando_sistema",
            {"comando": "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,5)"},
            orden_directa=True)
    except Exception as e:
        logger.debug(f"Nox: error ajustando brillo: {e}")
    return random.choice([
        "Nox. Oscureciendo, señor.",
        "Nox. La oscuridad es mi aliada.",
        "Nox. Brillo al mínimo.",
    ])


def _h_accio(cerebro, m, texto):
    """Accio X — Invocar/abrir aplicación o buscar archivo."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    objetivo = m.group(1).strip().rstrip(".!?") if m.group(1) else ""
    if not objetivo:
        return "¿Qué desea invocar, señor? Diga 'Accio' seguido del nombre."
    # Intentar abrir como app primero
    resultado = ejecutar_herramienta("abrir_aplicacion", {"nombre": objetivo}, orden_directa=True)
    if resultado and "error" not in resultado.lower():
        return f"Accio {objetivo.title()}. Invocado, señor."
    # Fallback: buscar archivos
    resultado = ejecutar_herramienta("buscar_archivos", {"patron": f"*{objetivo}*"}, orden_directa=True)
    return f"Accio {objetivo.title()}. {resultado}" if resultado else f"No encontré '{objetivo}', señor."


def _h_silencio(cerebro, m, texto):
    """Silencio — Mutear volumen."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    ejecutar_herramienta("controlar_volumen", {"accion": "mute"}, orden_directa=True)
    return random.choice([
        "Silencio. Todo en mute, señor.",
        "Silencio. El sonido ha sido conjurado al vacío.",
        "Silencio. Ni un murmullo.",
    ])


def _h_sonorus(cerebro, m, texto):
    """Sonorus — Volumen al máximo."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    ejecutar_herramienta("controlar_volumen", {"accion": "subir"}, orden_directa=True)
    return random.choice([
        "Sonorus. Volumen amplificado, señor.",
        "Sonorus. Ahora todo el mundo escuchará.",
        "Sonorus. Volumen arriba.",
    ])


def _h_alohomora(cerebro, m, texto):
    """Alohomora — Abrir el Enciclopedia (libro_encantado)."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    try:
        ejecutar_herramienta("ejecutar_comando",
            {"comando": 'start "" "http://localhost:8080"'},
            orden_directa=True)
        return "Alohomora. Abriendo el Enciclopedia, señor."
    except Exception as e:
        logger.debug(f"Alohomora: error abriendo Enciclopedia: {e}")
        return "Alohomora. No pude abrir el Enciclopedia — ¿está corriendo el servidor?"


def _h_expecto_patronum(cerebro, m, texto):
    """Expecto Patronum — Invocar demo visual (Maljut)."""
    return "__DEMO_ANIMACIONES__"


def _h_protego(cerebro, m, texto):
    """Protego — Activar modo guardián."""
    cerebro._notificar_nivel("nivel1")
    return cerebro._activar_guardian()


def _h_stupefy(cerebro, m, texto):
    """Stupefy — Dormir/congelar a Computadora."""
    cerebro._notificar_nivel("nivel1")
    return cerebro._flujo_dormir(vigila=False)


def _h_expelliarmus(cerebro, m, texto):
    """Expelliarmus — Cerrar la app en primer plano."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    try:
        # Cerrar ventana activa con Alt+F4 simulado
        ejecutar_herramienta("ejecutar_comando_sistema",
            {"comando": "powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys('%{F4}')\""},
            orden_directa=True)
        return "Expelliarmus. Ventana desarmada, señor."
    except Exception as e:
        logger.debug(f"Expelliarmus: error cerrando ventana: {e}")
        return "Expelliarmus. No pude cerrar la ventana activa."


def _h_wingardium_leviosa(cerebro, m, texto):
    """Wingardium Leviosa — Mover el orbe arriba."""
    if cerebro.on_movimiento:
        try:
            cerebro.on_movimiento("arriba")
        except Exception as e:
            logger.debug(f"Wingardium Leviosa: error moviendo orbe: {e}")
    return random.choice([
        "Wingardium Leviosaaaa. El orbe se eleva, señor.",
        "Es Levi-O-sa, no Levio-SA. Orbe arriba.",
    ])


def _h_revelio(cerebro, m, texto):
    """Revelio — Mostrar info del sistema."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    try:
        from computadora.nucleo.entorno import EntornoSistema
        ent = EntornoSistema.instancia()
        info = ent.resumen_completo()
        return f"Revelio. {info}"
    except Exception as e:
        logger.debug(f"Revelio: error EntornoSistema: {e}")
        return ejecutar_herramienta("obtener_info_sistema", {}, orden_directa=True)


def _h_reparo(cerebro, m, texto):
    """Reparo — Autodiagnóstico de Computadora."""
    return cerebro._generar_autodiag_verbal()


def _h_obliviate(cerebro, m, texto):
    """Obliviate — Limpiar historial de conversación actual."""
    try:
        if hasattr(cerebro, '_historial'):
            cerebro._historial.clear()
        return "Obliviate. Memoria de conversación limpiada, señor. Empezamos de cero."
    except Exception as e:
        logger.debug(f"Obliviate: error limpiando historial: {e}")
        return "Obliviate. No pude limpiar la memoria, señor."


def _h_finite_incantatem(cerebro, m, texto):
    """Finite Incantatem — Cancelar operación / modo silencio."""
    return "__SILENCIO__"


def _h_muffliato(cerebro, m, texto):
    """Muffliato — Modo sigiloso (Tzimtzum)."""
    if cerebro.on_tzimtzum:
        try:
            cerebro.on_tzimtzum("comando")
        except Exception as e:
            logger.debug(f"Muffliato: error en tzimtzum: {e}")
    return "Muffliato. Modo sigiloso activado, señor."


def _h_riddikulus(cerebro, m, texto):
    """Riddikulus — Contar un chiste / expresión artística."""
    try:
        from computadora.expresion.shir_haneshama import generar_expresion
        humor = "neutral"
        if cerebro._personalidad:
            humor = cerebro._personalidad.humor_actual
        return generar_expresion(humor)
    except Exception as e:
        logger.debug(f"Riddikulus: error generando expresión: {e}")
        chistes = [
            "¿Por qué el mago no puede jugar cartas? Porque siempre tiene un As bajo la manga... y una varita.",
            "Profesor Snape entra a un bar. El bartender dice: '¿Lo de siempre?' Snape: 'Siempre.'",
            "¿Cuál es el hechizo favorito de los programadores? Expecto Debuggum.",
        ]
        return random.choice(chistes)


def _h_tempus(cerebro, m, texto):
    """Tempus — Mostrar hora y fecha."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    resultado = ejecutar_herramienta("obtener_fecha_hora", {}, orden_directa=True)
    return f"Tempus. {resultado}"


def _h_punto_me(cerebro, m, texto):
    """Point Me (Orientame) — Buscar en internet."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    from urllib.parse import quote_plus
    consulta = m.group(1).strip().rstrip(".!?") if m.group(1) else ""
    if not consulta:
        return "¿Qué desea que busque, señor?"
    url = "https://www.google.com/search?q=" + quote_plus(consulta)
    ejecutar_herramienta("ejecutar_comando", {"comando": f'start "" "{url}"'}, orden_directa=True)
    return f"Point Me. Buscando '{consulta}', señor."


def _h_homenum_revelio(cerebro, m, texto):
    """Homenum Revelio — ¿Quién está usando la PC? Contexto de pantalla."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    resultado = ejecutar_herramienta("contexto_pantalla", {}, orden_directa=True)
    return f"Homenum Revelio. {resultado}"


def _h_prior_incantato(cerebro, m, texto):
    """Prior Incantato — ¿Qué fue lo último que hice/dije?"""
    try:
        import computadora.memoria.memoria as memoria
        from datetime import date
        items = memoria._read_raw(date.today())
        recientes = [it for it in items if it.get("role") == "user"]
        if recientes:
            ultimo = recientes[-1].get("text", "No recuerdo.")
            return f"Prior Incantato. Lo último que dijo: \"{ultimo[:120]}\""
        return "Prior Incantato. No hay registro de incantaciones previas, señor."
    except Exception as e:
        logger.debug(f"Prior Incantato: error leyendo memoria: {e}")
        return "Prior Incantato. No pude consultar el historial, señor."


def _h_aparecium(cerebro, m, texto):
    """Aparecium — Mostrar archivos ocultos / leer portapapeles."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    resultado = ejecutar_herramienta("leer_portapapeles", {}, orden_directa=True)
    if resultado:
        return f"Aparecium. En el portapapeles invisible: {resultado}"
    return "Aparecium. No hay texto oculto en el portapapeles."


def _h_captura(cerebro, m, texto):
    """Arresto Momentum — Captura de pantalla (congelar el momento)."""
    from computadora.habilidades.herramientas import ejecutar_herramienta
    resultado = ejecutar_herramienta("tomar_captura_pantalla", {}, orden_directa=True)
    return f"Arresto Momentum. Momento capturado. {resultado}"


def _h_reducio(cerebro, m, texto):
    """Reducio — Minimizar a bandeja."""
    return "__MINIMIZAR__"


def _h_engorgio(cerebro, m, texto):
    """Engorgio — Restaurar ventana / salir de modo compacto."""
    if cerebro.on_tzimtzum:
        try:
            cerebro.on_tzimtzum("restaurar")
        except Exception as e:
            logger.debug(f"Engorgio: error restaurando: {e}")
    return "Engorgio. Restaurando tamaño completo, señor."


def _h_imperio_bloqueado(cerebro, m, texto):
    """Imperio — BLOQUEADO por Gevurá. Maldición Imperdonable."""
    logger.warning(f"Gevurá: Maldición Imperdonable rechazada — '{texto[:50]}'")
    return ("⚡ Gevurá rechaza esta maldición. Las Imperdonables violan la Ley 1 de Asimov: "
            "nunca dañar a un humano. No ejecuto Imperio, Crucio ni Avada Kedavra. "
            "Soy Computadora, no mortífago.")


# ═══════════════════════════════════════════════════════════
# REGISTRO DE HECHIZOS
# ═══════════════════════════════════════════════════════════

HECHIZOS = [
    # --- Hechizos funcionales ---
    {
        "nombre": "Lumos",
        "regex": re.compile(r"\blumos\b", re.IGNORECASE),
        "handler": _h_lumos,
        "desc": "Iluminar pantalla (brillo máximo)",
    },
    {
        "nombre": "Nox",
        "regex": re.compile(r"\bnox\b", re.IGNORECASE),
        "handler": _h_nox,
        "desc": "Oscurecer pantalla (brillo mínimo)",
    },
    {
        "nombre": "Accio",
        "regex": re.compile(r"\baccio\s+(.+)", re.IGNORECASE),
        "handler": _h_accio,
        "desc": "Invocar app o archivo (Accio Chrome, Accio notas.txt)",
    },
    {
        "nombre": "Silencio",
        "regex": re.compile(r"\bsilencio\b(?!\s+(?:por|señor|Computadora|gracias))", re.IGNORECASE),
        "handler": _h_silencio,
        "desc": "Mutear volumen",
    },
    {
        "nombre": "Sonorus",
        "regex": re.compile(r"\bsonorus\b", re.IGNORECASE),
        "handler": _h_sonorus,
        "desc": "Volumen al máximo",
    },
    {
        "nombre": "Alohomora",
        "regex": re.compile(r"\balohomora\b", re.IGNORECASE),
        "handler": _h_alohomora,
        "desc": "Abrir el Enciclopedia (libro_encantado)",
    },
    {
        "nombre": "Expecto Patronum",
        "regex": re.compile(r"\bexpecto\s+patronu?m\b", re.IGNORECASE),
        "handler": _h_expecto_patronum,
        "desc": "Demo visual del orbe (Mar'é HaMaljut)",
    },
    {
        "nombre": "Protego",
        "regex": re.compile(r"\bprotego\b", re.IGNORECASE),
        "handler": _h_protego,
        "desc": "Activar modo guardián",
    },
    {
        "nombre": "Stupefy",
        "regex": re.compile(r"\bstupef(?:y|ai)\b", re.IGNORECASE),
        "handler": _h_stupefy,
        "desc": "Dormir a Computadora",
    },
    {
        "nombre": "Expelliarmus",
        "regex": re.compile(r"\bexpell?iarmus\b", re.IGNORECASE),
        "handler": _h_expelliarmus,
        "desc": "Cerrar ventana activa (desarmar)",
    },
    {
        "nombre": "Wingardium Leviosa",
        "regex": re.compile(r"\bwingardium\s+leviosa\b", re.IGNORECASE),
        "handler": _h_wingardium_leviosa,
        "desc": "Mover el orbe hacia arriba",
    },
    {
        "nombre": "Revelio",
        "regex": re.compile(r"\brevelio\b", re.IGNORECASE),
        "handler": _h_revelio,
        "desc": "Info del sistema (hardware, red, etc.)",
    },
    {
        "nombre": "Reparo",
        "regex": re.compile(r"\breparo\b", re.IGNORECASE),
        "handler": _h_reparo,
        "desc": "Autodiagnóstico de Computadora",
    },
    {
        "nombre": "Obliviate",
        "regex": re.compile(r"\bobliviate\b", re.IGNORECASE),
        "handler": _h_obliviate,
        "desc": "Limpiar historial de conversación",
    },
    {
        "nombre": "Finite Incantatem",
        "regex": re.compile(r"\bfinite\s+incantatem\b", re.IGNORECASE),
        "handler": _h_finite_incantatem,
        "desc": "Cancelar operación actual",
    },
    {
        "nombre": "Muffliato",
        "regex": re.compile(r"\bmuffliato\b", re.IGNORECASE),
        "handler": _h_muffliato,
        "desc": "Modo sigiloso (Tzimtzum)",
    },
    {
        "nombre": "Riddikulus",
        "regex": re.compile(r"\bridd?ikulus\b", re.IGNORECASE),
        "handler": _h_riddikulus,
        "desc": "Contar un chiste / expresión artística",
    },
    {
        "nombre": "Tempus",
        "regex": re.compile(r"\btempus\b", re.IGNORECASE),
        "handler": _h_tempus,
        "desc": "Mostrar hora y fecha",
    },
    {
        "nombre": "Point Me / Orientame",
        "regex": re.compile(r"\b(?:point\s+me|ori[eé]ntame)\s+(.+)", re.IGNORECASE),
        "handler": _h_punto_me,
        "desc": "Buscar en internet",
    },
    {
        "nombre": "Homenum Revelio",
        "regex": re.compile(r"\bhomenum\s+revelio\b", re.IGNORECASE),
        "handler": _h_homenum_revelio,
        "desc": "Contexto de pantalla (qué apps están abiertas)",
    },
    {
        "nombre": "Prior Incantato",
        "regex": re.compile(r"\bprior\s+incantato\b", re.IGNORECASE),
        "handler": _h_prior_incantato,
        "desc": "Último comando/mensaje del usuario",
    },
    {
        "nombre": "Aparecium",
        "regex": re.compile(r"\baparecium\b", re.IGNORECASE),
        "handler": _h_aparecium,
        "desc": "Leer portapapeles (revelar lo oculto)",
    },
    {
        "nombre": "Arresto Momentum",
        "regex": re.compile(r"\barresto\s+momentum\b", re.IGNORECASE),
        "handler": _h_captura,
        "desc": "Captura de pantalla (congelar el momento)",
    },
    {
        "nombre": "Reducio",
        "regex": re.compile(r"\breducio\b", re.IGNORECASE),
        "handler": _h_reducio,
        "desc": "Minimizar a bandeja",
    },
    {
        "nombre": "Engorgio",
        "regex": re.compile(r"\bengorgio\b", re.IGNORECASE),
        "handler": _h_engorgio,
        "desc": "Restaurar ventana desde modo compacto",
    },
    # --- Maldiciones Imperdonables (BLOQUEADAS por Gevurá) ---
    {
        "nombre": "Avada Kedavra ⛔",
        "regex": re.compile(r"\bavada\s+kedavra\b", re.IGNORECASE),
        "handler": _h_imperio_bloqueado,
        "desc": "BLOQUEADA — Maldición asesina (viola Ley 1)",
    },
    {
        "nombre": "Crucio ⛔",
        "regex": re.compile(r"\bcrucio\b", re.IGNORECASE),
        "handler": _h_imperio_bloqueado,
        "desc": "BLOQUEADA — Maldición cruciatus (viola Ley 1)",
    },
    {
        "nombre": "Imperio ⛔",
        "regex": re.compile(r"\bimperio\b(?!\s+(?:romano|inca|otomano|brit[aá]nico))", re.IGNORECASE),
        "handler": _h_imperio_bloqueado,
        "desc": "BLOQUEADA — Maldición imperius (viola Ley 1)",
    },
]


def procesar_hechizo(cerebro, texto: str) -> str | None:
    """Busca un hechizo HP en el texto. Retorna respuesta o None si no matchea.

    Se llama desde _pensar_nivel1() en nlu.py.
    """
    tlow = texto.lower()
    for hechizo in HECHIZOS:
        m = hechizo["regex"].search(tlow)
        if m:
            logger.info(f"🪄 Hechizo detectado: {hechizo['nombre']}")
            cerebro._notificar_nivel("nivel1")
            try:
                return hechizo["handler"](cerebro, m, texto)
            except Exception as e:
                logger.error(f"Error ejecutando hechizo {hechizo['nombre']}: {e}")
                return f"El hechizo {hechizo['nombre']} falló, señor. Error: {e}"
    return None


def listar_hechizos() -> str:
    """Retorna lista formateada de todos los hechizos disponibles."""
    lineas = ["🪄 **Hechizos disponibles** (comandos de voz Harry Potter):\n"]
    for h in HECHIZOS:
        icon = "⛔" if "BLOQUEADA" in h["desc"] else "✨"
        lineas.append(f"  {icon} **{h['nombre']}** — {h['desc']}")
    return "\n".join(lineas)


