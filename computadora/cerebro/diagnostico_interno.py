"""
בִּינָה פְּנִימִית (Biná Pnimít) — Comprensión Interna.

Módulo de introspección que analiza el estado de runtime de Computadora:
diagnóstico de módulos, latencia, uso de recursos, salud de Sefirot.

A diferencia de monitor_sistema (Hod — percepción externa del sistema),
Biná Pnimít mira hacia ADENTRO: la propia Computadora.

Sefirá: Biná (בינה) — Pilar izquierdo, comprensión analítica.
Senderos: Biná → Jesed (análisis → acción proactiva)
           Biná → Gevurá (comprensión → restricciones informadas)
"""

from __future__ import annotations

import os
import sys
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from loguru import logger


@dataclass
class DiagnosticoModulo:
    """Estado de salud de un módulo de Computadora."""
    nombre: str
    sefira: str
    cargado: bool = False
    errores_recientes: int = 0
    ultima_actividad: float = 0.0  # monotonic timestamp
    latencia_ms: float = 0.0


@dataclass
class DiagnosticoComputadora:
    """Snapshot completo del estado interno de Computadora."""
    timestamp: str = ""
    uptime_s: float = 0.0
    ram_mb: float = 0.0
    threads_activos: int = 0
    modulos: list[DiagnosticoModulo] = field(default_factory=list)
    lollama_ok: bool = False  # Ollama health check (legacy Ollama alias)
    copilot_ok: bool = False
    gemini_ok: bool = False
    nivel_activo: str = "N1"
    sefirot_salud: dict[str, str] = field(default_factory=dict)


# Mapeo canónico módulo → Sefirá
_MODULO_SEFIRA = {
    "nlu": "Tiféret", "parseo_herramientas": "Tiféret",
    "copilot_api": "Kéter", "gemini_api": "Kéter", "meta_workflow": "Kéter",
    "modelo_discovery": "Biná", "jojma_local": "Jojmá", "diagnostico_interno": "Biná",
    "proactividad": "Jesed", "baseline_sistema": "Jesed",
    "permisos": "Gevurá", "comando_seguro": "Gevurá",
    "memoria": "Netzaj", "personalidad": "Netzaj", "perfil_linguistico": "Netzaj",
    "escucha": "Hod", "habla": "Hod", "servidor_api": "Hod",
    "orquestador": "Yesod", "herramientas": "Yesod", "eventos": "Yesod",
    "ventana_principal": "Maljut", "vida_autonoma": "Maljut", "fsm_golem": "Maljut",
    "ciclo_circadiano": "Da'at", "perceptor": "Da'at",
}


