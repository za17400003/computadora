from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Callable, Dict, List

from loguru import logger


class TemaVisualTipo(Enum):
    """Tipos de tema visual del orbe.

    CLASICO conserva el valor "legacy" a propósito: es la clave persistida en
    datos/maljut_dev_config.json de instalaciones existentes; cambiarla
    invalidaría esos archivos sin ningún beneficio real.
    """
    CLASICO = "legacy"

    @classmethod
    def from_str(cls, value: str) -> "TemaVisualTipo":
        return cls.CLASICO


class VisualTheme:
    """Contrato de tema visual para el orbe de Computadora.

    Un tema decide CÓMO se ve el orbe (partículas, anillos, núcleo, colores)
    sin que OrbeComputadora necesite saber qué tema está activo. Para agregar
    un tema nuevo: heredar de esta clase e implementar renderizar() y
    manejar_cambio_estado(), luego registrarlo con ThemeFactory.registrar_tema().
    """

    def __init__(self, orbe: Any | None = None):
        self.orbe = orbe
        self.tipo = TemaVisualTipo.CLASICO
        self.name = "VisualTheme"

    def initialize(self) -> None:
        pass

    def on_demo_start(self) -> None:
        pass

    def on_demo_end(self) -> None:
        pass

    def update(self, delta_t: float) -> None:
        """Llamado una vez por frame, antes de renderizar."""
        pass

    def manejar_cambio_estado(self, estado: str) -> None:
        """Llamado cada vez que OrbeComputadora cambia de estado (FSM)."""
        pass

    def renderizar(self, painter, cx: int, cy: int, brillo: float, color_primario, color_secundario) -> None:
        """Dibuja anillos/núcleo/partículas/letras/emet. No dibuja el chrome
        compartido del orbe (indicadores de herramientas, ripple, indicador de
        nivel, glow de proximidad) — eso lo sigue dibujando OrbeComputadora
        después de llamar a este método, igual para cualquier tema."""
        pass


class ClasicoTheme(VisualTheme):
    """Tema clásico: partículas, anillos sagrados y zonas táctiles.

    Es el único tema real hoy. Implementación tipo "strangler fig": delega a
    los métodos de dibujo que ya existen en OrbeComputadora (a su vez,
    funciones puras en dibujante_orbe.py, ya desacopladas) en vez de duplicar
    su lógica aquí. Mover físicamente ese estado (partículas, zona táctil,
    color alquímico, etc.) a esta clase queda como limpieza interna futura,
    una vez que la interfaz de temas esté probada en uso real.
    """

    def __init__(self, orbe: Any | None = None):
        super().__init__(orbe)
        self.tipo = TemaVisualTipo.CLASICO
        self.name = "ClasicoTheme"

    def initialize(self) -> None:
        logger.debug("Tema visual cargado: ClasicoTheme")

    def renderizar(self, painter, cx: int, cy: int, brillo: float, color_primario, color_secundario) -> None:
        orbe = self.orbe
        if orbe is None:
            return

        from computadora.interfaz.dibujante_orbe import (
            dibujar_anillos_con_recursos_optimizado,
            dibujar_particulas_con_fractales,
            DrawState,
        )
        from computadora.interfaz.ventana_principal import EtapaAlquimica

        draw_state_anillos = DrawState(
            escala=orbe._escala,
            fase=orbe._fase,
            rot_anillo1=orbe._rot_anillo1,
            rot_anillo2=orbe._rot_anillo2,
            rot_letras=orbe._rot_letras,
            particulas=orbe._particulas,
            indicadores_herramientas=orbe._indicadores_herramientas,
            cerebro_nivel=orbe._cerebro_nivel or "nivel1",
            patron_sagrado=orbe._patron_sagrado,
            patron_progreso=max(0, orbe._patron_timer / max(1, orbe._patron_duracion)) if orbe._patron_duracion > 0 else 0,
            etapa_alquimica=orbe._etapa_alquimica.value,
            carga_emocional=getattr(getattr(orbe, 'personalidad', None), '_rasgos', {}).get('energia', 0.5),
            morph_factor=getattr(orbe, '_morph_factor', 0.0),
        )
        dibujar_anillos_con_recursos_optimizado(
            painter, cx, cy, brillo, color_primario, draw_state_anillos,
            cpu=orbe._cpu_actual, ram=orbe._ram_actual, gpu=orbe._gpu_actual, disco=orbe._disk_actual,
            gpu_motor=getattr(orbe, '_gpu_motor_actual', 'desconocido'),
        )

        if orbe._etapa_alquimica in (EtapaAlquimica.CITRINITAS, EtapaAlquimica.RUBEDO):
            dibujar_particulas_con_fractales(painter, cx, cy, color_secundario, orbe._draw_state())
        else:
            orbe._dibujar_particulas(painter, cx, cy, color_secundario)

        en_movimiento = orbe._arrastrando or abs(orbe._impulso_vx) > 0.5 or abs(orbe._impulso_vy) > 0.5
        if not en_movimiento:
            orbe._dibujar_letras_orbitantes(painter, cx, cy, brillo, color_secundario)

        orbe._dibujar_nucleo(painter, cx, cy, brillo, color_primario, color_secundario)

        emet_brillo = 0.3 if orbe._estado == "idle" else brillo
        orbe._dibujar_emet(painter, cx, cy, emet_brillo, color_secundario)


