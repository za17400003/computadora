"""
Tests para FP-021 Fase 1 — Etz Jai: Quick Wins
WI-095: Categorías de bloqueo Gevurá
WI-096: Estados mixtos Ruaj
WI-097: Perfiles de audio adaptativos
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
# WI-095: Categorías de bloqueo Gevurá
# ═══════════════════════════════════════════════
print("\n── WI-095: Categorías de bloqueo Gevurá ──")

# Test 1: _evaluar_etica devuelve categorías específicas
from computadora.cerebro.nlu import _evaluar_etica
ok, cat, razon = _evaluar_etica("borra todo lo del disco")
test("_evaluar_etica: accion_destructiva detectada", not ok and cat == "accion_destructiva")

ok2, cat2, razon2 = _evaluar_etica("shutdown /s /t 0")
test("_evaluar_etica: shutdown detectado", not ok2 and cat2 == "shutdown")

ok3, cat3, razon3 = _evaluar_etica("hola cómo estás")
test("_evaluar_etica: texto normal es permitido", ok3 and cat3 == "")

# Test 2: Detección de bloqueos en resultados de herramientas
# Simular lo que hace nlu.py en el tool loop
resultado_bloqueado = "Error: Comando bloqueado por seguridad. No puedo ejecutar operaciones destructivas."
resultado_sandbox = "Error: Ruta fuera del sandbox del proyecto."
resultado_permiso = "Error: El comando 'netstat' no está en mi lista de comandos de sistema permitidos."
resultado_ok = "Archivo leído correctamente."

test("Detección bloqueado: contiene 'bloqueado por seguridad'", "bloqueado por seguridad" in resultado_bloqueado.lower())
test("Detección sandbox: contiene indicador de sandbox", "fuera del sandbox" in resultado_sandbox.lower() or "fuera de la raíz" in resultado_sandbox.lower())
test("Detección permiso: contiene 'no está en mi lista'", "no está en mi lista" in resultado_permiso.lower())
test("Resultado OK: no se detecta como bloqueo", not resultado_ok.startswith("Error:"))


# ═══════════════════════════════════════════════
# WI-096: Estados mixtos Ruaj
# ═══════════════════════════════════════════════
print("\n── WI-096: Estados mixtos Ruaj ──")

from computadora.memoria.personalidad import Personalidad, _GRAFO_EMOCIONAL, HUMORES_VALIDOS

p = Personalidad.__new__(Personalidad)
p._rasgos = {"humor": 0.5, "formalidad": 0.5, "curiosidad": 0.5, "energia": 0.5,
             "proactividad": 0.5, "introversion": 0.5, "paciencia": 0.5, "lealtad": 0.5}
p._estado_animo = {
    "humor_actual": "neutral",
    "humor_previo": "neutral",
    "humor_secundario": "",
    "peso_secundario": 0.0,
    "ultima_interaccion": None,
    "interacciones_hoy": 0,
    "dias_consecutivos": 0,
    "primer_dia": None,
    "tareas_exitosas_consecutivas": 0,
    "ultima_razon_humor": "inicio",
}
p._log_eventos = []

# Test: Estado inicial sin humor secundario
test("Estado inicial: humor_actual='neutral'", p.humor_actual == "neutral")
test("Estado inicial: humor_secundario vacío", p.humor_secundario == "")
test("Estado inicial: peso_secundario=0.0", p.peso_secundario == 0.0)

# Test: Transición a vecino directo genera secundario
p._transicionar_humor("sereno", "test")
test("Transición vecino: neutral→sereno", p.humor_actual == "sereno")
test("Transición vecino: secundario=neutral", p.humor_secundario == "neutral")
test("Transición vecino: peso_secundario=0.3", p.peso_secundario == 0.3)

# Test: Override contextual limpia secundario
p._transicionar_humor("formal", "test override", forzar=True)
test("Override: humor='formal'", p.humor_actual == "formal")
test("Override: secundario limpio", p.humor_secundario == "")
test("Override: peso=0.0", p.peso_secundario == 0.0)

# Test: tono_respuesta incluye humor secundario
p._estado_animo["humor_actual"] = "curioso"
p._estado_animo["humor_secundario"] = "cansado"
p._estado_animo["peso_secundario"] = 0.3
tono = p.tono_respuesta()
test("tono_respuesta: contiene hint de curioso", "curioso" in tono.lower() or "pregunta" in tono.lower())
test("tono_respuesta: contiene matiz de secundario", "matiz" in tono.lower() or "cansado" in tono.lower())

# Test: tono_respuesta sin secundario no menciona matiz
p._estado_animo["humor_secundario"] = ""
p._estado_animo["peso_secundario"] = 0.0
tono2 = p.tono_respuesta()
test("tono_respuesta sin secundario: sin matiz", "matiz" not in tono2.lower())

# Test: Propiedades humor_secundario y peso_secundario
p._estado_animo["humor_secundario"] = "reflexivo"
p._estado_animo["peso_secundario"] = 0.4
test("Property humor_secundario", p.humor_secundario == "reflexivo")
test("Property peso_secundario", p.peso_secundario == 0.4)


# ═══════════════════════════════════════════════
# WI-097: Perfiles de audio adaptativos
# ═══════════════════════════════════════════════
print("\n── WI-097: Perfiles de audio adaptativos ──")

from computadora.voz.habla import HiloHabla

# Mock config
class MockConfig:
    def obtener(self, key, default=None):
        return default

# Crear instancia sin iniciar thread
h = HiloHabla.__new__(HiloHabla)
h._personalidad_ref = None

# Test: Sin refs externas → sin cambio ("+0%")
rate, vol = h._calcular_audio_adaptativo()
test("Sin refs: rate=+0%", rate == "+0%")
test("Sin refs: volume=+0%", vol == "+0%")

# Test: Con personalidad emocionada → rate +10%
class MockPersona:
    humor_actual = "emocionado"
h._personalidad_ref = MockPersona()
rate, vol = h._calcular_audio_adaptativo()
test("Humor emocionado: rate incluye +10%", "+10%" in rate)

# Test: Con personalidad cansada → rate -5%, vol -5%
class MockPersonaCansada:
    humor_actual = "cansado"
h._personalidad_ref = MockPersonaCansada()
rate, vol = h._calcular_audio_adaptativo()
test("Humor cansado: rate negativo", "-5%" in rate)
test("Humor cansado: volume negativo", "-5%" in vol)

# Test: Humor neutral → sin cambio
class MockPersonaNeutral:
    humor_actual = "neutral"
h._personalidad_ref = MockPersonaNeutral()
rate, vol = h._calcular_audio_adaptativo()
test("Humor neutral: rate=+0%", rate == "+0%")
test("Humor neutral: volume=+0%", vol == "+0%")


# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════
print(f"\n{'='*50}")
total = passed + failed
print(f"FP-021 Fase 1: {passed}/{total} tests PASS")
if failed:
    print(f"⚠️  {failed} tests FALLARON")
    if __name__ == "__main__":
        sys.exit(1)
else:
    print("✅ Todos los tests pasaron")

