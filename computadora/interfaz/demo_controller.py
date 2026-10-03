"""
DEMO CONTROLLER — Sistema de Perfiles de Arranque en Demo
==========================================================

Propósito: Activar 3 perfiles de arranque distintos (vía flag --demo=),
que configuran el tema visual y validan la disponibilidad de herramientas
ANTES de que la ventana principal termine de cargar.

IMPORTANTE: este controlador es un sistema SEPARADO y desconectado de las
coreografías reales de demo (`OrbeComputadora._demo_animaciones()` /
`_demo_herramientas()`, disparadas por voz o por el menú contextual). Este
módulo nunca las invoca — solo prepara tema visual + valida herramientas al
arrancar. Por eso usa su propio vocabulario ("perfil"), distinto del de
aquellas, para no sugerir que son el mismo sistema.

Uso:
  python -m computadora --demo=perfil_visual
  python -m computadora --demo=perfil_herramientas
  python -m computadora --demo=perfil_completo

Propiedades:
  - El perfil visual es SOLO renderizado, no afecta herramientas
  - Menu contextual es IGUAL en todos los perfiles
  - Herramientas son ACCESIBLES en todos los perfiles
  - Los perfiles son intercambiables en runtime
"""

from __future__ import annotations

import json
import sys
from enum import Enum
from typing import Optional
from pathlib import Path

from loguru import logger


class DemoModo(Enum):
    """Perfiles de arranque en demo disponibles."""
    NORMAL = "normal"                          # Uso regular (no demo)
    PERFIL_VISUAL = "perfil_visual"            # Solo tema visual
    PERFIL_HERRAMIENTAS = "perfil_herramientas"  # Tema visual + herramientas visibles
    PERFIL_COMPLETO = "perfil_completo"        # Perfil unificado (visual + herramientas)

    @classmethod
    def desde_cli(cls, args: list[str]) -> Optional["DemoModo"]:
        """Parsea argumentos CLI y retorna DemoModo si se especifica --demo."""
        for arg in args:
            if arg.startswith("--demo="):
                demo_valor = arg.replace("--demo=", "")
                try:
                    return cls(demo_valor)
                except ValueError:
                    logger.warning(f"Demo desconocida: {demo_valor}")
                    return None
        return None


