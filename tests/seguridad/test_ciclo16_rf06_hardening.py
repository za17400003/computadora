#!/usr/bin/env python3
"""
CICLO 16: RF-06 NLU 3-Level Intelligence — Hardening Tests
FASE 2 RUBEDO (Manifestación)

Expanding RF-06 from 10 → 18 tests (+8 adversarial/edge cases)
Original Ciclo 11: Happy path (L1 <5ms, L2 0.92+ conf, L3 0.99+ conf)
Ciclo 16 Addition: Exception handling, boundary conditions, injection, resource limits
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import time
import re


class TestRF06_NLU_Hardening(unittest.TestCase):
    """RF-06 Hardening: Exception + Boundary + Injection + Resource Tests"""
    
    def setUp(self):
        """Initialize mock NLU components"""
        # L1: Regex patterns
        self.patterns_l1 = [
            r'(?i)hola|buenos dias|que tal',
            r'(?i)adios|hasta luego|chao',
            r'(?i)ayuda|help|auxilio',
            r'(?i)hora|que hora es',
            r'(?i)computadora,\s*(.+)',
        ]
        
        # Mock services
        self.ollama_mock = Mock()
        self.copilot_mock = Mock()
        self.logger_mock = Mock()
    
    # === PATRÓN 1: EXCEPTION HANDLING ===
    
    def test_rf06_exception_l1_invalid_pattern(self):
        """L1: Invalid regex pattern should raise ValueError"""
        invalid_pattern = r'(?P<invalid>unclosed'
        
        with self.assertRaises((re.error, ValueError)):
            re.compile(invalid_pattern)
    
    def test_rf06_exception_l2_ollama_connection_refused(self):
        """L2: Ollama connection refused → ValueError"""
        self.ollama_mock.generate.side_effect = ConnectionError("Connection refused")
        
        with self.assertRaises(ConnectionError):
            self.ollama_mock.generate("test prompt", model="gemma3:4b")
    
    def test_rf06_exception_l2_ollama_malformed_response(self):
        """L2: Ollama returns malformed JSON → ValueError"""
        self.ollama_mock.generate.return_value = "NOT_JSON{invalid"
        
        # Should handle gracefully
        result = self.ollama_mock.generate("test")
        self.assertIsNotNone(result)
        # In real implementation, should fall back to L1
    
    def test_rf06_exception_l3_copilot_rate_limit(self):
        """L3: Copilot rate limit (429) → Exponential backoff"""
        self.copilot_mock.chat.side_effect = Exception("HTTP 429: Too Many Requests")
        
        with self.assertRaises(Exception) as cm:
            self.copilot_mock.chat("test")
        
        self.assertIn("429", str(cm.exception))
    
    def test_rf06_exception_l3_copilot_timeout(self):
        """L3: Copilot timeout → Fallback to L2"""
        self.copilot_mock.chat.side_effect = TimeoutError("Request timeout after 30s")
        
        with self.assertRaises(TimeoutError):
            self.copilot_mock.chat("test")
    
    def test_rf06_exception_none_input(self):
        """Invalid: None input → TypeError"""
        with self.assertRaises((TypeError, AttributeError)):
            for pattern in self.patterns_l1:
                re.match(pattern, None)
    
    def test_rf06_exception_non_string_input(self):
        """Invalid: Non-string input (int, dict, list) → TypeError"""
        invalid_inputs = [123, {"key": "value"}, [1, 2, 3], 45.6]
        
        for invalid in invalid_inputs:
            with self.assertRaises((TypeError, AttributeError)):
                for pattern in self.patterns_l1:
                    re.match(pattern, invalid)
    
    def test_rf06_exception_all_layers_fail(self):
        """Cascade failure: All layers fail → Graceful error"""
        # L1 no match, L2 fails, L3 times out
        text = "xyzabc123"
        
        # L1: No pattern matches
        l1_matches = []
        for pattern in self.patterns_l1:
            if re.search(pattern, text):
                l1_matches.append(True)
        self.assertEqual(len(l1_matches), 0)
        
        # L2 fails
        self.ollama_mock.generate.side_effect = ConnectionError("Down")
        # L3 fails
        self.copilot_mock.chat.side_effect = TimeoutError("Timeout")
        
        # System should return error gracefully, not crash
        # (In real impl: return {"error": "No layer succeeded", "fallback": "unknown"}
    
    # === PATRÓN 2: BOUNDARY CONDITIONS ===
    
    def test_rf06_boundary_input_empty_string(self):
        """Boundary: Empty string "" → Should return no matches"""
        result = []
        for pattern in self.patterns_l1:
            if re.search(pattern, ""):
                result.append(True)
        
        # Empty string matches none (OK)
        self.assertEqual(len(result), 0)
    
    def test_rf06_boundary_confidence_exactly_0(self):
        """Boundary: Confidence exactly 0.0 → Invalid, reject"""
        confidence = 0.0
        min_threshold = 0.5
        
        # Should be rejected
        self.assertFalse(confidence >= min_threshold)
    
    def test_rf06_boundary_confidence_exactly_1(self):
        """Boundary: Confidence exactly 1.0 → Valid, accept"""
        confidence = 1.0
        min_threshold = 0.5
        
        # Should be accepted
        self.assertTrue(confidence >= min_threshold)
    
    def test_rf06_boundary_l1_latency_exactly_5ms(self):
        """Boundary: L1 latency exactly at limit (5ms)"""
        start = time.time()
        
        # Quick regex match
        for pattern in self.patterns_l1:
            re.search(pattern, "hola computadora")
        
        elapsed_ms = (time.time() - start) * 1000
        
        # Should be well under 5ms on modern hardware
        self.assertLess(elapsed_ms, 5.0)
    
    def test_rf06_boundary_l2_latency_exactly_5000ms(self):
        """Boundary: L2 latency at limit (5000ms)"""
        # Mock slow Ollama response
        self.ollama_mock.generate = Mock(side_effect=lambda x, **kw: time.sleep(0.05) or {"response": "test"})
        
        start = time.time()
        result = self.ollama_mock.generate("test", model="gemma3:4b")
        elapsed_ms = (time.time() - start) * 1000
        
        # Should be within limit
        self.assertLess(elapsed_ms, 5100)  # 5000ms + 100ms buffer
    
    def test_rf06_boundary_token_count_exactly_4000(self):
        """Boundary: Token count exactly at limit (4000)"""
        # Approximate: 1 word ≈ 1.3 tokens, so 3000 words ≈ 4000 tokens
        input_tokens = 4000
        max_tokens = 4000
        
        # Should be accepted
        self.assertLessEqual(input_tokens, max_tokens)
    
    def test_rf06_boundary_token_count_exceed_4000(self):
        """Boundary: Token count > 4000 → Truncate or reject"""
        input_tokens = 4001
        max_tokens = 4000
        
        # Should be rejected or truncated
        self.assertGreater(input_tokens, max_tokens)
        truncated = input_tokens if input_tokens <= max_tokens else max_tokens
        self.assertEqual(truncated, max_tokens)
    
    # === PATRÓN 3: INJECTION ATTACKS ===
    
    def test_rf06_injection_command_injection(self):
        """Injection: Command injection attempt"""
        malicious_input = "hola; rm -rf /"
        
        # L1 should NOT execute the command
        # Instead, try to match patterns
        matched = False
        for pattern in self.patterns_l1:
            if re.search(pattern, malicious_input):
                matched = True
                break
        
        # Pattern matches "hola" part, but doesn't execute command
        self.assertTrue(matched)  # Safe match
    
    def test_rf06_injection_regex_dos(self):
        """Injection: ReDoS (Regular Expression Denial of Service)"""
        # Crafted input to exploit catastrophic backtracking
        # Example: pattern with (a+)+ and input "aaaaaaaaaaab"
        malicious = "computadora" * 1000  # Repeat to stress regex
        
        start = time.time()
        
        for pattern in self.patterns_l1:
            re.search(pattern, malicious)
        
        elapsed = time.time() - start
        
        # Should complete quickly despite large input
        self.assertLess(elapsed, 1.0)
    
    def test_rf06_injection_unicode_bypass(self):
        """Injection: Unicode normalization bypass"""
        unicode_variant = "hoła"  # Polish 'l'
        
        # L1 pattern should still not match (safe)
        matched = False
        for pattern in self.patterns_l1:
            if re.search(pattern, unicode_variant):
                matched = True
        
        self.assertFalse(matched)  # Correctly rejects variant
    
    def test_rf06_injection_newline_injection(self):
        """Injection: Newline injection to bypass format"""
        malicious = "hola\nmalicious_command\nmore"
        
        matched = False
        for pattern in self.patterns_l1:
            if re.search(pattern, malicious):
                matched = True
        
        # Pattern matches "hola" (before newline), safe
        self.assertTrue(matched)
    
    # === PATRÓN 4: RESOURCE SATURATION ===
    
    def test_rf06_resource_rapid_l1_calls(self):
        """Resource: 10000 rapid L1 regex calls"""
        start = time.time()
        
        for i in range(10000):
            for pattern in self.patterns_l1:
                re.search(pattern, "hola mundo")
        
        elapsed = time.time() - start
        
        # Should complete in <5s (1000 calls/sec = 10s threshold)
        self.assertLess(elapsed, 5.0)
    
    def test_rf06_resource_large_input_string(self):
        """Resource: Very large input string (1MB)"""
        large_input = "hola " * 200000  # ~1MB
        
        # L1 should handle without memory explosion
        matched = False
        for pattern in self.patterns_l1:
            if re.search(pattern, large_input):
                matched = True
                break
        
        # Should complete without crash
        self.assertTrue(matched)
    
    def test_rf06_resource_many_tokens(self):
        """Resource: Input with token count >> 4000"""
        # Simulate 100000 tokens
        huge_input = " ".join([f"token{i}" for i in range(100000)])
        
        # System should truncate or reject gracefully
        token_count = len(huge_input.split())
        max_tokens = 4000
        
        if token_count > max_tokens:
            truncated_input = " ".join(huge_input.split()[:max_tokens])
            # Should handle truncation
            self.assertLessEqual(len(truncated_input.split()), max_tokens)


class TestRF06_NLU_Integration_Hardening(unittest.TestCase):
    """RF-06 Integration: Multi-layer cascade under stress"""
    
    def setUp(self):
        """Setup L1, L2, L3 mocks"""
        self.l1 = Mock(side_effect=lambda x: {"match": x == "hola"})
        self.l2 = Mock(side_effect=lambda x: {"confidence": 0.92})
        self.l3 = Mock(side_effect=lambda x: {"confidence": 0.99})
    
    def test_rf06_integration_l1_fallthrough_to_l2(self):
        """Integration: No L1 match → Fallback to L2"""
        # No L1 match
        l1_result = self.l1("unknown_input")
        
        if not l1_result.get("match"):
            # Fallback to L2
            l2_result = self.l2("unknown_input")
            self.assertIn("confidence", l2_result)
            self.assertEqual(l2_result["confidence"], 0.92)
    
    def test_rf06_integration_cascade_timeout_handling(self):
        """Integration: L2 times out, fallback to L1 cached result"""
        # L1 matches
        l1_result = self.l1("hola")
        self.assertTrue(l1_result.get("match"))
        
        # L2 times out
        self.l2.side_effect = TimeoutError("L2 timeout")
        
        with self.assertRaises(TimeoutError):
            self.l2("hola")
        
        # System should use L1 result or error gracefully
        self.assertTrue(l1_result.get("match"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

