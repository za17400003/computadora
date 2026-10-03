"""
RF-227 (FP-077): Flujos del Shomer HaBáyit — extraídos de nlu.py.
Funciones de flujo guardián (RF-210→RF-219) para equilibrar Tiféret.

Las funciones reciben el cerebro (CerebroComputadora) como primer argumento
para acceder a estado y callbacks sin ser métodos de la clase.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from computadora.cerebro.nlu import CerebroComputadora

logger = logging.getLogger("computadora_shim")


def activar_guardian(cerebro: CerebroComputadora) -> str:
    """RF-210/212, FP-113 WI-154: Activa modo guardián.
    El guardián nunca descansa — mantiene mic y cámara encendidas.
    No afecta ciclo circadiano: usa descanso_guardian, no fase activa."""
    # WI-AUDIO: Bloquear activación si feature flag está desactivado (raíz del problema)
    from computadora.nucleo.feature_flags import FeatureFlags
    if not FeatureFlags.obtener("guardian_activo"):
        logger.info("⛔ Intento de activar guardián BLOQUEADO (feature_flag=False)")
        return "Guardian temporalmente desactivado. Sistema en modo de prueba."
    
    if cerebro.guardian_manager.activo:
        return "Ya estoy en modo guardián, señor."
    
    # Usar guardian_manager para centralizar estado
    cerebro.guardian_manager.activar(razon="flujos_guardian_activar", origen="flujos_guardian")
    cerebro._guardian_eventos: list[dict] = []
    cerebro._guardian_mantener_sensores = True  # FP-113: flag para mic+cam
    # Activar vigía nocturna en ciclo circadiano (descanso_guardian, no activo)
    try:
        from computadora.nucleo.proactividad import obtener_ciclo_circadiano
        ciclo = obtener_ciclo_circadiano()
        if ciclo and hasattr(ciclo, 'forzar_vigia_nocturna'):
            ciclo.forzar_vigia_nocturna()
    except Exception as e:
        logger.debug(f"Error activando vigía nocturna: {e}")
    # Conectar cámara via GestorKelim (compartida, no exclusiva)
    try:
        from computadora.nucleo.kli import GestorKelim
        from computadora.habilidades.vision import KliCamara
        gestor = GestorKelim.instancia()
        if "camara_local" not in {k["id"] for k in gestor.listar()}:
            cam = KliCamara()
            gestor.registrar(cam)
        gestor.conectar("camara_local")
        logger.info("🛡️ Cámara conectada para guardián")
    except Exception as e:
        logger.debug(f"Error conectando cámara para guardián: {e}")
    # Notificar a interfaz
    if cerebro._on_despedida_guardian:
        cerebro._on_despedida_guardian()
    logger.info("🛡️ Modo guardián ACTIVADO — sensores activos")
    return "Modo guardián activado, señor. Vigilo con ojos y oídos."


def desactivar_guardian(cerebro: CerebroComputadora) -> str:
    """RF-211: Desactiva modo guardián. Libera flag de sensores."""
    if not cerebro.guardian_manager.activo:
        return "No estoy en modo guardián, señor."
    
    # Usar guardian_manager para centralizar estado
    cerebro.guardian_manager.desactivar(razon="flujos_guardian_desactivar", origen="flujos_guardian")
    cerebro._guardian_mantener_sensores = False
    # Restaurar fase activa en ciclo circadiano
    try:
        from computadora.nucleo.proactividad import obtener_ciclo_circadiano
        ciclo = obtener_ciclo_circadiano()
        if ciclo and hasattr(ciclo, 'forzar_activo'):
            ciclo.forzar_activo()
    except Exception as e:
        logger.debug(f"Error restaurando fase activa: {e}")
    logger.info("🛡️ Modo guardián DESACTIVADO")
    return "Modo guardián desactivado, señor. Bienvenido de vuelta."


def flujo_dormir(cerebro: CerebroComputadora, *, vigila: bool) -> str:
    """RF-213/214: Flujo nocturno. vigila=True activa cámara si disponible."""
    activar_guardian(cerebro)
    partes = ["Entendido, señor. Activo modo guardián nocturno."]
    if vigila:
        try:
            from computadora.nucleo.kli import GestorKelim
            from computadora.habilidades.vision import KliCamara
            gestor = GestorKelim.instancia()
            if "camara_local" not in {k["id"] for k in gestor.listar()}:
                cam = KliCamara()
                gestor.registrar(cam)
            if gestor.conectar("camara_local"):
                partes.append("Cámara activada. Vigilaré con visión nocturna.")
            else:
                partes.append("No pude activar la cámara, pero vigilo la red.")
        except Exception as e:
            logger.debug(f"Error activando cámara nocturna: {e}")
            partes.append("Vigilo la red. La cámara no está disponible.")
    partes.append("Descanse bien.")
    return " ".join(partes)


def tzimtzum_con_mic(cerebro: CerebroComputadora) -> str:
    """RF-215: Tzimtzum pero mantiene micrófono activo."""
    if cerebro.on_tzimtzum:
        try:
            cerebro.on_tzimtzum("comando")
        except Exception as e:
            logger.debug("Error en tzimtzum callback: %s", e)
    return "Entendido, señor. Me duermo pero mantengo el oído activo. Diga mi nombre para despertarme."


def confirmar_reinicio(cerebro: CerebroComputadora) -> str:
    """RF-219: Solicita confirmación antes de reiniciar."""
    cerebro._reinicio_pendiente = True
    return "¿Está seguro de que quiere reiniciarme, señor? Diga 'sí' para confirmar."


def generar_reporte_matutino(cerebro: CerebroComputadora) -> str:
    """RF-217: Genera reporte de eventos nocturnos."""
    eventos = getattr(cerebro, '_guardian_eventos', [])
    if not eventos:
        return "Buenos días, señor. Noche tranquila, sin novedades que reportar."
    n = len(eventos)
    resumen = f"Buenos días, señor. Durante la noche registré {n} evento{'s' if n > 1 else ''}. "
    tipos: dict[str, int] = {}
    for ev in eventos:
        t = ev.get("tipo", "otro")
        tipos[t] = tipos.get(t, 0) + 1
    detalles = ", ".join(f"{v} de {k}" for k, v in tipos.items())
    resumen += f"Resumen: {detalles}."
    cerebro._guardian_eventos = []
    return resumen


