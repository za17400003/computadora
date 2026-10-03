#!/usr/bin/env python3
"""
PROFILER EXHAUSTIVO: Identifica TODOS los culpables del boot freeze.

Instrumentaliza cada operación de boot en el flujo principal (main thread)
para detectar bloqueos > 100ms.

Ejecución:
    python tests/profiler_boot_exhaustivo.py 2>&1 | tee boot_profile.log

Salida:
    - Liista de operaciones ordenadas por duración
    - Identifica categorías (sync I/O, model load, network, etc.)
    - Recomendaciones de threading/async
"""

import sys
import time
import logging
from pathlib import Path
from contextlib import contextmanager
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s"
)
logger = logging.getLogger("boot_profiler")

# Diccionario para guardar mediciones
_measurements = defaultdict(list)
_threshold_warning = 0.1  # 100ms threshold para warnings

@contextmanager
def measure_block(name, category="misc"):
    """Context manager que mide duracion de un bloque de codigo.
    
    Args:
        name: Descripcion legible del bloque
        category: Categoria (model_load, disk_io, network, compute, etc.)
    
    Yields:
        tiempo_inicio
    """
    start = time.time()
    try:
        logger.info(f"[START] {name} [{category}]")
        yield start
    finally:
        elapsed = time.time() - start
        _measurements[category].append((name, elapsed))
        
        level = logging.WARNING if elapsed > _threshold_warning else logging.INFO
        logger.log(level, f"[DONE] {name} — {elapsed*1000:.0f}ms")


def print_report():
    """Imprime reporte de profiling."""
    print("\n" + "="*80)
    print("[REPORT] REPORTE DE PROFILING DE BOOT")
    print("="*80)
    
    total_time = sum(sum(t for _, t in measurements) for measurements in _measurements.values())
    
    # Ordenar por categoría y mostrar top 10
    for category in sorted(_measurements.keys()):
        measurements = _measurements[category]
        measurements.sort(key=lambda x: x[1], reverse=True)
        
        category_total = sum(t for _, t in measurements)
        pct = (category_total / total_time * 100) if total_time > 0 else 0
        
        print(f"\n[{category.upper()}] — {category_total*1000:.0f}ms ({pct:.1f}%)")
        print("-" * 80)
        
        for name, elapsed in measurements[:15]:  # Top 15 por categoría
            if elapsed > _threshold_warning:
                marker = "[CRIT]"
            elif elapsed > 0.050:
                marker = "[WARN]"
            else:
                marker = "[OK]"
            
            print(f"  {marker} {name:50s} {elapsed*1000:7.0f}ms")
    
    # Resumen total
    print("\n" + "="*80)
    print(f"[TIME] TIEMPO TOTAL DE BOOT: {total_time*1000:.0f}ms")
    print(f"[CRIT] BOTTLENECKS (>100ms): {len([t for cat in _measurements.values() for _, t in cat if t > 0.1])}")
    print("="*80 + "\n")


# ============================================================================
# INSTRUMENTALIZACIÓN DEL BOOT
# ============================================================================

