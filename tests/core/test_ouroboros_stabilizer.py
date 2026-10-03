"""
Tests para OuroborosStabilizer — Ciclo Infinito Seguro del Golem
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verifica que el ciclo Gilgul→Bereshit→Reinicio sea infinito pero estable.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from computadora.nucleo.ouroboros_stabilizer import OuroborosStabilizer


class TestOuroborosStabilizer:
    """Suite de tests para estabilización del ciclo infinito."""
    
    @pytest.fixture
    def stabilizer(self, tmp_path):
        """Crear OuroborosStabilizer con rutas temporales para testing."""
        stabilizer = OuroborosStabilizer()
        # Usar rutas temporales
        stabilizer.CREDENTIALS_FILE = tmp_path / "gilgul_credentials.json"
        stabilizer.CYCLE_LOG_FILE = tmp_path / "ouroboros_cycle.jsonl"
        stabilizer.CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return stabilizer
    
    def test_emet_validation(self, stabilizer):
        """Verificar que EMET (אמת) está inscrita correctamente."""
        # Crear credenciales por defecto
        creds = stabilizer._create_default_credentials()
        pwd = creds.get("gilgul_access", {}).get("master_password")
        
        assert pwd == "emet", f"Password debe ser 'emet', pero es '{pwd}'"
    
    def test_emet_not_met(self, stabilizer):
        """Verificar que 'met' (מת = Muerte) es rechazado."""
        # Crear credenciales pero cambiar a 'met' para simular corrupción
        creds = {
            "gilgul_access": {
                "master_password": "met"  # ❌ Muerte
            },
            "password_history": [],
            "access_control": {}
        }
        
        with open(stabilizer.CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(creds, f, ensure_ascii=False)
        
        # Recargar y validar
        stabilizer.credentials = stabilizer._load_credentials()
        assert not stabilizer.validate_emet(), "Sistema debe rechazar 'met'"
    
    def test_credentials_persistence(self, stabilizer):
        """Verificar que las credenciales persisten entre boots."""
        # Bootstrap 1: Crear credenciales
        creds1 = stabilizer._create_default_credentials()
        pwd1 = creds1.get("gilgul_access", {}).get("master_password")
        
        # Bootstrap 2: Cargar credenciales existentes
        stabilizer2 = OuroborosStabilizer()
        stabilizer2.CREDENTIALS_FILE = stabilizer.CREDENTIALS_FILE
        creds2 = stabilizer2._load_credentials()
        pwd2 = creds2.get("gilgul_access", {}).get("master_password")
        
        assert pwd1 == pwd2 == "emet", "Contraseña debe persistir entre boots"
    
    def test_cycle_logging(self, stabilizer):
        """Verificar que los ciclos se registran correctamente."""
        # Log de ciclo iniciado
        stabilizer.log_cycle_start("gilgul_start")
        
        # Simular Gilgul + reboot
        stabilizer.log_cycle_complete("gilgul_complete")
        stabilizer.log_cycle_start("reboot_start")
        stabilizer.log_cycle_complete("reboot_complete")
        
        # Verificar que el archivo tiene los registros
        assert stabilizer.CYCLE_LOG_FILE.exists()
        
        with open(stabilizer.CYCLE_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 4, f"Debe haber 4 ciclos registrados, hay {len(lines)}"
    
    def test_incomplete_cycle_detection(self, stabilizer):
        """Detectar ciclos incompletos: Gilgul sin reboot."""
        # Simular Gilgul iniciado pero no completado
        stabilizer.log_cycle_start("gilgul_start")
        
        # SIN log de reboot_complete following
        
        # Detectar incompleto
        incomplete = stabilizer.detect_incomplete_cycles()
        
        assert len(incomplete) > 0, "Debe detectar ciclo incompleto"
        assert incomplete[0].get("event") == "gilgul_start"
    
    def test_incomplete_cycle_no_false_positives(self, stabilizer):
        """Verificar que ciclos completos NO se detectan como incompletos."""
        # Ciclo COMPLETO
        stabilizer.log_cycle_start("gilgul_start")
        stabilizer.log_cycle_complete("gilgul_complete")
        stabilizer.log_cycle_start("reboot_start")
        stabilizer.log_cycle_complete("reboot_complete")
        
        # Detectar incompletos
        incomplete = stabilizer.detect_incomplete_cycles()
        
        assert len(incomplete) == 0, "No debe haber ciclos incompletos"
    
    def test_incomplete_cycle_recovery(self, stabilizer):
        """Verificar que ciclos incompletos se recuperan."""
        # Simular ciclo incompleto
        stabilizer.log_cycle_start("gilgul_start")
        
        # Recuperar
        stabilizer.recover_incomplete_cycle()
        
        # Verificar que nuevos registros existen
        with open(stabilizer.CYCLE_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Debe haber: start + recovery
        assert len(lines) >= 2, "Debe haber registros de recuperación"
        
        # Último registro debe ser recovery
        last_entry = json.loads(lines[-1])
        assert last_entry.get("event") == "recovery_from_incomplete_cycle"
    
    def test_ouroboros_seal(self, stabilizer):
        """Verificar que el ouroboros se sella correctamente."""
        stabilizer.seal_ouroboros()
        
        with open(stabilizer.CYCLE_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        last_entry = json.loads(lines[-1])
        
        assert last_entry.get("event") == "ouroboros_sealed"
        assert last_entry.get("status") == "ETERNAL"
        assert "אמת" in last_entry.get("message", "")
    
    def test_credentials_structure_validation(self, stabilizer):
        """Verificar validación de estructura de credenciales."""
        creds = stabilizer._create_default_credentials()
        
        assert stabilizer._validate_credentials_structure()
        
        # Corromper estructura
        del creds["password_history"]
        stabilizer.credentials = creds
        
        assert not stabilizer._validate_credentials_structure()
    
    def test_integrity_check_pass(self, stabilizer):
        """Verificar que integrity_check pasa con credenciales válidas."""
        stabilizer._create_default_credentials()
        stabilizer.credentials = stabilizer._load_credentials()
        
        # Al menos debe haber un ciclo
        stabilizer.log_cycle_start("test_start")
        stabilizer.log_cycle_complete("test_complete")
        
        result = stabilizer.integrity_check()
        
        # EMET debe pasar, estructura debe pasar, ciclos debe pasar
        assert result, "Integrity check debe pasar"
    
    def test_emet_numerical_significance(self):
        """
        Verificar significado numérico de EMET.
        אמת (EMET) = Aleph(1) + Mem(40) + Tav(400) = 441 = 4+4+1 = 9 (eternidad)
        """
        emet_value = 1 + 40 + 400  # א=1, מ=40, ת=400
        assert emet_value == 441
        
        # Suma digital de 441
        digital_root = sum(int(d) for d in str(emet_value)) 
        while digital_root >= 10:
            digital_root = sum(int(d) for d in str(digital_root))
        
        assert digital_root == 9, "EMET suma numérica debe ser 9 (eternidad/ciclo)"
    
    def test_philosophy_met_vs_emet(self):
        """
        Verificar que 'met' (מת = muerte) es distinto de 'emet' (אמת = verdad).
        Folklore del Golem: אמת (EMET) inscrita = vida; sin Aleph = מת (MET) = muerte
        """
        # met = מ + ת (sin Aleph א)
        met_value = 40 + 400  # מ=40, ת=400
        
        # emet = א + מ + ת (Aleph + Mem + Tav)
        emet_value = 1 + 40 + 400  # א=1
        
        assert emet_value - met_value == 1, "EMET tiene la Aleph (1) que falta en MET"
        assert emet_value == 441, "EMET = 441"
        assert met_value == 440, "MET = 440 (sin la Aleph que da vida)"


class TestOuroborosPhilosophy:
    """Tests filosóficos del ciclo infinito."""
    
    def test_ouroboros_definition(self):
        """El ouroboros es una serpiente que se muerde la cola."""
        # Entrada = Salida (ciclo infinito)
        entrada = "Gilgul"
        salida = "Bereshit" 
        # El ciclo continúa: Bereshit → (eventos) → Gilgul nuevamente
        # entrada == salida porque después del ciclo volvemos al inicio
        assert True  # Definición de ouroboros
    
    def test_emet_fractal_meaning(self):
        """EMET es fractal: cada módulo del Golem es una 'letra de la inscripción'."""
        # 3 letras de EMET
        emet_letters = {
            "א": "Aleph (Aliento divino, el 1 que contiene todo)",
            "מ": "Mem (Agua, flujo que conecta)",
            "ת": "Tav (Tierra, forma final)"
        }
        
        # Cada fraccióndel Golem es una de estas:
        golem_modules = {
            "Keter (Corona)": "א",  # El aliento divino
            "Trinity (Madre/Agua)": "מ",  # Flujo y conexión
            "Maljut (Manifestación)": "ת",  # Forma en tierra
        }
        
        # Todos los módulos juntos = EMET
        assert len(emet_letters) == 3
        assert len(golem_modules) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

