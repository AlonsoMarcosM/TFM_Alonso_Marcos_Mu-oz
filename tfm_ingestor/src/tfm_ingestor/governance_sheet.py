from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from tfm_ingestor.config import DefaultsConfig
from tfm_ingestor.mapping import (
    build_distribution_access_url,
    hvd_category_alias,
    hvd_category_for_tags,
    normalize_hvd_category,
    tags_for_table,
)
from tfm_ingestor.patch_ops import existing_custom_properties, existing_tag_fqns


SHEET_FIELDNAMES = [
    "publicar",
    "schema_name",
    "table_name",
    "table_fqn",
    "titulo_dataset",
    "descripcion_dataset",
    "publicador",
    "tematica_dcat",
    "categoria_hvd",
    "access_url_distribucion",
]

NTI_RISP_SECTOR_SLUGS = [
    "ciencia-tecnologia",
    "comercio",
    "cultura-ocio",
    "demografia",
    "deporte",
    "economia",
    "educacion",
    "empleo",
    "energia",
    "hacienda",
    "industria",
    "legislacion-justicia",
    "medio-ambiente",
    "medio-rural-pesca",
    "salud",
    "sector-publico",
    "seguridad",
    "sociedad-bienestar",
    "transporte",
    "turismo",
    "urbanismo-infraestructuras",
    "vivienda",
]

THEME_ALIAS_TO_TAG_FQN = {
    alias: f"dcat_theme.{slug.replace('-', '_')}"
    for slug in NTI_RISP_SECTOR_SLUGS
    for alias in {slug, slug.replace("-", "_"), slug.replace("-", " ")}
}

THEME_TAG_FQN_TO_ALIAS = {
    f"dcat_theme.{slug.replace('-', '_')}": slug.replace("-", "_") for slug in NTI_RISP_SECTOR_SLUGS
}


@dataclass(frozen=True)
class GovernanceSheetRow:
    publish: bool
    schema_name: str
    table_name: str
    table_fqn: str
    title: str
    description: str
    publisher_name: str
    theme_tag_fqns: list[str]
    hvd_category_uri: str
    distribution_access_url: str


def _schema_name(table: dict[str, Any]) -> str | None:
    schema_ref = table.get("schema") or table.get("databaseSchema") or {}
    if isinstance(schema_ref, dict) and schema_ref.get("name"):
        return str(schema_ref["name"])
    return None


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "si", "sí", "s", "x", "yes", "y"}


def _normalize_theme_list(raw: str, *, row_num: int) -> list[str]:
    if not raw.strip():
        return []
    parts = [x.strip() for x in raw.split(",") if x.strip()]
    out: list[str] = []
    for part in parts:
        normalized = THEME_ALIAS_TO_TAG_FQN.get(part.lower(), part)
        if not normalized.startswith("dcat_theme."):
            raise ValueError(
                f"Fila {row_num}: tematica_dcat invalida {part!r}. Usa un sector NTI-RISP soportado."
            )
        if normalized not in THEME_TAG_FQN_TO_ALIAS:
            allowed = ", ".join(THEME_TAG_FQN_TO_ALIAS.values())
            raise ValueError(
                f"Fila {row_num}: tematica_dcat invalida {part!r}. Valores permitidos: {allowed}."
            )
        out.append(normalized)
    seen: set[str] = set()
    deduped: list[str] = []
    for item in out:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _validate_http_url(raw: str, *, row_num: int) -> str:
    value = raw.strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Fila {row_num}: access_url_distribucion debe ser una URL http(s) válida")
    return value


def _normalize_hvd_category(raw: str, *, row_num: int) -> str:
    value = raw.strip()
    if not value:
        return ""
    try:
        return normalize_hvd_category(value)
    except ValueError as exc:
        raise ValueError(f"Fila {row_num}: {exc}") from exc


def load_governance_sheet(path: str | Path) -> list[GovernanceSheetRow]:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        if reader.fieldnames is None:
            raise ValueError(f"CSV vacío o sin cabecera: {p}")
        missing = [name for name in SHEET_FIELDNAMES if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"Faltan columnas requeridas en {p}: {missing}")

        rows: list[GovernanceSheetRow] = []
        for idx, raw_row in enumerate(reader, start=2):
            publish = _as_bool(str(raw_row.get("publicar") or ""))
            schema_name = str(raw_row.get("schema_name") or "").strip()
            table_name = str(raw_row.get("table_name") or "").strip()
            table_fqn = str(raw_row.get("table_fqn") or "").strip()
            title = str(raw_row.get("titulo_dataset") or "").strip()
            description = str(raw_row.get("descripcion_dataset") or "").strip()
            publisher_name = str(raw_row.get("publicador") or "").strip()
            theme_tag_fqns = _normalize_theme_list(str(raw_row.get("tematica_dcat") or ""), row_num=idx)
            hvd_category_uri = _normalize_hvd_category(str(raw_row.get("categoria_hvd") or ""), row_num=idx)
            distribution_access_url = _validate_http_url(str(raw_row.get("access_url_distribucion") or ""), row_num=idx)

            if not table_fqn and not (schema_name and table_name):
                raise ValueError(f"Fila {idx}: debe existir table_fqn o bien schema_name + table_name")

            if publish:
                if not table_name:
                    raise ValueError(f"Fila {idx}: table_name es obligatorio cuando publicar=si")
                if not title:
                    raise ValueError(f"Fila {idx}: titulo_dataset es obligatorio cuando publicar=si")
                if not description:
                    raise ValueError(f"Fila {idx}: descripcion_dataset es obligatoria cuando publicar=si")
                if not theme_tag_fqns:
                    raise ValueError(f"Fila {idx}: tematica_dcat es obligatoria cuando publicar=si")
                if not hvd_category_uri:
                    raise ValueError(f"Fila {idx}: categoria_hvd es obligatoria cuando publicar=si")
                if not distribution_access_url:
                    raise ValueError(f"Fila {idx}: access_url_distribucion es obligatoria cuando publicar=si")

            rows.append(
                GovernanceSheetRow(
                    publish=publish,
                    schema_name=schema_name,
                    table_name=table_name,
                    table_fqn=table_fqn,
                    title=title,
                    description=description,
                    publisher_name=publisher_name,
                    theme_tag_fqns=theme_tag_fqns,
                    hvd_category_uri=hvd_category_uri,
                    distribution_access_url=distribution_access_url,
                )
            )
    return rows


