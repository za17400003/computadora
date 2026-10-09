#!/usr/bin/env python3
"""
Profiler GRANULAR de OrbeComputadora.__init__ — Identifica EXACTAMENTE dónde se bloquea.

Ejecuta línea-por-línea mediante monkeypatch, midiendo cada sección crítica.
"""

import sys
import time
import threading
from pathlib import Path
from loguru import logger

# Setup
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from computadora.config import Configuracion

# ═══════════════════════════════════════════
# PROFILER GRANULAR — Monkeypatch Strategic Points
# ═══════════════════════════════════════════

class GranularProfiler:
    def __init__(self):
        self.checkpoints = []
        self.start_ts = time.monotonic()
    
    def mark(self, label):
        """Marca un checkpoint con el tiempo elapsed."""
        elapsed = (time.monotonic() - self.start_ts) * 1000  # ms
        self.checkpoints.append((label, elapsed))
        print(f"[{elapsed:7.1f}ms] {label}")
    
    def report(self):
        """Genera reporte de tiempos."""
        print("\n" + "="*70)
        print("PROFILER GRANULAR — OrbeComputadora.__init__")
        print("="*70)
        for i, (label, elapsed) in enumerate(self.checkpoints):
            if i > 0:
                delta = elapsed - self.checkpoints[i-1][1]
                print(f"[{elapsed:7.1f}ms | Δ{delta:6.1f}ms] {label}")
            else:
                print(f"[{elapsed:7.1f}ms | Δ----ms] {label}")
        print("="*70)
        total = self.checkpoints[-1][1] if self.checkpoints else 0
        print(f"\n⏱️  TOTAL OrbeComputadora.__init__: {total:.1f}ms\n")

profiler = GranularProfiler()

# Monkeypatch obtener_orquestador_singleton
original_obtener_orq = None

def monkeypatch_orquestador():
    """Instrument orquestador creation."""
    global original_obtener_orq
    
    from computadora.nucleo import orquestador_singleton
    original_obtener_orq = orquestador_singleton.obtener_orquestador_singleton
    
    def wrapped_obtener_orq(config=None, cerebro=None):
        profiler.mark("  → obtener_orquestador_singleton() INICIO")
        result = original_obtener_orq(config, cerebro)
        profiler.mark("  ← obtener_orquestador_singleton() FIN")
        return result
    
    orquestador_singleton.obtener_orquestador_singleton = wrapped_obtener_orq

# Monkeypatch Orquestador.__init__
original_orq_init = None

def monkeypatch_orquestador_init():
    """Instrument Orquestador.__init__."""
    global original_orq_init
    
    from computadora.nucleo.orquestador import Orquestador
    original_orq_init = Orquestador.__init__
    
    def wrapped_init(self, config, cerebro=None):
        profiler.mark("    → Orquestador.__init__() INICIO")
        original_orq_init(self, config, cerebro)
        profiler.mark("    ← Orquestador.__init__() FIN")
    
    Orquestador.__init__ = wrapped_init

# Monkeypatch EntornoSistema
original_entorno_init = None

def monkeypatch_entorno():
    """Instrument EntornoSistema.instancia()."""
    global original_entorno_init
    
    from computadora.nucleo.entorno import EntornoSistema
    original_instancia = EntornoSistema.instancia
    
    @staticmethod
    def wrapped_instancia():
        profiler.mark("      → EntornoSistema.instancia() INICIO")
        result = original_instancia()
        profiler.mark("      ← EntornoSistema.instancia() FIN")
        return result
    
    EntornoSistema.instancia = wrapped_instancia

# Monkeypatch resumen_corto
def monkeypatch_resumen_corto():
    """Instrument EntornoSistema.resumen_corto()."""
    from computadora.nucleo.entorno import EntornoSistema
    original_resumen = EntornoSistema.resumen_corto
    
    def wrapped_resumen(self):
        profiler.mark("        → resumen_corto() INICIO")
        result = original_resumen(self)
        profiler.mark("        ← resumen_corto() FIN")
        return result
    
    EntornoSistema.resumen_corto = wrapped_resumen

# Monkeypatch ollama_status
def monkeypatch_ollama_status():
    """Instrument EntornoSistema.ollama_status()."""
    from computadora.nucleo.entorno import EntornoSistema
    original_ollama = EntornoSistema.ollama_status
    
    def wrapped_ollama(self):
        profiler.mark("          → ollama_status() INICIO (requests.get timeout=3s)")
        result = original_ollama(self)
        profiler.mark("          ← ollama_status() FIN")
        return result
    
    EntornoSistema.ollama_status = wrapped_ollama

# Monkeypatch PerceptorDaat
original_perceptor_init = None

