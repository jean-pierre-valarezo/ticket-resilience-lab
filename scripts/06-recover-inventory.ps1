Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

kubectl -n ticket-lab scale deployment/inventory --replicas=2
kubectl -n ticket-lab rollout status deployment/inventory --timeout=180s

Write-Host ""
kubectl -n ticket-lab get pods -o wide
