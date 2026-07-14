param(
    [string]$GatewayUrl = "http://localhost:8080"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot/lib/http.ps1"

Write-Host "Inyectando falla: Notifications down."
kubectl -n ticket-lab scale deployment/notifications --replicas=0
Start-Sleep -Seconds 5
kubectl -n ticket-lab get pods -o wide

$body = @{
    event_id = "concert-1"
    seat_id = "A7"
    user_id = "notification-down-demo"
    amount = 50
}

$result = Invoke-JsonPost -Uri "$GatewayUrl/reserve" -Body $body
Write-JsonResult -Title "Reserva con Notifications caido" -Result $result

Write-Host ""
Write-Host "Resultado esperado: reserva confirmada y notification.status=pending."
Write-Host "Captura recomendada: notifications en 0 replicas + reserva confirmada con fallback."
