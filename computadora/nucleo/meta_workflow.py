"""
כתר (Keter) — Corona. Supervisión de Keter (השגחת כתר).
Meta-Workflow Manager — Gestión multi-proyecto para Computadora.

La Corona observa todo desde arriba: audita proyectos, rastrea progreso,
notifica al usuario. Sello #12: Supervisión de Keter.
"""

import json
import os
import re
import time
from pathlib import Path
from loguru import logger


ARCHIVOS_CONTROL = [
    "DEVELOPMENT_WORKFLOW.md",
    "WorkItems.md",
    "SRS.md",
    "SDD.md",
    "TESTING_CHECKLISTS.md",
    "SECURITY_PLAN.md",
]

REGISTRO_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "datos", "proyectos_registrados.json"
)


class MetaWorkflow:
    """Gestiona múltiples proyectos: descubre, audita, reporta."""

    def __init__(self):
        self._proyectos: list[dict] = self._cargar_registro()
        # FP-043 B1+B7: Suscribir BusEventos
        self._suscribir_bus()

    # ─────────────────────────────────────────
    # BUS EVENTOS — Suscriptores (FP-043 B1+B7)
    # ─────────────────────────────────────────

    def _suscribir_bus(self):
        """Conecta BusEventos con handlers de Keter."""
        try:
            from computadora.nucleo.eventos import obtener_bus
            bus = obtener_bus()
            bus.suscribir("keter_auditoria", self._on_keter_auditoria)
            bus.suscribir("herramienta_error", self._on_herramienta_error)
            logger.info("MetaWorkflow: suscrito a BusEventos (keter_auditoria, herramienta_error)")
        except Exception as e:
            logger.warning(f"MetaWorkflow: no se pudo suscribir a BusEventos: {e}")

    def _on_keter_auditoria(self, datos):
        """B7: Recibe auditorías emitidas por Keter."""
        tipo = datos.get("tipo", "?") if isinstance(datos, dict) else "?"
        logger.info(f"BusEventos → keter_auditoria: tipo={tipo}")

    def _on_herramienta_error(self, datos):
        """B1: Conteo de fallos de herramientas."""
        nombre = datos.get("nombre", "?") if isinstance(datos, dict) else "?"
        logger.warning(f"BusEventos → herramienta_error: {nombre}")

    # ─────────────────────────────────────────
    # REGISTRO
    # ─────────────────────────────────────────

    def registrar_proyecto(self, ruta: str, nombre: str = "") -> str:
        """Registra un directorio como proyecto gestionado."""
        ruta = os.path.normpath(os.path.abspath(ruta))
        if not os.path.isdir(ruta):
            return f"Error: La ruta '{ruta}' no existe o no es un directorio."

        # Verificar que tenga al menos 1 archivo de control
        encontrados = [f for f in ARCHIVOS_CONTROL if os.path.isfile(os.path.join(ruta, f))]
        if not encontrados:
            return f"Error: No encontré archivos de control ({', '.join(ARCHIVOS_CONTROL[:3])}, ...) en '{ruta}'. No parece ser un proyecto del workflow."

        # No duplicar
        for p in self._proyectos:
            if os.path.normpath(p["ruta"]) == ruta:
                return f"El proyecto '{p['nombre']}' ya está registrado en esa ruta."

        if not nombre:
            nombre = os.path.basename(ruta)

        proyecto = {
            "nombre": nombre,
            "ruta": ruta,
            "archivos_control": encontrados,
            "registrado": time.strftime("%Y-%m-%d %H:%M"),
            "ultimo_escaneo": "",
        }
        self._proyectos.append(proyecto)
        self._guardar_registro()
        logger.info(f"Proyecto registrado: {nombre} en {ruta}")
        return f"Proyecto '{nombre}' registrado. Encontré {len(encontrados)} archivos de control: {', '.join(encontrados)}."

    def eliminar_proyecto(self, nombre_o_ruta: str) -> str:
        """Elimina un proyecto del registro (no borra archivos)."""
        p = self._buscar_proyecto(nombre_o_ruta)
        if not p:
            return f"No encontré un proyecto con ese nombre o ruta: '{nombre_o_ruta}'."
        self._proyectos.remove(p)
        self._guardar_registro()
        return f"Proyecto '{p['nombre']}' eliminado del registro."

    def listar_proyectos(self) -> str:
        """Lista todos los proyectos registrados."""
        if not self._proyectos:
            return "No hay proyectos registrados. Puede decirme 'registra este directorio como proyecto' o dar una ruta."
        lineas = []
        for p in self._proyectos:
            docs = len(p.get("archivos_control", []))
            lineas.append(f"{p['nombre']} en {p['ruta']}. {docs} archivos de control.")
        return "Proyectos registrados: " + " ".join(lineas)

    # ─────────────────────────────────────────
    # AUDITORÍA
    # ─────────────────────────────────────────

    def auditar_proyecto(self, nombre_o_ruta: str) -> str:
        """Auditoría de un proyecto: lee sus .md y evalúa estado."""
        p = self._buscar_proyecto(nombre_o_ruta)
        if not p:
            return f"No encontré un proyecto llamado '{nombre_o_ruta}'. Use 'listar proyectos' para ver los registrados."

        ruta = p["ruta"]
        hallazgos = []

        # Verificar archivos de control
        presentes = []
        faltantes = []
        for f in ARCHIVOS_CONTROL:
            if os.path.isfile(os.path.join(ruta, f)):
                presentes.append(f)
            else:
                faltantes.append(f)

        if faltantes:
            hallazgos.append(f"Faltan archivos de control: {', '.join(faltantes)}")

        # Leer WorkItems y contar pendientes
        wi_path = os.path.join(ruta, "WorkItems.md")
        if os.path.isfile(wi_path):
            wi_info = self._analizar_workitems(wi_path)
            if wi_info["pendientes"] > 0:
                hallazgos.append(f"{wi_info['pendientes']} WorkItems pendientes")
            if wi_info["completados"] > 0:
                hallazgos.append(f"{wi_info['completados']} WorkItems completados")
            if wi_info["pendientes"] == 0 and wi_info["completados"] == 0:
                hallazgos.append("No encontré WorkItems definidos")

        # Verificar fecha de última modificación de docs
        docs_viejos = []
        for f in presentes:
            fp = os.path.join(ruta, f)
            mod_time = os.path.getmtime(fp)
            dias = (time.time() - mod_time) / 86400
            if dias > 30:
                docs_viejos.append(f"{f} (hace {int(dias)} días)")
        if docs_viejos:
            hallazgos.append(f"Documentación antigua: {', '.join(docs_viejos)}")

        p["ultimo_escaneo"] = time.strftime("%Y-%m-%d %H:%M")
        p["archivos_control"] = presentes
        self._guardar_registro()

        if not hallazgos:
            return f"Auditoría de '{p['nombre']}': Todo en orden. {len(presentes)} archivos de control presentes y actualizados."

        resumen = f"Auditoría de '{p['nombre']}': " + ". ".join(hallazgos) + "."
        return resumen

    def resumen_general(self) -> str:
        """Resumen de todos los proyectos para briefing."""
        if not self._proyectos:
            return "No hay proyectos registrados."

        partes = []
        for p in self._proyectos:
            ruta = p["ruta"]
            if not os.path.isdir(ruta):
                partes.append(f"{p['nombre']}: ruta no accesible")
                continue

            wi_path = os.path.join(ruta, "WorkItems.md")
            if os.path.isfile(wi_path):
                wi_info = self._analizar_workitems(wi_path)
                pend = wi_info["pendientes"]
                comp = wi_info["completados"]
                partes.append(f"{p['nombre']}: {pend} pendientes, {comp} completados")
            else:
                presentes = sum(1 for f in ARCHIVOS_CONTROL if os.path.isfile(os.path.join(ruta, f)))
                partes.append(f"{p['nombre']}: {presentes} docs, sin WorkItems")

        return "Resumen de proyectos. " + ". ".join(partes) + "."

    def workitems_pendientes(self, nombre_o_ruta: str) -> str:
        """Lista WorkItems pendientes de un proyecto."""
        p = self._buscar_proyecto(nombre_o_ruta)
        if not p:
            return f"No encontré el proyecto '{nombre_o_ruta}'."

        wi_path = os.path.join(p["ruta"], "WorkItems.md")
        if not os.path.isfile(wi_path):
            return f"El proyecto '{p['nombre']}' no tiene WorkItems.md."

        wi_info = self._analizar_workitems(wi_path)
        if not wi_info["titulos_pendientes"]:
            return f"No hay WorkItems pendientes en '{p['nombre']}'."

        items = ". ".join(wi_info["titulos_pendientes"][:10])
        return f"WorkItems pendientes en '{p['nombre']}': {items}."

    # ─────────────────────────────────────────
    # ANÁLISIS INTERNO
    # ─────────────────────────────────────────

    def _analizar_workitems(self, wi_path: str) -> dict:
        """Analiza un WorkItems.md y cuenta pendientes/completados."""
        try:
            with open(wi_path, "r", encoding="utf-8") as f:
                contenido = f.read()
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            return {"pendientes": 0, "completados": 0, "titulos_pendientes": []}

        # Buscar headers WI-XXX
        wi_pattern = re.compile(r"^###\s+(WI-\d+:.+)$", re.MULTILINE)
        completado_pattern = re.compile(r"✅\s*COMPLETADO|Estado:\s*✅|COMPLETADO", re.IGNORECASE)

        pendientes = 0
        completados = 0
        titulos_pendientes = []

        matches = list(wi_pattern.finditer(contenido))
        for i, m in enumerate(matches):
            titulo = m.group(1).strip()
            # Buscar si está marcado como completado en el bloque siguiente
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(contenido)
            bloque = contenido[start:end]

            if completado_pattern.search(bloque) or "✅" in titulo:
                completados += 1
            else:
                pendientes += 1
                titulos_pendientes.append(titulo)

        return {
            "pendientes": pendientes,
            "completados": completados,
            "titulos_pendientes": titulos_pendientes,
        }

    def _buscar_proyecto(self, nombre_o_ruta: str) -> dict | None:
        """Busca proyecto por nombre o ruta parcial."""
        nombre_lower = nombre_o_ruta.lower().strip()
        for p in self._proyectos:
            if p["nombre"].lower() == nombre_lower:
                return p
            if nombre_lower in p["ruta"].lower():
                return p
        # Fuzzy: nombre parcial
        for p in self._proyectos:
            if nombre_lower in p["nombre"].lower():
                return p
        return None

    def _cargar_registro(self) -> list[dict]:
        """Carga el registro de proyectos desde disco."""
        try:
            path = os.path.normpath(REGISTRO_PATH)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.debug(f"No se pudo cargar registro de proyectos: {e}")
        return []

    def _guardar_registro(self):
        """Persiste el registro de proyectos."""
        try:
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(REGISTRO_PATH, self._proyectos)
        except Exception as e:
            logger.debug(f"No se pudo guardar registro de proyectos: {e}")

    # ─── Keter: Meta-cognición ──────────────────

    def autodiagnostico(self) -> dict:
        """Verifica el estado de los subsistemas críticos de COMPUTADORA.
        
        Retorna dict con estado (ok/error) de cada componente:
        tts, mic, memoria, ruaj."""
        resultado = {
            'tts': 'desconocido',
            'mic': 'desconocido',
            'memoria': 'desconocido',
            'ruaj': 'desconocido',
            'errores_recientes': 0,
        }

        # Nota: Ollama no se verifica aquí — usa local inference
        # El health check se enfoca en subsistemas críticos de usuario (TTS, micrófono)

        # TTS (edge-tts importable)
        try:
            import edge_tts  # noqa: F401
            resultado['tts'] = 'ok'
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            resultado['tts'] = 'error'

        # Micrófono
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            tiene_input = any(d.get('max_input_channels', 0) > 0 for d in devices)
            resultado['mic'] = 'ok' if tiene_input else 'error'
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            resultado['mic'] = 'error'

        # Memoria persistente
        try:
            datos_dir = Path(__file__).resolve().parent.parent.parent / "datos"
            memoria_dir = datos_dir / "memoria"
            resultado['memoria'] = 'ok' if memoria_dir.exists() else 'error'
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            resultado['memoria'] = 'error'

        # Ruaj (personalidad)
        try:
            personalidad_path = Path(__file__).resolve().parent.parent.parent / "datos" / "personalidad.json"
            resultado['ruaj'] = 'ok' if personalidad_path.exists() else 'error'
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            resultado['ruaj'] = 'error'

        # Errores recientes del aprendizaje
        try:
            errores_path = Path(__file__).resolve().parent.parent.parent / "datos" / "errores_aprendidos.json"
            if errores_path.exists():
                data = json.loads(errores_path.read_text(encoding='utf-8'))
                # Contar errores de últimas 24h
                ahora = time.time()
                def _ts_epoch(v):
                    if isinstance(v, (int, float)):
                        return float(v)
                    if isinstance(v, str):
                        try:
                            from datetime import datetime as _dt
                            return _dt.strptime(v, "%Y-%m-%d %H:%M").timestamp()
                        except (ValueError, TypeError):
                            return 0.0
                    return 0.0
                recientes = [e for e in data if ahora - _ts_epoch(e.get('timestamp', 0)) < 86400]
                resultado['errores_recientes'] = len(recientes)
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        return resultado

    def reporte_neshamot(self) -> str:
        """Reporte de estado de cada Sefirá activa de la Computadora."""
        diag = self.autodiagnostico()
        lineas = ["Estado de las Neshamot de la Computadora:"]

        mapa = {
            'ollama': ('Tiféret', 'Cerebro central — Ollama'),
            'tts': ('Maljut', 'Voz — Edge TTS'),
            'mic': ('Maljut', 'Oído — Micrófono'),
            'memoria': ('Jojmá', 'Memoria persistente'),
            'ruaj': ('Netzaj/Hod', 'Personalidad Ruaj'),
        }

        for clave, (sefira, desc) in mapa.items():
            estado = diag.get(clave, 'desconocido')
            icono = "✓" if estado == 'ok' else "✗" if estado == 'error' else "?"
            lineas.append(f"  {icono} {sefira}: {desc} — {estado}")

        errores = diag.get('errores_recientes', 0)
        if errores > 0:
            lineas.append(f"  ⚠ {errores} errores en las últimas 24 horas")
        else:
            lineas.append("  Sin errores recientes")

        return "\n".join(lineas)

    # ── שיווי משקל Shivui Mishkal — Equilibrio del Etz HaChaim (Regla #18) ──

    # Mapa de módulos → Sefirá (v3.0)
    _MAPA_SEFIROT = {
        "meta_workflow": "Keter", "actualizador": "Keter",
        "copilot_api": "Jojmá",
        "modelo_discovery": "Biná",
        "ciclo_circadiano": "Da'at", "entorno": "Da'at",
        "proactividad": "Jesed", "baseline_sistema": "Jesed",
        "permisos": "Gevurá", "aprendizaje": "Gevurá",
        "nlu": "Tiféret",
        "memoria": "Netzaj", "personalidad": "Netzaj",
        "personas": "Netzaj", "nivel1_aprendido": "Netzaj",
        "consciencia_temporal": "Netzaj",
        "escucha": "Hod", "habla": "Hod", "audio_log": "Hod",
        "windows": "Hod", "monitor_sistema": "Hod",
        "orquestador": "Yesod", "herramientas": "Yesod",
        "eventos": "Yesod", "watcher_solicitudes": "Yesod",
        "agenda": "Yesod", "copilot_bridge": "Yesod",
        "sistema": "Yesod", "web": "Yesod",
        "ventana_principal": "Maljut", "vida_autonoma": "Maljut",
        "estilos": "Maljut", "watchdog": "Maljut",
        # Cross-cutting (infraestructura, no Sefirá específica)
        "config": "Yesod", "logs": "Hod",
    }

    # Senderos (conexiones directas entre Sefirot)
    _SENDEROS = {
        ("Keter", "Tiféret"), ("Keter", "Jojmá"), ("Keter", "Biná"),
        ("Jojmá", "Tiféret"), ("Biná", "Tiféret"),
        ("Da'at", "Tiféret"), ("Da'at", "Jesed"), ("Da'at", "Netzaj"),
        ("Da'at", "Hod"),
        ("Jesed", "Tiféret"), ("Jesed", "Maljut"),
        ("Gevurá", "Tiféret"), ("Gevurá", "Yesod"), ("Gevurá", "Maljut"),
        ("Tiféret", "Netzaj"), ("Tiféret", "Hod"), ("Tiféret", "Yesod"),
        ("Tiféret", "Maljut"), ("Tiféret", "Da'at"),
        ("Netzaj", "Tiféret"), ("Netzaj", "Jesed"), ("Netzaj", "Maljut"),
        ("Hod", "Tiféret"), ("Hod", "Maljut"), ("Hod", "Netzaj"),
        ("Yesod", "Maljut"), ("Yesod", "Netzaj"),
        ("Maljut", "Hod"), ("Maljut", "Maljut"),
    }

    def analizar_impacto_sefirot(self, archivos_modificados: list[str]) -> dict:
        """Regla #18: Analiza qué Sefirot impacta un cambio y detecta desequilibrio.

        Args:
            archivos_modificados: Lista de nombres de archivo .py (sin ruta).

        Returns:
            dict con: sefirot_directas, sefirot_indirectas, senderos_afectados,
            requiere_reconceptualizar (bool), reporte (str).
        """
        # Identificar Sefirot directamente tocadas
        sefirot_directas = set()
        for archivo in archivos_modificados:
            nombre = archivo.replace(".py", "").split("/")[-1].split("\\")[-1]
            sefira = self._MAPA_SEFIROT.get(nombre)
            if sefira:
                sefirot_directas.add(sefira)

        # Expandir a Sefirot indirectas vía senderos
        sefirot_indirectas = set()
        senderos_afectados = []
        for s in sefirot_directas:
            for a, b in self._SENDEROS:
                if a == s and b not in sefirot_directas:
                    sefirot_indirectas.add(b)
                    senderos_afectados.append(f"{a}→{b}")
                elif b == s and a not in sefirot_directas:
                    sefirot_indirectas.add(a)
                    senderos_afectados.append(f"{a}→{b}")

        # Determinar si requiere reconceptualización
        total_impactados = len(sefirot_directas) + len(sefirot_indirectas)
        requiere_recon = total_impactados > len(sefirot_directas) + 1

        # Generar reporte
        lineas = [
            "═══ Análisis de Impacto por Sefirá (Regla #18) ═══",
            f"Sefirot directas: {', '.join(sorted(sefirot_directas)) or 'ninguna'}",
            f"Sefirot indirectas (vía senderos): {', '.join(sorted(sefirot_indirectas)) or 'ninguna'}",
            f"Senderos afectados: {len(senderos_afectados)}",
        ]
        if senderos_afectados:
            lineas.append(f"  {', '.join(senderos_afectados[:10])}")
        if requiere_recon:
            lineas.append(
                f"⚠ ATENCIÓN: El cambio impacta {total_impactados} Sefirot "
                f"(planeadas: {len(sefirot_directas)}, indirectas: {len(sefirot_indirectas)}). "
                "Reconceptualizar para mantener equilibrio del Etz HaChaim."
            )
        else:
            lineas.append("✓ Impacto contenido — equilibrio mantenido.")

        return {
            "sefirot_directas": sorted(sefirot_directas),
            "sefirot_indirectas": sorted(sefirot_indirectas),
            "senderos_afectados": senderos_afectados,
            "requiere_reconceptualizar": requiere_recon,
            "reporte": "\n".join(lineas),
        }

    # ── Feedback Loop Keter → BusEventos → Maljut ──

    def emitir_auditoria(self, tipo: str, reporte: str):
        """Keter emite resultado de auditoría al BusEventos y lo persiste en datos/auditorias/."""
        import json
        from datetime import datetime
        from pathlib import Path

        # Emitir al bus
        try:
            from computadora.nucleo.eventos import obtener_bus
            obtener_bus().emitir("keter_auditoria", {"tipo": tipo, "reporte": reporte[:500]})
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)

        # Persistir en datos/auditorias/
        try:
            audit_dir = Path(__file__).resolve().parent.parent.parent / "datos" / "auditorias"
            audit_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo = audit_dir / f"{ts}_{tipo}.json"
            from computadora.utilidades.io_seguro import escribir_json_atomico
            escribir_json_atomico(archivo, {
                "ts": datetime.now().isoformat(),
                "tipo": tipo,
                "reporte": reporte,
            })
            logger.info(f"Keter: auditoría '{tipo}' persistida en {archivo.name}")
        except Exception as e:
            logger.warning(f"Keter: error persistiendo auditoría: {e}")


