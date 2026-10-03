#!/usr/bin/env python3
"""
RUBEDO RONDA 2: BRUTE FORCE MASIVO - 59,681 candidatos
Usando diccionario mejorado de PALINGENESIA
"""

import pikepdf
import time
import threading
from datetime import datetime

print("\n" + "="*80)
print("RUBEDO RONDA 2: BRUTE FORCE MASIVO (59,681 candidatos)".center(80))
print("="*80 + "\n")

pdf_file = 'resiste-protected.pdf'

# Cargar candidatos
print("[*] Cargando diccionario Ronda 2...")
with open('candidatos_ronda2_palingenesia.txt', 'r', encoding='utf-8') as f:
    candidatos = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"[*] Total candidatos: {len(candidatos)}\n")

# Variables compartidas
lock = threading.Lock()
stats = {
    'intentos': 0,
    'inicio': time.time(),
    'encontrado': False,
    'password_encontrada': None,
    'ultimo_reportado': 0
}

def reporte_progreso():
    """Imprime progreso cada 3 segundos"""
    while not stats['encontrado']:
        time.sleep(3)
        with lock:
            if stats['intentos'] > stats['ultimo_reportado']:
                elapsed = time.time() - stats['inicio']
                velocidad = stats['intentos'] / elapsed if elapsed > 0 else 0
                pct = (stats['intentos'] / len(candidatos)) * 100
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {stats['intentos']:,}/{len(candidatos):,} ({pct:.1f}%) | "
                      f"{velocidad:.0f} pwd/s | ETA: {(len(candidatos)-stats['intentos'])/velocidad/60:.1f}min")
                stats['ultimo_reportado'] = stats['intentos']

# Thread de reporte
reporter = threading.Thread(target=reporte_progreso, daemon=True)
reporter.start()

# BRUTE FORCE
print("[!] Iniciando ataque Ronda 2...")
print(f"[!] Esto puede tomar varios minutos\n")

inicio = time.time()

for idx, candidato in enumerate(candidatos):
    if stats['encontrado']:
        break
    
    try:
        # Intentar abrir
        with pikepdf.open(pdf_file, password=candidato, allow_overwriting_input=True) as pdf:
            # ÉXITO
            with lock:
                stats['encontrado'] = True
                stats['password_encontrada'] = candidato
                elapsed = time.time() - stats['inicio']
                
                print(f"\n{'='*80}")
                print(f"[✓✓✓] ¡¡¡ CONTRASEÑA ENCONTRADA !!!".center(80))
                print(f"{'='*80}\n")
                print(f"    Candidato #{idx+1} de {len(candidatos)}")
                print(f"    Contraseña: {candidato}")
                print(f"    Intentos totales: {idx+1}")
                print(f"    Tiempo: {elapsed:.1f}s ({elapsed/60:.1f}min)")
                print(f"    Velocidad: {idx/elapsed:.0f} pwd/s\n")
                
                # Guardar la contraseña y el PDF desbloqueado
                try:
                    with pikepdf.open(pdf_file, password=candidato) as pdf_success:
                        pdf_success.save('resiste-DESBLOQUEADO.pdf')
                        print(f"    ✓ PDF desbloqueado guardado como: resiste-DESBLOQUEADO.pdf\n")
                except:
                    pass
                
                # Guardar password
                with open('RUBEDO_R2_PASSWORD_ENCONTRADA.txt', 'w') as f:
                    f.write(f"CONTRASEÑA: {candidato}\n")
                    f.write(f"TIMESTAMP: {datetime.now()}\n")
                    f.write(f"INTENTOS: {idx+1}\n")
                    f.write(f"TIEMPO: {elapsed:.1f}s\n")
            break
            
    except pikepdf.PasswordError:
        with lock:
            stats['intentos'] = idx + 1
    except Exception as e:
        with lock:
            stats['intentos'] = idx + 1

# Finalizar
if not stats['encontrado']:
    elapsed = time.time() - stats['inicio']
    print(f"\n{'='*80}")
    print("[✗] NO ENCONTRADA - Los 59,681 candidatos fallaron".center(80))
    print(f"{'='*80}")
    print(f"\nTiempo total: {elapsed:.1f}s ({elapsed/60:.1f} minutos)")
    print(f"Velocidad promedio: {len(candidatos)/elapsed:.0f} passwords/segundo")
    print(f"\nSiguientes pasos:")
    print(f"  1. La contraseña es probablemente más compleja")
    print(f"  2. Podría haber error en transcripción (Whisper)")
    print(f"  3. Podría estar en descripción de video o metadata")
    print(f"  4. Considerar contactar al creador del PDF")
else:
    print("\n[✓] PDF desbloqueado con éxito!")

print("\n" + "="*80)
print("RUBEDO RONDA 2 COMPLETADO".center(80))
print("="*80)
