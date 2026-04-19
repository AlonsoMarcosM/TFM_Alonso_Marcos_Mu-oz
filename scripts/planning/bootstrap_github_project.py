from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASE_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

DEFAULT_FIELD_STATUS = "Status"
DEFAULT_FIELD_FASE = "Fase TFM"
DEFAULT_FIELD_TIPO = "Tipo TFM"
DEFAULT_FIELD_FECHA_INICIO = "fecha_inicio"
DEFAULT_FIELD_FECHA_FIN = "fecha_fin"
LEGACY_FIELD_ESTADO = "Estado TFM"

TYPE_LABEL_COLORS = {
    "diseno": "0052cc",
    "implementacion": "1a7f37",
    "validacion": "bf8700",
    "documentacion": "57606a",
    "riesgo": "cf222e",
}
PHASE_LABEL_COLORS = [
    "0969da",
    "1f883d",
    "9a6700",
    "bc4c00",
    "8250df",
    "3fb950",
]
FIELD_OPTION_COLORS = [
    "BLUE",
    "GREEN",
    "YELLOW",
    "ORANGE",
    "RED",
    "PURPLE",
    "PINK",
    "GRAY",
]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def github_token_from_gh() -> str | None:
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    token = completed.stdout.strip()
    return token or None


def resolve_token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or github_token_from_gh()


class GitHubApiError(RuntimeError):
    pass


class GitHubApi:
    def __init__(self, token: str, timeout_s: int = 30) -> None:
        self.timeout_s = timeout_s
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "tfm-github-project-mvp",
        }

    def rest(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        url = API_BASE_URL + path
        if query:
            encoded = urllib.parse.urlencode(query, doseq=True)
            url = f"{url}?{encoded}"

        data = None
        headers = dict(self.headers)
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"{method} {path} -> {exc.code}\n{payload[:2000]}") from exc
        except urllib.error.URLError as exc:
            raise GitHubApiError(f"{method} {path} -> {exc.reason}") from exc

        if not raw.strip():
            return {}
        return json.loads(raw)

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {"query": query, "variables": variables or {}}
        headers = dict(self.headers)
        headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            GRAPHQL_URL,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            payload_txt = exc.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"POST /graphql -> {exc.code}\n{payload_txt[:2000]}") from exc
        except urllib.error.URLError as exc:
            raise GitHubApiError(f"POST /graphql -> {exc.reason}") from exc

        data = json.loads(raw) if raw.strip() else {}
        errors = data.get("errors")
        if errors:
            msg = "; ".join(str(e.get("message", e)) for e in errors if isinstance(e, dict))
            if not msg:
                msg = str(errors)
            raise GitHubApiError(f"GraphQL error: {msg}")
        return data


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")


def normalize_option_color(index: int) -> str:
    return FIELD_OPTION_COLORS[index % len(FIELD_OPTION_COLORS)]


def parse_iso_date(value: Any, *, task_title: str, field_name: str) -> dt.date:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Task {task_title!r} must define non-empty {field_name}")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Task {task_title!r} has invalid {field_name}: {value!r}") from exc


def load_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    cfg = json.loads(raw)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    required_keys = ("project_title", "status_options", "tipo_options", "phases")
    for key in required_keys:
        if key not in cfg:
            raise ValueError(f"Config missing key: {key}")

    if not isinstance(cfg["status_options"], list) or not cfg["status_options"]:
        raise ValueError("status_options must be a non-empty list")
    if not isinstance(cfg["tipo_options"], list) or not cfg["tipo_options"]:
        raise ValueError("tipo_options must be a non-empty list")
    if not isinstance(cfg["phases"], list) or not cfg["phases"]:
        raise ValueError("phases must be a non-empty list")

    tipos = set(cfg["tipo_options"])
    statuses = set(cfg["status_options"])
    seen_titles: set[str] = set()

    for phase in cfg["phases"]:
        if not isinstance(phase, dict):
            raise ValueError("Each phase must be an object")
        for key in ("name", "milestone", "tasks"):
            if key not in phase:
                raise ValueError(f"Phase missing key: {key}")
        if not isinstance(phase["tasks"], list) or not phase["tasks"]:
            raise ValueError(f"Phase {phase['name']!r} has no tasks")

        for task in phase["tasks"]:
            for key in ("title", "tipo", "status", "fecha_inicio", "fecha_fin", "descripcion", "evidencias"):
                if key not in task:
                    raise ValueError(f"Task in phase {phase['name']!r} missing key: {key}")
            title = str(task["title"]).strip()
            if not title:
                raise ValueError(f"Task with empty title in phase {phase['name']!r}")
            if title in seen_titles:
                raise ValueError(f"Duplicated task title in config: {title}")
            seen_titles.add(title)
            if task["tipo"] not in tipos:
                raise ValueError(f"Unknown tipo {task['tipo']!r} in task {title!r}")
            if task["status"] not in statuses:
                raise ValueError(f"Unknown status {task['status']!r} in task {title!r}")
            fecha_inicio = parse_iso_date(task["fecha_inicio"], task_title=title, field_name="fecha_inicio")
            fecha_fin = parse_iso_date(task["fecha_fin"], task_title=title, field_name="fecha_fin")
            if fecha_fin < fecha_inicio:
                raise ValueError(f"Task {title!r} has fecha_fin before fecha_inicio")
            if not isinstance(task["evidencias"], list):
                raise ValueError(f"Task evidencias must be a list in task {title!r}")


