param(
    [string]$GatewayUrl = "http://localhost:8080",
    [string]$InventoryUrl = "http://localhost:8082"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot/lib/http.ps1"

$gatewayHealth = Invoke-JsonGet -Uri "$GatewayUrl/health"
Write-JsonResult -Title "Gateway health" -Result $gatewayHealth

$inventoryHealth = Invoke-JsonGet -Uri "$InventoryUrl/health"
Write-JsonResult -Title "Inventory health" -Result $inventoryHealth

$inventoryBefore = Invoke-JsonGet -Uri "$InventoryUrl/inventory/concert-1"
Write-JsonResult -Title "Inventario antes de reservar" -Result $inventoryBefore

$seat = ($inventoryBefore.Body.seats | Where-Object { $_.status -eq "available" } | Select-Object -First 1).seat_id
if (-not $seat) {
    throw "No hay asientos disponibles. Ejecuta scripts/11-reset-lab.ps1 para reiniciar el laboratorio."
}

$body = @{
    event_id = "concert-1"
    seat_id = $seat
    user_id = "demo-user"
    amount = 50
}

$reservation = Invoke-JsonPost -Uri "$GatewayUrl/reserve" -Body $body
Write-JsonResult -Title "Reserva exitosa via gateway" -Result $reservation

$inventoryAfter = Invoke-JsonGet -Uri "$InventoryUrl/inventory/concert-1"
Write-JsonResult -Title "Inventario despues de reservar" -Result $inventoryAfter

Write-Host ""
Write-Host "Capturas recomendadas: health checks, inventario antes, reserva confirmada e inventario despues."
