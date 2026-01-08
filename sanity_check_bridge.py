"""Legacy bridge sanity check now routed through the unified t79 inference."""

from __future__ import annotations

import base64
from pprint import pprint

from bridge_logic import run_inference


def generate_dummy_base64() -> str:
    dummy_text = "This is a dummy request to the t79 pipeline"
    return base64.b64encode(dummy_text.encode("utf-8")).decode("utf-8")


def main() -> None:
    payload = {"text": generate_dummy_base64()}
    response = run_inference(payload)
    pprint(response)
    assert response.get("classification", {}).get("label"), "Prediction missing label"
    print("Bridge sanity check passed.")


if __name__ == "__main__":
    main()
