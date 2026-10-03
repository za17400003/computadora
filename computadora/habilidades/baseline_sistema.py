"""
נצח (Netzaj) — Victoria. Persistencia adaptativa.
Baseline del Sistema — Aprendizaje de patrones de uso.

Registra CPU/RAM por franja horaria y perfil de actividad.
Tras 7 días de datos suficientes, genera umbrales dinámicos (media ± 2σ).
Antes de eso, se usan los umbrales fijos de MonitorSistema como fallback.
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_BASELINE_ARCHIVO = _DATOS_DIR / "baseline_sistema.json"

# Mínimo de lecturas para considerar un perfil "maduro"
_MIN_LECTURAS = 50
# Días mínimos de datos antes de activar umbrales dinámicos
_DIAS_MINIMOS = 3
# Desviaciones estándar para considerar anómalo
_SIGMA_FACTOR = 2.0

# Franjas horarias
_FRANJAS = {
    'madrugada': range(0, 6),
    'mañana': range(6, 12),
    'tarde': range(12, 18),
    'noche': range(18, 24),
}

# Patrones de ventana activa → perfil de actividad
_PATRONES_PERFIL = {
    'gaming': ['steam', 'epic', 'riot', 'valorant', 'minecraft', 'genshin',
               'league', 'overwatch', 'fortnite', 'roblox'],
    'navegacion': ['chrome', 'firefox', 'edge', 'opera', 'brave', 'vivaldi'],
    'ide': ['code', 'visual studio', 'pycharm', 'intellij', 'android studio',
            'rider', 'webstorm', 'cursor'],
    'multimedia': ['vlc', 'spotify', 'netflix', 'youtube', 'discord'],
}


def _franja_actual() -> str:
    hora = datetime.now().hour
    for nombre, rango in _FRANJAS.items():
        if hora in rango:
            return nombre
    return 'noche'


def _detectar_perfil(ventana_activa: str | None) -> str:
    if not ventana_activa:
        return 'idle'
    titulo = ventana_activa.lower()
    for perfil, palabras in _PATRONES_PERFIL.items():
        if any(p in titulo for p in palabras):
            return perfil
    return 'general'


class BaselineSistema:
    """Aprende patrones de uso del sistema por franja horaria y perfil."""

    def __init__(self):
        self._datos: dict = self._cargar()
        self._ultima_persistencia: float = time.time()
        # Persistir cada 5 minutos máximo
        self._intervalo_persistencia = 300

    def _cargar(self) -> dict:
        try:
            if _BASELINE_ARCHIVO.exists():
                data = json.loads(_BASELINE_ARCHIVO.read_text(encoding='utf-8'))
                if isinstance(data, dict) and 'perfiles' in data:
                    return data
        except Exception as e:
            logger.warning(f"Baseline: error al cargar: {e}")
        return {
            'perfiles': {},
            'primer_registro': None,
            'total_lecturas': 0,
        }

    def _guardar(self):
        try:
            _DATOS_DIR.mkdir(parents=True, exist_ok=True)
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(_BASELINE_ARCHIVO, self._datos)
        except Exception as e:
            logger.warning(f"Baseline: error al guardar: {e}")

    def _guardar_si_toca(self):
        ahora = time.time()
        if ahora - self._ultima_persistencia >= self._intervalo_persistencia:
            self._guardar()
            self._ultima_persistencia = ahora

    def registrar_lectura(self, snapshot: dict, ventana_activa: str | None = None):
        """Acumula una lectura de CPU/RAM en el perfil correspondiente."""
        franja = _franja_actual()
        perfil = _detectar_perfil(ventana_activa)
        clave = f"{franja}_{perfil}"

        if clave not in self._datos['perfiles']:
            self._datos['perfiles'][clave] = {
                'ram_pct': [], 'cpu_pct': [],
                'lecturas': 0, 'franja': franja, 'perfil': perfil,
            }

        registro = self._datos['perfiles'][clave]

        # Mantener máximo 500 lecturas por perfil (FIFO)
        for metrica in ('ram_pct', 'cpu_pct'):
            valor = snapshot.get(metrica if metrica != 'ram_pct' else 'ram_ajena_pct',
                                 snapshot.get(metrica))
            if valor is not None:
                if len(registro[metrica]) >= 500:
                    registro[metrica] = registro[metrica][-400:]
                registro[metrica].append(round(float(valor), 1))

        registro['lecturas'] += 1

        if not self._datos['primer_registro']:
            self._datos['primer_registro'] = datetime.now().isoformat()
        self._datos['total_lecturas'] += 1

        self._guardar_si_toca()

    def obtener_baseline(self, perfil_clave: str | None = None) -> dict | None:
        """Retorna estadísticas para un perfil dado (o el actual)."""
        if perfil_clave is None:
            perfil_clave = f"{_franja_actual()}_{_detectar_perfil(None)}"

        registro = self._datos['perfiles'].get(perfil_clave)
        if not registro or registro['lecturas'] < _MIN_LECTURAS:
            return None

        resultado = {}
        for metrica in ('ram_pct', 'cpu_pct'):
            valores = registro[metrica]
            if len(valores) >= 10:
                resultado[f'{metrica}_media'] = statistics.mean(valores)
                resultado[f'{metrica}_sigma'] = statistics.stdev(valores) if len(valores) >= 2 else 0
            else:
                return None

        resultado['lecturas'] = registro['lecturas']
        resultado['franja'] = registro.get('franja', '')
        resultado['perfil'] = registro.get('perfil', '')
        return resultado

    def tiene_datos_suficientes(self) -> bool:
        """¿Hay al menos 7 días de datos y suficientes lecturas?"""
        primer = self._datos.get('primer_registro')
        if not primer:
            return False
        try:
            inicio = datetime.fromisoformat(primer)
            dias = (datetime.now() - inicio).days
            return dias >= _DIAS_MINIMOS and self._datos['total_lecturas'] >= _MIN_LECTURAS
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return False

    def es_anomalo(self, metrica: str, valor: float,
                   ventana_activa: str | None = None) -> bool:
        """Compara un valor contra media ± 2σ del perfil actual."""
        if not self.tiene_datos_suficientes():
            return False  # Sin datos suficientes, no declarar anomalía

        franja = _franja_actual()
        perfil = _detectar_perfil(ventana_activa)
        clave = f"{franja}_{perfil}"

        baseline = self.obtener_baseline(clave)
        if not baseline:
            return False

        media_key = f'{metrica}_media'
        sigma_key = f'{metrica}_sigma'
        if media_key not in baseline or sigma_key not in baseline:
            return False

        media = baseline[media_key]
        sigma = baseline[sigma_key]
        umbral = media + (_SIGMA_FACTOR * sigma)
        return valor > umbral

    def resumen(self) -> str:
        """Resumen para reporte de buenos días."""
        if not self.tiene_datos_suficientes():
            return "Aún recopilando datos del baseline del sistema."

        perfiles_activos = [
            k for k, v in self._datos['perfiles'].items()
            if v['lecturas'] >= _MIN_LECTURAS
        ]
        return (
            f"Baseline activo con {self._datos['total_lecturas']} lecturas "
            f"en {len(perfiles_activos)} perfiles aprendidos."
        )

    def cerrar(self):
        """Persiste datos pendientes."""
        self._guardar()


