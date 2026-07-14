Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot ".run/port-forward-pids.txt"

if (-not (Test-Path $pidFile)) {
    Write-Host "No hay archivo de PIDs de port-forward."
    return
}

Get-Content -Path $pidFile | ForEach-Object {
    $parts = $_ -split ","
    if ($parts.Count -ne 2) {
        return
    }

    $name = $parts[0]
    $processId = [int]$parts[1]
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Deteniendo port-forward $name con PID $processId..."
        Stop-Process -Id $processId -Force
    }
}

Remove-Item -Path $pidFile -Force
Write-Host "Port-forwards detenidos."
