#!/usr/bin/env python3
"""
Diagnóstico de cámaras disponibles en el sistema.
"""

import cv2
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnosticar_camaras():
    """Verifica qué índices de cámara están disponibles."""
    print("🔍 DIAGNÓSTICO DE CÁMARAS DISPONIBLES")
    print("=" * 50)

    camaras_disponibles = []

    # Probar índices 0-4 (típicamente las primeras cámaras)
    for idx in range(5):
        try:
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                # Obtener propiedades de la cámara
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)

                camaras_disponibles.append({
                    'indice': idx,
                    'resolucion': f"{int(width)}x{int(height)}",
                    'fps': fps
                })

                print(f"✅ Cámara {idx}: {int(width)}x{int(height)} @ {fps} FPS")
                cap.release()
            else:
                print(f"❌ Cámara {idx}: No disponible")
                cap.release()
        except Exception as e:
            print(f"❌ Cámara {idx}: Error - {e}")

    print("=" * 50)
    print(f"Total cámaras disponibles: {len(camaras_disponibles)}")

    if len(camaras_disponibles) >= 2:
        print("✅ SOLUCIÓN: Usar índices diferentes para KliCamara y CamaraVigilancia")
        print("   - KliCamara: índice 0")
        print("   - CamaraVigilancia: índice 1")
    elif len(camaras_disponibles) == 1:
        print("⚠️  SOLUCIÓN: Solo una cámara disponible")
        print("   - Ambos sistemas deben compartir la misma VideoCapture")
        print("   - O deshabilitar uno de los sistemas")
    else:
        print("❌ PROBLEMA: No hay cámaras disponibles")
        print("   - Verificar que la cámara esté conectada y el driver instalado")

    return camaras_disponibles

def verificar_conflictos():
    """Verifica posibles conflictos entre sistemas de cámara."""
    print("\n🔍 VERIFICACIÓN DE CONFLICTOS")
    print("=" * 50)

    try:
        # Verificar que ambos módulos se pueden importar
        from computadora.habilidades.vision import KliCamara
        from computadora.habilidades.camara import CamaraVigilancia

        print("✅ Ambos módulos de cámara se pueden importar")

        # Verificar configuraciones por defecto
        kli_cam = KliCamara()
        vig_cam = CamaraVigilancia()

        print(f"KliCamara índice por defecto: {kli_cam._indice}")
        print(f"CamaraVigilancia dispositivo por defecto: {vig_cam.dispositivo_id}")

        if kli_cam._indice == vig_cam.dispositivo_id:
            print("⚠️  CONFLICTO: Ambos sistemas usan el mismo índice de dispositivo (0)")
            print("   Esto causa que se roben la cámara entre sí")
        else:
            print("✅ No hay conflicto de índices")

    except Exception as e:
        print(f"❌ Error verificando conflictos: {e}")

if __name__ == "__main__":
    camaras = diagnosticar_camaras()
    verificar_conflictos()

    print("\n💡 RECOMENDACIONES:")
    print("=" * 50)
    if len(camaras) >= 2:
        print("1. Modificar CamaraVigilancia para usar dispositivo_id=1")
        print("2. Mantener KliCamara en dispositivo 0")
    elif len(camaras) == 1:
        print("1. Implementar sharing de VideoCapture entre sistemas")
        print("2. O deshabilitar CamaraVigilancia si no es esencial")
    else:
        print("1. Verificar conexión física de la cámara")
        print("2. Reinstalar drivers de cámara")
        print("3. Probar con otra aplicación de cámara")