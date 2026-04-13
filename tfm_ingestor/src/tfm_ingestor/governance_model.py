from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GovernanceIntent:
    table_fqn: str
    schema_name: str
    table_name: str
    publish: bool
    title: str | None
    description: str | None
    publisher_name: str | None
    theme_tag_fqns: list[str]
    hvd_category_uri: str | None
    distribution_access_url: str | None
    source: str
    domain_name: str | None = None


@dataclass(frozen=True)
class PlannedTableChange:
    table_fqn: str
    table_id: str
    ops: list[dict[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "tableFQN": self.table_fqn,
            "tableId": self.table_id,
            "ops": self.ops,
        }
