Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

kubectl -n ticket-lab scale deployment/notifications --replicas=1
kubectl -n ticket-lab rollout status deployment/notifications --timeout=180s

Write-Host ""
kubectl -n ticket-lab get pods -o wide
