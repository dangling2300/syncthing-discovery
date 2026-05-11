#!/usr/bin/env python3
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import datetime
import hashlib
import base64
import json
from cryptography import x509
from cryptography.hazmat.backends import default_backend


def generate_syncthing_cert():
    """Generate a Syncthing-style self-signed certificate"""
    # Generate private key (2048-bit RSA)
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Create certificate subject (self-signed)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Syncthing"),
            x509.NameAttribute(NameOID.COMMON_NAME, "syncthing.local"),
        ]
    )

    # Build certificate
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("syncthing.local")]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    return private_key, cert


def compute_device_id(pem_data):
    """
    Computes Syncthing device ID from a certificate file

    Args:
        cert_path: Path to PEM-encoded certificate file

    Returns:
        Device ID string without check digits (56 characters with dashes)
    """

    cert = x509.load_pem_x509_certificate(pem_data, default_backend())
    der_data = cert.public_bytes(encoding=serialization.Encoding.DER)

    # Compute SHA-256 hash
    sha256 = hashlib.sha256(der_data).digest()

    # Base32 encode without padding
    b32 = base64.b32encode(sha256).decode("utf-8").rstrip("=").upper()

    # Format into 7-character groups (without check digits)
    formatted = "-".join([b32[i : i + 7] for i in range(0, len(b32), 7)])

    return formatted[:63]  # Syncthing IDs have 63 characters with dashes


if __name__ == "__main__":
    # Generate certificate pair
    private_key, certificate = generate_syncthing_cert()

    # Serialize certificate to PEM format
    certificate_pem = certificate.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    device_id = compute_device_id(certificate_pem)
    # Print certificate
    print(
        json.dumps(
            {
                "cert": certificate_pem.decode("utf-8"),
                "key": key_pem.decode("utf-8"),
                "deviceID": device_id,
            }
        )
    )
