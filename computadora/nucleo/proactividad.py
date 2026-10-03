"""
חסד (Jesed) — Misericordia. El brazo derecho que da sin que le pidan.
Motor de Proactividad — La Iniciativa de la Computadora.

Hilo daemon que ejecuta chequeos periódicos y genera sugerencias
sin que el usuario pregunte. Como JARVIS: anticipa, alerta, asiste.
Equilibrado por Gevurá (seguridad) en Tiféret (nlu.py).

דעת (Da'at) — Conocimiento Oculto. Ciclo Circadiano Adaptativo.
COMPUTADORA percibe el ritmo de su amo y sincroniza su consciencia.
(Clase CicloCircadiano ahora vive en nucleo/ciclo_circadiano.py)
"""

from __future__ import annotations

import datetime
import json
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger

# METATRÓN — Optimización de recursos (RUBEDO Phase 2)
from computadora.geometria.flower_of_life import FlowerOfLife

if TYPE_CHECKING:
    from computadora.utilidades.windows import ContextoPantalla
    from computadora.habilidades.monitor_sistema import MonitorSistema
    from computadora.habilidades.baseline_sistema import BaselineSistema


# ═══════════════════════════════════════════════
# TIPOS
# ═══════════════════════════════════════════════

class Sugerencia(NamedTuple):
    tipo: str      # 'buenos_dias', 'recordatorio', 'alerta', 'clipboard', 'inactividad', 'error', 'salud'
    texto: str


# ═══════════════════════════════════════════════
# CICLO CIRCADIANO — Re-exportado desde nucleo/ciclo_circadiano.py (Da'at)
# ═══════════════════════════════════════════════

from computadora.nucleo.ciclo_circadiano import (
    CicloCircadiano,
    obtener_fase_actual,
    obtener_ciclo_circadiano,
    _set_ciclo_global,
)

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_RECORDATORIOS_ARCHIVO = _DATOS_DIR / "recordatorios.json"
_TAREAS_ARCHIVO = _DATOS_DIR / "tareas.json"
_PATRONES_USO_ARCHIVO = _DATOS_DIR / "patrones_uso.json"
_ESTADO_PROACTIVO_ARCHIVO = _DATOS_DIR / "proactividad_estado.json"

# Cooldown global: mínimo 5 minutos entre sugerencias
_COOLDOWN_GLOBAL = 300
# Cooldown de inactividad: 30 min
_UMBRAL_INACTIVIDAD_MIN = 30
# Máximo de "¿Todo bien?" sin respuesta antes de descanso_guardian
_MAX_INACTIVIDAD_SIN_RESPUESTA = 2


