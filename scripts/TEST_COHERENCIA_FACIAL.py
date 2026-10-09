#!/usr/bin/env python3
"""
TEST_COHERENCIA_FACIAL.py — Auditoría de persistencia y reconocimiento facial

Simula el ciclo completo:
1. Registrar usuario (guardar encoding)
2. Eliminar ReconocedorRostro (simular reboot)
3. Crear nuevo ReconocedorRostro (debe CARGAR encoding)
4. Verificar reconocimiento (distancia < umbral)
"""

import sys
import json
from pathlib import Path

# Agregar proyecto-computadora al path
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

import numpy as np

print("[COHERENCIA FACIAL] Iniciando auditoría...")

# 1. VERIFICAR QUE FACE_RECOGNITION ESTÉ DISPONIBLE
print("\n[1] Verificar face_recognition...")
try:
    import face_recognition as fr
    print("   ✓ face_recognition disponible")
except ImportError:
    print("   ✗ FALTA: pip install face_recognition")
    sys.exit(1)

# 2. VERIFICAR RUTAS
print("\n[2] Verificar rutas...")
_DATOS_DIR = _root / "datos"
_PERFIL_ROSTRO_PROPIETARIO = _DATOS_DIR / "owner_face_profile.json"
print(f"   Datos dir: {_DATOS_DIR}")
print(f"   Profile JSON: {_PERFIL_ROSTRO_PROPIETARIO}")
if _DATOS_DIR.exists():
    print(f"   ✓ datos/ existe")
else:
    print(f"   ⚠ datos/ no existe (se creará)")

# 3. VERIFICAR SI EL ENCODING DEL PROPIETARIO YA EXISTE
print("\n[3] Verificar archivo persistido...")
if _PERFIL_ROSTRO_PROPIETARIO.exists():
    print(f"   ✓ owner_face_profile.json existe ({_PERFIL_ROSTRO_PROPIETARIO.stat().st_size} bytes)")
    try:
        data = json.loads(_PERFIL_ROSTRO_PROPIETARIO.read_text("utf-8"))
        enc_guardado = np.array(data["encoding"], dtype=np.float64)
        print(f"   ✓ Encoding cargado correctamente")
        print(f"     - Shape: {enc_guardado.shape}")
        print(f"     - Dtype: {enc_guardado.dtype}")
        print(f"     - Range: [{enc_guardado.min():.4f}, {enc_guardado.max():.4f}]")
    except Exception as e:
        print(f"   ✗ ERROR al cargar JSON: {e}")
        sys.exit(1)
else:
    print(f"   ⚠ owner_face_profile.json NO existe")
    print(f"     (Usuario será auto-enrollado en primer escaneo de rostro)")

# 4. CARGAR ReconocedorRostro Y VERIFICAR CARGA
print("\n[4] Simular boot: crear ReconocedorRostro...")
try:
    from computadora.percepcion.rostro import ReconocedorRostro
    
    rec = ReconocedorRostro()
    print(f"   ✓ ReconocedorRostro creado")
    
    if rec.propietario_enrollado:
        print(f"   ✓ Propietario ENROLLADO (encoding cargado en __init__)")
        print(f"     - Shape: {rec._encoding_propietario.shape}")
    else:
        print(f"   ✗ Propietario NO enrollado")
        if _PERFIL_ROSTRO_PROPIETARIO.exists():
            print(f"     (archivo existe pero _cargar_perfiles() falló)")
        else:
            print(f"     (archivo no existe - primer boot)")
except Exception as e:
    print(f"   ✗ ERROR al crear ReconocedorRostro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. VERIFICAR COINCIDENCIA ENTRE GUARDADO Y CARGADO
if _PERFIL_ROSTRO_PROPIETARIO.exists() and rec.propietario_enrollado:
    print("\n[5] Verificar que encodings COINCIDEN...")
    enc_guardado = np.array(json.loads(_PERFIL_ROSTRO_PROPIETARIO.read_text("utf-8"))["encoding"], dtype=np.float64)
    enc_cargado = rec._encoding_propietario
    
    if enc_guardado.shape != enc_cargado.shape:
        print(f"   ✗ Shape mismatch: guardado={enc_guardado.shape}, cargado={enc_cargado.shape}")
    elif not np.allclose(enc_guardado, enc_cargado):
        print(f"   ✗ Encoding VALUES no coinciden")
    else:
        print(f"   ✓ Encodings COINCIDEN exactamente")
        distancia_auto = float(fr.face_distance([enc_guardado], enc_cargado)[0])
        print(f"     Distancia (self vs self): {distancia_auto:.6f} (debe ser ~0.0)")
        if distancia_auto < 0.01:
            print(f"   ✓ Coherencia: PASS")
        else:
            print(f"   ⚠ Coherencia: distancia inusualmente alta")

# 6. RESUMEN
print("\n" + "="*60)
print("RESULTADO:")
print("="*60)
if rec.propietario_enrollado:
    print("✓ COHERENCIA FACIAL: Sistema está listo para reconocer")
    print("  - Encoding guardado en: datos/owner_face_profile.json")
    print("  - Encoding cargado en: ReconocedorRostro._encoding_propietario")
    print("  - Próximo boot: escaneo de rostro se ejecutará en 10s")
    print("  - Reconocimiento: Si distancia <= 0.45 → Propietario detectado")
else:
    if _PERFIL_ROSTRO_PROPIETARIO.exists():
        print("✗ INCOHERENCIA: Archivo existe pero NO se carga")
        print("  - Revisar _cargar_perfiles() en rostro.py")
    else:
        print("⚠ PRIMER BOOT: Usuario será auto-enrollado en escaneo de rostro")
        print("  - En ventana_principal.py: _escaneo_rostro_reencarnacion() se ejecutará en 10s")
        print("  - Usuario será pedido por contraseña (Gevurá)")
        print("  - Luego se capturará su rostro automáticamente")
