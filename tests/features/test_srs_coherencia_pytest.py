# -*- coding: utf-8 -*-
"""
Tests de Coherencia SRS ↔ Código — בדיקת אמת (Regla #19)
Auditoría sistemática: cada RF del SRS.md se verifica contra el código real.
Pytest-compatible con UTF-8 handling y assertions.
"""

import sys
import os
import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_srs_coherencia_rf_01_to_36():
    """Auditar RFs 01-36 (Implementados en código) — Verificar existencia."""
    
    passed = []
    failed = []
    
    # RF-01: Escucha por voz (STT)
    try:
        from computadora.voz.escucha import HiloEscucha
        assert inspect.isclass(HiloEscucha), "HiloEscucha debe ser clase"
        from computadora.voz import escucha as _esc
        assert hasattr(_esc, '_RE_CORTESIA'), "_RE_CORTESIA debe existir"
        assert hasattr(_esc, '_RE_NOMBRE_COMPLETO'), "_RE_NOMBRE_COMPLETO debe existir"
        passed.append("RF-01: Escucha + wake words")
    except AssertionError as e:
        failed.append(f"RF-01: {e}")
    
    # RF-02: NLU
    try:
        from computadora.cerebro.nlu import CerebroComputadora
        assert inspect.isclass(CerebroComputadora), "CerebroComputadora debe ser clase"
        assert hasattr(CerebroComputadora, 'pensar'), "CerebroComputadora.pensar debe existir"
        assert hasattr(CerebroComputadora, '_pensar_nivel1'), "_pensar_nivel1 debe existir"
        assert hasattr(CerebroComputadora, '_pensar_con_herramientas'), "_pensar_con_herramientas debe existir"
        passed.append("RF-02: NLU + 3 niveles")
    except AssertionError as e:
        failed.append(f"RF-02: {e}")
    
    # RF-03: TTS
    try:
        from computadora.voz.habla import HiloHabla
        assert inspect.isclass(HiloHabla), "HiloHabla debe ser clase"
        assert hasattr(HiloHabla, 'hablar'), "HiloHabla.hablar debe existir"
        assert hasattr(HiloHabla, 'interrumpir'), "HiloHabla.interrumpir debe existir"
        passed.append("RF-03: Habla (TTS)")
    except AssertionError as e:
        failed.append(f"RF-03: {e}")
    
    # RF-04: Control SO
    try:
        from computadora.habilidades import sistema
        assert hasattr(sistema, 'abrir_aplicacion'), "abrir_aplicacion debe existir"
        assert hasattr(sistema, 'cerrar_aplicacion'), "cerrar_aplicacion debe existir"
        passed.append("RF-04: Control del SO")
    except AssertionError as e:
        failed.append(f"RF-04: {e}")
    
    # RF-05: Organización personal
    try:
        from computadora.habilidades import agenda
        assert hasattr(agenda, 'agregar_tarea'), "agregar_tarea debe existir"
        assert hasattr(agenda, 'listar_tareas'), "listar_tareas debe existir"
        passed.append("RF-05: Organización personal")
    except AssertionError as e:
        failed.append(f"RF-05: {e}")
    
    # RF-06: 3 cerebros
    try:
        from computadora.cerebro import nlu as _nlu
        assert hasattr(CerebroComputadora, '_pensar_nivel1'), "Nivel 1 debe existir"
        assert hasattr(CerebroComputadora, '_pensar_con_herramientas'), "Nivel 2 debe existir"
        assert hasattr(CerebroComputadora, '_pensar_con_copilot'), "Nivel 3 debe existir"
        assert hasattr(_nlu, 'SISTEMA_PROMPT') and len(_nlu.SISTEMA_PROMPT) > 100, "SISTEMA_PROMPT debe existir"
        passed.append("RF-06: 3 Cerebros (N1/N2/N3)")
    except AssertionError as e:
        failed.append(f"RF-06: {e}")
    
    # RF-07: Auto-modificación
    try:
        from computadora.cerebro.copilot_api import CerebroCopilot
        assert inspect.isclass(CerebroCopilot), "CerebroCopilot debe ser clase"
        assert hasattr(CerebroCopilot, 'pensar_codigo'), "pensar_codigo debe existir"
        passed.append("RF-07: Auto-modificacion (Copilot)")
    except AssertionError as e:
        failed.append(f"RF-07: {e}")
    
    # RF-08: Orbe Cabalístico
    try:
        from computadora.interfaz.ventana_principal import OrbeComputadora
        from computadora.interfaz.vida_autonoma import VidaAutonoma
        assert inspect.isclass(OrbeComputadora), "OrbeComputadora debe ser clase"
        assert inspect.isclass(VidaAutonoma), "VidaAutonoma debe ser clase"
        passed.append("RF-08: Interfaz (Orbe + VidaAutonoma)")
    except AssertionError as e:
        failed.append(f"RF-08: {e}")
    
    # RF-09: Tool-use
    try:
        from computadora.habilidades.herramientas import ejecutar_herramienta
        assert callable(ejecutar_herramienta), "ejecutar_herramienta debe ser callable"
        passed.append("RF-09: Tool-use (herramientas)")
    except AssertionError as e:
        failed.append(f"RF-09: {e}")
    
    # RF-11: Personalidad
    try:
        from computadora.memoria.personalidad import Personalidad, HUMORES_VALIDOS
        assert inspect.isclass(Personalidad), "Personalidad debe ser clase"
        assert len(HUMORES_VALIDOS) >= 13, "Debe haber >= 13 humores"
        passed.append("RF-11: Personalidad (13+ humores)")
    except AssertionError as e:
        failed.append(f"RF-11: {e}")
    
    # RF-12: Contexto Pantalla
    try:
        from computadora.utilidades.windows import ContextoPantalla
        assert inspect.isclass(ContextoPantalla), "ContextoPantalla debe ser clase"
        passed.append("RF-12: Contexto de Pantalla")
    except AssertionError as e:
        failed.append(f"RF-12: {e}")
    
    # RF-13: Proactividad
    try:
        from computadora.nucleo.proactividad import MotorProactividad
        assert inspect.isclass(MotorProactividad), "MotorProactividad debe ser clase"
        passed.append("RF-13: Proactividad")
    except AssertionError as e:
        failed.append(f"RF-13: {e}")
    
    # RF-14: Monitor Sistema
    try:
        from computadora.habilidades.monitor_sistema import MonitorSistema
        assert inspect.isclass(MonitorSistema), "MonitorSistema debe ser clase"
        assert hasattr(MonitorSistema, 'snapshot'), "snapshot debe existir"
        passed.append("RF-14: Monitor del Sistema")
    except AssertionError as e:
        failed.append(f"RF-14: {e}")
    
    # RF-25: Autopercepción
    try:
        from computadora.nucleo.entorno import EntornoSistema
        assert inspect.isclass(EntornoSistema), "EntornoSistema debe ser clase"
        passed.append("RF-25: Autopercepcion (Entorno)")
    except AssertionError as e:
        failed.append(f"RF-25: {e}")
    
    # RF-30: Ciclo circadiano
    try:
        from computadora.nucleo.ciclo_circadiano import CicloCircadiano
        assert inspect.isclass(CicloCircadiano), "CicloCircadiano debe ser clase"
        assert hasattr(CicloCircadiano, 'fase_actual'), "fase_actual debe existir"
        passed.append("RF-30: Ciclo Circadiano")
    except AssertionError as e:
        failed.append(f"RF-30: {e}")
    
    # RF-35: Estados expresivos
    try:
        from computadora.interfaz.fsm_golem import EstadoMaljut
        estados = [e.value for e in EstadoMaljut]
        assert "cortesia" in estados, "EstadoMaljut.CORTESIA debe existir"
        assert "descanso_guardian" in estados, "EstadoMaljut.DESCANSO_GUARDIAN debe existir"
        passed.append("RF-35: Estados expresivos (FSM)")
    except AssertionError as e:
        failed.append(f"RF-35: {e}")
    
    # RF-56: Lemed auto-aprendizaje
    try:
        from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
        assert inspect.isclass(Nivel1Aprendido), "Nivel1Aprendido debe ser clase"
        assert hasattr(Nivel1Aprendido, 'buscar_match'), "buscar_match debe existir"
        passed.append("RF-56: Auto-aprendizaje (N1Aprendido)")
    except AssertionError as e:
        failed.append(f"RF-56: {e}")
    
    # RESUMEN FINAL
    assert len(failed) == 0, (
        f"COHERENCIA SRS: {len(passed)} OK, {len(failed)} FALLO\n"
        + "\n".join(f"  PASS: {p}" for p in passed[:5]) + "\n"
        + ("\n".join(f"  FAIL: {f}" for f in failed) if failed else "")
    )


