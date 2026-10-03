#!/usr/bin/env python3
"""
🔐 Desencriptador de ENCICLOPEDIA — Enciclopedia de los 7 Metales

Descifra archivos .enc de ENCICLOPEDIA/ usando AES-256-GCM + PBKDF2-SHA256

PARÁMETROS CORRECTOS (extraído de servidor_enciclopedia.py línea 41-48):
  - Contraseña: "emet" (אמת = Verdad en hebreo)
  - Salt derivación contraseña: 1bd99be6d2bf895883375aca945b445a
  - Hash PBKDF2: 100,000 iteraciones (NO 480,000)
  - Hash EMET esperado: f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062
  - Hash AMET (hebreo) esperado: 776a244847427941e0434f527bc6502a12a650d5fdedc0f49e997c0311d3e64c
  - Salt archivo: a3c7f9e1b2d45608cafebabe12345678 (100k iteraciones)
  - Cifrado: AES-256-GCM(nonce 12 + ciphertext + tag 16)

FLUJO:
  1. Derivar hash de contraseña "emet" con PBKDF2-SHA256 (100k, salt)
  2. Derivar clave de archivo usando el HASH como contraseña (100k, file_salt)
  3. Descifrar archivos .enc con AES-256-GCM(clave, nonce, ciphertext_y_tag)
"""

import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ═══════════════════════════════════════════════
# PARÁMETROS DEL SERVIDOR ENCICLOPEDIA
# ═══════════════════════════════════════════════

# Paso 1: Derivar hash de contraseña
MASTER_PASSWORD_LATIN = "emet"
MASTER_PASSWORD_HEBREW = "אמת"

PASSWORD_SALT = bytes.fromhex("1bd99be6d2bf895883375aca945b445a")
PASSWORD_ITERATIONS = 100_000
PASSWORD_DKLEN = 32

# Hashes esperados (pre-calculados en servidor_enciclopedia.py)
HASH_EMET_LATIN = "f09e82871619790713b6c2577a75323c8d164a63c449ff3bb280571609fb2062"
HASH_EMET_HEBREW = "776a244847427941e0434f527bc6502a12a650d5fdedc0f49e997c0311d3e64c"

# Paso 2: Derivar clave de archivo desde el hash de contraseña
FILE_SALT = bytes.fromhex("a3c7f9e1b2d45608cafebabe12345678")
FILE_ITERATIONS = 100_000
FILE_DKLEN = 32

# Directorios
ENCICLOPEDIA_DIR = Path(__file__).parent.parent / "ENCICLOPEDIA"
OUTPUT_DIR = ENCICLOPEDIA_DIR / "decrypted"


# ═══════════════════════════════════════════════
# FUNCIONES
# ═══════════════════════════════════════════════

def derive_password_hash(password: str) -> str:
    """
    Paso 1: Derivar hash de contraseña usando PBKDF2-SHA256.
    
    Esto replica lo que hace servidor_enciclopedia.py en _hash_password():
        return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 100_000).hex()
    """
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), PASSWORD_SALT, PASSWORD_ITERATIONS, PASSWORD_DKLEN)
    return h.hex()


def derive_file_key(password_hash: str) -> bytes:
    """
    Paso 2: Derivar clave de archivo desde el HASH de contraseña.
    
    En servidor_enciclopedia.py línea 47:
        _FILE_KEY = hashlib.pbkdf2_hmac("sha256", _HASH.encode(), _FILE_SALT, 100_000)
    
    Donde _HASH es el STRING hexadecimal del hash anterior (no los bytes).
    """
    file_key = hashlib.pbkdf2_hmac("sha256", password_hash.encode(), FILE_SALT, FILE_ITERATIONS, FILE_DKLEN)
    return file_key


