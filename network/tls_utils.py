"""TLS-Zertifikate für Host-Server (Internet/LAN)."""

import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config.paths import data_dir

CERT_DIR = data_dir() / "network"
CERT_FILE = CERT_DIR / "host.crt"
KEY_FILE = CERT_DIR / "host.key"


def ensure_host_certificate() -> tuple[Path, Path]:
    """Erzeugt ein selbstsigniertes Zertifikat, falls noch keines existiert."""
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    if CERT_FILE.exists() and KEY_FILE.exists():
        return CERT_FILE, KEY_FILE

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError:
        return None, None

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SC Salvage Tracker"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SC Salvage Tracker Host"),
    ])

    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.DNSName("sc-salvage-tracker.local"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))
        .add_extension(san, critical=False)
        .sign(key, hashes.SHA256())
    )

    KEY_FILE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return CERT_FILE, KEY_FILE


def certificate_fingerprint(cert_path: Path | None = None) -> str:
    cert_path = cert_path or CERT_FILE
    if not cert_path or not cert_path.exists():
        return ""

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
    except ImportError:
        return ""

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    digest = cert.fingerprint(hashes.SHA256())
    return digest.hex().upper()
