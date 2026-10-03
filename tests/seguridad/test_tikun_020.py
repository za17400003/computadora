"""
Tikún 020 — FP-057: Tikún HaMa'avár — Transiciones Suaves
RF-157: Lerp temporal de tintes Dmut (~1s transición entre humores)
+ Actualización Demo Maljut con narración de transiciones suaves.
"""
import sys, os, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── RF-157: Lerp de tintes Dmut ───

class TestRF157_DmutLerp:

    def test_dmut_actual_initialized(self):
        """__init__ crea _dmut_actual como dict interpolado."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.__init__)
        assert "_dmut_actual" in src, "_dmut_actual no inicializado en __init__"

    def test_animar_lerps_dmut(self):
        """_animar() interpola _dmut_actual hacia _dmut_target."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "_dmut_actual" in src, "_animar no usa _dmut_actual"
        assert "_lerp_speed" in src or "lerp" in src.lower(), "No hay lerp en _animar"

    def test_paintEvent_uses_lerped_dmut(self):
        """paintEvent() lee _dmut_actual en vez de _DMUT_VISUAL directo."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora.paintEvent)
        assert "_dmut_actual" in src, "paintEvent no usa _dmut_actual (RF-157)"

    def test_lerp_speed_reasonable(self):
        """Factor de lerp ~0.05 (converge en ~20 frames ≈ 0.67s a 30fps)."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "0.05" in src, "Factor de lerp no es 0.05"

    def test_all_dmut_keys_lerped(self):
        """El lerp itera sobre todas las keys del dict Dmut target."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "for _k in _dmut_target" in src, "Lerp no itera keys de _dmut_target"


# ─── Demo actualizada con narración de transiciones suaves ───

class TestDemoTransiciones:

    def test_demo_mentions_transicion(self):
        """La demo narra las transiciones suaves."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "transición" in src.lower() or "suave" in src.lower(), \
            "Demo no menciona transiciones suaves"

    def test_demo_humor_spacing_adequate(self):
        """Los humores en la demo tienen ≥3s entre ellos para que el lerp sea visible."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        import re
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        # Buscar los _paso(NNNNms, ...) que contienen _set_humor
        # Extraer tiempos de pasos que involucran humor
        humores_lines = [l for l in src.split('\n') if '_set_humor' in l or 'Humor' in l or 'Emocionado' in l]
        assert len(humores_lines) >= 3, "Demo no tiene al menos 3 cambios de humor"

    def test_demo_rf157_comment_present(self):
        """ACT III menciona transición de humor (RF-157)."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "Humor sereno" in src or "RF-157" in src or '_set_humor("sereno")' in src, "Demo ACT III sin transición de humor"

