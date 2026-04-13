from __future__ import annotations

import json
from typing import Any

from tfm_ingestor.config import DefaultsConfig, RulesConfig
from tfm_ingestor.mapping import build_distribution_access_url, hvd_category_for_tags, normalize_hvd_category
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError
from tfm_ingestor.patch_ops import existing_custom_properties, existing_tag_fqns


DCAT_CONTEXT: dict[str, Any] = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcatap": "http://data.europa.eu/r5r/",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

THEME_TAXONOMY_BASE_URI = "http://datos.gob.es/kos/sector-publico/sector"
THEME_TAG_TO_URI = {
    "transporte": f"{THEME_TAXONOMY_BASE_URI}/transporte",
    "transport": f"{THEME_TAXONOMY_BASE_URI}/transporte",
    "cultura_ocio": f"{THEME_TAXONOMY_BASE_URI}/cultura-ocio",
    "society": f"{THEME_TAXONOMY_BASE_URI}/sociedad-bienestar",
}


def _tag_suffixes(tag_fqns: list[str], prefix: str) -> list[str]:
    out: list[str] = []
    for fqn in tag_fqns:
        if not fqn.startswith(prefix):
            continue
        out.append(fqn[len(prefix) :])
    seen: set[str] = set()
    uniq: list[str] = []
    for value in out:
        if value in seen:
            continue
        seen.add(value)
        uniq.append(value)
    return uniq


def _lang_literal_es(value: str) -> dict[str, str]:
    return {"@value": value, "@language": "es"}


def _typed_date(value: str) -> dict[str, str]:
    return {"@value": value, "@type": "xsd:date"}


def _publisher_node(*, publisher_uri: str, publisher_name: str) -> dict[str, Any]:
    return {
        "@id": publisher_uri,
        "@type": "foaf:Organization",
        "foaf:name": _lang_literal_es(publisher_name),
    }


def _as_id(url: str) -> dict[str, Any]:
    return {"@id": url}


