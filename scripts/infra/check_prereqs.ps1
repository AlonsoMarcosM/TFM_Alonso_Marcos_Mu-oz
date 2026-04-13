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

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$dockerInfo = Get-CommandInfo -Name "docker" -VersionArgs @("version", "--format", "{{.Server.Version}}")
$kubectlInfo = Get-CommandInfo -Name "kubectl" -VersionArgs @("version", "--client", "--output=yaml")
$kindInfo = Get-CommandInfo -Name "kind" -VersionArgs @("--version")
$helmInfo = Get-CommandInfo -Name "helm" -VersionArgs @("version", "--short")
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
