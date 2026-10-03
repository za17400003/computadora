#!/usr/bin/env python
"""
DIAGNÓSTICO REAL-TIME: Monitorea FPS DURANTE la ejecución actual
Lee el log en vivo mientras Computadora se ejecuta
"""
import subprocess
import time
import re
import sys

def monitor_fps_realtime():
    """Ejecuta Computadora y monitorea FPS en tiempo real"""
    print("=" * 80)
    print("MONITOR DE FPS EN TIEMPO REAL")
    print("=" * 80)
    print("Ejecutando: python -m computadora")
    print("Buscando: 'Frame rate' cada 60 frames")
    print("Ctrl+C para detener\n")
    
    try:
        # Ejecutar computadora y capturar salida EN VIVO
        process = subprocess.Popen(
            ["python", "-m", "computadora"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        frame_rate_pattern = re.compile(r"Frame rate: ([\d.]+) FPS")
        animacion_pattern = re.compile(r"Animación iniciada: (\d+) FPS")
        last_fps = None
        fps_readings = []
        
        for line in process.stdout:
            # Mostrar TODOS los logs
            print(line.rstrip())
            
            # Buscar "Animación iniciada"
            match_anim = animacion_pattern.search(line)
            if match_anim:
                print(f"\n>>> STARTUP FPS CLAIM: {match_anim.group(1)} FPS (NO VERIFICADO AÚN)")
            
            # Buscar "Frame rate"
            match_fps = frame_rate_pattern.search(line)
            if match_fps:
                fps = float(match_fps.group(1))
                fps_readings.append(fps)
                last_fps = fps
                
                # Análisis en vivo
                if fps < 40:
                    print(f"\n❌ BAJO FPS: {fps:.1f} FPS (PROBLEMA DETECTADO)")
                elif fps < 55:
                    print(f"\n⚠️  FPS DEGRADADO: {fps:.1f} FPS (debería ser 60+)")
                else:
                    print(f"\n✅ FPS OK: {fps:.1f} FPS")
                
                # Estadísticas después de 3+ lecturas
                if len(fps_readings) >= 3:
                    avg_fps = sum(fps_readings) / len(fps_readings)
                    min_fps = min(fps_readings)
                    max_fps = max(fps_readings)
                    print(f"   Stats (últimas {len(fps_readings)} mediciones):")
                    print(f"   - Promedio: {avg_fps:.1f} FPS")
                    print(f"   - Rango: {min_fps:.1f} - {max_fps:.1f} FPS")
        
        process.wait()
        
        print("\n" + "=" * 80)
        print("DIAGNÓSTICO FINAL")
        print("=" * 80)
        
        if fps_readings:
            avg_fps = sum(fps_readings) / len(fps_readings)
            min_fps = min(fps_readings)
            max_fps = max(fps_readings)
            
            print(f"✅ Se obtuvieron {len(fps_readings)} mediciones de FPS")
            print(f"   Promedio: {avg_fps:.1f} FPS")
            print(f"   Rango: {min_fps:.1f} - {max_fps:.1f} FPS")
            
            if avg_fps >= 55:
                print(f"\n✅ CONCLUSIÓN: FPS está BIEN (promedio {avg_fps:.1f})")
            elif avg_fps >= 45:
                print(f"\n⚠️  CONCLUSIÓN: FPS DEGRADADO (promedio {avg_fps:.1f}, debería ser 60+)")
            else:
                print(f"\n❌ CONCLUSIÓN: FPS CRÍTICO (promedio {avg_fps:.1f}, debería ser 60)")
        else:
            print("❌ NO se registraron mediciones de FPS")
            print("   Posibles causas:")
            print("   1. Sistema se cerró antes de completar 60 frames")
            print("   2. Instrumentación de FPS no se está ejecutando")
            print("   3. Logs no se están mostrando (revisar nivel de logging)")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n>>> Monitor interrumpido por usuario")
        process.terminate()
        process.wait()
        sys.exit(0)

if __name__ == "__main__":
    monitor_fps_realtime()
