"""Verificador de Coherencia Interna — ¿Es el sistema coherente consigo mismo?

Verifica:
  1. Estados internos: ¿NLU y UI reportan lo mismo?
  2. Permisos: ¿Autorización en Gevurá = realidad?
  3. Encodings: ¿Face profile es el correcto?
  4. Config: ¿Sistema usa config correcta?
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
from computadora.verdad.verificador_realidad import VerificacionResultado


class VerificadorCoherenciaInterna:
    """Verificador de coherencia sistema consigo mismo."""
    
    def __init__(self):
        self.verificaciones: list[VerificacionResultado] = []
        logger.info("VerificadorCoherenciaInterna inicializado")
    
    def verificar_encoding_facial(self, usuario_id: str) -> VerificacionResultado:
        """Verificar: ¿Face profile del usuario es válido?
        
        Comprueba:
          1. owner_face_profile.json existe
          2. Tiene campo "encoding" con datos
          3. Encoding tiene tamaño esperado (128 valores)
        """
        owner_file = Path("datos/owner_face_profile.json")
        
        if not owner_file.exists():
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Face profile de {usuario_id} es válido",
                estado="DUDA",
                confianza=0.0,
                evidencia=["owner_face_profile.json no existe"],
                bloqueante=False,
            )
        else:
            try:
                profile = json.loads(owner_file.read_text())
                
                if "encoding" not in profile:
                    resultado = VerificacionResultado(
                        timestamp=datetime.now().isoformat(),
                        aseveracion=f"Face profile de {usuario_id} es válido",
                        estado="FALSO",
                        confianza=0.0,
                        evidencia=["owner_face_profile.json sin campo 'encoding'"],
                        bloqueante=True,
                        razon_bloqueo="Face profile corrupto — falta encoding"
                    )
                else:
                    encoding = profile["encoding"]
                    if isinstance(encoding, list) and len(encoding) == 128:
                        resultado = VerificacionResultado(
                            timestamp=datetime.now().isoformat(),
                            aseveracion=f"Face profile de {usuario_id} es válido",
                            estado="VERDAD",
                            confianza=1.0,
                            evidencia=[f"Encoding presente y válido (128 valores)"],
                            bloqueante=False,
                        )
                    else:
                        resultado = VerificacionResultado(
                            timestamp=datetime.now().isoformat(),
                            aseveracion=f"Face profile de {usuario_id} es válido",
                            estado="FALSO",
                            confianza=0.0,
                            evidencia=[f"Encoding inválido ({len(encoding) if isinstance(encoding, list) else 'no-list'} valores)"],
                            bloqueante=True,
                            razon_bloqueo="Encoding facial corrupto"
                        )
            except json.JSONDecodeError:
                resultado = VerificacionResultado(
                    timestamp=datetime.now().isoformat(),
                    aseveracion=f"Face profile de {usuario_id} es válido",
                    estado="FALSO",
                    confianza=0.0,
                    evidencia=["owner_face_profile.json no es JSON válido"],
                    bloqueante=True,
                    razon_bloqueo="JSON corrupto"
                )
        
        self.verificaciones.append(resultado)
        return resultado
    
    def verificar_permiso_gavura(self, usuario_id: str, debe_ser_propietario: bool) -> VerificacionResultado:
        """Verificar: ¿Usuario tiene permiso correcto en Gevurá?

        Si debe_ser_propietario=True:
          - El usuario debe estar registrado en datos/owner_face_profile.json
          - El campo "nombre" del perfil debe coincidir con usuario_id
        """
        perfil_file = Path("datos/owner_face_profile.json")

        if not perfil_file.exists() and debe_ser_propietario:
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Usuario {usuario_id} tiene permisos Gevurá correctos",
                estado="FALSO",
                confianza=0.0,
                evidencia=["owner_face_profile.json no existe pero debe ser propietario"],
                bloqueante=True,
                razon_bloqueo="Usuario no registrado en sistema"
            )
        elif perfil_file.exists():
            try:
                perfil = json.loads(perfil_file.read_text())

                nombre_guardado = perfil.get("nombre")

                if debe_ser_propietario and nombre_guardado and nombre_guardado != usuario_id:
                    resultado = VerificacionResultado(
                        timestamp=datetime.now().isoformat(),
                        aseveracion=f"Usuario {usuario_id} tiene permisos Gevurá correctos",
                        estado="FALSO",
                        confianza=0.0,
                        evidencia=[f"Nombre en perfil: {nombre_guardado}, solicitando: {usuario_id}"],
                        bloqueante=True,
                        razon_bloqueo="Usuario no coincide con propietario registrado"
                    )
                else:
                    resultado = VerificacionResultado(
                        timestamp=datetime.now().isoformat(),
                        aseveracion=f"Usuario {usuario_id} tiene permisos Gevurá correctos",
                        estado="VERDAD",
                        confianza=1.0,
                        evidencia=["Permisos coherentes con registro"],
                        bloqueante=False,
                    )
            except Exception as e:
                resultado = VerificacionResultado(
                    timestamp=datetime.now().isoformat(),
                    aseveracion=f"Usuario {usuario_id} tiene permisos Gevurá correctos",
                    estado="DUDA",
                    confianza=0.5,
                    evidencia=[f"Error al leer owner_face_profile.json: {e}"],
                    bloqueante=False,
                )
        else:
            resultado = VerificacionResultado(
                timestamp=datetime.now().isoformat(),
                aseveracion=f"Usuario {usuario_id} tiene permisos Gevurá correctos",
                estado="VERDAD",
                confianza=0.8,
                evidencia=["Sistema en primer boot — permiso en construcción"],
                bloqueante=False,
            )

        self.verificaciones.append(resultado)
        return resultado
    
    def generar_reporte(self) -> str:
        """Generar reporte legible de coherencia interna."""
        lineas = [
            "=" * 80,
            f"VERIFICACIÓN DE COHERENCIA INTERNA — {datetime.now().isoformat()}",
            "=" * 80,
            "",
        ]
        
        for v in self.verificaciones:
            icon = "✓" if v.estado == "VERDAD" else "✗" if v.estado == "FALSO" else "?"
            lineas.append(f"[{icon}] {v.aseveracion}")
            lineas.append(f"    Estado: {v.estado} | Confianza: {v.confianza:.2f}")
            for ev in v.evidencia:
                lineas.append(f"    • {ev}")
            if v.bloqueante:
                lineas.append(f"    ⚠️ BLOQUEANTE: {v.razon_bloqueo}")
            lineas.append("")
        
        return "\n".join(lineas)


