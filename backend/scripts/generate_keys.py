import os
import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID

KEYS_DIR = "backend/keys"
CERTS_DIR = os.path.join(KEYS_DIR, "certs")

def generate_keys():
    os.makedirs(KEYS_DIR, exist_ok=True)
    os.makedirs(CERTS_DIR, exist_ok=True)

    # --- 1. Ed25519 Keys for Payload Signing (Brain -> Sentinel Instruction) ---
    brain_private = ed25519.Ed25519PrivateKey.generate()
    brain_public = brain_private.public_key()

    with open(os.path.join(KEYS_DIR, "brain_private.pem"), "wb") as f:
        f.write(brain_private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Write Hex for Sentinel Config (easier for env var)
    raw_bytes = brain_public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    with open(os.path.join(KEYS_DIR, "brain_public_hex.txt"), "w") as f:
        f.write(raw_bytes.hex())

    # --- 2. RSA Keys for Human Approver (Mocking) ---
    approver_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    approver_public = approver_private.public_key()

    with open(os.path.join(KEYS_DIR, "approver_private.pem"), "wb") as f:
         f.write(approver_private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    with open(os.path.join(KEYS_DIR, "approver_public.pem"), "wb") as f:
        f.write(approver_public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    # --- 3. mTLS Certificates (Brain <-> Sentinel Transport Security) ---

    # CA Key & Cert
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, u"Sovereign Mechanica CA"),
    ])
    ca_cert = x509.CertificateBuilder().subject_name(
        ca_subject
    ).issuer_name(
        ca_subject
    ).public_key(
        ca_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(ca_key, hashes.SHA256())

    with open(os.path.join(CERTS_DIR, "ca.key"), "wb") as f:
        f.write(ca_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(os.path.join(CERTS_DIR, "ca.crt"), "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

    # Sentinel Cert (Server)
    sentinel_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    sentinel_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"sentinel-agent")])
    sentinel_cert = x509.CertificateBuilder().subject_name(
        sentinel_subject
    ).issuer_name(
        ca_subject
    ).public_key(
        sentinel_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
         datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
         datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(ca_key, hashes.SHA256())

    with open(os.path.join(CERTS_DIR, "sentinel.key"), "wb") as f:
        f.write(sentinel_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(os.path.join(CERTS_DIR, "sentinel.crt"), "wb") as f:
        f.write(sentinel_cert.public_bytes(serialization.Encoding.PEM))

    # Brain Client Cert (Client)
    brain_client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    brain_client_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"brain-client")])
    brain_client_cert = x509.CertificateBuilder().subject_name(
        brain_client_subject
    ).issuer_name(
        ca_subject
    ).public_key(
        brain_client_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
         datetime.datetime.now(datetime.timezone.utc)
    ).not_valid_after(
         datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).sign(ca_key, hashes.SHA256())

    with open(os.path.join(CERTS_DIR, "brain_client.key"), "wb") as f:
        f.write(brain_client_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(os.path.join(CERTS_DIR, "brain_client.crt"), "wb") as f:
        f.write(brain_client_cert.public_bytes(serialization.Encoding.PEM))

    print("Keys and Certs generated in backend/keys/ and backend/keys/certs/")

if __name__ == "__main__":
    generate_keys()
