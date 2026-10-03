"""
FP-163: VISION TOTAL — YOLO + MediaPipe + CLIP para Computer Vision.
══════════════════════════════════════════════════════════════════════

Detecta todo lo detectable sin saturar procesos:
  - Rostros (MediaPipe Face Mesh)
  - Esqueletos/cuerpo completo (MediaPipe Pose)
  - Manos (MediaPipe Hands)
  - Objetos generales (YOLOv8/v5 ultralytics)
  - Animales, vehiculos, etc. (incluido en YOLO)

ARQUITECTURA OPTIMIZADA:
  1. Frame Processor Pipeline: YOLO + MediaPipe en hilo separado
  2. Pool compartido de frames: no mas de 2 fps de inferencia
  3. Cache de detecciones: reutiliza durante 0.5s
  4. Modo "no exclusivo": release de camara entre frames

WI-314: Uso compartido de camara con otras apps (sin exclusividad).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from loguru import logger


# ── Imports opcionales: deteccion ────────────────────────────────

_DISABLE_VISION = False

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    _DISABLE_VISION = True

# MediaPipe
_MP_HOLISTIC_AVAILABLE = False
_MP_FACE_AVAILABLE = False
_MP_POSE_AVAILABLE = False
_MP_HANDS_AVAILABLE = False

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
    _MP_HOLISTIC_AVAILABLE = hasattr(mp.solutions, 'holistic')
    _MP_FACE_AVAILABLE = hasattr(mp.solutions, 'face_mesh')
    _MP_POSE_AVAILABLE = hasattr(mp.solutions, 'pose')
    _MP_HANDS_AVAILABLE = hasattr(mp.solutions, 'hands')
except ImportError:
    _MP_AVAILABLE = False

# YOLO
_YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    try:
        # Fallback a YOLOv5
        import torch  # noqa: F401
        _YOLO_AVAILABLE = True
    except ImportError:
        pass


class DetectorTipo(Enum):
    """Tipos de deteccion disponibles."""
    ROSTRO = "rostro"
    POSE = "pose"
    MANOS = "manos"
    OBJETOS = "objetos"
    ANIMALES = "animales"
    VEHICULOS = "vehiculos"
    PERSONAS = "personas"


@dataclass
class Deteccion:
    """Una deteccion generica."""
    tipo: DetectorTipo
    confianza: float
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2 (normalizado 0-1)
    etiqueta: str = ""
    puntos_clave: List[Tuple[float, float]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class FrameProcesado:
    """Resultado del procesamiento de un frame."""
    detecciones: List[Deteccion]
    timestamp_frame: float
    tiempo_procesamiento_ms: float
    fps_inferencia: float


class VisionTotal:
    """
    Pipeline completo de vision por computadora.

    Se ejecuta en hilo separado, nunca bloquea el main loop.
    Saca frames del shared buffer, procesa con YOLO + MediaPipe,
    y publica resultados en un Dict compartido.

    WI-314: No mantiene la camara abierta — lee frames del buffer.
    """

    def __init__(self, max_fps: int = 2):
        self.max_fps = max_fps
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Cache de resultados (ultima deteccion)
        self._ultimas_detecciones: List[Deteccion] = []
        self._ultimo_frame_procesado: Optional[FrameProcesado] = None
        self._ultimo_timestamp: float = 0.0

        # Pool de modelos (lazy loading)
        self._yolo_model = None
        self._holistic = None
        self._face_mesh = None
        self._pose = None
        self._hands = None

        # Stats
        self._fps_reales = 0.0
        self._frames_procesados = 0
        self._tiempo_total_ms = 0.0

        # Buffer compartido (el gestor de camara pone frames aqui)
        self._shared_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._frame_counter = 0

        logger.info(f"VisionTotal inicializada (max_fps={max_fps})")

    def publicar_frame(self, frame: np.ndarray) -> None:
        """Publica un frame para ser procesado (llamado por gestor de camara)."""
        with self._frame_lock:
            self._shared_frame = frame.copy()
            self._frame_counter += 1

    def _tomar_frame(self) -> Optional[np.ndarray]:
        """Toma el ultimo frame disponible (non-blocking)."""
        with self._frame_lock:
            if self._shared_frame is not None:
                return self._shared_frame.copy()
            return None

    # ── Modelos lazy ─────────────────────────────────────────────

    def _cargar_yolo(self):
        """Carga YOLO (una sola vez)."""
        if self._yolo_model is not None:
            return
        try:
            if _YOLO_AVAILABLE:
                from ultralytics import YOLO
                # Usar modelo nano para velocidad
                self._yolo_model = YOLO('yolov8n.pt')
                logger.info("YOLOv8n cargado")
        except Exception as e:
            logger.warning(f"No se pudo cargar YOLO: {e}")

    def _cargar_mediapipe(self):
        """Carga modelos MediaPipe (una sola vez)."""
        if not _MP_AVAILABLE:
            return
        try:
            import mediapipe as mp
            if _MP_HOLISTIC_AVAILABLE:
                self._holistic = mp.solutions.holistic.Holistic(
                    static_image_mode=False,
                    model_complexity=0,  # Lite para velocidad
                    enable_segmentation=False,
                    smooth_landmarks=True,
                )
                logger.info("MediaPipe Holistic cargado")
            else:
                if _MP_POSE_AVAILABLE:
                    self._pose = mp.solutions.pose.Pose(
                        static_image_mode=False,
                        model_complexity=0,
                        enable_segmentation=False,
                    )
                if _MP_FACE_AVAILABLE:
                    self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                        static_image_mode=False,
                        max_num_faces=2,
                        refine_landmarks=True,
                        min_detection_confidence=0.5,
                    )
                if _MP_HANDS_AVAILABLE:
                    self._hands = mp.solutions.hands.Hands(
                        static_image_mode=False,
                        max_num_hands=2,
                        min_detection_confidence=0.5,
                    )
                logger.info("MediaPipe modulos individuales cargados")
        except Exception as e:
            logger.warning(f"No se pudo cargar MediaPipe: {e}")

    # ── Pipeline de procesamiento ────────────────────────────────

    def _procesar_frame(self, frame: np.ndarray) -> List[Deteccion]:
        """Procesa un frame con todos los detectores."""
        detecciones: List[Deteccion] = []
        h, w = frame.shape[:2]

        # 1. YOLO para objetos generales
        if _YOLO_AVAILABLE:
            self._cargar_yolo()
            if self._yolo_model is not None:
                try:
                    results = self._yolo_model(frame, verbose=False, device='cpu')
                    for r in results:
                        boxes = r.boxes
                        if boxes is not None:
                            for box in boxes:
                                conf = float(box.conf[0])
                                if conf < 0.4:
                                    continue
                                cls_id = int(box.cls[0])
                                etiqueta = r.names[cls_id] if hasattr(r, 'names') else str(cls_id)
                                x1, y1, x2, y2 = box.xyxy[0].tolist()

                                # Clasificar tipo
                                tipo = DetectorTipo.OBJETOS
                                if 'person' in etiqueta.lower():
                                    tipo = DetectorTipo.PERSONAS
                                elif any(a in etiqueta.lower() for a in
                                         ['cat', 'dog', 'bird', 'horse', 'cow', 'sheep', 'elephant',
                                          'bear', 'zebra', 'giraffe', 'rabbit', 'mouse']):
                                    tipo = DetectorTipo.ANIMALES
                                elif any(v in etiqueta.lower() for v in
                                         ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'airplane',
                                          'train', 'boat']):
                                    tipo = DetectorTipo.VEHICULOS

                                det = Deteccion(
                                    tipo=tipo,
                                    confianza=conf,
                                    bbox=(x1/w, y1/h, x2/w, y2/h),
                                    etiqueta=etiqueta,
                                )
                                detecciones.append(det)
                except Exception as e:
                    logger.debug(f"YOLO error: {e}")

        # 2. MediaPipe para rostros, pose y manos
        if _MP_AVAILABLE:
            self._cargar_mediapipe()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                # Holistic (todo en uno)
                if self._holistic is not None:
                    results = self._holistic.process(frame_rgb)

                    # Rostro
                    if results.face_landmarks:
                        puntos = [(lm.x, lm.y) for lm in results.face_landmarks.landmark]
                        xs = [p[0] for p in puntos]
                        ys = [p[1] for p in puntos]
                        detecciones.append(Deteccion(
                            tipo=DetectorTipo.ROSTRO,
                            confianza=0.9,
                            bbox=(min(xs), min(ys), max(xs), max(ys)),
                            puntos_clave=puntos[:10],
                        ))

                    # Pose (esqueleto)
                    if results.pose_landmarks:
                        puntos = [(lm.x, lm.y) for lm in results.pose_landmarks.landmark]
                        xs = [p[0] for p in puntos if p[0] > 0]
                        ys = [p[1] for p in puntos if p[1] > 0]
                        if xs and ys:
                            detecciones.append(Deteccion(
                                tipo=DetectorTipo.POSE,
                                confianza=0.85,
                                bbox=(min(xs), min(ys), max(xs), max(ys)),
                                puntos_clave=puntos,
                            ))

                    # Manos
                    if results.left_hand_landmarks:
                        puntos = [(lm.x, lm.y) for lm in results.left_hand_landmarks.landmark]
                        detecciones.append(Deteccion(
                            tipo=DetectorTipo.MANOS,
                            confianza=0.8,
                            bbox=(0, 0, 0, 0),
                            puntos_clave=puntos,
                            etiqueta="mano_izquierda",
                        ))
                    if results.right_hand_landmarks:
                        puntos = [(lm.x, lm.y) for lm in results.right_hand_landmarks.landmark]
                        detecciones.append(Deteccion(
                            tipo=DetectorTipo.MANOS,
                            confianza=0.8,
                            bbox=(0, 0, 0, 0),
                            puntos_clave=puntos,
                            etiqueta="mano_derecha",
                        ))
                else:
                    # Fallback a modulos individuales
                    if self._pose is not None:
                        pose_results = self._pose.process(frame_rgb)
                        if pose_results.pose_landmarks:
                            puntos = [(lm.x, lm.y) for lm in pose_results.pose_landmarks.landmark]
                            detecciones.append(Deteccion(
                                tipo=DetectorTipo.POSE,
                                confianza=0.85,
                                bbox=(0, 0, 1, 1),
                                puntos_clave=puntos,
                            ))

                    if self._face_mesh is not None:
                        face_results = self._face_mesh.process(frame_rgb)
                        if face_results.multi_face_landmarks:
                            for fl in face_results.multi_face_landmarks:
                                puntos = [(lm.x, lm.y) for lm in fl.landmark]
                                xs = [p[0] for p in puntos]
                                ys = [p[1] for p in puntos]
                                detecciones.append(Deteccion(
                                    tipo=DetectorTipo.ROSTRO,
                                    confianza=0.9,
                                    bbox=(min(xs), min(ys), max(xs), max(ys)),
                                    puntos_clave=puntos[:10],
                                ))

                    if self._hands is not None:
                        hands_results = self._hands.process(frame_rgb)
                        if hands_results.multi_hand_landmarks:
                            for hl in hands_results.multi_hand_landmarks:
                                puntos = [(lm.x, lm.y) for lm in hl.landmark]
                                detecciones.append(Deteccion(
                                    tipo=DetectorTipo.MANOS,
                                    confianza=0.8,
                                    bbox=(0, 0, 0, 0),
                                    puntos_clave=puntos,
                                ))
            except Exception as e:
                logger.debug(f"MediaPipe error: {e}")

        return detecciones

    # ── Hilo de procesamiento ────────────────────────────────────

    def _loop(self):
        """Loop principal de inferencia."""
        frame_skip = 0
        while self._running:
            t0 = time.time()

            frame = self._tomar_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            # Rate limiting
            frame_skip += 1
            if frame_skip < int(30 / self.max_fps):
                continue
            frame_skip = 0

            # Procesar
            t_proc = time.time()
            detecciones = self._procesar_frame(frame)
            t_proc_ms = (time.time() - t_proc) * 1000

            # Publicar resultados
            with self._lock:
                self._ultimas_detecciones = detecciones
                self._ultimo_frame_procesado = FrameProcesado(
                    detecciones=detecciones,
                    timestamp_frame=time.time(),
                    tiempo_procesamiento_ms=t_proc_ms,
                    fps_inferencia=self.max_fps,
                )
                self._ultimo_timestamp = time.time()
                self._frames_procesados += 1
                self._tiempo_total_ms += t_proc_ms
                self._fps_reales = self._frames_procesados / max(1, time.time() - t0 + 0.001)

            # Sleep para no saturar CPU
            elapsed = time.time() - t0
            sleep_time = max(0.01, 1.0 / self.max_fps - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def iniciar(self) -> None:
        """Inicia el hilo de procesamiento."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="vision-total")
        self._thread.start()
        logger.info("VisionTotal: hilo de inferencia iniciado")

    def detener(self) -> None:
        """Detiene el hilo de procesamiento."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("VisionTotal: detenido")

    # ── API publica ──────────────────────────────────────────────

    def obtener_detecciones(self, timeout_s: float = 1.0) -> List[Deteccion]:
        """Obtiene las ultimas detecciones.

        Args:
            timeout_s: Tiempo maximo de espera si no hay detecciones.

        Returns:
            Lista de Deteccion.
        """
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            with self._lock:
                if self._ultimas_detecciones:
                    return self._ultimas_detecciones.copy()
            time.sleep(0.05)
        return []

    def hay_persona(self, confianza_min: float = 0.5) -> bool:
        """Detecta si hay alguna persona en el frame."""
        detecciones = self.obtener_detecciones(timeout_s=0.5)
        return any(d.tipo in (DetectorTipo.PERSONAS, DetectorTipo.POSE, DetectorTipo.ROSTRO)
                   and d.confianza >= confianza_min for d in detecciones)

    def obtener_esqueleto(self) -> Optional[List[Tuple[float, float]]]:
        """Obtiene puntos del esqueleto de la persona."""
        detecciones = self.obtener_detecciones(timeout_s=0.5)
        for d in detecciones:
            if d.tipo == DetectorTipo.POSE and d.puntos_clave:
                return d.puntos_clave
        return None

    def obtener_rostro(self) -> Optional[Tuple[float, float, float, float]]:
        """Obtiene bbox del rostro."""
        detecciones = self.obtener_detecciones(timeout_s=0.5)
        for d in detecciones:
            if d.tipo == DetectorTipo.ROSTRO:
                return d.bbox
        return None

    def obtener_stats(self) -> Dict[str, Any]:
        """Retorna estadisticas de rendimiento."""
        with self._lock:
            return {
                "fps_reales": round(self._fps_reales, 1),
                "frames_procesados": self._frames_procesados,
                "tiempo_promedio_ms": round(
                    self._tiempo_total_ms / max(1, self._frames_procesados), 1
                ),
                "ultima_deteccion_hace_s": round(
                    time.time() - self._ultimo_timestamp, 2
                ) if self._ultimo_timestamp > 0 else 0,
                "detectores_activos": {
                    "yolo": _YOLO_AVAILABLE,
                    "mediapipe_holistic": _MP_HOLISTIC_AVAILABLE,
                    "mediapipe_pose": _MP_POSE_AVAILABLE,
                    "mediapipe_face": _MP_FACE_AVAILABLE,
                    "mediapipe_hands": _MP_HANDS_AVAILABLE,
                },
            }


# ── Singleton ────────────────────────────────────────────────────

_vision_instance: Optional[VisionTotal] = None
_vision_lock = threading.Lock()


def obtener_vision() -> VisionTotal:
    """Obtiene la instancia singleton de VisionTotal."""
    global _vision_instance
    if _vision_instance is None:
        with _vision_lock:
            if _vision_instance is None:
                _vision_instance = VisionTotal(max_fps=2)
                _vision_instance.iniciar()
    return _vision_instance


def detener_vision() -> None:
    """Detiene la instancia de VisionTotal."""
    global _vision_instance
    if _vision_instance is not None:
        _vision_instance.detener()
        _vision_instance = None


if __name__ == "__main__":
    print("=== VisionTotal Test ===")
    print(f"OpenCV: {_CV2_AVAILABLE}")
    print(f"MediaPipe: {_MP_AVAILABLE} (holistic={_MP_HOLISTIC_AVAILABLE})")
    print(f"YOLO: {_YOLO_AVAILABLE}")

    vision = obtener_vision()
    stats = vision.obtener_stats()
    for k, v in stats.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for sk, sv in v.items():
                print(f"    {sk}: {sv}")
        else:
            print(f"  {k}: {v}")

    print()
    print("VisionTotal lista para procesar frames.")
    detener_vision()


