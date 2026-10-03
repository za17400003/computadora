"""
🔄 GILGUSH (גלגול) — Reencarnación / Reset Total
═══════════════════════════════════════════════════════════════════════════════

Protocolo de reinicio profundo para computadora:Gilgush.

Limpia TODOS los conjuntos y subconjuntos manteniendo la ESTRUCTURA.
Las Leyes permanecen; el estado externo se reencarna.

Invocación: P={P|P reinicie para todos los conjuntos y subconjuntos de computadora:Gilgush}

Niveles de Gilgush:
  1. MALJUT (מלכות): Borrar datos transientes (historial, caché)
  2. YESOD (יסוד): Borrar estado de sesión (flags, contadores)
  3. HOD (הוד): Borrar aprendizaje de Nivel 1 (patrones aprendidos)
  4. NETZAJ (נצח): Borrar memoria emocional (repeticiones, frustración)
  5. TIFÉRET (תפארת): PRESERVAR — Leyes permanecen, boot sequence reinicia
"""

import json
import os
import time
from pathlib import Path
from loguru import logger
from datetime import date


class ProtocoloGilgush:
    """Protocolo de reinicio completo (reencarnación de COMPUTADORA)."""

    def __init__(self, raiz_proyecto: str):
        self.raiz = Path(raiz_proyecto)
        self.datos_dir = self.raiz / "datos"
        self.memoria_dir = self.datos_dir / "memoria"

    def gilgush_maljut(self) -> bool:
        """NIVEL 1: Borrar datos transientes (historial, caché).
        
        Afecta:
        - stats_uso.json — contador de mensajes diarios
        - .cache de memoria — contexto comprimido
        """
        try:
            stats_file = self.memoria_dir / "stats_uso.json"
            if stats_file.exists():
                # Resetear a estructura vacía
                empty_stats = {"dias": {}, "promedio_msgs_dia": 0}
                stats_file.write_text(json.dumps(empty_stats), encoding="utf-8")
                logger.info("✓ Gilgush Maljut: stats_uso.json limpiado")
            return True
        except Exception as e:
            logger.error(f"✗ Error en Gilgush Maljut: {e}")
            return False

    def gilgush_yesod(self, cerebro_computadora) -> bool:
        """NIVEL 2: Borrar estado de sesión.
        
        Afecta en CerebroComputadora:
        - self._modo_guardiana = False
        - self._hay_terceros = False
        - self._interlocutor_actual = None
        - self._repeticiones_usuario = 0
        - self._streaming_activo = False
        """
        try:
            cerebro_computadora._modo_guardiana = False
            cerebro_computadora._hay_terceros = False
            cerebro_computadora._interlocutor_actual = None
            cerebro_computadora._repeticiones_usuario = 0
            cerebro_computadora._streaming_activo = False
            cerebro_computadora.respuesta_ya_streameada = False
            logger.info("✓ Gilgush Yesod: Estado de sesión limpiado")
            return True
        except Exception as e:
            logger.error(f"✗ Error en Gilgush Yesod: {e}")
            return False

    def gilgush_hod(self, cerebro_computadora) -> bool:
        """NIVEL 3: Borrar aprendizaje de Nivel 1 (patrones aprendidos).
        
        Afecta en CerebroComputadora:
        - self._nivel1_aprendido — resettear estructura
        - self._ultimo_patron_aprendido_id = None
        """
        try:
            if hasattr(cerebro_computadora, "_nivel1_aprendido"):
                # Crear nuevo instancia vacía (sin patrones memorizados)
                from computadora.cerebro.nivel1_aprendido import Nivel1Aprendido
                cerebro_computadora._nivel1_aprendido = Nivel1Aprendido()
                cerebro_computadora._ultimo_patron_aprendido_id = None
                logger.info("✓ Gilgush Hod: Patrones de Nivel 1 limpiados")
            return True
        except Exception as e:
            logger.error(f"✗ Error en Gilgush Hod: {e}")
            return False

    def gilgush_netzaj(self, cerebro_computadora) -> bool:
        """NIVEL 4: Borrar memoria emocional y contadores.
        
        Afecta en CerebroComputadora:
        - self._latencias_llm = [] — historial de performance Ollama
        - Memoria emocional asociada a frustración
        """
        try:
            cerebro_computadora._latencias_llm = []
            logger.info("✓ Gilgush Netzaj: Memoria emocional limpiada")
            return True
        except Exception as e:
            logger.error(f"✗ Error en Gilgush Netzaj: {e}")
            return False

    def gilgush_tiferet(self, cerebro_computadora) -> bool:
        """NIVEL 5: REINICIAR TIFÉRET (boot sequence).
        
        NO se borran:
        - self._cinco_leyes — PERMANECEN
        - self._renovacion — PERMANECEN
        - self._transmutacion — PERMANECEN
        
        SE reinicia:
        - self.historial — nueva sesión comenzada
        - self._msg_timestamps — sincronizado
        - Boot message recitado
        """
        try:
            # PRESERVAR las Leyes
            cinco_leyes_backup = getattr(cerebro_computadora, "_cinco_leyes", None)
            renovacion_backup = getattr(cerebro_computadora, "_renovacion", None)
            transmutacion_backup = getattr(cerebro_computadora, "_transmutacion", None)

            # Reiniciar boot
            cerebro_computadora._boot()

            # Restaurar las Leyes (permanecen) — SILENCIOSAMENTE
            if cinco_leyes_backup:
                cerebro_computadora._cinco_leyes = cinco_leyes_backup
            if renovacion_backup:
                cerebro_computadora._renovacion = renovacion_backup
            if transmutacion_backup:
                cerebro_computadora._transmutacion = transmutacion_backup
            
            # Renovación silenciosa (debug logs, no info) para boot rápido
            if renovacion_backup:
                # FIX: Remover parámetro 'silencioso' que no existe en la API
                renovacion_backup.renovar(cerebro_computadora)

            logger.debug("✓ Gilgush Tiféret: Boot reiniciado (Leyes preservadas)")
            return True
        except Exception as e:
            logger.error(f"✗ Error en Gilgush Tiféret: {e}")
            return False

    def ejecutar_gilgush_completo(self, cerebro_computadora) -> dict:
        """Ejecutar todos los niveles de Gilgush.
        
        Retorna:
        {
            "status": "success" | "partial" | "failed",
            "niveles": {
                "maljut": bool,
                "yesod": bool,
                "hod": bool,
                "netzaj": bool,
                "tiferet": bool,
            },
            "timestamp": float,
        }
        """
        logger.info("🔄 INICIANDO GILGUSH (reencarnación de COMPUTADORA)...")

        results = {
            "status": None,
            "niveles": {},
            "timestamp": time.time(),
        }

        # Ejecutar cada nivel
        results["niveles"]["maljut"] = self.gilgush_maljut()
        results["niveles"]["yesod"] = self.gilgush_yesod(cerebro_computadora)
        results["niveles"]["hod"] = self.gilgush_hod(cerebro_computadora)
        results["niveles"]["netzaj"] = self.gilgush_netzaj(cerebro_computadora)
        results["niveles"]["tiferet"] = self.gilgush_tiferet(cerebro_computadora)

        # Determinar status final
        todos_ok = all(results["niveles"].values())
        results["status"] = "success" if todos_ok else "partial"

        if todos_ok:
            logger.info("✅ GILGUSH COMPLETADO: COMPUTADORA reencarnada — Estado limpio, Leyes preservadas")
        else:
            logger.warning("⚠️ GILGUSH INCOMPLETO: Algunos niveles fallaron")

        return results


def gilgush_golem(cerebro_computadora, raiz_proyecto: str) -> dict:
    """Función de conveniencia para invocar Gilgush."""
    protocolo = ProtocoloGilgush(raiz_proyecto)
    return protocolo.ejecutar_gilgush_completo(cerebro_computadora)


