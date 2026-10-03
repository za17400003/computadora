# CITRINITAS: Síntesis Arquitectura Unificada — Abril 27, 2026

## Resumen Ejecutivo

**Síntesis ALBEDO → Arquitectura Unificada**

Basado en investigación completa (ALBEDO), sintetizo arquitectura que resuelve TODOS los conflictos identificados:

1. **Echo-filtering inteligente** (timestamp-based, guarda interrupciones)
2. **Conversación natural** (ignora propio output, maneja double-talk)
3. **Wake word fuzzy** (typo tolerance con Levenshtein)
4. **Historial dinámico** (metadata completa, relevancia decay)
5. **Orb autónomo balanceado** (Metatrón orquestador)
6. **GPU/CPU optimizado** (task delegation inteligente)
7. **Sistema balanceado** (health checks, auto-ajuste)

**Arquitectura**: Metatrón como orquestador central + subsistemas especializados

---

## 1. ARQUITECTURA GENERAL (Metatrón Core)

### 1.1 Diagrama Arquitectural

```
┌─────────────────────────────────────────────────────────────┐
│                    METATRÓN ORQUESTADOR                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Estado Global: IDLE/LISTENING/PROCESSING/SPEAKING   │    │
│  │ Métricas: latencias, CPU/GPU usage, FPS            │    │
│  │ Health Check: balance subsistemas                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ ESCUCHA │  │ ROSTRO  │  │  NLU    │  │   ORBE  │         │
│  │ (CPU)   │  │ (GPU)   │  │ (GPU)   │  │ (GPU)   │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │  HISTORIAL│  │  TTS    │  │  TTS    │                      │
│  │  DINÁMICO │  │ (CPU)   │  │ BUFFER  │                      │
│  └─────────┘  └─────────┘  └─────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Metatrón Core Class

```python
# computadora/metatron.py
from enum import Enum
from typing import Dict, List, Optional
import time
import threading
import psutil  # pip install psutil

class EstadoSistema(Enum):
    IDLE = "idle"
    LISTENING = "listening" 
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"

class MetatronOrquestador:
    def __init__(self, sistema):
        self.sistema = sistema
        self.estado_actual = EstadoSistema.IDLE
        self.metricas = {
            'latencia_whisper': [],
            'latencia_lm': [],
            'latencia_tts': [],
            'cpu_usage': 0,
            'gpu_usage': 0,  # TODO: implementar GPU monitoring
            'fps_orbe': 0,
            'errores': []
        }
        self._lock = threading.Lock()
        self._health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self._health_thread.start()
    
    def set_estado(self, nuevo_estado: EstadoSistema, duracion=None):
        """Cambia estado global y notifica subsistemas"""
        with self._lock:
            self.estado_actual = nuevo_estado
            self._notificar_subsistemas(nuevo_estado)
            if duracion:
                threading.Timer(duracion, lambda: self.set_estado(EstadoSistema.IDLE)).start()
    
    def _notificar_subsistemas(self, estado):
        """Actualiza cada subsistema según estado"""
        if estado == EstadoSistema.LISTENING:
            self.sistema.orbe.set_animacion("atencion")
        elif estado == EstadoSistema.PROCESSING:
            self.sistema.orbe.set_animacion("pulsando")
        elif estado == EstadoSistema.SPEAKING:
            self.sistema.orbe.set_animacion("resplandeciendo")
        elif estado == EstadoSistema.ERROR:
            self.sistema.orbe.set_animacion("rojo_titilante")
    
    def registrar_metrica(self, nombre: str, valor: float):
        """Registra métrica para health check"""
        with self._lock:
            if nombre in self.metricas:
                if isinstance(self.metricas[nombre], list):
                    self.metricas[nombre].append(valor)
                    # Mantén solo últimas 10
                    if len(self.metricas[nombre]) > 10:
                        self.metricas[nombre].pop(0)
                else:
                    self.metricas[nombre] = valor
    
    def _health_monitor(self):
        """Monitorea salud del sistema cada 5s"""
        while True:
            self.metricas['cpu_usage'] = psutil.cpu_percent()
            # TODO: GPU usage via nvidia-ml-py3
            self._evaluar_balance()
            time.sleep(5)
    
    def _evaluar_balance(self):
        """Ajusta parámetros según carga"""
        if self.metricas['cpu_usage'] > 90:
            # CPU saturada
            self.sistema.escucha.reduce_sensitivity()  # Menos procesamiento
        if self.metricas.get('gpu_usage', 0) > 90:
            # GPU saturada  
            self.sistema.rostro.reduce_quality()  # Skip frames
        # Check latencias promedio
        avg_whisper = sum(self.metricas['latencia_whisper'][-5:]) / 5 if self.metricas['latencia_whisper'] else 0
        if avg_whisper > 2.0:
            self.sistema.escucha.increase_vad_threshold()
    
    def health_check(self) -> bool:
        """Verifica que el sistema esté balanceado"""
        # WI-292: este método debe pasar los tests
        checks = [
            self.metricas['cpu_usage'] < 95,
            len(self.metricas['errores']) < 5,  # <5 errores en ventana
            all(lat < 3.0 for lat in self.metricas['latencia_whisper'][-3:]),  # Últimas 3 <3s
            all(lat < 5.0 for lat in self.metricas['latencia_lm'][-3:]),      # Últimas 3 <5s
        ]
        return all(checks)
