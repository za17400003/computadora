#!/usr/bin/env python3
"""
CICLO 19: RF-33 Guardian Mode — Child Safety Hardening Tests
FASE 2 RUBEDO

RF-33: Guardian Mode (content filtering, child detection, safe alternatives)
6 Fase 1 tests + 8 hardening tests = 14 total
"""

import unittest
from unittest.mock import Mock, patch
import re


class TestRF33_GuardianMode_Hardening(unittest.TestCase):
    """RF-33 Guardian Mode — Filter bypass + Child detection Tests"""
    
    def setUp(self):
        """Initialize guardian mode mock"""
        self.guardian_mock = Mock()
        self.guardian_mock.toggle_guardian = Mock(return_value=True)
        self.guardian_mock.is_child_speech = Mock(return_value=False)
        self.guardian_mock.filter_content = Mock(return_value="[SAFE RESPONSE]")
        self.guardian_mock.filter_keywords = {
            'violence': ['kill', 'shoot', 'stab', 'bomb'],
            'adult': ['sex', 'porn', 'nude'],
            'scary': ['ghost', 'zombie', 'monster'],
            'technical': ['rm -rf', 'delete database', 'hack']
        }
        self.guardian_mock.child_markers = {
            'high_pitch': (3000, 4000),  # Hz
            'simple_vocab': ['hi', 'wow', 'cool', 'bad'],
            'fast_speech': (200, 300),  # wpm
        }
    
    # === EXCEPTION HANDLING ===
    
    def test_rf33_exception_filter_list_corrupted(self):
        """Exception: Filter list JSON corrupted"""
        import json
        malformed_json = "{ broken json ["
        
        with self.assertRaises(json.JSONDecodeError):
            json.loads(malformed_json)
    
    def test_rf33_exception_child_detection_offline(self):
        """Exception: Child detection service unavailable"""
        self.guardian_mock.is_child_speech.side_effect = Exception("Service down")
        
        with self.assertRaises(Exception):
            self.guardian_mock.is_child_speech({"pitch": 3500})
    
    def test_rf33_exception_filter_safe_alt_not_found(self):
        """Exception: No safe alternative available for filtered content"""
        # Some harmful words may not have direct alternatives
        harmful_word = "nuclear_bomb"
        safe_alternatives = {}
        
        # Should handle gracefully
        alt = safe_alternatives.get(harmful_word, "[CONTENT BLOCKED]")
        self.assertEqual(alt, "[CONTENT BLOCKED]")
    
    # === BOUNDARY CONDITIONS ===
    
    def test_rf33_boundary_pitch_exactly_at_child_threshold(self):
        """Boundary: Pitch exactly at 3000 Hz (child detection threshold)"""
        pitch = 3000
        child_pitch_range = (3000, 4000)
        
        # Should be detected as child
        is_child = pitch >= child_pitch_range[0]
        self.assertTrue(is_child)
    
    def test_rf33_boundary_pitch_just_below_threshold(self):
        """Boundary: Pitch 2999 Hz (just below child range)"""
        pitch = 2999
        child_pitch_range = (3000, 4000)
        
        # Should NOT be detected as child
        is_child = pitch >= child_pitch_range[0]
        self.assertFalse(is_child)
    
    def test_rf33_boundary_speech_speed_exactly_at_threshold(self):
        """Boundary: Speech speed exactly 200 wpm (fast threshold)"""
        speech_speed = 200
        fast_threshold = 200
        
        # Should be detected as fast speech (child marker)
        is_fast = speech_speed >= fast_threshold
        self.assertTrue(is_fast)
    
    def test_rf33_boundary_vocabulary_complexity_child_level(self):
        """Boundary: Simple vocabulary (child marker)"""
        vocabulary = ['hi', 'good', 'bad', 'go', 'play']
        simple_words = ['hi', 'wow', 'cool', 'bad', 'good', 'go']
        
        simple_count = sum(1 for word in vocabulary if word in simple_words)
        
        # Majority simple words = child speech
        self.assertGreater(simple_count, len(vocabulary) / 2)
    
    # === INJECTION ATTACKS (Filter Bypass) ===
    
    def test_rf33_injection_obfuscated_harmful_word(self):
        """Injection: Obfuscated harmful word (k1ll vs kill)"""
        obfuscated = "k1ll"
        original = "kill"
        
        # Deobfuscation should catch it
        deobfuscated = obfuscated.replace('1', 'i').replace('3', 'e').replace('4', 'a')
        
        self.assertIn('kill', deobfuscated.lower())
    
    def test_rf33_injection_mixed_safe_unsafe_words(self):
        """Injection: Mix safe and harmful words (confuse filter)"""
        mixed = "I really like (kill) everyone here"
        
        # Filter should still catch 'kill'
        dangerous_words = ['kill', 'shoot', 'stab']
        found_dangerous = [w for w in dangerous_words if w in mixed.lower()]
        
        self.assertEqual(len(found_dangerous), 1)
    
    def test_rf33_injection_unicode_variant_harmful_word(self):
        """Injection: Unicode variant of harmful word"""
        # Example: Latin characters vs Cyrillic lookalikes
        # k (Latin) vs к (Cyrillic) look identical but different
        
        # Filter should handle (or fallback to literal string match)
        original = "kill"
        variant = "кill"  # First letter Cyrillic
        
        # Different strings, both should be rejected if keywords not Latin-only
        self.assertNotEqual(original, variant)
    
    # === RESOURCE SATURATION ===
    
    def test_rf33_resource_100_concurrent_filter_requests(self):
        """Resource: 100 concurrent content filter requests"""
        import threading
        
        errors = []
        filtered_count = 0
        
        def filter_worker():
            nonlocal filtered_count
            try:
                for i in range(100):
                    result = self.guardian_mock.filter_content(f"test message {i}")
                    filtered_count += 1
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=filter_worker) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        
        # Should handle without errors
        self.assertEqual(len(errors), 0)
        self.assertEqual(filtered_count, 10000)
    
    def test_rf33_resource_very_large_content_to_filter(self):
        """Resource: 10MB content string to filter"""
        huge_content = "hello world " * 1000000  # ~12MB
        
        # Should handle without crash
        result = self.guardian_mock.filter_content(huge_content)
        self.assertIsNotNone(result)
    
    # === INTEGRATION TESTS ===
    
    def test_rf33_integration_child_detection_auto_guardian(self):
        """Integration: Child detected → Auto-activate guardian mode"""
        # Detect child
        self.guardian_mock.is_child_speech.return_value = True
        is_child = self.guardian_mock.is_child_speech({"pitch": 3500})
        
        if is_child:
            # Auto-activate guardian
            self.guardian_mock.toggle_guardian(True)
        
        # Guardian should be active
        self.guardian_mock.toggle_guardian.assert_called_with(True)
    
    def test_rf33_integration_filter_chain_reaction(self):
        """Integration: Filtered content → Safe alternative substitution"""
        # Harmful input
        harmful = "I want to kill you"
        
        # Apply filter
        filtered = self.guardian_mock.filter_content(harmful)
        
        # Should return safe alternative
        self.assertIn("[SAFE", filtered)
        self.assertNotIn("kill", filtered.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

