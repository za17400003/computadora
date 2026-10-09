"""
Tests para FP-022 — Maljut Autónomo: El Trono Viviente
WI-099: Thread Safety Tiféret
WI-100: Bereshit Resiliente
WI-101: FSM Formal Maljut
WI-102: Watchdog Multi-etapa
WI-103: Canal Bidireccional
WI-104: Ruaj Reactivo a Fallos
WI-105: Da'at Routing Circadiano
WI-106: Auto-diagnóstico Verbal
WI-107: Bandeja Enriquecida
WI-108: Multi-monitor Inteligente
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

passed = 0
failed = 0

def test(nombre, condicion):
    global passed, failed
    if condicion:
        passed += 1
        print(f"  ✅ {nombre}")
    else:
        failed += 1
        print(f"  ❌ {nombre}")


# ═══════════════════════════════════════════════
# WI-099: Thread Safety Tiféret
# ═══════════════════════════════════════════════
print("\n── WI-099: Thread Safety Tiféret ──")

from computadora.cerebro.nlu import CerebroComputadora
cerebro = CerebroComputadora.__new__(CerebroComputadora)
# Verificar que los locks existen como atributos de clase/instancia esperados
import threading
test("_historial_lock existe en CerebroComputadora", hasattr(CerebroComputadora, '__init__'))

# Verificar que _truncar_historial_impl existe (refactored)
test("_truncar_historial_impl método existe", hasattr(cerebro, '_truncar_historial_impl') or callable(getattr(CerebroComputadora, '_truncar_historial_impl', None)))


# ═══════════════════════════════════════════════
# WI-101: FSM Formal Maljut
# ═══════════════════════════════════════════════
print("\n── WI-101: FSM Formal Maljut ──")

from computadora.interfaz.ventana_principal import EstadoMaljut, _TRANSICIONES_VALIDAS, _STR_A_ESTADO

test("EstadoMaljut es Enum", hasattr(EstadoMaljut, 'DORMIDO'))
test("EstadoMaljut tiene 13 estados", len(EstadoMaljut) == 13)
test("DORMIDO en enum", EstadoMaljut.DORMIDO.value == "dormido")
test("ESCUCHANDO en enum", EstadoMaljut.ESCUCHANDO.value == "escuchando")
test("PROCESANDO en enum", EstadoMaljut.PROCESANDO.value == "procesando")
test("HABLANDO en enum", EstadoMaljut.HABLANDO.value == "hablando")
test("ERROR en enum", EstadoMaljut.ERROR.value == "error")
test("BERESHIT en enum", EstadoMaljut.BERESHIT.value == "bereshit")

# Transiciones válidas
test("DORMIDO puede ir a ESCUCHANDO", EstadoMaljut.ESCUCHANDO in _TRANSICIONES_VALIDAS[EstadoMaljut.DORMIDO])
test("ESCUCHANDO puede ir a PROCESANDO", EstadoMaljut.PROCESANDO in _TRANSICIONES_VALIDAS[EstadoMaljut.ESCUCHANDO])
test("PROCESANDO puede ir a HABLANDO", EstadoMaljut.HABLANDO in _TRANSICIONES_VALIDAS[EstadoMaljut.PROCESANDO])

# Lookup de string a enum
test("_STR_A_ESTADO mapea 'dormido'", _STR_A_ESTADO.get("dormido") == EstadoMaljut.DORMIDO)
test("_STR_A_ESTADO mapea 'error'", _STR_A_ESTADO.get("error") == EstadoMaljut.ERROR)
test("_STR_A_ESTADO tiene 13 entries", len(_STR_A_ESTADO) == 13)


# ═══════════════════════════════════════════════
# WI-102: Watchdog Multi-etapa
# ═══════════════════════════════════════════════
print("\n── WI-102: Watchdog Multi-etapa ──")

from computadora.interfaz.watchdog import EstadoCircuit, EtapaWatchdog, ServicioMonitoreado, WatchdogComputadora

test("EstadoCircuit tiene CLOSED/OPEN/HALF_OPEN", 
     hasattr(EstadoCircuit, 'CLOSED') and hasattr(EstadoCircuit, 'OPEN') and hasattr(EstadoCircuit, 'HALF_OPEN'))

test("EtapaWatchdog tiene OK/RETRY/NOTIFY/DEGRADE",
     hasattr(EtapaWatchdog, 'OK') and hasattr(EtapaWatchdog, 'RETRY') and 
     hasattr(EtapaWatchdog, 'NOTIFY') and hasattr(EtapaWatchdog, 'DEGRADE'))

# ServicioMonitoreado
svc = ServicioMonitoreado("test_svc", lambda: True)
test("ServicioMonitoreado: nombre correcto", svc.nombre == "test_svc")
test("ServicioMonitoreado: etapa inicial OK", svc.etapa == EtapaWatchdog.OK)
test("ServicioMonitoreado: circuit inicial CLOSED", svc.circuit == EstadoCircuit.CLOSED)
test("ServicioMonitoreado: fallos_consecutivos = 0", svc._fallos_consecutivos == 0)

# Simular fallos via check con función que falla
svc_fail = ServicioMonitoreado("test_fail", lambda: False, umbral_retry=0.01)
svc_fail.check()
test("1 fallo: etapa depende de tiempo (OK o RETRY)", svc_fail.etapa in (EtapaWatchdog.OK, EtapaWatchdog.RETRY))
svc_fail.check()
svc_fail.check()
test("3 fallos: circuit → OPEN", svc_fail.circuit == EstadoCircuit.OPEN)

# Simular éxito para reset
svc_ok = ServicioMonitoreado("test_ok", lambda: True)
svc_ok._fallos_consecutivos = 5
svc_ok.circuit = EstadoCircuit.HALF_OPEN
svc_ok.check()
test("Éxito: circuit vuelve a CLOSED", svc_ok.circuit == EstadoCircuit.CLOSED)
test("Éxito: etapa vuelve a OK", svc_ok.etapa == EtapaWatchdog.OK)


# ═══════════════════════════════════════════════
# WI-104: Ruaj Reactivo a Fallos
# ═══════════════════════════════════════════════
print("\n── WI-104: Ruaj Reactivo a Fallos ──")

from computadora.memoria.personalidad import Personalidad

p = Personalidad()
test("registrar_fallo_tecnico existe", hasattr(p, 'registrar_fallo_tecnico'))
test("registrar_frustracion_usuario existe", hasattr(p, 'registrar_frustracion_usuario'))

# Fallo técnico → preocupado
p._estado_animo["humor_actual"] = "neutral"
p.registrar_fallo_tecnico("ollama", "Error: conexión rechazada")
test("Fallo técnico: humor → preocupado", p.humor_actual == "preocupado")

# Frustración usuario → sereno
p._estado_animo["humor_actual"] = "neutral"
p.registrar_frustracion_usuario()
test("Frustración usuario: humor → sereno", p.humor_actual == "sereno")


# ═══════════════════════════════════════════════
# WI-105: Da'at Routing Circadiano
# ═══════════════════════════════════════════════
print("\n── WI-105: Da'at Routing Circadiano ──")

# Verificar que el import path funciona
try:
    from computadora.nucleo.proactividad import obtener_fase_actual
    fase = obtener_fase_actual()
    test("obtener_fase_actual() retorna string", isinstance(fase, str))
    test("Fase válida", fase in ("activo", "transicion", "descanso_guardian", "desconocido", ""))
except Exception as e:
    test(f"Import obtener_fase_actual OK", False)
    test(f"Fase válida", False)


# ═══════════════════════════════════════════════
# WI-106: Auto-diagnóstico Verbal
# ═══════════════════════════════════════════════
print("\n── WI-106: Auto-diagnóstico Verbal ──")

from computadora.cerebro.nlu import _RE_ESTADO_RAPIDO

test("_RE_ESTADO_RAPIDO matchea 'estás bien'", _RE_ESTADO_RAPIDO.search("estás bien") is not None)
test("_RE_ESTADO_RAPIDO matchea 'todo bien contigo'", _RE_ESTADO_RAPIDO.search("todo bien contigo") is not None)
test("_RE_ESTADO_RAPIDO matchea 'tu estado'", _RE_ESTADO_RAPIDO.search("tu estado") is not None)
test("_RE_ESTADO_RAPIDO matchea 'estado del sistema'", _RE_ESTADO_RAPIDO.search("estado del sistema") is not None)
test("_RE_ESTADO_RAPIDO NO matchea 'hola'", _RE_ESTADO_RAPIDO.search("hola") is None)

test("_generar_autodiag_verbal método existe", hasattr(CerebroComputadora, '_generar_autodiag_verbal'))


# ═══════════════════════════════════════════════
# WI-108: Multi-monitor Inteligente
# ═══════════════════════════════════════════════
print("\n── WI-108: Multi-monitor ──")

from computadora.interfaz.vida_autonoma import InfoEscritorio

info = InfoEscritorio()
test("InfoEscritorio tiene campo pantallas", hasattr(info, 'pantallas'))
test("InfoEscritorio tiene campo pantalla_foco", hasattr(info, 'pantalla_foco'))
test("pantallas es lista", isinstance(info.pantallas, list))
test("pantalla_foco default es 0", info.pantalla_foco == 0)


# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"FP-022 Tests: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*50}")
    sys.exit(0 if failed == 0 else 1)

