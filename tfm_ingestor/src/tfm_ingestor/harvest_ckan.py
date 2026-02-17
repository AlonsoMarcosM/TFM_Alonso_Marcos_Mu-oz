from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from tfm_ingestor.ckan import CkanApiError, CkanClient
from tfm_ingestor.config import CkanHarvestConfig, DefaultsConfig
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError
from tfm_ingestor.patch_ops import build_table_patch_ops


def _ckan_extras(dataset: dict[str, Any]) -> dict[str, str]:
    extras = dataset.get("extras") or []
    out: dict[str, str] = {}
    if not isinstance(extras, list):
        return out
    for item in extras:
        if not isinstance(item, dict):
            continue
        k = item.get("key")
        v = item.get("value")
        if not k or v is None:
            continue
        out[str(k)] = str(v)
    return out


def _ckan_tags(dataset: dict[str, Any]) -> list[str]:
    tags = dataset.get("tags") or []
    out: list[str] = []
    if not isinstance(tags, list):
        return out
    for t in tags:
        if not isinstance(t, dict):
            continue
        name = t.get("name") or t.get("display_name")
        if not name:
            continue
        out.append(str(name))
    return out


def _ckan_groups(dataset: dict[str, Any]) -> list[str]:
    groups = dataset.get("groups") or []
    out: list[str] = []
    if not isinstance(groups, list):
        return out
    for g in groups:
        if not isinstance(g, dict):
            continue
        name = g.get("name") or g.get("display_name") or g.get("title")
        if not name:
            continue
        out.append(str(name))
    return out


def _ckan_publisher_name(dataset: dict[str, Any]) -> str | None:
    org = dataset.get("organization")
    if isinstance(org, dict):
        title = org.get("title") or org.get("name")
        if title:
            return str(title)
    for k in ("author", "maintainer"):
        v = dataset.get(k)
        if v:
            return str(v)
    return None


def _ckan_contact_email(dataset: dict[str, Any]) -> str | None:
    for k in ("maintainer_email", "author_email"):
        v = dataset.get(k)
        if v:
            return str(v)
    return None


def _ckan_license(dataset: dict[str, Any]) -> str | None:
    for k in ("license_id", "license_title"):
        v = dataset.get(k)
        if v:
            return str(v)
    return None


def _ckan_created_modified(dataset: dict[str, Any]) -> tuple[str | None, str | None]:
    created = dataset.get("metadata_created")
    modified = dataset.get("metadata_modified")
    created_val = str(created).strip() if created else None
    modified_val = str(modified).strip() if modified else None
    return created_val or None, modified_val or None


def _ckan_landing_page(base_url: str, dataset: dict[str, Any]) -> str | None:
    name = dataset.get("name")
    if not name:
        return None
    return f"{base_url.rstrip('/')}/dataset/{name}"


def _choose_resource(dataset: dict[str, Any], resource_index: int) -> dict[str, Any] | None:
    resources = dataset.get("resources") or []
    if not isinstance(resources, list) or not resources:
        return None
    idx = resource_index if resource_index < len(resources) else 0
    r = resources[idx]
    if not isinstance(r, dict):
        return None
    return r


def _iter_datasets_with_fallback(
    *,
    base_urls: list[str],
    query: str,
    rows: int,
    start: int,
    max_datasets: int | None,
    api_key: str | None,
):
    last_error: Exception | None = None
    for base_url in base_urls:
        client = CkanClient(base_url=base_url, api_key=api_key)
        try:
            for ds in client.iter_datasets(query=query, rows=rows, start=start, max_datasets=max_datasets):
                yield ds
            return
        except CkanApiError as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error


@dataclass(frozen=True)
class CkanHarvestPlanItem:
    ckan_dataset: str
    table_fqn: str
    ops: list[dict[str, Any]]


