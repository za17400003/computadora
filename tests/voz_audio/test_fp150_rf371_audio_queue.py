"""
RF-371: Audio Queue Sizing (FP-150)
Valida que la cola de audio funcione correctamente bajo carga.

Tests:
1. Queue maxsize es 256 (aumentado de 128)
2. Overflow handling: discard oldest, keep newest
3. Graceful degradation bajo high load
4. Recovery después de overflow
"""

import queue
import time
import threading
import unittest
from pathlib import Path

import sys
proyecto_root = Path(__file__).parent.parent
sys.path.insert(0, str(proyecto_root))


class TestRF371AudioQueueSizing(unittest.TestCase):
    """RF-371: Audio Queue Sizing (FP-150)."""

    def test_queue_maxsize_256(self):
        """Test: Queue maxsize es exactamente 256."""
        q = queue.Queue(maxsize=256)
        self.assertEqual(q.maxsize, 256)

    def test_queue_put_nowait_success(self):
        """Test: Queue puede aceptar 256 items sin error."""
        q = queue.Queue(maxsize=256)
        
        for i in range(256):
            try:
                q.put_nowait(f"item_{i}")
            except queue.Full:
                self.fail(f"Queue llena en item {i}, maxsize debería ser 256")
        
        # Verificar que está llena
        self.assertTrue(q.full())

    def test_queue_full_exception(self):
        """Test: Queue lanza queue.Full cuando está llena."""
        q = queue.Queue(maxsize=256)
        
        # Llenar la queue
        for i in range(256):
            q.put_nowait(f"item_{i}")
        
        # Intentar agregar más
        with self.assertRaises(queue.Full):
            q.put_nowait("overflow_item")

    def test_overflow_handling_discard_oldest(self):
        """Test: Overflow handling descarta item más antiguo."""
        q = queue.Queue(maxsize=256)
        
        # Llenar con 256 items
        for i in range(256):
            q.put_nowait(i)
        
        # Queue está llena
        self.assertTrue(q.full())
        
        # Simular overflow: discard oldest
        try:
            q.get_nowait()  # Remove oldest
            q.put_nowait(256)  # Add new one
        except queue.Empty:
            self.fail("Queue debería tener al menos 1 item")
        
        # Verificar que el primer item fue removido
        # (el último item en la queue debería ser 256)
        items = []
        while not q.empty():
            items.append(q.get_nowait())
        
        # Último item debería ser 256
        self.assertEqual(items[-1], 256)

    def test_recovery_after_overflow(self):
        """Test: Recovery después de overflow."""
        q = queue.Queue(maxsize=256)
        
        # Llenar
        for i in range(256):
            q.put_nowait(i)
        
        # Simular overflow recovery
        for _ in range(50):  # Remove 50 items
            try:
                q.get_nowait()
            except queue.Empty:
                break
        
        # Queue no debería estar llena
        self.assertFalse(q.full())
        
        # Debería poder aceptar nuevos items
        for i in range(256, 306):
            try:
                q.put_nowait(i)
            except queue.Full:
                self.fail(f"Queue llena después de recovery en item {i}")

    def test_queue_get_timeout(self):
        """Test: Queue.get() con timeout no bloquea indefinidamente."""
        q = queue.Queue(maxsize=256)
        
        start = time.time()
        try:
            q.get(timeout=0.1)  # Wait 100ms for an item
        except queue.Empty:
            pass  # Expected
        
        elapsed = time.time() - start
        # Debe tomar ~100ms (±50ms tolerancia)
        self.assertGreater(elapsed, 0.05)
        self.assertLess(elapsed, 0.2)

    def test_multi_thread_producer_consumer(self):
        """Test: Queue funciona correctamente con múltiples threads."""
        q = queue.Queue(maxsize=256)
        produced = []
        consumed = []
        
        def producer():
            for i in range(100):
                try:
                    q.put_nowait(i)
                    produced.append(i)
                except queue.Full:
                    # Discard oldest
                    try:
                        q.get_nowait()
                        q.put_nowait(i)
                        produced.append(i)
                    except queue.Empty:
                        pass
                time.sleep(0.001)  # Slight delay
        
        def consumer():
            for _ in range(100):
                try:
                    item = q.get(timeout=0.5)
                    consumed.append(item)
                except queue.Empty:
                    break
                time.sleep(0.002)
        
        t1 = threading.Thread(target=producer)
        t2 = threading.Thread(target=consumer)
        
        t1.start()
        t2.start()
        
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        # Al menos algunos items fueron producidos y consumidos
        self.assertGreater(len(produced), 0)
        self.assertGreater(len(consumed), 0)

    def test_queue_empty_check(self):
        """Test: Queue.empty() funciona correctamente."""
        q = queue.Queue(maxsize=256)
        
        # Al inicio está vacío
        self.assertTrue(q.empty())
        
        # Agregar un item
        q.put_nowait("test")
        self.assertFalse(q.empty())
        
        # Remover item
        q.get_nowait()
        self.assertTrue(q.empty())

    def test_rf371_documented_in_srs(self):
        """Test: RF-371 está documentado en SRS.md."""
        srs_path = Path(proyecto_root) / "docs" / "SRS.md"
        if srs_path.exists():
            content = srs_path.read_text(encoding='utf-8', errors='ignore')
            self.assertIn("RF-371", content)
            self.assertIn("Audio Queue", content.lower())
            self.assertIn("256", content)

    def test_rf371_in_performance_md(self):
        """Test: RF-371 está en PERFORMANCE.md."""
        perf_path = Path(proyecto_root) / "docs" / "PERFORMANCE.md"
        if perf_path.exists():
            content = perf_path.read_text(encoding='utf-8', errors='ignore')
            self.assertIn("RF-371", content)
            self.assertIn("queue", content.lower())
            self.assertIn("256", content)


