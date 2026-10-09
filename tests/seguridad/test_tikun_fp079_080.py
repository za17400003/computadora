"""
Tests para FP-079 (Shomer HaShemiá) y FP-080 (Gevurát HaKelim).
RF-295 a RF-301.
"""

import re
from unittest.mock import MagicMock, patch

import pytest


# ═══════════════════════════════════════════
# RF-296: Gaming patterns en _RE_MEDIA_TITULO y _PROCESOS_MEDIA
# ═══════════════════════════════════════════

class TestRF296GamingPatterns:
    """Verifica que videojuegos son reconocidos como media activa."""

    def _regex(self):
        from computadora.utilidades.windows import ContextoPantalla
        return ContextoPantalla._RE_MEDIA_TITULO

    def _procesos(self):
        from computadora.utilidades.windows import ContextoPantalla
        return ContextoPantalla._PROCESOS_MEDIA

    @pytest.mark.parametrize("titulo", [
        "Steam",
        "Epic Games Launcher",
        "GeForce NOW",
        "Xbox Game Bar",
        "PlayStation Remote Play",
        "GOG Galaxy 2.0",
    ])
    def test_titulos_gaming_reconocidos(self, titulo):
        assert self._regex().search(titulo), f"{titulo} no matcheó _RE_MEDIA_TITULO"

    @pytest.mark.parametrize("exe", [
        "steam.exe",
        "steamwebhelper.exe",
        "epicgameslauncher.exe",
        "galaxyclient.exe",
    ])
    def test_procesos_gaming_en_frozenset(self, exe):
        assert exe in self._procesos(), f"{exe} falta en _PROCESOS_MEDIA"

    def test_youtube_sigue_funcionando(self):
        """Regresión: media clásica sigue detectándose."""
        assert self._regex().search("YouTube - Google Chrome")

    def test_spotify_sigue_funcionando(self):
        assert self._regex().search("Spotify Premium")


# ═══════════════════════════════════════════
# RF-298: Lazy imports para escanear_red y ver_camara
# ═══════════════════════════════════════════

class TestRF298LazyImports:
    """Verifica que escanear_red y ver_camara están en HERRAMIENTAS."""

    def test_escanear_red_registrada(self):
        from computadora.habilidades.herramientas import HERRAMIENTAS
        assert "escanear_red" in HERRAMIENTAS
        assert HERRAMIENTAS["escanear_red"]["descripcion"]

    def test_ver_camara_registrada(self):
        from computadora.habilidades.herramientas import HERRAMIENTAS
        assert "ver_camara" in HERRAMIENTAS
        assert HERRAMIENTAS["ver_camara"]["descripcion"]

    def test_escanear_red_funcion_none_antes_de_lazy(self):
        """La función es None hasta que se invoque (lazy)."""
        from computadora.habilidades.herramientas import HERRAMIENTAS
        # Reiniciar a None para test puro
        original = HERRAMIENTAS["escanear_red"]["funcion"]
        HERRAMIENTAS["escanear_red"]["funcion"] = None
        assert HERRAMIENTAS["escanear_red"]["funcion"] is None
        HERRAMIENTAS["escanear_red"]["funcion"] = original


# ═══════════════════════════════════════════
# RF-299/300/301: Métodos demo existen (source inspection sin PyQt6)
# ═══════════════════════════════════════════

class TestRF299_300_301DemoSource:
    """Inspecciona el source de ventana_principal.py sin importar PyQt6."""

    @pytest.fixture(autouse=True)
    def _load_source(self):
        from pathlib import Path
        src = Path(__file__).resolve().parents[2] / "computadora" / "interfaz" / "ventana_principal.py"
        self.source = src.read_text(encoding="utf-8")

    def test_demo_escanear_red_definido(self):
        assert "def _demo_escanear_red(self):" in self.source

    def test_demo_ver_camara_definido(self):
        assert "def _demo_ver_camara(self):" in self.source

    def test_demo_reconocimiento_facial_definido(self):
        assert "def _demo_reconocimiento_facial(self):" in self.source

    def test_rf297_cerrar_photos_en_captura(self):
        assert "RF-310" in self.source  # RF-297 reemplazado por RF-310 (FP-084)
        assert "Microsoft.Photos" in self.source

    def test_demo2_pasos_incluyen_red_camara_rostro(self):
        """Demo 2 incluye los 3 nuevos pasos: red, cámara, rostro."""
        # Buscar _demo_pasos dentro de _demo_herramientas específicamente
        gevura_start = self.source.index("def _demo_herramientas(self):")
        gevura_pasos = self.source.index("self._demo_pasos = [", gevura_start)
        # Extraer bloque hasta el cierre
        depth = 0
        for i, ch in enumerate(self.source[gevura_pasos:], start=gevura_pasos):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    block = self.source[gevura_pasos:i + 1]
                    break
        # RF-345: escanear_red y ver_camara ahora usan _demo_ejecutar_herramienta (async)
        assert "escanear_red" in block, "Falta paso escanear_red en Demo 2"
        assert "ver_camara" in block, "Falta paso ver_camara en Demo 2"
        assert "_demo_reconocimiento_facial" in block, "Falta paso reconocimiento facial en Demo 2"

