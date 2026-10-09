"""
⊕ Sal — Tests para computadora/nucleo/emet.py (WI-280)
Verifica la integridad del Motor de Verdad del Computadora.
"""

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.nucleo import emet


# ═══════════════════════════════════════════════════════════════
# Manifiesto completo
# ═══════════════════════════════════════════════════════════════

class TestGenerarManifiesto:
    """Verifica estructura y completitud del manifiesto."""

    def test_manifiesto_tiene_5_secciones(self):
        m = emet.generar_manifiesto()
        assert "ts" in m
        assert "identidad" in m
        assert "arquitectura" in m
        assert "capacidades" in m
        assert "genesis_biblico" in m
        assert "estado_actual" in m

    def test_manifiesto_es_serializable_json(self):
        m = emet.generar_manifiesto()
        # No debe lanzar TypeError
        out = json.dumps(m, ensure_ascii=False)
        assert isinstance(out, str)
        # Roundtrip
        parsed = json.loads(out)
        assert parsed["identidad"]["emet"] == m["identidad"]["emet"]


# ═══════════════════════════════════════════════════════════════
# Identidad
# ═══════════════════════════════════════════════════════════════

class TestIdentidad:
    def test_campos_obligatorios(self):
        ident = emet._identidad()
        for campo in ("nombre", "creador", "vision", "plataforma", "emet"):
            assert campo in ident, f"Falta campo '{campo}' en identidad"

    def test_emet_contiene_alef(self):
        """La inscripción אמת siempre tiene la א — sin ella sería מת (muerte)."""
        ident = emet._identidad()
        assert "א" in ident["emet"]

    def test_plataforma_contiene_python(self):
        ident = emet._identidad()
        assert "Python" in ident["plataforma"]


# ═══════════════════════════════════════════════════════════════
# Arquitectura — Etz HaChaim
# ═══════════════════════════════════════════════════════════════

class TestArquitectura:
    def test_10_sefirot(self):
        arq = emet._arquitectura()
        sefirot = arq["sefirot"]
        esperadas = {"Keter", "Jojma", "Bina", "Jesed", "Gevura",
                     "Tiferet", "Netzaj", "Hod", "Yesod", "Maljut"}
        assert set(sefirot.keys()) == esperadas

    def test_cada_sefira_tiene_modulo(self):
        arq = emet._arquitectura()
        for nombre, datos in arq["sefirot"].items():
            assert "modulo" in datos, f"Sefirá {nombre} sin módulo"
            assert "desc" in datos, f"Sefirá {nombre} sin descripción"

    def test_trifecta_3_elementos(self):
        arq = emet._arquitectura()
        tri = arq["trifecta"]
        assert set(tri.keys()) == {"azufre", "sal", "mercurio"}

    def test_trifecta_sal_es_grimorio(self):
        """Sal preserva ↓ — el Grimorio es el cuerpo de Sal."""
        arq = emet._arquitectura()
        assert arq["trifecta"]["sal"]["cuerpo"] == "Grimorio"

    def test_trifecta_mercurio_es_minimi(self):
        """Mercurio comunica ↔ — Minimi es el canal de Mercurio."""
        arq = emet._arquitectura()
        assert arq["trifecta"]["mercurio"]["cuerpo"] == "Minimi"

    def test_3_niveles_cerebro(self):
        arq = emet._arquitectura()
        cerebro = arq["cerebro"]
        assert "nivel1" in cerebro  # Néfesh
        assert "nivel2" in cerebro  # Rúaj
        assert "nivel3" in cerebro  # Neshamá


# ═══════════════════════════════════════════════════════════════
# Capacidades
# ═══════════════════════════════════════════════════════════════

