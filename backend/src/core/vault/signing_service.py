
import os
import hashlib
import jwt
from fastapi import HTTPException
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Configuration
# In a real setup, these would be loaded from env vars or a secure vault
KEYS_DIR = os.getenv("KEYS_DIR", "backend/keys")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "brain_private.pem")
HUMAN_APPROVAL_PUBLIC_KEY = os.path.join(KEYS_DIR, "approver_public.pem")

def get_private_key():
    """Loads the Ed25519 private key from disk."""
    if not os.path.exists(PRIVATE_KEY_PATH):
        raise RuntimeError(f"Private key not found at {PRIVATE_KEY_PATH}")
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        return serialization.load_pem_private_key(key_file.read(), password=None)

def get_approver_public_key():
    """Loads the RSA public key for verifying human approval."""
    if not os.path.exists(HUMAN_APPROVAL_PUBLIC_KEY):
        raise RuntimeError(f"Approver public key not found at {HUMAN_APPROVAL_PUBLIC_KEY}")
    with open(HUMAN_APPROVAL_PUBLIC_KEY, "rb") as key_file:
        return key_file.read()

def hash_payload(payload: str) -> str:
    """Hashes the payload using SHA256."""
    return hashlib.sha256(payload.encode()).hexdigest()

class SignRequest(BaseModel):
    payload: str        # The command: "patch --service=api"
    approval_jwt: str   # The token signed by the Human Approver's device

class SignedResponse(BaseModel):
    payload: str
    signature: str
    signer: str

class SigningService:
    def sign_instruction(self, request: SignRequest) -> SignedResponse:
        # 1. Verify the Human-in-the-Loop Approval
        try:
            public_key = get_approver_public_key()
            # We verify that a HUMAN actually pressed 'Approve' on their mobile/web app
            decoded_approval = jwt.decode(
                request.approval_jwt,
                public_key,
                algorithms=["RS256"]
            )
            # Ensure the JWT payload matches the command we are signing
            if decoded_approval.get("cmd_hash") != hash_payload(request.payload):
                raise HTTPException(status_code=403, detail="Approval/Payload mismatch")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=403, detail="Approval token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=403, detail=f"Human Approval Invalid: {str(e)}")
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Internal verification error: {str(e)}")

        # 2. Perform the Cryptographic Signing
        try:
            private_key = get_private_key()
            if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                 raise TypeError("Key is not an Ed25519PrivateKey")

            payload_bytes = request.payload.encode('utf-8')

            # Generate Ed25519 Signature
            signature = private_key.sign(payload_bytes)

            # 3. Return the Hex-Encoded Signature for the Sentinel
            return SignedResponse(
                payload=request.payload,
                signature=signature.hex(),
                signer="Sovereign-Mechanica-Vault-01"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")

signing_service = SigningService()