class ThemeFactory:
    """Factory y registry para temas visuales.

    Provee: crear_tema(), listar_temas(), registrar_tema(), eliminar_tema(), builtin/custom separation.
    """

    # Registry: name -> callable(orbe=None) -> VisualTheme
    _registry: Dict[str, Callable[[Any | None], VisualTheme]] = {}
    _builtin_names = {"ClasicoTheme"}

    # Inicializar registry con temas por defecto
    @classmethod
    def _ensure_defaults(cls):
        if not cls._registry:
            cls._registry["ClasicoTheme"] = lambda orbe=None: ClasicoTheme(orbe)

    @classmethod
    def crear_tema(cls, tipo: TemaVisualTipo | str | None = None, orbe: Any | None = None) -> VisualTheme:
        cls._ensure_defaults()

        if isinstance(tipo, TemaVisualTipo):
            tipo = tipo.value

        if isinstance(tipo, str) and tipo:
            # Intentar match por nombre exacto o por tipo value
            factory = cls._registry.get(tipo)
            if factory:
                return factory(orbe)
            # Match por lower name
            for key, f in cls._registry.items():
                if key.lower() == tipo.lower() or key.lower() == tipo.replace(' ', '').lower():
                    return f(orbe)

        # None o desconocido → tema clásico (default)
        return ClasicoTheme(orbe)

    @classmethod
    def listar_temas(cls) -> List[str]:
        cls._ensure_defaults()
        return list(cls._registry.keys())

    @classmethod
    def registrar_tema(cls, name: str, factory: Callable[[Any | None], VisualTheme] | None = None) -> bool:
        """Registra un tema dinámico. No sobrescribe builtins."""
        cls._ensure_defaults()
        if not name or not isinstance(name, str):
            return False
        if name in cls._builtin_names:
            return False
        if factory is None:
            # Crear factory que genere VisualTheme con custom name
            def _factory(orbe=None):
                t = VisualTheme(orbe)
                t.name = name
                return t
            factory = _factory
        cls._registry[name] = factory
        logger.info(f"Tema registrado dinámicamente: {name}")
        return True

    @classmethod
    def eliminar_tema(cls, name: str) -> bool:
        cls._ensure_defaults()
        if not name or name in cls._builtin_names:
            logger.debug(f"No se puede eliminar tema builtin o inválido: {name}")
            return False
        if name in cls._registry:
            del cls._registry[name]
            logger.info(f"Tema eliminado: {name}")
            return True
        return False

    @classmethod
    def es_builtin(cls, name: str) -> bool:
        cls._ensure_defaults()
        return name in cls._builtin_names

    @classmethod
    def listar_custom(cls) -> List[str]:
        cls._ensure_defaults()
        return [n for n in cls._registry.keys() if n not in cls._builtin_names]


# Inicializar defaults al importar
ThemeFactory._ensure_defaults()
