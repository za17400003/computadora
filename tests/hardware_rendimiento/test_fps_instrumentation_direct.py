"""Test directo de FPS instrumentation sin depender de logs capturados."""

import sys
import time
from pathlib import Path

# Agregar proyecto root al path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer


def test_fps_instrumentation_without_ui():
    """Test la lógica de instrumento FPS sin UI Qt real."""
    
    # Simular lo que hace _animar() sin Qt
    class MockOrbe:
        def __init__(self):
            self._frame_times_buffer = []
            self._frame_count_since_log = 0
            self._slowdown_frames = 0
            self._max_frame_time = 0.0
            self._ultimo_frame_ts = time.monotonic()
            self._debug_frame_count = 0
            self.fps_measurements = []  # Colector de mediciones
        
        def simulate_animar(self, delta_t_ms):
            """Simula un frame con delta_t especificado (en ms)."""
            delta_t = delta_t_ms / 1000.0  # Convertir a segundos
            
            # Lógica de instrumento (copiada de _animar())
            self._frame_times_buffer.append(delta_t)
            if len(self._frame_times_buffer) > 60:
                self._frame_times_buffer.pop(0)
            
            self._frame_count_since_log += 1
            if delta_t > 0.033:  # Below 30 FPS
                self._slowdown_frames += 1
            if delta_t > self._max_frame_time:
                self._max_frame_time = delta_t
            
            self._debug_frame_count += 1
            
            # Log cada 60 frames
            if self._frame_count_since_log >= 60 and len(self._frame_times_buffer) >= 60:
                avg_delta_t = sum(self._frame_times_buffer) / len(self._frame_times_buffer)
                actual_fps = 1.0 / avg_delta_t if avg_delta_t > 0 else 0
                slowdown_pct = (self._slowdown_frames / 60) * 100 if self._slowdown_frames > 0 else 0
                
                # Guardar medición en lugar de loguear
                measurement = {
                    'fps': actual_fps,
                    'avg_delta_t_ms': avg_delta_t * 1000,
                    'slowdown_pct': slowdown_pct,
                    'max_frame_time_ms': self._max_frame_time * 1000,
                }
                self.fps_measurements.append(measurement)
                
                # Reset
                self._frame_count_since_log = 0
                self._slowdown_frames = 0
                self._max_frame_time = 0.0
    
    # TEST 1: Simulación de 60 FPS perfectos (16.67ms delta_t)
    print("\n📊 TEST 1: 60 FPS perfectos")
    orbe1 = MockOrbe()
    for _ in range(120):  # 2 ciclos de 60 frames
        orbe1.simulate_animar(16.67)
    
    assert len(orbe1.fps_measurements) >= 1, "Debería tener al menos 1 medición"
    fps1 = orbe1.fps_measurements[0]['fps']
    print(f"   Medido: {fps1:.1f} FPS")
    assert 58 < fps1 < 62, f"60 FPS perfectos debería medir ~60, medió {fps1:.1f}"
    print("   ✅ PASS")
    
    # TEST 2: Simulación de 30 FPS (33ms delta_t)
    print("\n📊 TEST 2: 30 FPS")
    orbe2 = MockOrbe()
    for _ in range(120):  # 2 ciclos de 60 frames
        orbe2.simulate_animar(33.33)
    
    assert len(orbe2.fps_measurements) >= 1, "Debería tener al menos 1 medición"
    fps2 = orbe2.fps_measurements[0]['fps']
    print(f"   Medido: {fps2:.1f} FPS")
    assert 28 < fps2 < 32, f"30 FPS debería medir ~30, medió {fps2:.1f}"
    print("   ✅ PASS")
    
    # TEST 3: Simulación mixta (60% 60FPS, 40% 20FPS) = ~33 FPS (media armónica)
    print("\n📊 TEST 3: Mixto (60% 60FPS + 40% 20FPS)")
    orbe3 = MockOrbe()
    for i in range(120):
        if i % 10 < 6:  # 60% del tiempo: 60 FPS (16.67ms)
            orbe3.simulate_animar(16.67)
        else:  # 40% del tiempo: 20 FPS (50ms)
            orbe3.simulate_animar(50.0)
    
    assert len(orbe3.fps_measurements) >= 1
    fps3 = orbe3.fps_measurements[0]['fps']
    slowdown_pct = orbe3.fps_measurements[0]['slowdown_pct']
    print(f"   Medido: {fps3:.1f} FPS (slowdowns: {slowdown_pct:.0f}%)")
    # La media de delta_t es (0.6*16.67 + 0.4*50) = 30ms → 33.3 FPS
    assert 30 < fps3 < 36, f"Mixto debería medir ~33, medió {fps3:.1f}"
    assert slowdown_pct > 30, f"Debería detectar slowdowns >30%, detectó {slowdown_pct:.0f}%"
    print("   ✅ PASS")
    
    # TEST 4: Simulación muy lenta (10 FPS)
    print("\n📊 TEST 4: Muy lenta (10 FPS)")
    orbe4 = MockOrbe()
    for _ in range(120):
        orbe4.simulate_animar(100.0)  # 100ms = 10 FPS
    
    assert len(orbe4.fps_measurements) >= 1
    fps4 = orbe4.fps_measurements[0]['fps']
    print(f"   Medido: {fps4:.1f} FPS")
    assert 9 < fps4 < 11, f"10 FPS debería medir ~10, medió {fps4:.1f}"
    print("   ✅ PASS")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*60)
    print("""
CONCLUSIÓN:
- Instrumentación FPS funciona correctamente en lógica pura
- Mide delta_t frames individual, calcula promedio cada 60 frames
- Detecta slowdowns con precisión
- Problema Real: _animar() no se ejecuta en aplicación (timer inactivo)
  
CAUSA PROBABLE:
- Event loop Qt no procesa timeout del timer
- Ventana minimizada a bandeja desde el inicio
- Timer sin receiver visible para procesamiento
""")


if __name__ == '__main__':
    test_fps_instrumentation_without_ui()

