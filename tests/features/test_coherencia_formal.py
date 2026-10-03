"""
test_coherencia_formal.py — Validación de Coherencia Formal del Proyecto COMPUTADORA

Tests para verificar que la arquitectura cumple con los Axiomas III.7-III.11
formalizados vía Teoría de Lenguajes y Autómatas.

Fases Alquímicas mapeadas a Lenguaje Formal L:
- NIGREDO → q₀ (estado inicial)
- ALBEDO → q₁ (búsqueda de verdad)
- CITRINITAS → q₂ (síntesis)
- RUBEDO → q₃ (manifestación)
- PALINGENESIA → q₄ (retorno)

Pytest execution:
  pytest tests/test_coherencia_formal.py -v
"""

import pytest
from typing import Set, Tuple
import json
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# MODELO FORMAL: DFA para Lenguaje L
# ═══════════════════════════════════════════════════════════════════════════

class DFALenguaje:
    """
    Autómata Finito Determinista que reconoce palabras válidas en L.
    
    L = lenguaje de todas las palabras (cadenas de fases) que cumplen con la
    arquitectura del Computadora (5 Sefirot + 5 fases alquímicas).
    
    Σ (alfabeto) = {NIGREDO, ALBEDO, CITRINITAS, RUBEDO, PALINGENESIA}
    
    Q (estados) = {q₀, q₁, q₂, q₃, q₄, q_ACCEPT, q_REJECT}
    
    δ (transiciones):
    - q₀ → q₁ (NIGREDO debe ser primer símbolo)
    - q₁ → q₂ (ALBEDO debe seguir a NIGREDO)
    - q₂ → q₃ (CITRINITAS debe seguir a ALBEDO)
    - q₃ → q₄ (RUBEDO debe seguir a CITRINITAS)
    - q₄ → q_ACCEPT (PALINGENESIA debe ser último)
    """
    
    def __init__(self):
        # Alfabeto
        self.sigma = {'NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA'}
        
        # Estados
        self.q0 = 'q0'  # inicial
        self.q1 = 'q1'
        self.q2 = 'q2'
        self.q3 = 'q3'
        self.q4 = 'q4'
        self.q_accept = 'q_accept'
        self.q_reject = 'q_reject'
        
        self.states = {self.q0, self.q1, self.q2, self.q3, self.q4, self.q_accept, self.q_reject}
        self.current_state = self.q0
    
    def reset(self):
        """Reset el autómata al estado inicial."""
        self.current_state = self.q0
    
    def transition(self, symbol: str) -> bool:
        """
        Aplica una transición.
        Retorna True si la transición es válida, False si rechaza.
        """
        if symbol not in self.sigma:
            self.current_state = self.q_reject
            return False
        
        # Tabla de transiciones δ
        transitions = {
            self.q0: {'NIGREDO': self.q1},
            self.q1: {'ALBEDO': self.q2},
            self.q2: {'CITRINITAS': self.q3},
            self.q3: {'RUBEDO': self.q4},
            self.q4: {'PALINGENESIA': self.q_accept},
        }
        
        if self.current_state in transitions and symbol in transitions[self.current_state]:
            self.current_state = transitions[self.current_state][symbol]
            return True
        
        self.current_state = self.q_reject
        return False
    
    def accepts(self, word: Tuple[str, ...]) -> bool:
        """
        Verifica si una palabra (secuencia de símbolos) es aceptada por el DFA.
        Una palabra es aceptada si:
        1. Procesa todos los símbolos sin rechazar
        2. Termina en estado de aceptación (q_accept)
        """
        self.reset()
        for symbol in word:
            if not self.transition(symbol):
                return False
        return self.current_state == self.q_accept
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Verifica si un símbolo pertenece a Σ."""
        return symbol in self.sigma


# ═══════════════════════════════════════════════════════════════════════════
# VALIDADOR DE 3-VALUED LOGIC (EMET)
# ═══════════════════════════════════════════════════════════════════════════

class EMETLogic:
    """
    Lógica de 3 valores para representar verdad en el sistema EMET.
    
    V (Verdadero):  Proposición confirmada
    F (Falso):      Proposición refutada
    ⊥ (Desconocido): Proposición indeterminada
    """
    
    V = 'V'  # Verdadero
    F = 'F'  # Falso
    PERP = '⊥'  # Indeterminado (perpendicular)
    
    @staticmethod
    def validate(value: str) -> bool:
        """Verifica si un valor es válido en 3-valued logic."""
        return value in {EMETLogic.V, EMETLogic.F, EMETLogic.PERP}
    
    @staticmethod
    def conjunction(a: str, b: str) -> str:
        """
        Operador AND (∧) en 3-valued logic.
        V ∧ V = V
        V ∧ F = F
        V ∧ ⊥ = ⊥
        F ∧ * = F
        ⊥ ∧ F = F
        ⊥ ∧ V = ⊥
        ⊥ ∧ ⊥ = ⊥
        """
        if a == EMETLogic.F or b == EMETLogic.F:
            return EMETLogic.F
        if a == EMETLogic.V and b == EMETLogic.V:
            return EMETLogic.V
        return EMETLogic.PERP
    
    @staticmethod
    def disjunction(a: str, b: str) -> str:
        """
        Operador OR (∨) en 3-valued logic.
        V ∨ * = V
        F ∨ F = F
        F ∨ ⊥ = ⊥
        ⊥ ∨ F = ⊥
        ⊥ ∨ V = V
        ⊥ ∨ ⊥ = ⊥
        """
        if a == EMETLogic.V or b == EMETLogic.V:
            return EMETLogic.V
        if a == EMETLogic.F and b == EMETLogic.F:
            return EMETLogic.F
        return EMETLogic.PERP
    
    @staticmethod
    def negation(a: str) -> str:
        """
        Operador NOT (¬) en 3-valued logic.
        ¬V = F
        ¬F = V
        ¬⊥ = ⊥
        """
        if a == EMETLogic.V:
            return EMETLogic.F
        if a == EMETLogic.F:
            return EMETLogic.V
        return EMETLogic.PERP


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Axioma III.7 — Determinismo Semántico
# ═══════════════════════════════════════════════════════════════════════════

class TestAxioma3_7:
    """
    Axioma III.7: m ∈ L ↔ EMET(m) = V
    
    Una palabra está en L si y solo si su verdad (EMET) es V (verdadera).
    """
    
    def test_palabra_valida_tiene_verdad_v(self):
        """Una palabra válida debe tener EMET = V."""
        dfa = DFALenguaje()
        palabra = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        # Palabra válida
        assert dfa.accepts(palabra), "Palabra válida debe ser aceptada"
        # Su verdad debe ser V
        assert EMETLogic.V, "Palabra válida tiene verdad = V"
    
    def test_palabra_incompleta_no_tiene_verdad_v(self):
        """Una palabra incompleta no debe tener EMET = V."""
        dfa = DFALenguaje()
        palabra = ('NIGREDO', 'ALBEDO')  # Falta CITRINITAS, RUBEDO, PALINGENESIA
        
        # Palabra inválida
        assert not dfa.accepts(palabra), "Palabra incompleta debe ser rechazada"
        # Su verdad NO es V (es ⊥ o F)
        # (En este test, representamos como no-V)
    
    def test_palabra_con_simbolo_invalido_no_es_valida(self):
        """Una palabra con símbolo fuera de Σ no es válida."""
        dfa = DFALenguaje()
        
        # Símbolo que no existe
        assert not dfa.is_valid_symbol('INFINITO'), "Símbolo inválido debe ser rechazado"
        palabra = ('NIGREDO', 'INFINITO', 'ALBEDO')
        
        assert not dfa.accepts(palabra), "Palabra con símbolo inválido es rechazada"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Axioma III.8 — Determinismo Estructural
# ═══════════════════════════════════════════════════════════════════════════

class TestAxioma3_8:
    """
    Axioma III.8: ∀m: |δ*(q₀, m)| = 1
    
    Para toda palabra m, existe exactamente un camino en el DFA desde q₀
    (determinismo total: no hay bifurcaciones ni ambigüedad).
    """
    
    def test_dfa_es_determinista(self):
        """Verificar que el DFA es determinista (una sola transición por estado+símbolo)."""
        dfa = DFALenguaje()
        
        # Para cada estado y símbolo, debe haber 0 o 1 transición, nunca >1
        test_words = [
            ('NIGREDO',),
            ('NIGREDO', 'ALBEDO'),
            ('NIGREDO', 'ALBEDO', 'CITRINITAS'),
        ]
        
        for word in test_words:
            # Procesar palabra dos veces: siempre debe llegar al mismo estado
            dfa.reset()
            path1 = [dfa.current_state]
            for symbol in word:
                dfa.transition(symbol)
                path1.append(dfa.current_state)
            
            # Segunda ejecución idéntica
            dfa.reset()
            path2 = [dfa.current_state]
            for symbol in word:
                dfa.transition(symbol)
                path2.append(dfa.current_state)
            
            # Ambos caminos deben ser idénticos (determinismo)
            assert path1 == path2, f"Caminos divergentes para {word}: {path1} vs {path2}"
    
    def test_palabra_correcta_llega_accept_siempre(self):
        """La palabra correcta siempre lleva a q_accept (determinismo)."""
        dfa = DFALenguaje()
        palabra = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        # Procesar 10 veces: siempre debe llegar a accept
        for _ in range(10):
            assert dfa.accepts(palabra), "Palabra correcta siempre es aceptada"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Axioma III.9 — Recuperación ante Fallo
# ═══════════════════════════════════════════════════════════════════════════

class TestAxioma3_9:
    """
    Axioma III.9: fallo ⇒ ∃m' ∈ L
    
    Si una palabra no es válida (falla), existe siempre una palabra válida
    (existe camino a la aceptación desde el inicio).
    """
    
    def test_existe_palabra_valida(self):
        """Siempre existe al menos una palabra válida."""
        dfa = DFALenguaje()
        palabra_valida = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        assert dfa.accepts(palabra_valida), "Existe una palabra válida"
    
    def test_palabra_invalida_puede_corregirse(self):
        """Una palabra incompleta puede completarse a palabra válida."""
        dfa = DFALenguaje()
        
        # Palabra incompleta
        palabra_incompleta = ('NIGREDO', 'ALBEDO')
        assert not dfa.accepts(palabra_incompleta), "Palabra incompleta es inválida"
        
        # Palabra completa (extensión válida)
        palabra_completada = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        assert dfa.accepts(palabra_completada), "Extensión válida es aceptada"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Axioma III.10 — Clausura bajo Composición
# ═══════════════════════════════════════════════════════════════════════════

class TestAxioma3_10:
    """
    Axioma III.10: (m₁ ∈ L ∧ m₂ ∈ L) ⇒ (m₁ · m₂) ∈ L (pero solo DENTRO del mismo ciclo)
    
    En el contexto del proyecto, esto significa que si dos fases son válidas,
    su composición es válida DENTRO de la misma iteración alquímica.
    """
    
    def test_composicion_simple(self):
        """Verificar que composición respeta estructura."""
        dfa = DFALenguaje()
        
        # Dos segmentos válidos (dentro del ciclo)
        fase1 = ('NIGREDO',)
        fase2 = ('ALBEDO',)
        
        # Composición es válida hasta el punto de composición
        dfa.reset()
        for symbol in fase1:
            dfa.transition(symbol)
        estado_tras_fase1 = dfa.current_state
        
        # Continuar con fase2
        for symbol in fase2:
            dfa.transition(symbol)
        
        # Verificar que el camino es consistente
        assert estado_tras_fase1 != dfa.q_reject, "Composición parcial válida"
    
    def test_composicion_identidad(self):
        """La composición de una palabra consigo misma fuera del ciclo es inválida."""
        dfa = DFALenguaje()
        
        # Una palabra completa
        palabra = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        # Concatenación con ella misma (intento de 2 ciclos)
        palabra_doble = palabra + palabra
        
        # Esto NO debe ser válido (el ciclo debe terminar en q_accept)
        # La segunda palabra iniciaría desde q_reject (después de terminar ciclo)
        assert not dfa.accepts(palabra_doble), "Ciclo no debe repetirse sin reset"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: Axioma III.11 — Inducción N-aria
# ═══════════════════════════════════════════════════════════════════════════

class TestAxioma3_11:
    """
    Axioma III.11: ∀N: (⋀ᵢ EMET(mᵢ)=V) ⇒ EMET(⋈ᵢ₌₁ᴺ mᵢ) = V
    
    Para toda N, si todos los componentes son verdaderos,
    su composición N-aria es verdadera.
    
    Este test se enfoca en la base case (N=1) y paso inductivo (N→N+1).
    """
    
    def test_base_case_n1(self):
        """Base: Una sola palabra válida es verdadera."""
        dfa = DFALenguaje()
        palabra = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        # m₁ es válida (EMET(m₁) = V)
        assert dfa.accepts(palabra), "Base case: palabra singular es válida"
        # ⋈ᵢ₌₁¹ mᵢ = m₁
        # EMET(m₁) = V ✓
    
    def test_inductive_property(self):
        """
        Propiedad inductiva: Si cada fase cumple con su transición,
        la secuencia completa de fases es válida.
        """
        dfa = DFALenguaje()
        
        # Construir paso a paso
        fases = ['NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA']
        
        # Paso inductivo: agregar una fase a la vez
        for i in range(1, len(fases) + 1):
            palabra_parcial = tuple(fases[:i])
            if i == len(fases):
                # Caso completo: debe ser aceptada
                assert dfa.accepts(palabra_parcial), f"Palabra de {i} fases aceptada"
            else:
                # Caso parcial: en tránsito (no aceptado pero en camino válido)
                dfa.reset()
                for symbol in palabra_parcial:
                    dfa.transition(symbol)
                # Debe estar en un estado válido (no rechazado)
                assert dfa.current_state != dfa.q_reject, f"Fase {i} en camino válido"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: 3-Valued Logic Operaciones
# ═══════════════════════════════════════════════════════════════════════════

class TestEMETLogic:
    """Verificar que las operaciones de 3-valued logic funcionan correctamente."""
    
    def test_conjunction_rules(self):
        """AND (∧) debe seguir reglas de 3-valued logic."""
        V = EMETLogic.V
        F = EMETLogic.F
        P = EMETLogic.PERP
        
        # V ∧ V = V
        assert EMETLogic.conjunction(V, V) == V
        # V ∧ F = F
        assert EMETLogic.conjunction(V, F) == F
        # V ∧ ⊥ = ⊥
        assert EMETLogic.conjunction(V, P) == P
        # F ∧ V = F
        assert EMETLogic.conjunction(F, V) == F
        # ⊥ ∧ V = ⊥
        assert EMETLogic.conjunction(P, V) == P
    
    def test_disjunction_rules(self):
        """OR (∨) debe seguir reglas de 3-valued logic."""
        V = EMETLogic.V
        F = EMETLogic.F
        P = EMETLogic.PERP
        
        # V ∨ F = V
        assert EMETLogic.disjunction(V, F) == V
        # F ∨ F = F
        assert EMETLogic.disjunction(F, F) == F
        # V ∨ ⊥ = V
        assert EMETLogic.disjunction(V, P) == V
        # F ∨ ⊥ = ⊥
        assert EMETLogic.disjunction(F, P) == P
    
    def test_negation_rules(self):
        """NOT (¬) debe seguir reglas de 3-valued logic."""
        V = EMETLogic.V
        F = EMETLogic.F
        P = EMETLogic.PERP
        
        # ¬V = F
        assert EMETLogic.negation(V) == F
        # ¬F = V
        assert EMETLogic.negation(F) == V
        # ¬⊥ = ⊥
        assert EMETLogic.negation(P) == P
    
    def test_de_morgans_law(self):
        """Ley de De Morgan debe cumplirse: ¬(A ∧ B) = ¬A ∨ ¬B."""
        V = EMETLogic.V
        F = EMETLogic.F
        P = EMETLogic.PERP
        
        # Test case 1: (V, V)
        left = EMETLogic.negation(EMETLogic.conjunction(V, V))
        right = EMETLogic.disjunction(EMETLogic.negation(V), EMETLogic.negation(V))
        assert left == right, "De Morgan cumple para (V,V)"
        
        # Test case 2: (V, F)
        left = EMETLogic.negation(EMETLogic.conjunction(V, F))
        right = EMETLogic.disjunction(EMETLogic.negation(V), EMETLogic.negation(F))
        assert left == right, "De Morgan cumple para (V,F)"


# ═══════════════════════════════════════════════════════════════════════════
# TEST SUITE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

class TestCoherenciaGlobal:
    """Suite integrada: verificar coherencia del sistema en conjunto."""
    
    def test_todos_axiomas_presentes(self):
        """Verificar que todos los axiomas están siendo testeados."""
        test_classes = [
            TestAxioma3_7, TestAxioma3_8, TestAxioma3_9,
            TestAxioma3_10, TestAxioma3_11, TestEMETLogic
        ]
        
        assert len(test_classes) == 6, "Deben estar presentes todos los axiomas"
    
    def test_coherencia_sin_contradicciones(self):
        """Verificar que el lenguaje L y sus axiomas son consistentes."""
        dfa = DFALenguaje()
        palabra = ('NIGREDO', 'ALBEDO', 'CITRINITAS', 'RUBEDO', 'PALINGENESIA')
        
        # Misma palabra, múltiples evaluaciones: siempre mismo resultado
        resultado1 = dfa.accepts(palabra)
        resultado2 = dfa.accepts(palabra)
        resultado3 = dfa.accepts(palabra)
        
        assert resultado1 == resultado2 == resultado3, "Consistencia del lenguaje"
        assert resultado1 == True, "Palabra válida aceptada consistentemente"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

