import base64
from pprint import pprint

from bridge_logic import ProjectABridge


def main() -> None:
    """Quick sanity check for the Project A <-> Project B bridge."""
    try:
        bridge = ProjectABridge()
    except ModuleNotFoundError as exc:  # pragma: no cover - explicit debugging aid
        print(f"Module import failed inside the bridge: {exc}")
        raise

    sample_payload = base64.b64encode(b"This is a dummy Project B request").decode("utf-8")
    response = bridge.execute(sample_payload)

    print("Bridge response:")
    pprint(response)


if __name__ == "__main__":
    main()
