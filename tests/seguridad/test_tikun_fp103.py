"""Tests para RF-341 (Jojmá Mekomít) y RF-342 (Biná Pnimít).
FP-103: Jojmá VeBiná — Sabiduría Local + Comprensión Interna.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
CODE_JL = (RAIZ / "computadora" / "cerebro" / "jojma_local.py").read_text(encoding="utf-8")
CODE_BP = (RAIZ / "computadora" / "cerebro" / "diagnostico_interno.py").read_text(encoding="utf-8")
CODE_NLU = (RAIZ / "computadora" / "cerebro" / "nlu.py").read_text(encoding="utf-8")


# ═══ RF-341: Jojmá Mekomít — Motor de sabiduría local ═══

class TestRF341_JojmaLocal:
    def test_modulo_existe(self):
        assert (RAIZ / "computadora" / "cerebro" / "jojma_local.py").exists()

    def test_clase_jojma_local(self):
        assert "class JojmaLocal:" in CODE_JL

    def test_singleton_obtener(self):
        assert "def obtener_jojma_local()" in CODE_JL

    def test_metodo_generar(self):
        assert "def generar(" in CODE_JL

    def test_plantillas_categorias(self):
        for cat in ("opinion", "explicacion", "sugerencia", "empatia", "desconocido"):
            assert f'"{cat}"' in CODE_JL, f"Falta categoría: {cat}"

    def test_clasificar_intencion(self):
        assert "def _clasificar_intencion(" in CODE_JL

    def test_extraer_tema(self):
        assert "def _extraer_tema(" in CODE_JL

    def test_integrado_en_nlu(self):
        assert "from computadora.cerebro.jojma_local import obtener_jojma_local" in CODE_NLU

    def test_nlu_usa_jojma_en_sin_llm(self):
        assert "jojma.generar(" in CODE_NLU


# ═══ RF-342: Biná Pnimít — Comprensión Interna ═══

class TestRF342_BinaPnimit:
    def test_modulo_existe(self):
        assert (RAIZ / "computadora" / "cerebro" / "diagnostico_interno.py").exists()

    def test_clase_bina_pnimit(self):
        assert "class DiagnosticoInterno:" in CODE_BP

    def test_singleton_obtener(self):
        assert "def obtener_diagnostico_interno()" in CODE_BP

    def test_metodo_diagnosticar(self):
        assert "def diagnosticar(self)" in CODE_BP

    def test_metodo_resumen_texto(self):
        assert "def resumen_texto(self)" in CODE_BP

    def test_dataclasses(self):
        assert "class DiagnosticoComputadora:" in CODE_BP
        assert "class DiagnosticoModulo:" in CODE_BP

    def test_check_cerebros(self):
        for cerebro in ("_check_ollama", "_check_copilot", "_check_gemini"):
            assert cerebro in CODE_BP, f"Falta: {cerebro}"

    def test_mapa_modulo_sefira(self):
        assert "_MODULO_SEFIRA" in CODE_BP

    def test_integrado_en_nlu(self):
        assert "from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno" in CODE_NLU

    def test_registrar_error(self):
        assert "def registrar_error(" in CODE_BP


# ═══ Tests funcionales ═══

class TestRF341_Funcional:
    def test_jojma_instancia(self):
        from computadora.cerebro.jojma_local import obtener_jojma_local
        assert obtener_jojma_local() is not None

    def test_jojma_generar_responde(self):
        from computadora.cerebro.jojma_local import obtener_jojma_local
        resp = obtener_jojma_local().generar("qué opinas sobre la IA")
        assert isinstance(resp, str) and len(resp) > 10

    def test_clasificar_opinion(self):
        from computadora.cerebro.jojma_local import _clasificar_intencion
        assert _clasificar_intencion("qué opinas de esto") == "opinion"

    def test_clasificar_explicacion(self):
        from computadora.cerebro.jojma_local import _clasificar_intencion
        assert _clasificar_intencion("explícame qué es Python") == "explicacion"

    def test_clasificar_sugerencia(self):
        from computadora.cerebro.jojma_local import _clasificar_intencion
        assert _clasificar_intencion("qué debo hacer con esto") == "sugerencia"

    def test_clasificar_empatia(self):
        from computadora.cerebro.jojma_local import _clasificar_intencion
        assert _clasificar_intencion("me siento triste") == "empatia"

    def test_extraer_tema(self):
        from computadora.cerebro.jojma_local import _extraer_tema
        assert "luna" in _extraer_tema("dime sobre la luna llena").lower()


class TestRF342_Funcional:
    def test_bina_instancia(self):
        from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno
        assert obtener_diagnostico_interno() is not None

    def test_bina_diagnosticar(self):
        from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno
        d = obtener_diagnostico_interno().diagnosticar()
        assert d.timestamp
        assert d.threads_activos > 0
        assert len(d.modulos) > 0

    def test_bina_resumen(self):
        from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno
        resumen = obtener_diagnostico_interno().resumen_texto()
        assert isinstance(resumen, str) and len(resumen) > 20

    def test_bina_registrar_error(self):
        from computadora.cerebro.diagnostico_interno import obtener_diagnostico_interno
        b = obtener_diagnostico_interno()
        b.registrar_error("test_modulo")
        assert b._errores_por_modulo.get("test_modulo", 0) >= 1

