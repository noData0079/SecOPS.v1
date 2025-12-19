from __future__ import annotations

import base64
from pprint import pprint

from bridge_logic import ProjectABridge


def main() -> None:
    bridge = ProjectABridge()
    sample_payload = {"text": "This is a dummy Project B request"}
    encoded_payload = base64.b64encode(sample_payload["text"].encode("utf-8")).decode("utf-8")

    try:
        response = bridge.execute(encoded_payload)
    except ModuleNotFoundError as exc:  # pragma: no cover - explicit debugging aid
        print(f"Module import failed inside the bridge: {exc}")
        raise

    print("Bridge response:")
    pprint(response)


if __name__ == "__main__":
    main()
