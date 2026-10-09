#!/usr/bin/env python3
"""
Profiler ULTRA-GRANULAR — mide EXACTAMENTE dónde se cuelga OrbeComputadora.__init__.
Enfoque: Medir super().__init__() vs el resto.
"""

import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# ═══════════════════════════════════════════
# ULTRA-GRANULAR TIMER
# ═══════════════════════════════════════════

class Timer:
    def __init__(self):
        self.start = time.monotonic()
    
    def elapsed(self):
        return (time.monotonic() - self.start) * 1000
    
    def mark(self, label):
        print(f"[{self.elapsed():7.1f}ms] {label}")

timer = Timer()

# ═══════════════════════════════════════════
# MONKEYPATCH OrbeComputadora.__init__ para medir cada línea
# ═══════════════════════════════════════════

def test_orbecomputadora_super_init():
    """Testa SOLO super().__init__() y líneas antes de obtener_orquestador_singleton."""
    
    from computadora.config import Configuracion
    from computadora.cerebro.nlu import CerebroComputadora
    from PyQt6.QtWidgets import QApplication, QWidget
    
    config = Configuracion()
    cerebro = CerebroComputadora(modelo="gemma3:4b")
    
    timer.mark("=== Iniciando prueba de super().__init__()")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    timer.mark("Importando OrbeComputadora...")
    from computadora.interfaz.ventana_principal import OrbeComputadora
    
    # Medir SOLO super().__init__() sin el resto
    timer.mark("Creando instancia de OrbeComputadora...")
    timer.mark("  → Ejecutando super().__init__() [QWidget init]...")
    
    # Hack: crear una subclase para medir solo super()
    class TestOrbe(QWidget):
        def __init__(self):
            timer.mark("    → [INICIO] QWidget.__init__()")
            super().__init__()
            timer.mark("    ← [FIN] QWidget.__init__()")
    
    try:
        test_orbe = TestOrbe()
        timer.mark("  ← QWidget super().__init__() completado")
    except Exception as e:
        timer.mark(f"  ✗ Error en super().__init__(): {e}")
    
    # Ahora mide el RESTO de OrbeComputadora.__init__
    timer.mark("\nAhora mediremos todo OrbeComputadora.__init__()...")
    timer.mark("  → [INICIO COMPLETO] OrbeComputadora.__init__()")
    
    try:
        orbe = OrbeComputadora(config, cerebro=cerebro)
        timer.mark("  ← [FIN COMPLETO] OrbeComputadora.__init__()")
    except Exception as e:
        timer.mark(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    timer.mark("\n=== Test completado")

if __name__ == "__main__":
    test_orbecomputadora_super_init()
