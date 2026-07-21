import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


MAGIC_HEADER = b"ZIPENCv1"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 390000


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive AES key from user string/password.
    """
    if not password:
        raise ValueError("Encryption password is required")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )

    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(raw_bytes: bytes, password: str) -> bytes:
    """
    Encrypt raw file bytes using AES-GCM.
    Output format:
    MAGIC_HEADER + salt + nonce + encrypted_data
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    encrypted_data = aesgcm.encrypt(nonce, raw_bytes, None)

    return MAGIC_HEADER + salt + nonce + encrypted_data


def decrypt_bytes(encrypted_bytes: bytes, password: str) -> bytes:
    """
    Decrypt encrypted bytes back to original ZIP bytes.
    """
    if not encrypted_bytes.startswith(MAGIC_HEADER):
        raise ValueError("Invalid encrypted file format")

    offset = len(MAGIC_HEADER)

    salt = encrypted_bytes[offset:offset + SALT_SIZE]
    offset += SALT_SIZE

    nonce = encrypted_bytes[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE

    encrypted_data = encrypted_bytes[offset:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    return aesgcm.decrypt(nonce, encrypted_data, None)