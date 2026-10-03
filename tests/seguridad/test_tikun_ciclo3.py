"""
Tests para Tikún Jai Ciclo 3 — seguridad y thread safety.
Verifica TOOL_PATTERN (ReDoS fix), GestorKelim lock, Gemini model whitelist.
"""
import re
import threading


def test_tool_pattern_non_greedy_nested_json():
    """TOOL_PATTERN con .*? captura JSON anidado correctamente."""
    from computadora.cerebro.parseo_herramientas import TOOL_PATTERN

    texto = '```tool\n{"herramienta": "abrir_app", "args": {"nombre": "notepad"}}\n```'
    m = TOOL_PATTERN.search(texto)
    assert m is not None
    parsed = m.group(1)
    assert '"herramienta"' in parsed
    assert '"args"' in parsed
    assert '"nombre"' in parsed
    # Debe capturar JSON completo incluyendo inner braces
    assert parsed.count("{") == parsed.count("}")


def test_tool_pattern_simple_json():
    """TOOL_PATTERN captura JSON simple."""
    from computadora.cerebro.parseo_herramientas import TOOL_PATTERN

    texto = '```tool\n{"herramienta": "hora"}\n```'
    m = TOOL_PATTERN.search(texto)
    assert m is not None
    assert '"hora"' in m.group(1)


def test_tool_pattern_deeply_nested():
    """TOOL_PATTERN maneja 3 niveles de anidación."""
    from computadora.cerebro.parseo_herramientas import TOOL_PATTERN

    texto = '```tool\n{"herramienta": "foo", "args": {"a": {"b": 1}}}\n```'
    m = TOOL_PATTERN.search(texto)
    assert m is not None
    assert m.group(1).count("{") == 3
    assert m.group(1).count("}") == 3


def test_tool_pattern_no_redos():
    """TOOL_PATTERN no causa backtracking catastrófico en input malicioso."""
    from computadora.cerebro.parseo_herramientas import TOOL_PATTERN
    import time

    # Input sin cierre ``` — debería fallar rápido sin hang
    malicioso = "```tool\n" + "{" * 100 + "a" * 1000 + "}" * 100
    inicio = time.perf_counter()
    m = TOOL_PATTERN.search(malicioso)
    duracion = time.perf_counter() - inicio
    assert m is None  # No match esperado
    assert duracion < 1.0, f"ReDoS potencial: {duracion:.2f}s"


def test_gestor_kelim_tiene_lock():
    """GestorKelim tiene _lock para thread safety."""
    from computadora.nucleo.kli import GestorKelim
    gestor = GestorKelim.instancia()
    assert hasattr(gestor, "_lock")
    assert isinstance(gestor._lock, type(threading.Lock()))
    GestorKelim._reset()


def test_gemini_modelo_whitelist():
    """CerebroGemini rechaza modelos no permitidos."""
    try:
        from computadora.cerebro.gemini_api import CerebroGemini
    except Exception:
        return  # Sin httpx o sin .env — skip silencioso

    cerebro = CerebroGemini.__new__(CerebroGemini)
    cerebro._api_key = "fake-key-for-test"
    # Modelo inválido debería retornar None sin hacer request
    resultado = cerebro._pensar_con_modelo(
        "test", None, "modelo-malicioso/../../../etc/passwd"
    )
    assert resultado is None

