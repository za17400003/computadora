"""
יסוד (Yesod) — Fundamento. Canal entre Tiféret y Maljut.
Orquestador central de Computadora.
Recibe input → cerebro LLM → respuesta → memoria.
"""

from loguru import logger
from computadora.cerebro.nlu import CerebroComputadora  # WI-VOICE-FIX: NLU imports
from computadora.memoria.memoria import add_memory, start_daily_compressor

# Bandera para evitar logs duplicados desde instancias previas
_orquestador_ya_inicializado = False


class Orquestador:
    def __init__(self, config, cerebro=None):
        global _orquestador_ya_inicializado
        
        self.config = config
        modelo = config.obtener("ollama.modelo", "gemma3:4b")
        if cerebro is not None:
            self.cerebro = cerebro
            if not _orquestador_ya_inicializado:
                logger.info(f"Orquestador inicializado con cerebro compartido (modelo '{modelo}')")
                _orquestador_ya_inicializado = True
        else:
            self.cerebro = CerebroComputadora(modelo=modelo)
            if not _orquestador_ya_inicializado:
                logger.info(f"Orquestador inicializado con modelo '{modelo}'")
                _orquestador_ya_inicializado = True

        # Autopercepción del entorno (נשמה Neshamá) — SOLO PRIMERA VEZ
        try:
            from computadora.nucleo.entorno import EntornoSistema
            self.entorno = EntornoSistema.instancia()
            if not hasattr(EntornoSistema, '_ya_logueado'):
                logger.info(f"Entorno: {self.entorno.resumen_corto()}")
                EntornoSistema._ya_logueado = True
        except Exception as e:
            self.entorno = None
            logger.warning(f"EntornoSistema no disponible: {e}")

        # WI-119: Da'at — Hub sensorial (percepción multimodal) — SOLO PRIMERA VEZ
        try:
            from computadora.percepcion.perceptor import PerceptorDaat
            self.perceptor = PerceptorDaat()
            if not hasattr(PerceptorDaat, '_ya_logueado'):
                logger.info("PerceptorDaat inicializado")
                PerceptorDaat._ya_logueado = True
        except Exception as e:
            self.perceptor = None
            logger.warning(f"PerceptorDaat no disponible: {e}")

        # Iniciar compresor diario en background (no bloqueante)
        try:
            start_daily_compressor()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

    def set_callbacks(self, on_nivel=None, on_herramienta=None, solicitar_permiso_copilot=None, on_movimiento=None, on_fin_conversacion=None, on_despedida_guardian=None, on_fragmento=None, on_progreso=None, on_preguntar_modo=None, solicitar_permiso_sistema=None, on_enroll_persona=None, on_bloqueo_seguridad=None, on_tzimtzum=None, on_confianza=None, on_complejidad=None, on_frustracion=None):
        """Asigna callbacks del cerebro para comunicarse con la UI."""
        self.cerebro.on_nivel = on_nivel
        self.cerebro.on_herramienta = on_herramienta
        self.cerebro.on_movimiento = on_movimiento
        self.cerebro.on_fragmento = on_fragmento
        self.cerebro.solicitar_permiso_copilot = solicitar_permiso_copilot
        self.cerebro._on_fin_conversacion = on_fin_conversacion
        self.cerebro._on_despedida_guardian = on_despedida_guardian
        self.cerebro.on_progreso = on_progreso
        self.cerebro.on_preguntar_modo = on_preguntar_modo
        self.cerebro._on_enroll_persona = on_enroll_persona
        self.cerebro.on_bloqueo_seguridad = on_bloqueo_seguridad
        self.cerebro.on_tzimtzum = on_tzimtzum
        # FP-022: Canal bidireccional
        self.cerebro.on_confianza = on_confianza
        self.cerebro.on_complejidad = on_complejidad
        self.cerebro.on_frustracion = on_frustracion

        # Gestor de permisos del sistema (שמירה Shmirah) — crear solo una vez
        if not hasattr(self, 'permisos') or self.permisos is None:
            try:
                from computadora.nucleo.permisos import GestorPermisos
                self.permisos = GestorPermisos()
                logger.info("GestorPermisos inicializado")
            except Exception as e:
                self.permisos = None
                logger.warning(f"GestorPermisos no disponible: {e}")
        if self.permisos and solicitar_permiso_sistema:
            self.permisos.set_callback(solicitar_permiso_sistema)

    def recrear_cerebro(self):
        """Hot-reload: reimporta nlu y recrea CerebroComputadora preservando callbacks."""
        # Guardar callbacks actuales
        callbacks = {}
        for attr in ("on_nivel", "on_herramienta", "on_movimiento", "on_fragmento",
                      "solicitar_permiso_copilot", "_on_fin_conversacion",
                      "_on_despedida_guardian", "on_progreso", "on_preguntar_modo",
                      "_on_enroll_persona", "on_bloqueo_seguridad", "on_tzimtzum",
                      "on_confianza", "on_complejidad", "on_frustracion"):
            callbacks[attr] = getattr(self.cerebro, attr, None)

        # Guardar refs inyectadas
        personalidad_ref = getattr(self.cerebro, "_personalidad_ref", None)
        gestor_personas = getattr(self.cerebro, "_gestor_personas", None)
        orbe_ref = getattr(self.cerebro, "_orbe_ref", None)

        # Reimportar y recrear
        import importlib
        from computadora.cerebro import nlu
        importlib.reload(nlu)
        from computadora.cerebro.nlu import CerebroComputadora as CerebroFresco

        modelo = self.config.obtener("ollama.modelo", "gemma3:4b")
        self.cerebro = CerebroFresco(modelo=modelo)

        # Restaurar callbacks
        for attr, cb in callbacks.items():
            if cb is not None:
                setattr(self.cerebro, attr, cb)

        # Restaurar refs
        if personalidad_ref:
            self.cerebro._personalidad_ref = personalidad_ref
        if gestor_personas:
            self.cerebro._gestor_personas = gestor_personas
        if orbe_ref:
            self.cerebro._orbe_ref = orbe_ref

        logger.info("Cerebro recreado por hot-reload — callbacks restaurados")

    def procesar(self, texto: str) -> str:
        """Procesa texto del usuario y devuelve respuesta."""
        logger.info(f"Procesando: '{texto}'")
        # Registrar en memoria local
        try:
            add_memory("user", texto)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        respuesta = self.cerebro.pensar(texto)

        # Registrar respuesta en memoria
        try:
            if respuesta:
                add_memory("assistant", respuesta)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        logger.info(f"Respuesta: '{respuesta}'")
        return respuesta


