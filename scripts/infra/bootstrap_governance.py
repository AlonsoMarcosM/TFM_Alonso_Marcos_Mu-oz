from __future__ import annotations

import argparse
import json
from typing import Any

import requests


class OmApiError(RuntimeError):
    pass


class OmApi:
    def __init__(self, *, base_url: str, token: str, timeout_s: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"
        try:
            r = self.session.request(method, url, timeout=self.timeout_s, **kwargs)
        except requests.RequestException as exc:
            raise OmApiError(str(exc)) from exc
        if r.status_code >= 400:
            raise OmApiError(f"{method} {path} -> {r.status_code}\n{r.text[:2000]}")
        if not r.content:
            return {}
        return r.json()

    def list_classifications(self) -> dict[str, dict[str, Any]]:
        data = self._request("GET", "/classifications", params={"limit": 1000})
        items = data.get("data", [])
        return {str(x["name"]): x for x in items if isinstance(x, dict) and x.get("name")}

    def create_classification(self, *, name: str, description: str) -> dict[str, Any]:
        return self._request("POST", "/classifications", json={"name": name, "description": description})

    def list_tags(self) -> set[str]:
        data = self._request("GET", "/tags", params={"limit": 1000})
        items = data.get("data", [])
        out: set[str] = set()
        for x in items:
            if isinstance(x, dict) and x.get("fullyQualifiedName"):
                out.add(str(x["fullyQualifiedName"]))
        return out

    def create_tag(self, *, classification: str, name: str, description: str) -> dict[str, Any]:
        body = {"classification": classification, "name": name, "description": description}
        return self._request("POST", "/tags", json=body)

    def get_type(self, *, name: str, fields: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if fields:
            params["fields"] = fields
        return self._request("GET", f"/metadata/types/name/{name}", params=params)

    def add_custom_property(
        self,
        *,
        entity_type_id: str,
        property_name: str,
        property_description: str,
        field_type_id: str,
        field_type_name: str,
    ) -> dict[str, Any]:
        body = {
            "name": property_name,
            "description": property_description,
            "propertyType": {
                "id": field_type_id,
                "type": "type",
                "name": field_type_name,
            },
        }
        return self._request("PUT", f"/metadata/types/{entity_type_id}", json=body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create OpenMetadata classifications/tags/custom properties for TFM PoC")
    parser.add_argument("--base-url", default="http://localhost:8585/api/v1")
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    api = OmApi(base_url=args.base_url, token=args.token)

    required_classifications = [
        ("dcat_theme", "DCAT theme tags for the TFM PoC"),
        ("dcat_keyword", "DCAT keyword tags for the TFM PoC"),
    ]
    required_tags = [
        ("dcat_theme", "transport", "DCAT theme: transport"),
        ("dcat_theme", "society", "DCAT theme: society"),
        ("dcat_keyword", "bici", "DCAT keyword: bici"),
        ("dcat_keyword", "eventos", "DCAT keyword: eventos"),
    ]
    required_custom_properties = [
        ("dcat_publisher_name", "DCAT publisher name"),
        ("dcat_contact_email", "DCAT contact email"),
        ("dct_spatial", "DCAT spatial coverage"),
        ("dct_language", "DCAT language"),
        ("dct_license", "DCAT license"),
        ("dct_accrual_periodicity", "DCAT accrual periodicity"),
        ("tfm_layer", "TFM logical layer (Bronze/Silver/Gold)"),
    ]

    summary: dict[str, Any] = {
        "classifications_created": [],
        "classifications_existing": [],
        "tags_created": [],
        "tags_existing": [],
        "custom_properties_created": [],
        "custom_properties_existing": [],
    }

    existing_classifications = api.list_classifications()
    for name, description in required_classifications:
        if name in existing_classifications:
            summary["classifications_existing"].append(name)
            continue
        api.create_classification(name=name, description=description)
        summary["classifications_created"].append(name)

    existing_tags = api.list_tags()
    for classification, tag_name, description in required_tags:
        fqn = f"{classification}.{tag_name}"
        if fqn in existing_tags:
            summary["tags_existing"].append(fqn)
            continue
        api.create_tag(classification=classification, name=tag_name, description=description)
        summary["tags_created"].append(fqn)

    table_type = api.get_type(name="table", fields="customProperties")
    string_type = api.get_type(name="string")

    table_type_id = str(table_type["id"])
    string_type_id = str(string_type["id"])
    string_type_name = str(string_type["name"])

    existing_props = {
        str(cp["name"])
        for cp in (table_type.get("customProperties") or [])
        if isinstance(cp, dict) and cp.get("name")
    }
    for prop_name, prop_description in required_custom_properties:
        if prop_name in existing_props:
            summary["custom_properties_existing"].append(prop_name)
            continue
        updated_type = api.add_custom_property(
            entity_type_id=table_type_id,
            property_name=prop_name,
            property_description=prop_description,
            field_type_id=string_type_id,
            field_type_name=string_type_name,
        )
        existing_props = {
            str(cp["name"])
            for cp in (updated_type.get("customProperties") or [])
            if isinstance(cp, dict) and cp.get("name")
        }
        summary["custom_properties_created"].append(prop_name)

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
