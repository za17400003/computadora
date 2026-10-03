# tests/test_hardware_optimizer.py
import pytest
from unittest.mock import patch, MagicMock
from computadora.utilidad.hardware_optimizer import HardwareOptimizer
from computadora.metatron import MetatronOrquestador

def test_hardware_optimizer_init():
    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    assert optimizer.metatron == metatron
    assert isinstance(optimizer._task_assignments, dict)
    assert optimizer._monitoring == True

@patch('psutil.cpu_count')
def test_detect_gpu_available(mock_cpu_count):
    mock_cpu_count.return_value = 4

    with patch('GPUtil.getGPUs', return_value=[MagicMock()]):
        metatron = MetatronOrquestador()
        optimizer = HardwareOptimizer(metatron)
        assert optimizer._has_gpu == True

@patch('psutil.cpu_count')
def test_detect_gpu_unavailable(mock_cpu_count):
    mock_cpu_count.return_value = 4

    with patch('GPUtil.getGPUs', side_effect=ImportError):
        metatron = MetatronOrquestador()
        optimizer = HardwareOptimizer(metatron)
        assert optimizer._has_gpu == False

def test_assign_task_high_priority_gpu():
    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)
    optimizer._has_gpu = True

    device = optimizer.assign_task('whisper_stt', lambda: None, 'high')
    assert device == 'gpu'
    assert optimizer._task_assignments['whisper_stt'] == 'gpu'

def test_assign_task_low_priority():
    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    device = optimizer.assign_task('background_task', lambda: None, 'low')
    assert device == 'cpu_low'
    assert optimizer._task_assignments['background_task'] == 'cpu_low'

def test_assign_task_normal_priority():
    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    device = optimizer.assign_task('normal_task', lambda: None, 'normal')
    assert device == 'cpu_high'
    assert optimizer._task_assignments['normal_task'] == 'cpu_high'

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
def test_get_system_load(mock_vmem, mock_cpu):
    mock_cpu.return_value = 45.5
    mock_vmem.return_value.percent = 67.8

    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    load = optimizer.get_system_load()
    assert load['cpu_percent'] == 45.5
    assert load['ram_percent'] == 67.8
    assert load['cpu_available'] == 54.5
    assert load['ram_available'] == 32.2

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
def test_optimize_for_load_high_cpu(mock_vmem, mock_cpu):
    mock_cpu.return_value = 85.0
    mock_vmem.return_value.percent = 50.0

    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    optimizations = optimizer.optimize_for_load()
    assert optimizations['reduce_fps'] == True
    assert optimizations['disable_animations'] == True

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
def test_optimize_for_load_moderate_cpu(mock_vmem, mock_cpu):
    mock_cpu.return_value = 65.0
    mock_vmem.return_value.percent = 50.0

    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    optimizations = optimizer.optimize_for_load()
    assert optimizations['reduce_fps'] == True
    assert optimizations['disable_animations'] == False

@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
def test_optimize_for_load_normal(mock_vmem, mock_cpu):
    mock_cpu.return_value = 45.0
    mock_vmem.return_value.percent = 50.0

    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    optimizations = optimizer.optimize_for_load()
    assert optimizations['reduce_fps'] == False
    assert optimizations['disable_animations'] == False

def test_stop_monitoring():
    metatron = MetatronOrquestador()
    optimizer = HardwareOptimizer(metatron)

    # Let monitoring start
    import time
    time.sleep(0.1)

    optimizer.stop_monitoring()
    assert optimizer._monitoring == False
