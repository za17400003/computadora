#!/usr/bin/env python3
"""
NIGREDO EXHAUSTIVA — Análisis de problemas de animación en DEMO COMPUTADORA
Mayo 30, 2026

Problemas reportados:
1. Las animaciones de computadora no se muestran correctamente en demo
2. Sus anillos giran todos al unísono (deberían girar a velocidades distintas)
3. Tienen animaciones discretas cuando deben ser fluidas
4. Los colores de los anillos deben ser según recursos pero tienen color sólido
5. Las animaciones se ejecutan solo cuando mouse está sobre ventana (incorrecto)
"""

from pathlib import Path
import re
import json

print("=" * 90)
print("NIGREDO EXHAUSTIVA — PROBLEMAS DE ANIMACION EN DEMO COMPUTADORA")
print("=" * 90)

vp_path = Path("computadora/interfaz/ventana_principal.py")

if vp_path.exists():
    with open(vp_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = f.readlines()

# PROBLEMA 1: Animaciones solo cuando mouse sobre ventana
print("\n[PROBLEMA 1] Animaciones solo cuando mouse está sobre ventana")
print("-" * 90)

# Buscar si hay condiciones en _animar que verifiquen cursor
with open(vp_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_animar = False
animar_checks = []
for i, line in enumerate(lines):
    if 'def _animar(self):' in line:
        in_animar = True
        animar_start = i
    elif in_animar and line.strip().startswith('def '):
        break
    
    if in_animar and any(x in line for x in ['mapFromGlobal', '_cached_cursor', '_proximidad', 'enterEvent', 'leaveEvent']):
        animar_checks.append((i+1, line.strip()))

if animar_checks:
    print("⚠️  ENCONTRADO: Código relacionado con mouse/cursor en _animar()")
    for lineno, code in animar_checks:
        print(f"   Línea {lineno}: {code[:70]}")
else:
    print("✅ No hay código de mouse/cursor en _animar() — debería estar limpio")

# PROBLEMA 2: Anillos giran al unísono
print("\n[PROBLEMA 2] Anillos giran todos al unísono (deberían tener velocidades distintas)")
print("-" * 90)

# Buscar velocidades de rotación
with open(vp_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patrones de rotación
rot_patterns = [
    (r'_rot_anillo1\s*\+=\s*\(([\d.]+)\s*\*\s*60\s*\)\s*\*\s*_rot_mod\s*\*\s*delta_t', "anillo1"),
    (r'_rot_anillo2\s*-=\s*\(([\d.]+)\s*\*\s*60\s*\)\s*\*\s*_rot_mod\s*\*\s*delta_t', "anillo2"),
    (r'_rot_letras\s*\+=\s*\(([\d.]+)\s*\*\s*60\s*\)\s*\*\s*_rot_mod\s*\*\s*delta_t', "letras"),
]

velocidades = {}
for pattern, nombre in rot_patterns:
    matches = re.findall(pattern, content)
    if matches:
        velocidades[nombre] = matches
        print(f"   {nombre}: velocidad = {matches} rad/s")

# Verificar si hay condición que las congela
if '_demo_en_curso' in content:
    print("\n⚠️  ENCONTRADO: '_demo_en_curso' en código")
    print("   → Posible: rotaciones congeladas cuando _demo_en_curso == True")
    
    # Buscar donde se modifica la rotación basado en estado demo
    demo_patterns = re.findall(r'if.*_demo.*:|_demo_en_curso.*:', content)
    if demo_patterns:
        print(f"   → Encontradas {len(demo_patterns)} condiciones de demo")

# PROBLEMA 3: Animaciones discretas en lugar de fluidas
print("\n[PROBLEMA 3] Animaciones discretas (deberían ser fluidas)")
print("-" * 90)

# Verificar suavizado
if 'delta_t' in content and '_delta_t_smooth' in content:
    smooth_factor_match = re.search(r'_delta_smooth_factor\s*=\s*([\d.]+)', content)
    if smooth_factor_match:
        factor = float(smooth_factor_match.group(1))
        print(f"✅ EMA smoothing factor: {factor}")
        if factor >= 0.9:
            print(f"   → Factor {factor} es adecuado para suavidad")
    else:
        print("❌ No encontrado _delta_smooth_factor")
else:
    print("❌ No usa delta_t o _delta_t_smooth — animaciones serán discretas")

# Verificar si hay frame skipping
if 'continue' in content.split('def _animar')[1].split('def ')[0] if 'def _animar' in content else False:
    print("⚠️  Posible: frame skipping en _animar (causaría discreteness)")

# PROBLEMA 4: Colores sólidos en lugar de basados en recursos
print("\n[PROBLEMA 4] Colores sólidos en lugar de basados en recursos")
print("-" * 90)

# Verificar si colores se calculan con CPU/RAM/GPU
if 'cpu_pct' in content and 'ram_pct' in content:
    print("✅ Datos de CPU/RAM disponibles en paintEvent()")
    
    # Verificar si se usan en _renderizar o donde se calcula color
    if 'dibujar_anillos_con_recursos_optimizado' in content:
        print("✅ Parámetros cpu/ram/gpu pasados a dibujante")
    else:
        print("⚠️  Datos CPU/RAM presentes pero posible no se usan en colores")
else:
    print("❌ No hay cpu_pct/ram_pct — imposible colorear según recursos")

# PROBLEMA 5: Animaciones solo cuando mouse sobre ventana
print("\n[PROBLEMA 5] Animaciones se ejecutan solo cuando mouse está sobre ventana")
print("-" * 90)

# Verificar si enterEvent/leaveEvent detiene la animación
enter_event_code = re.search(r'def enterEvent\(self, event\):.*?(?=def \w+|\Z)', content, re.DOTALL)
leave_event_code = re.search(r'def leaveEvent\(self, event\):.*?(?=def \w+|\Z)', content, re.DOTALL)

problemas_mouse = []
if enter_event_code:
    code = enter_event_code.group(0)
    if '_timer.start()' in code or 'start()' in code:
        problemas_mouse.append("enterEvent inicia timer")
    if '_timer.stop()' in code or 'stop()' in code:
        problemas_mouse.append("enterEvent detiene timer")

if leave_event_code:
    code = leave_event_code.group(0)
    if '_timer.stop()' in code or 'stop()' in code:
        problemas_mouse.append("leaveEvent DETIENE TIMER ❌ PROBLEMA CRITICO")
    if 'self._hover = False' in code:
        problemas_mouse.append("leaveEvent modifica _hover")

if problemas_mouse:
    print("❌ PROBLEMAS ENCONTRADOS:")
    for p in problemas_mouse:
        print(f"   → {p}")
else:
    print("✅ enterEvent/leaveEvent están vacíos o no controlan timer")

# RESUMEN FINAL
print("\n" + "=" * 90)
print("RESUMEN DE PROBLEMAS IDENTIFICADOS")
print("=" * 90)

problemas_encontrados = {
    "1. Cursor control en _animar": len(animar_checks) > 0,
    "2. Rotaciones congeladas en demo": '_demo_en_curso' in content,
    "3. Sin suavizado delta_t": 'delta_t' not in content,
    "4. Sin colores dinámicos": 'cpu_pct' not in content,
    "5. Timer detenido por mouse": 'leaveEvent DETIENE TIMER' in str(problemas_mouse),
}

print()
for problema, existe in problemas_encontrados.items():
    estado = "❌ PRESENTE" if existe else "✅ Ausente"
    print(f"{estado}: {problema}")

print("\n" + "=" * 90)
