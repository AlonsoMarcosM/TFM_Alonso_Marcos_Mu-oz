param(
  [string]$Path = ".env",
  [switch]$Quiet
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $Path)) {
  if (-not $Quiet) {
    Write-Host "No existe $Path. Copia .env.example a .env y rellena los valores locales."
  }
  return
}

Get-Content -LiteralPath $Path | ForEach-Object {
  $line = $_.Trim()
  if ($line -and -not $line.StartsWith("#")) {
    $parts = $line.Split("=", 2)
    if ($parts.Count -eq 2) {
      $name = $parts[0].Trim()
      $value = $parts[1].Trim()
      if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
      Set-Item -Path "Env:$name" -Value $value
    }
  }
}

if (-not $Quiet) {
  Write-Host "Variables cargadas desde $Path"
}
