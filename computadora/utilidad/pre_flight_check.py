"""
PRE-FLIGHT CHECK — Auto-detección de hardware + Descarga automática de modelos.

FP-154: Sistema se auto-verifica y auto-repara en boot.
- Detecta hardware disponible (GPU VRAM, RAM, CPU)
- Selecciona modelo Ollama apropiado (coherencia + velocidad)
- Descarga modelo automáticamente si falta
- Valida todo antes de iniciar interfaz gráfica

Fases:
  1. DETECTAR: Hardware disponible
  2. SELECCIONAR: Modelo Ollama óptimo para el hardware
  3. VERIFICAR: Ollama corriendo + modelo descargado
  4. DESCARGAR: Si falta, iniciar descarga automática
  5. VALIDAR: Status listo para usar
"""

import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from loguru import logger


@dataclass
class HardwareProfile:
    """Perfil de hardware disponible."""
    total_ram_gb: float
    gpu_available: bool
    gpu_vram_gb: Optional[float]
    gpu_type: Optional[str]  # "nvidia", "amd", "intel", None
    cuda_available: bool
    cuda_compute_capability: Optional[str]


@dataclass
class OllamaModelProfile:
    """Perfil de modelo Ollama con requisitos y características."""
    name: str
    size_gb: float
    min_ram_gb: float
    min_vram_gb: Optional[float]  # None = no requiere GPU
    coherence_score: float  # 0-10, mayor = mejor razonamiento
    speed_score: float  # 0-10, mayor = más rápido
    recommended_for: List[str]  # e.g., ["reasoning", "fast", "coding"]
    chat_capable: bool = True  # False para modelos de embeddings sólo
    # FIX (investigación 2026-10-03): el catálogo anterior no registraba si
    # un modelo soporta tool-calling nativo de Ollama (parámetro `tools` en
    # /api/chat). Computadora SIEMPRE manda `tools` cuando hay herramientas
    # disponibles (feature flag nlu_herramientas) — un modelo sin este
    # soporte (confirmado con llama2:7b: "does not support tools") rompe
    # TODA interacción tipo-tarea con un 400 inmediato, no solo "responde
    # peor". Por eso es un filtro duro en _select_optimal_model, no solo
    # un bonus de puntaje.
    supports_tools: bool = False


