from __future__ import annotations

from dataclasses import dataclass


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

    # "DCAT-like" custom properties kept intentionally small for the PoC.
    cp: dict[str, str] = {
        "dcat_publisher_name": catalog_defaults["publisher_name"],
        "dcat_contact_email": catalog_defaults["contact_email"],
        "dct_spatial": catalog_defaults["spatial"],
        "dct_language": catalog_defaults["language"],
        "dct_license": catalog_defaults["license_default"],
    }

    accrual = dataset_defaults.get("accrual_periodicity")
    if accrual:
        cp["dct_accrual_periodicity"] = str(accrual)

    if layer:
        cp["tfm_layer"] = layer

    return GovernanceSpec(
        layer=layer,
        domain_name=domain_name,
        tag_fqns=tag_fqns,
        custom_properties=cp,
    )