class DiagnosticoInterno:
    """Motor de introspección de Computadora."""

    def __init__(self):
        self._inicio = time.monotonic()
        self._lock = threading.Lock()
        self._errores_por_modulo: dict[str, int] = {}

    def registrar_error(self, modulo: str) -> None:
        """Registra un error en un módulo para tracking de salud."""
        with self._lock:
            self._errores_por_modulo[modulo] = (
                self._errores_por_modulo.get(modulo, 0) + 1
            )

    def diagnosticar(self) -> DiagnosticoComputadora:
        """Ejecuta diagnóstico completo del estado interno."""
        diag = DiagnosticoComputadora(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            uptime_s=time.monotonic() - self._inicio,
            threads_activos=threading.active_count(),
        )

        # RAM del proceso
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            diag.ram_mb = proc.memory_info().rss / (1024 * 1024)
        except Exception as e:  # RF-167
            logger.debug("psutil no disponible para RAM: %s", e)

        # RF-350: Checks de cerebros EN PARALELO con timeout 2s total
        from concurrent.futures import ThreadPoolExecutor, as_completed
        checks = {"ollama": self._check_ollama, "copilot": self._check_copilot, "gemini": self._check_gemini}
        resultados_checks = {"ollama": False, "copilot": False, "gemini": False}
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futuros = {pool.submit(fn): nombre for nombre, fn in checks.items()}
                for fut in as_completed(futuros, timeout=2.0):
                    nombre = futuros[fut]
                    try:
                        resultados_checks[nombre] = fut.result(timeout=0.1)
                    except Exception as e:  # RF-167
                        logger.debug("Check %s falló: %s", nombre, e)
        except Exception as e:
            logger.debug("Timeout en checks de cerebros: %s", e)
        diag.lollama_ok = resultados_checks["ollama"]
        diag.copilot_ok = resultados_checks["copilot"]
        diag.gemini_ok = resultados_checks["gemini"]

        # Determinar nivel activo
        if diag.lollama_ok:
            diag.nivel_activo = "N2"
        elif diag.copilot_ok or diag.gemini_ok:
            diag.nivel_activo = "N3"
        else:
            diag.nivel_activo = "N1"

        # Módulos cargados
        for nombre, sefira in _MODULO_SEFIRA.items():
            cargado = any(
                nombre in m for m in sys.modules if "computadora" in m
            )
            mod = DiagnosticoModulo(
                nombre=nombre,
                sefira=sefira,
                cargado=cargado,
                errores_recientes=self._errores_por_modulo.get(nombre, 0),
            )
            diag.modulos.append(mod)

        # Salud por Sefirá (agregada)
        sefirot_errores: dict[str, int] = {}
        sefirot_cargados: dict[str, int] = {}
        sefirot_total: dict[str, int] = {}
        for mod in diag.modulos:
            sefirot_errores[mod.sefira] = sefirot_errores.get(mod.sefira, 0) + mod.errores_recientes
            sefirot_total[mod.sefira] = sefirot_total.get(mod.sefira, 0) + 1
            if mod.cargado:
                sefirot_cargados[mod.sefira] = sefirot_cargados.get(mod.sefira, 0) + 1

        for sefira in sefirot_total:
            total = sefirot_total[sefira]
            cargados = sefirot_cargados.get(sefira, 0)
            errores = sefirot_errores.get(sefira, 0)
            if errores > 3:
                diag.sefirot_salud[sefira] = "crítico"
            elif cargados < total:
                diag.sefirot_salud[sefira] = "parcial"
            else:
                diag.sefirot_salud[sefira] = "sano"

        return diag

    def resumen_texto(self) -> str:
        """Genera un resumen legible del diagnóstico para respuesta de voz."""
        d = self.diagnosticar()
        partes = [
            f"Llevo {d.uptime_s / 60:.0f} minutos activo.",
            f"Usando {d.ram_mb:.0f} MB de RAM con {d.threads_activos} hilos.",
        ]

        # Cerebros
        cerebros = []
        if d.lollama_ok:
            cerebros.append("Ollama")
        if d.copilot_ok:
            cerebros.append("Copilot")
        if d.gemini_ok:
            cerebros.append("Gemini")
        if cerebros:
            partes.append(f"Cerebros activos: {', '.join(cerebros)}.")
        else:
            partes.append("Operando solo con reglas locales, señor.")

        # Sefirot con problemas
        criticos = [s for s, v in d.sefirot_salud.items() if v == "crítico"]
        if criticos:
            partes.append(f"Sefirot con problemas: {', '.join(criticos)}.")
        else:
            partes.append("Todas las Sefirot operando con normalidad.")

        return " ".join(partes)

    @staticmethod
    def _check_ollama() -> bool:
        """Verifica Ollama en puerto 1234."""
        try:
            import httpx
            r = httpx.get("http://127.0.0.1:1234/v1/models", timeout=2)
            return r.status_code == 200
        except Exception as e:  # RF-167
            logger.debug("Ollama check falló: %s", e)
            return False

    @staticmethod
    def _check_copilot() -> bool:
        try:
            from computadora.cerebro.copilot_api import obtener_cerebro_copilot
            return obtener_cerebro_copilot().esta_autenticado()
        except Exception as e:  # RF-167
            logger.debug("Copilot check falló: %s", e)
            return False

    @staticmethod
    def _check_gemini() -> bool:
        try:
            from computadora.cerebro.gemini_api import obtener_cerebro_gemini
            return obtener_cerebro_gemini().esta_disponible()
        except Exception as e:  # RF-167
            logger.debug("Gemini check falló: %s", e)
            return False


# ═══════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════

_instancia: DiagnosticoInterno | None = None


def obtener_diagnostico_interno() -> DiagnosticoInterno:
    """Retorna la instancia singleton de DiagnosticoInterno."""
    global _instancia
    if _instancia is None:
        _instancia = DiagnosticoInterno()
    return _instancia