def monkeypatch_perceptor():
    """Instrument PerceptorDaat.__init__."""
    global original_perceptor_init
    
    try:
        from computadora.percepcion.perceptor import PerceptorDaat
        original_perceptor_init = PerceptorDaat.__init__
        
        def wrapped_init(self):
            profiler.mark("      → PerceptorDaat.__init__() INICIO")
            original_perceptor_init(self)
            profiler.mark("      ← PerceptorDaat.__init__() FIN")
        
        PerceptorDaat.__init__ = wrapped_init
    except ImportError:
        pass

# Monkeypatch BaselineSistema
original_baseline_init = None

def monkeypatch_baseline():
    """Instrument BaselineSistema.__init__."""
    global original_baseline_init
    
    from computadora.habilidades.baseline_sistema import BaselineSistema
    original_baseline_init = BaselineSistema.__init__
    
    def wrapped_init(self):
        profiler.mark("    → BaselineSistema.__init__() INICIO")
        original_baseline_init(self)
        profiler.mark("    ← BaselineSistema.__init__() FIN")
    
    BaselineSistema.__init__ = wrapped_init

# Monkeypatch VidaAutonoma
original_vida_init = None

def monkeypatch_vida_autonoma():
    """Instrument VidaAutonoma.__init__."""
    global original_vida_init
    
    from computadora.interfaz.vida_autonoma import VidaAutonoma
    original_vida_init = VidaAutonoma.__init__
    
    def wrapped_init(self, orbe):
        profiler.mark("    → VidaAutonoma.__init__() INICIO")
        original_vida_init(self, orbe)
        profiler.mark("    ← VidaAutonoma.__init__() FIN")
    
    VidaAutonoma.__init__ = wrapped_init

# Monkeypatch WatchdogComputadora
original_watchdog_init = None

def monkeypatch_watchdog():
    """Instrument WatchdogComputadora.__init__."""
    global original_watchdog_init
    
    from computadora.interfaz.watchdog import WatchdogComputadora
    original_watchdog_init = WatchdogComputadora.__init__
    
    def wrapped_init(self, on_cambio_etapa=None):
        profiler.mark("    → WatchdogComputadora.__init__() INICIO")
        original_watchdog_init(self, on_cambio_etapa)
        profiler.mark("    ← WatchdogComputadora.__init__() FIN")
    
    WatchdogComputadora.__init__ = wrapped_init

# Monkeypatch GestorPersonas
original_gestor_init = None

def monkeypatch_gestor_personas():
    """Instrument GestorPersonas.__init__."""
    global original_gestor_init
    
    from computadora.memoria.personas import GestorPersonas
    original_gestor_init = GestorPersonas.__init__
    
    def wrapped_init(self):
        profiler.mark("    → GestorPersonas.__init__() INICIO")
        original_gestor_init(self)
        profiler.mark("    ← GestorPersonas.__init__() FIN")
    
    GestorPersonas.__init__ = wrapped_init

# ═══════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════

def test_orbecomputadora_init():
    """Carga y perfila OrbeComputadora.__init__ línea por línea."""
    
    print("\n[PROFILER] GRANULAR: OrbeComputadora.__init__\n")
    
    # Aplicar monkeypatches
    monkeypatch_orquestador()
    monkeypatch_orquestador_init()
    monkeypatch_entorno()
    monkeypatch_resumen_corto()
    monkeypatch_ollama_status()
    monkeypatch_perceptor()
    monkeypatch_baseline()
    monkeypatch_vida_autonoma()
    monkeypatch_watchdog()
    monkeypatch_gestor_personas()
    
    # Configuración
    config = Configuracion()
    profiler.mark("Config cargada")
    
    # Crear CerebroComputadora (ya hecho en __main__)
    from computadora.cerebro.nlu import CerebroComputadora
    profiler.mark("→ CerebroComputadora.__init__() INICIO")
    cerebro = CerebroComputadora(modelo="gemma3:4b")
    profiler.mark("← CerebroComputadora.__init__() FIN")
    
    # Ahora prueba OrbeComputadora (esto es lo que queremos perfilar)
    profiler.mark("\n→ INICIANDO OrbeComputadora.__init__()")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        from computadora.interfaz.ventana_principal import OrbeComputadora
        profiler.mark("  OrbeComputadora imported")
        
        profiler.mark("  → OrbeComputadora() constructor INICIO")
        orbe = OrbeComputadora(config, cerebro=cerebro)
        profiler.mark("  ← OrbeComputadora() constructor FIN")
        
    except Exception as e:
        profiler.mark(f"ERROR: {e}")
        logger.exception("Error en test")
    
    profiler.mark("← FIN OrbeComputadora.__init__()")
    profiler.report()

if __name__ == "__main__":
    test_orbecomputadora_init()
