[CmdletBinding()]
param(
    [string]$InputFile = "",
    [ValidateRange(2, 64)]
    [int]$StencilSize = 7,
    [switch]$NoVerbose
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".local\venv-domino\Scripts\python.exe"
$workflow = Join-Path $repoRoot ".local\physicsnemo-cfd\workflows\domino_design_sensitivities"
$checkpoint = Join-Path $repoRoot ".local\domino-assets\DoMINO.0.501.mdlus"
$compatibilityPath = Join-Path $repoRoot "scripts\windows_compat"

foreach ($requiredPath in @($python, $workflow, $checkpoint)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Missing native DoMINO prerequisite: $requiredPath"
    }
}

$env:WARP_CACHE_PATH = Join-Path $repoRoot ".local\warp-cache"
$env:LOCAL_CACHE = Join-Path $repoRoot ".local\physicsnemo-cache"
$env:PYTHONPATH = if ($env:PYTHONPATH) {
    "$compatibilityPath;$env:PYTHONPATH"
} else {
    $compatibilityPath
}

$dominoArgs = @(
    "main.py",
    "--model-checkpoint-path", $checkpoint,
    "--stencil-size", "$StencilSize"
)

if ($InputFile) {
    $resolvedInput = (Resolve-Path -LiteralPath $InputFile).Path
    $dominoArgs += @("--input-file", $resolvedInput)
}

$dominoArgs += if ($NoVerbose) { "--no-verbose" } else { "--verbose" }

Push-Location $workflow
try {
    & $python @dominoArgs
    if ($LASTEXITCODE -ne 0) {
        throw "DoMINO exited with code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
