#!/usr/bin/env python
"""Autodetectar hardware y configurar Continue/Ollama local en home y workspace."""

import json
import shutil
import socket
import subprocess
from pathlib import Path

import psutil

REPO_ROOT = Path(__file__).resolve().parent.parent
HOME_CONTINUE_PATH = Path.home() / '.continue' / 'config.json'
WORKSPACE_CONTINUE_PATH = REPO_ROOT / '.continue' / 'config.json'


def _detect_ollama_port(ports=(11434, 1234)) -> int:
    for port in ports:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return port
        except OSError:
            continue
    return 11434


def _build_continue_model_config(
    chat_model: str,
    autocomplete_model: str,
    embeddings_model: str,
    api_base: str,
) -> dict:
    return {
        'models': [
            {
                'title': 'Ollama Local Chat',
                'provider': 'ollama',
                'model': chat_model,
                'apiBase': api_base,
            }
        ],
        'tabAutocompleteModel': {
            'title': 'Ollama Local Autocomplete',
            'provider': 'ollama',
            'model': autocomplete_model,
            'apiBase': api_base,
        },
        'embeddingsModel': {
            'title': 'Ollama Local Embeddings',
            'provider': 'ollama',
            'model': embeddings_model,
            'apiBase': api_base,
        },
        'allowAnonymousTelemetry': False,
        'headless': False,
    }


def _safe_load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"Advertencia: no se pudo leer {path}: {e}")
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


print('=' * 60)
print('AUTODETECCIÓN DE HARDWARE PARA CONTINUE + OLLAMA')
print('=' * 60)
print()

# 1. Detectar hardware
hw_info = {
    'cpu_cores': psutil.cpu_count(logical=False),
    'cpu_logical': psutil.cpu_count(logical=True),
    'ram_gb': psutil.virtual_memory().total / (1024**3),
}

print(f"[1] CPU: {hw_info['cpu_cores']} físicos, {hw_info['cpu_logical']} lógicos")
print(f"    RAM: {hw_info['ram_gb']:.1f} GB")

# Detectar GPU
gpu_model = 'CPU only'
try:
    result = subprocess.run(
        ['wmic', 'path', 'win32_videocontroller', 'get', 'Name', '/value'],
        capture_output=True,
        text=True,
        timeout=5,
    )
    lines = [l.strip() for l in result.stdout.split('\n') if 'Name=' in l]
    if lines:
        gpu_model = lines[0].replace('Name=', '')
except Exception as e:
    print(f"    GPU detection: {e}")

print(f"[2] GPU: {gpu_model}")
print()

# 2. Recomendar modelo según hardware
print('[3] Recomendación de modelo Ollama:')
if hw_info['ram_gb'] >= 12 and 'NVIDIA' in gpu_model:
    chat_model = 'llama3.1:8b'
    autocomplete_model = 'qwen2.5-coder:1.5b-base'
    embeddings_model = 'nomic-embed-text:latest'
    reason = 'NVIDIA GPU + 12GB+ RAM → modelos chat y autocomplete locales recomendados'
elif hw_info['ram_gb'] >= 8:
    chat_model = 'deepseek-r1:1.5b'
    autocomplete_model = 'qwen2.5-coder:1.5b-base'
    embeddings_model = 'nomic-embed-text:latest'
    reason = '8GB+ RAM → modelo 1.5B + autocomplete local recomendado'
elif hw_info['ram_gb'] >= 4:
    chat_model = 'orca-mini:3b'
    autocomplete_model = 'qwen2.5-coder:1.5b-base'
    embeddings_model = 'nomic-embed-text:latest'
    reason = '4GB+ RAM → modelo 3B + autocomplete local recomendado'
else:
    chat_model = 'tinyllama:1.1b'
    autocomplete_model = 'qwen2.5-coder:1.5b-base'
    embeddings_model = 'nomic-embed-text:latest'
    reason = f'< 4GB RAM ({hw_info["ram_gb"]:.1f}GB) → modelo ligero recomendado'

print(f"    ✓ Chat model: {chat_model}")
print(f"    ✓ Autocomplete model: {autocomplete_model}")
print(f"    ✓ Embeddings model: {embeddings_model}")
print(f"    ✓ Razón: {reason}")
print()

ollama_port = _detect_ollama_port()
api_base = f'http://127.0.0.1:{ollama_port}/v1'
print(f'    ✓ Ollama API base detectado: {api_base}')
print()

model_config = _build_continue_model_config(chat_model, autocomplete_model, embeddings_model, api_base)

# 3. Guardar configuración global en home
_save_json(HOME_CONTINUE_PATH, model_config)
print('[4] Configuración guardada en home:')
print(f'    {HOME_CONTINUE_PATH}')
print()

# 4. Actualizar configuración workspace .continue
workspace_config = _safe_load_json(WORKSPACE_CONTINUE_PATH)
if workspace_config and not workspace_config.get('models'):
    backup_path = WORKSPACE_CONTINUE_PATH.parent / 'config.legacy.json'
    if not backup_path.exists():
        WORKSPACE_CONTINUE_PATH.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(WORKSPACE_CONTINUE_PATH, backup_path)
        print(f'    Se guardó copia de seguridad de configuración anterior en: {backup_path}')

workspace_merge = {**workspace_config, **model_config}
_save_json(WORKSPACE_CONTINUE_PATH, workspace_merge)
print('[5] Configuración workspace guardada en:')
print(f'    {WORKSPACE_CONTINUE_PATH}')
print()

print('=' * 60)
print('✅ CONTINUE CONFIGURADO')
print('=' * 60)
print()
print('Configuración guardada:')
print(f'  • Chat model: {chat_model}')
print(f'  • Autocomplete model: {autocomplete_model}')
print(f'  • Embeddings model: {embeddings_model}')
print(f'  • API Base: {api_base}')
print('  • Archivos:')
print(f'      - {HOME_CONTINUE_PATH}')
print(f'      - {WORKSPACE_CONTINUE_PATH}')
print()
print('INSTRUCCIONES DE USO:')
print('  1. Abre VS Code')
print('  2. Inicia Ollama: ollama serve')
print("  3. Abre la pestaña 'Continue' (panel lateral)")
print('  4. Comienza a programar con Ctrl+K (inline) o Ctrl+L (chat)')
print()
print('HOTKEYS:')
print('  Ctrl+K   : Generar código inline')
print('  Ctrl+L   : Abrir chat con el modelo')
print('  Tab      : Autocompletar (con tabAutocompleteModel)')
print()
print(f'Hardware detectado: {hw_info["cpu_logical"]} CPU @ {hw_info["ram_gb"]:.1f}GB')
print(f'Recomendación: {reason}')
