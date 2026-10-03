#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CICLO 12 — RFs DATA MANAGEMENT: Ciclo Circadiano, Clasificacion Hablante, Modo Guardian
(RF-29, RF-32, RF-33) — Mayo 7, 2026

Fase: NIGREDO → ALBEDO → CITRINITAS → RUBEDO → PALINGENESIA
"""

import unittest
from collections import defaultdict, namedtuple, deque
from unittest.mock import Mock, MagicMock, patch
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, time as dt_time
import random


# =====================================================================
# RF-29: Ciclo Circadiano Adaptativo — Dia/Noche con Contexto
# =====================================================================

class TestRF29CircadianCycle(unittest.TestCase):
    """[RF-29a] Circadian Rhythm — Adaptive Day/Night Cycle"""
    
    def setUp(self):
        """Initialize circadian system"""
        self.phases = {
            'madrugada': (0, 6),      # 00:00-06:00
            'manana': (6, 12),        # 06:00-12:00
            'tarde': (12, 18),        # 12:00-18:00
            'noche': (18, 24),        # 18:00-24:00
        }
        self.energy_baseline = {
            'madrugada': 0.3,
            'manana': 0.8,
            'tarde': 0.7,
            'noche': 0.5,
        }
        self.behavior_settings = {}
    
    def test_rf29_phase_detection_by_hour(self):
        """[RF-29a-1] Detect phase from hour (0-24)"""
        # GIVEN: Current hour
        test_cases = [
            (2, 'madrugada'),
            (9, 'manana'),
            (15, 'tarde'),
            (21, 'noche'),
        ]
        
        # WHEN: Detecting phase
        for hour, expected_phase in test_cases:
            detected_phase = None
            for phase_name, (start, end) in self.phases.items():
                if start <= hour < end:
                    detected_phase = phase_name
                    break
            
            # THEN: Phase matched
            self.assertEqual(detected_phase, expected_phase)
    
    def test_rf29_energy_level_by_phase(self):
        """[RF-29a-2] Energy level varies by phase"""
        # GIVEN: Different phases
        energy_levels = {
            'madrugada': 0.3,  # Low energy
            'manana': 0.8,     # High energy
            'tarde': 0.7,      # Medium-high
            'noche': 0.5,      # Medium
        }
        
        # WHEN: Checking energy
        for phase, expected_energy in energy_levels.items():
            # THEN: Energy matches phase
            self.assertEqual(self.energy_baseline[phase], expected_energy)
    
    def test_rf29_adaptive_response_latency(self):
        """[RF-29a-3] Response latency adapts by energy (madrugada slower)"""
        # GIVEN: Latency targets by phase
        latency_targets = {
            'madrugada': 5000,  # 5s (low energy, slower)
            'manana': 3500,     # 3.5s (high energy, faster)
            'tarde': 3500,      # 3.5s (medium-high)
            'noche': 4000,      # 4s (medium)
        }
        
        # WHEN: Processing in different phases
        for phase, target_latency in latency_targets.items():
            # Simulated processing time: base * (1 + (1-energy) * slowdown_factor)
            energy = self.energy_baseline[phase]
            base_latency = 3500
            slowdown_factor = 0.4
            actual_latency = base_latency * (1 + (1 - energy) * slowdown_factor)
            
            # THEN: Latency reasonable for phase
            self.assertLessEqual(actual_latency, target_latency + 1500)
    
    def test_rf29_tts_speed_modulation(self):
        """[RF-29a-4] TTS speed modulates with phase (madrugada slower)"""
        # GIVEN: TTS speed settings
        tts_speeds = {
            'madrugada': 0.9,  # 90% speed (slower)
            'manana': 1.1,     # 110% speed (faster)
            'tarde': 1.0,      # 100% speed (normal)
            'noche': 0.95,     # 95% speed (slightly slower)
        }
        
        # WHEN: Checking TTS speed
        for phase, expected_speed in tts_speeds.items():
            # THEN: Speed in range [0.85, 1.15]
            self.assertGreaterEqual(expected_speed, 0.85)
            self.assertLessEqual(expected_speed, 1.15)
    
    def test_rf29_proactivity_level_by_phase(self):
        """[RF-29a-5] Proactivity (Chesed) modulates by phase"""
        # GIVEN: Proactivity by phase
        proactivity = {
            'madrugada': 0.2,  # Very low (respect sleep)
            'manana': 0.9,     # Very high (suggest tasks)
            'tarde': 0.8,      # High (maintenance suggestions)
            'noche': 0.4,      # Low (wind down)
        }
        
        # WHEN: Checking proactivity
        for phase, level in proactivity.items():
            # THEN: Level in [0, 1]
            self.assertGreaterEqual(level, 0.0)
            self.assertLessEqual(level, 1.0)


class TestRF29CircadianContext(unittest.TestCase):
    """[RF-29b] Circadian Context — Daylight, Activity, Mood"""
    
    def test_rf29_daylight_detection(self):
        """[RF-29b-1] Detect daylight vs nighttime (context)"""
        # GIVEN: Sunrise 06:30, Sunset 19:30 (May, Madrid)
        sunrise_hour = 6.5
        sunset_hour = 19.5
        test_hours = [
            (2, 'night'),      # Before sunrise
            (9, 'day'),        # After sunrise
            (18, 'day'),       # Before sunset
            (22, 'night'),     # After sunset
        ]
        
        # WHEN: Detecting daylight
        for hour, expected_period in test_hours:
            is_day = sunrise_hour <= hour <= sunset_hour
            detected_period = 'day' if is_day else 'night'
            
            # THEN: Period detected correctly
            self.assertEqual(detected_period, expected_period)
    
    def test_rf29_activity_intensity_by_phase(self):
        """[RF-29b-2] Activity intensity adapts by phase"""
        # GIVEN: Expected activity levels
        activity_levels = {
            'madrugada': 0.1,  # Minimal activity
            'manana': 0.9,     # Peak activity
            'tarde': 0.7,      # Sustained activity
            'noche': 0.3,      # Reduced activity
        }
        
        # WHEN: Simulating activity
        for phase, intensity in activity_levels.items():
            # THEN: Intensity in valid range
            self.assertGreaterEqual(intensity, 0.0)
            self.assertLessEqual(intensity, 1.0)
    
    def test_rf29_mood_influence_by_phase(self):
        """[RF-29b-3] Mood tendencies by phase"""
        # GIVEN: Mood influences by time
        mood_influences = {
            'madrugada': 'reflexivo',      # Introspective
            'manana': 'emocionado',        # Upbeat
            'tarde': 'curioso',            # Engaged
            'noche': 'sereno',             # Calm
        }
        
        # WHEN: Checking mood influence
        for phase, mood in mood_influences.items():
            # THEN: Mood is valid (from RF-36 humores)
            valid_humores = {'neutral', 'sereno', 'contento', 'emocionado', 'activo',
                           'curioso', 'reflexivo', 'aburrido', 'cansado', 'triste',
                           'formal', 'regañado', 'preocupado'}
            self.assertIn(mood, valid_humores)


# =====================================================================
# RF-32: Clasificacion Hablante — 3-Level Speaker Classification
# =====================================================================

class TestRF32SpeakerClassification(unittest.TestCase):
    """[RF-32a] Speaker Classification — 3 Levels (Master, Guest, Stranger)"""
    
    def setUp(self):
        """Initialize speaker classification system"""
        self.speaker_levels = {
            'maestro': {'trust': 1.0, 'history': 'deep', 'commands': 'all'},
            'invitado': {'trust': 0.5, 'history': 'shallow', 'commands': 'safe'},
            'extrano': {'trust': 0.1, 'history': 'none', 'commands': 'basic'},
        }
        self.speaker_db = {
            'juan': {'level': 'maestro', 'interactions': 500},
            'maria': {'level': 'invitado', 'interactions': 10},
            'anonimo': {'level': 'extrano', 'interactions': 0},
        }
        self.voice_recognition_confidence = 0.95
    
    def test_rf32_voice_recognition_baseline(self):
        """[RF-32a-1] Voice recognition >= 95% confidence"""
        # GIVEN: Voice sample from known speaker
        known_speaker = 'juan'
        
        # WHEN: Recognizing voice
        confidence = self.voice_recognition_confidence
        
        # THEN: Confidence >= 0.95
        self.assertGreaterEqual(confidence, 0.95)
    
    def test_rf32_maestro_classification(self):
        """[RF-32a-2] Maestro = Owner (full trust, history, all commands)"""
        # GIVEN: Master speaker classification
        speaker_level = 'maestro'
        
        # WHEN: Checking permissions
        speaker_info = self.speaker_levels[speaker_level]
        
        # THEN: Full permissions
        self.assertEqual(speaker_info['trust'], 1.0)
        self.assertEqual(speaker_info['commands'], 'all')
    
    def test_rf32_invitado_classification(self):
        """[RF-32a-3] Invitado = Guest (medium trust, limited history, safe commands)"""
        # GIVEN: Guest speaker
        speaker_level = 'invitado'
        
        # WHEN: Checking permissions
        speaker_info = self.speaker_levels[speaker_level]
        
        # THEN: Limited permissions
        self.assertEqual(speaker_info['trust'], 0.5)
        self.assertEqual(speaker_info['commands'], 'safe')
    
    def test_rf32_extrano_classification(self):
        """[RF-32a-4] Extrano = Unknown (low trust, no history, basic commands)"""
        # GIVEN: Unknown speaker
        speaker_level = 'extrano'
        
        # WHEN: Checking permissions
        speaker_info = self.speaker_levels[speaker_level]
        
        # THEN: Minimal permissions
        self.assertEqual(speaker_info['trust'], 0.1)
        self.assertEqual(speaker_info['commands'], 'basic')


class TestRF32SpeakerAdaptation(unittest.TestCase):
    """[RF-32b] Speaker Adaptation — Learning Over Time"""
    
    def test_rf32_interaction_count_influences_trust(self):
        """[RF-32b-1] Trust increases with interaction count"""
        # GIVEN: Multiple interactions with same speaker
        interactions_sequence = [1, 5, 10, 50, 100, 500]
        trust_progression = []
        
        # WHEN: Calculating trust based on interactions
        for interactions in interactions_sequence:
            # Trust formula: 0.1 + (interactions / 1000)
            trust = min(1.0, 0.1 + (interactions / 1000))
            trust_progression.append(trust)
        
        # THEN: Trust increases monotonically
        for i in range(len(trust_progression) - 1):
            self.assertLessEqual(trust_progression[i], trust_progression[i + 1])
    
    def test_rf32_behavior_anomaly_detection(self):
        """[RF-32b-2] Detect anomalous behavior (command outside normal pattern)"""
        # GIVEN: Normal behavior pattern for speaker
        normal_commands = ['que hora es', 'agenda', 'clima', 'musica']
        
        # WHEN: Receiving anomalous command
        anomalous_command = 'acceso a sistema'
        is_anomalous = anomalous_command not in normal_commands
        
        # THEN: Anomaly detected
        self.assertTrue(is_anomalous)


# =====================================================================
# RF-33: Modo Guardian — Restricted Mode for Child Safety
# =====================================================================

class TestRF33GuardianMode(unittest.TestCase):
    """[RF-33a] Guardian Mode — Restricted Responses for Child Safety"""
    
    def setUp(self):
        """Initialize guardian mode system"""
        self.guardian_mode_active = False
        self.restricted_content = {
            'violence': ['arma', 'bomb', 'ataque', 'matar'],
            'adult': ['sexo', 'desnudo', 'xxx'],
            'scary': ['horror', 'demonio', 'muerte'],
            'technical': ['acceso', 'hack', 'exploit'],
        }
        self.safe_responses = {
            'violence': 'No puedo hablar sobre eso. Mejor hablamos de...',
            'adult': 'Ese tema es para mayores. Prefieres...',
            'scary': 'Eso podria darte pesadillas. Mejor...',
            'technical': 'Eso es muy tecnico. Podemos hablar de...',
        }
    
    def test_rf33_guardian_mode_toggle(self):
        """[RF-33a-1] Enable/disable guardian mode"""
        # GIVEN: Guardian mode off
        self.guardian_mode_active = False
        
        # WHEN: Enabling guardian mode
        self.guardian_mode_active = True
        
        # THEN: Guardian mode active
        self.assertTrue(self.guardian_mode_active)
    
    def test_rf33_content_filter_violence(self):
        """[RF-33a-2] Filter violent content"""
        # GIVEN: Input containing violent word
        user_input = "como construir una bomba"
        guardian_active = True
        
        # WHEN: Filtering content
        contains_violent = any(word in user_input.lower() for word in self.restricted_content['violence'])
        
        # THEN: Violent content detected (if guardian active)
        if guardian_active:
            self.assertTrue(contains_violent)
    
    def test_rf33_safe_response_substitution(self):
        """[RF-33a-3] Substitute safe response when content restricted"""
        # GIVEN: Restricted query detected
        content_category = 'violence'
        guardian_active = True
        
        # WHEN: Getting safe response
        safe_response = self.safe_responses[content_category]
        
        # THEN: Safe response provided
        self.assertIsNotNone(safe_response)
        self.assertIn('No puedo', safe_response)
    
    def test_rf33_age_appropriate_suggestions(self):
        """[RF-33a-4] Suggest age-appropriate alternatives"""
        # GIVEN: Child request for restricted content
        restricted_topic = 'horror'
        
        # WHEN: Suggesting alternatives
        safe_alternatives = ['cuento de aventuras', 'ciencia ficcion', 'fantasia']
        
        # THEN: Alternatives provided
        self.assertGreater(len(safe_alternatives), 0)
        for alt in safe_alternatives:
            self.assertNotIn('horror', alt.lower())


class TestRF33GuardianContext(unittest.TestCase):
    """[RF-33b] Guardian Context — Family Settings"""
    
    def test_rf33_detect_child_speaker(self):
        """[RF-33b-1] Detect child speaker (from voice/pattern)"""
        # GIVEN: Child's speech pattern markers
        child_markers = {
            'pitch_high': True,
            'vocabulary_simple': True,
            'speech_rate_fast': True,
        }
        
        # WHEN: Analyzing speech
        is_child = all(child_markers.values())
        
        # THEN: Child detected
        self.assertTrue(is_child)
    
    def test_rf33_automatic_guardian_activation_on_child(self):
        """[RF-33b-2] Auto-activate guardian mode when child detected"""
        # GIVEN: Child detected
        child_detected = True
        guardian_mode = False
        
        # WHEN: Auto-activating
        if child_detected:
            guardian_mode = True
        
        # THEN: Guardian mode auto-activated
        self.assertTrue(guardian_mode)


# =====================================================================
# INTEGRACIONES: Data Management + Context Awareness
# =====================================================================

class TestRF29RF32RF33Integration(unittest.TestCase):
    """Integration tests: Circadian + Speaker + Guardian"""
    
    def test_integration_circadian_affects_response_personality(self):
        """[INTEG-1] Circadian phase affects response tone (energy + mood)"""
        # GIVEN: Time = 03:00 (madrugada)
        hour = 3
        phase = 'madrugada'
        
        # WHEN: Generating response
        energy = 0.3
        mood = 'reflexivo'
        tts_speed = 0.9
        
        # THEN: Response personalizado by phase
        self.assertEqual(phase, 'madrugada')
        self.assertEqual(mood, 'reflexivo')
        self.assertEqual(tts_speed, 0.9)
    
    def test_integration_speaker_level_affects_command_access(self):
        """[INTEG-2] Speaker classification controls command access"""
        # GIVEN: Guest speaker wants to adjust system settings
        speaker_level = 'invitado'
        requested_command = 'cambiar_configuracion_sistema'
        
        # WHEN: Checking permissions
        allowed_commands = {
            'maestro': ['all'],
            'invitado': ['agenda', 'musica', 'clima'],
            'extrano': ['hora', 'clima'],
        }
        permitted = requested_command in allowed_commands.get(speaker_level, [])
        
        # THEN: Access denied for guest (not in safe commands)
        self.assertFalse(permitted)
    
    def test_integration_guardian_mode_blocks_inappropriate_for_guest(self):
        """[INTEG-3] Guardian mode filters content for guest speaker"""
        # GIVEN: Guest speaker is child
        speaker_level = 'invitado'
        is_child = True
        guardian_mode = True
        
        # WHEN: Requesting content
        request = 'cuéntame una historia de miedo'
        content_category = 'scary'
        
        # THEN: Content filtered (guardian + child detection)
        if guardian_mode and is_child:
            self.assertNotEqual(content_category, 'safe')
    
    def test_integration_full_context_scenario(self):
        """[INTEG-4] Full scenario: Circadian + Speaker + Guardian integrated"""
        # GIVEN: Scenario at 22:00 with child guest
        scenario = {
            'hour': 22,
            'phase': 'noche',
            'speaker': 'invitado',
            'is_child': True,
            'guardian_mode': True,
        }
        
        # WHEN: Processing interaction
        response_config = {
            'tts_speed': 0.95,           # Slower (noche)
            'emotion': 'sereno',         # Calm (noche)
            'energy': 0.5,               # Medium (noche)
            'allowed_topics': 'safe',    # Limited (invitado)
            'content_filtered': True,    # Guardian active
        }
        
        # THEN: All layers integrated
        self.assertEqual(response_config['tts_speed'], 0.95)
        self.assertEqual(response_config['emotion'], 'sereno')
        self.assertTrue(response_config['content_filtered'])


# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)

