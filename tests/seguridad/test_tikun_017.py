"""
FP-054 Tikún HaGvúl — Tests RF-146/RF-147/RF-148
- RF-146: Re-aplicar DWM post-Tzimtzum (_reasegurar_transparencia llama _eliminar_sombra_dwm)
- RF-147: NIGREDO+ALBEDO obligatorios en cada ciclo Tikún
- RF-148: ALBEDO ampliada con Filosofía y Ciencia
"""
import sys, os, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ═══════ RF-146: Re-aplicar DWM post-Tzimtzum ═══════

class TestRF146_DWMPostTzimtzum:
    """RF-146: _reasegurar_transparencia debe re-aplicar fixes Win32/DWM."""

    def test_reasegurar_llama_eliminar_sombra(self):
        """_reasegurar_transparencia() debe llamar _eliminar_sombra_dwm()."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._reasegurar_transparencia)
        assert "_eliminar_sombra_dwm" in src, "No llama _eliminar_sombra_dwm"

    def test_reasegurar_mantiene_qt_attrs(self):
        """_reasegurar_transparencia() debe mantener atributos Qt."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._reasegurar_transparencia)
        assert "WA_TranslucentBackground" in src
        assert "WA_NoSystemBackground" in src
        assert "border: none" in src

    def test_eliminar_sombra_tiene_ws_popup(self):
        """_eliminar_sombra_dwm() debe forzar WS_POPUP."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._eliminar_sombra_dwm)
        assert "WS_POPUP" in src, "Falta WS_POPUP en _eliminar_sombra_dwm"

    def test_eliminar_sombra_tiene_framechanged(self):
        """_eliminar_sombra_dwm() debe aplicar SWP_FRAMECHANGED (directa o delegada)."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._eliminar_sombra_dwm)
        src_dwm = inspect.getsource(OrbeComputadora._aplicar_dwm_nosombra)
        assert "SWP_FRAMECHANGED" in src or "SWP_FRAMECHANGED" in src_dwm, "Falta SWP_FRAMECHANGED"

    def test_eliminar_sombra_tiene_dwm_disable(self):
        """_eliminar_sombra_dwm() debe desactivar DWM non-client rendering."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._eliminar_sombra_dwm)
        assert "DWMNCRP_DISABLED" in src or "c_int(2)" in src

    def test_desactivar_tzimtzum_llama_reasegurar(self):
        """_desactivar_tzimtzum() debe llamar _reasegurar_transparencia."""
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        src = inspect.getsource(VidaAutonoma._desactivar_tzimtzum)
        assert "_reasegurar_transparencia" in src


# ═══════ RF-147: NIGREDO+ALBEDO obligatorios ═══════

class TestRF147_NigredoAlbedoObligatorio:
    """RF-147: Workflow debe exigir NIGREDO+ALBEDO en cada ciclo."""

    def test_workflow_nigredo_obligatorio(self):
        """Regla #17 debe marcar NIGREDO como OBLIGATORIO."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        assert "NIGREDO" in contenido and "OBLIGATORIO" in contenido

    def test_workflow_albedo_obligatorio(self):
        """Regla #17 debe marcar ALBEDO como OBLIGATORIO."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        assert "ALBEDO" in contenido and "OBLIGATORIO" in contenido

    def test_workflow_nunca_saltar(self):
        """Regla #17 debe decir que NUNCA se va directo a CITRINITAS."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        assert "NUNCA se saltan" in contenido or "NUNCA se va directo a CITRINITAS" in contenido


# ═══════ RF-148: ALBEDO ampliada ═══════

class TestRF148_AlbedoAmpliada:
    """RF-148: ALBEDO debe incluir Filosofía y Ciencia además de esoterismo."""

    def test_albedo_tiene_filosofia(self):
        """ALBEDO debe mencionar ramas filosóficas."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        filosofos = ["Platón", "Aristóteles", "Estoicismo", "Fenomenología"]
        encontrados = sum(1 for f in filosofos if f in contenido)
        assert encontrados >= 3, f"Solo {encontrados}/4 ramas filosóficas encontradas"

    def test_albedo_tiene_ciencia(self):
        """ALBEDO debe mencionar ramas científicas."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        ciencias = ["Neurociencia", "Cibernética", "Teoría de Sistemas", "Psicología cognitiva"]
        encontrados = sum(1 for c in ciencias if c in contenido)
        assert encontrados >= 3, f"Solo {encontrados}/4 ramas científicas encontradas"

    def test_albedo_4_subtareas(self):
        """ALBEDO debe tener 4 sub-tareas (antes eran 3)."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        # Debe tener sub-tareas (A), (B), (C) y (D)
        assert "(D) Milot" in contenido, "Falta sub-tarea (D) Milot Kóaj Jai"
        assert "(B) Investigación Filosófica" in contenido, "Falta sub-tarea (B) Filosófica"

    def test_albedo_max_5_consultas(self):
        """ALBEDO ahora permite máx 5 consultas fetch_webpage (antes 3)."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        assert "máx 5 consultas" in contenido


# ═══════ Integración ═══════

class TestFP054_Integracion:
    """Tests de integración FP-054."""

    def test_fp054_actualizado_en_regla17(self):
        """Regla #17 debe referenciar FP-054."""
        with open(os.path.join(os.path.dirname(__file__), '..', 'DEVELOPMENT_WORKFLOW.md'),
                  encoding='utf-8') as f:
            contenido = f.read()
        assert "FP-054" in contenido

    def test_reasegurar_tiene_rf146_comment(self):
        """_reasegurar_transparencia debe tener comentario RF-146."""
        from computadora.interfaz.ventana_principal import OrbeComputadora
        src = inspect.getsource(OrbeComputadora._reasegurar_transparencia)
        assert "RF-146" in src

