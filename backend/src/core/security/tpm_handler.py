"""
TPM Handler - Hardware Root of Trust.

This module simulates the binding of Policy Memory to a physical TPM chip.
In a real environment, this would interface with `tpm2-tools` or `tpm2-tss`.
Here, we implement the logic for signing and verifying data integrity.
"""

from __future__ import annotations

import logging
import hashlib
import hmac
import os
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class TPMHandler:
    """
    Handles interactions with the Trusted Platform Module (TPM).
    Falls back to a software-based root of trust if hardware is unavailable.
    """

    def __init__(self, use_simulation: bool = True):
        """
        Initialize the TPM Handler.

        Args:
            use_simulation: If True, uses a local key file instead of real TPM.
        """
        self.use_simulation = use_simulation
        self.root_key = self._load_or_generate_root_key()

    def _load_or_generate_root_key(self) -> bytes:
        """
        Load or generate a root key.
        In production, this key would never leave the TPM.
        """
        # Store in a persistent location (relative to this file or project root)
        # Using backend/data/ for persistence
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        key_path = os.path.join(data_dir, "tpm_sim_key")

        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Generate a random 32-byte key
            key = os.urandom(32)
            with open(key_path, "wb") as f:
                f.write(key)
            return key

    def sign_policy_memory(self, memory_data: Dict[str, Any]) -> str:
        """
        Sign the policy memory data to ensure immutability.

        Args:
            memory_data: The policy memory to sign.

        Returns:
            Hex string of the signature (HMAC).
        """
        # Canonicalize the data
        data_str = json.dumps(memory_data, sort_keys=True)
        data_bytes = data_str.encode('utf-8')

        if self.use_simulation:
            signature = hmac.new(self.root_key, data_bytes, hashlib.sha256).hexdigest()
            logger.info("Signed policy memory using simulated TPM.")
            return signature
        else:
            # Placeholder for actual TPM signing call
            # subprocess.run(["tpm2_quote", ...])
            logger.warning("Real TPM signing not implemented, using simulation.")
            signature = hmac.new(self.root_key, data_bytes, hashlib.sha256).hexdigest()
            return signature

    def verify_policy_memory(self, memory_data: Dict[str, Any], signature: str) -> bool:
        """
        Verify the integrity of the policy memory.

        Args:
            memory_data: The policy memory data.
            signature: The signature to verify against.

        Returns:
            True if valid, False otherwise.
        """
        expected_signature = self.sign_policy_memory(memory_data)
        is_valid = hmac.compare_digest(expected_signature, signature)

        if is_valid:
            logger.info("Policy memory verification successful.")
        else:
            logger.critical("SECURITY ALERT: Policy memory verification failed!")

        return is_valid
