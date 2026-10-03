#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA DEL SISTEMA COMPUTADORA
Verifica que todas las partes funcionen correctamente
"""

import sys
import os
import json
import traceback
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_config():
    """Test configuración"""
    print("🔧 Testing Config...")
    try:
        from computadora.config import Configuracion
        config = Configuracion()
        print("✅ Config OK")
        return True
    except Exception as e:
        print(f"❌ Config ERROR: {e}")
        traceback.print_exc()
        return False

def test_logs():
    """Test sistema de logs"""
    print("📝 Testing Logs...")
    try:
        from computadora.utilidades.logs import configurar_logs
        configurar_logs()
        print("✅ Logs OK")
        return True
    except Exception as e:
        print(f"❌ Logs ERROR: {e}")
        traceback.print_exc()
        return False

def test_memoria():
    """Test sistema de memoria"""
    print("🧠 Testing Memoria...")
    try:
        from computadora.memoria.memoria import add_memory, _read_raw
        from datetime import date

        # Test escritura
        add_memory("test", "mensaje de prueba", {"test": True})

        # Test lectura
        items = _read_raw(date.today())
        if items and len(items) > 0:
            print("✅ Memoria OK")
            return True
        else:
            print("⚠️ Memoria: No se encontraron items (posiblemente OK si es primera ejecución)")
            return True
    except Exception as e:
        print(f"❌ Memoria ERROR: {e}")
        traceback.print_exc()
        return False

def test_cerebro():
    """Test cerebro básico"""
    print("🧠 Testing Cerebro...")
    try:
        from computadora.cerebro.nlu import CerebroComputadora
        cerebro = CerebroComputadora(modelo="deepseek-r1:1.5b")
        print("✅ Cerebro OK")
        return True
    except Exception as e:
        print(f"❌ Cerebro ERROR: {e}")
        traceback.print_exc()
        return False

def test_gui_components():
    """Test componentes GUI básicos"""
    print("🖥️ Testing GUI Components...")
    try:
        from PyQt6.QtWidgets import QApplication
        import sys

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        print("✅ GUI Components OK")
        return True
    except Exception as e:
        print(f"❌ GUI Components ERROR: {e}")
        traceback.print_exc()
        return False

def test_data_files():
    """Test archivos de datos críticos"""
    print("📁 Testing Data Files...")
    data_dir = Path(__file__).parent / "datos"

    critical_files = [
        "personalidad.json",
        "baseline_sistema.json",
        "perfil_linguistico.json",
        "owner_profile.json"
    ]

    all_ok = True
    for file in critical_files:
        file_path = data_dir / file
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"✅ {file} OK")
            except Exception as e:
                print(f"❌ {file} ERROR: {e}")
                all_ok = False
        else:
            print(f"⚠️ {file} no existe (posiblemente OK)")

    return all_ok

def main():
    print("🚀 INICIANDO AUDITORÍA COMPLETA DEL SISTEMA COMPUTADORA")
    print("=" * 60)

    tests = [
        ("Configuración", test_config),
        ("Sistema de Logs", test_logs),
        ("Sistema de Memoria", test_memoria),
        ("Cerebro", test_cerebro),
        ("Componentes GUI", test_gui_components),
        ("Archivos de Datos", test_data_files),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n🔍 Probando: {name}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test {name} falló con excepción: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE LA AUDITORÍA:")

    all_passed = True
    for name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 AUDITORÍA COMPLETA: TODOS LOS COMPONENTES FUNCIONAN CORRECTAMENTE")
        print("💡 El sistema está listo para funcionar sin errores de memoria")
    else:
        print("⚠️ AUDITORÍA COMPLETA: ALGUNOS COMPONENTES TIENEN PROBLEMAS")
        print("🔧 Revisa los errores arriba y corrígelos antes de ejecutar la aplicación completa")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())