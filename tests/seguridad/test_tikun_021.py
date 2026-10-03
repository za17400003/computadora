"""
Tikún 021 — FP-058: Tikún HaSéder — Orden Durante la Demo
RF-158: Demo pausa subsistemas (vida autónoma, proactividad, escucha)
RF-159: _al_iniciar_habla / _al_terminar_habla respetan _demo_en_curso
RF-160: Escucha pausada durante demo (RF-158 la pausa en _demo_animaciones)
RF-161: Clamp-aware targeting — limpiar _pos_objetivo si clamped al borde
"""
import sys, os, inspect, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─── RF-158: Demo pausa subsistemas ───

class TestRF158_DemoPausaSubsistemas:

    def test_demo_stops_vida_timers(self):
        """_demo_animaciones detiene _vida._timer y _timer_movimiento."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_vida._timer.stop()" in src
        assert "_vida._timer_movimiento.stop()" in src

    def test_demo_clears_pos_objetivo(self):
        """_demo_animaciones limpia _vida._pos_objetivo."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_vida._pos_objetivo = None" in src

    def test_demo_silences_proactividad(self):
        """_demo_animaciones activa silencio en proactividad."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "activar_silencio" in src

    def test_demo_pauses_escucha(self):
        """_demo_animaciones pausa la escucha."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "hilo_escucha.pausar()" in src

    def test_finale_restarts_vida_timers(self):
        """_paso_final reinicia _vida._timer y _timer_movimiento."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "_vida._timer.start(500)" in src
        assert "_vida._timer_movimiento.start(16)" in src

    def test_finale_resumes_escucha(self):
        """_paso_final reanuda la escucha."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "hilo_escucha.reanudar()" in src

    def test_finale_deactivates_silencio(self):
        """_paso_final desactiva silencio de proactividad."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._demo_animaciones)
        assert "desactivar_silencio()" in src


# ─── RF-159: habla respeta demo ───

class TestRF159_HablaRespetaDemo:

    def test_al_iniciar_habla_skips_demo(self):
        """_al_iniciar_habla retorna temprano si _demo_en_curso."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._al_iniciar_habla)
        assert "_demo_en_curso" in src, "_al_iniciar_habla no checa _demo_en_curso"

    def test_al_terminar_habla_skips_demo(self):
        """_al_terminar_habla retorna temprano si _demo_en_curso."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._al_terminar_habla)
        assert "_demo_en_curso" in src, "_al_terminar_habla no checa _demo_en_curso"

    def test_demo_check_is_early_return(self):
        """El check de _demo_en_curso está ANTES del cambiar_estado."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._al_iniciar_habla)
        lines = src.split('\n')
        demo_line = next(i for i, l in enumerate(lines) if '_demo_en_curso' in l)
        hablando_line = next(i for i, l in enumerate(lines) if 'hablando' in l)
        assert demo_line < hablando_line, "demo check debe estar ANTES de cambiar_estado(hablando)"


# ─── RF-161: Clamp-aware targeting ───

class TestRF161_ClampAwareTargeting:

    def test_interpolar_clears_at_boundary(self):
        """RF-340: _interpolar_movimiento limpia _pos_objetivo al llegar."""
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        src = inspect.getsource(VidaAutonoma._interpolar_movimiento)
        assert "_pos_objetivo = None" in src
        assert "_render_offset" in src

    def test_no_move_when_clamped(self):
        """RF-340: ventana expandida con clamp en _expandir_ventana_transito."""
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        src = inspect.getsource(VidaAutonoma._expandir_ventana_transito)
        # Verify screen bounds clamping exists in expand
        assert "self._pantalla.left()" in src
        assert "self._pantalla.right()" in src

