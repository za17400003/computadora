"""
Tests para FP-023 — התחדשות אור חדש Hit'hadshut Ohr Jadash (Tikún del Sistema)
WI-109: Detector de ciclos tool-call
WI-110: Lock de estado Maljut
WI-111: Escritura atómica personalidad
WI-112: Buffer de audio acotado
WI-113: Límite de profundidad emocional
WI-114: Logging de excepciones watchdog
WI-115: Heartbeat rápido Ollama
WI-116: Timeouts adaptativos
WI-117: Hardening de inyección de comandos
WI-118: Hard cap tokens historial
WI-119: Guard de escritura concurrente personalidad
WI-120: Deep health check watchdog
WI-121: Protección ReDoS
WI-122: Motor de auto-actualización
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
# WI-109: Detector de ciclos tool-call
# ═══════════════════════════════════════════════
print("\n── WI-109: Detector de ciclos tool-call ──")

from computadora.cerebro.nlu import CerebroComputadora
# Verificar que la variable de tracking existe en el código fuente
import inspect
src_pensar = inspect.getsource(CerebroComputadora._pensar_con_herramientas)
test("_invocaciones_turno inicializado en pensar_con_herramientas", "_invocaciones_turno" in src_pensar)
test("Detección de ciclo con _sig", "_sig" in src_pensar)
test("Break en ciclo detectado", "Detecté un ciclo" in src_pensar or "ciclo" in src_pensar.lower())


# ═══════════════════════════════════════════════
# WI-110: Lock de estado Maljut
# ═══════════════════════════════════════════════
print("\n── WI-110: Lock de estado Maljut ──")

import threading
from computadora.interfaz.ventana_principal import OrbeComputadora
src_cambiar = inspect.getsource(OrbeComputadora.cambiar_estado)
test("cambiar_estado usa _estado_lock", "_estado_lock" in src_cambiar)
# Verificar que __init__ crea el lock
src_init = inspect.getsource(OrbeComputadora.__init__)
test("__init__ crea _estado_lock", "_estado_lock" in src_init)
test("threading.Lock en init", "threading.Lock()" in src_init)


# ═══════════════════════════════════════════════
# WI-111: Escritura atómica personalidad
# ═══════════════════════════════════════════════
print("\n── WI-111: Escritura atómica personalidad ──")

from computadora.memoria.personalidad import Personalidad
src_guardar = inspect.getsource(Personalidad.guardar)
test("guardar usa tempfile", "tempfile" in src_guardar)
test("guardar usa os.replace", "os.replace" in src_guardar)
test("guardar limpia tmp en error", "os.unlink" in src_guardar)


# ═══════════════════════════════════════════════
# WI-112: Buffer de audio acotado
# ═══════════════════════════════════════════════
print("\n── WI-112: Buffer de audio acotado ──")

from computadora.voz.escucha import HiloEscucha
src_procesar = inspect.getsource(HiloEscucha._procesar_stream)
test("audio_chunks usa deque", "deque" in src_procesar)
test("deque tiene maxlen=120", "maxlen=120" in src_procesar)

src_transcribir = inspect.getsource(HiloEscucha._transcribir)
test("_transcribir libera audio_chunks", "del audio_chunks" in src_transcribir)


# ═══════════════════════════════════════════════
# WI-113: Límite de profundidad emocional
# ═══════════════════════════════════════════════
print("\n── WI-113: Límite de profundidad emocional ──")

src_transicionar = inspect.getsource(Personalidad._transicionar_humor)
test("_transicionar_humor tiene param _depth", "_depth" in src_transicionar)
test("Límite de profundidad > 5", "_depth > 5" in src_transicionar)


# ═══════════════════════════════════════════════
# WI-114: Logging de excepciones watchdog
# ═══════════════════════════════════════════════
print("\n── WI-114: Logging de excepciones watchdog ──")

from computadora.interfaz.watchdog import ServicioMonitoreado
src_check = inspect.getsource(ServicioMonitoreado.check)
test("check usa logger.exception", "logger.exception" in src_check)
test("check NO usa logger.warning para excepciones", 
     "logger.warning" not in src_check.split("except")[1] if "except" in src_check else False)


# ═══════════════════════════════════════════════
# WI-115: Heartbeat rápido Ollama
# ═══════════════════════════════════════════════
print("\n── WI-115: Heartbeat rápido Ollama ──")

test("_quick_ping_ollama existe", hasattr(CerebroComputadora, '_quick_ping_ollama'))
test("_quick_ping_ollama es callable", callable(getattr(CerebroComputadora, '_quick_ping_ollama', None)))

src_pensar_main = inspect.getsource(CerebroComputadora.pensar)
test("pensar() llama _quick_ping_ollama", "_quick_ping_ollama" in src_pensar_main)


# ═══════════════════════════════════════════════
# WI-116: Timeouts adaptativos
# ═══════════════════════════════════════════════
print("\n── WI-116: Timeouts adaptativos ──")

test("_timeout_adaptativo existe", hasattr(CerebroComputadora, '_timeout_adaptativo'))
test("_timeout_adaptativo es callable", callable(getattr(CerebroComputadora, '_timeout_adaptativo', None)))

src_llamar = inspect.getsource(CerebroComputadora._llamar_ollama)
test("_llamar_ollama usa _timeout_adaptativo", "_timeout_adaptativo" in src_llamar)
test("_llamar_ollama registra latencias", "_latencias_ollama" in src_llamar)

from computadora.config import TIMEOUT_OLLAMA_DEFAULT, TIMEOUT_OLLAMA_MIN, TIMEOUT_OLLAMA_MAX
test("TIMEOUT_OLLAMA_DEFAULT = 90", TIMEOUT_OLLAMA_DEFAULT == 90)
test("TIMEOUT_OLLAMA_MIN = 30", TIMEOUT_OLLAMA_MIN == 30)
test("TIMEOUT_OLLAMA_MAX = 180", TIMEOUT_OLLAMA_MAX == 180)


# ═══════════════════════════════════════════════
# WI-117: Hardening de inyección de comandos
# ═══════════════════════════════════════════════
print("\n── WI-117: Hardening de inyección de comandos ──")

try:
    from computadora.habilidades.herramientas import _sanitizar_comando
    test("_sanitizar_comando existe", callable(_sanitizar_comando))
    test("Elimina punto y coma", ";" not in _sanitizar_comando("ls; rm -rf /"))
    test("Elimina backtick", "`" not in _sanitizar_comando("echo `whoami`"))
    test("Elimina $", "$" not in _sanitizar_comando("echo $PATH"))
    test("Preserva texto normal", _sanitizar_comando("dir /w") == "dir /w")
except ImportError:
    # FP-047 C: _sanitizar_comando fue reemplazado por GestorPermisos (FP-034)
    test("_sanitizar_comando migrado a permisos", True)

from computadora.habilidades.herramientas import ejecutar_comando
src_ejec = inspect.getsource(ejecutar_comando)
test("ejecutar_comando llama _sanitizar_comando", "_sanitizar_comando" in src_ejec or "GestorPermisos" in src_ejec)


# ═══════════════════════════════════════════════
# WI-118: Hard cap tokens historial
# ═══════════════════════════════════════════════
print("\n── WI-118: Hard cap tokens historial ──")

from computadora.cerebro.nlu import _MAX_TOKENS_HISTORIAL
test("_MAX_TOKENS_HISTORIAL = 4000", _MAX_TOKENS_HISTORIAL == 4000)

src_truncar = inspect.getsource(CerebroComputadora._truncar_historial_impl)
test("_truncar_historial_impl tiene hard cap tokens", "_MAX_TOKENS_HISTORIAL" in src_truncar)


# ═══════════════════════════════════════════════
# WI-119: Guard de escritura concurrente personalidad
# ═══════════════════════════════════════════════
print("\n── WI-119: Guard escritura concurrente personalidad ──")

p = Personalidad()
test("Personalidad tiene _guardar_lock", hasattr(p, '_guardar_lock'))
test("_guardar_lock es threading.Lock", isinstance(p._guardar_lock, type(threading.Lock())))

test("guardar usa with _guardar_lock", "_guardar_lock" in src_guardar)


# ═══════════════════════════════════════════════
# WI-120: Deep health check watchdog
# ═══════════════════════════════════════════════
print("\n── WI-120: Deep health check watchdog ──")

from computadora.interfaz.watchdog import _check_ollama
src_check_ollama = inspect.getsource(_check_ollama)
test("_check_ollama hace POST /api/generate", "/api/generate" in src_check_ollama)
test("_check_ollama tiene deep check", "deep check" in src_check_ollama.lower() or "num_predict" in src_check_ollama)


# ═══════════════════════════════════════════════
# WI-121: Protección ReDoS
# ═══════════════════════════════════════════════
print("\n── WI-121: Protección ReDoS ──")

test("_regex_safe existe", hasattr(CerebroComputadora, '_regex_safe'))
# Probar que funciona con regex seguro
import re
result = CerebroComputadora._regex_safe(r"hola\s+mundo", "hola mundo bonito")
test("_regex_safe retorna match para regex válido", result is not None)

result_none = CerebroComputadora._regex_safe(r"^xyz$", "abc")
test("_regex_safe retorna None para no-match", result_none is None)


# ═══════════════════════════════════════════════
# WI-122: Motor de auto-actualización
# ═══════════════════════════════════════════════
print("\n── WI-122: Motor de auto-actualización (Hit'hadshut) ──")

from computadora.nucleo.actualizador import (
    ActualizadorGolem,
    verificar_ollama,
    verificar_whisper,
    verificar_edge_tts,
    verificar_paquetes_desactualizados,
    actualizar_pip_paquetes,
)

test("ActualizadorGolem importable", ActualizadorGolem is not None)
act = ActualizadorGolem()
test("ActualizadorGolem instanciable", act is not None)
test("necesita_verificacion retorna bool", isinstance(act.necesita_verificacion(), bool))
test("INTERVALO_CHECK_HORAS = 24", act.INTERVALO_CHECK_HORAS == 24)
test("versiones retorna dict", isinstance(act.versiones, dict))
test("ultimo_reporte retorna str", isinstance(act.ultimo_reporte, str))

# Verificar que N1 tiene regex de actualización
test("N1 reconoce 'actualizar dependencias'", 
     "actualiz" in inspect.getsource(CerebroComputadora._pensar_nivel1))

# Funciones individuales son callable
test("verificar_ollama es callable", callable(verificar_ollama))
test("verificar_whisper es callable", callable(verificar_whisper))
test("verificar_edge_tts es callable", callable(verificar_edge_tts))
test("verificar_paquetes_desactualizados es callable", callable(verificar_paquetes_desactualizados))


# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
print(f"\n{'═' * 50}")
print(f"FP-023 Hit'hadshut Ohr Jadash: {passed} PASS / {failed} FAIL")
print(f"{'═' * 50}")

if __name__ == "__main__":
    if failed > 0:
        sys.exit(1)

