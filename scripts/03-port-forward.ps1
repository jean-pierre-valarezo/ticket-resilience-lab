Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$namespace = "ticket-lab"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot ".run"
$pidFile = Join-Path $runDir "port-forward-pids.txt"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$forwards = @(
    @{ Name = "gateway"; Service = "gateway"; LocalPort = 8080; RemotePort = 8000 },
    @{ Name = "reservations"; Service = "reservations"; LocalPort = 8081; RemotePort = 8001 },
    @{ Name = "inventory"; Service = "inventory"; LocalPort = 8082; RemotePort = 8002 }
)

foreach ($forward in $forwards) {
    $mapping = "$($forward.LocalPort):$($forward.RemotePort)"
    $arguments = @("-n", $namespace, "port-forward", "svc/$($forward.Service)", $mapping)
    $process = Start-Process -FilePath "kubectl" -ArgumentList $arguments -WindowStyle Hidden -PassThru
    "$($forward.Name),$($process.Id)" | Add-Content -Path $pidFile
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Port-forwards iniciados. PIDs guardados en $pidFile"
Get-Content -Path $pidFile

Write-Host ""
Write-Host "URLs locales:"
Write-Host "- Gateway:      http://localhost:8080"
Write-Host "- Reservations: http://localhost:8081"
Write-Host "- Inventory:    http://localhost:8082"
