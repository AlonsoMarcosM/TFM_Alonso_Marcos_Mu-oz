param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$HelmArgs
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Resolve-Helm3 {
  $repoRoot = Resolve-RepoRoot
  $localHelm = Join-Path $repoRoot ".tools\helm-v3.14.4\windows-amd64\helm.exe"

  $helmCmd = Get-Command helm -ErrorAction SilentlyContinue
  if ($helmCmd) {
    $ver = (& $helmCmd.Source version --short) 2>$null
    if ($ver -match "v3\.") {
      return $helmCmd.Source
    }
  }

  if (Test-Path $localHelm) {
    return $localHelm
  }

  throw "Helm 3 no encontrado. Ejecuta primero: powershell -ExecutionPolicy Bypass -File .\scripts\infra\launch_infra.ps1"
}

$helm = Resolve-Helm3
Write-Host "Helm usado: $helm"
& $helm @HelmArgs
exit $LASTEXITCODE
