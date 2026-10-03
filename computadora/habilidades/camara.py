"""
צילום (Tsílum) — Vigilancia por Cámara
Módulo de visión continua para Computadora.

Responsabilidades:
- Captura de video en tiempo real (webcam)
- Detección de rostro + contexto visual
- Almacenamiento de frames + embeddings
- Integración con Observador para vigilancia inteligente
"""

import threading
import cv2
import json
import numpy as np
import time
import warnings
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import dataclass, asdict
from loguru import logger

# GEVURAH FIX: Suppressar warnings de FFMPEG y libpcap
warnings.filterwarnings('ignore', message='.*FFMPEG.*')
warnings.filterwarnings('ignore', message='.*libpcap.*')
import os
os.environ['CV_LOG_LEVEL'] = 'OFF'  # Suppressar logs de OpenCV
if cv2:
    # Suppressar warnings de OpenCV a nivel C++
    try:
        cv2.setLogLevel(0)  # Log level 0 = silent
    except:
        pass


def _abrir_video_capture(device_id):
    """Abre un VideoCapture local con el backend Windows más robusto."""
    backends = []
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    backends.append(None)

    for backend in backends:
        try:
            cap = cv2.VideoCapture(device_id) if backend is None else cv2.VideoCapture(device_id, backend)
            if cap.isOpened():
                return cap
            cap.release()
        except Exception:
            continue

    return cv2.VideoCapture(device_id)


@dataclass
class MetadataFrame:
    """Metadata de un fotograma capturado."""
    timestamp: str
    rostro_detectado: bool
    num_rostros: int
    iluminacion_nivel: float  # 0.0-1.0 (brillo promedio)
    archivo_jpg: Optional[str] = None
    embedding_size: Optional[int] = None


