from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote


HVD_CATEGORY_ALIAS_TO_URI = {
    "geoespacial": "http://data.europa.eu/bna/c_ac64a52d",
    "geospatial": "http://data.europa.eu/bna/c_ac64a52d",
    "observacion_de_la_tierra_y_medio_ambiente": "http://data.europa.eu/bna/c_dd313021",
    "observacion_tierra_medio_ambiente": "http://data.europa.eu/bna/c_dd313021",
    "earth_observation_environment": "http://data.europa.eu/bna/c_dd313021",
    "meteorologia": "http://data.europa.eu/bna/c_164e0bf5",
    "meteorological": "http://data.europa.eu/bna/c_164e0bf5",
    "estadistica": "http://data.europa.eu/bna/c_e1da4e07",
    "movilidad": "http://data.europa.eu/bna/c_b79e35eb",
    "mobility": "http://data.europa.eu/bna/c_b79e35eb",
    "estadisticas": "http://data.europa.eu/bna/c_e1da4e07",
    "statistics": "http://data.europa.eu/bna/c_e1da4e07",
    "sociedades_y_propiedad_de_sociedades": "http://data.europa.eu/bna/c_a9135398",
    "sociedades": "http://data.europa.eu/bna/c_a9135398",
    "empresas": "http://data.europa.eu/bna/c_a9135398",
    "companies_company_ownership": "http://data.europa.eu/bna/c_a9135398",
}
HVD_CATEGORY_URI_TO_ALIAS = {
    "http://data.europa.eu/bna/c_ac64a52d": "geoespacial",
    "http://data.europa.eu/bna/c_dd313021": "observacion_de_la_tierra_y_medio_ambiente",
    "http://data.europa.eu/bna/c_164e0bf5": "meteorologia",
    "http://data.europa.eu/bna/c_e1da4e07": "estadisticas",
    "http://data.europa.eu/bna/c_a9135398": "sociedades_y_propiedad_de_sociedades",
    "http://data.europa.eu/bna/c_b79e35eb": "movilidad",
}


def layer_for_schema(schema_name: str, schema_to_layer: dict[str, str]) -> str | None:
    return schema_to_layer.get(schema_name)


def domain_for_schema(schema_name: str, schema_to_domain: dict[str, str]) -> str | None:
    return schema_to_domain.get(schema_name)


def tags_for_table(table_name: str, tags_by_prefix: dict[str, list[str]]) -> list[str]:
    """
    Apply prefix rules deterministically:
    - For every prefix that matches, append its tags.
    - Preserve config order, then de-duplicate keeping first occurrence.
    """
    out: list[str] = []
    for prefix, tags in tags_by_prefix.items():
        if table_name.startswith(prefix):
            out.extend(tags)

    seen: set[str] = set()
    uniq: list[str] = []
    for t in out:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def merge_tag_fqns(existing: list[str], desired: list[str]) -> list[str]:
    seen = set(existing)
    merged = list(existing)
    for t in desired:
        if t not in seen:
            merged.append(t)
            seen.add(t)
    return merged


def build_distribution_access_url(*, base_url: str, schema_name: str, table_name: str) -> str:
    base = base_url.rstrip("/")
    schema = quote(schema_name.strip(), safe="")
    table = quote(table_name.strip().replace("_", "-"), safe="")
    return f"{base}/{schema}/{table}"


def normalize_hvd_category(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    alias_uri = HVD_CATEGORY_ALIAS_TO_URI.get(raw.lower())
    if alias_uri is not None:
        return alias_uri
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    supported = ", ".join(HVD_CATEGORY_URI_TO_ALIAS.values())
    raise ValueError(
        f"categoria_hvd invalida. Usa uno de estos alias: {supported}; "
        "o una URI http(s) completa del vocabulario HVD."
    )


def hvd_category_alias(uri: str) -> str:
    return HVD_CATEGORY_URI_TO_ALIAS.get(uri.strip(), uri.strip())


def hvd_category_for_tags(*, tag_fqns: list[str], dataset_defaults: dict[str, str]) -> str:
    raw_mapping = dataset_defaults.get("hvd_category_by_theme_tag", {}) or {}
    if not isinstance(raw_mapping, dict):
        return ""
    normalized_mapping: dict[str, str] = {}
    for key, value in raw_mapping.items():
        key_str = str(key).strip()
        value_str = str(value).strip()
        if not key_str or not value_str:
            continue
        normalized_mapping[key_str] = normalize_hvd_category(value_str)
    for tag_fqn in tag_fqns:
        uri = normalized_mapping.get(tag_fqn)
        if uri:
            return uri
    return ""


@dataclass(frozen=True)
class GovernanceSpec:
    layer: str | None
    domain_name: str | None
    tag_fqns: list[str]
    custom_properties: dict[str, str]


def build_governance_spec(
    *,
    schema_name: str,
    table_name: str,
    schema_to_layer: dict[str, str],
    schema_to_domain: dict[str, str],
    tags_by_prefix: dict[str, list[str]],
    catalog_defaults: dict[str, str],
    dataset_defaults: dict[str, str],
) -> GovernanceSpec:
    layer = layer_for_schema(schema_name, schema_to_layer)
    domain_name = domain_for_schema(schema_name, schema_to_domain)
    tag_fqns = tags_for_table(table_name, tags_by_prefix)

    # Minimal mandatory profile: keep only metadata required for Dataset.
    cp: dict[str, str] = {
        "dcat_publisher_name": catalog_defaults["publisher_name"],
    }
    access_url_base = str(dataset_defaults.get("access_url_base") or "").strip()
    if access_url_base:
        cp["dcat_access_url"] = build_distribution_access_url(
            base_url=access_url_base,
            schema_name=schema_name,
            table_name=table_name,
        )
    hvd_category = hvd_category_for_tags(tag_fqns=tag_fqns, dataset_defaults=dataset_defaults)
    if hvd_category:
        cp["dcat_hvd_category"] = hvd_category

    return GovernanceSpec(
        layer=layer,
        domain_name=domain_name,
        tag_fqns=tag_fqns,
        custom_properties=cp,
    )
