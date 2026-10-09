"""
FP-053 Shemirat Tzimtzum — Tests RF-142/RF-143/RF-144/RF-145
- RF-142: Hysteresis de proceso (verificar si sigue corriendo)
- RF-143: Debounce gradual (decrementar en vez de resetear)
- RF-144: Restauración sin robo de foco (SWP_NOACTIVATE)
- RF-145: Inercia en movimiento autónomo
"""
import sys, os, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from computadora.interfaz.vida_autonoma import (
    _proceso_sigue_corriendo,
    _detectar_proceso_pesado,
    VidaAutonoma,
    EstadoPresencia,
)


# ═══════ RF-142: Hysteresis de proceso ═══════

class TestRF142_Hysteresis:
    """RF-142: Verificar que el proceso tzimtzum sigue corriendo antes de desactivar."""

    def test_proceso_sigue_corriendo_existe(self):
        """La función helper _proceso_sigue_corriendo debe existir."""
        assert callable(_proceso_sigue_corriendo)

    def test_proceso_sigue_corriendo_python(self):
        """python.exe siempre debe estar corriendo (es nuestro propio proceso)."""
        assert _proceso_sigue_corriendo("python.exe")

    def test_proceso_no_corriendo(self):
        """Un proceso inventado no debe estar corriendo."""
        assert not _proceso_sigue_corriendo("zzzfakeprocess_computadoratest.exe")

    def test_hysteresis_en_tick(self):
        """_tick() debe contener lógica de hysteresis con _proceso_sigue_corriendo."""
        src = inspect.getsource(VidaAutonoma._tick)
        assert "_proceso_sigue_corriendo" in src, "Falta hysteresis en _tick"
        assert "tzimtzum_proceso" in src, "No verifica el proceso guardado"

    def test_hysteresis_ignora_inactividad(self):
        """Hysteresis no debe aplicar para Tzimtzum por inactividad."""
        src = inspect.getsource(VidaAutonoma._tick)
        assert 'inactividad >5 min' in src, "No excluye inactividad de hysteresis"


# ═══════ RF-143: Debounce gradual ═══════

class TestRF143_Debounce:
    """RF-143: ticks_carga_pesada decrementa en vez de resetear a 0."""

    def test_debounce_en_tick(self):
        """_tick() debe usar decremento gradual, no reset a 0."""
        src = inspect.getsource(VidaAutonoma._tick)
        # Debe tener max(0, ... - 1) en vez de = 0
        assert "max(0," in src and "- 1)" in src, "Falta debounce gradual"

    def test_no_reset_directo_a_cero(self):
        """No debe haber _ticks_carga_pesada = 0 en la rama else de es_pesado."""
        src = inspect.getsource(VidaAutonoma._tick)
        # Buscar el patrón específico del bug: else → reset a 0
        lines = src.split('\n')
        in_else = False
        for line in lines:
            stripped = line.strip()
            if 'else:' in stripped and 'es_pesado' not in stripped:
                in_else = True
                continue
            if in_else:
                if '_ticks_carga_pesada = 0' in stripped and 'max(' not in stripped:
                    assert False, "Aún existe reset directo _ticks_carga_pesada = 0"
                if stripped and not stripped.startswith('#'):
                    break


# ═══════ RF-144: Restauración sin robo de foco ═══════

class TestRF144_SinRoboFoco:
    """RF-144: _desactivar_tzimtzum no debe robar foco."""

    def test_no_raise_directo(self):
        """_desactivar_tzimtzum no debe usar raise_() directo."""
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        # raise_() robaría foco — debe usar SetWindowPos
        assert "raise_()" not in src, "Aún usa raise_() que roba foco"

    def test_usa_swp_noactivate(self):
        """_desactivar_tzimtzum debe usar SWP_NOACTIVATE."""
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert "SetWindowPos" in src, "Falta SetWindowPos para no robar foco"
        assert "NOACTIVATE" in src or "0x0010" in src, "Falta flag SWP_NOACTIVATE"

    def test_usa_shownoactivate(self):
        """_desactivar_tzimtzum debe usar SW_SHOWNOACTIVATE en vez de show()."""
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert "ShowWindow" in src, "Falta ShowWindow con SW_SHOWNOACTIVATE"
        # SW_SHOWNOACTIVATE = 4
        assert ", 4)" in src, "Falta SW_SHOWNOACTIVATE (valor 4)"

    def test_no_show_directo(self):
        """No debe usar .show() que podría activar la ventana."""
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert ".show()" not in src, "Aún usa .show() que podría robar foco"


