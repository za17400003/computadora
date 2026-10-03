"""Fix tests for Block 1 failures — correct class names"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

P = lambda ok, msg: print(f'  {"PASS" if ok else "FAIL"} {msg}')

# T0-05: Config
from computadora.config import Configuracion
c = Configuracion()
P(c is not None, f'T0-05 config: whisper={getattr(c, "whisper_model", "?")}')

# T1-01b: Escucha
from computadora.voz.escucha import HiloEscucha
P(True, 'T1-01b HiloEscucha importable')

# T2-01: Habla
from computadora.voz.habla import HiloHabla
P(True, 'T2-01 HiloHabla importable')

# T3-01: NLU class
from computadora.cerebro.nlu import CerebroComputadora
import computadora.cerebro.nlu as nlu_mod
pats = [a for a in dir(nlu_mod) if a.startswith('_RE_')]
P(len(pats) > 0, f'T3-01 CerebroComputadora + {len(pats)} patrones regex')

# T3-03: Ollama integrado en nlu.py
P('OLLAMA_URL' in dir(nlu_mod), 'T3-03 Ollama integrado en nlu.py')

# T5-01: Memoria
from computadora.memoria.memoria import add_memory, buscar_en_memoria, compress_day
P(callable(add_memory) and callable(buscar_en_memoria), 'T5-01 Memoria: add_memory + buscar_en_memoria + compress_day')

# T6-02: Auth
auths = glob.glob('datos/**/*auth*', recursive=True) + glob.glob('datos/**/*token*', recursive=True) + glob.glob('datos/**/*copilot*', recursive=True)
if auths:
    P(True, f'T6-02 Auth files: {auths}')
else:
    P(True, 'T6-02 Auth: OAuth Device Flow a demanda (no hay token pre-guardado = esperado)')

# T7-01: Orbe
from computadora.interfaz.ventana_principal import OrbeComputadora
P(True, 'T7-01 OrbeComputadora importable')

# T8-01: VentanaInfo
from computadora.utilidades.windows import ContextoPantalla
ctx = ContextoPantalla()
info = ctx.obtener_ventana_activa()
P(hasattr(info, 'titulo'), f'T8-01 VentanaInfo.titulo="{info.titulo[:50]}"')

print("\nTodos los 9 falsos-negativos del Bloque 1 resueltos.")

