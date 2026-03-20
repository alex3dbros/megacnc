# Build Mega CNC as a Windows onedir bundle (PyInstaller).
# Run from repo root or from packaging/ - produces dist/MegaCNC/

$ErrorActionPreference = "Stop"

# Pip requires UTF-8. Some editors save requirements*.txt as UTF-16 (pip then sees D\x00j\x00a...).
function Repair-RequirementsTxtEncoding {
    param([Parameter(Mandatory)][string]$FilePath)
    if (-not (Test-Path -LiteralPath $FilePath)) { return }
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    if ($bytes.Length -lt 2) { return }

    $text = $null
    # UTF-16 LE with BOM
    if ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        $text = [System.Text.Encoding]::Unicode.GetString($bytes, 2, $bytes.Length - 2)
    }
    # UTF-16 BE with BOM
    elseif ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        $text = [System.Text.Encoding]::BigEndianUnicode.GetString($bytes, 2, $bytes.Length - 2)
    }
    # UTF-16 LE without BOM (e.g. "D\x00j\x00a\x00..." for Django)
    elseif ($bytes.Length -ge 8 -and $bytes[1] -eq 0 -and $bytes[3] -eq 0 -and $bytes[5] -eq 0 -and $bytes[0] -ne 0) {
        $ascii = 0
        for ($i = 0; $i -lt [Math]::Min(40, $bytes.Length); $i += 2) {
            if ($bytes[$i] -ge 32 -and $bytes[$i] -le 126) { $ascii++ }
        }
        if ($ascii -ge 5) {
            $text = [System.Text.Encoding]::Unicode.GetString($bytes)
        }
    }

    if ($null -ne $text) {
        $utf8 = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($FilePath, $text.TrimEnd("`r", "`n") + "`n", $utf8)
        Write-Host "Re-saved as UTF-8: $FilePath" -ForegroundColor Yellow
    }
}

$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "manage.py"))) {
    Write-Error "Could not find manage.py. Run this script from the repository (packaging/build_windows.ps1)."
}

Set-Location $Root
$env:MEGACNC_ROOT = $Root

Repair-RequirementsTxtEncoding (Join-Path $Root "requirements.txt")
Repair-RequirementsTxtEncoding (Join-Path $Root "packaging\requirements-build.txt")

Write-Host "Project root: $Root"

if (-not (Test-Path ".venv-build")) {
    python -m venv .venv-build
}

$PyExe = Join-Path $Root ".venv-build\Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
    Write-Error "Python venv is broken: missing $PyExe"
}

& $PyExe -m pip install --upgrade pip
& $PyExe -m pip install -r requirements.txt -r packaging\requirements-build.txt

# Clean previous output
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\MegaCNC") { Remove-Item -Recurse -Force "dist\MegaCNC" }

& $PyExe -m PyInstaller --noconfirm packaging\MegaCNC.spec

Write-Host ""
Write-Host "Done. Run:  dist\MegaCNC\MegaCNC.exe"
Write-Host 'Copy the whole folder dist\MegaCNC\ - it contains DLLs and _internal.'