# ═══════ RF-145: Inercia en movimiento autónomo ═══════

class TestRF145_InerciaAutonoma:
    """RF-145: Partículas deben tener inercia durante movimiento autónomo."""

    def test_no_sync_pos_anterior_durante_movimiento(self):
        """_interpolar_movimiento NO debe sincronizar _pos_anterior durante movimiento."""
        src = inspect.getsource(VidaAutonoma._interpolar_movimiento)
        # Buscar la zona de movimiento (después de self._orbe.move(int(nx)...)
        lines = src.split('\n')
        in_move_zone = False
        for line in lines:
            if 'move(int(nx)' in line:
                in_move_zone = True
                continue
            if in_move_zone:
                # No debe haber sync de _pos_anterior en las líneas siguientes
                if '_pos_anterior_x = float' in line or '_pos_anterior_y = float' in line:
                    assert False, "Sync de _pos_anterior durante movimiento anula inercia"
                # Solo verificar las siguientes 3 líneas
                if line.strip() and not line.strip().startswith('#'):
                    break

    def test_sync_al_llegar(self):
        """RF-340: _interpolar_movimiento usa render_offset y colapsa ventana al llegar."""
        src = inspect.getsource(VidaAutonoma._interpolar_movimiento)
        # RF-340: movimiento via render offset, colapso en _colapsar_ventana_transito
        assert "_render_offset_x" in src, "Falta render_offset en interpolar"
        assert "_colapsar_ventana_transito" in src, "Falta colapso al llegar"

    def test_particula_recibe_delta(self):
        """Particula.actualizar() debe recibir delta_x/delta_y para inercia."""
        from computadora.interfaz.ventana_principal import Particula
        src = inspect.getsource(Particula.actualizar)
        assert "delta_x" in src and "delta_y" in src, "Particula no recibe deltas"
        assert "self.vx -= delta_x" in src, "No aplica delta a velocidad"

    def test_animar_calcula_delta(self):
        """_animar() debe calcular delta desde _pos_anterior para partículas."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._animar)
        assert "_raw_dx" in src or "_pos_anterior_x" in src, "No calcula delta en _animar"


# ═══════ Integración ═══════

class TestFP053_Integracion:
    """Tests de integración FP-053."""

    def test_activar_tzimtzum_guarda_proceso(self):
        """_activar_tzimtzum debe guardar el nombre del proceso."""
        src = inspect.getsource(VidaAutonoma._activar_tzimtzum)
        assert "_tzimtzum_proceso = proceso" in src, "No guarda proceso en activación"

    def test_estados_presencia_tiene_tzimtzum(self):
        """EstadoPresencia debe incluir TZIMTZUM."""
        assert hasattr(EstadoPresencia, 'TZIMTZUM')

    def test_desactivar_limpia_estado(self):
        """_desactivar_tzimtzum debe limpiar flags y contadores."""
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert '_en_tzimtzum = False' in src
        assert '_ticks_carga_pesada = 0' in src
        assert '_ticks_carga_ligera = 0' in src

    def test_constantes_tzimtzum(self):
        """Los umbrales de Tzimtzum deben ser razonables."""
        src = inspect.getsource(VidaAutonoma.__init__)
        assert '_TICKS_UMBRAL_TZIMTZUM' in src
        assert '_TICKS_UMBRAL_RETORNO' in src

