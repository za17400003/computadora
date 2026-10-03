#!/usr/bin/env python3
"""
Diagnóstico exhaustivo de problemas de animación en COMPUTADORA demo
- Animaciones solo cuando mouse sobre ventana
- Anillos giran al unísono
- Animaciones discretas en lugar de fluidas
- Colores sólidos en lugar de basados en recursos
"""

import json
from pathlib import Path
import re

print("=" * 80)
print("DIAGNOSTICO: PROBLEMAS DE ANIMACION EN DEMO COMPUTADORA")
print("=" * 80)

# 1. Buscar dónde se controla la animación
print("\n[1] BUSQUEDA: Control de Animación")
vp_path = Path("computadora/interfaz/ventana_principal.py")

if vp_path.exists():
    with open(vp_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar patrones que podrían frenar animación
    problemas = []
    
    # PROBLEMA 1: Animación solo con mouse over
    if "enterEvent" in content or "leaveEvent" in content:
        print("⚠️  ENCONTRADO: enterEvent/leaveEvent (posible control de animación por mouse)")
        if "stop()" in content or "_timer.stop()" in content:
            problemas.append("TIMER DETENIDO en leaveEvent (animación se frena cuando mouse sale)")
    
    # PROBLEMA 2: Rotaciones al unísono
    print("\n[2] ROTACIONES: Velocidades de anillos")
    rot_patterns = [
        ("_rot_anillo1", r"_rot_anillo1\s*[+\-]=\s*([\d.]+)"),
        ("_rot_anillo2", r"_rot_anillo2\s*[+\-]=\s*([\d.]+)"),
        ("_rot_letras", r"_rot_letras\s*[+\-]=\s*([\d.]+)"),
    ]
    
    velocidades = {}
    for nombre, pattern in rot_patterns:
        matches = re.findall(pattern, content)
        if matches:
            velocidades[nombre] = matches
            print(f"   {nombre}: {matches} rad/s")
    
    # Verificar si usan delta_t para frame-rate independence
    if "delta_t" in content:
        print("   ✅ Usa delta_t para suavidad independiente de frame rate")
    else:
        print("   ❌ NO usa delta_t — animaciones podrían ser discretas")
    
    # PROBLEMA 3: Colores fijos en lugar de basados en recursos
    print("\n[3] COLORES: Basados en recursos")
    if "_calcular_color_ohr" in content or "_DMUT_VISUAL" in content:
        print("   ✅ Sistema de colores dinámico detectado")
        if "cpu_pct" in content or "ram_pct" in content:
            print("   ✅ Valores CPU/RAM/GPU disponibles")
        else:
            print("   ⚠️  Colores detectados pero no se basan en CPU/RAM/GPU")
    else:
        print("   ❌ Sistema de colores fijo — no responde a recursos")
    
    # PROBLEMA 4: Validación de discreteness
    print("\n[4] SUAVIDAD: Factor de suavizado")
    if "_delta_t_smooth" in content:
        smooth_factor = re.search(r"_delta_smooth_factor\s*=\s*([\d.]+)", content)
        if smooth_factor:
            factor = float(smooth_factor.group(1))
            print(f"   ✅ EMA factor: {factor} (suavizado)")
            if factor >= 0.9:
                print(f"      → Factor {factor} es MÁXIMO (muy suave)")
            elif factor >= 0.5:
                print(f"      → Factor {factor} es ADECUADO")
            else:
                print(f"      → Factor {factor} es BAJO (discreto)")
    else:
        print("   ❌ NO usa suavizado EMA — animaciones serán discretas")
    
    problemas_encontrados = [
        ("enterEvent/leaveEvent", "enterEvent" in content or "leaveEvent" in content),
        ("Timer control por mouse", "_timer.stop()" in content),
        ("sin delta_t", "delta_t" not in content),
        ("sin colores dinámicos", "_calcular_color_ohr" not in content),
        ("sin EMA suavizado", "_delta_t_smooth" not in content),
    ]
    
    print("\n[5] RESUMEN DE PROBLEMAS DETECTADOS:")
    print("=" * 80)
    for nombre, existe in problemas_encontrados:
        estado = "❌ PRESENTE" if existe else "✅ Ausente"
        print(f"   {estado}: {nombre}")
    
else:
    print("❌ ventana_principal.py no encontrada")

# 2. Buscar patrón específico de mouse control
print("\n[6] CODIGO RELEVANTE: Buscar enterEvent/leaveEvent")
if vp_path.exists():
    with open(vp_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if "enterEvent" in line or "leaveEvent" in line:
            print(f"   Línea {i+1}: {line.strip()}")
            # Mostrar siguiente línea
            if i+1 < len(lines):
                print(f"   Línea {i+2}: {lines[i+1].strip()}")

print("\n" + "=" * 80)
print("FIN DIAGNOSTICO")
print("=" * 80)