def build_plan(
    *,
    ckan_cfg: CkanHarvestConfig,
    defaults: DefaultsConfig,
    om_tables_by_fqn: dict[str, dict[str, Any]],
    datasets: list[dict[str, Any]],
) -> tuple[list[CkanHarvestPlanItem], list[dict[str, Any]]]:
    planned: list[CkanHarvestPlanItem] = []
    skipped: list[dict[str, Any]] = []

    for ds in datasets:
        ds_name = str(ds.get("name") or ds.get("id") or "").strip()
        if not ds_name:
            skipped.append({"reason": "missing_dataset_id", "dataset": ds})
            continue

        # Map CKAN dataset -> OM table FQN (by name or id)
        table_fqn = ckan_cfg.dataset_to_table_fqn.get(str(ds.get("name"))) or ckan_cfg.dataset_to_table_fqn.get(str(ds.get("id")))  # type: ignore[arg-type]
        if not table_fqn:
            skipped.append({"reason": "no_mapping_for_dataset", "dataset": ds_name})
            continue

        table = om_tables_by_fqn.get(table_fqn)
        if not table:
            skipped.append({"reason": "table_not_found_in_om", "dataset": ds_name, "table_fqn": table_fqn})
            continue

        extras = _ckan_extras(ds)
        tags = _ckan_tags(ds)
        groups = _ckan_groups(ds)

        desired_tags: list[str] = []
        for t in tags:
            mapped = ckan_cfg.keyword_to_tag_fqn.get(t) or ckan_cfg.keyword_to_tag_fqn.get(t.lower())
            if mapped:
                desired_tags.append(mapped)
        for g in groups:
            mapped = ckan_cfg.theme_to_tag_fqn.get(g) or ckan_cfg.theme_to_tag_fqn.get(g.lower())
            if mapped:
                desired_tags.append(mapped)

        # DCAT-like custom properties
        cp: dict[str, str] = {}
        identifier = str(ds.get("id") or ds.get("name") or "").strip()
        if identifier:
            cp["dct_identifier"] = identifier

        landing = _ckan_landing_page(ckan_cfg.ckan.base_url, ds)
        if landing:
            cp["dcat_landing_page"] = landing

        cp["dcat_publisher_name"] = _ckan_publisher_name(ds) or defaults.catalog.publisher_name
        cp["dcat_contact_email"] = _ckan_contact_email(ds) or defaults.catalog.contact_email
        cp["dct_license"] = _ckan_license(ds) or defaults.catalog.license_default

        created, modified = _ckan_created_modified(ds)
        if created:
            cp["dct_issued"] = created
        if modified:
            cp["dct_modified"] = modified

        # Extra fields -> custom properties (configurable)
        for extra_key, prop_name in ckan_cfg.extras_to_custom_properties.items():
            v = extras.get(extra_key)
            if v:
                cp[prop_name] = v

        # Fallbacks for common DCAT-ish keys if not already set by extras mapping.
        if "dct_spatial" not in cp:
            cp["dct_spatial"] = extras.get("spatial") or defaults.catalog.spatial
        if "dct_language" not in cp:
            cp["dct_language"] = extras.get("language") or defaults.catalog.language
        if "dct_accrual_periodicity" not in cp:
            cp["dct_accrual_periodicity"] = extras.get("accrual_periodicity") or str(defaults.dataset_defaults.get("accrual_periodicity") or "")

        # Distribution (pick one resource for MVP)
        res = _choose_resource(ds, ckan_cfg.ckan.resource_index)
        if res:
            url = res.get("url")
            if url:
                cp["dcat_access_url"] = str(url)
                cp["dcat_download_url"] = str(url)

        desired_description = str(ds.get("notes") or "").strip() if ckan_cfg.write_description else None
        if desired_description == "":
            desired_description = None
        desired_display_name = str(ds.get("title") or "").strip() if ckan_cfg.write_display_name else None
        if desired_display_name == "":
            desired_display_name = None

        ops = build_table_patch_ops(
            table=table,
            desired_tag_fqns=desired_tags,
            desired_custom_properties=cp,
            desired_domain_ref=None,
            desired_description=desired_description,
            desired_display_name=desired_display_name,
        )
        if not ops:
            skipped.append({"reason": "no_changes", "dataset": ds_name, "table_fqn": table_fqn})
            continue

        planned.append(CkanHarvestPlanItem(ckan_dataset=ds_name, table_fqn=table_fqn, ops=ops))

    return planned, skipped


def run_harvest(
    *,
    ckan_cfg: CkanHarvestConfig,
    defaults: DefaultsConfig,
    om_api: OpenMetadataApi,
    dry_run: bool,
    limit_tables: int = 1000,
    datasets_input: list[dict[str, Any]] | None = None,
    write_datasets_path: str | None = None,
    ckan_api_key: str | None = None,
    max_datasets: int | None = None,
) -> dict[str, Any]:
    tables = om_api.list_tables(limit=limit_tables, fields="tags,extension")
    tables_by_fqn = {str(t.get("fullyQualifiedName")): t for t in tables if isinstance(t, dict) and t.get("fullyQualifiedName")}

    datasets: list[dict[str, Any]]
    if datasets_input is not None:
        datasets = [x for x in datasets_input if isinstance(x, dict)]
    else:
        base_urls = [ckan_cfg.ckan.base_url, *ckan_cfg.ckan.fallback_base_urls]
        effective_max = max_datasets if max_datasets is not None else ckan_cfg.ckan.max_datasets
        datasets = list(
            _iter_datasets_with_fallback(
                base_urls=base_urls,
                query=ckan_cfg.ckan.query,
                rows=ckan_cfg.ckan.rows,
                start=ckan_cfg.ckan.start,
                max_datasets=effective_max,
                api_key=ckan_api_key,
            )
        )

    if write_datasets_path:
        with open(write_datasets_path, "w", encoding="utf-8") as f:
            json.dump(datasets, f, indent=2, ensure_ascii=False)

    planned, skipped = build_plan(
        ckan_cfg=ckan_cfg,
        defaults=defaults,
        om_tables_by_fqn=tables_by_fqn,
        datasets=datasets,
    )

    applied = 0
    errors: list[dict[str, Any]] = []
    if not dry_run:
        for item in planned:
            table = tables_by_fqn.get(item.table_fqn) or {}
            table_id = table.get("id")
            if not table_id:
                errors.append({"dataset": item.ckan_dataset, "table_fqn": item.table_fqn, "error": "missing_table_id"})
                continue
            try:
                om_api.patch_table(table_id=str(table_id), patch_ops=item.ops)
                applied += 1
            except OpenMetadataApiError as exc:
                errors.append({"dataset": item.ckan_dataset, "table_fqn": item.table_fqn, "error": str(exc)})

    return {
        "dry_run": bool(dry_run),
        "datasets": {"count": len(datasets), "written_to": write_datasets_path},
        "planned": [{"ckan_dataset": x.ckan_dataset, "tableFQN": x.table_fqn, "ops": x.ops} for x in planned],
        "skipped": skipped,
        "applied": applied,
        "errors": errors,
    }