class MotorProactividad(QThread):
    """Hilo que monitorea y emite sugerencias proactivas."""

    sugerencia_lista = pyqtSignal(str, str)  # (tipo, mensaje)
    fase_cambio = pyqtSignal(str)  # Emitida cuando cambia la fase circadiana

    def __init__(
        self,
        contexto_pantalla: ContextoPantalla | None = None,
        monitor_sistema: MonitorSistema | None = None,
        baseline: BaselineSistema | None = None,
    ):
        super().__init__()
        self.setObjectName("MotorProactividad")
        self.daemon = True

        self._contexto = contexto_pantalla
        self._monitor = monitor_sistema
        self._baseline = baseline

        self._detener = False
        self._modo_silencio = False
        self._silencio_hasta: float = 0
        self._ultima_sugerencia: float = 0
        self._ya_saludo_hoy: str = ""  # fecha ISO de último saludo
        self._ultimo_clipboard: str = ""
        self._ultimo_error_titulo: str = ""
        self._alertas_sistema_activas: bool = True
        # FIX: hay_alerta() hace hasta 3 barridos completos de
        # psutil.process_iter() (ram_sin_propios → _ram_es_entorno_normal →
        # diagnosticar_proceso_anomalo). El cooldown global (_COOLDOWN_GLOBAL)
        # solo se reinicia cuando SE EMITE una sugerencia, así que en idle
        # prolongado (sin sugerencias) el ciclo de ~10s dejaba de estar
        # throttleado y este check pesado corría sin parar, causando
        # microcortes periódicos. Se le da su propio intervalo independiente.
        self._ultimo_chequeo_alertas: float = 0
        self._intervalo_chequeo_alertas: float = 60.0

        # Keter: meta-cognición
        self._ultimo_autodiag: float = 0
        self._intervalo_autodiag: float = 1800  # 30 minutos

        # Emet: integridad de la verdad
        self._ultimo_emet_check: float = 0
        self._intervalo_emet: float = 3600  # 1 hora

        # דעת Da'at — Ciclo Circadiano Adaptativo
        try:
            self.ciclo = CicloCircadiano()
            _set_ciclo_global(self.ciclo)
        except Exception as e:
            logger.error(f"Error inicializando CicloCircadiano: {e}")
            self.ciclo = None
        
        # ⌛ METATRÓN Phase 2: Flor de la Vida — Balance automático de recursos (Φ)
        self.flor_vida = FlowerOfLife()
        self._ultimo_balance_check: float = 0
        self._intervalo_balance: float = 60  # Verificar cada minuto
        
        self._inactividades_sin_respuesta: int = 0
        self._fase_anterior: str = ""
        self._ya_sugirio_salud_hoy: bool = False
        self._ultimo_bienestar: float = 0
        self._intervalo_bienestar: float = 14400  # 4 horas

        # FP-108: Estado proactivo persistente — equilibrio y sabiduría
        # Cooldowns por tema para evitar repetición entre reinicios
        self._temas_emitidos_hoy: dict[str, str] = {}  # {tema: fecha_iso}
        self._cargar_estado_proactivo()

        # RF-328: Presencia visual del propietario (cámara)
        self._propietario_visto_ts: float = 0.0  # última vez que la cámara vio al propietario

        self._checks = [
            self._check_buenos_dias,
            self._check_recordatorios_proximos,
            self._check_alertas_sistema,
            self._check_salud_computadora,
            self._check_emet_integridad,
            self._check_patron_repetido,
            self._check_bienestar,
            self._check_clipboard_inteligente,
            self._check_inactividad,
            self._check_error_en_pantalla,
            self._check_salud_circadiana,
            self._check_balance_recursos_phi,  # METATRÓN Phase 2: Flor de la Vida
        ]

        logger.info("MotorProactividad creado — COMPUTADORA tiene iniciativa")

    # ─── Persistencia de estado (FP-108: Equilibrio/Sabiduría) ──

    def _cargar_estado_proactivo(self):
        """Carga estado persistente: qué temas ya se emitieron hoy."""
        hoy = datetime.date.today().isoformat()
        try:
            if _ESTADO_PROACTIVO_ARCHIVO.exists():
                data = json.loads(_ESTADO_PROACTIVO_ARCHIVO.read_text(encoding="utf-8"))
                temas = data.get("temas_emitidos", {})
                # Solo restaurar temas del día actual
                self._temas_emitidos_hoy = {
                    k: v for k, v in temas.items() if v == hoy
                }
                if "salud" in self._temas_emitidos_hoy:
                    self._ya_sugirio_salud_hoy = True
                if "buenos_dias" in self._temas_emitidos_hoy:
                    self._ya_saludo_hoy = hoy
                logger.debug(f"Estado proactivo cargado: {len(self._temas_emitidos_hoy)} temas activos hoy")
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"No pude cargar estado proactivo: {e}")

    def _guardar_estado_proactivo(self):
        """Persiste estado al disco — sobrevive reinicios de la Computadora."""
        try:
            _DATOS_DIR.mkdir(parents=True, exist_ok=True)
            data = {"temas_emitidos": self._temas_emitidos_hoy}
            contenido = json.dumps(data, ensure_ascii=False, indent=2)
            tmp = _ESTADO_PROACTIVO_ARCHIVO.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(contenido)
            tmp.replace(_ESTADO_PROACTIVO_ARCHIVO)
        except OSError as e:
            logger.debug(f"No pude guardar estado proactivo: {e}")

    def _registrar_tema_emitido(self, tema: str):
        """Marca un tema como ya dicho hoy y persiste."""
        self._temas_emitidos_hoy[tema] = datetime.date.today().isoformat()
        self._guardar_estado_proactivo()

    def _tema_ya_dicho_hoy(self, tema: str) -> bool:
        """¿Ya se dijo este tema hoy? Sabiduría: no repetir."""
        hoy = datetime.date.today().isoformat()
        return self._temas_emitidos_hoy.get(tema) == hoy

    # ─── Control ────────────────────────────────

    def detener(self):
        self._detener = True

    def activar_silencio(self, minutos: int = 30):
        """El usuario pidió no ser molestado."""
        self._modo_silencio = True
        self._silencio_hasta = time.time() + (minutos * 60)
        logger.info(f"Modo silencio activado por {minutos} minutos")

    def desactivar_silencio(self):
        self._modo_silencio = False
        self._silencio_hasta = 0
        logger.info("Modo silencio desactivado")

    def desactivar_alertas_sistema(self):
        """El usuario no quiere más alertas del sistema."""
        self._alertas_sistema_activas = False
        logger.info("Alertas del sistema desactivadas por el usuario")

    def activar_alertas_sistema(self):
        """El usuario quiere alertas del sistema de nuevo."""
        self._alertas_sistema_activas = True
        logger.info("Alertas del sistema reactivadas")

    def registrar_respuesta_usuario(self):
        """El amo respondió — resetear contador de inactividad y registrar interacción."""
        self._inactividades_sin_respuesta = 0
        self.ciclo.registrar_interaccion()
        # Si estábamos en descanso_guardian, despertar
        if self.ciclo._fase == "descanso_guardian":
            self.ciclo.forzar_activo()
            self.fase_cambio.emit("activo")
            logger.info("MotorProactividad: amo respondió → despertando de descanso_guardian")

    def registrar_presencia_visual(self):
        """RF-328: La cámara detectó al propietario — actualizar timestamp."""
        self._propietario_visto_ts = time.time()
        self._inactividades_sin_respuesta = 0

    # ─── Loop principal ─────────────────────────

    def run(self):
        # RF-13: Feature flag para pausar proactividad
        try:
            from computadora.nucleo.feature_flags import obtener_flag
            if not obtener_flag("proactividad"):
                logger.info("RF-13 Proactividad PAUSADA por feature flag")
                # Mantenerse en espera sin hacer nada
                while not self._detener:
                    time.sleep(10)
                return
        except Exception as e:
            logger.debug(f"Feature flag check error (no crítico): {e}")
        
        logger.info("MotorProactividad iniciado")
        # Esperar 30s al arrancar para que Ollama, monitor y subsistemas estén operativos
        for _ in range(30):
            if self._detener:
                return
            time.sleep(1)

        while not self._detener:
            try:
                self._ciclo()
            except Exception as e:
                logger.error(f"Error en ciclo proactivo: {e}")
            # Dormir 10s entre ciclos
            for _ in range(10):
                if self._detener:
                    return
                time.sleep(1)

    def _ciclo(self):
        # WI-314 BUG #5: Proteger acceso a self.ciclo
        if self.ciclo is None:
            try:
                logger.info("Reintentando inicializar CicloCircadiano...")
                self.ciclo = CicloCircadiano()
                _set_ciclo_global(self.ciclo)
            except Exception as e:
                logger.error(f"Reinicio de CicloCircadiano falló: {e}")
                return
        
        # ¿En modo silencio?
        if self._modo_silencio:
            if time.time() > self._silencio_hasta:
                self._modo_silencio = False
                logger.info("Modo silencio expiró")
            else:
                return

        # Actualizar fase circadiana y emitir si cambió
        try:
            fase = self.ciclo.fase_actual()
        except Exception as e:
            logger.error(f"Error obteniendo fase_actual: {e}")
            return
            
        if fase != self._fase_anterior:
            self._fase_anterior = fase
            try:
                self.fase_cambio.emit(fase)
            except Exception as e:
                logger.error(f"Error emitiendo fase_cambio: {e}")
            logger.info(f"CicloCircadiano: fase → {fase}")

        # ── Gevurá nocturna: suprimir sugerencias en descanso_guardian ──
        # Equilibrio Jesed↔Gevurá: de noche, Gevurá prevalece.
        # COMPUTADORA permanece alerta (monitorea) pero NO emite sugerencias
        # habladas que puedan despertar o molestar al propietario.
        if fase == "descanso_guardian":
            return

        # Reset diario
        hoy = datetime.date.today().isoformat()
        if self._ya_saludo_hoy and self._ya_saludo_hoy != hoy:
            self.ciclo.notificar_nuevo_dia()
            self._ya_sugirio_salud_hoy = False
            # FP-108: Limpiar temas del día anterior
            self._temas_emitidos_hoy = {}
            self._guardar_estado_proactivo()

        # ¿Cooldown cumplido?
        if time.time() - self._ultima_sugerencia < _COOLDOWN_GLOBAL:
            return

        # FP-014/HF-027: Si el usuario está acariciando (contacto >1s), no sugerir
        _orbe = getattr(self, '_orbe_ref', None)
        if _orbe:
            inicio = getattr(_orbe, '_tacto_continuo_inicio', 0.0)
            if inicio > 0.0 and (time.time() - inicio) > 1.0:
                return

        # Alimentar baseline con snapshot actual
        if self._baseline and self._monitor:
            try:
                snap = self._monitor.snapshot()
                _vi = self._contexto.obtener_ventana_activa() if self._contexto else None
                ventana = _vi.titulo if _vi else None  # RF-223: VentanaInfo→str
                self._baseline.registrar_lectura(snap, ventana)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        # Ejecutar checks en orden
        for check in self._checks:
            try:
                sug = check()
                if sug:
                    self.sugerencia_lista.emit(sug.tipo, sug.texto)
                    self._ultima_sugerencia = time.time()
                    return  # Solo 1 sugerencia por ciclo
            except Exception as e:
                logger.debug(f"Error en check {check.__name__}: {e}")

    # ─── Checks individuales ────────────────────

    def _check_buenos_dias(self) -> Sugerencia | None:
        """Primer saludo del día con briefing — espera a tener datos reales."""
        hoy = datetime.date.today().isoformat()
        if self._ya_saludo_hoy == hoy:
            return None
        # FP-108: También verificar estado persistido (evita saludo repetido entre reinicios)
        if self._tema_ya_dicho_hoy("buenos_dias"):
            self._ya_saludo_hoy = hoy  # sincronizar flag en memoria
            return None

        # No saludar hasta tener al menos un snapshot real del sistema
        if self._monitor:
            snap = self._monitor.snapshot()
            if not snap or not snap.get('cpu_pct'):
                return None  # Aún no hay datos reales, esperar al siguiente ciclo
        
        self._ya_saludo_hoy = hoy
        self._registrar_tema_emitido("buenos_dias")
        partes = []

        # Hora del día → saludo apropiado
        hora = datetime.datetime.now().hour
        if hora < 12:
            partes.append("Buenos días, señor")
        elif hora < 19:
            partes.append("Buenas tardes, señor")
        else:
            partes.append("Buenas noches, señor")

        # Recordatorios de hoy
        recs = self._cargar_recordatorios_hoy()
        if recs:
            if len(recs) == 1:
                partes.append(f"Tiene un recordatorio pendiente: {recs[0]}")
            else:
                partes.append(f"Tiene {len(recs)} recordatorios pendientes para hoy")

        # Tareas pendientes
        tareas = self._contar_tareas_pendientes()
        if tareas > 0:
            partes.append(f"{tareas} tarea{'s' if tareas > 1 else ''} pendiente{'s' if tareas > 1 else ''}")

        # Estado del sistema — usar datos reales del snapshot
        if self._monitor:
            alerta = self._monitor.hay_alerta()
            if alerta:
                partes.append(f"Alerta del sistema: {alerta}")
            else:
                # Reportar dato real: RAM y CPU actuales
                if snap:
                    cpu = snap.get('cpu_pct', 0)
                    ram = snap.get('ram_pct', 0)
                    partes.append(f"Sistema operativo: CPU al {cpu:.0f}%, RAM al {ram:.0f}%. Todo en orden")
                else:
                    partes.append("El sistema está en buen estado")

        # Solo mencionar baseline si tiene datos maduros (7+ días)
        if self._baseline and self._baseline.tiene_datos_suficientes():
            try:
                resumen = self._baseline.resumen()
                if resumen:
                    partes.append(resumen)
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)

        return Sugerencia('buenos_dias', ". ".join(partes))

    def _check_recordatorios_proximos(self) -> Sugerencia | None:
        """Avisa 5 min antes de un recordatorio."""
        try:
            if not _RECORDATORIOS_ARCHIVO.exists():
                return None
            recs = json.loads(_RECORDATORIOS_ARCHIVO.read_text(encoding="utf-8"))
            ahora = datetime.datetime.now()
            for r in recs:
                cuando = datetime.datetime.fromisoformat(r['cuando'])
                diff = (cuando - ahora).total_seconds()
                # Entre 4.5 y 5.5 minutos (ventana de detección de ~1 min)
                if 270 < diff < 330:
                    return Sugerencia(
                        'recordatorio',
                        f"Señor, en 5 minutos tiene un recordatorio: {r['mensaje']}"
                    )
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return None

    def _check_alertas_sistema(self) -> Sugerencia | None:
        """CPU/RAM/disco excedidos — contextualizado con perfil de actividad.
        
        WI-284: Ahora retorna alerta + sugerencia equilibradora (Gevurá + Jesed).
        """
        if not self._monitor or not self._alertas_sistema_activas:
            return None
        ahora = time.time()
        if ahora - self._ultimo_chequeo_alertas < self._intervalo_chequeo_alertas:
            return None
        self._ultimo_chequeo_alertas = ahora
        alerta = self._monitor.hay_alerta()
        if alerta:
            contexto = ""
            if self._baseline and self._baseline.tiene_datos_suficientes():
                _vi = self._contexto.obtener_ventana_activa() if self._contexto else None
                ventana = _vi.titulo if _vi else None  # RF-223: VentanaInfo→str
                from computadora.habilidades.baseline_sistema import _detectar_perfil
                perfil = _detectar_perfil(ventana)
                contexto = f" (perfil actual: {perfil})"
            
            # WI-284: Registrar alerta en matemáticas transparentes
            try:
                from computadora.cerebro.matematicas import registrar_alerta_sistema
                # Inferir tipo de alerta del texto
                if "CPU" in alerta:
                    registrar_alerta_sistema("cpu", 0, 0, True, contexto)
                elif "RAM" in alerta or "memoria" in alerta.lower():
                    registrar_alerta_sistema("ram", 0, 0, True, contexto)
                elif "disco" in alerta.lower():
                    registrar_alerta_sistema("disk", 0, 0, True, contexto)
            except Exception as e:
                logger.debug(f"No pude registrar alerta en MAT: {e}")
            
            # WI-284: Generar sugerencia positiva balanceadora (Jesed)
            sugerencia_positiva = self._generar_sugerencia_balanceadora(alerta)
            if sugerencia_positiva:
                # Emitir primero la alerta (Gevurá severa)
                self.sugerencia_lista.emit('alerta', f"Señor, alerta del sistema{contexto}: {alerta}")
                # Luego la sugerencia positiva (Jesed balanceadora)
                return sugerencia_positiva
            
            return Sugerencia('alerta', f"Señor, alerta del sistema{contexto}: {alerta}")
        return None
    
    def _generar_sugerencia_balanceadora(self, alerta: str) -> Sugerencia | None:
        """WI-284: Genera sugerencia positiva contextual para balancear alerta.
        
        Mapeo: alerta-negativa + patrones-usuario → sugerencia-positiva (Jesed).
        """
        sugerencias_por_tipo = {
            "CPU": [
                "¿Ejecuto un análisis de procesos activos?",
                "Puedo priorizar procesos críticos si lo desea.",
                "¿Inicio limpieza de cache?",
            ],
            "RAM": [
                "¿Cierro aplicaciones innecesarias?",
                "Puedo liberar memoria caché del sistema.",
                "¿Ejecuto optimización de memoria?",
            ],
            "disco": [
                "¿Identifico archivos temporales para limpiar?",
                "Puedo generar reporte de uso de disco.",
                "¿Ejecuto desfragmentación?",
            ],
        }
        
        for tipo, sugs in sugerencias_por_tipo.items():
            if tipo.lower() in alerta.lower():
                import random
                sug = random.choice(sugs)
                return Sugerencia('sugerencia_balanceadora', sug)
        
        return None

    def _check_salud_computadora(self) -> Sugerencia | None:
        """Keter: autodiagnóstico periódico cada 30 min."""
        ahora = time.time()
        if ahora - self._ultimo_autodiag < self._intervalo_autodiag:
            return None
        self._ultimo_autodiag = ahora

        try:
            from computadora.nucleo.meta_workflow import MetaWorkflow
            # FP-047 B2: Reusar instancia para evitar leak de subscripciones BusEventos
            if not hasattr(self, '_meta_workflow_inst'):
                self._meta_workflow_inst = MetaWorkflow()
            diag = self._meta_workflow_inst.autodiagnostico()

            fallos = [
                k for k, v in diag.items()
                if v == 'error' and k != 'errores_recientes'
            ]
            if fallos:
                nombres = ", ".join(fallos)
                return Sugerencia(
                    'salud',
                    f"Señor, detecté problemas en mis subsistemas: {nombres}. "
                    "Puedo intentar recuperarme si me lo indica."
                )
        except Exception as e:
            logger.debug(f"Error en autodiagnóstico: {e}")
        return None

    def _check_emet_integridad(self) -> Sugerencia | None:
        """אמת Emet: verificación periódica de integridad del manifiesto de verdad."""
        ahora = time.time()
        if ahora - self._ultimo_emet_check < self._intervalo_emet:
            return None
        self._ultimo_emet_check = ahora

        if self._tema_ya_dicho_hoy("emet_integridad"):
            return None

        try:
            from computadora.nucleo.emet import generar_manifiesto
            m = generar_manifiesto()

            problemas: list[str] = []

            # Verdad: la inscripción א debe existir
            ident = m.get("identidad", {})
            emet_val = ident.get("emet", "")
            if "א" not in emet_val:
                problemas.append("falta א en inscripción Emet")

            # Arquitectura: 10 Sefirot en Etz HaChaim
            arq = m.get("arquitectura", {})
            sefirot = arq.get("sefirot", {})
            if len(sefirot) < 10:
                problemas.append(f"solo {len(sefirot)}/10 Sefirot en Etz HaChaim")

            # Trifecta: azufre, sal, mercurio presentes (dict keys)
            trifecta = arq.get("trifecta", {})
            for esperado in ("azufre", "sal", "mercurio"):
                if esperado not in trifecta:
                    problemas.append(f"falta {esperado} en Tria Prima")

            # Génesis: 7 días creados
            genesis = m.get("genesis_biblico", [])
            if len(genesis) < 7:
                problemas.append(f"solo {len(genesis)}/7 días en Génesis")

            if problemas:
                detalle = "; ".join(problemas)
                self._registrar_tema_emitido("emet_integridad")
                return Sugerencia(
                    "salud",
                    f"Señor, la verificación de integridad אמת detectó: {detalle}. "
                    "La verdad dCOMPUTADORA puede estar incompleta."
                )
        except ImportError:
            logger.debug("Módulo emet no disponible para check de integridad")
        except Exception as e:
            logger.debug(f"Error en check Emet: {e}")
        return None

    def _check_clipboard_inteligente(self) -> Sugerencia | None:
        """Detecta URL o texto largo copiado."""
        try:
            import ctypes
            import ctypes.wintypes
            # RF-167: argtypes/restype para Win32 64-bit (evita truncar HANDLE)
            _user32 = ctypes.windll.user32
            _user32.OpenClipboard.argtypes = [ctypes.wintypes.HWND]
            _user32.OpenClipboard.restype = ctypes.wintypes.BOOL
            _user32.GetClipboardData.argtypes = [ctypes.wintypes.UINT]
            _user32.GetClipboardData.restype = ctypes.c_void_p
            _user32.CloseClipboard.argtypes = []
            _user32.CloseClipboard.restype = ctypes.wintypes.BOOL
            # Leer clipboard via Win32
            if not _user32.OpenClipboard(None):
                return None
            try:
                h = _user32.GetClipboardData(13)  # CF_UNICODETEXT
                if not h:
                    return None
                texto = ctypes.wstring_at(h)
            finally:
                _user32.CloseClipboard()

            if not texto or texto == self._ultimo_clipboard:
                return None
            self._ultimo_clipboard = texto

            # Detectar URL
            if re.match(r'https?://', texto.strip()):
                url = texto.strip()[:80]
                return Sugerencia('clipboard', f"Copiaste una URL: {url}. ¿Quieres que la abra?")

        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
        return None

    def _check_inactividad(self) -> Sugerencia | None:
        """30 min sin cambio de ventana → saludo suave.
        
        דעת Da'at: Respeta el ciclo circadiano.
        - En descanso_guardian: NO emitir (solo alertas críticas llegan aquí)
        - Tras 2 sin respuesta: entrar en descanso_guardian
        - En transición: emitir pero con tono suave
        """
        if not self._contexto:
            return None

        fase = self.ciclo.fase_actual()

        # En descanso_guardian: NO molestar con inactividad
        if fase == "descanso_guardian":
            return None

        if not self._contexto.detectar_inactividad(_UMBRAL_INACTIVIDAD_MIN):
            return None

        # RF-328: Si la cámara vio al propietario hace < 5 min, no es inactividad real
        if self._propietario_visto_ts > 0:
            segs_desde_visto = time.time() - self._propietario_visto_ts
            if segs_desde_visto < 300:  # 5 minutos
                return None  # Usuario presente físicamente, solo en silencio

        # ¿Ya se superó el máximo de intentos sin respuesta?
        self._inactividades_sin_respuesta += 1

        if self._inactividades_sin_respuesta > _MAX_INACTIVIDAD_SIN_RESPUESTA:
            # Entrar en descanso_guardian (fusión descanso + guardián)
            self.ciclo.forzar_descanso_guardian()
            self.fase_cambio.emit("descanso_guardian")
            logger.info(
                f"Inactividad sin respuesta ×{self._inactividades_sin_respuesta} "
                f"→ entrando en descanso_guardian (silencioso)"
            )
            # Vigilia silenciosa = NO hablar, solo contraer orbe y vigilar
            return None

        if fase == "transicion":
            return Sugerencia('inactividad', "Señor, ¿sigue ahí? Si necesita descansar, yo me encargo de vigilar.")
        return Sugerencia('inactividad', "¿Todo bien, señor? Lleva un rato sin actividad.")

    def _check_error_en_pantalla(self) -> Sugerencia | None:
        """Título de ventana contiene 'error'."""
        if not self._contexto:
            return None
        error = self._contexto.detectar_error_en_pantalla()
        if error and error != self._ultimo_error_titulo:
            self._ultimo_error_titulo = error
            return Sugerencia(
                'error',
                f"Detecté un error en tu pantalla: {error[:60]}. ¿Necesitas ayuda?"
            )
        return None

    # ─── Helpers ────────────────────────────────

    def _check_patron_repetido(self) -> Sugerencia | None:
        """Jesed: detecta acciones repetidas 3+ veces/semana a la misma hora."""
        try:
            ahora = datetime.datetime.now()
            hora_bloque = ahora.hour  # Agrupar por hora

            # Cargar patrones
            patrones = {}
            if _PATRONES_USO_ARCHIVO.exists():
                patrones = json.loads(_PATRONES_USO_ARCHIVO.read_text(encoding='utf-8'))

            # Registrar actividad actual (ventana activa como proxy)
            ventana = ""
            if self._contexto:
                try:
                    _vi = self._contexto.obtener_ventana_activa()
                    ventana = _vi.titulo if _vi else ""  # RF-223: VentanaInfo→str
                except Exception as e:  # RF-167
                    logger.debug("Excepcion ignorada: %s", e)

            if not ventana:
                return None

            clave = f"h{hora_bloque}_{ventana[:30].lower().strip()}"
            dia_semana = ahora.strftime('%A')

            if clave not in patrones:
                patrones[clave] = {'dias': [], 'ventana': ventana[:50], 'hora': hora_bloque, 'sugerido': False}

            registro = patrones[clave]
            if dia_semana not in registro['dias']:
                registro['dias'].append(dia_semana)
                # Mantener solo últimos 14 días de datos
                registro['dias'] = registro['dias'][-14:]

            # Persistir
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(_PATRONES_USO_ARCHIVO, patrones)

            # ¿3+ ocurrencias distintas y no sugerido aún?
            if len(set(registro['dias'])) >= 3 and not registro.get('sugerido'):
                registro['sugerido'] = True
                escribir_json_atomico(_PATRONES_USO_ARCHIVO, patrones)
                app = registro['ventana']
                return Sugerencia(
                    'patron',
                    f"Señor, noto que usa {app} frecuentemente a esta hora. "
                    "¿Quiere que lo automatice o se lo recuerde?"
                )
        except Exception as e:
            logger.debug(f"Error en check patrón: {e}")
        return None

    def _check_bienestar(self) -> Sugerencia | None:
        """Jesed: tras 4h de uso continuo, sugerir descanso (respeta Ruaj).
        FP-108: Máximo 1 vez al día para no abrumar."""
        if self._tema_ya_dicho_hoy("bienestar"):
            return None
        ahora = time.time()
        if ahora - self._ultimo_bienestar < self._intervalo_bienestar:
            return None

        # Verificar si hay interacciones recientes (uso continuo)
        try:
            ultima_interaccion = self.ciclo._ultimo_evento
            if ahora - ultima_interaccion > 3600:
                return None  # No hay uso continuo
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return None

        # Respetar Ruaj: no interrumpir si está enfocado/activo
        try:
            from computadora.memoria.personalidad import Personalidad
            _p = Personalidad()
            humor = _p.humor_actual()
            if humor in ('enfocado', 'activo', 'inspirado'):
                return None
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        self._ultimo_bienestar = ahora
        self._registrar_tema_emitido("bienestar")
        return Sugerencia(
            'bienestar',
            "Señor, lleva varias horas de actividad continua. "
            "Un descanso breve podría ser beneficioso. "
            "No paro hasta saber que está bien — ¿necesita algo antes de seguir?"
        )

    def _check_salud_circadiana(self) -> Sugerencia | None:
        """Una vez al día, sugerir mejora de salud si el horario es inestable.
        FP-108: Persistido al disco — no repite entre reinicios.
        Sabiduría: solo en fase activa matutina (6-11h)."""
        if self._ya_sugirio_salud_hoy:
            return None
        if self._tema_ya_dicho_hoy("salud"):
            self._ya_sugirio_salud_hoy = True  # sincronizar flag
            return None
        # Sabiduría: solo sugerir salud por la mañana (fase activa, 6-11h)
        hora = datetime.datetime.now().hour
        if hora < 6 or hora > 11:
            return None
        msg = self.ciclo.sugerir_mejora_salud()
        if msg:
            self._ya_sugirio_salud_hoy = True
            self._registrar_tema_emitido("salud")
            return Sugerencia('salud', msg)
        return None

    def _check_balance_recursos_phi(self) -> Sugerencia | None:
        """METATRÓN Phase 2: Verifica balance de recursos usando proporción áurea (Φ).
        
        Flor de la Vida optimiza: RAM ≈ CPU / Φ, NET ≈ (CPU + RAM) * Φ / 5
        Emite sugerencia si recursos están desbalanceados.
        """
        ahora = time.time()
        if ahora - self._ultimo_balance_check < self._intervalo_balance:
            return None
        
        self._ultimo_balance_check = ahora
        
        try:
            if not self._monitor:
                return None
            
            # Obtener métricas actuales
            cpu = self._monitor._get_cpu_percent()
            ram = self._monitor._get_ram_percent()
            net = self._monitor._get_network_percent() if hasattr(self._monitor, '_get_network_percent') else 0.0
            
            # Verificar balance usando Flor de la Vida
            is_balanced, adjustments = self.flor_vida.balance_recursos(cpu, ram, net)
            
            if not is_balanced:
                # Generar sugerencia contextual
                if not adjustments['cpu']['ok']:
                    msg = f"⚠️ CPU elevada ({cpu:.0f}%) — considera cerrar aplicaciones pesadas"
                    return Sugerencia('alerta', msg)
                elif not adjustments['ram']['ok']:
                    ideal = adjustments['ram']['ideal']
                    msg = f"💾 RAM desbalanceada ({ram:.0f}%, ideal ~{ideal:.0f}%) — optimiza uso de memoria"
                    return Sugerencia('alerta', msg)
                elif not adjustments['net']['ok']:
                    ideal = adjustments['net']['ideal']
                    msg = f"🌐 Red desbalanceada ({net:.0f}%, ideal ~{ideal:.0f}%) — verifica descargas"
                    return Sugerencia('alerta', msg)
            
            return None
        except Exception as e:
            logger.debug(f"Error en balance Φ check: {e}")
            return None

    def _cargar_recordatorios_hoy(self) -> list[str]:
        """Recordatorios programados para hoy."""
        try:
            if not _RECORDATORIOS_ARCHIVO.exists():
                return []
            recs = json.loads(_RECORDATORIOS_ARCHIVO.read_text(encoding="utf-8"))
            hoy = datetime.date.today()
            resultado = []
            for r in recs:
                cuando = datetime.datetime.fromisoformat(r['cuando'])
                if cuando.date() == hoy and cuando > datetime.datetime.now():
                    resultado.append(r['mensaje'])
            return resultado
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return []

    def _contar_tareas_pendientes(self) -> int:
        """Cuenta tareas no completadas."""
        try:
            if not _TAREAS_ARCHIVO.exists():
                return 0
            tareas = json.loads(_TAREAS_ARCHIVO.read_text(encoding="utf-8"))
            return sum(1 for t in tareas if not t.get('completada', False))
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return 0