class CamaraVigilancia:
    """Captura y procesa video continuo de la webcam."""

    def __init__(self, dispositivo_id: int = 0, fps: int = 15, resolucion: Tuple[int, int] = (1280, 720)):
        self.dispositivo_id = dispositivo_id
        self.fps = fps
        self.resolucion = resolucion
        self._captura: Optional[cv2.VideoCapture] = None
        self._hilo_captura: Optional[threading.Thread] = None
        self._ejecutando = False
        self._ultimo_frame: Optional[np.ndarray] = None
        self._log_path = Path(__file__).resolve().parent.parent.parent / "datos" / "camara_logs"
        self._log_path.mkdir(parents=True, exist_ok=True)
        
        # WI-295: Contadores para supresión inteligente de warnings
        self._fallos_consecutivos = 0
        self._umbral_warning = 50  # Solo warning si 50+ fallos consecutivos
        self._ultimo_warning_tiempo = 0.0  # throttle: máx 1 warning cada 30s
        
        # Detector de rostro (usar dlib si disponible, sino cascade haar)
        self._detector_rostro = None
        self._inicializar_detector()

    def _inicializar_detector(self):
        """Inicializa detector de rostros con Haar Cascade para evitar memory corruption."""
        try:
            self._detector_haar = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            logger.info("✓ Usando Haar Cascade para detección de rostros (memory-safe)")
        except Exception as e:
            self._detector_haar = None
            logger.warning(f"No se pudo inicializar detector de rostros: {e}")

    def iniciar(self):
        """Inicia la captura de video."""
        if self._ejecutando:
            logger.warning("Cámara ya está en ejecución")
            return
        
        try:
            self._captura = _abrir_video_capture(self.dispositivo_id)
            if self._captura is None or not self._captura.isOpened():
                raise RuntimeError(f"No se pudo abrir cámara {self.dispositivo_id}")
            self._captura.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucion[0])
            self._captura.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucion[1])
            self._captura.set(cv2.CAP_PROP_FPS, self.fps)
            
            self._ejecutando = True
            self._hilo_captura = threading.Thread(
                target=self._bucle_captura,
                daemon=True,
                name="HiloCapturaCamara"
            )
            self._hilo_captura.start()
            logger.info(f"📹 Cámara iniciada (dispositivo {self.dispositivo_id}, {self.fps} FPS)")
        except Exception as e:
            logger.error(f"Error iniciando cámara: {e}")
            self._ejecutando = False

    def detener(self):
        """Detiene la captura de video."""
        self._ejecutando = False
        if self._hilo_captura:
            self._hilo_captura.join(timeout=2)
        if self._captura:
            self._captura.release()
        logger.info("📹 Cámara detenida")

    def obtener_ultimo_frame(self) -> Optional[np.ndarray]:
        """Retorna el último fotograma capturado."""
        return self._ultimo_frame

    def _bucle_captura(self):
        """Bucle principal de captura de video."""
        contador_frames = 0
        contador_intentos_reconexion = 0  # GEVURAH FIX: Rastrear reintentos
        while self._ejecutando:
            try:
                ret, frame = self._captura.read()
                if not ret:
                    self._fallos_consecutivos += 1
                    # WI-295: throttle warnings — máx 1 cada 30s
                    ahora = time.time()
                    if (self._fallos_consecutivos >= self._umbral_warning and 
                        ahora - self._ultimo_warning_tiempo >= 30.0):
                        logger.warning(f"⚠️ Cámara: {self._fallos_consecutivos} fallos consecutivos (reinicia: {contador_intentos_reconexion})")
                        self._ultimo_warning_tiempo = ahora
                        # GEVURAH FIX: Reintentar conexión cada 50 fallos, máx 3 intentos
                        if self._fallos_consecutivos >= 50 and contador_intentos_reconexion < 3:
                            contador_intentos_reconexion += 1
                            self._intentar_reconexion_camara()
                            self._fallos_consecutivos = 0  # Reset después de reintento
                        elif contador_intentos_reconexion >= 3:
                            logger.error("⚠️ Cámara: 3 reintentos fallidos. Continuando sin cámara.")
                            time.sleep(5)  # Esperar 5s antes de reintentar el ciclo completo
                    time.sleep(0.1)  # Esperar antes de reintentar
                    continue
                
                # Reset counters si funciona
                if self._captura is not None and self._fallos_consecutivos == 0:
                    contador_intentos_reconexion = 0  # GEVURAH FIX: Reset reintentos si funciona
                    self._ultimo_frame = frame
                    contador_frames += 1
                
                # Cada 30 frames (2s a 15 FPS), procesar y guardar
                if contador_frames % 30 == 0:
                    self._procesar_y_guardar_frame(frame)
                    contador_frames = 0
                    
            except Exception as e:
                logger.error(f"Error en bucle captura: {e}")
                self._fallos_consecutivos += 1
            
            # Controlar FPS
            time.sleep(1.0 / self.fps)
    
    def _intentar_reconexion_camara(self):
        """GEVURAH FIX: Reintenta reconectar cámara si está en estado fallido."""
        try:
            if self._captura:
                self._captura.release()
            self._captura = _abrir_video_capture(self.dispositivo_id)
            if self._captura is not None and self._captura.isOpened():
                self._captura.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolucion[0])
                self._captura.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolucion[1])
                logger.info("✓ Cámara reconectada exitosamente")
            else:
                logger.warning("⚠️ No se pudo reconectar cámara")
        except Exception as e:
            logger.warning(f"Error reconectando cámara: {e}")

    def _procesar_y_guardar_frame(self, frame: np.ndarray):
        """Procesa un fotograma: detecta rostros, genera metadata y guarda."""
        try:
            # Detectar rostros
            rostros = self._detectar_rostros(frame)
            rostro_detectado = len(rostros) > 0
            
            # Calcular iluminación
            iluminacion = self._calcular_iluminacion(frame)
            
            # Generar metadata
            timestamp_iso = datetime.now().isoformat()
            metadata = MetadataFrame(
                timestamp=timestamp_iso,
                rostro_detectado=rostro_detectado,
                num_rostros=len(rostros),
                iluminacion_nivel=iluminacion,
            )
            
            # Guardar frame como JPEG
            nombre_archivo = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_jpg = self._log_path / f"{nombre_archivo}_frame.jpg"
            cv2.imwrite(str(ruta_jpg), frame)
            metadata.archivo_jpg = ruta_jpg.name
            
            # Guardar metadata en JSON
            ruta_json = self._log_path / f"{nombre_archivo}_meta.json"
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Frame guardado: {metadata.num_rostros} rostro(s), iluminación {metadata.iluminacion_nivel:.2f}")
        
        except Exception as e:
            logger.error(f"Error procesando frame: {e}")

    def _detectar_rostros(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detecta rostros en el frame (retorna coordenadas)."""
        try:
            if self._detector_haar is None:
                return []
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            rostros = self._detector_haar.detectMultiScale(gray, 1.3, 5)
            return [(y, x + w, y + h, x) for (x, y, w, h) in rostros]
        except Exception as e:
            logger.debug(f"Error detectando rostros: {e}")
            return []

    def _calcular_iluminacion(self, frame: np.ndarray) -> float:
        """Calcula nivel de iluminación del frame (0.0-1.0)."""
        try:
            # Convertir a escala de grises
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Calcular brillo promedio normalizado
            brillo_promedio = np.mean(gray) / 255.0
            return float(brillo_promedio)
        except Exception as e:
            logger.debug(f"Error calculando iluminación: {e}")
            return 0.5


# Singleton global + flag de proteccion
_camara_instancia: Optional[CamaraVigilancia] = None
_CAMARA_FORZADA_ON = False  # GEVURAH FIX: Bandera para evitar cierre accidental


def obtener_camara() -> CamaraVigilancia:
    """Retorna la instancia singleton de la cámara."""
    global _camara_instancia
    if _camara_instancia is None:
        _camara_instancia = CamaraVigilancia()
    return _camara_instancia


def iniciar_camara():
    """Inicia vigilancia de cámara con proteccion contra cierres.
    
    GEVURAH FIX: Garantiza que la cámara siempre esté ON excepto Tzimtzum.
    """
    global _CAMARA_FORZADA_ON
    _CAMARA_FORZADA_ON = True
    camara = obtener_camara()
    if not camara._ejecutando:
        camara.iniciar()
        logger.info("Camara PROTEGIDA — siempre activa excepto Tzimtzum")


def detener_camara(fuerza_cierre: bool = False):
    """Detiene vigilancia de cámara solo si está permitido.
    
    GEVURAH FIX: No cierra si está marcada como forzada ON, excepto Tzimtzum.
    fuerza_cierre=True solo para Tzimtzum.
    """
    global _camara_instancia, _CAMARA_FORZADA_ON
    if not fuerza_cierre and _CAMARA_FORZADA_ON:
        logger.warning("Camara protegida — rechazando cierre fuera de Tzimtzum")
        return
    _CAMARA_FORZADA_ON = False
    if _camara_instancia:
        _camara_instancia.detener()
        _camara_instancia = None
        logger.info("Camara detenida (Tzimtzum)")


