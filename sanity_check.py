from __future__ import annotations

import base64
from pprint import pprint

from bridge_logic import ProjectABridge


def main() -> None:
    try:
        bridge = ProjectABridge()
    except ModuleNotFoundError as exc:  # pragma: no cover - debugging aid
        print(f"ModuleNotFoundError detected while loading bridge: {exc}")
        raise

    sample_text = "Suspicious login anomaly observed"
    encoded_payload = base64.b64encode(sample_text.encode("utf-8")).decode("utf-8")
    result = bridge.execute(encoded_payload)
    pprint(result)


if __name__ == "__main__":
    main()
