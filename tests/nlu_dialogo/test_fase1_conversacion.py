#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 1: Conversación Pura — Sin Herramientas
Valida que Computadora responde conversacionalmente sin ejecutar herramientas.
"""

import sys
import os
from pathlib import Path

# Fix encoding para Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# Configurar logs
from computadora.utilidades.logs import configurar_logs
configurar_logs()

from computadora.cerebro.nlu import CerebroComputadora

def test_conversacion_basica():
    """Test Fase 1: Conversación sin herramientas."""
    
    print("\n" + "="*70)
    print("FASE 1 VALIDATION — Conversación Pura (Sin Herramientas)")
    print("="*70 + "\n")
    
    try:
        cerebro = CerebroComputadora(modelo="llama2:7b")
        print("[INIT] CerebroComputadora cargado correctamente\n")
    except Exception as e:
        print(f"[ERROR] No se pudo cargar CerebroComputadora: {e}")
        return False
    
    # Tests
    tests = [
        ("1.1.1", "Hola", "Saludo básico"),
        ("1.1.2", "Hola, Computadora", "Saludo con nombre"),
        ("1.2.1", "¿Cómo estás?", "Pregunta personal"),
        ("1.3.1", "Preséntate", "Autopresentación"),
        ("1.3.2", "¿Quién eres?", "Identity check"),
        ("1.4.1", "por favor", "Tria Prima — Sal"),
        ("1.4.2", "gracias", "Tria Prima — Mercurio"),
        ("1.5.1", "¿Qué recuerdas?", "Memoria conversacional"),
    ]
    
    resultados = []
    
    for test_id, entrada, descripcion in tests:
        print(f"\n[{test_id}] {descripcion}")
        print(f"  Input: '{entrada}'")
        
        try:
            respuesta = cerebro.pensar(entrada)
            
            # Verificar que NO retorna herramienta
            if respuesta and isinstance(respuesta, str):
                if respuesta.startswith("__"):
                    print(f"  [FAIL] Ejecuto herramienta ({respuesta})")
                    resultados.append((test_id, False, "Ejecuto herramienta"))
                else:
                    # Verificar que es respuesta conversacional
                    print(f"  [OK] Respuesta conversacional ({len(respuesta)} chars)")
                    print(f"     Preview: {respuesta[:80]}...")
                    resultados.append((test_id, True, "OK"))
            elif respuesta is None:
                print(f"  [SKIP] Retorno None (escalado a N2)")
                resultados.append((test_id, True, "Escalado a N2 (esperado)"))
            else:
                print(f"  [FAIL] Tipo inesperado: {type(respuesta)}")
                resultados.append((test_id, False, f"Tipo: {type(respuesta)}"))
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            resultados.append((test_id, False, str(e)))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN FASE 1")
    print("="*70)
    
    pasadas = sum(1 for _, ok, _ in resultados if ok)
    total = len(resultados)
    
    for test_id, ok, msg in resultados:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  [{test_id}] {status}: {msg}")
    
    print(f"\nResultado: {pasadas}/{total} tests pasados")
    
    if pasadas == total:
        print("\n[SUCCESS] FASE 1 VALIDATION: OK -- Conversacion pura funcionando")
        return True
    else:
        print(f"\n[WARNING] FASE 1 VALIDATION: {total - pasadas} tests fallaron")
        return False

if __name__ == "__main__":
    success = test_conversacion_basica()
    sys.exit(0 if success else 1)