def _as_id_list(*uris: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for uri in uris:
        value = uri.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(_as_id(value))
    return out


def _theme_ids_from_tags(tag_fqns: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in _tag_suffixes(tag_fqns, "dcat_theme."):
        theme_uri = THEME_TAG_TO_URI.get(raw)
        if theme_uri is None:
            theme_uri = f"{THEME_TAXONOMY_BASE_URI}/{raw.replace('_', '-')}"
        if theme_uri in seen:
            continue
        seen.add(theme_uri)
        out.append(_as_id(theme_uri))
    return out


def _schema_name(table: dict[str, Any]) -> str | None:
    schema_ref = table.get("schema") or table.get("databaseSchema") or {}
    if isinstance(schema_ref, dict) and schema_ref.get("name"):
        return str(schema_ref["name"])
    return None


def _table_slug(*, table: dict[str, Any]) -> tuple[str, str] | None:
    schema_name = _schema_name(table) or ""
    table_name = str(table.get("name") or "").strip()
    if not schema_name or not table_name:
        return None
    return schema_name, table_name


def _distribution_access_url(*, table: dict[str, Any], defaults: DefaultsConfig) -> str | None:
    cp = existing_custom_properties(table)
    access_url = str(cp.get("dcat_access_url") or "").strip()
    if not access_url:
        slug = _table_slug(table=table)
        access_url_base = str(defaults.dataset_defaults.get("access_url_base") or "").strip()
        if access_url_base and slug is not None:
            access_url = build_distribution_access_url(
                base_url=access_url_base,
                schema_name=slug[0],
                table_name=slug[1],
            )
    if access_url.startswith("http://") or access_url.startswith("https://"):
        return access_url
    return None


def _derived_url(*, base_url: str, table: dict[str, Any]) -> str | None:
    value = base_url.strip()
    slug = _table_slug(table=table)
    if not value or slug is None:
        return None
    return build_distribution_access_url(
        base_url=value,
        schema_name=slug[0],
        table_name=slug[1],
    )


def _hvd_enabled(defaults: DefaultsConfig) -> bool:
    return bool(defaults.hvd_defaults.get("enabled", False))


def _hvd_applicable_legislation(defaults: DefaultsConfig) -> str:
    return str(defaults.hvd_defaults.get("applicable_legislation") or "").strip()


def _hvd_license(defaults: DefaultsConfig) -> str:
    return str(defaults.hvd_defaults.get("distribution_license") or "").strip()


def _hvd_access_rights(defaults: DefaultsConfig) -> str:
    return str(defaults.hvd_defaults.get("access_rights") or "").strip()


def _hvd_category_uri(*, table: dict[str, Any], tags: list[str], defaults: DefaultsConfig) -> str:
    cp = existing_custom_properties(table)
    explicit = str(cp.get("dcat_hvd_category") or "").strip()
    if explicit:
        return normalize_hvd_category(explicit)
    return hvd_category_for_tags(tag_fqns=tags, dataset_defaults=defaults.dataset_defaults)


def _contact_point_node(*, defaults: DefaultsConfig) -> dict[str, Any] | None:
    raw = defaults.hvd_defaults.get("contact", {}) or {}
    if not isinstance(raw, dict):
        return None

    name = str(raw.get("fn") or "").strip()
    organization_name = str(raw.get("organization_name") or defaults.catalog.publisher_name).strip()
    uid = str(raw.get("has_uid") or defaults.catalog.publisher_uri).strip()
    email = str(raw.get("has_email") or "").strip()
    url = str(raw.get("has_url") or "").strip()
    telephone = str(raw.get("has_telephone") or "").strip()

    if not name or not (email or url):
        return None

    node: dict[str, Any] = {
        "@type": "vcard:Kind",
        "vcard:organization-name": _lang_literal_es(organization_name),
        "vcard:fn": _lang_literal_es(name),
        "vcard:hasUID": _as_id(uid),
    }
    if email:
        node["vcard:hasEmail"] = _as_id(email)
    if url:
        node["vcard:hasURL"] = _as_id(url)
    if telephone:
        node["vcard:hasTelephone"] = _as_id(telephone)
    return node


def _build_hvd_service_node(
    *,
    table: dict[str, Any],
    defaults: DefaultsConfig,
    dataset_id: str,
    dataset_title: str,
    publisher_name: str,
    themes: list[dict[str, Any]],
    hvd_category_uri: str,
) -> dict[str, Any] | None:
    legislation_uri = _hvd_applicable_legislation(defaults)
    license_uri = _hvd_license(defaults)
    access_rights_uri = _hvd_access_rights(defaults)
    contact_point = _contact_point_node(defaults=defaults)
    endpoint_url = _derived_url(
        base_url=str(defaults.hvd_defaults.get("service_endpoint_url_base") or ""),
        table=table,
    )
    endpoint_description = _derived_url(
        base_url=str(defaults.hvd_defaults.get("service_endpoint_description_base") or ""),
        table=table,
    )
    documentation_url = _derived_url(
        base_url=str(defaults.hvd_defaults.get("service_documentation_base") or ""),
        table=table,
    )
    if not (legislation_uri and license_uri and endpoint_url and endpoint_description and documentation_url and contact_point):
        return None

    service_id = f"{dataset_id}:service"
    node: dict[str, Any] = {
        "@type": "dcat:DataService",
        "@id": service_id,
        "dct:title": _lang_literal_es(f"Servicio de datos HVD de {dataset_title}"),
        "dcat:theme": themes,
        "dct:publisher": _publisher_node(
            publisher_uri=defaults.catalog.publisher_uri,
            publisher_name=publisher_name,
        ),
        "dcat:endpointURL": [_as_id(endpoint_url)],
        "dcat:endpointDescription": [_as_id(endpoint_description)],
        "dcat:contactPoint": [contact_point],
        "dcatap:applicableLegislation": _as_id_list(legislation_uri),
        "dcatap:hvdCategory": _as_id_list(hvd_category_uri),
        "foaf:page": [_as_id(documentation_url)],
        "dcat:servesDataset": [_as_id(dataset_id)],
        "dct:license": _as_id(license_uri),
    }
    if access_rights_uri:
        node["dct:accessRights"] = _as_id(access_rights_uri)
    return node


def build_dataset_graph_nodes(*, table: dict[str, Any], defaults: DefaultsConfig) -> list[dict[str, Any]]:
    fqn = str(table.get("fullyQualifiedName") or "").strip()
    name = str(table.get("displayName") or table.get("name") or "").strip()
    desc = str(table.get("description") or "").strip()
    if not fqn or not name:
        return []

    cp = existing_custom_properties(table)
    tags = existing_tag_fqns(table)

    themes = _theme_ids_from_tags(tags)
    distribution_access_url = _distribution_access_url(table=table, defaults=defaults)
    publisher_name = str(cp.get("dcat_publisher_name") or defaults.catalog.publisher_name).strip()
    if not desc or not publisher_name or not themes or not distribution_access_url:
        return []

    dataset_id = f"urn:openmetadata:table:{fqn}"
    distribution_id = f"{dataset_id}:distribution"
    dataset: dict[str, Any] = {
        "@type": "dcat:Dataset",
        "@id": dataset_id,
        "dct:title": _lang_literal_es(name),
        "dct:description": _lang_literal_es(desc),
        "dct:publisher": _publisher_node(
            publisher_uri=defaults.catalog.publisher_uri,
            publisher_name=publisher_name,
        ),
        "dcat:theme": themes,
        "dcat:distribution": [_as_id(distribution_id)],
    }
    distribution: dict[str, Any] = {
        "@type": "dcat:Distribution",
        "@id": distribution_id,
        "dcat:accessURL": [_as_id(distribution_access_url)],
    }

    nodes: list[dict[str, Any]] = [dataset, distribution]
    if not _hvd_enabled(defaults):
        return nodes

    legislation_uri = _hvd_applicable_legislation(defaults)
    hvd_category_uri = _hvd_category_uri(table=table, tags=tags, defaults=defaults)
    license_uri = _hvd_license(defaults)
    if not (legislation_uri and hvd_category_uri and license_uri):
        return []

    service = _build_hvd_service_node(
        table=table,
        defaults=defaults,
        dataset_id=dataset_id,
        dataset_title=name,
        publisher_name=publisher_name,
        themes=themes,
        hvd_category_uri=hvd_category_uri,
    )
    if service is None:
        return []

    dataset["dcatap:applicableLegislation"] = _as_id_list(legislation_uri)
    dataset["dcatap:hvdCategory"] = _as_id_list(hvd_category_uri)
    distribution["dcatap:applicableLegislation"] = _as_id_list(legislation_uri)
    distribution["dct:license"] = _as_id(license_uri)
    distribution["dcat:accessService"] = [_as_id(str(service["@id"]))]
    nodes.append(service)
    return nodes


def build_catalog_jsonld(*, tables: list[dict[str, Any]], defaults: DefaultsConfig) -> dict[str, Any]:
    graph_nodes: list[dict[str, Any]] = []
    datasets: list[dict[str, Any]] = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        nodes = build_dataset_graph_nodes(table=table, defaults=defaults)
        if not nodes:
            continue
        graph_nodes.extend(nodes)
        datasets.extend(
            node for node in nodes if isinstance(node, dict) and node.get("@type") == "dcat:Dataset" and node.get("@id")
        )

    catalog_id = f"urn:tfm:catalog:{defaults.catalog.title}"
    catalog: dict[str, Any] = {
        "@type": "dcat:Catalog",
        "@id": catalog_id,
        "dct:title": _lang_literal_es(defaults.catalog.title),
        "dct:description": _lang_literal_es(defaults.catalog.description),
        "dct:publisher": _publisher_node(
            publisher_uri=defaults.catalog.publisher_uri,
            publisher_name=defaults.catalog.publisher_name,
        ),
        "foaf:homepage": _as_id(defaults.catalog.homepage),
        "dcat:themeTaxonomy": _as_id(defaults.catalog.theme_taxonomy),
        "dct:issued": _typed_date(defaults.catalog.issued),
        "dct:modified": _typed_date(defaults.catalog.modified),
        "dct:language": _as_id(defaults.catalog.language),
        "dct:license": _as_id(defaults.catalog.license_default),
    }
    if datasets:
        catalog["dcat:dataset"] = [_as_id(str(ds["@id"])) for ds in datasets]

    return {"@context": DCAT_CONTEXT, "@graph": [catalog, *graph_nodes]}


def _list_tables_for_export(*, om_api: OpenMetadataApi, limit_tables: int) -> list[dict[str, Any]]:
    field_candidates = [
        "tags,extension,databaseSchema,schema",
        "tags,extension,databaseSchema",
        "tags,extension,schema",
        "tags,extension",
    ]
    last_error: OpenMetadataApiError | None = None

    for fields in field_candidates:
        try:
            return om_api.list_tables(limit=limit_tables, fields=fields)
        except OpenMetadataApiError as exc:
            last_error = exc
            if "Invalid field name" in str(exc):
                continue
            raise

    if last_error is not None:
        raise last_error
    return []


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
        tables = _list_tables_for_export(om_api=om_api, limit_tables=limit_tables)  # type: ignore[arg-type]

    allowed_schemas = set(rules.schema_to_layer.keys())
    filtered = [t for t in tables if _schema_name(t) in allowed_schemas]

    doc = build_catalog_jsonld(tables=filtered, defaults=defaults)
    preview_dataset_count = len(
        [x for x in doc.get("@graph", []) if isinstance(x, dict) and x.get("@type") == "dcat:Dataset"]
    )
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file_obj:
            json.dump(doc, file_obj, indent=2, ensure_ascii=False)

    return {
        "tables_total": len(tables),
        "tables_exported": preview_dataset_count,
        "output_path": output_path,
        "preview_dataset_count": preview_dataset_count,
    }
