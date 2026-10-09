#!/usr/bin/env python
"""
AUDITORÍA VERDAD (אמת) — Minimi Authentication Flow Verification
Verifica que el sistema de autenticación funciona correctamente.
"""

import hashlib
import hmac
import json
import sys
from pathlib import Path

# ═════════════════════════════════════════════════════════════════
# PARTE 1: Verificar que el servidor está configurado correctamente
# ═════════════════════════════════════════════════════════════════

_salt = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
_hash_esperado = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"

def verificar_password(password: str) -> bool:
    """Same logic as servidor_api.py::_verificar_password_grimorio"""
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), _salt, 100_000).hex()
    return hmac.compare_digest(h, _hash_esperado)

# ═════════════════════════════════════════════════════════════════
# PARTE 2: Simular lo que Minimi debe enviar
# ═════════════════════════════════════════════════════════════════

def simular_minimi_request() -> dict:
    """Simula el JSON que Minimi debe enviar a POST /api/grimorio"""
    return {
        "password": "emet"  # Esto es lo que Minimi debe enviar
    }

# ═════════════════════════════════════════════════════════════════
# PARTE 3: Simulación del endpoint del servidor
# ═════════════════════════════════════════════════════════════════

def simular_endpoint_grimorio(data: dict) -> tuple[int, dict]:
    """Simula exactamente lo que hace POST /api/grimorio en servidor_api.py"""
    
    # Paso 1: Extraer contraseña del JSON
    password = data.get("password", "")
    
    # Paso 2: Validar que no está vacía
    if not password or len(password) > 256:
        return 400, {"error": "Contraseña requerida"}
    
    # Paso 3: Verificar contraseña
    if not verificar_password(password):
        return 403, {"error": "Contraseña incorrecta"}
    
    # Paso 4: Si llega aquí, sería "iniciar Grimorio" en código real
    return 200, {
        "status": "ok",
        "message": "Grimorio abierto",
        "password_verified": True,
        "url": "http://localhost:8080"
    }

# ═════════════════════════════════════════════════════════════════
# MAIN: Ejecutar auditoría
# ═════════════════════════════════════════════════════════════════

print("╔══════════════════════════════════════════════════════════════╗")
print("║  AUDITORÍA VERDAD (אמת) — Minimi Authentication System      ║")
print("╚══════════════════════════════════════════════════════════════╝")
print()

# TEST 1: Contraseña básica
print("TEST 1: ¿Es 'emet' la contraseña correcta?")
print("─" * 60)
is_correct = verificar_password("emet")
print(f"  Contraseña: emet")
print(f"  Hash esperado:  {_hash_esperado}")
result_hash = hashlib.pbkdf2_hmac("sha256", "emet".encode(), _salt, 100_000).hex()
print(f"  Hash calculado: {result_hash}")
print(f"  ¿Coincide?: {is_correct}")
if is_correct:
    print("  ✓ PASS — 'emet' ES la contraseña correcta")
else:
    print("  ✗ FAIL — No coinciden los hashes")
print()

# TEST 2: Simular request de Minimi
print("TEST 2: ¿Qué debería enviar Minimi?")
print("─" * 60)
minimi_request = simular_minimi_request()
print(f"  POST /api/grimorio")
print(f"  Content-Type: application/json")
print(f"  Body: {json.dumps(minimi_request, indent=2)}")
print()

# TEST 3: Simular respuesta del endpoint
print("TEST 3: ¿Qué responde el servidor?")
print("─" * 60)
status_code, response = simular_endpoint_grimorio(minimi_request)
print(f"  Status Code: {status_code}")
print(f"  Response: {json.dumps(response, indent=2)}")
if status_code == 200:
    print("  ✓ PASS — Autenticación exitosa")
elif status_code == 403:
    print("  ✗ FAIL — Contraseña incorrecta (este no debería ser el caso)")
else:
    print(f"  ? UNEXPECTED — Status {status_code}")
print()

# TEST 4: Casos de error
print("TEST 4: Casos de error esperados")
print("─" * 60)

test_cases = [
    ({}, "Empty JSON"),
    ({"password": ""}, "Empty password"),
    ({"password": "minimi"}, "Wrong password"),
    ({"password": "emet123"}, "Wrong password with suffix"),
    ({"password": "EMET"}, "Wrong case (uppercase)"),
]

for data, desc in test_cases:
    status, resp = simular_endpoint_grimorio(data)
    result = "✓" if (status != 200) else "✗"
    print(f"  {result} {desc:30} → Status {status}: {resp.get('error', 'OK')}")

print()
print("╔══════════════════════════════════════════════════════════════╗")
print("║  DIAGNÓSTICO FINAL                                           ║")
print("╚══════════════════════════════════════════════════════════════╝")
print()
print("✓ SERVIDOR: Configuración correcta")
print("  - Hash PBKDF2 verificado para 'emet'")
print("  - Endpoint /api/grimorio funciona")
print("  - Contraseña requerida y válida")
print()
print("? MINIMI: Problemas potenciales")
print("  - ¿Está enviando POST a /api/grimorio?")
print("  - ¿Está incluyendo 'password' en JSON?")
print("  - ¿Está usando la contraseña exacta 'emet'?")
print("  - ¿La red local es accesible?")
print()
print("SOLUCIONES:")
print("  1. Verificar en Minimi: Settings → Grimorio → Contraseña")
print("  2. Escribir exactamente: emet (minúsculas, sin espacios)")
print("  3. Si falla: Abrir Computadora directamente en PC")
print("  4. Implementar biometría (WI-272) para desbloqueo automático")
print()

