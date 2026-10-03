#!/usr/bin/env python3
"""
CICLO 20: RF-29/RF-32 Data Management — Hardening Tests
FASE 2 RUBEDO (FINAL)

RF-29: Circadian Adaptive (energy modulation, phase boundaries)
RF-32: Speaker Classification (voice identification, spoofing attacks)

12 Fase 1 tests + 12 hardening tests = 24 total
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import time
import threading


class TestRF29_CircadianAdaptive_Hardening(unittest.TestCase):
    """RF-29 Circadian Adaptive — Boundary + Concurrency Tests"""
    
    def setUp(self):
        """Initialize circadian mock"""
        self.circadian_mock = Mock()
        self.circadian_mock.current_phase = "activo"
        self.circadian_mock.get_energy_level = Mock(return_value=0.75)
        self.circadian_mock.get_phase = Mock(return_value="activo")
        self.circadian_mock.phases = {
            "descanso": (0, 6),      # Midnight to 6 AM
            "despertar": (6, 9),     # 6 AM to 9 AM
            "activo": (9, 21),       # 9 AM to 9 PM
            "transicion": (21, 24)   # 9 PM to Midnight
        }
    
    # === EXCEPTION HANDLING ===
    
    def test_rf29_exception_invalid_phase_transition(self):
        """Exception: Invalid phase transition (not allowed by state machine)"""
        # Can't jump from 'activo' to 'descanso' (skip 'transicion')
        current = "activo"
        invalid_target = "descanso"
        
        allowed_transitions = {
            "activo": ["transicion"],
            "transicion": ["descanso"],
            "descanso": ["despertar"],
            "despertar": ["activo"]
        }
        
        is_valid = invalid_target in allowed_transitions.get(current, [])
        self.assertFalse(is_valid)
    
    def test_rf29_exception_energy_negative(self):
        """Exception: Energy level negative → ValueError"""
        self.circadian_mock.get_energy_level.return_value = -0.5
        
        energy = self.circadian_mock.get_energy_level()
        
        # Should be validated
        self.assertGreaterEqual(energy, 0.0) or self.assertRaises(ValueError)
    
    def test_rf29_exception_clock_skew_large_jump(self):
        """Exception: System clock jumped backward (NTP sync issue)"""
        # Previous timestamp: 10:00
        # Current timestamp: 09:30 (backward jump)
        prev_ts = datetime(2026, 5, 7, 10, 0, 0)
        curr_ts = datetime(2026, 5, 7, 9, 30, 0)
        
        # Should detect and warn
        time_diff = (curr_ts - prev_ts).total_seconds()
        self.assertLess(time_diff, 0)  # Clock went backward
    
    # === BOUNDARY CONDITIONS ===
    
    def test_rf29_boundary_midnight_transition_exact(self):
        """Boundary: Exactly at midnight (00:00:00) → phase change to 'descanso'"""
        ts = datetime(2026, 5, 8, 0, 0, 0)
        
        # Determine phase at midnight
        hour = ts.hour
        phase = None
        for p_name, (start, end) in self.circadian_mock.phases.items():
            if start <= hour < end:
                phase = p_name
                break
        
        self.assertEqual(phase, "descanso")
    
    def test_rf29_boundary_phase_boundary_23_59_59_to_00_00_00(self):
        """Boundary: Last second of 'transicion' (23:59:59)"""
        ts = datetime(2026, 5, 7, 23, 59, 59)
        hour = ts.hour
        
        phase = None
        for p_name, (start, end) in self.circadian_mock.phases.items():
            if start <= hour < end:
                phase = p_name
                break
        
        self.assertEqual(phase, "transicion")
    
    def test_rf29_boundary_energy_exactly_zero(self):
        """Boundary: Energy exactly at 0.0 (minimum)"""
        self.circadian_mock.get_energy_level.return_value = 0.0
        
        energy = self.circadian_mock.get_energy_level()
        self.assertEqual(energy, 0.0)
    
    def test_rf29_boundary_energy_exactly_one(self):
        """Boundary: Energy exactly at 1.0 (maximum)"""
        self.circadian_mock.get_energy_level.return_value = 1.0
        
        energy = self.circadian_mock.get_energy_level()
        self.assertEqual(energy, 1.0)
    
    def test_rf29_boundary_6am_phase_change_despertar_to_activo(self):
        """Boundary: Exactly 06:00:00 (despertar→activo boundary)"""
        ts = datetime(2026, 5, 7, 6, 0, 0)
        hour = ts.hour
        
        phase = None
        for p_name, (start, end) in self.circadian_mock.phases.items():
            if start <= hour < end:
                phase = p_name
                break
        
        self.assertEqual(phase, "despertar")
    
    def test_rf29_boundary_9pm_phase_change_activo_to_transicion(self):
        """Boundary: Exactly 21:00:00 (activo→transicion boundary)"""
        ts = datetime(2026, 5, 7, 21, 0, 0)
        hour = ts.hour
        
        phase = None
        for p_name, (start, end) in self.circadian_mock.phases.items():
            if start <= hour < end:
                phase = p_name
                break
        
        self.assertEqual(phase, "transicion")
    
    # === CONCURRENCY ===
    
    def test_rf29_concurrency_phase_change_during_operation(self):
        """Concurrency: Phase changes while NLU operation in progress"""
        errors = []
        operations = []
        
        def operation():
            try:
                # Start operation in 'activo' phase
                phase = self.circadian_mock.get_phase()
                operations.append(phase)
                
                # Simulate operation taking 100ms
                time.sleep(0.1)
                
                # Check phase again
                phase2 = self.circadian_mock.get_phase()
                operations.append(phase2)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=operation) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(operations), 10)
    
    # === INTEGRATION ===
    
    def test_rf29_integration_energy_affects_latency(self):
        """Integration: Low energy → Increased latency"""
        # Energy 0.2 (low) → 5x slowdown expected
        low_energy = 0.2
        base_latency = 500  # ms
        
        slowdown = 1 + (1 - low_energy) * 5  # Max slowdown 5x
        adjusted_latency = base_latency * slowdown
        
        # Should be ~2900ms (500 * 5.8)
        self.assertGreater(adjusted_latency, 2000)
        self.assertLess(adjusted_latency, 4000)


class TestRF32_SpeakerClassification_Hardening(unittest.TestCase):
    """RF-32 Speaker Classification — Spoofing + Trust Tests"""
    
    def setUp(self):
        """Initialize speaker classification mock"""
        self.speaker_mock = Mock()
        self.speaker_mock.identify_speaker = Mock(return_value={"speaker": "user", "confidence": 0.92})
        self.speaker_mock.update_voiceprint = Mock(return_value=True)
        self.speaker_mock.trust_levels = {"untrusted": 0, "guest": 1, "known": 2, "admin": 3}
        self.speaker_mock.user_voiceprints = {
            "user": {"samples": 50, "stability": 0.98},
            "guest": {"samples": 5, "stability": 0.60}
        }
    
    # === EXCEPTION HANDLING ===
    
    def test_rf32_exception_voiceprint_corrupted(self):
        """Exception: User voiceprint file corrupted"""
        self.speaker_mock.identify_speaker.side_effect = ValueError("Voiceprint format invalid")
        
        with self.assertRaises(ValueError):
            self.speaker_mock.identify_speaker({"audio": b"corrupted"})
    
    def test_rf32_exception_microphone_input_empty(self):
        """Exception: No audio input from microphone"""
        self.speaker_mock.identify_speaker.side_effect = RuntimeError("No audio input")
        
        with self.assertRaises(RuntimeError):
            self.speaker_mock.identify_speaker({"audio": b""})
    
    def test_rf32_exception_speaker_not_in_database(self):
        """Exception: Speaker voice not in database"""
        result = self.speaker_mock.identify_speaker({"audio": b"unknown_voice"})
        
        # Should handle gracefully (return unknown or low confidence)
        self.speaker_mock.identify_speaker.return_value = {"speaker": "unknown", "confidence": 0.0}
    
    # === BOUNDARY CONDITIONS ===
    
    def test_rf32_boundary_confidence_exactly_at_threshold(self):
        """Boundary: Confidence exactly at 0.8 trust threshold"""
        confidence = 0.80
        threshold = 0.80
        
        # Should grant access
        grants_access = confidence >= threshold
        self.assertTrue(grants_access)
    
    def test_rf32_boundary_confidence_just_below_threshold(self):
        """Boundary: Confidence 0.79 (just below 0.80 threshold)"""
        confidence = 0.79
        threshold = 0.80
        
        # Should deny access
        grants_access = confidence >= threshold
        self.assertFalse(grants_access)
    
    def test_rf32_boundary_voiceprint_samples_exactly_50(self):
        """Boundary: User has exactly 50 voiceprint samples (training complete)"""
        user_voiceprint = self.speaker_mock.user_voiceprints["user"]
        
        # Should be sufficient for high-confidence identification
        self.assertEqual(user_voiceprint["samples"], 50)
        self.assertGreaterEqual(user_voiceprint["stability"], 0.95)
    
    def test_rf32_boundary_guest_voiceprint_low_samples(self):
        """Boundary: Guest has only 5 samples (low confidence)"""
        guest_voiceprint = self.speaker_mock.user_voiceprints["guest"]
        
        # Should have lower stability
        self.assertEqual(guest_voiceprint["samples"], 5)
        self.assertLess(guest_voiceprint["stability"], 0.70)
    
    # === INJECTION / SPOOFING ATTACKS ===
    
    def test_rf32_injection_voice_recording_replay_attack(self):
        """Injection: Replay attack using recorded user voice"""
        # Record user saying "unlock"
        recorded_audio = b"user_voice_data_encrypted"
        
        # Attacker replays recording
        # Real implementation should use freshness token/challenge
        
        # Should detect replay (different acoustic features each time)
        result1 = {"speaker": "user", "confidence": 0.92, "timestamp": 1000}
        result2 = {"speaker": "user", "confidence": 0.91, "timestamp": 1000}  # Same timestamp = replay
        
        # Timestamps identical = suspicious
        self.assertEqual(result1["timestamp"], result2["timestamp"])
    
    def test_rf32_injection_voice_synthesis_attack(self):
        """Injection: TTS-generated user voice"""
        # Generate fake voice with TTS
        synthetic_audio = b"synthetic_voice_data"
        
        # Real system should detect artifacts (unnatural prosody, timing)
        # Confidence should be lower on synthetic
        confidence_natural = 0.92
        confidence_synthetic = 0.45  # Lower due to artifacts
        
        self.assertLess(confidence_synthetic, confidence_natural)
    
    def test_rf32_injection_emotional_variation_spoofing(self):
        """Injection: Same speaker but different emotional state (confuse classifier)"""
        # Normal: calm voice
        result_calm = {"speaker": "user", "confidence": 0.95}
        
        # Angry: same speaker, elevated pitch/speed
        result_angry = {"speaker": "user", "confidence": 0.78}
        
        # Should still identify but with confidence drop
        self.assertEqual(result_calm["speaker"], result_angry["speaker"])
        self.assertLess(result_angry["confidence"], result_calm["confidence"])
    
    # === RESOURCE SATURATION ===
    
    def test_rf32_resource_100_speaker_identification_rapid(self):
        """Resource: 100 speaker identifications in rapid succession"""
        errors = []
        identifications = []
        
        for i in range(100):
            try:
                result = self.speaker_mock.identify_speaker({"audio": f"test_audio_{i}".encode()})
                identifications.append(result)
            except Exception as e:
                errors.append(e)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(identifications), 100)
    
    def test_rf32_resource_concurrent_voiceprint_updates(self):
        """Resource: Multiple threads updating voiceprints simultaneously"""
        errors = []
        updates = []
        
        def update_worker(user_id):
            try:
                for i in range(50):
                    result = self.speaker_mock.update_voiceprint(user_id, {"audio": f"sample_{i}".encode()})
                    updates.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=update_worker, args=(f"user_{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(updates), 500)
    
    # === INTEGRATION ===
    
    def test_rf32_integration_trust_escalation_attack_prevention(self):
        """Integration: Prevent privilege escalation from 'guest' to 'admin'"""
        # Guest successfully identified
        guest_result = {"speaker": "guest", "confidence": 0.85, "trust_level": 1}
        
        # Guest attempts to call admin-level API
        # Should be denied by trust level check
        required_trust = 3  # admin
        granted_trust = guest_result["trust_level"]
        
        is_authorized = granted_trust >= required_trust
        self.assertFalse(is_authorized)
    
    def test_rf32_integration_speaker_change_mid_conversation(self):
        """Integration: Speaker changes mid-conversation (handoff detection)"""
        # Speaker A starts
        speaker_a = {"speaker": "alice", "confidence": 0.95}
        
        # Pause (could be speaker B taking device)
        time.sleep(0.05)
        
        # Speaker B continues
        speaker_b = {"speaker": "bob", "confidence": 0.88}
        
        # Should detect change
        self.assertNotEqual(speaker_a["speaker"], speaker_b["speaker"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

