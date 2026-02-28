from __future__ import annotations

from typing import Any

from tfm_ingestor.mapping import merge_tag_fqns
from tfm_ingestor.om_api import OmRef


def tag_labels(tag_fqns: list[str]) -> list[dict[str, Any]]:
    # OpenMetadata TagLabel (simplified)
    return [{"tagFQN": fqn, "labelType": "Manual", "state": "Confirmed"} for fqn in tag_fqns]


def existing_tag_fqns(table: dict[str, Any]) -> list[str]:
    tags = table.get("tags") or []
    out: list[str] = []
    for t in tags:
        if isinstance(t, dict) and t.get("tagFQN"):
            out.append(str(t["tagFQN"]))
    return out


def existing_custom_properties(table: dict[str, Any]) -> dict[str, str]:
    ext = table.get("extension") or {}
    if not isinstance(ext, dict):
        return {}
    # In OM 1.12.x table custom properties are stored directly in `extension`.
    out: dict[str, str] = {}
    for k, v in ext.items():
        if v is None:
            continue
        out[str(k)] = str(v)
    return out


def _json_patch_op_for_field(*, obj: dict[str, Any], field: str, value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    current = obj.get(field)
    if (current or "") == value:
        return None
    op = "replace" if field in obj else "add"
    return {"op": op, "path": f"/{field}", "value": value}


def build_table_patch_ops(
    *,
    table: dict[str, Any],
    desired_tag_fqns: list[str],
    desired_custom_properties: dict[str, str],
    desired_domain_ref: OmRef | None = None,
    desired_description: str | None = None,
    desired_display_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Build JSON Patch operations for an OpenMetadata Table.

    Idempotent behavior:
    - tags are merged (union)
    - customProperties are merged (desired keys override)
    - optional description/displayName are replaced only if different
    - optional domain ref is set if different
    """
    ops: list[dict[str, Any]] = []

    desc_op = _json_patch_op_for_field(obj=table, field="description", value=desired_description)
    if desc_op:
        ops.append(desc_op)

    dn_op = _json_patch_op_for_field(obj=table, field="displayName", value=desired_display_name)
    if dn_op:
        ops.append(dn_op)

    # Tags (union)
    existing_fqns = existing_tag_fqns(table)
    merged_fqns = merge_tag_fqns(existing_fqns, desired_tag_fqns)
    if merged_fqns != existing_fqns:
        ops.append({"op": "add" if not table.get("tags") else "replace", "path": "/tags", "value": tag_labels(merged_fqns)})

    # Custom properties (merge, override desired keys)
    existing_cp = existing_custom_properties(table)
    merged_cp = dict(existing_cp)
    merged_cp.update(desired_custom_properties)

    ext = table.get("extension")
    if merged_cp != existing_cp:
        if not isinstance(ext, dict) or not ext:
            ops.append({"op": "add", "path": "/extension", "value": merged_cp})
        else:
            ops.append({"op": "replace", "path": "/extension", "value": merged_cp})

    # Domains (OM 1.12.x uses `/domains` list on Table)
    if desired_domain_ref:
        desired_domain_value = {
            "id": desired_domain_ref.id,
            "type": desired_domain_ref.type,
            "name": desired_domain_ref.name,
        }
        current_domains = table.get("domains") or []
        current_ids = {
            str(d.get("id"))
            for d in current_domains
            if isinstance(d, dict) and d.get("id")
        }
        if desired_domain_ref.id not in current_ids:
            op = "add" if "domains" not in table else "replace"
            ops.append({"op": op, "path": "/domains", "value": [desired_domain_value]})

    return ops
