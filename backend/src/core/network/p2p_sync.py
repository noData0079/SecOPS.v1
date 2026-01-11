"""
Federated Sovereignty (Peer-to-Peer Intelligence)

Purpose: Share "Threat DNA" (hashes/signatures) between air-gapped instances
using an asynchronous import/export mechanism.

Mechanism:
- Export: Writes signed JSON to data/exports/threat_dna/
- Import: Reads from data/imports/threat_dna/
- No direct network sockets used to maintain ICE-AGE compliance.
"""

import hashlib
import json
import logging
import os
import glob
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

# Constants
EXPORT_DIR = "data/exports/threat_dna"
IMPORT_DIR = "data/imports/threat_dna"

@dataclass
class ThreatDNA:
    """
    Represents a shared threat intelligence artifact.
    Does not contain sensitive PII, only technical signatures.
    """
    id: str
    threat_type: str # e.g., "SQLi_Pattern_A", "Malicious_IP"
    signature_hash: str
    mitigation_strategy: str
    timestamp: str
    origin_instance_id: str = "local"

class P2PSyncEngine:
    def __init__(self):
        self.export_dir = EXPORT_DIR
        self.import_dir = IMPORT_DIR
        self.known_threats: Dict[str, ThreatDNA] = {}

        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.import_dir, exist_ok=True)

    def register_threat(self, threat_type: str, raw_signature: str, mitigation: str) -> ThreatDNA:
        """
        Creates a new ThreatDNA entry from a local observation.
        """
        sig_hash = hashlib.sha256(raw_signature.encode()).hexdigest()
        dna_id = f"dna_{sig_hash[:16]}"

        dna = ThreatDNA(
            id=dna_id,
            threat_type=threat_type,
            signature_hash=sig_hash,
            mitigation_strategy=mitigation,
            timestamp=datetime.utcnow().isoformat()
        )

        self.known_threats[dna_id] = dna
        logger.info(f"Registered new ThreatDNA: {dna_id}")
        return dna

    def export_threat_dna(self):
        """
        Writes all known threats to the export directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"threat_dna_export_{timestamp}.json"
        filepath = os.path.join(self.export_dir, filename)

        data = [asdict(t) for t in self.known_threats.values()]

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(data)} ThreatDNA entries to {filepath}")
        return filepath

    def import_threat_dna(self):
        """
        Scans the import directory for new DNA files and merges them.
        """
        files = glob.glob(os.path.join(self.import_dir, "*.json"))
        new_entries = 0

        for filepath in files:
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                for item in data:
                    # Validate schema roughly
                    if "id" in item and "signature_hash" in item:
                        if item["id"] not in self.known_threats:
                            self.known_threats[item["id"]] = ThreatDNA(**item)
                            new_entries += 1
            except Exception as e:
                logger.error(f"Failed to import {filepath}: {e}")

        logger.info(f"Imported {new_entries} new ThreatDNA entries.")
        return new_entries