# Catálogo de modelos Ollama con perfiles.
# FIX: min_vram_gb ahora se deriva de mediciones reales (ollama ps) con
# margen, no de estimaciones arbitrarias — antes, p.ej., llama2:7b
# declaraba min_vram_gb=2 cuando en la práctica carga ~6GB (confirmado con
# `ollama ps`: 64%/36% CPU/GPU split en una GPU de 4GB, la causa real de
# que Ollama tardara 30-50s+ por respuesta en vez de <1s).
_OLLAMA_MODELS = [
    # Modelos modernos con tool-calling nativo — preferidos siempre que
    # quepan, por el filtro duro de supports_tools.
    OllamaModelProfile(
        name="qwen2.5:7b-instruct",
        size_gb=4.7,
        min_ram_gb=8,
        min_vram_gb=6.0,
        coherence_score=8.5,
        speed_score=7.5,
        recommended_for=["tools", "reasoning", "chat"],
        supports_tools=True,
    ),
    OllamaModelProfile(
        name="qwen2.5:3b-instruct",
        size_gb=1.9,
        min_ram_gb=4,
        min_vram_gb=2.8,
        coherence_score=7.5,
        speed_score=9.0,
        recommended_for=["tools", "chat", "fast"],
        supports_tools=True,
    ),
    OllamaModelProfile(
        name="llama3.2:3b",
        size_gb=2.0,
        min_ram_gb=4,
        min_vram_gb=2.8,
        coherence_score=7.0,
        speed_score=8.5,
        recommended_for=["tools", "chat"],
        supports_tools=True,
    ),
    OllamaModelProfile(
        name="qwen2.5:1.5b-instruct",
        size_gb=1.0,
        min_ram_gb=3,
        min_vram_gb=1.5,
        coherence_score=6.0,
        speed_score=9.5,
        recommended_for=["tools", "fast", "mobile"],
        supports_tools=True,
    ),
    # Modelos legacy sin tool-calling nativo — se mantienen en el catálogo
    # solo para reconocer instalaciones existentes (p.ej. un usuario que ya
    # tenía llama2:7b de antes); nunca se eligen como óptimos a descargar
    # mientras exista una alternativa con supports_tools=True que quepa.
    OllamaModelProfile(
        name="llama2:7b",
        size_gb=4.2,
        min_ram_gb=8,
        min_vram_gb=5.5,
        coherence_score=7.5,
        speed_score=4.0,
        recommended_for=["legacy"],
        supports_tools=False,
    ),
    OllamaModelProfile(
        name="mistral:7b",
        size_gb=4.1,
        min_ram_gb=8,
        min_vram_gb=5.0,
        coherence_score=7.0,
        speed_score=5.0,
        recommended_for=["legacy"],
        supports_tools=False,
    ),
    OllamaModelProfile(
        name="gemma3:4b",
        size_gb=2.5,
        min_ram_gb=6,
        min_vram_gb=3.2,
        coherence_score=6.5,
        speed_score=6.0,
        recommended_for=["legacy"],
        supports_tools=False,
    ),
    OllamaModelProfile(
        name="orca-mini:3b",
        size_gb=1.9,
        min_ram_gb=4,
        min_vram_gb=2.5,
        coherence_score=5.5,
        speed_score=6.5,
        recommended_for=["legacy"],
        supports_tools=False,
    ),
    OllamaModelProfile(
        name="nomic-embed-text:latest",
        size_gb=0.3,
        min_ram_gb=2,
        min_vram_gb=None,
        coherence_score=0.0,
        speed_score=10.0,
        recommended_for=["embeddings"],
        chat_capable=False,
    ),
]


def _detect_hardware() -> HardwareProfile:
    """
    Detecta hardware disponible del sistema.
    
    Returns:
        HardwareProfile con especificaciones detectadas
    """
    try:
        import psutil
    except ImportError:
        logger.warning("⚠ psutil no disponible, usando defaults")
        return HardwareProfile(
            total_ram_gb=8.0,
            gpu_available=False,
            gpu_vram_gb=None,
            gpu_type=None,
            cuda_available=False,
            cuda_compute_capability=None,
        )

    # RAM
    try:
        total_ram_bytes = psutil.virtual_memory().total
        total_ram_gb = total_ram_bytes / (1024 ** 3)
    except Exception as e:
        logger.warning(f"⚠ No se pudo detectar RAM: {e}")
        total_ram_gb = 8.0

    # GPU NVIDIA
    gpu_available = False
    gpu_vram_gb = None
    gpu_type = None
    cuda_available = False
    cuda_compute_capability = None

    try:
        import torch

        if torch.cuda.is_available():
            gpu_available = True
            gpu_type = "nvidia"
            cuda_available = True

            # VRAM
            try:
                gpu_vram_bytes = torch.cuda.get_device_properties(0).total_memory
                gpu_vram_gb = gpu_vram_bytes / (1024 ** 3)
            except Exception as e:
                logger.warning(f"⚠ No se pudo detectar VRAM NVIDIA: {e}")
                gpu_vram_gb = 2.0

            # Compute capability
            try:
                capability = torch.cuda.get_device_capability(0)
                cuda_compute_capability = f"{capability[0]}.{capability[1]}"
            except Exception:
                pass

            logger.info(f"✓ GPU NVIDIA detectada: {gpu_vram_gb:.1f} GB VRAM (CC {cuda_compute_capability})")

    except ImportError:
        logger.debug("torch no disponible para GPU detection")

    # AMD/Intel GPUs (futuro: agregar soporte)
    # Por ahora, solo NVIDIA

    return HardwareProfile(
        total_ram_gb=total_ram_gb,
        gpu_available=gpu_available,
        gpu_vram_gb=gpu_vram_gb,
        gpu_type=gpu_type,
        cuda_available=cuda_available,
        cuda_compute_capability=cuda_compute_capability,
    )


