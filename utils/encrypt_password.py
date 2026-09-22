"""CLI: generate a local Fernet key + token for config/credentials.json.

The key is written only to local `config/fernet.key` (git-ignored)
and must never be committed. The reviewer receives it out of band.
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils.config import (  # noqa: E402
    REPO_ROOT,
    credentials_path,
    encrypt_password_token,
    fernet_key_path,
    generate_fernet_key,
)


def write_credentials(username: str, password_token: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, str] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    existing["username"] = username or existing.get("username", "")
    existing["password_token"] = password_token
    path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")


def write_fernet_key(key: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a local Fernet key and encrypt the ACC password token."
    )
    parser.add_argument(
        "--username",
        default="",
        help="Username to store in config/credentials.json (keeps the existing value if omitted).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    password = getpass.getpass("ACC password (input hidden): ")
    if not password:
        print("Password is required.", file=sys.stderr)
        return 1

    key = generate_fernet_key()
    token = encrypt_password_token(password, key)
    creds_file = credentials_path(args.root)
    key_file = fernet_key_path(args.root)
    write_credentials(args.username, token, creds_file)
    write_fernet_key(key, key_file)

    print(f"Wrote encrypted token to {creds_file.relative_to(args.root)}.")
    print(f"Wrote decryption key to {key_file.relative_to(args.root)} (git-ignored).")
    print("Send the key to the reviewer separately. Do not commit it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
