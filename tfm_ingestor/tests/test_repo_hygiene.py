import subprocess
from hashlib import sha256
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_TFE_FILE = REPO_ROOT / "docs" / "tfe_ficha_oficial_uclm.txt"
OFFICIAL_TFE_SHA256 = "4131c300929f18ee602d7d3b155f3714dcda52b670463e02f17eb4f08bd11df4"


def _git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_private_folders_are_not_tracked():
    tracked = _git_ls_files()
    forbidden_prefixes = (
        "TFM/",
        "docs_private/",
    )
    offenders = [p for p in tracked if p.startswith(forbidden_prefixes)]
    assert offenders == []


def test_official_tfe_file_is_unchanged():
    digest = sha256(OFFICIAL_TFE_FILE.read_bytes()).hexdigest()
    assert digest == OFFICIAL_TFE_SHA256
