"""
הוד (Hod) — Esplendor. Recepción de la palabra.
Módulo de escucha — Captura audio del micrófono y transcribe con Whisper.
Detección de שם (Shem/Nombre) "COMPUTADORA" + filtrado de ruido.
"""

import queue
import re
import time
import unicodedata
import json
import zlib
import threading
from collections import deque
from difflib import SequenceMatcher
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import numpy as np
try:
    import torch
except ImportError:
    torch = None
from scipy.signal import resample
from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger

# 🔥 RUBEDO: Fuzzy Wake Word — FP-153: Auto-instalar si falta
try:
    from fuzzywuzzy import fuzz
    _FUZZY_AVAILABLE = True
except ImportError:
    fuzz = None
    _FUZZY_AVAILABLE = False
    # FP-153: Intenta instalar automáticamente
    try:
        from computadora.utilidad.auto_instalar_deps import intentar_importar
        if intentar_importar("fuzzywuzzy", "fuzzywuzzy"):
            from fuzzywuzzy import fuzz
            _FUZZY_AVAILABLE = True
            logger.info("✅ fuzzywuzzy instalado automáticamente")
        else:
            logger.warning("⚠️ fuzzywuzzy no disponible; usando fallback de SequenceMatcher para wake words")
    except Exception as e:
        logger.debug(f"FP-153: Error auto-instalando fuzzywuzzy: {e}")
        logger.debug("Usando fallback de SequenceMatcher para wake words")

try:
    import Levenshtein as _levenshtein
    _LEVENSHTEIN_AVAILABLE = True
except ImportError:
    _levenshtein = None
    _LEVENSHTEIN_AVAILABLE = False
    # FP-153: Intenta instalar automáticamente
    try:
        from computadora.utilidad.auto_instalar_deps import intentar_importar
        if intentar_importar("Levenshtein", "python-Levenshtein"):
            import Levenshtein as _levenshtein
            _LEVENSHTEIN_AVAILABLE = True
            logger.info("✅ python-Levenshtein instalado automáticamente")
    except Exception as e:
        logger.debug(f"FP-153: Error auto-instalando python-Levenshtein: {e}")

from computadora.voz.audio_log import registrar_evento as _log_audio
from computadora.voz.multi_microphone import MultiMicrophoneSystem

# ── RF-139: Silero VAD — Detección de Voz Humana pre-Whisper (FP-153: Auto-install) ──
# WI-PERF-CRITICAL: Lazy-init para NO bloquear imports. Cargamos solo en HiloEscucha.run()
_SILERO_VAD_MODEL = None
_SILERO_VAD_DISPONIBLE = False
_SILERO_VAD_LOADED = False  # Flag para lazy-loading
get_speech_timestamps = None  # Será importado en _ensure_silero_vad()

def _ensure_silero_vad():
    """Lazy-init Silero VAD solo cuando sea necesario (HiloEscucha.run())."""
    global _SILERO_VAD_MODEL, _SILERO_VAD_DISPONIBLE, _SILERO_VAD_LOADED, get_speech_timestamps
    
    if _SILERO_VAD_LOADED:
        return  # Ya cargado
    
    _SILERO_VAD_LOADED = True
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps as _gst
        _SILERO_VAD_MODEL = load_silero_vad()
        get_speech_timestamps = _gst
        _SILERO_VAD_DISPONIBLE = True
        logger.info("Silero VAD cargado correctamente (lazy-init)")
    except Exception as _e:
        _SILERO_VAD_MODEL = None
        get_speech_timestamps = None
        _SILERO_VAD_DISPONIBLE = False
        # FP-153: Intenta instalar automáticamente
        try:
            from computadora.utilidad.auto_instalar_deps import intentar_importar
            if intentar_importar("silero_vad", "silero-vad"):
                from silero_vad import load_silero_vad, get_speech_timestamps as _gst
                _SILERO_VAD_MODEL = load_silero_vad()
                get_speech_timestamps = _gst
                _SILERO_VAD_DISPONIBLE = True
                logger.info("✅ Silero VAD instalado automáticamente y cargado (lazy-init)")
            else:
                logger.warning(f"⚠️ Silero VAD no disponible: {_e}")
        except Exception as _e2:
            logger.warning(f"Silero VAD no disponible: {_e2}")

try:
    import librosa
    _LIBROSA_DISPONIBLE = True
except Exception as _e:
    librosa = None  # type: ignore[assignment]
    _LIBROSA_DISPONIBLE = False
    logger.debug("librosa no disponible: %s", _e)

# WI-BERESHIT-DEADLOCK-FIX: Lazy loading de Whisper — no cargar en __init__
# Se cargará solo cuando se necesite (primer uso de transcribir)
_WHISPER_MODELO = None
_WHISPER_CARGADO = False
_WHISPER_DISPOSITIVO = None

def _ensure_whisper_loaded(config):
    """Lazy-init Whisper solo cuando sea necesario (primera transcripción).
    
    NO se llama en __init__() — se llama en _bucle_escucha() cuando sea necesario.
    Permite que Qt event loop se inicie mientras Whisper se carga en background.
    """
    global _WHISPER_MODELO, _WHISPER_CARGADO, _WHISPER_DISPOSITIVO
    
    if _WHISPER_CARGADO:
        return _WHISPER_MODELO  # Ya cargado
    
    _WHISPER_CARGADO = True  # Marcar como "en progreso" para evitar reentrada
    
    try:
        import whisper
        
        # Obtener configuración de dispositivo
        dispositivo = config.obtener("escucha.whisper_dispositivo", None)
        modelo_nombre = config.obtener("whisper.modelo", "small")
        
        # Auto-detectar GPU si no se especificó
        if dispositivo is None:
            try:
                import torch
                if torch.cuda.is_available():
                    dispositivo = "cuda"
                else:
                    dispositivo = "cpu"
            except:
                dispositivo = "cpu"
        
        logger.info(f"🎧 Cargando modelo Whisper (lazy-init) '{modelo_nombre}' en '{dispositivo}'...")
        
        try:
            _WHISPER_MODELO = whisper.load_model(modelo_nombre, device=dispositivo)
            _WHISPER_DISPOSITIVO = dispositivo
            logger.info(f"✅ Whisper cargado exitosamente en {dispositivo}")
            
            # Verificar GPU si es CUDA
            if dispositivo.startswith("cuda"):
                try:
                    import numpy as np
                    logger.debug(f"Verificando GPU Whisper en {dispositivo}...")
                    dummy_audio = np.zeros((16000 * 3,), dtype=np.float32)
                    start_gpu_test = time.time()
                    _ = _WHISPER_MODELO.transcribe(dummy_audio, language="es", verbose=False)
                    gpu_test_time = time.time() - start_gpu_test
                    logger.info(f"✅ GPU funcional: dummy transcribe en {gpu_test_time:.2f}s")
                except Exception as e:
                    logger.warning(f"⚠️ GPU Whisper falló, retrocediendo a CPU: {e}")
                    _WHISPER_MODELO = whisper.load_model(modelo_nombre, device="cpu")
                    _WHISPER_DISPOSITIVO = "cpu"
        
        except Exception as e:
            logger.error(f"❌ Whisper: Error cargando en {dispositivo}: {e}")
            logger.info("Reintentando con CPU...")
            _WHISPER_MODELO = whisper.load_model(modelo_nombre, device="cpu")
            _WHISPER_DISPOSITIVO = "cpu"
            logger.info("✅ Whisper cargado en CPU (fallback)")
        
        return _WHISPER_MODELO
    
    except Exception as e:
        logger.critical(f"❌ Whisper no disponible: {e}")
        _WHISPER_MODELO = None
        return None

# Variantes fonéticas que Whisper puede producir para "COMPUTADORA" o legacy "Computadora"
_WAKE_WORD_RE = re.compile(
    r"\b(?:computadora|compu|computador)\b",
    re.IGNORECASE,
)

# שמות Shemot — Nombre completo "COMPUTADORA Emet" / legacy "Computadora Emet" (= regaño del propietario)
_RE_NOMBRE_COMPLETO = re.compile(
    r"\b(?:computadora|g[oó]l[eé][mn])\s+(?:[eé]met|embed|emmet|amet|emed|ahmed)\b",
    re.IGNORECASE,
)

# Apellido "Emet" como wake word formal (+ variantes Whisper base)
_RE_APELLIDO = re.compile(
    r"\b(?:[eé]met|embed|emmet|amet|emed|ahmed)\b", re.IGNORECASE,
)

# Apodo "Gol" / "Col" / "Go" — solo acepta en contexto vocativo
# Frontera \b obligatoria para no matchear "goles", "golpe", "color"
_RE_APODO = re.compile(r"\b(?:gol|col|go)\b", re.IGNORECASE)

# Patrones vocativos que validan al apodo como wake word
_RE_VOCATIVO_APODO = re.compile(
    r"(?:"
    # Cortesía + apodo al final: "hola gol", "buenos días gol"
    r"(?:hola|buenos?\s+d[ií]as?|buenas?\s+tardes?|buenas?\s+noches?|oye|hey|eh)\s+(?:gol|col|go)\b"
    r"|"
    # Apodo al inicio + orden/pregunta: "gol necesito", "gol busca", "col ayúdame"
    r"\b(?:gol|col|go)[,\s]+\S"
    r")",
    re.IGNORECASE,
)

# דעת Da'at — Cortesía sin wake word (saludos, despedidas, estado)
_RE_CORTESIA = re.compile(
    r"^\s*(?:"
    r"buenos?\s+d[ií]as?|buenas?\s+tardes?|buenas?\s+noches?"
    r"|hola(?:\s+hola)?"
    r"|adi[oó]s|hasta\s+luego|me\s+voy|ya\s+me\s+voy"
    r"|ya\s+llegu[eé]|ya\s+volv[ií]|estoy\s+aqu[ií]"
    r"|me\s+voy\s+a\s+dormir|ya\s+vengo|ya\s+regres[eé]"
    r")[\s.,!?]*$",
    re.IGNORECASE,
)

# Detección de preguntas de presencia para responder a "computadora, estás ahí?"
_RE_PRESENCIA = re.compile(
    r"\b(?:est(?:á|a)s?\s+(?:ah[ií]|ahi|aquí|aqui)|estoy\s+ah[ií]|estoy\s+aquí)\b",
    re.IGNORECASE,
)
_MIN_AUDIO_DURACION = 0.6
# Probabilidad máxima de no-speech de Whisper para aceptar
_MAX_NO_SPEECH_PROB = 0.6
# Ventana de conversación activa (segundos) — no requiere wake word
_VENTANA_CONVERSACION = 120.0  # 120s — conversación activa sin wake word
# WI-AUTONOMO-FIX: AUMENTADO de 0.68 a 0.88 para prevenir falsos positivos (e.g. audio de video)
_DEFAULT_VOX_THRESHOLD = 0.88  # Mucho más restrictivo: requiere similitud MUY alta sin wake word
_CONOCIDO_VOX_THRESHOLD = 0.35  # REDUCIDO de 0.40 a 0.35 para mejor reconocimiento
# WI-296: BAJADO threshold para mejor reconocimiento del dueño (solo con wake word)
_OWNER_VOX_THRESHOLD = 0.5  # Nuevo threshold más bajo para propietario
# RF-139: Umbral mínimo de probabilidad de voz humana (Silero VAD) — BAJADO para mejor detección
_MIN_SPEECH_PROB_VAD = 0.3
# RF-140: Umbral de entropía léxica para detectar hallucinations repetitivas
_ENTROPY_RATIO_UMBRAL = 0.4
_ENTROPY_MIN_PALABRAS = 4
# RF-140: Ratio de compresión textual para detectar repeticiones
_COMPRESSION_RATIO_UMBRAL = 0.5

