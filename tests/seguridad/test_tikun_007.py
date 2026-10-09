"""
FP-044 \u05e9\u05c1\u05d5\u05b9\u05de\u05b5\u05e8 \u05e7\u05d5\u05b9\u05dc Shomer Kol \u2014 Tests
RF-109 (Media detection), RF-110 (__MINIMIZAR__), RF-111 (Demo Maljut Whisper), RF-112 (print sanitizer)
"""
import re
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ========================================================
# RF-109: ContextoPantalla.hay_media_activa()
# ========================================================

class TestMediaActiva:
    """Verifica que hay_media_activa detecta t\u00edtulos de media correctamente."""

    def _make_ctx(self, titulo="", proceso=""):
        from computadora.utilidades.windows import ContextoPantalla
        ctx = ContextoPantalla.__new__(ContextoPantalla)
        ctx._titulo_actual = titulo
        ctx._proceso_actual = proceso
        ctx._hwnd_actual = 0
        ctx._historial = []
        ctx._ultimo_cambio = 0.0
        ctx._cambios_recientes = []
        ctx._detener = None
        return ctx

    def test_youtube_in_title(self):
        ctx = self._make_ctx("Mi Video Favorito - YouTube - Google Chrome", "chrome.exe")
        assert ctx.hay_media_activa() is True

    def test_netflix_in_title(self):
        ctx = self._make_ctx("Breaking Bad - Netflix", "msedge.exe")
        assert ctx.hay_media_activa() is True

    def test_spotify_process(self):
        ctx = self._make_ctx("Spotify Premium", "spotify.exe")
        assert ctx.hay_media_activa() is True

    def test_vlc_in_title(self):
        ctx = self._make_ctx("video.mp4 - VLC media player", "vlc.exe")
        assert ctx.hay_media_activa() is True

    def test_twitch_in_title(self):
        ctx = self._make_ctx("Streamer123 - Twitch - Firefox", "firefox.exe")
        assert ctx.hay_media_activa() is True

    def test_vscode_no_media(self):
        ctx = self._make_ctx("nlu.py - Visual Studio Code", "code.exe")
        assert ctx.hay_media_activa() is False

    def test_explorer_no_media(self):
        ctx = self._make_ctx("Documentos", "explorer.exe")
        assert ctx.hay_media_activa() is False

    def test_empty_title(self):
        ctx = self._make_ctx("", "")
        assert ctx.hay_media_activa() is False

    def test_disney_plus(self):
        ctx = self._make_ctx("The Mandalorian - Disney+", "chrome.exe")
        assert ctx.hay_media_activa() is True

    def test_hbo_max(self):
        ctx = self._make_ctx("House of the Dragon - HBO", "msedge.exe")
        assert ctx.hay_media_activa() is True


# ========================================================
# RF-109: Correcciones Whisper sin "golden"
# ========================================================

class TestCorreccionesWhisper:
    """Verifica que golden ya no se corrige a computadora."""

    def test_golden_not_corrected(self):
        from computadora.voz.escucha import _CORRECCIONES_WHISPER
        assert "golden" not in _CORRECCIONES_WHISPER

    def test_gordon_still_corrected(self):
        from computadora.voz.escucha import _CORRECCIONES_WHISPER
        assert _CORRECCIONES_WHISPER.get("gordon") == "computadora"

    def test_ahmed_still_corrected(self):
        from computadora.voz.escucha import _CORRECCIONES_WHISPER
        assert _CORRECCIONES_WHISPER.get("ahmed") == "emet"


# ========================================================
# RF-110: __MINIMIZAR__ interceptor presente
# ========================================================

class TestMinimizarInterceptor:
    """Verifica que __MINIMIZAR__ est\u00e1 en la cadena de interceptores."""

    def test_minimizar_in_al_recibir_respuesta(self):
        from pathlib import Path
        src = Path(__file__).resolve().parents[2] / "computadora" / "interfaz" / "ventana_principal.py"
        code = src.read_text(encoding="utf-8")
        assert '"__MINIMIZAR__"' in code, "__MINIMIZAR__ no encontrado en ventana_principal.py"

    def test_minimizar_calls_showMinimized(self):
        from pathlib import Path
        src = Path(__file__).resolve().parents[2] / "computadora" / "interfaz" / "ventana_principal.py"
        code = src.read_text(encoding="utf-8")
        idx_min = code.index('"__MINIMIZAR__"')
        assert "showMinimized" in code[idx_min:idx_min + 200]


