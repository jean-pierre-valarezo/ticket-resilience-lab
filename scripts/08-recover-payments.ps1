Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

kubectl -n ticket-lab set env deployment/payments PAYMENT_DELAY_MS=0 PAYMENT_FAILURE_RATE=0
kubectl -n ticket-lab rollout status deployment/payments --timeout=180s

Write-Host "Reiniciando reservations para limpiar el estado en memoria del circuit breaker."
kubectl -n ticket-lab rollout restart deployment/reservations
kubectl -n ticket-lab rollout status deployment/reservations --timeout=180s

Write-Host ""
kubectl -n ticket-lab get pods -o wide
