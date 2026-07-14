Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

kubectl -n ticket-lab scale deployment/postgres deployment/inventory deployment/payments deployment/notifications deployment/reservations deployment/gateway --replicas=1
kubectl -n ticket-lab set env deployment/payments PAYMENT_DELAY_MS=0 PAYMENT_FAILURE_RATE=0
kubectl -n ticket-lab set env deployment/notifications NOTIFICATION_DELAY_MS=0 NOTIFICATION_FAILURE_RATE=0

Write-Host "Reiniciando deployments para volver a un estado limpio..."
kubectl -n ticket-lab rollout restart deployment/postgres deployment/inventory deployment/payments deployment/notifications deployment/reservations deployment/gateway

$deployments = @(
    "postgres",
    "inventory",
    "payments",
    "notifications",
    "reservations",
    "gateway"
)

foreach ($deployment in $deployments) {
    kubectl -n ticket-lab rollout status "deployment/$deployment" --timeout=180s
}

Write-Host ""
kubectl -n ticket-lab get pods -o wide