def decrypt_file(enc_path: Path, file_key: bytes) -> bytes | None:
    """
    Paso 3: Descifrar archivo .enc usando AES-256-GCM.
    
    Formato de archivo (desde _cifrar_bytes() en servidor_enciclopedia.py):
        nonce (12 bytes) + ciphertext + auth_tag (incluido en ciphertext por GCM)
    """
    try:
        data = enc_path.read_bytes()
        
        if len(data) < 28:  # 12 (nonce) + 16 (tag mínimo)
            print(f"  ⚠ Archivo demasiado corto: {enc_path.name}")
            return None
        
        nonce = data[:12]
        ciphertext_and_tag = data[12:]
        
        # AES-256-GCM.decrypt() espera ciphertext + tag
        aesgcm = AESGCM(file_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext_and_tag, None)
        return plaintext
    
    except Exception as e:
        return None


def main():
    print("\n🔓 Desencriptador de ENCICLOPEDIA — Enciclopedia de los 7 Metales")
    print("=" * 70)
    
    # Verificar directorio
    if not ENCICLOPEDIA_DIR.exists():
        print(f"  ❌ ENCICLOPEDIA_DIR no encontrado: {ENCICLOPEDIA_DIR}")
        return False
    
    # Listar archivos .enc
    enc_files = sorted(ENCICLOPEDIA_DIR.glob("*.enc"))
    if not enc_files:
        print(f"  ℹ No hay archivos .enc en {ENCICLOPEDIA_DIR}")
        return False
    
    print(f"  📂 Encontrados {len(enc_files)} archivos .enc")
    
    # Paso 1: Derivar hash de contraseña
    print("\n1️⃣  Derivando hash de contraseña 'emet'...")
    password_hash_latin = derive_password_hash(MASTER_PASSWORD_LATIN)
    password_hash_hebrew = derive_password_hash(MASTER_PASSWORD_HEBREW)
    
    print(f"  Derivado (latin): {password_hash_latin[:16]}...")
    print(f"  Derivado (hebrew): {password_hash_hebrew[:16]}...")
    print(f"  Esperado (latin): {HASH_EMET_LATIN[:16]}...")
    print(f"  Esperado (hebrew): {HASH_EMET_HEBREW[:16]}...")
    
    # Verificar que los hashes sean correctos
    if password_hash_latin != HASH_EMET_LATIN:
        print(f"  ❌ Hash NO coincide con HASH_EMET_LATIN")
        print(f"     Derivado: {password_hash_latin}")
        print(f"     Esperado: {HASH_EMET_LATIN}")
        return False
    
    print(f"  ✅ Hash verificado correctamente (EMET LATIN)")
    
    # Paso 2: Derivar clave de archivo
    print("\n2️⃣  Derivando clave de archivo...")
    file_key = derive_file_key(HASH_EMET_LATIN)
    print(f"  Clave derivada (hex): {file_key.hex()[:32]}...")
    
    # Paso 3: Descifrar archivos
    print(f"\n3️⃣  Desencriptando {len(enc_files)} archivos...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    descifrados = 0
    fallidos = 0
    
    for enc_path in enc_files:
        plaintext = decrypt_file(enc_path, file_key)
        
        if plaintext is None:
            print(f"  ❌ {enc_path.name}")
            fallidos += 1
            continue
        
        # Guarda con nombre hash (igual que en disco cifrado)
        output_path = OUTPUT_DIR / (enc_path.stem + ".txt")
        output_path.write_bytes(plaintext)
        
        # Intenta detectar tipo de contenido
        try:
            # Si es UTF-8, mostrar preview
            texto = plaintext.decode("utf-8", errors="ignore")
            if len(texto) > 0:
                preview = texto[:50].replace("\n", " ")
                print(f"  ✅ {enc_path.name} → {enc_path.stem} ({len(plaintext)} bytes)")
                print(f"     Preview: {preview}...")
            else:
                print(f"  ✅ {enc_path.name} → {enc_path.stem} (binario, {len(plaintext)} bytes)")
        except:
            print(f"  ✅ {enc_path.name} → {enc_path.stem} (binario, {len(plaintext)} bytes)")
        
        descifrados += 1
    
    # Resumen
    print("\n" + "=" * 70)
    print(f"✨ Desencriptación completada:")
    print(f"  ✅ {descifrados} archivos desencriptados")
    if fallidos > 0:
        print(f"  ❌ {fallidos} archivos fallaron")
    print(f"  📂 Guardados en: {OUTPUT_DIR}")
    
    return descifrados > 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
