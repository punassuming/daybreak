[CmdletBinding()]
param(
    [ValidateSet("toggle", "light", "dark", "select", "setup")]
    [string]$Mode = "toggle",

    [switch]$ReloadTheme
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-PythonCommand {
    foreach ($candidate in @("py", "python", "python3")) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }
    return $null
}

function Invoke-Daybreak {
    $daybreakCmd = Get-Command "daybreak" -ErrorAction SilentlyContinue
    if ($daybreakCmd) {
        & $daybreakCmd.Source $Mode
        return $LASTEXITCODE
    }

    $localSrc = Join-Path $PSScriptRoot "daybreak\src"
    if (-not (Test-Path $localSrc)) {
        throw "Could not find 'daybreak' command or local source path at '$localSrc'."
    }

    $pythonCmd = Resolve-PythonCommand
    if (-not $pythonCmd) {
        throw "Could not find a Python executable (tried: py, python, python3)."
    }

    $oldPythonPath = $env:PYTHONPATH
    if ([string]::IsNullOrWhiteSpace($oldPythonPath)) {
        $env:PYTHONPATH = $localSrc
    }
    else {
        $env:PYTHONPATH = "$localSrc;$oldPythonPath"
    }

    try {
        & $pythonCmd -m daybreak.main $Mode
        return $LASTEXITCODE
    }
    finally {
        $env:PYTHONPATH = $oldPythonPath
    }
}

$exitCode = Invoke-Daybreak
if ($exitCode -ne 0) {
    exit $exitCode
}

if ($ReloadTheme -or $Mode -in @("toggle", "light", "dark")) {
    $themeScript = Join-Path $HOME ".config\daybreak\theme.ps1"
    if (Test-Path $themeScript) {
        . $themeScript
    }
}
