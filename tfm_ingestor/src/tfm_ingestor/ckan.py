from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class CkanApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class CkanPackageSearchResult:
    count: int
    results: list[dict[str, Any]]


class CkanClient:
    """
    Minimal CKAN client for harvesting.

    References:
    - CKAN Action API: /api/3/action/<action>
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout_s: int = 30,
        verify_ssl: bool = True,
        user_agent: str = "tfm-ckan-harvester",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        if api_key:
            # CKAN expects the API key in the Authorization header for private actions.
            self.session.headers.update({"Authorization": api_key})

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            r = self.session.request(
                method,
                self._url(path),
                timeout=self.timeout_s,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise CkanApiError(str(exc)) from exc

        if r.status_code >= 400:
            raise CkanApiError(f"{method} {path} -> {r.status_code}\n{r.text[:2000]}")
        data = r.json()
        if not isinstance(data, dict) or not data.get("success"):
            raise CkanApiError(f"{method} {path} -> invalid CKAN response: {str(data)[:2000]}")
        return data

    def package_search(self, *, query: str = "", rows: int = 100, start: int = 0) -> CkanPackageSearchResult:
        params = {"q": query, "rows": rows, "start": start}
        data = self._request("GET", "/api/3/action/package_search", params=params)
        result = data.get("result") or {}
        if not isinstance(result, dict):
            raise CkanApiError("CKAN package_search: missing result")
        count = int(result.get("count") or 0)
        results = result.get("results") or []
        if not isinstance(results, list):
            raise CkanApiError("CKAN package_search: invalid results type")
        return CkanPackageSearchResult(count=count, results=[x for x in results if isinstance(x, dict)])

    def iter_datasets(self, *, query: str = "", rows: int = 100, start: int = 0, max_datasets: int | None = None):
        fetched = 0
        current_start = start
        while True:
            resp = self.package_search(query=query, rows=rows, start=current_start)
            if not resp.results:
                break
            for ds in resp.results:
                yield ds
                fetched += 1
                if max_datasets is not None and fetched >= max_datasets:
                    return
            current_start += rows
            if current_start >= resp.count:
                break

