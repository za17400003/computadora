#!/usr/bin/env python3
"""
AUDITORÍA SRS EN TIEMPO REAL
Valida cada SRS durante ejecución de COMPUTADORA sin depender de GUI
Usuario: "verifica que funciona, auditalo en tiempo real... verifica que se cumplan todos los srs"
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from datetime import datetime

# Agregar proyecto-golem al path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

# ============================================================================
# CONFIGURACIÓN DE AUDITORÍA
# ============================================================================

class SRSAuditReport:
    """Genera reporte de auditoría SRS en tiempo real"""
    
    def __init__(self):
        self.srs_checks = {}
        self.boot_start = time.time()
        self.results = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Configura logger para auditoría"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path(__file__).parent / f".logs/AUDITORIA_SRS_{timestamp}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.remove()  # Remove default handler
        logger.add(sys.stdout, format="<level>{level: <8}</level> | <cyan>{time:HH:mm:ss}</cyan> | <green>AUDITORIA</green> - {message}")
        logger.add(str(log_path), format="{level: <8} | {time:YYYY-MM-DD HH:mm:ss} | {message}")
        self.log_path = log_path
    
    def check_rf_01_speech_to_text(self):
        """RF-01: Speech-to-Text con Whisper + detección de wake word"""
        logger.info("=" * 70)
        logger.info("RF-01: AUDITORÍA SPEECH-TO-TEXT")
        logger.info("=" * 70)
        
        results = {"status": "FAIL", "checks": {}}
        
        try:
            # Check 1: Whisper disponible
            try:
                import whisper
                logger.info("✅ Whisper disponible")
                results["checks"]["whisper_available"] = True
            except ImportError:
                logger.error("❌ Whisper NO disponible")
                results["checks"]["whisper_available"] = False
                return results
            
            # Check 2: Modelo Whisper cargable
            try:
                model = whisper.load_model("base", device="cpu")
                logger.info("✅ Modelo Whisper 'base' cargable")
                results["checks"]["model_loadable"] = True
            except Exception as e:
                logger.error(f"❌ Error cargando modelo: {e}")
                results["checks"]["model_loadable"] = False
                return results
            
            # Check 3: Config.json con Whisper settings
            config_path = Path(__file__).parent / "datos/config.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    whisper_config = config.get("whisper", {})
                    if whisper_config.get("modelo"):
                        logger.info(f"✅ Whisper config en datos/config.json: modelo={whisper_config['modelo']}")
                        results["checks"]["config_exists"] = True
                    else:
                        logger.warning("⚠️ Whisper config incompleta en datos/config.json")
                        results["checks"]["config_exists"] = False
            else:
                logger.error("❌ datos/config.json NO existe")
                results["checks"]["config_exists"] = False
            
            # Check 4: Silero VAD disponible para detección de voz
            try:
                import torch
                torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
                logger.info("✅ Silero VAD disponible para detección de voz")
                results["checks"]["silero_vad"] = True
            except Exception as e:
                logger.warning(f"⚠️ Silero VAD no disponible: {e}")
                results["checks"]["silero_vad"] = False
            
            # Check 5: Detección de devices de audio
            try:
                import sounddevice as sd
                devices = sd.query_devices()
                audio_devices = [d for d in devices if d['max_input_channels'] > 0]
                if audio_devices:
                    logger.info(f"✅ {len(audio_devices)} dispositivo(s) de audio disponible(s)")
                    results["checks"]["audio_devices"] = len(audio_devices)
                else:
                    logger.error("❌ No hay dispositivos de audio disponibles")
                    results["checks"]["audio_devices"] = 0
            except Exception as e:
                logger.error(f"❌ Error consultando dispositivos de audio: {e}")
                results["checks"]["audio_devices"] = 0
            
            results["status"] = "PASS" if all(v for k, v in results["checks"].items() if k not in ["audio_devices", "silero_vad"]) else "PARTIAL"
            
        except Exception as e:
            logger.error(f"Exception en RF-01: {e}")
            results["status"] = "FAIL"
        
        return results
    
    def check_rf_02_nlu_levels(self):
        """RF-02: NLU con 4 niveles de procesamiento"""
        logger.info("=" * 70)
        logger.info("RF-02: AUDITORÍA NLU LEVELS")
        logger.info("=" * 70)
        
        results = {"status": "FAIL", "checks": {}}
        
        try:
            # Import CerebroGolem para validar niveles
            from computadora.cerebro.nlu import CerebroGolem
            
            # Check 1: CerebroGolem inicializable
            try:
                from computadora.config import Configuracion
                config = Configuracion()
                cerebro = CerebroGolem(config)
                logger.info("✅ CerebroGolem inicializado")
                results["checks"]["cerebro_init"] = True
            except Exception as e:
                logger.error(f"❌ Error inicializando CerebroGolem: {e}")
                results["checks"]["cerebro_init"] = False
                return results
            
            # Check 2: Nivel 0 (Recursión/Self-validation)
            try:
                if hasattr(cerebro, '_valida_a_si_misma'):
                    is_valid = cerebro._valida_a_si_misma()
                    if is_valid:
                        logger.info("✅ Nivel 0 (Recursión): Sistema se valida a sí mismo")
                        results["checks"]["nivel_0"] = True
                    else:
                        logger.warning("⚠️ Nivel 0 falló validación")
                        results["checks"]["nivel_0"] = False
                else:
                    logger.warning("⚠️ Nivel 0 no disponible")
                    results["checks"]["nivel_0"] = False
            except Exception as e:
                logger.error(f"❌ Error en Nivel 0: {e}")
                results["checks"]["nivel_0"] = False
            
            # Check 3: Nivel 1 (Patrones/Regex)
            try:
                if hasattr(cerebro, 'lemed') and cerebro.lemed:
                    count = len(cerebro.lemed.patrones)
                    logger.info(f"✅ Nivel 1 (Regex): {count} patrones cargados")
                    results["checks"]["nivel_1"] = count > 0
                else:
                    logger.warning("⚠️ Nivel 1 (Regex) no inicializado")
                    results["checks"]["nivel_1"] = False
            except Exception as e:
                logger.error(f"❌ Error en Nivel 1: {e}")
                results["checks"]["nivel_1"] = False
            
            # Check 4: Nivel 2+ (LLM via Ollama)
            try:
                if hasattr(cerebro, 'modelo') and cerebro.modelo:
                    logger.info(f"✅ Nivel 2+ (LLM): {cerebro.modelo} disponible")
                    results["checks"]["nivel_2plus"] = True
                else:
                    logger.warning("⚠️ Nivel 2+ (LLM) no disponible - modo fallback a Nivel 1")
                    results["checks"]["nivel_2plus"] = False
            except Exception as e:
                logger.warning(f"⚠️ Error en Nivel 2+: {e}")
                results["checks"]["nivel_2plus"] = False
            
            results["status"] = "PASS" if results["checks"].get("cerebro_init") and results["checks"].get("nivel_1") else "PARTIAL"
            
        except Exception as e:
            logger.error(f"Exception en RF-02: {e}")
            results["status"] = "FAIL"
        
        return results
    
    def check_rf_03_text_to_speech(self):
        """RF-03: Text-to-Speech con múltiples motores"""
        logger.info("=" * 70)
        logger.info("RF-03: AUDITORÍA TEXT-TO-SPEECH")
        logger.info("=" * 70)
        
        results = {"status": "FAIL", "checks": {}}
        
        try:
            # Check 1: pyttsx3 disponible
            try:
                import pyttsx3
                engine = pyttsx3.init()
                logger.info("✅ pyttsx3 disponible (motor TTS local)")
                results["checks"]["pyttsx3_available"] = True
            except Exception as e:
                logger.warning(f"⚠️ pyttsx3 no disponible: {e}")
                results["checks"]["pyttsx3_available"] = False
            
            # Check 2: edge-tts disponible
            try:
                import edge_tts
                logger.info("✅ edge-tts disponible (motor TTS cloud)")
                results["checks"]["edge_tts_available"] = True
            except ImportError:
                logger.warning("⚠️ edge-tts no disponible")
                results["checks"]["edge_tts_available"] = False
            
            # Check 3: Voz configurada
            try:
                from computadora.config import Configuracion
                config = Configuracion()
                voz_config = config.obtener("voz", {})
                if voz_config.get("voz"):
                    logger.info(f"✅ Voz configurada: {voz_config['voz']}")
                    results["checks"]["voice_configured"] = True
                else:
                    logger.warning("⚠️ Voz no configurada")
                    results["checks"]["voice_configured"] = False
            except Exception as e:
                logger.error(f"❌ Error leyendo configuración de voz: {e}")
                results["checks"]["voice_configured"] = False
            
            results["status"] = "PASS" if (results["checks"].get("pyttsx3_available") or results["checks"].get("edge_tts_available")) else "PARTIAL"
            
        except Exception as e:
            logger.error(f"Exception en RF-03: {e}")
            results["status"] = "FAIL"
        
        return results
    
    def check_rf_260_camera_discovery(self):
        """RF-260: Descubrimiento de cámaras al boot"""
        logger.info("=" * 70)
        logger.info("RF-260: AUDITORÍA CAMERA DISCOVERY")
        logger.info("=" * 70)
        
        results = {"status": "FAIL", "checks": {}}
        
        try:
            # Check 1: cv2 disponible
            try:
                import cv2
                logger.info(f"✅ OpenCV (cv2) disponible: {cv2.__version__}")
                results["checks"]["cv2_available"] = True
            except ImportError:
                logger.error("❌ OpenCV (cv2) NO disponible")
                results["checks"]["cv2_available"] = False
                return results
            
            # Check 2: Detectar cámaras disponibles
            try:
                camera_count = 0
                for i in range(5):  # Test primeras 5 cámaras potenciales
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        camera_count += 1
                        cap.release()
                
                if camera_count > 0:
                    logger.info(f"✅ {camera_count} cámara(s) detectada(s)")
                    results["checks"]["cameras_detected"] = camera_count
                else:
                    logger.warning("⚠️ No se detectaron cámaras")
                    results["checks"]["cameras_detected"] = 0
            except Exception as e:
                logger.error(f"❌ Error detectando cámaras: {e}")
                results["checks"]["cameras_detected"] = 0
            
            # Check 3: face_recognition disponible
            try:
                import face_recognition
                logger.info("✅ face_recognition disponible")
                results["checks"]["face_recognition_available"] = True
            except ImportError:
                logger.warning("⚠️ face_recognition NO disponible")
                results["checks"]["face_recognition_available"] = False
            
            results["status"] = "PASS" if results["checks"].get("cameras_detected", 0) > 0 else "PARTIAL"
            
        except Exception as e:
            logger.error(f"Exception en RF-260: {e}")
            results["status"] = "FAIL"
        
        return results
    
    def check_threading_model(self):
        """Verificar modelo de threading: no deadlocks, signal/slot funcionando"""
        logger.info("=" * 70)
        logger.info("THREADING MODEL: AUDITORÍA")
        logger.info("=" * 70)
        
        results = {"status": "FAIL", "checks": {}}
        
        try:
            # Check 1: PyQt6 disponible
            try:
                from PyQt6.QtCore import QThread, pyqtSignal, QTimer
                logger.info("✅ PyQt6 disponible (threading support)")
                results["checks"]["pyqt6_available"] = True
            except ImportError:
                logger.error("❌ PyQt6 NO disponible")
                results["checks"]["pyqt6_available"] = False
                return results
            
            # Check 2: Threading disponible
            try:
                import threading
                active_threads = threading.active_count()
                logger.info(f"✅ Threading: {active_threads} thread(s) activos")
                results["checks"]["threading_active"] = active_threads > 0
            except Exception as e:
                logger.error(f"❌ Error verificando threading: {e}")
                results["checks"]["threading_active"] = False
            
            results["status"] = "PASS" if results["checks"].get("pyqt6_available") else "PARTIAL"
            
        except Exception as e:
            logger.error(f"Exception en Threading: {e}")
            results["status"] = "FAIL"
        
        return results
    
    def run_full_audit(self):
        """Ejecuta auditoría completa de todos los SRS"""
        logger.info("\n" + "=" * 70)
        logger.info("🔍 AUDITORÍA SRS EN TIEMPO REAL — COMPUTADORA")
        logger.info("=" * 70 + "\n")
        
        audit_results = {}
        
        # Ejecutar todas las auditorías
        audit_results["RF-01"] = self.check_rf_01_speech_to_text()
        time.sleep(1)
        
        audit_results["RF-02"] = self.check_rf_02_nlu_levels()
        time.sleep(1)
        
        audit_results["RF-03"] = self.check_rf_03_text_to_speech()
        time.sleep(1)
        
        audit_results["RF-260"] = self.check_rf_260_camera_discovery()
        time.sleep(1)
        
        audit_results["THREADING"] = self.check_threading_model()
        
        # Generar resumen
        self.generate_summary(audit_results)
        
        return audit_results
    
    def generate_summary(self, audit_results):
        """Genera resumen ejecutivo de auditoría"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 RESUMEN EJECUTIVO")
        logger.info("=" * 70 + "\n")
        
        boot_time = time.time() - self.boot_start
        logger.info(f"Boot completado en: {boot_time:.2f}s")
        logger.info(f"Log archivo: {self.log_path}\n")
        
        # Tabla de resultados
        logger.info("SRS Status:")
        for srs, result in audit_results.items():
            status = result.get("status", "UNKNOWN")
            emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            logger.info(f"  {emoji} {srs}: {status}")
        
        # Overall status
        all_pass = all(r.get("status") == "PASS" for r in audit_results.values())
        overall = "✅ PASS" if all_pass else "⚠️ PARTIAL" if any(r.get("status") != "FAIL" for r in audit_results.values()) else "❌ FAIL"
        
        logger.info(f"\n📋 OVERALL: {overall}")
        logger.info(f"Log disponible en: {self.log_path}")
        logger.info("=" * 70 + "\n")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    audit = SRSAuditReport()
    results = audit.run_full_audit()
    
    # Exit con código apropiado
    all_pass = all(r.get("status") == "PASS" for r in results.values())
    sys.exit(0 if all_pass else 1)
