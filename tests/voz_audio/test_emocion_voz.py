"""
⊕ Sal — Tests para golem/percepcion/emocion_voz.py (WI-291)
Verifica la detección de emoción por voz (heurísticas).
"""

import numpy as np
import pytest

from computadora.percepcion.emocion_voz import (
    _PITCH_ALTO,
    _PITCH_BAJO,
    _RMS_ALTO,
    _RMS_BAJO,
    _extraer_pitch,
    _extraer_rms,
    analizar_emocion_voz,
)


# ═══════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════

class TestConstantes:
    def test_pitch_rangos_coherentes(self):
        assert 0 < _PITCH_BAJO < _PITCH_ALTO

    def test_rms_rangos_coherentes(self):
        assert 0 < _RMS_BAJO < _RMS_ALTO


# ═══════════════════════════════════════════════════════════════
# _extraer_rms
# ═══════════════════════════════════════════════════════════════

class TestExtraerRms:
    def test_silencio_retorna_cero(self):
        audio = np.zeros(16000, dtype=np.float32)
        assert _extraer_rms(audio) == 0.0

    def test_audio_no_vacio_retorna_positivo(self):
        audio = np.random.randn(16000).astype(np.float32) * 0.1
        rms = _extraer_rms(audio)
        assert rms > 0

    def test_vacio_retorna_cero(self):
        audio = np.array([], dtype=np.float32)
        assert _extraer_rms(audio) == 0.0

    def test_rms_capped_a_1(self):
        # Audio extremo
        audio = np.ones(100, dtype=np.float32) * 5.0
        rms = _extraer_rms(audio)
        assert rms <= 1.0


# ═══════════════════════════════════════════════════════════════
# _extraer_pitch
# ═══════════════════════════════════════════════════════════════

class TestExtraerPitch:
    def test_audio_corto_retorna_cero(self):
        audio = np.zeros(100, dtype=np.float32)
        assert _extraer_pitch(audio, 16000) == 0.0

    def test_retorna_float(self):
        audio = np.random.randn(16000).astype(np.float32)
        pitch = _extraer_pitch(audio, 16000)
        assert isinstance(pitch, float)


# ═══════════════════════════════════════════════════════════════
# analizar_emocion_voz
# ═══════════════════════════════════════════════════════════════

class TestAnalizarEmocionVoz:
    def test_retorna_dict_con_campos(self):
        audio = np.random.randn(16000).astype(np.float32) * 0.05
        result = analizar_emocion_voz(audio, sr=16000)
        assert "emocion" in result
        assert "confianza" in result
        assert "detalles" in result

    def test_emocion_es_string_valido(self):
        audio = np.zeros(16000, dtype=np.float32)
        result = analizar_emocion_voz(audio, sr=16000)
        assert result["emocion"] in ("calma", "alegría", "estrés", "enojo", "tristeza")

    def test_confianza_en_rango(self):
        audio = np.random.randn(16000).astype(np.float32) * 0.05
        result = analizar_emocion_voz(audio, sr=16000)
        assert 0.0 <= result["confianza"] <= 1.0

    def test_detalles_contiene_pitch_y_rms(self):
        audio = np.random.randn(16000).astype(np.float32)
        result = analizar_emocion_voz(audio, sr=16000)
        det = result["detalles"]
        assert "pitch_hz" in det
        assert "rms" in det

    def test_silencio_retorna_emocion_valida(self):
        audio = np.zeros(16000, dtype=np.float32)
        result = analizar_emocion_voz(audio, sr=16000)
        assert result["emocion"] in ("calma", "alegría", "estrés", "enojo", "tristeza")