# ── Correcciones post-transcripción de Whisper ──
# Palabras que Whisper transcribe incorrectamente de forma recurrente
_CORRECCIONES_WHISPER = {
    # Wake word variants
    "ahmed": "emet",
    "gordon": "computadora",
    "gorden": "computadora",
    "golen": "computadora",
    "goleen": "computadora",
    "gölem": "computadora",
    "conlem": "computadora",
    "colem": "computadora",
    "gonem": "computadora",
    "colom": "computadora",
    "conlém": "computadora",
    "conlen": "computadora",
    "golén": "computadora",
    "emmet": "emet",
    "emed": "emet",
    "amet": "emet",
    # Nombre del propietario — variantes Whisper
    "saudí": "esaú",
    "saudi": "esaú",
    "esau": "esaú",
    "azar": "díaz",
    "azernández": "díaz hernández",
    "azernandes": "díaz hernández",
    "asernández": "díaz hernández",
    "asernandes": "díaz hernández",
    "azernándes": "díaz hernández",
    "diaz": "díaz",
    "hernandes": "hernández",
    "ernández": "hernández",
    "ernandes": "hernández",
    # Frases comunes mal transcritas
    "te muestra de vos": "toma muestra de voz",
}

# Prompt inicial para Whisper — sesga la transcripción hacia vocabulario conocido
_WHISPER_INITIAL_PROMPT = (
    "Conversación con Computadora Emet, asistente de José Esaú Díaz Hernández. "
    "Computadora, Emet, Maljut, Tiféret, Gevurá, José Esaú, Díaz, Hernández. "
    "¿Dónde estás? ¿Cómo te llamas? ¿Qué haces?"
)
_RE_CORRECCIONES = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _CORRECCIONES_WHISPER) + r")\b",
    re.IGNORECASE,
)


def _corregir_nombre_propietario(texto: str) -> str:
    """Corrección fuzzy del nombre del propietario post-Whisper.

    Whisper frecuentemente mangla nombres propios multi-palabra.
    Usa SequenceMatcher para detectar variantes cercanas y corregirlas.
    """
    _NOMBRE_COMPLETO = "José Esaú Díaz Hernández"
    _FRAGMENTOS = {
        "josé esaú": "José Esaú",
        "díaz hernández": "Díaz Hernández",
        "josé": "José",
        "esaú": "Esaú",
        "díaz": "Díaz",
        "hernández": "Hernández",
    }
    resultado = texto
    t_low = resultado.lower()
    for patron, correcto in _FRAGMENTOS.items():
        # Buscar variantes fuzzy — si una subseq del texto es >0.7 similar al patrón
        plen = len(patron)
        for i in range(len(t_low) - plen + 1):
            sub = t_low[i:i + plen + 3]  # +3 tolerancia de longitud
            ratio = SequenceMatcher(None, patron, sub[:plen]).ratio()
            if ratio >= 0.70 and sub[:plen] != patron:
                # Reemplazar la subcadena original por la versión correcta
                original_sub = resultado[i:i + plen]
                resultado = resultado[:i] + correcto + resultado[i + plen:]
                t_low = resultado.lower()
                break
    return resultado


# ── Filtro de falsos positivos por ruido corporal/ambiental ──
# Palabras inglesas cortas que Whisper genera al escuchar tos, ruido, etc.
_FALSOS_POSITIVOS_EN = frozenset({
    "die", "proud", "bye", "hi", "the", "a", "i", "oh", "so", "do",
    "go", "no", "you", "me", "he", "she", "we", "my", "to", "up",
    "it", "at", "an", "or", "is", "am", "be", "in", "on", "of",
    "if", "as", "by", "us", "ok", "uh", "ah", "um", "hm", "eh",
    "wow", "hey", "ya", "yep", "nah", "nope", "huh", "hmm",
    "thanks", "thank", "please", "sorry", "yes", "yeah",
    "one", "two", "three", "four", "five", "six", "set", "get",
    "but", "not", "all", "was", "are", "has", "had", "her", "his",
    "out", "can", "may", "let", "say", "see", "how", "now", "new",
    "our", "way", "who", "did", "got", "put", "run", "too",
})

# Palabras/frases comunes que Whisper genera de ruido ambiental
_FRASES_RUIDO = frozenset({
    "subtítulos", "suscríbete", "amara.org", "mokaplayer",
    "gracias por ver", "subtitulado por", "suscríbete al canal",
    "gracias.", "¡suscríbete!", "thank you for watching",
    "thanks for watching",
})

# Palabras españolas cortas válidas que NO deben descartarse
_ESPAÑOL_CORTAS_VALIDAS = frozenset({
    "sí", "no", "ya", "te", "se", "es", "en", "el", "la", "lo",
    "un", "tu", "mi", "de", "al", "yo", "ir", "da", "más", "qué",
    "hay", "eso", "esa", "ese", "uno", "dos", "vez", "ver",
    "hoy", "ayer", "bien", "mal", "aquí", "ven", "hola",
    "dame", "dime", "oye", "para", "como", "cosa",
    # Palabras sin acento que son español válido (no confundir con inglés)
    "que", "esta", "esto", "pero", "por", "con", "sin", "mas",
    "muy", "del", "les", "nos", "sus", "son", "ser", "tan",
    "fue", "era", "van", "esa", "sol", "fin", "si", "algo",
    "alegra", "contento", "mucho", "poco", "mejor", "peor",
    "nuevo", "todo", "cada", "otro", "mismo", "solo",
    # Palabras largas válidas en conversación sin wake word
    "gracias", "claro", "exacto", "perfecto", "listo", "vale",
    "bueno", "cierto", "correcto", "entendido", "repite",
    "detente", "silencio", "espera", "continua", "siguiente",
    "adelante", "nada", "nunca", "siempre", "ayuda",
    "adiós", "búscalo", "repítelo", "cállate", "muéstrame",
    "explica", "hazlo", "déjalo", "apaga", "prende",
    # Variantes Whisper de "maljut" (demo visual) — RF-130
    "maljut", "malkut", "malcut", "malhut", "malhud", "maljud",
})


def _es_hallucination_repetitiva(texto: str) -> str:
    """RF-140: Detecta hallucinations repetitivas de Whisper por entropía léxica.

    Retorna motivo del descarte o cadena vacía si es válido.
    Ejemplo: '¡La, la, la, la, la! ¡La, la, la!' → ratio 0.14 → DESCARTAR
    """
    # Limpiar puntuación para contar palabras reales
    limpio = re.sub(r"[^\w\s]", "", texto.lower()).strip()
    palabras = limpio.split()
    n = len(palabras)
    if n < _ENTROPY_MIN_PALABRAS:
        return ""

    # Entropía léxica: ratio de palabras únicas vs total
    unicas = len(set(palabras))
    ratio = unicas / n
    if ratio < _ENTROPY_RATIO_UMBRAL:
        return f"hallucination_repetitiva:ratio={ratio:.2f},unicas={unicas},total={n}"

    # Compresión textual: texto muy repetitivo comprime mucho
    texto_bytes = limpio.encode("utf-8")
    if len(texto_bytes) > 10:
        comprimido = zlib.compress(texto_bytes, 9)
        ratio_compresion = len(comprimido) / len(texto_bytes)
        if ratio_compresion < _COMPRESSION_RATIO_UMBRAL:
            return f"hallucination_compresion:ratio={ratio_compresion:.2f}"

    return ""


def _es_falso_positivo_conversacion(texto: str, no_speech_prob: float = 0.0) -> str:
    """Detecta falsos positivos durante conversación activa en español.

    Retorna motivo del descarte o cadena vacía si es válido.
    """
    t = texto.strip()
    t_low = t.lower()

    # Frase de ruido conocida
    if t_low in _FRASES_RUIDO or t_low.rstrip(".!?,") in _FRASES_RUIDO:
        return "frase_ruido_conocida"

    palabras = t_low.split()
    n_palabras = len(palabras)

    # Una sola palabra en inglés (sin caracteres españoles) = casi seguro falso positivo
    if n_palabras == 1:
        palabra = t_low.rstrip(".!?,;:¡¿")
        if palabra in _FALSOS_POSITIVOS_EN:
            return f"palabra_inglesa_sola:{palabra}"
        # Cualquier palabra sola de ≤4 chars sin acentos españoles típicos
        if len(palabra) <= 4 and not re.search(r"[áéíóúñü]", palabra):
            # Verificar que no sea una palabra española válida corta
            if palabra not in _ESPAÑOL_CORTAS_VALIDAS:
                return f"palabra_corta_no_española:{palabra}"
        # Palabra sola ≥5 chars que no es español reconocible = ruido transcrito
        # En conversación sin wake word, una sola palabra rara vez es comando legítimo
        if len(palabra) >= 5 and palabra not in _ESPAÑOL_CORTAS_VALIDAS:
            # Contar acentos españoles reales (no contar solo 1 acento en palabra mayormente ASCII)
            acentos = len(re.findall(r"[áéíóúñü]", palabra))
            if acentos <= 1:
                return f"palabra_sola_no_reconocida:{palabra}"

    # Dos palabras, ambas inglesas, sin sentido en español
    if n_palabras == 2:
        p1, p2 = [w.rstrip(".!?,;:") for w in palabras]
        if p1 in _FALSOS_POSITIVOS_EN and p2 in _FALSOS_POSITIVOS_EN:
            return f"par_ingles:{p1}_{p2}"

    # Frase mixta español+inglés con mayoría de palabras inglesas = ruido de Whisper
    # Ejemplo real: "el medio noche. ¡EN cut meanwhile tomorrow!"
    # NOTA: Solo contar palabras que están en _FALSOS_POSITIVOS_EN (inglés conocido).
    # NO asumir que cualquier palabra ASCII sin acento es inglesa — muchas
    # palabras españolas válidas son ASCII puro (alegra, contento, como, etc.)
    if n_palabras >= 3:
        palabras_limpias = [w.rstrip(".!?,;:¡¿") for w in palabras]
        n_en = sum(1 for w in palabras_limpias if w in _FALSOS_POSITIVOS_EN)
        ratio_en = n_en / n_palabras
        if ratio_en >= 0.5 and n_en >= 2:
            return f"frase_mixta_mayoria_ingles:{ratio_en:.0%}"

    # RF-246 Shomer HaLashón: Frase con CERO palabras español reconocible.
    # Ejemplo real: "hu trails team. 3" — ninguna palabra está en español.
    # Palabras alfanuméricas que no son español válido NI tienen acentos = basura.
    if n_palabras >= 2:
        palabras_limpias = [w.rstrip(".!?,;:¡¿") for w in palabras]
        solo_alfa = [w for w in palabras_limpias if w.isalpha()]
        if solo_alfa:
            n_es = sum(
                1 for w in solo_alfa
                if w in _ESPAÑOL_CORTAS_VALIDAS or re.search(r"[áéíóúñü]", w)
            )
            if n_es == 0:
                return f"cero_español_reconocible:{len(solo_alfa)}_palabras_sin_español"

    # No-speech prob alta + texto muy corto = sospechoso
    if no_speech_prob > 0.4 and n_palabras <= 2:
        return f"no_speech_alto_texto_corto:{no_speech_prob:.2f}"

    # FP-045C: Alucinación Whisper — caracteres no-latinos (CJK, cirílico, árabe, etc.)
    # Whisper a veces genera basura con ideogramas cuando el audio es ruido/media.
    if re.search(r'[\u3000-\u9fff\u4e00-\u9fff\uff00-\uffef\u0400-\u04ff\u0600-\u06ff\u3040-\u309f\u30a0-\u30ff]', t):
        return "alucinacion_whisper_chars_no_latinos"

    return ""


