import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from computadora.utilidad.pre_flight_check import (
    _is_chat_capable_model,
    _select_best_from_installed,
    HardwareProfile,
)


def test_is_chat_capable_model_rejects_embedding_only():
    assert not _is_chat_capable_model('nomic-embed-text:latest')
    assert _is_chat_capable_model('llama2:7b')


def test_select_best_from_installed_skips_embedding_only_models():
    hardware = HardwareProfile(
        total_ram_gb=16.0,
        gpu_available=True,
        gpu_vram_gb=8.0,
        gpu_type='nvidia',
        cuda_available=True,
        cuda_compute_capability='8.0',
    )
    best = _select_best_from_installed(['nomic-embed-text:latest', 'llama2:7b'], hardware)
    assert best == 'llama2:7b'
