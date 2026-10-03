#!/usr/bin/env python
import hashlib
import hmac

# Valores del servidor
_salt = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
_hash_esperado = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"

# Probar varias contraseñas
candidates = ["emet", "met", "Emet", "EMET", "emet123", "", "minimi"]

print("╔═ ANÁLISIS DE CONTRASEÑA GRIMORIO ═╗")
print(f"Hash esperado: {_hash_esperado}")
print()

for test_password in candidates:
    if test_password:
        h = hashlib.pbkdf2_hmac("sha256", test_password.encode(), _salt, 100_000).hex()
        match = "✓ MATCH" if hmac.compare_digest(h, _hash_esperado) else "✗"
        print(f"{test_password:15} → {h[:16]}... {match}")

print()
print("═" * 50)
print("RESULTADO:")
# Calculate for "emet" one more time for detailed output
h_emet = hashlib.pbkdf2_hmac("sha256", "emet".encode(), _salt, 100_000).hex()
if hmac.compare_digest(h_emet, _hash_esperado):
    print("✓ La contraseña correcta es: 'emet'")
else:
    print("✗ 'emet' no es la contraseña correcta.")
    print("The hash generation code may have a different salt/iterations.")