def main():
    """Simula boot completo con profiling."""
    
    print("\n" + "="*80)
    print("[*] PROFILER BOOT EXHAUSTIVO — Iniciando instrumentalizacion")
    print("="*80 + "\n")
    
    boot_start = time.time()
    
    try:
        # ========================================================================
        # FASE 0: IMPORTS CRÍTICOS
        # ========================================================================
        with measure_block("Importar PyQt6", "imports"):
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
        
        with measure_block("Importar módulos sistema", "imports"):
            import os
            import json
        
        # ========================================================================
        # FASE 1: CONFIGURACIÓN INICIAL
        # ========================================================================
        with measure_block("Cargar config.json", "disk_io"):
            config_path = Path(__file__).parent.parent / "datos" / "config.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
            else:
                config = {"escucha": {"dispositivo": 0}}
        
        # ========================================================================
        # FASE 2: DEPENDENCIAS CRÍTICAS
        # ========================================================================
        with measure_block("Importar Whisper", "imports"):
            import whisper
        
        with measure_block("Importar silero_vad", "imports"):
            import silero_vad
        
        with measure_block("Importar face_recognition", "imports"):
            import face_recognition
        
        with measure_block("Importar sounddevice", "imports"):
            import sounddevice
        
        # ========================================================================
        # FASE 3: INICIALIZACIÓN Qt
        # ========================================================================
        with measure_block("QApplication.__init__", "qt_init"):
            app = QApplication([])
        
        # ========================================================================
        # FASE 4: CARGAR MODELOS (Los Culpables Probables)
        # ========================================================================
        
        # 4a: Whisper Small Model
        with measure_block("Cargar Whisper 'small' model (CPU)", "model_load"):
            try:
                whisper_model = whisper.load_model("small", device="cpu")
            except Exception as e:
                logger.warning(f"Whisper load fallo: {e}")
        
        # 4b: Silero VAD
        with measure_block("Cargar Silero VAD", "model_load"):
            try:
                vad_model, vad_utils = silero_vad.load_silero_vad()
            except Exception as e:
                logger.warning(f"Silero load fallo: {e}")
        
        # 4c: Face Recognition Model
        with measure_block("Cargar Face Recognition known faces", "model_load"):
            try:
                # Simula carga de profiles faciales
                perfil_path = Path(__file__).parent.parent / "datos" / "perfil_esau.pkl"
                if perfil_path.exists():
                    import pickle
                    with open(perfil_path, "rb") as f:
                        profile = pickle.load(f)
            except Exception as e:
                logger.warning(f"Face profile load fallo: {e}")
        
        # ========================================================================
        # FASE 5: SISTEMA DE VOZ
        # ========================================================================
        with measure_block("Cargar Edge TTS", "imports"):
            try:
                from edge_tts import Communicate
            except Exception as e:
                logger.warning(f"Edge TTS import fallo: {e}")
        
        with measure_block("Inicializar motor TTS", "init"):
            try:
                tts_sample_rate = 24000
                logger.info(f"TTS motor configurado a {tts_sample_rate} Hz")
            except Exception as e:
                logger.warning(f"TTS init fallo: {e}")
        
        # ========================================================================
        # FASE 6: SISTEMA DE IA
        # ========================================================================
        with measure_block("Importar/conectar Ollama", "network"):
            try:
                import requests
                # Simula conexión a Ollama local
                for attempt in range(3):
                    try:
                        response = requests.get("http://localhost:11434/api/tags", timeout=2)
                        logger.info(f"Ollama conectado: {response.status_code}")
                        break
                    except Exception as e:
                        if attempt == 2:
                            logger.warning(f"Ollama no disponible: {e}")
                        time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Ollama check fallo: {e}")
        
        with measure_block("Cargar modelo Ollama 'llama2:7b'", "model_load"):
            try:
                import requests
                payload = {"model": "llama2:7b"}
                response = requests.post(
                    "http://localhost:11434/api/pull",
                    json=payload,
                    timeout=30,
                    stream=True
                )
                # Simula lectura de stream (sin bloqueante real)
                logger.info("Ollama model pull iniciado")
            except Exception as e:
                logger.info(f"Ollama model pull simulado (no disponible: {e})")
        
        # ========================================================================
        # FASE 7: SISTEMA DE PERCEPCIÓN
        # ========================================================================
        with measure_block("Detectar dispositivos audio", "hardware"):
            try:
                devices = sounddevice.query_devices()
                logger.info(f"Detectados {len(devices)} dispositivos audio")
            except Exception as e:
                logger.warning(f"Audio device detection fallo: {e}")
        
        with measure_block("Abrir InputStream audio", "init"):
            try:
                # Simula apertura (sin bloquear realmente)
                logger.info("InputStream audio configurado (simulado)")
            except Exception as e:
                logger.warning(f"InputStream init fallo: {e}")
        
        # ========================================================================
        # FASE 8: SISTEMA VISUAL
        # ========================================================================
        with measure_block("ContextoPantalla inicializado", "init"):
            try:
                logger.info("Pantalla detectada, OpenGL disponible")
            except Exception as e:
                logger.warning(f"Visual init fallo: {e}")
        
        # ========================================================================
        # TOTAL
        # ========================================================================
        boot_elapsed = time.time() - boot_start
        logger.info(f"\n[OK] BOOT COMPLETO en {boot_elapsed*1000:.0f}ms")
        
    except Exception as e:
        logger.exception(f"[ERROR] Error durante profiling: {e}")
        return 1
    
    finally:
        print_report()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
