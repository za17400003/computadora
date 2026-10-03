"""
הכרת פנים (Hakarat Panim) — Reconocimiento Facial.
RF-249: Detecta e identifica rostros usando face_recognition (dlib, CPU).
Auto-enrolla al propietario cuando la voz ya está verificada.

Dependencia opcional:
  - face_recognition: reconocimiento facial basado en dlib (CPU)
  Se instala con: pip install face_recognition
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

# Importación opcional
try:
    import face_recognition as fr
    _FR_DISPONIBLE = True
    
    # Verificar soporte CUDA en dlib
    try:
        import dlib
        _DLIB_CUDA_DISPONIBLE = dlib.DLIB_USE_CUDA
    except ImportError:
        _DLIB_CUDA_DISPONIBLE = False
        
except ImportError:
    fr = None  # type: ignore[assignment]
    _FR_DISPONIBLE = False
    _DLIB_CUDA_DISPONIBLE = False

# WI-285: Integración de LogicaTransparente para auditoría matemática de reconocimiento facial
try:
    from computadora.cerebro.matematicas import registrar_facial
    _MATEMATICAS_DISPONIBLE = True
except ImportError:
    _MATEMATICAS_DISPONIBLE = False

# Auditoría de verdad: registra cada verificación de propietario para detectar
# contradicciones (ver computadora/verdad/). No bloquea el reconocimiento —
# usa el mismo umbral que _UMBRAL_PROPIETARIO, es una capa de auditoría, no una
# segunda puerta de seguridad independiente.
try:
    from computadora.verdad.verificador_realidad import VerificadorRealidad
    from computadora.verdad.verificador_coherencia_interna import VerificadorCoherenciaInterna
    _VERDAD_DISPONIBLE = True
except ImportError:
    _VERDAD_DISPONIBLE = False

# Ruta de perfiles faciales
_DATOS_DIR = Path(__file__).resolve().parents[2] / "datos"
_PERFIL_ROSTRO_PROPIETARIO = _DATOS_DIR / "owner_face_profile.json"
_PERFILES_CONOCIDOS = _DATOS_DIR / "rostros_conocidos.json"

# Umbral de distancia facial (menor = más estricto). 0.6 es el default de face_recognition.
# Se relajan ligeramente los umbrales para mejorar reconocimiento en condiciones reales.
_UMBRAL_PROPIETARIO = 0.50
_UMBRAL_CONOCIDO = 0.65


class ReconocedorRostro(QObject):
    """Detecta e identifica rostros a partir de frames BGR (numpy array).

    Señales:
        propietario_detectado: emitida cuando se reconoce al propietario
        persona_detectada(str): emitida con el nombre de una persona conocida
        rostro_desconocido: emitida cuando hay un rostro no identificado
    """

    propietario_detectado = pyqtSignal()
    persona_detectada = pyqtSignal(str)
    rostro_desconocido = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._encoding_propietario: np.ndarray | None = None
        self._nombre_propietario: str | None = None
        self._conocidos: dict[str, np.ndarray] = {}
        self._ultimo_check: float = 0.0
        self._intervalo_check: float = 2.0  # segundos entre checks
        self._cargar_perfiles()

        self._verdad: VerificadorRealidad | None = None
        if _VERDAD_DISPONIBLE:
            self._verdad = VerificadorRealidad()
            coherencia = VerificadorCoherenciaInterna()
            chequeo = coherencia.verificar_encoding_facial(self._nombre_propietario or "propietario")
            if chequeo.estado == "FALSO":
                logger.warning(f"Perfil facial del propietario inconsistente: {chequeo.evidencia}")

    @staticmethod
    def disponible() -> bool:
        return _FR_DISPONIBLE

    def _cargar_perfiles(self) -> None:
        """Carga perfiles faciales persistidos en JSON."""
        if not _FR_DISPONIBLE:
            return
        if _PERFIL_ROSTRO_PROPIETARIO.exists():
            try:
                data = json.loads(_PERFIL_ROSTRO_PROPIETARIO.read_text("utf-8"))
                self._encoding_propietario = np.array(data["encoding"], dtype=np.float64)
                self._nombre_propietario = data.get("nombre")
                logger.info(f"Perfil facial del propietario cargado{' (' + self._nombre_propietario + ')' if self._nombre_propietario else ''}")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Error cargando perfil facial propietario: {e}")

        if _PERFILES_CONOCIDOS.exists():
            try:
                data = json.loads(_PERFILES_CONOCIDOS.read_text("utf-8"))
                for nombre, enc in data.items():
                    self._conocidos[nombre] = np.array(enc, dtype=np.float64)
                logger.info(f"Cargados {len(self._conocidos)} perfiles faciales conocidos")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error cargando perfiles faciales conocidos: {e}")

    def _guardar_perfil_propietario(self) -> None:
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        if self._encoding_propietario is not None:
            data = {"encoding": self._encoding_propietario.tolist()}
            if self._nombre_propietario:
                data["nombre"] = self._nombre_propietario
            _PERFIL_ROSTRO_PROPIETARIO.write_text(
                json.dumps(data, indent=2),
                encoding="utf-8",
            )
            logger.info("Perfil facial del propietario guardado")

    def _guardar_conocidos(self) -> None:
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        data = {n: e.tolist() for n, e in self._conocidos.items()}
        _PERFILES_CONOCIDOS.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def enrollar_propietario(self, frame_bgr: np.ndarray, nombre: str | None = None) -> bool:
        """Registra el rostro del propietario desde un frame BGR.

        Debe llamarse solo cuando la identidad del hablante ya fue verificada por voz.
        Retorna True si se logró detectar y registrar un rostro.
        """
        if not _FR_DISPONIBLE:
            logger.warning("face_recognition no disponible, no se puede enrollar")
            return False
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        encodings = fr.face_encodings(rgb)
        if not encodings:
            logger.debug("No se detectó rostro para enrollar propietario")
            return False
        self._encoding_propietario = encodings[0]
        if nombre:
            self._nombre_propietario = nombre
        self._guardar_perfil_propietario()
        logger.info(f"Rostro del propietario enrollado{' (' + nombre + ')' if nombre else ''}")
        return True

    def enrollar_conocido(self, nombre: str, frame_bgr: np.ndarray) -> bool:
        """Registra el rostro de una persona conocida."""
        if not _FR_DISPONIBLE:
            return False
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        encodings = fr.face_encodings(rgb)
        if not encodings:
            return False
        self._conocidos[nombre] = encodings[0]
        self._guardar_conocidos()
        logger.info(f"Rostro de '{nombre}' enrollado")
        return True

    def analizar_frame(self, frame_bgr: np.ndarray) -> dict[str, Any]:
        """Analiza un frame buscando rostros conocidos.

        Respeta el intervalo mínimo entre checks para no saturar CPU.
        Retorna dict con resultado: propietario/conocido/desconocido/sin_rostro/no_disponible.
        """
        # RF-49: Feature flag para desactivar reconocimiento facial
        try:
            from computadora.nucleo.feature_flags import obtener_flag
            if not obtener_flag("reconocimiento_facial"):
                return {"resultado": "desactivado", "razon": "RF-49 pausado"}
        except Exception as e:
            logger.debug(f"Feature flag check error (no crítico): {e}")
        
        if not _FR_DISPONIBLE:
            return {"resultado": "no_disponible"}

        ahora = time.monotonic()
        if (ahora - self._ultimo_check) < self._intervalo_check:
            return {"resultado": "cooldown"}
        self._ultimo_check = ahora

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Usar CNN si CUDA disponible, HOG si no (CPU)
        modelo = "cnn" if _DLIB_CUDA_DISPONIBLE else "hog"
        logger.debug(f"Usando modelo facial: {modelo} (CUDA: {_DLIB_CUDA_DISPONIBLE})")
        
        locations = fr.face_locations(rgb, model=modelo)
        if not locations:
            return {"resultado": "sin_rostro", "locations": []}

        encodings = fr.face_encodings(rgb, locations)
        if not encodings:
            return {"resultado": "sin_rostro", "locations": locations}

        resultados = []
        for i, enc in enumerate(encodings):
            resultado = {"location": locations[i], "resultado": "desconocido"}
            
            # Check propietario
            if self._encoding_propietario is not None:
                dist = float(fr.face_distance([self._encoding_propietario], enc)[0])
                
                # WI-285: Registrar cálculo facial en LogicaTransparente
                if _MATEMATICAS_DISPONIBLE:
                    confianza = 1.0 - min(dist, 1.0)  # Convertir distancia a confianza (0-1)
                    try:
                        registrar_facial(
                            distancia=dist,
                            pitch=1.0,  # TODO: extraer del análisis de audio futuro
                            lighting="normal",  # TODO: estimar del frame actual
                            confianza=confianza
                        )
                    except Exception as e:
                        logger.debug(f"Error registrando facial (propietario): {e}")
                
                if self._verdad is not None:
                    veredicto = self._verdad.verificar_usuario_propietario(
                        self._nombre_propietario or "propietario", dist
                    )
                    if veredicto.estado == "FALSO" and dist <= _UMBRAL_PROPIETARIO:
                        logger.warning(
                            f"Auditoría de verdad discrepa del umbral de rostro.py "
                            f"(dist={dist:.3f}, veredicto={veredicto.estado}) — revisar UMBRAL_DISTANCIA_PROPIETARIO"
                        )

                if dist <= _UMBRAL_PROPIETARIO:
                    resultado = {"location": locations[i], "resultado": "propietario", "distancia": dist}
                    if self._nombre_propietario:
                        resultado["nombre"] = self._nombre_propietario
                    self.propietario_detectado.emit()
                    resultados.append(resultado)
                    continue

            # Check conocidos
            if self._conocidos:
                nombres = list(self._conocidos.keys())
                conocidos_enc = [self._conocidos[n] for n in nombres]
                dists = fr.face_distance(conocidos_enc, enc)
                min_idx = int(np.argmin(dists))
                dist_conocido = float(dists[min_idx])
                
                # WI-285: Registrar cálculo facial en LogicaTransparente
                if _MATEMATICAS_DISPONIBLE:
                    confianza_conocido = 1.0 - min(dist_conocido, 1.0)
                    try:
                        registrar_facial(
                            distancia=dist_conocido,
                            pitch=1.0,  # TODO
                            lighting="normal",  # TODO
                            confianza=confianza_conocido
                        )
                    except Exception as e:
                        logger.debug(f"Error registrando facial (conocido): {e}")
                
                if dists[min_idx] <= _UMBRAL_CONOCIDO:
                    nombre = nombres[min_idx]
                    resultado = {"location": locations[i], "resultado": "conocido", "nombre": nombre, "distancia": dist_conocido}
                    self.persona_detectada.emit(nombre)
                    resultados.append(resultado)
                    continue
            
            # Desconocido
            self.rostro_desconocido.emit()
            resultados.append(resultado)

        return {"resultado": "multiple" if len(resultados) > 1 else resultados[0]["resultado"] if resultados else "sin_rostro", "rostros": resultados, "locations": locations}

    def identificar_rostros(self, frame_bgr: np.ndarray) -> list[dict[str, Any]]:
        """Retorna una lista de rostros identificados en el frame."""
        resultado = self.analizar_frame(frame_bgr)
        if resultado.get("resultado") in ("sin_rostro", "no_disponible", "cooldown"):
            return []

        rostros = resultado.get("rostros")
        if isinstance(rostros, list):
            return rostros

        return [resultado]

    @property
    def propietario_enrollado(self) -> bool:
        return self._encoding_propietario is not None


