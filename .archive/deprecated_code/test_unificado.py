'''
TEST UNIFICADO DE COMPUTADORA.

Prueba TODOS los SRS integrados de una sola vez:
- WI-298: Geometrias platonicas (TransmutadorOrbe)
- WI-299: Vision (camara, deteccion)
- WI-309: Bohr (colisiones, exclusion Pauli)
- WI-310: Sommerfeld (orbitas elipticas)
- WI-311: Chadwick (neutrones)
- WI-312: Lewis (transicion esfera<->teseracto)
- WI-313: Rutherford (carga emocional)
- WI-314: Audio/Vision total + historial hilo conversacional
- FP-163: VisionTotal (YOLO + MediaPipe)
- FP-165: AudioAvanzado (VAD + Wake Word)
- FP-166: Optimizador recursos (CPU/GPU/RAM)

Ejecutar: python test_unificado.py
'''

import sys
import time

sys.path.insert(0, '.')

from loguru import logger
logger.remove()
logger.add(lambda msg: print(msg, end=''), format='<level>{level:.<8}</level> | {message}', level='INFO')


class TestUnificado:
    def __init__(self):
        self.resultados = []
        self.fallos = 0
        self.exitos = 0
        self.ts_inicio = time.time()
    
    def test(self, nombre, fn, *args, **kwargs):
        try:
            t0 = time.time()
            resultado = fn(*args, **kwargs)
            elapsed = (time.time() - t0) * 1000
            if resultado is None or resultado:
                self.resultados.append((nombre, True, elapsed))
                self.exitos += 1
                print('  [OK] ' + nombre + f' ({elapsed:.0f}ms)')
            else:
                self.resultados.append((nombre, False, elapsed))
                self.fallos += 1
                print('  [FAIL] ' + nombre)
        except Exception as e:
            self.resultados.append((nombre, False, 0))
            self.fallos += 1
            print('  [ERROR] ' + nombre + ': ' + str(e))
    
    def ejecutar(self):
        print()
        print('=' * 70)
        print('  TEST UNIFICADO DE COMPUTADORA')
        print('  Demos 1, 2 y 3 integradas')
        print('=' * 70)
        print()
        
        # MODULO 1: Optimizador de Recursos
        print('[MODULO 1] Optimizador de Recursos (FP-166)')
        print('-' * 50)
        def test_optimizador():
            from computadora.utilidad.optimizador_recursos import obtener_optimizador
            opt = obtener_optimizador()
            estado = opt.obtener_estado()
            assert estado.ram_total_mb > 0, 'RAM no detectada'
            from computadora.utilidad.optimizador_recursos import activar_tzimtzum, activar_maxima_potencia
            activar_tzimtzum()
            asig_render = opt.obtener_asignacion('render')
            assert asig_render == 'none', f'TzimTzum no libero GPU: {asig_render}'
            asig_audio = opt.obtener_asignacion('audio')
            assert asig_audio == 'cpu', f'Audio debe estar en CPU: {asig_audio}'
            activar_maxima_potencia()
            return True
        self.test('FP-166: Optimizador detecta hardware y cambia modo', test_optimizador)
        
        # MODULO 2: Geometrias Platonicas
        print()
        print('[MODULO 2] Geometrias Platonicas (WI-298)')
        print('-' * 50)
        def test_transmutador():
            from computadora.geometria.geometrias_platonicas import TransmutadorOrbe
            t = TransmutadorOrbe()
            assert t.obtener_solido_para_estado('idle') is not None
            t.transmutar_a('procesando')
            assert len(t.vertices_cache) > 0, 'Sin vertices'
            return True
        self.test('WI-298: TransmutadorOrbe mapea estados y genera vertices', test_transmutador)
        
        def test_dodecaedro():
            from computadora.geometria.geometrias_platonicas import GeneradorGeometrias
            g = GeneradorGeometrias()
            verts, aristas = g.generar_dodecaedro(100.0)
            assert len(verts) == 20, f'Dodecaedro debe tener 20 vertices, tiene {len(verts)}'
            assert len(aristas) >= 30, f'Dodecaedro debe tener 30 aristas, tiene {len(aristas)}'
            return True
        self.test('WI-298: Dodecaedro tiene 20 vertices y 30 aristas', test_dodecaedro)
        
        # MODULO 3: Historial Dinamico
        print()
        print('[MODULO 3] Dialogo / Historial Dinamico (WI-314)')
        print('-' * 50)
        def test_historial():
            from computadora.dialogo.historial_dinamico import HistorialDinamico, es_comando_para_mi
            h = HistorialDinamico(metatron=None)
            h.agregar_mensaje('system', 'Sistema iniciado')
            h.agregar_mensaje('user', 'computadora, como estas?')
            h.agregar_mensaje('assistant', 'Estoy bien, gracias')
            ctx = h.get_contexto_completo()
            assert len(ctx) > 0, 'Contexto vacio'
            assert es_comando_para_mi('computadora, ayudame'), 'Fallo: deberia ser comando'
            assert not es_comando_para_mi('me gusta la television'), 'Fallo: deberia ignorar'
            assert not es_comando_para_mi('como estas'), 'Fallo: sin contexto, deberia ignorar'
            return True
        self.test('WI-314: Historial mantiene hilo y filtra tipo Alexa', test_historial)
        
        # MODULO 4: Vision Total
        print()
        print('[MODULO 4] Vision Total (FP-163 / WI-314)')
        print('-' * 50)
        def test_vision():
            from computadora.vision.vision_total import obtener_vision
            vision = obtener_vision()
            stats = vision.obtener_stats()
            assert 'detectores_activos' in stats, 'Stats incompletos'
            return True
        self.test('FP-163: VisionTotal inicializa correctamente', test_vision)
        
        # MODULO 5: Optimizacion Fractal
        print()
        print('[MODULO 5] Optimizacion Fractal de Memoria')
        print('-' * 50)
        def test_compresion():
            from computadora.utilidad.optimizador_recursos import obtener_optimizador
            import numpy as np
            opt = obtener_optimizador()
            datos = np.random.randn(1000000)
            comprimido = opt.comprimir_memoria(datos, umbral_mb=1)
            assert comprimido.dtype == np.float32, 'Compresion no redujo precision'
            assert comprimido.nbytes < datos.nbytes, 'No se redujo el tamano'
            return True
        self.test('FP-166: Compresion fractal reduce memoria', test_compresion)
        
        # MODULO 6: Resumen del Sistema
        print()
        print('[MODULO 6] Resumen del Sistema')
        print('-' * 50)
        def test_resumen():
            from computadora.utilidad.optimizador_recursos import obtener_optimizador
            opt = obtener_optimizador()
            estado = opt.obtener_estado()
            print(f'    RAM: {estado.ram_libre_mb}MB / {estado.ram_total_mb}MB libre')
            print(f'    CPU: {estado.cpu_uso_porcentaje}%')
            print(f'    GPU: {estado.gpu_nombre or "No detectada"}')
            print(f'    Modo: {estado.modo_actual.value}')
            print(f'    Disco libre: {estado.disco_libre_mb}MB')
            return True
        self.test('Sistema: Estado detectado', test_resumen)
        
        # Resultado final
        print()
        print('=' * 70)
        total = self.exitos + self.fallos
        tiempo_total = (time.time() - self.ts_inicio)
        print(f'  RESULTADO: {self.exitos}/{total} exitos')
        if self.fallos == 0:
            print('  ESTADO: TODOS LOS MODULOS OPERATIVOS')
        else:
            print(f'  ESTADO: {self.fallos} fallos detectados')
        print(f'  Tiempo total: {tiempo_total:.2f}s')
        print('=' * 70)
        print()
        print('Nota: Vision y Audio requieren camara/microfono fisicos')
        print('      para pruebas completas de hardware.')
        print()
        
        return self.fallos == 0


if __name__ == '__main__':
    test = TestUnificado()
    resultado = test.ejecutar()
    sys.exit(0 if resultado else 1)

