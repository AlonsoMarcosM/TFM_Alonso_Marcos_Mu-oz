from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import subprocess
from typing import Any

import jwt
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_der_private_key,
)


def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def _get_secret_value(secret_name: str, key: str, namespace: str) -> str | None:
    try:
        raw = _run(
            [
                "kubectl",
                "get",
                "secret",
                secret_name,
                "-n",
                namespace,
                "-o",
                "json",
            ]
        )
    except subprocess.CalledProcessError:
        return None

    data = json.loads(raw).get("data", {})
    v = data.get(key)
    if not v:
        return None
    return base64.b64decode(v).decode("utf-8").strip().strip('"')


def _load_private_key_der(namespace: str, deployment: str) -> bytes:
    b64 = _run(
        [
            "kubectl",
            "exec",
            f"deployment/{deployment}",
            "-n",
            namespace,
            "--",
            "sh",
            "-c",
            "base64 /opt/openmetadata/conf/private_key.der",
        ]
    )
    return base64.b64decode("".join(b64.split()))


def build_token(
    *,
    namespace: str,
    deployment: str,
    subject: str,
    email: str,
    preferred_username: str,
    ttl_hours: int,
) -> str:
    key_der = _load_private_key_der(namespace=namespace, deployment=deployment)
    key = load_der_private_key(key_der, password=None)
    pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

    issuer = _get_secret_value("openmetadata-jwt-secret", "JWT_ISSUER", namespace) or "open-metadata.org"
    key_id = _get_secret_value("openmetadata-jwt-secret", "JWT_KEY_ID", namespace) or "Gb389a-9f76-gdjs-a92j-0242bk94356"

    now = dt.datetime.now(dt.timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "preferred_username": preferred_username,
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(hours=ttl_hours)).timestamp()),
    }

    return jwt.encode(payload, pem, algorithm="RS256", headers={"kid": key_id})


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a JWT token accepted by local OpenMetadata deployment")
    p.add_argument("--namespace", default="default")
    p.add_argument("--deployment", default="openmetadata")
    p.add_argument("--subject", default="admin")
    p.add_argument("--email", default="admin@open-metadata.org")
    p.add_argument("--preferred-username", default="admin")
    p.add_argument("--ttl-hours", type=int, default=8)
    args = p.parse_args()

    token = build_token(
        namespace=args.namespace,
        deployment=args.deployment,
        subject=args.subject,
        email=args.email,
        preferred_username=args.preferred_username,
        ttl_hours=args.ttl_hours,
    )
    print(token, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

