param(
  [string]$OutputPath = ".\\tmp_pytest\\prereqs_report.json",
  [switch]$Strict
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
}

function Get-CommandInfo {
  param([string]$Name, [string[]]$VersionArgs = @("--version"))

  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) {
    return @{
      name = $Name
      available = $false
      version = $null
      path = $null
    }
  }

  $versionText = $null
  try {
    $versionText = (& $cmd.Source @VersionArgs) 2>&1 | Out-String
    $versionText = $versionText.Trim()
  } catch {
    $versionText = $null
  }

  return @{
    name = $Name
    available = $true
    version = $versionText
    path = $cmd.Source
  }
}

function Get-ToolInfoWithLocalFallback {
  # helm y kind pueden no estar en PATH pero si provisionados en .tools/ por los
  # scripts de infra (launch_infra.ps1). Reconocerlos -y, si faltan, autodescargarlos
  # con el mismo patron/version que launch_infra- evita falsos negativos en -Strict
  # y hace que la comprobacion funcione en un equipo con solo Docker Desktop + Python.
  param(
    [string]$Name,
    [string[]]$VersionArgs = @("--version"),
    [string]$LocalPath,
    [scriptblock]$Provision
  )

  $info = Get-CommandInfo -Name $Name -VersionArgs $VersionArgs
  if ($info.available) { return $info }

  if ($LocalPath -and -not (Test-Path $LocalPath) -and $Provision) {
    try {
      Write-Host "$Name no encontrado en PATH ni en .tools/. Autoprovisionando..."
      & $Provision
    } catch {
      Write-Host "No se pudo autoprovisionar ${Name}: $($_.Exception.Message)"
    }
  }

  if ($LocalPath -and (Test-Path $LocalPath)) {
    $versionText = $null
    try {
      $versionText = (& $LocalPath @VersionArgs) 2>&1 | Out-String
      $versionText = $versionText.Trim()
    } catch {
      $versionText = $null
    }
    return @{
      name = $Name
      available = $true
      version = $versionText
      path = $LocalPath
    }
  }

  return $info
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$localHelm = Join-Path $repoRoot ".tools\helm-v3.14.4\windows-amd64\helm.exe"
$localKind = Join-Path $repoRoot ".tools\kind\kind.exe"

# Provisioning portable identico al de launch_infra.ps1 (versiones fijadas).
$provisionHelm = {
  $toolsDir = Join-Path $repoRoot ".tools"
  New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
  $zipPath = Join-Path $toolsDir "helm-v3.14.4-windows-amd64.zip"
  Invoke-WebRequest -Uri "https://get.helm.sh/helm-v3.14.4-windows-amd64.zip" -OutFile $zipPath
  Expand-Archive -Path $zipPath -DestinationPath (Join-Path $toolsDir "helm-v3.14.4") -Force
}
$provisionKind = {
  $kindDir = Join-Path $repoRoot ".tools\kind"
  New-Item -ItemType Directory -Path $kindDir -Force | Out-Null
  Invoke-WebRequest -Uri "https://kind.sigs.k8s.io/dl/v0.24.0/kind-windows-amd64" -OutFile $localKind
}

$dockerInfo = Get-CommandInfo -Name "docker" -VersionArgs @("version", "--format", "{{.Server.Version}}")
$kubectlInfo = Get-CommandInfo -Name "kubectl" -VersionArgs @("version", "--client", "--output=yaml")
$kindInfo = Get-ToolInfoWithLocalFallback -Name "kind" -VersionArgs @("--version") -LocalPath $localKind -Provision $provisionKind
$helmInfo = Get-ToolInfoWithLocalFallback -Name "helm" -VersionArgs @("version", "--short") -LocalPath $localHelm -Provision $provisionHelm
$pythonInfo = Get-CommandInfo -Name "python" -VersionArgs @("--version")

$commands = @($dockerInfo, $kubectlInfo, $kindInfo, $helmInfo, $pythonInfo)
$missing = @($commands | Where-Object { -not $_.available } | ForEach-Object { $_.name })
$conforms = ($missing.Count -eq 0)

$report = @{
  conforms = $conforms
  commands = $commands
  missing = $missing
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir) {
  New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}
$json = $report | ConvertTo-Json -Depth 6
Set-Content -Path $OutputPath -Value $json -Encoding utf8
$report.output = $OutputPath
$report | ConvertTo-Json -Depth 6

if ($Strict -and -not $conforms) {
  exit 2
}
