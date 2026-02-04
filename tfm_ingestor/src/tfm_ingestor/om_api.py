from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


class OpenMetadataApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class OmRef:
    id: str
    type: str
    name: str


class OpenMetadataApi:
    """
    Minimal OpenMetadata REST client (api/v1) for the PoC.

    Notes:
    - Auth: JWT via `Authorization: Bearer <token>` (recommended for API operations).
    - This client intentionally implements only the endpoints we need for the TFM PoC.
    """

    def __init__(
        self,
        *,
        base_url: str,
        jwt_token: str | None,
        timeout_s: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        if jwt_token:
            self.session.headers.update({"Authorization": f"Bearer {jwt_token}"})

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            r = self.session.request(
                method,
                self._url(path),
                timeout=self.timeout_s,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as e:
            raise OpenMetadataApiError(str(e)) from e

        if r.status_code >= 400:
            raise OpenMetadataApiError(
                f"{method} {path} -> {r.status_code}\n{r.text[:2000]}"
            )
        if r.content:
            return r.json()
        return None

    def list_tables(self, *, limit: int = 1000, fields: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if fields:
            params["fields"] = fields
        data = self._request("GET", "/tables", params=params)
        return list(data.get("data", []))

    def patch_table(self, *, table_id: str, patch_ops: list[dict[str, Any]]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json-patch+json"}
        return self._request("PATCH", f"/tables/{table_id}", headers=headers, json=patch_ops)

    def get_domain_by_name(self, *, domain_name: str) -> dict[str, Any] | None:
        # Some OM endpoints use fullyQualifiedName under /name/{fqn}. We keep it simple (single-level names).
        try:
            return self._request("GET", f"/domains/name/{quote(domain_name, safe='')}")
        except OpenMetadataApiError as e:
            # Treat 404-like as "missing". OM error bodies vary; keep it defensive.
            msg = str(e)
            if "-> 404" in msg or "Not Found" in msg:
                return None
            raise

    def create_domain(self, *, name: str, description: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        return self._request("POST", "/domains", json=body)
