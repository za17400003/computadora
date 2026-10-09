"""
computadora/nucleo/mother_feedback_loop.py — Binah Multiplier (FP-137 C1)

La Madre que recibe PIEDAD, procesa con COMPASIÓN, aprende por MULTIPLICACIÓN.
Retroalimentación bidireccional: Minimi captura eventos usuario → Computadora enriquece → retorna mejorado.

Flujo:
1. Usuario interactúa en Minimi (Android): click, voz, contexto
2. MotherFeedback CAPTURA evento (timestamp, acción, contexto, emoción)
3. Envía al Enciclopedia (server): procesamiento asincrónico
4. MULTIPLICA vs Nivel 1 patterns: confianza += si coincide
5. RETORNA mejorado a Computadora: "Este patrón 87% seguro" (antes: Nivel 1 crudo)

Filosofía:
- No castiga inconsistencias (Gevurah)
- Amplifica tendencias positivas (Jesed)
- Balanza: PC (proactivo) ↔ Móvil (reactivo)

Arquitectura:
- MotherFeedback: clase que captura + procesa evento
- FeedbackMultiplier: refuerza patrones vs histórico
- BidirectionalSync: mantiene sincronía PC/Móvil
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any, Callable
from dataclasses import dataclass, asdict
from loguru import logger


@dataclass
class UserEvent:
    """Evento capturado del usuario en Minimi/Computadora."""
    timestamp: float
    platform: str  # "minimi" o "computadora"
    accion: str  # "voz_query", "click_menu", "alarma_activada", etc.
    contexto: Optional[str] = None  # contexto donde ocurrió
    emocion_detectada: Optional[str] = None  # "alegría", "confusión", "frustración"
    resultado: Optional[str] = None  # qué pasó después
    confianza_usuario: float = 0.5  # 0.0-1.0, cuán seguro estaba user


@dataclass
class FeedbackResult:
    """Resultado del procesamiento de feedback por Mother."""
    evento_original: UserEvent
    patron_detectado: Optional[str] = None  # "patrón X encontrado"
    confianza_mejorada: float = 0.0  # cuánto subió confianza
    insight: Optional[str] = None  # "Aprendes mejor a las 15:00"
    recomendacion: Optional[str] = None  # "Intenta esto mañana"


class MotherFeedback:
    """
    Captura y procesa eventos del usuario en Minimi/Computadora.
    Objetivo: entender patrones y multiplicar insights.
    """
    
    def __init__(self, on_feedback: Optional[Callable[[FeedbackResult], None]] = None):
        """
        Args:
            on_feedback: Callback cuando Mother procesa evento significativo
                        on_feedback(FeedbackResult) — retorna a usuario
        """
        self.on_feedback = on_feedback or (lambda res: None)
        self._historial_eventos: list[UserEvent] = []
        self._patrones_detectados: dict[str, dict] = {}
        self._data_path = Path(__file__).resolve().parents[2] / "datos" / "mother_feedback.jsonl"
        self._minimi_cache_path = Path(__file__).resolve().parents[2] / "datos" / "minimi_feedback_cache.json"
    
    def capturar_evento(self, 
                       accion: str,
                       platform: str = "computadora",
                       contexto: Optional[str] = None,
                       emocion: Optional[str] = None,
                       resultado: Optional[str] = None,
                       confianza: float = 0.5) -> FeedbackResult:
        """
        Captura evento del usuario.
        
        Args:
            accion: tipo acción ("voz_query", "autocompletado_usado", "timer_activado")
            platform: "minimi" o "computadora"
            contexto: dónde ocurrió ("búsqueda", "configuración", "inicio")
            emocion: emoción detectada ("alegría", "confusión", "frustración")
            resultado: qué pasó ("exitoso", "error", "cancelado")
            confianza: 0.0-1.0, cuán seguro estaban
        
        Returns:
            FeedbackResult con procesamiento
        """
        evento = UserEvent(
            timestamp=time.time(),
            platform=platform,
            accion=accion,
            contexto=contexto,
            emocion_detectada=emocion,
            resultado=resultado,
            confianza_usuario=confianza,
        )
        
        # Registrar en historial
        self._historial_eventos.append(evento)
        
        # Procesar el evento
        resultado_proc = self._procesar_evento(evento)
        
        # Persistir
        self._guardar_evento(evento)
        
        # Notificar si encontró insight significativo
        if resultado_proc.insight or resultado_proc.recomendacion:
            self.on_feedback(resultado_proc)
        
        return resultado_proc
    
    def _procesar_evento(self, evento: UserEvent) -> FeedbackResult:
        """Procesa evento: detección de patrones + multiplicación."""
        resultado = FeedbackResult(
            evento_original=evento,
            patron_detectado=None,
            confianza_mejorada=0.0,
            insight=None,
            recomendacion=None,
        )
        
        # Detector 1: ¿Es repitición?
        patron_key = f"{evento.accion}@{evento.contexto}"
        if patron_key in self._patrones_detectados:
            patron_info = self._patrones_detectados[patron_key]
            patron_info["hits"] += 1
            patron_info["ultima_vez"] = evento.timestamp
            
            # Multiplicar confianza según repeticiones
            hits = patron_info["hits"]
            confianza_mejorada = min(0.1 * hits, 0.5)  # Máx +0.5
            resultado.confianza_mejorada = confianza_mejorada
            resultado.patron_detectado = patron_key
            
            # Generar insight si lo merece
            if hits >= 3:
                resultado.insight = f"🔄 Detecté patrón: {evento.accion} en {evento.contexto} ({hits}x)"
                resultado.recomendacion = f"Considera automatizar esto"
        else:
            # Primer sighting
            self._patrones_detectados[patron_key] = {
                "hits": 1,
                "primera_vez": evento.timestamp,
                "ultima_vez": evento.timestamp,
                "emociones": [evento.emocion_detectada] if evento.emocion_detectada else [],
                "confianza_promedio": evento.confianza_usuario,
            }
        
        # Detector 2: ¿Emoción recurrente?
        if evento.emocion_detectada:
            emociones = self._patrones_detectados[patron_key]["emociones"]
            emociones.append(evento.emocion_detectada)
            
            # Si emoción negativa recurrente → insight de mejora
            if evento.emocion_detectada in ["frustración", "confusión", "error"]:
                if emociones.count(evento.emocion_detectada) >= 2:
                    resultado.insight = f"⚠️ Noté {evento.emocion_detectada} recurrente en {evento.contexto}"
                    resultado.recomendacion = f"¿Necesitas ayuda? Podemos mejorar esto"
        
        # Detector 3: Platforma específica — sinergia PC/Móvil
        platform_stats = self._calcular_stats_por_platform(evento.accion)
        if platform_stats["minimi_hits"] > 0 and platform_stats["computadora_hits"] > 0:
            # Mismo patrón en ambas plataformas = mayor confianza
            resultado.confianza_mejorada += 0.15
            if platform_stats["minimi_hits"] >= 2:
                resultado.insight = f"✨ Patrón sincronizado (Computadora + Minimi): {evento.accion}"
        
        return resultado
    
    def _guardar_evento(self, evento: UserEvent) -> None:
        """Persiste evento a archivo."""
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._data_path, "a", encoding="utf-8") as f:
                evento_dict = asdict(evento)
                evento_dict["timestamp_iso"] = datetime.fromtimestamp(evento.timestamp).isoformat()
                f.write(json.dumps(evento_dict, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"No se pudo guardar evento Mother: {e}")
    
    def _calcular_stats_por_platform(self, accion: str) -> dict[str, int]:
        """Calcula estadísticas por plataforma para una acción."""
        minimi_hits = sum(1 for e in self._historial_eventos 
                         if e.accion == accion and e.platform == "minimi")
        computadora_hits = sum(1 for e in self._historial_eventos 
                        if e.accion == accion and e.platform == "computadora")
        return {"minimi_hits": minimi_hits, "computadora_hits": computadora_hits}
    
    def estadisticas_sesion(self) -> dict[str, Any]:
        """Estadísticas globales de sesión."""
        if not self._historial_eventos:
            return {"total_eventos": 0, "patrones": 0, "confianza_promedio": 0.0}
        
        total_eventos = len(self._historial_eventos)
        patrones = len(self._patrones_detectados)
        confianza_prom = sum(e.confianza_usuario for e in self._historial_eventos) / total_eventos
        
        minimi_count = sum(1 for e in self._historial_eventos if e.platform == "minimi")
        computadora_count = total_eventos - minimi_count
        
        return {
            "total_eventos": total_eventos,
            "patrones_detectados": patrones,
            "confianza_promedio": round(confianza_prom, 2),
            "eventos_minimi": minimi_count,
            "eventos_computadora": computadora_count,
            "sincronia_bidireccional": minimi_count > 0 and computadora_count > 0,
        }
    
    def recomendacion_diaria(self) -> Optional[str]:
        """Genera recomendación based en patrones observados."""
        if not self._patrones_detectados:
            return None
        
        # Encontrar patrón más consistente
        patron_top = max(
            self._patrones_detectados.items(),
            key=lambda x: x[1]["hits"],
            default=(None, {})
        )
        
        if not patron_top[0]:
            return None
        
        patron_key, info = patron_top
        hits = info["hits"]
        
        # Generar recomendación basada en fortaleza del patrón
        if hits >= 5:
            return f"🏆 Tu patrón más fuerte: {patron_key} ({hits}x). Considera optimizarlo."
        elif hits >= 3:
            return f"🔄 Patrón emergente: {patron_key}. Ocurre {hits} veces."
        else:
            return None


class BidirectionalSync:
    """
    Sincroniza estado entre Computadora PC y Minimi Android.
    Asegura que aprendizajes en una plataforma benefician la otra.
    """
    
    def __init__(self):
        self._cache_path = Path(__file__).resolve().parents[2] / "datos" / "bidirectional_sync.json"
        self._ultima_sincronizacion = 0.0
        self._sync_interval = 300.0  # 5 minutos
    
    def sincronizar(self, eventos_minimi: list[UserEvent], 
                   patrones_computadora: dict) -> dict[str, Any]:
        """
        Sincroniza eventos de Minimi con patrones de Computadora.
        Retorna: eventos enriquecidos + patrones mejorados.
        """
        ahora = time.time()
        
        # Verificar throttle
        if ahora - self._ultima_sincronizacion < self._sync_interval:
            return {"sincronizado": False, "razon": "throttle_activo"}
        
        resultado = {
            "sincronizado": True,
            "eventos_procesados": len(eventos_minimi),
            "patrones_enriquecidos": 0,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Procesar cada evento de Minimi
        for evento in eventos_minimi:
            # Verificar si existe patrón similar en Computadora
            patron_key = f"{evento.accion}@{evento.contexto}"
            if patron_key in patrones_computadora:
                # Enriquecer con datos de Computadora
                evento.confianza_usuario = min(
                    evento.confianza_usuario + 0.15,
                    1.0
                )
                resultado["patrones_enriquecidos"] += 1
        
        self._ultima_sincronizacion = ahora
        self._guardar_sync_cache(resultado)
        
        return resultado
    
    def _guardar_sync_cache(self, resultado: dict) -> None:
        """Persiste resultado de sincronización."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar sync cache: {e}")


# Singleton global
_mother_feedback: Optional[MotherFeedback] = None
_bidirectional_sync: Optional[BidirectionalSync] = None


def crear_mother_feedback(on_feedback: Optional[Callable[[FeedbackResult], None]] = None) -> MotherFeedback:
    """Crea o retorna instancia global de Mother."""
    global _mother_feedback
    
    if _mother_feedback is None:
        _mother_feedback = MotherFeedback(on_feedback=on_feedback)
        logger.info("🌙 Mother Feedback Loop activado — Binah despierta")
    
    return _mother_feedback


def obtener_mother_feedback() -> Optional[MotherFeedback]:
    """Obtiene instancia global (si existe)."""
    return _mother_feedback


def crear_sync() -> BidirectionalSync:
    """Crea o retorna instancia global de Sync."""
    global _bidirectional_sync
    
    if _bidirectional_sync is None:
        _bidirectional_sync = BidirectionalSync()
        logger.info("🔄 Bidirectional Sync activado — PC ↔ Móvil")
    
    return _bidirectional_sync


