from __future__ import annotations

import json
from typing import Any

from tfm_ingestor.config import DefaultsConfig, RulesConfig
from tfm_ingestor.om_api import OpenMetadataApi
from tfm_ingestor.patch_ops import existing_custom_properties, existing_tag_fqns


DCAT_CONTEXT: dict[str, Any] = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


def _tag_suffixes(tag_fqns: list[str], prefix: str) -> list[str]:
    out: list[str] = []
    for fqn in tag_fqns:
        if not fqn.startswith(prefix):
            continue
        out.append(fqn[len(prefix) :])
    # de-dupe keep order
    seen: set[str] = set()
    uniq: list[str] = []
    for v in out:
        if v in seen:
            continue
        seen.add(v)
        uniq.append(v)
    return uniq


def _publisher_node(name: str) -> dict[str, Any]:
    return {"@type": "foaf:Agent", "foaf:name": name}


def _contact_node(email: str) -> dict[str, Any]:
    email = email.strip()
    if email and not email.startswith("mailto:"):
        email = f"mailto:{email}"
    return {"@type": "vcard:Kind", "vcard:hasEmail": email}


def _as_id(url: str) -> dict[str, Any]:
    return {"@id": url}


def build_dataset_jsonld(*, table: dict[str, Any], defaults: DefaultsConfig) -> dict[str, Any] | None:
    fqn = str(table.get("fullyQualifiedName") or "").strip()
    name = str(table.get("displayName") or table.get("name") or "").strip()
    desc = str(table.get("description") or "").strip()
    if not fqn or not name:
        return None

    cp = existing_custom_properties(table)
    tags = existing_tag_fqns(table)

    keywords = _tag_suffixes(tags, "dcat_keyword.")
    themes = _tag_suffixes(tags, "dcat_theme.")
    if not themes:
        default_theme = defaults.dataset_defaults.get("theme_default")
        if isinstance(default_theme, list):
            themes = [str(x) for x in default_theme if str(x).strip()]
        elif isinstance(default_theme, str) and default_theme.strip():
            themes = [default_theme]

    dataset_id = cp.get("dct_identifier") or fqn
    landing_page = cp.get("dcat_landing_page")

    publisher_name = cp.get("dcat_publisher_name") or defaults.catalog.publisher_name
    contact_email = cp.get("dcat_contact_email") or defaults.catalog.contact_email

    out: dict[str, Any] = {
        "@type": "dcat:Dataset",
        "@id": landing_page or f"urn:openmetadata:table:{dataset_id}",
        "dct:identifier": dataset_id,
        "dct:title": name,
    }
    if desc:
        out["dct:description"] = desc

    if landing_page:
        out["dcat:landingPage"] = _as_id(landing_page)

    if publisher_name:
        out["dct:publisher"] = _publisher_node(publisher_name)
    if contact_email:
        out["dcat:contactPoint"] = _contact_node(contact_email)

    spatial = cp.get("dct_spatial") or defaults.catalog.spatial
    if spatial:
        out["dct:spatial"] = spatial

    language = cp.get("dct_language") or defaults.catalog.language
    if language:
        out["dct:language"] = language

    accrual = cp.get("dct_accrual_periodicity") or str(defaults.dataset_defaults.get("accrual_periodicity") or "")
    if accrual:
        out["dct:accrualPeriodicity"] = accrual

    if keywords:
        out["dcat:keyword"] = keywords
    if themes:
        out["dcat:theme"] = themes

    issued = cp.get("dct_issued")
    if issued:
        out["dct:issued"] = issued
    modified = cp.get("dct_modified")
    if modified:
        out["dct:modified"] = modified
    temporal = cp.get("dct_temporal")
    if temporal:
        out["dct:temporal"] = temporal

    access_url = cp.get("dcat_access_url")
    download_url = cp.get("dcat_download_url")
    endpoint_url = cp.get("dcat_endpoint_url")
    if access_url or download_url or endpoint_url:
        dist: dict[str, Any] = {"@type": "dcat:Distribution"}
        license_value = cp.get("dct_license") or defaults.catalog.license_default
        if license_value:
            dist["dct:license"] = license_value
        if access_url:
            dist["dcat:accessURL"] = _as_id(access_url)
        if download_url:
            dist["dcat:downloadURL"] = _as_id(download_url)
        if endpoint_url:
            dist["dcat:accessService"] = {"@type": "dcat:DataService", "dcat:endpointURL": _as_id(endpoint_url)}
        out["dcat:distribution"] = [dist]

    return out


def build_catalog_jsonld(*, tables: list[dict[str, Any]], defaults: DefaultsConfig) -> dict[str, Any]:
    datasets: list[dict[str, Any]] = []
    for t in tables:
        if not isinstance(t, dict):
            continue
        ds = build_dataset_jsonld(table=t, defaults=defaults)
        if ds is not None:
            datasets.append(ds)

    catalog_id = f"urn:tfm:catalog:{defaults.catalog.title}"
    catalog: dict[str, Any] = {
        "@type": "dcat:Catalog",
        "@id": catalog_id,
        "dct:title": defaults.catalog.title,
        "dct:description": defaults.catalog.description,
        "dct:publisher": _publisher_node(defaults.catalog.publisher_name),
        "dcat:contactPoint": _contact_node(defaults.catalog.contact_email),
        "foaf:homepage": _as_id(defaults.catalog.homepage),
        "dcat:themeTaxonomy": _as_id(defaults.catalog.theme_taxonomy),
        "dct:issued": defaults.catalog.issued,
        "dct:modified": defaults.catalog.modified,
        "dct:spatial": defaults.catalog.spatial,
        "dct:language": defaults.catalog.language,
        "dct:license": defaults.catalog.license_default,
    }
    if datasets:
        catalog["dcat:dataset"] = [{"@id": ds["@id"]} for ds in datasets if ds.get("@id")]

    return {"@context": DCAT_CONTEXT, "@graph": [catalog, *datasets]}


def _schema_name(table: dict[str, Any]) -> str | None:
    schema_ref = table.get("schema") or table.get("databaseSchema") or {}
    if isinstance(schema_ref, dict) and schema_ref.get("name"):
        return str(schema_ref["name"])
    return None


def export_catalog(
    *,
    defaults: DefaultsConfig,
    rules: RulesConfig,
    om_api: OpenMetadataApi | None = None,
    limit_tables: int = 1000,
    tables_input: list[dict[str, Any]] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    if tables_input is None and om_api is None:
        raise ValueError("export_catalog requires either tables_input or om_api")

    if tables_input is not None:
        tables = [x for x in tables_input if isinstance(x, dict)]
    else:
        tables = om_api.list_tables(limit=limit_tables, fields="tags,extension,databaseSchema,schema")  # type: ignore[union-attr]

    allowed_schemas = set(rules.schema_to_layer.keys())
    filtered = [t for t in tables if _schema_name(t) in allowed_schemas]

    doc = build_catalog_jsonld(tables=filtered, defaults=defaults)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

    return {
        "tables_total": len(tables),
        "tables_exported": len(filtered),
        "output_path": output_path,
        "preview_dataset_count": max(0, len(doc.get("@graph", [])) - 1),
    }
