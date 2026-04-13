from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from tfm_ingestor.ckan import CkanApiError, CkanClient
from tfm_ingestor.config import CkanHarvestConfig, DefaultsConfig
from tfm_ingestor.mapping import hvd_category_for_tags
from tfm_ingestor.om_api import OpenMetadataApi, OpenMetadataApiError
from tfm_ingestor.patch_ops import build_table_patch_ops


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


def _ckan_distribution_access_url(dataset: dict[str, Any], *, resource_index: int) -> str | None:
    resources = dataset.get("resources") or []
    if isinstance(resources, list) and resources:
        if 0 <= resource_index < len(resources):
            resource = resources[resource_index]
            if isinstance(resource, dict):
                for key in ("access_url", "download_url", "url"):
                    value = resource.get(key)
                    if value:
                        return str(value).strip()
        for resource in resources:
            if not isinstance(resource, dict):
                continue
            for key in ("access_url", "download_url", "url"):
                value = resource.get(key)
                if value:
                    return str(value).strip()
    dataset_url = dataset.get("url")
    if dataset_url:
        return str(dataset_url).strip()
    return None


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

        groups = _ckan_groups(ds)

        desired_tags: list[str] = []
        for g in groups:
            mapped = ckan_cfg.theme_to_tag_fqn.get(g) or ckan_cfg.theme_to_tag_fqn.get(g.lower())
            if mapped:
                desired_tags.append(mapped)

        # Minimal mandatory profile for the active HVD profile:
        # publisher + HVD category + at least one distribution with access URL.
        cp: dict[str, str] = {}
        cp["dcat_publisher_name"] = _ckan_publisher_name(ds) or defaults.catalog.publisher_name
        hvd_category = hvd_category_for_tags(tag_fqns=desired_tags, dataset_defaults=defaults.dataset_defaults)
        if hvd_category:
            cp["dcat_hvd_category"] = hvd_category
        access_url = _ckan_distribution_access_url(ds, resource_index=ckan_cfg.ckan.resource_index)
        if access_url:
            cp["dcat_access_url"] = access_url

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
            managed_custom_property_keys=[
                "dcat_publisher_name",
                "dcat_hvd_category",
                "dcat_contact_email",
                "dct_spatial",
                "dct_language",
                "dct_license",
                "dct_issued",
                "dct_modified",
                "dct_temporal",
                "dct_accrual_periodicity",
                "dcat_access_url",
                "dcat_download_url",
                "dcat_endpoint_url",
                "dcat_landing_page",
                "dct_identifier",
                "tfm_layer",
            ],
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
