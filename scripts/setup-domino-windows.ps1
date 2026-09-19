[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$workspaceRoot = (Resolve-Path (Join-Path $repoRoot "..")).Path
$localRoot = Join-Path $repoRoot ".local"
$venv = Join-Path $workspaceRoot ".venv"
$python = Join-Path $venv "Scripts\python.exe"
$upstream = Join-Path $localRoot "physicsnemo-cfd"
$lock = Get-Content (Join-Path $repoRoot "config\upstream-lock.json") -Raw | ConvertFrom-Json
$artifactLock = Get-Content (Join-Path $repoRoot "config\domino-artifacts.json") -Raw | ConvertFrom-Json
$repository = $lock.physicsnemo_cfd.repository
$commit = $lock.physicsnemo_cfd.commit
$artifactRoot = Join-Path $localRoot "domino-assets"
$uv = Join-Path $workspaceRoot ".tools\uv\uv.exe"
$env:UV_CACHE_DIR = Join-Path $workspaceRoot ".cache\uv"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $workspaceRoot ".tools\python"

if (-not (Test-Path -LiteralPath $uv)) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uvCommand) {
        throw "uv is required but was not found in .tools/uv or on PATH"
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $uv -Parent) | Out-Null
    Copy-Item -LiteralPath $uvCommand.Source -Destination $uv
}

New-Item -ItemType Directory -Force -Path $localRoot | Out-Null

if (-not (Test-Path -LiteralPath $upstream)) {
    & git clone --filter=blob:none $repository $upstream
    if ($LASTEXITCODE -ne 0) { throw "Could not clone PhysicsNeMo-CFD" }
}

$null = & git -C $upstream diff --quiet --ignore-submodules --
$workingTreeChanged = $LASTEXITCODE -ne 0
$null = & git -C $upstream diff --cached --quiet --ignore-submodules --
$indexChanged = $LASTEXITCODE -ne 0
$untrackedFiles = & git -C $upstream ls-files --others --exclude-standard
if ($LASTEXITCODE -ne 0) { throw "Could not inspect the PhysicsNeMo-CFD checkout" }
if ($workingTreeChanged -or $indexChanged -or $untrackedFiles) {
    throw "The local PhysicsNeMo-CFD checkout has changes; preserve or remove them before setup"
}

& git -C $upstream fetch origin $commit
if ($LASTEXITCODE -ne 0) { throw "Could not fetch pinned PhysicsNeMo-CFD commit $commit" }
& git -C $upstream checkout --detach $commit
if ($LASTEXITCODE -ne 0) { throw "Could not check out pinned PhysicsNeMo-CFD commit $commit" }

New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null
$artifactBaseUrl = $artifactLock.source_url -replace "/tree/", "/resolve/"
foreach ($artifact in $artifactLock.required) {
    $target = Join-Path $artifactRoot $artifact.path
    $verified = (Test-Path -LiteralPath $target) -and (
        (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -eq $artifact.sha256
    )
    if (-not $verified) {
        $partial = "$target.part"
        Invoke-WebRequest -Uri "$artifactBaseUrl/$($artifact.path)?download=true" -OutFile $partial
        $actualHash = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $artifact.sha256) {
            Remove-Item -LiteralPath $partial -Force
            throw "Checksum mismatch for $($artifact.path): expected $($artifact.sha256), got $actualHash"
        }
        Move-Item -LiteralPath $partial -Destination $target -Force
    }
}

if (-not (Test-Path -LiteralPath $python)) {
    & $uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw "Could not install the workspace Python 3.12 runtime" }
    & $uv venv $venv --python 3.12
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Python 3.12 environment" }
}

& $uv pip install --python $python torch --index-url https://download.pytorch.org/whl/cu128
if ($LASTEXITCODE -ne 0) { throw "Could not install CUDA-enabled PyTorch" }

& $uv pip install --python $python -e $upstream tyro warp-lang requests scikit-learn
if ($LASTEXITCODE -ne 0) { throw "Could not install PhysicsNeMo-CFD dependencies" }

& $uv pip install --python $python -e $repoRoot
if ($LASTEXITCODE -ne 0) { throw "Could not install Zephyr into the workspace environment" }

$env:WARP_CACHE_PATH = Join-Path $workspaceRoot ".cache\warp"
$env:LOCAL_CACHE = Join-Path $workspaceRoot ".cache\physicsnemo"

& $python -c "import torch; from physicsnemo.models.domino.model import DoMINO; assert torch.cuda.is_available(); print(torch.__version__); print(torch.cuda.get_device_name(0)); print(DoMINO.__name__)"
if ($LASTEXITCODE -ne 0) { throw "PhysicsNeMo CUDA verification failed" }

Write-Host "Native Windows DoMINO environment is ready."
