$ErrorActionPreference = 'Stop'

$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$OutputRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot 'output'))
$ControlRoot = [System.IO.Path]::GetFullPath((Join-Path $ProjectRoot '00_control'))
$BuildLockPath = Join-Path $ProjectRoot '.o002-build.lock'
$BuildMarkerPath = Join-Path $ControlRoot 'BUILD_IN_PROGRESS'
$OutputManifestPath = Join-Path $ControlRoot 'OUTPUT_FILE_MANIFEST.csv'
$ReceiptRoot = Join-Path $ProjectRoot 'tmp\build-receipts'
$SourceQAReceipt = Join-Path $ReceiptRoot 'SOURCE_QA.json'
$TestQAReceipt = Join-Path $ReceiptRoot 'TEST_QA.json'
$ToolchainQAReceipt = Join-Path $ReceiptRoot 'TOOLCHAIN_QA.json'
$PdfVisualControlReceipt = Join-Path $ControlRoot 'PDF_VISUAL_QA.json'
$PdfName = 'Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf'
$PdfPath = Join-Path $OutputRoot $PdfName
$CatalogPath = Join-Path $ProjectRoot 'backend\catalog.json'
$OutputCatalogPath = Join-Path $OutputRoot 'backend\catalog.json'
$DefaultPython = $null
$PythonCandidates = @()
foreach ($VariableName in @('O002_PYTHON', 'QUARTO_PYTHON')) {
    $Candidate = [System.Environment]::GetEnvironmentVariable($VariableName)
    if (-not [string]::IsNullOrWhiteSpace($Candidate)) {
        $PythonCandidates += $Candidate
    }
}
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $PythonCandidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe')
}
$PathPython = Get-Command python -ErrorAction SilentlyContinue
if ($null -ne $PathPython) {
    $PythonCandidates += $PathPython.Source
}
foreach ($Candidate in $PythonCandidates) {
    if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
        $DefaultPython = [System.IO.Path]::GetFullPath($Candidate)
        break
    }
}
if ($null -eq $DefaultPython) {
    throw 'No Python runtime found. Set O002_PYTHON to Python 3.13.1.'
}

if (-not $OutputRoot.StartsWith($ProjectRoot + [System.IO.Path]::DirectorySeparatorChar)) {
    throw "Output path escapes project root: $OutputRoot"
}

