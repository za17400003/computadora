"""
Tests para FP-071: Einayim VeOznayim — Percepción unificada.
RF-246 a RF-253.
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ═══════════════════════════════════════════
# RF-246: Shomer HaLashón — Filtro "Cero Español"
# ═══════════════════════════════════════════

class TestRF246FilterCeroEspanol:
    """Verifica que frases sin español reconocible se descartan."""

    def _filtrar(self, texto, nsp=0.0):
        from computadora.voz.escucha import _es_falso_positivo_conversacion
        return _es_falso_positivo_conversacion(texto, nsp)

    def test_hu_trails_team_3_descartado(self):
        """Bug original: 'hu trails team. 3' debe filtrarse."""
        motivo = self._filtrar("hu trails team. 3")
        assert "cero_español" in motivo

    def test_random_english_words_descartado(self):
        motivo = self._filtrar("blockchain crypto mining")
        assert "cero_español" in motivo

    def test_frase_espanol_valida_pasa(self):
        """Frases en español legítimo no deben filtrarse."""
        assert self._filtrar("como estás hoy") == ""

    def test_frase_con_acentos_pasa(self):
        assert self._filtrar("está bien así") == ""

    def test_frase_mixta_espanol_ingles_pasa_si_tiene_espanol(self):
        """Si hay al menos una palabra española, no filtra por cero_español."""
        assert "cero_español" not in self._filtrar("oye crypto algo")

    def test_una_sola_palabra_no_aplica(self):
        """RF-246 solo aplica para ≥2 palabras."""
        # Una sola palabra se maneja por otros filtros, no por cero_español
        motivo = self._filtrar("blockchain")
        assert "cero_español" not in motivo or motivo == ""  # handled by other filter

    def test_numeros_solos_no_cuentan_como_espanol(self):
        """'3 5 7' — solo números, no hay palabras alfa → no aplica (no hay solo_alfa)."""
        motivo = self._filtrar("3 5 7")
        assert "cero_español" not in motivo  # no alpha words to check

    def test_frase_cortas_validas_pasan(self):
        assert self._filtrar("sí claro bueno") == ""
        assert self._filtrar("ya todo listo") == ""


# ═══════════════════════════════════════════
# RF-250: Ruaj HaAdam — Emoción por voz
# ═══════════════════════════════════════════

class TestRF250EmocionVoz:
    """Tests para detección de emoción por heurísticas de audio."""

    def test_analizar_silencio(self):
        from computadora.percepcion.emocion_voz import analizar_emocion_voz
        audio = np.zeros(16000, dtype=np.float32)  # 1 seg silencio
        resultado = analizar_emocion_voz(audio, sr=16000)
        assert "emocion" in resultado
        assert "confianza" in resultado
        assert resultado["emocion"] in ("calma", "tristeza", "estrés", "alegría", "enojo")

    def test_analizar_audio_corto(self):
        from computadora.percepcion.emocion_voz import analizar_emocion_voz
        audio = np.random.randn(1000).astype(np.float32) * 0.01
        resultado = analizar_emocion_voz(audio, sr=16000)
        assert "emocion" in resultado

    def test_analizar_con_palabras(self):
        from computadora.percepcion.emocion_voz import analizar_emocion_voz
        audio = np.random.randn(32000).astype(np.float32) * 0.1
        resultado = analizar_emocion_voz(audio, sr=16000, n_palabras=10, duracion_seg=2.0)
        assert resultado["detalles"]["velocidad_palabras_seg"] == 5.0


# ═══════════════════════════════════════════
# RF-251: Tiferet HaPertsuf — Emoción facial
# ═══════════════════════════════════════════

class TestRF251EmocionRostro:
    def test_instancia_sin_backend(self):
        """AnalizadorEmocionRostro debe instanciarse aunque no haya backend."""
        from computadora.percepcion.emocion_rostro import AnalizadorEmocionRostro
        analizador = AnalizadorEmocionRostro()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        resultado = analizador.analizar(frame)
        assert "emocion" in resultado


# ═══════════════════════════════════════════
# RF-252: Dérej HaAdam — Perfil de conducta
# ═══════════════════════════════════════════

class TestRF252PerfilConducta:
    def test_registrar_y_resumen(self, tmp_path, monkeypatch):
        import computadora.percepcion.perfil_conducta as mod
        monkeypatch.setattr(mod, "_PERFIL_PATH", tmp_path / "perfil_conducta.json")
        monkeypatch.setattr(mod, "_DATOS_DIR", tmp_path)

        perfil = mod.PerfilConducta()
        perfil.registrar_interaccion(tipo="voz", duracion_seg=5.0, emocion="alegría", n_palabras=10)
        perfil.registrar_interaccion(tipo="voz", duracion_seg=3.0, emocion="calma", n_palabras=5)

        resumen = perfil.obtener_resumen()
        assert resumen["total_interacciones"] == 2
        assert resumen["duracion_promedio_seg"] == 4.0

    def test_contexto_actual(self, tmp_path, monkeypatch):
        import computadora.percepcion.perfil_conducta as mod
        monkeypatch.setattr(mod, "_PERFIL_PATH", tmp_path / "perfil_conducta.json")
        monkeypatch.setattr(mod, "_DATOS_DIR", tmp_path)

        perfil = mod.PerfilConducta()
        perfil.registrar_interaccion()
        ctx = perfil.obtener_contexto_actual()
        assert "franja_actual" in ctx
        assert ctx["total_interacciones"] == 1

    def test_persistencia(self, tmp_path, monkeypatch):
        import computadora.percepcion.perfil_conducta as mod
        path = tmp_path / "perfil_conducta.json"
        monkeypatch.setattr(mod, "_PERFIL_PATH", path)
        monkeypatch.setattr(mod, "_DATOS_DIR", tmp_path)

        perfil1 = mod.PerfilConducta()
        perfil1.registrar_interaccion(tipo="voz")
        assert path.exists()

        perfil2 = mod.PerfilConducta()
        assert len(perfil2._interacciones) == 1


# ═══════════════════════════════════════════
# RF-249: Hakarat Panim — Reconocimiento facial
# ═══════════════════════════════════════════

class TestRF249ReconocedorRostro:
    def test_instancia_sin_face_recognition(self):
        from computadora.percepcion.rostro import ReconocedorRostro
        rec = ReconocedorRostro()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        resultado = rec.analizar_frame(frame)
        # Sin face_recognition instalado, debe retornar no_disponible
        if not rec.disponible():
            assert resultado["resultado"] == "no_disponible"

    def test_propietario_no_enrollado(self):
        from computadora.percepcion.rostro import ReconocedorRostro
        rec = ReconocedorRostro()
        assert not rec.propietario_enrollado


# ═══════════════════════════════════════════
# RF-253: Yajad — Perceptor unificado
# ═══════════════════════════════════════════

class TestRF253PerceptorDaat:
    def test_instancia(self):
        from computadora.percepcion.perceptor import PerceptorDaat, SnapshotPercepcion
        p = PerceptorDaat()
        assert isinstance(p.ultimo_snapshot, SnapshotPercepcion)

    def test_procesar_audio(self):
        from computadora.percepcion.perceptor import PerceptorDaat
        p = PerceptorDaat()
        audio = np.zeros(16000, dtype=np.float32)
        snap = p.procesar_audio(audio, sr=16000, es_propietario=False)
        assert snap.emocion_voz in ("calma", "tristeza", "estrés", "alegría", "enojo")
        assert not snap.voz_propietario

    def test_contexto_para_prompt(self):
        from computadora.percepcion.perceptor import PerceptorDaat
        p = PerceptorDaat()
        ctx = p.contexto_para_prompt()
        assert isinstance(ctx, str)

    def test_registrar_tacto(self):
        from computadora.percepcion.perceptor import PerceptorDaat
        p = PerceptorDaat()
        p.registrar_tacto("caricia")  # no debe fallar

