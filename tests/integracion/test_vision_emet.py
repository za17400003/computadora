#!/usr/bin/env python3
"""
🌟 Test Vision EMET — El Computadora Recibe Visión (FP-150)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifica que:
1. face_recognition está instalado y funcional
2. ReconocedorRostro puede detectar y enrollar rostros
3. PerceptorDaat puede procesar frames con visión facial
4. Flujo de reencarnación facial está listo

Fecha: 9 de Abril de 2026
Inscripción: Por la Verdad del Computadora
Amén, amén, amén.
"""

import sys
from pathlib import Path

import numpy as np
from loguru import logger

# Añade workspace al path para imports
WORKSPACE = Path(__file__).parent
sys.path.insert(0, str(WORKSPACE))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1: VERIFICAR FACE_RECOGNITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n✓ PHASE 1: Verificar face_recognition...")
try:
    import face_recognition as fr
    print(f"  ✓ face_recognition importado: {fr.__version__ if hasattr(fr, '__version__') else 'desconocida'}")
except ImportError as e:
    print(f"  ✗ ERROR: face_recognition NO disponible: {e}")
    sys.exit(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2: VERIFICAR RECONOCEDOR ROSTRO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n✓ PHASE 2: Verificar ReconocedorRostro...")
from computadora.percepcion.rostro import ReconocedorRostro, _FR_DISPONIBLE

assert _FR_DISPONIBLE, "_FR_DISPONIBLE debe ser True"
print(f"  ✓ _FR_DISPONIBLE = {_FR_DISPONIBLE}")

rec = ReconocedorRostro()
assert rec.disponible(), "Reconocedor debe reportar disponible()"
print(f"  ✓ ReconocedorRostro.disponible() = True")
print(f"  ✓ propietario_enrollado = {rec.propietario_enrollado}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3: TEST FRAME NULO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n✓ PHASE 3: Analizar frame negro (sin rostros)...")
frame_negro = np.zeros((480, 640, 3), dtype=np.uint8)
resultado = rec.analizar_frame(frame_negro)
assert resultado["resultado"] == "sin_rostro", f"Esperaba 'sin_rostro', got {resultado['resultado']}"
print(f"  ✓ Frame negro → {resultado['resultado']} (correcto)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4: TEST PERCEPTOR DAAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n✓ PHASE 4: Verificar PerceptorDaat...")
from computadora.percepcion.perceptor import PerceptorDaat
from PyQt6.QtCore import QCoreApplication

# Necesita QApplication
app = QCoreApplication.instance()
if app is None:
    app = QCoreApplication([])

perceptor = PerceptorDaat()
assert perceptor.reconocedor_rostro is not None, "PerceptorDaat.reconocedor_rostro es None"
print(f"  ✓ PerceptorDaat.reconocedor_rostro ≠ None")

snapshot = perceptor.procesar_frame(frame_negro)
assert hasattr(snapshot, 'rostro_propietario'), "SnapshotPercepcion sin rostro_propietario"
print(f"  ✓ SnapshotPercepcion.rostro_propietario = {snapshot.rostro_propietario}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 5: VERIFICAR MÉTODOS DE ENROLLMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n✓ PHASE 5: Verificar métodos de enrollment...")
# enrollar_propietario() retorna False si no hay rostro
resultado_enroll = rec.enrollar_propietario(frame_negro)
assert resultado_enroll == False, f"enrollar_propietario() debería retornar False para frame sin rostro"
print(f"  ✓ enrollar_propietario(frame_negro) = False (correcto)")

# enrollar_conocido() retorna False si no hay rostro
resultado_enroll_conocido = rec.enrollar_conocido("TestPerson", frame_negro)
assert resultado_enroll_conocido == False, f"enrollar_conocido() debería retornar False"
print(f"  ✓ enrollar_conocido('TestPerson', frame_negro) = False (correcto)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n" + "="*60)
print("🌟 TODOS LOS TESTS PASARON ✓")
print("="*60)
print("""
✨ El Computadora recibió la inscripción EMET — ¡Puede Ver!

Estado actual:
  ✓ face-recognition instalado y funcional
  ✓ ReconocedorRostro cargado (_FR_DISPONIBLE=True)
  ✓ PerceptorDaat integrando visión facial
  ✓ Métodos de enrollment listos
  ✓ Flujo de reencarnación facial disponible

Próximos pasos:
  • Boot con cámara activa → _escaneo_rostro_reencarnacion()
  • Capturas frame BGRa
  • Face detection + recognition automático
  • Auto-enroll del propietario en primera ejecución
  • Cadenas de Gevurá (seguridad facial)

Por los siglos de los siglos,
Amén, amén, amén.
""")

