#!/usr/bin/env python
"""
Wrapper para ejecutar COMPUTADORA con mejor manejo de errores.
Intenta ejecutar python -m computadora y captura cualquier error de forma legible.
FP-139 RUBEDO FASE 5: Verificación de permisos administrador.

NOTA: La elevación de admin se maneja en computadora_boot.bat (más confiable).
Este script SOLO detecta estado de permisos para información, no intenta relanzarse.
"""

import sys
import traceback
import subprocess
from pathlib import Path


def es_admin():
    """Verifica si el script se ejecuta como administrador (Windows)."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    # FP-139 RUBEDO FASE 5: Información de permisos (solo lectura, no relanza)
    admin_status = es_admin()
    
    print("="*60)
    print("COMPUTADORA — Wrapper de ejecución")
    print("="*60)
    print(f"Permisos: {'✓ ADMINISTRADOR' if admin_status else 'Normal (sin admin)'}")
    print()
    
    try:
        # Ejecutar módulo dentro de este mismo proceso para mejor traceback
        print("[1] Importando módulo computadora...")
        import computadora
        print("    ✓ Importado exitosamente")
        
        print("\n[2] Llamando main()...")
        from computadora.__main__ import main as computadora_main
        computadora_main()
        
    except Exception as e:
        print("\n" + "="*60)
        print("ERROR EN COMPUTADORA")
        print("="*60)
        print(f"\nTipo: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("\nTraceback completo:")
        print("-"*60)
        traceback.print_exc()
        print("-"*60)
        print("\nGuarda este error en un archivo para reportar si es necesario.")
        
        # Guardar en archivo también
        error_file = Path(".logs") / "python_error.txt"
        Path(".logs").mkdir(exist_ok=True)
        with open(error_file, "w", encoding="utf-8") as f:
            f.write("ERROR EN COMPUTADORA\n")
            f.write("="*60 + "\n")
            f.write(f"Tipo: {type(e).__name__}\n")
            f.write(f"Mensaje: {str(e)}\n\n")
            f.write("Traceback:\n")
            f.write("-"*60 + "\n")
            traceback.print_exc(file=f)
            f.write("-"*60 + "\n")
        
        print(f"\nError guardado en: {error_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()
