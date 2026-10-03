#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

try:
    from computadora.metatron import MetatronOrquestador, EstadoSistema
    print("Import successful")

    # Test basic functionality
    metatron = MetatronOrquestador()
    print(f"Initial state: {metatron.estado_actual}")
    print("Basic test passed")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()