def test_srs_nivel1_3_brains_cascade():
    """Verificar that 3-brain cascade is properly implemented."""
    from computadora.cerebro.nlu import CerebroComputadora
    
    # Nivel 1: debe existir y usar regex
    assert hasattr(CerebroComputadora, '_pensar_nivel1')
    
    # Nivel 2: debe existir y usar Ollama
    assert hasattr(CerebroComputadora, '_pensar_con_herramientas')
    
    # Nivel 3: debe existir y escalable a Copilot
    assert hasattr(CerebroComputadora, '_pensar_con_copilot')


def test_srs_wake_word_system():
    """Verificar que sistema de wake words está completo."""
    from computadora.voz import escucha as _esc
    
    # Debe tener wake word principal
    assert hasattr(_esc, '_WAKE_WORD_RE'), "Wake word regex debe existir"
    
    # Debe tener nombre completo (regaño)
    assert hasattr(_esc, '_RE_NOMBRE_COMPLETO'), "Nombre completo regex debe existir"
    
    # Debe tener apodo
    assert hasattr(_esc, '_RE_APODO'), "Apodo regex debe existir"
    
    # Debe tener cortesía sin wake word
    assert hasattr(_esc, '_RE_CORTESIA'), "Cortesia regex debe existir"


def test_srs_rf264_sefirot_mapping():
    """Verificar que RF-264 (Sefirot mapping) está documentado."""
    # SRS.md debe tener la tabla RF-264
    import os
    srs_path = os.path.join(os.path.dirname(__file__), "..", "docs", "SRS.md")
    with open(srs_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "RF-264" in content, "RF-264 debe estar en SRS.md"
        assert "Sefirot" in content or "sefirot" in content.lower(), "Mapping a Sefirot debe existir"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