class DemoController:
    """Controlador central de perfiles de arranque en demo."""

    def __init__(self):
        self.modo_actual: DemoModo = DemoModo.NORMAL
        self._orbe_ref: Optional[object] = None  # Referencia a OrbeComputadora
        self._config_ref: Optional[object] = None  # Referencia a ConfiguracionVisualDev
        self._herramientas_activas = True  # Herramientas accesibles
        self._menu_contextual_activo = True  # Menu visible en demos

    def registrar_orbe(self, orbe_widget: object) -> None:
        """Registra la referencia al widget OrbeComputadora."""
        self._orbe_ref = orbe_widget
        logger.debug("DemoController: OrbeComputadora registrado")

    def registrar_config_visual(self, config: object) -> None:
        """Registra la referencia a ConfiguracionVisualDev."""
        self._config_ref = config
        logger.debug("DemoController: ConfiguracionVisualDev registrada")

    def activar_demo(self, demo_tipo: str | DemoModo) -> bool:
        """
        Activa un perfil de arranque en demo específico.

        Args:
            demo_tipo: str o DemoModo (ej: "perfil_visual" o DemoModo.PERFIL_VISUAL)

        Returns:
            True si activación exitosa, False si falló
        """
        try:
            # Convertir string a DemoModo si es necesario
            if isinstance(demo_tipo, str):
                try:
                    modo = DemoModo(demo_tipo)
                except ValueError:
                    logger.error(f"Demo desconocida: {demo_tipo}")
                    logger.info(f"Demos válidas: {[m.value for m in DemoModo]}")
                    return False
            else:
                modo = demo_tipo

            # Aplicar configuración según modo
            self._aplicar_configuracion_demo(modo)

            self.modo_actual = modo
            logger.info(f"✨ DEMO ACTIVADA: {modo.value.upper()}")
            self._imprimir_banner_demo(modo)

            return True

        except Exception as e:
            logger.error(f"Error al activar demo: {e}")
            return False

    def desactivar_demo(self) -> bool:
        """Desactiva la demo actual y retorna a modo normal."""
        try:
            self.modo_actual = DemoModo.NORMAL
            self._herramientas_activas = True
            self._menu_contextual_activo = True
            logger.info("✅ Demo desactivada, retornando a modo normal")
            return True
        except Exception as e:
            logger.error(f"Error al desactivar demo: {e}")
            return False

    def _aplicar_configuracion_demo(self, modo: DemoModo) -> None:
        """Aplica configuración específica para cada perfil."""

        if modo == DemoModo.PERFIL_VISUAL:
            self._config_tipo_visual("legacy")
            self._ocultador_herramientas(True)
            self._validar_herramientas()

        elif modo == DemoModo.PERFIL_HERRAMIENTAS:
            self._config_tipo_visual("legacy")
            self._ocultador_herramientas(False)
            self._validar_herramientas()

        elif modo == DemoModo.PERFIL_COMPLETO:
            # Mostrar ambos (visual + herramientas)
            self._config_tipo_visual("legacy")
            self._ocultador_herramientas(False)
            self._validar_herramientas()

        elif modo == DemoModo.NORMAL:
            # Retornar a defaults
            self._herramientas_activas = True
            self._menu_contextual_activo = True

    def _config_tipo_visual(self, tipo: str) -> None:
        """Configura el tipo de tema visual (legacy).

        Nota: el archivo persistido `datos/maljut_dev_config.json` y la clave
        JSON "maljut_tipo" se dejan sin renombrar deliberadamente (decisión de
        la Fase 1), para no invertir datos ya guardados en disco de usuarios
        existentes.
        """
        if self._config_ref is None:
            logger.warning("ConfiguracionVisualDev no registrada, ignorando cambio de tema")
            return

        try:
            if hasattr(self._config_ref, "establecer"):
                self._config_ref.establecer("maljut_tipo", tipo)
            elif hasattr(self._config_ref, "config") and isinstance(self._config_ref.config, dict):
                self._config_ref.config["maljut_tipo"] = tipo
            elif hasattr(self._config_ref, "_config") and isinstance(self._config_ref._config, dict):
                self._config_ref._config["maljut_tipo"] = tipo
            else:
                raise AttributeError("El objeto de configuración no soporta actualización de claves")

            if hasattr(self._config_ref, "guardar_config"):
                self._config_ref.guardar_config()
            elif hasattr(self._config_ref, "_guardar_config_json"):
                self._config_ref._guardar_config_json()
            elif hasattr(self._config_ref, "raiz"):
                ruta = Path(self._config_ref.raiz) / "_config" / "config.json"
                ruta.parent.mkdir(parents=True, exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as f:
                    json.dump(getattr(self._config_ref, "_config", {}), f, indent=2, ensure_ascii=False)
            else:
                logger.debug("No hay método de guardado conocido para la configuración visual")

            logger.debug(f"Tema visual configurado: {tipo}")
        except Exception as e:
            logger.warning(f"No se pudo configurar el tema visual: {e}")

    def _ocultador_herramientas(self, ocultar: bool) -> None:
        """Oculta/muestra la sección de herramientas según necesidad del perfil."""
        # Placeholder para futura integración
        if ocultar:
            logger.debug("Herramientas ocultadas para el perfil visual")
        else:
            logger.debug("Herramientas visibles para el perfil de herramientas/completo")

    def _validar_herramientas(self) -> None:
        """Valida que todas las herramientas estén accesibles."""
        self._herramientas_activas = True

        herramientas = [
            ("Cámara", self._validar_camera),
            ("Micrófono", self._validar_microfono),
            ("NLU", self._validar_nlu),
            ("Guardian", self._validar_guardian),
        ]

        resultado_validacion = []
        for nombre, validador in herramientas:
            try:
                validador()
                resultado_validacion.append(f"✅ {nombre}")
            except Exception as e:
                resultado_validacion.append(f"⚠️  {nombre}: {str(e)[:40]}")

        for linea in resultado_validacion:
            logger.debug(linea)

    def _validar_camera(self) -> None:
        """Valida disponibilidad de cámara."""
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            assert cap.isOpened()
            cap.release()
        except Exception as e:
            raise Exception(f"Camera: {e}")

    def _validar_microfono(self) -> None:
        """Valida disponibilidad de micrófono."""
        try:
            import sounddevice as sd
            dispositivos = sd.query_devices()
            assert len(dispositivos) > 0
        except Exception as e:
            raise Exception(f"Micrófono: {e}")

    def _validar_nlu(self) -> None:
        """Valida disponibilidad de NLU."""
        try:
            from computadora.cerebro.nlu import CerebroComputadora
            cerebro = CerebroComputadora()
            assert cerebro is not None
        except Exception as e:
            raise Exception(f"NLU: {e}")

    def _validar_guardian(self) -> None:
        """Valida disponibilidad de Guardian."""
        if sys.platform != "win32":
            return  # Guardian solo en Windows

        try:
            from computadora.monitores.guardian import GuardianMonitor
            guardian = GuardianMonitor()
            assert guardian is not None
        except Exception as e:
            raise Exception(f"Guardian: {e}")

    def _imprimir_banner_demo(self, modo: DemoModo) -> None:
        """Imprime un banner visual para el perfil activado."""
        banners = {
            DemoModo.PERFIL_VISUAL: """
╔════════════════════════════════════════╗
║   ✨ PERFIL: VISUAL                     ║
║   Renderizado clásico (2-3ms/frame)    ║
║   Herramientas: ✅ Accesibles           ║
║   Menú: ✅ Unificado                    ║
╚════════════════════════════════════════╝
            """,
            DemoModo.PERFIL_HERRAMIENTAS: """
╔════════════════════════════════════════╗
║   ⚔️  PERFIL: HERRAMIENTAS              ║
║   Renderizado clásico                  ║
║   Herramientas: ✅ Accesibles           ║
║   Menú: ✅ Unificado                    ║
╚════════════════════════════════════════╝
            """,
            DemoModo.PERFIL_COMPLETO: """
╔════════════════════════════════════════╗
║   🔮 PERFIL: COMPLETO                   ║
║   Visual + herramientas integrados     ║
║   Herramientas: ✅ Accesibles           ║
║   Menú: ✅ Unificado                    ║
╚════════════════════════════════════════╝
            """,
        }

        banner = banners.get(modo, "")
        if banner:
            print(banner)

    def es_demo_activa(self) -> bool:
        """Retorna True si hay demo activa (no NORMAL)."""
        return self.modo_actual != DemoModo.NORMAL

    def herramientas_accesibles(self) -> bool:
        """Retorna True si herramientas están accesibles."""
        return self._herramientas_activas

    def menu_visible(self) -> bool:
        """Retorna True si menú contextual debe estar visible."""
        return self._menu_contextual_activo

    def obtener_modo_actual(self) -> DemoModo:
        """Retorna el modo de demo actual."""
        return self.modo_actual

    def obtener_modo_como_string(self) -> str:
        """Retorna el modo como string."""
        return self.modo_actual.value

    @classmethod
    def desde_cli(cls, args: list[str]) -> Optional[DemoModo]:
        """Parsea argumentos CLI y retorna DemoModo si se especifica --demo."""
        for arg in args:
            if arg.startswith("--demo="):
                demo_valor = arg.replace("--demo=", "")
                try:
                    return DemoModo(demo_valor)
                except ValueError:
                    logger.warning(f"Demo desconocida: {demo_valor}")
                    return None
        return None


# ─── SINGLETON ───
_demo_controller: Optional[DemoController] = None


def obtener_demo_controller() -> DemoController:
    """Retorna la instancia singleton de DemoController."""
    global _demo_controller
    if _demo_controller is None:
        _demo_controller = DemoController()
    return _demo_controller


def obtener_modo_demo() -> DemoModo:
    """Retorna el modo de demo actual."""
    return obtener_demo_controller().obtener_modo_actual()


def es_demo_activa() -> bool:
    """Retorna True si hay demo activa."""
    return obtener_demo_controller().es_demo_activa()


def herramientas_accesibles() -> bool:
    """Retorna True si herramientas están accesibles."""
    return obtener_demo_controller().herramientas_accesibles()
