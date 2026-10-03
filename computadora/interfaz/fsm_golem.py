"""
FP-027 WI-155: FSM formal del Maljut — extraído de ventana_principal.py.
Máquina de estados, enum y tabla de transiciones válidas.
"""

from enum import Enum


class EstadoMaljut(Enum):
    """Estados formales del orbe — reemplazo de strings ad-hoc."""
    DORMIDO = "dormido"
    ESCUCHANDO = "escuchando"
    PROCESANDO = "procesando"
    HABLANDO = "hablando"
    TRABAJANDO = "trabajando"
    ERROR = "error"
    BERESHIT = "bereshit"
    DESPERTANDO = "despertando"
    DESCANSO_GUARDIAN = "descanso_guardian"
    VIGILIA = "vigilia"
    CORTESIA = "cortesia"
    ALERTA_EXTRANO = "alerta_extrano"
    GEVURA_ACTIVA = "gevura_activa"


# Tabla de transiciones válidas: {estado_actual: {estados_destino_permitidos}}
TRANSICIONES_VALIDAS: dict[EstadoMaljut, set[EstadoMaljut]] = {
    EstadoMaljut.DORMIDO: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.BERESHIT, EstadoMaljut.DESPERTANDO,
        EstadoMaljut.VIGILIA, EstadoMaljut.DESCANSO_GUARDIAN,
        EstadoMaljut.HABLANDO,  # RF-224: TTS pendiente llega tras dormir (respuesta Ollama tardía)
    },
    EstadoMaljut.BERESHIT: {
        EstadoMaljut.DESPERTANDO, EstadoMaljut.DORMIDO, EstadoMaljut.ERROR,
    },
    EstadoMaljut.DESPERTANDO: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO, EstadoMaljut.PROCESANDO,
        EstadoMaljut.HABLANDO,  # RF-224: interrupción voz en Bereshit
    },
    EstadoMaljut.ESCUCHANDO: {
        EstadoMaljut.PROCESANDO, EstadoMaljut.DORMIDO, EstadoMaljut.HABLANDO,
        EstadoMaljut.ERROR, EstadoMaljut.DESCANSO_GUARDIAN,
        EstadoMaljut.ALERTA_EXTRANO, EstadoMaljut.CORTESIA, EstadoMaljut.VIGILIA,
        EstadoMaljut.DESPERTANDO,  # RF-224: cambio fase circadiana
        EstadoMaljut.ESCUCHANDO,  # RF-224: self-loop (Whisper sin cambio)
    },
    EstadoMaljut.PROCESANDO: {
        EstadoMaljut.HABLANDO, EstadoMaljut.TRABAJANDO, EstadoMaljut.ERROR,
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO, EstadoMaljut.GEVURA_ACTIVA,
        EstadoMaljut.DESCANSO_GUARDIAN,  # RF-224: despedida activa guardián
        EstadoMaljut.ALERTA_EXTRANO,  # WI-AUDIO: voz desconocida durante procesamiento
        EstadoMaljut.PROCESANDO,  # RF-224: self-loop (re-entrada Ollama)
    },
    EstadoMaljut.TRABAJANDO: {
        EstadoMaljut.HABLANDO, EstadoMaljut.PROCESANDO, EstadoMaljut.ESCUCHANDO,
        EstadoMaljut.ERROR, EstadoMaljut.DORMIDO,
        EstadoMaljut.TRABAJANDO,  # RF-224: self-loop (tool-loop iteraciones sucesivas)
    },
    EstadoMaljut.HABLANDO: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.PROCESANDO, EstadoMaljut.DORMIDO,
        EstadoMaljut.ERROR,
        EstadoMaljut.HABLANDO,  # RF-224: self-loop (chunks TTS streaming)
    },
    EstadoMaljut.ERROR: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO, EstadoMaljut.PROCESANDO,
    },
    EstadoMaljut.DESCANSO_GUARDIAN: {
        EstadoMaljut.DESPERTANDO, EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO,
        EstadoMaljut.CORTESIA, EstadoMaljut.VIGILIA,
        EstadoMaljut.HABLANDO,  # RF-224: TTS habla en modo guardián
        EstadoMaljut.DESCANSO_GUARDIAN,  # RF-224: self-loop (guardian tick)
    },
    EstadoMaljut.VIGILIA: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO, EstadoMaljut.DESCANSO_GUARDIAN,
        EstadoMaljut.PROCESANDO,
    },
    EstadoMaljut.CORTESIA: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.DORMIDO, EstadoMaljut.PROCESANDO,
        EstadoMaljut.DESCANSO_GUARDIAN,
    },
    EstadoMaljut.ALERTA_EXTRANO: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.PROCESANDO, EstadoMaljut.DORMIDO,
    },
    EstadoMaljut.GEVURA_ACTIVA: {
        EstadoMaljut.ESCUCHANDO, EstadoMaljut.PROCESANDO, EstadoMaljut.DORMIDO,
    },
}

# Lookup rápido de string→enum para compatibilidad con código existente
STR_A_ESTADO: dict[str, EstadoMaljut] = {e.value: e for e in EstadoMaljut}


