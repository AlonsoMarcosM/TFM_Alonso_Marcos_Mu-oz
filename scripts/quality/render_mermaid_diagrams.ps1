# -------------------------------------------------------------------
# render_mermaid_diagrams.ps1
# Extrae todos los bloques ```mermaid de los .md de docs/ y los
# renderiza como PNG en TFM/Memoria/figs/ con encoding UTF-8.
# Resuelve los problemas de tildes/acentos cuando mmdc no recibe
# el contenido en UTF-8 puro.
# Requiere: Node.js + mmdc (Mermaid CLI) en PATH.
# -------------------------------------------------------------------

[CmdletBinding()]
param(
    [string] $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string] $OutputDir = $null,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

if (-not $OutputDir) {
    $OutputDir = Join-Path $RepoRoot "TFM\Memoria\figs"
}

$docsDir = Join-Path $RepoRoot "docs"
if (-not (Test-Path $docsDir)) { throw "No se encuentra docs/: $docsDir" }
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }

# Mapa de extracción: cada bloque mermaid se identifica por (archivo, indice 1-based)
# y se asocia a un nombre de figura final reutilizado por la memoria.
$mapping = @(
    @{ File = "diagramas_mermaid.md"; Index = 1; OutName = "fig_arquitectura_logica_capas.png" },
    @{ File = "diagramas_mermaid.md"; Index = 2; OutName = "fig_flujo_operativo_validacion.png" },
    @{ File = "diagramas_mermaid.md"; Index = 3; OutName = "fig_pipeline_metadatos.png" },
    @{ File = "diagramas_mermaid.md"; Index = 4; OutName = "fig_mapeo_activo_dcat_openmetadata.png" },
    @{ File = "diagramas_mermaid.md"; Index = 5; OutName = "fig_actor_funcional_sistema.png" },
    @{ File = "diagramas_mermaid.md"; Index = 6; OutName = "fig_opciones_orquestacion.png" },
    @{ File = "diagramas_mermaid.md"; Index = 7; OutName = "fig_web_nucleo_python.png" },
    @{ File = "diagramas_mermaid.md"; Index = 8; OutName = "fig_kubernetes_reproducible.png" },
    @{ File = "diagramas_mermaid.md"; Index = 9; OutName = "fig_artefactos_evidencias.png" },
    @{ File = "diagramas_mermaid.md"; Index = 10; OutName = "fig_arquitectura_logica_detalle.png" },
    @{ File = "diagramas_mermaid.md"; Index = 11; OutName = "fig_arquitectura_fisica.png" },
    @{ File = "diagramas_mermaid.md"; Index = 12; OutName = "fig_vision_funcional_solucion.png" },
    @{ File = "diagramas_mermaid.md"; Index = 13; OutName = "fig_secuencia_operacion.png" },
    @{ File = "diagramas_mermaid.md"; Index = 14; OutName = "fig_medallion_arquitectura.png" },
    @{ File = "gobierno_funcional_gold.md"; Index = 1; OutName = "fig_gobierno_funcional_gold.png" },
    @{ File = "refactor_orquestacion_operativa.md"; Index = 1; OutName = "fig_refactor_orquestacion_operativa.png" }
)

function Get-MermaidBlocks {
    param([string] $Path)
    if (-not (Test-Path $Path)) { return @() }
    $raw = [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
    $blocks = @()
    $pattern = '(?s)```mermaid\s*\r?\n(.*?)\r?\n```'
    $matches = [regex]::Matches($raw, $pattern)
    foreach ($m in $matches) {
        $blocks += $m.Groups[1].Value
    }
    return $blocks
}

# Configuración mmdc: tema neutro, fuente que admite acentos.
$puppeteerConfig = @{
    args = @("--no-sandbox", "--disable-dev-shm-usage")
} | ConvertTo-Json -Compress

$puppeteerCfgPath = Join-Path $env:TEMP "tfm_mmdc_puppeteer.json"
[System.IO.File]::WriteAllText($puppeteerCfgPath, $puppeteerConfig, [System.Text.UTF8Encoding]::new($false))

$mmdcConfig = @{
    theme = "default"
    fontFamily = "Segoe UI, Arial, sans-serif"
    flowchart = @{ htmlLabels = $true; curve = "basis" }
} | ConvertTo-Json -Depth 5 -Compress
$mmdcCfgPath = Join-Path $env:TEMP "tfm_mmdc_config.json"
[System.IO.File]::WriteAllText($mmdcCfgPath, $mmdcConfig, [System.Text.UTF8Encoding]::new($false))

$workDir = Join-Path $env:TEMP "tfm_mermaid_render"
if (-not (Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir | Out-Null }

$rendered = 0
$failed   = 0

foreach ($entry in $mapping) {
    $docPath = Join-Path $docsDir $entry.File
    $blocks = Get-MermaidBlocks -Path $docPath
    if ($blocks.Count -lt $entry.Index) {
        Write-Warning "Faltan bloques en $($entry.File): se pidio indice $($entry.Index) pero hay $($blocks.Count)."
        $failed++
        continue
    }
    $content = $blocks[$entry.Index - 1]
    $mmdPath = Join-Path $workDir ($entry.OutName -replace '\.png$', '.mmd')
    [System.IO.File]::WriteAllText($mmdPath, $content, [System.Text.UTF8Encoding]::new($false))

    $outPath = Join-Path $OutputDir $entry.OutName
    Write-Host "[render] $($entry.OutName) <- $($entry.File) bloque #$($entry.Index)"

    if ($DryRun) { $rendered++; continue }

    try {
        & mmdc -i $mmdPath -o $outPath -c $mmdcCfgPath -p $puppeteerCfgPath -b transparent -s 2 2>&1 | Out-Null
        if (-not (Test-Path $outPath)) { throw "mmdc no produjo $outPath" }
        $rendered++
    } catch {
        Write-Warning "Error renderizando $($entry.OutName): $_"
        $failed++
    }
}

Write-Host ""
Write-Host "Renderizado completado: $rendered figuras OK, $failed con error."
Write-Host "Salida: $OutputDir"
