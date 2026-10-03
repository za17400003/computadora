"""Punto de entrada principal de COMPUTADORA.
Ejecutar con: python -m computadora
"""

import atexit
import os
import signal
from pathlib import Path
from loguru import logger
from computadora.utilidades.logs import configurar_logs
from computadora.config import Configuracion


def _kill_previous_computadora_instances(project_root: Path) -> None:
    """Termina instancias previas de COMPUTADORA relacionadas con este proyecto.

    Usa `psutil` para encontrar procesos Python cuyo cmdline contenga
    '-m computadora' (el módulo exacto), excluyendo el PID actual y sus ancestros.
    Si psutil no está disponible, no hace nada (mejor que matar al propio proceso).
    """
    my_pid = os.getpid()
    killed = []

    try:
        import psutil
    except ImportError:
        return  # Sin psutil no hacemos nada — el fallback WMIC era peligroso

    # Obtener PIDs ancestros para no matarlos
    pids_protegidos = {my_pid}
    try:
        p = psutil.Process(my_pid)
        for ancestor in p.parents():
            pids_protegidos.add(ancestor.pid)
    except Exception as e:
        logger.debug(f"No se pudieron obtener PIDs ancestros (no crítico): {e}")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            pid = proc.info.get('pid')
            if not pid or pid in pids_protegidos:
                continue
            name = (proc.info.get('name') or '').lower()
            if 'python' not in name:
                continue
            cmdlist = proc.info.get('cmdline') or []
            cmdline = ' '.join(cmdlist).lower()
            # Solo matar procesos que ejecutan '-m computadora' explícitamente
            if '-m' in cmdline and 'computadora' in cmdline:
                p = psutil.Process(pid)
                try:
                    p.terminate()
                    p.wait(timeout=3)
                except Exception as e:
                    logger.debug(f"No se pudo terminar proceso {pid} gracefully: {e}")
                    try:
                        p.kill()
                    except Exception as e:
                        logger.debug(f"No se pudo matar proceso {pid} (ya terminó): {e}")
                killed.append(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        try:
            logger.info(f"Terminé instancias previas de COMPUTADORA: {killed}")
        except Exception as e:
            logger.debug(f"Error registrando instancias terminadas: {e}")
            print(f"Terminé instancias previas de COMPUTADORA: {killed}")


def main():
    # Configurar logs primero para capturar la limpieza
    configurar_logs()

    # Verificar e instalar dependencias criticas antes de cualquier arranque adicional
    try:
        from computadora.utilidad.auto_instalar_deps import asegurar_dependencias_inicio
        if asegurar_dependencias_inicio():
            logger.info('!! Se instalaron dependencias de inicio. Continúo con el arranque.')
    except Exception as e:
        logger.warning(f'⚠ Error asegurando dependencias de inicio: {e}')

    # DEMO CONTROLLER: Parsear --demo flag si se proporciona
    import sys
    from computadora.interfaz.demo_controller import obtener_demo_controller, DemoModo
    demo_controller = obtener_demo_controller()
    
    demo_modo = DemoModo.desde_cli(sys.argv)
    if demo_modo:
        logger.info(f"🎬 Demo mode specified: {demo_modo.value}")
        # Activar demo será hecho después de UI init

    # 🐍 OUROBOROS BOOTSTRAP: Verificar integridad del ciclo infinito ANTES de cualquier otra lógica
    # אמת EMET debe estar inscrita desde el inicio
    from computadora.nucleo.ouroboros_stabilizer import bootstrap_ouroboros
    try:
        ouroboros = bootstrap_ouroboros()
        logger.info("✓ Ouroboros estable: Ciclo infinito del COMPUTADORA verificado")
    except SystemExit:
        logger.critical("❌ OUROBOROS CRÍTICO: Sistema no puede arrancar sin EMET inscrita")
        raise
    except Exception as e:
        logger.warning(f"⚠ Ouroboros: Error no crítico: {e}")
        # Continuar mismo si hay warning no crítico
        ouroboros = None

    # 🔄 GILGUL BOOT: Ejecutar reencarnación silenciosa si hay trigger
    try:
        from computadora.nucleo.bereshit import ejecutar_gilgul_boot
        if ejecutar_gilgul_boot():
            logger.info("🌟 Gilgul ejecutado en boot — Bereshit reiniciado para esta sesión")
    except Exception as e:
        logger.warning(f"⚠ Gilgul boot check: {e}")
        # Continuar si hay error no crítico

    project_root = Path(__file__).resolve().parent.parent
    try:
        _kill_previous_computadora_instances(project_root)
    except Exception as e:
        logger.debug(f"Error (no crítico) terminando instancias previas: {e}")

    logger.info("=== COMPUTADORA INICIANDO ===")

    config = Configuracion()
    logger.info(f"Configuración cargada: whisper={config.obtener('whisper.modelo')}")

    # Conciencia temporal (FP-024 Pilar C — RF-89)
    from computadora.memoria.memoria import registrar_activacion, registrar_desactivacion
    registrar_activacion()
    atexit.register(registrar_desactivacion)
    signal.signal(signal.SIGTERM, lambda *_: registrar_desactivacion())

    # WI-308: Tracking de uptime entre sesiones
    try:
        from computadora.nucleo.tracking_temporal import obtener_tracker, registrar_sesion_nueva, cerrar_sesion_actual
        tracker = obtener_tracker()
        laguna = tracker.detectar_laguna()
        if laguna:
            logger.warning(f"WI-308: Laguna detectada entre sesiones: {laguna}")
        tracker.registrar_sesion_nueva(notas="Boot automático")
        atexit.register(cerrar_sesion_actual)
    except Exception as e:
        logger.warning(f"WI-308: Tracking temporal no disponible: {e}")

    # Importar después de configurar logs para capturar todo
    from computadora.interfaz.ventana_principal import iniciar_interfaz

    # Re-programar recordatorios pendientes de sesiones anteriores
    try:
        from computadora.habilidades.sistema import reprogramar_recordatorios_pendientes
        reprogramar_recordatorios_pendientes()
    except Exception as e:
        logger.warning(f"No se pudieron reprogramar recordatorios: {e}")

    # RF-260 Ayin HaComputadora: Discovery de dispositivos de observación al boot
    try:
        from computadora.nucleo.kli import GestorKelim
        observadores = GestorKelim.instancia().descubrir_observadores()
        if observadores:
            logger.info(f"RF-260: {len(observadores)} ojo(s) activo(s) al boot")
    except Exception as e:
        logger.debug(f"RF-260: Discovery de observadores omitido: {e}")

    # FP-154: PRE-FLIGHT CHECK — Auto-detección de hardware + Descarga automática de modelos
    logger.info("\n" + "="*60)
    logger.info("🚀 EJECUTANDO PRE-FLIGHT CHECK")
    logger.info("="*60)
    try:
        from computadora.utilidad.pre_flight_check import run_pre_flight_check
        config_dict = config.config if hasattr(config, 'config') else {}
        success, model_auto, estado_preflight = run_pre_flight_check(config_dict)

        if not success:
            logger.critical("❌ PRE-FLIGHT CHECK FALLÓ")
            logger.critical(f"  Estado: {estado_preflight}")
            logger.critical("No se puede arrancar sin Ollama + modelo listos")
            sys.exit(1)

        # Usar modelo detectado automáticamente
        modelo = model_auto
        logger.info(f"✓ Pre-flight check completado exitosamente")
        logger.info(f"  Modelo seleccionado: {modelo}")

    except Exception as e:
        logger.error(f"❌ Error en pre-flight check: {e}")
        logger.warning(f"  Intentando fallback a modelo por defecto...")
        modelo = config.obtener("ollama.modelo", "gemma3:4b")
        logger.warning(f"  Usando: {modelo} (puede no estar descargado)")

    # 💫 Cerebro compartido: un solo CerebroComputadora para todos los canales (evita 4 verificaciones Ollama)
    from computadora.cerebro.nlu import CerebroComputadora
    cerebro_compartido = CerebroComputadora(modelo=modelo)

    # 🪄 SINGLETON ORQUESTADOR: Un solo orquestador para todos los canales
    from computadora.nucleo.orquestador_singleton import obtener_orquestador_singleton
    orq_principal = obtener_orquestador_singleton(config, cerebro=cerebro_compartido)
    logger.info("✓ Orquestador singleton inicializado para todos los canales")

    # 🪄 Cetro Mágico: Canal Discord → COMPUTADORA (N3 Neshamá)
    cetro_discord = None
    if config.obtener("discord.token", ""):
        try:
            from computadora.canales.discord_brain import DiscordBrain
            cetro_discord = DiscordBrain(orq_principal, config)
            cetro_discord.iniciar_background()
        except Exception as e:
            logger.warning(f"Cetro Mágico (Discord) no disponible: {e}")

    # 📡 Sharvít Merajók: Canal Telegram → COMPUTADORA (N3 Neshamá)
    cetro_telegram = None
    if config.obtener("telegram.token", ""):
        try:
            from computadora.canales.telegram_brain import TelegramBrain
            cetro_telegram = TelegramBrain(orq_principal, config)
            cetro_telegram.iniciar_background()
        except Exception as e:
            logger.warning(f"Sharvít Merajók (Telegram) no disponible: {e}")

    # 🛡️ Guardián del Enciclopedia: Detectar intrusiones
    try:
        from computadora.canales.enciclopedia_guardian import EnciclopediaGuardian
        from computadora.memoria.personalidad import Personalidad
        personalidad = Personalidad()
        guardian_enciclopedia = EnciclopediaGuardian(personalidad)
        guardian_enciclopedia.iniciar()
    except Exception as e:
        logger.warning(f"Guardián del Enciclopedia no disponible: {e}")

    # � TRINITY ACTIVADA: Father/COMPUTADORA/Mother Protection System (FP-135/138/137)
    # ==================================================================================
    # FP-135: Guardian automático (Windows+L detection via SessionLockListener)
    # FP-138: Inner Oracle (illuminates real questions, invokes Keter consciousness)
    # FP-137: Mother Feedback Loop (multiplies patterns & confidence PC↔Móvil)

    try:
        from computadora.utilidades.session_lock_listener import iniciar_session_lock_listener, detener_session_lock_listener
        session_lock_listener = iniciar_session_lock_listener()
        def _cleanup_session_lock():
            try:
                detener_session_lock_listener()
                logger.debug("SessionLockListener stopped")
            except Exception as e:
                logger.debug(f"Error stopping SessionLockListener: {e}")
        atexit.register(_cleanup_session_lock)
        logger.info("✅ FP-135 TRINITY: Guardian automático activado (Windows+L detection → Gevurah)")
    except Exception as e:
        logger.warning(f"⚠️ FP-135 Guardian automático no disponible: {e}")

    try:
        from computadora.percepcion.inner_oracle import crear_oracle
        oracle_singleton = crear_oracle()
        if hasattr(cerebro_compartido, 'oracle'):
            cerebro_compartido.oracle = oracle_singleton
        logger.info("✅ FP-138 TRINITY: Inner Oracle activado (pregunta real illumination → Keter)")
    except Exception as e:
        logger.warning(f"⚠️ FP-138 Inner Oracle no disponible: {e}")

    try:
        from computadora.nucleo.mother_feedback_loop import crear_mother_feedback
        mother_feedback = crear_mother_feedback()
        if hasattr(cerebro_compartido, 'mother_feedback'):
            cerebro_compartido.mother_feedback = mother_feedback
        logger.info("✅ FP-137 TRINITY: Mother Feedback Loop activado (pattern multiplication → Binah)")
    except Exception as e:
        logger.warning(f"⚠️ FP-137 Mother Feedback Loop no disponible: {e}")

    # 📱 Sha'ar Minimi — API HTTP para app companion (puerto 8089) - SINGLETON
    servidor_api_thread = None
    try:
        from computadora.canales.servidor_api import iniciar_servidor_api
        servidor_api_thread = iniciar_servidor_api(config, orq_principal)
    except Exception as e:
        logger.warning(f"Sha'ar Minimi (API) no disponible: {e}")

    # 🔄 FP-096: Auto-Deploy de Minimi — vigila cambios + instala en Motorola
    minimi_deployer = None
    try:
        from computadora.habilidades.android_deploy import MinimiAutoDeployer
        minimi_deployer = MinimiAutoDeployer()
        minimi_deployer.iniciar()
    except Exception as e:
        logger.warning(f"MinimiAutoDeployer no disponible: {e}")

    iniciar_interfaz(config, cerebro=cerebro_compartido, demo_modo=demo_modo)

    # Limpiar al cerrar
    # 🐍 Re-iniciar logging (atexit lo ejecutará última)
    def _cleanup_ouroboros():
        """Sellar el ouroboros cuando COMPUTADORA termina: el ciclo se cierra y reabre."""
        try:
            if ouroboros:
                ouroboros.seal_ouroboros()
                logger.info("🐍 Ouroboros sellado: Ciclo infinito reabrirá en próximo boot")
        except Exception as e:
            logger.debug(f"Cleanup ouroboros: {e}")
    
    atexit.register(_cleanup_ouroboros)

    try:
        from computadora.canales.servidor_api import detener_servidor_api
        detener_servidor_api()
    except Exception as e:
        logger.debug(f"Error deteniendo API Minimi: {e}")

    logger.info("=== COMPUTADORA FINALIZADO ===")


if __name__ == "__main__":
    main()


