"""
נצח (Netzaj) — Victoria/Eternidad. Memoria de Netzaj (זכרון). Sello #9.
Módulo de memoria local de Computadora.

WI-307: Memoria con Hash SHA256 + Índices para búsqueda O(1).
WI-308: Detección de lagunas entre sesiones + tiempo PC encendido.

Victoria sobre el olvido: almacena conversaciones localmente,
un compresor diario que resume y guarda una versión comprimida
de la memoria del día para evitar saturar el disco.

Formato de almacenamiento WI-307:
- Datos crudos: `datos/memoria/memoria_raw_YYYY-MM-DD.jsonl` (JSON por línea con hash)
- Índice hash: `datos/memoria/memoria_idx_YYYY-MM-DD.json` (hash→timestamp)
- Resumen: `datos/memoria/memoria_summary_YYYY-MM-DD.txt`
- Conciencia temporal: `datos/consciencia_temporal.json` (sesiones + lagunas)
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import psutil
from loguru import logger

from computadora.nucleo.gestor_procesos import obtener_gestor_procesos
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datos" / "memoria"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_TEMPORAL_PATH = _DATOS_DIR / "consciencia_temporal.json"


def _raw_path_for(d: date) -> Path:
    return DATA_DIR / f"memoria_raw_{d.isoformat()}.jsonl"


def _index_path_for(d: date) -> Path:
    """WI-307: Ruta del índice hash para un día."""
    return DATA_DIR / f"memoria_idx_{d.isoformat()}.json"


def _keyword_path_for(d: date) -> Path:
    """WI-317: Ruta del índice invertido (keywords→[hashes]) para un día."""
    return DATA_DIR / f"memoria_kw_{d.isoformat()}.json"


def _summary_path_for(d: date) -> Path:
    return DATA_DIR / f"memoria_summary_{d.isoformat()}.txt"


def _sample_path_for(d: date) -> Path:
    return DATA_DIR / f"memoria_sample_{d.isoformat()}.json"


# ── WI-307: Hash de entrada ───────────────────────────────────────

def _hash_entry(entry: dict) -> str:
    """WI-307: Genera hash SHA256 del contenido de una entrada de memoria.
    
    Excluye 'ts' (timestamp) para que el hash refleje solo el contenido.
    """
    content = {k: v for k, v in entry.items() if k != 'ts'}
    raw = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _leer_indice(d: date) -> Dict[str, str]:
    """WI-307: Lee el índice hash para un día."""
    path = _index_path_for(d)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada al leer índice: %s", e)
        return {}


def _guardar_indice(d: date, indice: Dict[str, str]) -> None:
    """WI-307: Guarda el índice hash para un día."""
    try:
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_index_path_for(d), indice)
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada al guardar índice: %s", e)


# ── WI-317: Índice invertido de keywords ──────────────────────────────────

def _extract_keywords(texto: str, max_keywords: int = 20) -> List[str]:
    """WI-317: Extrae palabras clave de un texto.
    
    Filtra stopwords, palabras cortas (<3 chars), y limita a max_keywords.
    """
    palabras = [w.lower() for w in texto.split() if len(w) > 2 and w.lower() not in _SPANISH_STOPWORDS]
    # Deduplicar y limitar
    return list(set(palabras))[:max_keywords]


def _leer_indice_kw(d: date) -> Dict[str, List[str]]:
    """WI-317: Lee el índice invertido (keywords→[hashes]) para un día."""
    path = _keyword_path_for(d)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return {k: v for k, v in data.items() if isinstance(v, list)}
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada al leer índice kw: %s", e)
        return {}


def _guardar_indice_kw(d: date, indice: Dict[str, List[str]]) -> None:
    """WI-317: Guarda el índice invertido para un día."""
    try:
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(_keyword_path_for(d), indice)
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada al guardar índice kw: %s", e)


def _construir_indice_kw(d: date) -> Dict[str, List[str]]:
    """WI-317: Construye índice invertido desde JSONL raw.
    
    Mapea: keyword → [hashes que contienen esa keyword]
    """
    indice = {}
    items = _read_raw(d)
    for item in items:
        h = item.get('meta', {}).get('hash')
        if not h:
            continue
        texto = item.get('text', '')
        keywords = _extract_keywords(texto)
        for kw in keywords:
            if kw not in indice:
                indice[kw] = []
            if h not in indice[kw]:  # Evitar duplicados
                indice[kw].append(h)
    return indice


# ── Funciones principales ─────────────────────────────────────────

def add_memory(role: str, text: str, meta: dict | None = None) -> None:
    """Añade una entrada de memoria con hash de deduplicación.
    
    WI-307: Si el hash ya existe, no duplica.
    
    Args:
        role: 'user'|'assistant'|'system'
        text: texto a almacenar
        meta: dict opcional con metadatos
    """
    d = date.today()
    path = _raw_path_for(d)
    entry = {
        "ts": datetime.now().isoformat(),
        "role": role,
        "text": text,
        "meta": meta or {},
    }
    
    # WI-307: Calcular hash y verificar duplicado
    h = _hash_entry(entry)
    indice = _leer_indice(d)
    if h in indice:
        logger.debug(f"Memoria: entrada duplicada (hash {h[:8]}...)")
        return
    
    # Guardar con hash en meta
    entry['meta']['hash'] = h
    
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # Actualizar índice
        indice[h] = entry['ts']
        _guardar_indice(d, indice)
        
        logger.debug(f"Memoria: +{role} ({len(text)} chars, hash {h[:8]}...)")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)


def _read_raw(d: date) -> List[dict]:
    path = _raw_path_for(d)
    if not path.exists():
        return []
    items = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    items.append(json.loads(ln))
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)
                    continue
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
        return []
    return items


_SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este",
}


def _extract_summary(d: date) -> str:
    """ALBEDO: Extrae resumen del día."""
    items = _read_raw(d)
    if not items:
        return "Sin actividad."
    
    roles = {'user': 0, 'assistant': 0, 'system': 0}
    char_count = 0
    for item in items:
        role = item.get('role', '?')
        if role in roles:
            roles[role] += 1
        char_count += len(item.get('text', ''))
    
    resumen = (
        f"Resumen del {d.isoformat()}:\n"
        f"  {roles['user']} intervenciones del usuario\n"
        f"  {roles['assistant']} respuestas de Computadora\n"
        f"  {roles['system']} eventos de sistema\n"
        f"  {char_count} caracteres totales\n"
        f"  Última actividad: {items[-1].get('ts', 'desconocida')[:16]}\n"
    )
    return resumen


def _simple_extractive_summary(texts: List[str], max_sentences: int = 3) -> str:
    """Genera un resumen extractivo simple a partir de una lista de textos.

    Toma hasta `max_sentences` oraciones de los textos en orden de aparición.
    """
    if not texts:
        return ""

    sentences: List[str] = []
    for text in texts:
        if not isinstance(text, str):
            continue
        cleaned = text.replace("\n", " ").strip()
        if not cleaned:
            continue

        # Dividir en oraciones simples por punto.
        for sentence in cleaned.split("."):
            sentence = sentence.strip()
            if not sentence:
                continue
            sentences.append(sentence)
            if len(sentences) >= max_sentences:
                break
        if len(sentences) >= max_sentences:
            break

    if not sentences:
        return ""

    summary = ". ".join(sentences[:max_sentences])
    if not summary.endswith("."):
        summary += "."
    return summary


def compress_day(d: date) -> None:
    """Compress day: genera resumen + muestra + limpia raw si muy grande."""
    items = _read_raw(d)
    if not items:
        return
    
    # Resumen
    summary = _extract_summary(d)
    sp = _summary_path_for(d)
    try:
        sp.write_text(summary, encoding="utf-8")
        logger.debug(f"Memoria: resumen {d.isoformat()} guardado")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
    
    # Muestra reducida (primeros 5 y últimos 5)
    if len(items) > 10:
        sample = items[:5] + items[-5:]
    else:
        sample = items
    smp = _sample_path_for(d)
    try:
        from computadora.utilidades.io_seguro import escribir_json_atomico
        escribir_json_atomico(smp, sample)
        logger.debug(f"Memoria: muestra {d.isoformat()} guardada")
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)


def compress_yesterday_if_pending() -> None:
    """Comprime ayer si no se comprimió."""
    yesterday = date.today() - timedelta(days=1)
    sp = _summary_path_for(yesterday)
    if not sp.exists() and _raw_path_for(yesterday).exists():
        compress_day(yesterday)


_RETENCION_RAW_DIAS = 90


def purgar_raw_antiguos(dias_retencion: int = _RETENCION_RAW_DIAS) -> int:
    """Libera espacio de verdad: borra el .jsonl crudo de días más viejos
    que `dias_retencion`, una vez que ya existe su resumen+muestra.

    FIX: compress_day() generaba resumen y muestra pero NUNCA tocaba el
    crudo original — con el tiempo esto solo SUMA archivos, nunca libera
    espacio (confirmado: 572KB tras ~6 meses de uso real, no urgente hoy,
    pero crecería sin límite indefinidamente). Nunca se borra un crudo sin
    resumen (lo genera primero si falta) — así nunca se pierde información
    sin al menos un respaldo comprimido. El índice hash/keyword y la
    muestra NO se borran (son pequeños y es lo que usa buscar_en_memoria
    para recuperar contexto de días viejos).

    Returns:
        Cantidad de archivos crudos eliminados.
    """
    if not DATA_DIR.exists():
        return 0
    limite = date.today() - timedelta(days=dias_retencion)
    eliminados = 0
    for raw_file in sorted(DATA_DIR.glob("memoria_raw_*.jsonl")):
        fecha_str = raw_file.stem.replace("memoria_raw_", "")
        try:
            d = date.fromisoformat(fecha_str)
        except ValueError:
            continue
        if d >= limite:
            continue
        if not _summary_path_for(d).exists():
            try:
                compress_day(d)
            except Exception as e:  # RF-167
                logger.debug(f"No se pudo comprimir {d} antes de purgar: {e}")
                continue
            if not _summary_path_for(d).exists():
                continue  # compress_day no generó resumen (día vacío) — no purgar a ciegas
        try:
            raw_file.unlink()
            eliminados += 1
            logger.info(f"Memoria: crudo de {d.isoformat()} purgado (ya resumido, >{dias_retencion}d de retención)")
        except Exception as e:  # RF-167
            logger.debug(f"No se pudo purgar {raw_file}: {e}")
    return eliminados


def buscar_en_memoria(consulta: str, dias: int = 30) -> str:
    """WI-317: Busca en memoria usando índice invertido (O(k) donde k=matches).
    
    Algoritmo:
    1. Normaliza query → keywords
    2. Lee índice invertido (keyword→[hashes]) para cada día
    3. Intersección: hashes que contengan TODAS las keywords
    4. Lazy-load solo items que matchean
    """
    if not consulta or not consulta.strip():
        return "No se proporcionó una consulta de búsqueda."

    # Normalizar query
    palabras = set(
        w.lower() for w in consulta.split()
        if len(w) > 2 and w.lower() not in _SPANISH_STOPWORDS
    )
    if not palabras:
        palabras = {consulta.lower().strip()}

    resultados = []
    hoy = date.today()

    for i in range(dias):
        d = hoy - timedelta(days=i)
        
        # WI-317: Intentar leer índice kw, si no existe construir y guardar
        indice_kw = _leer_indice_kw(d)
        if not indice_kw and _raw_path_for(d).exists():
            indice_kw = _construir_indice_kw(d)
            _guardar_indice_kw(d, indice_kw)
        
        if not indice_kw:
            continue
        
        # Intersección: hashes que matchean TODAS las palabras
        hashes_match = None
        for palabra in palabras:
            palabra_lower = palabra.lower()
            hashes_palabra = set(indice_kw.get(palabra_lower, []))
            if hashes_match is None:
                hashes_match = hashes_palabra
            else:
                hashes_match &= hashes_palabra  # Intersección
        
        if not hashes_match:
            continue
        
        # Lazy-load: solo leer items que matchean
        raw = _read_raw(d)
        item_by_hash = {item.get('meta', {}).get('hash'): item for item in raw}
        
        encontrados = []
        for h in sorted(hashes_match):
            if h in item_by_hash:
                item = item_by_hash[h]
                role = item.get("role", "?")
                ts = item.get("ts", "")
                hora = ts[11:16] if len(ts) > 16 else ""
                encontrados.append(f"  [{hora} {role}] (hash:{h[:8]}) {item.get('text', '')[:150]}")
        
        if encontrados:
            dia_label = "Hoy" if i == 0 else ("Ayer" if i == 1 else d.strftime("%d/%m/%Y"))
            resultados.append(f"{dia_label}:\n" + "\n".join(encontrados[:5]))

    if not resultados:
        return f"No encontré recuerdos sobre '{consulta}' en los últimos {dias} días."

    return "Recuerdos encontrados:\n\n" + "\n\n".join(resultados[:10])


def obtener_recuerdo_reciente(dias: int = 7) -> Optional[dict]:
    """Retorna el ítem de memoria más reciente (de cualquier contenido)
    dentro de los últimos `dias` días, o None si no hay ninguno.

    A diferencia de `buscar_en_memoria`, no requiere una palabra clave —
    sirve para mostrar un recuerdo genuino reciente sin depender de que el
    texto contenga un término concreto (p.ej. buscar "señor" como placeholder
    casi nunca matchea nada real, porque el texto almacenado rara vez
    contiene esa palabra exacta).
    """
    hoy = date.today()
    for i in range(dias):
        d = hoy - timedelta(days=i)
        items = _read_raw(d)
        if items:
            return items[-1]
    return None


def get_by_hash(h: str, search_days: int = 30) -> Optional[dict]:
    """WI-317: Busca por hash exacto en O(1) si índice existe.
    
    Intenta primero leer índice hash (O(1) si está pre-indexado),
    fallback a búsqueda lineal si es necesario.
    """
    hoy = date.today()
    for i in range(search_days):
        d = hoy - timedelta(days=i)
        
        # Intentar lectura rápida desde índice hash
        idx_hash = _leer_indice(d)
        if h in idx_hash:  # Hash encontrado en índice
            # Aún necesita lazy-load del item, pero sabemos qué día
            items = _read_raw(d)
            for item in items:
                if item.get('meta', {}).get('hash') == h:
                    return item
        
        # Fallback: búsqueda lineal si índice no tiene el hash
        items = _read_raw(d)
        for item in items:
            if item.get('meta', {}).get('hash') == h:
                return item
    
    return None


_daemon_thread = None


def _daemon_loop():
    try:
        compress_yesterday_if_pending()
        purgar_raw_antiguos()
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)

    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
        wait = (tomorrow - now).total_seconds()
        time.sleep(max(60, wait))
        try:
            target = date.today() - timedelta(days=1)
            compress_day(target)
            purgar_raw_antiguos()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)


_compressor_lock = threading.Lock()


def _migrar_jsonl_a_hash_index(d: date) -> bool:
    """WI-317: Migrador: asegura que JSONL tenga hashes + índices.
    
    Para datos viejos (sin estructura hash), genera hashes, guarda en
    índices, y reescribe JSONL con hashes en meta.
    
    Returns:
        True si se realizó migración, False si ya estaba migrado.
    """
    items = _read_raw(d)
    if not items:
        return False
    
    # Verificar si ya tiene hashes
    items_sin_hash = [item for item in items if not item.get('meta', {}).get('hash')]
    if not items_sin_hash:
        return False  # Ya está migrado
    
    # Reindexar todos los items
    indice_hash = _leer_indice(d)
    indice_kw = _leer_indice_kw(d)
    
    for item in items:
        # Generar hash si falta
        if not item.get('meta'):
            item['meta'] = {}
        if not item['meta'].get('hash'):
            h = _hash_entry(item)
            item['meta']['hash'] = h
            indice_hash[h] = item.get('ts', '')
        
        # Agregar a índice de keywords
        h = item['meta']['hash']
        texto = item.get('text', '')
        for kw in _extract_keywords(texto):
            if kw not in indice_kw:
                indice_kw[kw] = []
            if h not in indice_kw[kw]:
                indice_kw[kw].append(h)
    
    # Reescribir JSONL con hashes
    try:
        path = _raw_path_for(d)
        with path.open('w', encoding='utf-8') as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        _guardar_indice(d, indice_hash)
        _guardar_indice_kw(d, indice_kw)
        logger.info(f"WI-317: Migración completada para {d.isoformat()} ({len(items_sin_hash)} items reindexados)")
        return True
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada en migración: %s", e)
        return False


def init_memory_index(dias: int = 90) -> int:
    """WI-317: Inicializa índices para días existentes.
    
    Itera sobre últimos N días, construye índices faltantes,
    y ejecuta migración si es necesario.
    
    Returns:
        Número de días reindexados.
    """
    hoy = date.today()
    reindexados = 0
    
    for i in range(dias):
        d = hoy - timedelta(days=i)
        path_raw = _raw_path_for(d)
        path_kw = _keyword_path_for(d)
        
        if not path_raw.exists():
            continue
        
        # Si no existe índice kw, construir
        if not path_kw.exists():
            try:
                indice_kw = _construir_indice_kw(d)
                _guardar_indice_kw(d, indice_kw)
                reindexados += 1
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada en init_memory_index: %s", e)
        
        # Ejecutar migración si hay datos sin hash
        try:
            if _migrar_jsonl_a_hash_index(d):
                reindexados += 1
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada en migración: %s", e)
    
    logger.info(f"WI-317: init_memory_index completado ({reindexados} días procesados)")
    return reindexados


def start_daily_compressor():
    global _daemon_thread
    if _daemon_thread and _daemon_thread.is_alive():
        return
    with _compressor_lock:
        if _daemon_thread and _daemon_thread.is_alive():
            return
        t = threading.Thread(target=_daemon_loop, daemon=True, name="memoria-compressor")
        _daemon_thread = t
        t.start()


# ── WI-308: Conciencia Temporal — Lagunas y Tiempo PC ────────────

def _leer_temporal() -> dict:
    """Lee o inicializa el archivo de conciencia temporal."""
    if _TEMPORAL_PATH.exists():
        try:
            return json.loads(_TEMPORAL_PATH.read_text(encoding="utf-8"))
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
    return {
        "sesiones": [],
        "tiempo_activo_total_s": 0,
        "primera_activacion": None,
        "ultimo_boot_pc": None,  # WI-308: Boot time del PC
        "lagunas": [],  # WI-308: Periodos donde Computadora estuvo apagada pero PC encendido
    }


def _guardar_temporal(data: dict) -> None:
    from computadora.utilidades.io_seguro import escribir_json_atomico
    escribir_json_atomico(_TEMPORAL_PATH, data)


def registrar_activacion() -> None:
    """WI-308: Registra activación con detección de lagunas."""
    data = _leer_temporal()
    ahora = datetime.now()
    boot_pc = datetime.fromtimestamp(psutil.boot_time())
    
    # WI-308: Guardar boot time del PC
    data["ultimo_boot_pc"] = boot_pc.isoformat()
    
    # WI-308: Detectar laguna desde última desactivación
    sesiones = data.get("sesiones", [])
    if sesiones and sesiones[-1].get("desactivacion") is not None:
        ultima_desac = datetime.fromisoformat(sesiones[-1]["desactivacion"])
        
        # Calcular laguna: tiempo entre última desactivación y ahora
        # Pero restar tiempo de PC apagado (boot_time marca reinicio)
        laguna_total = (ahora - ultima_desac).total_seconds()
        
        # Si hubo reinicio del PC, la laguna real es desde el boot
        if boot_pc > ultima_desac:
            laguna_real = (ahora - boot_pc).total_seconds()
        else:
            laguna_real = laguna_total
        
        if laguna_real > 60:  # Solo lagunas > 1 minuto
            laguna = {
                "inicio_laguna": ultima_desac.isoformat(),
                "fin_laguna": ahora.isoformat(),
                "duracion_s": int(laguna_real),
                "hubo_reinicio_pc": boot_pc > ultima_desac,
            }
            data.setdefault("lagunas", []).append(laguna)
            logger.info(f"WI-308: Laguna detectada: {laguna_real/3600:.1f}h desde última sesión")
    
    # Registrar sesión actual
    data["sesiones"].append({
        "activacion": ahora.isoformat(),
        "desactivacion": None,
        "duracion_s": 0,
        "boot_pc": boot_pc.isoformat(),
    })
    
    if data["primera_activacion"] is None:
        data["primera_activacion"] = ahora.isoformat()
    
    _guardar_temporal(data)
    logger.info(f"Conciencia temporal: sesión #{len(data['sesiones'])} iniciada")


def registrar_desactivacion() -> None:
    """Registra el fin de la sesión actual."""
    try:
        gestor = obtener_gestor_procesos()
        gestor.terminar_todos()
        logger.info("Procesos huérfanos terminados en shutdown")
    except Exception as e:
        logger.warning(f"Error en cleanup procesos: {e}")

    data = _leer_temporal()
    if not data["sesiones"]:
        return
    ultima = data["sesiones"][-1]
    if ultima["desactivacion"] is not None:
        return
    
    ahora = datetime.now()
    ultima["desactivacion"] = ahora.isoformat()
    try:
        inicio = datetime.fromisoformat(ultima["activacion"])
        duracion = max(0, (ahora - inicio).total_seconds())
    except Exception as e:  # RF-167
        logger.debug("Excepcion ignorada: %s", e)
        duracion = 0
    ultima["duracion_s"] = int(duracion)
    
    data["tiempo_activo_total_s"] = sum(
        s.get("duracion_s", 0) for s in data["sesiones"]
    )
    _guardar_temporal(data)
    logger.info(f"Conciencia temporal: sesión cerrada ({duracion:.0f}s)")


def calcular_tiempo_activo() -> dict:
    """WI-308: Retorna estadísticas completas de tiempo activo + PC.
    
    Incluye:
    - horas: tiempo total que Computadora ha estado activa
    - sesiones: número de sesiones
    - lagunas: periodos donde PC estaba encendido pero Computadora no
    - tiempo_pc_encendido_h: horas totales del PC desde primera activación
    
    Returns:
        dict con estadísticas.
    """
    data = _leer_temporal()
    total_s = data.get("tiempo_activo_total_s", 0)
    
    # Sumar sesión actual en curso
    sesiones = data.get("sesiones", [])
    if sesiones and sesiones[-1].get("desactivacion") is None:
        try:
            inicio = datetime.fromisoformat(sesiones[-1]["activacion"])
            total_s += max(0, (datetime.now() - inicio).total_seconds())
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
    
    # WI-308: Calcular tiempo del PC encendido
    primera_activacion = data.get("primera_activacion")
    if primera_activacion:
        try:
            inicio = datetime.fromisoformat(primera_activacion)
            tiempo_pc = (datetime.now() - inicio).total_seconds()
        except Exception:
            tiempo_pc = total_s
    else:
        tiempo_pc = total_s
    
    # WI-308: Calcular lagunas totales
    lagunas = data.get("lagunas", [])
    lagunas_total_s = sum(l.get("duracion_s", 0) for l in lagunas)
    
    result = {
        "horas": round(total_s / 3600, 2),
        "sesiones": len(sesiones),
        "primera_activacion": primera_activacion,
        "lagunas_detectadas": len(lagunas),
        "lagunas_horas": round(lagunas_total_s / 3600, 2),
        "tiempo_pc_encendido_h": round(tiempo_pc / 3600, 2),
        "horas_reales_ejecucion": round((total_s + lagunas_total_s) / 3600, 2),
    }
    return result


def obtener_lagunas(detallado: bool = False) -> List[dict]:
    """WI-308: Retorna lista de lagunas de memoria.
    
    Args:
        detallado: Si True, incluye duración legible.
    
    Returns:
        Lista de lagunas.
    """
    data = _leer_temporal()
    lagunas = data.get("lagunas", [])
    if not detallado:
        return lagunas[-10:]  # Últimas 10
    
    detalladas = []
    for l in lagunas[-20:]:
        detalladas.append({
            **l,
            "duracion_h": round(l.get("duracion_s", 0) / 3600, 2),
            "desde": l.get("inicio_laguna", "")[:19],
            "hasta": l.get("fin_laguna", "")[:19],
        })
    return detalladas


