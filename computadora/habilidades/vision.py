# Hod — Esplendor. Adaptador de Cámara.
# KliCamara — Captura de frames, detección de movimiento, modo nocturno.

# Dependencia opcional:
#   - opencv-python-headless: para captura y procesamiento de imagen
#   Se eligió *headless* para evitar conflicto Qt con PyQt6.

from __future__ import annotations

import time
from typing import Any

import numpy as np
from loguru import logger

from computadora.nucleo.kli import DispositivoKli, EstadoKli

# Importación opcional de OpenCV
try:
    import cv2
    _CV2_DISPONIBLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    _CV2_DISPONIBLE = False


def _abrir_video_capture(source):
    """Abre un VideoCapture con un backend Windows más seguro si está disponible."""
    if not _CV2_DISPONIBLE:
        return None

    backends: list[int | None] = []
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    backends.append(None)

    for backend in backends:
        cap = None
        try:
            cap = cv2.VideoCapture(source) if backend is None else cv2.VideoCapture(source, backend)
            if cap is not None and cap.isOpened():
                return cap
        except Exception as exc:
            logger.debug(f"Vision: VideoCapture open failed for source={source} backend={backend}: {exc}")
        finally:
            if cap is not None and not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass

    return None


# ═══════════════════════════════════════════════
# KliCamara — Adaptador de Cámara
# ═══════════════════════════════════════════════

