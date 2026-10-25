param([switch]$Install, [switch]$RepairFrontend)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
function Invoke-Checked([scriptblock]$Action) {
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE). Stop and read the error above." }
}
if (!(Test-Path "requirements.txt") -or !(Test-Path "frontend/package.json")) {
    throw "Run this script from the updated VigiloForge checkout."
}
# Refuse to replace native modules while this project's Node processes hold them.
# Never terminate unrelated servers or delete credentials as part of repair.
$projectNodes = @(Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($projectRoot, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ($projectNodes.Count -gt 0) {
    $projectNodes | Select-Object ProcessId, CommandLine | Format-Table -Wrap
    throw "This project's Node processes are still running. Press Ctrl+C in their terminals (or stop the listed project PIDs), then retry. This prevents npm EPERM errors on next-swc."
}
foreach ($port in @(8000, 8001, 3000)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is occupied. Stop the old stack with Ctrl+C before setup. No process was stopped."
    }
}
if (!(Get-Command node -ErrorAction SilentlyContinue) -or !(Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Install Node.js 22 or newer with npm, then reopen this terminal."
}
Invoke-Checked { node -e "if (Number(process.versions.node.split('.')[0]) < 22) { console.error('Node.js 22 or newer is required.'); process.exit(1); }" }
if (!(Test-Path ".venv/Scripts/python.exe")) {
    Invoke-Checked { py -3.12 -m venv .venv }
    $Install = $true
}
$python = Join-Path $projectRoot ".venv/Scripts/python.exe"
$version = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($version -ne "3.12") { throw "This .venv uses Python $version. A Python 3.12 environment is required; your existing environment was not deleted." }
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
if (!(Test-Path "frontend/.env.local")) { Copy-Item "frontend/.env.example" "frontend/.env.local" }
if ($Install) {
    Invoke-Checked { & $python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu }
    Invoke-Checked { & $python -m pip install -r requirements.txt }
}
if ($Install -or $RepairFrontend) {
    Push-Location frontend
    try {
        & npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend install failed. If npm reports EPERM on next-swc, close this project's Node processes or restart Windows, then retry with -RepairFrontend. Your .env files and lockfile were preserved."
        }
    } finally { Pop-Location }
}
Invoke-Checked { & $python scripts/prepare_data.py }
Invoke-Checked { & $python scripts/run_stack.py --open-browser }