def iter_tasks(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for phase in cfg["phases"]:
        for task in phase["tasks"]:
            row = dict(task)
            row["phase_name"] = phase["name"]
            row["milestone"] = phase["milestone"]
            rows.append(row)
    return rows


def build_issue_body(task: dict[str, Any]) -> str:
    evidencias = task.get("evidencias", [])
    lines = [
        "## Objetivo",
        str(task["descripcion"]).strip(),
        "",
        "## Contexto",
        f"- Fase: `{task['phase_name']}`",
        f"- Tipo: `{task['tipo']}`",
        f"- Status inicial: `{task['status']}`",
        f"- Fecha inicio: `{task['fecha_inicio']}`",
        f"- Fecha fin: `{task['fecha_fin']}`",
        "",
        "## Evidencias / referencias",
    ]
    if evidencias:
        for path in evidencias:
            lines.append(f"- `{path}`")
    else:
        lines.append("- (sin referencias declaradas)")

    lines.extend(
        [
            "",
            "## Checklist sugerido",
            "- [ ] Ejecutar la tarea",
            "- [ ] Guardar evidencia tecnica",
            "- [ ] Actualizar documentacion relacionada",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def resolve_owner(api: GitHubApi, owner_login: str) -> tuple[str, str, list[dict[str, Any]]]:
    q_user = """
    query ResolveUserOwner($login: String!) {
      user(login: $login) {
        id
        login
        projectsV2(first: 100) {
          nodes { id title url number }
        }
      }
    }
    """
    user_data = api.graphql(q_user, {"login": owner_login}).get("data", {})
    user_node = user_data.get("user")
    if user_node:
        projects = user_node.get("projectsV2", {}).get("nodes", []) or []
        return str(user_node["id"]), "user", projects

    q_org = """
    query ResolveOrgOwner($login: String!) {
      organization(login: $login) {
        id
        login
        projectsV2(first: 100) {
          nodes { id title url number }
        }
      }
    }
    """
    org_data = api.graphql(q_org, {"login": owner_login}).get("data", {})
    org_node = org_data.get("organization")
    if not org_node:
        raise GitHubApiError(f"Owner not found in GitHub: {owner_login}")
    projects = org_node.get("projectsV2", {}).get("nodes", []) or []
    return str(org_node["id"]), "organization", projects


def get_or_create_project(
    api: GitHubApi,
    *,
    owner_id: str,
    owner_projects: list[dict[str, Any]],
    project_title: str,
    project_number: int | None = None,
) -> tuple[dict[str, Any], bool]:
    if project_number is not None:
        for proj in owner_projects:
            try:
                current_number = int(proj.get("number", -1))
            except (TypeError, ValueError):
                continue
            if current_number == project_number:
                return proj, False
        raise GitHubApiError(f"Project number not found for owner: {project_number}")

    for proj in owner_projects:
        if str(proj.get("title", "")).strip().lower() == project_title.strip().lower():
            return proj, False

    m = """
    mutation CreateProject($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 { id title url number }
      }
    }
    """
    data = api.graphql(m, {"ownerId": owner_id, "title": project_title}).get("data", {})
    created = data.get("createProjectV2", {}).get("projectV2")
    if not created:
        raise GitHubApiError("Could not create project")
    return created, True


def list_project_fields(api: GitHubApi, project_id: str) -> list[dict[str, Any]]:
    q = """
    query ProjectFields($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 100) {
            nodes {
              __typename
              ... on ProjectV2Field { id name dataType }
              ... on ProjectV2SingleSelectField {
                id
                name
                options { id name }
              }
              ... on ProjectV2IterationField { id name }
            }
          }
        }
      }
    }
    """
    data = api.graphql(q, {"projectId": project_id}).get("data", {})
    node = data.get("node", {})
    if not node:
        raise GitHubApiError(f"Project node not found: {project_id}")
    return node.get("fields", {}).get("nodes", []) or []


def get_repository_id(api: GitHubApi, *, owner: str, repo: str) -> str:
    q = """
    query RepoId($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        nameWithOwner
      }
    }
    """
    data = api.graphql(q, {"owner": owner, "name": repo}).get("data", {})
    node = (data or {}).get("repository") or {}
    repo_id = node.get("id")
    if not repo_id:
        raise GitHubApiError(f"Repository not found or inaccessible: {owner}/{repo}")
    return str(repo_id)


def list_project_repositories(api: GitHubApi, project_id: str) -> set[str]:
    q = """
    query ProjectRepos($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          repositories(first: 100) {
            nodes { id nameWithOwner }
          }
        }
      }
    }
    """
    data = api.graphql(q, {"projectId": project_id}).get("data", {})
    repos = (((data or {}).get("node") or {}).get("repositories") or {}).get("nodes") or []
    out: set[str] = set()
    for r in repos:
        if isinstance(r, dict) and r.get("id"):
            out.add(str(r["id"]))
    return out


def link_project_to_repository(api: GitHubApi, *, project_id: str, repository_id: str) -> None:
    m = """
    mutation LinkProjectToRepo($projectId: ID!, $repositoryId: ID!) {
      linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repositoryId}) {
        repository { id nameWithOwner }
      }
    }
    """
    api.graphql(m, {"projectId": project_id, "repositoryId": repository_id})


def ensure_project_linked_to_repo(api: GitHubApi, *, project_id: str, owner: str, repo: str) -> bool:
    """
    Projects v2 are owned by user/org, but they can be linked to repositories so they appear under repo -> Projects.
    Returns True if it linked during this run, False if it was already linked.
    """
    repo_id = get_repository_id(api, owner=owner, repo=repo)
    linked_repo_ids = list_project_repositories(api, project_id)
    if repo_id in linked_repo_ids:
        return False
    link_project_to_repository(api, project_id=project_id, repository_id=repo_id)
    return True


def ensure_single_select_field(
    api: GitHubApi,
    *,
    project_id: str,
    field_name: str,
    option_names: list[str],
) -> tuple[str, dict[str, str], bool]:
    fields = list_project_fields(api, project_id)
    for field in fields:
        if field.get("name") != field_name:
            continue
        if field.get("__typename") != "ProjectV2SingleSelectField":
            raise GitHubApiError(f"Field '{field_name}' exists but is not single-select")
        options = {str(x["name"]): str(x["id"]) for x in field.get("options", []) if x.get("name") and x.get("id")}
        missing = [opt for opt in option_names if opt not in options]
        if missing:
            update_single_select_field_options(
                api,
                field_id=str(field["id"]),
                field_name=field_name,
                option_names=option_names,
            )
            refreshed_fields = list_project_fields(api, project_id)
            for refreshed in refreshed_fields:
                if refreshed.get("name") == field_name and refreshed.get("__typename") == "ProjectV2SingleSelectField":
                    refreshed_options = {
                        str(x["name"]): str(x["id"])
                        for x in refreshed.get("options", [])
                        if x.get("name") and x.get("id")
                    }
                    still_missing = [opt for opt in option_names if opt not in refreshed_options]
                    if still_missing:
                        raise GitHubApiError(
                            f"Field '{field_name}' still missing options after update: {', '.join(still_missing)}"
                        )
                    return str(refreshed["id"]), refreshed_options, False
            raise GitHubApiError(f"Field '{field_name}' not found after updating options")
        return str(field["id"]), options, False

    # GitHub API expects non-null description for each single-select option.
    options_payload = [
        {
            "name": name,
            "description": name,
            "color": normalize_option_color(idx),
        }
        for idx, name in enumerate(option_names)
    ]
    m = """
    mutation CreateField($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
      createProjectV2Field(
        input: {
          projectId: $projectId
          name: $name
          dataType: SINGLE_SELECT
          singleSelectOptions: $options
        }
      ) {
        projectV2Field {
          __typename
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
        }
      }
    }
    """
    data = api.graphql(
        m,
        {
            "projectId": project_id,
            "name": field_name,
            "options": options_payload,
        },
    ).get("data", {})
    field = data.get("createProjectV2Field", {}).get("projectV2Field")
    if not field or field.get("__typename") != "ProjectV2SingleSelectField":
        raise GitHubApiError(f"Could not create field: {field_name}")
    options = {str(x["name"]): str(x["id"]) for x in field.get("options", []) if x.get("name") and x.get("id")}
    return str(field["id"]), options, True


def ensure_date_field(
    api: GitHubApi,
    *,
    project_id: str,
    field_name: str,
) -> tuple[str, bool]:
    fields = list_project_fields(api, project_id)
    for field in fields:
        if field.get("name") != field_name:
            continue
        if field.get("__typename") != "ProjectV2Field" or field.get("dataType") != "DATE":
            raise GitHubApiError(f"Field '{field_name}' exists but is not a date field")
        return str(field["id"]), False

    m = """
    mutation CreateDateField($projectId: ID!, $name: String!) {
      createProjectV2Field(
        input: {
          projectId: $projectId
          name: $name
          dataType: DATE
        }
      ) {
        projectV2Field {
          __typename
          ... on ProjectV2Field { id name dataType }
        }
      }
    }
    """
    data = api.graphql(m, {"projectId": project_id, "name": field_name}).get("data", {})
    field = data.get("createProjectV2Field", {}).get("projectV2Field")
    if not field or field.get("__typename") != "ProjectV2Field" or field.get("dataType") != "DATE":
        raise GitHubApiError(f"Could not create date field: {field_name}")
    return str(field["id"]), True


def update_single_select_field_options(
    api: GitHubApi,
    *,
    field_id: str,
    field_name: str,
    option_names: list[str],
) -> None:
    options_payload = [
        {
            "name": name,
            "description": name,
            "color": normalize_option_color(idx),
        }
        for idx, name in enumerate(option_names)
    ]
    m = """
    mutation UpdateField($fieldId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
      updateProjectV2Field(
        input: {
          fieldId: $fieldId
          name: $name
          singleSelectOptions: $options
        }
      ) {
        projectV2Field {
          __typename
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
        }
      }
    }
    """
    api.graphql(m, {"fieldId": field_id, "name": field_name, "options": options_payload})


def list_repo_labels(api: GitHubApi, owner: str, repo: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    page = 1
    while True:
        data = api.rest(
            "GET",
            f"/repos/{owner}/{repo}/labels",
            query={"per_page": 100, "page": page},
        )
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict) and item.get("name"):
                out[str(item["name"])] = item
        page += 1
    return out


def expected_labels(cfg: dict[str, Any]) -> list[dict[str, str]]:
    labels: list[dict[str, str]] = []
    for tipo in cfg["tipo_options"]:
        key = slugify(tipo)
        labels.append(
            {
                "name": f"tipo/{key}",
                "color": TYPE_LABEL_COLORS.get(key, "57606a"),
                "description": f"TFM tipo de tarea: {tipo}",
            }
        )
    for idx, phase in enumerate(cfg["phases"]):
        phase_name = phase["name"]
        labels.append(
            {
                "name": f"fase/{slugify(phase_name)}",
                "color": PHASE_LABEL_COLORS[idx % len(PHASE_LABEL_COLORS)],
                "description": f"TFM fase: {phase_name}",
            }
        )
    return labels


def ensure_labels(api: GitHubApi, owner: str, repo: str, cfg: dict[str, Any]) -> dict[str, list[str]]:
    existing = list_repo_labels(api, owner, repo)
    created: list[str] = []
    kept: list[str] = []
    for label in expected_labels(cfg):
        if label["name"] in existing:
            kept.append(label["name"])
            continue
        api.rest("POST", f"/repos/{owner}/{repo}/labels", body=label)
        created.append(label["name"])
    return {"created": created, "existing": kept}


def list_milestones(api: GitHubApi, owner: str, repo: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    page = 1
    while True:
        data = api.rest(
            "GET",
            f"/repos/{owner}/{repo}/milestones",
            query={"state": "all", "per_page": 100, "page": page},
        )
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict) and item.get("title"):
                out[str(item["title"])] = item
        page += 1
    return out


def delete_milestone(api: GitHubApi, owner: str, repo: str, number: int) -> None:
    api.rest("DELETE", f"/repos/{owner}/{repo}/milestones/{number}")


def ensure_milestones(api: GitHubApi, owner: str, repo: str, cfg: dict[str, Any]) -> dict[str, Any]:
    existing = list_milestones(api, owner, repo)
    created: list[str] = []
    kept: list[str] = []
    numbers: dict[str, int] = {}

    for phase in cfg["phases"]:
        title = str(phase["milestone"])
        item = existing.get(title)
        if item:
            kept.append(title)
            numbers[title] = int(item["number"])
            continue
        created_item = api.rest("POST", f"/repos/{owner}/{repo}/milestones", body={"title": title, "state": "open"})
        created.append(title)
        numbers[title] = int(created_item["number"])

    return {"created": created, "existing": kept, "numbers": numbers}


def list_repo_issues(api: GitHubApi, owner: str, repo: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    page = 1
    while True:
        data = api.rest(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            query={"state": "all", "per_page": 100, "page": page},
        )
        if not isinstance(data, list) or not data:
            break
        for item in data:
            if isinstance(item, dict) and "pull_request" not in item:
                issues.append(item)
        page += 1
    return issues


def _issue_label_names(issue: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for lbl in issue.get("labels", []) or []:
        if isinstance(lbl, str):
            out.add(lbl)
            continue
        if isinstance(lbl, dict) and lbl.get("name"):
            out.add(str(lbl["name"]))
    return out


def _issue_milestone_number(issue: dict[str, Any]) -> int | None:
    ms = issue.get("milestone")
    if isinstance(ms, dict) and ms.get("number") is not None:
        try:
            return int(ms["number"])
        except (TypeError, ValueError):
            return None
    return None


def add_labels_to_issue(api: GitHubApi, owner: str, repo: str, issue_number: int, labels: list[str]) -> None:
    if not labels:
        return
    api.rest("POST", f"/repos/{owner}/{repo}/issues/{issue_number}/labels", body=labels)


def set_issue_milestone(api: GitHubApi, owner: str, repo: str, issue_number: int, milestone_number: int) -> dict[str, Any]:
    return api.rest("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", body={"milestone": milestone_number})


def build_issue_title(prefix: str, title: str) -> str:
    pref = prefix.strip()
    if not pref:
        return title
    if pref.endswith(" "):
        return f"{pref}{title}"
    return f"{pref} {title}"


def ensure_issues(
    api: GitHubApi,
    *,
    owner: str,
    repo: str,
    cfg: dict[str, Any],
    milestone_numbers: dict[str, int],
    issue_prefix: str,
) -> dict[str, Any]:
    existing = list_repo_issues(api, owner, repo)
    by_title = {str(issue.get("title")): issue for issue in existing if issue.get("title")}
    created_titles: list[str] = []
    existing_titles: list[str] = []
    issues_by_config_title: dict[str, dict[str, Any]] = {}

    for phase in cfg["phases"]:
        phase_label = f"fase/{slugify(phase['name'])}"
        milestone_number = milestone_numbers[phase["milestone"]]
        for task in phase["tasks"]:
            full_title = build_issue_title(issue_prefix, task["title"])
            item = by_title.get(full_title)
            if item is None:
                labels = [f"tipo/{slugify(task['tipo'])}", phase_label]
                body = {
                    "title": full_title,
                    "body": build_issue_body(
                        {
                            **task,
                            "phase_name": phase["name"],
                        }
                    ),
                    "labels": labels,
                    "milestone": milestone_number,
                }
                item = api.rest("POST", f"/repos/{owner}/{repo}/issues", body=body)
                by_title[full_title] = item
                created_titles.append(full_title)
            else:
                # Make runs idempotent even if issues existed from a previous run with old labels/milestones.
                desired_labels = [f"tipo/{slugify(task['tipo'])}", phase_label]
                current_labels = _issue_label_names(item)
                missing = [lbl for lbl in desired_labels if lbl not in current_labels]
                if missing:
                    add_labels_to_issue(api, owner, repo, int(item["number"]), missing)

                current_ms = _issue_milestone_number(item)
                if current_ms != milestone_number:
                    item = set_issue_milestone(api, owner, repo, int(item["number"]), milestone_number) or item
                    by_title[full_title] = item
                existing_titles.append(full_title)
            issues_by_config_title[task["title"]] = item

    return {
        "created": created_titles,
        "existing": existing_titles,
        "issues_by_task_title": issues_by_config_title,
    }


def list_project_issue_items(api: GitHubApi, project_id: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    cursor: str | None = None
    q = """
    query ProjectItems($projectId: ID!, $cursor: String) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
            nodes {
              id
              content {
                __typename
                ... on Issue { id number title }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
      }
    }
    """
    while True:
        data = api.graphql(q, {"projectId": project_id, "cursor": cursor}).get("data", {})
        items_block = data.get("node", {}).get("items", {})
        nodes = items_block.get("nodes", []) or []
        for node in nodes:
            content = node.get("content") or {}
            content_id = content.get("id")
            item_id = node.get("id")
            if content_id and item_id:
                out.append(
                    {
                        "content_id": str(content_id),
                        "item_id": str(item_id),
                        "title": str(content.get("title", "")),
                        "number": str(content.get("number", "")),
                    }
                )
        page_info = items_block.get("pageInfo", {}) or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")
        if not cursor:
            break
    return out


def list_project_items_by_content_id(api: GitHubApi, project_id: str) -> dict[str, str]:
    return {item["content_id"]: item["item_id"] for item in list_project_issue_items(api, project_id)}


def add_issue_to_project(api: GitHubApi, project_id: str, issue_node_id: str) -> str:
    m = """
    mutation AddIssueToProject($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    data = api.graphql(m, {"projectId": project_id, "contentId": issue_node_id}).get("data", {})
    item = data.get("addProjectV2ItemById", {}).get("item")
    if not item or not item.get("id"):
        raise GitHubApiError("Could not add issue to project")
    return str(item["id"])


def delete_project_item(api: GitHubApi, *, project_id: str, item_id: str) -> None:
    m = """
    mutation DeleteProjectItem($projectId: ID!, $itemId: ID!) {
      deleteProjectV2Item(input: {projectId: $projectId, itemId: $itemId}) {
        deletedItemId
      }
    }
    """
    api.graphql(m, {"projectId": project_id, "itemId": item_id})


def delete_project_v2(api: GitHubApi, project_id: str) -> None:
    m = """
    mutation DeleteProject($projectId: ID!) {
      deleteProjectV2(input: {projectId: $projectId}) {
        clientMutationId
      }
    }
    """
    api.graphql(m, {"projectId": project_id})


def set_single_select_value(
    api: GitHubApi,
    *,
    project_id: str,
    item_id: str,
    field_id: str,
    option_id: str,
) -> None:
    m = """
    mutation SetFieldValue(
      $projectId: ID!
      $itemId: ID!
      $fieldId: ID!
      $optionId: String!
    ) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: {singleSelectOptionId: $optionId}
        }
      ) {
        projectV2Item { id }
      }
    }
    """
    api.graphql(
        m,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "optionId": option_id,
        },
    )


def set_date_value(
    api: GitHubApi,
    *,
    project_id: str,
    item_id: str,
    field_id: str,
    date_value: str,
) -> None:
    m = """
    mutation SetDateFieldValue(
      $projectId: ID!
      $itemId: ID!
      $fieldId: ID!
      $dateValue: Date!
    ) {
      updateProjectV2ItemFieldValue(
        input: {
          projectId: $projectId
          itemId: $itemId
          fieldId: $fieldId
          value: {date: $dateValue}
        }
      ) {
        projectV2Item { id }
      }
    }
    """
    api.graphql(
        m,
        {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "dateValue": date_value,
        },
    )


def delete_project_field(api: GitHubApi, field_id: str) -> None:
    m = """
    mutation DeleteField($fieldId: ID!) {
      deleteProjectV2Field(input: {fieldId: $fieldId}) {
        clientMutationId
      }
    }
    """
    api.graphql(m, {"fieldId": field_id})


def delete_project_field_by_name(
    api: GitHubApi,
    *,
    project_id: str,
    field_name: str,
    keep_field_id: str | None = None,
) -> bool:
    for field in list_project_fields(api, project_id):
        if field.get("name") != field_name:
            continue
        field_id = str(field.get("id", ""))
        if not field_id or field_id == keep_field_id:
            continue
        delete_project_field(api, field_id)
        return True
    return False


def run_apply(
    *,
    cfg: dict[str, Any],
    owner: str,
    repo: str,
    project_title: str,
    project_number: int | None,
    issue_prefix: str,
    token: str,
    field_status_name: str,
    field_fase_name: str,
    field_tipo_name: str,
    field_fecha_inicio_name: str,
    field_fecha_fin_name: str,
    legacy_field_status_name: str,
) -> dict[str, Any]:
    api = GitHubApi(token=token)

    owner_id, owner_kind, owner_projects = resolve_owner(api, owner)
    project, project_created = get_or_create_project(
        api,
        owner_id=owner_id,
        owner_projects=owner_projects,
        project_title=project_title,
        project_number=project_number,
    )
    project_id = str(project["id"])

    linked = ensure_project_linked_to_repo(api, project_id=project_id, owner=owner, repo=repo)

    labels_summary = ensure_labels(api, owner, repo, cfg)
    milestones_summary = ensure_milestones(api, owner, repo, cfg)

    issues_summary = ensure_issues(
        api,
        owner=owner,
        repo=repo,
        cfg=cfg,
        milestone_numbers=milestones_summary["numbers"],
        issue_prefix=issue_prefix,
    )

    status_field_id, status_options, status_field_created = ensure_single_select_field(
        api, project_id=project_id, field_name=field_status_name, option_names=list(cfg["status_options"])
    )
    fase_field_id, fase_options, fase_field_created = ensure_single_select_field(
        api,
        project_id=project_id,
        field_name=field_fase_name,
        option_names=[str(p["name"]) for p in cfg["phases"]],
    )
    tipo_field_id, tipo_options, tipo_field_created = ensure_single_select_field(
        api, project_id=project_id, field_name=field_tipo_name, option_names=list(cfg["tipo_options"])
    )
    fecha_inicio_field_id, fecha_inicio_field_created = ensure_date_field(
        api, project_id=project_id, field_name=field_fecha_inicio_name
    )
    fecha_fin_field_id, fecha_fin_field_created = ensure_date_field(
        api, project_id=project_id, field_name=field_fecha_fin_name
    )

    desired_issue_titles = {build_issue_title(issue_prefix, str(task["title"])) for task in iter_tasks(cfg)}
    stale_project_items_removed: list[str] = []
    project_issue_items = list_project_issue_items(api, project_id)
    for item in project_issue_items:
        title = item["title"]
        if title.startswith(issue_prefix) and title not in desired_issue_titles:
            delete_project_item(api, project_id=project_id, item_id=item["item_id"])
            stale_project_items_removed.append(title)

    project_items = {
        item["content_id"]: item["item_id"]
        for item in project_issue_items
        if item["title"] in desired_issue_titles
    }
    items_added = 0
    items_existing = 0
    field_updates = 0

    issue_by_title = issues_summary["issues_by_task_title"]
    for phase in cfg["phases"]:
        phase_option_id = fase_options[phase["name"]]
        for task in phase["tasks"]:
            issue = issue_by_title[task["title"]]
            issue_node_id = str(issue["node_id"])
            item_id = project_items.get(issue_node_id)
            if item_id is None:
                item_id = add_issue_to_project(api, project_id, issue_node_id)
                project_items[issue_node_id] = item_id
                items_added += 1
            else:
                items_existing += 1

            status_option_id = status_options[task["status"]]
            tipo_option_id = tipo_options[task["tipo"]]
            set_single_select_value(
                api,
                project_id=project_id,
                item_id=item_id,
                field_id=status_field_id,
                option_id=status_option_id,
            )
            set_single_select_value(
                api,
                project_id=project_id,
                item_id=item_id,
                field_id=fase_field_id,
                option_id=phase_option_id,
            )
            set_single_select_value(
                api,
                project_id=project_id,
                item_id=item_id,
                field_id=tipo_field_id,
                option_id=tipo_option_id,
            )
            set_date_value(
                api,
                project_id=project_id,
                item_id=item_id,
                field_id=fecha_inicio_field_id,
                date_value=str(task["fecha_inicio"]),
            )
            set_date_value(
                api,
                project_id=project_id,
                item_id=item_id,
                field_id=fecha_fin_field_id,
                date_value=str(task["fecha_fin"]),
            )
            field_updates += 5

    legacy_status_deleted = False
    if legacy_field_status_name and legacy_field_status_name != field_status_name:
        legacy_status_deleted = delete_project_field_by_name(
            api,
            project_id=project_id,
            field_name=legacy_field_status_name,
            keep_field_id=status_field_id,
        )

    return {
        "project": {
            "title": project.get("title"),
            "id": project_id,
            "url": project.get("url"),
            "created": project_created,
            "owner_kind": owner_kind,
            "linked_to_repo": bool(linked),
        },
        "labels": labels_summary,
        "milestones": {
            "created": milestones_summary["created"],
            "existing": milestones_summary["existing"],
        },
        "issues": {
            "created": issues_summary["created"],
            "existing": issues_summary["existing"],
        },
        "fields": {
            field_status_name: {"created": status_field_created, "options": list(cfg["status_options"])},
            field_fase_name: {"created": fase_field_created, "options": [str(p["name"]) for p in cfg["phases"]]},
            field_tipo_name: {"created": tipo_field_created, "options": list(cfg["tipo_options"])},
            field_fecha_inicio_name: {"created": fecha_inicio_field_created, "type": "DATE"},
            field_fecha_fin_name: {"created": fecha_fin_field_created, "type": "DATE"},
            "deleted_legacy_status_field": {
                "name": legacy_field_status_name,
                "deleted": legacy_status_deleted,
            },
        },
        "project_items": {
            "added": items_added,
            "existing": items_existing,
            "field_updates": field_updates,
            "stale_removed": stale_project_items_removed,
        },
    }


def build_dry_run_summary(
    cfg: dict[str, Any],
    *,
    owner: str | None,
    repo: str | None,
    project_title: str,
    project_number: int | None,
    issue_prefix: str,
    field_status_name: str,
    field_fase_name: str,
    field_tipo_name: str,
    field_fecha_inicio_name: str,
    field_fecha_fin_name: str,
    legacy_field_status_name: str,
) -> dict[str, Any]:
    tasks = iter_tasks(cfg)
    return {
        "mode": "dry-run",
        "owner": owner,
        "repo": repo,
        "project_title": project_title,
        "project_number": project_number,
        "issue_prefix": issue_prefix,
        "task_count": len(tasks),
        "phase_count": len(cfg["phases"]),
        "fields_to_create": {
            field_status_name: cfg["status_options"],
            field_fase_name: [str(p["name"]) for p in cfg["phases"]],
            field_tipo_name: cfg["tipo_options"],
            field_fecha_inicio_name: "DATE",
            field_fecha_fin_name: "DATE",
        },
        "fields_to_delete": [legacy_field_status_name]
        if legacy_field_status_name and legacy_field_status_name != field_status_name
        else [],
        "labels_to_create": [lbl["name"] for lbl in expected_labels(cfg)],
        "milestones_to_create": [str(phase["milestone"]) for phase in cfg["phases"]],
        "issue_titles_preview": [build_issue_title(issue_prefix, str(t["title"])) for t in tasks],
    }


def parse_args() -> argparse.Namespace:
    default_cfg = Path(__file__).with_name("github_project_mvp.json")
    load_dotenv(Path.cwd() / ".env")
    p = argparse.ArgumentParser(description="MVP: crear/actualizar GitHub Project del TFM de forma idempotente.")
    p.add_argument("--config", type=Path, default=default_cfg)
    p.add_argument("--owner", default=os.getenv("GITHUB_OWNER"))
    p.add_argument("--repo", default=os.getenv("GITHUB_REPO"))
    p.add_argument("--project-title", default=None)
    default_project_number = int(os.getenv("GITHUB_PROJECT_NUMBER")) if os.getenv("GITHUB_PROJECT_NUMBER") else None
    p.add_argument("--project-number", type=int, default=default_project_number)
    p.add_argument("--issue-prefix", default="[TFM]")
    p.add_argument("--field-status", "--field-estado", dest="field_status", default=DEFAULT_FIELD_STATUS)
    p.add_argument("--field-fase", default=DEFAULT_FIELD_FASE)
    p.add_argument("--field-tipo", default=DEFAULT_FIELD_TIPO)
    p.add_argument("--field-fecha-inicio", default=DEFAULT_FIELD_FECHA_INICIO)
    p.add_argument("--field-fecha-fin", default=DEFAULT_FIELD_FECHA_FIN)
    p.add_argument("--legacy-field-estado", default=LEGACY_FIELD_ESTADO)
    p.add_argument("--token", default=resolve_token())
    p.add_argument("--apply", action="store_true", help="Aplicar cambios reales en GitHub API.")
    p.add_argument(
        "--delete-projects",
        action="store_true",
        help="Borra todos los Projects v2 del owner (accion destructiva).",
    )
    p.add_argument(
        "--delete-old-milestones",
        action="store_true",
        help="Borra milestones antiguas del repo que no formen parte del roadmap actual.",
    )
    p.add_argument(
        "--milestone-prefix",
        default="Fase ",
        help="Prefijos (separados por coma) para identificar milestones antiguas. Por defecto: 'Fase '.",
    )
    p.add_argument(
        "--confirm",
        default=None,
        help="Confirmacion explicita para acciones destructivas. Valores: DELETE_ALL_PROJECTS, DELETE_OLD_MILESTONES.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config)
    project_title = args.project_title or str(cfg["project_title"])

    if args.delete_old_milestones:
        missing = [name for name, value in (("owner", args.owner), ("repo", args.repo), ("token", args.token)) if not value]
        if missing:
            print(f"Missing required args/env for --delete-old-milestones: {', '.join(missing)}", file=sys.stderr)
            return 2
        if args.confirm != "DELETE_OLD_MILESTONES":
            print("Refusing to delete milestones without --confirm DELETE_OLD_MILESTONES", file=sys.stderr)
            return 2
        api = GitHubApi(token=str(args.token))
        prefixes = [p.strip() for p in str(args.milestone_prefix).split(",") if p.strip()]
        current_titles = {str(p["milestone"]) for p in cfg["phases"]}
        existing = list_milestones(api, str(args.owner), str(args.repo))
        deleted: list[str] = []
        kept: list[str] = []
        errors: list[str] = []
        for title, item in existing.items():
            if title in current_titles:
                kept.append(title)
                continue
            if prefixes and not any(title.startswith(p) for p in prefixes):
                kept.append(title)
                continue
            number = int(item["number"])
            try:
                delete_milestone(api, str(args.owner), str(args.repo), number)
                deleted.append(title)
            except GitHubApiError as exc:
                errors.append(f"{title}: {exc}")
        summary = {
            "mode": "delete-old-milestones",
            "owner": str(args.owner),
            "repo": str(args.repo),
            "current_milestones": sorted(current_titles),
            "prefixes": prefixes,
            "deleted": deleted,
            "kept": kept,
            "errors": errors,
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if args.delete_projects:
        missing = [name for name, value in (("owner", args.owner), ("token", args.token)) if not value]
        if missing:
            print(f"Missing required args/env for --delete-projects: {', '.join(missing)}", file=sys.stderr)
            return 2
        if args.confirm != "DELETE_ALL_PROJECTS":
            print("Refusing to delete projects without --confirm DELETE_ALL_PROJECTS", file=sys.stderr)
            return 2
        api = GitHubApi(token=str(args.token))
        try:
            owner_id, owner_kind, owner_projects = resolve_owner(api, str(args.owner))
        except GitHubApiError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        deleted: list[str] = []
        errors: list[str] = []
        for proj in owner_projects:
            proj_id = str(proj.get("id", ""))
            title = str(proj.get("title", "(sin titulo)"))
            if not proj_id:
                continue
            try:
                delete_project_v2(api, proj_id)
                deleted.append(title)
            except GitHubApiError as exc:
                errors.append(f"{title}: {exc}")
        summary = {
            "mode": "delete-projects",
            "owner": str(args.owner),
            "owner_kind": owner_kind,
            "projects_found": [str(p.get("title", "(sin titulo)")) for p in owner_projects],
            "projects_deleted": deleted,
            "errors": errors,
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    if not args.apply:
        summary = build_dry_run_summary(
            cfg,
            owner=args.owner,
            repo=args.repo,
            project_title=project_title,
            project_number=args.project_number,
            issue_prefix=args.issue_prefix,
            field_status_name=args.field_status,
            field_fase_name=args.field_fase,
            field_tipo_name=args.field_tipo,
            field_fecha_inicio_name=args.field_fecha_inicio,
            field_fecha_fin_name=args.field_fecha_fin,
            legacy_field_status_name=args.legacy_field_estado,
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    missing = [name for name, value in (("owner", args.owner), ("repo", args.repo), ("token", args.token)) if not value]
    if missing:
        print(f"Missing required args/env for --apply: {', '.join(missing)}", file=sys.stderr)
        return 2

    try:
        summary = run_apply(
            cfg=cfg,
            owner=str(args.owner),
            repo=str(args.repo),
            project_title=project_title,
            project_number=args.project_number,
            issue_prefix=str(args.issue_prefix),
            token=str(args.token),
            field_status_name=str(args.field_status),
            field_fase_name=str(args.field_fase),
            field_tipo_name=str(args.field_tipo),
            field_fecha_inicio_name=str(args.field_fecha_inicio),
            field_fecha_fin_name=str(args.field_fecha_fin),
            legacy_field_status_name=str(args.legacy_field_estado),
        )
    except (GitHubApiError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