# ========================================================
# RF-111: Demo Maljut Whisper variants
# ========================================================

class TestDemoMaljutWhisperVariants:
    """Verifica que _RE_DEMO_ANIMACIONES reconoce variantes garbled de Whisper."""

    @pytest.fixture
    def regex(self):
        from computadora.cerebro.nlu import _RE_DEMO_ANIMACIONES
        return _RE_DEMO_ANIMACIONES

    def test_demo_de_maljut(self, regex):
        assert regex.search("ejecuta tu demo de maljut")

    def test_demo_de_mal_juzg(self, regex):
        """Whisper garble: 'demo de mal juzg'"""
        assert regex.search("ejecuta tu demo de mal juzg")

    def test_demo_de_malhod(self, regex):
        """Whisper garble: 'demo de malhod'"""
        assert regex.search("demo de malhod")

    def test_demo_de_mal_ajudo(self, regex):
        """Whisper garble: 'demo de mal ajudo'"""
        assert regex.search("demo de mal ajudo")

    def test_demo_de_malhut(self, regex):
        """Whisper garble: 'demo de malhut'"""
        assert regex.search("demo de malhut")

    def test_demo_de_maljud(self, regex):
        """Whisper garble: 'demo de maljud'"""
        assert regex.search("demo de mal jud")

    def test_original_patterns_still_work(self, regex):
        assert regex.search("hazme una demo")
        assert regex.search("lucite")
        assert regex.search("muestrate")

    def test_no_false_positive(self, regex):
        assert not regex.search("hola que tal")
        assert not regex.search("abre chrome")


# ========================================================
# RF-112: Sanitize print() from Ollama
# ========================================================

class TestSanitizePrint:
    """Verifica que _limpiar_para_voz extrae texto de print()."""

    @pytest.fixture
    def cerebro(self):
        """Crea CerebroComputadora minimal para testear _limpiar_para_voz."""
        from computadora.cerebro.nlu import CerebroComputadora

        class FakeConfig:
            def obtener(self, k, default=None):
                defaults = {
                    "copilot.api_key": "",
                    "copilot.modelo": "gpt-4",
                    "ollama.modelo": "gemma3:4b",
                    "ollama.url": "http://localhost:11434",
                    "personalidad.nombre": "Computadora",
                    "personalidad.titulo_amo": "señor",
                }
                return defaults.get(k, default)

        return CerebroComputadora(FakeConfig())

    def test_print_simple(self, cerebro):
        inp = 'print("Hola señor, todo bien")'
        out = cerebro._limpiar_para_voz(inp)
        assert out == "Hola señor, todo bien"

    def test_print_single_quotes(self, cerebro):
        inp = "print('Entendido señor')"
        out = cerebro._limpiar_para_voz(inp)
        assert out == "Entendido señor"

    def test_console_log(self, cerebro):
        inp = 'console.log("Test output")'
        out = cerebro._limpiar_para_voz(inp)
        assert out == "Test output"

    def test_normal_text_unchanged(self, cerebro):
        inp = "Hola señor, todo bien."
        out = cerebro._limpiar_para_voz(inp)
        assert out == "Hola señor, todo bien."

    def test_echo(self, cerebro):
        inp = 'echo("Mensaje de prueba")'
        out = cerebro._limpiar_para_voz(inp)
        assert out == "Mensaje de prueba"


# ========================================================
# Part E: librosa warned flag exists
# ========================================================

class TestLibrosaWarnedFlag:
    """Verifica que HiloEscucha tiene flag para limitar spam de librosa."""

    def test_flag_exists(self):
        import inspect
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha.__init__)
        assert "_librosa_warned" in src

    def test_flag_used_in_embedding(self):
        import inspect
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._extraer_embedding)
        assert "_librosa_warned" in src


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

