"""Script para analizar y sugerir migración de tests a grupos.

Modo por defecto: dry-run (solo informa). Para aplicar, correr con `--apply`.

Estrategia:
- Clasificar ficheros por prefijos o keywords
- Mostrar propuesta de movimiento
- (Opcional) mover archivos físicamente si --apply
"""
import argparse
import shutil
from pathlib import Path

NAME_MAP = {
    # Core / system behavior
    'test_bereshit.py': 'core',
    'test_fsm_golem.py': 'core',
    'test_gestor_procesos.py': 'core',
    'test_memoria.py': 'core',
    'test_operatividad_core_mayo3.py': 'core',
    'test_ouroboros_stabilizer.py': 'core',
    'test_proactividad.py': 'core',
    'test_proactividad_manual.py': 'core',
    'test_profile.py': 'core',
    'test_red_parsing.py': 'core',
    'test_session_lock_listener.py': 'core',
    'test_vida_autonoma.py': 'core',
    'test_cache_ttl.py': 'core',
    'test_balance_proactividad.py': 'core',
    'test_hot_reload.py': 'core',
    'test_historial_dinamico.py': 'core',
    'test_shir_haneshama.py': 'core',
    'test_unificado.py': 'core',
    'test_jojma_local.py': 'nlu_dialogo',
    'test_inner_oracle.py': 'nlu_dialogo',
    'test_web.py': 'integracion',
    'test_web_security.py': 'seguridad',
    'test_discord_brain.py': 'integracion',
    'test_emet.py': 'integracion',
    'test_emet_minimi_audit.py': 'integracion',
    'test_grimorio_emet_codigo.py': 'integracion',
    'test_mother_feedback_loop.py': 'integracion',
    'test_copilot_bridge.py': 'integracion',
    'test_watcher_solicitudes.py': 'integracion',
    'test_vision_emet.py': 'integracion',
    'test_verificador_grimorio.py': 'integracion',
    'test_dibujante_orbe.py': 'features',
    'test_demo_secuencia.py': 'features',
    'test_demos_expand.py': 'features',
    'test_estilos.py': 'features',
    'test_ferrofluid.py': 'features',
    'test_hechizos_hp.py': 'features',
    'test_maljut_fixes.py': 'features',
    'test_maljut_smoothing.py': 'features',
    'test_coherencia_formal.py': 'features',
    'test_coherencia_99_100_completa.py': 'features',
    'test_srs_coherencia.py': 'features',
    'test_srs_coherencia_pytest.py': 'features',
    'test_validacion_visual_wi325_wi326.py': 'features',
    'test_pre_flight_check.py': 'instalacion',
    'test_wmic.py': 'hardware_rendimiento',
    'test_wi272a_biometry_framework.py': 'seguridad',
    'test_wi273a_coocurrence_predictor.py': 'features',
    'test_wi308_uptime_tracking.py': 'hardware_rendimiento',
    'test_vision_emet.py': 'integracion',
    'test_emocion_rostro.py': 'features',
    'test_ciclo14_live_execution.py': 'integracion',
    'test_ciclo18_rf54_56_57_security.py': 'seguridad',
    'test_concurrent_animation.py': 'hardware_rendimiento',
    'test_recovery_checkpoint.py': 'core',
    '_test_whisper.py': 'voz_audio',
    '_test_animation_instrumentation.py': 'hardware_rendimiento',
}

KEYWORDS = {
    'core': ['bloque', 'boot', 'import', 'app_resolve', 'bereshit', 'gestor', 'memoria', 'proactividad', 'profile', 'operatividad', 'ouroboros', 'vida_autonoma', 'cache', 'balance', 'session', 'red_parsing', 'hot_reload', 'historial', 'shir_haneshama', 'unificado'],
    'nlu_dialogo': ['nlu', 'dialogo', 'conversacion', 'nlu_mercurio', 'inner_oracle', 'jojma', 'wi324_watchdog_nlu_sync'],
    'voz_audio': ['voz', 'tts', 'audio', 'wake_word', 'habla', 'demo_tts', 'echo', 'wakeup', 'habla_tts'],
    'hardware_rendimiento': ['gpu', 'hardware', 'perf', 'fps', 'profiler', 'stress_testing', 'ciclo13_stress_testing'],
    'seguridad': ['seguridad', 'hardening', 'rfs', 'hf', 'tikun', 'web_security', 'minimi_password', 'gilgul_master_password', 'control_remoto_auth'],
    'integracion': ['metatron', 'integration', 'integracion', 'guardian', 'emet', 'discord', 'grimo', 'watcher', 'web', 'vision_emet', 'copilot_bridge', 'patrones_guardian', 'grinorio', 'grimorio', 'yikavu'],
    'instalacion': ['install', 'pyqt6', 'android_deploy', 'auto_install_deps', 'pre_flight_check'],
    'features': ['fp', 'feature', 'patrones', 'demos', 'demo', 'coherencia', 'composicion_inductiva', 'ferrofluid', 'estilos', 'validacion_visual', 'srs_coherencia', 'maljut', 'shaman', 'axiomas', 'emocion_rostro', 'niveles_me_n', 'coocurrence_predictor'],
    'smoke': ['smoke', 'run_all_tests_maestro'],
}


def classify(name):
    if name in NAME_MAP:
        return NAME_MAP[name]
    lname = name.lower()
    for grp, keys in KEYWORDS.items():
        for k in keys:
            if k in lname:
                return grp
    return 'otros'


def main(dry_run=True):
    tests_dir = Path('tests')
    moved = []
    for p in sorted(tests_dir.glob('*.py')):
        grp = classify(p.name)
        target_dir = tests_dir / grp
        target_dir.mkdir(parents=True, exist_ok=True)
        if grp == 'otros' or p.parent.name == grp:
            continue
        dest = target_dir / p.name
        moved.append((p.name, grp, str(dest)))
        if not dry_run:
            shutil.move(str(p), str(dest))
    # print report
    for name, grp, dest in moved:
        print(f'{name} -> {grp} ({dest})')
    print(f'Total candidates: {len(moved)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='Mover archivos (por defecto dry-run)')
    args = parser.parse_args()
    main(dry_run=not args.apply)