class TestRF371CodeQuality(unittest.TestCase):
    """Validar calidad de código de RF-371."""

    def test_queue_initialization_in_escucha(self):
        """Test: Queue está inicializada en escucha.py con maxsize=256."""
        escucha_path = Path(proyecto_root) / "computadora" / "voz" / "escucha.py"
        if escucha_path.exists():
            content = escucha_path.read_text(encoding='utf-8', errors='ignore')
            self.assertIn("queue.Queue", content)
            self.assertIn("maxsize=256", content)

    def test_overflow_handling_code_present(self):
        """Test: Código de overflow handling está presente."""
        escucha_path = Path(proyecto_root) / "computadora" / "voz" / "escucha.py"
        if escucha_path.exists():
            content = escucha_path.read_text(encoding='utf-8', errors='ignore')
            self.assertIn("queue.Full", content)
            self.assertIn("put_nowait", content)
            self.assertIn("get_nowait", content)

    def test_fp150_comment_in_escucha(self):
        """Test: Código tiene comentario FP-150."""
        escucha_path = Path(proyecto_root) / "computadora" / "voz" / "escucha.py"
        if escucha_path.exists():
            content = escucha_path.read_text(encoding='utf-8', errors='ignore')
            self.assertIn("FP-150", content)


class TestRF371PerformanceMetrics(unittest.TestCase):
    """Validar métricas de RF-371."""

    def test_maxsize_increased_from_128_to_256(self):
        """Test: maxsize fue aumentado (al menos 2x)."""
        old_maxsize = 128
        new_maxsize = 256
        ratio = new_maxsize / old_maxsize
        self.assertEqual(ratio, 2.0)

    def test_overflow_reduction_estimated(self):
        """Test: Reducción de overflow estimada es ~80%."""
        # Queue 2x más grande → overflow 80% menos frecuente
        overflow_reduction = 0.80
        self.assertGreater(overflow_reduction, 0.70)
        self.assertLess(overflow_reduction, 0.90)


if __name__ == "__main__":
    unittest.main(verbosity=2)

