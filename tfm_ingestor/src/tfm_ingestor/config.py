from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping at top-level: {path}")
    return data


@dataclass(frozen=True)
class CatalogDefaults:
    title: str
    description: str
    publisher_name: str
    contact_email: str
    spatial: str
    language: str
    license_default: str


@dataclass(frozen=True)
class DefaultsConfig:
    catalog: CatalogDefaults
    dataset_defaults: dict[str, Any]


def load_defaults(path: str | Path) -> DefaultsConfig:
    p = Path(path)
    raw = _load_yaml(p)

    catalog = raw.get("catalog")
    if not isinstance(catalog, dict):
        raise ValueError(f"Missing/invalid 'catalog' in {p}")

    required = [
        "title",
        "description",
        "publisher_name",
        "contact_email",
        "spatial",
        "language",
        "license_default",
    ]
    missing = [k for k in required if not catalog.get(k)]
    if missing:
        raise ValueError(f"Missing required catalog keys in {p}: {missing}")

    dataset_defaults = raw.get("dataset_defaults", {})
    if dataset_defaults is None:
        dataset_defaults = {}
    if not isinstance(dataset_defaults, dict):
        raise ValueError(f"Invalid 'dataset_defaults' in {p} (must be mapping)")

    return DefaultsConfig(
        catalog=CatalogDefaults(
            title=str(catalog["title"]),
            description=str(catalog["description"]),
            publisher_name=str(catalog["publisher_name"]),
            contact_email=str(catalog["contact_email"]),
            spatial=str(catalog["spatial"]),
            language=str(catalog["language"]),
            license_default=str(catalog["license_default"]),
        ),
        dataset_defaults=dataset_defaults,
    )


@dataclass(frozen=True)
class RulesConfig:
    schema_to_layer: dict[str, str]
    schema_to_domain: dict[str, str]
    table_tags_by_prefix: dict[str, list[str]]


def load_rules(path: str | Path) -> RulesConfig:
    p = Path(path)
    raw = _load_yaml(p)

    schema_to_layer = raw.get("schema_to_layer", {})
    schema_to_domain = raw.get("schema_to_domain", {})
    table_tags_by_prefix = raw.get("table_tags_by_prefix", {})

    if not isinstance(schema_to_layer, dict) or not schema_to_layer:
        raise ValueError(f"Missing/invalid 'schema_to_layer' in {p}")
    if not isinstance(schema_to_domain, dict) or not schema_to_domain:
        raise ValueError(f"Missing/invalid 'schema_to_domain' in {p}")
    if not isinstance(table_tags_by_prefix, dict):
        raise ValueError(f"Invalid 'table_tags_by_prefix' in {p}")

    # Ensure lists of strings
    normalized_tags: dict[str, list[str]] = {}
    for prefix, tags in table_tags_by_prefix.items():
        if not isinstance(prefix, str) or not prefix:
            raise ValueError(f"Invalid prefix in {p}: {prefix!r}")
        if tags is None:
            normalized_tags[prefix] = []
            continue
        if not isinstance(tags, list) or not all(isinstance(t, str) and t for t in tags):
            raise ValueError(f"Invalid tags list for prefix {prefix!r} in {p}")
        normalized_tags[prefix] = tags

    return RulesConfig(
        schema_to_layer={str(k): str(v) for k, v in schema_to_layer.items()},
        schema_to_domain={str(k): str(v) for k, v in schema_to_domain.items()},
        table_tags_by_prefix=normalized_tags,
    )

