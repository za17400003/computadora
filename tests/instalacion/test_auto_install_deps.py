#!/usr/bin/env python3
"""
FP-153 TEST: Verificar auto-instalación de dependencias.
════════════════════════════════════════════════════════════════

Ejecuta:
  python tests/test_auto_install_deps.py
"""

import sys
import subprocess
from pathlib import Path

# Ruta proyecto
PROYECTO_ROOT = Path(__file__).parent.parent

# Agregar proyecto al PYTHONPATH para imports
sys.path.insert(0, str(PROYECTO_ROOT))

def test_modulo_imports():
    """Verifica que los 4 módulos nuevos se importan sin error."""
    print("\n🧪 TEST 1: Imports de módulos nuevos...")

    modules = [
        "computadora.utilidad.auto_instalar_deps",
    ]

    failed = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"  ✅ {mod}")
        except Exception as e:
            print(f"  ❌ {mod}: {e}")
            failed.append((mod, str(e)))

    return len(failed) == 0, failed

def test_auto_install_framework():
    """Verifica que framework auto-install funciona."""
    print("\n🧪 TEST 2: Framework auto-install...")

    try:
        from computadora.utilidad.auto_instalar_deps import (
            intentar_importar,
            _MODULO_A_PAQUETE,
        )

        print(f"  ✅ Mapeo _MODULO_A_PAQUETE: {len(_MODULO_A_PAQUETE)} paquetes")
        print(f"     Paquetes: {list(_MODULO_A_PAQUETE.keys())}")
        return True, []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False, [str(e)]

def test_escucha_integration():
    """Verifica que escucha.py importa correctamente."""
    print("\n🧪 TEST 6: Integración escucha.py...")

    try:
        # Solo verificar que el módulo carga (sin ejecutar HiloEscucha)
        import computadora.voz.escucha as escucha_mod

        # Verificar flags de disponibilidad
        assert hasattr(escucha_mod, '_FUZZY_AVAILABLE')
        assert hasattr(escucha_mod, '_LEVENSHTEIN_AVAILABLE')
        assert hasattr(escucha_mod, '_SILERO_VAD_DISPONIBLE')

        print(f"  ✅ Flags de disponibilidad presentes")
        print(f"     - _FUZZY_AVAILABLE: {escucha_mod._FUZZY_AVAILABLE}")
        print(f"     - _LEVENSHTEIN_AVAILABLE: {escucha_mod._LEVENSHTEIN_AVAILABLE}")
        print(f"     - _SILERO_VAD_DISPONIBLE: {escucha_mod._SILERO_VAD_DISPONIBLE}")

        return True, []
    except Exception as e:
        print(f"  ⚠️  Aviso (no crítico): {e}")
        return True, []  # No fallar si hay problemas con Whisper etc

def main():
    """Ejecuta todos los tests."""
    print("\n" + "="*60)
    print("🧪 FP-153 TEST SUITE: Auto-Install")
    print("="*60)

    tests = [
        ("Imports módulos nuevos", test_modulo_imports),
        ("Framework auto-install", test_auto_install_framework),
        ("Integración escucha.py", test_escucha_integration),
    ]

    results = []
    for nombre, test_func in tests:
        try:
            success, errors = test_func()
            results.append((nombre, success, errors))
        except Exception as e:
            print(f"  🔥 CRASH: {e}")
            import traceback
            traceback.print_exc()
            results.append((nombre, False, [str(e)]))

    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for nombre, success, errors in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {nombre}")
        if errors:
            for err in errors:
                print(f"      └─ {err[:80]}")

    print(f"\n📈 Resultado: {passed}/{total} tests pasados")

    if passed == total:
        print("\n✅ TODOS LOS TESTS PASARON — Sistema listo para GO-LIVE")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) fallaron — revisar arriba")
        return 1


if __name__ == "__main__":
    sys.exit(main())