class HiloEscucha(QThread):
    """Hilo que escucha continuamente el micrófono y emite texto transcrito."""

    texto_detectado = pyqtSignal(str)
    estado_cambio = pyqtSignal(str)  # "escuchando", "procesando", "inactivo", "error"
    voz_activa = pyqtSignal()  # Emitida cuando se detecta voz (para ripple visual sin cambiar estado)
    mensaje_sistema = pyqtSignal(str)
    interrupcion_detectada = pyqtSignal(str)  # Emitida cuando el usuario interrumpe durante TTS

    def __init__(self, config):
        super().__init__()
        self._config = config
        self._activo = True
        self._pausado = False
        self._texto_recitando = ""  # Texto TTS en curso, para filtrar eco propio
        self._modelo = None
        # WI-BERESHIT-DEADLOCK-FIX: Lazy loading de Whisper (no cargar en __init__)
        self._modelo_whisper_cargado = False  # Flag para lazy-init
        self._umbral = config.obtener("escucha.umbral_volumen", 0.03)  # FP-044B: Aumentado 0.015→0.03 (menos sensible a ruido)
        self._umbral_base = self._umbral
        # Multiplicador configurable: con bocina externa (más volumen/reverberación
        # que el altavoz interno de una laptop) puede necesitar subirse más de 8x
        # para que la VAD deje de disparar con la propia voz de Computadora.
        self._umbral_habla = self._umbral * config.obtener("escucha.umbral_habla_mult", 8)
        self._silencio_max = config.obtener("escucha.silencio_max_segundos", 3.0)  # FP-044B: Aumentado 1.5→3.0s (timeout más largo)
        self._duracion_max_captura = 15.0  # FP-044B: NUEVO — máximo 15s de captura sin importar ruido
        self._fs = config.obtener("escucha.frecuencia_muestreo", 16000)  # FIX: Restaurado (accidental delete)
        self._ultimo_intercambio = 0.0  # timestamp del último intercambio
        # Variantes aprendidas del wake word basadas en tu pronunciación
        self._wake_variants: set[str] = set()
        # Path para persistir variantes aprendidas
        datos_dir = Path(__file__).resolve().parent.parent.parent / "datos"
        datos_dir.mkdir(parents=True, exist_ok=True)
        self._wake_variants_path = datos_dir / "wake_variants.json"
        # cargar variantes si existen
        try:
            if self._wake_variants_path.exists():
                loaded = json.loads(self._wake_variants_path.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    self._wake_variants.update(v for v in loaded if isinstance(v, str))
        except (json.JSONDecodeError, OSError) as e:
            logger.exception("Error cargando wake_variants.json")
        # Umbral de correlación estéreo para detectar múltiples hablantes
        self._stereo_multi_threshold = 0.6
        # Estado de confirmación cuando Computadora pregunta "¿Me hablas a mí?"
        self._esperando_confirmacion = False
        self._confirmacion_origen = None
        # Bandera: Computadora hizo una pregunta y espera respuesta (relaja filtro FP)
        self._esperando_respuesta = False
        self._esperando_respuesta_ts = 0.0  # FP-046A: timestamp de activación
        _TIMEOUT_ESPERANDO_RESPUESTA = 30.0  # segundos
        # Bandera sobre si el último interlocutor fue el propietario reconocido
        self._ultima_interlocutor_es_propietario = False
        # Clasificación de hablante: "amo", "conocido", "extraño"
        self.clasificacion_hablante = "desconocido"
        # Perfil del propietario (embedding) — se carga/guarda en datos/
        self._owner_profile = None
        self._owner_count = 0
        self._vox_threshold = config.obtener("escucha.verificacion_vox_threshold", _DEFAULT_VOX_THRESHOLD)
        self._owner_profile_path = datos_dir / "owner_profile.json"
        # Cargar perfil si existe
        try:
            if self._owner_profile_path.exists():
                op = json.loads(self._owner_profile_path.read_text(encoding="utf-8"))
                emb = op.get("embedding")
                cnt = int(op.get("count", 0))
                if isinstance(emb, list) and len(emb) > 0:
                    self._owner_profile = np.array(emb, dtype=float)
                    self._owner_count = cnt
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.debug("No se pudo cargar owner_profile.json")
        # Flag para enrolamiento manual: la próxima muestra registrada actualizará el perfil
        self._force_enroll = False
        # WI-DETECTAR-PROPIETARIO-DISABLED: Desactivar reconocimiento de propietario sin wake word (FP-048 — solicitud de usuario)
        # Si False: NO activar por voz propietario sin wake word
        # Si True: Permitir activación por voz propietario sin wake word
        self._detectar_propietario_sin_wake = False
        # הכרת פנים Hakarat Panim — Personas conocidas
        self._personas_path = datos_dir / "personas_conocidas.json"
        self._personas_conocidas: list[dict] = []
        self._cargar_personas()
        # Modo enrolamiento: nombre de persona a registrar con la próxima muestra de voz
        self._enroll_persona_nombre: str | None = None
        # HF-024a: Flag seteado por ventana_principal cuando el orbe está pensando
        self._pensando_flag = False
        # WI-CRIT-TRANSCRIPTION: Synchronization lock para evitar re-entrant _transcribir() calls
        self._transcribiendo_lock = threading.Lock()
        self._transcribiendo = False
        # FP-044: Referencia a ContextoPantalla para detectar media activa
        self._contexto_pantalla = None
        # FP-044: Flag para loguear librosa solo una vez
        self._librosa_warned = False

        # 🎙️ MULTI-MICROPHONE SYSTEM — DESACTIVADO (WI-CRIT: causa problemas de cascada)
        # No inicializar en __init__ porque causa problemas en QThread
        self._multi_mic = None
        self._use_multi_mic = False
        _allow_multi_mic = False  # ← WI-CRIT-MULTIMIC: FORCE DISABLED
        self._allow_multi_mic = False  # Forzado desactivado hasta próximo fix
        logger.info(
            "🎙️ Sistema multi-micrófono en modo lazy (%s)",
            "habilitado" if self._allow_multi_mic else "deshabilitado"
        )

        # 🔥 METATRÓN INTEGRATION — Orquestador central
        self.metatron = None  # Se asigna desde main

        # 🔥 ECHO-FILTERING TIMESTAMP-BASED — Buffer inteligente con timing mejorado
        self.tts_buffer = []  # Lista de dicts: {'timestamp_start', 'timestamp_end', 'texto', 'activo'}
        self._lock = threading.Lock()  # Para sincronización tts_buffer — WI-CRIT-ECHO

    def registrar_tts_output(self, texto: str):
        """Llamado por TTS antes de hablar"""
        with self._lock:
            self.tts_buffer.append({
                'timestamp': time.time(),
                'texto': texto.lower(),
                'activo': True,
                'fin_ts': None,
            })
            # Cleanup: remove old entries (>30s)
            cutoff = time.time() - 30
            self.tts_buffer = [b for b in self.tts_buffer if b['timestamp'] > cutoff]

    def marcar_tts_completado(self):
        """Llamado por TTS al terminar"""
        with self._lock:
            if self.tts_buffer:
                self.tts_buffer[-1]['activo'] = False
                self.tts_buffer[-1]['fin_ts'] = time.time()

    def _check_echo_timestamp(self, texto_usuario: str) -> tuple[bool, Optional[str]]:
        """
        Returns: (is_echo, interrupted_content)
        Si es echo: True, None
        Si es interrupción: False, contenido_interrumpido

        FIX: antes solo se comparaba contra entradas con 'activo'==True — si el
        audio del propio eco quedaba atrapado en el buffer de captura justo
        cuando marcar_tts_completado() ya había marcado la entrada como
        inactiva (habitual con bocina externa: más distancia/reverberación
        añade latencia entre que el audio termina de sonar y Whisper termina
        de transcribirlo), ese eco no se comparaba contra nada y pasaba
        directo como voz nueva. Ahora también se compara contra la última
        entrada ya terminada durante un margen de gracia configurable.
        """
        margen_gracia = self._config.obtener("escucha.eco_margen_gracia_s", 2.5)
        ratio_echo = self._config.obtener("escucha.eco_ratio_echo", 0.70)
        ratio_interrupcion = self._config.obtener("escucha.eco_ratio_interrupcion", 0.35)
        with self._lock:
            ahora = time.time()
            texto_lower = texto_usuario.lower()

            for tts_entry in self.tts_buffer:
                if not tts_entry['activo']:
                    fin_ts = tts_entry.get('fin_ts')
                    if fin_ts is None or (ahora - fin_ts) > margen_gracia:
                        continue  # TTS ya terminó hace rato — no comparar

                # Check similarity
                ratio = SequenceMatcher(None, texto_lower, tts_entry['texto']).ratio()

                if ratio >= ratio_echo:  # Muy similar = echo
                    return True, None
                elif ratio >= ratio_interrupcion:  # Similar pero no tanto = posible interrupción
                    # Calcular qué parte del TTS fue interrumpida
                    matcher = SequenceMatcher(None, texto_lower, tts_entry['texto'])
                    opcodes = matcher.get_opcodes()
                    partes = [texto_lower[a:b] for tag, a, b, c, d in opcodes if tag in ('replace', 'delete') and a < b]
                    contenido_interrumpido = ' '.join(partes).strip() if partes else texto_lower
                    return False, contenido_interrumpido
        return False, None

    def _fuzzy_ratio(self, a: str, b: str) -> float:
        if _FUZZY_AVAILABLE and fuzz is not None:
            try:
                return fuzz.ratio(a, b)
            except Exception as e:
                logger.debug("Error en fuzzywuzzy ratio: %s", e)
        if _LEVENSHTEIN_AVAILABLE and _levenshtein is not None:
            try:
                distancia = _levenshtein.distance(a, b)
                longitud = max(len(a), len(b), 1)
                return max(0.0, (1.0 - distancia / longitud) * 100.0)
            except Exception as e:
                logger.debug("Error en Levenshtein ratio: %s", e)
        return SequenceMatcher(None, a, b).ratio() * 100.0

    def _check_wake_word_fuzzy(self, texto: str) -> bool:
        """Wake word con typo tolerance usando fuzzy matching o SequenceMatcher."""
        tokens = re.findall(r"\w+", texto.lower())
        if not tokens:
            return False

        for token in tokens:
            # Exact matches
            if token in ['computadora', 'computa', 'compu']:
                return True
            if token in self._wake_variants:
                return True
            # Fuzzy matching con fuzzywuzzy/Levenshtein/SequenceMatcher
            ratio = self._fuzzy_ratio(token, 'computadora')
            if ratio >= 78.0:
                return True
            if len(token) <= 7 and ratio >= 68.0:
                return True
        return False

    def pausar(self):
        self._pausado = True

    def reanudar(self):
        self._pausado = False

    def subir_umbral(self):
        """Sube umbral durante habla para ignorar la voz del parlante."""
        self._umbral = self._umbral_habla
        self._tts_inicio_ts = time.time()  # RF-275: timestamp guard
        logger.debug(f"Umbral subido a {self._umbral:.4f} (Computadora hablando)")

    def restaurar_umbral(self):
        """Restaura umbral normal después de hablar."""
        self._umbral = self._umbral_base
        logger.debug(f"Umbral restaurado a {self._umbral:.4f}")

    def set_texto_recitando(self, texto: str):
        """Registra el texto que TTS va a recitar, para filtrar eco propio."""
        self._texto_recitando = (self._texto_recitando + " " + texto).strip()
        logger.debug(f"Texto recitando actualizado ({len(self._texto_recitando)} chars)")

    def limpiar_texto_recitando(self):
        """Limpia el texto de recitación (TTS terminó)."""
        self._texto_recitando = ""

    def _cargar_wake_variants(self):
        try:
            if self._wake_variants_path.exists():
                data = json.loads(self._wake_variants_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, OSError) as e:
            logger.exception("Error leyendo wake_variants.json")
        return []

    def _guardar_wake_variant(self, variant: str):
        variant = variant.strip().lower()
        if not variant:
            return
        if variant in self._wake_variants:
            return
        # add to set and persist as list
        try:
            self._wake_variants.add(variant)
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(self._wake_variants_path, list(self._wake_variants))
            logger.info(f"Wake-variant aprendida: '{variant}'")
        except OSError as e:
            logger.exception("Error persistiendo wake variant")

    # ---------------------- Verificación de voz (timbre) ----------------------
    def _save_owner_profile(self):
        try:
            if self._owner_profile is None:
                return
            payload = {"embedding": self._owner_profile.tolist(), "count": int(self._owner_count)}
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(self._owner_profile_path, payload)
            logger.debug("Owner profile guardado")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error guardando owner_profile")

    # ---- הכרת פנים Hakarat Panim — Personas conocidas ----
    def _cargar_personas(self):
        try:
            if self._personas_path.exists():
                data = json.loads(self._personas_path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "personas" in data:
                    self._personas_conocidas = data["personas"]
                    logger.info(f"Cargadas {len(self._personas_conocidas)} personas conocidas")
        except (json.JSONDecodeError, OSError) as e:
            logger.exception("Error cargando personas_conocidas.json")

    def _guardar_personas(self):
        try:
            payload = {"personas": self._personas_conocidas}
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(self._personas_path, payload)
            logger.debug("personas_conocidas.json guardado")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error guardando personas_conocidas")

    def iniciar_enroll_persona(self, nombre: str):
        """Activa modo enrolamiento: la próxima voz no-amo se registra como persona."""
        self._enroll_persona_nombre = nombre
        logger.info(f"Modo enroll activado para: {nombre}")

    def _enroll_persona(self, nombre: str, emb: list):
        """Registra o actualiza el embedding de una persona conocida."""
        vec = np.array(emb, dtype=float)
        vec = vec / (np.linalg.norm(vec) + 1e-12)
        # FP-019: Delegar a GestorPersonas si disponible
        gestor = getattr(self, '_gestor_personas', None)
        if gestor:
            existente = gestor.obtener_persona(nombre)
            if existente:
                gestor.actualizar_embedding(nombre, vec.tolist())
                logger.info(f"Persona actualizada via GestorPersonas: {nombre}")
            else:
                gestor.registrar_persona(nombre, embedding=vec.tolist(), presentado_por="propietario")
                logger.info(f"Nueva persona registrada via GestorPersonas: {nombre}")
            return
        # Fallback: JSON plano (legacy)
        # Buscar si ya existe
        for p in self._personas_conocidas:
            if p.get("nombre", "").lower() == nombre.lower():
                cnt = max(1, int(p.get("count", 1)))
                old = np.array(p["embedding"], dtype=float)
                p["embedding"] = ((old * cnt + vec) / (cnt + 1)).tolist()
                p["count"] = cnt + 1
                self._guardar_personas()
                logger.info(f"Persona actualizada: {nombre} (count={p['count']})")
                return
        # Nueva persona
        from datetime import date
        self._personas_conocidas.append({
            "nombre": nombre,
            "embedding": vec.tolist(),
            "count": 1,
            "fecha_conocido": str(date.today()),
            "presentado_por": "propietario",
        })
        self._guardar_personas()
        logger.info(f"Nueva persona registrada: {nombre}")

    def _identificar_persona(self, emb: list) -> str | None:
        """Compara embedding contra personas conocidas. Retorna nombre o None."""
        # FP-019: Delegar a GestorPersonas si disponible
        gestor = getattr(self, '_gestor_personas', None)
        if gestor:
            nombre, sim = gestor.identificar_por_voz(emb)
            if nombre:
                logger.debug(f"Persona identificada via GestorPersonas: {nombre} (sim={sim:.2f})")
            return nombre
        # Fallback: JSON plano (legacy)
        if not self._personas_conocidas:
            return None
        mejor_sim = 0.0
        mejor_nombre = None
        for p in self._personas_conocidas:
            p_emb = p.get("embedding")
            if not p_emb:
                continue
            sim = self._cosine_similarity(emb, p_emb)
            if sim > mejor_sim:
                mejor_sim = sim
                mejor_nombre = p.get("nombre")
        if mejor_sim >= _CONOCIDO_VOX_THRESHOLD:
            return mejor_nombre
        return None


    def _update_owner_profile(self, emb: list):
        try:
            vec = np.array(emb, dtype=float)
            if vec.size == 0:
                logger.warning("Embedding vacío, no se actualiza owner_profile")
                return
            # normalizar
            norm = np.linalg.norm(vec) + 1e-12
            vec = vec / norm
            if self._owner_profile is None:
                self._owner_profile = vec
                self._owner_count = 1
            else:
                if self._owner_profile.shape != vec.shape:
                    L = min(self._owner_profile.shape[0], vec.shape[0])
                    logger.debug(
                        "Ajustando owner_profile (%d -> %d) y nueva muestra a longitud mínima",
                        self._owner_profile.shape[0], L
                    )
                    self._owner_profile = self._owner_profile[:L]
                    vec = vec[:L]
                cnt = max(1, int(self._owner_count))
                self._owner_profile = (self._owner_profile * cnt + vec) / (cnt + 1)
                self._owner_count = cnt + 1
            self._save_owner_profile()
            logger.info("Perfil de voz del propietario actualizado")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error actualizando perfil de voz")

    def _cosine_similarity(self, a, b):
        try:
            a = np.array(a, dtype=float)
            b = np.array(b, dtype=float)
            la = a.shape[0]
            lb = b.shape[0]
            if la != lb:
                # ajustar al tamaño mínimo para estabilidad
                L = min(la, lb)
                a = a[:L]
                b = b[:L]
            na = np.linalg.norm(a) + 1e-12
            nb = np.linalg.norm(b) + 1e-12
            return float(np.dot(a, b) / (na * nb))
        except (ValueError, TypeError) as e:
            logger.exception("Error calculando similitud coseno")
            return 0.0

    def _extraer_embedding(self, audio: np.ndarray, sr: int):
        """Extrae un embedding corto del audio para verificación de hablante.

        Intenta usar `librosa` para MFCCs; si no está disponible, usa
        características espectrales simples como fallback.
        """
        try:
            if _LIBROSA_DISPONIBLE and librosa:
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)
                mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=20)
                emb = np.mean(mfcc, axis=1)
                # normalizar
                emb = emb / (np.linalg.norm(emb) + 1e-12)
                return emb.tolist()
            else:
                # Fallback: características espectrales simples
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32)
                # FFT simple para características básicas
                fft = np.fft.rfft(audio)
                mag = np.abs(fft)
                # Tomar primeras 20 componentes como "embedding" básico
                emb = mag[:20] / (np.linalg.norm(mag[:20]) + 1e-12)
                return emb.tolist()
        except Exception as e:
            if not self._librosa_warned:
                logger.debug("Error extrayendo embedding: %s", e)
                self._librosa_warned = True
            try:
                # fallback: estadísticas simples del espectro
                from scipy.signal import stft

                f, t, Zxx = stft(audio, fs=sr, nperseg=512)
                mag = np.abs(Zxx) + 1e-12
                centroid = (f[:, None] * mag).sum(axis=0) / mag.sum(axis=0)
                roll = np.sum(np.cumsum(mag, axis=0) >= 0.85 * mag.sum(axis=0), axis=0)
                features = [np.mean(centroid), np.std(centroid), np.mean(roll), np.std(roll), np.mean(np.abs(audio)), np.std(np.abs(audio))]
                emb = np.array(features, dtype=float)
                emb = emb / (np.linalg.norm(emb) + 1e-12)
                return emb.tolist()
            except Exception as e:
                logger.debug("Fallback espectral falló, usando energía+zcr: %s", e)
                # fallback mínimo: energía + zcr
                try:
                    zcr = ((audio[:-1] * audio[1:]) < 0).mean()
                except (ValueError, IndexError) as e:
                    logger.debug("Error calculando ZCR: %s", e)
                    zcr = 0.0
                e = float(np.mean(audio ** 2))
                emb = np.array([e, zcr], dtype=float)
                emb = emb / (np.linalg.norm(emb) + 1e-12)
                return emb.tolist()
            # Fallback final: vector cero
            return [0.0] * 20


    def marcar_intercambio(self, owner: bool = False):
        """Marca que hubo un intercambio — abre ventana sin wake word.

        Si `owner` es True se marca que el último interlocutor fue el
        propietario reconocido, permitiendo follow-ups sin wake word.
        """
        self._ultimo_intercambio = time.monotonic()
        if owner:
            self._ultima_interlocutor_es_propietario = True

    @property
    def _en_conversacion(self) -> bool:
        """True si estamos dentro de la ventana de conversación activa y
        el último interlocutor fue el propietario reconocido.
        """
        if not self._ultima_interlocutor_es_propietario:
            return False
        return (time.monotonic() - self._ultimo_intercambio) < _VENTANA_CONVERSACION

    def detener(self):
        self._activo = False

    def _encontrar_mejor_dispositivo(self):
        """Detecta el mejor dispositivo de input (micrófono).

        Retorna: (device_id, sample_rate, channels)
        - Intenta leer config de escucha.dispositivo (legacy support)
        - Si no existe, usa el dispositivo de input DEFAULT real del sistema
          (sd.default.device / sd.query_devices(kind='input')), evitando
          meta-dispositivos de enrutamiento tipo "Sound Mapper" (Windows MME)
        - Si eso falla, busca el primer dispositivo de input real (no-mapper)
        - Último recurso: primer dispositivo de input que exista, aunque sea
          un mapper (mejor eso que no abrir ningún stream)
        """
        import sounddevice as sd

        # FIX #2.1: Intentar leer dispositivo configurado
        dispositivo_cfg = self._config.obtener("escucha.dispositivo", None)
        if dispositivo_cfg is not None and isinstance(dispositivo_cfg, int):
            try:
                info = sd.query_devices(dispositivo_cfg)
                if info['max_input_channels'] > 0:
                    sr = int(info.get('default_samplerate', 44100))
                    ch = min(2, int(info.get('max_input_channels', 1)))
                    logger.info(f"📍 Dispositivo escucha configurado: [{dispositivo_cfg}] {info.get('name')} @ {sr}Hz, {ch}ch")
                    return dispositivo_cfg, sr, ch
            except Exception as e:
                logger.warning(f"⚠️ Dispositivo configurado [{dispositivo_cfg}] no disponible: {e}")

        def _es_mapper(nombre: str) -> bool:
            n = (nombre or "").lower()
            return "sound mapper" in n or "mapper" in n or "asignador de sonido" in n

        # FIX: preferir el dispositivo de input DEFAULT real del sistema ANTES
        # que la enumeración naive — en Windows/MME el primer dispositivo con
        # max_input_channels > 0 suele ser el meta-dispositivo "Microsoft
        # Sound Mapper - Input" (índice 0), que abre un InputStream válido
        # pero puede entregar silencio/basura en vez de audio real del
        # micrófono físico, dejando la app "sorda" sin ningún error visible.
        try:
            idx_default = sd.default.device[0] if sd.default.device else None
            if idx_default is not None and idx_default >= 0:
                info = sd.query_devices(idx_default)
                if info.get('max_input_channels', 0) > 0 and not _es_mapper(info.get('name', '')):
                    sr = int(info.get('default_samplerate', 44100))
                    ch = min(2, int(info.get('max_input_channels', 1)))
                    logger.info(f"📍 Dispositivo input default del sistema: [{idx_default}] {info.get('name')} @ {sr}Hz, {ch}ch")
                    return idx_default, sr, ch
        except Exception as e:
            logger.debug(f"No se pudo leer sd.default.device: {e}")

        # FIX #2.2: Auto-detectar primer dispositivo de input real (NO mapper)
        try:
            dispositivos = sd.query_devices()
            candidato_mapper = None
            for idx, d in enumerate(dispositivos):
                if d.get('max_input_channels', 0) > 0:
                    if _es_mapper(d.get('name', '')):
                        if candidato_mapper is None:
                            candidato_mapper = (idx, d)
                        continue
                    sr = int(d.get('default_samplerate', 44100))
                    ch = min(2, int(d.get('max_input_channels', 1)))
                    logger.info(f"📍 Auto-detectado dispositivo input: [{idx}] {d.get('name')} @ {sr}Hz, {ch}ch")
                    return idx, sr, ch
            # Último recurso: un mapper es mejor que ningún dispositivo
            if candidato_mapper is not None:
                idx, d = candidato_mapper
                sr = int(d.get('default_samplerate', 44100))
                ch = min(2, int(d.get('max_input_channels', 1)))
                logger.warning(
                    f"⚠️ Solo se encontró un dispositivo mapper/virtual: [{idx}] {d.get('name')} — "
                    "puede no capturar audio real. Configure 'escucha.dispositivo' manualmente si no responde."
                )
                return idx, sr, ch
        except Exception as e:
            logger.warning(f"⚠️ Error auto-detectando dispositivos: {e}")

        # Fallback: usar dispositivo default del sistema
        logger.info("📍 Usando dispositivo input default del sistema")
        try:
            default_info = sd.query_devices(kind='input')
            sr = int(default_info.get('default_samplerate', 44100))
            ch = min(2, int(default_info.get('max_input_channels', 1)))
            return None, sr, ch
        except Exception:
            return None, 44100, 1

    def run(self):
        """Inicia el bucle de escucha (ejecuta en QThread)."""
        logger.info("🎧 HiloEscucha.run() — iniciando escucha en QThread")
        # WI-PERF-CRITICAL: Lazy-init Silero VAD aquí, NO en imports
        _ensure_silero_vad()
        
        # WI-WHISPER-EAGER-LOAD-JUNIO1: Cargar Whisper aquí (es safe porque estamos en QThread)
        # Esto evita delay en la primera interacción del usuario
        logger.info("⏳ Precargando Whisper en GPU (esto toma ~20-30s la primera vez)...")
        self._modelo = _ensure_whisper_loaded(self._config)
        self._modelo_whisper_cargado = True
        if self._modelo is not None:
            logger.info("✅ Whisper precargado exitosamente — listo para transcribir")
        else:
            logger.warning("⚠️ Whisper no pudo ser precargado (continuando sin modelo)")
        
        self.estado_cambio.emit("escuchando")  # Emitir estado
        
        try:
            self._bucle_escucha()
        except Exception as e:
            logger.error(f"❌ FATAL ERROR en HiloEscucha.run(): {e}")
            logger.exception("Stack trace completo:")
            self.estado_cambio.emit("error")
            self.mensaje_sistema.emit(f"ESCUCHA ERROR: {e}")

    def _cargar_modelo(self):
        """Carga el modelo Whisper."""
        try:
            import torch
        except ImportError:
            from computadora.utilidad.auto_instalar_deps import intentar_importar
            if not intentar_importar("torch", "torch"):
                raise
            import torch

        import whisper

        modelo_nombre = self._config.obtener("whisper.modelo", "base")
        dispositivo_cfg = self._config.obtener("whisper.dispositivo", "auto")

        def _gpu_disponible() -> bool:
            try:
                return torch.cuda.is_available()
            except Exception:
                return False

        def _gpu_count() -> int:
            try:
                return torch.cuda.device_count()
            except Exception:
                return 0

        if dispositivo_cfg == "auto":
            if _gpu_disponible():
                dispositivo = "cuda:0"
            elif _gpu_count() > 0:
                dispositivo = "cuda:0"
                logger.warning("GPU detectada por device_count, pero torch.cuda.is_available() es False; intentando cuda:0 de todos modos.")
            else:
                dispositivo = "cpu"
        elif dispositivo_cfg == "cuda":
            dispositivo = "cuda:0"
        else:
            dispositivo = dispositivo_cfg

        if dispositivo.startswith("cuda"):
            device_count = _gpu_count()
            gpu_name = None
            if device_count > 0:
                try:
                    gpu_name = torch.cuda.get_device_name(0)
                except Exception:
                    gpu_name = None
            logger.info(f"Whisper GPU candidate: {dispositivo} count={device_count} name={gpu_name}")

        self.mensaje_sistema.emit(f"Inscribiendo la Palabra en {dispositivo}... modelo '{modelo_nombre}'")
        logger.info(f"Cargando Whisper modelo='{modelo_nombre}' dispositivo='{dispositivo}'")

        try:
            self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
            
            # VALIDACIÓN GPU: Verificar que realmente funciona
            if dispositivo.startswith("cuda"):
                try:
                    import numpy as np
                    logger.info(f"✓ Verificando GPU Whisper en {dispositivo}...")
                    # Transcripción dummy de 3 segundos para forzar kernel GPU
                    dummy_audio = np.zeros((16000 * 3,), dtype=np.float32)
                    start_gpu_test = time.time()
                    _ = self._modelo.transcribe(dummy_audio, language="es", verbose=False)
                    gpu_test_time = time.time() - start_gpu_test
                    logger.info(f"✅ GPU funcional: dummy transcribe en {gpu_test_time:.2f}s (expected <2s)")
                except Exception as e:
                    logger.error(f"❌ GPU verificación falló: {e}. Retrocediendo a CPU.")
                    dispositivo = "cpu"
                    self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
        except Exception as e:
            logger.warning(f"No se pudo cargar Whisper en {dispositivo}: {e}. Reintentando en cpu.")
            dispositivo = "cpu"
            self._modelo = whisper.load_model(modelo_nombre, device=dispositivo)
        self.mensaje_sistema.emit("La Palabra fue inscrita. COMPUTADORA escucha.")
        logger.info("Modelo Whisper cargado exitosamente")

    def _bucle_escucha(self):
        """Bucle principal de escucha continua.
        
        Lazy initialization: Detecta cantidad de micrófonos en tiempo de ejecución
        e inicializa multi-micrófono solo si es necesario (>1 dispositivo).
        """
        # Lazy init: Verificar dispositivos y decidir estrategia
        if self._multi_mic is None:
            if not self._allow_multi_mic:
                logger.info("🎙️ Modo multi-micrófono desactivado. Usando single-device seguro.")
                self._use_multi_mic = False
            else:
                try:
                    import sounddevice as sd
                    input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
                    num_mics = len(input_devices)
                    
                    if num_mics > 1:
                        logger.info(f"🎙️ {num_mics} micrófono(s) detectado(s) — inicializando multi-micrófono...")
                        try:
                            self._multi_mic = MultiMicrophoneSystem(self._config)
                            self._use_multi_mic = True
                            logger.info(f"✅ Sistema multi-micrófono activo con {len(self._multi_mic.devices)} dispositivos")
                        except Exception as e:
                            logger.warning(f"⚠️ Multi-micrófono opcional no disponible: {e}")
                            self._multi_mic = None
                            self._use_multi_mic = False
                    else:
                        logger.info(f"🎙️ {num_mics} micrófono(s) detectado(s) — usando modo single-device")
                        self._use_multi_mic = False
                except Exception as e:
                    logger.warning(f"⚠️ Error enumerando dispositivos: {e}")
                    self._use_multi_mic = False
        
        # Ejecutar bucle apropiado según dispositivos disponibles
        if self._use_multi_mic and self._multi_mic:
            self._bucle_escucha_multi_mic()
        else:
            self._bucle_escucha_single_device()

    def _bucle_escucha_multi_mic(self):
        """Bucle de escucha usando sistema multi-micrófono."""
        # Iniciar captura multi-micrófono
        try:
            self._multi_mic.start_capture()
            logger.info("🎙️ Captura multi-micrófono iniciada")
        except Exception as e:
            logger.error(f"❌ Error iniciando captura multi-micrófono: {e}")
            self.estado_cambio.emit("error")
            self.mensaje_sistema.emit(f"Error en sistema multi-micrófono: {e}")
            return

        # Configuración para procesamiento
        duracion_chunk = 0.5  # segundos por chunk
        audio_chunks: deque = deque(maxlen=120)
        silencio_consecutivo = 0
        voz_confirmada_chunks = 0
        _CHUNKS_CONFIRMACION = 3
        hay_voz = False
        self._voz_activa = False
        self._vacias_consecutivas = 0
        contador_chunks = 0  # WI-AUDIO: DEBUG counter

        self.estado_cambio.emit("escuchando")
        logger.info("🎧 Escuchando en todos los micrófonos disponibles...")
        
        tiempo_inicio_procesando = None  # WI-AUDIO: DEBUG timeout
        TIMEOUT_PROCESANDO = 15.0  # WI-AUDIO: 15 segundos máximo esperando transcripción

        while self._activo:
            if self._pausado:
                self.msleep(100)
                continue

            try:
                # WI-AUDIO: Timeout safeguard — si lleva >15s esperando transcripción, reiniciar
                if hay_voz and tiempo_inicio_procesando is not None:
                    tiempo_transcurrido = time.time() - tiempo_inicio_procesando
                    if tiempo_transcurrido > TIMEOUT_PROCESANDO:
                        logger.warning(f"⏱️ TIMEOUT transcripción ({tiempo_transcurrido:.1f}s) — reiniciando estado")
                        hay_voz = False
                        voz_confirmada_chunks = 0
                        audio_chunks.clear()
                        silencio_consecutivo = 0
                        tiempo_inicio_procesando = None
                        self.estado_cambio.emit("escuchando")

                # Obtener el mejor chunk de audio de todos los micrófonos
                chunk_data = self._multi_mic.get_best_audio_chunk(timeout=0.1)

                if chunk_data is None:
                    # No hay audio disponible de ningún micrófono
                    continue

                # WI-AUDIO: DEBUG log cada 10 chunks (cada 5 segundos)
                contador_chunks += 1
                if contador_chunks % 10 == 0:
                    logger.debug(f"🎙️ {contador_chunks} chunks procesados, hay_voz={hay_voz}, silencio_consec={silencio_consecutivo}")

                # Extraer datos del chunk
                chunk = chunk_data.audio_data
                device_index = chunk_data.device_index
                volume_level = chunk_data.volume_level

                # Log del dispositivo que capturó el audio
                if volume_level > self._umbral:
                    logger.debug(f"🎙️ Audio de dispositivo [{device_index}] - Vol:{volume_level:.4f}")

                # Procesar volumen (usar el nivel calculado por el sistema multi-mic)
                volumen = volume_level

                if volumen > self._umbral:
                    if not hay_voz:
                        voz_confirmada_chunks += 1
                        audio_chunks.append(chunk)
                        if voz_confirmada_chunks < _CHUNKS_CONFIRMACION:
                            continue
                        # Confirmado: suficientes chunks consecutivos sobre umbral
                        if self._pensando_flag:
                            self.voz_activa.emit()
                        else:
                            # 🔥 METATRÓN: Set estado LISTENING
                            if self.metatron:
                                self.metatron.set_estado(EstadoSistema.LISTENING)
                            self.estado_cambio.emit("procesando")
                            tiempo_inicio_procesando = time.time()  # WI-AUDIO: DEBUG timeout
                        logger.debug(f"🎙️ Voz detectada desde dispositivo [{device_index}] (volumen={volumen:.4f}, confirmado tras {voz_confirmada_chunks} chunks)")
                        voz_confirmada_chunks = 0
                    else:
                        audio_chunks.append(chunk)
                    hay_voz = True
                    self._voz_activa = True
                    silencio_consecutivo = 0
                elif hay_voz:
                    silencio_consecutivo += 1
                    audio_chunks.append(chunk)
                    corte = int(self._silencio_max / duracion_chunk)
                    if silencio_consecutivo >= corte:
                        # Suficiente silencio → transcribir (con lock WI-CRIT)
                        if not self._transcribiendo:
                            with self._transcribiendo_lock:
                                if not self._transcribiendo:  # Double-check pattern
                                    self._transcribiendo = True
                            try:
                                self._transcribir(list(audio_chunks))
                            finally:
                                with self._transcribiendo_lock:
                                    self._transcribiendo = False
                        audio_chunks.clear()
                        silencio_consecutivo = 0
                        hay_voz = False
                        self._voz_activa = False
                        tiempo_inicio_procesando = None  # WI-AUDIO: DEBUG reset
                        if not self._pensando_flag:
                            # 🔥 METATRÓN: Back to IDLE
                            if self.metatron:
                                self.metatron.set_estado(EstadoSistema.IDLE)
                            self.estado_cambio.emit("escuchando")
                else:
                    # Bajo umbral y no hay voz confirmada — resetear pre-confirmación
                    if voz_confirmada_chunks > 0:
                        voz_confirmada_chunks = 0
                        audio_chunks.clear()

            except Exception as e:
                logger.error(f"Error en bucle de escucha multi-micrófono: {e}")
                self.msleep(1000)  # Esperar antes de reintentar

        # Detener captura al salir
        try:
            self._multi_mic.stop_capture()
            logger.info("🎙️ Captura multi-micrófono detenida")
        except Exception as e:
            logger.error(f"Error deteniendo captura multi-micrófono: {e}")

    def _bucle_escucha_single_device(self):
        """Bucle de escucha usando sistema original single-device."""
        import sounddevice as sd

        dispositivo_id, sr_nativo, canales = self._encontrar_mejor_dispositivo()
        self._sr_nativo = sr_nativo

        duracion_chunk = 0.2  # segundos por chunk (increased from 0.1 to reduce callback frequency)
        muestras_chunk = int(duracion_chunk * sr_nativo)
        # FP-150 RF-371: Increased queue size to reduce overflow on high-load scenarios (128 → 256)
        cola_audio = queue.Queue(maxsize=256)  # RF-371: Audio Queue Sizing (FP-150)

        def callback_audio(indata, frames, time_info, status):
            if status:
                if getattr(status, "input_overflow", False):
                    logger.warning("Audio input overflow detectado, descartando paquete de audio")
                elif getattr(status, "output_underflow", False):
                    logger.debug("Audio output underflow detectado")
                else:
                    logger.warning(f"Estado audio: {status}")
            try:
                cola_audio.put_nowait(indata.copy())
            except queue.Full:
                # Mantener el fragmento más reciente y liberar solo un buffer antiguo.
                # Esto reduce la pérdida de audio abrupta y mejora la resiliencia contra overflow.
                if not cola_audio.empty():
                    try:
                        cola_audio.get_nowait()
                    except queue.Empty:
                        pass
                logger.debug("Cola de audio llena, descartando un buffer antiguo para recuperar espacio")
                try:
                    cola_audio.put_nowait(indata.copy())
                except queue.Full:
                    logger.debug("Cola desbordada, descartando paquete actual")

        self.estado_cambio.emit("escuchando")
        logger.info(f"✅ Estado emitido: escuchando")
        logger.info(f"🎧 Escucha activa iniciada (dispositivo={dispositivo_id}, sr={sr_nativo}, ch={canales})")

        while self._activo:
            try:
                logger.debug(f"Abriendo InputStream (dispositivo={dispositivo_id}, sr={sr_nativo})...")
                with sd.InputStream(
                    device=dispositivo_id,
                    samplerate=sr_nativo,
                    channels=canales,
                    dtype="float32",
                    blocksize=muestras_chunk,
                    callback=callback_audio,
                ):
                    logger.info("✅ InputStream abierto correctamente")
                    self._procesar_stream(cola_audio, muestras_chunk, duracion_chunk)
                    logger.info("✅ _procesar_stream completó")

            except Exception as e:
                logger.error(f"❌ Error abriendo InputStream: {e}")
                logger.exception("Stack trace:")
                self.estado_cambio.emit("error")
                self.mensaje_sistema.emit(f"Error de micrófono: {e}")
                self.msleep(3000)
                try:
                    dispositivos = sd.query_devices()
                    entradas = [i for i, d in enumerate(dispositivos) if d.get("max_input_channels", 0) > 0]
                    if entradas:
                        candidato = entradas[0]
                        if candidato != dispositivo_id:
                            info = dispositivos[candidato]
                            logger.warning(f"Reintentando con dispositivo de entrada disponible: [{candidato}] {info.get('name')}")
                            dispositivo_id = candidato
                            sr_nativo = int(info.get("default_samplerate", 44100))
                            canales = min(2, int(info.get("max_input_channels", 1)))
                            self._sr_nativo = sr_nativo
                            muestras_chunk = int(duracion_chunk * sr_nativo)
                            continue
                except Exception as e2:
                    logger.debug(f"No se pudo consultar dispositivos para reintentar: {e2}")

                if dispositivo_id is not None:
                    logger.warning("Reintentando con dispositivo default...")
                    dispositivo_id = None
                    sr_nativo = 44100
                    canales = 1
                    self._sr_nativo = sr_nativo
                    muestras_chunk = int(duracion_chunk * sr_nativo)
                else:
                    break

    def _procesar_stream(self, cola_audio: queue.Queue, muestras_chunk: int, duracion_chunk: float = 0.5):
        """Procesa el stream de audio buscando voz."""
        audio_chunks: deque = deque(maxlen=120)
        silencio_consecutivo = 0
        voz_confirmada_chunks = 0  # Chunks consecutivos sobre umbral antes de confirmar
        _CHUNKS_CONFIRMACION = 3  # Requiere 3 chunks (~1.5s) sobre umbral para confirmar voz
        hay_voz = False
        self._voz_activa = False  # Flag visible para otros componentes
        self._vacias_consecutivas = 0  # FP-046D: backoff de vacías
        tiempo_inicio_captura = None  # FP-044B: Timestamp para hard timeout

        while self._activo:
            if self._pausado:
                # Vaciar cola mientras está pausado
                while not cola_audio.empty():
                    try:
                        cola_audio.get_nowait()
                    except queue.Empty:
                        break
                self.msleep(100)
                continue

            try:
                chunk = cola_audio.get(timeout=1.0)
            except queue.Empty:
                continue

            volumen = np.abs(chunk).mean()

            if volumen > self._umbral:
                if not hay_voz:
                    voz_confirmada_chunks += 1
                    audio_chunks.append(chunk)
                    if voz_confirmada_chunks < _CHUNKS_CONFIRMACION:
                        continue  # Acumular pero no confirmar aún
                    # Confirmado: suficientes chunks consecutivos sobre umbral
                    if self._pensando_flag:
                        self.voz_activa.emit()
                    else:
                        self.estado_cambio.emit("procesando")
                    logger.debug(f"Voz detectada (volumen={volumen:.4f}, confirmado tras {voz_confirmada_chunks} chunks)")
                    voz_confirmada_chunks = 0
                    tiempo_inicio_captura = time.time()  # FP-044B: Iniciar contador de max duración
                else:
                    audio_chunks.append(chunk)
                hay_voz = True
                self._voz_activa = True
                silencio_consecutivo = 0
            elif hay_voz:
                silencio_consecutivo += 1
                audio_chunks.append(chunk)
                corte = int(self._silencio_max / duracion_chunk)
                # FP-044B: Check timeout de captura máxima (evita listening infinito con música)
                duracion_captura = time.time() - tiempo_inicio_captura if tiempo_inicio_captura else 0
                if silencio_consecutivo >= corte or duracion_captura > self._duracion_max_captura:
                    motivo = "silencio" if silencio_consecutivo >= corte else f"timeout ({duracion_captura:.1f}s > {self._duracion_max_captura}s)"
                    logger.debug(f"Transcribiendo por {motivo}")
                    # Suficiente silencio O timeout → transcribir (con lock WI-CRIT)
                    if not self._transcribiendo:
                        with self._transcribiendo_lock:
                            if not self._transcribiendo:  # Double-check pattern
                                self._transcribiendo = True
                        try:
                            self._transcribir(list(audio_chunks))
                        finally:
                            with self._transcribiendo_lock:
                                self._transcribiendo = False
                    audio_chunks.clear()
                    silencio_consecutivo = 0
                    hay_voz = False
                    self._voz_activa = False
                    tiempo_inicio_captura = None  # FP-044B: Reset
                    if not self._pensando_flag:
                        self.estado_cambio.emit("escuchando")
            else:
                # Bajo umbral y no hay voz confirmada — resetear pre-confirmación
                if voz_confirmada_chunks > 0:
                    voz_confirmada_chunks = 0
                    audio_chunks.clear()

    def _transcribir(self, audio_chunks: list):
        """Transcribe los chunks de audio con Whisper."""
        logger.info(f"🎙️ _transcribir() INICIADO: {len(audio_chunks)} chunks")  # WI-AUDIO: DEBUG
        try:
            # FP-044: Detectar media activa ANTES de transcribir
            _media_activa = False
            if self._contexto_pantalla is not None:
                try:
                    _media_activa = self._contexto_pantalla.hay_media_activa()
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

            audio = np.concatenate(audio_chunks)
            del audio_chunks  # Liberar referencia a chunks originales

            # Si es multicanal, tomar solo canal 0
            if audio.ndim > 1:
                audio = audio[:, 0]

            audio = audio.flatten()
            logger.info(f"🎙️ Audio concatenado: {len(audio)} muestras, duracion={len(audio)/self._fs:.1f}s")  # WI-AUDIO: DEBUG

            # Resamplear de sr_nativo a 16kHz para Whisper
            sr_nativo = getattr(self, '_sr_nativo', self._fs)
            if sr_nativo != self._fs:
                num_muestras_destino = int(len(audio) * self._fs / sr_nativo)
                audio = resample(audio, num_muestras_destino).astype(np.float32)

            duracion = len(audio) / self._fs
            logger.debug(f"Transcribiendo {duracion:.1f}s de audio (resample {sr_nativo}->{self._fs})")

            # Filtrar audio muy corto (tos, golpe, etc.)
            if duracion < _MIN_AUDIO_DURACION:
                logger.debug(f"Audio muy corto ({duracion:.1f}s), descartando")
                return

            # Normalizar audio para Whisper (espera rango aprox -1 a 1)
            max_val = np.max(np.abs(audio))
            if max_val > 0.001:
                audio = audio / max_val * 0.95
            else:
                logger.debug("Audio demasiado silencioso, descartando")
                return

            # ── RF-139: Silero VAD pre-filtro — detectar voz humana ANTES de Whisper ──
            if _SILERO_VAD_DISPONIBLE and _SILERO_VAD_MODEL is not None:
                try:
                    audio_tensor = torch.from_numpy(audio).float()
                    speech_timestamps = get_speech_timestamps(
                        audio_tensor, _SILERO_VAD_MODEL,
                        sampling_rate=self._fs,
                        threshold=_MIN_SPEECH_PROB_VAD,
                    )
                    if not speech_timestamps:
                        logger.debug(f"VAD: Sin voz humana detectada ({duracion:.1f}s), descartando")
                        _log_audio("", "vad_sin_voz", descartado=True,
                                   motivo_descarte="silero_vad_sin_voz")
                        return
                    # Calcular proporción de voz en el audio
                    total_speech = sum(ts["end"] - ts["start"] for ts in speech_timestamps)
                    total_samples = len(audio)
                    speech_ratio = total_speech / total_samples if total_samples > 0 else 0
                    logger.debug(f"VAD: {len(speech_timestamps)} segmentos de voz, ratio={speech_ratio:.2f}")
                except Exception as e:
                    logger.debug(f"VAD: Error en Silero ({e}), continuando sin filtro")

            # ── RF-141: Parámetros Whisper optimizados anti-hallucination ──
            fp16_enabled = False
            if hasattr(self._modelo, 'device'):
                try:
                    fp16_enabled = self._modelo.device.type == "cuda"
                except Exception:
                    fp16_enabled = False

            _whisper_params = dict(
                language="es",
                fp16=fp16_enabled,
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                logprob_threshold=-0.8,
                no_speech_threshold=0.4,
                initial_prompt=_WHISPER_INITIAL_PROMPT,
                beam_size=1,  # Optimización: beam_size=1 es 50% más rápido que beam_size=5 (default)
                temperature=0.0,  # Temperatura fija para coherencia sin penalidad de velocidad
            )

            # 🔥 METATRÓN: Registrar latencia Whisper
            start_time = time.time()
            try:
                # WI-WHISPER-EAGER-LOAD-JUNIO1: Verificar si ya se cargó en run()
                if not self._modelo:
                    logger.info("⏳ Whisper no precargado — cargando modelo ahora...")
                    self._modelo = _ensure_whisper_loaded(self._config)
                    if not self._modelo:
                        logger.error("❌ Whisper no disponible, descartando audio")
                        return
                
                resultado = self._modelo.transcribe(audio, **_whisper_params)
            except RuntimeError:
                _whisper_params["fp16"] = False
                resultado = self._modelo.transcribe(audio, **_whisper_params)
            latency = time.time() - start_time
            if self.metatron:
                self.metatron.registrar_metrica('latencia_whisper', latency)

            texto = resultado["text"].strip()

            # Correcciones post-transcripción de errores recurrentes de Whisper
            # FP-044: No aplicar correcciones cuando hay media activa (evita falsos positivos)
            texto_original = texto
            if not _media_activa:
                texto = _RE_CORRECCIONES.sub(
                    lambda m: _CORRECCIONES_WHISPER[m.group(0).lower()], texto
                )
                # Corrección fuzzy de nombres propios (propietario)
                texto = _corregir_nombre_propietario(texto)

            # Logging detallado de Whisper
            segmentos = resultado.get("segments", [])
            no_speech_promedio = 0.0
            if segmentos:
                no_speech_promedio = sum(s.get("no_speech_prob", 0) for s in segmentos) / len(segmentos)
            lang = resultado.get("language", "?")
            corregido_tag = f" → '{texto}'" if texto != texto_original else ""
            logger.info(
                f"Whisper: '{texto_original}'{corregido_tag} | "
                f"lang={lang} no_speech={no_speech_promedio:.2f} "
                f"dur={duracion:.1f}s segs={len(segmentos)}"
            )

            if no_speech_promedio > _MAX_NO_SPEECH_PROB:
                    logger.debug(f"No-speech prob alta ({no_speech_promedio:.2f}), descartando: '{texto}'")
                    _log_audio(texto, "ruido_ambiente", descartado=True,
                               motivo_descarte=f"no_speech:{no_speech_promedio:.2f}",
                               no_speech_prob=no_speech_promedio)
                    return

            # ── RF-140: Detector de hallucination por entropía ──
            motivo_hallu = _es_hallucination_repetitiva(texto)
            if motivo_hallu:
                logger.info(f"Hallucination repetitiva detectada: '{texto}' ({motivo_hallu})")
                _log_audio(texto, "hallucination", descartado=True,
                           motivo_descarte=motivo_hallu, no_speech_prob=no_speech_promedio)
                return

            # Filtrar transcripciones vacías o ruido conocido
            ruido = {".", "...", "¡", "!", "?", ",", "Subtítulos", "subtítulos",
                     "Gracias.", "¡Suscríbete!", "..", "Amara.org", "MokaPlayer"}
            if not texto:
                logger.debug(f"Transcripción vacía, descartando")
                # FP-046D: backoff tras vacías consecutivas — evitar quemar GPU
                self._vacias_consecutivas = getattr(self, '_vacias_consecutivas', 0) + 1
                if self._vacias_consecutivas >= 3:
                    self._silencio_max = min(self._silencio_max * 2, 6.0)
                    logger.debug(f"Backoff vacías: silencio_max → {self._silencio_max:.1f}s ({self._vacias_consecutivas} vacías)")
                return

            # FP-046D: reset backoff al recibir transcripción no-vacía
            if getattr(self, '_vacias_consecutivas', 0) > 0:
                self._vacias_consecutivas = 0
                self._silencio_max = self._config.obtener("escucha.silencio_max_segundos", 1.5)

            # ── ECHO-FILTERING TIMESTAMP-BASED — Detectar eco vs interrupción ──
            # 🔥 NUEVO SISTEMA: Reemplaza lógica antigua de SequenceMatcher simple
            is_echo, interrupted_content = self._check_echo_timestamp(texto)
            if is_echo:
                logger.debug(f"Eco TTS filtrado: '{texto}'")
                return

            # Si es interrupción, emitir señal especial con contexto
            if interrupted_content:
                logger.info(f"¡Interrupción detectada durante TTS!: '{texto}' (TTS interrumpido: '{interrupted_content[:50]}...')")
                self.interrupcion_detectada.emit(texto)
                return

            # Si estamos esperando confirmación, aceptar respuestas cortas
            if self._esperando_confirmacion:
                try:
                    txt_low = texto.lower().strip()
                    # Aceptar respuestas afirmativas/negativas incluso si son cortas
                    if any(w in txt_low for w in ("sí", "si", "no", "claro", "afirmativo", "negativo", "s")):
                        logger.info(f"Confirmación detectada en escucha: '{texto}'")
                        self.texto_detectado.emit(texto)
                        # Limpiar flag local para evitar dobles
                        self._esperando_confirmacion = False
                        return
                    # Si no parece un sí/no, igualmente emitir para que la UI decida
                    self.texto_detectado.emit(texto)
                    self._esperando_confirmacion = False
                    return
                except Exception as e:
                    logger.exception("Error procesando confirmación de voz")

            if len(texto) <= 2 or texto in ruido:
                logger.debug(f"Transcripción descartada (ruido): '{texto}'")
                _log_audio(texto, "ruido_corto", descartado=True,
                           motivo_descarte="texto_corto_o_ruido")
                return

            # === HEURÍSTICAS DE SPOKENS ===
            # Detectar posible multi-hablante si el audio es estéreo y los canales difieren
            multi_hablantes = False
            try:
                if audio.ndim > 1 and audio.shape[1] >= 2:
                    ch0 = audio[:, 0]
                    ch1 = audio[:, 1]
                    # Correlación simple
                    corr = np.corrcoef(ch0, ch1)[0, 1]
                    if abs(corr) < self._stereo_multi_threshold:
                        multi_hablantes = True
            except (ValueError, IndexError) as e:
                logger.debug("Error en detección multi-hablante estéreo: %s", e)
            self.hay_terceros = multi_hablantes

            # Normalizar texto para matching
            def _normalize(s: str) -> str:
                s = s.lower()
                s = unicodedata.normalize("NFKD", s)
                s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "M")
                s = re.sub(r"[^a-zñáéíóúü\s]", "", s)
                return s.strip()

            def _is_fuzzy_wake(s: str, _SM=SequenceMatcher) -> bool:
                # FP-044: Desactivar fuzzy cuando hay media activa
                if _media_activa:
                    return False
                # Tokenizar y comparar con 'computadora' por ratio
                target = "computadora"
                for tok in re.findall(r"\w+", s.lower()):
                    # Exact match o variante aprendida
                    if tok in self._wake_variants:
                        return True
                    # Sequence matcher ratio
                    ratio = _SM(None, tok, target).ratio()
                    if ratio > 0.72:
                        return True
                    # Allow short edit distance via ratio threshold
                    if len(tok) <= 7 and ratio > 0.62:
                        return True
                return False

            tiene_wake = False
            es_regano = False   # Nombre completo "COMPUTADORA Emet" / "Computadora Emet" = propietario molesto
            es_apodo = False    # "Gol"/"Col" en contexto vocativo

            # FP-035.3: Extraer embedding ANTES de los checks de wake word
            # (los checks de nombre completo y apellido necesitan 'emb' para verificar propietario)
            emb = None
            try:
                emb = self._extraer_embedding(audio, self._fs)
            except (ValueError, TypeError) as e:
                logger.debug("Error extrayendo embedding de hablante: %s", e)

            # 1. Nombre completo primero — SOLO propietario verificado
            #    El nombre completo "COMPUTADORA Emet" / "Computadora Emet" es secreto. Solo el creador puede usarlo.
            if _RE_NOMBRE_COMPLETO.search(texto):
                _sim_amo = 0.0
                if emb is not None and self._owner_profile is not None:
                    _sim_amo = self._cosine_similarity(emb, self._owner_profile)
                if _sim_amo >= float(self._vox_threshold):
                    tiene_wake = True
                    es_regano = True
                    logger.info(f"¡Nombre completo detectado! (regaño, propietario verificado): '{texto}'")
                else:
                    logger.debug(f"Nombre completo detectado pero hablante NO es propietario — ignorando")

            # 2. Nombre "COMPUTADORA" (regex + fuzzy)
            if not tiene_wake:
                m = _WAKE_WORD_RE.search(texto)
                if m:
                    tiene_wake = True
                    # aprender la variante textual que produjo el modelo
                    try:
                        variante = m.group(0).lower()
                        variante_norm = _normalize(variante)
                        if variante_norm:
                            self._wake_variants.add(variante_norm)
                    except (ValueError, re.error) as e:
                        logger.debug("Error normalizando wake variant: %s", e)
                else:
                    # 🔥 RUBEDO: Fuzzy check mejorado con Levenshtein
                    if self._check_wake_word_fuzzy(texto) or self._check_wake_word_fuzzy(_normalize(texto)):
                        tiene_wake = True

            # 3. Apellido "Emet" (wake word formal) — SOLO propietario verificado
            #    Para extraños, Computadora NO reconoce "Emet" como su nombre.
            if not tiene_wake and _RE_APELLIDO.search(texto):
                _sim_amo = 0.0
                if emb is not None and self._owner_profile is not None:
                    _sim_amo = self._cosine_similarity(emb, self._owner_profile)
                if _sim_amo >= float(self._vox_threshold):
                    tiene_wake = True
                    logger.info(f"Apellido 'Emet' detectado (propietario verificado): '{texto}'")
                else:
                    logger.debug(f"Apellido 'Emet' detectado pero hablante NO es propietario — ignorando")

            # 4. Apodo "Gol"/"Col"/"Go" — solo en contexto vocativo
            if not tiene_wake and _RE_APODO.search(texto):
                if _RE_VOCATIVO_APODO.search(texto):
                    tiene_wake = True
                    es_apodo = True
                    logger.info(f"Apodo detectado en contexto vocativo: '{texto}'")

            # FP-035.3: emb ya extraído ANTES de checks de wake word (arriba)

            # Si se solicitó enrolamiento manual, usar esta muestra para actualizar perfil
            if emb is not None and getattr(self, "_force_enroll", False):
                try:
                    self._update_owner_profile(emb)
                    self.mensaje_sistema.emit("Muestra de propietario registrada (manual).")
                    logger.info("Muestra manual registrada en perfil del propietario")
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                    logger.exception("Error registrando muestra manual de propietario")
                finally:
                    self._force_enroll = False

            # הכרת פנים — Enrolamiento de persona presentada
            if emb is not None and self._enroll_persona_nombre:
                nombre_enroll = self._enroll_persona_nombre
                # Verificar que NO sea el propietario (queremos la voz ajena)
                es_amo = False
                if self._owner_profile is not None:
                    sim_amo = self._cosine_similarity(emb, self._owner_profile)
                    if sim_amo >= float(self._vox_threshold):
                        es_amo = True
                if not es_amo:
                    self._enroll_persona(nombre_enroll, emb)
                    self._enroll_persona_nombre = None
                    self.mensaje_sistema.emit(f"Voz de {nombre_enroll} registrada.")
                    logger.info(f"Enrolamiento completado: {nombre_enroll}")

            # Si no tiene wake pero estamos en conversación (y la conversación
            # pertenece al propietario) aceptamos — con filtro de falsos positivos.
            if not tiene_wake and self._en_conversacion:
                # FP-045A: Si hay media activa y NO estamos esperando respuesta directa,
                # descartar — es audio del video, no del propietario.
                if _media_activa and not self._esperando_respuesta:
                    logger.info(f"Media activa, descartando audio en conversación: '{texto[:60]}'")
                    _log_audio(texto, "media_descartada", descartado=True,
                               motivo_descarte="media_activa_en_conversacion")
                    return
                # Si Computadora hizo una pregunta, aceptar respuesta con filtro relajado
                if self._esperando_respuesta:
                    # FP-046A: expirar si pasaron >30s
                    if (time.monotonic() - self._esperando_respuesta_ts) > 30.0:
                        logger.info("Timeout de _esperando_respuesta (>30s), tratando como conversación normal")
                        self._esperando_respuesta = False
                        # Cae al filtro normal de _es_falso_positivo_conversacion abajo
                    else:
                        # FP-046B: filtro mínimo — descartar basura obvia
                        _nsp_resp = 0.0
                        if segmentos:
                            _nsp_resp = sum(s.get("no_speech_prob", 0) for s in segmentos) / len(segmentos)
                        motivo_resp = _es_falso_positivo_conversacion(texto, _nsp_resp)
                        if motivo_resp:
                            logger.info(f"Respuesta esperada descartada (falso positivo): '{texto}' ({motivo_resp})")
                            _log_audio(texto, "falso_positivo", descartado=True,
                                       motivo_descarte=f"esperando_resp_fp:{motivo_resp}", no_speech_prob=_nsp_resp)
                            return
                        self._esperando_respuesta = False
                        logger.info(f"Respuesta esperada recibida, sin wake word: '{texto}'")
                        _log_audio(texto, "habla_propietario")
                        self.texto_detectado.emit(texto)
                        return
                # Obtener no_speech_prob promedio para el filtro
                _nsp = 0.0
                if segmentos:
                    _nsp = sum(s.get("no_speech_prob", 0) for s in segmentos) / len(segmentos)
                motivo_fp = _es_falso_positivo_conversacion(texto, _nsp)
                if motivo_fp:
                    logger.info(f"Falso positivo filtrado en conversación: '{texto}' ({motivo_fp})")
                    _log_audio(texto, "falso_positivo", descartado=True,
                               motivo_descarte=motivo_fp, no_speech_prob=_nsp)
                    return
                logger.info(f"Conversación activa, sin wake word: '{texto}'")
                _log_audio(texto, "habla_propietario")
                self.texto_detectado.emit(texto)
                return

            # RF-248 Hakará BeKol: si NO hay wake word y NO estamos en conversación,
            # pero la voz coincide con el propietario → activar sin wake word.
            # RF-295: Guard media — no activar por voz sin wake si hay media activa
            # WI-DETECTAR-PROPIETARIO-DISABLED: Flag desactivado por solicitud del usuario
            if _media_activa and not self._esperando_respuesta:
                logger.debug("RF-295: Voz sin wake descartada por media activa")
            elif not tiene_wake and not self._en_conversacion and self._detectar_propietario_sin_wake:
                if emb is not None and self._owner_profile is not None:
                    _sim_voz = self._cosine_similarity(emb, self._owner_profile)
                    if _sim_voz >= float(self._vox_threshold):
                        _nsp_voz = 0.0
                        if segmentos:
                            _nsp_voz = sum(s.get("no_speech_prob", 0) for s in segmentos) / len(segmentos)
                        motivo_fp_voz = _es_falso_positivo_conversacion(texto, _nsp_voz)
                        if motivo_fp_voz:
                            logger.info(f"Voz propietario sin wake, pero falso positivo: '{texto}' ({motivo_fp_voz})")
                            _log_audio(texto, "falso_positivo", descartado=True,
                                       motivo_descarte=f"voz_sin_wake_fp:{motivo_fp_voz}", no_speech_prob=_nsp_voz)
                        else:
                            logger.info(f"Voz propietario reconocida sin wake word (sim={_sim_voz:.2f}): '{texto}'")
                            self.clasificacion_hablante = "amo"
                            try:
                                self.marcar_intercambio(owner=True)
                            except Exception as e:
                                logger.exception("Error marcando intercambio (voz sin wake)")
                            _log_audio(texto, "habla_propietario_sin_wake")
                            self.texto_detectado.emit(texto)
                            return

            # Si hay múltiples hablantes detectados, ser más conservador
            if not tiene_wake and multi_hablantes:
                # Si parece dirigido (prefijo vocativo), preguntar confirmación
                if re.search(r"\b(oye|oye\s+tú|eh|hey|por\s+fa|por\s+favor)\b", texto, re.IGNORECASE):
                    logger.info(f"Posible direccion a Computadora en ambiente con varias personas: '{texto}' -> pedir confirmación")
                    self.texto_detectado.emit(f"[confirmar]{texto}")
                else:
                    logger.debug(f"Multi-hablantes detectado, ignorando: '{texto}'")
                return

            # Si tiene wake word — verificar identidad del hablante
            if tiene_wake:
                # Limpiar todas las formas del nombre del texto
                texto_limpio = texto
                if es_regano:
                    texto_limpio = _RE_NOMBRE_COMPLETO.sub("", texto_limpio)
                texto_limpio = _WAKE_WORD_RE.sub("", texto_limpio)
                texto_limpio = _RE_APELLIDO.sub("", texto_limpio)
                if es_apodo:
                    texto_limpio = _RE_APODO.sub("", texto_limpio, count=1)
                # Limpiar puntuación huérfana tras eliminar wake word
                texto_limpio = re.sub(r'\s*,\s*,', ',', texto_limpio)  # ", ," → ","
                texto_limpio = re.sub(r'\s{2,}', ' ', texto_limpio)    # espacios dobles
                texto_limpio = texto_limpio.strip(" ,.:;¿¡")
                # Verificación por timbre — 3 niveles
                verificado = False
                sim = 0.0
                try:
                    if emb is not None and self._owner_profile is not None:
                        sim = self._cosine_similarity(emb, self._owner_profile)
                        if sim >= _OWNER_VOX_THRESHOLD:  # WI-296: Usar threshold más bajo para propietario
                            verificado = True
                            self.clasificacion_hablante = "amo"
                        elif sim >= _CONOCIDO_VOX_THRESHOLD:
                            self.clasificacion_hablante = "conocido"
                            # Intentar identificar persona específica
                            nombre_id = self._identificar_persona(emb)
                            if nombre_id:
                                self.clasificacion_hablante = f"conocido:{nombre_id}"
                        else:
                            self.clasificacion_hablante = "extraño"
                    elif emb is not None and self._owner_profile is None and not multi_hablantes:
                        # Primer registro automático — inicializar perfil del propietario
                        self._update_owner_profile(emb)
                        verificado = True
                        self.clasificacion_hablante = "amo"
                        self.mensaje_sistema.emit("Perfil de voz creado (registro inicial).")
                    else:
                        self.clasificacion_hablante = "extraño"
                except (ValueError, TypeError) as e:
                    logger.exception("Error en verificación de voz del hablante")
                    verificado = False
                    self.clasificacion_hablante = "extraño"

                if texto_limpio:
                    if not verificado and _RE_PRESENCIA.search(texto_limpio):
                        logger.info(f"Presencia solicitada sin voz verificada: '{texto_limpio}'")
                        self.mensaje_sistema.emit("Solicitan presencia. Respondiendo sin ejecutar comando.")
                        self.texto_detectado.emit("[presencia]")
                        return

                    if not verificado:
                        logger.info(f"Voz no reconocida (sim={sim:.2f}) — RUBEDO: Filtro desactivado, aceptando voz: '{texto_limpio}'")
                        # RUBEDO: Aceptar todas las voces (filtro desactivado temporalmente)
                        # Si necesita ser más restrictivo, cambiar la siguiente línea a:
                        # self.texto_detectado.emit(f"[confirmar]{texto}")
                        # return

                    # Marca intercambio del propietario: permite follow-ups
                    try:
                        self.marcar_intercambio(owner=True)
                    except Exception as e:
                        logger.exception("Error marcando intercambio del propietario")

                    logger.info(f"Wake word + comando: '{texto_limpio}'")
                    if es_regano:
                        self.texto_detectado.emit(f"[regano]{texto_limpio}")
                    else:
                        self.texto_detectado.emit(texto_limpio)
                else:
                    # Wake word sola detectada — RUBEDO: Filtro desactivado, aceptar todas las voces
                    if not verificado:
                        logger.info(f"Wake word detectada sin verificación (sim={sim:.2f}) — RUBEDO: Filtro desactivado")
                        # Aceptar la voz sin requerir confirmación
                        self.texto_detectado.emit("[presencia]")
                        return
                    logger.info("Wake word sola detectada")
                    self.texto_detectado.emit("[presencia]")
                return

            # Si no tiene wake word y no estamos en conversación:
            # SOLO responder a vocativos explícitos (no cualquier ruido transcrito)
            if re.search(r"^\s*(oye|hey|por\s+favor|porfa)\b", texto, re.IGNORECASE):
                logger.info(f"Vocativo explícito detectado: '{texto}' -> pedir confirmación")
                self.texto_detectado.emit(f"[confirmar]{texto}")
                return

            # דעת Da'at — Cortesía sin wake word (incluye cortesía+apodo)
            # FP-018 WI-083: En descanso_guardian, exigir wake word explícito
            from computadora.nucleo.proactividad import obtener_fase_actual
            _fase = obtener_fase_actual()
            if _fase != "descanso_guardian":
                cortesia_match = _RE_CORTESIA.match(texto)
                if cortesia_match:
                    logger.info(f"Cortesía detectada sin wake word: '{texto}'")
                    _log_audio(texto, "cortesia")
                    self.texto_detectado.emit(f"[cortesia]{texto}")
                    return
                # Cortesía con apodo: "hola gol", "buenos días gol"
                if _RE_VOCATIVO_APODO.search(texto) and _RE_APODO.search(texto):
                    texto_sin_apodo = _RE_APODO.sub("", texto, count=1).strip(" ,.:;¿¡")
                    if _RE_CORTESIA.match(texto_sin_apodo):
                        logger.info(f"Cortesía+apodo detectada: '{texto}'")
                        _log_audio(texto, "cortesia_apodo")
                        self.texto_detectado.emit(f"[cortesia]{texto_sin_apodo}")
                        return
            else:
                logger.debug(f"Descanso guardian: cortesía ignorada sin wake word: '{texto}'")
                if _RE_CORTESIA.match(texto):
                    return  # Silenciar cortesía en descanso

            # Fuera de conversación y sin wake word — ignorar
            logger.debug(f"Sin wake word, ignorando: '{texto}'")

        except Exception as e:
            logger.error(f"Error en transcripción: {e}")