try {
    $BuildLock = [System.IO.File]::Open(
        $BuildLockPath,
        [System.IO.FileMode]::OpenOrCreate,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
} catch {
    throw "Another O002 build holds the lane lock: $BuildLockPath"
}

try {
Set-Location -LiteralPath $ProjectRoot
$BuildSucceeded = $false
[System.IO.File]::WriteAllText(
    $BuildMarkerPath,
    "Build in progress; OUTPUT_FILE_MANIFEST.csv is invalid until this marker is removed.`n",
    [System.Text.UTF8Encoding]::new($false)
)
if (Test-Path -LiteralPath $OutputManifestPath -PathType Leaf) {
    Remove-Item -LiteralPath $OutputManifestPath -Force
}
New-Item -ItemType Directory -Path $ReceiptRoot -Force | Out-Null
foreach ($Receipt in @($SourceQAReceipt, $TestQAReceipt, $ToolchainQAReceipt)) {
    if (Test-Path -LiteralPath $Receipt -PathType Leaf) {
        Remove-Item -LiteralPath $Receipt -Force
    }
}

# Fix timestamps embedded by TeX so repeated builds on the frozen toolchain can
# be compared byte-for-byte.
$env:SOURCE_DATE_EPOCH = '1787270400'
$env:FORCE_SOURCE_DATE = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

$env:QUARTO_PYTHON = $DefaultPython
if (-not (Test-Path -LiteralPath $env:QUARTO_PYTHON -PathType Leaf)) {
    throw "Python build runtime not found: $env:QUARTO_PYTHON"
}
$PythonDirectory = [System.IO.Path]::GetDirectoryName($env:QUARTO_PYTHON)
$PythonScriptsDirectory = Join-Path $PythonDirectory 'Scripts'
$env:PATH = $PythonDirectory + [System.IO.Path]::PathSeparator + $PythonScriptsDirectory + [System.IO.Path]::PathSeparator + $env:PATH
$JupyterDataDirectory = Join-Path $ProjectRoot 'build-support\jupyter'
$env:JUPYTER_PATH = $JupyterDataDirectory + [System.IO.Path]::PathSeparator + $env:JUPYTER_PATH

$ResolvedPython = [System.IO.Path]::GetFullPath((Get-Command python -ErrorAction Stop).Source)
if ($ResolvedPython -ne [System.IO.Path]::GetFullPath($env:QUARTO_PYTHON)) {
    throw "Jupyter kernel launcher resolves a different Python: $ResolvedPython"
}
$PythonVersion = (& $env:QUARTO_PYTHON -B -c 'import platform; print(platform.python_version())').Trim()
if ($PythonVersion -ne '3.13.1') {
    throw "O002 requires Python 3.13.1; resolved $PythonVersion at $ResolvedPython"
}

& $env:QUARTO_PYTHON -B scripts/toolchain_receipt.py --receipt $ToolchainQAReceipt
if ($LASTEXITCODE -ne 0) { throw 'Frozen toolchain validation failed.' }

& $env:QUARTO_PYTHON -B scripts/update_backend.py --qa-status pending --pdf-visual-status pending
if ($LASTEXITCODE -ne 0) { throw 'Backend could not be placed in pending state.' }

& $env:QUARTO_PYTHON -B scripts/source_qa.py --receipt $SourceQAReceipt
if ($LASTEXITCODE -ne 0) { throw 'Source-structure QA failed.' }

& $env:QUARTO_PYTHON -B scripts/run_tests.py --receipt $TestQAReceipt
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }

if (Test-Path -LiteralPath $OutputRoot) {
    $OutputItem = Get-Item -LiteralPath $OutputRoot -Force
    if (($OutputItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to clean reparse-point output path: $OutputRoot"
    }
    Remove-Item -LiteralPath $OutputRoot -Recurse -Force
}

$GeneratedTex = Join-Path $ProjectRoot 'Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.tex'
if (Test-Path -LiteralPath $GeneratedTex -PathType Leaf) {
    Remove-Item -LiteralPath $GeneratedTex -Force
}
$LegacySiteLibs = Join-Path $ProjectRoot 'site_libs'
if (Test-Path -LiteralPath $LegacySiteLibs -PathType Container) {
    $LegacySiteLibsItem = Get-Item -LiteralPath $LegacySiteLibs -Force
    if (($LegacySiteLibsItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to clean reparse-point legacy site_libs: $LegacySiteLibs"
    }
    Remove-Item -LiteralPath $LegacySiteLibs -Recurse -Force
}

quarto render
if ($LASTEXITCODE -ne 0) { throw 'Quarto reader build failed.' }

& $env:QUARTO_PYTHON -B source/code/unit01_experiment.py --limit 1000 --output output/unit01-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 1 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit02_objects.py --output output/unit02-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 2 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit03_arrays.py --output output/unit03-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 3 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit04_visualization.py --output-dir output/unit04
if ($LASTEXITCODE -ne 0) { throw 'Unit 4 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit05_symbolic.py --output output/unit05-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 5 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit06_floating.py --output output/unit06-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 6 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit07_experiment_design.py --output output/unit07-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 7 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit08_validation.py --output output/unit08-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 8 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit09_provenance.py --output output/unit09-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 9 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit10_pipeline.py --output output/unit10-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 10 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit11_numerical.py --output output/unit11-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 11 experiment failed.' }

& $env:QUARTO_PYTHON -B source/code/unit12_capstone.py verify --root source/data/unit12-demo --manifest source/data/unit12-demo/RUN_MANIFEST.json --output output/unit12-results.json
if ($LASTEXITCODE -ne 0) { throw 'Unit 12 verification failed.' }

Copy-Item -LiteralPath $SourceQAReceipt -Destination (Join-Path $OutputRoot 'SOURCE_QA.json')
Copy-Item -LiteralPath $TestQAReceipt -Destination (Join-Path $OutputRoot 'TEST_QA.json')
Copy-Item -LiteralPath $ToolchainQAReceipt -Destination (Join-Path $OutputRoot 'TOOLCHAIN_QA.json')

if (-not (Test-Path -LiteralPath $PdfPath -PathType Leaf)) {
    throw "PDF final tidak ditemukan: $PdfPath"
}
& $env:QUARTO_PYTHON -B scripts/pdf_visual_receipt.py verify --receipt $PdfVisualControlReceipt --pdf $PdfPath
if ($LASTEXITCODE -ne 0) { throw 'Durable PDF visual QA receipt does not match the current PDF.' }
Copy-Item -LiteralPath $PdfVisualControlReceipt -Destination (Join-Path $OutputRoot 'PDF_VISUAL_QA.json')

& $env:QUARTO_PYTHON -B scripts/update_backend.py --qa-status pass --pdf-visual-status pass
if ($LASTEXITCODE -ne 0) { throw 'Backend completion update failed.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $OutputCatalogPath) -Force | Out-Null
Copy-Item -LiteralPath $CatalogPath -Destination $OutputCatalogPath -Force

& $env:QUARTO_PYTHON -B scripts/qa.py
if ($LASTEXITCODE -ne 0) { throw 'Post-build QA failed.' }

& $env:QUARTO_PYTHON -B scripts/make_manifests.py --include-output
if ($LASTEXITCODE -ne 0) { throw 'Manifest generation failed.' }
$BuildSucceeded = $true
Remove-Item -LiteralPath $BuildMarkerPath -Force
} finally {
    if (-not $BuildSucceeded) {
        if (Test-Path -LiteralPath $OutputManifestPath -PathType Leaf) {
            Remove-Item -LiteralPath $OutputManifestPath -Force
        }
        if (Test-Path -LiteralPath $DefaultPython -PathType Leaf) {
            & $DefaultPython -B (Join-Path $ProjectRoot 'scripts\update_backend.py') --qa-status pending --pdf-visual-status pending | Out-Null
        }
    }
    if ($null -ne $BuildLock) {
        $BuildLock.Dispose()
    }
    if (Test-Path -LiteralPath $BuildLockPath -PathType Leaf) {
        Remove-Item -LiteralPath $BuildLockPath -Force
    }
}
