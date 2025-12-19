"""Sanity check for the Project A/B bridge."""

from __future__ import annotations

import base64
from pprint import pprint

from bridge_logic import ProjectABridge


def main() -> None:
    try:
        bridge = ProjectABridge()
    except ModuleNotFoundError as exc:  # pragma: no cover - explicit debugging aid
        print("ModuleNotFoundError detected while loading bridge: ", exc)
        raise

    sample_text = "Suspicious login anomaly observed"
    encoded_payload = base64.b64encode(sample_text.encode("utf-8")).decode("utf-8")
    response = bridge.execute(encoded_payload)

    print("Sanity check response:")
    pprint(response)

    assert response.get("status") == "success"
    prediction = response.get("prediction", {})
    assert isinstance(prediction, dict)
    assert prediction.get("classification", {}).get("label")
    print("Validation passed.")


if __name__ == "__main__":
    main()
