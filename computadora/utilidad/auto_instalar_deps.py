"""
FP-153: AUTO-INSTALLER — Dependencias faltantes se instalan automáticamente.

Soluciona el problema recurrente: "fuzzywuzzy no disponible".
En lugar de fallar silenciosamente, intenta instalar la dependencia.

NIGREDO: Detecta falta -> CITRINITAS: Instala -> RUBEDO: Recarga.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# Mapa de modulos Python -> paquetes pip (puede diferir)
_MODULO_A_PAQUETE = {
    "fuzzywuzzy": "fuzzywuzzy",
    "Levenshtein": "python-Levenshtein",
    "silero_vad": "silero-vad",
    "whisper": "whisper",
    "face_recognition": "face-recognition",
    "cv2": "opencv-python-headless",
    "dlib": "dlib",
    "librosa": "librosa",
    "scipy": "scipy",
    "numpy": "numpy",
    "torch": "torch",
    "pygame": "pygame",
    "discord": "discord.py",
    "telegram": "python-telegram-bot",
    "dotenv": "python-dotenv",
    "watchdog": "watchdog",
    "scapy": "scapy",
    "psutil": "psutil",
    "pyautogui": "pyautogui",
    "pywin32": "pywin32",
    "sounddevice": "sounddevice",
    "tinydb": "tinydb",

    # FP-156: GPU OpenGL para renderizado del orbe
    "OpenGL": "PyOpenGL",
    "OpenGL_accelerate": "PyOpenGL_accelerate",
    "onnxruntime": "onnxruntime",
    "torchaudio": "torchaudio",
}

_TORCH_CUDA_INDEX_URLS = [
    "cu118",
    "cu121",
]


def intentar_importar(nombre_modulo: str, paquete: Optional[str] = None) -> bool:
    """Intenta importar un modulo. Si falla, instala el paquete."""
    if paquete is None:
        paquete = _MODULO_A_PAQUETE.get(nombre_modulo, nombre_modulo)

    try:
        __import__(nombre_modulo)
        
        # Verificaciones especiales para módulos que necesitan CUDA
        if nombre_modulo == "torch":
            import torch
            if not torch.cuda.is_available():
                logger.warning("!! PyTorch instalado pero sin soporte CUDA, intentando instalar versión CUDA...")
                # Forzar reinstalación con CUDA
                for cuda_tag in _TORCH_CUDA_INDEX_URLS:
                    if _instalar_torch_cuda(cuda_tag):
                        # Re-importar para verificar
                        import importlib
                        importlib.reload(torch)
                        if torch.cuda.is_available():
                            logger.info("!! PyTorch actualizado exitosamente con soporte CUDA")
                            return True
                logger.warning("!! No se pudo instalar PyTorch con CUDA")
                return True  # El módulo está disponible, aunque sin CUDA
        
        logger.debug(f"! {nombre_modulo} disponible")
        return True
    except Exception as e:
        logger.warning(f"!! {nombre_modulo} no importable ({e}), instalando {paquete}...")
        instalado = _instalar_paquete(paquete, nombre_modulo)
        if not instalado and nombre_modulo in {"torch", "torchaudio"}:
            # For torch/torchaudio mismatch scenarios, attempt a paired reinstall.
            for cuda_tag in _TORCH_CUDA_INDEX_URLS:
                if _instalar_torch_cuda(cuda_tag):
                    return True
        elif not instalado and nombre_modulo == "dlib":
            # For dlib, try CUDA version if GPU is available
            try:
                import torch
                if torch.cuda.is_available():
                    logger.info("!! GPU detectada, intentando instalar dlib con CUDA...")
                    if _instalar_dlib_cuda():
                        return True
            except ImportError:
                pass
        return instalado


def _modulo_importable(nombre_modulo: str) -> bool:
    try:
        __import__(nombre_modulo)
        return True
    except ImportError:
        return False


def _instalar_paquete(paquete: str, nombre_modulo: str, extra_args: Optional[List[str]] = None) -> bool:
    """Intenta instalar un paquete con pip."""
    try:
        logger.info(f"!! Instalando {paquete}...")
        cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--prefer-binary", paquete]
        if extra_args:
            cmd.extend(extra_args)
        subprocess.check_call(cmd, timeout=300)
        if _modulo_importable(nombre_modulo):
            logger.info(f"!! {paquete} instalado exitosamente")
            return True
        logger.error(f"!! {paquete} instalado pero {nombre_modulo} no importable")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"!! Timeout instalando {paquete} (>5min)")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"!! Error instalando {paquete}: {e}")
        return False
    except Exception as e:
        logger.error(f"!! Error inesperado instalando {paquete}: {e}")
        return False


def _instalar_torch_cuda(cuda_tag: str) -> bool:
    logger.info(f"!! Intentando instalar PyTorch CUDA {cuda_tag}...")
    try:
        if cuda_tag.startswith("http://") or cuda_tag.startswith("https://"):
            index_url = cuda_tag
        else:
            index_url = f"https://download.pytorch.org/whl/{cuda_tag}"

        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--prefer-binary",
            "--upgrade",
            "--force-reinstall",
            "torch",
            "torchvision",
            "torchaudio",
            "--extra-index-url",
            index_url,
        ]
        subprocess.check_call(cmd, timeout=900)

        try:
            import torch
            import torchaudio
            cuda_ready = torch.cuda.is_available()
        except Exception as e:
            logger.warning(f"!! torch/torchaudio instalado pero no puede importarse tras instalación CUDA: {e}")
            return False

        if not cuda_ready:
            logger.warning(f"!! torch instalado pero CUDA sigue sin estar disponible después de instalar {cuda_tag}")
            return False

        return True
    except subprocess.TimeoutExpired:
        logger.error(f"!! Timeout instalando torch CUDA {cuda_tag}")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"!! Error instalando torch CUDA {cuda_tag}: {e}")
        return False


def _instalar_dlib_cuda() -> bool:
    """Instala dlib con soporte CUDA para face recognition GPU."""
    logger.info("!! Intentando instalar dlib con CUDA...")
    try:
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--prefer-binary",
            "--upgrade",
            "--force-reinstall",
            "dlib",
            "--install-option=--yes",
            "--install-option=--cuda",
        ]
        subprocess.check_call(cmd, timeout=1800)  # 30 min timeout

        # Verificar que dlib se instaló con CUDA
        try:
            import dlib
            cuda_support = dlib.DLIB_USE_CUDA
            if cuda_support:
                logger.info("!! dlib instalado exitosamente con soporte CUDA")
                return True
            else:
                logger.warning("!! dlib instalado pero sin soporte CUDA")
                return False
        except Exception as e:
            logger.warning(f"!! dlib instalado pero no puede importarse: {e}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("!! Timeout instalando dlib CUDA (>30min)")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"!! Error instalando dlib CUDA: {e}")
        return False
    except Exception as e:
        logger.error(f"!! Error inesperado instalando torch CUDA {cuda_tag}: {e}")
        return False


def garantizar_torch_gpu(gpu_disponible: bool, gpu_modelo: Optional[str] = None) -> bool:
    if _modulo_importable("torch"):
        try:
            import torch
            # Verificar si hay GPUs NVIDIA disponibles, incluso si la principal es integrada
            has_nvidia = False
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                for i in range(device_count):
                    try:
                        name = torch.cuda.get_device_name(i)
                        if any(keyword in name for keyword in ['GTX', 'RTX', 'GeForce', 'TITAN', 'Quadro']):
                            has_nvidia = True
                            break
                    except Exception:
                        continue
            
            if has_nvidia and not torch.cuda.is_available():
                # Hay NVIDIA pero torch no tiene CUDA
                logger.warning("!! GPUs NVIDIA detectadas pero torch no tiene CUDA; instalando versión CUDA")
                for cuda_tag in _TORCH_CUDA_INDEX_URLS:
                    if _instalar_torch_cuda(cuda_tag):
                        logger.info(f"!! torch actualizado con CUDA ({cuda_tag})")
                        return True
                logger.warning("!! No pude actualizar torch a CUDA; manteniendo instalación existente")
            elif gpu_disponible and gpu_modelo and "nvidia" in gpu_modelo.lower():
                # Modelo principal es NVIDIA
                if not torch.cuda.is_available():
                    logger.warning("!! torch instalado pero CUDA no está habilitado; intentando instalar versión CUDA")
                    for cuda_tag in _TORCH_CUDA_INDEX_URLS:
                        if _instalar_torch_cuda(cuda_tag):
                            logger.info(f"!! torch actualizado con CUDA ({cuda_tag})")
                            return True
                    logger.warning("!! No pude actualizar torch a CUDA; manteniendo instalación existente")
        except Exception as e:
            logger.debug(f"!! Error verificando CUDA en torch instalado: {e}")

        logger.info("!! torch ya disponible")
        return False

    # Instalar torch por primera vez
    has_nvidia = False
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            for i in range(device_count):
                try:
                    name = torch.cuda.get_device_name(i)
                    if any(keyword in name for keyword in ['GTX', 'RTX', 'GeForce', 'TITAN', 'Quadro']):
                        has_nvidia = True
                        break
                except Exception:
                    continue
    except ImportError:
        # torch no instalado aún
        pass
    
    if has_nvidia or (gpu_disponible and gpu_modelo and "nvidia" in gpu_modelo.lower()):
        for cuda_tag in _TORCH_CUDA_INDEX_URLS:
            if _instalar_torch_cuda(cuda_tag):
                logger.info(f"!! torch instalado con CUDA ({cuda_tag})")
                return True
        logger.warning("!! No pude instalar torch CUDA específico, intentando CPU fallback")

    return _instalar_paquete("torch", "torch")


def _verificar_torch_torchaudio() -> bool:
    """Verifica que torch y torchaudio se importen correctamente y funcionen juntos."""
    try:
        import torch
        import torchaudio
        import torchaudio.functional  # noqa: F401
        return True
    except Exception as e:
        logger.warning(f"!! Verificacion torch/torchaudio falló: {e}")
        return False


def asegurar_dependencias_inicio() -> bool:
    """Asegura dependencias criticas antes de iniciar COMPUTADORA."""
    logger.info("!! Asegurando dependencias criticas de inicio...")
    garantizar_librerias_criticas()
    reinicio_necesario = garantizar_torch_gpu(False)

    if not _verificar_torch_torchaudio():
        logger.warning("!! Detectada incompatibilidad torch/torchaudio; reinstalando pares emparejados.")
        for cuda_tag in _TORCH_CUDA_INDEX_URLS:
            if _instalar_torch_cuda(cuda_tag):
                reinicio_necesario = True
                break
        else:
            if _instalar_paquete("torch", "torch"):
                _instalar_paquete("torchaudio", "torchaudio")
                reinicio_necesario = True

    if _verificar_torch_torchaudio():
        logger.info("!! torch/torchaudio listos para el arranque")
    else:
        logger.error("!! No se pudo asegurar torch/torchaudio. Revisa la instalacion del entorno.")

    return reinicio_necesario


def garantizar_entorno_hardware(gpu_disponible: bool, gpu_modelo: Optional[str] = None) -> bool:
    """Asegura dependencias del runtime según el hardware detectado.
    Retorna True si se instaló algo y debe reiniciarse.
    """
    reinicio_necesario = False
    criticas = [
        ("fuzzywuzzy", "fuzzywuzzy"),
        ("Levenshtein", "python-Levenshtein"),
        ("onnxruntime", "onnxruntime"),
        ("silero_vad", "silero-vad"),
        ("whisper", "whisper"),
        ("face_recognition", "face-recognition"),
        ("cv2", "opencv-python-headless"),
        ("sounddevice", "sounddevice"),
        ("OpenGL", "PyOpenGL"),
        ("OpenGL_accelerate", "PyOpenGL_accelerate"),
        ("torchaudio", "torchaudio"),
    ]

    for nombre_mod, paquete in criticas:
        if not _modulo_importable(nombre_mod):
            if _instalar_paquete(paquete, nombre_mod):
                reinicio_necesario = True

    if garantizar_torch_gpu(gpu_disponible, gpu_modelo):
        reinicio_necesario = True

    logger.info(f"Dependencias hardware aseguradas. Reinicio necesario={reinicio_necesario}")
    return reinicio_necesario


def garantizar_librerias_criticas() -> None:
    """FP-153: Verifica y asegura que las librerias CRITICAS esten disponibles."""
    criticas = [
        ("fuzzywuzzy", "fuzzywuzzy"),
        ("Levenshtein", "python-Levenshtein"),
        ("silero_vad", "silero-vad"),
        ("whisper", "whisper"),
        ("face_recognition", "face-recognition"),
        ("cv2", "opencv-python-headless"),
        ("sounddevice", "sounddevice"),

        # FP-156: GPU OpenGL para renderizado 3D del orbe
        ("OpenGL", "PyOpenGL"),
        ("OpenGL_accelerate", "PyOpenGL_accelerate"),
    ]

    resultados: Dict[str, bool] = {}
    for nombre_mod, paquete in criticas:
        disponible = intentar_importar(nombre_mod, paquete)
        resultados[nombre_mod] = disponible
        logger.info(f"  {nombre_mod}: {'!!' if disponible else '!! FALTA'}")

    total = len(criticas)
    disponibles = sum(1 for v in resultados.values() if v)
    logger.info(f"Librerias criticas: {disponibles}/{total} disponibles")


def garantizar_libreria_soft(nombre_modulo: str, paquete: Optional[str] = None) -> bool:
    """FP-153: Intenta asegurar que una libreria SOFT (no critica) este disponible."""
    return intentar_importar(nombre_modulo, paquete)


if __name__ == "__main__":
    print("\n!! FP-153: Verificando e instalando dependencias...\n")
    garantizar_librerias_criticas()
    print("\n!! Verificacion completada.\n")


