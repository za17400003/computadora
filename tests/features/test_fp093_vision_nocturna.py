"""
FP-093 — אור בחושך (Or BaJóshej) — Tests de visión nocturna automática.
RF-323: brillo_medio en leer_ohr()
RF-324: Auto-CLAHE si brillo < 50
RF-326: Frame diff siempre sobre frame crudo (anti-falsos positivos)
RF-327: Guardian manual conecta cámara
"""
import numpy as np
import pytest


# ═══ Mock de cv2 para tests sin OpenCV real ═══

class _MockCLAHE:
    def apply(self, img):
        return np.clip(img.astype(np.int16) + 60, 0, 255).astype(np.uint8)


class _MockCap:
    """Simula VideoCapture con brillo configurable."""

    def __init__(self, brillo: int = 128):
        self._brillo = brillo
        self._abierta = True

    def isOpened(self):
        return self._abierta

    def read(self):
        frame = np.full((480, 640, 3), self._brillo, dtype=np.uint8)
        return True, frame

    def release(self):
        self._abierta = False


@pytest.fixture
def kli_camara(monkeypatch):
    """Crea KliCamara con mock de cv2."""
    import computadora.habilidades.vision as vis
    monkeypatch.setattr(vis, "_CV2_DISPONIBLE", True)

    # Mock cv2 functions
    class _cv2:
        @staticmethod
        def cvtColor(frame, code):
            return np.mean(frame, axis=2).astype(np.uint8)

        @staticmethod
        def absdiff(a, b):
            return np.abs(a.astype(np.int16) - b.astype(np.int16)).astype(np.uint8)

        @staticmethod
        def VideoCapture(idx):
            return _MockCap()

        @staticmethod
        def createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)):
            return _MockCLAHE()

        @staticmethod
        def equalizeHist(img):
            return np.clip(img.astype(np.int16) + 60, 0, 255).astype(np.uint8)

        COLOR_BGR2GRAY = 6

    monkeypatch.setattr(vis, "cv2", _cv2)

    from computadora.habilidades.vision import KliCamara
    cam = KliCamara()
    cam._cap = _MockCap()
    cam._clahe = _MockCLAHE()
    cam._estado = vis.EstadoKli.CONECTADO
    return cam


# ═══ RF-323: brillo_medio en retorno de leer_ohr() ═══

class TestRF323_BrilloMedio:
    def test_brillo_presente_en_respuesta(self, kli_camara):
        resultado = kli_camara.leer_ohr()
        assert "brillo_medio" in resultado
        assert isinstance(resultado["brillo_medio"], float)

    def test_brillo_correcto_frame_claro(self, kli_camara):
        kli_camara._cap = _MockCap(brillo=200)
        resultado = kli_camara.leer_ohr()
        assert resultado["brillo_medio"] == pytest.approx(200.0, abs=1.0)

    def test_brillo_correcto_frame_oscuro(self, kli_camara):
        kli_camara._cap = _MockCap(brillo=20)
        resultado = kli_camara.leer_ohr()
        assert resultado["brillo_medio"] == pytest.approx(20.0, abs=1.0)


# ═══ RF-324: Auto-CLAHE en baja luminosidad ═══

class TestRF324_AutoCLAHE:
    def test_nocturno_auto_activado_brillo_bajo(self, kli_camara):
        kli_camara._cap = _MockCap(brillo=30)
        resultado = kli_camara.leer_ohr()
        assert resultado["nocturno_auto"] is True

    def test_nocturno_auto_desactivado_brillo_alto(self, kli_camara):
        kli_camara._cap = _MockCap(brillo=180)
        resultado = kli_camara.leer_ohr()
        assert resultado["nocturno_auto"] is False

    def test_histeresis_evita_parpadeo(self, kli_camara):
        """Brillo justo arriba del umbral no desactiva si fue nocturno."""
        kli_camara._cap = _MockCap(brillo=30)
        kli_camara.leer_ohr()  # activa nocturno
        assert kli_camara._modo_nocturno_auto is True

        # Brillo sube a 55 (< 50+15=65) → NO debe desactivar por histéresis
        kli_camara._cap = _MockCap(brillo=55)
        resultado = kli_camara.leer_ohr()
        assert resultado["nocturno_auto"] is True

        # Brillo sube a 70 (> 65) → SÍ desactiva
        kli_camara._cap = _MockCap(brillo=70)
        resultado = kli_camara.leer_ohr()
        assert resultado["nocturno_auto"] is False


# ═══ RF-326: Frame diff siempre sobre frame crudo ═══

class TestRF326_FrameDiffConsistencia:
    def test_sin_falso_positivo_transicion_clahe(self, kli_camara):
        """Transición de brillo alto→bajo no debe disparar falso movimiento."""
        # Frame 1: brillo alto (sin CLAHE)
        kli_camara._cap = _MockCap(brillo=150)
        kli_camara.leer_ohr()

        # Frame 2: brillo bajo (con CLAHE) — mismo contenido estático
        kli_camara._cap = _MockCap(brillo=30)
        resultado = kli_camara.leer_ohr()

        # El diff del brillo (150 vs 30) SÍ genera "cambio" real en la escena
        # pero lo importante es que _frame_anterior se guarda crudo
        # Verificamos que _frame_anterior NO está CLAHE-enhanced
        assert kli_camara._frame_anterior is not None
        brillo_almacenado = float(np.mean(kli_camara._frame_anterior))
        # Debe ser ~30 (frame crudo), no ~90 (CLAHE-enhanced)
        assert brillo_almacenado < 50

    def test_frame_anterior_siempre_crudo(self, kli_camara):
        """Múltiples frames oscuros: _frame_anterior sigue siendo crudo."""
        for _ in range(5):
            kli_camara._cap = _MockCap(brillo=25)
            kli_camara.leer_ohr()

        brillo_almacenado = float(np.mean(kli_camara._frame_anterior))
        assert brillo_almacenado == pytest.approx(25.0, abs=2.0)

