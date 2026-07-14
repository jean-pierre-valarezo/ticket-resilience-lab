param(
    [string]$GatewayUrl = "http://localhost:8080",
    [string]$ReservationsUrl = "http://localhost:8081"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot/lib/http.ps1"

Write-Host "Inyectando falla: pasarela de pagos lenta con 20 segundos de latencia."
kubectl -n ticket-lab set env deployment/payments PAYMENT_DELAY_MS=20000
kubectl -n ticket-lab rollout status deployment/payments --timeout=180s

$seats = @("A3", "A4", "A5", "A6")
for ($i = 0; $i -lt $seats.Count; $i++) {
    $body = @{
        event_id = "concert-1"
        seat_id = $seats[$i]
        user_id = "slow-payment-demo-$i"
        amount = 50
    }

    $result = Invoke-JsonPost -Uri "$GatewayUrl/reserve" -Body $body
    Write-JsonResult -Title "Intento $($i + 1) con pagos lentos" -Result $result
}

$resilience = Invoke-JsonGet -Uri "$ReservationsUrl/resilience"
Write-JsonResult -Title "Estado del circuit breaker de pagos" -Result $resilience

Write-Host ""
Write-Host "Resultado esperado: timeouts controlados y circuit breaker abierto despues de varios fallos."
Write-Host "Captura recomendada: PAYMENT_DELAY_MS=20000, respuestas 503 y /resilience con estado open."
