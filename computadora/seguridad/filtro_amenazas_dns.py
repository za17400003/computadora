"""
גבורה (Gevurá) — Shomer HaSha'ar — Guardián del Umbral.
Sendero 61: Gevurá→Hod  (filtro_amenazas_dns → escucha — threat filter).

Filtro DNS local para protección contra:
  - Malware / phishing
  - Trackers / ads
  - Dominios sospechosos

Listas de bloqueo auto-actualizables. Alertas al Computadora.

RF-347: Threat Protection + Ad Blocking
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from loguru import logger

# ═══════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════

_DATOS_DIR = Path(__file__).parent.parent.parent / "datos" / "shomer"
_BLOCKLIST_PATH = _DATOS_DIR / "blocklist.json"
_LOG_PATH = _DATOS_DIR / "amenazas.jsonl"
_HOSTS_PATH = Path("C:/Windows/System32/drivers/etc/hosts")

# Listas de bloqueo por defecto (dominios a bloquear)
_LISTAS_DEFAULT: dict[str, list[str]] = {
    "malware": [
        "malware-domain-list.de",
        "zeus-tracker.abuse.ch",
    ],
    "phishing": [
        "phishing.database",
    ],
    "trackers": [
        "tracking.example.com",
        "analytics.ads.example.com",
    ],
}

# URLs de listas públicas conocidas (para actualización)
_FUENTES_BLOCKLIST = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://adaway.org/hosts.txt",
]


@dataclass
class AmenazaDetectada:
    """Registro de una amenaza detectada."""
    dominio: str
    categoria: str  # malware, phishing, tracker, ad
    origen: str     # dns_query, url_click, etc.
    timestamp: float = 0.0
    bloqueada: bool = True


class FiltroAmenazasDNS:
    """Guardián del Umbral — Protección contra amenazas y ads.

    Uso:
        shomer = FiltroAmenazasDNS()
        shomer.esta_bloqueado("malware-site.com")  # -> True/False
        shomer.filtrar_url("http://phishing.com/login")
        shomer.agregar_a_lista("dominio.malo", "malware")
        shomer.activar_dns_local()  # Escribe reglas en hosts (requiere admin)
    """

    def __init__(self, on_alerta: Callable[[str], None] | None = None):
        self._datos_dir = _DATOS_DIR
        self._datos_dir.mkdir(parents=True, exist_ok=True)
        self._on_alerta = on_alerta
        self._blocklist: dict[str, set[str]] = {}
        self._stats = {"bloqueados": 0, "permitidos": 0, "alertas": 0}
        self._cargar_listas()

    def _cargar_listas(self):
        """Carga las listas de bloqueo desde disco o usa defaults."""
        if _BLOCKLIST_PATH.exists():
            try:
                data = json.loads(_BLOCKLIST_PATH.read_text(encoding="utf-8"))
                self._blocklist = {k: set(v) for k, v in data.items()}
                total = sum(len(v) for v in self._blocklist.values())
                logger.info(f"[Shomer] Listas cargadas: {total} dominios en {len(self._blocklist)} categorías")
                return
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"[Shomer] Error cargando listas: {e}")

        # Inicializar con defaults
        self._blocklist = {k: set(v) for k, v in _LISTAS_DEFAULT.items()}
        self._guardar_listas()

    def _guardar_listas(self):
        """Persiste listas a disco."""
        serializable = {k: sorted(v) for k, v in self._blocklist.items()}
        _BLOCKLIST_PATH.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def esta_bloqueado(self, dominio: str) -> tuple[bool, str]:
        """Verifica si un dominio está en alguna lista de bloqueo.

        Returns:
            (bloqueado: bool, categoria: str)
        """
        dom = dominio.lower().strip().rstrip(".")
        for cat, dominios in self._blocklist.items():
            if dom in dominios or any(dom.endswith("." + d) for d in dominios):
                self._stats["bloqueados"] += 1
                self._registrar_amenaza(dom, cat, "dns_query")
                return True, cat
        self._stats["permitidos"] += 1
        return False, ""

    def filtrar_url(self, url: str) -> tuple[bool, str]:
        """Filtra una URL completa extrayendo el dominio."""
        # Extraer dominio de URL
        m = re.match(r'https?://([^/:]+)', url)
        if not m:
            return False, ""
        return self.esta_bloqueado(m.group(1))

    def agregar_a_lista(self, dominio: str, categoria: str = "custom") -> str:
        """Agrega un dominio a una lista de bloqueo."""
        dom = dominio.lower().strip().rstrip(".")
        if not dom:
            return "Dominio vacío."
        if categoria not in self._blocklist:
            self._blocklist[categoria] = set()
        if dom in self._blocklist[categoria]:
            return f"'{dom}' ya está en la lista '{categoria}'."
        self._blocklist[categoria].add(dom)
        self._guardar_listas()
        return f"'{dom}' agregado a lista '{categoria}'."

    def remover_de_lista(self, dominio: str, categoria: str = "custom") -> str:
        """Remueve un dominio de una lista."""
        dom = dominio.lower().strip()
        if categoria in self._blocklist:
            self._blocklist[categoria].discard(dom)
            self._guardar_listas()
            return f"'{dom}' removido de '{categoria}'."
        return f"Categoría '{categoria}' no encontrada."

    def actualizar_desde_fuentes(self) -> str:
        """Descarga listas de bloqueo de fuentes públicas (hosts format)."""
        import urllib.request

        nuevos = 0
        for url in _FUENTES_BLOCKLIST:
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    content = resp.read().decode("utf-8", errors="replace")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                        dom = parts[1].lower()
                        if dom not in ("localhost", "localhost.localdomain", "local"):
                            if "ads" not in self._blocklist:
                                self._blocklist["ads"] = set()
                            if dom not in self._blocklist["ads"]:
                                self._blocklist["ads"].add(dom)
                                nuevos += 1
            except Exception as e:
                logger.warning(f"[Shomer] Error descargando {url}: {e}")

        if nuevos:
            self._guardar_listas()
        total = sum(len(v) for v in self._blocklist.values())
        return f"Listas actualizadas: {nuevos} dominios nuevos. Total: {total}."

    def activar_dns_local(self) -> str:
        """Escribe reglas de bloqueo en el archivo hosts de Windows (requiere admin)."""
        try:
            # Leer hosts actual
            contenido_actual = ""
            if _HOSTS_PATH.exists():
                contenido_actual = _HOSTS_PATH.read_text(encoding="utf-8")

            # Generar bloque Computadora
            marcador_inicio = "# === Computadora SHOMER SHAAR START ==="
            marcador_fin = "# === Computadora SHOMER SHAAR END ==="

            # Remover bloque anterior si existe
            if marcador_inicio in contenido_actual:
                antes = contenido_actual[:contenido_actual.index(marcador_inicio)]
                despues_idx = contenido_actual.find(marcador_fin)
                despues = contenido_actual[despues_idx + len(marcador_fin):] if despues_idx >= 0 else ""
                contenido_actual = antes.rstrip() + "\n" + despues.lstrip()

            # Generar nuevas reglas
            lineas = [marcador_inicio]
            for cat, dominios in sorted(self._blocklist.items()):
                lineas.append(f"# Categoría: {cat}")
                for dom in sorted(dominios):
                    lineas.append(f"0.0.0.0 {dom}")
            lineas.append(marcador_fin)

            nuevo = contenido_actual.rstrip() + "\n\n" + "\n".join(lineas) + "\n"
            _HOSTS_PATH.write_text(nuevo, encoding="utf-8")

            total = sum(len(v) for v in self._blocklist.values())
            logger.info(f"[Shomer] DNS local activado: {total} dominios bloqueados en hosts")
            return f"DNS local activado: {total} dominios bloqueados."
        except PermissionError:
            return "Se requieren permisos de administrador para modificar el archivo hosts."
        except Exception as e:
            return f"Error activando DNS local: {e}"

    def desactivar_dns_local(self) -> str:
        """Remueve las reglas de Computadora del archivo hosts."""
        try:
            if not _HOSTS_PATH.exists():
                return "Archivo hosts no encontrado."
            contenido = _HOSTS_PATH.read_text(encoding="utf-8")
            marcador_inicio = "# === Computadora SHOMER SHAAR START ==="
            marcador_fin = "# === Computadora SHOMER SHAAR END ==="
            if marcador_inicio not in contenido:
                return "No hay reglas de Computadora en hosts."
            antes = contenido[:contenido.index(marcador_inicio)]
            despues_idx = contenido.find(marcador_fin)
            despues = contenido[despues_idx + len(marcador_fin):] if despues_idx >= 0 else ""
            _HOSTS_PATH.write_text(antes.rstrip() + "\n" + despues.lstrip(), encoding="utf-8")
            logger.info("[Shomer] DNS local desactivado")
            return "DNS local desactivado — reglas de Computadora removidas."
        except PermissionError:
            return "Se requieren permisos de administrador."
        except Exception as e:
            return f"Error: {e}"

    def _registrar_amenaza(self, dominio: str, categoria: str, origen: str):
        """Registra una amenaza detectada en log y emite alerta."""
        evento = {
            "dominio": dominio,
            "categoria": categoria,
            "origen": origen,
            "timestamp": time.time(),
            "bloqueada": True,
        }
        try:
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(evento, ensure_ascii=False) + "\n")
        except OSError:
            pass

        self._stats["alertas"] += 1
        if self._on_alerta:
            self._on_alerta(
                f"Amenaza bloqueada: {dominio} (categoría: {categoria})"
            )
        logger.warning(f"[Shomer] Bloqueado: {dominio} [{categoria}] desde {origen}")

    def resumen(self) -> str:
        """Resumen para voz."""
        total = sum(len(v) for v in self._blocklist.values())
        cats = ", ".join(f"{k}: {len(v)}" for k, v in self._blocklist.items())
        return (
            f"Shomer HaSha'ar activo. {total} dominios bloqueados ({cats}). "
            f"Sesión: {self._stats['bloqueados']} bloqueados, "
            f"{self._stats['alertas']} alertas."
        )


