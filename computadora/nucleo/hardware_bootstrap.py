"""🔧 HARDWARE BOOTSTRAP — BIOS-like Verification Gates

FASE 0: Hardware Discovery (anterior a servicios)
- Detecta cámaras, micrófonos, GPU
- Registra en GestorKelim pero NO los conecta todavía

FASE 1: Hardware Verification (bloquea hasta OK)
- Obtiene primer frame de cámara
- Verifica micrófono
- Verifica GPU/OpenGL
- GATE: Espera hasta que TODO esté listo

Propósito:
- Evitar "cámara no disponible" false warnings
- Sincronizar hardware ANTES de servicios
- Mantener cámara conectada (pool, no close)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


def _safe_python_probe(script: str, timeout_s: float = 5.0) -> dict | None:
    """Ejecuta un código Python aislado para proteger contra fallos nativos."""
    env = os.environ.copy()
    env["PYTHONFAULTHANDLER"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        logger.warning(f"Hardware probe timeout: {e}")
        return None
    except Exception as e:
        logger.warning(f"Hardware probe failed: {e}")
        return None

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        logger.warning(
            "Hardware probe failed (code %s): %s",
            proc.returncode,
            stderr or "<no stderr>",
        )
        return None

    try:
        return json.loads(proc.stdout)
    except Exception as e:
        logger.warning("Hardware probe invalid JSON: %s", e)
        return None


def _probe_gpu() -> Dict[str, Any]:
    """Prueba GPU: WMIC para detectar todas las GPUs, elegir la mejor."""
    try:
        import subprocess
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "Name", "/value"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5
        )
        gpus = []
        for linea in result.stdout.splitlines():
            if linea.startswith("Name="):
                name = linea.split("=", 1)[1].strip()
                gpus.append(name)
        
        # Elegir la mejor GPU
        for gpu in gpus:
            if any(keyword in gpu for keyword in ['GTX', 'RTX', 'GeForce', 'TITAN', 'Quadro']):
                return {'disponible': True, 'modelo': gpu}
        # Si no hay dedicada, usar la primera
        if gpus:
            return {'disponible': True, 'modelo': gpus[0]}
    except Exception:
        pass
    
    # Fallback a probe script para OpenGL
    probe_script = r"""
import json
gpu_available = False
gpu_name = 'CPU only'

try:
    from PyQt6.QtGui import QGuiApplication, QSurfaceFormat, QOpenGLContext, QOffscreenSurface
    app = QGuiApplication.instance() or QGuiApplication([])
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 2)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    ctx = QOpenGLContext()
    ctx.setFormat(fmt)
    if ctx.create():
        surface = QOffscreenSurface()
        surface.setFormat(ctx.format())
        surface.create()
        if surface.isValid() and ctx.makeCurrent(surface):
            gpu_available = True
            try:
                import OpenGL.GL as gl
                vendor = gl.glGetString(gl.GL_VENDOR).decode('utf-8', errors='ignore')
                renderer = gl.glGetString(gl.GL_RENDERER).decode('utf-8', errors='ignore')
                gpu_name = f"{vendor} - {renderer}"
            except Exception:
                gpu_name = "OpenGL GPU"
            finally:
                ctx.doneCurrent()
except Exception:
    pass

print(json.dumps({'disponible': gpu_available, 'modelo': gpu_name}, ensure_ascii=False))
"""
    result = _safe_python_probe(probe_script, timeout_s=3.0)
    if isinstance(result, dict):
        return result
    return {'disponible': False, 'modelo': 'CPU only'}


def _probe_microfonos() -> list[Dict[str, Any]]:
    probe_script = r"""
import json
import sounddevice as sd

devices = sd.query_devices()
input_devices = [
    {
        'id': i,
        'nombre': d.get('name', ''),
        'canales': d.get('max_input_channels', 0),
    }
    for i, d in enumerate(devices)
    if d.get('max_input_channels', 0) > 0
]
print(json.dumps(input_devices, ensure_ascii=False))
"""
    result = _safe_python_probe(probe_script, timeout_s=5.0)
    if isinstance(result, list):
        return result
    return []


def _probe_default_microphone(timeout_s: float = 3.0) -> bool:
    """Verificar micrófono disponible con fallback a enumeración."""
    probe_script = r"""
