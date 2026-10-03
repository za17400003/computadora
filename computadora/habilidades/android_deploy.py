"""
הוד+נצח (Hod+Netzaj) — Percepción + Persistencia.
Auto-Deploy de Minimi: vigila cambios en el proyecto Android, detecta
dispositivo conectado (USB o wireless debug), compila y despliega APK.

FP-096: Cuando Minimi se actualiza y el Motorola está conectado, Computadora
ejecuta automáticamente la instalación.

Seguridad:
  - Solo ejecuta 'adb' y 'gradlew.bat' (allowlist cerrada)
  - shell=False siempre (OWASP OS Command Injection Prevention)
  - Solo dispositivos en DISPOSITIVOS_AUTORIZADOS
  - Timeouts estrictos (120s Gradle, 30s ADB)
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from loguru import logger

from computadora.nucleo.kli import DispositivoKli, EstadoKli

# ═══════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════

# Dispositivos autorizados para auto-deploy (serial → nombre amigable)
DISPOSITIVOS_AUTORIZADOS: dict[str, str] = {
    "ZY227SCXF6": "Motorola (USB)",
}

# Rutas
MINIMI_PROJECT = Path(r"C:\Users\woire\AndroidStudioProjects\Minimi")
GRADLEW = MINIMI_PROJECT / "gradlew.bat"
APK_DEBUG = MINIMI_PROJECT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"

# JAVA_HOME requerido para Gradle
JAVA_HOME = r"C:\Program Files\Android\Android Studio\jbr"

# Timeouts
_GRADLE_TIMEOUT = 180  # 3 min para compilación
_ADB_TIMEOUT = 30
_POLL_INTERVAL = 30  # segundos entre polls de dispositivos

# ═══════════════════════════════════════════════
# KliAndroid — Adaptador de dispositivo ADB
# ═══════════════════════════════════════════════

class KliAndroid(DispositivoKli):
    """Dispositivo Android conectado vía ADB (USB o wireless debug)."""

    def __init__(self, device_id: str, nombre: str = ""):
        super().__init__(
            id_kli=f"android_{device_id}",
            nombre=nombre or f"Android {device_id}",
        )
        self.device_id = device_id

    def conectar(self) -> bool:
        """Verifica que el dispositivo esté visible para ADB."""
        try:
            r = subprocess.run(
                ["adb", "devices"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=_ADB_TIMEOUT, shell=False,
            )
            if self.device_id in r.stdout and "device" in r.stdout.split(self.device_id)[1].split("\n")[0]:
                self._estado = EstadoKli.CONECTADO
                logger.info(f"KliAndroid: {self.device_id} conectado")
                return True
            self._estado = EstadoKli.DESCONECTADO
            return False
        except Exception as e:
            self._estado = EstadoKli.ERROR
            logger.debug(f"KliAndroid: error verificando {self.device_id}: {e}")
            return False

    def desconectar(self) -> None:
        self._estado = EstadoKli.DESCONECTADO

    def leer_ohr(self) -> dict[str, Any]:
        """Lee info básica del dispositivo."""
        try:
            r = subprocess.run(
                ["adb", "-s", self.device_id, "shell", "getprop", "ro.product.model"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=_ADB_TIMEOUT, shell=False,
            )
            return {"modelo": r.stdout.strip(), "device_id": self.device_id}
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return {"modelo": "desconocido", "device_id": self.device_id}

    def enviar_pekuda(self, comando: str, **kwargs: Any) -> dict[str, Any]:
        """Ejecuta comandos ADB seguros."""
        if comando == "install_apk":
            return self._install_apk(kwargs.get("apk_path", ""))
        return {"ok": False, "error": f"Comando desconocido: {comando}"}

    def _install_apk(self, apk_path: str) -> dict[str, Any]:
        """Instala un APK en el dispositivo."""
        apk = Path(apk_path)
        if not apk.exists() or not apk.suffix == ".apk":
            return {"ok": False, "error": f"APK no encontrado: {apk_path}"}

        try:
            r = subprocess.run(
                ["adb", "-s", self.device_id, "install", "-r", str(apk)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=_ADB_TIMEOUT, shell=False,
            )
            ok = r.returncode == 0 and "Success" in r.stdout
            return {
                "ok": ok,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout instalando APK"}
        except Exception as e:
            return {"ok": False, "error": str(e)}


# ═══════════════════════════════════════════════
# AUTO-DEPLOYER — Daemon de compilación y despliegue
# ═══════════════════════════════════════════════

class MinimiAutoDeployer:
    """Vigila cambios en Minimi, detecta dispositivo, compila y despliega.

    Ciclo:
    1. Vigila archivos .kt/.xml/.gradle en MINIMI_PROJECT
    2. Cuando detecta cambio → flag build_pendiente = True
    3. Poll periódico: si build_pendiente + dispositivo conectado → build + install
    """

    def __init__(self):
        self._build_pendiente = False
        self._ultimo_cambio_ts: float = 0.0
        self._ultimo_build_ts: float = 0.0
        self._ultimo_hash: str = ""
        self._activo = False
        self._thread: threading.Thread | None = None
        self._dispositivo: KliAndroid | None = None
        self._adb_warned = False  # RF-308: solo advertir una vez si adb no está en PATH

        # Callbacks para notificar a la UI
        self.on_estado: Any = None  # on_estado(str) — "compilando", "instalando", "listo", "error"
        self.on_log: Any = None     # on_log(str) — líneas de log

    def iniciar(self) -> None:
        """Inicia el daemon de vigilancia en background."""
        if self._activo:
            return
        if not MINIMI_PROJECT.exists():
            logger.warning(f"MinimiAutoDeployer: proyecto no encontrado en {MINIMI_PROJECT}")
            return
        if not GRADLEW.exists():
            logger.warning(f"MinimiAutoDeployer: gradlew.bat no encontrado")
            return

        self._activo = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="minimi-deployer"
        )
        self._thread.start()
        logger.info("MinimiAutoDeployer: daemon iniciado")

    def detener(self) -> None:
        """Detiene el daemon."""
        self._activo = False
        logger.info("MinimiAutoDeployer: daemon detenido")

    def notificar_cambio(self) -> None:
        """Llamado externamente cuando se detectan cambios en Minimi."""
        self._build_pendiente = True
        self._ultimo_cambio_ts = time.time()
        logger.info("MinimiAutoDeployer: cambio detectado en Minimi, build pendiente")

    def _emitir_estado(self, estado: str) -> None:
        if self.on_estado:
            try:
                self.on_estado(estado)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

    def _emitir_log(self, msg: str) -> None:
        logger.info(f"MinimiAutoDeployer: {msg}")
        if self.on_log:
            try:
                self.on_log(msg)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

    def _loop(self) -> None:
        """Loop principal del daemon."""
        while self._activo:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"MinimiAutoDeployer: error en tick: {e}")
            # Dormir entre polls
            for _ in range(_POLL_INTERVAL):
                if not self._activo:
                    return
                time.sleep(1)

    def _tick(self) -> None:
        """Un ciclo: verificar cambios → detectar dispositivo → build + install."""
        # 1. Verificar si hay cambios pendientes via snapshot de timestamps
        cambio = self._verificar_cambios()
        if cambio:
            self._build_pendiente = True

        if not self._build_pendiente:
            return

        # 2. Buscar dispositivo autorizado
        dispositivo = self._buscar_dispositivo()
        if dispositivo is None:
            return  # No hay dispositivo, esperar

        # 3. Compilar
        self._emitir_estado("compilando")
        self._emitir_log("Compilando Minimi...")
        ok_build = self._compilar()
        if not ok_build:
            self._emitir_estado("error_build")
            return

        # 4. Instalar
        self._emitir_estado("instalando")
        self._emitir_log(f"Instalando en {dispositivo.nombre}...")
        resultado = dispositivo.enviar_pekuda("install_apk", apk_path=str(APK_DEBUG))
        if resultado["ok"]:
            self._build_pendiente = False
            self._ultimo_build_ts = time.time()
            self._emitir_estado("listo")
            self._emitir_log(f"✓ Minimi instalado en {dispositivo.nombre}")
            # Emitir evento al bus
            self._emitir_evento_bus(dispositivo)
        else:
            self._emitir_estado("error_install")
            self._emitir_log(f"✗ Error instalando: {resultado.get('error', resultado.get('stderr', ''))}")

    def _verificar_cambios(self) -> bool:
        """Verifica si archivos fuente de Minimi cambiaron desde el último build."""
        if not MINIMI_PROJECT.exists():
            return False

        try:
            # Snapshot rápido: max mtime de archivos fuente
            max_mtime: float = 0.0
            src_dir = MINIMI_PROJECT / "app" / "src"
            build_gradle = MINIMI_PROJECT / "app" / "build.gradle.kts"

            if build_gradle.exists():
                max_mtime = max(max_mtime, build_gradle.stat().st_mtime)

            if src_dir.exists():
                for ext in ("*.kt", "*.xml", "*.kts"):
                    for f in src_dir.rglob(ext):
                        try:
                            mt = f.stat().st_mtime
                            if mt > max_mtime:
                                max_mtime = mt
                        except OSError:
                            continue

            if max_mtime > self._ultimo_build_ts and max_mtime != self._ultimo_cambio_ts:
                self._ultimo_cambio_ts = max_mtime
                return True
            return False
        except Exception as e:
            logger.debug(f"MinimiAutoDeployer: error verificando cambios: {e}")
            return False

    def _buscar_dispositivo(self) -> KliAndroid | None:
        """Busca un dispositivo autorizado conectado vía ADB."""
        try:
            r = subprocess.run(
                ["adb", "devices"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=_ADB_TIMEOUT, shell=False,
            )
            if r.returncode != 0:
                return None

            for linea in r.stdout.strip().splitlines()[1:]:
                partes = linea.split()
                if len(partes) >= 2 and partes[1] == "device":
                    serial = partes[0]
                    if serial in DISPOSITIVOS_AUTORIZADOS:
                        kli = KliAndroid(serial, DISPOSITIVOS_AUTORIZADOS[serial])
                        kli._estado = EstadoKli.CONECTADO
                        self._dispositivo = kli
                        return kli
            return None
        except FileNotFoundError:
            if not self._adb_warned:
                logger.info("MinimiAutoDeployer: 'adb' no encontrado en PATH — Android deploy deshabilitado")
                self._adb_warned = True
            return None
        except Exception as e:
            logger.debug(f"MinimiAutoDeployer: error buscando dispositivo: {e}")
            return None

    def _compilar(self) -> bool:
        """Ejecuta gradlew assembleDebug."""
        if not GRADLEW.exists():
            self._emitir_log("gradlew.bat no encontrado")
            return False

        env = os.environ.copy()
        env["JAVA_HOME"] = JAVA_HOME

        try:
            r = subprocess.run(
                [str(GRADLEW), "assembleDebug"],
                cwd=str(MINIMI_PROJECT),
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=_GRADLE_TIMEOUT, shell=False,
                env=env,
            )
            if r.returncode == 0 and APK_DEBUG.exists():
                self._emitir_log("Build exitoso")
                return True
            else:
                self._emitir_log(f"Build falló (exit {r.returncode})")
                # Log últimas líneas del error
                for line in r.stderr.strip().splitlines()[-5:]:
                    self._emitir_log(f"  {line}")
                return False
        except subprocess.TimeoutExpired:
            self._emitir_log("Build timeout (>3 min)")
            return False
        except Exception as e:
            self._emitir_log(f"Error compilando: {e}")
            return False

    def _emitir_evento_bus(self, dispositivo: KliAndroid) -> None:
        """Emite evento al bus de Computadora."""
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("minimi_instalado", {
                "device": dispositivo.device_id,
                "nombre": dispositivo.nombre,
                "apk": str(APK_DEBUG),
                "timestamp": time.time(),
            })
        except Exception as e:
            logger.debug(f"MinimiAutoDeployer: no pudo emitir evento: {e}")