class KliCamara(DispositivoKli):
    """Sensor visual de la Computadora.

    Capacidades:
      - Captura de frame desde cámara local (índice configurable)
      - Detección de movimiento, modo nocturno.
    """

    UMBRAL_BAJA_LUZ = 50  # RF-323
    UMBRAL_MOVIMIENTO = 25
    PORCENTAJE_MOVIMIENTO = 2.0

    def __init__(self, indice_camara: int = 0):
        super().__init__(id_kli="camara_local", nombre="Cámara Local")
        self._indice = indice_camara
        self._cap: Any = None
        self._frame_anterior: Any = None
        self._clahe: Any = None
        self._modo_nocturno_auto: bool = False  # RF-324: auto-CLAHE activo

    @staticmethod
    def _abrir_video_capture(source):
        return _abrir_video_capture(source)

    def conectar(self) -> bool:
        if not _CV2_DISPONIBLE:
            logger.error("OpenCV no disponible — instalar opencv-python-headless")
            self._estado = EstadoKli.ERROR
            return False
        try:
            indices = [self._indice] + [i for i in range(4) if i != self._indice]
            for indice_prueba in indices:
                cap = _abrir_video_capture(indice_prueba)
                if cap is not None and cap.isOpened():
                    self._cap = cap
                    self._indice = indice_prueba
                    self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    self._estado = EstadoKli.CONECTADO
                    logger.info(f"KliCamara conectada (índice={self._indice})")
                    return True
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
            logger.error(f"No se pudo abrir ninguna cámara local en índices {indices}")
            self._estado = EstadoKli.ERROR
            return False
        except Exception as e:
            logger.error(f"Error conectando cámara: {e}")
            self._estado = EstadoKli.ERROR
            return False

    def capturar_frame(self) -> Any | None:
        """Captura un frame BGR válido y conecta la cámara si aún no estaba abierta.
        
        FP-140 AUDIT: Agregado retry logic para evitar desconexiones silenciosas.
        Si la captura falla, intenta reconectar hasta 3 veces antes de fallar.
        """
        max_intentos = 3
        for intento in range(max_intentos):
            if self._cap is None or not self._cap.isOpened():
                if not self.conectar():
                    return None
            
            ret, frame = self._cap.read()
            if ret and frame is not None:
                logger.debug("📹 Captura de frame exitosa en intento %d", intento + 1)
                return frame
            
            # Si falla, desconectar y reintentar
            if intento < max_intentos - 1:
                logger.debug(f"Captura falló (intento {intento+1}/{max_intentos}), reconectando cámara...")
                self.desconectar()
            else:
                logger.warning(f"Captura falló después de {max_intentos} intentos")
        
        return None

    def desconectar(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception as e:
                logger.debug("Error liberando cámara: %s", e)
            self._cap = None
        self._frame_anterior = None
        self._estado = EstadoKli.DESCONECTADO
        logger.info("📹 Cámara local desconectada")

    def leer_ohr(self) -> dict[str, Any]:
        """Captura un frame y detecta movimiento."""
        if self._cap is None or not self._cap.isOpened():
            return {"error": "Cámara no conectada"}

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return {"error": "No se pudo capturar frame"}

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # RF-323: Medir brillo medio del frame crudo
        brillo_medio = float(np.mean(gris))

        # RF-324: Auto-CLAHE si baja luminosidad
        # RF-326: Guardar frame crudo para diff (evitar falsos positivos en transición CLAHE)
        gris_raw = gris
        nocturno_prev = self._modo_nocturno_auto
        if brillo_medio < self.UMBRAL_BAJA_LUZ:
            if self._clahe is not None:
                gris = self._clahe.apply(gris)
            else:
                gris = cv2.equalizeHist(gris)
            if not self._modo_nocturno_auto:
                self._modo_nocturno_auto = True
                logger.info("👁️ Visión nocturna AUTO activada (brillo=%.1f)", brillo_medio)
        elif self._modo_nocturno_auto and brillo_medio > self.UMBRAL_BAJA_LUZ + 15:
            self._modo_nocturno_auto = False
            logger.info("☀️ Visión nocturna AUTO desactivada (brillo=%.1f)", brillo_medio)

        # Detección de movimiento — siempre sobre frame crudo (consistencia)
        movimiento = False
        porcentaje = 0.0
        if self._frame_anterior is not None:
            diff = cv2.absdiff(self._frame_anterior, gris_raw)
            pixeles_cambio = np.count_nonzero(diff > self.UMBRAL_MOVIMIENTO)
            total_pixeles = gris_raw.shape[0] * gris_raw.shape[1]
            porcentaje = (pixeles_cambio / total_pixeles) * 100
            movimiento = porcentaje > self.PORCENTAJE_MOVIMIENTO

        self._frame_anterior = gris_raw  # RF-326: siempre frame crudo

        if movimiento:
            logger.warning(
                "👁️ Movimiento detectado: %.2f%% de cambio en cámara local (brillo=%.1f)",
                porcentaje,
                brillo_medio,
            )

        return {
            "tipo": "frame",
            "ts": time.time(),
            "movimiento": movimiento,
            "porcentaje_cambio": round(porcentaje, 2),
            "brillo_medio": round(brillo_medio, 1),
            "nocturno_auto": self._modo_nocturno_auto,
            "resolucion": f"{frame.shape[1]}x{frame.shape[0]}",
        }

    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Comandos: capturar, nocturno_on, nocturno_off, estado."""
        if comando == "capturar":
            return self.leer_ohr()

        if comando == "nocturno":
            return self._aplicar_nocturno()

        if comando == "estado":
            abierta = self._cap is not None and self._cap.isOpened()
            return {"abierta": abierta, "estado": self._estado.name}

        return {"error": f"Comando desconocido: {comando!r}"}

    def _aplicar_nocturno(self) -> dict[str, Any]:
        """Captura frame con CLAHE para baja luminosidad."""
        if self._cap is None or not self._cap.isOpened():
            return {"error": "Cámara no conectada"}

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return {"error": "No se pudo capturar frame"}

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self._clahe is not None:
            mejorado = self._clahe.apply(gris)
        else:
            mejorado = cv2.equalizeHist(gris)

        brillo_medio = float(np.mean(mejorado))
        return {
            "tipo": "frame_nocturno",
            "ts": time.time(),
            "brillo_medio": round(brillo_medio, 1),
            "clahe": self._clahe is not None,
        }


# ═══════════════════════════════════════════════
# RF-259 KliCamaraIP — Adaptador RTSP
# ═══════════════════════════════════════════════

import ipaddress


def _es_ip_privada(ip_str: str) -> bool:
    """Valida que una IP sea privada (anti-SSRF)."""
    try:
        return ipaddress.ip_address(ip_str).is_private
    except ValueError:
        return False


class KliCamaraIP(DispositivoKli):
    """RF-259 עין הגולם - Cámara IP via RTSP.

    Hereda capacidades de KliCamara (movimiento, CLAHE)
    pero conecta via URL RTSP en vez de índice local.
    Solo acepta IPs privadas (anti-SSRF).
    """

    UMBRAL_MOVIMIENTO = 25
    PORCENTAJE_MOVIMIENTO = 2.0

    def __init__(self, url_rtsp: str):
        super().__init__(id_kli="camara_ip", nombre="Cámara IP")
        self._url = url_rtsp
        self._cap: Any = None
        self._frame_anterior: Any = None
        self._clahe: Any = None

    def conectar(self) -> bool:
        if not _CV2_DISPONIBLE:
            logger.error("OpenCV no disponible")
            self._estado = EstadoKli.ERROR
            return False
        # Anti-SSRF: solo IPs privadas
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self._url)
            host = parsed.hostname or ""
            if not _es_ip_privada(host):
                logger.error(f"RF-259: IP no privada rechazada: {host}")
                self._estado = EstadoKli.ERROR
                return False
        except Exception as e:
            logger.debug("RF-259: error parseando URL: %s", e)
            self._estado = EstadoKli.ERROR
            return False
        try:
            self._cap = cv2.VideoCapture(self._url)
            if not self._cap.isOpened():
                self._estado = EstadoKli.ERROR
                return False
            self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            self._estado = EstadoKli.CONECTADO
            logger.info(f"KliCamaraIP conectada: {self._url}")
            return True
        except Exception as e:
            logger.error(f"Error conectando cámara IP: {e}")
            self._estado = EstadoKli.ERROR
            return False

    def desconectar(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception as e:
                logger.debug("Error liberando cámara IP: %s", e)
            self._cap = None
        self._frame_anterior = None
        self._estado = EstadoKli.DESCONECTADO

    def leer_ohr(self) -> dict[str, Any]:
        """Captura un frame y detecta movimiento."""
        if self._cap is None or not self._cap.isOpened():
            return {"error": "Cámara IP no conectada"}
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return {"error": "No se pudo capturar frame"}
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        movimiento = False
        porcentaje = 0.0
        if self._frame_anterior is not None:
            diff = cv2.absdiff(self._frame_anterior, gris)
            pixeles_cambio = np.count_nonzero(diff > self.UMBRAL_MOVIMIENTO)
            total_pixeles = gris.shape[0] * gris.shape[1]
            porcentaje = (pixeles_cambio / total_pixeles) * 100
            movimiento = porcentaje > self.PORCENTAJE_MOVIMIENTO
        self._frame_anterior = gris
        return {
            "tipo": "frame",
            "ts": time.time(),
            "movimiento": movimiento,
            "porcentaje_cambio": round(porcentaje, 2),
            "resolucion": f"{frame.shape[1]}x{frame.shape[0]}",
            "fuente": "rtsp",
        }

    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        if comando == "capturar":
            return self.leer_ohr()
        if comando == "estado":
            abierta = self._cap is not None and self._cap.isOpened()
            return {"abierta": abierta, "estado": self._estado.name, "url": self._url}
        return {"error": f"Comando desconocido: {comando!r}"}


