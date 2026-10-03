#!/usr/bin/env python3
"""
RUBEDO (קידושין): Manifestación - BRUTE FORCE MASIVO
Ataca el PDF con los 3,375 candidatos usando pikepdf
Estrategia: Paralización Python con threads, tiempo real
"""

import pikepdf
import time
import threading
from datetime import datetime
import sys

print("\n" + "="*80)
print("RUBEDO: FASE DE MANIFESTACIÓN - BRUTE FORCE MASIVO".center(80))
print("="*80 + "\n")

pdf_file = 'resiste-protected.pdf'

# Cargar candidatos
print("[*] Cargando diccionario de candidatos...")
with open('candidatos_albedo_citrinitas.txt', 'r', encoding='utf-8') as f:
    candidatos = [line.strip() for line in f if line.strip()]

print(f"[*] Total candidatos: {len(candidatos)}\n")

# Variables compartidas (thread-safe)
lock = threading.Lock()
stats = {
    'intentos': 0,
    'inicio': time.time(),
    'ultimo_reporte': time.time(),
    'encontrado': False,
    'password_encontrada': None
}

def reporte_progreso():
    """Imprime progreso cada 5 segundos"""
    while not stats['encontrado']:
        time.sleep(5)
        with lock:
            elapsed = time.time() - stats['inicio']
            velocidad = stats['intentos'] / elapsed if elapsed > 0 else 0
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {stats['intentos']:,} intentos | "
                  f"{velocidad:.0f} pwd/s | Tiempo: {elapsed:.1f}s")

# Thread de reporte
reporter = threading.Thread(target=reporte_progreso, daemon=True)
reporter.start()

# BRUTE FORCE
print("[!] Iniciando ataque...")
print(f"[!] Esto puede tomar minutos. El sistema probará hasta {len(candidatos)} passwords\n")

encontrado = False
password_correcta = None

for idx, candidato in enumerate(candidatos):
    if stats['encontrado']:
        break
    
    try:
        # Intentar abrir con este candidato
        with pikepdf.open(pdf_file, password=candidato, allow_overwriting_input=True) as pdf:
            # Si llegamos aquí, la contraseña es correcta
            with lock:
                stats['encontrado'] = True
                stats['password_encontrada'] = candidato
                password_correcta = candidato
                print(f"\n{'='*80}")
                print(f"[✓✓✓] ¡¡¡ CONTRASEÑA ENCONTRADA !!!".center(80))
                print(f"{'='*80}")
                print(f"\n    Candidato #{idx+1}")
                print(f"    Contraseña: {candidato}")
                print(f"    Intentos totales: {idx+1}")
                print(f"    Tiempo: {time.time() - stats['inicio']:.1f}s\n")
            break
            
    except pikepdf.PasswordError:
        # Contraseña incorrecta, continuar
        with lock:
            stats['intentos'] = idx + 1
    except Exception as e:
        # Error inesperado, loguear pero continuar
        print(f"[!] Error en candidato '{candidato}': {e}")
        with lock:
            stats['intentos'] = idx + 1

# Finalizar
if not stats['encontrado']:
    elapsed = time.time() - stats['inicio']
    print(f"\n{'='*80}")
    print("[✗] NO ENCONTRADA - Los 3,375 candidatos fallaron".center(80))
    print(f"{'='*80}")
    print(f"\nTiempo total: {elapsed:.1f}s")
    print(f"Velocidad promedio: {len(candidatos)/elapsed:.0f} passwords/segundo")
    print(f"\nPróximos pasos (PALINGENESIA):")
    print(f"  1. Generar diccionario más agresivo")
    print(f"  2. Intentar con palabras españolas adicionales")
    print(f"  3. Analizar patrones del usuario")
else:
    elapsed = time.time() - stats['inicio']
    print(f"\nEstadísticas finales:")
    print(f"  Contraseña: {password_correcta}")
    print(f"  Intentos: {len(candidatos)}")
    print(f"  Tiempo: {elapsed:.1f}s")
    print(f"  Velocidad: {len(candidatos)/elapsed:.0f} pwd/s")
    
    # Guardar resultado
    with open('RUBEDO_PASSWORD_ENCONTRADA.txt', 'w') as f:
        f.write(f"CONTRASEÑA: {password_correcta}\n")
        f.write(f"TIMESTAMP: {datetime.now()}\n")
        f.write(f"INTENTOS: {len(candidatos)}\n")

print("\n" + "="*80)
print("RUBEDO COMPLETADO".center(80))
print("="*80)