def _get_installed_models(base_url: str = "http://localhost:11434") -> List[str]:
    """
    Obtiene lista de modelos ya instalados en Ollama.
    
    Returns:
        Lista de nombres de modelos instalados
    """
    try:
        url = f"{base_url}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            installed = [m["name"] for m in data.get("models", [])]
            return installed
    except Exception as e:
        logger.debug(f"⚠ No se pudo obtener lista de modelos: {e}")
        return []


def _is_chat_capable_model(model_name: str, profile: Optional[OllamaModelProfile] = None) -> bool:
    """Determina si un modelo Ollama debe ser usado para chat conversacional."""
    if profile is not None and not profile.chat_capable:
        return False
    lower = model_name.lower()
    if "embed" in lower or "embedding" in lower:
        return False
    return True


_MARGEN_VRAM = 0.85  # FIX: dejar ~15% de VRAM libre (contexto, otras apps) en vez de usar el 100%


def _cabe_en_hardware(model: "OllamaModelProfile", hardware: HardwareProfile) -> bool:
    if model.min_ram_gb > hardware.total_ram_gb:
        return False
    if model.min_vram_gb is not None:
        if not hardware.gpu_available:
            return False
        if hardware.gpu_vram_gb and model.min_vram_gb > hardware.gpu_vram_gb * _MARGEN_VRAM:
            return False
    return True


def _score(model: "OllamaModelProfile") -> float:
    # FIX: supports_tools ahora es un bono grande y decisivo, no un matiz —
    # un modelo sin tool-calling nativo rompe (400 inmediato) toda petición
    # tipo-tarea mientras la app tenga herramientas activas, así que debe
    # superar en puntaje a cualquier modelo legacy sin ese soporte, salvo
    # que NINGÚN modelo con tools quepa en el hardware disponible.
    base = model.coherence_score * 0.6 + model.speed_score * 0.4
    return base + (3.0 if model.supports_tools else 0.0)


def _generic_profile(model_name: str) -> "OllamaModelProfile":
    """Perfil conservador para un modelo instalado que no está en el catálogo."""
    return OllamaModelProfile(
        name=model_name,
        size_gb=0,
        min_ram_gb=4,
        min_vram_gb=None,
        coherence_score=7.0,
        speed_score=6.0,
        recommended_for=["general"],
        chat_capable=_is_chat_capable_model(model_name),
        supports_tools=False,  # Conservador: no asumir soporte de tools sin confirmarlo
    )


def _select_best_from_installed(installed_models: List[str], hardware: HardwareProfile) -> Optional[str]:
    """
    Selecciona el mejor modelo de los que YA ESTÁN INSTALADOS y caben en el
    hardware. Usado solo como vía rápida cuando coincide con el óptimo
    global (ver run_pre_flight_check) — ya NO se usa para preferir un
    modelo instalado peor sobre uno mejor que haría falta descargar.
    """
    if not installed_models:
        return None

    compatible_models = []
    for model_name in installed_models:
        model_profile = next((p for p in _OLLAMA_MODELS if p.name == model_name), None)
        if model_profile is None:
            logger.debug(f"  ℹ {model_name}: modelo no en catálogo, perfil genérico conservador")
            model_profile = _generic_profile(model_name)

        if not _is_chat_capable_model(model_name, model_profile):
            logger.debug(f"  ✗ {model_name}: no es modelo conversacional (embeddings-only)")
            continue
        if not _cabe_en_hardware(model_profile, hardware):
            logger.debug(f"  ✗ {model_name}: no cabe en el hardware disponible")
            continue

        compatible_models.append(model_profile)
        logger.debug(f"  ✓ {model_name}: coherencia={model_profile.coherence_score}, "
                     f"velocidad={model_profile.speed_score}, tools={model_profile.supports_tools}")

    if not compatible_models:
        return None

    best_model = max(compatible_models, key=_score)
    logger.info(f"✓ Modelo instalado seleccionado: {best_model.name}")
    logger.info(f"  - Coherencia: {best_model.coherence_score}/10 | Velocidad: {best_model.speed_score}/10 "
                f"| Tools: {'sí' if best_model.supports_tools else 'no'}")
    return best_model.name


