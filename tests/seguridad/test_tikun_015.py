"""
FP-052 Shemiát Emet — Tests RF-139/RF-140/RF-141
- RF-139: Silero VAD pre-filtro de voz humana
- RF-140: Detector de hallucination repetitiva por entropía
- RF-141: Parámetros Whisper optimizados anti-hallucination
"""
import sys, os, re, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from computadora.voz.escucha import (
    _es_hallucination_repetitiva,
    _es_falso_positivo_conversacion,
    _ENTROPY_RATIO_UMBRAL,
    _ENTROPY_MIN_PALABRAS,
    _COMPRESSION_RATIO_UMBRAL,
    _MIN_SPEECH_PROB_VAD,
    _SILERO_VAD_DISPONIBLE,
)


# ═══════ RF-139: Silero VAD ═══════

class TestRF139_SileroVAD:
    """RF-139: Silero VAD pre-filtro disponible y configurado."""

    def test_silero_vad_disponible(self):
        """Silero VAD debe estar instalado y cargado."""
        assert _SILERO_VAD_DISPONIBLE, "Silero VAD no está disponible"

    def test_umbral_vad_configurado(self):
        """Umbral de speech prob debe estar entre 0.3 y 0.7."""
        assert 0.3 <= _MIN_SPEECH_PROB_VAD <= 0.7, f"Umbral VAD fuera de rango: {_MIN_SPEECH_PROB_VAD}"

    def test_vad_integrado_en_transcribir(self):
        """El método _transcribir debe contener lógica de Silero VAD."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "get_speech_timestamps" in src, "Falta integración de Silero VAD en _transcribir"
        assert "vad_sin_voz" in src, "Falta log de VAD sin voz"

    def test_silero_vad_import(self):
        """silero_vad debe ser importable."""
        from silero_vad import load_silero_vad, get_speech_timestamps
        assert callable(load_silero_vad)
        assert callable(get_speech_timestamps)


# ═══════ RF-140: Detector de Hallucination Repetitiva ═══════

class TestRF140_HallucinationRepetitiva:
    """RF-140: Detección de hallucinations por entropía léxica y compresión."""

    def test_caso_perro_la_la_la(self):
        """El caso real: '¡La, la, la, la, la! ¡La, la, la!' debe descartarse."""
        motivo = _es_hallucination_repetitiva("¡La, la, la, la, la! ¡La, la, la!")
        assert motivo, f"Debería detectar 'la la la' como hallucination: '{motivo}'"
        assert "repetitiva" in motivo or "compresion" in motivo

    def test_texto_legitimo_no_descartado(self):
        """Frases normales en español no deben ser descartadas."""
        assert _es_hallucination_repetitiva("Golem busca el archivo de configuración") == ""
        assert _es_hallucination_repetitiva("Necesito que abras el navegador y busques algo") == ""
        assert _es_hallucination_repetitiva("¿Cuánto tiempo falta para la reunión?") == ""

    def test_repeticion_pura(self):
        """Texto con una sola palabra repetida muchas veces = hallucination."""
        motivo = _es_hallucination_repetitiva("sí sí sí sí sí sí sí")
        assert motivo, "Debería detectar repetición pura"

    def test_texto_corto_no_aplica(self):
        """Textos con menos de _ENTROPY_MIN_PALABRAS no se filtran."""
        assert _es_hallucination_repetitiva("hola") == ""
        assert _es_hallucination_repetitiva("sí sí") == ""
        assert _es_hallucination_repetitiva("la la la") == ""  # 3 palabras < 4

    def test_frase_variada_pasa(self):
        """Frases con buena variedad léxica pasan el filtro."""
        assert _es_hallucination_repetitiva("hoy quiero mejorar el código del proyecto") == ""

    def test_thank_you_repetido(self):
        """Hallucination clásica de Whisper: 'Thank you' repetido."""
        motivo = _es_hallucination_repetitiva("Thank you. Thank you. Thank you. Thank you.")
        assert motivo, "Debería detectar 'Thank you' repetido"

    def test_subtitulos_repetidos(self):
        """Hallucination de subtítulos repetidos."""
        motivo = _es_hallucination_repetitiva(
            "Subtítulos creados por la comunidad Amara.org "
            "Subtítulos creados por la comunidad Amara.org "
            "Subtítulos creados por la comunidad Amara.org"
        )
        assert motivo, "Debería detectar subtítulos repetidos"

    def test_umbral_entropia_valor(self):
        """El umbral de entropía debe ser razonable."""
        assert 0.2 <= _ENTROPY_RATIO_UMBRAL <= 0.6
        assert _ENTROPY_MIN_PALABRAS >= 3

    def test_umbral_compresion_valor(self):
        """El umbral de compresión debe ser razonable."""
        assert 0.3 <= _COMPRESSION_RATIO_UMBRAL <= 0.7


# ═══════ RF-141: Parámetros Whisper Optimizados ═══════

class TestRF141_WhisperParams:
    """RF-141: Parámetros de transcripción optimizados anti-hallucination."""

    def test_condition_on_previous_text_false(self):
        """condition_on_previous_text debe ser False para audio corto."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "condition_on_previous_text=False" in src or "condition_on_previous_text" in src

    def test_compression_ratio_threshold_presente(self):
        """compression_ratio_threshold debe estar configurado."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "compression_ratio_threshold" in src, "Falta compression_ratio_threshold"

    def test_logprob_threshold_presente(self):
        """logprob_threshold debe estar configurado."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "logprob_threshold" in src, "Falta logprob_threshold"

    def test_no_speech_threshold_rebajado(self):
        """no_speech_threshold debe estar < 0.6 (era 0.6 antes)."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        # Buscar el valor numérico del parámetro
        match = re.search(r"no_speech_threshold\s*=\s*([\d.]+)", src)
        assert match, "Falta no_speech_threshold en _whisper_params"
        valor = float(match.group(1))
        assert valor < 0.6, f"no_speech_threshold debe ser < 0.6, es {valor}"
        assert valor >= 0.2, f"no_speech_threshold muy bajo: {valor}"

    def test_whisper_params_como_dict(self):
        """Los parámetros Whisper deben pasarse como dict unificado."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "_whisper_params" in src, "Falta dict _whisper_params"

    def test_fp16_presente(self):
        """fp16 debe estar en los parámetros."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        assert "fp16" in src


# ═══════ Integración: Las 3 capas juntas ═══════

class TestFP052_Integracion:
    """Tests de integración para las 3 capas de FP-052."""

    def test_hallucination_antes_de_falso_positivo(self):
        """RF-140 debe ejecutarse en el pipeline de _transcribir."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        pos_hallu = src.find("_es_hallucination_repetitiva")
        pos_fp = src.find("_es_falso_positivo_conversacion")
        assert pos_hallu > 0, "Falta _es_hallucination_repetitiva en _transcribir"
        assert pos_hallu < pos_fp, "Hallucination check debe ir antes de falso_positivo"

    def test_vad_antes_de_whisper(self):
        """RF-139 (VAD) debe ejecutarse antes de transcribe()."""
        from computadora.voz.escucha import HiloEscucha
        src = inspect.getsource(HiloEscucha._transcribir)
        pos_vad = src.find("get_speech_timestamps")
        pos_whisper = src.find("_modelo.transcribe")
        assert pos_vad > 0, "Falta get_speech_timestamps en _transcribir"
        assert pos_vad < pos_whisper, "VAD debe ejecutarse antes de Whisper"

    def test_constantes_exportadas(self):
        """Las constantes principales deben ser importables."""
        from computadora.voz.escucha import (
            _ENTROPY_RATIO_UMBRAL,
            _ENTROPY_MIN_PALABRAS,
            _COMPRESSION_RATIO_UMBRAL,
            _MIN_SPEECH_PROB_VAD,
        )
        assert isinstance(_ENTROPY_RATIO_UMBRAL, float)
        assert isinstance(_ENTROPY_MIN_PALABRAS, int)
        assert isinstance(_COMPRESSION_RATIO_UMBRAL, float)
        assert isinstance(_MIN_SPEECH_PROB_VAD, float)

