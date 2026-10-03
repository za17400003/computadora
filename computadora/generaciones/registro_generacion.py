"""Registro de Generación — Captura estado completo de una sesión.

Una "generación" = una sesión completa del usuario.
Registra: duración, eventos, errores, mejoras, version código.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from loguru import logger


@dataclass
class MetricasGeneracion:
    """Métricas cuantificables de una generación — Maljut (lo materializado).
    
    Captura TODOS los parámetros observables de COMPUTADORA:
    - Coherencia (auditoría)
    - Rendimiento (latencia, CPU, memoria)
    - Percepción (sensores, rostros)
    - Verdad (verificaciones, bloques)
    - Comunicación (comandos, respuestas)
    - Integridad (purga, caché)
    - Aprendizaje (patrones, recomendaciones)
    """
    
    # ===== COHERENCIA (Auditoría) =====
    coherencia_porcentaje: float  # 0-100
    auditorias_ejecutadas: int = 0
    incoherencias_detectadas: int = 0
    incoherencias_resueltas: int = 0
    
    # ===== RENDIMIENTO =====
    uptime_minutos: float = 0.0
    latencia_promedio_ms: float = 0.0
    latencia_maxima_ms: float = 0.0
    pico_cpu_porcentaje: float = 0.0
    pico_memoria_mb: float = 0.0
    temperatura_promedio_celsius: float = 0.0  # si disponible
    
    # ===== PERCEPCIÓN (Sensores) =====
    rostros_detectados: int = 0
    rostros_no_detectados: int = 0
    confianza_facial_promedio: float = 0.0  # 0-1
    dispositivos_audio_activos: int = 0
    dispositivos_audio_fallidos: int = 0
    sensores_totales: int = 0
    sensores_operacionales: int = 0
    
    # ===== VERDAD (Verificación EMET) =====
    verificaciones_exitosas: int = 0
    verificaciones_fallidas: int = 0
    bloques_por_incoherencia: int = 0  # VerificadorRealidad bloqueante
    contradicciones_detectadas: int = 0
    
    # ===== COMUNICACIÓN (NLU/TTS) =====
    comandos_procesados: int = 0
    comandos_exitosos: int = 0
    comandos_fallidos: int = 0
    respuestas_generadas: int = 0
    tokens_usados: int = 0
    tasa_exito_comandos: float = 0.0  # 0-1
    
    # ===== INTEGRIDAD (Purga) =====
    archivos_purgados: int = 0
    cache_limpiado_mb: float = 0.0
    duplicados_encontrados: int = 0
    duplicados_consolidados: int = 0
    
    # ===== APRENDIZAJE (Mejora) =====
    patrones_detectados: int = 0
    recomendaciones_generadas: int = 0
    recomendaciones_aplicadas: int = 0
    features_usados: int = 0
    features_no_usados: int = 0
    confianza_sistema_promedio: float = 0.0  # 0-1
    
    # ===== ESTADO GENERAL =====
    errores_cantidad: int = 0
    errores_severidad_promedio: str = "BAJA"  # "BAJA" | "MEDIA" | "ALTA" | "CRITICA"
    feedback_usuario_promedio: float = 0.0  # 0-1
    mejoras_aplicadas: int = 0
    problemas_encontrados: int = 0


@dataclass
class RegistroGeneracion:
    """Registro completo de una generación (sesión) — Maljut completo."""
    generacion_id: str  # hash de timestamp
    boot_timestamp: str
    shutdown_timestamp: Optional[str] = None
    duracion_minutos: Optional[float] = None
    version_codigo: str = "unknown"  # git commit
    usuario_conectado: Optional[str] = None
    eventos_principales: list[str] = None  # WIs ejecutadas
    errores_encontrados: list[str] = None
    mejoras_aplicadas: list[str] = None
    estado_final: str = "unknown"  # "shutdown_normal" | "error" | "timeout"
    metricas: Optional[MetricasGeneracion] = None
    notas: Optional[str] = None
    # Nuevos campos para captura completa de Maljut
    sensores_snapshot: Optional[dict] = None  # Estado de sensores al shutdown
    logs_resumen: Optional[str] = None  # Resumen de logs por categoría
    caché_estado: Optional[dict] = None  # Estado del caché al shutdown
    
    def __post_init__(self):
        if self.eventos_principales is None:
            self.eventos_principales = []
        if self.errores_encontrados is None:
            self.errores_encontrados = []
        if self.mejoras_aplicadas is None:
            self.mejoras_aplicadas = []
    
    def to_dict(self) -> dict:
        """Convertir a dict para JSON."""
        d = asdict(self)
        if self.metricas:
            d["metricas"] = asdict(self.metricas)
        return d
    
    def to_json(self) -> str:
        """Convertir a JSON."""
        return json.dumps(self.to_dict(), indent=2)


class GestorGeneraciones:
    """Gestor de registro y almacenamiento de generaciones."""
    
    def __init__(self, gen_dir: str = ".audit/generaciones"):
        self.gen_dir = Path(gen_dir)
        self.gen_dir.mkdir(parents=True, exist_ok=True)
        self.generacion_actual: Optional[RegistroGeneracion] = None
        logger.info(f"GestorGeneraciones inicializado ({self.gen_dir})")
    
    def crear_generacion(self, usuario_id: Optional[str] = None, 
                        version_codigo: str = "unknown") -> RegistroGeneracion:
        """Crear nueva generación (al boot)."""
        import hashlib
        
        timestamp = datetime.now().isoformat()
        gen_id = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        
        self.generacion_actual = RegistroGeneracion(
            generacion_id=gen_id,
            boot_timestamp=timestamp,
            usuario_conectado=usuario_id,
            version_codigo=version_codigo,
        )
        
        logger.info(f"✓ Generación {gen_id} creada")
        return self.generacion_actual
    
    def registrar_evento(self, evento: str):
        """Registrar evento importante en generación actual."""
        if not self.generacion_actual:
            logger.warning("No hay generación activa")
            return
        
        self.generacion_actual.eventos_principales.append(evento)
    
    def registrar_error(self, error: str):
        """Registrar error detectado."""
        if not self.generacion_actual:
            logger.warning("No hay generación activa")
            return
        
        self.generacion_actual.errores_encontrados.append(error)
    
    def registrar_mejora(self, mejora: str):
        """Registrar mejora aplicada."""
        if not self.generacion_actual:
            logger.warning("No hay generación activa")
            return
        
        self.generacion_actual.mejoras_aplicadas.append(mejora)
    
    def shutdown_generacion(self, estado_final: str = "shutdown_normal", 
                           metricas: Optional[MetricasGeneracion] = None):
        """Finalizar generación actual (al shutdown)."""
        if not self.generacion_actual:
            logger.warning("No hay generación activa")
            return
        
        self.generacion_actual.shutdown_timestamp = datetime.now().isoformat()
        self.generacion_actual.estado_final = estado_final
        self.generacion_actual.metricas = metricas
        
        # Calcular duración
        try:
            boot = datetime.fromisoformat(self.generacion_actual.boot_timestamp)
            shutdown = datetime.fromisoformat(self.generacion_actual.shutdown_timestamp)
            duracion = (shutdown - boot).total_seconds() / 60
            self.generacion_actual.duracion_minutos = duracion
        except Exception as e:
            logger.warning(f"No se pudo calcular duración: {e}")
        
        # Guardar
        self._guardar_generacion()
    
    def _guardar_generacion(self):
        """Guardar generación a archivo JSON."""
        if not self.generacion_actual:
            return
        
        filename = f"gen_{self.generacion_actual.generacion_id}.json"
        filepath = self.gen_dir / filename
        
        filepath.write_text(self.generacion_actual.to_json())
        logger.info(f"✓ Generación guardada: {filepath}")
    
    def cargar_ultimas_generaciones(self, n: int = 10) -> list[RegistroGeneracion]:
        """Cargar últimas N generaciones."""
        archivos = sorted(self.gen_dir.glob("gen_*.json"))[-n:]
        generaciones = []
        
        for archivo in archivos:
            try:
                datos = json.loads(archivo.read_text())
                metricas_dict = datos.pop("metricas", None)
                metricas = MetricasGeneracion(**metricas_dict) if metricas_dict else None
                
                gen = RegistroGeneracion(**datos)
                gen.metricas = metricas
                generaciones.append(gen)
            except Exception as e:
                logger.warning(f"No se pudo cargar {archivo}: {e}")
        
        return generaciones


# Singleton global
_gestor: GestorGeneraciones | None = None


def obtener_gestor_generaciones() -> GestorGeneraciones:
    """Obtener o crear gestor global."""
    global _gestor
    if _gestor is None:
        _gestor = GestorGeneraciones()
    return _gestor