def _select_optimal_model(hardware: HardwareProfile) -> str:
    """
    Selecciona modelo Ollama óptimo basado en hardware, del catálogo
    completo (instalado o no) — el soporte de tool-calling nativo es un
    filtro decisivo (ver _score), no solo un matiz de calidad.

    Returns:
        Nombre del modelo recomendado
    """
    available_models = [m for m in _OLLAMA_MODELS if m.chat_capable and _cabe_en_hardware(m, hardware)]
    for m in _OLLAMA_MODELS:
        if not m.chat_capable:
            logger.debug(f"  ✗ {m.name}: no es modelo conversacional (embeddings-only)")
        elif not _cabe_en_hardware(m, hardware):
            logger.debug(f"  ✗ {m.name}: no cabe en el hardware disponible "
                         f"(RAM={m.min_ram_gb}GB, VRAM={m.min_vram_gb}GB)")

    if not available_models:
        logger.error("❌ No hay modelos Ollama que quepan en el hardware disponible")
        logger.error(f"  RAM: {hardware.total_ram_gb:.1f}GB, GPU VRAM: {hardware.gpu_vram_gb}")
        raise RuntimeError("Hardware insuficiente para cualquier modelo Ollama")

    best_model = max(available_models, key=_score)

    logger.info(f"✓ Modelo óptimo para hardware: {best_model.name}")
    logger.info(f"  - Coherencia: {best_model.coherence_score}/10")
    logger.info(f"  - Velocidad: {best_model.speed_score}/10")
    logger.info(f"  - Tools nativos: {'sí' if best_model.supports_tools else 'no'}")
    logger.info(f"  - Tamaño: {best_model.size_gb} GB")

    return best_model.name


def _is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """
    Verifica si Ollama está corriendo y accesible.
    
    Returns:
        True si accesible, False en caso contrario
    """
    try:
        with urllib.request.urlopen(f"{base_url}/api/version", timeout=2) as response:
            data = response.read()
            logger.debug(f"✓ Ollama accesible: {data.decode()}")
            return True
    except (urllib.error.URLError, Exception) as e:
        logger.warning(f"⚠ Ollama no accesible en {base_url}: {e}")
        return False


