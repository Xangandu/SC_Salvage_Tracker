import hashlib
import os
import secrets


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return f"{salt}${digest.hex()}"


def verify_password(password, password_hash):
    if not password_hash or "$" not in password_hash:
        return False

    salt, stored_digest = password_hash.split("$", 1)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )

    return secrets.compare_digest(
        digest.hex(),
        stored_digest,
    )