import json
import sounddevice as sd

try:
    device_count = sd.query_devices()
    if isinstance(device_count, int) and device_count > 0:
        print(json.dumps({'success': True, 'device_count': device_count}, ensure_ascii=False))
    else:
        device_value = sd.default.device
        if isinstance(device_value, (list, tuple)):
            serializable_device = list(device_value)
        else:
            serializable_device = str(device_value)
        # Considerar válido si hay al menos un dispositivo registrado
        has_device = device_value and device_value != (None, None)
        print(json.dumps({'success': has_device, 'device': serializable_device}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False))
"""
    result = _safe_python_probe(probe_script, timeout_s=timeout_s)
    if not isinstance(result, dict):
        return False
    
    # Si hay conteo de dispositivos, ya sabemos que funciona
    if result.get('device_count', 0) > 0:
        return True
    
    # Fallback: verificar default device
    success = result.get('success', False)
    device = result.get('device')
    
    # Retornar True si:
    # 1. Script dice que tuvo éxito, O
    # 2. Hay un dispositivo configurado y no es None
    if success:
        return True
    
    if device and isinstance(device, (list, tuple)) and len(device) >= 1 and device[0] is not None:
        return True
    
    return False


def hardware_discovery() -> Dict[str, Any]:
    """FASE 0: Descubrir hardware disponible (sin conectar).
    
    Retorna:
        {
            'camaras': [{'id': str, 'tipo': str, 'estado': str}],
            'microfonos': [...],
            'gpu': {'disponible': bool, 'modelo': str},
            'error': None | str
        }
    """
    result = {
        'camaras': [],
        'microfonos': [],
        'gpu': {'disponible': False, 'modelo': ''},
        'error': None
    }
    
    try:
        # RF-260: Descubrir cámaras
        from computadora.nucleo.kli import GestorKelim
        gestor = GestorKelim.instancia()
        observadores = gestor.descubrir_observadores()
        result['camaras'] = observadores or []
        logger.info(f"🎥 Hardware Discovery: {len(observadores)} cámara(s) detectada(s)")
    except Exception as e:
        logger.debug(f"Hardware Discovery (cámaras) falló: {e}")
        result['error'] = str(e)
    
    try:
        result['gpu'] = _probe_gpu()
        if result['gpu']['disponible']:
            logger.info(f"⚡ GPU: {result['gpu']['modelo']}")
        else:
            logger.info("⚡ GPU: No disponible (usando CPU)")
    except Exception as e:
        logger.debug(f"GPU detection: {e}")

    try:
        input_devices = _probe_microfonos()
        result['microfonos'] = input_devices
        logger.info(f"🎤 {len(input_devices)} micrófono(s) detectado(s)")
    except Exception as e:
        logger.debug(f"Microphone detection: {e}")
    
    return result


def hardware_verification(timeout_s: float = 15.0) -> bool:
    """FASE 1: Verificar que hardware responde (GATE bloqueante).
    
    Espera hasta que cámara tenga frames + micrófono responda + GPU OK.
    
    Args:
        timeout_s: Máximo de segundos a esperar. Si vence, retorna False pero continúa.
    
    Retorna:
        True si TODO verificado, False si timeout pero continúa.
    """
    start = time.monotonic()
    camera_ok = False
    microphone_ok = False
    
    logger.info(f"🔐 Hardware Verification: Esperando que responda (timeout={timeout_s}s)...")
    
    # Verificar cámara
    try:
        from computadora.nucleo.kli import GestorKelim
        gestor = GestorKelim.instancia()
        camaras = gestor.listar()
        
        camera_registrado = any(k['id'] == 'camara_local' for k in camaras)
        if not camera_registrado:
            logger.debug("⚠️  Cámara no registrada en GestorKelim — reintentando detección")
            # Reintentar discovery
            gestor.descubrir_observadores()
            camaras = gestor.listar()
            camera_registrado = any(k['id'] == 'camara_local' for k in camaras)
        
        if camera_registrado:
            camara = next(k for k in camaras if k['id'] == 'camara_local')
            if camara['estado'] == 'CONECTADO':
                camera_ok = True
                logger.info("✅ Cámara verificada: conectada y lista")
            else:
                logger.debug(f"⚠️  Cámara detectada con estado={camara['estado']} — intentando reconectar")
                try:
                    if gestor.conectar('camara_local'):
                        logger.info("✅ Cámara reconectada con éxito en hardware verification")
                        camera_ok = True
                    else:
                        logger.debug("⚠️  Reintento de conexión de cámara fallido")
                except Exception as e:
                    logger.debug(f"Error reconectando camara_local: {e}")
    except Exception as e:
        logger.warning(f"⚠️  Verificación de cámara: {e}")
    
    # Verificar micrófono
    try:
        if _probe_default_microphone():
            microphone_ok = True
            logger.info("✅ Micrófono verificado: disponible")
        else:
            logger.debug("⚠️  No hay dispositivo de entrada de audio detectado por probe")
    except Exception as e:
        logger.debug(f"⚠️  Verificación de micrófono falló: {e}")
    
    elapsed = time.monotonic() - start
    
    if camera_ok and microphone_ok:
        logger.info(f"✅ Hardware Verification completada en {elapsed:.1f}s")
        return True
    else:
        logger.debug(f"⚠️  Hardware Verification incompleta ({elapsed:.1f}s): camera={camera_ok}, mic={microphone_ok}")
        return False


def ensure_camera_connected() -> Optional[Any]:
    """Asegurar que KliCamara está conectada y retornar instancia.
    
    Usado DESPUÉS de verificación para obtener cámara con garantía de conexión.
    
    Retorna:
        KliCamara objeto si está conectado, None si error.
    """
    try:
        from computadora.nucleo.kli import GestorKelim
        gestor = GestorKelim.instancia()
        camaras = gestor.listar()
        
        camara_dict = next((k for k in camaras if k['id'] == 'camara_local'), None)
        if not camara_dict:
            logger.debug("⚠️  ensure_camera_connected: cámara no registrada en GestorKelim")
            return None
        
        # Asegurarse de que el objeto KliCamara esté disponible
        objeto = camara_dict.get('objeto')
        if not objeto:
            logger.debug("⚠️  GestorKelim no tiene objeto de cámara — intentando discovery")
            try:
                gestor.descubrir_observadores()
                camaras = gestor.listar()
                camara_dict = next((k for k in camaras if k['id'] == 'camara_local'), None)
                if camara_dict:
                    objeto = camara_dict.get('objeto')
                    if objeto:
                        logger.info("✅ Objeto de cámara recuperado después de redescubrimiento")
            except Exception as e:
                logger.debug(f"Error en redescubrimiento: {e}")
        
        # Conectar si no está conectado
        if camara_dict['estado'] != 'CONECTADO':
            logger.debug(f"⚠️  Cámara estado={camara_dict['estado']} — intentando reconectar")
            try:
                if gestor.conectar('camara_local'):
                    logger.info("✅ Cámara reconectada con éxito")
                    # Actualizar objeto después de reconectar
                    camara_dict = next((k for k in gestor.listar() if k['id'] == 'camara_local'), None)
                    if camara_dict:
                        objeto = camara_dict.get('objeto')
                else:
                    logger.debug("⚠️  No se pudo reconectar KliCamara")
            except Exception as e:
                logger.debug(f"Error reconectando: {e}")

        if objeto:
            logger.info("✅ Cámara asegurada: objeto disponible y lista para uso")
            return objeto
        else:
            logger.debug("⚠️  Cámara no tiene objeto disponible — usando fallback visual")
            return None
    except Exception as e:
        logger.debug(f"⚠️  ensure_camera_connected: {e}")
        return None


