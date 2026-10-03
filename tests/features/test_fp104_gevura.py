"""
Tests FP-104: שלשלת גבורה (Shalshelet Gevurá) — Security modules.
WI-124: VPN Motor, WI-125: Cifrado Comms, WI-126: Gestor Claves, WI-127: Shomer HaSha'ar.
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

resultados = []
def check(id, desc, fn):
    try:
        ok, detalle = fn()
        resultados.append((id, desc, ok, detalle))
        print(f"{'PASS' if ok else 'FAIL'} {id}: {desc} — {detalle}")
    except Exception as e:
        resultados.append((id, desc, False, str(e)))
        print(f"FAIL {id}: {desc} — {e}")


# ═══════════════════════════════════════════════
# WI-124: VPN Motor — import tests
# ═══════════════════════════════════════════════

check("WI124-01", "Import vpn_motor", lambda: (
    __import__('golem.seguridad.vpn_motor', fromlist=['VpnMotor']) is not None,
    "módulo importable"
))

check("WI124-02", "VpnMotor class exists", lambda: (
    callable(getattr(__import__('golem.seguridad.vpn_motor',
        fromlist=['VpnMotor']), 'VpnMotor')),
    "clase VpnMotor accesible"
))

check("WI124-03", "VpnEstado dataclass", lambda: (
    hasattr(__import__('golem.seguridad.vpn_motor', fromlist=['VpnEstado']), 'VpnEstado'),
    "dataclass VpnEstado existe"
))

check("WI124-04", "VpnMotor.resumen() funciona", lambda: (
    isinstance(
        __import__('golem.seguridad.vpn_motor', fromlist=['VpnMotor']).VpnMotor().resumen(),
        str
    ),
    "resumen retorna string"
))


# ═══════════════════════════════════════════════
# WI-125: Cifrado Comms — import + functionality tests
# ═══════════════════════════════════════════════

check("WI125-01", "Import cifrado_comms", lambda: (
    __import__('golem.seguridad.cifrado_comms', fromlist=['CifradoComms']) is not None,
    "módulo importable"
))

_crypto_mod = __import__('golem.seguridad.cifrado_comms', fromlist=['CifradoComms', '_CRYPTO_DISPONIBLE'])
_CRYPTO_OK = getattr(_crypto_mod, '_CRYPTO_DISPONIBLE', False)

if _CRYPTO_OK:
    check("WI125-02", "Cifrar y descifrar bytes", lambda: (
        (lambda: (
            cc := _crypto_mod.CifradoComms(),
            datos := b"Emet - Verdad del Golem",
            cifrado := cc.cifrar(datos),
            descifrado := cc.descifrar(cifrado),
            descifrado == datos
        )[-1])(),
        "roundtrip bytes OK"
    ))

    check("WI125-03", "Cifrar y descifrar texto", lambda: (
        (lambda: (
            cc := _crypto_mod.CifradoComms(),
            texto := "El Golem protege la verdad",
            cifrado := cc.cifrar_texto(texto),
            descifrado := cc.descifrar_texto(cifrado),
            descifrado == texto
        )[-1])(),
        "roundtrip texto OK"
    ))

    check("WI125-04", "Resumen cifrado", lambda: (
        isinstance(_crypto_mod.CifradoComms().resumen(), str),
        "resumen retorna string"
    ))
else:
    check("WI125-02", "cryptography no disponible (skip)", lambda: (True, "skip — dep no instalada"))


# ═══════════════════════════════════════════════
# WI-126: Gestor Claves — import tests
# ═══════════════════════════════════════════════

check("WI126-01", "Import gestor_claves", lambda: (
    __import__('golem.seguridad.gestor_claves', fromlist=['GestorClaves']) is not None,
    "módulo importable"
))

check("WI126-02", "Credencial dataclass", lambda: (
    hasattr(__import__('golem.seguridad.gestor_claves', fromlist=['Credencial']), 'Credencial'),
    "dataclass Credencial existe"
))

if _CRYPTO_OK:
    check("WI126-03", "Generar password seguro", lambda: (
        (lambda: (
            gc := __import__('golem.seguridad.gestor_claves', fromlist=['GestorClaves']).GestorClaves(),
            pwd := gc.generar_password(16),
            len(pwd) == 16 and isinstance(pwd, str)
        )[-1])(),
        "password de 16 chars generado"
    ))

    check("WI126-04", "Resumen vault", lambda: (
        isinstance(
            __import__('golem.seguridad.gestor_claves', fromlist=['GestorClaves']).GestorClaves().resumen(),
            str
        ),
        "resumen retorna string"
    ))
else:
    check("WI126-03", "cryptography no disponible (skip)", lambda: (True, "skip — dep no instalada"))


# ═══════════════════════════════════════════════
# WI-127: Filtro de Amenazas DNS — functionality tests
# ═══════════════════════════════════════════════

check("WI127-01", "Import filtro_amenazas_dns", lambda: (
    __import__('computadora.seguridad.filtro_amenazas_dns', fromlist=['FiltroAmenazasDNS']) is not None,
    "módulo importable"
))

_shomer_mod = __import__('computadora.seguridad.filtro_amenazas_dns', fromlist=['FiltroAmenazasDNS'])

check("WI127-02", "FiltroAmenazasDNS init + resumen", lambda: (
    isinstance(_shomer_mod.FiltroAmenazasDNS().resumen(), str),
    "resumen retorna string"
))

check("WI127-03", "Bloqueo de dominio malware", lambda: (
    (lambda: (
        sh := _shomer_mod.FiltroAmenazasDNS(),
        sh.agregar_a_lista("evil.malware.test", "malware"),
        bloqueado := sh.esta_bloqueado("evil.malware.test"),
        bloqueado[0] is True and bloqueado[1] == "malware"
    )[-1])(),
    "dominio malware bloqueado correctamente"
))

check("WI127-04", "Dominio limpio NO bloqueado", lambda: (
    (lambda: (
        sh := _shomer_mod.FiltroAmenazasDNS(),
        resultado := sh.esta_bloqueado("google.com"),
        resultado[0] is False
    )[-1])(),
    "google.com no bloqueado"
))

check("WI127-05", "Filtrado de URL", lambda: (
    (lambda: (
        sh := _shomer_mod.FiltroAmenazasDNS(),
        sh.agregar_a_lista("phishing.test.xyz", "phishing"),
        resultado := sh.filtrar_url("https://phishing.test.xyz/login"),
        resultado[0] is True
    )[-1])(),
    "URL phishing filtrada"
))

check("WI127-06", "AmenazaDetectada dataclass", lambda: (
    hasattr(_shomer_mod, 'AmenazaDetectada'),
    "dataclass accesible"
))


# ═══════════════════════════════════════════════
# WI-128: NLU regex patterns
# ═══════════════════════════════════════════════

import re
from computadora.cerebro import nlu as nlu_mod

check("WI128-01", "Regex VPN ON existe", lambda: (
    hasattr(nlu_mod, '_RE_VPN_ON') and nlu_mod._RE_VPN_ON.search("activa la vpn") is not None,
    "match 'activa la vpn'"
))

check("WI128-02", "Regex VPN OFF existe", lambda: (
    hasattr(nlu_mod, '_RE_VPN_OFF') and nlu_mod._RE_VPN_OFF.search("desactiva la vpn") is not None,
    "match 'desactiva la vpn'"
))

check("WI128-03", "Regex VPN status", lambda: (
    hasattr(nlu_mod, '_RE_VPN_STATUS') and nlu_mod._RE_VPN_STATUS.search("estado de la vpn") is not None,
    "match 'estado de la vpn'"
))

check("WI128-04", "Regex vault buscar", lambda: (
    hasattr(nlu_mod, '_RE_VAULT_BUSCAR') and nlu_mod._RE_VAULT_BUSCAR.search("dame la contraseña de gmail") is not None,
    "match 'dame la contraseña de gmail'"
))

check("WI128-05", "Regex vault listar", lambda: (
    hasattr(nlu_mod, '_RE_VAULT_LISTAR') and nlu_mod._RE_VAULT_LISTAR.search("lista mis contraseñas") is not None,
    "match 'lista mis contraseñas'"
))

check("WI128-06", "Regex generar password", lambda: (
    hasattr(nlu_mod, '_RE_GENERAR_PASSWORD') and nlu_mod._RE_GENERAR_PASSWORD.search("genera una contraseña segura") is not None,
    "match 'genera una contraseña segura'"
))

check("WI128-07", "Regex shomer status", lambda: (
    hasattr(nlu_mod, '_RE_SHOMER_STATUS') and nlu_mod._RE_SHOMER_STATUS.search("estado de seguridad") is not None,
    "match 'estado de seguridad'"
))

check("WI128-08", "Regex bloquear dominio", lambda: (
    hasattr(nlu_mod, '_RE_BLOQUEAR_DOMINIO') and nlu_mod._RE_BLOQUEAR_DOMINIO.search("bloquea el dominio malo.com") is not None,
    "match 'bloquea el dominio malo.com'"
))


# ═══════════════════════════════════════════════
# Resumen
# ═══════════════════════════════════════════════

print("\n" + "=" * 60)
total = len(resultados)
pasados = sum(1 for _, _, ok, _ in resultados if ok)
fallados = total - pasados
print(f"FP-104 Shalshelet Gevurá — {pasados}/{total} PASS, {fallados} FAIL")
if fallados:
    print("\nFallados:")
    for id_, desc, ok, det in resultados:
        if not ok:
            print(f"  ✗ {id_}: {desc} — {det}")
print("=" * 60)

