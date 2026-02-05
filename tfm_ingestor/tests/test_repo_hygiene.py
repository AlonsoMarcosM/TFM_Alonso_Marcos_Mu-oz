import subprocess


def _git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def test_private_folders_are_not_tracked():
    tracked = _git_ls_files()
    forbidden_prefixes = (
        "TFM/",
    )
    offenders = [p for p in tracked if p.startswith(forbidden_prefixes)]
    assert offenders == []
