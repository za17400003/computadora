"""Tests para FP-096: MinimiAutoDeployer + KliAndroid."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from computadora.habilidades.android_deploy import (
    DISPOSITIVOS_AUTORIZADOS,
    KliAndroid,
    MinimiAutoDeployer,
    _ADB_TIMEOUT,
)
from computadora.nucleo.kli import EstadoKli


# ═══════════════════════════════════════════════
# KliAndroid
# ═══════════════════════════════════════════════

class TestKliAndroid:
    """Tests para el adaptador de dispositivo Android."""

    def test_init_sets_id_and_name(self):
        kli = KliAndroid("ABC123", "Mi Motorola")
        assert kli.id_kli == "android_ABC123"
        assert kli.nombre == "Mi Motorola"
        assert kli.device_id == "ABC123"
        assert kli.estado == EstadoKli.DESCONECTADO

    def test_init_default_name(self):
        kli = KliAndroid("ABC123")
        assert kli.nombre == "Android ABC123"

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_conectar_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\nZY227SCXF6\tdevice\n\n",
            returncode=0,
        )
        kli = KliAndroid("ZY227SCXF6")
        assert kli.conectar() is True
        assert kli.estado == EstadoKli.CONECTADO
        mock_run.assert_called_once_with(
            ["adb", "devices"],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=_ADB_TIMEOUT, shell=False,
        )

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_conectar_device_not_found(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\n\n",
            returncode=0,
        )
        kli = KliAndroid("ZY227SCXF6")
        assert kli.conectar() is False
        assert kli.estado == EstadoKli.DESCONECTADO

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_conectar_unauthorized(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\nZY227SCXF6\tunauthorized\n\n",
            returncode=0,
        )
        kli = KliAndroid("ZY227SCXF6")
        assert kli.conectar() is False

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_conectar_exception(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=30)
        kli = KliAndroid("ZY227SCXF6")
        assert kli.conectar() is False
        assert kli.estado == EstadoKli.ERROR

    def test_desconectar(self):
        kli = KliAndroid("ZY227SCXF6")
        kli._estado = EstadoKli.CONECTADO
        kli.desconectar()
        assert kli.estado == EstadoKli.DESCONECTADO

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_leer_ohr(self, mock_run):
        mock_run.return_value = MagicMock(stdout="moto g84 5G\n", returncode=0)
        kli = KliAndroid("ZY227SCXF6")
        datos = kli.leer_ohr()
        assert datos["modelo"] == "moto g84 5G"
        assert datos["device_id"] == "ZY227SCXF6"

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_install_apk_success(self, mock_run, tmp_path):
        apk = tmp_path / "test.apk"
        apk.write_bytes(b"fake apk")
        mock_run.return_value = MagicMock(
            stdout="Performing Streamed Install\nSuccess\n",
            stderr="",
            returncode=0,
        )
        kli = KliAndroid("ZY227SCXF6")
        result = kli.enviar_pekuda("install_apk", apk_path=str(apk))
        assert result["ok"] is True

    def test_install_apk_missing_file(self):
        kli = KliAndroid("ZY227SCXF6")
        result = kli.enviar_pekuda("install_apk", apk_path="/no/existe.apk")
        assert result["ok"] is False
        assert "no encontrado" in result["error"]

    def test_unknown_command(self):
        kli = KliAndroid("ZY227SCXF6")
        result = kli.enviar_pekuda("reboot")
        assert result["ok"] is False
        assert "desconocido" in result["error"]


# ═══════════════════════════════════════════════
# MinimiAutoDeployer
# ═══════════════════════════════════════════════

class TestMinimiAutoDeployer:
    """Tests para el daemon de auto-deploy."""

    def test_init_defaults(self):
        deployer = MinimiAutoDeployer()
        assert deployer._build_pendiente is False
        assert deployer._activo is False

    def test_notificar_cambio_sets_flag(self):
        deployer = MinimiAutoDeployer()
        deployer.notificar_cambio()
        assert deployer._build_pendiente is True
        assert deployer._ultimo_cambio_ts > 0

    def test_detener(self):
        deployer = MinimiAutoDeployer()
        deployer._activo = True
        deployer.detener()
        assert deployer._activo is False

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_buscar_dispositivo_found(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\nZY227SCXF6\tdevice\n\n",
            returncode=0,
        )
        deployer = MinimiAutoDeployer()
        dev = deployer._buscar_dispositivo()
        assert dev is not None
        assert dev.device_id == "ZY227SCXF6"

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_buscar_dispositivo_none(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\n\n",
            returncode=0,
        )
        deployer = MinimiAutoDeployer()
        assert deployer._buscar_dispositivo() is None

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_buscar_dispositivo_unauthorized_serial(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="List of devices attached\nUNKNOWN123\tdevice\n\n",
            returncode=0,
        )
        deployer = MinimiAutoDeployer()
        assert deployer._buscar_dispositivo() is None

    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_buscar_dispositivo_adb_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("adb not found")
        deployer = MinimiAutoDeployer()
        assert deployer._buscar_dispositivo() is None

    def test_emitir_estado_callback(self):
        deployer = MinimiAutoDeployer()
        estados = []
        deployer.on_estado = lambda e: estados.append(e)
        deployer._emitir_estado("compilando")
        assert estados == ["compilando"]

    def test_emitir_log_callback(self):
        deployer = MinimiAutoDeployer()
        logs = []
        deployer.on_log = lambda m: logs.append(m)
        deployer._emitir_log("test message")
        assert len(logs) == 1
        assert "test message" in logs[0]

    @patch("computadora.habilidades.android_deploy.GRADLEW")
    @patch("computadora.habilidades.android_deploy.subprocess.run")
    def test_compilar_success(self, mock_run, mock_gradlew):
        mock_gradlew.exists.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        deployer = MinimiAutoDeployer()
        with patch("computadora.habilidades.android_deploy.APK_DEBUG") as mock_apk:
            mock_apk.exists.return_value = True
            assert deployer._compilar() is True

    @patch("computadora.habilidades.android_deploy.GRADLEW")
    def test_compilar_no_gradlew(self, mock_gradlew):
        mock_gradlew.exists.return_value = False
        deployer = MinimiAutoDeployer()
        assert deployer._compilar() is False

    def test_dispositivos_autorizados_contains_motorola(self):
        assert "ZY227SCXF6" in DISPOSITIVOS_AUTORIZADOS

    def test_security_shell_false(self):
        """Verifica que ningún subprocess.run use shell=True."""
        import inspect
        import computadora.habilidades.android_deploy as mod
        source = inspect.getsource(mod)
        assert "shell=True" not in source, "SEGURIDAD: shell=True detectado en android_deploy.py"

    @patch("computadora.habilidades.android_deploy.MINIMI_PROJECT")
    def test_iniciar_proyecto_no_existe(self, mock_project):
        mock_project.exists.return_value = False
        deployer = MinimiAutoDeployer()
        deployer.iniciar()
        assert deployer._activo is False

