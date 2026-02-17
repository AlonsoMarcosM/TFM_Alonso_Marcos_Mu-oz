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
    homepage: str
    theme_taxonomy: str
    issued: str
    modified: str
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
        "homepage",
        "theme_taxonomy",
        "issued",
        "modified",
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
            homepage=str(catalog["homepage"]),
            theme_taxonomy=str(catalog["theme_taxonomy"]),
            issued=str(catalog["issued"]),
            modified=str(catalog["modified"]),
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


@dataclass(frozen=True)
class CkanConfig:
    base_url: str
    fallback_base_urls: list[str]
    query: str
    rows: int
    start: int
    resource_index: int
    max_datasets: int | None


@dataclass(frozen=True)
class CkanHarvestConfig:
    ckan: CkanConfig
    dataset_to_table_fqn: dict[str, str]
    keyword_to_tag_fqn: dict[str, str]
    theme_to_tag_fqn: dict[str, str]
    extras_to_custom_properties: dict[str, str]
    write_description: bool
    write_display_name: bool


def load_ckan_harvest(path: str | Path) -> CkanHarvestConfig:
    """
    Load CKAN harvesting config.

    YAML schema (MVP):
    - ckan.base_url (required)
    - mapping.dataset_to_table_fqn (required for patching OM)
    - mapping.keyword_to_tag_fqn (optional)
    - mapping.theme_to_tag_fqn (optional)
    - extras_to_custom_properties (optional)
    - behavior.write_description / behavior.write_display_name (optional)
    """
    p = Path(path)
    raw = _load_yaml(p)

    ckan_raw = raw.get("ckan")
    if not isinstance(ckan_raw, dict):
        raise ValueError(f"Missing/invalid 'ckan' in {p}")

    base_url = ckan_raw.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError(f"Missing/invalid 'ckan.base_url' in {p}")

    query = ckan_raw.get("query") or ""
    if not isinstance(query, str):
        raise ValueError(f"Invalid 'ckan.query' in {p} (must be string)")

    rows = ckan_raw.get("rows", 100)
    start = ckan_raw.get("start", 0)
    resource_index = ckan_raw.get("resource_index", 0)
    max_datasets = ckan_raw.get("max_datasets", None)
    for key, value in (("rows", rows), ("start", start), ("resource_index", resource_index)):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Invalid 'ckan.{key}' in {p} (must be int >= 0)")
    if max_datasets is not None and (not isinstance(max_datasets, int) or max_datasets <= 0):
        raise ValueError(f"Invalid 'ckan.max_datasets' in {p} (must be int > 0)")

    fallback_base_urls = ckan_raw.get("fallback_base_urls", []) or []
    if not isinstance(fallback_base_urls, list) or not all(isinstance(x, str) and x.strip() for x in fallback_base_urls):
        raise ValueError(f"Invalid 'ckan.fallback_base_urls' in {p} (must be list of strings)")

    mapping_raw = raw.get("mapping", {})
    if mapping_raw is None:
        mapping_raw = {}
    if not isinstance(mapping_raw, dict):
        raise ValueError(f"Invalid 'mapping' in {p} (must be mapping)")

    dataset_to_table_fqn = mapping_raw.get("dataset_to_table_fqn", {})
    if not isinstance(dataset_to_table_fqn, dict) or not dataset_to_table_fqn:
        raise ValueError(f"Missing/invalid 'mapping.dataset_to_table_fqn' in {p}")
    dataset_to_table_fqn_norm = {str(k): str(v) for k, v in dataset_to_table_fqn.items() if str(k).strip() and str(v).strip()}
    if not dataset_to_table_fqn_norm:
        raise ValueError(f"Invalid 'mapping.dataset_to_table_fqn' in {p} (empty after normalization)")

    keyword_to_tag_fqn = mapping_raw.get("keyword_to_tag_fqn", {}) or {}
    theme_to_tag_fqn = mapping_raw.get("theme_to_tag_fqn", {}) or {}
    if not isinstance(keyword_to_tag_fqn, dict):
        raise ValueError(f"Invalid 'mapping.keyword_to_tag_fqn' in {p} (must be mapping)")
    if not isinstance(theme_to_tag_fqn, dict):
        raise ValueError(f"Invalid 'mapping.theme_to_tag_fqn' in {p} (must be mapping)")

    extras_to_custom_properties = raw.get("extras_to_custom_properties", {}) or {}
    if not isinstance(extras_to_custom_properties, dict):
        raise ValueError(f"Invalid 'extras_to_custom_properties' in {p} (must be mapping)")

    behavior = raw.get("behavior", {}) or {}
    if not isinstance(behavior, dict):
        raise ValueError(f"Invalid 'behavior' in {p} (must be mapping)")

    write_description = behavior.get("write_description", True)
    write_display_name = behavior.get("write_display_name", True)
    if not isinstance(write_description, bool):
        raise ValueError(f"Invalid 'behavior.write_description' in {p} (must be bool)")
    if not isinstance(write_display_name, bool):
        raise ValueError(f"Invalid 'behavior.write_display_name' in {p} (must be bool)")

    return CkanHarvestConfig(
        ckan=CkanConfig(
            base_url=str(base_url).rstrip("/"),
            fallback_base_urls=[str(x).rstrip("/") for x in fallback_base_urls],
            query=str(query),
            rows=int(rows),
            start=int(start),
            resource_index=int(resource_index),
            max_datasets=int(max_datasets) if max_datasets is not None else None,
        ),
        dataset_to_table_fqn=dataset_to_table_fqn_norm,
        keyword_to_tag_fqn={str(k): str(v) for k, v in keyword_to_tag_fqn.items() if str(k).strip() and str(v).strip()},
        theme_to_tag_fqn={str(k): str(v) for k, v in theme_to_tag_fqn.items() if str(k).strip() and str(v).strip()},
        extras_to_custom_properties={str(k): str(v) for k, v in extras_to_custom_properties.items() if str(k).strip() and str(v).strip()},
        write_description=bool(write_description),
        write_display_name=bool(write_display_name),
    )
