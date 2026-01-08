"""Sanity check for the unified t79 inference pipeline."""

from __future__ import annotations

from pprint import pprint

from bridge_logic import run_inference


def main() -> None:
    sample_payload = {"text": "Potential credential dumping detected"}
    response = run_inference(sample_payload)

    print("Sanity check result:")
    pprint(response)

    assert response.get("classification", {}).get("label"), "Prediction missing label"
    print("Validation passed.")


if __name__ == "__main__":
    main()
