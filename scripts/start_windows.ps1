param([switch]$Install)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
function Invoke-Checked([scriptblock]$Action) {
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE). Stop and read the error above." }
}
if (!(Test-Path "requirements.txt") -or !(Test-Path "frontend/package.json")) {
    throw "This is not the updated project root. Pull the latest GitHub main branch first."
}
if (!(Test-Path ".venv/Scripts/python.exe")) {
    Invoke-Checked { py -3.12 -m venv .venv }
    $Install = $true
}
$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
$version = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($version -ne "3.12") { throw "This .venv uses Python $version. Create a separate Python 3.12 environment before continuing; your existing environment was not deleted." }
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
if (!(Test-Path "frontend/.env.local")) { Copy-Item "frontend/.env.example" "frontend/.env.local" }
if ($Install) {
    Invoke-Checked { & $python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu }
    Invoke-Checked { & $python -m pip install -r requirements.txt }
    Push-Location frontend
    try { Invoke-Checked { npm ci } } finally { Pop-Location }
}
Invoke-Checked { & $python scripts/prepare_data.py }
Invoke-Checked { & $python scripts/run_stack.py }