def _is_model_installed(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Verifica si un modelo está descargado en Ollama.
    
    Returns:
        True si está disponible, False si falta
    """
    try:
        import json

        url = f"{base_url}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            installed = [m["name"] for m in data.get("models", [])]

            if model_name in installed:
                logger.info(f"✓ Modelo {model_name} ya instalado")
                return True
            else:
                logger.warning(f"⚠ Modelo {model_name} NO instalado")
                logger.info(f"  Modelos disponibles: {installed}")
                return False

    except Exception as e:
        logger.warning(f"⚠ No se pudo verificar modelos: {e}")
        return False


def _download_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Descarga modelo Ollama automáticamente.
    
    Returns:
        True si descargó exitosamente, False si falló
    """
    logger.info(f"⏳ Descargando modelo {model_name}...")
    logger.info(f"  (Esto puede tomar 5-20 minutos dependiendo del tamaño)")

    try:
        # Usar ollama CLI directamente
        cmd = ["ollama", "pull", model_name]
        logger.debug(f"  Ejecutando: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Monitorear progreso
        start_time = time.time()
        last_log = start_time

        while process.poll() is None:
            # Leer output en tiempo real
            try:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    if line:
                        logger.debug(f"    {line}")

                    # Log de progreso cada 10 segundos
                    current_time = time.time()
                    if current_time - last_log > 10:
                        elapsed = int(current_time - start_time)
                        logger.info(f"  ⏳ Descargando ({elapsed}s)...")
                        last_log = current_time

            except Exception as e:
                logger.debug(f"    Error leyendo output: {e}")

            time.sleep(0.1)

        # Esperar a que termine
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"❌ Error descargando {model_name}")
            logger.error(f"  stderr: {stderr}")
            return False

        elapsed = time.time() - start_time
        logger.info(f"✓ Modelo {model_name} descargado exitosamente ({int(elapsed)}s)")
        return True

    except FileNotFoundError:
        logger.error("❌ Comando 'ollama' no encontrado. Asegúrate de que Ollama esté instalado.")
        logger.info("  Descarga desde: https://ollama.ai/download")
        return False
    except Exception as e:
        logger.error(f"❌ Error descargando modelo: {e}")
        return False


def run_pre_flight_check(config: Optional[Dict] = None) -> Tuple[bool, str, Dict]:
    """
    Ejecuta verificación pre-arranque completa.

    FIX (investigación 2026-10-03): la estrategia anterior prefería "el
    mejor modelo YA INSTALADO" sobre el óptimo real para el hardware — en
    la práctica esto significaba que, una vez que llama2:7b quedaba
    instalado, SIEMPRE se re-seleccionaba en cada arranque (su
    coherence_score hardcoded ganaba a cualquier modelo recién instalado
    que no estuviera en el catálogo), sin importar qué modelo mejor se
    descargara manualmente después. Confirmado en logs reales: esto
    explicaba por completo por qué la app seguía usando llama2:7b pese a
    cambios de configuración.

    Estrategia corregida:
    1. Detectar hardware
    2. Calcular el modelo ÓPTIMO GLOBAL para el hardware (catálogo completo,
       tool-calling nativo como filtro decisivo)
    3. Si ya está instalado → vía rápida, usarlo (sin descargar)
    4. Si NO está instalado → descargarlo
    5. Solo si el óptimo global no se puede determinar/descargar, caer a
       "el mejor de los ya instalados" como último recurso
    6. Validar

    Args:
        config: Configuración (para obtener base_url de Ollama)

    Returns:
        Tupla (éxito: bool, modelo_listo: str, estado: Dict con detalles)
    """
    logger.info("=" * 60)
    logger.info("🚀 PRE-FLIGHT CHECK — Verificación de sistema")
    logger.info("=" * 60)

    estado = {}

    # Fase 1: Detectar hardware
    logger.info("\n📊 FASE 1: Detectando hardware...")
    try:
        hardware = _detect_hardware()
        estado["hardware"] = {
            "ram_gb": hardware.total_ram_gb,
            "gpu_available": hardware.gpu_available,
            "gpu_type": hardware.gpu_type,
            "gpu_vram_gb": hardware.gpu_vram_gb,
            "cuda_available": hardware.cuda_available,
        }
        logger.info(f"  ✓ RAM: {hardware.total_ram_gb:.1f} GB")
        logger.info(f"  ✓ GPU: {hardware.gpu_type or 'No disponible'}")
        if hardware.gpu_vram_gb:
            logger.info(f"  ✓ VRAM: {hardware.gpu_vram_gb:.1f} GB")
    except Exception as e:
        logger.error(f"❌ Error detectando hardware: {e}")
        return False, "", estado

    # Fase 3: Verificar Ollama accesible (ANTES de intentar obtener modelos)
    logger.info("\n🔗 FASE 2: Verificando acceso a Ollama...")
    base_url = "http://localhost:11434"
    if config and "ollama" in config:
        base_url = config["ollama"].get("base_url", base_url)

    if not _is_ollama_running(base_url):
        logger.error(f"❌ Ollama no accesible en {base_url}")
        logger.info("  Intenta: ollama serve")
        estado["ollama_running"] = False
        return False, "", estado

    logger.info(f"✓ Ollama accesible")
    estado["ollama_running"] = True

    # Fase 3: Modelos ya instalados (informativo, para la vía rápida)
    logger.info("\n📦 FASE 3: Obteniendo modelos instalados...")
    installed_models = _get_installed_models(base_url)
    if installed_models:
        logger.info(f"  ✓ Modelos instalados encontrados: {installed_models}")
    else:
        logger.info("  ℹ No hay modelos instalados previamente")

    # Fase 4: SIEMPRE calcular el óptimo global primero (ver docstring —
    # esto es lo que corrige el bug de "se queda pegado al modelo viejo").
    logger.info("\n🎯 FASE 4: Seleccionando modelo óptimo para el hardware...")
    try:
        model_name = _select_optimal_model(hardware)
        estado["selected_model"] = model_name
    except RuntimeError as e:
        logger.error(f"❌ {e}")
        # Último recurso: algo ya instalado, aunque no sea el óptimo global
        fallback = _select_best_from_installed(installed_models, hardware) if installed_models else None
        if fallback:
            logger.warning(f"  ⚠ Usando {fallback} como último recurso (ya instalado)")
            estado["selected_model"] = fallback
            estado["selection_strategy"] = "fallback_installed"
            estado["model_ready"] = True
            return True, fallback, estado
        return False, "", estado

    if model_name in (installed_models or []):
        logger.info(f"  ✓ Modelo óptimo {model_name} ya instalado — vía rápida, sin descargar")
        estado["selection_strategy"] = "optimal_already_installed"
        estado["model_ready"] = True
    else:
        logger.info(f"\n📦 FASE 4 (continuación): Descargando modelo óptimo {model_name}...")
        estado["selection_strategy"] = "optimal_download"
        estado["model_ready"] = False

        if _download_model(model_name, base_url):
            logger.info(f"✓ Descarga completada")
            estado["model_ready"] = True
            if not _is_model_installed(model_name, base_url):
                logger.error(f"❌ {model_name} no se verificó después de descargar")
                return False, "", estado
        else:
            logger.error(f"❌ No se pudo descargar {model_name} — probando último recurso")
            fallback = _select_best_from_installed(installed_models, hardware) if installed_models else None
            if fallback:
                logger.warning(f"  ⚠ Usando {fallback} como último recurso (ya instalado)")
                estado["selected_model"] = fallback
                estado["selection_strategy"] = "fallback_installed"
                estado["model_ready"] = True
                return True, fallback, estado
            return False, "", estado

    # Fase 5: Validación final
    logger.info("\n✅ FASE 5: Validación final...")
    if estado.get("model_ready") and estado.get("ollama_running"):
        logger.info("=" * 60)
        logger.info("🎉 SISTEMA LISTO PARA ARRANCAR")
        logger.info(f"  Modelo: {model_name}")
        logger.info(f"  Estrategia: {estado.get('selection_strategy', 'unknown')}")
        logger.info(f"  Hardware: {hardware.gpu_type or 'CPU'}")
        logger.info("=" * 60)
        return True, model_name, estado
    else:
        logger.error("❌ Sistema NO está listo")
        return False, "", estado


if __name__ == "__main__":
    # Test standalone
    success, model, estado = run_pre_flight_check()
    print(f"\nResultado: {'OK' if success else 'FALLO'}")
    print(f"Modelo: {model}")
    print(json.dumps(estado, indent=2, ensure_ascii=False).encode("utf-8", "replace").decode("utf-8"))
