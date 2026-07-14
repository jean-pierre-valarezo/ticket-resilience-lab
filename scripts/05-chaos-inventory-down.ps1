param(
    [string]$GatewayUrl = "http://localhost:8080"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot/lib/http.ps1"

Write-Host "Inyectando falla: Inventory down."
kubectl -n ticket-lab scale deployment/inventory --replicas=0
Start-Sleep -Seconds 5
kubectl -n ticket-lab get pods -o wide

$body = @{
    event_id = "concert-1"
    seat_id = "A2"
    user_id = "inventory-down-demo"
    amount = 50
}

$result = Invoke-JsonPost -Uri "$GatewayUrl/reserve" -Body $body
Write-JsonResult -Title "Reserva con Inventory caido" -Result $result

Write-Host ""
Write-Host "Resultado esperado: HTTP 503/504. El sistema falla rapido y no confirma una reserva sin inventario."
Write-Host "Captura recomendada: deployment inventory en 0 replicas + respuesta controlada del gateway."
