"""
⊕ Sal — Tests para Demo 0 Emet y API Grimorio Emet/Bereshit (WI-281)
Verifica: source code structure de _demo_introduccion, dispatcher sentinels,
menu entry, y endpoints /api/emet y /api/bereshit en servidor_grimorio.
"""

import inspect
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════
# Demo 0 Emet — Source code validation
# ═══════════════════════════════════════════════════════════════

_VP_SOURCE = Path(__file__).resolve().parents[1] / "computadora" / "interfaz" / "ventana_principal.py"


class TestDemo0EmetSource:
    """Valida la presencia de Demo 0 Emet en ventana_principal.py."""

    @classmethod
    def setup_class(cls):
        cls.source = _VP_SOURCE.read_text(encoding="utf-8")

    def test_demo_emet_method_exists(self):
        assert "def _demo_introduccion(self):" in self.source

    def test_demo_emet_imports_emet_module(self):
        """Demo 0 debe importar resumen_para_demo y resumen_genesis_para_demo."""
        # Buscar dentro del bloque _demo_introduccion
        start = self.source.index("def _demo_introduccion(self):")
        # Buscar hasta el siguiente def
        end = self.source.index("\n    def ", start + 1)
        bloque = self.source[start:end]
        assert "resumen_para_demo" in bloque
        assert "resumen_genesis_para_demo" in bloque

    def test_demo_emet_chaining_flag(self):
        """Demo 0 establece _demo_introduccion_activo para encadenar Demo 1→2."""
        assert "_demo_introduccion_activo" in self.source

    def test_demo_emet_chains_to_maljut(self):
        """El finale de Demo 0 debe encadenar a _demo_animaciones."""
        start = self.source.index("def _demo_introduccion(self):")
        end = self.source.index("\n    def ", start + 1)
        bloque = self.source[start:end]
        assert "_demo_animaciones" in bloque

    def test_context_menu_has_emet(self):
        """Menú contextual contiene entrada Demo Emet."""
        assert "Demo Emet" in self.source

    def test_sentinel_demo_emet_in_accion_remota(self):
        """_ejecutar_accion_remota maneja __DEMO_INTRODUCCION__."""
        start = self.source.index("def _ejecutar_accion_remota")
        end = self.source.index("\n    def ", start + 1)
        bloque = self.source[start:end]
        assert "__DEMO_INTRODUCCION__" in bloque

    def test_sentinel_demo_emet_in_respuesta(self):
        """_al_recibir_respuesta maneja __DEMO_INTRODUCCION__."""
        start = self.source.index("def _al_recibir_respuesta")
        end = self.source.index("\n    def ", start + 1)
        bloque = self.source[start:end]
        assert "__DEMO_INTRODUCCION__" in bloque

    def test_maljut_respects_emet_chain(self):
        """Demo 1 (Maljut) no pregunta si encadenar cuando _demo_introduccion_activo."""
        start = self.source.index("def _demo_animaciones(self):")
        end = self.source.index("\n    def ", start + 1)
        bloque = self.source[start:end]
        assert "_demo_introduccion_activo" in bloque

    def test_gevura_clears_emet_flag(self):
        """Demo 2 (Gevurá) limpia _demo_introduccion_activo al terminar."""
        start = self.source.index("def _demo_herramientas(self):")
        end = self.source.index("\n    @pyqtSlot", start + 1)
        bloque = self.source[start:end]
        assert "_demo_introduccion_activo = False" in bloque


# ═══════════════════════════════════════════════════════════════
# API Grimorio — /api/emet y /api/bereshit
# ═══════════════════════════════════════════════════════════════

_GRIMORIO_SOURCE = Path(__file__).resolve().parents[1] / "libro_encantado" / "servidor_grimorio.py"


class TestGrimorioAPIEmet:
    """Valida que el servidor del Grimorio expone /api/emet y /api/bereshit."""

    @classmethod
    def setup_class(cls):
        cls.source = _GRIMORIO_SOURCE.read_text(encoding="utf-8")

    def test_api_emet_endpoint_exists(self):
        assert "api/emet" in self.source

    def test_api_bereshit_endpoint_exists(self):
        assert "api/bereshit" in self.source

    def test_emet_triggers_in_search(self):
        """La búsqueda tiene EMET_TRIGGERS para cross-referencia."""
        assert "EMET_TRIGGERS" in self.source or "_EMET_TRIGGERS" in self.source

    def test_buscar_en_emet_imported(self):
        """servidor_grimorio importa buscar_en_emet."""
        assert "buscar_en_emet" in self.source

    def test_generar_manifiesto_imported(self):
        """servidor_grimorio importa generar_manifiesto."""
        assert "generar_manifiesto" in self.source


# ═══════════════════════════════════════════════════════════════
# Grimorio index.html — Bereshit Genesis page
# ═══════════════════════════════════════════════════════════════

_INDEX_HTML = Path(__file__).resolve().parents[1] / "libro_encantado" / "index.html"


class TestGrimorioGenesisPage:
    """Valida que index.html tiene la página de Génesis Bíblico."""

    @classmethod
    def setup_class(cls):
        cls.source = _INDEX_HTML.read_text(encoding="utf-8")

    def test_toc_has_bereshit_entry(self):
        assert "bereshit_genesis" in self.source

    def test_template_has_7_dias(self):
        """El template debe contener marcadores para los 7 días."""
        start = self.source.index('data-chapter="bereshit_genesis"')
        end = self.source.index("</template>", start)
        bloque = self.source[start:end]
        for dia in range(1, 8):
            assert f"Día {dia}" in bloque, f"Falta Día {dia} en template bereshit_genesis"

    def test_template_has_genesis_citations(self):
        start = self.source.index('data-chapter="bereshit_genesis"')
        end = self.source.index("</template>", start)
        bloque = self.source[start:end]
        assert "Génesis 1:" in bloque
        assert "Génesis 2:" in bloque  # Día 7

