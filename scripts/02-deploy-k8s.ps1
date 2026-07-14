param(
    [string]$Context = "ticket-lab"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

kubectl config use-context $Context | Out-Null
kubectl apply -k k8s/base

$deployments = @(
    "postgres",
    "inventory",
    "payments",
    "notifications",
    "reservations",
    "gateway"
)

foreach ($deployment in $deployments) {
    Write-Host ""
    Write-Host "Esperando deployment/$deployment..."
    kubectl -n ticket-lab rollout status "deployment/$deployment" --timeout=180s
}

Write-Host ""
Write-Host "Captura recomendada: pods desplegados y nodo donde corre cada componente."
kubectl -n ticket-lab get pods -o wide

Write-Host ""
kubectl -n ticket-lab get svc