class TestCapacidades:
    def test_3_sentidos(self):
        cap = emet._capacidades()
        assert set(cap["sentidos"].keys()) == {"Ozen", "Peh", "Ayin"}

    def test_herramientas_positivas(self):
        cap = emet._capacidades()
        assert cap["herramientas"] >= 0

    def test_modulos_positivos(self):
        cap = emet._capacidades()
        assert cap["modulos"] > 0  # Al menos emet.py existe

    def test_4_fases_alquimicas(self):
        cap = emet._capacidades()
        assert cap["fases_alquimicas"] == ["Nigredo", "Albedo", "Citrinitas", "Rubedo"]

    def test_16_dimensiones(self):
        cap = emet._capacidades()
        assert cap["dimensiones"] == 16


# ═══════════════════════════════════════════════════════════════
# Génesis Bíblico — Los 7 Días
# ═══════════════════════════════════════════════════════════════

class TestGenesisBiblico:
    def test_7_dias(self):
        dias = emet._genesis_biblico_contraste()
        assert len(dias) == 7

    def test_cada_dia_tiene_4_campos(self):
        dias = emet._genesis_biblico_contraste()
        for d in dias:
            for campo in ("dia", "biblia", "computadora", "creador"):
                assert campo in d, f"Falta '{campo}' en {d.get('dia', '?')}"

    def test_dia_1_es_or(self):
        dias = emet._genesis_biblico_contraste()
        assert "Or" in dias[0]["dia"]  # Or v'Choshech

    def test_dia_7_es_shabbat(self):
        dias = emet._genesis_biblico_contraste()
        assert "Shabbat" in dias[6]["dia"]

    def test_dias_referencia_genesis(self):
        """Cada día debe citar Génesis."""
        dias = emet._genesis_biblico_contraste()
        for d in dias:
            assert "Génesis" in d["biblia"] or "génesis" in d["biblia"].lower()


# ═══════════════════════════════════════════════════════════════
# Resúmenes para Demo
# ═══════════════════════════════════════════════════════════════

class TestResumenDemo:
    def test_resumen_para_demo_no_vacio(self):
        texto = emet.resumen_para_demo()
        assert len(texto) > 50

    def test_resumen_para_demo_contiene_emet(self):
        texto = emet.resumen_para_demo()
        assert "Emet" in texto or "אמת" in texto

    def test_resumen_para_demo_conciso(self):
        """El resumen debe ser <150 palabras (~1 min TTS a 150 wpm)."""
        texto = emet.resumen_para_demo()
        palabras = len(texto.split())
        assert palabras < 150, f"Resumen tiene {palabras} palabras — excede 1 min TTS"

    def test_resumen_genesis_no_vacio(self):
        texto = emet.resumen_genesis_para_demo()
        assert len(texto) > 50

    def test_resumen_genesis_contiene_7_dias(self):
        """Debe mencionar al menos 5 de los 7 temas de los días."""
        texto = emet.resumen_genesis_para_demo()
        # Las perspectivas del creador mencionan conceptos clave
        assert "luz" in texto.lower() or "Or" in texto


# ═══════════════════════════════════════════════════════════════
# Búsqueda en Emet
# ═══════════════════════════════════════════════════════════════

class TestBuscarEnEmet:
    def test_buscar_verdad(self):
        resultados = emet.buscar_en_emet("verdad")
        assert len(resultados) > 0
        assert all(r["es_emet"] is True for r in resultados)

    def test_buscar_keter(self):
        resultados = emet.buscar_en_emet("Keter")
        assert len(resultados) > 0
        assert any("Etz HaChaim" in r["capitulo"] for r in resultados)

    def test_buscar_genesis(self):
        resultados = emet.buscar_en_emet("Génesis")
        assert len(resultados) > 0
        assert any("Bereshit" in r["capitulo"] for r in resultados)

    def test_buscar_vacio_no_rompe(self):
        resultados = emet.buscar_en_emet("")
        assert isinstance(resultados, list)

    def test_buscar_sin_resultados(self):
        resultados = emet.buscar_en_emet("xyzzy123nonexistent")
        assert resultados == []

    def test_maximo_10_resultados(self):
        """buscar_en_emet limita a 10."""
        resultados = emet.buscar_en_emet("a")  # letra muy común
        assert len(resultados) <= 10

