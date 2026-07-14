param(
    [string]$Profile = "ticket-lab"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    throw "minikube no esta instalado. Instala minikube o usa el archivo k8s/base con otro cluster Kubernetes."
}

$running = $true
try {
    minikube -p $Profile status | Out-Null
}
catch {
    $running = $false
}

if (-not $running) {
    Write-Host "Iniciando perfil $Profile con 2 nodos y CNI kindnet..."
    minikube start -p $Profile --nodes=2 --cni=kindnet
}

kubectl config use-context $Profile | Out-Null

$nodes = @(kubectl get nodes --no-headers 2>$null)
if ($nodes.Count -lt 2) {
    Write-Host "El cluster tiene $($nodes.Count) nodo(s). Agregando un worker para cumplir la practica..."
    minikube -p $Profile node add --worker
}

for ($attempt = 1; $attempt -le 30; $attempt++) {
    $readyNodes = @(kubectl get nodes --no-headers | Where-Object { $_ -match "\sReady\s" })
    if ($readyNodes.Count -ge 2) {
        break
    }

    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "Captura recomendada: cluster Kubernetes con minimo 2 nodos."
kubectl get nodes -o wide