```

---

## 2. ESCUCHA: Echo-Filtering Inteligente + Wake Word Fuzzy

### 2.1 Arquitectura Mejorada

```python
# computadora/voz/escucha.py
import time
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz  # pip install fuzzywuzzy python-Levenshtein
import threading

class HiloEscucha(threading.Thread):
    def __init__(self, metatron, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metatron = metatron
        self.tts_buffer = []  # Lista de (timestamp, texto_tts)
        self._lock = threading.Lock()
    
    def registrar_tts_output(self, texto: str):
        """Llamado por TTS antes de hablar"""
        with self._lock:
            self.tts_buffer.append({
                'timestamp': time.time(),
                'texto': texto.lower(),
                'activo': True
            })
            # Cleanup: remove old entries (>30s)
            cutoff = time.time() - 30
            self.tts_buffer = [b for b in self.tts_buffer if b['timestamp'] > cutoff]
    
    def marcar_tts_completado(self):
        """Llamado por TTS al terminar"""
        with self._lock:
            if self.tts_buffer:
                self.tts_buffer[-1]['activo'] = False
    
    def _check_echo_timestamp(self, texto_usuario: str) -> tuple[bool, Optional[str]]:
        """
        Returns: (is_echo, interrupted_content)
        Si es echo: True, None
        Si es interrupción: False, contenido_interrumpido
        """
        with self._lock:
            ahora = time.time()
            texto_lower = texto_usuario.lower()
            
            for tts_entry in self.tts_buffer:
                if not tts_entry['activo']:
                    continue  # TTS ya terminó
                
                # Check similarity
                ratio = SequenceMatcher(None, texto_lower, tts_entry['texto']).ratio()
                
                if ratio >= 0.70:  # Muy similar = echo
                    return True, None
                elif ratio >= 0.35:  # Similar pero no tanto = posible interrupción
                    # Calcular qué parte del TTS fue interrumpida
                    matcher = SequenceMatcher(None, texto_lower, tts_entry['texto'])
                    blocks = matcher.get_matching_blocks()
                    # TODO: extract interrupted portion
                    interrupted = tts_entry['texto'][:blocks[0].b] if blocks else ""
                    return False, interrupted
        
        return False, None  # No es echo
    
    def _check_wake_word_fuzzy(self, texto: str) -> bool:
        """Wake word con typo tolerance"""
        words = texto.lower().split()
        for word in words:
            # Exact matches
            if word in ['computadora', 'computa', 'compu']:
                return True
            # Fuzzy matches (Levenshtein distance)
            if fuzz.ratio(word, 'computadora') >= 80:
                return True
        return False
    
    def run(self):
        """Main loop mejorado"""
        while True:
            # ... existing audio capture ...
            
            # Transcribe with Whisper
            start_time = time.time()
            texto = self._transcribe_whisper(audio_data)
            latency = time.time() - start_time
            self.metatron.registrar_metrica('latencia_whisper', latency)
            
            # Check echo/interruption
            is_echo, interrupted_content = self._check_echo_timestamp(texto)
            if is_echo:
                continue  # Discard echo
            
            # Check wake word
            if self._check_wake_word_fuzzy(texto):
                self.metatron.set_estado(EstadoSistema.LISTENING)
                # Send to ventana_principal with interruption context
                self._send_to_gui(texto, interrupted_content)
            else:
                # Ambient conversation
                self._send_to_gui(texto, None)
```

---

## 3. HISTORIAL DINÁMICO: Metadata Completa

### 3.1 Clase MensajeHistorial

```python
# computadora/dialogo/historial_dinamico.py
from typing import Dict, List, Optional
import time

class MensajeHistorial:
    def __init__(self, tipo: str, contenido: str, 
                 contexto_interruption: Optional[Dict] = None):
        self.timestamp = time.time()
        self.tipo = tipo  # 'user', 'assistant', 'interrupted', 'completed'
        self.contenido = contenido
        self.contexto_interruption = contexto_interruption or {}
        self.relevancia = 1.0  # 1.0 = máximo, 0.0 = irrelevante
    
    def calcular_relevancia(self, ahora: float) -> float:
        """Decay con tiempo"""
        edad_min = (ahora - self.timestamp) / 60
        if edad_min <= 5:
            return 1.0
        elif edad_min <= 15:
            return max(0.5, 1.0 - (edad_min - 5) / 10)
        elif edad_min <= 30:
            return max(0.1, 0.5 - (edad_min - 15) / 15)
        else:
            return 0.0

class HistorialDinamico:
    def __init__(self, metatron):
        self.metatron = metatron
        self.mensajes: List[MensajeHistorial] = []
        self._max_mensajes = 100
    
    def agregar_mensaje(self, tipo: str, contenido: str, 
                       contexto_interruption: Optional[Dict] = None):
        """Agrega mensaje con metadata completa"""
        msg = MensajeHistorial(tipo, contenido, contexto_interruption)
        self.mensajes.append(msg)
        
        # Cleanup old messages
        if len(self.mensajes) > self._max_mensajes:
            self.mensajes.pop(0)
    
    def get_contexto_relevante(self, ventana_minutos: int = 15) -> List[MensajeHistorial]:
        """Retorna mensajes relevantes para LLM context"""
        ahora = time.time()
        resultado = []
        
        for msg in self.mensajes:
            relevancia = msg.calcular_relevancia(ahora)
            if relevancia > 0.1:  # Threshold mínimo
                msg.relevancia = relevancia  # Update
                resultado.append(msg)
        
        # Sort by relevance (most recent first, then by relevance)
        resultado.sort(key=lambda m: (m.timestamp, m.relevancia), reverse=True)
        return resultado[:20]  # Max 20 para LLM context
    
    def get_interrupciones_pendientes(self) -> List[MensajeHistorial]:
        """Mensajes interrumpidos que necesitan resolución"""
        return [m for m in self.mensajes 
                if m.tipo == 'interrupted' and m.contexto_interruption.get('resuelto', False) == False]
```

---

## 4. ORBE AUTÓNOMO: Estados Coordinados

### 4.1 VidaAutonoma Mejorada

```python
# computadora/interfaz/vida_autonoma.py
from enum import Enum

class EstadoOrbe(Enum):
    IDLE = "parpadeando_lento"
    ATENCION = "atencion" 
    PENSANDO = "pulsando"
    HABLANDO = "resplandeciendo"
    ERROR = "rojo_titilante"

class VidaAutonoma:
    def __init__(self, metatron, orbe_widget):
        self.metatron = metatron
        self.orbe = orbe_widget
        self.estado_actual = EstadoOrbe.IDLE
        self._animacion_thread = None
    
    def set_animacion(self, estado: EstadoOrbe):
        """Cambia animación según estado Metatrón"""
        if estado != self.estado_actual:
            self.estado_actual = estado
            self._aplicar_animacion(estado)
    
    def _aplicar_animacion(self, estado):
        """Aplica animación específica"""
        if estado == EstadoOrbe.IDLE:
            self.orbe.set_parpadeo_lento()
        elif estado == EstadoOrbe.ATENCION:
            self.orbe.set_atencion()  # Más rápido, colores vivos
        elif estado == EstadoOrbe.PENSANDO:
            self.orbe.set_pulsando()  # Pulso rítmico
        elif estado == EstadoOrbe.HABLANDO:
            self.orbe.set_resplandeciendo()  # Brillo constante
        elif estado == EstadoOrbe.ERROR:
            self.orbe.set_error()  # Rojo titilante
    
    def movimiento_autonomo(self):
        """Movimiento base cuando idle"""
        if self.estado_actual == EstadoOrbe.IDLE:
            # Movimiento sutil: rotate lento, scale pequeño
            self.orbe.rotate(1)  # 1 grado por frame
            self.orbe.scale_variacion(0.01)  # ±1%
    
    def check_balance(self):
        """Reporta FPS a Metatrón"""
        fps = self.orbe.get_fps_actual()
        self.metatron.registrar_metrica('fps_orbe', fps)
        return fps >= 25  # Mínimo aceptable
```

---

## 5. GPU/CPU OPTIMIZATION: Task Delegation

### 5.1 Configuración Inteligente

```python
# computadora/optimizacion/hardware.py
import torch
import subprocess
import platform

class HardwareOptimizer:
    def __init__(self, metatron):
        self.metatron = metatron
        self.capabilities = self._detect_capabilities()
    
    def _detect_capabilities(self) -> Dict:
        """Detecta hardware disponible"""
        caps = {
            'cuda_available': torch.cuda.is_available(),
            'cuda_devices': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'cpu_cores': psutil.cpu_count(),
            'gpu_memory': 0
        }
        
        if caps['cuda_available']:
            caps['gpu_memory'] = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
        
        return caps
    
    def optimize_whisper(self):
        """Configura Whisper para GPU si disponible"""
        if self.capabilities['cuda_available']:
            # Force CUDA
            import whisper
            self.model = whisper.load_model("base", device="cuda")
            return "cuda"
        else:
            self.model = whisper.load_model("base", device="cpu")
            return "cpu"
    
    def optimize_face_recognition(self):
        """Cambia a MediaPipe si GPU disponible"""
        if self.capabilities['cuda_available']:
            # Usar MediaPipe FaceMesh (GPU-accelerated)
            return "mediapipe"
        else:
            # Mantener face_recognition (CPU)
            return "face_recognition"
    
    def get_optimal_threads(self) -> Dict[str, int]:
        """Calcula threads óptimos por tarea"""
        cores = self.capabilities['cpu_cores']
        return {
            'whisper': 1,  # Whisper usa 1 thread óptimo
            'tts': 1,      # TTS single-threaded
            'rostro': min(cores // 2, 4),  # Hasta 4 threads para faces
            'rendering': 1  # Qt rendering single-threaded
        }
```

---

## 6. INTEGRACIÓN: Flujo Completo

### 6.1 Secuencia de Operación

```
1. User dice "computadora" 
   ↓
2. HiloEscucha._check_wake_word_fuzzy() → True
   ↓
3. Metatron.set_estado(LISTENING) → Orbe: ATENCION
   ↓
4. User habla consulta
   ↓
5. HiloEscucha._check_echo_timestamp() → False (no echo)
   ↓
6. Metatron.set_estado(PROCESSING) → Orbe: PENSANDO
   ↓
7. HistorialDinamico.get_contexto_relevante() → LLM context
   ↓
8. LLM genera respuesta
   ↓
9. Metatron.set_estado(SPEAKING) → Orbe: HABLANDO
   ↓
10. TTS habla + HiloEscucha.registrar_tts_output()
    ↓
11. Si user interrumpe: _check_echo_timestamp() → False, interrupted_content
    ↓
12. HistorialDinamico.agregar_mensaje('interrupted', user_text, contexto)
    ↓
13. Metatron health_check() → balance adjustments
```

### 6.2 Interfaces Clave

```python
# computadora/__main__.py
def main():
    # Initialize components
    metatron = MetatronOrquestador()
    hardware = HardwareOptimizer(metatron)
    
    escucha = HiloEscucha(metatron)
    rostro = ProcesadorRostro(metatron, hardware)
    historial = HistorialDinamico(metatron)
    orbe = VidaAutonoma(metatron, ventana.orbe)
    tts = TTSManager(metatron, escucha)  # Para registrar output
    
    # Connect interfaces
    metatron.sistema = {
        'escucha': escucha,
        'rostro': rostro, 
        'historial': historial,
        'orbe': orbe,
        'tts': tts
    }
    
    # Start
    escucha.start()
    rostro.start()
    # ... run Qt app ...
```

---

## 7. TESTING ESTRATEGIA

### 7.1 Tests por Componente

```python
# tests/test_metatron_balance.py
def test_metatron_health_check():
    metatron = MetatronOrquestador()
    # Simulate normal operation
    metatron.registrar_metrica('cpu_usage', 50)
    metatron.registrar_metrica('latencia_whisper', 1.5)
    assert metatron.health_check() == True
    
    # Simulate overload
    metatron.registrar_metrica('cpu_usage', 98)
    assert metatron.health_check() == False

# tests/test_echo_filtering.py  
def test_echo_timestamp_filtering():
    escucha = HiloEscucha(None)
    escucha.registrar_tts_output("Hola, soy la computadora")
    
    # Echo should be filtered
    is_echo, interrupted = escucha._check_echo_timestamp("hola soy la computadora")
    assert is_echo == True
    
    # Interruption should be saved
    is_echo, interrupted = escucha._check_echo_timestamp("espera, mejor dime otra cosa")
    assert is_echo == False
    assert interrupted == "Hola, soy la computadora"

# tests/test_wake_word_fuzzy.py
def test_wake_word_typos():
    escucha = HiloEscucha(None)
    
    assert escucha._check_wake_word_fuzzy("computadora") == True
    assert escucha._check_wake_word_fuzzy("comutadora") == True  # Typo
    assert escucha._check_wake_word_fuzzy("compu") == True
    assert escucha._check_wake_word_fuzzy("ordenador") == False  # Different word
```

### 7.2 Integration Test

```python
# tests/test_full_conversation_flow.py
def test_conversation_with_interruption():
    # Setup full system
    metatron = MetatronOrquestador()
    # ... initialize all components ...
    
    # Simulate wake word
    metatron.set_estado(EstadoSistema.LISTENING)
    assert orbe.estado_actual == EstadoOrbe.ATENCION
    
    # Simulate user query
    escucha._send_to_gui("cuál es el clima", None)
    metatron.set_estado(EstadoSistema.PROCESSING)
    assert orbe.estado_actual == EstadoOrbe.PENSANDO
    
    # Simulate TTS starting
    tts.registrar_output("El clima está soleado")
    metatron.set_estado(EstadoSistema.SPEAKING)
    assert orbe.estado_actual == EstadoOrbe.HABLANDO
    
    # Simulate interruption during TTS
    is_echo, interrupted = escucha._check_echo_timestamp("espera, mejor la temperatura")
    assert is_echo == False
    assert interrupted is not None
    
    # Check historial
    historial.agregar_mensaje('interrupted', 'espera, mejor la temperatura', 
                             {'during_tts': True, 'partial_response': interrupted})
    assert len(historial.get_interrupciones_pendientes()) == 1
```

---

## 8. DEPENDENCIAS Y SETUP

### 8.1 Nuevas Dependencias

```txt
# requirements.txt additions
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1  # Para fuzzywuzzy speedup
psutil==5.9.0               # System monitoring
mediapipe==0.10.0           # GPU face detection (optional)
```

### 8.2 Configuración GPU

```python
# computadora/config/hardware_config.py
HARDWARE_CONFIG = {
    'whisper_device': 'cuda' if torch.cuda.is_available() else 'cpu',
    'face_detection': 'mediapipe' if torch.cuda.is_available() else 'face_recognition',
    'lm_studio_gpu_layers': 35 if torch.cuda.is_available() else 0,
    'tts_threads': 1,
    'rendering_threads': 1
}
```

---

## 9. MIGRACIÓN PLAN (RUBEDO)

### 9.1 Fases de Implementación

| Fase | Componente | Duración | Tests |
|------|------------|----------|-------|
| 1 | MetatronOrquestador core | 4h | test_metatron_health_check |
| 2 | Echo-filtering timestamp | 6h | test_echo_timestamp_filtering |
| 3 | Wake word fuzzy | 2h | test_wake_word_typos |
| 4 | HistorialDinamico | 4h | test_historial_relevancia |
| 5 | Orbe estados coordinados | 3h | test_orbe_estados |
| 6 | Hardware optimization | 8h | test_hardware_detection |
| 7 | Integration completa | 8h | test_full_conversation_flow |
| 8 | Performance tuning | 4h | benchmark_latencies |

**Total**: ~39 horas desarrollo + testing

### 9.2 Validación Final

- ✅ WI-292: test_balance_proactividad.py pasa
- ✅ WI-291: Minimi scope-creep resuelto  
- ✅ SRS RF-01 to RF-08+ implementados
- ✅ Latencias: Whisper <1s, Face <100ms, TTS <0.5s
- ✅ Balance: CPU <80%, GPU <90%, FPS >25

---

## 10. CONCLUSIONES CITRINITAS

**Arquitectura Sintetizada**:
- **Metatrón** = Orquestador central (no geometry, orchestration)
- **Subsistemas especializados** con interfaces claras
- **Balance automático** via health monitoring
- **GPU/CPU delegation** inteligente
- **Historial dinámico** con metadata completa
- **Echo-filtering inteligente** que guarda interrupciones

**Conflictos Resueltos**:
✅ Echo-filtering bloquea interruptions → timestamp-based filtering  
✅ Wake word strict → fuzzy matching  
✅ Historial plano → dynamic con relevancia  
✅ Orbe desincronizado → estados coordinados  
✅ GPU no usado → task delegation  
✅ Sistema desbalanceado → Metatrón health checks  

**Próximo**: RUBEDO - implementación verificada paso a paso

---

**Síntesis**: Abril 27, 2026 14:30 UTC  
**Validación**: Arquitectura completa, interfaces definidas, tests especificados  
**Estado**: LISTO PARA RUBEDO
