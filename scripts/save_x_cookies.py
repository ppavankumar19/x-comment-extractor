from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings


def build_storage_state(auth_token: str, ct0: str) -> dict:
    return {
        "cookies": [
            {
                "name": "auth_token",
                "value": auth_token,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "ct0",
                "value": ct0,
                "domain": ".x.com",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            },
        ],
        "origins": [],
    }


def main() -> None:
    settings = get_settings()
    path = Path(settings.x_storage_state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    auth_token = input("Paste your X auth_token cookie value: ").strip()
    ct0 = input("Paste your X ct0 cookie value: ").strip()

    storage_state = build_storage_state(auth_token, ct0)
    path.write_text(json.dumps(storage_state, indent=2), encoding="utf-8")
    print(f"Saved X cookie session to {path}")


if __name__ == "__main__":
    main()
