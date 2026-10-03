"""
יסוד (Yesod) — Fundamento de Extensión.
Marco Kli HaHarjavá — Device Extension Framework.

Un Kli (כלי, "recipiente") es cualquier dispositivo externo que Computadora
puede adoptar como extensión sensorial. Cada Kli recibe Ohr (luz/datos)
del mundo físico y ejecuta Pekudot (comandos) de Computadora.

Arquitectura:
  - DispositivoKli (ABC): contrato que todo adaptador debe cumplir
  - SensorOhr (Protocol): duck-typing para lectura sin herencia
  - GestorKelim: singleton que registra, conecta y monitorea dispositivos
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable

from loguru import logger

try:
    from PyQt6.QtCore import QObject, pyqtSignal
    _QT_DISPONIBLE = True
except ImportError:
    QObject = object
    _QT_DISPONIBLE = False


# ═══════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════

class EstadoKli(Enum):
    """Estado del ciclo de vida de un Kli."""
    DESCONECTADO = auto()
    CONECTANDO = auto()
    CONECTADO = auto()
    ERROR = auto()


# ═══════════════════════════════════════════════
# PROTOCOL — SensorOhr (duck-typing)
# ═══════════════════════════════════════════════

@runtime_checkable
class SensorOhr(Protocol):
    """Protocol para cualquier objeto que pueda leer datos sensoriales.
    No requiere herencia, solo implementar leer_ohr()."""

    def leer_ohr(self) -> dict[str, Any]:
        """Retorna lectura sensorial como dict."""
        ...


# ═══════════════════════════════════════════════
# ABC — DispositivoKli
# ═══════════════════════════════════════════════

class DispositivoKli(ABC):
    """Contrato base para todo dispositivo-extensión de Computadora.

    Cada subclase DEBE implementar los 5 métodos abstractos.
    El id_kli debe ser único por instancia.
    """

    def __init__(self, id_kli: str, nombre: str):
        self.id_kli = id_kli
        self.nombre = nombre
        self._estado = EstadoKli.DESCONECTADO

    @property
    def estado(self) -> EstadoKli:
        return self._estado

    @abstractmethod
    def conectar(self) -> bool:
        """Intenta conexión. Retorna True si exitoso."""
        ...

    @abstractmethod
    def desconectar(self) -> None:
        """Libera recursos y desconecta."""
        ...

    @abstractmethod
    def leer_ohr(self) -> dict[str, Any]:
        """Lee datos sensoriales del dispositivo."""
        ...

    @abstractmethod
    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Envía un comando al dispositivo. Retorna resultado."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id_kli!r} estado={self._estado.name}>"


# ═══════════════════════════════════════════════
# GESTOR KELIM — Singleton
# ═══════════════════════════════════════════════

class _SeñalesKli(QObject):
    """Señales Qt para eventos de dispositivos."""
    if _QT_DISPONIBLE:
        kli_conectado = pyqtSignal(str)        # id_kli
        kli_desconectado = pyqtSignal(str)     # id_kli
        ohr_recibido = pyqtSignal(str, dict)   # id_kli, datos
        kli_error = pyqtSignal(str, str)       # id_kli, mensaje


class GestorKelim:
    """Registro central de dispositivos-extensión.

    Singleton: usar GestorKelim.instancia() para obtener la instancia única.

    Responsabilidades:
      - Registrar/desregistrar Kelim
      - Ciclo de vida: descubrir → conectar → leer → desconectar
      - Health check periódico
      - Emitir señales Qt en eventos
    """

    _instancia: GestorKelim | None = None

    @classmethod
    def instancia(cls) -> GestorKelim:
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    @classmethod
    def _reset(cls) -> None:
        """Solo para tests."""
        cls._instancia = None

    def __init__(self):
        if GestorKelim._instancia is not None:
            raise RuntimeError("Usar GestorKelim.instancia()")
        self._lock = threading.Lock()
        self._kelim: dict[str, DispositivoKli] = {}
        self._señales = _SeñalesKli() if _QT_DISPONIBLE else None
        self._log_eventos: list[dict[str, Any]] = []

    @property
    def señales(self) -> _SeñalesKli | None:
        return self._señales

    @property
    def log_eventos(self) -> list[dict[str, Any]]:
        return list(self._log_eventos)

    def registrar(self, kli: DispositivoKli) -> None:
        """Registra un Kli en el gestor."""
        with self._lock:
            if kli.id_kli in self._kelim:
                logger.warning(f"Kli {kli.id_kli!r} ya registrado, se reemplaza")
            self._kelim[kli.id_kli] = kli
        logger.info(f"Kli registrado: {kli}")

    def desregistrar(self, id_kli: str) -> None:
        """Desregistra y desconecta un Kli."""
        with self._lock:
            kli = self._kelim.pop(id_kli, None)
        if kli is None:
            return
        if kli.estado == EstadoKli.CONECTADO:
            try:
                kli.desconectar()
            except Exception as e:
                logger.error(f"Error desconectando {id_kli}: {e}")
        self._emitir("kli_desconectado", id_kli)
        logger.info(f"Kli desregistrado: {id_kli}")

    def conectar(self, id_kli: str) -> bool:
        """Conecta un Kli registrado."""
        kli = self._kelim.get(id_kli)
        if kli is None:
            logger.error(f"Kli {id_kli!r} no registrado")
            return False
        try:
            ok = kli.conectar()
            if ok:
                self._emitir("kli_conectado", id_kli)
                self._registrar_evento(id_kli, "conectado")
            return ok
        except Exception as e:
            kli._estado = EstadoKli.ERROR
            self._emitir("kli_error", id_kli, str(e))
            self._registrar_evento(id_kli, "error", str(e))
            logger.error(f"Error conectando {id_kli}: {e}")
            return False

    def desconectar(self, id_kli: str) -> None:
        """Desconecta un Kli."""
        kli = self._kelim.get(id_kli)
        if kli is None:
            return
        try:
            kli.desconectar()
            self._emitir("kli_desconectado", id_kli)
            self._registrar_evento(id_kli, "desconectado")
        except Exception as e:
            logger.error(f"Error desconectando {id_kli}: {e}")

    def leer(self, id_kli: str) -> dict[str, Any]:
        """Lee datos de un Kli conectado."""
        kli = self._kelim.get(id_kli)
        if kli is None:
            return {"error": f"Kli {id_kli!r} no registrado"}
        if kli.estado != EstadoKli.CONECTADO:
            return {"error": f"Kli {id_kli!r} no conectado (estado: {kli.estado.name})"}
        try:
            datos = kli.leer_ohr()
            self._emitir("ohr_recibido", id_kli, datos)
            return datos
        except Exception as e:
            self._emitir("kli_error", id_kli, str(e))
            return {"error": str(e)}

    def enviar(self, id_kli: str, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Envía comando a un Kli conectado."""
        kli = self._kelim.get(id_kli)
        if kli is None:
            return {"error": f"Kli {id_kli!r} no registrado"}
        if kli.estado != EstadoKli.CONECTADO:
            return {"error": f"Kli {id_kli!r} no conectado"}
        try:
            return kli.enviar_pekuda(comando, **kwargs)
        except Exception as e:
            self._emitir("kli_error", id_kli, str(e))
            return {"error": str(e)}

    def leer_frame_camera(self, id_kli: str = "camara_local") -> Any | None:
        """Lee el frame actual de una cámara. Especial para dev tools.
        
        FP-152: Permite que camera_dev_tool acceda al frame sin conflicto de device exclusiva.
        Retorna ndarray BGR o None si no disponible.
        """
        kli = self._kelim.get(id_kli)
        if kli is None:
            return None
        # Solo funciona con KliCamara y derivados
        try:
            if hasattr(kli, 'capturar_frame'):
                frame = kli.capturar_frame()  # type: ignore
                return frame
        except Exception as e:
            logger.debug(f"Error leyendo frame de {id_kli}: {e}")
        return None

    def listar(self) -> list[dict[str, Any]]:
        """Lista todos los Kelim registrados con su estado."""
        return [
            {"id": k.id_kli, "nombre": k.nombre, "estado": k.estado.name, "instancia": k}
            for k in self._kelim.values()
        ]

    def health_check(self) -> dict[str, str]:
        """Verifica estado de todos los Kelim conectados."""
        resultado: dict[str, str] = {}
        for id_kli, kli in self._kelim.items():
            if kli.estado == EstadoKli.CONECTADO:
                try:
                    kli.leer_ohr()
                    resultado[id_kli] = "OK"
                except Exception as e:
                    resultado[id_kli] = f"ERROR: {e}"
                    kli._estado = EstadoKli.ERROR
                    self._emitir("kli_error", id_kli, str(e))
            else:
                resultado[id_kli] = kli.estado.name
        return resultado

    def descubrir_observadores(self) -> list[str]:
        """RF-258 Ayin HaComputadora — Auto-discovery de dispositivos de observación.

        Busca: (a) cámaras locales USB (cv2 índice 0-4),
               (b) cámaras IP en red local (RTSP probe 554/8554).
        Sin Gevurá — la visión es libre.
        
        CRÍTICO: Verifica feature flag ANTES de auto-conectar.
        Si RF-49 (reconocimiento_facial) está desactivado, NO descubre/conecta cámaras.
        """
        encontrados: list[str] = []
        
        # ⚠️ CRÍTICO: Feature flag check ANTES de cualquier operación
        try:
            from computadora.nucleo.feature_flags import obtener_flag
            if not obtener_flag("reconocimiento_facial"):
                logger.info("RF-258: Discovery de observadores OMITIDO — RF-49 (reconocimiento_facial) desactivado")
                return []  # ← NO descubrir si facial recognition está OFF
        except Exception as e:
            logger.debug(f"Feature flag check error (continuando): {e}")
        
        # --- Cámaras locales USB ---
        try:
            import cv2 as _cv2
            found_primary_camera = False
            for idx in range(5):
                id_kli = f"camara_local_{idx}" if idx > 0 else "camara_local"
                if id_kli in self._kelim:
                    if self._kelim[id_kli].estado == EstadoKli.CONECTADO:
                        encontrados.append(id_kli)
                        if id_kli == "camara_local":
                            found_primary_camera = True
                    elif self._kelim[id_kli].estado == EstadoKli.DESCONECTADO:
                        # FP-139: Intentar reconectar dispositivos descubiertos
                        if self.conectar(id_kli):
                            encontrados.append(id_kli)
                            logger.info(f"RF-260: {id_kli} reconectado al boot")
                            if id_kli == "camara_local":
                                found_primary_camera = True
                    if found_primary_camera:
                        break
                    continue
                from computadora.habilidades.vision import KliCamara
                cap = KliCamara._abrir_video_capture(idx)
                if cap is None:
                    continue

                try:
                    cap.release()
                except Exception:
                    pass

                cam = KliCamara(indice_camara=idx)
                if idx > 0:
                    cam.id_kli = id_kli
                    cam.nombre = f"Cámara Local {idx}"
                self.registrar(cam)
                # FP-139: Auto-conectar inmediatamente después de registrar
                if self.conectar(id_kli):
                    encontrados.append(id_kli)
                    logger.info(f"RF-260: {id_kli} descubierto y conectado al boot")
                    if id_kli == "camara_local":
                        found_primary_camera = True
                else:
                    logger.warning(f"RF-260: {id_kli} descubierto pero NO se pudo conectar")
                if found_primary_camera:
                    break
        except ImportError:
            logger.warning("RF-258: OpenCV no disponible — discovery de cámaras locales omitido")
        except Exception as e:
            logger.debug(f"RF-258: Error en discovery cámaras locales: {e}")

        # --- Cámaras IP en red local (RTSP probe) ---
        try:
            from computadora.habilidades.vision import KliCamaraIP
            from computadora.habilidades.red import _arp_scan
            dispositivos = _arp_scan(timeout=2)
            for dev in dispositivos:
                ip = dev.get("ip", "")
                if not ip:
                    continue
                for puerto in (554, 8554):
                    id_kli = f"camara_ip_{ip}_{puerto}"
                    if id_kli in self._kelim:
                        if self._kelim[id_kli].estado == EstadoKli.CONECTADO:
                            encontrados.append(id_kli)
                        continue
                    url = f"rtsp://{ip}:{puerto}/stream"
                    cam_ip = KliCamaraIP(url_rtsp=url)
                    cam_ip.id_kli = id_kli
                    cam_ip.nombre = f"Cámara IP {ip}:{puerto}"
                    self.registrar(cam_ip)
                    if self.conectar(id_kli):
                        encontrados.append(id_kli)
                        break  # un puerto basta por IP
                    else:
                        self.desregistrar(id_kli)
        except ImportError:
            logger.debug("RF-258: Módulos de red/visión no disponibles para discovery IP")
        except Exception as e:
            logger.debug(f"RF-258: Error en discovery cámaras IP: {e}")

        if encontrados:
            logger.info(f"RF-258 Ayin HaComputadora: {len(encontrados)} observador(es) encontrado(s): {encontrados}")
        else:
            logger.info("RF-258 Ayin HaComputadora: Ningún dispositivo de observación encontrado")
        return encontrados

    def obtener_observadores(self) -> list[str]:
        """Retorna IDs de Kelim conectados que son observadores (cámaras)."""
        return [
            id_kli for id_kli, kli in self._kelim.items()
            if kli.estado == EstadoKli.CONECTADO
            and ("camara" in id_kli or "vision" in id_kli)
        ]

    def desconectar_todos(self) -> None:
        """Desconecta todos los Kelim. Llamar al cerrar Computadora."""
        for id_kli in list(self._kelim):
            self.desconectar(id_kli)

    def _emitir(self, señal: str, id_kli: str, extra: Any = None) -> None:
        if self._señales is None or not _QT_DISPONIBLE:
            return
        sig = getattr(self._señales, señal, None)
        if sig is None:
            return
        try:
            if extra is not None:
                sig.emit(id_kli, extra)
            else:
                sig.emit(id_kli)
        except Exception as e:
            logger.debug("Error emitiendo señal: %s", e)

    def _registrar_evento(self, id_kli: str, tipo: str, detalle: str = "") -> None:
        self._log_eventos.append({
            "ts": time.time(),
            "kli": id_kli,
            "tipo": tipo,
            "detalle": detalle,
        })


