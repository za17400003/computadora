"""
קֶשֶׁר Késher — GestorPersonas (FP-019)
Sefirá: Netzaj (נצח) — Persistencia relacional

BD NoSQL embebida con TinyDB para perfiles de personas.
Migra automáticamente desde personas_conocidas.json y owner_profile.json.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from loguru import logger
from tinydb import TinyDB, Query

_DATOS_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
_DB_PATH = _DATOS_DIR / "computadora_personas.json"

# ── Singleton ──
_gestor_global: GestorPersonas | None = None


def obtener_gestor() -> GestorPersonas | None:
    """Acceso global al GestorPersonas (None si no inicializado)."""
    return _gestor_global


class GestorPersonas:
    """Gestiona perfiles de personas con TinyDB."""

    def __init__(self):
        global _gestor_global
        _DATOS_DIR.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(str(_DB_PATH), ensure_ascii=False, indent=2)
        self._tabla = self._db.table("personas")
        self._Q = Query()
        _gestor_global = self
        logger.info(f"GestorPersonas iniciado — {len(self._tabla)} perfiles en BD")

    # ── Bootstrap del amo ──

    def bootstrap_amo(self) -> dict | None:
        """Crea/actualiza el perfil del amo con datos del sistema.

        - Infiere alias del username de Windows
        - Importa embedding de owner_profile.json si existe
        - Importa schedule de perfil_amo.json si existe
        - Idempotente: no duplica si ya existe.
        """
        existente = self._tabla.search(self._Q.rol == "amo")
        if existente:
            perfil = existente[0]
            # Enriquecer alias si el username no está
            username = os.getenv("USERNAME") or os.getenv("USER") or ""
            if username and username.lower() not in [a.lower() for a in perfil.get("aliases", [])]:
                aliases = perfil.get("aliases", [])
                aliases.append(username)
                self._tabla.update({"aliases": aliases}, self._Q.rol == "amo")
                logger.info(f"Alias '{username}' añadido al perfil del amo")
            return self._tabla.search(self._Q.rol == "amo")[0]

        # Crear perfil nuevo del amo
        username = os.getenv("USERNAME") or os.getenv("USER") or ""
        aliases = [username] if username else []

        # Importar embedding de owner_profile.json
        embedding = None
        voz_count = 0
        owner_path = _DATOS_DIR / "owner_profile.json"
        if owner_path.exists():
            try:
                data = json.loads(owner_path.read_text(encoding="utf-8"))
                embedding = data.get("embedding")
                voz_count = data.get("count", 0)
                logger.info(f"Embedding del amo importado ({voz_count} muestras)")
            except Exception as e:  # RF-167
                logger.debug("Excepcion ignorada: %s", e)
                logger.debug("No se pudo importar owner_profile.json")

        perfil = {
            "nombre": username.title() if username else "Señor",
            "aliases": aliases,
            "rol": "amo",
            "relacion": "propietario",
            "voz_embedding": embedding,
            "voz_count": voz_count,
            "fecha_conocido": str(date.today()),
            "ultima_interaccion": datetime.now().isoformat(),
            "interacciones_count": 0,
            "temas_frecuentes": [],
            "preferencias": {},
            "notas": [],
            "presentado_por": None,
            "confianza": 1.0,
        }
        self._tabla.insert(perfil)
        logger.info(f"Perfil del amo creado: {perfil['nombre']} (aliases={aliases})")
        return perfil

    # ── Migración desde JSON plano ──

    def migrar_desde_json(self):
        """Importa personas de personas_conocidas.json (si existe y no migradas)."""
        json_path = _DATOS_DIR / "personas_conocidas.json"
        if not json_path.exists():
            return
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            personas = data.get("personas", [])
            migradas = 0
            for p in personas:
                nombre = p.get("nombre", "").strip()
                if not nombre:
                    continue
                # No duplicar
                if self._tabla.search(self._Q.nombre == nombre):
                    continue
                perfil = {
                    "nombre": nombre,
                    "aliases": [],
                    "rol": "conocido",
                    "relacion": p.get("presentado_por", "desconocida"),
                    "voz_embedding": p.get("embedding"),
                    "voz_count": p.get("count", 1),
                    "fecha_conocido": p.get("fecha_conocido", str(date.today())),
                    "ultima_interaccion": None,
                    "interacciones_count": 0,
                    "temas_frecuentes": [],
                    "preferencias": {},
                    "notas": [],
                    "presentado_por": p.get("presentado_por"),
                    "confianza": 0.5,
                }
                self._tabla.insert(perfil)
                migradas += 1
            if migradas:
                logger.info(f"Migradas {migradas} personas desde personas_conocidas.json")
        except Exception as e:  # RF-167
            logger.debug("Excepcion ignorada: %s", e)
            logger.exception("Error migrando personas_conocidas.json")

    # ── CRUD de personas ──

    def obtener_amo(self) -> dict | None:
        """Retorna el perfil del amo o None."""
        r = self._tabla.search(self._Q.rol == "amo")
        return r[0] if r else None

    def obtener_titulo(self, interlocutor_id: str | None = None) -> str:
        """RF-316 כבוד האדון — Título dinámico según persona.
        - 'señor' si el interlocutor es el amo
        - nombre si es persona conocida
        - '' si no se puede determinar
        """
        if not interlocutor_id or interlocutor_id in ("extraño", "desconocido"):
            return ""
        persona = self.obtener_persona(interlocutor_id)
        if persona and persona.get("rol") == "amo":
            return "señor"
        if persona and persona.get("nombre"):
            return persona["nombre"]
        return ""

    def obtener_persona(self, nombre: str) -> dict | None:
        """Busca persona por nombre (case-insensitive)."""
        todos = self._tabla.all()
        for p in todos:
            if p.get("nombre", "").lower() == nombre.lower():
                return p
            if nombre.lower() in [a.lower() for a in p.get("aliases", [])]:
                return p
        return None

    def registrar_persona(self, nombre: str, embedding: list | None = None,
                          relacion: str | None = None,
                          presentado_por: str | None = None) -> dict:
        """Registra nueva persona o actualiza existente."""
        existente = self.obtener_persona(nombre)
        if existente:
            updates = {}
            if embedding:
                updates["voz_embedding"] = embedding
                updates["voz_count"] = existente.get("voz_count", 0) + 1
            if relacion:
                updates["relacion"] = relacion
            if updates:
                self._tabla.update(updates, doc_ids=[existente.doc_id])
            return self._tabla.get(doc_id=existente.doc_id)

        perfil = {
            "nombre": nombre,
            "aliases": [],
            "rol": "conocido",
            "relacion": relacion or "desconocida",
            "voz_embedding": embedding,
            "voz_count": 1 if embedding else 0,
            "fecha_conocido": str(date.today()),
            "ultima_interaccion": datetime.now().isoformat(),
            "interacciones_count": 0,
            "temas_frecuentes": [],
            "preferencias": {},
            "notas": [],
            "presentado_por": presentado_por,
            "confianza": 0.5,
        }
        doc_id = self._tabla.insert(perfil)
        logger.info(f"Nueva persona registrada: {nombre}")
        return self._tabla.get(doc_id=doc_id)

    def actualizar_embedding(self, nombre: str, emb: list):
        """Actualiza embedding con media incremental (igual que escucha.py actual)."""
        import numpy as np
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        vec = np.array(emb, dtype=float)
        vec = vec / (np.linalg.norm(vec) + 1e-12)

        old_emb = persona.get("voz_embedding")
        cnt = max(1, persona.get("voz_count", 1))
        if old_emb:
            old_vec = np.array(old_emb, dtype=float)
            new_vec = ((old_vec * cnt + vec) / (cnt + 1)).tolist()
        else:
            new_vec = vec.tolist()

        self._tabla.update(
            {"voz_embedding": new_vec, "voz_count": cnt + 1},
            doc_ids=[persona.doc_id],
        )

    def actualizar_amo_embedding(self, emb: list):
        """Actualiza el embedding del amo (llamado desde escucha.py)."""
        amo = self.obtener_amo()
        if not amo:
            return
        self.actualizar_embedding(amo["nombre"], emb)

    def identificar_por_voz(self, emb: list, umbral: float = 0.40) -> tuple[str | None, float]:
        """Compara embedding contra todas las personas conocidas (no amo).

        Returns: (nombre, similitud) o (None, 0.0)
        """
        import numpy as np

        todos = self._tabla.search(self._Q.rol == "conocido")
        mejor_sim = 0.0
        mejor_nombre = None
        vec = np.array(emb, dtype=float)

        for p in todos:
            p_emb = p.get("voz_embedding")
            if not p_emb:
                continue
            p_vec = np.array(p_emb, dtype=float)
            # Manejar dimensiones diferentes
            min_dim = min(len(vec), len(p_vec))
            sim = float(np.dot(vec[:min_dim], p_vec[:min_dim]) /
                        (np.linalg.norm(vec[:min_dim]) * np.linalg.norm(p_vec[:min_dim]) + 1e-12))
            if sim > mejor_sim:
                mejor_sim = sim
                mejor_nombre = p.get("nombre")

        if mejor_sim >= umbral:
            return mejor_nombre, mejor_sim
        return None, 0.0

    # ── Enriquecimiento orgánico ──

    def registrar_interaccion(self, nombre: str):
        """Incrementa contador de interacciones y actualiza timestamp."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        self._tabla.update(
            {
                "interacciones_count": persona.get("interacciones_count", 0) + 1,
                "ultima_interaccion": datetime.now().isoformat(),
            },
            doc_ids=[persona.doc_id],
        )

    def agregar_nota(self, nombre: str, nota: str):
        """Agrega una nota al perfil de la persona."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        notas = persona.get("notas", [])
        if nota not in notas:
            notas.append(nota)
            self._tabla.update({"notas": notas}, doc_ids=[persona.doc_id])

    def actualizar_nombre_amo(self, nombre: str):
        """El amo reveló su nombre real."""
        amo = self.obtener_amo()
        if not amo:
            return
        old_name = amo.get("nombre", "")
        aliases = amo.get("aliases", [])
        if old_name and old_name.lower() != nombre.lower() and old_name.lower() not in [a.lower() for a in aliases]:
            aliases.append(old_name)
        self._tabla.update(
            {"nombre": nombre, "aliases": aliases},
            doc_ids=[amo.doc_id],
        )
        logger.info(f"Nombre del amo actualizado: {nombre}")

    def agregar_alias(self, nombre_persona: str, alias: str):
        """Agrega un alias a una persona."""
        persona = self.obtener_persona(nombre_persona)
        if not persona:
            return
        aliases = persona.get("aliases", [])
        if alias.lower() not in [a.lower() for a in aliases]:
            aliases.append(alias)
            self._tabla.update({"aliases": aliases}, doc_ids=[persona.doc_id])

    def actualizar_relacion(self, nombre: str, relacion: str):
        """Actualiza la relación de una persona (ej: 'hermana del propietario')."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        self._tabla.update({"relacion": relacion}, doc_ids=[persona.doc_id])

    def agregar_tema(self, nombre: str, tema: str):
        """Agrega un tema frecuente al perfil."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        temas = persona.get("temas_frecuentes", [])
        if tema.lower() not in [t.lower() for t in temas]:
            temas.append(tema)
            # Mantener máximo 20 temas
            if len(temas) > 20:
                temas = temas[-20:]
            self._tabla.update({"temas_frecuentes": temas}, doc_ids=[persona.doc_id])

    def ajustar_confianza(self, nombre: str, delta: float):
        """Incrementa/decrementa la confianza en la identidad de una persona."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return
        confianza = max(0.0, min(1.0, persona.get("confianza", 0.5) + delta))
        self._tabla.update({"confianza": confianza}, doc_ids=[persona.doc_id])

    # ── Correlación nombre↔voz ──

    def correlacionar_nombre(self, nombre_mencionado: str, emb_hablante: list,
                             umbral: float = 0.40) -> bool:
        """Si alguien dice un nombre y una voz similar responde, asociar.

        Retorna True si se hizo correlación.
        """
        import numpy as np
        persona = self.obtener_persona(nombre_mencionado)
        if not persona:
            return False
        if persona.get("voz_embedding"):
            # Ya tiene embedding — verificar que coincide
            p_emb = np.array(persona["voz_embedding"], dtype=float)
            vec = np.array(emb_hablante, dtype=float)
            min_dim = min(len(vec), len(p_emb))
            sim = float(np.dot(vec[:min_dim], p_emb[:min_dim]) /
                        (np.linalg.norm(vec[:min_dim]) * np.linalg.norm(p_emb[:min_dim]) + 1e-12))
            if sim >= umbral:
                self.ajustar_confianza(nombre_mencionado, 0.05)
                return True
        else:
            # No tiene embedding — asociar esta voz
            self.actualizar_embedding(nombre_mencionado, emb_hablante)
            self.ajustar_confianza(nombre_mencionado, 0.10)
            logger.info(f"Correlación: voz asociada a '{nombre_mencionado}'")
            return True
        return False

    # ── Contexto para inyección en prompt ──

    def generar_contexto_persona(self, nombre: str) -> str | None:
        """Genera bloque de contexto para inyectar en el prompt del LLM.

        Máximo ~80 tokens para no saturar contexto de gemma3:4b.
        """
        persona = self.obtener_persona(nombre)
        if not persona:
            return None
        partes = [f"Interlocutor: {persona['nombre']}"]
        if persona.get("relacion") and persona["relacion"] != "desconocida":
            partes.append(f"Relación: {persona['relacion']}")
        if persona.get("temas_frecuentes"):
            temas = ", ".join(persona["temas_frecuentes"][:5])
            partes.append(f"Temas frecuentes: {temas}")
        if persona.get("notas"):
            notas = "; ".join(persona["notas"][:3])
            partes.append(f"Notas: {notas}")
        n_int = persona.get("interacciones_count", 0)
        if n_int > 0:
            partes.append(f"Interacciones: {n_int}")
        return " | ".join(partes)

    # ── Privacidad ──

    def olvidar_persona(self, nombre: str) -> bool:
        """Elimina completamente el perfil de una persona. Retorna True si existía."""
        persona = self.obtener_persona(nombre)
        if not persona:
            return False
        if persona.get("rol") == "amo":
            logger.warning("No se puede olvidar al amo")
            return False
        self._tabla.remove(doc_ids=[persona.doc_id])
        logger.info(f"Persona olvidada: {nombre}")
        return True

    def listar_personas(self) -> list[dict]:
        """Retorna lista de todas las personas (sin embeddings por privacidad)."""
        resultado = []
        for p in self._tabla.all():
            resultado.append({
                "nombre": p.get("nombre"),
                "rol": p.get("rol"),
                "relacion": p.get("relacion"),
                "confianza": p.get("confianza"),
                "interacciones": p.get("interacciones_count", 0),
            })
        return resultado

    def cerrar(self):
        """Cierra la BD."""
        self._db.close()


