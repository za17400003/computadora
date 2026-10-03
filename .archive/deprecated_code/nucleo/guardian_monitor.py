"""
GUARDIAN MONITOR — Scheduling + Auto-Activation + Persistent Logging
═════════════════════════════════════════════════════════════════════

Implementa:
- Scheduling por hora programable
- Auto-activación cuando usuario no está detectado (cámara + voz)
- Persistent logging de detecciones a disco
- Verificación de intrusiones
"""

import time
import json
import threading
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable
import os

logger = logging.getLogger(__name__)


class GuardianMonitor:
    """Monitor de Guardian con scheduling, auto-activación y logging persistente."""
    
    def __init__(self, config_path: str = "datos/guardian_config.json", cerebro_ref=None):
        """
        Args:
            config_path: Ruta a guardian_config.json
            cerebro_ref: Referencia a CerebroComputadora para activar modo_guardiana
        """
        self.config_path = Path(config_path)
        self.cerebro_ref = cerebro_ref
        self._config = self._cargar_config()
        
        # Estado de Guardian
        self._guardiana_activa = False
        self._ultima_deteccion_usuario_ts = time.time()  # Cuando fue última detección (rostro/voz)
        self._thread_monitor = None
        self._corriendo = False
        self._lock = threading.Lock()
        
        # Callbacks opcionales
        self._on_activar = None
        self._on_desactivar = None
        
        # Crear directorios necesarios
        self._crear_directorios()
        
    def _cargar_config(self) -> Dict:
        """Carga configuración desde JSON."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando guardian_config.json: {e}")
        
        # Config por defecto
        return {
            "enabled": True,
            "schedule": {"start_hour": 22, "start_minute": 0, "end_hour": 8, "end_minute": 0},
            "auto_activation": {"enabled": True, "absence_timeout_minutes": 30},
            "persistent_logging": {"enabled": True, "log_file": "datos/guardian_detections.jsonl"},
            "monitoring": {"camera_enabled": True, "audio_enabled": True, "check_interval_seconds": 60}
        }
    
    def guardar_config(self) -> bool:
        """Guarda configuración actual a JSON."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Guardian config guardada: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando guardian_config.json: {e}")
            return False
    
    def _crear_directorios(self):
        """Crea directorios necesarios para logging."""
        dirs = [
            Path("datos"),
            Path("datos/guardian_snapshots")
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _en_horario_guardian(self) -> bool:
        """Verifica si estamos dentro del horario programado de Guardian."""
        if not self._config.get("schedule"):
            return False
        
        sched = self._config["schedule"]
        start_h = sched.get("start_hour", 22)
        start_m = sched.get("start_minute", 0)
        end_h = sched.get("end_hour", 8)
        end_m = sched.get("end_minute", 0)
        
        ahora = datetime.now()
        hora_actual = ahora.hour + ahora.minute / 60.0
        start_hm = start_h + start_m / 60.0
        end_hm = end_h + end_m / 60.0
        
        # Si start > end (ej: 22:00-08:00 = overnight)
        if start_hm > end_hm:
            return hora_actual >= start_hm or hora_actual < end_hm
        else:
            return start_hm <= hora_actual < end_hm
    
    def registrar_deteccion_usuario(self):
        """Registra que se detectó usuario (rostro/voz activa). Resetea contador de ausencia."""
        with self._lock:
            self._ultima_deteccion_usuario_ts = time.time()
            logger.debug("🔔 Detección de usuario registrada — contador de ausencia reseteado")
    
    def _minutos_sin_detectar_usuario(self) -> float:
        """Retorna minutos desde última detección de usuario."""
        return (time.time() - self._ultima_deteccion_usuario_ts) / 60.0
    
    def activar_guardiana(self):
        """Activa modo Guardian."""
        with self._lock:
            if self._guardiana_activa:
                return
            
            self._guardiana_activa = True
            
            # Activar en cerebro
            if self.cerebro_ref:
                self.cerebro_ref._modo_guardiana = True
            
            logger.info("🛡️ GUARDIAN ACTIVADO — Vigilancia persistente iniciada")
            
            # Registrar evento
            self._registrar_evento("guardian_activated", {"reason": "schedule_or_absence"})
            
            # Callback
            if self._on_activar:
                self._on_activar()
    
    def desactivar_guardiana(self):
        """Desactiva modo Guardian."""
        with self._lock:
            if not self._guardiana_activa:
                return
            
            self._guardiana_activa = False
            
            # Desactivar en cerebro
            if self.cerebro_ref:
                self.cerebro_ref._modo_guardiana = False
            
            logger.info("✅ GUARDIAN DESACTIVADO — Fin de vigilancia")
            
            # Registrar evento
            self._registrar_evento("guardian_deactivated", {})
            
            # Callback
            if self._on_desactivar:
                self._on_desactivar()
    
    def _registrar_evento(self, tipo: str, datos: Dict):
        """Registra evento a guardian_detections.jsonl."""
        if not self._config.get("persistent_logging", {}).get("enabled"):
            return
        
        log_file = Path(self._config.get("persistent_logging", {}).get("log_file", "datos/guardian_detections.jsonl"))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        evento = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": tipo,
            "data": datos
        }
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(evento, ensure_ascii=False) + '\n')
            logger.debug(f"📝 Evento guardado: {tipo}")
        except Exception as e:
            logger.error(f"❌ Error registrando evento Guardian: {e}")
    
    def registrar_deteccion_rostro(self, num_rostros: int, confianza: float, snapshot_path: Optional[str] = None):
        """Registra detección de rostro."""
        if self._guardiana_activa and self._config.get("persistent_logging", {}).get("enabled"):
            datos = {
                "num_faces": num_rostros,
                "confidence": confianza,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            if snapshot_path:
                datos["snapshot_path"] = snapshot_path
            
            self._registrar_evento("face_detected", datos)
            logger.info(f"📸 GUARDIAN: {num_rostros} rostro(s) detectado(s) (confianza: {confianza:.2f})")
    
    def registrar_deteccion_voz(self, transcript: str, confianza: float = 1.0):
        """Registra detección de voz."""
        if self._guardiana_activa and self._config.get("persistent_logging", {}).get("enabled"):
            datos = {
                "transcript": transcript,
                "confidence": confianza,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            self._registrar_evento("voice_detected", datos)
            logger.info(f"🎤 GUARDIAN: Voz detectada — '{transcript}'")
    
    def registrar_acceso_enciclopedia(self, tipo: str, detalles: Optional[Dict] = None):
        """Registra acceso o intento de acceso a Enciclopedia."""
        if self._guardiana_activa and self._config.get("persistent_logging", {}).get("enabled"):
            datos = {"access_type": tipo}
            if detalles:
                datos.update(detalles)
            datos["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            self._registrar_evento("enciclopedia_access", datos)
            logger.warning(f"⚠️ GUARDIAN: Acceso a Enciclopedia — {tipo}")
    
    def _bucle_monitor(self):
        """Bucle principal de monitoreo."""
        check_interval = self._config.get("monitoring", {}).get("check_interval_seconds", 60)
        
        while self._corriendo:
            try:
                # Verificar horario programado
                en_horario = self._en_horario_guardian() if self._config.get("schedule") else False
                
                # Verificar ausencia de usuario
                minutos_sin_usuario = self._minutos_sin_detectar_usuario()
                timeout_mins = self._config.get("auto_activation", {}).get("absence_timeout_minutes", 30)
                ausencia_detectada = minutos_sin_usuario >= timeout_mins if self._config.get("auto_activation", {}).get("enabled") else False
                
                # Decidir si activar
                debe_activarse = en_horario or ausencia_detectada
                
                if debe_activarse and not self._guardiana_activa:
                    razon = "horario programado" if en_horario else f"ausencia ({minutos_sin_usuario:.1f} min sin usuario)"
                    logger.info(f"🛡️ Guardian activado por {razon}")
                    self.activar_guardiana()
                
                elif not debe_activarse and self._guardiana_activa:
                    logger.info("✅ Guardian desactivado — usuario activo")
                    self.desactivar_guardiana()
                
                # Debug info
                logger.debug(f"Guardian check: en_horario={en_horario}, ausencia={ausencia_detectada:.1f}min, activa={self._guardiana_activa}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error en bucle de Guardian: {e}")
                time.sleep(check_interval)
    
    def iniciar(self, on_activar: Optional[Callable] = None, on_desactivar: Optional[Callable] = None):
        """Inicia monitoreo de Guardian."""
        if self._corriendo:
            return
        
        self._on_activar = on_activar
        self._on_desactivar = on_desactivar
        self._corriendo = True
        self._thread_monitor = threading.Thread(target=self._bucle_monitor, daemon=True, name="GuardianMonitor")
        self._thread_monitor.start()
        
        logger.info("✅ Guardian Monitor iniciado")
    
    def detener(self):
        """Detiene monitoreo de Guardian."""
        self._corriendo = False
        if self._thread_monitor:
            self._thread_monitor.join(timeout=2.0)
        logger.info("✅ Guardian Monitor detenido")
    
    def obtener_estado(self) -> Dict:
        """Retorna estado actual de Guardian."""
        return {
            "activa": self._guardiana_activa,
            "minutos_sin_usuario": self._minutos_sin_detectar_usuario(),
            "en_horario_programado": self._en_horario_guardian(),
            "config": self._config
        }
    
    def leer_log_detecciones(self, limite: int = 100) -> list:
        """Lee últimas N líneas del log de detecciones."""
        log_file = Path(self._config.get("persistent_logging", {}).get("log_file", "datos/guardian_detections.jsonl"))
        
        if not log_file.exists():
            return []
        
        eventos = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        eventos.append(json.loads(line))
                    except:
                        pass
            
            # Retornar últimas N líneas
            return eventos[-limite:]
        except Exception as e:
            logger.error(f"Error leyendo log de detecciones: {e}")
            return []


# Singleton global
_guardian_monitor_instance = None


def obtener_guardian_monitor(config_path: str = "datos/guardian_config.json", cerebro_ref=None) -> GuardianMonitor:
    """Obtiene instancia singleton de GuardianMonitor."""
    global _guardian_monitor_instance
    if _guardian_monitor_instance is None:
        _guardian_monitor_instance = GuardianMonitor(config_path, cerebro_ref)
    return _guardian_monitor_instance


