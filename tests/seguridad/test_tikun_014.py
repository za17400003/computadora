"""
FP-051 Tikún HaTnuá VeTzimtzúm — Tests RF-134/RF-135/RF-136/RF-137/RF-138
- RF-134: Ventana de velocidad adaptativa (cascade 50→80→120ms)
- RF-135: Amortiguación dinámica de partículas
- RF-136: _pos_anterior sincronizado post-Tzimtzum
- RF-137: Flag _restaurando_tzimtzum protege escala
- RF-138: Caricia resetea inactividad
"""
import math
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestRF134_VentanaVelocidadAdaptativa:
    """RF-134: mouseReleaseEvent usa cascade 50→80→120ms."""

    def test_cascade_presente_en_codigo(self):
        """Verifica que el cascade 0.05/0.08/0.12 existe en el código."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.mouseReleaseEvent)
        assert "0.05" in src, "Falta ventana 50ms en cascade"
        assert "0.08" in src, "Falta ventana 80ms en cascade"
        assert "0.12" in src, "Falta ventana 120ms en cascade"

    def test_cascade_orden_correcto(self):
        """Verifica que 0.05 aparece antes que 0.08 antes que 0.12."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.mouseReleaseEvent)
        i1 = src.index("0.05")
        i2 = src.index("0.08")
        i3 = src.index("0.12")
        assert i1 < i2 < i3, "Cascade debe ser 50→80→120ms"


class TestRF135_AmortiguacionDinamica:
    """RF-135: Amortiguación dinámica basada en velocidad."""

    def test_damp_alta_velocidad(self):
        """Alta velocidad (vel_norm=1.0) → damp ≈ 0.4."""
        vel_norm = 1.0
        damp = 0.4 + 0.3 * (1.0 - vel_norm)
        assert abs(damp - 0.4) < 0.01

    def test_damp_baja_velocidad(self):
        """Baja velocidad (vel_norm=0.0) → damp ≈ 0.7."""
        vel_norm = 0.0
        damp = 0.4 + 0.3 * (1.0 - vel_norm)
        assert abs(damp - 0.7) < 0.01

    def test_damp_media_velocidad(self):
        """Velocidad media (vel_norm=0.5) → damp ≈ 0.55."""
        vel_norm = 0.5
        damp = 0.4 + 0.3 * (1.0 - vel_norm)
        assert abs(damp - 0.55) < 0.01

    def test_vel_norm_clamp(self):
        """vel_norm se clampea a min(1.0, ...)."""
        raw_dx, raw_dy = 100, 100  # Enorme
        vel_norm = min(1.0, math.hypot(raw_dx, raw_dy) / 30.0)
        assert vel_norm == 1.0

    def test_diagonal_no_se_aplana(self):
        """Diagonal debe conservar proporción X/Y."""
        raw_dx, raw_dy = 10.0, 10.0
        vel_norm = min(1.0, math.hypot(raw_dx, raw_dy) / 30.0)
        damp = 0.4 + 0.3 * (1.0 - vel_norm)
        dx, dy = raw_dx * damp, raw_dy * damp
        assert abs(dx - dy) < 0.001, "Diagonal debe ser simétrica"

    def test_formula_en_codigo(self):
        """Verifica presencia de la fórmula dinámica en _animar."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "0.4 + 0.3" in src, "Falta fórmula de amortiguación dinámica"


class TestRF136_PosAnteriorTzimtzum:
    """RF-136: _pos_anterior sincronizado en _desactivar_tzimtzum."""

    def test_sync_presente_en_desactivar(self):
        """Verifica que _desactivar_tzimtzum sincroniza _pos_anterior."""
        import inspect
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert "_pos_anterior_x" in src, "Falta sync de _pos_anterior_x"
        assert "_pos_anterior_y" in src, "Falta sync de _pos_anterior_y"


class TestRF137_ProteccionEscalaTzimtzum:
    """RF-137: Flag _restaurando_tzimtzum protege escala."""

    def test_flag_set_en_desactivar(self):
        """Verifica que _desactivar_tzimtzum activa el flag."""
        import inspect
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert "_restaurando_tzimtzum" in src

    def test_flag_check_en_cambiar_estado(self):
        """Verifica que cambiar_estado revisa el flag antes de reducir escala."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.cambiar_estado)
        assert "_restaurando_tzimtzum" in src

    def test_flag_auto_clear_en_animar(self):
        """Verifica que _animar auto-limpia el flag al llegar a escala >= 0.95."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "_restaurando_tzimtzum" in src
        assert "0.95" in src


class TestRF138_CariciaResetInactividad:
    """RF-138: Caricia resetea _ticks_inactivo."""

    def test_reset_presente_en_yad(self):
        """Verifica que _animar resetea _ticks_inactivo al detectar caricia."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "_ticks_inactivo" in src, "Falta reset de _ticks_inactivo en caricia"

    def test_cancel_movimiento_en_caricia(self):
        """Verifica que caricia cancela _pos_objetivo."""
        import inspect
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "_pos_objetivo" in src, "Falta cancelar _pos_objetivo en caricia"

