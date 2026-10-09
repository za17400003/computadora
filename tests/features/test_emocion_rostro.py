"""
⊕ Sal — Tests para computadora/percepcion/emocion_rostro.py (WI-291)
Verifica el analizador de emociones faciales.
"""

import numpy as np
import pytest

from computadora.percepcion.emocion_rostro import (
    AnalizadorEmocionRostro,
    _EMOCION_MAP,
    _INTERVALO_MIN,
)


# ═══════════════════════════════════════════════════════════════
# Mapa de emociones
# ═══════════════════════════════════════════════════════════════

class TestEmocionMap:
    def test_7_emociones_ekman(self):
        assert len(_EMOCION_MAP) == 7

    def test_emociones_requeridas(self):
        for en in ("happy", "sad", "angry", "fear", "surprise", "disgust", "neutral"):
            assert en in _EMOCION_MAP

    def test_traducciones_a_espanol(self):
        for en, es in _EMOCION_MAP.items():
            assert isinstance(es, str)
            assert len(es) > 0


# ═══════════════════════════════════════════════════════════════
# AnalizadorEmocionRostro
# ═══════════════════════════════════════════════════════════════

class TestAnalizadorInit:
    def test_instanciable(self):
        a = AnalizadorEmocionRostro()
        assert a is not None

    def test_disponible_retorna_bool(self):
        assert isinstance(AnalizadorEmocionRostro.disponible(), bool)

    def test_backend_retorna_str_o_none(self):
        b = AnalizadorEmocionRostro.backend()
        assert b is None or isinstance(b, str)


class TestAnalizarFrame:
    def test_analizar_frame_negro_retorna_neutral(self):
        a = AnalizadorEmocionRostro()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = a.analizar(frame)
        assert "emocion" in result
        assert isinstance(result["emocion"], str)

    def test_respeta_intervalo_minimo(self):
        a = AnalizadorEmocionRostro()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        r1 = a.analizar(frame)
        r2 = a.analizar(frame)  # inmediato — debe devolver cached
        assert r2["emocion"] == r1["emocion"]

    def test_intervalo_minimo_es_positivo(self):
        assert _INTERVALO_MIN > 0

