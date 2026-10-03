"""
⊕ Sal — Tests para golem/nucleo/hot_reload.py (WI-291)
Verifica el sistema de hot-reload del Golem.
"""

from pathlib import Path

import pytest

from computadora.nucleo.hot_reload import (
    CAPAS,
    CAPAS_REINICIO_MANUAL,
    clasificar_capa,
    ruta_a_modulo,
)


# ═══════════════════════════════════════════════════════════════
# CAPAS
# ═══════════════════════════════════════════════════════════════

class TestCapas:
    def test_tiene_8_capas(self):
        assert len(CAPAS) == 8

    def test_capas_requeridas(self):
        for capa in ("cerebro", "voz", "habilidades", "interfaz",
                      "memoria", "nucleo", "expresion", "utilidades"):
            assert capa in CAPAS

    def test_valores_son_paths_golem(self):
        for capa, prefijo in CAPAS.items():
            assert prefijo.startswith("golem/")


class TestCapasReinicioManual:
    def test_es_subconjunto_de_capas(self):
        assert CAPAS_REINICIO_MANUAL.issubset(set(CAPAS.keys()))

    def test_contiene_interfaz_y_voz(self):
        assert "interfaz" in CAPAS_REINICIO_MANUAL
        assert "voz" in CAPAS_REINICIO_MANUAL


# ═══════════════════════════════════════════════════════════════
# clasificar_capa
# ═══════════════════════════════════════════════════════════════

class TestClasificarCapa:
    def test_clasifica_cerebro(self):
        ruta = Path("C:/proyecto/golem/cerebro/nlu.py")
        assert clasificar_capa(ruta) == "cerebro"

    def test_clasifica_voz(self):
        ruta = Path("C:/proyecto/golem/voz/escucha.py")
        assert clasificar_capa(ruta) == "voz"

    def test_clasifica_nucleo(self):
        ruta = Path("C:/proyecto/golem/nucleo/emet.py")
        assert clasificar_capa(ruta) == "nucleo"

    def test_ruta_desconocida_retorna_none(self):
        ruta = Path("C:/otro/lugar/script.py")
        assert clasificar_capa(ruta) is None


# ═══════════════════════════════════════════════════════════════
# ruta_a_modulo
# ═══════════════════════════════════════════════════════════════

class TestRutaAModulo:
    def test_convierte_ruta_a_modulo(self):
        raiz = Path("C:/proyecto")
        ruta = Path("C:/proyecto/golem/cerebro/nlu.py")
        assert ruta_a_modulo(ruta, raiz) == "golem.cerebro.nlu"

    def test_init_se_omite(self):
        raiz = Path("C:/proyecto")
        ruta = Path("C:/proyecto/golem/cerebro/__init__.py")
        assert ruta_a_modulo(ruta, raiz) == "golem.cerebro"

    def test_ruta_fuera_retorna_none(self):
        raiz = Path("C:/proyecto")
        ruta = Path("D:/otro/golem.py")
        assert ruta_a_modulo(ruta, raiz) is None

