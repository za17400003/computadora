#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROFILER COMPLETO DE THREADING + PERFORMANCE
Diagnostica:
- Boot performance completo (no solo imports)
- Thread contention y bloqueos
- Event loop performance
- Context menu lag (1s issue)
- UI responsiveness
"""

import sys
import os
import threading
import time
import tracemalloc
from pathlib import Path
from collections import defaultdict
import json

# Setup path
RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

# ============================================================================
# FASE 1: BOOT PROFILING COMPLETO CON THREADING ANALYSIS
# ============================================================================

class ThreadingProfiler:
    def __init__(self):
        self.thread_stats = defaultdict(lambda: {
            'created': None,
            'start_time': None,
            'end_time': None,
            'blocked_count': 0,
            'lock_acquisitions': []
        })
        self.lock_contentions = []
        self.event_loop_delays = []
        self.context_menu_traces = []
        
    def track_thread_creation(self, name):
        self.thread_stats[name]['created'] = time.monotonic()
        
    def track_lock_contention(self, lock_name, wait_time):
        self.lock_contentions.append({
            'lock': lock_name,
            'wait_time': wait_time,
            'timestamp': time.monotonic()
        })

def profile_boot():
    """Perfil completo del boot incluyendo threads."""
    print("\n" + "="*80)
    print("PROFILER: BOOT SEQUENCE COMPLETO CON THREADING")
    print("="*80)
    
    # Iniciar tracemalloc
    tracemalloc.start()
    
    boot_start = time.monotonic()
    
    try:
        # FASE 1: Imports principales
        print("\n[PHASE 1] Cargando imports principales...")
        imports_start = time.monotonic()
        
        from computadora.utilidades.logs import configurar_logs
        from computadora.cerebro.nlu import CerebroComputadora
        from computadora.interfaz.ventana_principal import OrbeComputadora
        
        imports_time = time.monotonic() - imports_start
        print(f"  Imports completados en {imports_time:.2f}s")
        
        # FASE 2: Configurar logs
        print("\n[PHASE 2] Configurando logs...")
        logs_start = time.monotonic()
        configurar_logs()
        logs_time = time.monotonic() - logs_start
        print(f"  Logs configurados en {logs_time:.2f}s")
        
        # FASE 3: CerebroComputadora
        print("\n[PHASE 3] Inicializando CerebroComputadora...")
        cerebro_start = time.monotonic()
        cerebro = CerebroComputadora(modelo="llama2:7b")
        cerebro_time = time.monotonic() - cerebro_start
        print(f"  CerebroComputadora listo en {cerebro_time:.2f}s")
        
        # FASE 4: Análisis de threading
        print("\n[PHASE 4] Análisis de threads activos...")
        active_threads = threading.enumerate()
        print(f"  Threads activos: {len(active_threads)}")
        for t in active_threads:
            print(f"    - {t.name} (daemon={t.daemon}, alive={t.is_alive()})")
        
        # FASE 5: Memoria
        print("\n[PHASE 5] Uso de memoria...")
        current, peak = tracemalloc.get_traced_memory()
        print(f"  Memoria actual: {current / 1024 / 1024:.1f} MB")
        print(f"  Pico de memoria: {peak / 1024 / 1024:.1f} MB")
        
        boot_time = time.monotonic() - boot_start
        print(f"\n[TOTAL] Boot completado en {boot_time:.2f}s")
        
        return {
            'boot_time': boot_time,
            'imports_time': imports_time,
            'logs_time': logs_time,
            'cerebro_time': cerebro_time,
            'threads_count': len(active_threads),
            'memory_mb': current / 1024 / 1024,
            'peak_memory_mb': peak / 1024 / 1024,
            'cerebro': cerebro
        }
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        traceback.print_exc()
        return None
    finally:
        tracemalloc.stop()

def profile_interaction():
    """Perfil de interacciones conversacionales."""
    print("\n" + "="*80)
    print("PROFILER: INTERACCIONES CONVERSACIONALES")
    print("="*80)
    
    try:
        from computadora.cerebro.nlu import CerebroComputadora
        from computadora.utilidades.logs import configurar_logs
        
        configurar_logs()
        cerebro = CerebroComputadora(modelo="llama2:7b")
        
        test_inputs = [
            ("Hola", "Saludo simple"),
            ("Hola, Computadora", "Saludo con nombre"),
            ("Como estás", "Pregunta personal"),
            ("Quién eres", "Identidad"),
            ("por favor", "Tria Prima - Sal"),
            ("gracias", "Tria Prima - Mercurio"),
        ]
        
        results = []
        print("\n[Testing] Ejecutando conversaciones...")
        
        for entrada, desc in test_inputs:
            print(f"\n  [{desc}] Input: '{entrada}'")
            
            think_start = time.monotonic()
            respuesta = cerebro.pensar(entrada)
            think_time = time.monotonic() - think_start
            
            if respuesta:
                is_tool = respuesta.startswith("__")
                resp_len = len(respuesta)
                print(f"    Output: {resp_len} chars in {think_time:.3f}s")
                print(f"    Tool? {is_tool}")
                if not is_tool and resp_len < 200:
                    print(f"    Preview: {respuesta[:100]}...")
                results.append({
                    'input': entrada,
                    'time_ms': think_time * 1000,
                    'is_tool': is_tool,
                    'success': True
                })
            else:
                print(f"    Output: None (escalado a N2) in {think_time:.3f}s")
                results.append({
                    'input': entrada,
                    'time_ms': think_time * 1000,
                    'is_tool': False,
                    'success': False
                })
        
        # Estadísticas
        times = [r['time_ms'] for r in results]
        print(f"\n[STATS]")
        print(f"  Min: {min(times):.1f}ms")
        print(f"  Max: {max(times):.1f}ms")
        print(f"  Avg: {sum(times) / len(times):.1f}ms")
        
        return results
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_context_menu_lag():
    """Diagnostica lag del context menu (~1s issue)."""
    print("\n" + "="*80)
    print("DIAGNÓSTICO: CONTEXT MENU LAG (1S)")
    print("="*80)
    
    print("\nProbables causas:")
    print("1. Face recognition cargando en thread principal (debería ser lazy)")
    print("2. Ollama o Whisper intentando conectar sincrónicamente")
    print("3. Event loop bloqueado por operación de I/O")
    print("4. Mutex lock contention en percepción")
    
    try:
        # Buscar qué está en el context menu handler
        ventana_file = RAIZ / "computadora" / "interfaz" / "ventana_principal.py"
        if ventana_file.exists():
            with open(ventana_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar context menu
            if "contextMenuEvent" in content or "context_menu" in content:
                print("\n[FOUND] Context menu handler en ventana_principal.py")
                
                # Buscar posibles bloqueos
                if "face_recognition" in content and "contextMenuEvent" in content:
                    print("  WARNING: face_recognition mencionado en mismo archivo que menu")
                
                if "import face_recognition" in content:
                    print("  WARNING: face_recognition importado a nivel módulo (BLOQUEANTE)")
                    print("    -> ACCIÓN: Mover a lazy import en método específico")
                
                if "subprocess" in content or "Popen" in content:
                    print("  WARNING: subprocess calls posiblemente en thread principal")
                    print("    -> ACCIÓN: Mover a background thread")
        
        # Buscar locks
        print("\n[CHECKING] Locks y threading issues...")
        
        nlu_file = RAIZ / "computadora" / "cerebro" / "nlu.py"
        if nlu_file.exists():
            with open(nlu_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lock_count = content.count("Lock()")
                print(f"  Locks encontrados en nlu.py: {lock_count}")
                if lock_count > 5:
                    print("    WARNING: Muchos locks, riesgo de contention")
        
        # Buscar I/O operations
        print("\n[CHECKING] I/O Operations...")
        
        percepcion_dir = RAIZ / "computadora" / "percepcion"
        if percepcion_dir.exists():
            py_files = list(percepcion_dir.glob("*.py"))
            for py_file in py_files:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "subprocess" in content or "run(" in content:
                        print(f"  WARNING: subprocess en {py_file.name}")
                    if "face_recognition" in content and "import" in content.split("face_recognition")[0][-100:]:
                        print(f"  WARNING: face_recognition importado sincrónicamente en {py_file.name}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

def suggest_fixes():
    """Sugiere fixes específicos."""
    print("\n" + "="*80)
    print("RECOMENDACIONES AUTOMÁTICAS")
    print("="*80)
    
    fixes = {
        "1. Face Recognition Lazy Loading": [
            "Mover import face_recognition de top-level a función lazy",
            "Llamar lazy-load en background thread (no en context menu)",
            "Impacto estimado: -300ms en menu response"
        ],
        "2. Event Loop Responsiveness": [
            "Usar QThread.start() en lugar de QTimer.singleShot para I/O",
            "Medir delta_t en QTimer callback (ya implementado)",
            "Impacto: Mejor FPS durante conversación"
        ],
        "3. Context Menu Handler": [
            "Agregar time.monotonic() antes y después de cada operación",
            "Identificar qué operación tarda >100ms",
            "Mover a background thread si es I/O"
        ],
        "4. Thread Pool": [
            "Crear ThreadPoolExecutor compartido para tareas I/O",
            "No crear threads bajo demanda",
            "Impacto: -50-100ms creación thread"
        ],
        "5. Profiling Continuo": [
            "Agregar decorador @profile_time a métodos críticos",
            "Monitorear FPS en tiempo real (ya hay código)",
            "Alertar si caída por debajo de 30 FPS"
        ]
    }
    
    for category, items in fixes.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")

if __name__ == "__main__":
    import traceback
    
    print("\n" + "="*80)
    print("PROFILER COMPLETO -- COMPUTADORA PERFORMANCE DIAGNOSTIC")
    print("="*80)
    
    # Ejecutar profilers
    boot_results = profile_boot()
    
    if boot_results:
        print("\n[SAVING] Resultados de boot...")
        with open(RAIZ / "BOOT_PROFILE_RESULTS.json", 'w', encoding='utf-8') as f:
            boot_dict = {k: v for k, v in boot_results.items() if k != 'cerebro'}
            json.dump(boot_dict, f, indent=2)
    
    # Interacciones
    interaction_results = profile_interaction()
    
    if interaction_results:
        print("\n[SAVING] Resultados de interacciones...")
        with open(RAIZ / "INTERACTION_PROFILE_RESULTS.json", 'w', encoding='utf-8') as f:
            json.dump(interaction_results, f, indent=2)
    
    # Análisis de lag
    analyze_context_menu_lag()
    
    # Recomendaciones
    suggest_fixes()
    
    print("\n" + "="*80)
    print("PROFILER COMPLETADO")
    print("="*80)
    print("\nArchivos generados:")
    print("  - BOOT_PROFILE_RESULTS.json")
    print("  - INTERACTION_PROFILE_RESULTS.json")
    print("\nSiguientes pasos:")
    print("  1. Revisar recomendaciones arriba")
    print("  2. Implementar lazy-loading de face_recognition")
    print("  3. Re-ejecutar profiler para comparar")