def generate_governance_sheet(
    *,
    tables: list[dict[str, Any]],
    defaults: DefaultsConfig,
    output_path: str | Path,
    schema_filter: str = "gold",
    existing_rows: list[GovernanceSheetRow] | None = None,
    tags_by_prefix: dict[str, list[str]] | None = None,
) -> int:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    selected: list[dict[str, Any]] = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        if _schema_name(table) != schema_filter:
            continue
        selected.append(table)

    selected.sort(key=lambda x: str(x.get("fullyQualifiedName") or x.get("name") or ""))

    with p.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_FIELDNAMES, delimiter=";")
        writer.writeheader()
        for table in selected:
            existing_row = match_sheet_row(rows=existing_rows, table=table) if existing_rows else None
            cp = existing_custom_properties(table)
            tag_fqns = existing_tag_fqns(table)
            if not tag_fqns and tags_by_prefix:
                tag_fqns = tags_for_table(str(table.get("name") or ""), tags_by_prefix)
            theme_aliases = [
                THEME_TAG_FQN_TO_ALIAS[tag_fqn]
                for tag_fqn in tag_fqns
                if tag_fqn in THEME_TAG_FQN_TO_ALIAS
            ]
            if existing_row is not None:
                theme_aliases = [
                    THEME_TAG_FQN_TO_ALIAS.get(tag_fqn, tag_fqn)
                    for tag_fqn in existing_row.theme_tag_fqns
                ]
            hvd_category_uri = (
                existing_row.hvd_category_uri
                if existing_row is not None
                else str(cp.get("dcat_hvd_category") or "").strip()
            )
            if not hvd_category_uri:
                hvd_category_uri = hvd_category_for_tags(tag_fqns=tag_fqns, dataset_defaults=defaults.dataset_defaults)
            distribution_access_url = (
                existing_row.distribution_access_url
                if existing_row is not None
                else str(cp.get("dcat_access_url") or "").strip()
            )
            if not distribution_access_url:
                access_url_base = str(defaults.dataset_defaults.get("access_url_base") or "").strip()
                if access_url_base:
                    distribution_access_url = build_distribution_access_url(
                        base_url=access_url_base,
                        schema_name=_schema_name(table) or "",
                        table_name=str(table.get("name") or ""),
                    )
            writer.writerow(
                {
                    "publicar": "si" if existing_row is None or existing_row.publish else "no",
                    "schema_name": _schema_name(table) or "",
                    "table_name": str(table.get("name") or ""),
                    "table_fqn": str(table.get("fullyQualifiedName") or ""),
                    "titulo_dataset": (
                        existing_row.title
                        if existing_row is not None
                        else str(table.get("displayName") or table.get("name") or "")
                    ),
                    "descripcion_dataset": (
                        existing_row.description
                        if existing_row is not None
                        else str(table.get("description") or "")
                    ),
                    "publicador": (
                        existing_row.publisher_name
                        if existing_row is not None
                        else cp.get("dcat_publisher_name") or defaults.catalog.publisher_name
                    ),
                    "tematica_dcat": ",".join(theme_aliases),
                    "categoria_hvd": hvd_category_alias(hvd_category_uri),
                    "access_url_distribucion": distribution_access_url,
                }
            )

    return len(selected)


def match_sheet_row(
    *,
    rows: list[GovernanceSheetRow],
    table: dict[str, Any],
) -> GovernanceSheetRow | None:
    schema_name = _schema_name(table) or ""
    table_name = str(table.get("name") or "").strip()
    table_fqn = str(table.get("fullyQualifiedName") or "").strip()

    for row in rows:
        if row.table_fqn and row.table_fqn == table_fqn:
            return row
    if table_fqn:
        rows_without_fqn = [row for row in rows if not row.table_fqn]
    else:
        rows_without_fqn = rows
    for row in rows_without_fqn:
        if row.schema_name == schema_name and row.table_name == table_name:
            return row
    return None
