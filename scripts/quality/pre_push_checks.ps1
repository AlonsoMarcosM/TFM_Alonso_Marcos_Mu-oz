param(
  [string]$OutputPath = ".\\tmp_pytest\\pre_push_checks.json"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"

Push-Location ".\\tfm_ingestor"
try {
  python -m pytest
} finally {
  Pop-Location
}

$diffCheckOutput = (& cmd /c "git diff --check 2>&1" | Out-String)
$diffCheckOk = ($LASTEXITCODE -eq 0)
if (-not $diffCheckOk) {
  throw "git diff --check ha encontrado errores."
}

$statusTracked = git status --short | Out-String
$statusIgnored = git status --ignored --short | Out-String

$report = @{
  pytest = @{
    executed = $true
    command = '$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"; python -m pytest'
  }
  git = @{
    diff_check_ok = $diffCheckOk
    diff_check_output = $diffCheckOutput.Trim()
    status_short = $statusTracked.Trim()
    status_ignored_short = $statusIgnored.Trim()
  }
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir) {
  New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}
$json = $report | ConvertTo-Json -Depth 6
Set-Content -Path $OutputPath -Value $json -Encoding utf8
$report.output = $OutputPath
$report | ConvertTo-Json -Depth 6
